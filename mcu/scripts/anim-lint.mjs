#!/usr/bin/env node
// 动画自检：把 docs/public/anim/*.svg 的规范条款变成可执行的检查。
// 为什么需要：SMIL 的坑肉眼看不出来（最后一个阶段值写成 values="0;0;0;0;1" 就永远不显示、
// 自造十六进制色在深色模式下是白块、连续动画 dur 不整除主 dur 会在回环处跳帧），
// 而这些都要等到人眼盯截图才能发现。用法：node scripts/anim-lint.mjs [文件…]
import { readFileSync, readdirSync } from 'node:fs'
import { basename, join } from 'node:path'
import { FILL_CLASS, STROKE_CLASS } from '../docs/.vitepress/anim-decorate.mjs'

const DIR = 'docs/public/anim'
const files = process.argv.slice(2).length
  ? process.argv.slice(2)
  : readdirSync(DIR).filter((f) => f.endsWith('.svg')).map((f) => join(DIR, f))

const VOID = new Set(['animate', 'animateTransform', 'animateMotion', 'set', 'circle', 'rect', 'line', 'path', 'polygon', 'polyline', 'ellipse', 'use', 'stop'])

// §4「必须有在跑的东西」：只有会改变位置/形状的属性才算运动，
// opacity 的 discrete 阶段切换是幻灯片，不是动画。
const MOTION_ATTR = new Set([
  'x', 'y', 'x1', 'x2', 'y1', 'y2', 'cx', 'cy', 'r', 'rx', 'ry',
  'width', 'height', 'd', 'points', 'stroke-dashoffset', 'stroke-dasharray'
])

function checkTags(src) {
  const stack = []
  const errs = []
  const re = /<!--[\s\S]*?-->|<\/([A-Za-z][\w:-]*)\s*>|<([A-Za-z][\w:-]*)((?:"[^"]*"|'[^']*'|[^'">])*)>/g
  let m
  while ((m = re.exec(src))) {
    if (m[0].startsWith('<!--')) continue
    if (m[1]) {
      const top = stack.pop()
      if (top !== m[1]) errs.push(`</${m[1]}> 处标签不配对（栈顶是 ${top ?? '空'}）`)
    } else if (!m[3]?.trim().endsWith('/')) {
      stack.push(m[2])
    }
  }
  for (const t of stack) if (!VOID.has(t)) errs.push(`<${t}> 没有闭合`)
  return errs
}

function keyTimesOf(v) {
  return v.split(';').map((x) => parseFloat(x.trim()))
}

function lint(file) {
  const src = readFileSync(file, 'utf8')
  const name = basename(file, '.svg')
  const out = []
  const add = (msg) => out.push(msg)

  checkTags(src).forEach(add)

  const vb = /viewBox="0 0 (\d+) (\d+)"/.exec(src)
  if (!vb) add('缺 viewBox')
  else if (+vb[1] !== 720) add(`viewBox 宽 ${vb[1]}，规范是 720`)
  const H = vb ? +vb[2] : 0

  if (!/<title>/.test(src)) add('缺 <title>')
  if (!/<desc>/.test(src)) add('缺 <desc>')

  // 色板：站点靠映射表换主题 class，映射不到的色在深色模式里保持硬编码
  for (const m of src.matchAll(/\b(fill|stroke)="([^"]+)"/g)) {
    const val = m[2].toLowerCase()
    if (val === 'none' || val.startsWith('url(')) continue
    const map = m[1] === 'fill' ? FILL_CLASS : STROKE_CLASS
    if (!map[val]) add(`${m[1]}="${m[2]}" 不在主题映射表里（深色模式会漏）`)
  }
  if (/rgba\(/.test(src)) add('出现 rgba() 底纹：换成色板里的 wash 或先补映射表')

  // <animate attributeName="fill|stroke"> 的颜色不过映射表路径，同样得在色板里
  for (const m of src.matchAll(/<animate\b[^>]*attributeName="(fill|stroke)"[^>]*/g)) {
    const map = m[1] === 'fill' ? FILL_CLASS : STROKE_CLASS
    const vals = /values="([^"]*)"/.exec(m[0])?.[1]?.split(';') ??
      [/from="([^"]*)"/.exec(m[0])?.[1], /to="([^"]*)"/.exec(m[0])?.[1]].filter(Boolean)
    for (const v of vals) {
      const val = v.trim().toLowerCase()
      if (!val || val === 'none' || val.startsWith('url(')) continue
      if (!map[val]) add(`${m[1]} 动画值 "${v}" 不在主题映射表里（深色模式会漏）`)
    }
  }

  // 主时间轴
  const durs = [...src.matchAll(/dur="([\d.]+)s"/g)].map((m) => +m[1])
  const master = Math.max(...durs)

  let moving = 0
  for (const m of src.matchAll(/<animate\b([^>]*)/g)) {
    const attrs = m[1]
    const get = (k) => new RegExp(`${k}="([^"]*)"`).exec(attrs)?.[1]
    const values = get('values')
    const kt = get('keyTimes')
    const dur = get('dur')
    const attr = get('attributeName')
    if (!dur) { add(`${attr ?? '?'} 的 <animate> 没有 dur`); continue }
    const d = parseFloat(dur)
    if (get('calcMode') === 'discrete' && values && kt) {
      const vs = values.split(';')
      const ts = keyTimesOf(kt)
      if (vs.length !== ts.length) add(`${attr} discrete 动画 values(${vs.length}) 与 keyTimes(${ts.length}) 数量不等`)
      if (ts[0] !== 0 || ts[ts.length - 1] !== 1) add(`${attr} 的 keyTimes 必须首 0 尾 1`)
      for (let i = 1; i < ts.length; i++) if (ts[i] <= ts[i - 1]) add(`${attr} 的 keyTimes 必须严格递增`)
      // discrete 语义：值 i 生效于 [kt[i], kt[i+1])，末值只在回环瞬间出现一次
      const lit = vs.map((v, i) => [parseFloat(v), i]).filter(([v]) => v > 0.5)
      if (lit.length === 1 && lit[0][1] === vs.length - 1) {
        add(`${attr} 的高亮值只落在末槽（keyTimes=${kt}）→ 这一阶段永远看不见`)
      }
    }
    // 连续动画要能在主循环里整数次跑完，否则回环处肉眼可见地跳
    const steps = values ? values.split(';').length : 0
    const isContinuous = get('calcMode') !== 'discrete'
    if (attr && MOTION_ATTR.has(attr) && isContinuous && steps >= 2) moving++
    // 节拍脉冲（§4 第三件武器）：比主时间轴短的独立循环，也是一处在跑的东西
    if (attr === 'opacity' && isContinuous && master && d < master &&
        get('repeatCount') === 'indefinite') moving++
    const continuous = isContinuous && values && steps >= 2
    if (continuous && master && d < master && Math.abs(master / d - Math.round(master / d)) > 1e-9) {
      add(`${attr} 连续动画 dur=${d}s 不整除主 dur=${master}s，回环处会跳帧`)
    }
  }

  for (const m of src.matchAll(/<animateTransform\b([^>]*)/g)) {
    if (/calcMode="discrete"/.test(m[1])) continue
    if (!/values="[^"]*;[^"]*"/.test(m[1])) continue
    moving++
  }

  if (!moving) add('没有任何连续位移动画（§4：只有阶段切换 = 幻灯片，不算动画）')

  // 有阶段字幕就该有阶段指示点；点位不许跑出画布
  const dots = (src.match(/<circle[^>]*r="5"/g) || []).length
  const hasCaptions = /<g font-size="13" font-weight="bold" fill="#3451b2">/.test(src)
  if (hasCaptions && !dots) add('有阶段字幕却没有阶段指示点')
  if (dots) {
    const dy = /<g transform="translate\((\d+),(\d+)"[^>]*fill="#3451b2">/.exec(src)
    if (dy) {
      const x = +dy[1]
      const y = +dy[2]
      if (x + (dots - 1) * 18 > 710) add(`指示点起点 x=${x} 配 ${dots} 个点会超出右边界`)
      if (y > H - 4) add(`指示点 y=${y} 已越过画布底边 ${H}`)
    }
  }
  return out
}

// 总览页收录校验：新图忘了登记 docs/animations.md 时，build 只查"死链"不查
// "漏链"，任何既有门禁都拦不住——总览页悄悄缺一张，直到有人肉眼发现。
const gallery = readFileSync('docs/animations.md', 'utf8')

let bad = 0
for (const f of files) {
  const errs = lint(f)
  const name = basename(f, '.svg')
  if (!gallery.includes(`/anim/${name}.svg`)) {
    errs.push(`未收录进 docs/animations.md——新图必须登记总览页`)
  }
  if (!errs.length) continue
  bad++
  console.log(`\n${f}`)
  for (const e of [...new Set(errs)]) console.log(`  · ${e}`)
}
console.log(bad ? `\n${bad}/${files.length} 张图待修` : `\n${files.length} 张图全部通过`)
process.exit(bad ? 1 : 0)
