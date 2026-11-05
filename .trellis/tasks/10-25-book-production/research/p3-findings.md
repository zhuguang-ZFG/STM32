# P3 前置/后置页 + 索引 + 视觉重设计（2026-10-25 实测）

产物：`.temp/book-p3-final7/mcu-deep-book-print.pdf`（1122 页，185.3×260.3 mm ✓）。

## 本轮新增

### 前置/后置页（R3/R4/R10）

- **版权与版本页**（封面后，不编页码）：书名/版本/日期/许可/作者/来源与冻结点摘要/
  构建可复现说明/书号口径。模板 `build_html.py::COPYRIGHT_HTML`，字段全部来自
  manifest 单一真源。
- **勘误与贡献页**（书末，索引前）：勘误入口（仓库 Issues）、参与入口
  （CONTRIBUTING.md / docs/reference/book.md）、贡献者名单链接。
- 两页都是 `<section class="frontmatter">`，不进附录集合——`test_build.py` 对附录
  的精确断言不动，27 项单测全绿。

### 术语索引（附录 G，两遍法）

- 词源：`docs/reference/glossary.md` 表格首列，93 个术语。
- 第一遍分页时用 paged.js 页面盒逐页扫文本收集 术语→页码；第二遍注入索引再分页
  （索引在书尾，不移动任何正文页码）。
- 别名匹配：组合词按 `/`、`vs` 拆、剥括号注（"ABI / 调用约定"→ABI；"MMIO（内存
  映射外设）"→MMIO）；纯 ASCII 别名叫词边界正则，防 "AF" 误中 "AFIO"。
- 结构页排除：封面/版权/导读/目录/书尾页/术语表/索引自身不算"出现"（实测不修则
  ABI 首次命中附录 D 续页 1080、IDF 命中目录页）。
- 90/93 入索引；漏的 3 个（Flash 存储器、期限监控、波特率误差预算）经 rg 核实
  为术语表独有词（正文零出现），不列入是对的。
- 版式：两栏、词左码右同行；屏幕样式 `dl{display:grid}` 会杀掉多栏（grid 赢），
  印刷层显式 `display:block`。

### 视觉重设计（用户要求"提升精美度，视觉冲击"）

- **封面**：满幅深青（#0a5044）出血到纸边、白字、浅色 eyebrow、统计网格（88 章 /
  58 小时 / 109 图 / 47 工程 / 65 题 / 60 来源）白字可读、版本信息收底。
- **分部隔页**：垂直居中（不再上半页空跑）、左侧色条 + PART 标签、目标与导读
  分层、统计收尾。
- **章首页**：章号（accent 色、加宽字距）+ 22pt 标题 + 通栏色条 + 元信息行。
- **目录**：点线与页码顺序修正（flex order：词 → 点线 → 页码；此前页码跑到点线
  前面）。

### 关键根因：paged.js 的 text-align-last 继承污染（全书级排版事故）

- 现象：标题、罗盘标签、分部统计、段落末行全部整行散布（"本 章 罗 盘"
  "另 —— 种 C"）。
- 机制：paged.js 给"跨页的最后元素"打 `data-align-last-split-element="justify"`
  （`text-align-last: justify`），而整章 `article` 必跨页；`text-align-last` 可继承，
  于是章内一切末行被拉散。inline 元素（章号 span）经由祖先 header 的匿名块继承。
- 修法：结构性元素（article/header/h1-h6/标签族）显式 `text-align-last: auto
  !important`；正文 p/li 不加 !important，让真正跨页的段落仍吃到 paged.js 打在
  那个元素上的属性（属性选择器特异性更高）。
- 证据链：浏览器计算样式探针（分页前 auto → 分页后 justify）→ paged.js 源码
  `handleAlignment` → !important 修复后逐页目检。

## 终态指标

| 指标 | 值 |
|---|---|
| 页数 | 1122（含版权页、勘误页、2 页索引） |
| 开本 | 185.3×260.3 mm ✓ |
| Type3 | **0** |
| 系统字体 span | **0**（⁷ 已从 Book Mono 兜底链取到字形） |
| 重复 SVG id | 0 |
| 索引 | 90 条、两栏、页码来自 paged.js 分页实况 |
| 末页页码 | 1122 / 1122 ✓ |

## 验证

- `ruff check build_print.py build_html.py print/index.py`：PASS
- `python -m unittest discover mcu-book/tests`：27 项 OK（新增前置/后置页未触碰
  任何现有断言）
- `python mcu-book/build_html.py --check`：PASS（88 章契约）
- 逐页渲染目检：封面 / 版权页 / 目录 / 分部隔页 / 章首页 / 正文带图页 / 索引页
  （`.temp/p3-visual/*.png`；分部隔页与章首页的图来自同 CSS 的 v2/v4 样本产物，
  final7 全量仅复渲了封面/版权/索引）
- `task_verify`：unverified（无配置门）

## 评审修回（第二轮，全部实测验证）

- **出血版死代码**：`prepare_site` 的出血扩边距替换的 margin 字符串早已漂移
  （CSS 现为 20/23/22/24，代码还在找 18/16/18/20）——静默不替换，出血版
  封面四角露白。改为逐条命中校验、漏配即报错；`:left/:right` 边距一并扩展。
- **封面高度塌陷**：`width/height:100%` 在分页盒里父链无确定高度，底部露白。
  改为 `@page cover { background: #0a5044 }`——页面级底色，精确版与出血版
  都自动满幅（两版产物四角像素实测均非白）。
- **目录缺索引条目**：附录 G 是印刷层注入的，`toc_html` 不知道它存在——目录
  附录区补「附录 G 术语索引」入口（`rfind("</ol></section>")` 定位，页码由
  target-counter 解析）。
- **`p>5` 魔数删除**：页码阈值在插入版权页后就错了；结构页排除已在收集侧
  完成，阈值整体移除。零命中术语现在打印到构建日志（3 个：Flash 存储器、
  期限监控、波特率误差预算——术语表独有词，正文零出现，不收是正确行为）。
- **index.py 收口**：删掉未被使用的 COLLECT_JS（收集 JS 实际内联在
  build_print.py），docstring 改为实装口径（每条最多 6 页码、结构排除），
  术语渲染加 `html.escape`；索引说明写明「仅收录正文出现过的术语」。

## 遗留（G3 复核门）

- **章首页仍带页眉**（R5 要求章首页无页眉）：CSS 分页无法表达"每组的第一页"，
  paged.js 的 `page` 属性换名会强制分页；放 P4 页眉自洽阶段处理。
- 索引排序为 Unicode 码位序（design §7 决策），拼音序若要需引入 pypinyin（新依赖）。
- 版权页"来源"行内 URL 换行处有 justify 拉伸，可接受（dd 网格窄栏）。
- P6 时把这轮抓到的三类回归固化进 check_pdf 门：①全页系统字体回退扫描
  （不只前 6 页）②标题/标签末行不得两端对齐 ③索引页码不得落在结构页。
