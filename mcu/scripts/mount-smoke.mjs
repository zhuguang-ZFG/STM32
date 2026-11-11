// 挂载冒烟：把 staging 按真实 Pages 挂载（/STM32/）起本地服务，用 Chromium 做
// 真实浏览器验证：页面导航、同源资源加载（requestfailed/HTTP>=400 监听）、
// 客户端搜索交互、导读导航、book/downloads 可达。
// 用法（cwd=mcu/）：node scripts/mount-smoke.mjs --root ../.temp/pages-site [--mount /STM32]
import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from '@playwright/test'
import { BASE, HOST } from './site-config.mjs'

export function parseArgs(argv) {
  const args = { root: '../.temp/pages-site', mount: '/STM32' }
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--root') args.root = argv[++i]
    else if (argv[i] === '--mount') args.mount = argv[++i]
    else throw new Error(`未知参数: ${argv[i]}`)
  }
  return args
}

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css',
  '.js': 'text/javascript',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.gif': 'image/gif',
  '.ico': 'image/x-icon',
  '.pdf': 'application/pdf',
  '.xml': 'application/xml',
  '.txt': 'text/plain; charset=utf-8',
  '.woff2': 'font/woff2',
  '.zip': 'application/zip',
}

export function serve(root, mount) {
  const server = http.createServer((req, res) => {
    const url = decodeURIComponent((req.url || '/').split('?')[0])
    if (!url.startsWith(mount + '/') && url !== mount) {
      res.writeHead(404).end('outside mount')
      return
    }
    let rel = url.slice(mount.length) || '/'
    let file = path.join(root, rel)
    if (fs.existsSync(file) && fs.statSync(file).isDirectory()) file = path.join(file, 'index.html')
    if (!fs.existsSync(file) || !fs.statSync(file).isFile()) {
      res.writeHead(404).end('not found: ' + rel)
      return
    }
    res.writeHead(200, { 'content-type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream' })
    fs.createReadStream(file).pipe(res)
  })
  return new Promise((resolve) => {
    server.listen(0, '127.0.0.1', () => resolve({ server, port: server.address().port }))
  })
}

export async function runSmoke({ root, mount }) {
  const mcuDir = path.join(root, 'mcu')
  const fails = []
  const notes = []
  if (!fs.existsSync(path.join(mcuDir, 'index.html'))) {
    return { ok: false, fails: [`staging 缺少 mcu/index.html（${mcuDir}）——先跑 assemble-pages.mjs`], notes }
  }
  const { server, port } = await serve(root, mount)
  const origin = `http://127.0.0.1:${port}`
  const browser = await chromium.launch()
  const page = await browser.newPage()
  // 真实浏览器口径：导航期间所有同源请求失败 / HTTP>=400 都算挂载故障
  //（JS/CSS/图片由页面实际加载触发，不靠我们逐个猜 URL）。
  const netFails = []
  page.on('requestfailed', (req) => {
    // ERR_ABORTED 是客户端主动取消（路由预取被导航打断等），属正常浏览器行为；
    // 真正的挂载故障会表现为 404/5xx（response 监听）或连接级错误。
    if (req.failure()?.errorText === 'net::ERR_ABORTED') return
    if (req.url().startsWith(origin)) netFails.push(`${req.url()} → ${req.failure()?.errorText || 'failed'}`)
  })
  page.on('response', (res) => {
    if (res.url().startsWith(origin) && res.status() >= 400) netFails.push(`${res.url()} → HTTP ${res.status()}`)
  })
  const httpOk = async (name, urlPath) => {
    const res = await page.request.get(origin + urlPath)
    if (res.status() !== 200) fails.push(`${name} ${urlPath} → HTTP ${res.status()}`)
    else notes.push(`${name} ${urlPath} → 200`)
    return res
  }
  try {
    // 1. 根入口（重定向页）
    const rootRes = await page.goto(origin + mount + '/', { waitUntil: 'domcontentloaded' })
    if (!rootRes || rootRes.status() !== 200) fails.push(`根入口 ${mount}/ → HTTP ${rootRes?.status()}`)
    else if (!(await rootRes.text()).includes('url=./mcu/')) fails.push('根入口未返回重定向页')
    else notes.push(`根入口 ${mount}/ → 200 重定向页`)

    // 2. 首页（真实浏览器加载：CSS/JS/图片/字体都在这次导航里实际请求）
    let homeRes = null
    for (let attempt = 0; attempt < 2 && !homeRes; attempt += 1) {
      homeRes = await page.goto(origin + BASE, { waitUntil: 'domcontentloaded', timeout: 30000 }).catch(() => null)
    }
    if (!homeRes || homeRes.status() !== 200) {
      fails.push(`首页 ${BASE} → HTTP ${homeRes?.status()}`)
    } else {
      await page.waitForSelector('#app', { timeout: 5000 })
      const title = await page.title()
      if (!title || title.length < 2) fails.push('首页 200 但 title 为空')
      else notes.push(`首页 ${BASE} → 200「${title}」`)
    }
    const html = await page.content()
    const abs = (attrRe) => {
      const m = html.match(attrRe)
      if (!m) return null
      try {
        const u = new URL(m[1], page.url())
        return u.origin === origin ? u.pathname + u.search : null
      } catch {
        return null
      }
    }
    const deep = abs(new RegExp(`href="(${BASE.replace(/\//g, '\\/')}(?:[a-z0-9-]+\\/)+[a-z0-9-]+\\.html)"`))
    const guideLink = abs(new RegExp(`href="(${BASE.replace(/\//g, '\\/')}reference\\/book\\.html)"`))

    // 3. 章节深链（真实导航）
    if (deep) {
      const r = await page.goto(origin + deep, { waitUntil: 'domcontentloaded' })
      if (!r || r.status() !== 200) fails.push(`章节深链 ${deep} → HTTP ${r?.status()}`)
      else {
        const h1 = await page.locator('h1').first().textContent().catch(() => '')
        if (!h1 || h1.trim().length < 2) fails.push(`深链 ${deep} 200 但没有 h1`)
        else notes.push(`章节深链 ${deep} → 200「${h1.trim().slice(0, 24)}…」`)
      }
    } else {
      fails.push('首页未发现任何章节深链链接——产物形态异常')
    }

    // 4. 客户端搜索交互（VitePress local search：开框 → 输入 → 出结果）
    await page.goto(origin + BASE, { waitUntil: 'domcontentloaded' })
    try {
      const searchBtn = page.locator('[class*="VPNavBarSearch"] button, button[aria-label*="搜索" i], button[title*="搜索" i]').first()
      await searchBtn.click({ timeout: 5000 })
      const input = page.locator('[class*="VPLocalSearchBox"] input, [class*="VPNavBarSearch"] input').first()
      await input.fill('RCC', { timeout: 5000 })
      await page.waitForSelector('[class*="VPLocalSearchBox"] [class*="result"], [class*="VPLocalSearchBox"] [class*="results"]', { timeout: 8000 })
      notes.push('客户端搜索「RCC」→ 结果框出现')
    } catch (e) {
      fails.push(`客户端搜索交互失败：${String(e).split('\n')[0]}`)
    }

    // 5. 导读导航：书页可达 + book-guide 可导航
    if (guideLink) {
      const r = await page.goto(origin + guideLink, { waitUntil: 'domcontentloaded' })
      if (!r || r.status() !== 200) fails.push(`导读 ${guideLink} → HTTP ${r?.status()}`)
      else notes.push(`导读 ${guideLink} → 200`)
    } else {
      fails.push('首页未发现导读入口链接（reference/book.html）')
    }
    await httpOk('导读索引', `${BASE}book-guide/index.html`)
    await httpOk('导读 manifest', `${BASE}book-guide/manifest.json`)

    // 6. book/downloads（大文件只验 HTTP，不渲染）
    await httpOk('book HTML', `${BASE}book/mcu-deep-book.html`)
    for (const f of fs.readdirSync(path.join(mcuDir, 'downloads')).slice(0, 4)) {
      await httpOk('downloads: ' + f, `${BASE}downloads/${f}`)
    }
  } finally {
    await browser.close().catch(() => {})
    server.close()
  }
  fails.push(...netFails)
  return { ok: fails.length === 0, fails, notes, origin }
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
if (isMain) {
  const r = await runSmoke(parseArgs(process.argv.slice(2)))
  for (const n of r.notes) console.log(`✓ ${n}`)
  if (r.ok) {
    console.log(`挂载冒烟通过（${r.origin}${'/STM32'} 挂载，Chromium 真实导航 + 搜索交互）`)
  } else {
    for (const f of r.fails) console.error(`✖ ${f}`)
    process.exit(1)
  }
}
