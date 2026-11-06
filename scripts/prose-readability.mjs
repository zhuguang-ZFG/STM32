// 通俗度棘轮门：把"通俗易懂"变成可回归的数字，只允许变好，不允许变差。
//
//   node scripts/prose-readability.mjs            # 全表：每章长句占比 / 平均句长
//   node scripts/prose-readability.mjs --check    # 与基线比，任一章变差超阈值即非零退出
//   node scripts/prose-readability.mjs --update   # 把当前值写成新基线（改完正文后收紧）
//
// 口径（只统计成稿章节的正文散文）：
//   - 统计前剥掉围栏代码块、行内代码、表格、图片、链接目标与 `<...>` 标签：读者读的是句子，不是 URL 与寄存器位表；
//   - 句子切分按中英文句读 `。！？；.!?;`，切完长度 <12 字的不计（标题、残行、表格碎片）；
//   - 长句 = 去空白后 >60 字。60 是中文技术写作的经验线：超过它，一句话里通常塞了两个以上从句，
//     读者第一次读需要回读；本书的目标是"一遍读懂"，所以把长句占比当主指标；
//   - 平均句长是副指标，防止有人只切句号不改内容（把一句拆成两半、中间加逗号反而更长）。
//
// 基线只降不升：`--update` 写入的值必须不高于旧基线，否则报错（防"改差了再刷基线"）。
import { existsSync, writeFileSync } from 'node:fs'
import { dirname, join, relative } from 'node:path'
import { pathToFileURL } from 'node:url'
import { fileURLToPath } from 'node:url'

import * as fs from 'node:fs'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const DOCS = join(ROOT, 'docs')
const BASELINE = join(ROOT, '.prose-baseline.json')
const LONG_SENTENCE = 60
const MIN_SENTENCE = 12
/** 单章长句占比允许的上升幅度（百分点）与平均句长允许的上升幅度（字）。 */
const SLACK_LONG = 1.5
const SLACK_AVG = 2

/** 扫描的章节：只认成稿教学篇章，参考/日志/事件/导航页不算散文。 */
const TRACKS = ['c', 'build', 'stm32', 'rtos', 'esp32', 'gd32']
const SKIP_FILES = new Set(['index.md'])

/* 用 fs 的最小封装，避免在 ESM 里重复 import 一堆名字。 */
const readdir = (d) => fs.readdirSync(d)
const statIsDir = (p) => fs.statSync(p).isDirectory()
const read = (p) => fs.readFileSync(p, 'utf8')

function walk(dir, out = []) {
  for (const e of readdir(dir)) {
    const p = join(dir, e)
    if (statIsDir(p)) walk(p, out)
    else if (p.endsWith('.md')) out.push(p)
  }
  return out
}

/** 摘掉非散文成分，返回切成句子的数组。 */
export function sentences(md) {
  let s = md
  s = s.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, '') // frontmatter
  s = s.replace(/```[\s\S]*?```/g, ' ') // 围栏代码
  s = s.replace(/`[^`\n]*`/g, ' ') // 行内代码
  s = s.replace(/^\|.*$/gm, ' ') // 表格行
  s = s.replace(/!\[[^\]]*\]\([^)]*\)/g, ' ') // 图片
  s = s.replace(/\[([^\]]*)\]\([^)]*\)/g, '$1') // 链接留文字
  s = s.replace(/<[^>]+>/g, ' ') // 内联 HTML/Vue 组件
  s = s.replace(/^\s{0,3}#{1,6}\s.*$/gm, ' ') // 标题
  s = s.replace(/^\s*>\s?/gm, ' ') // 引用符号
  const flat = s.replace(/\s+/g, ' ')
  const parts = []
  for (const raw of flat.split(/(?<=[。！？；.!?;])/)) {
    const t = raw.trim()
    if (!t) continue
    const len = t.replace(/[\s，、（）()【】“”"':：]/g, '').length
    if (len < MIN_SENTENCE) continue
    parts.push(len)
  }
  return parts
}

/** 一章的指标：长句占比（%）与平均句长（字）。 */
export function metrics(md) {
  const lens = sentences(md)
  if (!lens.length) return { count: 0, longShare: 0, avg: 0 }
  const long = lens.filter((l) => l > LONG_SENTENCE).length
  const sum = lens.reduce((a, b) => a + b, 0)
  return { count: lens.length, longShare: +((long / lens.length) * 100).toFixed(1), avg: +(sum / lens.length).toFixed(1) }
}

function chapters() {
  const out = []
  for (const track of TRACKS) {
    const dir = join(DOCS, track)
    if (!existsSync(dir)) continue
    for (const p of walk(dir)) {
      const base = p.split(/[\\/]/).pop()
      if (SKIP_FILES.has(base)) continue
      const m = metrics(read(p))
      if (m.count < 20) continue // 太短的页面（导航、占位）不进基线
      out.push({ file: relative(ROOT, p).replace(/\\/g, '/'), ...m })
    }
  }
  return out.sort((a, b) => a.file.localeCompare(b.file))
}

function loadBaseline() {
  if (!existsSync(BASELINE)) return null
  return JSON.parse(read(BASELINE))
}

function main() {
  const args = process.argv.slice(2)
  const rows = chapters()
  const current = Object.fromEntries(rows.map((r) => [r.file, { longShare: r.longShare, avg: r.avg }]))

  if (args.includes('--update')) {
    const old = loadBaseline()
    if (old) {
      const worse = []
      for (const [file, cur] of Object.entries(current)) {
        const prev = old.files?.[file]
        if (!prev) continue
        if (cur.longShare > prev.longShare + SLACK_LONG || cur.avg > prev.avg + SLACK_AVG) {
          worse.push(`${file}（长句 ${prev.longShare}→${cur.longShare}%，均长 ${prev.avg}→${cur.avg}）`)
        }
      }
      if (worse.length) {
        console.error('✗ 拒绝刷新基线：以下章节比旧基线更差，先把正文改回去或改短：')
        worse.forEach((w) => console.error('    - ' + w))
        process.exit(1)
      }
    }
    writeFileSync(BASELINE, JSON.stringify({ longSentence: LONG_SENTENCE, files: current }, null, 2) + '\n')
    console.log(`✓ 基线已写入 ${relative(ROOT, BASELINE)}（${rows.length} 章）`)
    return
  }

  if (args.includes('--check')) {
    const old = loadBaseline()
    if (!old) {
      console.error('✗ 缺少 .prose-baseline.json：先跑 node scripts/prose-readability.mjs --update')
      process.exit(1)
    }
    const problems = []
    for (const r of rows) {
      const prev = old.files?.[r.file]
      if (!prev) {
        problems.push(`${r.file} 不在基线里（新增章节：跑 --update 登记）`)
        continue
      }
      if (r.longShare > prev.longShare + SLACK_LONG) {
        problems.push(`${r.file} 长句占比 ${prev.longShare}% → ${r.longShare}%（上限 +${SLACK_LONG}）`)
      }
      if (r.avg > prev.avg + SLACK_AVG) {
        problems.push(`${r.file} 平均句长 ${prev.avg} → ${r.avg} 字（上限 +${SLACK_AVG}）`)
      }
    }
    if (problems.length) {
      console.error(`✗ 通俗度回退 ${problems.length} 处：`)
      problems.forEach((p) => console.error('    - ' + p))
      process.exit(1)
    }
    const overall = rows.reduce((a, r) => a + r.longShare, 0) / rows.length
    console.log(`✓ 通俗度不回退：${rows.length} 章，平均长句占比 ${overall.toFixed(1)}%（逐章均在基线 +${SLACK_LONG}pt 以内）`)
    return
  }

  console.log('长句%  均长  句数  章节')
  for (const r of rows) {
    console.log(`${String(r.longShare).padStart(5)}  ${String(r.avg).padStart(5)}  ${String(r.count).padStart(5)}  ${r.file}`)
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) main()
