# 印刷版构建

A4 竖版，正文版心 176mm，页边距 21/17/19mm。当前活动样式在
`book/print_css.py`；`book/print/book-print.css` 是旧的 185×260mm
paged.js 草稿，不参与构建，不要按它改字号。

## 生成

```bash
python book/build_print_edition.py
python book/print_pdf.py \
  --html book/dist/print/merged-book.html \
  --meta book/dist/print/merged-book.meta.json \
  --out book/dist/print/merged-book.pdf
python book/build_epub.py
```

产物写入 `book/dist/print/`，该目录被 `.gitignore` 忽略。

体检：`python book/print/pdf_audit.py book/dist/print/merged-book.pdf`。
它会核对 A4、Type3、正文字体族、页码、页眉和目录页码；插图 SVG 的系统
字体单独列为已知例外。

## 字体子集

正文用 `NotoSerifSC`，标题/表头用 `NotoSansSC`，代码用
`CascadiaMono`；woff2 以 data URI 内嵌，PDF 不依赖系统字体。页眉/页码由
PyMuPDF 后处理写入，需要 `head-regular.ttf`。

重新生成（源字体在本机 `C:\Windows\Fonts`，需要 `fonttools` 与 `brotli`）：

```bash
python book/build_fonts.py
```

脚本扫描 `docs/` 与 `book/` 的字符，实例化可变字体，写入
`book/print/fonts/*.woff2`、`head-regular.ttf` 和 `provenance.json`。
新增正文/代码字符后必须重跑，否则 PDF 会回退到系统字体。

## 三个不能删的约束

1. **表宽**：`table-layout: fixed` + `overflow-wrap: break-word`。自动布局会
   按最长 URL 的 min-content 把表格撑到 833px，Chromium 随即扩宽整本书的
   打印视口并全局缩字（10.2pt → 8.6pt）。
2. **图片段落**：`p:has(img) { text-indent: 0 }`。整段图片叠加 2em 首行缩进
   会从 665px 溢出到 692px，同样触发全局缩放。
3. **行内代码/链接**：`code, a { overflow-wrap: anywhere }`。长 API 名在
   罗盘卡里溢出 3px 也会触发缩放。

`book/tests/test_print_sections.py` 锁住这些契约。改版后若 PDF 正文突然
变小，先查有没有新的固定宽度元素把打印视口撑宽。

## SVG 插图的字体例外

`docs/public/figures/*.svg` 作为 `<img>` 嵌入，SVG 内部 `<text>` 读不到页面
的 `@font-face`，会回退到系统字体（Microsoft YaHei、Segoe UI、Consolas
等）。正文、代码、标题、页眉页码都已使用内嵌子集；只有这些插图标签保留
系统字体，换取矢量清晰度。✓/✗ 已换成 √/×，避免 Chromium 生成 Type3。
不要为了消除它去改 SVG 的 `font-family`：Chromium 对孤立 SVG 文本会改出
Type3 字体。若要彻底移除，只能把插图文字栅格化，代价是失去可搜索文本。
