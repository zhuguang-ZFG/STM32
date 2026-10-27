"""印前 PDF 构建器：把整书 HTML 重排成 16 开（185×260 mm）的印刷版。


与 `build_html.py` 的分工：那个负责**内容装配**（章节、罗盘、测验、附录、目录、单文件 HTML）；
这个负责**版式**（开本、版心、字体、分页、页眉页脚、目录页码）。内容一律复用前者的产物，
所以"工艺改、内容不改"是结构上成立的，不需要另一套正文处理。

分页用 paged.js（钉在 devDependencies）跑在已经装好的 Chromium 里：
  · `@page` 的尺寸/版心/页眉页脚由 `print/book-print.css` 声明；
  · 目录页码由 `target-counter(attr(href), page)` 解析成真实页码；
  · 打印时把 Chromium 的页面盒子设成与开本一致、边距归零 —— paged.js 已经把内容
    切成"每页一个盒子"，Chromium 再套一层页边距就会双重缩排、页数也会变。

用法：
  python mcu-book/build_print.py --out-dir mcu-book/dist            # 全量
  python mcu-book/build_print.py --sample 2 --out-dir .temp/print    # 原型：前 2 章
  python mcu-book/build_print.py --bleed 3 --out-dir mcu-book/dist   # 胶印出血版
"""

from __future__ import annotations

import argparse
import base64
import collections
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

# Windows 控制台默认 GBK：模块导入即切 UTF-8，避免子进程/提前打印把 ✓ 炸成
# UnicodeEncodeError（三次踩坑后钉死在导入期）。StringIO 场景无 reconfigure，跳过。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

BOOK_DIR = Path(__file__).resolve().parent
REPO_ROOT = BOOK_DIR.parent
sys.path.insert(0, str(BOOK_DIR))

import build_html  # noqa: E402  —— 与 build_html.py 自身的调用约定一致（脚本方式运行）

PRINT_DIR = BOOK_DIR / "print"
PRINT_CSS = PRINT_DIR / "book-print.css"
FONTS_DIR = PRINT_DIR / "fonts"
PAGED_LIB = REPO_ROOT / "node_modules" / "pagedjs" / "dist" / "paged.js"

# 寡行守卫：paged.js 0.4.3 声明了 CSS widows/orphans 但 chunker 的断点决策
# 从不读它们（needsBreak 只有 break-before/after），属性等于没写。这里在
# onBreakToken 钩子里补上：断点之后整块只剩一行（下一页首行就是段尾
# 孤行）时，把断点回移到本页最后一行的行首，让下一页以两行起排。
#
# v3.2 统一版要点（对应 dist/paged.js 源码语义）：
# - 断点渲染位置统一取 (overflow.startContainer, startOffset)：文本断点
#   即克隆文本节点内偏移；元素断点（断在内联元素前）startContainer 是
#   父元素、startOffset 是子节点序号，Range 语义同样成立。
# - 行数判据纯计数（与坐标系无关，绝对 top 不可比——预览布局会把 rect
#   排到页盒外、文档序倒挂）：clean 断点 ⟺ before == total-1；行内断点
#   ⟺ before == total。Chromium 怪癖：range 跨内联元素边界（<strong>/
#   <a>/<code>）时 getClientRects 重复返回同一片段的 rect 且枚举序来回
#   跳行，簇计数把跳变当新行（复现：2 行段数出 4 簇，3 行段 5 簇）——
#   rectsOf 收集口按 (top,bottom,x,w) 去重即恢复视觉序。簇再按
#   rect.bottom（基线）聚：同行混排字体基线差 <1px，阈值 4px 对行距
#   ~16.5px 有 4 倍余量。
# - 克隆是源块的全文（首现）或后缀（续页）：块级 textContent 比对得
#   cloneStart，克隆内前缀字符数 + cloneStart 即源内偏移，按字符计数
#   走源块文本节点定位，无需 data-ref 逐节点映射。
# - removeOverflow 只吃 overflow range（extractContents），不吃 token——
#   回移必须同步 overflow.setStart，否则被移文本两页各渲染一遍（v1 实证
#   p114→p115 重复 36 字）。
# - equals() 只在两个 offset 均真值时才比较，offset 0 是 falsy——回移目标
#   若等于续段克隆起点（= 上一页断点位置），equals 挡板会跳过
#   removeOverflow 反而造成可见重复，此时放弃该寡行（skip "collide"）。
# - 本页块恰两行且为首现（目标即块首）时整块下移：token 落 (srcBlock,
#   0)、overflow 起点移到块前——治目录导语这类两行段。若块前紧邻 H1–H4，
#   标题随块一起下移（token 落 (srcPrev, 0)），否则标题被孤零零留在页底
#   （样张实证 p4/p5 末）；源/克隆两侧 tagName+data-ref 对不上则弃
#   （skip "orphan-head"）。
WIDOW_GUARD_JS = r"""
class WidowGuard extends window.Paged.Handler {
  constructor(chunker, polisher, caller) {
    super(chunker, polisher, caller);
    this.checked = 0;
    this.moved = 0;
  }
  onBreakToken(breakToken, overflow, rendered) {
    try {
      let rec = null;
      const skip = (why) => {
        const s = (window.__widowSkip = window.__widowSkip || {});
        s[why] = (s[why] || 0) + 1;
        if (rec) {
          rec.why = why;
          (window.__widowTrace = window.__widowTrace || []).push(rec);
        }
      };
      if (!breakToken || !overflow || !breakToken.node) return;
      const INLINE = { STRONG:1, EM:1, B:1, I:1, SPAN:1, A:1, CODE:1, SUP:1,
                       SUB:1, SMALL:1, MARK:1, ABBR:1, U:1, S:1, DEL:1, INS:1 };
      const climb = (el) => {
        let b = el, hops = 0;
        while (b && b.nodeType === 1 && INLINE[b.tagName] && hops++ < 8) {
          b = b.parentElement;
        }
        return (b && b.nodeType === 1) ? b : null;
      };
      // 源块：token 节点可能是文本节点，也可能是内联元素（元素断点）
      const srcNode = breakToken.node;
      rec = { tag: "", tail: String(srcNode.textContent || "").slice(-24),
              after: -1, total: -1, before: -1 };
      const srcBlock = climb(srcNode.nodeType === 3 ? srcNode.parentElement : srcNode);
      if (!srcBlock) { skip("no-src-block"); return; }
      const tag = srcBlock.tagName;
      rec.tag = tag;
      if (tag !== "P" && tag !== "LI") { skip("not-pli"); return; }
      // 渲染断点位置及其所在块
      const sc = overflow.startContainer, so = overflow.startOffset;
      if (!sc) { skip("no-overflow"); return; }
      let rNode;
      if (sc.nodeType === 3) rNode = sc.parentElement;
      else rNode = sc.childNodes[so] || sc;
      const blockClone = climb(rNode);
      if (!blockClone) { skip("no-clone-block"); return; }
      if (blockClone.tagName !== tag) { skip("clone-drift"); return; }
      // 克隆必须是源块全文（首现）或后缀（续页）
      const srcText = srcBlock.textContent;
      const cloneText = blockClone.textContent;
      if (!srcText || !cloneText || cloneText.length > srcText.length) { skip("len"); return; }
      let cloneStart = 0;
      if (cloneText !== srcText) {
        if (!srcText.endsWith(cloneText)) { skip("suffix"); return; }
        cloneStart = srcText.length - cloneText.length;
      }
      const doc = sc.ownerDocument;
      const range = doc.createRange();
      const rectsOf = (sn, so_, en, eo) => {
        try {
          range.setStart(sn, so_);
          range.setEnd(en, eo);
        } catch (e) { return []; }
        // Chromium 怪癖：range 跨内联元素边界（<strong>/<a>/<code>）时 getClientRects
        // 会把同一片段的 rect 重复返回，枚举序来回跳行——文档序无排序的行簇计数
        // 把每次跳变都当成新行（独立复现实证：2 行段 9 rect、序列 [12,12,33,12,33,…]，
        // 数出 4 簇；去重后 6 rect 单调，2 簇）。按 (top,bottom,x,w) 去重即恢复视觉序。
        const seen = new Set();
        const rs = [];
        for (const r of range.getClientRects()) {
          if (r.width < 0.5 || r.height < 1) continue;
          const k = r.top + "," + r.bottom + "," + r.x + "," + r.width;
          if (seen.has(k)) continue;
          seen.add(k);
          rs.push(r);
        }
        return rs;
      };
      // 行簇计数（按基线 rect.bottom 聚类，返回行数，与坐标系无关）。top 漂移不是
      // 根因（换 bottom 聚类后计数不变），真凶是上面的重复 rect；bottom 阈值 4px
      // 对行距 ~16.5px 有 4 倍余量，且同行文本基线对齐（rect.bottom 差 <1px）。
      const lineCount = (rects) => {
        let n = 0;
        let prev = NaN;
        for (const r of rects) {
          if (isNaN(prev) || Math.abs(r.bottom - prev) > 4) n++;
          prev = r.bottom;
        }
        return n;
      };
      const blockEndOff = blockClone.childNodes.length;
      // 断点之后（下一页起排部分）在整块内的行数
      const after = lineCount(rectsOf(sc, so, blockClone, blockEndOff));
      rec.after = after;
      this.checked++;
      window.__widowGuard = { checked: this.checked, moved: this.moved };
      if (after !== 1) { skip("after-" + after); return; }
      const total = lineCount(rectsOf(blockClone, 0, blockClone, blockEndOff));
      rec.total = total;
      if (total < 2) { skip("short-" + total); return; }
      const before = lineCount(rectsOf(blockClone, 0, sc, so));
      rec.before = before;
      if (!before) { skip("no-before"); return; }
      // 纯计数判据（与坐标系无关）：行首断点 ⟺ before == total-1；
      // 行内断点 ⟺ before == total（断点在寡行行内，before 连寡行前半也计入）
      if (before === total) { skip("mid-line"); return; }
      if (before !== total - 1) { skip("count-mismatch"); return; }
      // 克隆内全部文本节点（文档序）→ 块级字符坐标
      const texts = [];
      let totalLen = 0;
      const w2 = doc.createTreeWalker(blockClone, NodeFilter.SHOW_TEXT);
      while (w2.nextNode()) {
        const t = w2.currentNode;
        const len = t.textContent.length;
        if (!len) continue;
        texts.push({ node: t, start: totalLen, len: len });
        totalLen += len;
      }
      if (!texts.length) { skip("no-text"); return; }
      const locate = (pos) => {
        for (const e of texts) {
          if (pos < e.start + e.len) return { node: e.node, offset: pos - e.start };
        }
        const last = texts[texts.length - 1];
        return { node: last.node, offset: last.len };
      };
      const linesBefore = (pos) => {
        const p = locate(pos);
        return lineCount(rectsOf(blockClone, 0, p.node, p.offset));
      };
      // 块级二分（纯行数）：最小 pos 使 [块首→pos) 行数达到 before，
      // 其前一位置 = 倒数第二行行首（回移目标）。行首在首文本之前（块首带图）→ 整块。
      let minPos;
      if (linesBefore(0) >= before) {
        minPos = 0;
      } else {
        let lo = 0, hi = totalLen;
        while (hi - lo > 1) {
          const mid = (lo + hi) >> 1;
          if (linesBefore(mid) >= before) hi = mid; else lo = mid;
        }
        minPos = hi;
      }
      const targetPos = Math.max(0, minPos - 1);
      const target = locate(targetPos);
      // 回移后下一页应恰得 2 行（上一行 + 寡行）；计数异常则弃
      const movedLines = lineCount(rectsOf(target.node, target.offset, blockClone, blockEndOff));
      if (movedLines !== after + 1) { skip("bad-target"); return; }
      // 目标边界上下文（节点局部坐标）——落盘供对账"移到的位置到底在哪"
      const ctxTxt = target.node.textContent;
      rec.tgt = ctxTxt.slice(Math.max(0, target.offset - 8), target.offset) + "⇢" + ctxTxt.slice(target.offset, target.offset + 10);
      const srcOffset = cloneStart + targetPos;
      if (targetPos === 0) {
        if (cloneStart > 0) { skip("collide"); return; }
        // 首现两行段：整块下移。若克隆里紧邻的前兄弟是 H1–H4，标题必须随块一起
        // 下移，否则它会孤零零留在页底（实测样张 p4/p5 末：整块移动后 h2 独占页尾）。
        const parent = blockClone.parentNode;
        if (!parent) { skip("no-parent"); return; }
        const prevSib = blockClone.previousElementSibling;
        if (prevSib && /^H[1-4]$/.test(prevSib.tagName)) {
          // 源侧同名前置元素 + data-ref 双向对上才动；对不上宁可不动（orphan-head 弃）
          const srcPrev = srcBlock.previousElementSibling;
          const aRef = prevSib.getAttribute("data-ref");
          const bRef = srcPrev && srcPrev.getAttribute("data-ref");
          if (!srcPrev || srcPrev.tagName !== prevSib.tagName || !aRef || !bRef || aRef !== bRef) {
            skip("orphan-head");
            return;
          }
          // 标题自身的 childNodes 索引（不能取 idx-1：标题与块之间可能有空白文本节点）
          let hIdx = -1;
          let ci = 0;
          for (let n = parent.firstChild; n; n = n.nextSibling, ci++) {
            if (n === prevSib) { hIdx = ci; break; }
          }
          if (hIdx < 0) { skip("orphan-head"); return; }
          overflow.setStart(parent, hIdx);
          const fromOffset = breakToken.offset;
          breakToken.node = srcPrev;
          breakToken.offset = 0;
          this.moved++;
          (window.__widowMoves = window.__widowMoves || []).push({
            tag: tag, from: fromOffset, to: 0, whole: true, head: true,
          });
          rec.why = "MOVED-head";
          (window.__widowTrace = window.__widowTrace || []).push(rec);
          window.__widowGuard = { checked: this.checked, moved: this.moved };
          return breakToken;
        }
        // 非标题前置：普通整块下移
        let idx = 0;
        for (let sib = parent.firstChild; sib && sib !== blockClone; sib = sib.nextSibling) idx++;
        overflow.setStart(parent, idx);
        const fromOffset = breakToken.offset;
        breakToken.node = srcBlock;
        breakToken.offset = 0;
        this.moved++;
        (window.__widowMoves = window.__widowMoves || []).push({
          tag: tag, from: fromOffset, to: 0, whole: true,
        });
        rec.why = "MOVED-whole";
        (window.__widowTrace = window.__widowTrace || []).push(rec);
        window.__widowGuard = { checked: this.checked, moved: this.moved };
        return breakToken;
      }
      // 源内定位 srcOffset（字符计数走源块文本节点）
      const w3 = doc.createTreeWalker(srcBlock, NodeFilter.SHOW_TEXT);
      let rem = srcOffset, srcT = null, srcC = 0;
      while (w3.nextNode()) {
        const t = w3.currentNode;
        const len = t.textContent.length;
        if (rem <= len) { srcT = t; srcC = rem; break; }
        rem -= len;
      }
      if (!srcT) { skip("no-src-pos"); return; }
      // 关键：overflow 与 token 同步回移，removeOverflow 只认 overflow range。
      // 目标恰落某文本节点 offset 0 时必须换成元素边界形态，且要抬到"内联元素
      // 之前"而不是 (code, 0)：元素内起点只搬走子节点，留下空 <code>——背景
      // #f2f2f2 + 内边距在上一页行尾渲染成 ~5pt 灰点（实测 p492/p577/p716，
      // 文本 grep 不可见，须行尾像素检查）。沿 firstChild 链上抬即可越过全部
      // 内联包装（code/strong/em），停在 blockClone 或首个非首位置——元素间
      // 边界与 paged.js 原生元素断点同型：不切文本节点、startContainer 非文本，
      // hyphenateAtBreak 不触发（旧版空左节点 prevLetter=undefined 被 /^\w/
      // 强转 "undefined" 命中 u，追加 U+2011）。行内分支 targetPos>=1 保证
      // 不可能抬成 (blockClone, 0)（那需块前 0 字符，与 targetPos>=1 矛盾）。
      let ovNode = target.node, ovOff = target.offset;
      if (ovOff === 0) {
        let tn = target.node;
        while (tn.parentNode && tn.parentNode !== blockClone && tn.parentNode.firstChild === tn) tn = tn.parentNode;
        const tp = tn.parentNode;
        if (!tp) { skip("no-parent"); return; }
        let ci = 0;
        for (let n = tp.firstChild; n && n !== tn; n = n.nextSibling) ci++;
        ovNode = tp; ovOff = ci;
      }
      overflow.setStart(ovNode, ovOff);
      const fromOffset = breakToken.offset;
      breakToken.node = srcT;
      breakToken.offset = srcC;
      this.moved++;
      (window.__widowMoves = window.__widowMoves || []).push({
        tag: tag, from: fromOffset, to: srcC,
        el: ovNode !== target.node,
      });
      rec.why = "MOVED";
      (window.__widowTrace = window.__widowTrace || []).push(rec);
      window.__widowGuard = { checked: this.checked, moved: this.moved };
      return breakToken;
    } catch (err) {
      (window.__widowGuardErrors = window.__widowGuardErrors || []).push(String(err));
    }
  }
}
window.Paged.registerHandlers(WidowGuard);
"""

TRIM_MM = (185.0, 260.0)
CHAPTER_RE = re.compile(r'<article class="chapter".*?</article>', re.S)


def slice_sample(html: str, chapters: int) -> str:
    """原型模式：只留前 N 章（封面/前言/目录保留，目录页码才有东西可解析）。"""
    matches = list(CHAPTER_RE.finditer(html))
    if len(matches) < chapters:
        raise SystemExit(f"HTML 里只有 {len(matches)} 章，取不到 {chapters} 章")
    keep_end = matches[chapters - 1].end()
    tail = html.rfind("</main>")
    return html[:keep_end] + html[tail:]


VARIATION_SELECTOR = "\ufe0f"
BOOK_TITLE_MARKER = "__BOOK_TITLE__"


def strip_variation_selectors(html: str) -> tuple[str, int]:
    """去掉 U+FE0F（变体选择符）。

    实测（最小用例可复现）：`💡` 走我们随书分发的单色 Noto Emoji，而 `💡️`（emoji + VS16）
    会让 Chromium 改用系统彩色 emoji 字体，印出来是**无名 Type3 位图**——既不能检索，
    在没装该 emoji 字体的机器上还会变成方块。纸面是单色印刷，VS16 没有任何意义。
    """
    return html.replace(VARIATION_SELECTOR, ""), html.count(VARIATION_SELECTOR)


TABLE_SCROLL_STYLE = re.compile(r'(<div class="table-scroll"[^>]*?) style="--table-columns: \d+"')


def strip_table_scroll_inline_vars(html: str) -> tuple[str, int]:
    """剥掉 .table-scroll 上的 `--table-columns` 内联样式。

    这个 CSS 变量只有屏幕版的 `min-width: max(100%, calc(var(--table-columns) * 8rem))`
    用；印刷版表格一律 `width: 100%`，变量是死值。但它必须剥：paged.js 的
    DisplayHandler 把**任何带内联 style 且没显式 display 的元素**标成
    `data-undisplayed`（实测全书 427 个 table-scroll 全部中标），于是
    `displayedElementAfter/Before` 一律跳过这些表格——`h2 { break-after: avoid }`
    的"下一个元素"标记落空，跟在表格前的标题会被孤伶伶留在页底
    （实测 p10「怎么读这一章」整页只有标题，表格翻到下一页）。
    """
    stripped, count = TABLE_SCROLL_STYLE.subn(r"\1", html)
    return stripped, count


def inline_svg_images(html: str) -> tuple[str, int]:
    """把 data-URI 的 SVG `<img>` 改成内联 `<svg>`。

    为什么：图是 `<img src="data:image/svg+xml;base64,…">` 时，SVG 是独立文档，
    印刷样式里的 `svg text { font-family: … }` 进不去，图内文字全部落到系统字体
    （Segoe UI / 微软雅黑 / Consolas…）——同一本书两台机器排出来不是同一本，
    CI 上没有这些字体时还会走样；且这些系统字体的子集被嵌进 PDF，不可检索。
    实测（同一张图，两份 1 页 PDF）：img 版嵌入 7 支系统字体；内联版只剩随书字体，
    中文标签保留。前提已核验：全部 103 张图无 `<style>`/`class`（不引入全局样式冲突），
    注释里合法含 `--` 的图在 DOM 化时交给浏览器解析（XML 严格模式会拒收，HTML 不拒）。

    SMIL：`pauseAnimations()` 对内联 SVG 一样有效（分页与打印发生在分页引擎切片之后，
    首帧口径不变）；`document.fonts.ready` 先于分页（build_print 主流程顺序不变）。
    """
    pattern = re.compile(
        r'<img\b(?P<pre>[^>]*?)\bsrc="data:image/svg\+xml;base64,(?P<svg>[^"]+)"(?P<post>[^>]*)>'
    )
    count = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal count
        svg = base64.b64decode(match.group("svg")).decode("utf-8")
        svg = re.sub(r"^<\?xml[^>]*\?>\s*", "", svg)
        # 印刷剥掉文本描边光晕（paint-order="stroke"）：带 stroke 的文字在
        # Chromium 打印管线里会变成无名 Type3 轮廓位图（不可检索、在低分辨率
        # 打印机上发虚）。实测最小复现：带 paint-order 的一行 hex 文本必出
        # 一个 Type3；去掉后回到 Type0 TrueType。全书仅 stack-frame.svg 用此
        # 技法。**只删携带 paint-order 的那个 <g>/<text> 标签上的 stroke 三件套**——
        # 整个 SVG 盲删会把 fill="none" 的虚线栈槽也抹掉（评审抓到的回归）。
        if 'paint-order="stroke"' in svg:
            def strip_halo(m: re.Match[str]) -> str:
                tag = m.group(0)
                tag = re.sub(r'\s*paint-order="stroke"', "", tag)
                tag = re.sub(r'\s*stroke-width="[^"]*"', "", tag)
                tag = re.sub(r'\s*stroke-linejoin="[^"]*"', "", tag)
                tag = re.sub(r'\s*stroke="[^"]*"', "", tag)
                return tag
            svg = re.sub(r'<(?:g|text|tspan)[^>]*paint-order="stroke"[^>]*>', strip_halo, svg)
        # id 作用域化：103 张图各自定义 id="arr" 这类箭头/渐变/裁剪引用，
        # 内联进同一文档后 url(#arr) 只解析到第一个定义——后续图的箭头会拿到
        # 错色/错尺寸（实测 id=arr 有 12 个互不相同的 marker 定义，fill #666 /
        # #94a3b8 / #3eaf7c、markerWidth 7 vs 8）。字体门抓不到这种错。
        # 每张图内联时给 id 与引用统一加前缀。
        prefix = f"svg{count}-"
        local_ids = set(re.findall(r'\bid="([^"]+)"', svg))
        for local_id in local_ids:
            svg = re.sub(rf'\bid="{re.escape(local_id)}"', f'id="{prefix}{local_id}"', svg)
        for local_id in local_ids:
            escaped = re.escape(local_id)
            svg = re.sub(rf"url\(#{escaped}\)", f"url(#{prefix}{local_id})", svg)
            svg = re.sub(rf'xlink:href="#{escaped}"', f'xlink:href="#{prefix}{local_id}"', svg)
            svg = re.sub(rf'\bhref="#{escaped}"', f'href="#{prefix}{local_id}"', svg)
        pre, post = match.group("pre"), match.group("post")
        attrs = pre + post
        # 图注等其余属性（class/alt…）保留在原位；class 迁到内联 svg 上
        cls = ""
        cls_match = re.search(r'\sclass="([^"]*)"', attrs)
        if cls_match:
            cls = f' class="{cls_match.group(1)}"'
        svg = re.sub(r"<svg\b", f"<svg{cls}", svg, count=1)
        count += 1
        return svg

    html = pattern.sub(replace, html)
    return html, count


def prepare_site(out_dir: Path, html: str, bleed_mm: float, fonts_dir: Path, book_title: str) -> Path:
    """把印刷用 HTML、样式与字体放到同一目录（相对引用，浏览器才能读到字体）。"""
    site = out_dir / "print"
    site.mkdir(parents=True, exist_ok=True)
    fonts_out = site / "fonts"
    if not fonts_dir.is_dir():
        raise SystemExit(
            f"缺少字体子集：{fonts_dir}\n先跑 mcu-book/subset_fonts.py（见该脚本 docstring 的用法）"
        )
    shutil.copytree(fonts_dir, fonts_out, dirs_exist_ok=True)

    css = PRINT_CSS.read_text(encoding="utf-8")
    # 偶数页页眉的书名：占位符必须在这里替换（占位符在 CSS 里，不在 HTML 里）
    css = css.replace(BOOK_TITLE_MARKER, book_title.replace('"', "'"))
    if bleed_mm:
        width, height = TRIM_MM[0] + bleed_mm * 2, TRIM_MM[1] + bleed_mm * 2
        # 出血版：页面扩到裁切尺寸 + 2b，版心各边距同步 +b（正文相对裁切线
        # 位置不变）。每处替换都必须命中——命中不了说明 CSS 改了这里没跟上，
        # 宁可当场报错也不许静默产出错误的出血版（实测 margin 字符串漂移后
        # 封面四角露白边也没人发现）。
        b = bleed_mm
        replacements = [
            (
                f"size: {TRIM_MM[0]:.0f}mm {TRIM_MM[1]:.0f}mm;",
                f"size: {width:.0f}mm {height:.0f}mm;\n  bleed: {b:.0f}mm;\n  marks: crop;",
            ),
            ("margin: 20mm 23mm 22mm 24mm;", f"margin: {20+b:.0f}mm {23+b:.0f}mm {22+b:.0f}mm {24+b:.0f}mm;"),
            ("margin-left: 23mm;", f"margin-left: {23+b:.0f}mm;"),
            ("margin-right: 24mm;", f"margin-right: {24+b:.0f}mm;"),
            ("margin-left: 24mm;", f"margin-left: {24+b:.0f}mm;"),
            ("margin-right: 23mm;", f"margin-right: {23+b:.0f}mm;"),
        ]
        for old, new in replacements:
            if old not in css:
                raise SystemExit(f"出血版式替换未命中（CSS 已漂移，先同步这里）: {old}")
            css = css.replace(old, new, 1)

    # 印刷样式必须排在书稿自带样式之后，才能覆盖屏幕版的栏宽与字号
    html = html.replace("</head>", f"<style>{css}</style>\n</head>", 1)
    page = site / "mcu-deep-book-print.html"
    page.write_text(html, encoding="utf-8")
    return page


def render_pdf(page_path: Path, pdf_path: Path, bleed_mm: float, browser_override: str | None,
               collect_terms: list[str] | None = None, widow_guard: bool = True) -> dict:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - 环境缺依赖时的明确报错
        raise SystemExit("需要 Playwright：python -m pip install -r mcu-book/requirements.txt") from exc

    width = TRIM_MM[0] + bleed_mm * 2
    height = TRIM_MM[1] + bleed_mm * 2
    stats: dict = {}
    # 与 build_html.py 同一套浏览器探测：CI 上用 Playwright 自带 Chromium，
    # 本机（Playwright 只装了 headless shell 时会缺）用系统 Edge/Chrome。
    candidates = build_html._browser_candidates(browser_override)  # noqa: SLF001
    executable = next((p for p in candidates if p.is_file()), None)
    if browser_override and executable is None:
        raise SystemExit(f"指定的浏览器不存在: {browser_override}")
    with sync_playwright() as playwright:
        launch: dict = {"headless": True}
        if executable is not None:
            launch["executable_path"] = str(executable)
        browser = playwright.chromium.launch(**launch)
        try:
            page = browser.new_page(viewport={"width": 900, "height": 1200})
            page.emulate_media(media="print", color_scheme="light")
            page.goto(page_path.resolve().as_uri(), wait_until="load")
            page.evaluate("document.fonts ? document.fonts.ready : Promise.resolve()")
            # 折叠块（大量「参考答案」）必须展开后再分页，否则印出来整段失踪
            page.evaluate("document.querySelectorAll('details').forEach(d => d.open = true)")
            # SMIL 动画统一回到第 0 帧并暂停：屏幕版是"离屏暂停、回视口续播"，
            # 印刷没有视口概念——任其跑的话打印快照取到的是随机时刻的帧，且实测
            # 分页引擎切片 SVG 时 SMIL 处于活动状态会产生重影字形（同一文本
            # Type3/Type0 双份，p87 的 0x2000FFF0）。归零后与"静态首帧"口径一致。
            page.evaluate(
                "document.querySelectorAll('svg').forEach(s => {"
                "  if (typeof s.setCurrentTime === 'function') s.setCurrentTime(0);"
                "  if (typeof s.pauseAnimations === 'function') s.pauseAnimations();"
                "})"
            )
            page.add_script_tag(path=str(PAGED_LIB))
            if widow_guard:
                page.add_script_tag(content=WIDOW_GUARD_JS)
            started = time.time()
            pages = page.evaluate(
                """async () => {
                    const previewer = new window.Paged.Previewer();
                    const flow = await previewer.preview();
                    return flow.total;
                }"""
            )
            stats["pagedSeconds"] = round(time.time() - started, 1)
            stats["pagedPages"] = pages
            widow_guard = page.evaluate(
                "(() => { const g = window.__widowGuard || null;"
                " if (!g) return null; g.moves = window.__widowMoves || [];"
                " g.skip = window.__widowSkip || {}; return g; })()"
            )
            if widow_guard:
                widow_guard["moves"] = widow_guard["moves"][:5]
                stats["widowGuard"] = widow_guard
            widow_errors = page.evaluate("window.__widowGuardErrors || null")
            if widow_errors:
                stats["widowGuardErrors"] = widow_errors[:5]
            if __import__("os").environ.get("WIDOW_TRACE"):
                import json as _json
                _trace = page.evaluate("window.__widowTrace || []")
                with open(".temp/widow-trace.json", "w", encoding="utf-8") as _f:
                    _f.write(_json.dumps(_trace, ensure_ascii=False, indent=1))
                print(f"trace: {len(_trace)} 条 → .temp/widow-trace.json")
                _moves = page.evaluate("window.__widowMoves || []")
                with open(".temp/widow-moves.json", "w", encoding="utf-8") as _f:
                    _f.write(_json.dumps(_moves, ensure_ascii=False, indent=1))
                print(f"moves: {len(_moves)} 条 → .temp/widow-moves.json")
            if collect_terms:
                import json as _json
                # 组合词按别名匹配："ABI / 调用约定" 正文里只写单边；
                # "MMIO（内存映射外设）" 正文只写 MMIO（剥掉括号注）。
                # 纯 ASCII 短别名（AF/UB）用词边界正则，防 "AF" 误中 "AFIO"。
                alias_map = {}
                for t in collect_terms:
                    aliases = []
                    for piece in re.split(r"\s*/\s*|\s+vs\.?\s+", t):
                        piece = re.sub(r"（[^）]*）", "", piece).strip()
                        if piece:
                            aliases.append(piece)
                    alias_map[t] = aliases or [t]
                terms_js = _json.dumps(alias_map, ensure_ascii=False)
                term_pages = page.evaluate(
                    f"""() => {{
  const pages = document.querySelectorAll('.pagedjs_page');
  const index = {{}};
  const aliasMap = {terms_js};
  for (const t of Object.keys(aliasMap)) index[t] = [];
  pages.forEach((pg, i) => {{
    // 结构性页面不算"出现"：封面/版权/导读/目录/书尾页，以及术语表
    // （附录 D）与索引（附录 H）自身——否则每个词都先指向附录/目录
    // 而不是正文（实测 ABI 首次命中 1080 = 附录 D 续页；IDF 命中目录）。
    // paged.js 克隆时分页盒保留祖先链，id 转为 data-id。
    if (pg.querySelector('.cover,.copyright,.contents,.part-divider,[data-id="how-to-read"],'
      + '[data-id="colophon"],[data-id="appendix-glossary"],[data-id="appendix-index"]')) return;
    const text = pg.textContent || '';
    for (const t of Object.keys(aliasMap)) {{
      const hit = aliasMap[t].some(a => {{
        if (/^[\x20-\x7e]+$/.test(a)) {{
          return new RegExp('\\\\b' + a.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&') + '\\\\b').test(text);
        }}
        return text.includes(a);
      }});
      if (hit) index[t].push(i + 1);
    }}
  }});
  // 章节/附录起始页映射：供目录与索引换算 folio（正文从 1 起）
  const starts = {{}};
  pages.forEach((pg, i) => {{
    pg.querySelectorAll('[data-id]').forEach(el => {{
      const id = el.dataset.id;
      if (/^(ch\\d+|appendix-)/.test(id) && !(id in starts)) starts[id] = i + 1;
    }});
  }});
  // 每页实际 folio：分部隔页等不占页码，固定偏移会错章（实测目录
  // 第 13 章 154 vs 物理-9=155）。按增量逐页累进，与引擎 target-counter 同源。
  const folios = {{}};
  let folio = 0;
  pages.forEach((pg, i) => {{
    const inc = getComputedStyle(pg).getPropertyValue('--pagedjs-page-counter-increment').trim();
    if (inc !== '0' && inc !== 'none') {{ folio++; folios[i + 1] = folio; }} else {{ folios[i + 1] = null; }}
  }});
  return {{ index, starts, folios }};
}}"""
                )
                stats["termPages"] = term_pages["index"]
                stats["chapterStarts"] = term_pages["starts"]
                stats["pageFolios"] = term_pages["folios"]
            # 大纲书签：paged.js 把文档重排成页盒子，Chromium 的 page.pdf()
            # 不再产出任何标题树（实测 get_toc() 为 0 条），所以书签只能在
            # 这里从分页后的 DOM 采集：遍历页盒子，记下每个 h1/h2 出现在
            # 哪一物理页。层级在 Python 侧按"部→章→节"整形。
            outline_rows = page.evaluate(
                """() => {
  const rows = [];
  // 容器选择器必须精确：附录是 <article class="appendix">（不是 section），
  // 而 <article class="source-card"> 也是 article —— 用 closest('article')
  // 会把来源卡片当成章。
  const OWNER = 'article.chapter, article.appendix, section.part-divider, section.frontmatter, section.contents';
  // 来源卡片嵌在附录 E 里面，closest(OWNER) 会越过卡片命中 article.appendix，
  // 于是 57 张来源卡的标题（"a1 RM0090 — …"）全都成了附录的 level-2 书签。
  // 卡片标题不是书的结构，命中就整条丢掉。
  const SKIP = 'article.source-card, figure';
  document.querySelectorAll('.pagedjs_page').forEach((pg, i) => {
    pg.querySelectorAll('h1, h2').forEach(el => {
      // 书内目录页的条目是 <a>，不是标题；分部隔页的 .part-label 也不是标题。
      const text = (el.textContent || '').replace(/\\s+/g, ' ').trim();
      if (!text) return;
      if (el.closest(SKIP)) return;
      const owner = el.closest(OWNER);
      if (!owner) return;
      rows.push({
        page: i + 1,
        tag: el.tagName,
        text,
        kind: owner.tagName.toLowerCase() + '.' + (owner.className.split(/\\s+/)[0] || ''),
      });
    });
  });
  return rows;
}"""
            )
            stats["outlineRows"] = outline_rows
            # 分母 = 正文页数（不计封面/前置页/分部隔页）：这些页面的
            # --pagedjs-page-counter-increment 已被样式归零（见 print CSS），
            # counter(page) 由引擎自然从 1 起。counter(pages) 实测不随
            # --pagedjs-page-count 变化（设 999 也不变），所以分母在分页后
            # 用一条 ::after 样式字面覆写；分子仍走 counter(page)。
            page.evaluate(
                """() => {
  let total = 0;
  document.querySelectorAll('.pagedjs_page').forEach(pg => {
    const inc = getComputedStyle(pg).getPropertyValue('--pagedjs-page-counter-increment').trim();
    if (inc !== '0' && inc !== 'none') total += 1;
  });
  const style = document.createElement('style');
  style.textContent = '.pagedjs_page:not(.pagedjs_cover_page):not(.pagedjs_frontmatter_page) .pagedjs_margin-bottom-center .pagedjs_margin-content::after { content: counter(page) " / " "' + total + '" !important; }';
  document.head.appendChild(style);
}"""
            )
            pdf_path.parent.mkdir(parents=True, exist_ok=True)
            page.pdf(
                path=str(pdf_path),
                width=f"{width}mm",
                height=f"{height}mm",
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
                print_background=True,
            )
        finally:
            browser.close()
    return stats


# 栏目名判定阈值：同一个 h2 标题在全书重复出现 >= 这么多次，就是章节模板
# 的栏目名（本章罗盘、学习目标、先跑起来、对照表……），不是"这一章讲了
# 什么"。手写名单维护不住 —— 实测写了 14 个名字仍漏掉 16 个（"先跑起来"
# 68×、"附录：工程完整源码" 39×、"对照表：本章概念 → 仓库落点" 28× 等，
# 共约 280 条照样进了书签面板）。改成按出现频次判，新增栏目自动覆盖。
# 标定：>=5 删 1167 条留 598；>=10 只删 1072（"板卡与版本前提" 8× 这类漏网）。
# 唯一的 4× 标题是"先跑起来（10 分钟 quick win，不用开发板）"，与 68× 的
# "先跑起来（10 分钟 quick win）"同名不同括号，归一化后并入同一桶。
TEMPLATE_SECTION_MIN_REPEATS = 5


def _section_key(text: str) -> str:
    """归一化小标题：去掉编号前缀与括号补语，只留栏目名本体。

    空结果要回退：整条都是括号的标题（"（一）概览"）split 后是空串，
    若放过就会把一堆无关标题并进同一个空桶，>=5 条时集体消失。
    """
    stripped = re.sub(r"^[一二三四五六七八九十〇零\d]+[、.．]\s*", "", text.strip())
    key = re.split(r"[（(]", stripped)[0].strip()
    return key or stripped


def print_outline(rows: list[dict], manifest: dict) -> list[list]:
    """把分页后采集的 h1/h2 行整形成 部(1) → 章(2) → 节(3) 书签树。

    不复用 build_html.restructured_outline：那支函数的输入是 Chromium 自己
    生成的标题树，而 paged.js 产物里 get_toc() 是 0 条（页盒子重排之后
    Chromium 不再输出标题树），两者前提不同。
    结构条目缺失按契约失败处理：一本书少了部或章的书签，不如当场报错。
    """
    expected_parts = [part["title"] for part in manifest["parts"]]
    # 栏目名按频次识别：先统计章内 h2 的归一化标题重复多少次。
    repeats = collections.Counter(
        _section_key(row["text"]) for row in rows if row["kind"] == "article.chapter" and row["tag"] == "H2"
    )
    outline: list[list] = []
    seen_parts: list[str] = []
    chapter_count = 0
    skipped_sections = 0
    for row in rows:
        text, page, kind, tag = row["text"], row["page"], row["kind"], row["tag"]
        if kind == "section.part-divider":
            if tag == "H1":
                outline.append([1, text, page])
                seen_parts.append(text)
            continue
        if kind == "article.chapter":
            if tag == "H1":
                outline.append([2, text, page])
                chapter_count += 1
            elif not outline:
                continue
            elif repeats[_section_key(text)] >= TEMPLATE_SECTION_MIN_REPEATS:
                skipped_sections += 1
            else:
                outline.append([3, text, page])
            continue
        if kind == "article.appendix":
            outline.append([1, text, page] if tag == "H1" else [2, text, page])
            continue
        if kind in {"section.frontmatter", "section.contents"} and tag == "H1":
            outline.append([1, text, page])
    missing = [title for title in expected_parts if title not in seen_parts]
    if missing:
        raise SystemExit(f"大纲：manifest 里的分部没出现在书签里：{missing}")
    chapters = len(build_html.chapter_files(manifest))
    if chapter_count != chapters:
        raise SystemExit(f"大纲：章书签 {chapter_count} 条 ≠ manifest 章数 {chapters}")
    # 层级不许越级（1→3 会让阅读器的书签树错位）
    previous = 0
    for level, title, page in outline:
        if level > previous + 1:
            raise SystemExit(f"大纲层级越级：{title!r}(level {level}) 紧跟 level {previous}，页 {page}")
        previous = level
    # 删掉多少必须印出来：这一轮返工的根源就是"删了多少"不可见 —— 名单
    # 漏掉 16 个栏目名、280 条脏书签照样进了产物，日志上看不出任何异常。
    print(f"大纲：按频次（>={TEMPLATE_SECTION_MIN_REPEATS}×）丢弃重复栏目名书签 {skipped_sections} 条")
    return outline


def finalize_pdf(pdf_path: Path, manifest: dict, rows: list[dict] | None) -> None:
    """给产物补上 PDF 元数据与大纲书签。

    Chromium 写进产物的只有 metadata.title（取自 <title>），作者/主题/
    关键词一概空白，大纲零条 —— 一本上千页的书在阅读器里没有书签面板
    是不能交付的。
    """
    try:
        import fitz
    except ImportError:
        print("（未装 PyMuPDF，跳过元数据与大纲）")
        return
    outline = print_outline(rows or [], manifest)
    document = fitz.open(pdf_path)
    try:
        document.set_toc(outline)
        document.set_metadata(
            {
                **document.metadata,
                "title": manifest["title"],
                "author": manifest.get("author", ""),
                "subject": manifest.get("subtitle", ""),
                "keywords": "单片机, STM32F407, ESP32-S3, FreeRTOS, RT-Thread, GD32, 寄存器",
                "creator": "mcu-book/build_print.py + paged.js",
            }
        )
        document.save(str(pdf_path), incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
    finally:
        document.close()
    levels = [row[0] for row in outline]
    print(
        "元数据与大纲：title/author/subject/keywords 已写入，"
        f"大纲 {len(outline)} 条（部 {levels.count(1)} / 章 {levels.count(2)} / 节 {levels.count(3)}）"
    )


def report(pdf_path: Path, bleed_mm: float) -> int:
    try:
        import fitz
    except ImportError:
        print("（未装 PyMuPDF，跳过产物体检）")
        return 0
    document = fitz.open(pdf_path)
    mm = lambda pt: round(pt / 72 * 25.4, 1)  # noqa: E731
    first = document[0].rect
    fonts = {}
    for index in range(min(document.page_count, 6)):
        for font in document[index].get_fonts():
            fonts[font[3]] = fonts.get(font[3], 0) + 1
    expected = (TRIM_MM[0] + bleed_mm * 2, TRIM_MM[1] + bleed_mm * 2)
    actual = (mm(first.width), mm(first.height))
    ok_size = abs(actual[0] - expected[0]) <= 0.5 and abs(actual[1] - expected[1]) <= 0.5
    type3 = [k for k in fonts if "Type3" in k]
    print(f"产物: {pdf_path}")
    print(f"  尺寸: {actual[0]}×{actual[1]} mm（期望 {expected[0]:.0f}×{expected[1]:.0f}）{'✓' if ok_size else '✗'}")
    print(f"  页数: {document.page_count}")
    print(f"  字体类型: {fonts}{'✗ 存在 Type3 位图字形' if type3 else '✓ 全部为可嵌入轮廓字体'}")
    document.close()
    return 0 if ok_size and not type3 else 1



def assert_vector_art(html: str) -> None:
    """印前硬门：题图必须纯矢量。

    实测（book-final12，2026-10-26）：滤镜题图（feTurbulence）内联进印前 HTML
    会被 Chromium 整块光栅化，全书位图从 6 涨到 100（光栅预算门捕获）。
    这里在排版前按快照断言，把「静默降质」变成硬失败。
    """
    if "feTurbulence" in html or "<filter" in html:
        raise SystemExit("✗ 印前中止：HTML 里含 feTurbulence/<filter>（题图滤镜会光栅化），必须纯矢量。")


def main(argv: list[str] | None = None) -> int:
    # Windows 控制台默认 GBK，报告里的 ✓/✗/中文会在收尾打印时炸
    # UnicodeEncodeError；入口即切 UTF-8（对已是 UTF-8 的环境是无操作）。
    # 守卫 hasattr：redirect_stdout(StringIO) 场景 StringIO 没有 reconfigure。
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out-dir", type=Path, default=BOOK_DIR / "dist")
    parser.add_argument("--sample", type=int, default=None, help="原型模式：只排前 N 章")
    parser.add_argument("--bleed", type=float, default=0.0, help="出血毫米数（0 = 精确裁切尺寸）")
    parser.add_argument("--browser", default=None, help="Chromium 可执行文件路径（默认用 Playwright 自带）")
    parser.add_argument("--html", type=Path, default=None, help="复用既有整书 HTML，不重新装配")
    parser.add_argument("--fonts-dir", type=Path, default=FONTS_DIR, help="字体子集目录（默认 mcu-book/print/fonts）")
    parser.add_argument("--no-index", action="store_true", help="跳过术语索引生成（原型/调试用）")
    parser.add_argument("--no-widow-guard", action="store_true", help="禁用寡行守卫（A/B 对照用）")
    options = parser.parse_args(argv)

    out_dir = options.out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="mcu-print-") as tmp:
        if options.html:
            html = options.html.read_text(encoding="utf-8")
        else:
            built = build_html.build_html(output_dir=Path(tmp))
            html = built.read_text(encoding="utf-8")
            assert_vector_art(html)
    if options.sample:
        html = slice_sample(html, options.sample)
    manifest = build_html.load_manifest()
    html, svg_count = inline_svg_images(html)
    if svg_count:
        print(f"印前排版：内联 {svg_count} 张 SVG 图（父文档字体进入图内文字）")
    html, removed = strip_variation_selectors(html)
    if removed:
        print(f"印前冻结：去掉 {removed} 个变体选择符（U+FE0F，否则 emoji 会走系统彩色字体并印成 Type3）")
    html, ts_stripped = strip_table_scroll_inline_vars(html)
    if ts_stripped:
        print(f"印前冻结：剥掉 {ts_stripped} 个 table-scroll 内联变量（否则 paged.js 把它们当隐藏元素，标题跟随保护落空）")

    page_path = prepare_site(out_dir, html, options.bleed, options.fonts_dir.resolve(), manifest["title"])
    pdf_path = out_dir / "mcu-deep-book-print.pdf"
    if not options.no_index and not options.sample:
        sys.path.insert(0, str(PRINT_DIR))
        import index as idx_mod  # noqa: E402
        terms = idx_mod.extract_terms()
        print(f"索引：第一遍分页收集 {len(terms)} 个术语的页码")
        stats = render_pdf(page_path, pdf_path, options.bleed, options.browser, collect_terms=terms,
                           widow_guard=not options.no_widow_guard)
        term_pages = stats.pop("termPages", {})
        page_folios = stats.pop("pageFolios", {})
        # 索引页码直接用收集器按页码增量算出的 folio（分部隔页不占号，
        # 固定偏移会越往后越偏）。folio 为 null 的页面不产落点。
        zero = [t for t, pages in term_pages.items() if not pages]
        if zero:
            print(f"索引：{len(zero)} 个术语正文零命中，不入索引：{'、'.join(zero)}")
        entries = [(t, [f for f in (page_folios.get(str(p)) for p in pages) if f][:6]) for t, pages in term_pages.items() if pages]
        index_html = idx_mod.render_index_html(entries, manifest["title"])
        # 目录/索引/页脚页码同源：前置页 --pagedjs-page-counter-increment: 0，
        # 引擎的 target-counter 与 counter(page) 都从 1 起，无需字面注入。
        toc_entry = '<li><a href="#appendix-index">附录 H 术语索引</a></li>'
        # 目录里每个分部都以 </ol></section> 收尾，索引要进最后的附录区
        tail_marker = "</ol></section>"
        tail_at = html.rfind(tail_marker)
        if tail_at == -1:
            raise SystemExit("目录里没有附录区（</ol></section> 未找到），索引入口无处可挂")
        html = html[:tail_at] + toc_entry + html[tail_at:]
        # 把索引注入到 </main> 之前
        html = html.replace("</main>", index_html + "\n</main>", 1)
        page_path = prepare_site(out_dir, html, options.bleed, options.fonts_dir.resolve(), manifest["title"])
        print(f"索引：第二遍分页（注入 {len(entries)} 条索引，页码按分页增量计算）")
        stats = render_pdf(page_path, pdf_path, options.bleed, options.browser,
                           widow_guard=not options.no_widow_guard)
    else:
        stats = render_pdf(page_path, pdf_path, options.bleed, options.browser,
                           widow_guard=not options.no_widow_guard)
    print(f"分页: {stats['pagedPages']} 页，用时 {stats['pagedSeconds']}s（paged.js）")
    widow_guard = stats.get("widowGuard")
    if widow_guard:
        print(f"寡行守卫: 检查 {widow_guard['checked']} 处断点，回移 {widow_guard['moved']} 处")
        for move in widow_guard.get("moves", []):
            mark = "整块" if move.get("whole") else "回移"
            print(f"  {mark} <{move['tag']}> offset {move['from']}→{move['to']}")
        skip_map = widow_guard.get("skip") or {}
        if skip_map:
            detail = "，".join(f"{k}×{v}" for k, v in sorted(skip_map.items(), key=lambda kv: -kv[1]))
            print(f"  跳过分布: {detail}")
    if stats.get("widowGuardErrors"):
        print(f"⚠ 寡行守卫异常: {stats['widowGuardErrors']}")
    # 原型模式只排前 N 章，结构条目不全，大纲整形必然报错——跳过。
    if not options.sample:
        finalize_pdf(pdf_path, manifest, stats.get("outlineRows"))
    return report(pdf_path, options.bleed)


if __name__ == "__main__":
    raise SystemExit(main())