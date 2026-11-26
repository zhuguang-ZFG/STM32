"""印刷版（A4 单文件 HTML）的样式：纸感、版心、章起页、目录、测验与代码。

与 style_css（屏幕版）分离：印刷的纸是白的，暖色纸底要收回成白，强调色
压深一档，表格与代码按纸面规则换行。目录行给页码留了槽位——纸上没有
页码这种东西，页码由 print_pdf.py 在 PyMuPDF 后处理里盖进去。

字体不依赖本机安装：`book/print/fonts/*.woff2` 是随仓库分发的 Noto /
Cascadia / 符号子集，构建时以 data URI 内联。这样本机与 CI 排出来的是
同一本书，也避免 Chromium 把系统字体嵌成 Type3 位图。
"""

from __future__ import annotations

import base64
from functools import lru_cache
from pathlib import Path

FONT_DIR = Path(__file__).resolve().parent / "print" / "fonts"

# 字体族名与 pdf_audit.py 的 SHIPPED_FAMILIES 对齐；alias 决定 PDF 里的族名。
FONT_FACES = (
    ("NotoSerifSC", 400, "serif-regular.woff2"),
    ("NotoSerifSC", 700, "serif-bold.woff2"),
    ("NotoSansSC", 400, "sans-regular.woff2"),
    ("NotoSansSC", 700, "sans-bold.woff2"),
    ("CascadiaMono", 400, "mono-regular.woff2"),
    ("CascadiaMono", 700, "mono-bold.woff2"),
    ("NotoSansSymbols2", 400, "symbols-regular.woff2"),
    ("NotoSansMath", 400, "math-regular.woff2"),
    ("NotoEmoji", 400, "emoji-regular.woff2"),
)


@lru_cache(maxsize=1)
def font_face_css() -> str:
    """把随书字体内联成 @font-face；缺文件直接报错，不静默回退系统字体。"""
    blocks = []
    for family, weight, name in FONT_FACES:
        path = FONT_DIR / name
        if not path.is_file():
            raise FileNotFoundError(
                f"print font missing: {path} — run book/build_fonts.py first")
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
        blocks.append(
            "@font-face{"
            f'font-family:"{family}";'
            f"font-weight:{weight};font-style:normal;font-display:block;"
            f'src:url(data:font/woff2;base64,{payload}) format("woff2")'
            "}")
    return "\n".join(blocks)


PRINT_CSS = r"""/* ------- A4 印刷版 ------- */
@page { size: A4; margin: 21mm 17mm 19mm; }
html { font-size: 10.2pt; }
body {
  margin: 0; padding: 0; background: #fff;
  font-family: "NotoSerifSC", "NotoSansSymbols2", "NotoSansMath",
               "NotoEmoji", "Songti SC", serif;
  line-height: 1.74; color: #26221B;
  text-align: justify; text-justify: inter-ideograph;
  line-break: strict;
  font-synthesis: none;
  --ink: #26221B; --muted: #675F4F; --rule: #E3D8C1;
  --paper: #FBF7EF; --paper-2: #F3EAD8; --paper-3: #EADFC7;
  --bronze: #43392B; --bronze-2: #8A7D68; --bronze-3: #5A5040;
  --cinnabar: #9C4630; --jade: #4E6E5D; --sky: #4C7093;
  --prussian: #1F4680; --sage: #2E5F42; --brick: #9C4630; --amber: #7A5B14;
  --code-bg: #F8F4EA; --code-line: #E3D8C1;
}
/* 版心：A4 210mm - 17mm×2 = 176mm。固定宽度是印刷 1:1 的关键：
   不设时 Chromium 按 1280px 视口排版，再把整页压进 A4，10.2pt 正文
   会缩成 8.6pt（旧产物就是这个毛病）。 */
.book { width: 176mm; max-width: 176mm; margin: 0; padding: 0; }
/* 封面：纸色内框，题名压中。封面在版心内，不单独做 named page。 */
.cover { break-after: page; box-sizing: border-box;
  min-height: 255mm; padding: 12mm 12mm; background: var(--paper);
  display: flex; align-items: stretch; }
.cover-inner { position: relative; flex: 1; display: flex;
  flex-direction: column; align-items: center; justify-content: space-between;
  text-align: center; box-sizing: border-box; padding: 18mm 14mm 14mm;
  background: linear-gradient(180deg, #FFFDF8, var(--paper));
  box-shadow: inset 0 0 0 1px #D2C4A6, inset 0 0 0 5px #FFFDF8,
              inset 0 0 0 5.5px var(--bronze-2), inset 0 0 0 6.5px #FFFDF8; }
.cover-inner::before { content: ""; position: absolute; top: 0; bottom: 0;
  left: 0; width: 5px;
  background: linear-gradient(180deg, var(--cinnabar), var(--bronze-2)); }
.cover-seal { position: absolute; top: 14mm; right: 14mm;
  display: flex; align-items: center; justify-content: center;
  writing-mode: vertical-rl; padding: .45rem .35rem;
  background: var(--cinnabar); color: var(--paper);
  font-family: "NotoSerifSC", serif; font-size: 1.05rem; line-height: 1.15;
  letter-spacing: .08em; transform: rotate(1.8deg);
  box-shadow: inset 0 0 0 2px rgba(251,247,239,.55); }
.cover-kicker, .cover .kicker { font-family: "NotoSansSC", sans-serif;
  font-size: .7rem; letter-spacing: .38em; text-transform: uppercase;
  color: var(--bronze-2); margin: 0; }
.book-title { margin: 8mm 0 0; line-height: 1.12; }
.bt-main { display: block; font-family: "NotoSerifSC", serif;
  font-size: 40pt; font-weight: 700; letter-spacing: .12em;
  text-indent: .12em; color: var(--ink); }
.bt-tail { display: block; font-family: "NotoSansSC", sans-serif;
  font-size: 12pt; font-weight: 400; letter-spacing: .18em;
  text-indent: .18em; color: var(--muted); margin-top: 5mm; }
.cover-rule { display: flex; align-items: center; justify-content: center;
  gap: 1rem; width: 72%; margin: 9mm auto 0; color: var(--bronze-2); }
.cover-rule i { flex: 1; height: 1px;
  background: linear-gradient(90deg, transparent, var(--bronze-2), transparent); }
.cover-mark { font-family: "NotoSansSC", sans-serif; font-size: .68rem;
  letter-spacing: .3em; text-indent: .3em; }
.book-sub { font-family: "NotoSansSC", sans-serif; font-size: 10pt;
  color: var(--muted); letter-spacing: .08em; margin: 8mm 0 0; }
.cover-foot { width: 100%; display: flex; justify-content: space-between;
  align-items: baseline; border-top: 1px solid var(--rule);
  padding-top: 4mm; font-family: "NotoSansSC", sans-serif;
  font-size: 8pt; letter-spacing: .08em; color: var(--muted); }
/* 兼容旧封面标记；新封面只保留 title/subtitle/meta 三类信息。 */
.cover .subtitle { font-size: 1.05em; color: var(--muted); margin: 0 0 1.6em; }
.cover .meta { font-size: .82em; color: var(--muted); line-height: 1.7; }
.cover .rule-block { border-top: 1px solid var(--rule); padding-top: 1em; }

/* 目录：整行 flex 链接，页码槽位由 PDF 后处理盖数 */
.toc-page { break-after: page; }
.toc-page h2 { font-family: "NotoSansSC", sans-serif; font-size: 1.6em;
  letter-spacing: .08em; border-bottom: 2px solid var(--bronze-2);
  padding-bottom: .28em; margin: 0 0 .8em; }
.toc-part { font-size: .84em; color: var(--muted); margin: 1.05em 0 .2em;
  font-weight: 700; }
a.toc-row, a.toc-part { display: flex; justify-content: space-between;
  align-items: baseline; text-decoration: none; color: var(--ink);
  padding: .2em .1em; border-bottom: 1px dotted var(--rule); }
a.toc-row { font-size: .92em; }
a.toc-part { color: var(--muted); font-weight: 700; margin-top: .9em;
  border-bottom: 1px solid var(--rule); }
a.toc-row .page-ref, a.toc-part .page-ref { /* 页码槽位：纸上不可见 */ }

/* 卷分隔页：大号卷号做淡水印，标题与卷目标压在中间 */
.part-page { break-before: page; min-height: 257mm; box-sizing: border-box;
  display: flex; flex-direction: column; justify-content: center;
  padding: 0; }
.part-page .part-kicker { font-family: "NotoSansSC", sans-serif;
  font-size: 6.5em; line-height: .9; letter-spacing: .02em;
  color: var(--paper-3); margin: 0 0 4mm; }
.part-page h1 { font-family: "NotoSerifSC", serif; font-size: 2.4em;
  line-height: 1.2; margin: 0 0 .35em; }
.part-page .part-goal { color: var(--muted); max-width: 30em;
  font-size: 1.05em; line-height: 1.8; margin: 0; }

/* 章 */
section.chapter { break-before: page; position: relative; }
.chapter-no { font-family: "NotoSansSC", sans-serif; font-size: 3.2em;
  line-height: 1; letter-spacing: .02em; color: var(--paper-3);
  margin: 0 0 2mm; }
section.chapter h1 { font-family: "NotoSerifSC", serif; font-size: 2em;
  line-height: 1.3; margin: 0 0 .45em; color: var(--ink); }
section.chapter h2 { font-family: "NotoSansSC", sans-serif; font-size: 1.35em;
  margin: 1.7em 0 .55em; border-bottom: 1px solid var(--rule);
  padding-bottom: .22em; color: var(--bronze-3); }
section.chapter h3 { font-family: "NotoSansSC", sans-serif; font-size: 1.08em;
  margin: 1.2em 0 .4em; color: var(--ink); }
h1, h2, h3, h4 { text-align: left; }
/* 章首题记：与正文同字体，朱砂竖线，不抢标题 */
section.chapter > h1 + blockquote { margin: 0 0 1.5em; padding: 0 0 0 1.1em;
  border-left: 3px solid var(--cinnabar); background: none;
  color: #4A4234; font-size: 1.06em; line-height: 1.8; }
/* 本章罗盘：四项做成 2×2 纸卡，章首不再是四条裸列表 */
section.chapter > h2#本章罗盘 { border-bottom: 0; font-size: 1.02em;
  letter-spacing: .12em; color: var(--bronze-2); margin: 1.4em 0 .5em; }
section.chapter > h2#本章罗盘 + ul { list-style: none; display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .45rem;
  margin: 0 0 1.6rem; padding: 0; }
section.chapter > h2#本章罗盘 + ul > li { background: var(--paper-2);
  border: 1px solid var(--rule); border-left: 3px solid var(--cinnabar);
  padding: .5rem .65rem; font-size: .86em; line-height: 1.62;
  break-inside: avoid; }
section.chapter > h2#本章罗盘 + ul > li > strong {
  display: block; font-family: "NotoSansSC", sans-serif; font-size: .78em;
  letter-spacing: .16em; color: var(--cinnabar); margin-bottom: .2em; }
p { margin: .35em 0; text-indent: 2em; orphans: 2; widows: 2; }
/* 图片独占段落不要首行缩进：665px 版心 + 2em 缩进会把图片推到 692px，
   Chromium 会把整本书的打印视口撑到 692px 再整体缩到 0.955 倍。 */
p:has(img) { text-indent: 0; }
section.chapter > blockquote p, li p, figcaption, .quiz p,
.cover p, .part-page p, .toc-page p { text-indent: 0; }
p[align="center"] + p { text-indent: 0; }
blockquote { margin: .8em 0; padding: .55em .9em;
  border-left: 3px solid var(--rule); background: var(--paper-2);
  color: #4A4234; }
blockquote p { margin: .25em 0; }

/* 代码：纸面换行；等宽字体也是随书子集 */
pre { background: var(--code-bg); border: 1px solid var(--code-line);
  padding: .55em .75em; font-family: "CascadiaMono", "NotoSansSC", "NotoSansSymbols2", "NotoSansMath", monospace;
  font-size: 8.6pt; line-height: 1.55; white-space: pre-wrap;
  word-break: break-word; overflow: visible; text-align: left;
  color: var(--ink);
  /* 高代码块（如 queue.c 90 行）允许跨页续排，避免整块推新页留下
     半页空板；orphan/widow 保证断口至少各留 3 行。 */
  break-inside: auto; orphans: 3; widows: 3; }
code { font-family: "CascadiaMono", "NotoSansSC", "NotoSansSymbols2", "NotoSansMath", monospace; font-size: .88em;
  background: var(--code-bg); padding: .05em .22em; }
/* 行内代码/链接可按字符换行：长 API 名（如 SCB_InvalidateDCache_by_Addr）
   若不许断，会从 2×2 罗盘卡里溢出 3px，触发整本书 0.995x 缩放。 */
code, a { overflow-wrap: anywhere; }
pre code { background: none; padding: 0; }

/* 表格：固定布局把列宽锁在 176mm 版心内。auto 布局会按最长 URL 的
   min-content 把表撑到 833px；Chromium 随即扩宽整本书的打印视口并
   全局缩字（10.2pt → 8.6pt）。 */
table { width: 100%; table-layout: fixed; border-collapse: collapse;
  font-size: 8.6pt; margin: .8em 0; break-inside: auto; }
thead { display: table-header-group; }
th, td { border: 1px solid var(--rule); padding: .3rem .45rem;
  text-align: left; vertical-align: top;
  overflow-wrap: break-word; word-break: normal;
  /* 数据表满列的地址/数值按等宽数字排（craft-floor：built 而非
     assembled 的最便宜信号）；Noto CJK 自带 tnum 特性。 */
  font-variant-numeric: tabular-nums; }
th { font-family: "NotoSansSC", sans-serif; white-space: normal;
  background: var(--paper-2); }
tr { break-inside: avoid; }

/* 图与动画帧 */
figure { margin: .9em 0; break-inside: avoid; text-align: center; }
figure.book-figure { margin: 1.15em 0; }
/* Markdown also permits images directly in list items and links. */
img { max-width: 100%; height: auto; }
figure.book-figure figcaption { max-width: 150mm; margin: .45em auto 0; }
figcaption { font-family: "NotoSansSC", sans-serif; font-size: .8em;
  color: var(--muted); margin-top: .35em; line-height: 1.5; }

/* 测验：印刷版答案直接展开（details[open] 在构建时写入）。
   整个测验盒允许跨页（此前 break-inside: avoid 让整盒不可拆，
   自测节被整体推到新页，最多留下 678pt 空板）；每道题的
   Q+答案仍然原子（.quiz-answer avoid），边框按 box-decoration
   slice 在断口处断开、左右边线连续。 */
.quiz { border: 1px solid var(--rule); padding: .7em 1em; margin: 1em 0;
  break-inside: auto; background: var(--paper-2); }
.quiz h3 { margin: .1em 0 .5em; break-after: avoid; }
.quiz-options { margin: .3em 0 .6em; padding-left: 1.4em; }
.quiz-answer summary { color: var(--prussian); font-weight: 700; }
.quiz-answer[open] summary { margin-bottom: .3em; }

/* 通用防割。pre 不在列：它自身规则里已放开跨页（orphans/widows 3 行
   兜底），长代码块整块 avoid 会把自测节前的半页空成白板。 */
h1, h2, h3 { break-after: avoid; }
blockquote, figure { break-inside: avoid; }
a { color: var(--ink); text-decoration: none; }

/* ------- 印刷精修（参考 yuyu_book/style_print.py）------- */
/* 单行孤行/寡行：不让第一行落单在页尾，也不让最后一行孤悬在页首 */
/* 屏幕的 padding-bottom 在纸上变成空页陷阱：最后一行离页底只剩留白，
   下一个 break-before 又翻页——纸上的空气由 @page margin 提供 */
section.chapter { padding-bottom: 0; }
/* 全页表格跨过页眉带时 zebra 条纹在纸上洗掉：收回透明 */
tbody tr:nth-child(2n) { background: transparent; }
/* 代码高亮在纸上用暖土色调（不是屏幕上的亮蓝绿红） */
pre .k, .k { color: #7A5B22; }
pre .s, .s { color: #4F6B3A; }
pre .m, .m { color: #8A5A2B; }
pre .c, .c1, .c2 { color: #7A6F58; }
pre .nt { color: #3A5F80; }
pre .nf { color: #7A5B14; }
pre .o, .ow { color: var(--ink); }
/* 插图高度上限：A4 版心 257mm，一张超过 150mm 的图会把正文全推到下一页
   留下空白纸。150mm 是大多数图仍然清晰可读、同时留在当前页的上限。 */
figure img, figure svg { max-height: 150mm; max-width: 100%; width: auto; }
figure.book-figure.fig-s img,
figure.book-figure.fig-s svg {
  max-height: 72mm;
  max-width: 100%;
  width: auto;
}
figure.book-figure.fig-m img,
figure.book-figure.fig-m svg {
  max-height: 150mm;
  max-width: 100%;
  width: auto;
}
figure.book-figure.fig-l.landscape {
  max-height: 170mm;
  overflow: hidden;
}
figure.book-figure.fig-l.landscape img,
figure.book-figure.fig-l.landscape svg {
  max-height: 150mm;
  max-width: 100%;
  width: auto;
}
/* 宽幅图：命名的横向页面让宽图独占一页，正文回竖版 */
@page plate-landscape { size: A4 landscape; margin: 21mm 17mm 19mm; }
figure.landscape { page: plate-landscape; break-before: page;
  display: flex; flex-direction: column; justify-content: center;
  min-height: 150mm; }
figure.landscape figcaption { margin-top: 1.2rem; }
/* 每道测验题不拆页；测验盒本身可跨页（见上）。
   跨页断口用 clone：每个分片自带完整边框与内边距（默认 slice 会让
   断口处文字贴边、只见左右边线）；不支持的阅读器回落 slice。 */
.quiz, pre { box-decoration-break: clone; -webkit-box-decoration-break: clone; }
.quiz-answer { break-inside: avoid; }
/* 目录行不加下划线（纸上有 dotted rule 已够） */
a.toc-row, a.toc-part { text-decoration: none; }
/* 卷分隔页留白由 flex 居中提供，不再叠加 padding 推高内容 */
/* 屏幕上用 hover 弹出的注音，纸上静音为虚线下划线（不拆行不占额外空间） */
.gloss { border-bottom: 1px dotted var(--rule); color: inherit; }
.gloss-pop { display: none; }
/* 章末不因残余 padding 空一整页 */
section { padding-bottom: 0; }
/* 断页后避免标题孤悬 */
h1, h2, h3 { break-after: avoid; }
/* 长表头/长 URL 在纸上按字符换行，不撑破固定列宽 */
th { white-space: normal; word-break: normal; overflow-wrap: break-word; }
table td { overflow-wrap: break-word; word-break: normal; }
"""


def build_css() -> str:
    """完整印刷样式：随书字体 + 版式。"""
    return font_face_css() + "\n" + PRINT_CSS
