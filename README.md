# Mobile Source Edition｜手机忠实阅读版

Codex Skill：把 PDF、网页、HTML、图片、音视频及混合材料整理成忠于来源的中文手机阅读 HTML。页面采用白底单栏、16px 正文、28px 行距、图片就近插入、响应式表格，以及可跳转并显示阅读位置的左侧章节导航。

## 使用

将本仓库放在 Codex 的 `~/.codex/skills/mobile-source-edition`，然后把材料交给 Codex，并说：

> 用 `$mobile-source-edition` 把这份材料做成忠实的中文手机阅读版，逐项核对正文和图表文字。

Skill 会先建立带页码、选择器或时间戳的来源清单，再翻译和本地化图表。它要求逐项核对原文与译文；无法读取的片段必须标明，不能宣称完整或严格忠实。

## 渲染器

内容写入 UTF-8 JSON，格式见 [`references/schema.md`](references/schema.md)。渲染器只负责排版与来源 ID 覆盖检查，**不自动翻译，也不能证明译文语义正确**。

```bash
python scripts/render.py examples/sample.json --output outputs/sample.html
python -m unittest discover -s tests -v
```

小型图片和媒体会嵌入 HTML；超过默认 20 MB 内嵌额度的媒体会放进同名资源目录，并生成包含 HTML 与资源的 ZIP。每次渲染还会产生 `.coverage.json`。交付前仍需按 [`references/fidelity.md`](references/fidelity.md) 对照来源检查，并在 320px、390px 和桌面宽度下查看页面。

`examples/` 是排版与覆盖校验样本，不代表真实论文或翻译质量测试。
