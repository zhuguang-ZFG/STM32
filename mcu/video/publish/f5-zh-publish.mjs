// F5 在知乎停在草稿箱：点「发布视频」页面不动，上一版只看到 200 /api/v4/content/publish，
// 分不清是前端拦下、还是服务端答了 200 但 body 里带 error。这一版专治这个——
// 续传草稿（不重传 45 MB）、只点一次发布、把每个非 GET 请求的 error/code/message 原样打出来。
// 闸门沿用 .temp/zh-run/I_HAVE_USER_OK=f5-sem-mutex（用户在对话里点了「执行发布：…知乎全」）。
import { chromium } from 'playwright'
import { readFileSync, existsSync, writeFileSync, rmSync } from 'node:fs'
const EP = 'f5-sem-mutex'
const RUN = 'D:/Users/mcu/.temp/zh-run'
const gate = `${RUN}/I_HAVE_USER_OK=${EP}`
const marker = `${RUN}/${EP}-published.txt`
if (existsSync(marker)) {
  console.log(`‼️ ${EP} 知乎已有留痕（${readFileSync(marker, 'utf8').slice(0, 80)}）——再点就是发第二条。\n   确实要重发，自己确认后把这条留痕挪走再跑。`)
  process.exit(1)
}
if (!existsSync(gate)) throw new Error(`没有闸门文件 ${gate}——不点发布`)
const ep = JSON.parse(readFileSync(`D:/Users/mcu/video/episodes/${EP}/episode.json`, 'utf8'))
const WANT = ep.publish.zhihu.titles[0]

const b = await chromium.connectOverCDP('http://127.0.0.1:9223')
const ctx = b.contexts()[0]
const page = await ctx.newPage()
page.setDefaultNavigationTimeout(180_000)
page.setDefaultTimeout(180_000)
page.on('dialog', async (d) => { if (d.type() === 'beforeunload') await d.accept().catch(() => {}); else await d.dismiss().catch(() => {}) })
const log = (...a) => console.log(`[${EP}]`, ...a)
const seen = []
const leads = []
page.on('response', async (res) => {
  const rq = res.request()
  if (rq.method() === 'GET') return
  const u = res.url()
  if (!/zhihu\.com\/(api|_zh)/.test(u)) return
  let j = null
  try { j = await res.json() } catch {}
  const flat = []
  const walk = (o, path) => {
    if (o === null || o === undefined) return
    if (typeof o !== 'object') { if (/code|error|message|msg|reason|invalid|status|title|need|forbid/i.test(path)) flat.push(`${path}=${String(o).slice(0, 70)}`); return }
    for (const [k, v] of Object.entries(o)) walk(v, `${path}.${k}`)
  }
  if (j) walk(j, '')
  seen.push(`${res.status()} ${u.replace(/^https:\/\/[^/]+/, '').split('?')[0]}${flat.length ? ' ｜' + [...new Set(flat)].slice(0, 6).join(' ') : ''}`)
  // 留痕要的是「这条作品的地址」，不是页面地址；从发布接口里挖 zhihu 链接和 19 位 id
  if (j && /content\/publish|zvideo|pins?/i.test(u)) {
    const got = []
    const dig = (o, path) => {
      if (o === null || o === undefined) return
      if (typeof o === 'string') { if (/zhihu\.com\/(pin|zvideo|video)\//.test(o)) got.push(o); return }
      if (typeof o === 'number') { if (/id$/i.test(path) && o > 1e15) got.push(`${path}=${o}`); return }
      if (typeof o !== 'object') return
      for (const [k, v] of Object.entries(o)) dig(v, `${path}.${k}`)
    }
    dig(j, '')
    for (const g of [...new Set(got)]) leads.push(g)
  }
})
try {
  await page.goto('https://www.zhihu.com/upload-video', { waitUntil: 'domcontentloaded' })
  await page.waitForTimeout(12000)
  const prompt = await page.evaluate(() => {
    const t = document.body.innerText.replace(/\s+/g, ' ')
    const m = t.match(/《知乎视频用户协议》\s*(.*?)\s*继续发布\s*忽略/)
    return m ? m[1].trim().slice(0, 60) : null
  })
  if (prompt !== WANT.replace(/\s+/g, ' ').slice(0, 60)) throw new Error(`页面上挂的草稿是「${prompt}」，不是本集——停手不动别人的稿`)
  log('续传草稿：' + prompt)
  await page.getByText('继续发布', { exact: true }).first().click({ timeout: 15000 })
  await page.waitForTimeout(12000)

  const pre = await page.evaluate(() => {
    const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
    const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
    const btn = [...document.querySelectorAll('button,[role=button],span,div')].filter((e) => !e.children.length && T(e) === '发布视频' && vis(e))[0]
    const r = btn?.getBoundingClientRect()
    return {
      标题: document.querySelector('.VideoUploadForm textarea')?.value ?? null,
      状态栏: [...document.querySelectorAll('*')].filter((e) => !e.children.length && vis(e) && /草稿|上传成功|转码|审核/.test(T(e))).map(T).slice(0, 6),
      按钮: btn ? { 禁用: !!btn.disabled, 类: String(btn.className).slice(0, 60), 位置: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` } : null,
    }
  })
  log('点之前：', JSON.stringify(pre))
  if (!pre.按钮) throw new Error('找不到「发布视频」按钮，停手')

  await page.getByRole('button', { name: '发布视频' }).first().click({ timeout: 15000 })
  let ok = false
  for (let i = 0; i < 12; i++) {
    await page.waitForTimeout(5000)
    const s = await page.evaluate(() => {
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const modal = [...document.querySelectorAll('[class*=Modal],[class*=modal],[role=dialog]')].filter(vis).map(T).filter((x) => x.length > 4 && x.length < 400)
      const toast = [...document.querySelectorAll('[class*=Toast],[class*=toast],[class*=Notification],[class*=Message]')].filter(vis).map(T).filter(Boolean)
      const bar = [...document.querySelectorAll('*')].filter((e) => !e.children.length && vis(e) && /草稿|已发布|发布成功|审核/.test(T(e))).map(T)
      return { ok: /发布成功/.test(document.body.innerText), modal: [...new Set(modal)].slice(0, 3), toast: [...new Set(toast)].slice(0, 6), bar: [...new Set(bar)].slice(0, 5) }
    })
    log(`点之后 ${(i + 1) * 5}s：`, JSON.stringify(s))
    if (s.ok) { ok = true; break }
  }
  await page.screenshot({ path: `D:/Users/mcu/.temp/zh-run/${EP}-publish2.png`, fullPage: true, timeout: 30000 }).catch(() => {})
  if (ok) {
    // 接口没吐链接时，「查看详情」点开的落地页是第二个来源
    const before = new Set(ctx.pages())
    await page.getByText('查看详情', { exact: false }).first().click({ timeout: 8000 }).catch(() => log('没有「查看详情」可点'))
    await page.waitForTimeout(4000)
    for (const q of ctx.pages().filter((x) => !before.has(x))) { leads.push(q.url()); await q.close().catch(() => {}) }
    const line = `${[...new Set(leads)].join(' ') || '发布成功（接口和详情页都没给链接，去 /creator/manage/creation 回查）'}\t${new Date().toISOString()}\n`
    writeFileSync(marker, line)
    rmSync(gate)
    log('留痕已写：' + line.trim())
    log('闸门用掉了、已删：' + gate)
  } else {
    log('没写成：留痕不落、闸门留着——下次直接重跑本脚本即可')
  }
  console.log('\n非 GET 请求（只记状态码、路径和 error 类字段）：')
  for (const line of [...new Set(seen)].slice(-20)) console.log('  ' + line)
} finally {
  await page.close().catch(() => {})
  console.log('（只断开连接，浏览器留着）')
}
