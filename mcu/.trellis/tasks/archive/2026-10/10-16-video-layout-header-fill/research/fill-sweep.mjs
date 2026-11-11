// 全量纵向填充扫描：改版 CSS 之后，18 集 × 双平台每场的填充比。
// 目的是给 cli.mjs 的那条新判据定阈值——阈值必须低于既有成片的实测最差值，
// 否则一上线就红一整片，判据本身就成了噪声。
// 用法：node .trellis/tasks/archive/2026-10/10-16-video-layout-header-fill/research/fill-sweep.mjs
// 只读测量，不写 video/out/。
import { loadEpisode, platformConfig, resolveScenes } from '../../../../../../video/src/spec.mjs'
import { openBrowser, openStage } from '../../../../../../video/src/stage.mjs'
import { readdirSync } from 'node:fs'
import { join } from 'node:path'

const ids = readdirSync(join(import.meta.dirname, '../../../../../../video/episodes')).filter((d) => !d.startsWith('.'))
const browser = await openBrowser()
const rows = []
for (const epId of ids) {
  let ep
  try {
    ep = loadEpisode(epId)
  } catch (e) {
    console.log(`# ${epId} 载入失败：${e.message.split('\n')[0]}`)
    continue
  }
  for (const platform of Object.keys(ep.platforms)) {
    const cfg = platformConfig(ep, platform)
    const scenes = resolveScenes(ep, platform)
    const stage = await openStage(browser, {
      platform,
      size: cfg.size,
      safe: cfg.safe,
      scenes,
      kicker: ep.cover?.kicker || '通往单片机之路',
      badge: ep.badge,
      sections: cfg.sections,
    })
    for (let i = 0; i < scenes.length; i++) {
      const m = await stage.page.evaluate((idx) => {
        window.MCU.setup(idx)
        const body = document.getElementById('body')
        const lay = body.querySelector('.lay')
        const bb = body.getBoundingClientRect()
        const boxes = [...lay.children]
          .filter((el) => !el.classList.contains('step'))
          .map((el) => el.getBoundingClientRect())
          .filter((r) => r.width && r.height)
        return {
          band: bb.height,
          top: boxes.length ? Math.min(...boxes.map((b) => b.top)) : null,
          bottom: boxes.length ? Math.max(...boxes.map((b) => b.bottom)) : null,
        }
      }, i)
      rows.push({
        epId,
        platform,
        id: scenes[i].id,
        kind: scenes[i].kind,
        fill: m.top === null ? 0 : +((m.bottom - m.top) / m.band).toFixed(3),
      })
    }
    await stage.close()
  }
  console.log(`# ${epId} done (${rows.length} scenes so far)`)
}
await browser.close()

const FLOORED = ['code', 'hook', 'card']
const byKind = {}
for (const r of rows) {
  const k = `${r.platform}/${r.kind}`
  byKind[k] ??= { n: 0, min: 1, max: 0, worst: null }
  const g = byKind[k]
  g.n++
  if (r.fill < g.min) {
    g.min = r.fill
    g.worst = `${r.epId}/${r.id}`
  }
  g.max = Math.max(g.max, r.fill)
}
console.log('\nplatform/kind      n    最差填充   最大填充   最差在哪个场')
for (const [k, g] of Object.entries(byKind)) {
  console.log(
    `${k.padEnd(18)} ${String(g.n).padStart(3)}   ${String(Math.round(g.min * 100)).padStart(4)}%    ` +
      `${String(Math.round(g.max * 100)).padStart(4)}%    ${g.worst}`,
  )
}
const floored = rows.filter((r) => FLOORED.includes(r.kind))
console.log(`\nfloored kinds: n=${floored.length}`)
for (const th of [0.5, 0.55, 0.6, 0.65, 0.7]) {
  const bad = floored.filter((r) => r.fill < th)
  console.log(
    `  阈值 ${th.toFixed(2)} → 不达标 ${String(bad.length).padStart(3)} 场` +
      (bad.length ? `：${bad.slice(0, 8).map((b) => `${b.epId}/${b.id}=${b.fill}`).join(' ')}` : ''),
  )
}
