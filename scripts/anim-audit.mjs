#!/usr/bin/env node
// 动画版式审计（命令行版）：出界 / 压字 / 光点压字 / 动色块啃半截字 / 整幅无可见文字。
// 判定逻辑与 scripts/anim-audit.html 同源（墨水盒而非 em 盒，见 animation.md §7），
// 区别是：① 用 Playwright 无头跑，可进门禁；② 清单直接扫 docs/public/anim/，不再手维护 LIST；
// ③ 除阶段中点外再按 --step 等距加采样点——阶段中点抓不到"渐显过程中两行短暂相叠"。
//
//   node scripts/anim-audit.mjs                 # 全量
//   node scripts/anim-audit.mjs context-switch  # 只审指定图（可多个）
//   node scripts/anim-audit.mjs --step 0.5      # 额外每 0.5s 采样一次（默认 1s；0 关闭）
//   node scripts/anim-audit.mjs --font-scale 1.08  # 模拟更宽的回退字体（本地复现 CI 的 Linux 字体度量）
//   node scripts/anim-audit.mjs --json          # 机器可读输出
//   node scripts/anim-audit.mjs --dots          # 列出"压在文字上"的明细：光点压字 / 动色块啃半截字（默认只给个数，不计失败）
//   node scripts/anim-audit.mjs --dir docs/public/images/labs  # 审静态示意图目录（同一套出界/压字规则）
//
// 为什么需要 --font-scale：图里写的是 'Segoe UI','Microsoft YaHei' 字栈，Windows 本地用雅黑，
// CI 的 ubuntu-24.04 上没有雅黑，Chromium 退回 Noto Sans CJK——同一串中文宽约 5~8%。
// 于是"本地全绿、CI 报 8 张出界"成了常态，且本地无从复现。这个开关按倍率放大文字的墨水盒
// （宽度绕水平中心、竖向绕基线），把 CI 的字体度量搬到本地来。
import { readdirSync, readFileSync } from 'node:fs'
import { resolve, basename } from 'node:path'
import { chromium } from '@playwright/test'

const args = process.argv.slice(2)
const flag = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d }
const step = Number(flag('--step', '1'))
const fontScale = Number(flag('--font-scale', '1'))
const asJson = args.includes('--json')
const showDots = args.includes('--dots')
const valued = ['--step', '--font-scale', '--dir']
const picked = args.filter((a, i) => !a.startsWith('--') && !valued.includes(args[i - 1]))

const dir = resolve(flag('--dir', 'docs/public/anim'))
const names = (picked.length ? picked : readdirSync(dir).filter(f => f.endsWith('.svg')).map(f => basename(f, '.svg'))).sort()

// 在页面里执行的审计函数：输入 svg 文本，返回问题列表
function auditInPage({ svgText, step, fontScale }) {
  const EPS = 0.5
  const box = document.createElement('div')
  box.style.cssText = 'position:fixed;left:0;top:0'
  box.innerHTML = svgText
  document.body.appendChild(box)
  const svg = box.querySelector('svg')
  const vb = svg.getAttribute('viewBox').split(/\s+/).map(Number)
  const W = vb[2], H = vb[3]
  svg.setAttribute('width', W); svg.setAttribute('height', H)
  void svg.getBoundingClientRect()
  const durs = [...svg.querySelectorAll('animate,animateTransform,animateMotion')]
    .map(a => parseFloat(a.getAttribute('dur'))).filter(n => !isNaN(n))
  const master = durs.length ? Math.max(...durs) : 0   // 静态示意图无 dur：只审 t=0 这一帧
  const rect0 = svg.getBoundingClientRect()
  const mctx = document.createElement('canvas').getContext('2d')

  const opacityOf = el => { let p = el, acc = 1; while (p && p.nodeType === 1) { acc *= parseFloat(getComputedStyle(p).opacity); p = p.parentElement } return acc }
  const boxOf = el => {
    const r = el.getBoundingClientRect()
    const out = { x: r.x - rect0.x, y: r.y - rect0.y, w: r.width, h: r.height }
    let baseline = null
    if (el.tagName === 'text') {
      try {
        const st = getComputedStyle(el)
        mctx.font = `${st.fontStyle} ${st.fontWeight} ${st.fontSize} ${st.fontFamily}`
        const m = mctx.measureText(el.textContent)
        const k = r.height / (m.fontBoundingBoxAscent + m.fontBoundingBoxDescent)
        baseline = out.y + m.fontBoundingBoxAscent * k
        out.iy0 = baseline - m.actualBoundingBoxAscent * k
        out.iy1 = baseline + m.actualBoundingBoxDescent * k
      } catch { /* 退回 em 盒 */ }
    }
    out.iy0 = out.iy0 ?? out.y; out.iy1 = out.iy1 ?? out.y + out.h
    if (fontScale !== 1 && el.tagName === 'text') {
      // 只放大字宽（绕锚点）：Linux 回退字体与雅黑的差异主要在字宽，
      // 竖向墨迹高度几乎不变——放大竖向会造出 CI 上不存在的压字。
      const anchor = getComputedStyle(el).textAnchor
      const ax = anchor === 'middle' ? out.x + out.w / 2 : anchor === 'end' ? out.x + out.w : out.x
      out.w *= fontScale; out.x = anchor === 'middle' ? ax - out.w / 2 : anchor === 'end' ? ax - out.w : ax
    }
    return out
  }
  const ts = new Set([master * 0.02, master * 0.9])
  for (const a of svg.querySelectorAll('animate')) {
    if (a.getAttribute('calcMode') !== 'discrete') continue
    const kt = (a.getAttribute('keyTimes') || '').split(';').map(Number).filter(n => !isNaN(n))
    for (let i = 0; i + 1 < kt.length; i++) ts.add(master * (kt[i] + kt[i + 1]) / 2)
  }
  if (step > 0) for (let t = step; t < master; t += step) ts.add(t)
  const times = master ? [...ts].filter(t => t >= 0 && t <= master).sort((a, b) => a - b) : [0]

  // 会动的图元：光点、方块、游标。原来只查 text×text，"光点正好落在标签文字上"
  // 这类一个都抓不到——why-rtos 的 led/uart 两条就是这么漏的（点本身不动，
  // 只闪透明度，位置从 t=0 一直压到 t=master）。
  const tokens = [...svg.querySelectorAll('circle,rect,ellipse')].filter((el) => {
    const host = el.parentElement && el.parentElement.tagName === 'g' ? el.parentElement : el
    return host.querySelector('animate,animateTransform,animateMotion')
  })
  // 文档序即 z 序：序号小的先画、在下面。
  const zOf = new Map([...svg.querySelectorAll('*')].map((el, i) => [el, i]))
  const eaters = [...svg.querySelectorAll('rect,path')].filter((el) => {
    const host = el.parentElement && el.parentElement.tagName === 'g' ? el.parentElement : el
    if (!host.querySelector('animate,animateTransform,animateMotion')) return false
    const cs = getComputedStyle(el)
    if (!cs.fill || cs.fill === 'none') return false
    return parseFloat(cs.fillOpacity) > 0.5
  })
  const problems = new Map()
  const push = (key, t, detail) => { if (!problems.has(key)) problems.set(key, { detail, ts: [] }); problems.get(key).ts.push(+t.toFixed(2)) }
  // 光点压字单独一档，不计入失败：这批图里"光标块盖住字符""标记点压在节点名上"
  // 是有意的画法，全量跑下来 101 张里 30 张命中，当门槛就把门禁打废了。
  // 所以它只出现在提示里，供人挑真错（why-rtos 的 led/uart 就是靠它挑出来的）。
  const notices = new Map()
  const note = (key, t, detail) => { if (!notices.has(key)) notices.set(key, { detail, ts: [] }); notices.get(key).ts.push(+t.toFixed(2)) }
  for (const t of times) {
    svg.setCurrentTime(t)
    const vis = [...svg.querySelectorAll('text')].filter(el => opacityOf(el) > 0.05 && el.textContent.trim() && el.getBoundingClientRect().width > 0)
    if (!vis.length) push('blank', t, '整幅无可见文字')
    const boxes = vis.map(el => ({ el, z: zOf.get(el) ?? 0, b: boxOf(el), s: el.textContent.trim().slice(0, 16) }))
    for (const { b, s } of boxes) {
      if (b.x < -EPS || b.y < -EPS || b.x + b.w > W + EPS || b.y + b.h > H + EPS)
        push('out|' + s, t, `出界「${s}」box=${Math.round(b.x)},${Math.round(b.y)},${Math.round(b.w)}x${Math.round(b.h)}`)
    }
    for (let i = 0; i < boxes.length; i++) for (let j = i + 1; j < boxes.length; j++) {
      if (boxes[i].s === boxes[j].s) continue
      const a = boxes[i].b, c = boxes[j].b
      const ox = Math.min(a.x + a.w, c.x + c.w) - Math.max(a.x, c.x)
      const oy = Math.min(a.iy1, c.iy1) - Math.max(a.iy0, c.iy0)
      if (ox > 3 && oy > 1)
        push('hit|' + boxes[i].s + '|' + boxes[j].s, t, `压字「${boxes[i].s}」×「${boxes[j].s}」横向 ${Math.round(ox)}px、竖向墨水重叠 ${oy.toFixed(1)}px`)
    }
    for (const tk of tokens) {
      const tb = boxOf(tk)
      // 30 用户单位以内才算"点"：大色块本来就该铺在文字底下，拿它报压字全是噪声
      if (tb.w > 30 || tb.h > 30 || opacityOf(tk) <= 0.05) continue
      for (const { b, s } of boxes) {
        const dx = Math.min(tb.x + tb.w, b.x + b.w) - Math.max(tb.x, b.x)
        const dy = Math.min(tb.y + tb.h, b.y + b.h) - Math.max(tb.y, b.y)
        if (dx > 2 && dy > 2)
          note(`dot|${s}|${tk.tagName}`, t, `${tk.tagName} 压在「${s}」上 横向 ${Math.round(dx)}px、竖向 ${Math.round(dy)}px`)
      }
    }
    // 会动的不透明色块啃掉半截字。text×text 查不到这一类：字没跟字重叠，
    // 是压栈块/进度条这类"盖在上面"的图元把字的墨水削掉了一半。
    // 文档序就是 z 序，所以只有"字先画、块后画"才会真被盖住——反过来的
    // 那种是刻意的底衬，报出来全是噪声。
    for (const rk of eaters) {
      // 只看真正能盖住墨水的：fill-opacity × 各级 opacity 才是落笔的浓度。
      // i2c-timing 那道 0.10 的阶段聚光带就是这么被误判成"啃字"的——它是底纹，
      // 字压在下面照样读。fillOpacity 在筛选时就查过了，这里补上随时间走的 opacity。
      if (opacityOf(rk) * parseFloat(getComputedStyle(rk).fillOpacity) <= 0.5) continue
      const rb = boxOf(rk)
      const rz = zOf.get(rk)
      for (const { b, s, el, z } of boxes) {
        // 块必须画在字之后才盖得住字；反过来是刻意的底衬，报出来全是噪声
        if (rz < z) continue
        const dx = Math.min(rb.x + rb.w, b.x + b.w) - Math.max(rb.x, b.x)
        const dy = Math.min(rb.y + rb.h, b.iy1) - Math.max(rb.y, b.iy0)
        if (dx <= 1 || dy <= 1) continue
        const cover = (dx * dy) / (b.w * Math.max(1, b.iy1 - b.iy0))
        // 同一句字画了两遍（底层常驻一份、各阶段再各自一份，坐标完全一样）时，
        // 块盖住的是那份被压在下面的副本，上面还有一份照读——software-timer-service
        // 的「执行回调（串行）」就是这么报出来的。
        if (boxes.some((o) => o.z > rz && o.el !== el && o.s === s
          && Math.abs(o.b.x - b.x) < 2 && Math.abs(o.b.y - b.y) < 2 && Math.abs(o.b.w - b.w) < 2)) continue
        // 只报"啃掉一角"：整条盖住多半是渐显时序，啃一角才是肉眼看得见的残字
        if (cover > 0.12 && cover < 0.9)
          note(`eat|${s}`, t, `动色块盖掉「${s}」约 ${Math.round(cover * 100)}%（${rk.tagName}）`)
      }
    }
  }
  box.remove()
  return { W, H, master, samples: times.length, problems: [...problems.values()], notices: [...notices.values()] }
}

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1400, height: 1000 } })
await page.setContent('<!doctype html><html lang="zh-CN"><body style="margin:0"></body></html>')
const report = []
for (const name of names) {
  const svgText = readFileSync(resolve(dir, name + '.svg'), 'utf8')
  try {
    const r = await page.evaluate(auditInPage, { svgText, step, fontScale })
    report.push({ name, ...r })
  } catch (e) {
    report.push({ name, error: String(e), problems: [{ detail: '异常 ' + e, ts: [] }] })
  }
}
await browser.close()

const bad = report.filter(r => r.problems.length)
if (asJson) {
  console.log(JSON.stringify(report, null, 2))
} else {
  for (const r of report) {
    if (!r.problems.length) continue
    console.log(`✗ ${r.name}（${r.W}x${r.H}，${r.master}s，采样 ${r.samples} 点）`)
    for (const p of r.problems) {
      const t = p.ts.length === 1 ? `${p.ts[0]}s` : `共 ${p.ts.length} 个时刻，${p.ts.slice(0, 4).join('/')}s…`
      console.log(`    ${p.detail}（${t}）`)
    }
  }
  console.log(bad.length ? `\n${report.length} 张审完，${bad.length} 张有版式问题` : `✓ ${report.length} 张动画版式审计通过（出界 / 压字 / 空幅）`)
  const dotted = report.filter((r) => r.notices?.length)
  if (showDots) {
    for (const r of dotted) {
      console.log(`· ${r.name}`)
      for (const n of r.notices) {
        const t = n.ts.length === 1 ? `${n.ts[0]}s` : `共 ${n.ts.length} 个时刻，${n.ts.slice(0, 4).join('/')}s…`
        console.log(`    ${n.detail}（${t}）`)
      }
    }
  } else if (dotted.length) {
    console.log(`（另有 ${dotted.length} 张图有"盖在文字上"的痕迹：光点压字多半是有意的光标画法，动色块啃掉半截字多半是真错，--dots 看明细；两类都不计失败）`)
  }
}
process.exit(bad.length ? 1 : 0)
