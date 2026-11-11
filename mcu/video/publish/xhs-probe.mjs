// 小红书可行性探针：只读。导航、取文本、截图，不点任何提交类按钮、不上传任何东西。
// 为什么要先探：这条通道的字段上限（标题几个字、正文几个字、能不能挂外链）是台账的地基，
// 照别的平台的数字猜会直接把第一次试发变成废稿。
// 凭证纪律：cookie 只报数量与域名，一个值都不打。
import { chromium } from 'playwright'
import { mkdirSync } from 'node:fs'

const OUT = 'D:/Users/mcu/.temp/xhs-probe'
mkdirSync(OUT, { recursive: true })
function arg(name, dflt) {
  const i = process.argv.findIndex((a) => a === name || a.startsWith(`${name}=`))
  if (i < 0) return dflt
  const a = process.argv[i]
  return a.includes('=') ? a.slice(a.indexOf('=') + 1) || dflt : process.argv[i + 1] ?? dflt
}
// 默认落创作者中心真首页：/creator/home 实测回「你访问的页面不见了」，/new/home 才是活着的那一个
const URLS = (arg('--urls', 'https://creator.xiaohongshu.com/new/home') + '').split(',')

const browser = await chromium.connectOverCDP('http://127.0.0.1:9223')
const ctx = browser.contexts()[0]
// 自己新开一页，绝不复用常驻页：上一版写成 find(p => p.url().includes('xiaohongshu'))，
// 拿到的正是 daemon 那唯一一页，收尾 page.close() 把常驻页关掉，node 以 unsettled await 退出（码 13），
// 窗口跟着消失，人还没来得及扫码。
const page = await ctx.newPage()
page.setDefaultTimeout(45_000)
page.setDefaultNavigationTimeout(45_000)

const seen = []
for (const url of URLS) {
  const tag = url.replace(/^https?:\/\//, '').replace(/[^a-z0-9]+/gi, '-').slice(0, 48)
  console.log(`\n▶ ${url}`)
  try {
    await page.goto(url, { waitUntil: 'domcontentloaded' })
    await page.waitForTimeout(4000)
  } catch (e) {
    console.log(`  导航失败：${e.message.split('\n')[0]}`)
    continue
  }
  console.log(`  最终 URL：${page.url()}`)
  console.log(`  document.title：${await page.title()}`)
  const info = await page.evaluate(() => {
    const txt = (s) => (s || '').replace(/\s+/g, ' ').trim()
    const body = txt(document.body?.innerText).slice(0, 600)
    const labels = []
    for (const el of document.querySelectorAll('a,button,[role="tab"],[role="menuitem"],.menu-item,.side-menu-item,span[class*="title"],div[class*="tab"]')) {
      const t = txt(el.innerText || el.textContent)
      if (!t || t.length > 24) continue
      const r = el.getBoundingClientRect()
      if (!r.width || !r.height) continue
      if (!labels.includes(t)) labels.push(t)
    }
    const inputs = [...document.querySelectorAll('input,textarea,[contenteditable="true"]')].map((el) => ({
      tag: el.tagName.toLowerCase(),
      type: el.getAttribute('type') || null,
      ph: el.getAttribute('placeholder') || null,
      max: el.getAttribute('maxlength') || null,
    }))
    // 只报同域或小红书记名域下的相对/绝对路径，别的域（第三方统计、广告）整个丢掉：
    // 一是别把无关 URL 抄进台账，二是"这条线能不能挂外链"这类结论只能从自家路由读出来，猜出来的 URL 会 404 到底。
    const links = []
    for (const a of document.querySelectorAll('a[href]')) {
      const raw = a.getAttribute('href') || ''
      if (!raw || raw.startsWith('javascript:') || raw.startsWith('#')) continue
      let u
      try {
        u = new URL(raw, location.href)
      } catch {
        continue
      }
      if (!/xiaohongshu\.com$/.test(u.hostname)) continue
      const t = (a.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20)
      const key = `${u.pathname}${u.search}`
      if (!links.some((l) => l.href === key && l.text === t)) links.push({ href: key, text: t })
    }
    return { body, labels: labels.slice(0, 60), inputs, links: links.slice(0, 40) }
  })
  console.log(`  可见入口/按钮（${info.labels.length}）：${info.labels.join(' | ')}`)
  console.log(`  输入框（${info.inputs.length}）：${info.inputs.map((i) => `${i.tag}${i.type ? `:${i.type}` : ''}${i.ph ? `「${i.ph}」` : ''}${i.max ? ` max=${i.max}` : ''}`).join(' | ') || '无'}`)
  console.log(`  正文前 600 字：${info.body}`)
  console.log(`  同域路由链接（${info.links.length}）：${info.links.map((l) => `${l.href}${l.text ? `「${l.text}」` : ''}`).join(' | ') || '无'}`)
  const cookies = (await ctx.cookies('https://xiaohongshu.com')).filter((c) => /xiaohongshu/i.test(c.domain))
  console.log(`  该域名 cookie 条数：${cookies.length}（值不打印）`)
  const shot = `${OUT}/${tag}.png`
  await page.screenshot({ path: shot, fullPage: false })
  console.log(`  截图：${shot}`)
  seen.push({ url, finalUrl: page.url(), labels: info.labels.length, cookies: cookies.length })
}
console.log('\n汇总：' + seen.map((s) => `${s.finalUrl.replace(/^https?:\/\//, '').slice(0, 40)} 入口=${s.labels} cookie=${s.cookies}`).join(' ;; '))

// --click 只在"读字段上限"这一步用：点的是打开编辑器的入口，不是任何提交类按钮。
// 上限这类事实只能从编辑器里读（标题 maxlength、正文计数器 "0/1000"），首页看不到，
// 照着别的平台的数字猜，第一次试发就会变成废稿。
const CLICK = arg('--click', null)
if (CLICK) {
  console.log(`\n▶ 点「${CLICK}」（只开编辑器，不提交）`)
  const before = new Set(ctx.pages())
  await page.getByText(CLICK, { exact: false }).first().click({ timeout: 20_000 })
  await page.waitForTimeout(6000)
  const fresh = ctx.pages().filter((p) => !before.has(p))
  const target = fresh[0] ?? page
  if (fresh.length) {
    try {
      await target.waitForLoadState('domcontentloaded', { timeout: 30_000 })
    } catch {}
    console.log(`  弹出了新标签页：${target.url()}`)
  } else {
    console.log(`  当前页导航到：${target.url()}`)
  }
  const form = await target.evaluate(() => {
    const txt = (s) => (s || '').replace(/\s+/g, ' ').trim()
    const fields = [...document.querySelectorAll('input,textarea,[contenteditable="true"]')].map((el) => {
      const r = el.getBoundingClientRect()
      return {
        tag: el.tagName.toLowerCase(),
        type: el.getAttribute('type') || null,
        ph: el.getAttribute('placeholder') || null,
        max: el.getAttribute('maxlength') || null,
        accept: el.getAttribute('accept') || null,
        visible: !!(r.width && r.height),
      }
    })
    // 计数器形态（"0/20"、"0/1000"）是上限的第二来源：正文多是 contenteditable，
    // 不带 maxlength 属性，只能靠它自己印出来的分母。
    const counters = [...new Set(document.body.innerText.match(/\d+\s*\/\s*\d{1,5}/g) || [])].slice(0, 20)
    const hints = []
    for (const el of document.querySelectorAll('[class*="limit"],[class*="count"],[class*="tip"],[class*="desc"],small,em')) {
      const t = txt(el.innerText)
      if (t && t.length <= 60 && /\d/.test(t) && !hints.includes(t)) hints.push(t)
    }
    const buttons = []
    for (const b of document.querySelectorAll('button,[role="button"],div[class*="btn"],span[class*="btn"]')) {
      const t = txt(b.innerText)
      if (!t || t.length > 16) continue
      const r = b.getBoundingClientRect()
      if (!r.width || !r.height) continue
      if (!buttons.includes(t)) buttons.push(t)
    }
    return { fields, counters, hints: hints.slice(0, 25), buttons: buttons.slice(0, 40), body: txt(document.body.innerText).slice(0, 900) }
  })
  console.log(`  字段（${form.fields.length}）：`)
  for (const f of form.fields) {
    console.log(`    ${f.tag}${f.type ? `:${f.type}` : ''}${f.ph ? ` 「${f.ph}」` : ''}${f.max ? ` maxlength=${f.max}` : ''}${f.accept ? ` accept=${f.accept}` : ''}${f.visible ? '' : ' [隐藏]'}`)
  }
  console.log(`  计数器：${form.counters.join(' | ') || '无'}`)
  console.log(`  带数字的提示：${form.hints.join(' | ') || '无'}`)
  console.log(`  按钮（${form.buttons.length}）：${form.buttons.join(' | ')}`)
  console.log(`  正文前 900 字：${form.body}`)
  const shot2 = `${OUT}/form-${CLICK.replace(/[^0-9a-zA-Z一-龥]+/g, '-')}.png`
  await target.screenshot({ path: shot2 })
  console.log(`  截图：${shot2}`)
  if (fresh.length) await target.close()
}
await page.close()
// 自己开的页已经关了，但 CDP 那条 websocket 还挂着会让进程永远不退（上一版就是靠 timeout 掐掉的）。
// 这里显式退，绝不碰 browser.close()——那是把常驻窗口连同登录态一起带走。
process.exit(0)
