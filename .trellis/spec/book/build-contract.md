# 整书装配合同（manifest → 离线 HTML / A4 PDF）

## 1. 适用范围与触发

- 改 `mcu-book/build_html.py`、`mcu-book/manifest.json`、`mcu-book/book/` 的附录、`docs/.vitepress/data/quizzes/*.json` 时读这份。
- 改 `docs/` 章节正文时也适用：装配器会拒绝缺章节、缺罗盘、缺来源、未成稿或组件残留的正文。
- 本合同的产物是**离线单文件 HTML** 与 **A4 PDF**；16 开印前 PDF 归 [print-contract.md](print-contract.md)，下载包归 §6。

## 2. 签名与产物

| 入口 | 输入 | 产物/副作用 |
|---|---|---|
| `python mcu-book/build_html.py [--out-dir DIR]` | manifest + `docs/` + `mcu-book/book/` + 测验 JSON | 写 `<out-dir>/mcu-deep-book.html`，默认 `mcu-book/dist/` |
| `python mcu-book/build_html.py --check` | 同上 | 在临时目录完整装配一遍，不写 `dist/`；失败非零退出 |
| `python mcu-book/build_html.py --pdf` | 以上 + Chromium/Playwright | 追加 `<out-dir>/mcu-deep-book.pdf`（A4）；临时文件 `.mcu-book.raw.pdf` 用后删除 |
| `npm run book:check` | `build_html.py --check` | 只读源文件；临时目录清理 |
| `npm run book:html` | `build_html.py` | 写 `mcu-book/dist/mcu-deep-book.html` |
| `python mcu-book/publish_downloads.py --out-dir DIR` | `dist/mcu-deep-book.html` + `dist/mcu-deep-book.pdf` | 产稳定名/版本名双份 + `SHA256SUMS.txt` + `book-downloads.json` + 落地页；staging 后整体替换 |

要点：

- `--out-dir` 只改变输出目录，不改变源路径；`--pdf` 依赖本机 Chrome/Edge（自动探测，`--browser` 显式指定）。
- `--check` 与正常构建走同一个 `build_html()`，区别只是目标目录是 `tempfile.TemporaryDirectory`；它验证的是装配契约，不验证 PDF。
- A4 PDF 由 Chromium 的 `page.pdf()` 打印：`prefer_css_page_size`、`outline`、`tagged`，打印前显式展开全部 `<details>`（`page.pdf()` 不触发 `beforeprint`），再盖页码、把标题大纲重排为 部(1)→章(2)→节(3)。PDF 不是印前产物。

## 3. 数据与环境契约

### 3.1 manifest

必填顶层键：`title`、`subtitle`、`version`、`date`、`language`、`author`、`repository`、`license`、`parts`、`chapter_guides`、`appendices`、`sources`。

- `parts` 非空数组；每部必须有 `id`、`title`、`goal`、`intro`、`files`；所有 `files` 必须存在于 `docs/`，且全书不得重复。
- 章数由 `sum(len(part.files))` 推导，不写死常量；新增/重命名章节必须同时改 manifest 的 `parts` 与 `chapter_guides`。
- `chapter_guides` 的键集合必须与章节文件集合完全相等；每项 `question`/`deliverable`/`boundary` 非空，`sources` 非空且全部命中 `sources` 注册表。
- `sources` 的 id 必须匹配 `[a-z0-9-]+`；每项 `title`/`authority`/`url`/`snapshot`/`accessed`/`license`/`scope` 全部非空。
- `appendices` 每项 `id` 以 `appendix-` 开头、`title` 与 `file` 非空、id/file 不重复、文件存在于 `mcu-book/book/`。

### 3.2 正文 frontmatter 与站点方言

- 每章必须有 frontmatter，且 `status` 必须是 `done`；`building` 也会被整书装配拒绝。
- `::: tip/warning/...` 容器必须成对闭合；未闭合或多余 `:::` 直接失败。
- `<AnimFigure>`、`<QuizBank>`、`<LabStatus>`、`<VideoEmbed>`、`<BaudCalc>`、`<ClockCalc>`、`<LabOverview>` 等组件必须在装配期全部静态化；任何残留标签原文报错并点名章节。
- `<QuizBank chapter="…">` 必须能在 `docs/.vitepress/data/quizzes/<chapter>.json` 找到非空题目；题目进正文，答案汇入附录 C。
- 站点方言里的交互内容（计算器、视频）替换为离线卡片，并给出站点/来源链接；不得假装离线可交互。

### 3.3 图片、链接与锚点

- 本地图片与动画（含 SVG/SMIL）全部内嵌为 `data:` URI；缺失、越出仓库或外链图片都是构建错误。
- 站内 `.md`/`.html` 链接改写为整书锚点；`#fragment` 必须能在本书的目标页找到。
- 锚点有两套 slug：VitePress 把全角标点折成 `-`，GitHub/书籍构建器直接丢标点。构建器用 `fragment_key` 去分隔符比较，**不要**在正文里写一套只对站点有效的锚点。
- 图片升级为 `<figure>` 时保留图注；题图与章节插图走 `mcu-book/print/art.py`，正文不得手写第二套 book 专属图片路径。

## 4. 校验与错误矩阵

| 输入/事件 | 结果 |
|---|---|
| manifest 缺任一必填键 | `manifest missing keys: [...]`，非零退出 |
| `parts` 为空或含重复章节 | 报错；不按"少一章也能出书"降级 |
| `docs/<file>` 不存在 | `chapter manuscript missing: docs/...` |
| `chapter_guides` 多/少章节 | `chapter guide mismatch: missing=…, extra=…` |
| 罗盘字段为空 / `sources` 未注册 | 点名章节与字段/未知来源 |
| 章节 `status` 不是 `done` | `chapter is not status=done: …` |
| `:::` 未闭合或多出闭合 | 点名源文件与容器栈 |
| `<QuizBank>` 无对应 JSON / 题目为空 | 点名章节；不允许空题卡静默通过 |
| 组件标签残留 | `unsupported component syntax remains in …` |
| 本地图片缺失 / 路径逃逸仓库 | 点名 `source:path` |
| 站内链接逃出站点 base | 点名源文件与原始路径 |
| `--pdf` 但找不到浏览器 | `browser does not exist` 或探测失败；不静默只出 HTML |
| `--check` 任一装配断言失败 | 非零退出；临时目录不写 `dist/` |

## 5. 正常、边界与失败案例

- 正常：新增一章 → 在 `docs/<section>/` 落稿并写 `status: done` → 在 manifest 的对应部 `files` 与 `chapter_guides` 各登记一次 → `npm run book:check` 通过。
- 边界：`--check` 在临时目录构建，不验证 `dist/` 里旧 HTML 是否过期；发布前仍要跑 `npm run book:html`。
- 边界：A4 与印前 PDF 是两条链；`build_html.py --pdf` 的产物不能送去 `check_pdf.py` 当印前产物。
- 失败：为了让构建通过而把 `status: building` 改成 `done`，或把缺失图片换成外链——两者都破坏"书与站点同源"的前提，必须补源文件。
- 失败：在正文写死"94 章/141 张动画"等数字。章数与工程数应从 manifest/`projects.json` 推导；正文手写数字由 `docs:check` 的 CLAIMS 对账拦截。

## 6. 下载包边界

- `publish_downloads.py` 从 `build_html` 导入 `OUTPUT_NAME`/`PDF_NAME`，当前打包的是**离线 HTML + A4 PDF**；16 开印前 PDF 不在默认下载包内。
- `--verify DIR` 用 hashlib 逐条核对既有包，不读构建器状态；`--out-dir` 与 `--verify` 二选一，都没有则用法错误。
- 版本号必须匹配 `^\d+\.\d+\.\d+$`；源产物缺失时保留旧包，不允许留下半个包。
- 下载包的权威摘要口径是 GNU `sha256sum -c`；Windows 本机用 `--verify` 自证，两者都在 CI 跑。

## 7. 测试与断言

| 文件 | 已覆盖 |
|---|---|
| `mcu-book/tests/test_build.py` | manifest 恰好覆盖全部章节、整书装配、页眉映射、缺 intro、容器闭合、缺图、缺罗盘、未知来源、附录 B 覆盖 `code/projects.json`、大纲三级树与缺章失败 |
| `mcu-book/tests/test_publish_downloads.py` | 产物齐备、`sha256sum` 行与 hashlib 一致、`--verify` 被篡改点名、缺输入保留旧包、升版不残留、缺参数用法错误 |
| `mcu-book/tests/test_print_html_freeze.py` | 印前冻结（变体选择符、table-scroll 内联变量）与 HTML 快照 |
| `mcu-book/tests/test_prose_guard.py` | 精修前后代码/表格/标题/链接/frontmatter 字节一致与口癖预算 |

未覆盖：`build_html.py --pdf` 的浏览器探测与 A4 实际页数没有单测；相关改动必须本机跑一次 `--pdf` 并记录产物路径与页数。

## 8. 错误与正确做法

- 错误：新增章节只改 `docs/`，靠构建时"自动发现"入书。正确：`manifest.json` 的 `parts.files` 与 `chapter_guides` 必须同时登记；构建器拒绝漏章。
- 错误：把站点组件原样留在整书里，期待浏览器端再渲染。正确：装配期静态化；残留即失败。
- 错误：用 `build_html.py --pdf` 的 A4 产物跑 `check_pdf.py`，看到"文件不存在/尺寸不符"就断定印前坏了。正确：先 `npm run book:pdf` 生成 `mcu-deep-book-print.pdf`，再 `book:pdfcheck`。
- 错误：正文写"94 章"当永久事实。正确：章数从 manifest 推导；站点正文的规模数字走 `progress.json` 消费链。
