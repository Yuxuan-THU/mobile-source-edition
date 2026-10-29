# Delivery audit

Before saying “complete,” inspect the actual source and output side by side. Keep the audit in a small local file; report only real limitations to the user.

1. **Coverage:** Every source-item ID is rendered or has a user-authorized omission. Revisit the original to check the inventory itself for missing paragraphs, captions, footnotes, tabs, frames, table headers, and image labels. A 100% ID match is not enough if the inventory skipped material.
2. **Meaning:** Read each source/translation pair in order. Check negation, modality/uncertainty, agency, comparisons, quantities, units, scope, causal claims, proper nouns, citations, code tokens, and whether a translator-added explanation crept into the prose.
3. **Figures and tables:** Compare the localized visual against the original at readable resolution. Check every label, legend, axis, tick, panel letter, arrow direction, rank order, statistical annotation, and caption. If the chart was rebuilt from data, confirm the source's sorting and denominators. Never infer fidelity from number-token presence alone.
4. **Media:** For audio/video, compare the transcript and on-screen localization against timestamps through the end. A thumbnail, sample clip, or poster is explicitly partial coverage.
5. **HTML QA:** Open the generated file offline at 320px, 390px, and desktop widths. Inspect title, mid-article figure, dense table, final section, left navigation open/closed and chapter jump, text wrapping, Chinese glyphs, and horizontal overflow. Confirm any sidecar ZIP contains all referenced media.
6. **Claim:** Say “严格逐项译本” only after the above passes with no unresolved source items. Otherwise say “阅读版” and list the exact remaining gaps. Do not claim “一字不差” across languages; describe the actual level of semantic and visual correspondence.
