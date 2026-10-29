---
name: mobile-source-edition
description: Turn a user-provided PDF, HTML page, URL, image, audio/video, slide, or mixed source into a faithful Chinese mobile reading edition with localized visuals and responsive HTML. Use when the user asks for a phone-friendly article or 微信公众号式阅读版; not for a brief summary alone.
---

# Mobile Source Edition

Create a Chinese reading edition that retains the source's claims, order, evidence, units, figure information, and uncertainty. The user may change the language, omit named parts, or request a summary; follow those choices. Never describe an edition as complete or strictly faithful until the coverage and visual checks below are done.

## Intake and source map

1. Preserve a source snapshot in the task workspace. For a URL, capture the rendered article and its assets/data, not only search-engine text. For PDF or other files, inspect the actual pages/frames. Read [references/intake.md](references/intake.md) for the relevant modality only.
2. Create a source-item inventory before writing: title, each heading/paragraph/list item, table cell or row as appropriate, caption, note, equation, figure label, and spoken segment. Give each item a stable ID and locator (page, selector, timestamp, or figure coordinate). Record user-requested omissions explicitly.
3. If a source cannot be accessed or transcribed, name the missing span and do not claim complete coverage. Do not infer invisible figure text or video narration.

## Translation and visuals

- Translate English into natural Chinese without compressing, strengthening, or adding claims. Preserve uncertainty words (may, suggests, approximately), negatives, comparison direction, order, numbers, units, symbols, names, and citations. Keep code/interface tokens in their original form when translation would change their function. For Chinese input, preserve the wording unless the user requests editing.
- Map every rendered heading/content block to its source-item ID(s). Prefer one source paragraph per translated paragraph. Put editorial explanations in a clearly marked separate note only if the user wants them; never blend them into translation.
- Keep the article body to source content and user-authorized translations. Do not add translation disclaimers, author/translator credit strips, dates, numbered section badges, a duplicate in-body table of contents, or headings invented for visual decoration. Use the source's real headings in their original order; the left rail may add navigation labels without adding prose to the article.
- Localize text-bearing figures. Preserve the original visual relationships and all labels, legends, axes, units, panel letters, footnotes, data values, and ordering. If a faithful Chinese redraw is not feasible, show the original plus a complete adjacent Chinese transcription and state that the image itself remains untranslated. Never substitute a generated schematic for a video or scientific figure while calling it a full translation.
- For charts, verify rank/order against the source data or rendered plot, not merely that the same numbers appear.

## Build and QA

1. Author the structured content file described in [references/schema.md](references/schema.md). The bundled renderer is an HTML formatter and coverage checker, not a translator:

   `python scripts/render.py content.json --output outputs/article.html`

2. The renderer uses `assets/mobile.css` and `assets/mobile.js`: white single-column layout, 16px/1.75 body text, spacious paragraphs, images near full content width, at most two article subheading levels, responsive tables, and a left chapter rail that shows reading position and supports jumps. It embeds small assets; large media are placed in an accompanying ZIP package. Keep technical QA and source-coverage notes in separate working files, not inside the reading page.
3. Read [references/fidelity.md](references/fidelity.md) before delivery. Complete sentence-level and figure-level checks; render at 320px and 390px plus desktop; inspect representative pages, navigation, tables, Chinese glyphs, and overflow. Save a short QA record with the source inventory coverage and any unresolved limitations.
4. Deliver only finished artifacts. Link the HTML, or the ZIP when sidecar media are needed. Explain any intentional departure from the source without claiming exact fidelity.

Keep working files and source extracts out of chat. For long material, checkpoint after each phase and continue in chunks without dropping source-item IDs.
