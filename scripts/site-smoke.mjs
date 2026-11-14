// B5 挂载冒烟：把 staging 按真实 Pages 挂载（/STM32/）起本地服务，用 Chromium
// 做真实浏览器验证：首页、新章深链、旧链跳转（meta-refresh 落地）、附录、
// 同源资源加载（requestfailed/HTTP>=400 监听）、quiz 交互。
// 用法（cwd=仓库根）：node scripts/site-smoke.mjs --root .temp/pages-site [--mount /STM32]
import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { chromium } from '@playwright/test'

export function parseArgs(argv) {
  const args = { root: '.temp/pages-site', mount: '/STM32' }
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
  return new Promise((resolve) => server.listen(0, '127.0.0.1', () => resolve(server)))
}

export async function smoke({ root, mount }) {
  const server = await serve(root, mount)
  const base = `http://127.0.0.1:${server.address().port}${mount}`
  const browser = await chromium.launch()
  const page = await browser.newPage()
  const failed = []
  page.on('requestfailed', (req) => failed.push(`requestfailed: ${req.url()}`))
  page.on('response', (res) => {
    if (res.url().startsWith(base) && res.status() >= 400) failed.push(`http ${res.status()}: ${res.url()}`)
  })
  const results = []
  const check = (name, ok, detail = '') => {
    results.push({ name, ok, detail })
    if (!ok) console.error(`FAIL ${name} ${detail}`)
  }
  try {
    // 1. 首页
    await page.goto(`${base}/`, { waitUntil: 'load' })
    check('首页加载', (await page.title()).length > 0)

    // 2. 新章深链（卷 1 第 9 章）
    await page.goto(`${base}/v1-drivers/09-gpio.html`, { waitUntil: 'load' })
    check('v1 ch09 深链', (await page.content()).includes('GPIO'))

    // 3. 旧链跳转：/mcu/stm32/03-gpio.html → v1 ch09
    await page.goto(`${base}/mcu/stm32/03-gpio.html`, { waitUntil: 'load' })
    await page.waitForURL('**/v1-drivers/09-gpio.html', { timeout: 5000 })
    check('旧链跳转落地 v1 ch09', page.url().includes('/v1-drivers/09-gpio.html'))

    // 4. 附录 A 深链
    await page.goto(`${base}/appendix/A-engineering-deep-read.html`, { waitUntil: 'load' })
    check('附录 A 深链', (await page.content()).includes('契约'))

    // 5. 第 40 章深链
    await page.goto(`${base}/v6-labs-projects/40-lab-method-instruments.html`, { waitUntil: 'load' })
    check('ch40 深链', (await page.content()).includes('实验'))

    // 6. 资源加载（动画 SVG）
    const res = await page.request.get(`${base}/anim/queue-passing.svg`)
    check('anim 资源 200', res.status() === 200, `status=${res.status()}`)

    // 7. quiz 交互（第 2 章：展开「答案与解析」details，答案文本可见）
    await page.goto(`${base}/v0-foundations/02-c-volatile-ub.html`, { waitUntil: 'load' })
    const answer = page.locator('.quiz-answer').first()
    if (await answer.count()) {
      const before = await answer.evaluate((el) => el.open)
      await answer.locator('summary').click()
      await page.waitForTimeout(200)
      const after = await answer.evaluate((el) => el.open)
      check('quiz 答案展开交互', after === true && before === false, `open ${before}→${after}`)
    } else {
      check('quiz 答案展开交互', false, '页面内没有 .quiz-answer 元素')
    }

    // 8. 资源失败清单
    check('同源资源无失败', failed.length === 0, failed.slice(0, 5).join(' | '))
  } finally {
    await browser.close()
    server.close()
  }
  return results
}

const isMain = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]
if (isMain) {
  const args = parseArgs(process.argv.slice(2))
  smoke(args).then((results) => {
    const bad = results.filter((r) => !r.ok)
    for (const r of results) console.log(`${r.ok ? 'OK  ' : 'FAIL'} ${r.name}${r.detail ? ' — ' + r.detail : ''}`)
    if (bad.length > 0) {
      console.error(`smoke failed: ${bad.length}/${results.length}`)
      process.exit(1)
    }
    console.log(`smoke passed: ${results.length}/${results.length}`)
  })
}
