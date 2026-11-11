/**
 * SEO / 分享元数据闸门：构建产物必须能被「分享出去」和「被收录」。
 *
 * 为什么单独有它：站点在内容与工程上都已到位，但线上实测（2026-10-08）
 * sitemap.xml 与 robots.txt 双双 404，<head> 里没有任何 og:/twitter: 分享标签、
 * 也没有 canonical——链接发到微信/论坛/X 就是一张白板卡，搜索引擎收录与排序也吃亏。
 * 这类能力「缺了不影响构建、也不触发死链」，只能靠专门的门禁守住。
 *
 * 用法：node scripts/seo-check.mjs（需先 npm run docs:build；--quiet 只在出错时输出）
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
export const HOST = 'https://zhuguang-zfg.github.io'
export const BASE = '/mcu/'

/** 每页必需的 meta：属性名 + 键名。 */
export const REQUIRED_META = [
  ['property', 'og:title'],
  ['property', 'og:description'],
  ['property', 'og:url'],
  ['property', 'og:image'],
  ['name', 'twitter:card'],
]

const escapeRe = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

/** 取出某条 meta 的 content（不存在或为空则返回 null）。 */
export function metaContent(html, attr, key) {
  const tag = new RegExp(`<meta\\b[^>]*\\b${attr}="${escapeRe(key)}"[^>]*>`, 'i').exec(html)
  if (!tag) return null
  const c = /\bcontent="([^"]*)"/i.exec(tag[0])
  return c && c[1].trim() ? c[1].trim() : null
}

export function canonicalHref(html) {
  const tag = /<link\b[^>]*\brel="canonical"[^>]*>/i.exec(html)
  if (!tag) return null
  const h = /\bhref="([^"]*)"/i.exec(tag[0])
  return h && h[1].trim() ? h[1].trim() : null
}

/** 单页检查：返回缺失项列表（空数组 = 合格）。 */
export function checkPageHtml(html) {
  const missing = []
  if (!/<html\b[^>]*\blang="zh-CN"/i.test(html)) missing.push('html[lang="zh-CN"]')
  if (!canonicalHref(html)) missing.push('canonical')
  for (const [attr, key] of REQUIRED_META) {
    const v = metaContent(html, attr, key)
    if (!v) missing.push(`${key}`)
    else if ((key === 'og:image' || key === 'og:url') && !/^https?:\/\//i.test(v)) {
      missing.push(`${key}（必须是绝对 URL，当前为 "${v}"）`)
    }
  }
  return missing
}

/** 递归收集产物里的 .html 页面。 */
export function collectHtmlPages(dir) {
  const out = []
  const walk = (d) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const abs = path.join(d, e.name)
      if (e.isDirectory()) walk(abs)
      else if (e.name.endsWith('.html')) out.push(abs)
    }
  }
  walk(dir)
  return out.sort()
}

/** sitemap.xml 必须声明 urlset，且每条 <loc> 都带 host+base 前缀（防「丢 base」回归）。 */
export function checkSitemap(xml) {
  const problems = []
  if (!/<urlset\b/i.test(xml)) problems.push('缺少 <urlset> 根元素')
  const locs = [...xml.matchAll(/<loc>([^<]*)<\/loc>/g)].map((m) => m[1].trim())
  if (!locs.length) problems.push('没有任何 <loc> 条目')
  const prefix = HOST + BASE
  const wrong = locs.filter((u) => !u.startsWith(prefix))
  if (wrong.length) {
    problems.push(`${wrong.length}/${locs.length} 条 URL 未带前缀 ${prefix}（如 ${wrong[0]}）`)
  }
  return { problems, count: locs.length }
}

/**
 * 本地搜索索引必须含中文二元组。
 * MiniSearch 默认按空白/标点切词，一整段中文会被当成 1 个 token，只有落在段首的词
 * 能靠 prefix 命中——实测搜「优先级反转」「上下文切换」「链接脚本」全部 0 结果。
 * 一旦有人误删 config.mts 里的 miniSearch.options.tokenize，构建不会报错、
 * 死链也查不出来，中文搜索只会「静默失效」，所以必须有门禁。
 */
export function checkSearchIndex(json, minBigram = 5000) {
  const problems = []
  const terms = Array.isArray(json?.index) ? json.index.map((x) => x[0]) : []
  if (!terms.length) problems.push('索引里没有任何 term')
  const bigram = terms.filter((t) => /^[一-鿿]{2}$/.test(t))
  if (bigram.length < minBigram) {
    problems.push(
      `中文二元组仅 ${bigram.length} 条（需 ≥ ${minBigram}）：中文搜索会静默失效，` +
        `请检查 config.mts 的 themeConfig.search.options.miniSearch.options.tokenize`
    )
  }
  return { problems, terms: terms.length, bigram: bigram.length }
}

/** 从 chunk 源码里取出索引 JSON。产物形如：`const t='{...}';export{t as default};` */
export function parseSearchIndexChunk(src) {
  const m = /const\s+\w+\s*=\s*'([\s\S]*)'\s*;\s*export\s*\{/.exec(src)
  if (!m) return null
  try {
    return JSON.parse(m[1].replace(/\\'/g, "'"))
  } catch {
    return null
  }
}

/**
 * 在产物里定位本地搜索索引 chunk 并解析。
 * 用文本解析而不是 import：直接 import 产物 chunk 会触发 Node 的
 * MODULE_TYPELESS_PACKAGE_JSON 警告，污染门禁输出。
 */
export function loadSearchIndex(dist) {
  const chunks = path.join(dist, 'assets', 'chunks')
  if (!fs.existsSync(chunks)) return null
  const file = fs.readdirSync(chunks).find((f) => f.startsWith('@localSearchIndex'))
  if (!file) return null
  return parseSearchIndexChunk(fs.readFileSync(path.join(chunks, file), 'utf8'))
}

/** robots.txt 必须放行抓取并指向 sitemap。 */
export function checkRobots(txt) {
  const problems = []
  if (!/^\s*User-agent:\s*\*/im.test(txt)) problems.push('缺少 `User-agent: *`')
  if (!/^\s*Allow:\s*\//im.test(txt)) problems.push('缺少 `Allow: /`')
  if (!/^\s*Sitemap:\s*https?:\/\/\S+/im.test(txt)) problems.push('缺少绝对 URL 的 `Sitemap:` 行')
  return problems
}

const isMain =
  process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href

if (isMain) {
  const dist = path.join(ROOT, 'docs', '.vitepress', 'dist')
  const quiet = process.argv.includes('--quiet')
  const fail = (msg) => {
    console.error(`✗ ${msg}`)
    process.exitCode = 1
  }

  if (!fs.existsSync(dist)) {
    console.error('✗ 找不到构建产物 docs/.vitepress/dist —— 请先运行 npm run docs:build')
    process.exit(1)
  }

  // 站点级资产
  const sitemapPath = path.join(dist, 'sitemap.xml')
  const robotsPath = path.join(dist, 'robots.txt')
  const ogPath = path.join(dist, 'og-cover.png')
  if (!fs.existsSync(sitemapPath)) fail('产物缺少 sitemap.xml')
  if (!fs.existsSync(robotsPath)) fail('产物缺少 robots.txt')
  if (!fs.existsSync(ogPath)) fail('产物缺少 og-cover.png（社交分享图）')

  if (fs.existsSync(sitemapPath)) {
    const { problems, count } = checkSitemap(fs.readFileSync(sitemapPath, 'utf8'))
    for (const p of problems) fail(`sitemap.xml：${p}`)
    if (!problems.length && !quiet) console.log(`✓ sitemap.xml 含 ${count} 条 URL`)
  }
  if (fs.existsSync(robotsPath)) {
    for (const p of checkRobots(fs.readFileSync(robotsPath, 'utf8'))) fail(`robots.txt：${p}`)
  }

  // 中文搜索可用性（索引必须含二元组，否则中文搜索静默失效）
  const index = loadSearchIndex(dist)
  if (!index) {
    fail('产物找不到本地搜索索引 chunk')
  } else {
    const { problems, bigram } = checkSearchIndex(index)
    for (const p of problems) fail(`搜索索引：${p}`)
    if (!problems.length && !quiet) console.log(`✓ 搜索索引含 ${bigram} 条中文二元组（中文词检索可用）`)
  }

  // 每页分享卡
  const pages = collectHtmlPages(dist)
  const bad = []
  for (const file of pages) {
    const missing = checkPageHtml(fs.readFileSync(file, 'utf8'))
    if (missing.length) bad.push({ file: path.relative(dist, file), missing })
  }
  if (bad.length) {
    fail(`${bad.length}/${pages.length} 个页面分享元数据不全：`)
    for (const { file, missing } of bad.slice(0, 10)) {
      console.error(`  - ${file} → 缺 ${missing.join('、')}`)
    }
    if (bad.length > 10) console.error(`  …还有 ${bad.length - 10} 个`)
    console.error('  修复：检查 config.mts 的 head / transformHead。')
  } else if (!quiet) {
    console.log(`✓ ${pages.length} 个页面均含 og/twitter 分享卡与 canonical`)
  }
}
