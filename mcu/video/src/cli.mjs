#!/usr/bin/env node
// 视频产线入口：
//   npm run video:lint  -- [id…]
//   npm run video:check -- [id…] [--platform …]   只跑舞台+排版审计，不渲帧、不合成配音
//   npm run video:build -- [id…] [--platform bilibili|douyin|both] [--force-audio] [--stills] [--no-bgm] [--variant vs|panel]
//   npm run video:pack  -- [id…]                按 publish 平台复用母版，重排发布包
//   npm run video:numbers -- [id…]              对账上屏数字与 research/<id>-numbers.json
//   npm run video:calib -- [--anims a,b,c]      seek 门限双向标定（改过 stage.mjs 的常量就跑它）
// 六个阶段顺序固定（lint → tts → timeline → stage → mux → package），
// 每阶段的产物都落在 video/out/<id>/<platform>/，改旁白只重合成改动句、改画面只重渲染该集。

import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { pathToFileURL } from 'node:url'
import { episodePath, loadEpisode, platformConfig, resolveScenes, validateEpisode } from './spec.mjs'
import { buildAudio } from './tts.mjs'
import { buildRenderPlan, planSummary } from './timeline.mjs'
import { openBrowser, openStage, seekSelfTest } from './stage.mjs'
import { runCalibration } from './calib.mjs'
import { captureStills, renderFrames } from './render.mjs'
import { BGM_PATH, LAB_BGM_PATH, mux } from './mux.mjs'
import { buildSfxEvents, renderSfx } from './audio/sfx.mjs'
import { buildAllCovers, buildCover, packJobs, writeRelease } from './package.mjs'
import { auditNumbers } from './numbers.mjs'
import { EPISODES_DIR, FFMPEG, OUT_DIR, VIDEO_ROOT, ensureDir, fmtClock, log } from './util.mjs'

const COVER_FILES = ['bilibili-cover.png', 'douyin-cover.png', 'zhihu-cover.png', 'xiaohongshu-cover.png']

function parseArgv(argv) {
  const [cmd, ...rest] = argv
  const pos = []
  const flags = {}
  for (let i = 0; i < rest.length; i++) {
    const a = rest[i]
    if (!a.startsWith('--')) {
      pos.push(a)
      continue
    }
    const eq = a.indexOf('=')
    if (eq > 2) {
      // --k=v 必须认：--out= 写错被当成布尔量吞掉，产物就落进 video/out/，
      // 而那条路径正被投稿队列读着。
      flags[a.slice(2, eq)] = a.slice(eq + 1)
      continue
    }
    const key = a.slice(2)
    const next = rest[i + 1]
    if (next && !next.startsWith('--')) {
      flags[key] = next
      i++
    } else {
      flags[key] = true
    }
  }
  return { cmd, pos, flags }
}

function listEpisodes() {
  if (!existsSync(EPISODES_DIR)) return []
  return readdirSync(EPISODES_DIR, { withFileTypes: true })
    .filter((d) => d.isDirectory() && existsSync(episodePath(d.name)))
    .map((d) => d.name)
    .sort()
}

function pickEpisodes(pos) {
  const ids = pos.length ? pos : listEpisodes()
  if (!ids.length) throw new Error(`video/episodes/ 下没有任何 episode，先写一个 episode.json`)
  for (const id of ids) {
    if (!existsSync(episodePath(id))) throw new Error(`找不到 ${episodePath(id)}`)
  }
  return ids
}

// ---------------------------------------------------------------- lint

// 抖音那两条「流量减少」，平台原文是"出现批量发布违规或低质内容的行为"，不指到具体元素。
// 逐条比对后，机制性的成因在文案本身：12 条挂的是完全相同的一组话题、同一句模板式首行，
// 外加仓库早删掉的 "*"。这类"批量同质"在单集里看不出来，只能在聚合处拦。
function lintDouyinOverlap() {
  const byTopics = new Map()
  const byLine1 = new Map()
  for (const id of listEpisodes()) {
    const cap = JSON.parse(readFileSync(episodePath(id), 'utf8')).publish?.douyin?.caption
    if (!cap) continue
    const [l1, , topicLine = ''] = cap.split('\n')
    const key = topicLine.split(/\s+/).filter(Boolean).sort().join(' ')
    if (key) byTopics.set(key, [...(byTopics.get(key) ?? []), id])
    if (l1) byLine1.set(l1.trim(), [...(byLine1.get(l1.trim()) ?? []), id])
  }
  const errs = []
  for (const [key, ids] of byTopics) if (ids.length > 1) errs.push(`话题组完全相同（${key}）：${ids.join('、')}`)
  for (const [line, ids] of byLine1) if (ids.length > 1) errs.push(`描述首行完全相同（${line}）：${ids.join('、')}`)
  return errs
}

function lintEpisode(id) {
  const ep = JSON.parse(readFileSync(episodePath(id), 'utf8'))
  const { errs, warns } = validateEpisode(ep, id)
  if (!ep.cover?.line1) errs.push('缺 cover.line1（封面大字）')
  if (!ep.publish) errs.push('缺 publish（发布标题/简介/标签）')
  for (const [name, cfg] of Object.entries(ep.platforms || {})) {
    if (!ep.publish?.[name]?.titles?.length) errs.push(`publish.${name}.titles 为空`)
    if (!ep.publish?.[name]?.intro?.trim()) errs.push(`publish.${name}.intro 为空`)
    // 抖音创作中心的作品标题框硬上限 30 字，超了不报错、直接从尾部截断——
    // c4 那条 32 字被截成 "…就是 0x400214"，把地址的尾巴砍掉了，所以在这里拦下来。
    if (name === 'douyin') {
      for (const [i, t] of (ep.publish.douyin.titles || []).entries()) {
        if ([...t].length > 30) errs.push(`publish.douyin.titles[${i}] ${[...t].length} 字 > 30（抖音标题框会静默截尾）：${t}`)
      }
      // "*" 是早代 packaging 的行首标记，仓库删掉了、线上 13 条还挂着它。
      // 描述是发布前最后一道能改的东西，这种脏字符不能等到 package 才发现。
      const cap = ep.publish.douyin.caption
      if (cap && /^\s*\*/m.test(cap)) errs.push(`publish.douyin.caption 有 "*" 行首（老 packaging 残留，会原样发到线上）`)
    }
    const sceneIds = new Set(resolveScenes(ep, name).map((s) => s.id))
    for (const key of Object.keys(cfg.narration || {})) {
      if (!sceneIds.has(key)) errs.push(`platforms.${name}.narration 覆写了不存在的场景 "${key}"`)
    }
    for (const [i, sid] of (cfg.pick || []).entries()) {
      const srcIds = ep.platforms[cfg.reuseFrom]?.scenes
      if (!srcIds?.some((s) => s.id === sid)) errs.push(`platforms.${name}.pick[${i}] = "${sid}" 不在 ${cfg.reuseFrom} 的场景里`)
    }
  }
  return { ep, errs, warns }
}

function cmdLint(ids) {
  let bad = 0
  for (const id of pickEpisodes(ids)) {
    const { ep, errs, warns } = lintEpisode(id)
    const plats = Object.keys(ep.platforms || {})
    log(`\n▶ ${id}  ${ep.title}  [${plats.join(', ')}]`)
    for (const w of warns) log(`  ⚠️  ${w}`)
    for (const e of errs) log(`  ❌ ${e}`)
    if (errs.length) bad++
    else log(`  ✅ 通过：${plats.map((p) => `${p} ${resolveScenes(ep, p).length} 场`).join('，')}`)
  }
  // 跨集检查看的是全集，跟本次选了哪几集无关：单集跑 lint 也得能发现"这个话题组别人用过了"
  const overlap = lintDouyinOverlap()
  if (overlap.length) {
    log(`\n▶ 跨集文案重复（抖音描述）`)
    for (const e of overlap) log(`  ❌ ${e}`)
    bad += overlap.length
  }
  log(`\n${bad ? `❌ ${bad} 个 episode 未通过` : '✅ 全部通过'}`)
  return bad ? 1 : 0
}

// ---------------------------------------------------------------- 排版审计
// 本机的模型读不了图片，计划里"抽帧人检"这条走不通，于是把人要盯的东西量化成七条：
// ① 中文字体真的加载了（否则整屏豆腐块）；② 没有任何元素越出画布；
// ③ .fit 兜底缩字之后不再被裁（被裁 = 这块内容该拆场）；④ 字幕条不压正文、
// 兄弟块不相叠、子块不顶穿 .lay；⑤ 缩完仍要 ≥16px；⑥ SVG 等比不变形；
// ⑦ 大标题折行后末行不许只剩一两个字。渲染前跑一遍，有问题直接 fail，
// 比渲两万帧再人眼找便宜得多。npm run video:check 单跑这一段，不渲帧。

export async function auditLayout(stage, plan) {
  const issues = []
  const longest = new Map()
  for (const cap of plan.captions) {
    const cur = longest.get(cap.scene)
    if (!cur || cap.text.length > cur.length) longest.set(cap.scene, cap.text)
  }
  const rows = []
  for (const sc of plan.scenes) {
    const r = await stage.page.evaluate(
      ({ index, capText }) => {
        window.MCU.setup(index)
        if (window.MCU.showAll) window.MCU.showAll()
        window.MCU.caption(capText || null, 1)
        const win = { w: window.innerWidth, h: window.innerHeight }
        const rect = (el) => el.getBoundingClientRect()
        const name = (el) => `${el.tagName.toLowerCase()}.${String(el.className || '-').replace(/\s+/g, '.')}`
        const capBox = rect(document.getElementById('caps'))

        const overflow = []
        for (const el of document.querySelectorAll('.frame *')) {
          const b = rect(el)
          if (!b.width || !b.height) continue
          if (b.left < -0.5 || b.top < -0.5 || b.right > win.w + 0.5 || b.bottom > win.h + 0.5) {
            overflow.push(`${el.tagName.toLowerCase()}.${el.className || '-'} ${Math.round(b.left)},${Math.round(b.top)},${Math.round(b.right)},${Math.round(b.bottom)}`)
          }
        }

        const clipped = []
        // fitAll 的地板是 6px，等于把"放不下"偷偷降级成"看不见"。抖音版三个 code
        // 场景的标题就是这么被 flex 挤成 5.9px 的——审计当时全绿。16px 按本机实测定：
        // 1080 画布上约 1.5% 高，手机上勉强可读；S16 抖音最紧的一场落在 16.9px。
        const MIN_FONT = 16
        // 横向裁切藏在块级子项里：pre.code 的超长一行是 .ln 自己 scrollWidth 超出，
        // 父级 .fit 的 pre 报 sw==cw（Chromium 不把可见子项的文字溢出冒泡上去）。
        // 只量 .fit 本身就会放行"字被切一半"，所以口径必须跟 layout.mjs 的 overX 一致。
        const overX = (el, bh) => {
          let v = el.scrollWidth - el.clientWidth - bh
          let src = el
          for (const k of el.children) {
            const kcs = getComputedStyle(k)
            if (kcs.overflowX !== 'visible') continue
            const kbh = parseFloat(kcs.borderLeftWidth) + parseFloat(kcs.borderRightWidth)
            const kv = k.scrollWidth - k.clientWidth - kbh
            if (kv > v) { v = kv; src = k }
          }
          return { v, src }
        }
        let minFont = Infinity
        let minFontTag = '-'
        const tooSmall = []
        for (const el of document.querySelectorAll('.fit')) {
          const cs = getComputedStyle(el)
          const fs = parseFloat(cs.fontSize)
          const tag = `${el.tagName.toLowerCase()}.${String(el.className).replace(/\s+/g, '.')}`
          if (fs < minFont) {
            minFont = fs
            minFontTag = `${tag}「${el.textContent.trim().slice(0, 14)}…」`.replace(/…」$/, '」')
          }
          if (fs < MIN_FONT) tooSmall.push(`${tag} 只剩 ${fs.toFixed(1)}px：${el.textContent.trim().slice(0, 24)}`)
          // Chromium 把 border 算进 scrollHeight/scrollWidth。pre.code 有一圈 1px 描边，
          // 于是它永远"超出" 2px/2px——那不是裁切，别拿它当失败。
          // 纵向容差跟 layout.mjs 的 fitAll 保持一致：中文字体行盒高于 line-height，
          // 每行亚像素下溢，四行能到 7px，两边口径不一样就会一边放行一边报错。
          const bv = parseFloat(cs.borderTopWidth) + parseFloat(cs.borderBottomWidth)
          const bh = parseFloat(cs.borderLeftWidth) + parseFloat(cs.borderRightWidth)
          const overV = el.scrollHeight - el.clientHeight - bv - Math.ceil(fs * 0.12)
          const ox = overX(el, bh)
          if (overV > 1 || ox.v > 1) {
            const who = ox.src === el ? '' : `（切在 ${ox.src.tagName.toLowerCase()}.${String(ox.src.className).split(' ')[0]}「${ox.src.textContent.trim().slice(0, 20)}」）`
            clipped.push(`${tag} 超出 ${Math.round(overV)}px/${Math.round(ox.v)}px @${fs.toFixed(1)}px${who}`)
          }
        }

        const hit = []
        if (capText) {
          for (const el of document.querySelectorAll('.title,.sub,.bullets,.cols,.animbox,.note,.url,.kicker,.secchip,.secbar')) {
            const b = rect(el)
            if (!b.width || !b.height) continue
            if (b.bottom > capBox.top + 1 && b.top < capBox.bottom - 1 && b.right > capBox.left + 1 && b.left < capBox.right - 1) {
              hit.push(`${el.tagName.toLowerCase()}.${String(el.className).split(' ')[0]}`)
            }
          }
        }

        // 兄弟相压：上面那三条各查了「越画布」「自身裁切」「压进字幕带」，
        // 但 .note 压在 .cols 上、.step 压在 .note 上这类同层相叠一个都不查。
        // 抖音版 .cols 是 column 方向，内容顶穿格子就是靠这条抓出来的。
        const clash = []
        const marks = [...document.querySelectorAll('.title,.sub,.bullets,.cols,.col,.note,.url,.kicker,.step,.animbox,.cardpanel,.secchip,.secbar')]
          .map((el) => ({ el, b: rect(el) }))
          .filter((m) => m.b.width > 1 && m.b.height > 1)
        for (let a = 0; a < marks.length; a++) {
          for (let c = a + 1; c < marks.length; c++) {
            const A = marks[a], B = marks[c]
            if (A.el.contains(B.el) || B.el.contains(A.el)) continue
            const ox = Math.min(A.b.right, B.b.right) - Math.max(A.b.left, B.b.left)
            const oy = Math.min(A.b.bottom, B.b.bottom) - Math.max(A.b.top, B.b.top)
            if (ox <= 1 || oy <= 1) continue
            const area = ox * oy
            const small = Math.min(A.b.width * A.b.height, B.b.width * B.b.height)
            if (area / small > 0.005) {
              clash.push(
                `${name(A.el)} × ${name(B.el)} 相叠 ${Math.round(ox)}×${Math.round(oy)}px`,
              )
            }
          }
        }

        // 容器被内容顶穿：.fit 只量自己，父级 .cols/.col 溢出 .lay 是查不出来的
        const burst = []
        const lay = document.querySelector('.lay')
        if (lay) {
          const lb = rect(lay)
          for (const el of document.querySelectorAll('.cols,.col,.bullets,.animbox')) {
            const b = rect(el)
            if (b.height && b.bottom > lb.bottom + 1) burst.push(`${name(el)} 超出 .lay 底边 ${Math.round(b.bottom - lb.bottom)}px`)
          }
        }

        // 按场的进度一根就够：横版底部有 .ticks，竖版把它 CSS 关掉、进度改走页头那根杠。
        // 两处同时亮就是同一件事说两遍，还会互相压——判据数的是**看得见的**那几根。
        // 不能数节点：竖版的 .ticks 一直挂在 DOM 里（只是 display:none），
        // 按节点数判会 12 场全部误报。
        const bars = []
        for (const el of document.querySelectorAll('.ticks,.secbar')) {
          if (getComputedStyle(el).display === 'none') continue
          const b = rect(el)
          if (b.width && b.height) bars.push(el.className.split(' ')[0] || el.tagName.toLowerCase())
        }

        // 孤字：大标题折行后末行只剩一两个字。S14 的金句卡就是这么碎成
        // 「Sleep 停脑，Stop 停钟，Standby 断 / 电」的——全片最该被记住的一帧，
        // 排版却是散的。MIN_FONT 那类几何量法抓不到它（字号完全合规），
        // 只能逐字符量行盒：从最后一个可见字符往回数，top 不变的就是末行的字数。
        const widows = []
        for (const el of document.querySelectorAll('.title')) {
          const nodes = []
          const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT)
          for (let n; (n = walker.nextNode()); ) if (n.nodeValue.trim()) nodes.push(n)
          if (!nodes.length) continue
          const rg = document.createRange()
          let li = nodes.length - 1
          let pos = nodes[li].nodeValue.trimEnd().length - 1
          const rectAt = (node, i) => {
            rg.setStart(node, i)
            rg.setEnd(node, i + 1)
            return rg.getBoundingClientRect()
          }
          const lastBox = rectAt(nodes[li], pos)
          if (lastBox.width < 1) continue
          // 只有一行的标题不是折行落单，是整句就短——别报。
          const head = nodes[0].nodeValue.length - nodes[0].nodeValue.trimStart().length
          if (Math.abs(rectAt(nodes[0], head).top - lastBox.top) <= 1) continue
          let tail = nodes[li].nodeValue[pos]
          let seen = 0
          while (seen < 6) {
            pos--
            if (pos < 0) {
              li--
              if (li < 0) break
              pos = nodes[li].nodeValue.trimEnd().length - 1
              if (pos < 0) continue
            }
            const b = rectAt(nodes[li], pos)
            if (Math.abs(b.top - lastBox.top) > 1) break
            tail = nodes[li].nodeValue[pos] + tail
            seen++
          }
          if (seen < 2) widows.push(`末行只剩 ${seen + 1} 字「${tail}」：${el.textContent.trim().slice(0, 22)}`)
        }

        let svgNote = ''
        const svgIssues = []
        const svg = document.querySelector('.animbox svg')
        if (svg) {
          const box = rect(svg.parentElement)
          const b = rect(svg)
          const vb = (svg.getAttribute('viewBox') || '').split(/\s+/).map(Number)
          const want = vb[2] / vb[3]
          const got = b.width / b.height
          svgNote = `svg ${Math.round(b.width)}×${Math.round(b.height)}`
          if (Math.abs(want - got) / want > 0.01) svgIssues.push(`动画被拉伸（比例 ${got.toFixed(3)}，应为 ${want.toFixed(3)}）`)
          if (b.left < box.left - 1 || b.right > box.right + 1 || b.top < box.top - 1 || b.bottom > box.bottom + 1) {
            svgIssues.push(`动画溢出容器 svg=${Math.round(b.left)},${Math.round(b.top)},${Math.round(b.right)},${Math.round(b.bottom)} box=${Math.round(box.left)},${Math.round(box.top)},${Math.round(box.right)},${Math.round(box.bottom)}`)
          }
        }
        const hidden = []
        for (const el of document.querySelectorAll('[data-beat-target]')) {
          const cs = getComputedStyle(el)
          if (parseFloat(cs.opacity) < 0.99) hidden.push(`${el.tagName.toLowerCase()} "${el.getAttribute('data-beat-target')}" opacity=${cs.opacity}`)
        }
        return { overflow, clipped, hit, clash, burst, bars, tooSmall, widows, svgIssues, hidden, minFont: minFont === Infinity ? null : minFont, minFontTag, svgNote, fonts: document.fonts.status }
      },
      { index: sc.index, capText: longest.get(sc.id) || null },
    )

    for (const o of r.overflow) issues.push(`${sc.id}: 越出画布 ${o}`)
    for (const c of r.clipped) issues.push(`${sc.id}: 内容被裁 ${c}`)
    for (const hh of r.hit) issues.push(`${sc.id}: 字幕压住 ${hh}`)
    for (const cl of r.clash) issues.push(`${sc.id}: 版式相叠 ${cl}`)
    for (const ts of r.tooSmall) issues.push(`${sc.id}: 字号不可读 ${ts}`)
    for (const bu of r.burst) issues.push(`${sc.id}: ${bu}`)
    for (const hd of r.hidden) issues.push(`${sc.id}: 审计时仍不可见 ${hd}`)
    if (r.bars.length > 1) issues.push(`${sc.id}: 同屏 ${r.bars.length} 根按场进度（${r.bars.join(' × ')}），只许留一根`)
    // 判据在 13 集成片 × 双平台上跑过一轮：17 处全是真孤字，零误报，所以升成闸。
    // 修法永远是那两个：宽屏在语义接缝补 \n，竖屏把短句再砍短。
    for (const w of r.widows) issues.push(`${sc.id}: 标题${w}（在语义接缝补 \\n 或改短）`)
    for (const s of r.svgIssues) issues.push(`${sc.id}: ${s}`)
    rows.push(
      `  ${String(sc.startFrame / plan.fps).padStart(7)}s  ${sc.id.padEnd(22)} 最小字号 ${
        r.minFont === null ? '-' : `${r.minFont.toFixed(1)}px`
      } ${r.minFontTag}  ${r.svgNote}`,
    )
    log(rows.at(-1))
  }
  if (plan.beatStats) log(`  🎛️ 节拍审计：${plan.beatStats.beats} 拍（含脉冲 ${plan.beatStats.pulses}），最长静止 ${plan.beatStats.maxGap.toFixed(1)}s`)
  // 字体不是看 CSS 写了什么，而是看 Chromium 真正用哪个字族栅格化了这批字。
  // CDP 的 getPlatformFontsForNode 给出实际用的字族 + 栅格化字形数：
  // 字形数为 0 或字族里没有中文字体，屏幕上就是豆腐块。
  const capEl = await stage.page.$('#captext')
  let used = null
  try {
    const cdp = await stage.page.context().newCDPSession(stage.page)
    await cdp.send('DOM.enable')
    await cdp.send('CSS.enable')
    const { root } = await cdp.send('DOM.getDocument', { depth: 1 })
    const { nodeId } = await cdp.send('DOM.querySelector', { nodeId: root.nodeId, selector: '#captext' })
    used = nodeId ? (await cdp.send('CSS.getPlatformFontsForNode', { nodeId })).fonts : null
    await cdp.detach()
  } catch (e) {
    log(`  ⚠️  字体审计降级（CDP 不可用：${e.message.split('\n')[0]}）`)
  }
  const cjk = (used || []).filter((f) => /yahei|pingfang|noto sans sc|source han|han sans|simsun|hei/i.test(f.familyName))
  const glyphs = (used || []).reduce((a, f) => a + (f.glyphCount || 0), 0)
  if (capEl) await capEl.evaluate((el) => (el.textContent = ''))
  if (used && (!cjk.length || !cjk.some((f) => f.glyphCount > 0))) {
    throw new Error(`中文字体没被真正使用，字幕会成豆腐块。实际栅格化字族：${JSON.stringify(used)}（共 ${glyphs} 个字形）`)
  }
  if (used) log(`  🔤 字幕字族：${cjk.map((f) => `${f.familyName}(${f.glyphCount})`).join(' / ')}`)
  if (issues.length) throw new Error(`排版审计未通过:\n${issues.map((e) => `  - ${e}`).join('\n')}`)
  log(`  🔍 排版审计通过：${plan.scenes.length} 场，越界/裁切/压字幕/版式相叠/字号不可读/顶穿容器/标题孤字/进度杠重复 0`)
  return rows
}

// ---------------------------------------------------------------- build

function srtPathOf(outDir) {
  return join(outDir, 'narration.srt')
}

// 验证清单第 5 条：字幕条数与旁白切句一致、时间轴单调、末句不越片尾
function verifySrt(srtFile, timeline, duration) {
  const chunks = readFileSync(srtFile, 'utf8').trim().split(/\n\s*\n/)
  if (chunks.length !== timeline.captions.length) {
    throw new Error(`${srtFile} 有 ${chunks.length} 条字幕，时间轴里是 ${timeline.captions.length} 条`)
  }
  let last = -1
  let end = 0
  for (const [i, ch] of chunks.entries()) {
    const m = ch.match(/(\d\d):(\d\d):(\d\d),(\d\d\d) --> (\d\d):(\d\d):(\d\d),(\d\d\d)/)
    if (!m) throw new Error(`${srtFile} 第 ${i + 1} 条没有时间轴`)
    const t = (a, b, c, d) => Number(a) * 3600 + Number(b) * 60 + Number(c) + Number(d) / 1000
    const s = t(m[1], m[2], m[3], m[4])
    const e = t(m[5], m[6], m[7], m[8])
    if (e <= s) throw new Error(`${srtFile} 第 ${i + 1} 条结束早于开始`)
    if (s < last) throw new Error(`${srtFile} 第 ${i + 1} 条时间倒流：${s} < ${last}`)
    last = s
    end = Math.max(end, e)
  }
  if (end > duration + 0.05) throw new Error(`${srtFile} 末句 ${end.toFixed(2)}s 超出视频时长 ${duration.toFixed(2)}s`)
  log(`  📄 字幕 ${chunks.length} 条，时间轴单调，末句 ${end.toFixed(2)}s ≤ ${duration.toFixed(2)}s`)
  return { count: chunks.length, end }
}

async function buildOne(browser, ep, id, platform, flags) {
  const cfg = platformConfig(ep, platform)
  const v2 = (ep.formatVersion ?? 1) === 2
  const scenes = resolveScenes(ep, platform)
  const workDir = ensureDir(join(OUT_DIR, id, platform))
  const distDir = ensureDir(join(OUT_DIR, id))
  const finalVideo = join(distDir, `${platform}.mp4`)
  log(`\n${'━'.repeat(72)}\n🎬 ${id} · ${platform}  ${cfg.size.join('×')} @ ${cfg.fps}fps  ${scenes.length} 场\n${'━'.repeat(72)}`)

  const t0 = Date.now()
  log('① 旁白合成 + 时间轴')
  const timeline = await buildAudio(ep, platform, workDir, { force: !!flags['force-audio'] })
  const plan = buildRenderPlan(ep, platform, timeline)
  log(planSummary(plan))
  const [lo, hi] = cfg.targetSec || []
  if (lo && hi) {
    const secs = plan.totalFrames / plan.fps
    if (secs < lo || secs > hi) throw new Error(`${platform} 成片 ${secs.toFixed(1)}s，不在目标 ${lo}-${hi}s 内`)
  }

  const animScenes = plan.scenes.filter((s) => s.anim)
  if (animScenes.length && !flags['skip-selftest']) {
    log('② seek 自检（前进/后退可复现 + 跨时刻确实在动）')
    await seekSelfTest(browser, { platform, size: cfg.size, anim: animScenes[0].anim })
  }

  log('③ 舞台 + 排版审计')
  const stage = await openStage(browser, {
    platform,
    size: cfg.size,
    safe: cfg.safe,
    scenes,
    kicker: ep.cover?.kicker || '通往单片机之路',
    badge: ep.badge || id.split('-')[0].toUpperCase(),
    sections: cfg.sections,
    formatVersion: ep.formatVersion ?? 1,
    fps: cfg.fps,
  })
  const srtFile = srtPathOf(workDir)
  verifySrt(srtFile, timeline, timeline.duration)
  let rendered
  try {
    await auditLayout(stage, plan)
    if (flags.stills) {
      const dir = ensureDir(join(workDir, 'stills'))
      // 抽帧要覆盖"首帧亮不亮"和"转场那一帧"：只从 0.5s 往后取，暗首帧恰好落在采样之外。
      // 0.5 / 片尾留给旧口径，场起点抓 reveal，动画场中点抓画面本身。
      const fps = plan.fps
      const last = (plan.totalFrames - 1) / fps
      const all = [
        ...new Set([
          0,
          0.5,
          ...plan.scenes.map((s) => s.startFrame / fps),
          ...plan.scenes.filter((s) => s.anim).map((s) => s.startFrame / fps + s.duration / 2),
          last,
        ]),
      ].sort((a, b) => a - b)
      const marks = all.slice(0, 12)
      if (all.length > 12 && !marks.includes(last)) marks.push(last)
      const picked = await captureStills(plan, stage, marks, (name, buf) => writeFileSync(join(dir, `${name}.png`), buf))
      log(`  🖼️  抽帧 ${picked.length} 张 → ${dir}`)
    }
    log(`④ 逐帧渲染 → ${finalVideo}`)
    let next = 0
    rendered = await renderFrames(plan, stage, {
      outPath: join(workDir, 'video.mp4'),
      ffmpeg: FFMPEG,
      onFrame: ({ done, total, shot, reused }) => {
        const now = Date.now()
        if (now < next) return
        next = now + 5000
        process.stdout.write(`\r    ${((done / total) * 100).toFixed(1)}%  ${done}/${total} 帧  截图 ${shot} 复用 ${reused}`)
      },
    })
    process.stdout.write('\n')
  } finally {
    await stage.close()
  }

  log(`⑤ 合流（旁白${v2 ? ' + 节拍 SFX' : ''} + BGM ducking + loudnorm）`)
  let sfxPath = null
  if (v2) {
    sfxPath = join(workDir, 'sfx.wav')
    const { events } = renderSfx(buildSfxEvents(plan), { duration: timeline.duration, outPath: sfxPath })
    if (!plan.beatStats) throw new Error('v2 渲染计划缺少 beatStats，无法对账 SFX')
    if (events.length !== plan.beatStats.beats) {
      throw new Error(`SFX 事件 ${events.length} ≠ 节拍 ${plan.beatStats.beats}`)
    }
    log(`  🔔 SFX ${events.length} 条 → ${sfxPath}`)
  }
  const info = await mux({
    videoPath: join(workDir, 'video.mp4'),
    narrationPath: join(workDir, 'narration.wav'),
    outPath: finalVideo,
    duration: timeline.duration,
    bgm: flags['no-bgm'] ? null : (v2 ? LAB_BGM_PATH : BGM_PATH),
    sfxPath,
    assertLoudness: v2,
  })
  const drift = Math.abs(info.duration - rendered.frames / plan.fps)
  if (drift > 1 / plan.fps) throw new Error(`${platform} 视频 ${rendered.frames / plan.fps}s 与成片 ${info.duration}s 差 ${drift}s`)

  log('⑥ 封面 + 发布文案')
  const cover = join(distDir, `${platform}-cover.png`)
  const srtOut = join(distDir, `${platform}.srt`)
  copyFileSync(srtFile, srtOut)
  if (v2) {
    // v2 的四张封面由 cmdBuild 在平台循环之前统一出齐：每集只排一次版，
    // 换平台重跑 build 时不会把别的平台的封面悄悄重画成另一版。
    const missing = COVER_FILES.map((f) => join(distDir, f)).filter((p) => !existsSync(p))
    if (missing.length) {
      throw new Error(`${id} v2 封面不齐：缺 ${missing.join('，')}——先跑 npm run video:build（v2 会在平台循环前统一出齐四张）`)
    }
  } else {
    await buildCover(browser, ep, platform, cover)
  }
  const release = writeRelease({
    ep,
    platform,
    outDir: distDir,
    timeline,
    cfg,
    videoPath: finalVideo,
    srtPath: srtOut,
    coverPath: cover,
    sceneTexts: scenes,
  })
  log(`✅ ${platform} 完成：${fmtClock(timeline.duration)}，用时 ${((Date.now() - t0) / 1000).toFixed(0)}s`)
  for (const f of [finalVideo, srtOut, cover, release]) log(`   ${f}`)
  return { id, platform, duration: timeline.duration, frames: rendered.frames }
}

async function cmdBuild(ids, flags) {
  const want = !flags.platform || flags.platform === 'both' ? ['bilibili', 'douyin'] : [flags.platform]
  const targets = pickEpisodes(ids)
  const variant = typeof flags.variant === 'string' ? flags.variant : undefined
  log(`🎞️  产线启动：${targets.join(', ')} × ${want.join('/')}`)
  const results = []
  const browser = await openBrowser()
  try {
    for (const id of targets) {
      const ep = loadEpisode(id)
      // v2 每集先出齐四平台封面（B站/抖音/知乎/小红书），再进平台循环；
      // buildOne 只断言四张存在，避免第二个平台把第一张覆盖成另一套文案。
      if ((ep.formatVersion ?? 1) === 2) {
        log(`\n🖼️  ${id} 四平台封面（v2 统一出图）`)
        await buildAllCovers(browser, ep, ensureDir(join(OUT_DIR, id)), { variant })
      }
      for (const platform of want) {
        if (!ep.platforms[platform]) {
          log(`⏭️  ${id} 没有 ${platform} 平台，跳过`)
          continue
        }
        results.push(await buildOne(browser, ep, id, platform, flags))
      }
    }
  } finally {
    await browser.close()
  }
  log(`\n${'━'.repeat(72)}`)
  for (const r of results) log(`✅ ${r.id} · ${r.platform}  ${fmtClock(r.duration)}  ${r.frames} 帧`)
  log(`📦 产物在 ${join(OUT_DIR, targets[0])}`)
  return 0
}

// 只跑「舞台 + 排版审计」，一帧不渲、一句配音都不合成（时间轴必须已存在）。
// 改完 episode.json 想确认版式没塌、孤字有没有犯，用这条：几秒出结果，
// 不用为了看一眼标题折行等两万帧。
// 只重画封面，一帧成片都不渲、一句配音都不合成。封面是 package 阶段里唯一能独立重做的产物
// （换钩子、换配色这类事不该付两万帧的代价）。--out 把候选画到别处，免得半成品封面被正在排队的投稿读走。
async function cmdCover(ids, flags) {
  const want = !flags.platform || flags.platform === 'both' ? ['bilibili', 'douyin'] : [flags.platform]
  const targets = pickEpisodes(ids)
  const browser = await openBrowser()
  let bad = 0
  try {
    for (const id of targets) {
      const ep = loadEpisode(id)
      for (const platform of want) {
        // 知乎/小红书是派生投放平台，episode 里可能只有 publish 没有 platforms 配置：
        // 这种也要能单独重出封面（pack 会校验目标封面存在）。
        if (!ep.platforms[platform] && !ep.publish?.[platform]) continue
        const dir = flags.out ? join(String(flags.out), targets.length > 1 ? id : '') : join(OUT_DIR, id)
        mkdirSync(dir, { recursive: true })
        try {
          await buildCover(browser, ep, platform, join(dir, `${platform}-cover.png`), {
            variant: typeof flags.variant === 'string' ? flags.variant : undefined,
          })
        } catch (e) {
          log(`❌ ${id} · ${platform}：${e.message}`)
          bad++
        }
      }
    }
  } finally {
    await browser.close()
  }
  if (bad) log(`\n❌ ${bad} 张封面装不下，见上面逐条`)
  return bad ? 1 : 0
}

// 发布包重排：不再跑一遍产线，只按 publish 里的平台把母版视频/字幕/时间轴和各自封面
// 拼成 out/<id>/发布-<platform>.md。知乎读 B站母版、小红书读抖音母版；
// cfg 必须按母版平台取，否则知乎/小红书的"规格"行会写出 1920×1080 这种不存在的成片。
// 两趟走：先把每集的平台映射和全部产物校验完，再统一写盘。
// 单趟的话，后一个平台缺文件会留下前几个平台已被覆盖的新发布包，发布队列读到的是半套。
async function cmdPack(ids) {
  const targets = pickEpisodes(ids)
  const batches = []
  for (const id of targets) {
    const ep = loadEpisode(id)
    const distDir = join(OUT_DIR, id)
    const jobs = packJobs(ep, id).map((job) => {
      const videoPath = join(distDir, job.video)
      const srtPath = join(distDir, job.srt)
      const coverPath = join(distDir, job.cover)
      const timelinePath = join(distDir, job.timeline)
      const need = [
        ['母版视频', videoPath],
        ['母版字幕', srtPath],
        ['封面', coverPath],
        ['时间轴', timelinePath],
      ]
      for (const [what, p] of need) {
        if (!existsSync(p)) throw new Error(`${id}/${job.platform}: 缺${what} ${p}——先跑 npm run video:build 与 npm run video:cover`)
      }
      // 时间轴解析、母版 cfg 与场景解析也放在第一趟：坏 JSON 或缺失的母版平台
      // 同样不该等到写了一半发布包才炸出来。
      return {
        ...job,
        videoPath,
        srtPath,
        coverPath,
        timelinePath,
        timeline: JSON.parse(readFileSync(timelinePath, 'utf8')),
        cfg: platformConfig(ep, job.base),
        sceneTexts: resolveScenes(ep, job.base),
      }
    })
    batches.push({ id, ep, distDir, jobs })
  }
  let n = 0
  for (const { id, ep, distDir, jobs } of batches) {
    for (const job of jobs) {
      writeRelease({
        ep,
        platform: job.platform,
        outDir: distDir,
        timeline: job.timeline,
        cfg: job.cfg,
        videoPath: job.videoPath,
        srtPath: job.srtPath,
        coverPath: job.coverPath,
        sceneTexts: job.sceneTexts,
      })
      n++
    }
    log(`✅ ${id}: ${jobs.map((j) => j.platform).join(' / ')} 发布包已更新`)
  }
  log(`\n📦 ${n} 份发布包 → ${OUT_DIR}/<id>/发布-*.md`)
  return 0
}

async function cmdCheck(ids, flags) {
  const want = !flags.platform || flags.platform === 'both' ? ['bilibili', 'douyin'] : [flags.platform]
  const targets = pickEpisodes(ids)
  const browser = await openBrowser()
  let bad = 0
  try {
    for (const id of targets) {
      const ep = loadEpisode(id)
      for (const platform of want) {
        if (!ep.platforms[platform]) continue
        const tlFile = join(OUT_DIR, id, platform, 'timeline.json')
        if (!existsSync(tlFile)) {
          log(`⏭️  ${id} · ${platform} 还没有时间轴，跳过（check 不合成配音）`)
          continue
        }
        const cfg = platformConfig(ep, platform)
        const scenes = resolveScenes(ep, platform)
        const plan = buildRenderPlan(ep, platform, JSON.parse(readFileSync(tlFile, 'utf8')))
        log(`\n🔎 ${id} · ${platform}  ${cfg.size.join('×')}  ${scenes.length} 场`)
        const stage = await openStage(browser, {
          platform,
          size: cfg.size,
          safe: cfg.safe,
          scenes,
          kicker: ep.cover?.kicker || '通往单片机之路',
          badge: ep.badge || id.split('-')[0].toUpperCase(),
          sections: cfg.sections,
          formatVersion: ep.formatVersion ?? 1,
          fps: cfg.fps,
        })
        try {
          await auditLayout(stage, plan)
        } catch (e) {
          bad++
          log(`  ❌ ${e.message.split('\n').slice(0, 12).join('\n')}`)
        } finally {
          await stage.close()
        }
      }
    }
  } finally {
    await browser.close()
  }
  log(bad ? `\n❌ ${bad} 个平台版式未过` : '\n✅ 全部通过')
  return bad ? 1 : 0
}

// ---------------------------------------------------------------- numbers

// 逐集对账：episode 里每个数字都要在 video/research/<id>-numbers.json 有出处。
// 没有 evidence 文件本身就是失败（不是"跳过"），否则新集忘写依据会静默通过。
export async function cmdNumbers(ids, flags = {}) {
  const unknown = Object.keys(flags)
  if (unknown.length) {
    throw new Error(`numbers 不认识参数 ${unknown.map((f) => `--${f}`).join(' ')}（只接受 episode id）`)
  }
  let bad = 0
  for (const id of pickEpisodes(ids)) {
    const ep = loadEpisode(id)
    const p = join(VIDEO_ROOT, 'research', `${id}-numbers.json`)
    if (!existsSync(p)) {
      log(`❌ ${id}: 缺 ${p}`)
      bad++
      continue
    }
    let r
    try {
      r = auditNumbers(ep, JSON.parse(readFileSync(p, 'utf8')))
    } catch (e) {
      log(`❌ ${id}: ${p} 不可用（${e.message}）`)
      bad++
      continue
    }
    if (r.unresolved.length) {
      bad++
      log(`❌ ${id}: ${r.unresolved.length} 个数字未命中`)
      for (const u of r.unresolved.slice(0, 40)) log(`   - ${u.token}  @${u.scene}/${u.field}「${u.text.slice(0, 60)}」`)
    } else log(`✅ ${id}: ${r.tokens.length} 个数字都有依据`)
  }
  return bad ? 1 : 0
}

// ---------------------------------------------------------------- entry

async function main() {
  const { cmd, pos, flags } = parseArgv(process.argv.slice(2))
  mkdirSync(OUT_DIR, { recursive: true })
  if (cmd === 'lint') return cmdLint(pos)
  if (cmd === 'check') return cmdCheck(pos, flags)
  if (cmd === 'cover') return cmdCover(pos, flags)
  if (cmd === 'pack') return cmdPack(pos)
  if (cmd === 'build') return cmdBuild(pos, flags)
  if (cmd === 'numbers') return cmdNumbers(pos, flags)
  if (cmd === 'calib') return runCalibration(flags.anims ? String(flags.anims).split(',') : undefined)
  throw new Error(`未知子命令 "${cmd || '(空)'}"，可用：lint / check / cover / pack / build / numbers / calib`)
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main()
    .then((code) => process.exit(code))
    .catch((err) => {
      console.error(`\n❌ ${err.message}`)
      process.exit(1)
    })
}
