# B46：版式基线（补登记）

日期：2026-11-08 基线，2026-11-10 补登记。基线提交 `7ab575b`（B46 合并）。
明细见 `b46-print-figure-height.md`（同批交付的图高上限改动）；
本文档登记 B46 计划要求的基线报告与门阈值，供 B47+ 对比。

## 工具覆盖（tools/audit_pdf_layout.py）

| 计划检查项 | 实现 |
| --- | --- |
| 标题落在页底（孤行标题） | `orphan_heading`（末块大字粗体且贴底） |
| 图与图注被分页拆开 | `caption_orphan`（页首 ▲ 图注且本页无图） |
| 右边距溢出 | `margin_overflow` |
| 整页只有一张小图 / 近空白页 | `near_blank`（字符 <40 且无图）+ 每页 `figure_coverage` |
| 连续无图页 | 逐章 `max_fig_free_pages`（章节 TOC 级） |
| 页底留白 | `bottom_gap` 分档 150-249 / 250-399 / ≥400pt |
| 超过一页的长表 | CSS 层保证（`thead { display: table-header-group }`、`tr` 不拆），工具不做文本模式识别；以 B47 抽查登记代替 |

## 门阈值（.github/workflows/book.yml）

`--max-gap-pages 145 --max-large-gap-pages 15 --min-anchors 8 --max-fig-free-pages 5`（zh/en 同）。

## 基线数值（B46 提交后，两语言重建实测）

| 指标 | zh | en |
| --- | ---: | ---: |
| 总页数 | 511 | 541 |
| 页底留白 ≥150pt 页 | 140 | 126 |
| 其中 ≥250pt 页 | 10 | 12 |
| 孤行标题 / 图注拆页 / 溢出 / 近空白 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |

`>=400pt` 档含于 ≥250pt 计数内（B46 前 47/50 页，压图高后 10/12 页）。

## 备注

- 150–249pt 中等留白略增（B46 前 129→140 / 119→126），来自相邻两图放不下第二张；
  归 B48/B49 图文重排处理，不靠继续压图。
- B47 起图版按信息量分大中小三档（见 `b47-typography-tiers.md`）。
