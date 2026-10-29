# Structured content schema for `scripts/render.py`

The renderer takes UTF-8 JSON. It escapes all supplied text and embeds local image/media assets; it does not fetch remote URLs or translate content. `source_refs` are stable IDs from `source_items`, not prose citations. Every substantive rendered block must have at least one source reference. The renderer rejects unknown/missing references and non-declared omissions.

```json
{
  "schema_version": 1,
  "title": "标题的中文译文",
  "title_source_refs": ["title-1"],
  "source_items": [
    {"id": "title-1", "kind": "title", "locator": "page 1"},
    {"id": "h-1", "kind": "heading", "locator": "page 1"},
    {"id": "p-1", "kind": "paragraph", "locator": "page 1, paragraph 1"},
    {"id": "fig-1", "kind": "figure", "locator": "page 2, figure 1"},
    {"id": "fig-1-caption", "kind": "caption", "locator": "page 2, figure 1 caption"}
  ],
  "omissions": [],
  "sections": [
    {
      "id": "introduction",
      "title": "原文一级小标题的中文译文",
      "source_refs": ["h-1"],
      "blocks": [
        {"kind": "paragraph", "source_refs": ["p-1"], "text": "逐段译文。"},
        {"kind": "figure", "source_refs": ["fig-1", "fig-1-caption"], "src": "assets/figure-1-zh.png", "alt": "图中信息的完整中文替代文本", "caption": "原图图注的译文"}
      ]
    }
  ]
}
```

If the source has no heading, a section may have `"title": null` and `"source_refs": []`; the navigation uses a neutral UI label such as “全文” without inserting a fabricated article heading. `nav_label` may be set to a shorter **verbatim substring** of an original heading when the full heading is too long for the left rail.

Block kinds:

- `paragraph`, `quote`, `label`, `subheading`: `text` or `runs`. `subheading` becomes `h3`; `label` is bold text for a deeper source heading flattened into the permitted two-level visual hierarchy.
- `list`: `items` (strings or run arrays), optional `ordered` boolean.
- `table`: `headers`, `rows` (equal-length arrays), optional `caption` and `footnotes` (array of strings).
- `figure`: local `src`, Chinese `alt`, optional `caption` and `credit`. Use a translated figure asset when possible.
- `equation`: `text` containing an exact accessible transcription of the formula; use a `figure` with a localized SVG when typography requires it.
- `code`: `text`, optional `language` label; preserves literal characters.
- `audio` or `video`: local `src`, optional local `poster`, `caption`, and `transcript` array of `{time, text}` entries. The transcript must be inventoried, not invented.

All blocks and titled sections require `source_refs`. An item intentionally omitted by explicit user direction belongs in `omissions` as `{"source_id":"...","reason":"..."}`. The renderer reports a missing source item as an error. It does not prove the translation is accurate; use [fidelity.md](fidelity.md) for that review.

Inline emphasis/links use `runs` instead of raw HTML:

```json
"runs": [
  {"text": "原句的译文"},
  {"text": "强调文字", "mark": "strong"},
  {"text": "论文链接", "href": "https://example.org/paper"}
]
```

Allowed marks are `strong`, `em`, and `code`. Text is HTML-escaped. URLs are limited to `https:`, `http:`, `mailto:`, or a local `#anchor`.
