# W2 设计：封面隔离预览与 EPUB3 两章薄切片

日期：2026-11-12
边界：本文件只交付**隔离预览**与**设计**。封面未接入 `build_html.py` / `build_print.py`；EPUB 未新增 `build_epub.py` / `check_epub.py` / npm 入口 / 测试 / CI。
依据：`11-07` PRD R2（不得静默删除 EPUB 承诺）、implement Wave 2（封面两构图×两配色隔离预览；EPUB 沿现有 HTML/manifest 真源做两章薄切片设计）。

## 1. 封面隔离预览

### 1.1 产物

目录：`.trellis/tasks/11-07-historical-spec-closure/research/w2-cover/`

| 文件 | 构图 | 配色 | 说明 |
|---|---|---|---|
| `A-light.svg` | A 字上图下 | 纸白墨绿 | 标题区在上，开发板线稿居中偏下，大量留白 |
| `A-dark.svg` | A 字上图下 | 夜墨青金 | 同上，暗底浅墨 |
| `B-light.svg` | B 图右出血 | 纸白墨绿 | 左栏标题，开发板放大后从右侧/底部出血 |
| `B-dark.svg` | B 图右出血 | 夜墨青金 | 同上 |
| `index.html` | 四宫格 | — | 本地打开即可并排比较 |
| `make.py` | 生成器 | — | 复用 `mcu-book/print/art.py` 的 `cover_art()`，只做缩放/平移/裁切 |

规格：740×1040 viewBox = 185×260 mm 比例；纯矢量、无外部素材、无生成图；文字为系统 sans（Noto Sans SC / 微软雅黑回退）；墨色通过 `--cover-ink` 注入，与现有封面同一变量名。

### 1.2 视觉口径

- 两构图共享同一套书稿身份：书名、副标题、作者、版本/日期、开发板线稿、暖色短线（`#d97706` / `#e0a35c`）。
- A 构图偏“书卷/留白”，B 构图偏“工程/版面张力”；两套配色分别对应纸书与暗色电子阅读。
- 开发板线稿来自生产 `cover_art()`，不新画一套，避免“预览与生产是两张图”。
- 星标/许可等非封面信息不进入封面。

### 1.3 已做验证

- 4 个 SVG 均通过 `xml.etree.ElementTree.parse`。
- `index.html` 在 Chromium（Playwright）1440–1600px 视口渲染，四张均正常显示；本地截图见 `.temp/w2-cover/contact.png`（临时证据，不入库）。
- 未跑生产构建；未修改 `mcu-book/print/art.py`、`build_html.py`、`build_print.py`。

### 1.4 待用户选定（本文件不替用户决定）

1. 构图 A 还是 B；
2. 纸白墨绿还是夜墨青金（也可“纸书用 A-light、电子书用 A-dark”这类组合）；
3. 书名/副标题字号与开发板占比是否再调。

选定后才进入生产接入评审：`build_html.py` 的 `.cover` 区块（约 1326 行）与 `build_print.py` 的封面页、`check_pdf.py` 的封面无页码/结构页规则都要一起过；EPUB 封面同源。

## 2. EPUB3 现状（事实）

- 当前仓库**不存在** `build_epub.py`、`check_epub.py`、`book:epub` / `book:epubcheck` 入口，也没有 EPUB 测试或 CI 步骤；历史“PDF + EPUB3”承诺中的 EPUB 侧未交付。
- 可用于薄切片的真源已经存在：
  - `mcu-book/manifest.json`：94 章 / 11 部 / 7 附录 / 75 个冻结来源；章节顺序、标题、分部、附录均在此。
  - `mcu-book/build_html.py`：产出单文件 HTML（章节 `<article class="chapter" id="chNN">`、附录 `<article class="appendix" id="appendix-*">`、内联 SVG、代码高亮、折叠答案）。
  - `mcu-book/subset_fonts.py`：已支持按用字出 WOFF2 子集，且只接受 SIL OFL 一类可分发许可，带 `provenance.json`。
- 因此薄切片必须**读构建后的 HTML + manifest**，不另写一套 Markdown 解析器；否则正文会出现第二真源。

## 3. 薄切片范围

选两章：**ch02 `c/01-memory-model.md`（C1 内存模型）** 与 **ch21 `stm32/03-gpio.md`（S3 GPIO）**。

选择理由：
- 一章宿主取证（含 `readelf`/`nm` 代码块、段归属表格），一章寄存器主线（含七个寄存器、位级图解、板级链接）；覆盖两类典型内容。
- 两章都有内部链接、代码块、标题层级、图/动画引用，足以暴露转换器的主要坑。
- 两章分属不同部（pc / ps），可验证“跨部章节选择 + 部信息”不会把 nav 弄乱。

不在薄切片内：其余 92 章、7 个附录、测验答案自动汇入、全文搜索、SMIL 动画播放、站点导航/主题切换。

## 4. 包结构（设计）

```text
mimetype                     # application/epub+zip，第一个条目，STORE 不压缩
META-INF/container.xml       # 指向 OEBPS/content.opf
OEBPS/
  content.opf                # EPUB3 package：metadata / manifest / spine
  nav.xhtml                  # EPUB3 导航（toc + landmarks）
  toc.ncx                    # 可选，仅兼容旧阅读器；不作为真源
  cover.xhtml                # 封面页（img 指向 cover.png）
  css/book.css               # 从书稿 CSS 裁剪的阅读版
  text/ch02.xhtml
  text/ch21.xhtml
  images/cover.png           # 选定封面 SVG → 1600×2250 PNG
  images/*.svg               # 章节内联 SVG 如保留为资源
  fonts/*.woff2              # 可选；subset_fonts.py 产出
  fonts/provenance.json      # 字体来源/许可/覆盖
```

## 5. 转换契约（从 HTML 到 XHTML）

| 源（build_html 产物） | 薄切片处理 |
|---|---|
| `<article class="chapter" id="chNN">` | 按 manifest 选中的两章各取一个 article；保留 `id`，输出为 `<section id="chNN">` 或 `<article>` |
| 章节 header / 本章罗盘 / 正文 | 保留；站点专用的 `book-title-marker`、`back-to-toc` 删除 |
| `<script>`（打印展开、主题等） | 全部删除；EPUB 不执行站点脚本 |
| `<details>` 折叠答案 | 保留 `<details>`；若阅读器不支持则按 CSS 展开（薄切片不依赖 JS） |
| 站内链接 `*.md` / `*.html#frag` | 只保留指向 ch02/ch21 的相对 XHTML 链接；指向切片外的链接改为绝对站点 URL 并加 `rel="external"`，或降级为纯文本（二选一，review 定） |
| 图片 `<img src>` | 复制到 `OEBPS/images/`，改写为相对路径；校验每个资源存在 |
| 内联 `<svg>`（题图/动画） | 保留内联；SMIL 动画在 EPUB 中不可靠，薄切片只保证静态首帧可读，不承诺播放 |
| 代码块 `<pre><code>` | 保留高亮 `<span>`；CSS 里给 `white-space: pre-wrap`、`overflow-wrap:anywhere` |
| 标题 `h1–h4` 与 `id` | 保留 id；重复 id 改为章前缀；nav 只取 h1/h2 |
| 脚注/引用/表格 | 保留；表格加 `border-collapse` 与窄屏可横向滚动 |
| 页面语言 | `<html xml:lang="zh-CN" lang="zh-CN">`；每页 `<title>` 用章标题 |

XHTML 约束：XML 良构（自闭合、属性引号、`&` 转义）；不使用 HTML5 专属的省略语法；`epub:type` 只用于 nav/landmarks。

## 6. OPF / nav 关键字段

- `dc:identifier`：`urn:uuid:<uuid5(NAMESPACE_URL, repository + "#" + version)>`，同一版本可复现，不随构建时间变化。
- `dc:title`：manifest `title`；副标题用 `<meta property="title-type">subtitle</meta>` 的 refinement，薄切片可先只放主标题。
- `dc:creator`：manifest `author`；`dc:language`：`zh-CN`；`dc:rights`：manifest 的 prose_and_images 许可。
- `dcterms:modified`：用 manifest `date` 的 `T00:00:00Z`（或 `SOURCE_DATE_EPOCH`），保证两次构建字节级可复现。
- `cover-image`：`cover.png` 标 `properties="cover-image"`；`nav` 标 `properties="nav"`。
- `spine`：`cover.xhtml` → `nav.xhtml`（可选 linear="no"）→ `ch02` → `ch21`。
- `nav.xhtml`：`toc` 两项（章标题），`landmarks` 含 `cover`、`toc`、`bodymatter`。

## 7. 检查器设计（`check_epub.py`，未来实现）

结构门：
1. ZIP 第一个条目必须是 `mimetype`，且 `compress_type=ZIP_STORED`，内容精确等于 `application/epub+zip`；
2. `META-INF/container.xml` 存在且指向的 OPF 存在；
3. OPF 可解析，`manifest` 中每个 `href` 在包内存在（含 CSS/图片/字体），`spine` 的 `idref` 都能在 manifest 找到；
4. `nav.xhtml` 存在且 `properties="nav"`，toc 链接都能解析到包内文件 + 片段；
5. 无远程资源引用（`http(s)://` 只允许显式站点链接，且不得出现在 `img`/`link`/`script` 资源位）。

内容门：
6. **章级同一性**：对 ch02/ch21，分别从源 HTML 的 `<article>` 与 EPUB 的 XHTML 提取可见文本，归一化空白后要求逐字相等（允许的差异只有站点 chrome 与链接 URL 文本）；这是“不另解析正文”的硬证据。
7. 章节 id 集合与 manifest 选择集完全相等；不得多章、少章、串章。
8. 代码块数量与源 article 一致；图片/内联 SVG 数量一致；所有图片资源存在。
9. 封面存在且尺寸/比例符合 185:260；`cover.xhtml` 引用它。

反向夹具（未来 `test_check_epub.py`）：
- 删 `mimetype` / 改成压缩 / 内容错；
- OPF 缺 nav / spine 指向不存在的 id；
- 少一章 / 多一章 / 章文本改一个字；
- 图片资源缺失；
- 远程图片 URL；
- 封面缺失或比例错误。

`epubcheck`：作为外部权威门，CI 里用固定版本（Java + epubcheck jar）单独跑；版本与调用方式属于新增 CI，需单独 review，不在本轮接。

## 8. 构建器设计（`build_epub.py`，未来实现）

接口（建议）：

```bash
python mcu-book/build_epub.py \
  --html mcu-book/dist/mcu-deep-book.html \
  --manifest mcu-book/manifest.json \
  --chapters c/01-memory-model.md stm32/03-gpio.md \
  --cover .trellis/.../w2-cover/A-light.svg \
  --out mcu-book/dist/epub-slice/
```

实现要点：
- 只用标准库（`zipfile`、`html.parser`、`xml.etree`）读取已构建 HTML；不重新解析 Markdown，不复制 `build_html.py` 的渲染规则。
- 章号由 manifest 顺序计算（薄切片实测：ch02 / ch21），不硬编码。
- 封面 SVG 用 Chromium（现有 Playwright 依赖）渲染为 1600×2250 PNG；或先由 `build_print.py` 的封面页导出，保证与纸书同源。
- 字体：优先复用 `subset_fonts.py`；当前 `--chars-from-sample N` 只支持“前 N 章”，薄切片选的是 ch02/ch21，需要给该工具加“按 manifest 章选择取字”的参数（属于工具改动，未来单独 review）。
- ZIP 时间戳固定（`SOURCE_DATE_EPOCH`），保证 `sha256` 可复现。
- 输出不直接替换站点下载包；先落 `dist/epub-slice/`，检查通过后再谈接入 `publish_downloads.py`。

## 9. 风险与开放问题

1. **EPUB 阅读器差异**：内联 SVG、`<details>`、CSS 变量、暗色模式在不同阅读器表现不一；薄切片只承诺“正文可读、结构正确”，不承诺像素级一致。
2. **动画**：SMIL 在 EPUB 中不可靠；薄切片用静态首帧，若未来要动效需另做视频/GIF 方案。
3. **字体**：全量 CJK 子集体积大；薄切片按两章用字出子集，需确认 `subset_fonts.py` 的许可白名单覆盖所选字体。
4. **跨章链接**：切片外链接策略（绝对站点 URL vs 纯文本）需 review 定；这会影响“离线可读”的承诺边界。
5. **确定性**：ZIP 时间戳、UUID、`dcterms:modified` 三处必须固定，否则两次构建 sha 不同。
6. **新增测试/CI**：`test_build_epub.py`、`test_check_epub.py`、`book:epub`、`book:epubcheck`、`mcu-book.yml` 新步骤都属测试/CI 变更，按任务约束单独 review，不与本轮设计混在一起。

## 10. 本轮证据与未做事项

已做：
- `research/w2-cover/{A,B}-{light,dark}.svg` + `index.html` + `make.py`；XML 解析通过；Chromium 截图核对（`.temp/w2-cover/contact.png`）。
- manifest 精确读取：94 章 / 11 部 / 7 附录；ch02、ch21 定位；`subset_fonts.py` 能力与限制确认。

未做（有意）：
- 未修改任何生产文件（`build_html.py`、`build_print.py`、`art.py`、`package.json`、workflows、测试）。
- 未生成 EPUB 包、未新增构建器/检查器/测试/CI。
- 未做封面用户选择；未接入封面到生产。

## 11. 复核时请拍板

1. 封面：A/B × 纸白/夜墨（或组合）。
2. EPUB 切片外链接：绝对站点 URL 还是纯文本。
3. 是否同意在下一回合实现 `build_epub.py` + `check_epub.py` 薄切片（连同新测试/CI 单独 review）。
