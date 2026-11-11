import { parse } from 'yaml'
import fs from 'node:fs'
import path from 'node:path'

export function readMetadata(text, label = '章节') {
  const match = text.replace(/^\uFEFF/, '').match(/^---\r?\n([\s\S]*?)\r?\n---/)
  const fm = match ? parse(match[1]) : null
  if (!fm || typeof fm !== 'object' || Array.isArray(fm)) throw new Error(`${label}: 缺少 frontmatter`)
  if (typeof fm.title !== 'string' || !fm.title.trim()) throw new Error(`${label}: title 必须为非空字符串`)
  if (!['done', 'building'].includes(fm.status)) throw new Error(`${label}: status 必须为 done/building`)
  if (![1, 2, 3].includes(fm.difficulty)) throw new Error(`${label}: difficulty 必须为 1/2/3`)
  if (!Number.isSafeInteger(fm.minutes) || fm.minutes <= 0) throw new Error(`${label}: minutes 必须为正整数`)
  return fm
}

export function readLabMetadata(fm, catalog, docs, label = '实验') {
  if (!['ready', 'planned'].includes(fm.code_status)) throw new Error(`${label}: 缺少/非法 code_status`)
  if (!['pending', 'verified'].includes(fm.hardware_status)) throw new Error(`${label}: 缺少/非法 hardware_status`)
  if (fm.hardware_status === 'verified') {
    const evidence = typeof fm.evidence === 'string' ? path.resolve(docs, fm.evidence) : ''
    if (!evidence.startsWith(path.resolve(docs) + path.sep) || !fs.statSync(evidence, { throwIfNoEntry: false })?.isFile()) {
      throw new Error(`${label}: 上板验证缺少 docs/ 下的证据文件`)
    }
  }
  if (typeof fm.code_note !== 'string' || !fm.code_note.trim()) throw new Error(`${label}: 缺 code_note`)
  const ids = fm.projects ?? []
  if (!Array.isArray(ids) || ids.some(id => !catalog.some(p => p.id === id))) throw new Error(`${label}: 引用了不存在的工程`)
  if (fm.code_status === 'ready' && !ids.length) throw new Error(`${label}: ready 必须有工程`)
  return { codeStatus: fm.code_status, hardwareStatus: fm.hardware_status, codeNote: fm.code_note, projects: ids }
}
