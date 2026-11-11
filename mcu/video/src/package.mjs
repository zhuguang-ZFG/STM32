import { copyFileSync, readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { codeHtml, inline, FONT, MONO } from './layout.mjs'
import { fmtClock, log } from './util.mjs'

// 封面走 HTML 截图而不是 PIL：和正片同一套字体回退、同一套配色，
// 不会出现"封面有字、正片豆腐块"这种两边字体栈不一致的坑。
// 封面 = 一句钩子 + 一张物证 + 一个数字。
// 物证卡吃 episode.json 里那几行实跑产物，行首 "!"、{{}}、[[]] 的解释直接借正片的 codeHtml/inline
// （layout.mjs 导出），所以封面上那条红边和观众点进去看到的红边是同一句真话——不为封面另写一套。
// 封面 v2「撞色对切」。上一版被否的原因是它在信息流里等于一张纯文字卡：
// 近黑底融进列表、中间一条死白带、336px 下除了标题全糊。这一版的三条硬指标：
//   ① 高饱和对切底（左预期=翠绿 / 右实测=警示红），16 集同一对色 ⇒ 刷到第二次就认得出是本系列
//   ② 画面里必须有一个"看得见的东西"：要么是会亮/会灭的主体，要么是红圈圈住的实测大数字
//   ③ 336px 缩略图下逐条回看，读不到的元素一律不上封面（汇编卡从横版撤下，竖版留）
// B站信息流按 16:9 裁 16:10 的封面，上下各切掉 60px，所以关键元素全部落在 5u 以内侧。
const VS_COLORS = ['#0f7a4f', '#c0251f']

// 主体图形：封面要的是"一眼看懂的那一下"，不是示意图。只画到能认出是什么为止。
// 只收两种"定性不定量"的图形：灯亮/灯灭、时钟密/疏。柱状图那种会被人当成数据的先不做，
// 除非哪天柱子的高度真能由标签里那两个实测数算出来。
function coverMotif(name, u, vert) {
  const mw = vert ? 46 : 44, mh = vert ? 29 : 28
  const wrap = (vb, inner) => `<svg class="motif" width="${u * mw}" height="${u * mh}" viewBox="${vb}">${inner}</svg>`
  if (name === 'led') {
    const led = (lit, x) => `
  <g transform="translate(${x},0)">
    ${lit ? '<circle cx="0" cy="0" r="150" fill="url(#cv-glow)"/>' : ''}
    <path d="M-64 40 L-64 -22 A64 64 0 0 1 64 -22 L64 40 Z" fill="${lit ? '#ffde59' : '#39445a'}" stroke="${lit ? '#fff3b0' : '#5a6478'}" stroke-width="8"/>
    <rect x="-64" y="40" width="128" height="26" rx="6" fill="${lit ? '#e8a020' : '#2b3446'}"/>
    <rect x="-30" y="66" width="14" height="70" fill="#9fb0c8"/><rect x="16" y="66" width="14" height="70" fill="#9fb0c8"/>
  </g>`
    return wrap('-270 -170 540 340', `
  <defs><radialGradient id="cv-glow"><stop offset="0%" stop-color="rgba(255,222,89,.95)"/><stop offset="55%" stop-color="rgba(255,170,40,.35)"/><stop offset="100%" stop-color="rgba(255,170,40,0)"/></radialGradient></defs>
  <g transform="translate(0,10)">${led(true, -108)}${led(false, 118)}</g>`)
  }
  if (name === 'wave') {
    // 一条方波跨过颜色分界：左半密、右半疏。跳变只发生在分界线那一格，读出来就是"同一个信号慢下来了"
    const sq = (x0, x1, half, top, bot) => {
      let d = `M${x0} ${top}`, cur = top, nxt = bot
      for (let x = x0 + half; x < x1; x += half) { d += ` L${x} ${cur} L${x} ${nxt}`; const t = cur; cur = nxt; nxt = t }
      return d + ` L${x1} ${cur}`
    }
    return wrap('-270 -170 540 340', `
  <path d="${sq(-250, -6, 31, -78, 78)}" fill="none" stroke="#fff6d0" stroke-width="15" stroke-linejoin="round" stroke-linecap="round"/>
  <path d="${sq(-6, 250, 86, -78, 78)}" fill="none" stroke="#ffd7d2" stroke-width="15" stroke-linejoin="round" stroke-linecap="round"/>
  <path d="M-6 -152 L-6 152" stroke="rgba(255,255,255,.5)" stroke-width="5" stroke-dasharray="14 12"/>`)
  }
  return ''
}

export function coverHtml({ kicker, line1, line2, tag, proof, proofShort, num, numNote, badge, vs, size }) {
  const [w, h] = size
  const u = coverU(size)
  const vert = h > w
  const [cl, cr] = VS_COLORS
  // 竖版一行只放得下 ⌊929/字号⌋ 个汉字，所以标题走 keep-all：整段汉字不许劈开，
  // 字号被自动顶到"最长那一段刚好放得下"的最大值，断点只会落在空格处。
  // 竖版这个上限是量出来的：12.4u 下"程序说 168MHz"会断成两行，四行标题一路压到底部证据卡，
  // 而缩字只量得出"出界"、量不出"多占一行"——所以宁可从源头就把字号定在断行点以下。
  const big = vert ? (line2 ? 10.6 : 12.0) : line2 ? 12.8 : 14.4
  const lab = vert ? 4.8 : 5.0
  const numFs = vert ? 8.8 : 11
  const card = vert ? (proofShort || proof || '') : ''
  const headTxt = `<div class="l1">${headline(line1 || '')}</div>${line2 ? `<div class="l2">${headline(line2)}</div>` : ''}`
  // 对撞区。横版：标签贴在自己那颗灯旁边，读"谁 vs 谁"不用让视线在画面上来回跳。
  // 竖版一行的宽度只够"一个图形 + 一列文字"，所以图形单独一行、两个标签压在它下面分居两侧。
  const slab = (t) => `<div class="vslab" data-want="${(u * lab).toFixed(2)}">${headline(t)}</div>`
  const colL = `<div class="col">${slab(vs.left)}</div>`
  const colR = `<div class="col r">${slab(vs.right)}</div>`
  const vsx = `<div class="vsx">VS</div>`
  const motif = vs.motif ? coverMotif(vs.motif, u, vert) : ''
  // 横版有图形：标签贴着图形，视线从字走到自己那颗灯。
  // 其余两种（横版无图形 / 竖版）：两列必须被推到行的两端——挤在中间的话，"左边那句"会掉到红色那一侧，
  // 而左右两侧各是什么颜色正是这套封面的读法，站错边就等于说反话。竖版一行也放不下"图+字+字"。
  const vsHtml = vs ? (motif && !vert
    ? `<div class="vs">${colL}${motif}${colR}</div>`
    : `<div class="vs">${motif}<div class="vsrow">${colL}${vsx}${colR}</div></div>`) : ''
  const numbox = num ? `<div class="numbox">
    <div class="numwrap"><svg class="cir" viewBox="0 0 460 300" preserveAspectRatio="none"><path d="M52 232 C14 128 118 26 250 24 C378 22 442 118 424 214 C406 306 250 300 150 276" fill="none" stroke="#ff4d4f" stroke-width="14" stroke-linecap="round" vector-effect="non-scaling-stroke" opacity=".92"/></svg>
      <div class="num" data-want="${(u * numFs).toFixed(2)}">${inline(num)}</div></div>
    ${numNote ? `<div class="numnote" data-want="${(u * 2.6).toFixed(2)}">${inline(numNote)}</div>` : ''}
  </div>` : ''
  const codeCard = card ? `<pre class="code fit" data-want="${(u * 3.35).toFixed(2)}">${codeHtml(card)}</pre>` : ''
  // 竖版也用近竖直的分界（96°），左右两列标签才分别落在两种颜色上；
  // 用 168° 会得到一条近乎水平的界线，"左绿右红"的读法当场失效。
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:${w}px;height:${h}px;font-family:${FONT};color:#e6eaf2;overflow:hidden;
  background:linear-gradient(${vert ? '96deg' : '112deg'},${cl} 0%,${cl} 46%,${cr} 46.2%,${cr} 100%)}
.grain{position:absolute;inset:0;background:repeating-linear-gradient(${vert ? '0deg' : '90deg'},rgba(0,0,0,.055) 0 ${u * 6}px,transparent ${u * 6}px ${u * 12}px)}
.pad{position:absolute;inset:0;padding:${u * (vert ? 5.4 : 6.6)}px ${u * 6}px;display:flex;flex-direction:column;gap:${u * 2.4}px;z-index:1}
.top{flex:none;display:flex;align-items:flex-start;gap:${u * 2}px}
.pill{flex:none;align-self:flex-start;font-size:${u * 2.5}px;font-weight:900;letter-spacing:.14em;color:#fff;
  background:rgba(4,10,22,.34);border-radius:999px;padding:${u * .95}px ${u * 2.6}px}
/* 数字牌不给 max-width：一旦封顶，牌子自己是"装得下"的，超长的数字却会从牌子里淌出去，
   而缩字量的是元素矩形，量不到这淌出去的半截——f0 的 "3298.96 ms" 就是这么被裁掉一个 s 的。
   让牌子跟着数字长，超界就会体现在 .num 的矩形上，缩字才管得住。 */
.numbox{flex:none;margin-left:auto;text-align:center;
  background:rgba(6,12,26,.62);border-radius:${u * 1.4}px;padding:${u * 1.4}px ${u * 2.2}px ${u * 1.6}px}
/* 红圈按 .numwrap 整框缩放，数字一长，弧的落点就爬进最后一个字形：实测 16 张竖封面 4 张越界，
   s2-rcc 的 "53.76 MHz" 被压成 "MH2"（弧就切在 z 的下半笔上）。往右外抛救不了——字形右缘距
   .pad 安全界只剩 38px（c2-pointer 竖版，最紧的一张），弧要同时让开字形和安全界是无解的；
   缩字也不行：框宽和弧同步收，缩 100px 字只换来 7px 净空。
   真凶是层序：.cir 是 absolute，默认盖在静态的 .num 上，红笔把黄字的像素吃了。
   让文字压在笔上，弧从字形后面穿过去——手绘圈本来就该是这样，且不多占一个像素的横向空间。 */
.numwrap{position:relative;display:inline-block;padding:0 ${u * 2.4}px}
.numwrap .cir{position:absolute;left:0;top:${u * -1.6}px;width:100%;height:calc(100% + ${u * 3.2}px)}
.num,.numnote{position:relative;z-index:1}
.num{font-size:${u * numFs}px;font-weight:900;line-height:.98;letter-spacing:-.03em;color:#ffde59;white-space:nowrap;
  text-shadow:0 ${u * .8}px 0 rgba(0,0,0,.4)}
.numnote{margin:${u * 1.2}px auto 0;max-width:${u * 44}px;font-size:${u * 2.6}px;font-weight:800;color:#fff;line-height:1.28;word-break:keep-all}
.mid{flex:1;display:flex;flex-direction:column;justify-content:center;gap:${u * 2.2}px;min-height:0}
.head{flex:none;font-size:${u * big}px;font-weight:900;line-height:1.04;letter-spacing:-.03em;word-break:keep-all;text-align:center;
  text-shadow:0 ${u * 1}px 0 rgba(0,0,0,.42)}
/* keep-all 之后不能再加 overflow-wrap：那会让超长段自己劈开，缩字就量不到溢出，
   等于把"装不下"从一次硬失败换成一张悄悄断错的封面。 */
.l1{color:#fff}
.l2{color:#ffe9a8}
.tk{white-space:nowrap}
.vs{flex:none;display:flex;flex-direction:${vert ? 'column' : 'row'};align-items:center;justify-content:center;gap:${u * (vert ? 1.6 : 2.4)}px;width:100%}
svg.motif{flex:none;display:block}
.vsrow{display:flex;flex-direction:row;align-items:baseline;justify-content:space-between;width:100%;gap:${u * 2}px}
/* 横版两列贴着图形（各自的文字朝灯那一侧收），竖版两列被拉到行两端对望 */
.col{min-width:0;text-align:right}
.col.r{text-align:left}
.vsrow .col{flex:1 1 0;text-align:left}
.vsrow .col.r{text-align:right}
.vslab{font-size:${u * lab}px;font-weight:900;color:#fff;line-height:1.16;word-break:keep-all;
  text-shadow:0 ${u * .7}px 0 rgba(0,0,0,.4)}
.vsx{flex:none;font-size:${u * 4}px;font-weight:900;color:rgba(255,255,255,.7);letter-spacing:.02em}
pre.code{flex:none;background:rgba(6,12,26,.82);border:1px solid rgba(255,255,255,.16);border-left:${u * .55}px solid #ffde59;
  border-radius:${u * .9}px;padding:${u * 1.5}px ${u * 1.8}px;font-family:${MONO};font-size:${u * 3.35}px;line-height:1.42;
  color:#dbe3f0;white-space:pre;tab-size:4;overflow:hidden}
pre.code .ln{display:block;padding:0 ${u * .5}px;border-radius:3px}
pre.code .ln.ev{background:rgba(255,138,128,.15);box-shadow:inset ${u * .35}px 0 0 #ff8a80;color:#ffd9d5}
pre.code .ln.dim{color:#7f8ba0}
pre.code .hl{font-style:normal;color:#ffde59;font-weight:700}
pre.code .bad{font-style:normal;color:#ff8a80;font-weight:700}
pre.code b{color:#8ab4ff}
.foot{flex:none;display:flex;align-items:center;justify-content:center;gap:${u * 1.6}px;font-size:${u * 2.2}px;color:rgba(255,255,255,.86)}
.chip{border:${u * .2}px solid rgba(255,255,255,.6);border-radius:999px;padding:${u * .5}px ${u * 1.8}px;color:#fff;font-weight:900;background:rgba(4,10,22,.28)}
</style></head><body>
<div class="grain"></div>
<div class="pad${vert ? ' v' : ''}">
  <div class="top">
    <div class="pill">${esc(kicker || '通往单片机之路')}</div>
    ${numbox}
  </div>
  <div class="mid">
    ${vsHtml}
    <div class="head" data-want="${(u * big).toFixed(2)}">${headTxt}</div>
    ${codeCard}
  </div>
  <div class="foot"><span class="chip">${esc(tag || '本机实跑')}</span><span>${esc(siteNote(size))}</span></div>
</div>
</body></html>`
}

// v2「实验室仪器风」封面：石墨底 + 细网格 + 四角框，物证卡压红左边，
// 大数字外面一圈红笔游标（::before 贴着自己的内容盒画，不占任何布局空间）。
// 和 v1 一样，模板只负责把话排上去；装不装得下由 fitCover 用量矩形来判，
// 所以 .head/.mid/.num/.numnote/pre.code/.vslab 这些类名一个都不能省。
// 336px 缩略图下读不清的元素不上封面——标题、数字、两列对撞是横版全部内容，
// 证据卡在 336px 下连行首都认不全（v1 横版早就撤了它），只留给竖版。
// 横版腾出来的面积全部给字号：head 10.4u / num 11.5u / vslab 4.6u / numnote 2.4u；
// 竖版维持 8.8/10/3.2/1.8，证据卡优先用短版 proofShort。
export function coverV2Html({ kicker, line1, line2, tag, proof, proofShort, num, numNote, badge, vs, size, variant, siteNote: siteNoteText }) {
  const [w, h] = size
  const u = coverU(size)
  const vert = h > w
  const panel = variant === 'panel'
  const headFs = vert ? 8.8 : 10.4
  const numFs = vert ? 10 : 11.5
  const vsFs = vert ? 3.2 : 4.6
  const noteFs = vert ? 1.8 : 2.4
  const slab = (side, label, text) =>
    `<div class="vslab ${side}" data-want="${(u * vsFs).toFixed(2)}" data-label="${label}">${headline(text || '')}</div>`
  // panel 版只留标题 + 证据卡，不摆对撞两列；两条路径都保留 .head/.mid/.num，
  // fitCover 的缩字与整列压出检查对两版是同一套口径。
  const vsHtml = vs && !panel
    ? `<div class="vs">${slab('l', vs.labels?.[0] || 'EXPECTED', vs.left)}${slab('r', vs.labels?.[1] || 'MEASURED', vs.right)}</div>`
    : ''
  const card = vert ? (proofShort || proof || '') : ''
  const proofHtml = card
    ? `<pre class="code" data-want="${(u * 3.35).toFixed(2)}">${codeHtml(card)}</pre>`
    : ''
  return `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:${w}px;height:${h}px;overflow:hidden;background:#080b10;color:#e6eaf2;font-family:${FONT}}
.pad.v2{position:absolute;inset:0;padding:${u * 5}px ${u * 6}px;display:flex;flex-direction:column;gap:${u * 1.6}px;
  background-color:#0d1118;
  background-image:linear-gradient(rgba(255,255,255,.03) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.03) 1px,transparent 1px),radial-gradient(120% 85% at 50% 0%,rgba(84,130,220,.12),transparent 62%);
  background-size:${u * 4}px ${u * 4}px,${u * 4}px ${u * 4}px,auto}
.corners{position:absolute;inset:${u * 1.5}px;pointer-events:none}
.corners i{position:absolute;width:${u * 3}px;height:${u * 3}px;border:0 solid rgba(255,255,255,.38)}
.corners i:nth-child(1){left:0;top:0;border-left-width:${u * .22}px;border-top-width:${u * .22}px}
.corners i:nth-child(2){right:0;top:0;border-right-width:${u * .22}px;border-top-width:${u * .22}px}
.corners i:nth-child(3){left:0;bottom:0;border-left-width:${u * .22}px;border-bottom-width:${u * .22}px}
.corners i:nth-child(4){right:0;bottom:0;border-right-width:${u * .22}px;border-bottom-width:${u * .22}px}
.top{flex:none;display:flex;align-items:center;justify-content:space-between;gap:${u * 2}px;
  font-family:${MONO};font-size:${u * 2.2}px;letter-spacing:.08em;color:#8fa0b8;white-space:nowrap}
.top b{color:#ffde59;font-weight:800}
.head{flex:none;font-size:${u * headFs}px;font-weight:900;line-height:1.04;letter-spacing:-.03em;word-break:keep-all;
  color:#fff;text-shadow:0 ${u * .8}px 0 rgba(0,0,0,.45)}
.mid{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:center;gap:${u * 2.2}px}
.vs{flex:none;display:flex;gap:${u * 2}px;width:100%}
.vslab{flex:1 1 0;min-width:0;font-size:${u * vsFs}px;font-weight:800;line-height:1.16;color:#dfe6f2;
  word-break:keep-all;border-top:${u * .3}px solid rgba(255,255,255,.18);padding-top:${u * .9}px}
.vslab::before{content:attr(data-label);display:block;margin-bottom:${u * .5}px;font-family:${MONO};
  font-size:${u * 1.5}px;font-weight:700;letter-spacing:.16em;color:#7f8ba0}
.vslab.l{border-top-color:rgba(53,201,138,.75)}
.vslab.r{border-top-color:rgba(255,77,79,.8);text-align:right}
.vslab.r::before{color:#ff8a80}
pre.code{flex:none;background:rgba(5,8,13,.92);border:1px solid rgba(255,255,255,.12);border-left:${u * .55}px solid #ff4d4f;
  border-radius:${u * .7}px;padding:${u * 1.4}px ${u * 1.6}px;font-family:${MONO};font-size:${u * 3.35}px;line-height:1.4;
  color:#cfd8e6;white-space:pre;tab-size:4;overflow:hidden;text-align:left}
pre.code .ln{display:block;padding:0 ${u * .5}px;border-radius:3px}
pre.code .ln.ev{background:rgba(255,138,128,.14);box-shadow:inset ${u * .35}px 0 0 #ff8a80;color:#ffd9d5}
pre.code .ln.dim{color:#7f8ba0}
pre.code .hl{font-style:normal;color:#ffde59;font-weight:700}
pre.code .bad{font-style:normal;color:#ff8a80;font-weight:700}
pre.code b{color:#8ab4ff}
.bottom{flex:none;display:flex;align-items:flex-end;justify-content:space-between;gap:${u * 2}px;
  border-top:1px solid rgba(255,255,255,.12);padding-top:${u * 1.5}px}
/* 游标贴在 .num 自己的内容盒里画（border-box + inset:0）：红圈不增加 scrollWidth，
   缩字量到的永远是文字本身，而不是这圈装饰。::before 是定位元素，默认画在行内文字之上；
   把 .num 立成层叠上下文、环放到 z-index:-1，红笔才从黄字后面穿过去。 */
.num{position:relative;isolation:isolate;flex:none;font-size:${u * numFs}px;font-weight:900;line-height:.98;letter-spacing:-.03em;
  color:#ffde59;white-space:nowrap;text-shadow:0 ${u * .6}px 0 rgba(0,0,0,.5)}
.num::before{content:'';position:absolute;z-index:-1;inset:0;box-sizing:border-box;border:${u * .3}px solid #ff4d4f;
  border-radius:50%;opacity:.9;pointer-events:none}
.numnote{flex:1 1 auto;min-width:0;font-size:${u * noteFs}px;font-weight:700;line-height:1.3;color:#9fb0c8;
  text-align:right;word-break:keep-all}
.tk{white-space:nowrap}
.foot{flex:none;display:flex;align-items:center;justify-content:space-between;gap:${u * 2}px;
  font-family:${MONO};font-size:${u * 2.2}px;color:#8fa0b8}
.chip{border:${u * .2}px solid rgba(255,255,255,.3);border-radius:999px;padding:${u * .5}px ${u * 1.6}px;
  color:#fff;font-weight:800;background:rgba(255,255,255,.04);letter-spacing:.04em}
</style></head><body>
<div class="pad v2">
  <div class="corners"><i></i><i></i><i></i><i></i></div>
  <div class="top"><span>CH1 · <b>${esc(badge || '')}</b></span><span>${esc(kicker || '通往单片机之路')}</span></div>
  <div class="mid">
    <div class="head" data-want="${(u * headFs).toFixed(2)}">${headline(line1 || '')}${line2 ? `<br>${headline(line2)}` : ''}</div>
    ${vsHtml}
    ${proofHtml}
  </div>
  <div class="bottom">
    <div class="num" data-want="${(u * numFs).toFixed(2)}">${esc(num || '')}</div>
    <div class="numnote" data-want="${(u * noteFs).toFixed(2)}">${esc(numNote || '')}</div>
  </div>
  <div class="foot"><span class="chip">${esc(tag || '本机实跑')}</span><span>${esc(siteNoteText || siteNote(size))}</span></div>
</div>
</body></html>`
}

function siteNote(size) {
  return size[0] > size[1] ? '寄存器级 · 每句话都能复现' : '寄存器级 · 全部可复现'
}

function esc(s) {
  return String(s).replace(/[&<>]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]))
}

// 标题里连着的英文/数字/符号必须整体换行：GPIOF->BSRR 断在箭头两边、168MHz 断成 168/MHz，
// 观众读到的是排版事故，不是钩子。汉字之间照常断，交给 text-wrap:balance 配平两行的长度。
function headline(s) {
  return esc(s).replace(/[A-Za-z0-9_][A-Za-z0-9_&;.#+\-/<>=:%()]*/g, (t) => `<span class="tk">${t}</span>`)
}

// 知乎视频封面板要求 16:9，喂 1920×1200 它不缩放、直接在底部切掉一条（实测把「本机实跑」那行
// 证据徽章切掉一半）。所以给它单开一档，让 coverHtml 按 u=10.8 重排，而不是裁交付物。
// 小红书笔记页的封面位是 4:3（1440×1080）；它和抖音共用竖版母版内容，但出图必须另排一版，
// 直接把 3:4 的抖音封面塞进 4:3 位里会被切掉上下两条。
export const COVER_SIZES = {
  bilibili: [1920, 1200],
  douyin: [1080, 1440],
  zhihu: [1920, 1080],
  xiaohongshu: [1440, 1080],
}

// 派生平台复用母版：知乎没有自己的成片，直接挂 B站横版；小红书挂抖音竖版。
// 只有封面按目标平台重排，视频/字幕/时间轴一律指向母版，不再重渲。
export const PACK_MAP = {
  bilibili: { base: 'bilibili', video: 'bilibili.mp4', cover: 'bilibili-cover.png', srt: 'bilibili.srt' },
  douyin: { base: 'douyin', video: 'douyin.mp4', cover: 'douyin-cover.png', srt: 'douyin.srt' },
  zhihu: { base: 'bilibili', video: 'bilibili.mp4', cover: 'zhihu-cover.png', srt: 'bilibili.srt' },
  xiaohongshu: { base: 'douyin', video: 'douyin.mp4', cover: 'xiaohongshu-cover.png', srt: 'douyin.srt' },
}

// pack 的第一趟只做纯解析，不读盘：未知平台在这里就抛，第二趟才动文件。
// 这样后一个平台缺产物时，前一个平台的发布包不会被覆盖成"一半新一半旧"。
export function packJobs(ep, id) {
  const plats = Object.keys(ep.publish || {})
  if (!plats.length) throw new Error(`${id}: 没有 publish，无法出发布包`)
  return plats.map((platform) => {
    const map = PACK_MAP[platform]
    if (!map) throw new Error(`${id}: publish 里有未知平台 "${platform}"，pack 只认 ${Object.keys(PACK_MAP).join('/')}`)
    return {
      platform,
      base: map.base,
      video: map.video,
      srt: map.srt,
      cover: map.cover,
      timeline: join(map.base, 'timeline.json'),
    }
  })
}

// 封面字号单位：跟短边走（竖版按高度算，同样的代码行会直接顶出画布）。
// 排版和缩字地板两处都用它，各算一次的话竖版会一个用 10.8、一个用 14.4，地板凭空抬高 33%。
function coverU(size) {
  return Math.min(size[0], size[1]) / 100
}

// 封面上任何一处溢出都会被截图无声裁掉——这正是这一轮正片花掉 19 场去修的那类 bug。
// 所以这里也做自适应缩字，缩到地板还装不下就直接失败，不留一张半个字出画的封面。
// 判据是"这块的矩形出了 .pad 内容区"，不是 scrollHeight>clientHeight：
// 雅黑的自然行高约 1.21em，标题和数字都是故意压着行高排的，用后者量会把每一张都判成溢出。
// 相应地 .pad 的每个直接子元素都写了 flex:none——一允许压缩，超出的部分就从"出界"变成"被压扁"，量不到了。
export async function fitCover(page, u) {
  return page.evaluate(async (u) => {
    const pad = document.querySelector('.pad')
    const cs = getComputedStyle(pad)
    const r = pad.getBoundingClientRect()
    const lim = {
      l: r.left + parseFloat(cs.paddingLeft),
      r: r.right - parseFloat(cs.paddingRight),
      t: r.top + parseFloat(cs.paddingTop),
      b: r.bottom - parseFloat(cs.paddingBottom),
    }
    const over = (el, own) => {
      const q = el.getBoundingClientRect()
      let v = Math.max(q.right - lim.r, lim.l - q.left, q.bottom - lim.b, lim.t - q.top)
      // 代码卡是 white-space:pre：行长超了自己的框就是被 overflow:hidden 剪掉，矩形看不出来
      if (own) v = Math.max(v, el.scrollWidth - el.clientWidth)
      return v
    }
    // 代码卡还要多量一层：.ln 那条证据高亮条是块级、宽度等于卡的内容宽，
    // 文字超出它只会淌进卡片自己的右内边距（u*1.8）。量卡片的话这十几像素是"装得下"的，
    // 量到的却是高亮条短了一截、末字符贴着卡片边框——c2 的 "@ zero_extendqisi2" 就是这么糊的。
    const codeOver = (el) => Math.max(over(el, true), ...[...el.querySelectorAll('.ln')].map((ln) => ln.scrollWidth - ln.clientWidth))
    const shrink = (el, floor, measure) => {
      const over1 = typeof measure === 'function' ? measure : (x) => over(x, measure === true)
      let fs = parseFloat(getComputedStyle(el).fontSize)
      const start = fs
      for (let i = 0; i < 400; i++) {
        if (over1(el) <= 1) break
        const next = Math.max(floor, fs - Math.max(0.25, fs * 0.02))
        if (next === fs) break
        fs = next
        el.style.fontSize = fs + 'px'
      }
      const q = el.getBoundingClientRect()
      return {
        from: start,
        to: fs,
        over: over1(el),
        // 起始字号对不上元素自己声明的期望值 ⇒ 那条 CSS 规则根本没生效。
        // 这一轮真踩过：把 // 注释写进 <style> 里，CSS 顺手吞掉紧跟它的 .l1 规则，
        // 标题退回 16px、缩字量不到溢出，于是一张废封面"渲染成功"。
        lost: el.dataset.want ? start < parseFloat(el.dataset.want) * 0.9 : false,
        want: el.dataset.want || '',
        box: `${Math.round(q.width)}×${Math.round(q.height)} 右${Math.round(q.right)} 底${Math.round(q.bottom)} / 界${Math.round(lim.r)}×${Math.round(lim.b)}${measure ? ` 文宽${el.scrollWidth}` : ''}`,
      }
    }
    const out = {}
    const code = document.querySelector('pre.code')
    if (code) out.code = shrink(code, u * 2.1, codeOver)
    const head = document.querySelector('.head')
    // own=true：标题里的英文段是 .tk nowrap、整段汉字是 keep-all，撑出去的是 scrollWidth 而不是块的矩形
    if (head) out.head = shrink(head, u * 7, true)
    const num = document.querySelector('.num')
    if (num) out.num = shrink(num, u * 5, true)
    const note = document.querySelector('.numnote')
    if (note) out.note = shrink(note, u * 1.8, true)
    // 对切两列标签各是独立的一段话，必须逐块量：只量第一块的话，右边那条悄悄出画没人知道
    document.querySelectorAll('.vslab').forEach((el, i) => { out['lab' + (i + 1)] = shrink(el, u * 2.6, true) })
    // 上面每一趟都只量"这一块自己出不出界"。竖版真正的失败方式是标题多断一行：
    // 每一块都还在自己框里，但 .mid 里最后那块（证据卡）被顶到画布外——单块量不出来，只能整列合量。
    const mid = document.querySelector('.mid')
    if (mid && head) {
      const kids = [...mid.children]
      // .mid 是 justify-content:center：内容一超高就上下同时溢出，所以两头都要量。
      // 容差给半格 gap，吸收居中带来的亚像素抖动，不让每张都误判。
      const spill = () => {
        const m = mid.getBoundingClientRect()
        return Math.max(0, ...kids.map((k) => {
          const q = k.getBoundingClientRect()
          return Math.max(q.bottom - m.bottom, m.top - q.top)
        })) - u * 0.6
      }
      const from = parseFloat(getComputedStyle(head).fontSize)
      let fs = from
      for (let i = 0; i < 200 && spill() > 0; i++) {
        const next = Math.max(u * 6, fs - Math.max(0.25, fs * 0.015))
        if (next === fs) break
        fs = next
        head.style.fontSize = fs + 'px'
      }
      out.mid = { from, to: fs, over: spill(), lost: false, want: '', box: `整列压出 ${Math.round(spill())}px` }
    }
    return out
  }, u)
}

export async function buildCover(browser, ep, platform, outPath, { variant } = {}) {
  // 平台可以整对象换一份封面：F0 的抖音短版讲的是另一个问题，不该继续挂横版那句钩子和那张跑分卡。
  // 是替换不是合并——合并会让横版的 num/proof 残影留在竖版上，"两个钩子同屏"正是要治的毛病。
  const cover = ep.platforms?.[platform]?.cover ?? ep.cover
  const size = cover?.sizes?.[platform] || COVER_SIZES[platform] || [1920, 1200]
  const u = coverU(size)
  const badge = ep.badge || ep.id.split('-')[0].toUpperCase()
  // v1 的模板与调用参数逐字不变：老封面已经发过稿，重出图必须字节一致。
  // v2 走仪器风模板；variant 先看调用方，再看封面自己的声明（平台 cover 已整体替换 ep.cover）。
  const v2 = (ep.formatVersion ?? 1) === 2
  const html = v2
    ? coverV2Html({ ...cover, badge, tag: cover?.tag, size, variant: variant ?? cover?.variant })
    : coverHtml({ ...cover, badge, tag: cover?.tag, size })
  const page = await browser.newPage({ viewport: { width: size[0], height: size[1] }, deviceScaleFactor: 1 })
  await page.setContent(html, { waitUntil: 'load' })
  await page.evaluate(() => document.fonts.ready)
  const fit = await fitCover(page, u)
  const lost = Object.entries(fit).filter(([, r]) => r.lost)
  if (lost.length) {
    await page.close()
    throw new Error(`${platform} 封面样式没生效：${lost.map(([k, r]) => `${k} 起始 ${r.from.toFixed(1)}px、期望 ${r.want}px`).join('，')}——CSS 规则被吞了，不是字太多`)
  }
  const bad = Object.entries(fit).filter(([, r]) => r.over > 1)
  if (bad.length) {
    await page.close()
    throw new Error(`${platform} 封面装不下：${bad.map(([k, r]) => `${k} 超出 ${Math.round(r.over)}px（${r.box}，已缩到 ${r.to.toFixed(1)}px）`).join('，')}——把 cover.proof/num/line 改短，别指望裁掉`)
  }
  const shrunk = Object.entries(fit).filter(([, r]) => r.to < r.from - 0.5).map(([k, r]) => `${k} ${r.from.toFixed(0)}→${r.to.toFixed(0)}px`)
  await page.screenshot({ path: outPath })
  await page.close()
  log(`  🖼️  封面 ${size.join('×')} → ${outPath}${shrunk.length ? `（缩字 ${shrunk.join('，')}）` : ''}`)
  return outPath
}

// PNG 头里的 IHDR 宽高（偏移 16/20）。不引依赖，测试与人检清单也用它读回实际出图尺寸。
export function pngSize(buf) {
  if (buf.length < 24 || buf.readUInt32BE(0) !== 0x89504e47 || buf.readUInt32BE(4) !== 0x0d0a1a0a) {
    throw new Error('不是 PNG 文件')
  }
  return { width: buf.readUInt32BE(16), height: buf.readUInt32BE(20) }
}

// 四张封面一次出齐：同一集换平台只换排版，不换事实；XHS 4:3 那张同时充当抖音的
// 1440×1080 备选（抖音信息流允许 4:3，部分投放位不裁 3:4）。contact sheet 是给人看的，
// 336px 下读不清就回去改文案，而不是靠它做自动判据。
export async function buildAllCovers(browser, ep, distDir, { variant } = {}) {
  const jobs = [
    ['bilibili', join(distDir, 'bilibili-cover.png')],
    ['douyin', join(distDir, 'douyin-cover.png')],
    ['zhihu', join(distDir, 'zhihu-cover.png')],
    ['xiaohongshu', join(distDir, 'xiaohongshu-cover.png')],
  ]
  for (const [p, out] of jobs) await buildCover(browser, ep, p, out, { variant })
  copyFileSync(join(distDir, 'xiaohongshu-cover.png'), join(distDir, 'douyin-cover-1440x1080.png'))
  await buildContactSheet(browser, jobs.map(([p, out]) => ({ p, out })), join(distDir, 'cover-contact-336.png'))
  return jobs
}

// contact sheet 不走 file://（路径里有空格/中文时 Chromium 的导航规则各不相同）：
// 四张 PNG 直接 base64 内联进 setContent，宽高从 PNG 头读回，标签写实际像素而不是配置值。
// 每列必须正好 336px 宽：标签用绝对定位压在列顶（不再占一行把图挤窄），
// 图宽封顶 336px，竖版 1080×1440 正好铺成 336×448，配上 6px 页边距塞进 460px 高的视口。
// 列框走 inset 阴影而不是 border——border 会吃掉 2px 内容宽，竖版就只能排到 334px。
export async function buildContactSheet(browser, jobs, outPath) {
  const cols = jobs.map(({ p, out }) => {
    const buf = readFileSync(out)
    const { width, height } = pngSize(buf)
    return `<div class="col"><div class="lab"><b>${esc(p)}</b><span>${width}×${height}</span></div>
<div class="shot"><img src="data:image/png;base64,${buf.toString('base64')}" alt="${esc(p)}"></div></div>`
  }).join('\n')
  const page = await browser.newPage({ viewport: { width: 1440, height: 460 }, deviceScaleFactor: 1 })
  try {
    await page.setContent(`<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}
body{width:1440px;height:460px;overflow:hidden;background:#0b0e13;color:#e6eaf2;font-family:${FONT}}
.sheet{display:flex;gap:12px;padding:6px}
.col{position:relative;width:336px;height:448px;flex:none;overflow:hidden;background:#05070a;
  border-radius:6px;box-shadow:inset 0 0 0 1px rgba(255,255,255,.12)}
.lab{position:absolute;left:0;right:0;top:0;z-index:1;display:flex;align-items:baseline;justify-content:space-between;
  padding:4px 8px;background:#05070a;border-bottom:1px solid rgba(255,255,255,.08);font-family:${MONO};font-size:12px;color:#9fb0c8}
.lab b{color:#ffde59;font-size:13px;letter-spacing:.08em}
.shot{width:336px;height:448px;display:flex;align-items:center;justify-content:center}
.shot img{display:block;max-width:336px;width:auto;height:auto}
</style></head><body><div class="sheet">${cols}</div></body></html>`, { waitUntil: 'load' })
    await page.evaluate(() => document.fonts.ready)
    await page.evaluate(() => Promise.all([...document.images].map((img) => img.decode().catch(() => {}))))
    const widths = await page.evaluate(() => [...document.querySelectorAll('.col')].map((el) => el.getBoundingClientRect().width))
    if (widths.some((w) => Math.round(w) !== 336)) throw new Error(`contact sheet 列宽不是 336px：${widths.map(Math.round).join(', ')}`)
    await page.screenshot({ path: outPath })
  } finally {
    await page.close()
  }
  log(`  🧾 封面人检表 1440×460 → ${outPath}`)
  return outPath
}

// B站的分P时间轴直接由实测时间轴生成，不手写（手写的对不上旁白）
// anim 场没有 title（画面本身就是内容），拿 note 当章节名，否则时间轴上会露出 cs-2 这种内部 id。
// 连 note 都没有时退回旁白首句：那个时间点观众听到的就是它，至少不是内部 id。
function sceneLabel(s) {
  if (!s) return ''
  if (s.title) return s.title
  if (s.kicker) return s.kicker
  const src = s.note?.trim() || s.narration?.trim()
  if (!src) return ''
  const act = src.match(/^第[一二三四五六七八九十百\d]+幕[：:]\s*([\s\S]+)$/)
  const body = (act ? act[1] : src).split(/[：:]/)[0].split(/[；;。]/)[0].split(/[，]/)[0].trim()
  return body.length > 24 ? `${body.slice(0, 24)}…` : body
}

function agenda(timeline, scenes) {
  const byId = new Map(scenes.map((s) => [s.id, s]))
  return timeline.scenes
    .filter((ts) => ts.frames / timeline.fps > 2)
    .map((ts) => `${fmtClock(ts.start)} ${sceneLabel(byId.get(ts.id)) || ts.id}`)
    .join('\n')
}

const OFFSITE_RE = /站内|通往单片机之路|全文免费|有全篇|仓库|链接|主页|公众号|微信|QQ|B站|b站|bilibili|抖音号|关注|加群|粉丝群/

// 抖音这条分支和 B站那条不共用正文：B站是"标题 + 长简介 + 时间轴 + 标签"，
// 抖音只有"一段 60 字上下的描述 + 一条置顶评论"，把时间轴和三个候选标题印上去，
// 投稿的人就得自己在里面挑——发布文案的职责是给出可以直接粘的东西，不是给一份需要再加工的材料。
function douyinBlock(ep, pub, secs, cfg, coverPath, videoPath, srtPath, timeline) {
  const id = ep.id
  const cap = pub.caption
  const pin = pub.pinned
  const repro = pub.repro
  const die = (m) => { throw new Error(`发布文案 ${id}/douyin：${m}`) }
  if (!cap) die('缺 publish.douyin.caption')
  if (!pin) die('缺 publish.douyin.pinned')
  if (!repro) die('缺 publish.douyin.repro')
  const wlen = (s) => s.replace(/\s/g, '').length
  const [l1, l2, topicLine = ''] = cap.split('\n')
  if (wlen(l1) > 20) die(`描述首行 ${wlen(l1)} 字 > 20——折叠前那一眼放不下：${l1}`)
  if (wlen(l2) > 24) die(`描述次行 ${wlen(l2)} 字 > 24`)
  if (wlen(cap) > 62) die(`描述共 ${wlen(cap)} 字 > 62`)
  if (OFFSITE_RE.test(cap)) die('描述里出现了站外导流字样——本站口径是全进置顶评论')
  if (!pin.includes('通往单片机之路')) die('置顶评论没写站名，导流就没落地')
  if (!pin.includes(repro.split(' ').pop())) die(`置顶评论没写复现脚本：${repro}`)
  const topics = topicLine.split(/\s+/).filter(Boolean)
  if (topics.length < 3 || topics.length > 5) die(`话题数 ${topics.length}，应为 3~5`)
  const [lo, hi] = ep.platforms.douyin.targetSec
  if (!(secs >= lo && secs <= hi)) die(`时长 ${secs.toFixed(1)}s 不在 ${lo}–${hi}s 区间`)
  if (cfg.size[0] >= cfg.size[1]) die('抖音这条不是竖屏尺寸')
  return [
    '## ① 作品描述（整段复制，含换行和话题）',
    '',
    '```text',
    cap,
    '```',
    '',
    `实测 ${wlen(cap)} 字（首行 ${wlen(l1)} / 次行 ${wlen(l2)} / 话题 ${topics.length} 个），描述里不含任何站外字样。`,
    '抖音早年的硬上限是 55 字、后来传已解除但查不到权威现值，所以这里自限 ≤62 并把两句话排在最前：',
    '真被截只会掉尾部话题。粘贴若报"超出字数"，删掉最后一个话题再贴。',
    '',
    '## ② 置顶评论（发布后立刻用自己账号发一条，长按 → 置顶）',
    '',
    '```text',
    pin,
    '```',
    '',
    `导流只出现在这一条，逐字对应仓库里的复现命令：\`${repro}\``,
    '',
    '## ③ 投稿参数',
    '',
    `- 竖屏 ${cfg.size.join('×')} / ${cfg.fps} fps / ${secs.toFixed(1)}s（${fmtClock(secs)}），落在 ${lo}–${hi}s`,
    `- 文件：\`${videoPath}\``,
    `- 封面：\`${coverPath}\`（竖版 3:4，图上的钩子与描述首行是同一句反差）`,
    `- 字幕：\`${srtPath}\`（${timeline.captions.length} 条，导剪映用；抖音本身不粘 srt）`,
    `- 序号：见 \`video/series.json\` 的 \`no\`（与 B站同一编号）；合集名 16 条共用，第一条发布时建`,
    '- 不填：位置/POI、@、商品、挑战（挑战名不在本机可核验范围，别顺手挂错话题）',
    '',
  ]
}

// 小红书没有"标题/简介两栏可撤回"：标题超 20 字会被截尾、正文超 1000 字会被截断，
// 站外地址会限流，合集漏选不报错但少一次分发。这些全部在写文件前拦死，
// 而不是等发布的人到编辑页里再自己发现。
function xiaohongshuBlock(ep, pub, cfg, coverPath, videoPath, srtPath, secs) {
  const die = (m) => { throw new Error(`发布文案 ${ep.id}/xiaohongshu：${m}`) }
  if (!pub.title?.trim()) die('缺 publish.xiaohongshu.title')
  if (!pub.body?.trim()) die('缺 publish.xiaohongshu.body')
  if ([...pub.title].length > 20) die(`标题 ${[...pub.title].length} 字 > 20`)
  if (pub.body.length > 1000) die(`正文 ${pub.body.length} 字 > 1000`)
  if (/(https?:\/\/|github|www\.)/i.test(`${pub.title}\n${pub.body}`)) die('标题/正文出现站外地址')
  if (!pub.collection?.trim()) die('缺 collection：小红书必须在发布前选合集')
  // 话题不是正文里的 "#名字"：实测只打 # 是黑字，必须接住弹层候选才成 chip。
  // 数组为空等于这条笔记没有话题可分发，不能静默放过。
  if (!Array.isArray(pub.topics) || !pub.topics.length || pub.topics.some((t) => typeof t !== 'string' || !t.trim())) {
    die('缺 topics：话题必须在发布时逐条接弹层，才能变成 chip')
  }
  if (!pub.repro?.trim()) die('缺 repro（复现命令）')
  if (!pub.pinned?.includes(pub.repro.split(' ').pop())) die('置顶评论没写复现脚本')
  const topics = pub.topics.map((t) => `#${String(t).trim().replace(/^#+/, '')}`).join(' ')
  return [
    `# ${ep.title} · 小红书发布（可直接粘贴）`,
    '',
    '## 标题',
    '',
    '```text',
    pub.title.trim(),
    '```',
    '',
    `标题 ${[...pub.title].length} 字（上限 20）。超 20 字不报错、直接从尾部截断，所以这里先拦一次。`,
    '',
    '## 正文',
    '',
    '```text',
    pub.body.trim(),
    '```',
    '',
    `正文 ${pub.body.length} 字（上限 1000）。标题和正文都不含站外地址；复现命令保持 \`${pub.repro}\` 这种纯文本。`,
    '',
    '## 话题',
    '',
    '```text',
    topics,
    '```',
    '',
    '话题必须逐条接弹层：输入 #名字 后接住候选（回车或点选）才会变成 chip；只打 # 只是普通文本，不会成话题。',
    pub.topicsNote ? `\n${pub.topicsNote}` : '',
    '',
    '## 置顶',
    '',
    '```text',
    pub.pinned,
    '```',
    '',
    `发布后立刻用自己的账号发这条并置顶。置顶评论可以出现 \`${pub.repro}\`，站外检查只管标题和正文。`,
    '',
    '## 封面',
    '',
    `- 文件：\`${coverPath}\`（xiaohongshu-cover.png，1440×1080，4:3）`,
    `- 母版：\`${videoPath}\``,
    `- 视频母版：${cfg.size.join('×')} / ${cfg.fps} fps / ${secs.toFixed(1)}s（复用竖版母版，不重渲）`,
    `- 字幕：\`${srtPath}\``,
    '- 小红书封面位是 4:3，不要上传抖音的 1080×1440 3:4 版（上下会被切掉）。',
    '',
    '## 合集',
    '',
    `- 合集：\`${pub.collection.trim()}\``,
    '- 发布前必须选好合集；漏选不报错，只是这次分发不进系列。',
    pub.collectionNote ? `\n${pub.collectionNote}` : '',
    '',
  ]
}

export function writeRelease({ ep, platform, outDir, timeline, cfg, videoPath, srtPath, coverPath, sceneTexts }) {
  const secs = timeline.totalFrames / timeline.fps
  const pub = ep.publish?.[platform] || {}
  if (platform === 'xiaohongshu') {
    const lines = xiaohongshuBlock(ep, pub, cfg, coverPath, videoPath, srtPath, secs)
    const p = join(outDir, `发布-${platform}.md`)
    writeFileSync(p, lines.join('\n'))
    log(`  📝 发布文案 → ${p}`)
    return p
  }
  if (platform === 'douyin') {
    const lines = [`# ${ep.title} · 抖音投稿（可直接粘贴）`, '']
    lines.push(...douyinBlock(ep, pub, secs, cfg, coverPath, videoPath, srtPath, timeline))
    const p = join(outDir, `发布-${platform}.md`)
    writeFileSync(p, lines.join('\n'))
    log(`  📝 发布文案 → ${p}`)
    return p
  }
  const lines = [
    `# ${ep.title} · ${platform} 发布文案`,
    '',
    '## 成片',
    '',
    `- 视频：\`${videoPath}\``,
    `- 字幕：\`${srtPath}\`（${timeline.captions.length} 条，可直接导剪映）`,
    `- 封面：\`${coverPath}\``,
    `- 规格：${cfg.size.join('×')} / ${cfg.fps} fps / ${secs.toFixed(1)}s（${fmtClock(secs)}）`,
    '',
    '## 标题',
    '',
    ...((pub.titles) || [ep.title]).map((t, i) => `${i + 1}. ${t}`),
    '',
    '## 简介',
    '',
    (pub.intro || '').trim(),
    '',
    '## 时间轴',
    '',
    '```',
    agenda(timeline, sceneTexts),
    '```',
    '',
    '## 标签',
    '',
    (pub.tags || []).map((t) => `#${t}`).join(' '),
    '',
    '## 话题',
    '',
    (pub.topics || []).map((t) => `#${t}`).join(' '),
    '',
  ]
  const p = join(outDir, `发布-${platform}.md`)
  writeFileSync(p, lines.join('\n'))
  log(`  📝 发布文案 → ${p}`)
  return p
}
