// 阅读时长校准：按正文与代码字数核对每章 frontmatter 的 minutes，离群的点名。
//
//   node scripts/reading-time.mjs            # 全表：正文字 / 代码字 / 标注分钟 / 模型分钟
//   node scripts/reading-time.mjs --check    # 只报离群（偏离模型 ±40% 之外），有则非零退出
//   node scripts/reading-time.mjs --fix      # 把离群章节的 minutes 改成模型值（取整到 5）
//
// 模型：minutes = 正文字数 / 300 + 代码字数 / 150 + 10
//   - 正文按每分钟 300 字：技术中文的常见阅读速度区间（250–350）取中；
//   - 代码按每分钟 150 字（去空白）：代码是逐行对照着读的，慢一倍；
//     正文里用 `<<< 路径` 引入的外部文件也按代码算，它在页面上和围栏代码块一样是要读的；
//   - +10 分钟：规范要求每章都有一个"10 分钟 quick win"，这是动手时间。
// 「## 附录…」整节不计：那里是 probe.c/probe.sh 全文这类备查材料（单章可达 2 万字），
// 和书末附录一样不算进"读完这章要多久"。算进去 S4 会变成 165 分，读者反而不敢点开。
// 口径只管 C/B/S/F/R/P/G/V 篇的成稿章节：lab/ 与 projects/ 的 minutes 是上板时长，不是阅读时长，不在这里校。
// 校准前全站密度从 42 到 387 字/分，差 9 倍——同一张学习地图上两章字数相当、标注时长差三倍，读者就会误判。
import { existsSync, globSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join, relative, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const DOCS = join(ROOT, 'docs')
export const PROSE_PER_MIN = 300
export const CODE_PER_MIN = 150
export const QUICK_WIN_MIN = 10
export const TOLERANCE = 0.4
const TRACKS = ['c', 'build', 'stm32', 'rtos', 'esp32', 'gd32']

// `<<< ../../code/x/main.c` 是 VitePress 的代码引入语法，构建期把整个文件内联进页面。
// 读不到文件时返回 null：宁可少算，也不猜一个数字。
function importedCode(line, fromDir) {
  const m = /^<<<\s+(\S+)/.exec(line.trim())
  if (!m) return null
  const target = resolve(fromDir, m[1].replace(/[#?].*$/, ''))
  if (!existsSync(target)) return null
  return readFileSync(target, 'utf8').replace(/\s/g, '').length
}

// 去掉「## 附录…」到下一个二级标题之间的内容；围栏代码块里的 `## ` 不算标题。
export function stripAppendix(body) {
  const out = []
  let fence = false, skip = false
  for (const line of body.split(/\r?\n/)) {
    if (/^\s*(```|~~~)/.test(line)) fence = !fence
    else if (!fence && /^## /.test(line)) skip = /^## \s*附录/.test(line)
    if (!skip) out.push(line)
  }
  return out.join('\n')
}

export function measure(src, file = '') {
  const fm = /^---\r?\n([\s\S]*?)\r?\n---\r?\n/.exec(src)
  const meta = {}
  if (fm) for (const line of fm[1].split(/\r?\n/)) {
    const m = /^(\w+):\s*(.*)$/.exec(line)
    if (m) meta[m[1]] = m[2].replace(/^['"]|['"]$/g, '')
  }
  let body = stripAppendix(fm ? src.slice(fm[0].length) : src)
  const fromDir = file ? dirname(file) : DOCS
  let code = 0
  body = body.replace(/```[\s\S]*?```/g, (block) => { code += block.replace(/\s/g, '').length; return ' ' })
  body = body.replace(/^.*<<<.*$/gm, (line) => {
    code += importedCode(line, fromDir) ?? 0
    return ' '
  })
  body = body
    .replace(/<[^>\n]+>/g, ' ')            // HTML 标签（AnimFigure/LabStatus 等）；不跨行，否则会把正文吃掉
    .replace(/\]\([^)]*\)/g, ']')          // 链接/图片的 URL
    .replace(/https?:\/\/\S+/g, ' ')
  const prose = body.replace(/\s/g, '').length
  return { meta, prose, code }
}

export function modelMinutes({ prose, code }) {
  const raw = prose / PROSE_PER_MIN + code / CODE_PER_MIN + QUICK_WIN_MIN
  return Math.max(15, Math.round(raw / 5) * 5)
}

export function calibrate(pages, tolerance = TOLERANCE) {
  return pages
    .filter((p) => p.meta.status === 'done' && Number(p.meta.minutes) > 0)
    .map((p) => {
      const minutes = Number(p.meta.minutes)
      const model = modelMinutes(p)
      const ratio = minutes / model
      return { ...p, minutes, model, ratio, outlier: ratio > 1 + tolerance || ratio < 1 - tolerance }
    })
}

function listPages() {
  return globSync('**/*.md', { cwd: DOCS })
    .map((f) => f.replace(/\\/g, '/'))
    .filter((f) => TRACKS.includes(f.split('/')[0]) && !f.endsWith('index.md'))
    .map((f) => {
      const file = join(DOCS, f)
      return { file, rel: relative(ROOT, file).replace(/\\/g, '/'), ...measure(readFileSync(file, 'utf8'), file) }
    })
}

function main() {
  const args = process.argv.slice(2)
  const check = args.includes('--check'), fix = args.includes('--fix')
  const rows = calibrate(listPages())
  const outliers = rows.filter((r) => r.outlier).sort((a, b) => b.ratio - a.ratio)
  const fmt = (r) => `${r.rel.padEnd(42)} 正文 ${String(r.prose).padStart(5)} + 代码 ${String(r.code).padStart(5)} → 模型 ${String(r.model).padStart(3)} 分，标注 ${String(r.minutes).padStart(3)}（×${r.ratio.toFixed(2)}）`
  console.log(`成稿章节 ${rows.length} 篇；模型 = 正文/${PROSE_PER_MIN} + 代码/${CODE_PER_MIN} + ${QUICK_WIN_MIN}，容忍 ±${TOLERANCE * 100}%`)
  if (!check) for (const r of [...rows].sort((a, b) => b.ratio - a.ratio)) console.log((r.outlier ? '✗ ' : '  ') + fmt(r))
  else for (const r of outliers) console.log('✗ ' + fmt(r))
  if (fix) {
    for (const r of outliers) {
      const src = readFileSync(r.file, 'utf8')
      writeFileSync(r.file, src.replace(/^(minutes:\s*)\d+/m, `$1${r.model}`))
    }
    console.log(`已把 ${outliers.length} 篇的 minutes 改成模型值`)
    return
  }
  if (outliers.length) {
    console.log(`\n${outliers.length} 篇时长离群；核对后用 --fix 采纳模型值，或手动改 frontmatter 的 minutes`)
    if (check) process.exit(1)
  } else console.log(`✓ ${rows.length} 篇章节时长都在模型 ±${TOLERANCE * 100}% 内`)
}

if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]) main()
