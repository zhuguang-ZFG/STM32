# B47：图版三档与排印 token 化

日期：2026-11-10。基线 `7ab575b`（B46 合并，基线登记见
`b46-layout-baseline.md`）。计划见
`docs/superpowers/plans/2026-11-08-book-visual-experience.md`。

## 改动

### 图版三档（book.css @media print）

按文档既有 width 档位映射信息量，不改正文 600+ 处嵌入：

| 档 | width 值 | 分布 | print 约束 |
| --- | --- | ---: | --- |
| 小 | 330 / 640 / 660 | 111 | max-width 68%（≈122mm）、max-height 95mm |
| 中 | 720 / 760 | 821 | max-height 120mm（B46 上限不变） |
| 大 | 820 / 860 / 880 | 100 | max-width 100%（=版心 180mm）、max-height 120mm |

小档原按属性宽度渲染（640px≈169mm，近撑满版心），现压到 122mm，
两张小图可同页共存，消除「小图独撑版心」；中档行为与 B46 完全一致；
大档原来就被版心宽度约束，显式声明后语义清晰。屏幕端不动
（B46 缺陷全部是 PDF 版式）。

### 排印 token 化（tokens.json + build_html.py）

- light 新增 `--space-code-block` / `--space-code-inline`（中英混排行内代码
  气隙，原硬编码 `.12em .35em`，屏幕/打印同源）。
- print 新增 11 个 token：正文字号/行高、图注字号/行高、sub 字号、
  三档图版的宽度/高度上限；book.css print 段全部改 `var()` 引用，
  硬编码值清零（font-size/line-height/max-height/max-width）。
- `build_html.py`：新增 `_CSS_PRINT_KEYS`（print 键集合 = 15 色键 + 11 排印键），
  print 校验从 `_CSS_COLOR_KEYS` 切到 `_CSS_PRINT_KEYS`。

### 章首页/分部页

核查 `.chapter > header`、`.chapter-compass`、`.part-divider`、
print 分段规则：全部走共享选择器与同一组 token（`--type-h1`、
`--radius`、`--panel`），版心/标题层级/导读块本就统一——**核查免改**。

### B46 基线补登记

`b46-layout-baseline.md`：工具覆盖映射、CI 门阈值
（`--max-gap-pages 145 --max-large-gap-pages 15 --min-anchors 8
--max-fig-free-pages 5`）、基线数值（zh 511 页/140/10，en 541/126/12，
硬缺陷 0）。

## 前后对比（audit_pdf_layout，阈值同 CI）

| 指标 | zh 前 | zh 后 | en 前 | en 后 |
| --- | ---: | ---: | ---: | ---: |
| 总页数 | 511 | 511 | 541 | 540 |
| 留白 ≥150pt 页 | 140 | 139 | 126 | 124 |
| 其中 ≥250pt 页 | 10 | 11 | 12 | 12 |
| 孤行标题 / 图注拆页 / 溢出 / 近空白 | 0 | 0 | 0 | 0 |

zh 版式门全绿（阈值：≥150pt ≤145、≥250pt ≤15、min-anchors 8、
max-fig-free 5；实测 139 / 11 / 10 / 4）。总留白页 −1；一档从
150–249 移入 250–399（页数 511 不变）。en 门同绿（124 ≤145、12 ≤15、
min-anchors 9、max-free 4），总留白页 −2、页数 −1。B46 已注明：
中等留白的收敛靠 B48/B49 图文重排，不靠继续压图——本次不追数值。

## 验证

- build_html --check zh/en：PASS。
- PDF 重建 + audit_pdf_layout（CI 阈值）：zh 511p/139/11 全绿，
  en 540p/124/12 全绿（报告 .temp/pdf-layout-b47-{zh,en}.json）。
- 测试锁更新：CSS sha256、tokens.json/book.css 文件哈希、
  print 排印字面断言、legal() fixture print 键集合（10 处，全部等值重钉）。
- 全量 pytest：195 passed（331s）。
