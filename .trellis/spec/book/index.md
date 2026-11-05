# book 规范索引

`mcu-book/` 是《通往单片机之路》的**整书生产层**：把 `docs/` 的章节正文、`manifest.json` 的分部/罗盘/来源、
`mcu-book/book/` 的附录与测验数据，装配成离线单文件 HTML、A4 PDF 与 16 开印前 PDF。
正文事实仍只维护在 `docs/`；这一层只维护"书稿工艺"。

| 文件 | 内容 |
|---|---|
| [build-contract.md](build-contract.md) | manifest→离线 HTML/A4 的装配合同：输入、输出、组件静态化、图片/链接、错误矩阵与测试 |
| [print-contract.md](print-contract.md) | 16 开印前 PDF：冻结、字体、两遍索引、寡行守卫、13 项产物检查与 sample/bleed 边界 |

## 适用范围

- 改 `mcu-book/build_html.py`、`build_print.py`、`check_pdf.py`、`publish_downloads.py`、`subset_fonts.py`、`print/`、`book/`、`manifest.json`。
- 改 `docs/` 下章节正文、frontmatter、测验 JSON 或图片：正文归 [docs-site](../docs-site/index.md)，本书层只负责装配后是否仍是同一本书。
- 改 `docs/public/arch/` 的架构图：制图规范归 [architecture-diagram](../docs-site/architecture-diagram.md)；本书层只关心它们是否仍是合法位图源。

## 动手前必读

- 先分清三条产物链：**离线 HTML/A4**（`build_html.py`）、**印前 PDF**（`build_print.py`）、**下载包**（`publish_downloads.py`）。
  三者不是同一条流水线，不能拿 A4 的产物去冒充印前 PDF。
- 改正文装配：读 [build-contract.md](build-contract.md) 的 manifest/罗盘/测验/附录/链接五组契约。
- 改印刷版式：读 [print-contract.md](print-contract.md) 的字体、冻结、两遍索引与 13 项检查。
- 只改正文措辞：不要动 `build_html.py` 的装配规则；用 `mcu-book/tools/prose_guard.py` 对照原文与精修稿，
  它断言代码围栏/行内代码/表格行/标题/链接目标/frontmatter 字节级一致，并单独报告口癖计数。

## 快速命令

```bash
npm run book:check                  # python build_html.py --check：临时目录装配，不写 dist
npm run book:html                   # 写 mcu-book/dist/mcu-deep-book.html
python mcu-book/build_html.py --pdf # 追加 A4 mcu-deep-book.pdf（Chromium/Playwright）
npm run book:pdf                    # build_print.py：写 16 开印前 PDF（不是 A4）
npm run book:pdfcheck               # check_pdf.py：默认校验 dist/mcu-deep-book-print.pdf
python -m unittest discover mcu-book/tests -v
```

## 金样例

- 装配主入口与契约：`mcu-book/tests/test_build.py`（manifest 覆盖、整书装配、罗盘/来源、图片缺失、容器闭合、大纲三级树）。
- 印前产物规则：`mcu-book/tests/test_check_pdf.py`（合成 PDF 夹具逐项命中）与 `test_print_vectors.py`（题图纯矢量/位图预算）。
- 冻结与大纲：`mcu-book/tests/test_print_html_freeze.py`、`test_print_outline.py`。
- 下载包：`mcu-book/tests/test_publish_downloads.py`。

## 质量检查

| 改动 | 检查 |
|---|---|
| 正文装配 / manifest / 附录 / 测验 | `npm run book:check` + `python -m unittest discover mcu-book/tests -v` |
| HTML/A4 产物 | `npm run book:html`，需要 PDF 时 `python mcu-book/build_html.py --pdf` |
| 印前版式 / 字体 / 索引 / 页眉 | `npm run book:pdf`，再 `python mcu-book/check_pdf.py <印前PDF>`；样张不能替代全书验收 |
| 下载包 | `python mcu-book/publish_downloads.py --out-dir .temp/book-downloads`，再 `--verify .temp/book-downloads` |

## 已修复的实现疑点

F01（2026-11-05 修复）：`.github/workflows/book.yml` 与 `quality.yml` 原先先跑 `build_html.py --pdf`
（A4），再跑无参数 `check_pdf.py`（默认读印前 PDF），干净 CI 必因 `mcu-deep-book-print.pdf`
不存在而红。两条 workflow 现在都在 A4 之后跑
`python mcu-book/build_print.py --html mcu-book/dist/mcu-deep-book.html`，再跑 `check_pdf.py`；
Book CI 另补 `actions/setup-node` + `npm ci`，提供 `pagedjs`。验证：PR #2 的 `book`/`checks`
全绿，本地 1174 页、13/13 通过。
