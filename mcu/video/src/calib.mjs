// seek 门限的双向标定：npm run video:calib
//
// 这道闸有两个方向的错法，只测一边一定会走偏：
//   放宽 → 把"SMIL 在跟墙钟走"当成抗锯齿噪声放过去，画面与旁白对不上还全绿；
//   收紧 → 把 1920×1080 的描边重排判成不可复现，整集渲到一半直接 fail（2026-10-12 就撞在这）。
// 所以每一张动画、每一个平台都测三条，并把实测数字打出来——stage.mjs 里那几个常量就是照这张表定的：
//   ① 回退可复现：同一个 t 前进 seek / 后退 seek 必须落在噪声形态内；
//   ② 一帧漂移必须仍可辨：t 与 t+1/fps 的差异不能被 ① 的判据吃掉；
//   ③ 那个"回退差异"得证明是光栅化滞后：同一条来回路径连续回退三次，互差必须仍在噪声带内。
// 只跑 ① 的自检不算标定：噪声和真漂移都得量，② 是 ① 的刹车。

import { createHash } from 'node:crypto'
import { openBrowser, openStage, reproducibleNoise, seekSelfTest } from './stage.mjs'
import { decodeRgba, diffRgba, log } from './util.mjs'
import { masterDuration } from './timeline.mjs'

const SIZES = { douyin: [1080, 1920], bilibili: [1920, 1080] }
// 默认这四张覆盖三种最容易走偏的形态：满屏描边（context-switch）、
// 大段静止夹瞬时跳变（stack-frame）、细字多（fsm-dispatch）、高频小图元移动（ring-buffer）。
export const CALIB_ANIMS = ['context-switch', 'stack-frame', 'fsm-dispatch', 'ring-buffer']

function fmt(d) {
  return `变化 ${(d.ratio * 100).toFixed(4)}%、强差异 ${d.strong} px、Δmax ${d.maxDelta}`
}

async function oneFrameDrift(browser, anim, platform, size) {
  const at = masterDuration(anim) * 0.5
  const stage = await openStage(browser, {
    platform,
    size,
    safe: null,
    scenes: [{ id: 'probe', kind: 'anim', anim, title: 'seek 标定', narration: '占位' }],
    kicker: 'calib',
    badge: 'one-frame',
  })
  try {
    // 必须串行：capture 内部是 seek→等两次 rAF→截图，并发调用会让两次取样互相踩时间轴。
    const x = await decodeRgba(await stage.capture(0, at, null, 1))
    const y = await decodeRgba(await stage.capture(0, at + 1 / 30, null, 1))
    return { at, diff: diffRgba(x, y) }
  } finally {
    await stage.close()
  }
}

// 第三条断言：把"回退差异"钉死成光栅化滞后，而不是"暂时没漂到那一点"。
// 同一条来回路径（先去别处再退回 t）走三次，三次结果必须互相落在噪声带内——
// 若 SMIL 真在跟墙钟走，三次回退处在三个不同的墙上时刻，差异会是一帧漂移的量级（强差异上百）。
// 注意要先暖一张：实测第一次回退与之后每次差 1～2 px（Chromium 栅格瓦片缓存建立过程），
// 第二次起逐字节相同。所以判据是"三次互差不漂移"，不是"三次字节相同"——后者会把暖机那次误报。
async function rewindHysteresis(browser, anim, platform, size) {
  const master = masterDuration(anim)
  const at = master * 0.37
  const stage = await openStage(browser, {
    platform,
    size,
    safe: null,
    scenes: [{ id: 'probe', kind: 'anim', anim, title: 'seek 标定', narration: '占位' }],
    kicker: 'calib',
    badge: 'hysteresis',
  })
  const shots = []
  const hashes = []
  try {
    await stage.capture(0, at, null, 1) // 暖机：先把这一时刻的瓦片建起来
    for (let i = 0; i < 3; i++) {
      await stage.capture(0, Math.min(master, at + 2.4), null, 1)
      const buf = await stage.capture(0, at, null, 1)
      hashes.push(createHash('sha1').update(buf).digest('hex').slice(0, 10))
      shots.push(await decodeRgba(buf))
    }
  } finally {
    await stage.close()
  }
  const pair = [diffRgba(shots[0], shots[1]), diffRgba(shots[1], shots[2])]
  return {
    at,
    drift: pair.some((d) => !reproducibleNoise(d)),
    worst: pair.reduce((a, b) => (b.strong > a.strong ? b : a)),
    identical: new Set(hashes).size === 1,
    hashes,
  }
}

export async function runCalibration(anims = CALIB_ANIMS) {
  const browser = await openBrowser()
  const rows = []
  let bad = 0
  try {
    for (const anim of anims) {
      for (const [platform, size] of Object.entries(SIZES)) {
        let noise = null
        try {
          const r = await seekSelfTest(browser, { platform, size, anim })
          noise = r.rewound
        } catch (e) {
          bad++
          log(`  ❌ ${anim}@${platform} 回退自检：${e.message}`)
        }
        const { at, diff } = await oneFrameDrift(browser, anim, platform, size)
        const caught = !reproducibleNoise(diff)
        if (!caught) bad++
        const hyst = await rewindHysteresis(browser, anim, platform, size)
        if (hyst.drift) bad++
        if (noise) {
          rows.push({
            anim,
            platform,
            noiseStrong: noise.strong,
            noiseRatio: +(noise.ratio * 100).toFixed(4),
            noiseMax: noise.maxDelta,
            driftStrong: diff.strong,
            driftRatio: +(diff.ratio * 100).toFixed(4),
            driftMax: diff.maxDelta,
            caught,
          })
        }
        log(
          `  ${noise ? '✓' : '✗'} ${anim.padEnd(16)}@${platform.padEnd(9)} 回退噪声 ${noise ? fmt(noise) : '(自检未过)'}｜` +
            `一帧漂移(t=${at}s) ${fmt(diff)} → ${caught ? '拦得住' : '❌ 被判成噪声'}｜` +
            `三次回退互差 ${fmt(hyst.worst)} → ${hyst.drift ? '❌ 在漂（像跟墙钟）' : `不漂移${hyst.identical ? '（且逐字节相同）' : '（滞后 1～2 px）'}`}`,
        )
      }
    }
  } finally {
    await browser.close()
  }
  if (rows.length) {
    log(`\n汇总（${rows.length} 组）：回退噪声强差异最大 ${Math.max(...rows.map((r) => r.noiseStrong))} px、` +
      `Δmax 最大 ${Math.max(...rows.map((r) => r.noiseMax))}、面积最大 ${Math.max(...rows.map((r) => r.noiseRatio))}%；` +
      `一帧漂移强差异最小 ${Math.min(...rows.map((r) => r.driftStrong))} px、Δmax 最小 ${Math.min(...rows.map((r) => r.driftMax))}`)
    log('  → 门限必须落在"噪声上限"与"漂移下限"之间，两个方向都留余量')
  }
  log(bad ? `\n❌ 标定失败 ${bad} 项` : '\n✅ 标定通过：回退可复现、一帧漂移仍可辨、多次回退不累积漂移')
  return bad ? 1 : 0
}
