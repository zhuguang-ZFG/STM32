/**
 * 产物锚点对账门：构建后的站内 fragment 链接必须真的落得到锚点上。
 *
 * 为什么有它：config.mts 的 ignoreDeadLinks:false 只在构建期保证「链接目标文件存在」，
 * 锚点（# 后面那段）没人管——改掉一个标题，全站指向旧锚点的链接构建照样绿，
 * 读者点过去只会停在页顶。姊妹项目 BMS-Z 用 check_pages.py 守的是同一件事，
 * 区别是这里直接对 dist 产物对账（部署物本人），而不是对源码做静态推测。
 *
 * 用法：node scripts/pages-check.mjs [--dist <dir>]（默认 docs/.vitepress/dist）
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { collectHtmlPages } from './seo-check.mjs'
import { BASE } from './site-config.mjs'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const DEFAULT_DIST = path.join(ROOT, 'docs', '.vitepress', 'dist')

/** 带协议的 href（http(s):、mailto: 等）是站外事，站内锚点门不管。 */
const SCHEME = /^[a-zA-Z][a-zA-Z0-9+.-]*:/

const toPosix = (p) => p.split(path.sep).join('/')

/**
 * 收集产物里每个页面声明的锚点。
 * @returns {Map<string, Set<string>>} 键 = 相对 dist 的 posix 路径（如 "stm32/03-gpio.html"）
 */
export function collectDistAnchors(distDir) {
  const anchors = new Map()
  for (const file of collectHtmlPages(distDir)) {
    const html = fs.readFileSync(file, 'utf8')
    anchors.set(
      toPosix(path.relative(distDir, file)),
      new Set([...html.matchAll(/\bid="([^"]*)"/g)].map((m) => m[1])),
    )
  }
  return anchors
}

/**
 * 把一条 href 解析成「目标页 + 锚点」；返回 null 表示无需检查
 * （外链、协议相对外链、纯 #、空锚点、不带锚点、非 html 资产）。
 * fromPage 是来源页相对 dist 的 posix 路径。
 */
export function resolveHref(href, fromPage) {
  if (!href || href === '#' || href.startsWith('//') || SCHEME.test(href)) return null
  const hash = href.indexOf('#')
  if (hash < 0 || hash === href.length - 1) return null // 无锚点 / 空锚点（如 "a.html#"）
  const fragment = href.slice(hash + 1)
  let p = href.slice(0, hash).split('?')[0]
  if (!p) return { target: fromPage, fragment }
  if (p === BASE.slice(0, -1)) p = '' // 裸 base（"/STM32/mcu"），按站点根处理
  else if (p.startsWith(BASE)) p = p.slice(BASE.length) // 站内绝对路径按 base 解析
  else if (p.startsWith('/')) {
    // BASE 之外的绝对路径：产物里不该出现。站点挂在 BASE（/mcu/）下，浏览器会把这种
    // href 解析成站外路径而 404；早期写法是去掉前导 "/" 当站内路径继续查，
    // 只要 dist 里恰好有同名文件就会**假绿**（现存测试覆盖过这个误映射）。
    return { outOfBase: p }
  }
  else p = path.posix.normalize(path.posix.join(path.posix.dirname(fromPage), p))
  if (p === '') p = 'index.html'
  else if (p.endsWith('/')) p += 'index.html'
  // 非 html 资产（svg/css/js/字体）的 # 是资产内部语义，不是页面锚点
  if (!p.endsWith('.html')) return null
  return { target: p, fragment }
}

/**
 * 全产物对账。
 * @returns {{ problems: string[], checked: number, pages: number }}
 * problems 逐条点名 文件:行 → 期望 vs 实际。
 */
export function checkDistAnchors(distDir) {
  const anchors = collectDistAnchors(distDir)
  const problems = []
  let checked = 0
  for (const file of collectHtmlPages(distDir)) {
    const page = toPosix(path.relative(distDir, file))
    const html = fs.readFileSync(file, 'utf8')
    // Inline runtimes contain CSS selectors such as a[href="#'+id+'"].
    // They are not links. Blank non-markup bodies without changing offsets,
    // preserving the file/line diagnostics for actual anchors below them.
    const markup = html.replace(/<(script|style)\b[^>]*>[\s\S]*?<\/\1\s*>/gi, block => block.replace(/[^\n]/g, ' '))
    for (const m of markup.matchAll(/href="([^"]*)"/g)) {
      const href = m[1]
      const resolved = resolveHref(href, page)
      if (!resolved) continue
      checked++
      const line = html.slice(0, m.index).split('\n').length
      if (resolved.outOfBase) {
        problems.push(
          `${page}:${line} → href "${href}" 是 BASE（${BASE}）之外的绝对路径，部署后浏览器会当站外路径解析（404）`,
        )
        continue
      }
      const ids = anchors.get(resolved.target)
      if (!ids) {
        problems.push(
          `${page}:${line} → href "${href}" 期望指向产物内页面 ${resolved.target}，实际该文件不存在`,
        )
      } else if (!ids.has(resolved.fragment)) {
        problems.push(
          `${page}:${line} → href "${href}" 期望 ${resolved.target} 含 id="${resolved.fragment}"，实际不存在`,
        )
      }
    }
  }
  return { problems, checked, pages: anchors.size }
}

const isMain =
  process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href

if (isMain) {
  const at = process.argv.indexOf('--dist')
  const dist = at >= 0 && process.argv[at + 1] ? path.resolve(process.argv[at + 1]) : DEFAULT_DIST

  if (!fs.existsSync(dist)) {
    console.error(`✗ 找不到构建产物 ${dist} —— 请先运行 npm run docs:build`)
    process.exit(1)
  }

  const { problems, checked, pages } = checkDistAnchors(dist)
  if (problems.length) {
    console.error(`✗ ${problems.length}/${checked} 条站内锚点链接对不上：`)
    for (const p of problems.slice(0, 20)) console.error(`  - ${p}`)
    if (problems.length > 20) console.error(`  …还有 ${problems.length - 20} 条`)
    process.exit(1)
  }
  console.log(`✓ ${pages} 个页面、${checked} 条带锚点链接全部命中目标 id`)
}
