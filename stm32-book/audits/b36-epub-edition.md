# B36：EPUB 版本（双语）

日期：2026-11-07（Asia/Shanghai）。基线为已合并并通过双语 CI 的 `94a7159`（PR #80，B35）。

## 交付

新增 `tools/build_epub.py`：把 `build_html.py` 产出的印刷版 HTML（视频块已剥离的
变体）打包为 EPUB 3。成品为本地构建产物，与 PDF 同目录同基线：

| 文件 | spine | 图像 | 大小 | epubcheck 5.1.0 |
| --- | --- | --- | --- | --- |
| `stm32-book/dist/stm32-practical-book.epub`（zh-CN） | 49 | 546 | 91.7 MB | 0 错误 / 0 警告 |
| `stm32-book/dist/stm32-practical-book-en.epub`（en） | 49 | 546 | 91.7 MB | 0 错误 / 0 警告 |

spine 顺序与整书一致：封面 → 版权页 → 版本与修订 → 怎么读 → 目录 →
七个分部（分部页 + 各章嵌套于 nav 层级）→ 29 章 → 分部收束 → 附录 A–F →
主题索引。图书内容与 HTML 同提交同源——打包器以成品 HTML 为唯一输入，
两个版本不可能漂移。

## 实现要点

- **分节**：对 `<main class="book">` 做标签深度切片，取顶层 section/article
  （589 对标签自平衡校验）；显式拒绝不平衡输入。
- **图像**：571 个 data-URI（SVG/PNG/GIF/JPEG）按内容哈希去重后提取为
  `images/imgNNNN.*`（去重后 546 个），`src` 改为相对引用；wide-figure 的
  `<a href="图像">` 缩放链接解包（EPUB 的 `<a>` 只能指向 spine 条目）。
- **XHTML**：lxml 解析后统一迁移命名空间（全部元素 → XHTML 命名空间，
  `<svg>` 子树 → SVG 命名空间）；章头被 `<span>` 包裹的标题提升出短语容器
  （印刷 HTML 的合法写法在 XHTML schema 中不允许）；剥离 toc-jump 等屏幕交互件。
- **跨章锚点**：`#chNN-…` 一类链接按「锚点 → 所在文件」改写为
  `segNN.xhtml#anchor`，章内引用保持 `#anchor`。
- **打包**：EPUB 3（OPF + nav.xhtml）并带 EPUB 2 NCX 兼容旧阅读器；
  `mimetype` 首条目 STORED；identifier 用 `uuid5`（标题+语言派生，构建可复现）；
  含 SVG 的内容文档在 manifest 声明 `properties="svg"`。
- **自校验**：打包后内置校验（zip 结构、全部 XHTML well-formed、spine 完整、
  锚点可达），再以 W3C epubcheck 5.1.0 出具权威结论。

## 测试

- 新增 `stm32-book/tests/test_epub_build.py`（5 项）：合成迷你书走完整打包，
  断言容器规则、mimetype 位置、图像提取（无 data: 残留）、跨章锚点文件限定、
  nav 覆盖 spine。全部通过。
- 全量 `unittest discover stm32-book/tests`：189 + 5 = **194 项全部通过**。
- `tools/slop_lint.py` 对新工具与测试无命中。

## 边界与说明

- EPUB 为离线产物（dist/ 同 PDF 一样不入库）；工具与测试入库。
- 打包器不依赖 playwright/网络；`--html/--out/--lang/--title` 可单本构建。
- 屏幕版 HTML（含视频）不是输入源；印刷变体中的旁白 `<details>` 与静态图
  即 EPUB 内容，动画以首帧静态图呈现，与 PDF 口径一致。
