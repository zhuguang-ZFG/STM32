/**
 * 仓库根 README.md / CONTRIBUTING.md 的相对链接检查。
 *
 * 为什么单独有这个脚本：VitePress 的死链门禁只扫 docs/ 底下的页面，
 * 仓库根目录那两个文件在站点之外——链接写错了没有任何自动化会拦下来。
 * 而这两个文件恰恰是新手进仓库后读的第一页，死链最贵。
 *
 * 用法：node scripts/links-check.mjs（--quiet 只在出错时输出）
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
// 锚点算法单一事实来源在 docs-check.mjs（GitHub 规则：不折叠连续空白）。
// 原先本地的 slug() 把 \s+ 折叠成一个 "-"，与 GitHub 实际行为不符，已删除。
import { slugify } from './docs-check.mjs'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const FILES = ['README.md', 'CONTRIBUTING.md']

// [text](target) —— 排除图片（前面带 !），图片坏了自己看得见
const LINK = /(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g

function anchorsIn(text) {
  const set = new Set()
  const lines = text.split(/\r?\n/)
  let inFence = false
  for (const line of lines) {
    if (/^```/.test(line.trim())) {
      inFence = !inFence
      continue
    }
    if (inFence) continue
    const m = line.match(/^(#{1,6})\s+(.*)$/)
    if (m) set.add(slugify(m[2]))
  }
  return set
}

const problems = []
let checked = 0

for (const rel of FILES) {
  const file = path.join(ROOT, rel)
  if (!fs.existsSync(file)) {
    problems.push(`${rel}: 文件不存在`)
    continue
  }
  const text = fs.readFileSync(file, 'utf8')
  const anchors = anchorsIn(text)
  // 代码块里的示例链接不是真链接（仓库结构树、bash 注释）
  const fenceFree = text.replace(/^```[\s\S]*?^```/gm, '')
  let m
  LINK.lastIndex = 0
  while ((m = LINK.exec(fenceFree))) {
    const target = m[1]
    checked++
    if (/^(https?:|mailto:)/.test(target)) continue
    if (target.startsWith('#')) {
      if (!anchors.has(target.slice(1))) problems.push(`${rel}: 本页锚点 ${target} 没有对应标题`)
      continue
    }
    if (target.startsWith('/')) {
      problems.push(`${rel}: ${target} 是站内绝对路径，README 里应写成 docs/… 相对链接`)
      continue
    }
    const [filePart, anchor] = target.split('#')
    if (!filePart) continue
    const abs = path.resolve(path.dirname(file), filePart)
    if (!fs.existsSync(abs)) {
      problems.push(`${rel}: ${target} 指向的 ${path.relative(ROOT, abs).replace(/\\/g, '/')} 不存在`)
      continue
    }
    if (anchor && fs.statSync(abs).isFile() && !anchorsIn(fs.readFileSync(abs, 'utf8')).has(anchor)) {
      problems.push(`${rel}: ${target} 锚点 #${anchor} 在 ${filePart} 里找不到对应标题`)
    }
  }
}

if (problems.length) {
  console.error(`✗ 根文档死链 ${problems.length} 处：`)
  problems.forEach((p) => console.error('  - ' + p))
  process.exit(1)
}
if (!process.argv.includes('--quiet')) {
  console.log(`✓ 根文档 ${checked} 个链接全部可达（README / CONTRIBUTING）`)
}
