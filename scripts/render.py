#!/usr/bin/env python3
"""Render a mapped Chinese mobile edition from structured JSON.

This script validates source-item coverage and formats content. It does not
translate, OCR, or verify that a translated sentence is semantically faithful.
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
import re
import shutil
import sys
import zipfile
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
ALLOWED_KINDS = {
    "paragraph", "quote", "label", "subheading", "list", "table", "figure",
    "equation", "code", "audio", "video",
}
SAFE_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]*$")


class ContentError(ValueError):
    pass


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContentError(message)


def nonempty(value: object, path: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), f"{path}: expected nonempty text")
    return value


def source_refs(value: object, known: set[str], path: str, allow_empty: bool = False) -> list[str]:
    require(isinstance(value, list), f"{path}: source_refs must be an array")
    require(allow_empty or bool(value), f"{path}: missing source_refs")
    require(all(isinstance(ref, str) and ref in known for ref in value),
            f"{path}: unknown source item in source_refs")
    return value


def attrs(refs: list[str]) -> str:
    return f' data-source-refs="{esc(" ".join(refs))}"' if refs else ""


def safe_href(value: object) -> str:
    require(isinstance(value, str), "link href must be text")
    parts = urlsplit(value)
    require(parts.scheme.lower() in {"https", "http", "mailto"} or
            (value.startswith("#") and bool(value[1:]) and not parts.scheme),
            f"unsafe link href: {value[:80]}")
    return esc(value)


def rich(value: object, path: str) -> str:
    if isinstance(value, str):
        return esc(value)
    require(isinstance(value, list), f"{path}: expected text or runs array")
    result = []
    for i, run in enumerate(value):
        require(isinstance(run, dict), f"{path}[{i}]: expected object")
        piece = esc(nonempty(run.get("text"), f"{path}[{i}].text"))
        mark = run.get("mark")
        require(mark in {None, "strong", "em", "code"}, f"{path}[{i}]: invalid mark")
        if mark:
            piece = f"<{mark}>{piece}</{mark}>"
        if "href" in run:
            piece = f'<a href="{safe_href(run["href"])}">{piece}</a>'
        result.append(piece)
    return "".join(result)


def text_content(obj: dict, path: str) -> str:
    require("text" in obj or "runs" in obj, f"{path}: missing text/runs")
    require(not ("text" in obj and "runs" in obj), f"{path}: use either text or runs")
    return rich(obj.get("runs", obj.get("text")), path)


def check_document(doc: object) -> tuple[list[dict], set[str], set[str]]:
    require(isinstance(doc, dict), "root must be an object")
    require(doc.get("schema_version") == 1, "schema_version must be 1")
    nonempty(doc.get("title"), "title")
    items = doc.get("source_items")
    require(isinstance(items, list) and bool(items), "source_items must be a nonempty array")
    known = set()
    for i, item in enumerate(items):
        require(isinstance(item, dict), f"source_items[{i}] must be an object")
        identifier = nonempty(item.get("id"), f"source_items[{i}].id")
        require(identifier not in known, f"duplicate source item: {identifier}")
        known.add(identifier)
        nonempty(item.get("kind"), f"source_items[{i}].kind")
        nonempty(item.get("locator"), f"source_items[{i}].locator")
    used = set(source_refs(doc.get("title_source_refs"), known, "title_source_refs"))
    omitted = set()
    omissions = doc.get("omissions", [])
    require(isinstance(omissions, list), "omissions must be an array")
    for i, omission in enumerate(omissions):
        require(isinstance(omission, dict), f"omissions[{i}] must be an object")
        identifier = omission.get("source_id")
        require(identifier in known and identifier not in omitted,
                f"omissions[{i}]: unknown or duplicate source_id")
        nonempty(omission.get("reason"), f"omissions[{i}].reason")
        omitted.add(identifier)
    sections = doc.get("sections")
    require(isinstance(sections, list) and bool(sections), "sections must be a nonempty array")
    section_ids = set()
    for i, section in enumerate(sections):
        path = f"sections[{i}]"
        require(isinstance(section, dict), f"{path} must be an object")
        identifier = nonempty(section.get("id"), f"{path}.id")
        require(SAFE_ID.fullmatch(identifier) is not None, f"{path}.id: use ASCII letters, digits, - or _")
        require(identifier not in section_ids, f"duplicate section id: {identifier}")
        section_ids.add(identifier)
        title = section.get("title")
        if title is not None:
            nonempty(title, f"{path}.title")
            label = section.get("nav_label")
            if label is not None:
                require(isinstance(label, str) and label in title,
                        f"{path}.nav_label must be a verbatim substring of title")
        refs = source_refs(section.get("source_refs", []), known, f"{path}.source_refs",
                           allow_empty=title is None)
        used.update(refs)
        blocks = section.get("blocks")
        require(isinstance(blocks, list), f"{path}.blocks must be an array")
        for j, block in enumerate(blocks):
            block_path = f"{path}.blocks[{j}]"
            require(isinstance(block, dict), f"{block_path} must be an object")
            require(block.get("kind") in ALLOWED_KINDS,
                    f"{block_path}: unsupported kind {block.get('kind')!r}")
            used.update(source_refs(block.get("source_refs"), known, f"{block_path}.source_refs"))
    if doc.get("lead_figure") is not None:
        lead = doc["lead_figure"]
        require(isinstance(lead, dict) and lead.get("kind") == "figure",
                "lead_figure must be a figure block")
        used.update(source_refs(lead.get("source_refs"), known, "lead_figure.source_refs"))
    require(not (used & omitted), f"source items both rendered and omitted: {sorted(used & omitted)}")
    missing = known - used - omitted
    require(not missing, f"unmapped source items: {', '.join(sorted(missing))}")
    return sections, used, omitted


class MediaStore:
    def __init__(self, source_dir: Path, output: Path, max_inline_bytes: int):
        self.source_dir = source_dir
        self.output = output
        self.max_inline_bytes = max_inline_bytes
        self.total_inline = 0
        self.sidecars: list[Path] = []

    def source(self, raw: object) -> Path:
        name = nonempty(raw, "media src")
        path = Path(name)
        require(not name.startswith(("http://", "https://", "data:")),
                "media src must be a local file")
        path = (self.source_dir / path).resolve() if not path.is_absolute() else path.resolve()
        require(path.is_file(), f"media file does not exist: {path}")
        return path

    def href(self, raw: object) -> str:
        path = self.source(raw)
        size = path.stat().st_size
        mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if self.total_inline + size <= self.max_inline_bytes:
            self.total_inline += size
            data = base64.b64encode(path.read_bytes()).decode("ascii")
            return f"data:{mime};base64,{data}"
        target_dir = self.output.with_name(self.output.stem + "_assets")
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / path.name
        if target.exists() and target.read_bytes() != path.read_bytes():
            target = target_dir / f"{len(self.sidecars) + 1:03d}-{path.name}"
        if not target.exists():
            shutil.copy2(path, target)
        if target not in self.sidecars:
            self.sidecars.append(target)
        return f"{target_dir.name}/{target.name}"


def render_block(block: dict, path: str, media: MediaStore) -> str:
    kind = block["kind"]
    marker = attrs(block["source_refs"])
    if kind in {"paragraph", "quote", "label", "subheading"}:
        content = text_content(block, path)
        if kind == "paragraph":
            return f"<p{marker}>{content}</p>"
        if kind == "quote":
            return f"<blockquote{marker}><p>{content}</p></blockquote>"
        if kind == "label":
            return f'<p class="label"{marker}>{content}</p>'
        return f"<h3{marker}>{content}</h3>"
    if kind == "list":
        items = block.get("items")
        require(isinstance(items, list) and bool(items), f"{path}.items must be a nonempty array")
        tag = "ol" if block.get("ordered", False) else "ul"
        content = "".join(f"<li>{rich(item, f'{path}.items[{i}]')}</li>" for i, item in enumerate(items))
        return f"<{tag}{marker}>{content}</{tag}>"
    if kind == "table":
        headers, rows = block.get("headers"), block.get("rows")
        require(isinstance(headers, list) and bool(headers), f"{path}.headers must be nonempty")
        require(isinstance(rows, list), f"{path}.rows must be an array")
        require(all(isinstance(h, str) and h.strip() for h in headers),
                f"{path}.headers must contain nonempty text")
        require(all(isinstance(row, list) and len(row) == len(headers) for row in rows),
                f"{path}.rows must have {len(headers)} columns")
        heads = "".join(f'<th scope="col">{esc(h)}</th>' for h in headers)
        body = "".join("<tr>" + "".join(
            f'<td data-label="{esc(headers[i])}">{rich(cell, f"{path}.rows[{r}][{i}]")}</td>'
            for i, cell in enumerate(row)) + "</tr>" for r, row in enumerate(rows))
        caption = f"<figcaption>{esc(block['caption'])}</figcaption>" if block.get("caption") else ""
        notes = block.get("footnotes", [])
        require(isinstance(notes, list) and all(isinstance(n, str) for n in notes),
                f"{path}.footnotes must be an array of text")
        footnotes = "".join(f'<p class="table-footnote">{esc(note)}</p>' for note in notes)
        return (f"<figure{marker}><div class=\"table-scroll\"><table><thead><tr>{heads}</tr></thead>"
                f"<tbody>{body}</tbody></table></div>{caption}{footnotes}</figure>")
    if kind == "figure":
        alt = nonempty(block.get("alt"), f"{path}.alt")
        src = media.href(block.get("src"))
        caption = f"<figcaption>{esc(block['caption'])}</figcaption>" if block.get("caption") else ""
        credit = f'<p class="figure-credit">{esc(block["credit"])}</p>' if block.get("credit") else ""
        return (f'<figure{marker}><img class="figure-image" src="{esc(src)}" '
                f'alt="{esc(alt)}" loading="lazy">{caption}{credit}</figure>')
    if kind == "equation":
        content = nonempty(block.get("text"), f"{path}.text")
        return f'<div class="equation" role="math"{marker}><code>{esc(content)}</code></div>'
    if kind == "code":
        require(isinstance(block.get("text"), str), f"{path}.text must be text")
        language = f' data-language="{esc(block["language"])}"' if block.get("language") else ""
        return f"<pre{marker}><code{language}>{esc(block['text'])}</code></pre>"
    if kind in {"audio", "video"}:
        src = media.href(block.get("src"))
        poster = ""
        if kind == "video" and block.get("poster"):
            poster = f' poster="{esc(media.href(block["poster"]))}"'
        player = (f'<{kind} class="figure-media" controls preload="metadata" '
                  f'src="{esc(src)}"{poster}></{kind}>')
        caption = f"<figcaption>{esc(block['caption'])}</figcaption>" if block.get("caption") else ""
        transcript = block.get("transcript", [])
        require(isinstance(transcript, list), f"{path}.transcript must be an array")
        rows = []
        for i, line in enumerate(transcript):
            require(isinstance(line, dict), f"{path}.transcript[{i}] must be an object")
            time = nonempty(line.get("time"), f"{path}.transcript[{i}].time")
            spoken = nonempty(line.get("text"), f"{path}.transcript[{i}].text")
            rows.append(f"<p><time>{esc(time)}</time>{esc(spoken)}</p>")
        transcript_html = (f'<details class="transcript"><summary>查看中文逐字稿</summary>'
                           f'{"".join(rows)}</details>') if rows else ""
        return f"<figure{marker}>{player}{caption}{transcript_html}</figure>"
    raise ContentError(f"{path}: unsupported block kind {kind}")


def render_document(doc: dict, sections: list[dict], media: MediaStore) -> str:
    nav = []
    body = []
    for i, section in enumerate(sections):
        title = section.get("title")
        label = section.get("nav_label") or title or "全文"
        nav.append(f'<li><a href="#{esc(section["id"])}"><span class="nav-index">'
                   f'{i + 1:02d}</span><span class="nav-label">{esc(label)}</span></a></li>')
        heading = f'<h2{attrs(section["source_refs"])}>{esc(title)}</h2>' if title else ""
        content = "".join(render_block(block, f'sections[{i}].blocks[{j}]', media)
                          for j, block in enumerate(section["blocks"]))
        body.append(f'<section class="article-section" id="{esc(section["id"])}">'
                    f'{heading}{content}</section>')
    lead = ""
    if doc.get("lead_figure"):
        lead = render_block(doc["lead_figure"], "lead_figure", media).replace(
            "<figure", '<figure class="lead-figure"', 1)
    css = (ASSETS / "mobile.css").read_text(encoding="utf-8")
    js = (ASSETS / "mobile.js").read_text(encoding="utf-8")
    return ("<!doctype html>\n<html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
            '<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            f'<title>{esc(doc["title"])}</title><style>{css}</style></head><body>'
            '<nav class="reading-nav" aria-label="章节导航"><button class="nav-toggle" '
            'type="button" aria-expanded="false" aria-label="展开章节目录">目录</button>'
            f'<div class="nav-status" aria-live="polite">1 / {len(sections)}</div>'
            f'<ol class="nav-links">{"".join(nav)}</ol></nav>'
            '<div class="page"><header class="article-header">'
            f'<h1{attrs(doc["title_source_refs"])}>{esc(doc["title"])}</h1>{lead}'
            f'</header><main>{"".join(body)}</main></div><script>{js}</script></body></html>')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("content", type=Path, help="UTF-8 structured content JSON")
    parser.add_argument("--output", type=Path, required=True, help="output HTML file")
    parser.add_argument("--max-inline-mb", type=float, default=20,
                        help="total media bytes to inline before creating sidecars (default: 20)")
    args = parser.parse_args()
    try:
        require(args.max_inline_mb >= 0, "--max-inline-mb cannot be negative")
        source = args.content.resolve()
        output = args.output.resolve()
        doc = json.loads(source.read_text(encoding="utf-8"))
        sections, used, omitted = check_document(doc)
        output.parent.mkdir(parents=True, exist_ok=True)
        media = MediaStore(source.parent, output, int(args.max_inline_mb * 1024 * 1024))
        rendered = render_document(doc, sections, media)
        output.write_text(rendered, encoding="utf-8")
        report = output.with_suffix(".coverage.json")
        report.write_text(json.dumps({
            "source_items": len(doc["source_items"]),
            "rendered_items": len(used),
            "omitted_items": len(omitted),
            "unmapped_items": [],
            "omissions": doc.get("omissions", []),
            "note": "ID coverage only; semantic and visual fidelity require human/source review.",
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"HTML: {output}")
        print(f"Coverage report: {report} ({len(used)}/{len(doc['source_items'])} mapped, {len(omitted)} omitted)")
        if media.sidecars:
            archive = output.with_suffix(".zip")
            with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
                bundle.write(output, output.name)
                bundle.write(report, report.name)
                for asset in media.sidecars:
                    bundle.write(asset, f"{asset.parent.name}/{asset.name}")
            print(f"Media package: {archive}")
        return 0
    except (ContentError, OSError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
