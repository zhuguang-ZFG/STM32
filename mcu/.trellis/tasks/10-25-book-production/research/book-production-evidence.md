# 研究：当前"书"的形态与做成一本书所需的前提（2026-10-25 实测）

## 1. 当前产物（实测，不是印象）

在生产产物 `mcu-book/dist/mcu-deep-book.pdf` 上直接读（PyMuPDF）：

| 事实 | 实测值 | 出处 |
|---|---|---|
| 页数 | 713 | `fitz.open(...).page_count` |
| 页面尺寸 | 594.96 × 841.92 pt = **210 × 297 mm（A4）** | `page.rect` |
| 正文用字 | **Type3（位图字形）8.2pt / 6.9pt**，页眉用 `MicrosoftYaHei` 7.5pt | `page.get_text("dict")` 的 span 统计 |
| 末页页脚 | **`713 / 712`**（分子 > 分母） | 末页文本尾部 |
| 目录 | 只有 PDF 书签树（深度分布 1 级 18 / 2 级 194 / 3 级 1677） | `get_toc()` |
| 前置/后置 | 封面、前言、分部隔页、6 附录（A 工程深读 / B 工程索引 / C 自测答案 / D 术语速查 / E 来源注册表 / F FAQ） | `manifest.json` |

**为什么是 Type3 与 7.5–8.2pt**：书稿的 CSS 是**屏幕优先**（`build_html.py` 里
`.book { width: min(100% - 2rem, 1000px); }`、`font-size: clamp(...)`、`line-height: 1.78`，
字体栈 `"Noto Sans CJK SC", "Microsoft YaHei", …`），PDF 走 Chromium 默认打印把 1000px 栏宽
压进 A4 宽度 → 字号被整体缩小；正文落到 Chromium 找不到合适 CJK 字形时的位图回退路径 → Type3。

## 2. 仓库现状：印前与电子书能力为零

全仓 grep（`epub|isbn|出血|bleed|裁切|crop mark|prepress|印刷`）只命中**参考文献里别人的 ISBN**
与 changelog 里视频封面的"裁切"。没有 EPUB 构建、没有出血/裁切标记、没有印前尺寸概念。

`manifest.json` 顶层字段：`title/subtitle/version/date/language/author/repository/license/parts/appendices/sources/chapter_guides`
—— **没有**版权页（imprint）、前言、索引（带页码）字段。

## 3. 技术选型前提（本机实测）

| 需要 | 可选方案 | 实测 |
|---|---|---|
| CSS Paged Media（分页、页眉页脚、目录页码） | `pagedjs` | npm 上 **0.4.3** 可用；跑在已装的 Chromium 里，复用现有 Playwright 链 |
| 同上（备选） | `@vivliostyle/cli` | npm 上 **11.4.0** 可用；专为书稿 PDF，若 paged.js 在 713 页上性能/保真不达标则换它 |
| 同上（不适合本项目） | WeasyPrint | Windows 需 GTK/Pango 运行时，本机 `import weasyprint` 直接 ModuleNotFoundError → 弃 |
| 可嵌入的中文衬线字体 | Noto Serif SC / Source Han Serif | 本机已有 `NotoSerifSC-VF.ttf`、`Noto Sans SC (TrueType).otf`、`Source Han Serif SC Heavy (TrueType).ttf`；许可 SIL OFL 1.1，可随书分发 |
| 字体子集化（控体积 + 保证嵌入） | `fontTools` | 已装 **4.66.1** |
| EPUB3 权威校验 | `epubcheck`（Java） | 本机 **OpenJDK 17** 在位；CI 侧 ubuntu-24.04 有 `epubcheck` 包 |

## 4. 由此得出的三条硬结论

1. **书稿工艺必须与屏幕样式分层**：现有 CSS 是给浏览器看的，不能直接当版心/字号/页眉的来源。
   要新增一份"印刷样式"（开本、版心、字号行距、章首页、页眉页脚、目录页码），屏幕版与印刷版共用正文 HTML，不共用版式。
2. **目录页码与页码自洽必须由分页引擎产出**，不能像现在这样事后用 PyMuPDF 去盖页眉页脚（盖出来的就是 `713 / 712` 那类算术错）。
   路线：CSS `target-counter()`（paged.js / vivliostyle 都支持）让目录自己带页码；页码用 `@page` 的 `counter(page)/counter(pages)`。
3. **"内容不改"必须是可验证的契约**：正文 markdown 冻结，所以新增一条对账——从新产物抽出的章节文本必须与现有单文件 HTML 的同一章文本一致（工艺改、内容不改）。

## 5. 未决（留给复核门）

- A4 屏幕版 PDF 是否退役（避免两条书路各自漂移）；若保留，由谁负责其契约。
- 出血/裁切标记：自助出版（按需印刷）通常要**精确裁切尺寸、不要出血**；胶印要 3mm 出血 + 裁切标记。
  两条都做的成本很低（同一份版式 + 一个开关），但默认产物要选一个。
- EPUB 是否内嵌字体（多数阅读器用系统字体；内嵌会显著增大体积）。
- 版权页/书号：走自助出版（ISBN 由平台给）还是只出具"自制版本页"。