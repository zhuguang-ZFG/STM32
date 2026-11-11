// 版式基线测量：现有成片版式里，每场的内容到底占满哪一段。
// 用法：node .trellis/tasks/.../research/fill-probe.mjs [epId] [platform] [--sections <file>] [--out <前缀>]
// 只做只读测量，不写 video/out/，产物落在本目录（<前缀>-<epId>.json / <前缀>-<platform>-<kind>.png）。
//
// --sections：分节表从外部 JSON 注入，**不写 video/episodes/**。
//   在那里放一个 `_layout-lab` 假集，`video:lint` 无参数会遍历整个目录、把它当成第 19 集校验，是污染。
//   文件形状是 { "bilibili": [{at,title}…], "douyin": [...] }——分节本来就是按平台声明的，
//   竖版 pick 的是横版的一个子集，同一份边界表在竖版里会命不中 scene id。
// --out：默认 baseline。baseline-* 那一份是「改之前长什么样」的唯一凭据，
//   改完 CSS 再跑一次会把改前读数覆盖掉，所以改版后的读数一律写 after-*。
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { episodePath, loadEpisode, platformConfig, resolveScenes } from '../../../../../../video/src/spec.mjs'
import { openBrowser, openStage } from '../../../../../../video/src/stage.mjs'

const HERE = import.meta.dirname
const argv = process.argv.slice(2)
const flag = (name) => {
  const i = argv.findIndex((a) => a === `--${name}`)
  if (i < 0) return null
  const v = argv[i + 1]
  if (!v || v.startsWith('--')) throw new Error(`--${name} 缺参数`)
  argv.splice(i, 2)
  return v
}
const sectionsFile = flag('sections')
const outPrefix = flag('out') || 'baseline'
const epId = argv[0] || 'f5-sem-mutex'
const only = argv[1]
const injectedSections = sectionsFile ? JSON.parse(readFileSync(sectionsFile, 'utf8')) : null

const ep = loadEpisode(epId)
const browser = await openBrowser()
const rows = []
const shots = []

// 页头/页脚/水印/字幕带/进度杠这些不参与内容高度，量内容时必须排除
for (const platform of ['bilibili', 'douyin']) {
  if (only && only !== platform) continue
  const cfg = platformConfig(ep, platform)
  const scenes = resolveScenes(ep, platform)
  const stage = await openStage(browser, {
    platform,
    size: cfg.size,
    safe: cfg.safe,
    scenes,
    kicker: ep.cover?.kicker || '通往单片机之路',
    badge: ep.badge,
    sections: injectedSections ? injectedSections[platform] : cfg.sections,
  })
  for (let i = 0; i < scenes.length; i++) {
    const m = await stage.page.evaluate(
      (idx) => {
        window.MCU.setup(idx)
        const body = document.getElementById('body')
        const lay = body.querySelector('.lay')
        const bb = body.getBoundingClientRect()
        const pick = [...lay.children].filter((el) => !el.classList.contains('step'))
        const boxes = pick
          .map((el) => {
            const r = el.getBoundingClientRect()
            if (!r.width || !r.height) return null
            return { cls: el.className.split(' ')[0], top: r.top, bottom: r.bottom, left: r.left, right: r.right }
          })
          .filter(Boolean)
        const topbar = document.querySelector('.topbar').getBoundingClientRect()
        const ticksEl = document.querySelector('.ticks')
        const tcs = getComputedStyle(ticksEl)
        // 页头 chip 是这次新加的元素，宽度上限（12 字）必须由它实测占宽来定，
        // 不能拍一个字数就当契约。
        const chipEl = document.getElementById('secchip')
        const barEl = document.getElementById('secbar')
        const cr = chipEl && chipEl.getBoundingClientRect()
        return {
          bodyTop: bb.top,
          bodyBottom: bb.bottom,
          contentTop: boxes.length ? Math.min(...boxes.map((b) => b.top)) : null,
          contentBottom: boxes.length ? Math.max(...boxes.map((b) => b.bottom)) : null,
          boxes,
          topbar: { top: topbar.top, bottom: topbar.bottom, text: document.querySelector('.topbar').textContent },
          ticksVisible: tcs.display !== 'none',
          chip: cr ? { text: chipEl.textContent, left: cr.left, right: cr.right, top: cr.top, bottom: cr.bottom, overX: chipEl.scrollWidth - chipEl.clientWidth } : null,
          barSegs: barEl ? barEl.childElementCount : null,
          // 按场的进度载体同屏只许有一根**看得见的**。竖版的 .ticks 一直在 DOM 里、
          // 只是 display:none，按节点数判会场场误报——判据要数的是可见性。
          perSceneBarNodes: [...document.querySelectorAll('.ticks, .secbar')]
            .filter((el) => getComputedStyle(el).display !== 'none').length,
        }
      },
      i,
    )
    const kind = scenes[i].kind
    const band = m.bodyBottom - m.bodyTop
    rows.push({
      platform,
      index: i,
      id: scenes[i].id,
      kind,
      kicker: scenes[i].kicker || null,
      bodyTop: +m.bodyTop.toFixed(1),
      bodyBottom: +m.bodyBottom.toFixed(1),
      contentTop: m.contentTop === null ? null : +m.contentTop.toFixed(1),
      contentBottom: m.contentBottom === null ? null : +m.contentBottom.toFixed(1),
      usedPx: m.contentTop === null ? 0 : +(m.contentBottom - m.contentTop).toFixed(1),
      bandPx: +band.toFixed(1),
      fill: m.contentTop === null ? 0 : +((m.contentBottom - m.contentTop) / band).toFixed(3),
      topbar: m.topbar,
      ticksVisible: m.ticksVisible,
      chip: m.chip,
      barSegs: m.barSegs,
      perSceneBarNodes: m.perSceneBarNodes,
      blocks: m.boxes.map((b) => b.cls),
    })
    // 每种 kind 只留一张代表截图，全量留档会把 research 目录塞成几百 MB。
    // 两平台都留：竖版这次的改动是单独一档（padding-block 3u/6u + 页头节进度杠），
    // 只留横版截图等于竖版没有视觉证据。
    if (!shots.includes(`${platform}-${kind}`)) {
      shots.push(`${platform}-${kind}`)
      const png = await stage.capture(i, 0, null, 0, 1)
      writeFileSync(join(HERE, `${outPrefix}-${platform}-${kind}.png`), png)
    }
  }
  await stage.close()
}

await browser.close()
writeFileSync(join(HERE, `${outPrefix}-${epId}.json`), JSON.stringify({ epId, episodePath: episodePath(epId), sections: injectedSections ?? null, rows }, null, 1))

const byKind = {}
for (const r of rows) {
  const k = `${r.platform}/${r.kind}`
  byKind[k] ??= { n: 0, top: 1e9, bottom: 0, fill: 0, minFill: 1, band: r.bandPx, chipW: 0, chipOver: 0 }
  const g = byKind[k]
  g.n++
  if (r.contentTop !== null) {
    g.top = Math.min(g.top, r.contentTop)
    g.bottom = Math.max(g.bottom, r.contentBottom)
    g.fill = Math.max(g.fill, r.fill)
    // 最差场才算数，平均数会骗人
    g.minFill = Math.min(g.minFill, r.fill)
  }
  if (r.chip) {
    g.chipW = Math.max(g.chipW, Math.round(r.chip.right - r.chip.left))
    g.chipOver = Math.max(g.chipOver, r.chip.overX)
  }
}
console.log(`# ${epId} 版式测量（单位 px，y 从画面顶部算；输出前缀 ${outPrefix}）`)
console.log('platform/kind      n   内容上界  内容下界   可用带   最大填充   最差场填充   chip宽/溢出')
for (const [k, g] of Object.entries(byKind)) {
  console.log(
    `${k.padEnd(18)} ${String(g.n).padStart(2)}  ${String(Math.round(g.top)).padStart(6)}   ` +
      `${String(Math.round(g.bottom)).padStart(6)}   ${String(Math.round(g.band)).padStart(5)}   ` +
      `${String(Math.round(g.fill * 100)).padStart(5)}%     ` +
      `${String(Math.round(g.minFill * 100)).padStart(6)}%     ` +
      `${g.chipW ? `${g.chipW}px/${g.chipOver}` : '—'}`,
  )
}
const bars = rows.filter((r) => r.perSceneBarNodes > 1)
console.log(bars.length ? `❌ ${bars.length} 场同屏有多于一根看得见的按场进度` : '✅ 看得见的按场进度：每场都只有一根')
