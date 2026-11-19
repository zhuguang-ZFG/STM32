// 页面集合对账：VitePress 产物里的书页必须与 manifest 一一对应。
//
// 为什么单列一道门：旧链存根（131 条）与读者收藏都指向 `<path>.html`，
// 页面被改名/漏构建时站点仍能起来，但深链会 404。构建后逐文件对账，
// 多一页少一页都失败，避免静默改名。
//
// 用法（cwd=仓库根）：
//   node scripts/check-site-pages.mjs --dist docs/.vitepress/dist
//   node scripts/check-site-pages.mjs --dist dist --manifest docs/manifest.json
//
// 退出码：0 = 页面集合一致；1 = 有缺失或多余页面。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

/** VitePress 自带的错误页，不属于书页集合。 */
const IGNORED = new Set(['404.html'])

export function parseArgs(argv) {
  const args = { dist: 'docs/.vitepress/dist', manifest: 'docs/manifest.json' }
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i]
    if (key === '--dist') args.dist = argv[++i]
    else if (key === '--manifest') args.manifest = argv[++i]
    else throw new Error(`未知参数: ${key}`)
  }
  return args
}

export function expectedPages(manifest) {
  const pages = new Set(['index.html'])
  for (const part of manifest.parts ?? []) {
    // 注意：manifest 的 status 全是 "planned"（= 列入书单），不是“未成稿”，
    // 所以这里不做过滤——页面集合以实际条目为准。
    for (const chapter of part.chapters ?? []) {
      pages.add(chapter.file.replace(/\.md$/, '.html'))
    }
  }
  for (const appendix of manifest.appendices ?? []) {
    pages.add(appendix.file.replace(/\.md$/, '.html'))
  }
  return pages
}

export function actualPages(dist) {
  const pages = new Set()
  const stack = [dist]
  while (stack.length) {
    const dir = stack.pop()
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name)
      if (entry.isDirectory()) {
        // 旧链存根由 site-assemble 单独校验，不在这里算书页
        if (path.relative(dist, full).split(path.sep)[0] === 'mcu') continue
        stack.push(full)
      } else if (entry.name.endsWith('.html')) {
        pages.add(path.relative(dist, full).split(path.sep).join('/'))
      }
    }
  }
  for (const name of IGNORED) pages.delete(name)
  return pages
}

export function comparePages({ expected, actual }) {
  const missing = [...expected].filter((page) => !actual.has(page)).sort()
  const extra = [...actual].filter((page) => !expected.has(page)).sort()
  return { missing, extra, ok: missing.length === 0 && extra.length === 0 }
}

export function checkSitePages({ dist, manifest }) {
  if (!fs.existsSync(dist)) throw new Error(`${dist}: 构建产物不存在，先跑 npm run docs:build`)
  const data = JSON.parse(fs.readFileSync(manifest, 'utf8'))
  const expected = expectedPages(data)
  const actual = actualPages(dist)
  return { ...comparePages({ expected, actual }), count: expected.size }
}

/** 爬虫约定：404 必须 noindex，robots.txt 必须指向真实 sitemap。 */
export function checkCrawlability(dist) {
  const problems = []
  const notFound = path.join(dist, '404.html')
  if (!fs.existsSync(notFound)) {
    problems.push('404.html 不存在')
  } else if (!/<meta name="robots" content="noindex">/.test(fs.readFileSync(notFound, 'utf8'))) {
    problems.push('404.html 缺少 <meta name="robots" content="noindex">')
  }
  const robots = path.join(dist, 'robots.txt')
  if (!fs.existsSync(robots)) {
    problems.push('robots.txt 未随站点发布（docs/public/robots.txt 缺失？）')
  } else {
    const text = fs.readFileSync(robots, 'utf8')
    if (!/^Sitemap: https:\/\/\S+\/sitemap\.xml$/m.test(text)) {
      problems.push('robots.txt 没有绝对 Sitemap 行')
    }
  }
  return { ok: problems.length === 0, problems }
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
if (isMain) {
  const args = parseArgs(process.argv.slice(2))
  const result = checkSitePages(args)
  const crawl = checkCrawlability(args.dist)
  if (result.ok && crawl.ok) {
    console.log(`site pages: manifest 与 dist 一一对应（${result.count} 页）；404 noindex 与 robots.txt 就位`)
    process.exit(0)
  }
  for (const page of result.missing) console.error(`MISSING ${page}`)
  for (const page of result.extra) console.error(`EXTRA ${page}`)
  for (const problem of crawl.problems) console.error(`CRAWL ${problem}`)
  if (!result.ok) {
    console.error(`site pages mismatch: ${result.missing.length} missing, ${result.extra.length} extra`)
  }
  process.exit(1)
}
