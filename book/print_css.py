"""印刷版（A4 单文件 HTML）的样式：纸感、版心、章起页、目录行、测验与代码。

与 style_css（屏幕版）分离：印刷的纸是白的，暖色纸底要收回成白，强调色
压深一档，表格与代码按纸面规则换行。目录行给页码留了槽位——纸上没有
页码这种东西，页码由 print_pdf.py 在 PyMuPDF 后处理里盖进去。
"""

PRINT_CSS = r"""/* ------- A4 印刷版 ------- */
@page { size: A4; margin: 17mm 16mm 16mm; }
html { font-size: 10.5pt; }
body {
  margin: 0; padding: 0; background: #fff;
  font-family: "Source Han Serif SC", "Noto Serif CJK SC", SimSun, Georgia, serif;
  line-height: 1.78; color: #26221B;
  --ink: #26221B; --muted: #6E6B60; --rule: #D8D2C0;
  --prussian: #1F4680; --sage: #2E5F42; --brick: #9C4630; --amber: #7A5B14;
  --paper-2: #F6F0E2; --code-bg: #F8F4EA; --code-line: #E3D8C1;
}
/* 封面：整页框，题名压中 */
.cover { break-after: page; min-height: 245mm; display: flex;
  flex-direction: column; justify-content: space-between;
  border: 1px solid var(--rule); padding: 18mm 14mm; }
.cover .kicker { font-size: 0.72em; letter-spacing: 0.14em;
  text-transform: uppercase; color: var(--muted); }
.cover h1 { font-size: 2.1em; line-height: 1.25; margin: 0 0 0.4em;
  color: var(--ink); font-weight: 700; }
.cover .subtitle { font-size: 1.05em; color: var(--muted); margin: 0 0 1.6em; }
.cover .meta { font-size: 0.82em; color: var(--muted); line-height: 1.7; }
.cover .rule-block { border-top: 1px solid var(--rule); padding-top: 1em; }

/* 目录：整行 flex 链接，页码槽位由 PDF 后处理盖数 */
.toc-page { break-after: page; }
.toc-page h2 { font-size: 1.3em; border-bottom: 1px solid var(--rule);
  padding-bottom: 0.35em; }
.toc-part { font-size: 0.92em; color: var(--muted); margin: 1.1em 0 0.25em;
  font-weight: 700; }
a.toc-row, a.toc-part { display: flex; justify-content: space-between;
  align-items: baseline; text-decoration: none; color: var(--ink);
  padding: 0.16em 0.1em; border-bottom: 1px dotted var(--rule); }
a.toc-part { color: var(--muted); font-weight: 700; margin-top: 0.9em;
  border-bottom: 1px solid var(--rule); }
a.toc-row .toc-label { }
a.toc-row .page-ref, a.toc-part .page-ref { /* 页码槽位：纸上不可见，PDF 后处理盖数 */ }

/* 卷分隔页 */
.part-page { break-before: page; min-height: 200mm;
  display: flex; flex-direction: column; justify-content: center; }
.part-page .part-kicker { color: var(--muted); font-size: 0.8em;
  letter-spacing: 0.12em; }
.part-page h1 { font-size: 1.8em; margin: 0.2em 0; }
.part-page .part-goal { color: var(--muted); max-width: 34em; }

/* 章 */
section.chapter { break-before: page; }
section.chapter h1 { font-size: 1.55em; line-height: 1.3; margin: 0 0 0.7em; }
section.chapter h2 { font-size: 1.18em; margin: 1.5em 0 0.55em;
  border-bottom: 1px solid var(--rule); padding-bottom: 0.25em; }
section.chapter h3 { font-size: 1.02em; margin: 1.2em 0 0.45em; }
p { margin: 0.45em 0; }
blockquote { margin: 0.8em 0; padding: 0.55em 0.9em; border-left: 3px solid var(--rule);
  background: var(--paper-2); color: #4A4234; }
blockquote p { margin: 0.25em 0; }

/* 代码：纸面换行 */
pre { background: var(--code-bg); border: 1px solid var(--code-line);
  padding: 0.55em 0.75em; font-size: 8.6pt; line-height: 1.5;
  white-space: pre-wrap; word-break: break-word; overflow: visible; }
code { font-family: Consolas, "Courier New", monospace; font-size: 0.88em;
  background: var(--code-bg); padding: 0.05em 0.22em; }
pre code { background: none; padding: 0; }

/* 表格：纸面无滚动条，表头换行按词 */
table { width: 100%; border-collapse: collapse; font-size: 8.8pt;
  margin: 0.8em 0; break-inside: auto; }
th, td { border: 1px solid var(--rule); padding: 0.3rem 0.45rem;
  text-align: left; vertical-align: top; overflow-wrap: break-word; }
th { white-space: normal; word-break: keep-all; background: var(--paper-2); }
tr { break-inside: avoid; }

/* 图与动画帧 */
figure { margin: 0.9em 0; break-inside: avoid; text-align: center; }
figure img, p img { max-width: 100%; height: auto; }
figcaption { font-size: 0.8em; color: var(--muted); margin-top: 0.35em;
  line-height: 1.5; }

/* 测验：印刷版答案直接展开（details[open] 在构建时写入） */
.quiz { border: 1px solid var(--rule); padding: 0.7em 1em; margin: 1em 0;
  break-inside: avoid; background: var(--paper-2); }
.quiz h3 { margin: 0.1em 0 0.5em; }
.quiz-options { margin: 0.3em 0 0.6em; padding-left: 1.4em; }
.quiz-answer summary { color: var(--prussian); font-weight: 700; }
.quiz-answer[open] summary { margin-bottom: 0.3em; }

/* 通用防割 */
h1, h2, h3 { break-after: avoid; }
blockquote, .quiz, figure, pre { break-inside: avoid; }
a { color: var(--ink); text-decoration: none; }

/* ------- 印刷精修（参考 yuyu_book/style_print.py）------- */
/* 单行孤行/寡行：不让第一行落单在页尾，也不让最后一行孤悬在页首 */
p { orphans: 2; widows: 2; }
/* 屏幕的 padding-bottom 在纸上变成空页陷阱：最后一行离页底只剩留白，
   下一个 break-before 又翻页——纸上的空气由 @page margin 提供 */
section.chapter { padding-bottom: 0; }
/* 全页表格跨过页眉带时 zebra 条纹在纸上洗掉：收回透明 */
tbody tr:nth-child(2n) { background: transparent; }
/* 代码高亮在纸上用暖土色调（不是屏幕上的亮蓝绿红） */
pre { color: var(--ink); }
pre .k, .k { color: #7A5B22; }
pre .s, .s { color: #4F6B3A; }
pre .m, .m { color: #8A5A2B; }
pre .c, .c1, .c2 { color: #7A6F58; }
pre .nt { color: #3A5F80; }
pre .nf { color: #7A5B14; }
pre .o, .ow { color: var(--ink); }
/* 插图高度上限：A4 版心 257mm，一张超过 200mm 的图会把正文全推到下一页
   留下空白纸。150mm 是大多数图仍然清晰可读、同时留在当前页的上限。 */
figure img, figure svg { max-height: 200mm; width: auto; }
/* 宽幅图：命名的横向页面让宽图独占一页，正文回竖版 */
@page plate-landscape { size: A4 landscape; margin: 21mm 17mm 19mm; }
figure.landscape { page: plate-landscape; break-before: page;
  display: flex; flex-direction: column; justify-content: center;
  min-height: 150mm; }
figure.landscape figcaption { margin-top: 1.2rem; }
/* 测验与附录块不拆页 */
.quiz, .quiz-answer { break-inside: avoid; }
/* 目录行不加下划线（纸上有 dotted rule 已够） */
a.toc-row, a.toc-part { text-decoration: none; }
/* 卷分隔页压缩：40/35mm 的留白加大三字标号把四项清单推成孤行 */
.part-page { padding: 26mm 0 24mm; min-height: 180mm; }
/* 屏幕上用 hover 弹出的注音，纸上静音为虚线下划线（不拆行不占额外空间） */
.gloss { border-bottom: 1px dotted var(--rule); color: inherit; }
.gloss-pop { display: none; }
/* 章末不因残余 padding 空一整页 */
section { padding-bottom: 0; }
/* 断页后避免标题孤悬 */
h1, h2, h3 { break-after: avoid; }
/* 长表头在纸上按词换行而非截断 */
th { white-space: normal; word-break: keep-all; overflow-wrap: break-word; }
table td { overflow-wrap: break-word; }
"""
