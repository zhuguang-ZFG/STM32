# 印前 PDF 合同（16 开 185×260 mm）

## 1. 适用范围与触发

- 改 `mcu-book/build_print.py`、`mcu-book/check_pdf.py`、`mcu-book/print/book-print.css`、
  `mcu-book/print/index.py`、`mcu-book/print/fonts/`、`mcu-book/subset_fonts.py` 时读这份。
- 只改正文内容时：先读 [build-contract.md](build-contract.md)。印前链复用它的整书 HTML，
  正文改动应通过重新装配进入印前，而不是直接编辑 `print/mcu-deep-book-print.html`。
- 本合同只管**印刷版式与产物校验**，不改变正文事实；正文最高法仍是 `CONTRIBUTING.md` 与 `docs/`。

## 2. 签名与产物

| 入口 | 输入 | 产物/副作用 |
|---|---|---|
| `python mcu-book/build_print.py [--out-dir DIR]` | 重新装配整书 HTML（或 `--html` 复用既有 HTML） | `<out>/mcu-deep-book-print.pdf`；同时写 `<out>/print/` 的 HTML/CSS/字体副本 |
| `--sample N` | 只排前 N 章 | 原型样张；跳过术语索引与最终大纲整形，**不能当全书验收** |
| `--bleed MM` | 出血毫米数，默认 0 | 页面尺寸变为 `185+2b × 260+2b` mm，版心四边距同步加 b；CSS 替换未命中即报错 |
| `--browser PATH` | Chromium/Edge 路径 | 默认用 `build_html._browser_candidates` 的探测结果 |
| `--html PATH` | 复用既有整书 HTML | 跳过重新装配；仍执行冻结、SVG 内联与排版 |
| `--fonts-dir DIR` | 字体子集目录，默认 `mcu-book/print/fonts` | 目录不存在直接退出并提示跑 `subset_fonts.py` |
| `--no-index` / `--no-widow-guard` | 调试开关 | 分别跳过术语索引两遍法与寡行守卫；不能用于交付 |
| `python mcu-book/check_pdf.py [pdf] [--manifest PATH] [--bleed]` | 印前 PDF，默认 `mcu-book/dist/mcu-deep-book-print.pdf` | 只读产物与 manifest；13 项检查任一失败非零退出 |
| `npm run book:pdf` / `npm run book:pdfcheck` | 上述两个脚本 | 同签名；`book:pdfcheck` 默认目标就是印前 PDF |

要点：

- `build_print.py` 与 `build_html.py` 的分工是**内容装配 vs 版式**：前者直接调用 `build_html.build_html()` 取同一份 HTML，
  所以"工艺改、内容不改"是结构上成立的。
- 默认输出文件名是 `mcu-deep-book-print.pdf`；`build_html.py --pdf` 的 A4 产物是 `mcu-deep-book.pdf`，两者不可互换。
- `check_pdf.py` 只读产物与 manifest，不读构建器中间状态；它不重新分页，也不修改 PDF。

## 3. 数据与环境契约

### 3.1 版式与字体

- 开本：`@page { size: 185mm 260mm; margin: 20mm 23mm 22mm 24mm }`；闸门允许 ±0.5 mm；出血版按 `--bleed` 加边。
- 字体只允许随仓库分发的子集：`mcu-book/print/fonts/` 下的 serif/sans/mono 各 regular+bold，以及 symbols/math/emoji 单色字体，
  许可与来源记录在 `OFL.txt` / `provenance.json`；不许依赖机器已装字体（否则 CI 与本机排出的不是同一本书）。
- 粗体等宽必须有真字形；只声明 400 会让 Chromium 合成加粗，打印管线把它嵌成无名 Type3 位图。
- 缺字体目录时 `prepare_site` 直接退出，提示先跑 `mcu-book/subset_fonts.py`；字体子集按书本实际用字 + 保险集生成，参数与字符覆盖写入 `provenance.json`。

### 3.2 印前冻结（在分页前）

- 去掉变体选择符 U+FE0F：否则 emoji 走系统彩色字体并印成 Type3。
- 剥掉 `table-scroll` 内联变量：否则 paged.js 把它们当隐藏元素，标题跟随保护落空。
- 内联 SVG 图片：父文档字体进入图内文字；随后 `assert_vector_art` 只扫 `<svg>` 块，含 `feTurbulence`/`<filter>` 立即中止
  （滤镜题图会被 Chromium 整块光栅化，全书位图从个位数涨到上百）。
- 打印前展开全部 `<details>`，SMIL 动画统一 `setCurrentTime(0)` 并暂停：印刷没有视口概念，活动 SMIL 会在分页切片时产生重影字形。

### 3.3 两遍索引

1. 第一遍正常分页，逐页扫文本，记录术语命中页码；结构页（封面/版权/导读/目录/书尾/附录 D/G）整页排除。
2. 把结果渲染成附录 H「术语索引」，注入 `</main>` 前，并补目录入口；第二遍重新分页产出最终 PDF。
3. 术语来自 `docs/reference/glossary.md` 的术语列；每条最多列 6 个页码；只在术语表定义、正文零命中的词不入索引。
4. 索引页码用分页增量算出的 folio（分部隔页不占号），不能用固定偏移。

### 3.4 页眉、页码与结构页

- 前置页/结构页不编页码不盖页眉；封面无页码；分部隔页无页眉。
- 章/附录首页无页眉（first-except），后续页奇偶页眉分别为书名/章名。
- 页码格式 `N / total`；编号页分子≤分母，末个编号页必须是 `N/N`。
- 目录页码由 paged.js 的 `target-counter(attr(href), page)` 解析；目录/索引/页脚页码同源。

## 4. 校验与错误矩阵

`check_pdf.py` 的 13 项：

| 检查 | 失败条件 |
|---|---|
| 开本 | MediaBox 不是 185×260 mm（或出血 191×266 mm，±0.5） |
| 字体 | 出现 Type3，或出现不在 `SHIPPED_FAMILIES` 的系统字体 |
| 页码 | 编号页不是 `N / total`、分子>分母、末页不是 N/N |
| 结构页 | 封面/前置页/分部隔页出现页眉或页码 |
| 页眉 | 章/附录首页有页眉，或奇偶页眉不是书名/章名 |
| 目录页码 | 抽检 ≥10 章的目录页码与正文实际起始页不一致 |
| 索引页码 | 术语页码没有对应页脚，或该页找不到该术语 |
| 版面利用率 | 正文页文本行密度超过阈值（默认 22 行）或异常 |
| 墨色对比 | 代码/正文墨色过淡，实际不可读 |
| 最小字号 | 纸上字号 < 5pt |
| 纸边裁字 | 正文文本越出页边界或内白边（订口 > 20 mm） |
| 大纲与元数据 | 大纲缺结构条目、层级越级、元数据与 manifest 不符 |
| 光栅预算 | 全书位图 > 6 张照片 + `docs/public/arch/*.png` 数 + 10 张余量 |

构建期另有硬失败：

| 事件 | 结果 |
|---|---|
| 缺字体子集目录 | `缺少字体子集：…` 并退出 |
| 出血 CSS 替换未命中 | `出血版式替换未命中（CSS 已漂移，先同步这里）` |
| SVG 题图含 `feTurbulence`/`<filter>` | `印前中止：SVG 题图含 …（滤镜会光栅化），必须纯矢量` |
| 目录里找不到 `</ol></section>` 附录区 | `目录里没有附录区`，索引入口无处可挂 |
| `print_outline` 缺分部/章数不符/层级越级 | 直接退出；不产出无书签的交付物 |
| `--sample` | 跳过索引与最终大纲整形；只算样张 |

## 5. 正常、边界与失败案例

- 正常：`npm run book:pdf` → `python mcu-book/check_pdf.py mcu-book/dist/mcu-deep-book-print.pdf` → 13 项全绿，并打印体量对账（源文字数/PDF 字数/页数）。
- 边界：`--sample 2` 只用于版式预览，不能替代全书；样张的大纲不完整，构建器本身会跳过最终整形。
- 边界：`--bleed 3` 产出 191×266 mm，校验必须带 `--bleed`，否则开本项会按 185×260 判红。
- 失败：直接改 `print/mcu-deep-book-print.html` 调版式。该文件是构建产物，下次构建会被覆盖；改 `print/book-print.css` 或 `build_print.py`。
- 失败：把 A4 产物 `mcu-deep-book.pdf` 传给 `check_pdf.py`。它默认读 `mcu-deep-book-print.pdf`，尺寸/页脚/大纲全不对；这是两条链。
- 失败：为了让光栅预算变绿而调大 `_raster_budget()`。先查题图是否被滤镜栅格化；预算的真源是照片锚点 + 注册架构图数。

## 6. 测试与断言

| 文件 | 已覆盖 |
|---|---|
| `mcu-book/tests/test_check_pdf.py` | 合成 PDF 夹具的完整契约、开本、元数据、封面页码、章首页页眉、无编号页、目录/索引页码漂移、淡墨、裁字/底溢出、大纲缺条/重复栏目/来源卡、缺文件 |
| `mcu-book/tests/test_print_vectors.py` | 纯矢量 HTML 通过、滤镜题图被拒、位图预算只接受照片 |
| `mcu-book/tests/test_print_outline.py` | 部/章/节三级树、重复栏目名丢弃、缺章失败 |
| `mcu-book/tests/test_print_html_freeze.py` | 变体选择符与 table-scroll 内联变量的冻结 |
| `mcu-book/tests/test_part_art.py` | 分部图/题图的矢量与版式约束 |

未覆盖：真实 Chromium 分页的页数/页码稳定性没有单测；改版式后必须本机跑一次全书 `book:pdf` + `book:pdfcheck`，记录页数与 13 项结果。

## 7. 错误与正确做法

- 错误：把 `check_pdf.py` 当成"PDF 都叫一本书"的通用检查。正确：它默认只认印前 16 开产物；A4 走 `build_html --pdf` 自己的页脚/大纲逻辑。
- 错误：用 `--no-index` / `--no-widow-guard` 出交付物。正确：它们只用于 A/B 与调试；交付必须两遍索引 + 寡行守卫。
- 错误：题图带滤镜"更好看"。正确：印前题图必须纯矢量；滤镜会在 Chromium 打印时整块栅格化，光栅预算门会红。
- 错误：看到 `check_pdf.py` 打印"未装 PyMuPDF，跳过"就当通过。正确：跳过不是通过；装依赖后重跑，或明确记录未验证。
