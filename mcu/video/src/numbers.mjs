// 上屏/口播数字审计：episode 里每个数字都必须能在 research/<id>-numbers.json
// 找到依据（或显式列进 exceptions）。CLI 的 numbers 命令靠它把"没出处的数字"拦在成片之前。

import { resolveScenes } from './spec.mjs'

// 只收真正会在画面或发布文案里出现的字段。topics/tags/notes 是平台元数据
// （日期、话题编号等），不算对观众的数值主张。
const SCENE_FIELDS = ['title', 'sub', 'note', 'kicker', 'code', 'codeB', 'codeLabel', 'narration']
const COVER_FIELDS = ['line1', 'line2', 'num', 'numNote', 'proof', 'proofShort']
const PUBLISH_FIELDS = ['caption', 'pinned', 'repro', 'title', 'body', 'intro']
const PLATFORMS = ['bilibili', 'douyin']

// 全角数字/逗号/句号、全角空格与 Unicode 减号先归一化，否则 `１６８０`、
// `1，680`、`−14 dB` 会整段漏审。
function normalizeText(value) {
  return String(value)
    .replace(/[０-９]/g, (d) => String.fromCharCode(d.charCodeAt(0) - 0xfee0))
    .replace(/，/g, ',')
    .replace(/．/g, '.')
    .replace(/\u3000/g, ' ')
    .replace(/\u2212/g, '-')
}

// C 整数字面量后缀：0x...UL/ull 之类。没有这截 suffix，末尾 \b 会失配，
// 十进制扫描再把开头的 0 当成独立 token，evidence 里写 0 就假通过。
const HEX_RE = /(?<![0-9A-Za-z_])0[xX][0-9a-fA-F_]+(?:[uUlL]{1,3})?\b/g
const BIN_RE = /(?<![0-9A-Za-z_])0[bB][01_]+(?:[uUlL]{1,3})?\b/g
const OCT_RE = /(?<![0-9A-Za-z_])0[oO][0-7_]+(?:[uUlL]{1,3})?\b/g

// 单位大小写不敏感：514 MS 与 514 ms 是同一个数。长单位排在短单位前面，
// 单位后必须是非字母，保证 `3.3 seconds` 只取 3.3，而 `3.3 s` 取 3.3s。
const UNITS = [
  'KiB', 'MiB', 'GiB', 'kbps', 'Mbps', 'GHz', 'MHz', 'kHz', 'mAh', 'dBm',
  'kΩ', 'MΩ', 'ms', 'us', 'µs', 'ns', 'Hz', 'mA', 'µA', 'dB', 'ppm',
  'KB', 'MB', 'GB', 'mV', 'mW', 'fps', '°C', 's', 'A', 'V', 'W', 'Ω', '%',
]
const UNIT_PATTERN = `(?:${UNITS.join('|')})(?![A-Za-z])`

// 符号只在前面不是字母/数字/下划线时并入 token：`-14 dB` → -14db，
// 但 `12-14` 必须拆成 12 和 14。指数里的符号由 [eE][+-]?\d+ 单独承接。
const DECIMAL_RE = new RegExp(
  `(?<![0-9A-Za-z_])[+\\-]?\\d+(?:_\\d+)*(?:[.,]\\d+)*(?:[eE][+\\-]?\\d+)?` +
    `(?:\\s*${UNIT_PATTERN})?`,
  'gi',
)

export function flattenEpisode(ep) {
  const out = []
  const push = (scene, field, text) => {
    if (typeof text === 'string' && text.trim()) out.push({ scene, field, text })
  }
  for (const p of Object.keys(ep.platforms || {})) {
    if (!PLATFORMS.includes(p)) continue
    for (const sc of resolveScenes(ep, p)) {
      for (const f of SCENE_FIELDS) push(`${p}:${sc.id}`, f, sc[f])
      ;(sc.bullets || []).forEach((b, i) => push(`${p}:${sc.id}`, `bullets[${i}]`, b))
    }
  }
  const cover = (scene, c) => {
    if (!c || typeof c !== 'object') return
    for (const f of COVER_FIELDS) push(scene, f, c[f])
    if (c.vs) for (const f of ['left', 'right']) push(scene, `vs.${f}`, c.vs[f])
  }
  cover('cover', ep.cover)
  // 平台可以整份替换封面（package.mjs 里 `cfg.cover ?? ep.cover`），
  // 抖音那版可能写着与主封面不同的数字，必须单独审。
  for (const p of PLATFORMS) cover(`cover.${p}`, ep.platforms?.[p]?.cover)
  for (const [p, pub] of Object.entries(ep.publish || {})) {
    if (!pub || typeof pub !== 'object') continue
    for (const f of PUBLISH_FIELDS) push(`publish.${p}`, f, pub[f])
    ;(pub.titles || []).forEach((t, i) => push(`publish.${p}`, `titles[${i}]`, t))
  }
  return out
}

function canonHex(raw) {
  const digits = normalizeText(raw)
    .replace(/^0[xX]/, '')
    .replace(/[uUlL]{1,3}$/, '')
    .replace(/[_\s]/g, '')
  if (!/^[0-9a-fA-F]+$/.test(digits)) return null
  return '0x' + BigInt(`0x${digits}`).toString(16)
}

function canonBin(raw) {
  const digits = normalizeText(raw)
    .replace(/^0[bB]/, '')
    .replace(/[uUlL]{1,3}$/, '')
    .replace(/[_\s]/g, '')
  if (!/^[01]+$/.test(digits)) return null
  return '0b' + BigInt(`0b${digits}`).toString(2)
}

function canonOct(raw) {
  const digits = normalizeText(raw)
    .replace(/^0[oO]/, '')
    .replace(/[uUlL]{1,3}$/, '')
    .replace(/[_\s]/g, '')
  if (!/^[0-7]+$/.test(digits)) return null
  return '0o' + BigInt(`0o${digits}`).toString(8)
}

// 数字去逗号/下划线/空白并小写单位：1,680,000 → 1680000，514 MS → 514ms。
function canonNum(s) {
  return normalizeText(s).replace(/[,_\s]/g, '').toLowerCase()
}

export function extractTokens(text) {
  const out = new Set()
  // 先摘掉 hex/bin/oct 再扫十进制：否则 0x4002 的开头 0 会被当成一个独立的
  // 数字 token（带 C 后缀时旧正则会整段失配，只漏出那个 0）。遮罩等长空格，
  // 偏移不变，最后按出现位置排序，混合写法也保持原文顺序。
  let rest = normalizeText(text)
  const hits = []
  for (const [re, canon] of [
    [HEX_RE, canonHex],
    [BIN_RE, canonBin],
    [OCT_RE, canonOct],
  ]) {
    rest = rest.replace(re, (m, offset) => {
      const token = canon(m)
      if (token) hits.push({ index: offset, token })
      return ' '.repeat(m.length)
    })
  }
  for (const m of rest.matchAll(DECIMAL_RE)) {
    hits.push({ index: m.index, token: canonNum(m[0]) })
  }
  hits.sort((a, b) => a.index - b.index)
  for (const hit of hits) out.add(hit.token)
  return [...out]
}

function isPlainObject(v) {
  return v !== null && typeof v === 'object' && !Array.isArray(v)
}

function checkShape(doc) {
  if (!isPlainObject(doc)) throw new Error('numbers JSON 不是对象')
  if (!('evidence' in doc)) throw new Error('numbers JSON 缺 evidence')
  if (!isPlainObject(doc.evidence)) throw new Error('numbers JSON 的 evidence 不是对象')
  if (doc.exceptions !== undefined && !isPlainObject(doc.exceptions)) {
    throw new Error('numbers JSON 的 exceptions 不是对象')
  }
  for (const field of ['evidence', 'exceptions']) {
    for (const [k, v] of Object.entries(doc[field] || {})) {
      if (typeof v !== 'string') throw new Error(`numbers JSON 的 ${field}["${k}"] 不是字符串`)
    }
  }
}

export function auditNumbers(ep, doc) {
  checkShape(doc)
  // evidence 与 exceptions 都算"有依据"：前者指向出处，后者解释为什么可以放行。
  // 键不再整体 canonKey，而是抽出其中所有数字 token，`2026-10-17` 这类复合键
  // 才能和上屏文本里的 2026/10/17 对称命中。
  const known = new Set()
  for (const key of [...Object.keys(doc.evidence), ...Object.keys(doc.exceptions || {})]) {
    for (const token of extractTokens(key)) known.add(token)
  }
  const tokens = []
  const seen = new Set()
  const resolved = []
  const unresolved = []
  for (const row of flattenEpisode(ep)) {
    for (const token of extractTokens(row.text)) {
      if (!seen.has(token)) {
        seen.add(token)
        tokens.push(token)
      }
      const hit = { token, scene: row.scene, field: row.field, text: row.text }
      ;(known.has(token) ? resolved : unresolved).push(hit)
    }
  }
  return { tokens, resolved, unresolved }
}
