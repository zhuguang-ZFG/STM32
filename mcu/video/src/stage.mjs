import { chromium } from '@playwright/test'
import { readAnim } from '../../docs/.vitepress/anim-decorate.mjs'
import { animMarkup, pageHtml, setAnimSourceReader } from './layout.mjs'
import { masterDuration } from './timeline.mjs'
import { decodeRgba, diffRgba, log } from './util.mjs'

// 逐帧定格渲染的浏览器侧。核心前提：docs/public/anim/*.svg 全是 SMIL，
// pauseAnimations() 之后 setCurrentTime(t) 可以把动画精确停在任意时刻，
// 所以不需要录屏、不需要等浏览器自己跑时间，每一帧都是确定性截图。
//
// 两个反直觉但必要的细节：
// 1) seek 之后必须等满两帧 rAF 再截图，否则可能拿到上一次合成的旧画面；
// 2) 每场景用一次 innerHTML 重置而不是 reload，SMIL 状态不会跨场景串，
//    导航开销也省掉了（一集上万帧，导航一次几百毫秒吃不消）。

setAnimSourceReader(readAnim)

function buildAnims(scenes, platform) {
  const anims = {}
  for (const [i, sc] of scenes.entries()) {
    if (!sc.anim) continue
    const slug = `${platform}-${i}`
    if (!anims[slug]) anims[slug] = animMarkup(sc.anim, slug)
  }
  return anims
}

export async function openBrowser() {
  return chromium.launch({
    args: [
      '--force-color-profile=srgb',
      '--font-render-hinting=none',
      '--hide-scrollbars',
      '--disable-lcd-text',
      '--disable-features=PaintHolding',
    ],
  })
}

export async function openStage(browser, { platform, size, safe, scenes, kicker, badge, sections, formatVersion = 1, fps = 30 }) {
  const [width, height] = size
  const page = await browser.newPage({
    viewport: { width, height },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
  })
  // 关掉平滑滚动和 transition：帧间只有我们 seek 出来的差异，不该有别的插值在动
  await page.addStyleTag({ content: '*,*::before,*::after{transition:none!important;animation:none!important}' })
  await page.setContent(
    pageHtml({ platform, size, safe, scenes, anims: buildAnims(scenes, platform), kicker, badge, sections, formatVersion, fps }),
    { waitUntil: 'load' },
  )
  await page.evaluate(() => document.fonts.ready)

  return {
    page,
    async capture(index, smilTime, caption, opacity, reveal, beat = null, transition = -1) {
      await page.evaluate(
        async (a) => {
          await window.MCU.frame(a.index, a.smilTime, a.caption, a.opacity, a.reveal)
          if (window.MCU.state) window.MCU.state(a.beat, a.transition)
        },
        { index, smilTime, caption: caption ?? null, opacity: opacity ?? 1, reveal: reveal ?? 1, beat, transition },
      )
      return page.screenshot({ type: 'png' })
    },
    async close() {
      await page.close()
    },
  }
}

// 渲染前的正确性自检（计划风险表第 2 条）。要证的是两件事：
// ① 可复现：同一个 t，前进 seek 与后退 seek 的画面必须一样（含"先推到别处再退回来"），
//    说明 SMIL 状态只由 setCurrentTime 决定，没有偷偷跟着墙钟走；
// ② 真的在动：t 与 t+Δ 的画面必须明显不同，否则等于在截一张静止假图。
//
// 判据用"变化像素占比"而不是逐字节相等：实测同一 t 的两次截图也会有个位数像素、
// 灰度差 ≤5 的出入（Chromium 文本图层的抗锯齿抖动），而真正动了是 6% 像素、
// 差值上百。占比这一项 2026-10-12 按四动画×两平台重标到 0.2%（理由见下面 NOISE_STRONG_PX 那段：
// 面积比单独用会两头错——噪声能铺到 0.15%，一帧真实漂移却只铺 0.0125%），主力判据是强差异像素数。
const NOISE_RATIO = 0.002
// 这条只回答一个问题：setCurrentTime 真的在换画面吗？所以量的是"有没有强差异像素"，
// 不是"动了多少面积"——竖屏 9:16 里一张 720 宽的图只占画面一小块，fsm-dispatch 在
// t=4.44→6.84 实测变化 0.81%（强差异 6784 px），按面积比判会被误杀。
// 对照：同一个 t 回退，强差异实测 0～1 px；差一帧（0.033 s）就有 219 px。
const MOTION_STRONG_PX = 64
// 拦的是"SMIL 在跟墙钟走"。四张动画 × 两平台全量标定（video:calib，2026-10-12）后，
// 两堆数字长这样：
//   回退到同一个 t（Chromium 描边抗锯齿重排）
//     strong 最大 2 px｜面积最大 0.1515%（context-switch）｜Δmax 最大 36
//     stack-frame 0/0.1178%/10 · fsm-dispatch 0/0.0046%/31 · ring-buffer 0/0.0378%/30
//   只差一帧（t+1/30 s）
//     strong 最小 193 px（ring-buffer@douyin）｜面积最小 0.0125%｜Δmax 最小 42（fsm-dispatch）
// 结论：**面积比根本不是判据**——一帧真实漂移铺开的面积（0.0125%）可以比抗锯齿噪声（0.1515%）还小，
// 因为噪声是满屏描边重排、漂移只动几个图元。能分开两者的只有"有多少像素强差异"：噪声 ≤2，漂移 ≥193，
// 差两个数量级。Δmax 那条也别指望：fsm-dispatch 一帧漂移的 Δmax 只有 42，噪声这边已经到 36。
// 所以两条判据是"或"：要么整片差异的幅度本就看不见（Δmax ≤ 16），
// 要么落在已知的抗锯齿形态里（强差异 ≤ 16 个像素，且面积 ≤ 0.2%——面积项只当兜底，不当主力）。
// 上一版面积上限写的是 0.05%，那是只在 1080×1920 上标出来的：换到 1920×1080，SVG 的非整数缩放
// 把同一批描边摊到 3 倍像素上，context-switch 的回退噪声因此到了 0.1515%、Δmax 36，被误判成"跟墙钟走"。
// 用 video:calib 的第三条断言复验过：先把该时刻暖一张，再沿同一条来回路径回退三次，三张逐字节相同；
// 换一条更远的回退路径也只差 1 px。没暖机时第一次回退与之后每次差 1～2 px（Chromium 栅格瓦片缓存建立），
// 所以判据写成"多次回退互差不漂移"，而不是"整片重绘幅度小"。跟墙钟走的图不可能给出三次一样的回退态。
//
// 灵敏度扫描（stack-frame，1080×1920，Δt=33 ms 即一帧）：t=1/3/6/9 s 各点强差异 180～531 px、
// Δmax 202～210，全部可辨；t=4.44/7.5/10.5 s 三点却是 Δmax 9～27、强差异 0——那不是门限失灵，
// 是这张图在两次离散步之间本来就停着不动（Δt 拉到 400 ms 才跳出 201 个强差异像素）。
// 换句话说：这道闸拦的是"看得见的画面对不上"，画面自己不动的时候，墙钟差两百毫秒也无所谓。
const NOISE_STRONG_PX = 16
const NOISE_AA_DELTA = 16

// 两帧之间是否只是噪声？标定脚本（video:lint 之外手工跑）也用这一个判据，避免走偏。
export function reproducibleNoise(d) {
  return d.maxDelta <= NOISE_AA_DELTA || (d.strong <= NOISE_STRONG_PX && d.ratio <= NOISE_RATIO)
}

export async function seekSelfTest(browser, { platform = 'selftest', size = [1280, 720], anim, t = null, delta = 2.4 }) {
  const scenes = [{ id: 'probe', kind: 'anim', anim, title: 'seek 自检', narration: '占位' }]
  const stage = await openStage(browser, { platform, size, safe: null, scenes, kicker: 'selftest', badge: 'seek' })
  const master = masterDuration(anim)
  const at = t === null ? master * 0.37 : t
  const at2 = Math.min(master, at + delta)

  const forward = await stage.capture(0, at, null, 1)
  const repeat = await stage.capture(0, at, null, 1)
  await stage.capture(0, at2, null, 1) // 先把时间推到别处，再退回来
  const backward = await stage.capture(0, at, null, 1)
  const other = await stage.capture(0, at2, null, 1)
  await stage.close()

  const [f, r, bw, o] = await Promise.all([forward, repeat, backward, other].map(decodeRgba))
  const report = {
    anim,
    master,
    t: Number(at.toFixed(3)),
    t2: Number(at2.toFixed(3)),
    stable: diffRgba(f, r),
    rewound: diffRgba(f, bw),
    motion: diffRgba(f, o),
  }
  const quiet = reproducibleNoise
  const fmt = (d) => `变化 ${(d.ratio * 100).toFixed(4)}%、强差异 ${d.strong} px（Δmax ${d.maxDelta}）`
  if (!quiet(report.stable)) throw new Error(`截图不可复现：${anim} 同一 t 连拍两次就不同（${fmt(report.stable)}）`)
  if (!quiet(report.rewound)) {
    throw new Error(`seek 不可复现：${anim} t=${report.t} 前进/后退不一致（${fmt(report.rewound)}），SMIL 可能在跟墙钟走`)
  }
  if (report.motion.strong < MOTION_STRONG_PX) {
    throw new Error(
      `seek 无效：${anim} t=${report.t} 与 t=${report.t2} 几乎没差别（${fmt(report.motion)}），setCurrentTime 可能没生效`,
    )
  }
  log(
    `seek 自检通过：${anim} @ ${report.t}s｜稳定 ${fmt(report.stable)}｜回退 ${fmt(report.rewound)}｜跨 ${report.t2 - report.t}s ${fmt(report.motion)}`,
  )
  return report
}
