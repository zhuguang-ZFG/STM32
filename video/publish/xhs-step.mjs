// 小红书视频笔记的分步驱动：连 video/publish/xhs-daemon.mjs 起的那个常驻浏览器（9223），一次只做一步。
// 为什么分步而不是一把梭：发布是不可逆的公开动作，而编辑器里的状态（选好的视频、填好的字）
// 只活在那一页上——脚本一退、标签页一关就得重传。所以本驱动**绝不关掉工作标签页**，
// 也绝不在 CDP 连接上调 browser.close()（红线：会把登录态所在的窗口一起带走）。
// 事实源纪律：一集的字只从 video/episodes/<ep>/episode.json 的 publish.xiaohongshu 与 video/out/<ep>/ 来，
// 脚本里不写任何一集的字面量。
import { chromium } from 'playwright'
import { existsSync, mkdirSync, readFileSync, statSync, unlinkSync, writeFileSync } from 'node:fs'

const RUN = 'D:/Users/mcu/.temp/xhs-run'
mkdirSync(RUN, { recursive: true })
const PUBLISH_URL = 'https://creator.xiaohongshu.com/publish/publish?target=video'
const WORK_HOST = '/publish/publish'
// 已发布笔记的编辑页是另一个 URL（/publish/update?id=…），noteId 只从笔记管理的「编辑」入口里拿，不拼、不抄。
const EDIT_HOST = '/publish/update'
const NOTE_MANAGER_URL = 'https://creator.xiaohongshu.com/new/note-manager'

const verb = process.argv[2]
function arg(name, dflt = null) {
  const i = process.argv.findIndex((a) => a === name || a.startsWith(`${name}=`))
  if (i < 0) return dflt
  const a = process.argv[i]
  return a.includes('=') ? a.slice(a.indexOf('=') + 1) || dflt : process.argv[i + 1] ?? dflt
}
const EP = arg('--ep')
if (!EP) throw new Error('缺 --ep <episode-id>（--ep x 和 --ep=x 都认）——不猜这是哪一集')

const epFile = `D:/Users/mcu/video/episodes/${EP}/episode.json`
if (!existsSync(epFile)) throw new Error(`没有这一集：${epFile}`)
const ep = JSON.parse(readFileSync(epFile, 'utf8'))
const VIDEO = `D:/Users/mcu/video/out/${EP}/douyin.mp4`
const COVER = `D:/Users/mcu/video/out/${EP}/douyin-cover.png`

const browser = await chromium.connectOverCDP('http://127.0.0.1:9223')
const ctx = browser.contexts()[0]
// comment 走的是网页版（www.xiaohongshu.com），collection/collectioncheck/collectioncreate 走的是编辑页（/publish/update），
// 都不是 /publish/publish 那页草稿编辑器，所以这几步不参与工作页认领——认领错了会把没填完的草稿页当输入
// （2026-10-17 补：collectioncheck 漏在这里过一版，会顺手开/认领一张发布页，纯只读的核对不该有这种副作用）。
const NO_WORK_PAGE = verb === 'comment' || verb === 'collection' || verb === 'collectioncheck' || verb === 'collectioncreate'
let page = null
if (!NO_WORK_PAGE) {
  // 工作标签页按 URL 认领：已开着编辑器就回来接着用，没有就新开一页。
  // 新开而不是复用常驻页——上一版探针就是因为关掉常驻页把整个浏览器带没了。
  page = ctx.pages().find((p) => p.url().includes(WORK_HOST))
  if (!page) {
    page = await ctx.newPage()
    await page.goto(PUBLISH_URL, { waitUntil: 'domcontentloaded' })
  }
  page.setDefaultTimeout(120_000)
}

async function dump(label) {
  const info = await page.evaluate(() => {
    const txt = (s) => (s || '').replace(/\s+/g, ' ').trim()
    const fields = [...document.querySelectorAll('input,textarea,[contenteditable="true"]')].map((el) => {
      const r = el.getBoundingClientRect()
      return {
        sel: el.tagName.toLowerCase() + (el.getAttribute('contenteditable') ? '[contenteditable]' : ''),
        type: el.getAttribute('type') || null,
        ph: el.getAttribute('placeholder') || null,
        max: el.getAttribute('maxlength') || null,
        accept: el.getAttribute('accept') || null,
        cls: (el.getAttribute('class') || '').slice(0, 42),
        text: txt(el.value ?? el.innerText).slice(0, 40),
        visible: !!(r.width && r.height),
      }
    })
    const counters = [...new Set(document.body.innerText.match(/\d+\s*\/\s*\d{1,5}/g) || [])]
    const hints = []
    for (const el of document.querySelectorAll('[class*="limit"],[class*="count"],[class*="tip"],small,em')) {
      const t = txt(el.innerText)
      if (t && t.length <= 60 && /\d/.test(t) && !hints.includes(t)) hints.push(t)
    }
    const buttons = []
    for (const b of document.querySelectorAll('button,[role="button"],div[class*="btn"],span[class*="btn"]')) {
      const t = txt(b.innerText)
      if (!t || t.length > 16) continue
      const r = b.getBoundingClientRect()
      if (r.width && r.height && !buttons.includes(t)) buttons.push(t)
    }
    return { url: location.href, title: document.title, fields, counters, hints: hints.slice(0, 25), buttons, body: txt(document.body.innerText).slice(0, 1200) }
  })
  console.log(`\n【${label}】${info.url}`)
  console.log(`  字段（${info.fields.length}）：`)
  for (const f of info.fields) {
    console.log(`    ${f.sel}${f.type ? `:${f.type}` : ''} ph=「${f.ph || ''}」 max=${f.max || '-'}${f.accept ? ` accept=${f.accept}` : ''}${f.visible ? '' : ' [隐藏]'}${f.text ? ` 现值=「${f.text}」` : ''} class=${f.cls}`)
  }
  console.log(`  计数器：${info.counters.join(' | ') || '无'}`)
  console.log(`  带数字的提示：${info.hints.join(' | ') || '无'}`)
  console.log(`  按钮：${info.buttons.join(' | ')}`)
  console.log(`  正文前 1200 字：${info.body}`)
  return info
}

// 这个页面是 SPA：domcontentloaded 时正文还是空的，直接 dump 会打出"字段 0 / 正文空"，
// 看着像通道挂了其实是没等。等到出现可交互的上传/编辑控件再读，等不到也继续（把真实状态打出来）。
async function settle(ms = 45_000) {
  const t0 = Date.now()
  while (Date.now() - t0 < ms) {
    const ready = await page
      .evaluate(() => !!document.querySelector('input[type=file],[contenteditable="true"],textarea'))
      .catch(() => false)
    if (ready) {
      await page.waitForTimeout(1500)
      return true
    }
    await page.waitForTimeout(1500)
  }
  return false
}

const TITLE_INPUT = 'input[placeholder="填写标题会有更多赞哦"]'

// 合集那一行怎么读、怎么算「已挂上」：
// 实测：没挂时这一行末尾是占位「选择合集」；写着合集名时（表单里刚选的、或服务端已挂的都一样），
// 占位没了、整行末尾换成合集名，而且 .collection-plugin-button 这个类也会消失——所以判据只能看整行文本。
const makeReadRow = (form, want) => () =>
  form.evaluate((want) => {
    const txt = (s) => (s || '').replace(/\s+/g, ' ').trim()
    const row = txt(document.querySelector('.collection-plugin-wrapper')?.innerText)
    return {
      row,
      picked: row.includes(want) && !row.includes('选择合集'),
      url: location.href,
    }
  }, want)

// 打开「选择合集」弹层。两种状态的入口不一样（2026-10-17 DOM 实测）：
// 没挂/没选时是 .collection-plugin-button（文案「选择合集」）；已挂/已选时那个类会消失，
// 那一行末尾换成 div.collection-plugin-choose（span.collection-name + span.icon-arrow 那个 ⌄）——
// 所以按状态回退，找不到就报现状，不硬点。
async function openCollectionPicker(form) {
  const btn = form.locator('.collection-plugin-button').first()
  let el = btn
  if (!(await btn.count())) {
    const choose = form.locator('.collection-plugin-choose').first()
    if (!(await choose.count())) throw new Error('合集那一行没有 .collection-plugin-button 也没有 .collection-plugin-choose——入口换了样子，别硬点')
    el = choose
  }
  await el.click({ timeout: 15_000 })
  await form.waitForTimeout(4000)
  const items = form.locator('.d-popover .item')
  if (!(await items.count())) {
    const state = await form.evaluate(() => {
      const txt = (s) => (s || '').replace(/\s+/g, ' ').trim()
      return {
        row: txt(document.querySelector('.collection-plugin-wrapper')?.innerText),
        popover: txt(document.querySelector('.d-popover')?.innerText).slice(0, 200),
      }
    })
    throw new Error(`点了合集入口但弹层里没有 .d-popover .item——行：「${state.row}」，弹层：「${state.popover || '(没开)'}」`)
  }
  return items
}

// 量「发布」那颗按钮的真实盒模型：<xhs-publish-btn> 是 closed shadow，page JS 够不到里面；
// 但 CDP 的 DOM.getDocument(pierce:true) 能穿透 shadow、DOM.getBoxModel 给出内部按钮的四边形。
// 2026-10-17 实测：发布页底栏是「暂存离开 429..549 | 发布 573..693」两颗（flex 居中、gap 24），
// 宿主矩形 221..901 的正中心 (561) 正好落在两颗**中间的空隙**上——点中心什么都不会发生（第一次就踩了这个）。
async function findPublishButtonBox(page) {
  const cdp = await page.context().newCDPSession(page)
  try {
    const { root } = await cdp.send('DOM.getDocument', { depth: -1, pierce: true })
    const walk = (n, out) => {
      out.push(n)
      for (const c of n.children || []) walk(c, out)
      for (const s of n.shadowRoots || []) walk(s, out)
    }
    const all = []
    walk(root, all)
    for (const host of all.filter((n) => n.nodeName === 'XHS-PUBLISH-BTN')) {
      const sub = []
      walk(host, sub)
      for (const n of sub) {
        if (n.nodeType !== 1) continue
        const own = (n.children || []).filter((c) => c.nodeType === 3).map((c) => (c.nodeValue || '').trim()).filter(Boolean)
        if (own.length !== 1 || own[0] !== '发布') continue
        const box = await cdp.send('DOM.getBoxModel', { nodeId: n.nodeId })
        const q = box.model.border
        return {
          cx: Math.round((q[0] + q[2] + q[4] + q[6]) / 4),
          cy: Math.round((q[1] + q[3] + q[5] + q[7]) / 4),
          quad: q.map(Math.round).join(','),
        }
      }
    }
    return null
  } finally {
    await cdp.detach().catch(() => {})
  }
}

// 认领/新开一条笔记的编辑页（/publish/update）。开着的编辑页不等于就是这一条的：
// 2026-10-17 实测踩到——F5 那步复用了 S5 留下的编辑页，把 S5 的合集行当 F5 的读了、截图还被覆盖成 S5 的页。
// 所以认领按标题框逐字；别的笔记的编辑页一律不碰（可能是人正开着要交的表），走笔记管理经「编辑」tooltip 另开。
async function claimEditPage(xsTitle) {
  let form = ctx.pages().find((p) => p.url().includes(EDIT_HOST))
  if (form) {
    const openTitle = await form
      .evaluate((sel) => document.querySelector(sel)?.value || '', TITLE_INPUT)
      .catch(() => '')
    if (openTitle && openTitle === xsTitle) {
      console.log(`  编辑页已经开着，接着用它（标题框：「${openTitle}」）`)
    } else {
      console.log(`  开着的编辑页是别的笔记的（标题框：「${openTitle.slice(0, 30)}」，要的是「${xsTitle}」）——不碰它，走笔记管理另开这一条`)
      form = null
    }
  }
  if (!form) {
    const nm = await ctx.newPage()
    nm.setDefaultTimeout(60_000)
    await nm.goto(NOTE_MANAGER_URL, { waitUntil: 'domcontentloaded' })
    await nm.waitForTimeout(9000)
    // 笔记管理是**虚拟列表**：默认只渲染可视区约 10 条，旧笔记整批看不见（2026-10-17 实测：
    // 44 条时 22:2x 那批一条都不在首屏）。所以先 Ctrl+Minus 缩小让一屏装更多，再
    // PageDown/滚轮/把可滚动祖先的 scrollTop 推着走——三种齐上，单用任一种都不动（实测）。
    for (let i = 0; i < 4; i++) { await nm.keyboard.press('Control+Minus'); await nm.waitForTimeout(300) }
    await nm.waitForTimeout(1200)
    const card = nm.locator('.note-card__body').filter({ hasText: xsTitle }).first()
    for (let round = 0; round < 25 && !(await card.count()); round++) {
      await nm.keyboard.press('PageDown')
      await nm.mouse.move(700, 600)
      await nm.mouse.wheel(0, 1400)
      await nm.evaluate(() => {
        let el = document.querySelector('.note-card__body')
        while (el && el.scrollHeight <= el.clientHeight) el = el.parentElement
        if (el) el.scrollTop = el.scrollTop + Math.floor(el.clientHeight * 0.9)
      })
      await nm.waitForTimeout(1200)
    }
    if (!(await card.count())) {
      await nm.close().catch(() => {})
      throw new Error(`笔记管理里没有标题含「${xsTitle}」的卡片（缩小+三种滚动扫了 25 轮）——先核这条到底发出去了没，别猜`)
    }
    await card.scrollIntoViewIfNeeded().catch(() => {})
    await nm.waitForTimeout(600)
    // 「编辑」是图标按钮，只能靠 hover 出来的 tooltip 认领（按下标猜会在别的集上点错）
    const icons = card.locator('[class*="action-btn"]')
    const n = await icons.count()
    let idx = -1
    for (let i = 0; i < n; i++) {
      await icons.nth(i).hover().catch(() => {})
      await nm.waitForTimeout(700)
      const tips = await nm.evaluate(() => {
        const txt = (s) => (s || '').replace(/\s+/g, ' ').trim()
        return [...document.querySelectorAll('[class*="tooltip"],[role="tooltip"],.d-popover,[class*="popover"]')]
          .filter((e) => e.getBoundingClientRect().width)
          .map((e) => txt(e.innerText))
          .filter(Boolean)
      })
      if (tips.some((t) => t === '编辑')) { idx = i; break }
    }
    if (idx < 0) {
      await nm.close().catch(() => {})
      throw new Error(`这张卡片上 hover 遍 ${n} 个图标都没冒出「编辑」tooltip，不敢点`)
    }
    const before = new Set(ctx.pages())
    await icons.nth(idx).click({ timeout: 15_000 })
    await nm.waitForTimeout(12_000)
    const fresh = ctx.pages().filter((x) => !before.has(x))
    form = fresh[0] || nm
    // 缩放是 origin 级的（编辑页与笔记管理同域）：把 nm 的缩放还原回 100%，
    // 免得编辑页的截图带着缩放、以及后续按截图像素读尺度时对不上。
    await nm.keyboard.press('Control+0').catch(() => {})
  }
  await form.waitForLoadState('domcontentloaded').catch(() => {})
  // SPA 带未保存改动时导航会弹原生 confirm（beforeunload 之类）；不接住的话 playwright 的竞态
  // 自动处理会抛 ProtocolError: No dialog is showing（2026-10-17 实测，创建合集后重载核对时撞上）——
  // 挂个 listener 一律接受：这条线上没有需要"取消"的原生对话。
  form.on('dialog', (d) => d.accept().catch(() => {}))
  await form.waitForTimeout(15_000)
  return form
}

// 编辑页的提交（挂合集/建合集之后要落盘的那一下）：
// 那颗 <xhs-publish-btn> 是 closed shadow——整页文本扫不到「发布」、getByText 点不中；
// 2026-10-17 章节批与 F5/S5 实测：真实鼠标在宿主 rect 内点击能命中内部按钮。
// 判据不认 toast 认服务端：点完把这条编辑页重新载一遍，那一行还写着合集名才算数。
async function submitEditAndVerify(form, readRow, want) {
  const url = form.url()
  await form.locator('xhs-publish-btn').first().scrollIntoViewIfNeeded().catch(() => {})
  await form.waitForTimeout(800)
  const pt = await findPublishButtonBox(form)
  if (!pt) throw new Error('CDP 穿透没量到「发布」那颗按钮——不猜坐标')
  console.log(`  提交：CDP 穿透量到「发布」盒=${pt.quad} → 真实点击 (${pt.cx},${pt.cy})`)
  await form.mouse.click(pt.cx, pt.cy)
  await form.waitForTimeout(7000)
  const toast = await form.evaluate(() => {
    const m = (document.body.innerText || '').replace(/\s+/g, ' ').match(/(更新成功|保存成功|发布成功|提交成功)/)
    return m ? m[1] : null
  })
  console.log(`  点完读到的提示：${toast ? `「${toast}」` : '没读到成功字样（以重开核对为准）'}`)
  await form.goto(url, { waitUntil: 'domcontentloaded' })
  await form.waitForTimeout(12_000)
  const ver = await readRow()
  console.log(`  重开编辑页核对：这一行写着「${ver.row}」`)
  console.log(`  服务端核对：显示「${want}」：${ver.picked ? '是（已落盘）' : '否（没落上，别当成功）'}`)
  await form.screenshot({ path: `${RUN}/${EP}-collection-submitted.png` })
  console.log(`  截图：${RUN}/${EP}-collection-submitted.png`)
  if (!ver.picked) {
    process.exitCode = 4
    throw new Error(`提交后重开编辑页，合集行没显示「${want}」——按未提交对待`)
  }
  return ver
}

// 发布成功后回笔记管理现取 noteId：noteId 是这条笔记的唯一凭据，标题会重名、日期只到分钟。
// 只读：按标题逐字命中 .note-card__title，从卡片的 data-impression 里读（归档适配器同源）；
// 不点「编辑」、不点删除。自己开的页自己关，缩放是 origin 级，先还原再关。
async function freshNoteIdByTitle(xsTitle) {
  const want = String(xsTitle || '').trim()
  if (!want) return null
  const nm = await ctx.newPage()
  nm.setDefaultTimeout(60_000)
  try {
    await nm.goto(NOTE_MANAGER_URL, { waitUntil: 'domcontentloaded' })
    await nm.waitForTimeout(9000)
    for (let i = 0; i < 4; i++) {
      await nm.keyboard.press('Control+Minus')
      await nm.waitForTimeout(300)
    }
    await nm.waitForTimeout(1200)
    for (let round = 0; round < 30; round++) {
      const hit = await nm.evaluate((t) => {
        const norm = (v) => (v || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
        for (const card of document.querySelectorAll('.note-card')) {
          if (norm(card.querySelector('.note-card__title')?.innerText) !== t) continue
          const impression = card.getAttribute('data-impression') || ''
          const id = (impression.match(/"noteId":"([0-9a-f]{24})"/) || [])[1] || ''
          return { id, text: norm(card.innerText).slice(0, 120) }
        }
        return null
      }, want)
      if (hit) return hit
      await nm.mouse.move(700, 600)
      await nm.mouse.wheel(0, 1400)
      await nm.evaluate(() => {
        const box = document.querySelector('.content')
        if (box) box.scrollTop = box.scrollHeight
      })
      await nm.waitForTimeout(1000)
    }
    return null
  } finally {
    await nm.keyboard.press('Control+0').catch(() => {})
    await nm.close().catch(() => {})
  }
}

if (verb === 'status') {
  await settle()
  await dump('status')
} else if (verb === 'open') {
  await page.goto(PUBLISH_URL, { waitUntil: 'domcontentloaded' })
  await settle()
  await dump('open')
} else if (verb === 'upload') {
  if (!existsSync(VIDEO)) throw new Error(`没有成片：${VIDEO}`)
  if (!existsSync(COVER)) throw new Error(`没有封面：${COVER}`)
  console.log(`上传成片 ${VIDEO}（${(statSize(VIDEO) / 1e6).toFixed(2)} MB）——只进编辑器，不点发布`)
  await page.setInputFiles('input[type=file]', VIDEO)
  await page.waitForTimeout(30_000)
  await dump('upload')
  await page.screenshot({ path: `${RUN}/${EP}-after-upload.png` })
} else if (verb === 'measure') {
  // 上限只能自己量：页面上标题框没有 maxlength 属性，正文计数器印的是 0/1000，
  // 抄别人的数字（或按别的平台上限写死）会把第一次试发变成废稿。
  const TITLE = '标题字数上限实测：一二三四五六七八九十一二三四五六七八九十一二三四五六七八九十'
  await page.fill('input[placeholder="填写标题会有更多赞哦"]', TITLE)
  await page.waitForTimeout(1200)
  const t = await page.evaluate((s) => {
    const el = document.querySelector('input[placeholder="填写标题会有更多赞哦"]')
    const box = el?.closest('div')?.parentElement
    return { typed: s.length, value: (el?.value || '').length, near: (box?.innerText || '').replace(/\s+/g, ' ').slice(0, 120) }
  }, TITLE)
  console.log(`\n【标题】喂进 ${t.typed} 字 → 留在框里 ${t.value} 字；框旁文案：「${t.near}」`)
  const BODY = '正文上限实测。'.repeat(200)
  await page.click('.tiptap.ProseMirror')
  await page.keyboard.insertText(BODY)
  await page.waitForTimeout(1500)
  const b = await page.evaluate(() => {
    const ed = document.querySelector('.tiptap.ProseMirror')
    const counters = [...new Set((document.body.innerText.match(/\d+\s*\/\s*\d{1,5}/g) || []))]
    return { kept: (ed?.innerText || '').replace(/\s/g, '').length, counters }
  })
  console.log(`【正文】喂进 ${BODY.replace(/\s/g, '').length} 字 → 编辑器里剩 ${b.kept} 字；计数器：${b.counters.join(' | ')}`)
  await page.screenshot({ path: `${RUN}/measure.png` })
  console.log(`  截图：${RUN}/measure.png`)
} else if (verb === 'fill') {
  const xs = ep.publish?.xiaohongshu
  if (!xs) throw new Error(`${EP} 的 episode.json 没有 publish.xiaohongshu——不替这一集猜文案`)
  // 护栏写在本机这一侧：实测这两个上限都**不在 DOM 上强制**（标题框没有 maxlength，
  // 正文 1400 字照样进编辑器），页面只把 "39 / 20"、"1400 /1000" 印成红色分母，
  // 拦住的是提交而不是输入。所以越界必须在这里死掉，不能指望平台替我们拦。
  const TITLE_MAX = 20
  const BODY_MAX = 1000
  const errs = []
  const cps = (s) => [...s].length
  if (cps(xs.title) > TITLE_MAX) errs.push(`标题 ${cps(xs.title)} 字 > ${TITLE_MAX}`)
  if (cps(xs.body) > BODY_MAX) errs.push(`正文 ${cps(xs.body)} 字 > ${BODY_MAX}`)
  for (const [k, v] of [['title', xs.title], ['body', xs.body], ['pinned', xs.pinned || '']]) {
    if (/https?:\/\//.test(v)) errs.push(`${k} 里有站外链接`)
    if (/github/i.test(v)) errs.push(`${k} 里有 GitHub 字样`)
  }
  if (errs.length) {
    console.log('停在填写前：')
    for (const e of errs) console.log(`  - ${e}`)
    process.exit(2)
  }
  await page.fill('input[placeholder="填写标题会有更多赞哦"]', xs.title)
  await page.click('.tiptap.ProseMirror')
  await page.keyboard.press('Control+a')
  await page.keyboard.press('Delete')
  const paras = xs.body.split('\n')
  for (let k = 0; k < paras.length; k++) {
    if (k) await page.keyboard.press('Enter')
    if (paras[k]) await page.keyboard.insertText(paras[k])
  }
  await page.waitForTimeout(1500)
  const back = await page.evaluate(() => {
    const t = document.querySelector('input[placeholder="填写标题会有更多赞哦"]')
    const ed = document.querySelector('.tiptap.ProseMirror')
    // 计数器只认"整个元素就是一串 a / b"的那种节点。上一版拿全页 innerText 正则扫，
    // 把稿件正文里那句「（6000 / 2500）」也读进来了——看着是页面在报数，其实是我们自己写的字。
    const counters = []
    for (const el of document.querySelectorAll('*')) {
      const own = (el.innerText || '').replace(/\s+/g, ' ').trim()
      if (/^[\d,]+\s*\/\s*[\d,]+$/.test(own)) {
        const r = el.getBoundingClientRect()
        if (r.width && r.height && !counters.includes(own)) counters.push(own)
      }
    }
    return {
      title: [...(t?.value || '')].length,
      body: [...(ed?.innerText || '').replace(/\s+/g, '')].length,
      counters,
    }
  })
  console.log(`\n【fill】标题回填 ${back.title} 字（目标 ${cps(xs.title)}）；正文编辑器内 ${back.body} 字（去空白）；计数器：${back.counters.join(' | ')}`)
  if (back.title !== cps(xs.title)) console.log(`  ⚠ 标题字数与稿件不一致，看截图再决定继不继续`)
  if (back.counters.some((c) => /^\s*0\s*\/\s*0/.test(c))) console.log('  ⚠ 计数器像是空的，填写可能没落到编辑器上')
  await page.screenshot({ path: `${RUN}/${EP}-filled.png` })
  console.log(`  截图：${RUN}/${EP}-filled.png`)
} else if (verb === 'topics') {
  // 话题必须是 chip，不是正文里的黑字：实测把 "#FreeRTOS #互斥锁" 直接写进正文，截图上就是普通文本，
  // 只有输入 "#名字" 之后弹出来的那条候选（带「1758浏览」）接住才算挂上话题。
  // 接法用回车，不用 locator 点候选：上一版 `text=/^#FreeRTOS/` 先匹配到的正是刚打进正文的那串黑字，
  // 点它只是移动光标，三次"clicked"最后拼出 "#优先" + "级反转斥锁RTOS" 这种交错垃圾（HTML 尾巴为证）。
  const list = ep.publish?.xiaohongshu?.topics || []
  if (!list.length) throw new Error(`${EP} 没有 publish.xiaohongshu.topics，不替这一集猜话题`)
  await page.click('.tiptap.ProseMirror')
  await page.keyboard.press('Control+End')
  for (const t of list) {
    await page.keyboard.insertText(` #${t}`)
    await page.waitForTimeout(2200)
    await page.keyboard.press('Enter')
    await page.waitForTimeout(900)
    const st = await page.evaluate(() => {
      const ed = document.querySelector('.tiptap.ProseMirror')
      const nodes = [...ed.querySelectorAll('a,[class*="topic"],[data-type]')].map((el) => `${el.tagName.toLowerCase()}.${el.getAttribute('class') || ''}[${(el.innerText || '').replace(/\s+/g, ' ')}]`)
      return { nodes, tail: ed.innerHTML.slice(-260) }
    })
    console.log(`  ${t} → 话题节点：${st.nodes.join(' ') || '无'}`)
    console.log(`    HTML 尾：${st.tail}`)
  }
  await page.screenshot({ path: `${RUN}/${EP}-topics.png` })
  console.log(`  截图：${RUN}/${EP}-topics.png`)
} else if (verb === 'cover') {
  // 只开面板读结构，不选图、不点应用：封面是这条线最强的点击变量，但换封面会改草稿状态，
  // 先把"能不能传自定义图、要求什么比例"量下来，再决定喂哪张。
  await page.getByText('设置封面', { exact: false }).first().click({ timeout: 15_000 })
  await page.waitForTimeout(3500)
  const panel = await page.evaluate(() => {
    const txt = (s) => (s || '').replace(/\s+/g, ' ').trim()
    const files = [...document.querySelectorAll('input[type=file]')].map((el) => el.getAttribute('accept') || '(任意)')
    const buttons = []
    for (const b of document.querySelectorAll('button,[role="button"],div[class*="btn"],span[class*="btn"]')) {
      const t = txt(b.innerText)
      const r = b.getBoundingClientRect()
      if (t && t.length <= 14 && r.width && r.height && !buttons.includes(t)) buttons.push(t)
    }
    return { files, buttons, body: txt(document.body.innerText).slice(0, 700) }
  })
  console.log(`\n【cover】file inputs accept：${panel.files.join(' | ') || '无'}`)
  console.log(`  按钮：${panel.buttons.join(' | ')}`)
  console.log(`  面板文案：${panel.body}`)
  // 「设置封面」那四个字只是标题，点它什么也不开（实测点了 3.5 秒，页面纹丝不动）。
  // 真正的入口是封面缩略图本身，点进去才看得到"能不能传自定义图"。
  const opened = await page.evaluate(() => {
    const host = [...document.querySelectorAll('div,section')].find((el) => (el.innerText || '').includes('智能推荐封面'))
    const img = host?.querySelector('img,canvas,[class*="cover"]')
    if (!img) return false
    img.click()
    return true
  })
  await page.waitForTimeout(3500)
  const deep = await page.evaluate(() => {
    const txt = (s) => (s || '').replace(/\s+/g, ' ').trim()
    const files = [...document.querySelectorAll('input[type=file]')].map((el) => el.getAttribute('accept') || '(任意)')
    const words = [...new Set((document.body.innerText.match(/[^\s]{0,6}(上传封面|更换封面|本地上传|裁剪|选择封面)[^\s]{0,8}/g) || []))]
    return { files, words, body: txt(document.body.innerText).slice(0, 400) }
  })
  console.log(`  点缩略图：${opened ? '已点' : '没找到缩略图'} → file inputs accept：${deep.files.join(' | ') || '无'}`)
  console.log(`  封面相关文案：${deep.words.join(' | ') || '无'}`)
  console.log(`  当前页面前 400 字：${deep.body}`)
  await page.screenshot({ path: `${RUN}/${EP}-cover.png` })
  console.log(`  截图：${RUN}/${EP}-cover.png`)
  await page.keyboard.press('Escape').catch(() => {})
} else if (verb === 'coverset') {
  // 封面能传自定义图，但入口藏得深：先点中默认封面缩略图，才会浮出「编辑封面」，
  // 进去之后才有 accept="image/*" 的那个 file input（页面上原本只有视频那一个）。
  // 这一步只喂图、只打印裁剪界面，**不点应用**——应用会改草稿状态，看图确认后再单独放行。
  if (!existsSync(COVER)) throw new Error(`没有封面：${COVER}`)
  // 幂等：编辑器可能已经开着（前一次探到一半没关），此时那层 d-modal-mask 会挡掉缩略图的点击，
  // 再点一次就是白等 15 秒超时。判据用"有没有图片 file input"，有就直接喂图。
  const img = page.locator('input[type=file][accept*="image"]').first()
  if (!(await img.count())) {
    await page.locator('.cover-plugin-preview .default.column').first().click({ timeout: 15_000 })
    await page.getByText('编辑封面', { exact: false }).first().click({ timeout: 15_000 })
    await page.waitForTimeout(2500)
  } else {
    console.log('  封面编辑器已经开着，直接喂图')
  }
  await img.waitFor({ state: 'attached', timeout: 15_000 })
  await img.setInputFiles(COVER)
  await page.waitForTimeout(8000)
  const st = await page.evaluate(() => {
    const txt = (s) => (s || '').replace(/\s+/g, ' ').trim()
    const buttons = []
    for (const b of document.querySelectorAll('button,[role="button"],div[class*="btn"],span[class*="btn"]')) {
      const t = txt(b.innerText)
      const r = b.getBoundingClientRect()
      if (t && t.length <= 12 && r.width && r.height && !buttons.includes(t)) buttons.push(t)
    }
    return { buttons, words: [...new Set(document.body.innerText.match(/[^\s]{0,8}(裁剪|比例|3:4|4:3|1:1|清晰|应用|取消|重选)[^\s]{0,8}/g) || [])].slice(0, 16) }
  })
  console.log(`\n【coverset】喂入 ${COVER}（${(statSize(COVER) / 1e6).toFixed(2)} MB，1080×1440）`)
  console.log(`  按钮：${st.buttons.join(' | ')}`)
  console.log(`  裁剪相关文案：${st.words.join(' | ') || '无'}`)
  await page.screenshot({ path: `${RUN}/${EP}-coverset.png` })
  console.log(`  截图：${RUN}/${EP}-coverset.png（还没点应用）`)
} else if (verb === 'coverapply') {
  // coverset 只把图喂进编辑器；点「完成」才把它落成笔记封面。仍然在草稿内，不碰发布。
  await page.getByText('完成', { exact: true }).last().click({ timeout: 15_000 })
  await page.waitForTimeout(4000)
  const st = await page.evaluate(() => ({
    modal: !!document.querySelector('.d-modal-mask'),
    thumbs: [...document.querySelectorAll('.cover-plugin-preview img')].map((i) => i.src.slice(0, 60)),
  }))
  console.log(`\n【coverapply】编辑器还开着：${st.modal ? '是' : '否'}；封面条：${st.thumbs.join(' | ') || '无'}`)
  await page.screenshot({ path: `${RUN}/${EP}-cover-applied.png` })
  console.log(`  截图：${RUN}/${EP}-cover-applied.png`)
} else if (verb === 'comment') {
  // 置顶评论只能在网页版发：创作者中心十项导航里没有任何评论项，数据看板只报「评论数」（实测与四条证据见 xhs-plan.md）。
  // 默认**只填不发**（「发送」那颗按钮归人点）；`--go` 且写好**独立闸门** `I_HAVE_USER_OK_COMMENT=<ep>` 才代发
  // （2026-10-17 F5/S5 各实发过一次；闸门只从对话里的点头来，不复用发布那张）。
  const text = ep.publish?.xiaohongshu?.pinned
  if (!text) throw new Error(`${EP} 没有 publish.xiaohongshu.pinned——不替这一集猜置顶评论`)
  const errs = []
  if (/https?:\/\//.test(text)) errs.push('置顶评论里有站外链接')
  if (/github/i.test(text)) errs.push('置顶评论里有 GitHub 字样')
  if (errs.length) {
    console.log('停在发评论前：')
    for (const e of errs) console.log(`  - ${e}`)
    process.exit(2)
  }
  const wp = await ctx.newPage()
  wp.setDefaultTimeout(60_000)
  // 笔记地址每次现取：/explore/<id> 少了 xsec_token 直接落 300031「当前笔记暂时无法浏览」，
  // 而 token 挂在主页那批 <a> 上、会跟着会话过期——抄进台账就是埋雷。
  await wp.goto('https://www.xiaohongshu.com/explore', { waitUntil: 'domcontentloaded' })
  await wp.waitForTimeout(8000)
  const prof = await wp.evaluate(() => {
    const a = document.querySelector('a[href^="/user/profile/"]')
    return a ? new URL(a.getAttribute('href'), location.href).href : null
  })
  if (!prof) throw new Error('网页版没登录：顶栏里没有 <a href="/user/profile/...">。先在这个窗口里登录网页版小红书再跑')
  await wp.goto(prof, { waitUntil: 'domcontentloaded' })
  await wp.waitForTimeout(9000)
  const xsTitle = ep.publish?.xiaohongshu?.title || ''
  const findCard = () =>
    wp.evaluate((t) => {
      const txt = (s) => (s || '').replace(/\s+/g, ' ').trim()
      for (const a of document.querySelectorAll('a[href*="xsec_token"]')) {
        if (t && txt(a.innerText).includes(t)) return a.href
      }
      return null
    }, xsTitle)
  let note = await findCard()
  // 主页是懒加载：首屏扫不到不等于没有——有界滚几轮再扫（2026-10-17 加：条目一多旧笔记会掉出首屏，
  // 原来直接抛"没找到"就误判了；S5 那次首屏就命中，纯属运气好）。
  for (let round = 0; round < 6 && !note; round++) {
    await wp.mouse.move(700, 600)
    for (let i = 0; i < 3; i++) {
      await wp.mouse.wheel(0, 1400)
      await wp.waitForTimeout(500)
    }
    await wp.waitForTimeout(1200)
    note = await findCard()
  }
  if (!note) throw new Error(`主页上没找到标题含「${xsTitle}」的卡片（滚了 6 轮）——先回笔记管理核这条到底发出去了没，别猜`)
  await wp.goto(note, { waitUntil: 'domcontentloaded' })
  await wp.waitForTimeout(9000)
  const box = wp.locator('p.content-input').first()
  await box.waitFor({ state: 'attached', timeout: 20_000 })
  // 「评论」那条占位（.inner-when-not-active）与 p.content-input 是同一个 rect 的兄弟，占位盖在上面；
  // 直接点 p 会被它拦下（实测 TimeoutError: intercepts pointer events）。先点占位换到输入态。
  const ph = wp.locator('.engage-bar .inner-when-not-active').first()
  if (await ph.count()) await ph.click({ timeout: 15_000 })
  else await box.click({ timeout: 15_000 })
  await wp.waitForTimeout(1200)
  await wp.keyboard.insertText(text)
  await wp.waitForTimeout(1500)
  const back = await wp.evaluate(() => {
    const el = document.querySelector('p.content-input')
    return { typed: [...(el?.innerText || '')].length, url: location.href }
  })
  console.log(`\n【comment】笔记页：${back.url}`)
  console.log(`  稿件 ${[...text].length} 字 → 评论框里 ${back.typed} 字${back.typed === [...text].length ? '（一致）' : '（不一致，看截图）'}`)
  await wp.screenshot({ path: `${RUN}/${EP}-comment.png` })
  console.log(`  截图：${RUN}/${EP}-comment.png`)
  // 发评论是公开写动作，闸门用**另一个文件名**：`I_HAVE_USER_OK=<ep>` 是"这一集可以发布"的授权，
  // 拿它来放行一条评论，等于把两种授权混成一种——以后谁看到它在就以为发布也批过了。
  if (!process.argv.includes('--go')) {
    console.log('  只填不发：这一页留在这里，核对完由人点「发送」。要脚本代发：加 --go 并写好评论闸门文件')
  } else {
    const gate = `${RUN}/I_HAVE_USER_OK_COMMENT=${EP}`
    if (!existsSync(gate)) {
      console.log(`  停在发评论前：闸门文件不存在 ${gate}`)
      console.log('  这个文件只能来自对话里对"发这条评论"的点头，脚本不自己造；字留在框里没动，人也可以直接点「发送」。')
      process.exitCode = 3
    } else {
      console.log(`  闸门：${gate}`)
      console.log(`    ${readFileSync(gate, 'utf8').trim()}`)
      await wp.getByText('发送', { exact: true }).last().click({ timeout: 15_000 })
      await wp.waitForTimeout(7000)
      const after = await wp.evaluate((t) => {
        const txt = (s) => (s || '').replace(/\s+/g, ' ').trim()
        const list = [...document.querySelectorAll('[id^="comment"], [class*="comment"]')].map((e) => txt(e.innerText)).filter((s) => s && s.length > 8)
        return { boxLeft: [...(document.querySelector('p.content-input')?.innerText || '')].length, posted: list.some((s) => s.includes(t.slice(0, 18))), sample: list.slice(0, 4) }
      }, text)
      console.log(`  点过「发送」：评论框剩 ${after.boxLeft} 字（清空=发出去了）；列表里找到这条：${after.posted ? '是' : '否'}`)
      for (const s of after.sample) console.log(`    评论节点：「${s.slice(0, 70)}」`)
      await wp.screenshot({ path: `${RUN}/${EP}-comment-sent.png` })
      console.log(`  截图：${RUN}/${EP}-comment-sent.png`)
    }
  }
} else if (verb === 'collection') {
  // 挂合集在**已发布笔记的编辑页**做：合集名从 episode.json 来，noteId 从笔记管理点「编辑」现拿（不拼 URL，noteId 抄进代码就是埋雷）。
  // 选到「这一行写着合集名」为止；--go 才点提交（闸门 I_HAVE_USER_OK_SUBMIT=<ep>，默认归人点）。
  const name = ep.publish?.xiaohongshu?.collection
  if (!name) throw new Error(`${EP} 没有 publish.xiaohongshu.collection——不替这一集猜合集名`)
  const xsTitle = ep.publish?.xiaohongshu?.title || ''
  const form = await claimEditPage(xsTitle)
  const readRow = makeReadRow(form, name)
  const pre = await readRow()
  console.log(`\n【collection】编辑页：${pre.url}`)
  console.log(`  合集那一行现在是：「${pre.row}」`)
  if (pre.picked) {
    console.log(`  这一行已经写着「${name}」，不用再点`)
  } else {
    // 弹层里可选项是 div.item（逐字合集名），「创建合集」在 footer 里——
    // 按整段文本全等来认，不按子串：子串会把含 footer 的容器也捞进来。
    const cand = await openCollectionPicker(form)
    const cnt = await cand.count()
    const labels = []
    let item = null
    for (let i = 0; i < cnt; i++) {
      const t = (await cand.nth(i).innerText().catch(() => '')).replace(/\s+/g, ' ').trim()
      labels.push(t)
      if (t === name) item = cand.nth(i)
    }
    console.log(`  弹层里的可选项（${cnt}）：${labels.map((s) => `「${s}」`).join(' | ') || '无'}`)
    if (!item) throw new Error(`弹层里没有逐字等于「${name}」的选项——不猜该点哪一条`)
    await item.click({ timeout: 15_000 })
    await form.waitForTimeout(4000)
  }
  const after = await readRow()
  console.log(`  现在这一行写着：「${after.row}」`)
  console.log(`  这一行显示合集名：${after.picked ? '是' : '否'}`)
  const btn = await form.evaluate(() => {
    const el = document.querySelector('xhs-publish-btn')
    if (!el) return null
    const r = el.getBoundingClientRect()
    return {
      attrs: [...el.attributes].map((a) => `${a.name}=${a.value}`).join(' '),
      rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}`,
      hasHandler: typeof el._onPublish === 'function',
    }
  })
  if (btn) {
    console.log(`  保存那颗按钮：<xhs-publish-btn ${btn.attrs}> rect=${btn.rect}，_onPublish 在=${btn.hasHandler}`)
    console.log('  它是 closed shadow 的自定义元素：整页文本扫不到「发布」、getByText 点不中；真实鼠标在宿主 rect 内坐标点能命中（2026-10-17 章节批实测）。')
  }
  await form.screenshot({ path: `${RUN}/${EP}-collection.png` })
  console.log(`  截图：${RUN}/${EP}-collection.png`)
  if (!process.argv.includes('--go')) {
    console.log('  到这里停手：没点提交。is-publish=true 时点下去等于把这条已发布笔记重新提交一遍（大概率再走一次审核）——要脚本代点加 --go，闸门文件另写。')
  } else {
    const gate = `${RUN}/I_HAVE_USER_OK_SUBMIT=${EP}`
    if (!existsSync(gate)) {
      console.log(`  停在提交前：闸门文件不存在 ${gate}`)
      console.log('  这个文件只能来自对话里对「提交那一下由脚本点」的点头，脚本不自己造。')
      process.exitCode = 3
    } else {
      console.log(`  闸门：${gate}`)
      console.log(`    ${readFileSync(gate, 'utf8').trim()}`)
      await submitEditAndVerify(form, readRow, name)
    }
  }
} else if (verb === 'collectioncheck') {
  // 只读核验一条已发布笔记的合集归属：认领编辑页（虚拟列表扫卡见 claimEditPage）→ **重载一次**
  // （读的是服务端，不信任何表单残留）→ 回读那一行。不点任何东西；
  // 退出码 0=那一行写着合集名，4=没写上。批后抽样与随时复查都用它，别再用一次性探针。
  const name = ep.publish?.xiaohongshu?.collection
  if (!name) throw new Error(`${EP} 没有 publish.xiaohongshu.collection——不替这一集猜合集名`)
  const xsTitle = ep.publish?.xiaohongshu?.title || ''
  const form = await claimEditPage(xsTitle)
  const readRow = makeReadRow(form, name)
  const url = form.url()
  await form.goto(url, { waitUntil: 'domcontentloaded' })
  await form.waitForTimeout(12_000)
  const ver = await readRow()
  console.log(`\n【collectioncheck】${EP}（重载后读的是服务端）编辑页：${ver.url}`)
  console.log(`  合集那一行写着：「${ver.row}」`)
  console.log(`  归属核验：显示「${name}」：${ver.picked ? '是' : '否'}`)
  await form.screenshot({ path: `${RUN}/${EP}-collectioncheck.png` })
  console.log(`  截图：${RUN}/${EP}-collectioncheck.png`)
  if (!ver.picked) {
    process.exitCode = 4
    throw new Error(`${EP} 的合集行没显示「${name}」——按未挂对待`)
  }
} else if (verb === 'collectioncreate') {
  // 建合集并把当前这条「创建并加入」：链路来自 ops 线实测（D:/tmp/xhs_make_collection.py，2026-10-17 建章节合集的同一条路）——
  // 点「选择合集」触发弹层 → footer「创建合集」→ 名称 input[placeholder*="合集名称"] / 简介 →「创建并加入」。
  // 建合集是公开内容：闸门 I_HAVE_USER_OK_COLLECTION=<合集名> 只能来自对话里的点头，名字从 episode.json 来（不写字面量）。
  const name = ep.publish?.xiaohongshu?.collection
  if (!name) throw new Error(`${EP} 没有 publish.xiaohongshu.collection——不替这一集猜合集名`)
  const desc = arg('--desc', '')
  const gate = `${RUN}/I_HAVE_USER_OK_COLLECTION=${name}`
  console.log(`\n【collectioncreate】要建的合集：「${name}」${desc ? `（简介：${desc}）` : ''}`)
  if (!existsSync(gate)) {
    console.log(`停在建合集前：闸门文件不存在 ${gate}`)
    console.log('这个文件只能来自对话里对「建这个合集」的点头，脚本不自己造。')
    process.exitCode = 3
  } else {
    console.log(`  闸门：${gate}`)
    console.log(`    ${readFileSync(gate, 'utf8').trim()}`)
    const xsTitle = ep.publish?.xiaohongshu?.title || ''
    const form = await claimEditPage(xsTitle)
    const readRow = makeReadRow(form, name)
    const pre = await readRow()
    console.log(`  编辑页：${pre.url}`)
    console.log(`  合集那一行现在是：「${pre.row}」`)
    const items = await openCollectionPicker(form)
    const cnt = await items.count()
    const labels = []
    for (let i = 0; i < cnt; i++) labels.push((await items.nth(i).innerText().catch(() => '')).replace(/\s+/g, ' ').trim())
    console.log(`  弹层里现有的可选项（${cnt}）：${labels.map((s) => `「${s}」`).join(' | ') || '无'}`)
    if (labels.includes(name)) throw new Error(`弹层里已经有逐字等于「${name}」的项——不重复建`)
    // footer 的「创建合集」按逐字文本点（不按子串：子串会把含 footer 的容器也捞进来）
    const foot = form.locator('.d-popover').getByText('创建合集', { exact: true }).last()
    if (!(await foot.count())) throw new Error('弹层里没有逐字「创建合集」的入口——不猜')
    await foot.click({ timeout: 15_000 })
    await form.waitForTimeout(3500)
    const nameIn = form.locator('input[placeholder*="合集名称"]').first()
    await nameIn.waitFor({ state: 'attached', timeout: 15_000 })
    await nameIn.click()
    await nameIn.fill(name)
    await form.waitForTimeout(600)
    const descIn = form.locator('textarea, input[placeholder*="简介"]').first()
    if (desc && (await descIn.count())) {
      await descIn.click()
      await descIn.fill(desc)
      await form.waitForTimeout(600)
    }
    const typed = await form.evaluate(() => {
      const txt = (s) => (s || '').replace(/\s+/g, ' ').trim()
      return [...document.querySelectorAll('input,textarea')]
        .filter((e) => e.getBoundingClientRect().width)
        .map((e) => ({ ph: e.getAttribute('placeholder') || '', v: txt(e.value).slice(0, 40) }))
        .filter((x) => x.v)
    })
    console.log(`  建合集弹层里已填：${typed.map((x) => `「${x.ph || '(无placeholder)'}」=「${x.v}」`).join(' | ') || '（一个都没回读到，危险）'}`)
    await form.screenshot({ path: `${RUN}/${EP}-collectioncreate-filled.png` })
    const mk = form.getByText('创建并加入', { exact: true }).last()
    if (!(await mk.count())) throw new Error('没有逐字「创建并加入」的按钮——不猜')
    await mk.click({ timeout: 15_000 })
    await form.waitForTimeout(7000)
    const post = await readRow()
    console.log(`  点完「创建并加入」：这一行写着「${post.row}」`)
    const words = await form.evaluate(() => {
      const m = (document.body.innerText || '').replace(/\s+/g, ' ').match(/(成功创建|创建成功|共\s*\d+\s*篇)/g)
      return m ? [...new Set(m)].slice(0, 4) : []
    })
    console.log(`  页面上读到的字：${words.join(' | ') || '无「成功创建/共N篇」字样（以重开核对为准）'}`)
    await form.screenshot({ path: `${RUN}/${EP}-collectioncreate.png` })
    console.log(`  截图：${RUN}/${EP}-collectioncreate.png`)
    // 服务端核对：重开这条编辑页，那一行要写着新合集名
    const url = form.url()
    await form.goto(url, { waitUntil: 'domcontentloaded' })
    await form.waitForTimeout(12_000)
    const ver = await readRow()
    console.log(`  重开编辑页核对：这一行写着「${ver.row}」→ 显示合集名：${ver.picked ? '是' : '否'}`)
    await form.screenshot({ path: `${RUN}/${EP}-collectioncreate-verified.png` })
    console.log(`  截图：${RUN}/${EP}-collectioncreate-verified.png`)
    console.log('  到这里停手：没点提交。这条要不要落盘，下一步 collection --go 决定。')
  }
} else if (verb === 'attach') {
  // 在发布表单（/publish/publish）上把合集选好——点发布时合集一并落盘，省掉"发完再回编辑页补一遍"。
  // 只改表单状态、不点任何提交，所以不要闸门；判据同 collection：读那一行整行文本。
  const name = ep.publish?.xiaohongshu?.collection
  if (!name) throw new Error(`${EP} 没有 publish.xiaohongshu.collection——不替这一集猜合集名`)
  await settle()
  const readRow = makeReadRow(page, name)
  const pre = await readRow()
  console.log(`\n【attach】发布表单：${pre.url}`)
  console.log(`  合集那一行现在是：「${pre.row}」`)
  if (pre.picked) {
    console.log('  已经选着，不用再点')
  } else {
    const items = await openCollectionPicker(page)
    const cnt = await items.count()
    const labels = []
    let item = null
    for (let i = 0; i < cnt; i++) {
      const t = (await items.nth(i).innerText().catch(() => '')).replace(/\s+/g, ' ').trim()
      labels.push(t)
      if (t === name) item = items.nth(i)
    }
    console.log(`  弹层里的可选项（${cnt}）：${labels.map((s) => `「${s}」`).join(' | ') || '无'}`)
    if (!item) throw new Error(`弹层里没有逐字等于「${name}」的选项——不猜该点哪一条`)
    await item.click({ timeout: 15_000 })
    await page.waitForTimeout(4000)
  }
  const after = await readRow()
  console.log(`  现在这一行写着：「${after.row}」→ 显示合集名：${after.picked ? '是' : '否'}`)
  await page.screenshot({ path: `${RUN}/${EP}-attach.png` })
  console.log(`  截图：${RUN}/${EP}-attach.png`)
} else if (verb === 'publish') {
  // 发布（不可逆）。闸门 I_HAVE_USER_OK=<ep> 只从对话里的点头来：
  // 2026-10-17 用户授权「今晚 17 条连跑全发」，每条一文件（内容=那句原话 + 该集 id）。
  // 点法同 collection 的提交：<xhs-publish-btn> 是 closed shadow，真实鼠标在宿主 rect 内坐标点能命中。
  // 判据：点完 URL 要变成 published=true（事后信号，实测过）；权威核对（笔记管理「已发布」）由批后统一跑一遍。
  const runStartedAt = new Date().toISOString()
  const gate = `${RUN}/I_HAVE_USER_OK=${EP}`
  if (!existsSync(gate)) {
    console.log(`停在发布前：闸门文件不存在 ${gate}`)
    console.log('这个文件只能来自对话里对这一条的点头，脚本不自己造。')
    process.exitCode = 3
  } else if (!process.argv.includes('--go')) {
    console.log(`闸门：${gate}\n  ${readFileSync(gate, 'utf8').trim()}`)
    console.log('闸门在，但没给 --go：这一步不代点（默认归人）。要脚本点发布加 --go。')
    process.exitCode = 3
  } else {
    const gateText = readFileSync(gate, 'utf8').trim()
    console.log(`闸门：${gate}`)
    console.log(`  ${gateText}`)
    await settle()
    const btn = await page.evaluate(() => {
      const el = document.querySelector('xhs-publish-btn')
      if (!el) return null
      const r = el.getBoundingClientRect()
      return {
        attrs: [...el.attributes].map((a) => `${a.name}=${a.value}`).join(' '),
        rect: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}x${Math.round(r.height)}`,
      }
    })
    if (!btn) throw new Error('发布页上找不到 <xhs-publish-btn>——按钮换样子了，别硬点')
    console.log(`  发布按钮：<xhs-publish-btn ${btn.attrs}> rect=${btn.rect}`)
    const url0 = page.url()
    await page.locator('xhs-publish-btn').first().scrollIntoViewIfNeeded().catch(() => {})
    await page.waitForTimeout(800)
    const pt = await findPublishButtonBox(page)
    if (!pt) throw new Error('CDP 穿透没量到「发布」那颗按钮——不猜坐标')
    console.log(`  CDP 穿透量到「发布」盒=${pt.quad} → 真实点击 (${pt.cx},${pt.cy})`)
    await page.mouse.click(pt.cx, pt.cy)
    let after = null
    for (let i = 0; i < 6; i++) {
      await page.waitForTimeout(4000)
      after = await page.evaluate(() => {
        const m = (document.body.innerText || '').replace(/\s+/g, ' ').match(/(发布成功|提交成功|更新成功|成功发布)/)
        return { toast: m ? m[1] : null, url: location.href }
      })
      if (/published=true/.test(after.url)) break
    }
    console.log(`  点完：提示=${after?.toast ? `「${after.toast}」` : '(没读到)'} URL=${(after?.url || '').slice(0, 110)}`)
    if (!/published=true/.test(after?.url || '')) {
      await page.screenshot({ path: `${RUN}/${EP}-publish-uncertain.png` })
      throw new Error(`点完 URL 没变成 published=true（原 ${url0.slice(0, 80)}）——按没发出去对待，截图 ${EP}-publish-uncertain.png`)
    }
    console.log('  URL 已 published=true；权威核对（笔记管理「已发布」）批后统一跑')
    await page.screenshot({ path: `${RUN}/${EP}-published.png` })
    console.log(`  截图：${RUN}/${EP}-published.png`)
    // 写 marker 再消费闸门：marker 是"这条在线"的凭据，闸门是"可以发"的授权。
    // 取不到 noteId 就记 noteId=null + since，不伪造；重跑幂等靠 noteId/since，不靠标题。
    let noteId = ''
    try {
      const hit = await freshNoteIdByTitle(ep.publish?.xiaohongshu?.title || '')
      noteId = hit?.id || ''
      console.log(noteId ? `  笔记管理里读到新 noteId=${noteId}` : '  笔记管理里暂未读到这张卡片的 noteId（不伪造）')
    } catch (e) {
      console.log(`  读 noteId 失败（不伪造）：${e.message}`)
    }
    const oneLine = (s) => String(s || '').replace(/\s+/g, ' ').trim()
    const now = new Date().toISOString()
    const marker = `${RUN}/${EP}-published.txt`
    const line = noteId
      ? `noteId=${noteId}\turl=${after.url}\tat=${now}\tgate=${oneLine(gateText)}`
      : `noteId=null\tsince=${runStartedAt}\turl=${after.url}\tat=${now}\tgate=${oneLine(gateText)}`
    writeFileSync(marker, line + '\n')
    console.log(`  台账：${marker}\n    ${line}`)
    unlinkSync(gate)
    console.log(`  闸门已消费：${gate}`)
  }
} else {
  throw new Error(`未知步骤「${verb}」，认得的是 status / open / upload / measure / fill / topics / cover / coverset / coverapply / comment / collection / collectioncheck / collectioncreate / attach / publish`)
}

function statSize(p) {
  return statSync(p).size
}
// 不调 browser.close()：那是 CDP 连接上的 close，会把常驻浏览器和登录态一起带走。
// 工作标签页留着不关（选好的视频与填好的字只活在那一页），进程退出、socket 跟着死就行。
process.exit(process.exitCode || 0)
