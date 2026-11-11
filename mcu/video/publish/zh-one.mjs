import { fileURLToPath } from 'node:url'
const MCU_ROOT = fileURLToPath(new URL('../../', import.meta.url)).replace(/[\\/]$/, '')
// 知乎视频投稿：一集一个进程从头走到尾。选择器全部沿用 zh-step.mjs 实测过的那套，不新猜。
//   node video/publish/zh-one.mjs --ep <id>            只填不发，走完把核对结果打出来
//   node video/publish/zh-one.mjs --ep <id> --publish  填完再发；仍要 .temp/zh-run/I_HAVE_USER_OK=<id> 放行
// 事实源只有 episode.json 的 publish.zhihu 和 video/out/<id>/，脚本里不写任何一集的字。
import { chromium } from 'playwright'
import { readFileSync, existsSync, mkdirSync, appendFileSync, writeFileSync } from 'node:fs'

const RUN = `${MCU_ROOT}/.temp/zh-run`
mkdirSync(RUN, { recursive: true })
function arg(n) { const i = process.argv.indexOf(n); return i >= 0 ? process.argv[i + 1] : null }
const EP = arg('--ep') || (() => { throw new Error('--ep 没给') })()
const DO_PUBLISH = process.argv.includes('--publish')
const TI = Number(arg('--title') ?? 0)

const epj = JSON.parse(readFileSync(`${MCU_ROOT}/video/episodes/${EP}/episode.json`, 'utf8'))
const P = epj.publish?.zhihu
if (!P) throw new Error(`episode.json 里没有 publish.zhihu：${EP}`)
const F = { video: `${MCU_ROOT}/video/out/${EP}/bilibili.mp4`, cover: `${MCU_ROOT}/video/out/${EP}/zhihu-cover.png` }
for (const [k, v] of Object.entries(F)) if (!existsSync(v)) throw new Error(`${k} 不存在：${v}`)

const browser = await chromium.connectOverCDP('http://127.0.0.1:9223')
const ctx = browser.contexts()[0]
// 上一个进程留下的 upload-video 标签会带着"已完成的上传会话"，新标签喂文件会卡死（实测 setInputFiles 30s 超时）。
// 所以开工前先把残留的清干净。
for (const p of ctx.pages()) if (/upload-video/.test(p.url())) { await p.close().catch(() => {}); console.log('关掉残留的 upload-video 标签') }
const page = await ctx.newPage()
page.setDefaultTimeout(180_000)
page.on('dialog', async (d) => {
  appendFileSync(`${RUN}/dialogs.log`, `${new Date().toISOString()} ${EP} ${d.type()} ${d.message()}\n`)
  if (d.type() === 'beforeunload') await d.accept().catch(() => {})
  else await d.dismiss().catch(() => {})
})
const shot = async (tag) => { try { await page.screenshot({ path: `${RUN}/${EP}-${tag}.png`, timeout: 20000 }) } catch {} }
const log = (...a) => console.log(`[${EP}]`, ...a)

try {
  await page.goto('https://www.zhihu.com/upload-video', { waitUntil: 'domcontentloaded', timeout: 60000 })
  await page.waitForTimeout(8000)

  // 0 知乎会把中断的上传留成「继续发布 / 忽略」提示。标题对得上就续传，别重传几十 MB 再留一条孤儿草稿。
  let resumed = false
  const prompt = await page.evaluate(() => {
    const t = document.body.innerText.replace(/\s+/g, ' ')
    const m = t.match(/《知乎视频用户协议》\s*(.*?)\s*继续发布\s*忽略/)
    return m ? m[1].trim().slice(0, 60) : null
  })
  if (prompt) {
    if (prompt === P.titles[TI].replace(/\s+/g, ' ').slice(0, 60)) {
      await page.getByText('继续发布', { exact: true }).first().click({ timeout: 15000 })
      await page.waitForTimeout(9000)
      resumed = true
      log(`续传草稿「${prompt}」，跳过上传`)
    } else {
      log(`⚠️ 页面上挂着另一条草稿「${prompt}」，不是本集的；点「忽略」放行（它仍留在草稿箱）`)
      await page.getByText('忽略', { exact: true }).first().click({ timeout: 10000 }).catch(() => {})
      await page.waitForTimeout(3000)
    }
  }

  // 1 片源。喂文件的 input 页面上有好几个，但首屏那个 .mp4 的就是"添加视频"——实测 feed 走它成功过。
  if (!resumed) {
    await page.locator('input[type=file][accept*=".mp4"]').first().setInputFiles(F.video, { timeout: 90000 })
    log('已投喂片源，等上传…')
    await page.waitForFunction(() => /上传成功/.test(document.body.innerText), null, { timeout: 900_000 })
    log('上传成功')
  }

  // 2 标题 + 介绍。介绍是 DraftEditor，fill() 不认，走键盘插入。
  await page.locator('.VideoUploadForm textarea').first().fill(P.titles[TI], { timeout: 20000 })
  const ed = page.locator('.VideoUploadForm [contenteditable=true]').first()
  await ed.click({ timeout: 20000 })
  await page.waitForTimeout(600)
  // 续传回来的草稿里介绍已经有字了，直接 insertText 会接在后面变成两遍。先全选清空。
  await page.keyboard.press('Control+a')
  await page.keyboard.press('Delete')
  await page.waitForTimeout(500)
  await page.keyboard.insertText(P.intro)
  await page.waitForTimeout(2500)
  log('标题/介绍已填')

  // 3 封面：点表头 → 面板里切「本地上传」→ 只喂"可见且在封面面板内"的那个 image input → 确认选择。
  await page.getByText(/选择视频封面|更改视频封面/).first().click({ timeout: 15000 })
  await page.waitForTimeout(3000)
  await page.getByText('本地上传', { exact: false }).first().click({ timeout: 15000 }).catch(() => {})
  await page.waitForTimeout(2000)
  const again = page.getByText('重新上传', { exact: true }).first()
  if (await again.count()) { await again.click({ timeout: 10000 }).catch(() => {}); await page.waitForTimeout(2000) }
  const img = page.locator('input[type=file][accept^="image"]')
  let fed = false
  for (let i = 0; i < await img.count(); i++) {
    const e = img.nth(i)
    const ok = await e.evaluate((el) => {
      const vis = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
      const modal = el.closest('[class*=Modal],[role=dialog]')
      return vis && !!modal && /封面/.test(modal.innerText || '')
    })
    if (!ok) continue
    await e.setInputFiles(F.cover, { timeout: 30000 })
    fed = true
    break
  }
  if (!fed) throw new Error('封面面板里没有"可见且在面板内"的 image input，停手不猜')
  await page.waitForTimeout(9000)
  await page.getByText('确认选择', { exact: true }).first().click({ timeout: 15000 })
  await page.waitForTimeout(7000)
  log('封面已确认')
  await shot('form')

  // 4 必填三项：视频标记 / 所属领域 / 原创视频。前两个的点击目标是盖在文字上的 aria-label 按钮。
  const pickInLayer = async (text) => {
    const hosts = page.locator('.Modal:visible, [role=dialog]:visible, [class*=Popover]:visible').filter({ hasText: text })
    const scope = (await hosts.count()) ? hosts.last() : page
    const opt = scope.getByText(text, { exact: true }).locator('visible=true').last()
    if (!(await opt.count())) throw new Error(`弹层里找不到可见的「${text}」`)
    await opt.click({ timeout: 10000 })
    await page.waitForTimeout(2500)
    const ok = scope.locator('button, [role=button]').filter({ hasText: /^(确认|确定)$/ }).last()
    if (await ok.count()) { await ok.click({ timeout: 10000 }).catch(() => {}); await page.waitForTimeout(2500) }
  }
  // 标记的点击目标是盖在文字上的 aria-label 按钮；领域没有 aria-label，实测是
  // button:has-text("选择领域")（选完文案会变成领域名，所以两个都列上）。
  const FIELDS = [
    [P.mark, '视频标记', ['button[aria-label="选择视频标记"]', 'button:has-text("选择标记")']],
    [P.domain, '所属领域', ['button:has-text("选择领域")', `button:has-text("${P.domain}")`, 'button[aria-label="选择所属领域"]']],
  ]
  for (const [text, name, sels] of FIELDS) {
    // 续传回来的草稿可能已经填过这一项；填过就别再点（点开后按钮文案会变，反而找不到）。
    const already = await page.evaluate(({ name, text }) => {
      const it = [...document.querySelectorAll('.VideoUploadForm-item')].find((e) => (e.innerText || '').includes(name))
      return !!it && (it.innerText || '').replace(/\s+/g, ' ').includes(text)
    }, { name, text })
    if (already) { log(`${name}=${text}（草稿里已有，跳过）`); continue }
    let hit = null
    for (const sel of sels) { const l = page.locator(sel).locator('visible=true').first(); if (await l.count()) { hit = l; break } }
    if (!hit) throw new Error(`找不到「${name}」的触发按钮（试过：${sels.join(' , ')}），停手`)
    await hit.click({ timeout: 15000 })
    await page.waitForTimeout(3500)
    await pickInLayer(text)
    log(`${name}=${text}`)
  }

  // 5 八项核对——和首条探针完全同一套断言，任何一项不过就不许碰发布按钮。
  const s = await page.evaluate(() => {
    const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
    const T = (e) => (e.innerText || e.value || '').replace(/\s+/g, ' ').trim()
    const form = document.querySelector('.VideoUploadForm')
    return {
      uploadOk: /上传成功/.test(document.body.innerText),
      titleVal: form?.querySelector('textarea')?.value ?? null,
      introLen: form?.querySelector('[contenteditable=true]')?.innerText.replace(/\s+/g, '').length ?? null,
      coverNat: (() => { const i = document.querySelector('.VideoUploadForm-image'); return i ? `${i.naturalWidth}×${i.naturalHeight}` : null })(),
      fields: [...document.querySelectorAll('.VideoUploadForm *')].filter((e) => !e.children.length && vis(e)).map(T)
        .filter((x) => /^(个人观点仅供参考|内容无需标注|含 AI 生成内容|科学工程|原创视频)$/.test(x)),
      originalChecked: (() => {
        const it = [...document.querySelectorAll('.VideoUploadForm-item')].find((e) => /原创视频/.test(e.innerText || ''))
        const c = it?.querySelector('input[type=checkbox]'); return c ? !!c.checked : null
      })(),
    }
  })
  const wantChars = P.intro.replace(/\s+/g, '').length
  const items = [
    ['片源已上传', s.uploadOk === true],
    ['标题一字不差', s.titleVal === P.titles[TI]],
    ['标题长度', s.titleVal ? [...s.titleVal].length <= 100 : false],
    ['介绍非空', (s.introLen ?? 0) > wantChars * 0.6],
    ['封面是 16:9 那张', s.coverNat === '1920×1080'],
    [`视频标记=${P.mark}`, s.fields.includes(P.mark)],
    [`所属领域=${P.domain}`, s.fields.includes(P.domain)],
    [`原创视频=${P.original ? '开' : '关'}`, s.originalChecked === !!P.original],
  ]
  for (const [k, ok] of items) log(`${ok ? '✅' : '❌'} ${k}`)
  log(`  介绍字数=${s.introLen}（本地=${wantChars}） 封面=${s.coverNat} 原创=${s.originalChecked}`)
  await shot('check')
  if (!items.every(([, ok]) => ok)) throw new Error('核对未过，停在这里')

  if (!DO_PUBLISH) {
    log('未带 --publish：只填不发，关页收工（草稿会留在知乎草稿箱，可回查）')
  } else {
    const gate = `${RUN}/I_HAVE_USER_OK=${EP}`
    if (!existsSync(gate)) throw new Error(`没有闸门文件 ${gate}；它只能来自对话里用户对这一条知乎投稿的点头`)
    log('闸门放行：' + readFileSync(gate, 'utf8').trim().replace(/\n/g, ' / '))

    const before = new Set(ctx.pages())
    // 点了「发布视频」页面不动时，光看正文分不出是前端自己拦下没发请求，还是请求发了被平台拒
    // （B站那边 p4 就是这个坑，投稿前挂一个 response 钩子才看清 add/v3 答了什么）。
    // 这里同样只记状态码和一行 message，正文一个字都不落盘。
    const seen = []
    page.on('response', async (res) => {
      if (res.request().method() === 'GET') return
      const u = res.url()
      if (!/zhihu\.com\/(api|_zh)/.test(u)) return
      let msg = ''
      try { const j = await res.json(); msg = String(j?.error?.message ?? j?.msg ?? j?.data?.error ?? '').slice(0, 90) } catch {}
      seen.push(`${res.status()} ${u.replace(/^https:\/\/[^/]+/, '').split('?')[0]}${msg ? ' ｜' + msg : ''}`)
    })
    await page.getByRole('button', { name: '发布视频' }).first().click({ timeout: 15000 })
    // 成功标志实测是弹窗「发布成功 / 感谢你的第 N 篇创作」，不是 URL 变化。
    await page.waitForFunction(() => /发布成功/.test(document.body.innerText), null, { timeout: 60000 })
      .then(() => log('弹窗：发布成功'))
      .catch(() => log('⚠️ 60s 内没看到「发布成功」弹窗'))
    await shot('published')
    if (seen.length) log('平台答了：\n   ' + [...new Set(seen)].slice(-8).join('\n   '))
    else log('‼️ 点完一个非 GET 请求都没发出去——是前端拦下的，去读下面这条表单状态')
    // 底部那条状态栏写的是「刚刚 · 草稿」还是「已发布」，是这一条到底落没落的直接凭据。
    const bar = await page.evaluate(() => {
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const bottom = [...document.querySelectorAll('*')].filter((e) => !e.children.length && vis(e) && /草稿|已发布|发布中|审核/.test(T(e))).map(T)
      const err = [...document.querySelectorAll('*')].filter((e) => !e.children.length && vis(e)
        && /(请|必须|不能为空|必填|失败|超出|稍后再试|未完成)/.test(T(e)) && T(e).length < 60).map(T)
      return { 状态栏: [...new Set(bottom)].slice(0, 6), 提示: [...new Set(err)].slice(0, 8) }
    })
    log('表单状态：', JSON.stringify(bar))
    await page.getByText('查看详情', { exact: false }).first().click({ timeout: 8000 }).catch(() => log('没有「查看详情」可点'))
    await page.waitForTimeout(4000)
    const fresh = ctx.pages().filter((p) => !before.has(p))
    for (const p of fresh) log('详情 URL=', p.url())
    if (!fresh.length) log('⚠️ 没拿到详情链接，稍后用 /creator/manage/creation 回查')
    // 知乎管理页的作品卡显示介绍正文、不显示标题（2026-10-29 实测），事后回读只能靠 pin id 锁行。
    // 把发布凭据落成 marker，verify --after 从这里面取 id。
    const pinPage = fresh.find((p) => /\/pin\/\d+/.test(p.url()))
    if (pinPage) {
      writeFileSync(
        `${RUN}/${EP}-published.txt`,
        `${pinPage.url()}\t${new Date().toISOString()}\t${readFileSync(gate, 'utf8').trim()}\n`,
      )
      log('发布凭据已落盘：', `${RUN}/${EP}-published.txt`)
      await pinPage.close().catch(() => {})
    }
  }
} finally {
  await page.close().catch(() => {})
  // 只关自己开的页：browser.close() 在 CDP 连接上会连带关掉常驻浏览器，三个平台共用它。
}
// 报错走上面的 throw，进程自己就退了；走通时 CDP socket 还挂着事件循环，显式退出让本进程的死带走连接。
process.exit(0)
