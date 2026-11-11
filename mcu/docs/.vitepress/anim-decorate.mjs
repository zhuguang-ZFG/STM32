import { readFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

// 构建期把 docs/public/anim/*.svg 原文注入页面（见 config.mts 的 image 规则）。
// 之所以内联而不是 <img src>：<img> 引的 SVG 是独立文档，站点的深浅主题（html.dark）
// 与 CSS 变量传不进去，动画会永远停在硬编码的浅色版。
// 之所以在构建期内联而不是运行时虚拟模块：虚拟模块会把全部动画塞进共享的 theme chunk，
// 每多一张图所有页面都跟着变重；内联进页面 chunk 则每页只带自己用到的那几张。

const ANIM_DIR = join(dirname(fileURLToPath(import.meta.url)), '..', 'public', 'anim')
const cache = new Map()

// 导出给 scripts/anim-lint.mjs：色板只有一份，检查工具和换色逻辑必须同源。
export const FILL_CLASS = {
  '#f6f8fa': 'a-bg',
  '#ffffff': 'a-card',
  '#fff': 'a-card',
  '#f8fafc': 'a-panel',
  '#f1f5f9': 'a-panel',
  '#e2e8f0': 'a-line',
  '#d0d7de': 'a-line',
  '#cbd5e1': 'a-line',
  '#dbe7ff': 'a-wash-blue',
  '#eef2ff': 'a-wash-blue',
  '#dbeafe': 'a-wash-blue',
  '#d8f3e5': 'a-wash-green',
  '#eef7f1': 'a-wash-green',
  '#dcfce7': 'a-wash-green',
  '#fdf0d5': 'a-wash-amber',
  '#fef3c7': 'a-wash-amber',
  '#fff7ed': 'a-wash-amber',
  '#3451b2': 'a-brand',
  '#3eaf7c': 'a-accent',
  '#1a7f56': 'a-accent-deep',
  '#166534': 'a-accent-deep',
  '#d97706': 'a-warn',
  '#92400e': 'a-warn-deep',
  '#a16207': 'a-warn-deep',
  '#e7c54b': 'a-gold',
  '#dc2626': 'a-danger',
  '#cf222e': 'a-danger',
  '#333': 'a-ink',
  '#24292f': 'a-ink',
  '#666': 'a-sub',
  '#57606a': 'a-sub',
  '#64748b': 'a-sub',
  '#888': 'a-muted',
  '#aaa': 'a-muted',
  '#94a3b8': 'a-muted',
  '#9ea7b3': 'a-muted',
}

export const STROKE_CLASS = {
  '#3451b2': 's-brand',
  '#3eaf7c': 's-accent',
  '#1a7f56': 's-accent-deep',
  '#d97706': 's-warn',
  '#dc2626': 's-danger',
  '#cf222e': 's-danger',
  '#ffffff': 's-card',
  '#fff': 's-card',
  '#cbd5e1': 's-line',
  '#d0d7de': 's-line',
  '#e2e8f0': 's-line',
  '#94a3b8': 's-muted',
  '#666': 's-sub',
  '#57606a': 's-sub',
  '#888': 's-sub',
  '#333': 's-ink',
}

const SHAPE_TAGS = 'rect|line|path|text|circle|polygon|polyline|ellipse|g'

function addClass(attrs, cls) {
  const m = attrs.match(/\bclass="([^"]*)"/)
  if (m) {
    if (m[1].split(/\s+/).includes(cls)) return attrs
    return attrs.replace(/\bclass="[^"]*"/, `class="${(m[1] + ' ' + cls).trim()}"`)
  }
  return ` class="${cls}"${attrs}`
}

export function readAnim(name) {
  if (!cache.has(name)) cache.set(name, readFileSync(join(ANIM_DIR, `${name}.svg`), 'utf8'))
  return cache.get(name)
}

// 一张图里 dur 不止一个：阶段组的 dur 是主时间轴，脉冲/爬线另有自己的短 dur。
// "一轮"要取最长者——与 scripts/anim-lint.mjs 的主时长口径（Math.max）一致。
// 取首个匹配会把 12s 主轴读成 1.5s：标签、进度条周期，以及"减少动效"的静止帧
// （setCurrentTime(dur*0.9)）全跟着错，静止帧会停在第①阶段而不是结论帧。
export function animDuration(raw) {
  const durs = [...raw.matchAll(/dur="([\d.]+)s"/g)].map((m) => Number(m[1]))
  return durs.length ? String(Math.max(...durs)) : ''
}

export function decorateAnim(raw, slug) {
  // 同一页可能内联多张图：marker/gradient 的 id 必须打命名空间，
  // 否则 url(#arrR) 会抓到前一张图定义的那个箭头。
  const prefix = `af-${slug}-`
  const ids = new Set([...raw.matchAll(/\sid="([^"]+)"/g)].map((m) => m[1]))
  let src = raw
  for (const id of ids) {
    src = src
      .split(`id="${id}"`).join(`id="${prefix}${id}"`)
      .split(`url(#${id})`).join(`url(#${prefix}${id})`)
      .split(`href="#${id}"`).join(`href="#${prefix}${id}"`)
  }

  // 保留自闭合斜杠：SVG 走 HTML 解析器，`<rect/>` 少一个 `/` 会把后面的兄弟节点全吞成子节点。
  return src.replace(new RegExp(`<(${SHAPE_TAGS})\\b([^>]*?)(/?)>`, 'g'), (tag, name, attrs, slash) => {
    let next = attrs
    const fill = next.match(/\bfill="([^"]+)"/)
    if (fill && FILL_CLASS[fill[1].toLowerCase()]) next = addClass(next, FILL_CLASS[fill[1].toLowerCase()])
    const stroke = next.match(/\bstroke="([^"]+)"/)
    if (stroke && STROKE_CLASS[stroke[1].toLowerCase()]) next = addClass(next, STROKE_CLASS[stroke[1].toLowerCase()])
    if (/\bfont-family="[^"]*(Consolas|monospace)[^"]*"/i.test(next)) next = addClass(next, 'a-mono')
    return `<${name}${next}${slash}>`
  })
}
