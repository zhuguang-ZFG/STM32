/**
 * 全站文档一致性门：相对链接/锚点、Markdown 卫生、仓库自链、手写数字声明对账。
 *
 * 为什么要有这个脚本：正文与 README 里手写的"88 章 / 109 张动画 / 47 个工程"这类结论，
 * 过去没有任何机器对账——写法漂移、数字过期都靠人眼发现。BMS-Z 的经验是"手工结论必须
 * 被机器对账，且对账正则捞不到句子时门必须红而不是绿"（防写法改了门静默变绿）。
 *
 * 与 links-check.mjs 的分工：links-check 只看根 README/CONTRIBUTING 两个文件；
 * 本脚本扫全站 docs/**\/*.md + 根目录所有 *.md，且锚点算法（slugify）是两边的单一事实来源。
 *
 * 用法：node scripts/docs-check.mjs [--quiet]
 */
import fs from 'node:fs'
import path from 'node:path'
import url from 'node:url'
import { BASE, HOST } from './site-config.mjs'

const ROOT = path.resolve(path.dirname(url.fileURLToPath(import.meta.url)), '..')

/** 扫描时永进的目录黑名单：构建产物与版本库元数据不是"手写文档"。 */
const SKIP_DIRS = new Set(['node_modules', '.temp', '.git', 'dist'])

/** 全站 Markdown 清单：docs 递归 + 根目录 *.md。mcu-book/book 不在内（书籍附录由 build_html.py 的契约管）。 */
export function collectMarkdown(root) {
  const files = []
  const walk = (dir) => {
    if (!fs.existsSync(dir)) return
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, e.name)
      if (e.isDirectory()) {
        if (!SKIP_DIRS.has(e.name)) walk(p)
      } else if (e.name.endsWith('.md')) {
        files.push(path.relative(root, p).replace(/\\/g, '/'))
      }
    }
  }
  walk(path.join(root, 'docs'))
  for (const name of fs.readdirSync(root)) {
    const p = path.join(root, name)
    if (name.endsWith('.md') && fs.statSync(p).isFile()) files.push(name)
  }
  return files.sort()
}

/**
 * GitHub 风格锚点：NFC → trim → 小写 → 去标点（保留 \w、空白、连字符、汉字与组合记音）
 * → 每个空白字符各换一个 "-"（不折叠）。
 * 关键差异：连续两个空格会得到两个 "-"，所以 "A + B"（去掉 + 后剩两个空格）→ "a--b"。
 * links-check.mjs 与全站锚点校验共用这一个实现，不许再长第二份。
 */
export function slugify(heading) {
  return heading
    .normalize('NFC')
    .trim()
    .toLowerCase()
    .replace(/[^\p{L}\p{M}\p{N}\p{Pc}\s-]/gu, '')
    .replace(/\s/g, '-')
}

/**
 * VitePress 渲染端锚点：NFKC 归一 → 去组合记号/控制符 → `[\s~`!@#$%^&*()\-_+=[\]{}|\\;:"'“”‘’<>,.?/]+` → "-"
 * → 去首尾 "-" → 小写。
 *
 * 为什么要两份：全角标点在两端行为不同。`第五步：接线（SWD 四线）` 在 VitePress 下是
 * `第五步-接线-swd-四线`（NFKC 把 `：（）` 折成 ASCII 标点后换 "-"），在 GitHub 下是
 * `第五步接线swd-四线`（直接丢标点）。全站有 798 个标题带全角标点，两套算法系统性不一致，
 * 所以源文件里的锚点按**两套渲染取并集**判定，站点那侧的真值另由 pages-check.mjs 对 dist 产物核对。
 */
export function vitePressSlug(heading) {
  return heading
    .normalize('NFKC')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[\s~`!@#$%^&*()\-_+=[\]{}|\\;:"'“”‘’<>,.?\/]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .toLowerCase()
}

/** 逐行收集标题锚点；跳过代码围栏（围栏里的 # 是注释不是标题）。支持 VitePress 自定义锚点 {#id}。 */
function anchorsIn(text) {
  const set = new Set()
  let inFence = false
  for (const line of text.split(/\r?\n/)) {
    if (/^```/.test(line.trim())) {
      inFence = !inFence
      continue
    }
    if (inFence) continue
    const m = line.match(/^(#{1,6})\s+(.*?)\s*$/)
    if (!m) continue
    // 自定义锚点 {#id} 会整体取代按标题文字生成的 slug（VitePress 语义）
    const custom = m[2].match(/\{#([A-Za-z0-9_-]+)\}\s*$/)
    if (custom) {
      set.add(custom[1])
      continue
    }
    set.add(slugify(m[2]))
    set.add(vitePressSlug(m[2]))
  }
  return set
}

/** 百分号解码容错：非法编码按原样返回，不让一个怪链接砸掉整个门。 */
function safeDecode(s) {
  try {
    return decodeURIComponent(s)
  } catch {
    return s
  }
}

function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

// [text](target) —— 排除图片（前面带 !），图片坏了自己看得见；与 links-check.mjs 同一表达式
const LINK = /(?<!!)\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)/g

/**
 * VitePress 干净链接解析：无扩展名的页面引用按 原路径 → .md → /index.md 顺序试。
 * 发布侧 07-usart.md 会变成 07-usart.html，源文件里写 "../stm32/07-usart" 是合法引用。
 */
function resolvePage(p) {
  if (fs.existsSync(p)) return p
  if (fs.existsSync(p + '.md')) return p + '.md'
  if (fs.existsSync(path.join(p, 'index.md'))) return path.join(p, 'index.md')
  return null
}

/**
 * 相对链接存在性 + 锚点解析。
 * 规则：.md 锚点按 slugify 解析；.html 锚点按 id="…" 解析；路径末尾带 "." 或空白直接拒；
 * /mcu/… 站内绝对路径是错误（base 前缀只在部署后存在，源文件里必须写相对路径）；
 * 其余 "/" 起头的路径按站点根解析（docs/ 与 docs/public/ 两处都试）。
 */
export function checkLinks(root) {
  const problems = []
  for (const rel of collectMarkdown(root)) {
    const abs = path.join(root, rel)
    const text = fs.readFileSync(abs, 'utf8')
    const ownAnchors = anchorsIn(text)
    let inFence = false
    const lines = text.split(/\r?\n/)
    lines.forEach((line, i) => {
      if (/^```/.test(line.trim())) {
        inFence = !inFence
        return
      }
      if (inFence) return
      let m
      LINK.lastIndex = 0
      while ((m = LINK.exec(line))) {
        const target = m[1]
        const at = `${rel}:${i + 1}`
        if (/^(https?:|mailto:)/.test(target)) continue
        if (target.startsWith('#')) {
          if (!ownAnchors.has(target.slice(1))) problems.push(`${at} 本页锚点 ${target} 没有对应标题`)
          continue
        }
        if (target.startsWith('/STM32/mcu/') || target.startsWith('/mcu/')) {
          problems.push(`${at} ${target} 是站内绝对路径——该前缀只在部署后存在，源文件里必须写相对路径`)
          continue
        }
        const hash = target.indexOf('#')
        const rawPart = hash === -1 ? target : target.slice(0, hash)
        const anchor = hash === -1 ? '' : target.slice(hash + 1)
        const filePart = safeDecode(rawPart.split('?')[0])
        if (!filePart) continue
        if (/[.\s]$/.test(filePart)) {
          problems.push(`${at} 链接路径 "${rawPart}" 末尾带 '.' 或空白——服务器/构建对这类路径处理不一致，源文件里不许出现`)
          continue
        }
        let resolved
        if (filePart.startsWith('/')) {
          // 站点根 = docs/；public 目录的资源也被发布到根，两处都试
          resolved = [path.join(root, 'docs', filePart), path.join(root, 'docs', 'public', filePart)].find((p) =>
            resolvePage(p),
          )
          if (!resolved) {
            problems.push(`${at} ${target} → 站点根下不存在（试过 docs${filePart} 与 docs/public${filePart}）`)
            continue
          }
          resolved = resolvePage(resolved)
        } else {
          resolved = resolvePage(path.resolve(path.dirname(abs), filePart))
          if (!resolved) {
            problems.push(
              `${at} ${target} 指向的 ${path.relative(root, path.resolve(path.dirname(abs), filePart)).replace(/\\/g, '/')} 不存在`,
            )
            continue
          }
        }
        if (!anchor || !fs.statSync(resolved).isFile()) continue
        if (/\.md$/i.test(resolved)) {
          if (!anchorsIn(fs.readFileSync(resolved, 'utf8')).has(anchor)) {
            problems.push(`${at} ${target} 锚点 #${anchor} 在 ${filePart} 里找不到对应标题`)
          }
        } else if (/\.html?$/i.test(filePart)) {
          const html = fs.readFileSync(resolved, 'utf8')
          if (!new RegExp(`id=["']${escapeRegExp(anchor)}["']`).test(html)) {
            problems.push(`${at} ${target} 锚点 #${anchor} 在 ${filePart} 里找不到 id="${anchor}"`)
          }
        }
      }
    })
  }
  return problems
}

/**
 * Markdown 卫生：正文（代码围栏之外）不许出现控制字符与 \(…\) 行内公式定界符。
 * 真 TAB 是最常见的事故——"\t" 被编辑器存成了真字符，渲染时静默吃掉缩进。
 * 围栏之内放行：Makefile/C 代码示例里的 TAB 是语义本身，不是污染。
 */
export function checkHygiene(root) {
  const problems = []
  const CONTROL = /[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/
  for (const rel of collectMarkdown(root)) {
    const lines = fs.readFileSync(path.join(root, rel), 'utf8').split(/\r?\n/)
    let inFence = false
    lines.forEach((line, i) => {
      if (/^```/.test(line.trim())) {
        inFence = !inFence
        return
      }
      if (inFence) return
      const at = `${rel}:${i + 1}`
      if (line.includes('\t')) {
        problems.push(`${at} 正文里出现真 TAB 控制字符——多半是 "\\t" 被存成了真字符， prose 里请改用空格或转义写法`)
      }
      const c = line.match(CONTROL)
      if (c) {
        problems.push(`${at} 正文里出现控制字符 U+${c[0].codePointAt(0).toString(16).toUpperCase().padStart(4, '0')}`)
      }
      const math = line.match(/\\[()]/)
      if (math) {
        problems.push(`${at} 出现行内公式定界符 "${math[0]}" —— 本站未接数学渲染，\\(…\\) 会原样漏进正文，请改写`)
      }
    })
  }
  return problems
}

// `<details><summary>…</summary>` 之后若跟一个空行，Markdown 的 HTML 块在此结束；
// 随后正文按普通段落解析。此时闭合标签若粘在段落末尾，产物是 <p>…</details></p>——
// 交叉嵌套，VitePress 的 Vue 编译期直接报 "Element is missing end tag"。闭合必须独立成行。
function checkDetailsNesting(root) {
  const problems = []
  for (const rel of collectMarkdown(root)) {
    const lines = fs.readFileSync(path.join(root, rel), 'utf8').split(/\r?\n/)
    let inFence = false
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i]
      if (/^```/.test(line.trim())) {
        inFence = !inFence
        continue
      }
      if (inFence) continue
      if (!/<details[^>]*>/.test(line) || /<\/details>/.test(line)) continue
      if ((lines[i + 1] ?? '').trim() !== '') continue
      for (let k = i + 1; k < Math.min(lines.length, i + 60); k++) {
        if (!/<\/details>/.test(lines[k])) continue
        if (lines[k].trim() !== '</details>') {
          problems.push(
            `${rel}:${k + 1} <details> 开标签后有空行，` +
              `闭合标签却粘在正文行末（第 ${i + 1} 行开启）——会编译成 <p>…</details></p>，` +
              'Vue 报 Element is missing end tag；闭合请独立成行',
          )
        }
        break
      }
    }
  }
  return problems
}

// 本仓库自链三种形态：
//  新（合并后）：github.com/zhuguang-ZFG/STM32/blob/<ref>/mcu/<path> —— <path> 剥掉 mcu/ 前缀对账
//  旧（合并前历史文档）：github.com/zhuguang-ZFG/mcu/blob/<ref>/<path> —— <path> 原样对账
//     （旧仓目录结构与 MCU 项目根同构，旧链按 MCU 根解析仍然成立；历史文档不做无条件改写）
//  前缀丢失/越域：STM32 单仓 blob 但路径不在 mcu/ 子树下 —— MCU 文档不许出现，当场点名
//     （作者想链 mcu/ 内文件却漏写前缀时，GitHub 上 404，门必须在这里抓住）
const SELF_BLOB_NEW = /https:\/\/github\.com\/zhuguang-ZFG\/STM32\/blob\/([^/\s)]+)\/mcu\/([^\s)]+)/g
const SELF_BLOB_OLD = /https:\/\/github\.com\/zhuguang-ZFG\/mcu\/blob\/([^/\s)]+)\/([^\s)]+)/g
const SELF_BLOB_OUTSIDE = /https:\/\/github\.com\/zhuguang-ZFG\/STM32\/blob\/[^/\s)]+\/(?!mcu\/)[^\s)]+/g

/**
 * 仓库自链按工作树存在性校验：GitHub 路由对 blob 链接很宽容（404 也是渲染后才看见），
 * 本地按文件系统对账，指向不存在的路径当场点名。
 */
export function checkSelfBlobLinks(root) {
  const problems = []
  for (const rel of collectMarkdown(root)) {
    const lines = fs.readFileSync(path.join(root, rel), 'utf8').split(/\r?\n/)
    let inFence = false
    lines.forEach((line, i) => {
      if (/^```/.test(line.trim())) {
        inFence = !inFence
        return
      }
      if (inFence) return
      let m
      SELF_BLOB_OUTSIDE.lastIndex = 0
      while ((m = SELF_BLOB_OUTSIDE.exec(line))) {
        problems.push(
          `${rel}:${i + 1} 自链 ${m[0]} 指向 STM32 仓库 mcu/ 子树之外——MCU 文档的仓库自链必须带 mcu/ 前缀`,
        )
      }
      for (const re of [SELF_BLOB_NEW, SELF_BLOB_OLD]) {
        let mm
        re.lastIndex = 0
        while ((mm = re.exec(line))) {
          const relPath = safeDecode(mm[2].split('#')[0])
          if (!fs.existsSync(path.join(root, relPath))) {
            problems.push(`${rel}:${i + 1} 自链 ${mm[0]} 指向工作树里不存在的 ${relPath}`)
          }
        }
      }
    })
  }
  return problems
}

/* ---------------- 手写数字声明对账 ---------------- */

/** 数字捕获既可能是阿拉伯数字也可能是中文数字（"六附录"、"五个契约"），统一解析。 */
const CN_DIGIT = { 一: 1, 二: 2, 两: 2, 三: 3, 四: 4, 五: 5, 六: 6, 七: 7, 八: 8, 九: 9 }
function parseClaimNumber(raw) {
  const s = String(raw).trim()
  if (/^\d+$/.test(s)) return Number(s)
  if (s === '十') return 10
  if (s.length === 1 && CN_DIGIT[s]) return CN_DIGIT[s]
  let m = s.match(/^十([一二两三四五六七八九])$/)
  if (m) return 10 + CN_DIGIT[m[1]]
  m = s.match(/^([一二两三四五六七八九])十$/)
  if (m) return CN_DIGIT[m[1]] * 10
  m = s.match(/^([一二两三四五六七八九])十([一二两三四五六七八九])$/)
  if (m) return CN_DIGIT[m[1]] * 10 + CN_DIGIT[m[2]]
  return NaN
}

function loadManifest(root) {
  return JSON.parse(fs.readFileSync(path.join(root, 'mcu-book', 'manifest.json'), 'utf8'))
}

/** 成书插图数（"109 张机制动画"的真源）：构建器把每个独立段落的图片与 <AnimFigure> 都包成 anim-figure。 */
function countBookFigures(root) {
  const manifest = loadManifest(root)
  let figures = 0
  for (const file of manifest.parts.flatMap((p) => p.files)) {
    let inFence = false
    for (const line of fs.readFileSync(path.join(root, 'docs', file), 'utf8').split(/\r?\n/)) {
      if (/^```/.test(line.trim())) {
        inFence = !inFence
        continue
      }
      if (inFence) continue
      if (/^!\[[^\]]*\]\([^)]+\)\s*$/.test(line.trim())) figures++
      figures += (line.match(/<AnimFigure\b/g) || []).length
    }
  }
  return figures
}

/** 附录 A 的串口协议契约数（"五个契约"的真源）：数 "^## 契约N" 小节。 */
function countProtocolContracts(root) {
  const text = fs.readFileSync(path.join(root, 'mcu-book', 'book', 'A-工程深读.md'), 'utf8')
  return text.split(/\r?\n/).filter((l) => /^##\s+契约[一二三四五六七八九\d]/.test(l)).length
}

const truth = {
  chapters: (root) => loadManifest(root).parts.reduce((n, p) => n + p.files.length, 0),
  parts: (root) => loadManifest(root).parts.length,
  appendices: (root) => loadManifest(root).appendices.length,
  sources: (root) => Object.keys(loadManifest(root).sources).length,
  projects: (root) => JSON.parse(fs.readFileSync(path.join(root, 'code', 'projects.json'), 'utf8')).length,
  quizzes: (root) =>
    fs.readdirSync(path.join(root, 'docs', '.vitepress', 'data', 'quizzes')).filter((f) => f.endsWith('.json')).length,
  animFiles: (root) => fs.readdirSync(path.join(root, 'docs', 'public', 'anim')).filter((f) => f.endsWith('.svg')).length,
  bookFigures: countBookFigures,
  protocolContracts: countProtocolContracts,
}

const CN = '一二两三四五六七八九十'
/**
 * 手写数字声明登记表。每一条都是全仓库真实存在的表述（2026-10-25 实测登记）：
 * 捕获值与真源不符 → 红；正则一条都捞不到（minMatches）→ 也红——写法改了门不许静默变绿。
 * changelog.md 里 "\d+ 章" 另有大量历史数字（新增 12 章之类），只能用带上下文的窄正则。
 */
export const CLAIMS = [
  // 章节数 ↔ manifest parts[].files 合计（88）
  { label: '章节数', file: 'README.md', pattern: /(\d+) 章/g, expected: truth.chapters, minMatches: 1 },
  { label: '章节数', file: 'docs/reference/book.md', pattern: /(\d+) 章/g, expected: truth.chapters, minMatches: 1 },
  { label: '章节数', file: 'docs/reference/changelog.md', pattern: /(\d+) 章(?=装订成书|正文装订为)/g, expected: truth.chapters, minMatches: 1 },
  { label: '章节数', file: 'mcu-book/README.md', pattern: /(\d+) 章/g, expected: truth.chapters, minMatches: 1 },
  // 分部数 ↔ manifest.parts.length（10）
  { label: '分部数', file: 'README.md', pattern: /(\d+) 个?分部/g, expected: truth.parts, minMatches: 1 },
  { label: '分部数', file: 'docs/reference/book.md', pattern: /(\d+) 个分部/g, expected: truth.parts, minMatches: 1 },
  { label: '分部数', file: 'mcu-book/README.md', pattern: /(\d+) 个分部/g, expected: truth.parts, minMatches: 1 },
  // 附录数 ↔ manifest.appendices.length（6）
  { label: '附录数', file: 'README.md', pattern: new RegExp(`([${CN}]+)附录`, 'g'), expected: truth.appendices, minMatches: 1 },
  { label: '附录数', file: 'docs/reference/book.md', pattern: new RegExp(`(\\d+|[${CN}]+) 份附录`, 'g'), expected: truth.appendices, minMatches: 1 },
  { label: '附录数', file: 'docs/reference/changelog.md', pattern: /(\d+) 附录/g, expected: truth.appendices, minMatches: 1 },
  { label: '附录数', file: 'mcu-book/README.md', pattern: /(\d+) 附录/g, expected: truth.appendices, minMatches: 1 },
  // 配套工程数 ↔ code/projects.json 长度（47）
  { label: '配套工程数', file: 'docs/reference/book.md', pattern: /(\d+) 个配套工程/g, expected: truth.projects, minMatches: 1 },
  { label: '配套工程数', file: 'docs/reference/changelog.md', pattern: /(\d+) 个配套工程/g, expected: truth.projects, minMatches: 1 },
  { label: '配套工程数', file: 'mcu-book/README.md', pattern: /(\d+) 个配套工程/g, expected: truth.projects, minMatches: 1 },
  { label: '示例工程数', file: 'README.md', pattern: /示例工程 \*\*(\d+)\*\* 个/g, expected: truth.projects, minMatches: 1 },
  // 自测组数 ↔ docs/.vitepress/data/quizzes/*.json 计数（13）
  { label: '自测组数', file: 'docs/reference/changelog.md', pattern: /(\d+) 组自测/g, expected: truth.quizzes, minMatches: 1 },
  { label: '自测组数', file: 'mcu-book/README.md', pattern: /(\d+) 组自动汇入/g, expected: truth.quizzes, minMatches: 1 },
  // 冻结来源数 ↔ manifest.sources 键数（60）
  { label: '冻结来源数', file: 'README.md', pattern: /(\d+) 项来源/g, expected: truth.sources, minMatches: 1 },
  { label: '冻结来源数', file: 'docs/reference/book.md', pattern: /(\d+) 项冻结来源/g, expected: truth.sources, minMatches: 1 },
  { label: '冻结来源数', file: 'docs/reference/changelog.md', pattern: /(\d+) 项冻结来源/g, expected: truth.sources, minMatches: 1 },
  { label: '来源注册表', file: 'mcu-book/README.md', pattern: /来源注册表 (\d+) 项/g, expected: truth.sources, minMatches: 1 },
  // 动画文件数 ↔ docs/public/anim/*.svg 计数（与 gen-progress.mjs 同源，103）
  { label: '动画文件数', file: 'README.md', pattern: /机制动画 \*\*(\d+)\*\* 张/g, expected: truth.animFiles, minMatches: 1 },
  // 成书插图/动画数 ↔ 构建器 anim-figure 计数口径（独立段落图片 + AnimFigure，109）
  // 2026-11-03 起 4 张 stack-diagram 架构图入书，口径=机制动画+架构图（120）
  { label: '成书插图数', file: 'docs/reference/book.md', pattern: /(\d+) 张机制动画/g, expected: truth.bookFigures, minMatches: 1 },
  { label: '成书插图数', file: 'docs/reference/changelog.md', pattern: /(\d+) 张机制动画/g, expected: truth.bookFigures, minMatches: 1 },
  { label: '成书插图数', file: 'mcu-book/README.md', pattern: /(\d+) 张(?:机制|SMIL) ?动画/g, expected: truth.bookFigures, minMatches: 1 },
  // 串口协议契约数 ↔ 附录 A "契约N" 小节数（5）
  { label: '帧协议契约数', file: 'docs/reference/book.md', pattern: new RegExp(`帧协议的(\\d+|[${CN}]+) ?个?契约`, 'g'), expected: truth.protocolContracts, minMatches: 1 },
  { label: '帧协议契约数', file: 'mcu-book/README.md', pattern: new RegExp(`帧协议的(\\d+|[${CN}]+) ?个?契约`, 'g'), expected: truth.protocolContracts, minMatches: 1 },
]

/**
 * 逐条对账 CLAIMS：捕获值 != 期望值 → 点名 file:line 与"实际 vs 期望"；
 * 命中句数 < minMatches → 同样点名（正则捞不到句子的唯一合法原因是写法变了，那门就该红）。
 */
export function checkNumberClaims(root, claims = CLAIMS) {
  const problems = []
  for (const claim of claims) {
    const min = claim.minMatches ?? 1
    const expected = claim.expected(root)
    const file = path.join(root, claim.file)
    if (!fs.existsSync(file)) {
      problems.push(`${claim.file} → 「${claim.label}」对账文件不存在`)
      continue
    }
    const flags = claim.pattern.flags.includes('g') ? claim.pattern.flags : claim.pattern.flags + 'g'
    const re = new RegExp(claim.pattern.source, flags)
    let hits = 0
    fs.readFileSync(file, 'utf8')
      .split(/\r?\n/)
      .forEach((line, i) => {
        re.lastIndex = 0
        let m
        while ((m = re.exec(line))) {
          hits++
          const actual = parseClaimNumber(m[1])
          if (actual !== expected) {
            const shown = Number.isNaN(actual) ? `无法解析的数字 "${m[1]}"` : `${actual}`
            problems.push(`${claim.file}:${i + 1} → 「${claim.label}」写的 ${m[1]}（=${shown}）与实际 ${expected} 不符`)
          }
        }
      })
    if (hits < min) {
      problems.push(`${claim.file} → 「${claim.label}」正则只命中 ${hits} 处（要求 ≥ ${min}）：写法若已改请同步更新 CLAIMS，门不许静默变绿`)
    }
  }
  return problems
}

/* ---------------- 元文件与发布口径对账 ---------------- */

/**
 * CITATION.cff 的关键字段必须与 manifest / 站点口径同源。
 * 为什么：引用格式是给外人抄的，版本号与仓库地址漂移了没有任何人会当场发现，
 * 抄进论文里的就是过期版本。
 */
export function checkCitation(root) {
  const problems = []
  const file = path.join(root, 'CITATION.cff')
  if (!fs.existsSync(file)) return ['CITATION.cff 缺失：外部引用没有可抄的版本与来源']
  const manifest = loadManifest(root)
  const text = fs.readFileSync(file, 'utf8')
  const scalar = (name) => {
    const m = text.match(new RegExp(`^${name}:[ \\t]*(.+)$`, 'm'))
    return m ? m[1].trim().replace(/^["']|["']$/g, '') : null
  }
  const expected = {
    title: manifest.title,
    version: String(manifest.version),
    'repository-code': manifest.repository,
    url: HOST + BASE,
  }
  for (const [name, want] of Object.entries(expected)) {
    const got = scalar(name)
    if (got !== want) {
      problems.push(
        `CITATION.cff 的 ${name} 是 ${JSON.stringify(got)}，与 manifest/站点口径 ${JSON.stringify(want)} 不一致`,
      )
    }
  }
  const author = text.match(/^authors:\s*\n\s*-\s*name:\s*(.+)$/m)
  const authorName = author ? author[1].trim().replace(/^["']|["']$/g, '') : null
  if (authorName !== manifest.author) {
    problems.push(
      `CITATION.cff 的 authors[0].name 是 ${JSON.stringify(authorName)}，manifest.author 是 ${JSON.stringify(manifest.author)}`,
    )
  }
  return problems
}

/**
 * 根 CHANGELOG.md 与站点更新日志、manifest 版本三者对账。
 * 分工：根文件按**版本**记对外承诺，站点侧按**日期**记过程。两处口径各自漂移的结果，
 * 就是读者拿到一个"最新版本"是半年前的引用格式。
 */
export function checkChangelog(root) {
  const problems = []
  const file = path.join(root, 'CHANGELOG.md')
  if (!fs.existsSync(file)) return ['CHANGELOG.md 缺失：发布版本没有对外记录']
  const versions = [...fs.readFileSync(file, 'utf8').matchAll(/^##\s+v(\d+\.\d+\.\d+)\s*·/gm)].map((m) => m[1])
  if (!versions.length) return ['CHANGELOG.md 里没有任何 `## vX.Y.Z · YYYY-MM-DD` 版本节']
  const site = fs.readFileSync(path.join(root, 'docs', 'reference', 'changelog.md'), 'utf8')
  for (const version of versions) {
    if (!site.includes(`v${version}`)) {
      problems.push(`CHANGELOG.md 的 v${version} 在站点更新日志（docs/reference/changelog.md）里找不到对应提法`)
    }
  }
  const manifest = loadManifest(root)
  if (versions[0] !== String(manifest.version)) {
    problems.push(`CHANGELOG.md 最新版本 v${versions[0]} 与 manifest.version ${manifest.version} 不一致`)
  }
  return problems
}

/* ---------------- CLI ---------------- */

function main() {
  const quiet = process.argv.includes('--quiet')
  const t0 = Date.now()
  const files = collectMarkdown(ROOT)
  const sections = [
    ['相对链接与锚点', checkLinks(ROOT)],
    ['Markdown 卫生', checkHygiene(ROOT)],
    ['details 嵌套', checkDetailsNesting(ROOT)],
    ['仓库自链', checkSelfBlobLinks(ROOT)],
    ['手写数字声明', checkNumberClaims(ROOT)],
    ['引用与发布口径', [...checkCitation(ROOT), ...checkChangelog(ROOT)]],
  ]
  const total = sections.reduce((n, [, ps]) => n + ps.length, 0)
  if (total) {
    console.error(`✗ 全站文档一致性检查 ${total} 处问题：`)
    for (const [name, ps] of sections) {
      if (!ps.length) continue
      console.error(`  ${name}：`)
      ps.forEach((p) => console.error('    - ' + p))
    }
    process.exit(1)
  }
  if (!quiet) {
    console.log(
      `✓ 全站文档一致性检查通过：扫描 ${files.length} 个 Markdown 文件，` +
        `${sections.length} 类检查（其中数字声明 ${CLAIMS.length} 条），${Date.now() - t0} ms`,
    )
  }
}

const invokedAsScript = process.argv[1] && import.meta.url === url.pathToFileURL(path.resolve(process.argv[1])).href
if (invokedAsScript) main()
