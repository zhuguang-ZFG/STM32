// 连到 video/publish/douyin-daemon.mjs 起的那个常驻浏览器，按名字执行一步，打印这一步看到了什么。
// 每步都只做一件可逆的事；唯一不可逆的 publish 步要等 I_HAVE_USER_OK=<ep> 这个标记文件出现才动。
// 事实源：video/episodes/<ep>/episode.json 与 video/out/<ep>/，脚本里不写任何一集的字。
import { chromium } from 'playwright'
import { readFileSync, existsSync, mkdirSync, writeFileSync, appendFileSync } from 'node:fs'

const RUN = 'D:/Users/mcu/.temp/douyin-run'
mkdirSync(RUN, { recursive: true })
const step = process.argv[2]
function arg(name) {
  const i = process.argv.findIndex((a) => a === name || a.startsWith(`${name}=`))
  if (i < 0) return null
  const a = process.argv[i]
  return a.includes('=') ? a.slice(a.indexOf('=') + 1) || null : process.argv[i + 1] ?? null
}
// 旧写法：arg('--ep') 只认空格形式，手打的 --ep=s2-rcc 解析不出来，于是静默回落到 c3-volatile，
// 拿着别人的 episode.json 往当前稿件里填标题和描述。缺集号宁可停手，也不猜。
const EP = arg('--ep')
if (!EP) throw new Error('缺 --ep <episode-id>（--ep x 和 --ep=x 都认）——不猜这是哪一集')

const ep = JSON.parse(readFileSync(`D:/Users/mcu/video/episodes/${EP}/episode.json`, 'utf8'))
const pub = ep.publish.douyin
const F = {
  video: `D:/Users/mcu/video/out/${EP}/douyin.mp4`,
  cover: `D:/Users/mcu/video/out/${EP}/douyin-cover.png`,
  hcover: `D:/Users/mcu/video/out/${EP}/douyin-cover-1440x1080.png`,
  square: 'D:/Users/mcu/video/out/season-cover-1080.png',
}
// 封面取证实验要拿减法版本喂平台检测，但不能覆盖 video/out/ 里已交付的那两张，所以留一个显式改道。
if (arg('--cover')) F.cover = arg('--cover')
if (arg('--hcover')) F.hcover = arg('--hcover')

const browser = await chromium.connectOverCDP('http://127.0.0.1:9223')
const ctx = browser.contexts()[0]
// 标签页身份：window.name 是唯一能跟着这一页活过刷新和跳转的东西（B站那边用的是 __biliEp，
// 但那是页面自己的变量，刷新就没；这里要的正是"我导航走了再回来它还认得我"）。
// 为什么非要有身份：上一版按"第一个 creator.douyin.com 页"选页，而 s2 的稿子就开在那儿。
// 连投 4 集时 nav 的 goto 会把上一集没发出去的草稿直接导航掉——草稿没了就得重传视频。
const WORK = EP
// 标签页身份用 sessionStorage，不用 window.name：实测在 about:blank 上写 window.name，
// goto 到 creator.douyin.com 之后就被清了（Chrome 只在同源导航之间保留它），nav 盖的章活不过第一步。
// sessionStorage 是"这一页 × 这个源"私有，投稿全程都在 creator.douyin.com，SPA 换路由和刷新都还在，
// 别的标签页读不到同一个键——正好是"这一页是哪一集的稿"要的那个作用域。
const workOf = (p) => p.evaluate(() => { try { return sessionStorage.getItem('dywork') || '' } catch { return '' } }).catch(() => '')
const stamp = async (p, ep) => {
  await p.evaluate((v) => { try { sessionStorage.setItem('dywork', v) } catch {} }, ep)
  const got = await workOf(p)
  if (got !== ep) throw new Error(`盖章失败：写进去 ${JSON.stringify(ep)}，读回来 ${JSON.stringify(got)}——这一页没认出来，别往下走`)
}
// claim 是唯一一个跨所有标签页操作的步骤，必须排在选页之前——否则选页逻辑看它没有工作页，
// 会先替它新开一页，"认领"就变成了"又生一个"。
if (step === 'claim') {
  const pages = ctx.pages()
  const rows = []
  for (const [i, p] of pages.entries()) {
    const url = p.url()
    rows.push({
      i,
      url: url.slice(0, 78),
      work: await workOf(p),
      // 标题框里那句话就是这一页伺候的那份稿——认页只认这个，不认顺序
      title: /creator\.douyin\.com/.test(url)
        ? await p.evaluate(() => document.querySelector('input[placeholder^="填写作品标题"]')?.value ?? '(没有标题框)').catch(() => '(读不到)')
        : null,
    })
  }
  console.log(JSON.stringify(rows, null, 1))
  const n = arg('--tab')
  if (n !== null) {
    const i = Number(n)
    if (!Number.isInteger(i) || !pages[i]) throw new Error(`--tab 序号越界：${n}`)
    if (!/creator\.douyin\.com/.test(pages[i].url())) throw new Error(`第 ${i} 页不是抖音创作服务平台：${pages[i].url().slice(0, 60)}——不认`)
    const cur = await workOf(pages[i])
    if (cur && cur !== WORK) throw new Error(`第 ${i} 页已经认给 ${cur} 了，不抢`)
    await stamp(pages[i], WORK)
    console.log(`第 ${i} 页盖章 ${WORK}  URL=${pages[i].url().slice(0, 90)}`)
  }
  // 这里原来跟着一个 browser.close()：CDP 连接上的 close 会把常驻浏览器一起带走，
  // 而认完标签页正要退出本进程——process.exit 已经够让 socket 死了，浏览器得留着。
  process.exit(0)
}
let page = null
for (const p of ctx.pages()) if (await workOf(p) === WORK) { page = p; break }
if (!page) {
  if (step !== 'nav') {
    const held = []
    for (const p of ctx.pages()) { const n = await workOf(p); if (n) held.push(n) }
    throw new Error(`没有标成 ${WORK} 的标签页，而这次要跑的是 ${step}——不猜哪一页是这一集的稿。`
      + `先跑 nav（它会自己新开一页并盖章），或 claim --list 看清现有页再用 claim --tab=<i> 认领。`
      + (held.length ? ` 现在被认领的页：${held.join(' / ')}` : ' 现在一个都没被认领'))
  }
  // nav 永远新开一页，绝不复用别人开着的稿——复用就是拿别人的草稿填这一集的字。
  page = await ctx.newPage()
  console.log(`新开一页给 ${WORK} 用（盖章要等 goto 落到 creator.douyin.com 之后）`)
}
page.setDefaultTimeout(90_000)
// 上一版对所有对话框一律 accept，结果离开发布页时那个「确认删除草稿」也被我顺手点了——
// 页面上就冒出过一条 删除成功。现在只放行 beforeunload，其余原样记下来，交给用户判断。
page.on('dialog', async (d) => {
  const line = `${new Date().toISOString()} type=${d.type()} message=${d.message()}`
  appendFileSync(`${RUN}/dialogs.log`, `${line}\n`)
  console.log('DIALOG', line)
  if (d.type() === 'beforeunload') await d.accept().catch(() => {})
  else await d.dismiss().catch(() => {})
})

async function shot(name) {
  const p = `${RUN}/${EP}-${name}.png`
  // 调试截图不该把投稿本身弄死：这张投稿页很高、上面还挂着预览视频，fullPage 有概率 90s 不返回
  // （实验室里换封面时就死在这儿——封面其实已经喂进去了，死的是后面的截图）。
  try {
    await page.screenshot({ path: p, fullPage: true, timeout: 20000 })
  } catch {
    await page.screenshot({ path: p, timeout: 20000 }).catch(() => {})
    console.log('📷', p, '(整页超时，退回视口截图)')
    return p
  }
  console.log('📷', p, '  URL:', page.url())
  return p
}

async function describe() {
  const rows = await page.evaluate(() => {
    const vis = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
    const t = (el) => (el.innerText || el.value || '').replace(/\s+/g, ' ').trim()
    return {
      inputs: [...document.querySelectorAll('input')].filter((e) => vis(e) || e.type === 'file').map((e) => ({ type: e.type, ph: e.getAttribute('placeholder'), accept: e.getAttribute('accept')?.slice(0, 30), name: e.name })),
      editors: [...document.querySelectorAll('[contenteditable="true"]')].map((e) => ({ ph: e.getAttribute('data-placeholder') ?? e.getAttribute('placeholder'), cls: e.className.slice(0, 60), text: t(e).slice(0, 40) })),
      buttons: [...document.querySelectorAll('button,[role="button"]')].filter(vis).map((e) => t(e).slice(0, 24)).filter(Boolean),
      counter: [...document.querySelectorAll('*')].map((e) => t(e)).find((s) => /^\d+ \/ \d+$/.test(s)) ?? null,
    }
  })
  console.log(JSON.stringify(rows, null, 1))
  return rows
}

// ---- 封面模态的三个公共动作 ----------------------------------------------
// 一次完整的封面设置 = 开槽位 → 选 tab 并投喂 → 点「完成」。少了最后一步，平台会退回视频首帧：
// 2026-10-21 实测 f5/s5 只跑 cover，作品列表缩略图是首帧；改走 coverup(投喂)+coverset(完成) 才落盘。
async function openCoverSlot(slot) {
  const slots = page.getByText('选择封面', { exact: true })
  const n = await slots.count()
  if (n <= slot) throw new Error(`页上只剩 ${n} 个"选择封面"位，取不到第 ${slot + 1} 个`)
  await slots.nth(slot).scrollIntoViewIfNeeded()
  await slots.nth(slot).click()
  await page.waitForTimeout(3000)
}

async function openCoverThumb(which) {
  // 已经设过封面之后，页面上就没有「选择封面」占位了，只剩「竖封面3:4 / 横封面4:3」两张缩略图；
  // 点缩略图本身（img 是 label 的前一个 img 兄弟）才重新开模态。
  // 缩略图上盖着一层 hover 遮罩，普通 click 会被它拦下无限重试——人手点的也是遮罩，所以直接 force。
  const label = which === 'v' ? '竖封面3:4' : '横封面4:3'
  const thumb = page.locator(`xpath=//div[text()="${label}"]/preceding::img[1]`)
  if (!(await thumb.count())) throw new Error(`找不到「${label}」缩略图，页面上封面位可能还没生成`)
  await thumb.first().click({ force: true, timeout: 15_000 })
  await page.waitForTimeout(3500)
}

async function pickCoverTab(which) {
  // 「设置X封面」这五个字页面上会出现两处：编辑器顶部的 tab，和竖封面点完「完成」后叠上来的
  // 「设置横封面获更多流量」推广模态里的按钮。文案完全相同，推广层在 DOM 里更靠后、同 z-index
  // 盖满视口，所以 .first() 必然点到被盖住的那个，重试到超时。先把推广那层点掉，它本身就是入口。
  const promo = page.locator('.dy-creator-content-modal-wrap', { hasText: '获更多流量' })
  if (await promo.count()) {
    const go = promo.getByText(which === 'v' ? '设置竖封面' : '设置横封面', { exact: true }).last()
    if (await go.count()) {
      await go.click({ timeout: 10000 })
      await page.waitForTimeout(3000)
      console.log(`推广模态「获更多流量」→ 点它的「设置${which === 'v' ? '竖' : '横'}封面」，剩 ${await page.locator('.dy-creator-content-modal-wrap').count()} 层`)
    }
  }
  const tab = page.getByText(which === 'v' ? '设置竖封面' : '设置横封面', { exact: true }).first()
  await tab.click({ timeout: 15_000 })
  await page.waitForTimeout(2500)
}

async function feedCoverFile(which) {
  const file = which === 'v' ? F.cover : F.hcover
  if (!existsSync(file)) throw new Error(`封面不存在：${file}`)
  // 模态里有两个 .semi-upload：左边那个（x≈72）是「生成参考图」，喂进去只会变成 AI 的参考图；
  // 真正换封面的是右边带「点击上传文件…」文案的那个。上一版 .first() 就踩在这儿。
  const up = page.locator('.dy-creator-content-modal-body .semi-upload').filter({ hasText: '点击上传文件' })
  if (await up.count() !== 1) throw new Error(`「上传封面」拖拽区匹配到 ${await up.count()} 个，不猜`)
  await up.locator('input[type=file]').first().setInputFiles(file)
  await page.waitForTimeout(9000)
  console.log(`已投喂 ${which === 'v' ? '竖' : '横'} 封面 ← ${file}`)
}

async function commitCoverModal() {
  // 画布上选中的这张就是结果，点「完成」才落盘。AI 封面在后台跑时模态文案有「生成中」，
  // 这时候点完成有概率把刚上传的那张冲掉（s16 实测中过一次），所以先等它跑完。
  for (let i = 0; i < 20; i++) {
    const busy = await page.evaluate(() => {
      const m = document.querySelector('.dy-creator-content-modal-body')
      return m ? /生成中/.test(String(m.innerText)) : false
    })
    if (!busy) break
    await page.waitForTimeout(2000)
  }
  await page.getByText('完成', { exact: true }).last().click({ timeout: 15_000 })
  await page.waitForTimeout(6000)
  const still = await page.locator('.dy-creator-content-modal-body').count()
  console.log(`已点完成，模态残留=${still}`)
  return still
}

const STEPS = {
  async status() {
    console.log('URL:', page.url())
    await describe()
    await shot('status')
  },
  async pick() {
    if (!existsSync(F.video)) throw new Error(`成片不存在：${F.video}`)
    const inp = page.locator('input[type=file][accept*="video"]').first()
    await inp.setInputFiles(F.video)
    console.log('已选：', F.video, '——等平台解析')
    await page.waitForTimeout(25_000)
    await describe()
    await shot('picked')
  },
  async text() {
    // 标题与简介在 web 端是两个字段（手机端只有描述一个框），所以这里分开落：
    // 标题 = episode.json 里那条 douyin titles[0]；简介 = caption 逐字（含换行和话题）
    const [l1, l2 = '', topics = ''] = pub.caption.split('\n')
    const title = pub.titles[0]
    const intro = [l1, l2].filter(Boolean).join('\n')
    await page.locator('input[placeholder^="填写作品标题"]').fill(title)
    const ed = page.locator('div[contenteditable="true"]').first()
    await ed.click()
    await page.keyboard.insertText(intro)
    await page.waitForTimeout(800)
    // 话题必须走平台的联想，直接敲 #xxx 只会留一串纯文本，进不了话题池
    for (const tag of topics.split(/\s+/).filter(Boolean)) {
      await page.keyboard.type(tag.slice(1), { delay: 120 }) // 编辑器里 # 是触发符，重复打会弹两层
      await page.waitForTimeout(1500)
      await page.keyboard.press('Enter')
      await page.waitForTimeout(600)
      await page.keyboard.press('Space')
    }
    await describe()
    await shot('text')
    console.log('标题:', title)
    console.log('简介:', JSON.stringify(intro))
  },
  async retxt() {
    // 上一版把 '#' 触发符去掉了，话题就变成一串纯文本粘在第二句尾巴上。
    // 这次照平台的走法：# → 等联想 → 打字 → 等面板 → 选中，每步都验一次 chip 数，不靠猜。
    const ed = page.locator('div[contenteditable="true"]').first()
    await ed.click()
    await page.keyboard.press('Control+a')
    await page.keyboard.press('Delete')
    await page.waitForTimeout(600)
    const [l1, l2 = '', topics = ''] = pub.caption.split('\n')
    await page.keyboard.insertText([l1, l2].filter(Boolean).join('\n'))
    await page.keyboard.press('Enter')
    const chips = async () => page.evaluate(() => {
      const e = document.querySelector('div[contenteditable="true"]')
      if (!e) return { n: -1, html: '' }
      const links = e.querySelectorAll('a,span[data-entity],[data-entity]')
      return { n: links.length, html: e.innerHTML.slice(0, 400), text: e.innerText.replace(/​/g, '') }
    })
    const seen = []
    for (const tag of topics.split(/\s+/).filter(Boolean)) {
      const name = tag.slice(1)
      await page.keyboard.type('#', { delay: 80 })
      await page.waitForTimeout(700)
      await page.keyboard.type(name, { delay: 150 })
      await page.waitForTimeout(2200)
      const panel = await page.locator('.semi-popup, [role="listbox"], [class*="topic"]').filter({ hasText: new RegExp(name, 'i') }).count()
      if (panel) {
        await page.keyboard.press('Enter')
        await page.waitForTimeout(700)
      }
      const c = await chips()
      seen.push(`${tag} 面板=${panel} chip=${c.n}`)
      await page.keyboard.press('Space')
      await page.waitForTimeout(400)
    }
    const c = await chips()
    console.log('话题过程：', seen.join(' | '))
    console.log('编辑器文本：', JSON.stringify(c.text))
    console.log('chip 总数：', c.n)
    console.log('innerHTML：', c.html)
    await describe()
    await shot('retxt')
  },
  async topicprobe() {
    // 直接在编辑器里敲 # 不弹联想（面板=0 chip=0），说明这条路平台不认键盘事件。
    // 编辑器下面那个「#添加话题」才是正规入口，探它点开长什么样。
    const btn = page.locator('text=#添加话题').first()
    console.log('找到 #添加话题：', await btn.count())
    await btn.click()
    await page.waitForTimeout(2500)
    const pop = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const t = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      return {
        dialogs: [...document.querySelectorAll('[role="dialog"],.semi-modal,.semi-popup,.semi-popover')].filter(vis).map((e) => t(e).slice(0, 120)),
        inputs: [...document.querySelectorAll('input')].filter((e) => vis(e)).map((e) => ({ ph: e.getAttribute('placeholder'), cls: e.className.slice(0, 40) })),
        focused: (() => { const a = document.activeElement; return a ? a.tagName + '.' + (a.className || '').toString().slice(0, 50) + ' ph=' + (a.getAttribute?.('placeholder') ?? '') : null })(),
      }
    })
    console.log(JSON.stringify(pop, null, 1))
    await shot('topicprobe')
  },
  async season() {
    // 合集标题框写死 0/20，清单里那个 22 字的名字塞不进去；标题用 series.json 的 series，
    // 口号那句移到合集简介（上限 200 字）。
    const series = JSON.parse(readFileSync('D:/Users/mcu/video/series.json', 'utf8')).series
    const name = arg('--name') ?? series
    const desc = arg('--desc') ?? '屏上每个数都是本机跑的。80 章图文 + 101 张动画，每条视频配一条能重跑的无板命令。'
    if ([...name].length > 20) throw new Error(`合集标题 ${[...name].length} 字 > 20：${name}`)
    await page.locator('input[placeholder="请输入合集的标题"]').fill(name)
    await page.locator('textarea, [contenteditable="true"]').first().fill?.(desc).catch?.(() => {})
    const ta = page.locator('textarea').first()
    if (await ta.count()) await ta.fill(desc)
    if (existsSync(F.square)) {
      await page.getByText('选择封面', { exact: true }).first().click()
      await page.waitForTimeout(2500)
      await page.locator('input[type=file][accept*="image"]').last().setInputFiles(F.square)
      await page.waitForTimeout(5000)
    }
    console.log(`合集标题 ${[...name].length} 字：${name}`)
    await describe()
    await shot('season-filled')
  },
  async click() {
    const want = arg('--text')
    if (!want) throw new Error('--text 必填')
    const el = page.getByText(want, { exact: arg('--fuzzy') ? false : true }).first()
    await el.scrollIntoViewIfNeeded().catch(() => {})
    await el.click({ timeout: 8000 }).catch(async () => {
      console.log('普通点击等不到，走 evaluate 直接触发')
      await el.evaluate((n) => n.click())
    })
    await page.waitForTimeout(4000)
    console.log('URL:', page.url())
    await describe()
    await shot(`click-${want}`)
  },
  async menu() {
    const want = arg('--text') ?? '内容管理'
    // 导航栏是折叠的图标栏，文字 span 一直"不可见"，普通 click 会等到超时——点它的可点祖先
    const item = page.locator(`.douyin-creator-master-navigation-item-text:text-is("${want}")`).first()
    await item.evaluate((el) => {
      let n = el
      while (n && n !== document.body) { if (n.onclick || n.getAttribute('role') === 'button' || /navigation-item(?!-text)/.test(n.className)) break; n = n.parentElement }
      ; (n ?? el.closest('div')).click()
    })
    await page.waitForTimeout(4000)
    const rows = await page.evaluate(() => ({
      url: location.href,
      links: [...document.querySelectorAll('a[href]')].map((e) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 18), h: e.getAttribute('href') })).filter((r) => r.t),
      texts: [...document.querySelectorAll('li,span,div')].map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter((t) => t && t.length <= 10 && /合集|管理|草稿|作品/.test(t)),
    }))
    console.log('URL:', rows.url)
    console.log('链接：', JSON.stringify([...new Map(rows.links.map((r) => [r.h, r.t])).values()].slice(0, 40), null, 1))
    console.log('相关文字：', [...new Set(rows.texts)].slice(0, 25).join(' | '))
    await shot('menu')
  },
  async links() {
    const u = arg('--url')
    if (u) { await page.goto(u, { waitUntil: 'domcontentloaded' }); await page.waitForTimeout(6000) }
    const rows = await page.evaluate(() => [...document.querySelectorAll('a[href]')]
      .map((e) => ({ t: (e.innerText || '').replace(/\s+/g, ' ').trim().slice(0, 20), h: e.getAttribute('href') }))
      .filter((r) => r.h && r.h !== '#'))
    console.log(JSON.stringify([...new Map(rows.map((r) => [r.h, r])).values()], null, 1))
    console.log('菜单文字：', await page.evaluate(() => [...document.querySelectorAll('[class*="menu"] , [class*="nav"]')]
      .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter((t) => t && t.length < 60).slice(0, 30).join(' | ')))
  },
  async nav() {
    const u = arg('--url')
    if (u) {
      await page.goto(u, { waitUntil: 'domcontentloaded' })
      await page.waitForTimeout(6000)
      await stamp(page, WORK)
    }
    // 发布页的合集下拉里只有「不选择合集」，没有新建入口——那就要去合集管理页建。
    // 先把站内所有提到"合集"的可点元素和链接列出来，不猜 URL。
    const hits = await page.evaluate(() => {
      const out = []
      for (const e of document.querySelectorAll('a,button,[role="button"],li,span,div')) {
        const t = (e.innerText || '').replace(/\s+/g, ' ').trim()
        if (t && t.length <= 14 && t.includes('合集') && (e.offsetWidth || e.offsetHeight)) {
          out.push({ t, tag: e.tagName.toLowerCase(), href: e.getAttribute('href'), cls: (e.className || '').toString().slice(0, 40) })
        }
      }
      return out.slice(0, 40)
    })
    console.log(JSON.stringify([...new Map(hits.map((h) => [h.t + h.href, h])).values()], null, 1))
    console.log('当前 URL:', page.url())
  },
  async modaldump() {
    // 上一版按「上传封面」这个文案找按钮，等 90 s 超时。把模态里所有能点的东西连 className
    // 一起打出来，别再猜平台叫什么名字。
    const rows = await page.evaluate(() => {
      const vis = (el) => !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
      const t = (el) => (el.innerText || el.value || '').replace(/\s+/g, ' ').trim()
      const modal = [...document.querySelectorAll('[class*="modal"],[class*="Modal"],[role="dialog"]')].filter(vis).pop()
      if (!modal) return { modal: null, fileInputs: document.querySelectorAll('input[type=file]').length }
      const texts = [...modal.querySelectorAll('*')]
        .filter((e) => vis(e) && e.children.length === 0)
        .map((e) => t(e)).filter(Boolean)
      const clickables = [...modal.querySelectorAll('button,[role="button"],a,[class*="btn"],[class*="upload"],[class*="tab"]')]
        .filter(vis)
        .map((e) => ({ tag: e.tagName, cls: e.className.toString().slice(0, 70), t: t(e).slice(0, 30) }))
      return {
        modalCls: modal.className.toString().slice(0, 80),
        texts: [...new Set(texts)].slice(0, 60),
        clickables,
        fileInputs: modal.querySelectorAll('input[type=file]').length,
      }
    })
    console.log(JSON.stringify(rows, null, 1))
    await shot('modaldump')
  },
  async coveredit() {
    // 封面一旦设过，页面上就没有「选择封面」了，只剩「竖封面3:4 / 横封面4:3」两张缩略图，
    // 要点缩略图本身（img 是 label 的前一个 img 兄弟）才重新开模态。
    const which = arg('--which') === 'h' ? 'h' : 'v'
    const label = which === 'v' ? '竖封面3:4' : '横封面4:3'
    const thumb = page.locator(`xpath=//div[text()="${label}"]/preceding::img[1]`)
    if (!(await thumb.count())) throw new Error(`找不到「${label}」缩略图，页面上封面位可能还没生成`)
    // 缩略图上盖着一层 hover 遮罩（div.background-*），正常 click 会被它拦下无限重试。
    // 人手点的时候吃这个事件的也正是遮罩，所以直接 force：跳过命中检查，点同一个坐标。
    await thumb.first().click({ force: true, timeout: 15_000 })
    await page.waitForTimeout(3500)
    const open = await page.locator('.dy-creator-content-modal-body').count()
    console.log(`点了「${label}」，模态=${open}`)
    if (open) await this.modaldump()
    else await shot(`coveredit-${which}`)
  },
  async coverup() {
    // 模态实测结构（见 modaldump）：顶部两个 tab「设置竖封面/设置横封面」，中间一个 semi-upload
    // 拖拽区（「上传封面 / 点击上传文件或拖拽文件到这里」），右下角「封面检测 | 设置X封面 | 完成」。
    const which = arg('--which') === 'v' ? 'v' : 'h'
    if (!(await page.locator('.dy-creator-content-modal-body').count())) await this.coveredit()
    await pickCoverTab(which)
    await feedCoverFile(which)
    await this.modaldump()
  },
  async coverset() {
    // 只做「点完成」这一件事；模态右下角在「竖」tab 是「重新检测 | 取消 | 完成」，
    // 在「横」tab 多一个「设置竖封面」（把横图复用到竖的便捷键，不是必经步骤）。
    await commitCoverModal()
    await describe()
    await shot(`coverdone-${arg('--which') === 'h' ? 'h' : 'v'}`)
  },
  async covermodal() {
    // 一次性把某一面封面设完：没有开着的模态就先点「选择封面」，再走 tab → 投喂 → 完成。
    // 旧版按「上传封面」这个按钮文案去找，页面上根本没有这个文案（挂 90 s 超时），
    // 现在统一走 feedCoverFile 里那个带「点击上传文件」的拖拽区。
    const which = arg('--which') === 'h' ? 'h' : 'v'
    if (!(await page.locator('.dy-creator-content-modal-body').count())) {
      if (!(await page.getByText('选择封面', { exact: true }).count())) {
        throw new Error('页上没有"选择封面"位，也没有开着的模态')
      }
      await openCoverSlot(0)
    }
    await pickCoverTab(which)
    await feedCoverFile(which)
    const still = await commitCoverModal()
    if (still) throw new Error(`点完成后封面模态还在（${still} 层），这张封面没落盘`)
    console.log(`${which === 'v' ? '竖' : '横'}封面已上传并点完成`)
    await describe()
    await shot(`covermodal-${which}`)
  },
  async cover() {
    // slot 0 = 竖封面 3:4（douyin-cover.png），slot 1 = 横封面 4:3（douyin-cover-1440x1080.png）。
    // 只设一个，右侧"快速检测"会一直挂着"横/竖双封面缺失"的黄字。
    //
    // 这一步以前只做「开模态 + 塞文件 + 点裁切框的保存」，没在模态里点「完成」——
    // 平台就把封面退回视频首帧（2026-10-21 f5/s5 实测：作品列表缩略图是首帧，改走 coverup+coverset 才落盘）。
    // 现在一步到位：开槽位 → 选 tab 并投喂 → 点完成，完成没让模态消失就报错，不再"看起来成功"。
    const slot = Number(arg('--slot') ?? 0)
    const which = slot ? 'h' : 'v'
    // 新稿有「选择封面」占位；已经设过一面之后占位就没了，退回点缩略图那条路。
    if (await page.getByText('选择封面', { exact: true }).count() > slot) await openCoverSlot(slot)
    else await openCoverThumb(which)
    await pickCoverTab(which)
    await feedCoverFile(which)
    const still = await commitCoverModal()
    if (still) throw new Error(`点完成后封面模态还在（${still} 层），这张封面没落盘——别往下走`)
    console.log(`封面 slot${slot}（${which === 'v' ? '竖' : '横'}）已落盘`)
    await describe()
    await shot(`cover${slot}`)
  },
  async title() {
    // 标题框在封面模态那通操作之后被清空过一次（0/30），发布前必须重新量一遍，不能假设还在。
    const box = page.locator('input[placeholder^="填写作品标题"]')
    if (!(await box.count())) throw new Error('找不到标题框')
    const title = pub.titles[0]
    await box.first().fill(title)
    await page.waitForTimeout(2000)
    const got = await box.first().inputValue()
    const cnt = await page.evaluate(() => {
      const t = (el) => (el.innerText || '').replace(/\s+/g, ' ').trim()
      return [...document.querySelectorAll('*')].map((e) => t(e)).find((s) => /^\d+ \/ 30$/.test(s)) ?? null
    })
    console.log(`标题=${JSON.stringify(got)}  ${got === title ? '[中]' : '[失]'}  计数=${cnt}`)
    await shot('title')
  },
  async verify() {
    // 发布前那一屏要能自己说清楚：标题、简介、合集、两张封面、快速检测。
    // 上一版两个毛病：desc 取成了另一个 contenteditable 所以是空串；detect 用「包含」匹配
    // 把每一层祖先 div 都打了出来，一条刷屏。都改成只取叶子节点。
    const rows = await page.evaluate(() => {
      const leaf = (el) => !el.children.length
      const t = (el) => (el.innerText || '').replace(/\s+/g, ' ').replace(/​/g, '').trim()
      const only = (re) => [...document.querySelectorAll('span,div,input')].filter(leaf)
        .map((e) => t(e) || e.value || '').filter((s) => re.test(s))
      const cover = (label) => {
        const a = [...document.querySelectorAll('div')].filter(leaf).find((e) => t(e) === label)
        if (!a) return null
        // 缩略图不是 label 的子节点，是文档序里它前面最近的那个 img（和 coveredit 的 XPath 同一个走法）
        const img = [...document.querySelectorAll('img')].filter((n) => n.compareDocumentPosition(a) & Node.DOCUMENT_POSITION_FOLLOWING).pop()
        return img?.src?.startsWith('blob:') ? 'blob ✓' : (img?.src ? img.src.slice(0, 40) : '无图')
      }
      return {
        title: document.querySelector('input[placeholder^="填写作品标题"]')?.value ?? null,
        titleCnt: only(/^\d+\/30$/)[0] ?? null,
        desc: t(document.querySelector('.zone-container.editor-kit-container') || document.querySelector('div[contenteditable="true"]')),
        descCnt: only(/^\d+ \/ \d+$/)[0] ?? null,
        coverV: cover('竖封面3:4'), coverH: cover('横封面4:3'),
        season: only(/^通往单片机之路$/).length ? '通往单片机之路' : null,
        episodeNo: only(/^第\d+集$/)[0] ?? null,
        detect: [...new Set(only(/检测通过|双封面缺失|低质|未见异常/))].slice(0, 4),
        visibility: only(/^公开$/).length ? '公开' : null,
        // 自主声明没选时页面不弹窗、不报错，只是点「发布」没反应——所以它必须进核对项，
        // 不能等发布失败才发现（f3 第一次就是这么静默卡住的）。
        declare: document.querySelector('.selectText-XSrMFZ')?.innerText?.trim() ?? null,
      }
    })
    console.log(JSON.stringify(rows, null, 1))
    await shot('verify')
    return rows
  },
  async seasonpick() {
    await page.getByText('请选择合集').first().click()
    await page.waitForTimeout(2500)
    const name = JSON.parse(readFileSync('D:/Users/mcu/video/series.json', 'utf8')).series
    const opt = page.getByText(name, { exact: true }).last()
    if (!(await opt.count())) throw new Error(`下拉里没有合集「${name}」`)
    await opt.click()
    await page.waitForTimeout(2500)
    console.log('已选合集：', name)
    await describe()
    await shot('seasonpick')
  },
  async coll() {
    await page.locator('text=请选择合集').first().click()
    await page.waitForTimeout(2500)
    const opts = await page.evaluate(() => [...document.querySelectorAll('[role="listbox"] *, .semi-select-option')].map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()).filter(Boolean).slice(0, 20))
    console.log('合集下拉可见项：', JSON.stringify([...new Set(opts)], null, 1))
    await shot('coll')
  },
  // 自主声明是必填项：没选的话点「发布」不会报错弹窗，只在提交后把「请选择自主声明」
  // 那行标红，页面纹丝不动——f3 第一次发布就是这么静默失败的，而 publish() 只记了 URL 就当成了成功。
  // 声明文案从 episode.json 的 publish.douyin.declare 读，脚本不替任何一集猜一个。
  async declare() {
    const want = pub.declare
    if (!want) throw new Error(`${EP} 的 publish.douyin 里没有 declare——自主声明是必填项，不猜`)
    const shown = () => page.evaluate(() => {
      const row = [...document.querySelectorAll('*')].find((e) => e.children.length === 0 && (e.innerText || '').trim() === '自主声明')
      if (!row) return '(页面上没有自主声明这一行)'
      let box = row.parentElement
      for (let k = 0; k < 5 && box; k++) { const hit = box.querySelector('.selectText-XSrMFZ'); if (hit) return hit.innerText.trim(); box = box.parentElement }
      return '(找不到显示框)'
    })
    const openWraps = () => page.locator('.semi-modal-wrap:visible')
    if ((await shown()).includes(want)) { console.log('自主声明已是：', want, '——不重开模态'); await shot('declare'); return }
    // 模态可能上一次没关干净（Escape 关不掉它，只有取消/X 能）。开着就别再点触发器，那会被它自己挡住。
    if (!(await openWraps().count())) {
      await page.locator('div.selectText-XSrMFZ').first().click()
      await page.waitForTimeout(2000)
    }
    const modal = page.locator('.semi-modal-wrap:visible').last()
    if (!(await modal.count())) throw new Error('点了自主声明却没弹出声明模态——不猜它现在要什么')
    const radio = modal.locator('label.semi-radio').filter({ hasText: want })
    if (!(await radio.count())) {
      const have = await modal.locator('label.semi-radio').allInnerTexts()
      throw new Error(`声明模态里没有「${want}」这一项，平台给的是：${have.map((s) => s.trim()).join(' / ')}`)
    }
    await radio.first().click()
    await page.waitForTimeout(800)
    const ok = modal.locator('button:has-text("确定")')
    if (await ok.isDisabled()) throw new Error(`选了「${want}」但「确定」还是灰的——没提交，停手`)
    await ok.click()
    await page.waitForTimeout(2500)
    const after = await shown()
    if (!after.includes(want)) throw new Error(`提交声明后显示的是 ${JSON.stringify(after)}，不是 ${JSON.stringify(want)}——没认，停手`)
    console.log('自主声明已设为：', want)
    await shot('declare')
  },
  async publish() {
    const gate = `D:/Users/mcu/.temp/douyin-run/I_HAVE_USER_OK=${EP}`
    if (!existsSync(gate)) throw new Error(`没有 ${gate}——这一步只能在对话里拿到点头之后手动放行`)
    const before = page.url()
    // 平台真正的裁决在 create_v2 的响应里，页面上可能一个字都不显示：
    // f3 那次七项全绿、点下去毫无反应，看 console 录到的响应才知道是
    // status_code:-2158「今天投稿次数已达到上限」。所以以这条响应为准，非 0 就把 status_msg 原样抛出来。
    let api = null
    page.on('response', (r) => {
      if (!/media\/aweme\/create/.test(r.url())) return
      r.json().then((j) => { api = j }).catch(() => {})
    })
    await page.locator('button:has-text("发布")').last().click()
    console.log('已点发布，等结果')
    // 成功只认两件事：平台回 status_code=0，或页面离开投稿页/出现成功提示。
    // 上一版点完固定睡 20 秒、把 page.url() 写进 published.txt 就算成了——f3 那次页面根本没动，
    // published.txt 里记的还是投稿表单自己的 URL，等于凭空造了一条"已发布"的假凭据。
    let done = null
    for (let k = 0; k < 30; k++) {
      await page.waitForTimeout(2000)
      if (api) break
      const t = await page.evaluate(() => document.body.innerText).catch(() => '')
      if (/发布成功|投稿成功/.test(t)) { done = 'toast'; break }
      if (!page.url().includes('content/post/video') && page.url() !== before) { done = 'navigated'; break }
    }
    await describe()
    await shot('published')
    if (api && api.status_code !== 0) {
      throw new Error(`平台驳回本次投稿：status_code=${api.status_code} ${api.status_msg || '(无文案)'}（logid ${api.extra?.logid ?? '?'}）——没发出去`)
    }
    if (!done && !api) {
      const blockers = await page.evaluate(() => [...document.querySelectorAll('*')]
        .filter((e) => e.children.length === 0 && /请选择|请填写|必填|不能为空|失败|审核中/.test(e.innerText || '') && (e.innerText || '').length < 60)
        .map((e) => e.innerText.trim()))
      throw new Error(`点了发布但 60 秒内既没等到 create_v2 的回应、也没离开投稿页——没发出去。页面拦路项：${[...new Set(blockers)].join(' / ') || '（读不到）'}`)
    }
    writeFileSync(`${RUN}/${EP}-published.txt`, `${done ?? 'api status_code=0'}\t${page.url()}\n`)
    console.log('✓ 发布确认（', done ?? '平台回 status_code=0', '）URL:', page.url())
  },
}

const fn = STEPS[step].bind(STEPS)
if (!fn) {
  console.log('可用步骤：', Object.keys(STEPS).join(' | '))
  process.exit(1)
}
await fn()
// 不调 browser.close()：那是 CDP 连接上的 close，某些版本会顺手把浏览器关掉，页面状态就没了。
// 直接退出本进程，socket 跟着我们死，常驻浏览器和它选好的视频留着。
process.exit(0)
