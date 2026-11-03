// B站网页投稿：连 9223 那个常驻浏览器，按名字执行一步，打印这一步看到了什么。
// 为什么换这条路：biliup-rs 那份凭证只有 SESSDATA/bili_jct/…，没有 buvid3/buvid4/bili_ticket，
// 投稿前检查一律回 21566（--submit client/app/web 三种口味都撞，31 秒就弹回，片源根本没传）。
// 浏览器里同一账号是完整会话，且已经证明发得出稿（同账号 EP10–EP18 在 10-14 23:22→10-15 00:26 连发 9 条）。
// 每步只做一件可逆的事；feed 只把文件交给页面，稿件在点「投稿」之前不存在，所以可关页放弃。
// 唯一不可逆的 publish 要等闸门文件 .temp/bili-web-run/I_HAVE_USER_OK=<ep> 出现才动，
// 那个文件只能来自对话里用户对这一条 B站稿件的点头，脚本不自己造。
// 要填的字全部来自 video/out/<ep>/bili-submit.yaml（它由 video/publish/bili-submit.mjs 从
// episode.json 的 publish.bilibili + series.json + timeline.json 生成），脚本里不写任何一集的字。
import { chromium } from 'playwright'
import { readFileSync, existsSync, mkdirSync, appendFileSync, writeFileSync, unlinkSync } from 'node:fs'

const RUN = 'D:/Users/mcu/.temp/bili-web-run'
mkdirSync(RUN, { recursive: true })
const step = process.argv[2]
// 之前只认 "--ep c4"，写成 "--ep=c4" 会被静默忽略、掉回默认值——批量跑 15 条时
// 这就是"给 c4 填了 c2 的字"。两种写法都认，且不再让默认值悄悄生效。
function arg(name) {
  const eq = process.argv.findIndex((a) => a.startsWith(`${name}=`))
  if (eq >= 0) return process.argv[eq].slice(name.length + 1)
  const i = process.argv.indexOf(name)
  return i >= 0 ? process.argv[i + 1] : null
}
const EP = arg('--ep') ?? 'c2-pointer'
const DECL = arg('--decl') ?? ''
const TID_NAME = arg('--tid') ?? ''

const CFG = `D:/Users/mcu/video/out/${EP}/bili-submit.yaml`
const ep = JSON.parse(readFileSync(`D:/Users/mcu/video/episodes/${EP}/episode.json`, 'utf8'))
const pub = ep.publish?.bilibili
const F = {
  video: `D:/Users/mcu/video/out/${EP}/bilibili.mp4`,
  cover: `D:/Users/mcu/video/out/${EP}/bilibili-cover.png`,
}
// yaml 是"键: 值"的扁平结构 + 一段块标量 desc；这里只取要填的四个字段，取不到就停手，不猜默认值。
function cfg(field) {
  if (!existsSync(CFG)) throw new Error(`投稿配置不存在：${CFG}`)
  const t = readFileSync(CFG, 'utf8')
  if (field === 'desc') {
    const m = t.match(/\n {4}desc: "((?:[^"\\]|\\.)*)"/)
    if (!m) throw new Error('配置里没读到 desc')
    return JSON.parse(`"${m[1]}"`)
  }
  let m = t.match(new RegExp(`^\\s{4}${field}:\\s*"(.*)"$`, 'm'))
  if (!m) m = t.match(new RegExp(`^\\s{4}${field}:\\s*(\\S[^\\n]*)$`, 'm'))
  if (!m) throw new Error(`配置里没读到 ${field}`)
  return m[1]
}

const browser = await chromium.connectOverCDP('http://127.0.0.1:9223')
const ctx = browser.contexts()[0]
// 投稿页与"稿件管理"（/platform/upload-manager/article）前缀撞；更麻烦的是这个浏览器有人同时在用，
// c5 的标签页就被关掉过一次——按"最新的 frame 页"选页于是挑中了 c4 的表单，挑错页就是给上一条稿件填下一条的字。
// 改成开页时给标签页盖一个 window.__biliEp 的章，选页只认盖了本集章的那个。
let page = null
for (const p of [...ctx.pages()].reverse()) {
  if (!/member\.bilibili\.com\/platform\/upload\/video\/frame/.test(p.url())) continue
  if ((await p.evaluate(() => window.__biliEp ?? '').catch(() => '')) === EP) { page = p; break }
}
// open 步还没有页；给任何新开的页统一装超时和 dialog 钩子，别只装挑中的那一个。
const withHooks = (p) => {
  p.setDefaultTimeout(180_000)
  p.on('dialog', async (d) => {
    const line = `${new Date().toISOString()} type=${d.type()} message=${d.message()}`
    appendFileSync(`${RUN}/dialogs.log`, `${line}\n`)
    console.log('DIALOG', line)
    if (d.type() === 'beforeunload') await d.accept().catch(() => {})
    else await d.dismiss().catch(() => {})
  })
  return p
}
// 换源的编辑页（?type=edit&bvid=）也落在 upload/video/frame 前缀下，靠同一枚章认页；
// 只认 URL 里就是这条 BV 的那张，免得把投稿表单当成编辑页。
async function editPageFor(bvid) {
  for (const p of [...ctx.pages()].reverse()) {
    const u = p.url()
    if (!/\/upload\/video\/frame\?/.test(u) || !u.includes('type=edit') || !u.includes(`bvid=${bvid}`)) continue
    if ((await p.evaluate(() => window.__biliEp ?? '').catch(() => '')) === EP) return p
  }
  return null
}
if (!page && step !== 'open' && step !== 'editopen') throw new Error(`没有 ${EP} 的投稿标签页（被关了？还是没跑过 open）：先 node video/publish/bili-web.mjs open --ep=${EP}`)
if (page) withHooks(page)

// 「更多设置」里那几格有两个坑，都是实测踩出来的：
// ①「杜比音效」「Hi-Res无损音质」的文本节点带子元素（后面那个 ⓘ），按"无子节点"筛
//    就永远找不到标签——要取"最深的、文本等于标签的可见节点"。
// ②控件不一定是原生 input：自绘开关/单选只看 input.checked，会量成"没找到"。
// 读现值和点掉必须共用这一套判据，否则 setmore 说点掉了、publish 又报还开着。
const PICK = `
  const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
  const T = (e) => (e.innerText || '').replace(/\\s+/g, ' ').trim()
  const pick = (lab) => {
    const ns = [...document.querySelectorAll('*')].filter((e) => vis(e) && T(e) === lab)
    return ns.filter((e) => ![...e.children].some((c) => T(c) === lab)).pop() || null
  }
  const isOn = (e) => e.checked === true || /checked|active|is-on|true/.test(String(e.className)) ||
    (e.getAttribute && e.getAttribute('aria-checked') === 'true')
  const ctrls = (r, onlyOn) => [...document.querySelectorAll('input,[class*=check-radio-v2-box],[class*=switch-container],[class*=switch-roll],[class*=bcc-checkbox-checkbox]')]
    .filter((e) => {
      const q = e.getBoundingClientRect()
      if (!(Math.abs(q.y - r.y) < 26 && q.x > r.x - 40)) return false
      if (!(vis(e) || e.tagName === 'INPUT')) return false
      return !onlyOn || isOn(e)
    })
`
const TICKLABS = ['添加水印', '公开可见', '仅自己可见', '关闭弹幕', '开启精选评论', '杜比音效', 'Hi-Res无损音质']
const readTicks = (labs) => page.evaluate(`(() => {
  ${PICK}
  const out = {}
  for (const lab of ${JSON.stringify(labs)}) {
    const n = pick(lab)
    if (!n) { out[lab] = 'no-label'; continue }
    const r = n.getBoundingClientRect()
    out[lab] = { 位置: Math.round(r.x) + ',' + Math.round(r.y),
      控件: ctrls(r, false).map((e) => e.tagName.toLowerCase() + '.' + String(e.className).split(' ')[0].slice(0, 20) + ':' + (isOn(e) ? '开' : '关')) }
  }
  return out
})()`)
const uncheckTicks = (labs) => page.evaluate(`(() => {
  ${PICK}
  const out = {}
  for (const lab of ${JSON.stringify(labs)}) {
    const n = pick(lab)
    if (!n) { out[lab] = 'no-label'; continue }
    const on = ctrls(n.getBoundingClientRect(), true)
    if (!on.length) { out[lab] = '本来就是关的'; continue }
    const t = on[0].closest('label') ?? on[0].parentElement ?? on[0]
    t.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }))
    out[lab] = '点掉了(' + on[0].tagName.toLowerCase() + '→' + t.tagName.toLowerCase() + ')'
  }
  return out
})()`)

// 创作声明这一格发布后锁死，只能投稿前定。实测新表单自带默认值「内容无需标注」，
// 下拉里那项还挂着 .bcc-option.selected——现值已经对就别去点开它：这个自定义下拉
// 点开后会盖住自己，再点 input 就是 Playwright 那句 "element is not visible"（c5 撞的就是这个）。
// 只有现值不等于目标才开下拉点那一项，点完必须读回，读不回目标值停手。
const declNow = () => page.evaluate(() => {
  const e = [...document.querySelectorAll('input')].find((x) => x.placeholder === '请选择符合您视频内容的创作声明')
  return e ? e.value : null
})
async function setDecl(log) {
  if (!DECL) { log('创作声明：未给 --decl，留空不碰'); return }
  const cur = await declNow()
  if (cur === null) throw new Error('找不到创作声明那一格（占位符变了？）')
  if (cur === DECL) { log(`创作声明：现值已是「${DECL}」，不点下拉`); return }
  const box = page.locator('input[placeholder="请选择符合您视频内容的创作声明"]').first()
  await box.evaluate((e) => e.scrollIntoView({ block: 'center' })).catch(() => {})
  await page.waitForTimeout(400)
  await box.click({ timeout: 8000 })
  await page.waitForTimeout(1200)
  const li = page.locator('.bcc-select-option-list li:visible', { hasText: DECL })
  const n = await li.count()
  if (!n) {
    const all = await page.locator('.bcc-select-option-list li:visible').allInnerTexts()
    throw new Error(`下拉里没有「${DECL}」，停手不猜。可见选项：${JSON.stringify(all).slice(0, 300)}`)
  }
  await li.first().click({ timeout: 8000 })
  await page.waitForTimeout(900)
  await page.getByText('标题', { exact: true }).first().click({ timeout: 4000 }).catch(() => {})
  const back = await declNow()
  if (back !== DECL) throw new Error(`点完读回是「${back}」不是「${DECL}」，停手`)
  log(`创作声明 ${cur} → ${back}（命中 ${n} 项）`)
}

async function shot(name) {
  const p = `${RUN}/${EP}-${name}.png`
  try { await page.screenshot({ path: p, timeout: 20000 }) }
  catch (e) { console.log('📷 截图失败', String(e).slice(0, 60)); return p }
  console.log('📷', p, '  URL:', page.url())
  return p
}

// 表单里能填的东西一次量全，后面的核对步与这里共用同一份量法。
const snap = () => page.evaluate(() => {
  const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
  const T = (e) => (e.innerText || e.value || e.getAttribute('placeholder') || '').replace(/\s+/g, ' ').trim()
  const box = (e) => { const r = e.getBoundingClientRect(); return `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }
  return {
    url: location.href,
    // 上传进度：网页上是"上传中 xx%"这类字，成功进表单后会消失。原文收回来，不解释。
    uploadText: [...document.querySelectorAll('*')].filter((e) => !e.children.length && vis(e))
      .map((e) => T(e)).filter((s) => /上传|转码|审核|完成/.test(s) && s.length < 40).slice(0, 12),
    inputs: [...document.querySelectorAll('input,textarea')].filter(vis).map((e) =>
      `type=${e.type || e.tagName.toLowerCase()} 占位="${String(e.placeholder || '').slice(0, 30)}" 值="${String(e.value || '').slice(0, 26)}" 位置=${box(e)}`).slice(0, 20),
    fileInputs: [...document.querySelectorAll('input[type=file]')].map((e, i) =>
      `#${i} accept="${String(e.accept).slice(0, 26)}" 可见=${vis(e)}`),
    buttons: [...document.querySelectorAll('button,[role=button],.el-button')].filter(vis)
      .map((e) => `${T(e).slice(0, 16) || '(空)'}[${e.disabled ? '禁用' : '可点'}] ${box(e)}`).slice(0, 26),
    labels: [...document.querySelectorAll('*')].filter((e) => !e.children.length && vis(e))
      .map((e) => T(e)).filter((s) => /^(标题|简介|标签|分区|封面|声明|定时发布|创建合集|标签：|更多信息)/.test(s)).slice(0, 16),
    bodyHead: document.body.innerText.replace(/\s+/g, ' ').slice(0, 320),
  }
})

// 编辑页的状态指纹：换源前后各量一次，「上传完成」是否回来、标题有没有被动过，一眼可查。
const editState = () => page.evaluate(() => {
  const T = (e) => (e.innerText || e.value || '').replace(/\s+/g, ' ').trim()
  const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
  const title = [...document.querySelectorAll('input')].find((x) => x.type !== 'file' && (/标题/.test(x.placeholder || '') || String(x.value || '').length > 12))
  return {
    标题: title ? String(title.value) : '',
    上传态: [...new Set([...document.querySelectorAll('*')].filter((e) => !e.children.length && vis(e) && T(e).length < 20 && /上传完成|上传中|转码|更换视频|失败/.test(T(e))).map(T))].slice(0, 8),
    提示: [...new Set([...document.querySelectorAll('*')].filter((e) => !e.children.length && vis(e) && T(e).length < 40 && /成功|失败|错误|稍后|重新/.test(T(e))).map(T))].slice(0, 8),
  }
})

// 点「更换视频」后的站内确认框：「更换视频后将产生以下影响 …[取消][确定]」。
// 这是自定义模态（DIV.bcc-dialog），不是系统 confirm；按钮在 dialog 的 footer 里，
// 从警告文案往上爬、找到同时含该按钮的祖先再点——绝不点页面别处的「确定」。
const clickReplaceModal = (label) => page.evaluate((label) => {
  const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
  const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
  const warns = [...document.querySelectorAll('*')].filter((e) => vis(e) && T(e).includes('更换视频后将产生以下影响'))
  if (!warns.length) return 'no-modal'
  let box = warns[warns.length - 1]
  for (let i = 0; i < 8 && box; i++, box = box.parentElement) {
    const btn = [...box.querySelectorAll('button,[role=button]')].filter((e) => vis(e) && T(e) === label)[0]
    if (btn) {
      btn.setAttribute('data-replace-modal', '1')
      return 'ok'
    }
  }
  return 'no-button'
}, label).then(async (r) => {
  if (r !== 'ok') return r
  await page.locator('[data-replace-modal="1"]').first().click({ timeout: 8000 })
  return r
})

// 编辑页的封面预览有时是 DIV.cover-img 的背景图，有时要按「封面」标签找右邻的
// background-image 节点；两套判据都留着，读同一个 URL。
const readCoverBg = () => page.evaluate(() => {
  const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
  const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
  const strip = (u) => u.replace(/^url\("?|"?\)$/g, '')
  const c = document.querySelector('.cover-img')
  if (c) { const u = strip(getComputedStyle(c).backgroundImage); if (u) return u }
  for (const e of document.querySelectorAll('*')) {
    if (!vis(e) || T(e) !== '封面') continue
    const cand = e.closest('div')?.parentElement?.querySelector('[style*="background-image"]')
    if (cand) { const u = strip(getComputedStyle(cand).backgroundImage); if (u) return u }
  }
  return ''
})

const V = {
  // 换源第 1 步（只读）：打开已发布稿的编辑页（?type=edit&bvid=），核对标题/合集/封面/提交按钮。
  // 不点「更换视频」、不点「立即投稿」——这一步只回答"这页是不是这条稿、能不能在这里换源"。
  async editopen() {
    const bvid = arg('--bvid') ?? ''
    if (!/^BV[0-9A-Za-z]{10}$/.test(bvid)) throw new Error('--bvid 缺失或不合法')
    const want = cfg('title')
    page = (await editPageFor(bvid)) ?? withHooks(await ctx.newPage())
    if (!page.url().includes('type=edit')) {
      await page.goto(`https://member.bilibili.com/platform/upload/video/frame?type=edit&bvid=${bvid}`, { waitUntil: 'domcontentloaded', timeout: 60000 })
      await page.evaluate((ep) => { window.__biliEp = ep }, EP)
      await page.waitForTimeout(8000)
    }
    const info = await page.evaluate((want) => {
      const T = (e) => (e.innerText || e.value || '').replace(/\s+/g, ' ').trim()
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const box = (e) => { const r = e.getBoundingClientRect(); return `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }
      const titleInput = [...document.querySelectorAll('input')].find((i) => String(i.value) === want)
        || [...document.querySelectorAll('input')].find((i) => /标题/.test(i.placeholder || ''))
      const submit = [...document.querySelectorAll('*')].filter((e) => !e.children.length && T(e) === '立即投稿' && vis(e))[0]
      let cover = ''
      for (const e of document.querySelectorAll('*')) {
        if (!vis(e) || T(e) !== '封面') continue
        const cand = e.closest('div')?.parentElement?.querySelector('[style*="background-image"]')
        if (cand) cover = getComputedStyle(cand).backgroundImage
        if (cover) break
      }
      return {
        url: location.href,
        标题: titleInput ? String(titleInput.value) : '(没找到标题框)',
        提交按钮: submit ? `灰=${/disabled/i.test(String(submit.className)) || !!submit.closest('[class*=disabled]')} ${box(submit)}` : '(没找到立即投稿)',
        封面背景: cover.replace(/^url\("?|"?\)$/g, '').slice(0, 200),
        合集行: [...new Set([...document.querySelectorAll('*')].filter((e) => !e.children.length && vis(e) && /加入合集|通往单片机之路|选择合集/.test(T(e))).map(T))].slice(0, 6),
        上传态: [...new Set([...document.querySelectorAll('*')].filter((e) => !e.children.length && vis(e) && /上传完成|上传中|转码|更换视频/.test(T(e))).map(T))].slice(0, 8),
        时钟: [...new Set((document.body.innerText.match(/\b\d{2}:\d{2}:\d{2}\b/g) || []))].slice(0, 6),
      }
    }, want)
    console.log(JSON.stringify(info, null, 1))
    if (!info.url.includes(`bvid=${bvid}`)) throw new Error(`编辑页 URL 里没有 bvid=${bvid}，停手：${info.url}`)
    if (info.标题 !== want) throw new Error(`编辑页标题「${info.标题}」≠ 配置「${want}」，停手`)
    if (/没找到立即投稿/.test(info.提交按钮)) throw new Error('编辑页上没有「立即投稿」，停手不猜')
    await shot('editopen')
  },
  // 只读探针：不校验任何值，只把编辑页此刻的输入框/提示/正文原样抄出来。
  // 提交后页面可能重绘成空表单或加载中，editopen 的断言会先抛错，看不到现场。
  async editpeek() {
    const bvid = arg('--bvid') ?? ''
    if (!/^BV[0-9A-Za-z]{10}$/.test(bvid)) throw new Error('--bvid 缺失或不合法')
    page = (await editPageFor(bvid)) ?? page
    if (!page) throw new Error(`没有 ${bvid} 的编辑页`)
    await page.waitForTimeout(3000)
    await page.evaluate(() => window.scrollTo(0, 0)).catch(() => {})
    await page.waitForTimeout(800)
    const info = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const T = (e) => (e.innerText || e.value || '').replace(/\s+/g, ' ').trim()
      return {
        url: location.href,
        readyState: document.readyState,
        文档标题: document.title,
        可见标题框: [...document.querySelectorAll('input')].filter((e) => vis(e) && /标题/.test(e.placeholder || ''))
          .map((e) => `value="${String(e.value).slice(0, 80)}" ph="${e.placeholder}" box=${Math.round(e.getBoundingClientRect().x)},${Math.round(e.getBoundingClientRect().y)}`),
        输入框: [...document.querySelectorAll('input')].filter(vis)
          .map((e, i) => `#${i} type=${e.type} value="${String(e.value).slice(0, 60)}" ph="${String(e.placeholder).slice(0, 30)}"`).slice(0, 14),
        视频区: [...new Set([...document.querySelectorAll('*')].filter((e) => !e.children.length && vis(e) && /n2610|bilibili|上传完成|上传中|转码|更换视频|\d{1,3}%/.test(T(e)) && T(e).length < 80).map(T))].slice(0, 20),
        按钮: [...new Set([...document.querySelectorAll('button,[role=button]')].filter(vis).map(T).filter(Boolean))].slice(0, 14),
        正文前400: T(document.body).slice(0, 400),
      }
    })
    console.log(JSON.stringify(info, null, 1))
    await page.screenshot({ path: `${RUN}/${EP}-editpeek-full.png`, fullPage: true, timeout: 20000 }).catch((e) => console.log('全页截图失败', String(e).slice(0, 60)))
    await shot('editpeek')
  },
  // 换源第 2 步（只传片，不交）：把新母版喂给编辑页。上传完成之前平台上的旧稿不受影响。
  // 只走真入口「更换视频 → 站内确认框 → filechooser」：页面上那几个 mp4 input 是分P/别处的，
  // 上一轮喂它们上了两条新片，主视频却仍是旧的——那是把新片传成了别的东西，不是换源。
  async replacesrc() {
    if (!existsSync(F.video)) throw new Error(`片源不存在：${F.video}`)
    if ((await clickReplaceModal('取消')) === 'ok') { console.log('  清掉遗留的更换确认框'); await page.waitForTimeout(1200) }
    const formState = () => page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const T = (e) => (e.innerText || e.value || '').replace(/\s+/g, ' ').trim()
      const title = [...document.querySelectorAll('input')].filter((e) => e.type !== 'file' && vis(e) && /标题/.test(e.placeholder || ''))[0]
      const body = document.body.innerText.replace(/\s+/g, ' ')
      return {
        标题: title ? String(title.value) : '(无可见标题框)',
        上传中: /上传中|转码中|转码/.test(body),
        上传完成: /上传完成/.test(body),
        更换视频: /更换视频/.test(body),
        视频项: [...new Set([...document.querySelectorAll('*')].filter((e) => !e.children.length && vis(e) && T(e).length < 40 && /bilibili|上传完成|上传中|转码|更换视频/.test(T(e))).map(T))].slice(0, 10),
      }
    })
    const net = []
    const onResp = async (res) => {
      const u = res.url()
      if (!/member\.bilibili\.com\/(upload\/multipart|x\/vupre\/web\/archive\/videocheck|x\/vu\/web\/(edit|draft|add))/.test(u)) return
      let j = null
      try { j = await res.json() } catch {}
      const line = `${res.status()} ${u.replace(/^https:\/\/[^/]+/, '').split('?')[0]} code=${j?.code ?? '?'} ${String(j?.message ?? j?.msg ?? '').slice(0, 60)}`
      net.push(line)
      console.log('  NET', line)
    }
    const onReq = (rq) => {
      if (!/\/x\/vu\/web\/(edit|draft)/.test(rq.url())) return
      const pd = rq.postData() || ''
      const files = [...pd.matchAll(/"filename":"([^"]+)"/g)].map((m) => m[1]).slice(0, 4)
      const titles = [...pd.matchAll(/"title":"((?:[^"\\]|\\.){0,30})/g)].map((m) => m[1]).slice(0, 3)
      console.log('  REQ', rq.method(), rq.url().replace(/^https:\/\/[^/]+/, '').split('?')[0], 'files=', JSON.stringify(files), 'titles=', JSON.stringify(titles))
    }
    page.on('response', onResp)
    page.on('request', onReq)
    try {
      console.log('  换前：', JSON.stringify(await formState()))
      const hop = page.waitForEvent('filechooser', { timeout: 15000 }).catch(() => null)
      await page.getByText('更换视频', { exact: true }).first().click({ timeout: 15000 })
        .catch((e) => console.log('  「更换视频」点不动：', String(e).split('\n')[0].slice(0, 90)))
      let fc = await hop
      if (!fc) {
        // 文件框是在点「确定」之后才唤起的，监听必须先挂上——上一版点完确定才去等，
        // 事件已经在那一瞬过去（没人接就自动取消），于是永远等不到。
        const hop2 = page.waitForEvent('filechooser', { timeout: 15000 }).catch(() => null)
        const r = await clickReplaceModal('确定')
        console.log('  确认框：', r)
        if (r !== 'ok') { await shot('replacesrc-nochooser'); throw new Error('「更换视频」没有唤起确认框/文件选择，停手') }
        fc = await hop2
      }
      if (!fc) { await shot('replacesrc-nochooser2'); throw new Error('确认框之后没有 filechooser，停手') }
      await fc.setFiles(F.video)
      console.log(`  filechooser 已喂 ${F.video}`)
      let sawDone = false
      for (let i = 0; i < 150; i++) {
        await page.waitForTimeout(2000)
        const s = await formState()
        if (i % 5 === 0 || sawDone !== s.上传完成) console.log(`  ${i * 2 + 2}s：`, JSON.stringify(s))
        sawDone = s.上传完成
        const netDone = net.some((l) => /upload\/multipart\/complete/.test(l)) && net.some((l) => /videocheck/.test(l) && /code=0/.test(l))
        if (s.上传完成 && !s.上传中 && netDone) { console.log(`  ${i * 2 + 2}s：上传完成（接口见 complete + videocheck code=0）`); break }
        if (i === 149) { await shot('replacesrc-timeout'); throw new Error('5 分钟没等到上传完成，停手（页面保留）') }
      }
      await page.waitForTimeout(8000)
      console.log('  换后：', JSON.stringify(await formState()))
      console.log('  接口：', JSON.stringify(net.slice(-12)))
      await shot('replacesrc')
    } finally {
      page.off('response', onResp)
      page.off('request', onReq)
    }
  },
  // 换源第 3 步（只换封面，不交）：点封面预览 → 传 v2 封面 → 勾「双比例同步改动」→「完成」。
  // 和投稿页的 cover 步同一套动作，只是入口从「添加封面」换成封面预览本身。
  async replacecover() {
    if (!existsSync(F.cover)) throw new Error(`封面不存在：${F.cover}`)
    const before = await readCoverBg()
    console.log('  换前封面：', before.slice(0, 120))
    if (!before) { await shot('replacecover-nobg'); throw new Error('页面上读不到封面背景 URL，停手') }
    // 上一轮 probe 可能把封面弹窗留在打开状态：已经开着就直接喂图，别再点被遮住的预览。
    const modalOpen = await page.evaluate(() => document.body.innerText.includes('封面制作'))
    if (modalOpen) console.log('  封面弹窗已开着，直接喂图')
    else {
      await page.locator('.cover-img').first().click({ timeout: 10000 })
      await page.waitForTimeout(3000)
    }
    const img = page.locator('input[type=file][accept*="png"], input[type=file][accept*="jpeg"]').first()
    if (!(await img.count())) { await shot('replacecover-noinput'); throw new Error('封面弹窗里没有图片 input，停手') }
    await img.setInputFiles(F.cover, { timeout: 60000 })
    console.log(`  已喂封面 ${F.cover}`)
    await page.waitForTimeout(4000)
    const previews = () => page.evaluate(() => [...document.querySelectorAll('img')]
      .filter((e) => (e.offsetWidth || e.offsetHeight) && e.getBoundingClientRect().width > 60)
      .map((e) => `${Math.round(e.getBoundingClientRect().width)}×${Math.round(e.getBoundingClientRect().height)} ${String(e.src).replace(/^https?:\/\/[^/]+\//, '').slice(0, 46)}`))
    console.log('  勾选前预览图：', JSON.stringify(await previews()))
    await page.getByText('双比例同步改动', { exact: true }).first().click({ timeout: 8000 })
      .catch((e) => console.log('  同步开关点不动：', String(e).split('\n')[0].slice(0, 80)))
    await page.waitForTimeout(2500)
    console.log('  勾选后预览图：', JSON.stringify(await previews()))
    await shot('replacecover-sync')
    await page.getByText('完成', { exact: true }).last().click({ timeout: 10000 })
    await page.waitForTimeout(3500)
    const after = await readCoverBg()
    console.log('  换后封面：', after.slice(0, 120))
    if (!after) { await shot('replacecover-empty'); throw new Error('完成后读不到封面背景，停手') }
    if (after === before) { await shot('replacecover-same'); throw new Error('封面 URL 没变——可能没应用成功，停手') }
    await shot('replacecover')
  },
  // 换源第 4 步（唯一不可逆）：点「立即投稿」提交这次换源——BV 不变，稿件进重新审核。
  // 两道闸门缺一不动：本脚本的 I_HAVE_USER_OK=<ep> 与 repost 的 I_HAVE_USER_OK_PUBLISH_<ep>，
  // 后者内容必须逐字等于用户在对话里的授权原话（--expect）。点过就消耗，绝不二次利用。
  async replace() {
    const bvid = arg('--bvid') ?? ''
    const day = arg('--day') ?? ''
    const expect = arg('--expect') ?? ''
    const collection = arg('--collection') ?? ''
    const oldcover = arg('--oldcover') ?? ''
    if (!/^BV[0-9A-Za-z]{10}$/.test(bvid)) throw new Error('--bvid 缺失或不合法')
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) throw new Error('--day=YYYY-MM-DD 缺失')
    if (!expect) throw new Error('--expect=用户授权原话 缺失')
    const gateA = `${RUN}/I_HAVE_USER_OK=${EP}`
    const gateB = `D:/Users/mcu/.temp/repost/${day}/${EP}/I_HAVE_USER_OK_PUBLISH_${EP}`
    for (const g of [gateA, gateB]) if (!existsSync(g)) throw new Error(`没有闸门文件 ${g} —— 用户对 ${EP} 这次换源点头之前不提交`)
    const ga = readFileSync(gateA, 'utf8').trim()
    const gb = readFileSync(gateB, 'utf8').trim()
    if (ga && ga !== expect) throw new Error(`闸门 A 内容「${ga}」≠ 授权原话「${expect}」，停手`)
    if (gb !== expect) throw new Error(`闸门 B 内容「${gb}」≠ 授权原话「${expect}」，停手`)
    console.log(`  闸门 A：${gateA}（「${ga || '(空)'}」）`)
    console.log(`  闸门 B：${gateB}（「${gb}」）`)

    const want = cfg('title')
    const cover = await readCoverBg()
    const st = await page.evaluate((want) => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const T = (e) => (e.innerText || e.value || '').replace(/\s+/g, ' ').trim()
      const title = [...document.querySelectorAll('input')].find((i) => i.type !== 'file' && vis(i) && String(i.value) === want)
        || [...document.querySelectorAll('input')].find((i) => i.type !== 'file' && vis(i) && /标题/.test(i.placeholder || ''))
      const submit = [...document.querySelectorAll('*')].filter((e) => !e.children.length && T(e) === '立即投稿' && vis(e))[0]
      const body = document.body.innerText.replace(/\s+/g, ' ')
      let hitTop = ''
      let rect = ''
      if (submit) {
        const r = submit.getBoundingClientRect()
        rect = `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`
        const top = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2)
        if (top && top !== submit && !top.contains(submit) && !submit.contains(top)) hitTop = `${top.tagName}.${String(top.className).slice(0, 60)} 文案="${T(top).slice(0, 20)}"`
      }
      return {
        url: location.href,
        标题: title ? String(title.value) : '',
        上传完成: /上传完成/.test(body),
        上传进行中: /上传中|转码中|\d{1,3}%/.test(body),
        更换视频: /更换视频/.test(body),
        视频项: [...new Set([...document.querySelectorAll('*')].filter((e) => !e.children.length && vis(e) && T(e).length < 40 && /bilibili|上传完成|上传中|转码|更换视频/.test(T(e))).map(T))].slice(0, 10),
        提交: submit ? { 位置: rect, 灰: /disabled/i.test(String(submit.className)) || !!submit.closest('[class*=disabled]'), 挡住: hitTop } : null,
      }
    }, want)
    const descWant = cfg('desc')
    const descNow = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const ql = [...document.querySelectorAll('.ql-editor')].filter(vis)[0]
      return ql ? (ql.innerText || '') : ''
    })
    console.log('  提交前：', JSON.stringify({ ...st, 封面: cover.slice(0, 100), 简介: `${descNow.replace(/\s+/g, '').length} 字（配置 ${descWant.replace(/\s+/g, '').length}）` }))
    const bad = []
    if (!st.url.includes('type=edit') || !st.url.includes(`bvid=${bvid}`)) bad.push(`不在 ${bvid} 的编辑页：${st.url}`)
    if (st.标题 !== want) bad.push(`标题「${st.标题}」≠ 配置「${want}」`)
    if (!st.上传完成 || st.上传进行中) bad.push(`上传态不干净：完成=${st.上传完成} 进行中=${st.上传进行中}`)
    if (!st.更换视频) bad.push('页面上没有「更换视频」——不是可换源的编辑页')
    if (!st.视频项.some((t) => /bilibili/.test(t))) bad.push(`视频项里没有新片 bilibili：${JSON.stringify(st.视频项)}`)
    if (!descNow || descNow.replace(/\s+/g, '').length < descWant.replace(/\s+/g, '').length * 0.95) bad.push(`简介没带上：页面 ${descNow.replace(/\s+/g, '').length} 字 / 配置 ${descWant.replace(/\s+/g, '').length} 字`)
    if (!st.提交) bad.push('找不到「立即投稿」')
    else if (st.提交.灰) bad.push('「立即投稿」是禁用态')
    else if (st.提交.挡住) bad.push(`「立即投稿」被 ${st.提交.挡住} 盖住`)
    if (!cover) bad.push('读不到封面背景 URL')
    if (oldcover && cover === oldcover) bad.push('封面还是旧 URL，换封面没生效')
    if (collection && !(await page.evaluate((c) => document.body.innerText.includes(c), collection))) bad.push(`页面上没有合集「${collection}」`)
    if (bad.length) throw new Error(`提交前核对不过：${bad.join('；')}`)

    const seen = []
    page.on('response', async (res) => {
      if (res.request().method() === 'GET') return
      const u = res.url()
      if (!/member\.bilibili\.com\/x\//.test(u)) return
      let j = null
      try { j = await res.json() } catch {}
      seen.push(`${res.status()} ${u.replace(/^https:\/\/[^/]+/, '').split('?')[0]} code=${j?.code ?? '?'} ${String(j?.message ?? j?.msg ?? '').slice(0, 70)}`)
    })
    let attempted = false
    let clickResolved = false
    try {
      attempted = true
      await page.getByText('立即投稿', { exact: true }).last().click({ timeout: 15000 })
      clickResolved = true
      console.log('  已点「立即投稿」，等结果……')
      for (let i = 0; i < 40; i++) {
        await page.waitForTimeout(3000)
        const u = page.url()
        const body = await page.evaluate(() => document.body.innerText.replace(/\s+/g, ' ').slice(0, 800))
        const ok = body.match(/.{0,30}(?:稿件投递成功|修改成功|提交成功|重新审核|审核中).{0,30}/)?.[0] ?? ''
        const err = [...new Set(body.match(/[^ ]{0,14}(?:失败|请检查|不能为空|超过|错误)[^ ]{0,20}/g) || [])].slice(0, 6)
        if (ok || err.length || u !== st.url) {
          console.log('  结果：', JSON.stringify({ url: u, 文案: ok, 报错: err }))
          break
        }
        if (i === 39) console.log('  2 分钟没有可判定的结果，URL 仍是：', u)
      }
      console.log('  非 GET 应答：', JSON.stringify(seen))
    } finally {
      await shot('replace')
      if (attempted) {
        const ev = { at: new Date().toISOString(), action: 'replace', platform: 'bilibili', gate: expect, oldId: bvid, newId: bvid, clicked: clickResolved, url: page.url(), response: seen, note: '编辑页换源提交（立即投稿），BV 不变' }
        appendFileSync(`D:/Users/mcu/.temp/repost/${day}/${EP}/events.jsonl`, JSON.stringify(ev) + '\n')
        for (const g of [gateA, gateB]) {
          try { unlinkSync(g); console.log(`  已消耗闸门 ${g}`) } catch (e) { console.log(`  ⚠ 闸门没删掉 ${g}：${String(e).slice(0, 80)}`) }
        }
      } else {
        console.log('  没有点提交，闸门原样保留')
      }
    }
  },
  async open() {
    page = withHooks(await ctx.newPage())
    await page.goto('https://member.bilibili.com/platform/upload/video/frame', { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(8000)
    // 给这个标签页盖章：浏览器是有人同时在用的，光按 URL 挑页会挑到上一条稿件的表单。
    await page.evaluate((ep) => { window.__biliEp = ep }, EP)
    const nav = await page.evaluate(async () => (await (await fetch('https://api.bilibili.com/x/web-interface/nav', { credentials: 'include' })).json()).data)
    console.log('登录=', nav?.isLogin, ' 昵称=', nav?.uname, ' mid=', nav?.mid)
    console.log(JSON.stringify(await snap(), null, 1))
    await shot('open')
  },
  // 只喂文件：稿件这时还不存在，关页就等于没投过。
  // 上一版按"可见的 .mp4 input"取第一个，setInputFiles 不报错但页面毫无反应——
  // 量到那两个 input 在 (200,60)，跟中央拖拽区不是一回事；真正的上传控件在 shadow root 里，
  // page.evaluate 的 querySelectorAll 穿不过去，所以"页面上可见的 mp4 input"这个判据本身就是错的。
  // 改成点「上传视频」并接住它真正唤起的 filechooser：这样"点的按钮"和"喂的 input"必然是一对。
  async feed() {
    if (!existsSync(F.video)) throw new Error(`片源不存在：${F.video}`)
    const all = page.locator('input[type=file]')
    const n = await all.count()
    for (let i = 0; i < n; i++) {
      const e = all.nth(i)
      console.log(`  mp4候选 #${i} 可见=${await e.isVisible().catch(() => '?')} accept="${await e.getAttribute('accept')}"`)
    }
    const prog = async () => page.evaluate(() => document.body.innerText.replace(/\s+/g, ' ')
      .match(/上传中[^ ]{0,12}|\d{1,3}%|转码中|上传失败|重新上传|解析中/g)?.join(' ') ?? '')
    const formReady = () => page.evaluate(() => [...document.querySelectorAll('input,textarea')]
      .some((e) => (e.offsetWidth || e.offsetHeight) && /标题|请输入.*标题|80/.test(String(e.placeholder || ''))))
    const watched = async (label, ms) => {
      for (let i = 0; i < ms / 2000; i++) {
        await page.waitForTimeout(2000)
        const s = await prog()
        if (s) { console.log(`  「${label}」后 ${(i * 2)}s 看到：${s}`); return true }
        if (await formReady()) { console.log(`  「${label}」后 ${(i * 2)}s 直接进了表单`); return true }
      }
      console.log(`  「${label}」后 ${ms / 1000}s 内页面没有任何上传迹象`)
      return false
    }
    // 先试隐藏那个 mp4 input：上传器通常把真控件藏起来、让按钮去 .click() 它。
    // 上一版挑了"可见"的那个，setInputFiles 不报错但页面毫无反应——不报错不等于喂对了。
    const hidden = page.locator('input[type=file][accept*=".mp4"]').first()
    await hidden.setInputFiles(F.video, { timeout: 30000 }).catch((e) => console.log('  隐藏 input 喂不进去：', String(e).slice(0, 70)))
    if (await watched('隐藏 mp4 input', 20000)) { console.log(JSON.stringify(await snap(), null, 1)); await shot('feed'); return }
    // 还不行就走 filechooser：点按钮并接住它真正唤起的对话框，"点的"和"喂的"必然成对。
    // catch 必须挂在 waitForEvent 当场——上一版挂在 click 之后，click 等可点的那几秒里
    // 8 秒超时先炸，未处理的 rejection 直接把进程带走了。
    const pick = async (label, locator) => {
      const hop = page.waitForEvent('filechooser', { timeout: 15000 }).catch(() => null)
      await locator.click({ timeout: 15000 }).catch((e) => console.log(`  「${label}」点不动：`, String(e).slice(0, 70)))
      const fc = await hop
      if (!fc) { console.log(`  「${label}」没唤起 filechooser`); return false }
      await fc.setFiles(F.video)
      console.log(`  「${label}」→ filechooser，已喂 ${F.video}`)
      return await watched(label, 20000)
    }
    let ok = await pick('上传视频按钮', page.getByText('上传视频', { exact: true }).first())
    if (!ok) ok = await pick('拖拽区', page.getByText('点击上传或将视频拖拽到此区域', { exact: false }).first())
    if (!ok) { console.log('三条路都没让页面开始上传，停手不猜'); await shot('feed-fail'); return }
    for (let i = 0; i < 200; i++) {
      await page.waitForTimeout(3000)
      const s = await page.evaluate(() => document.body.innerText.replace(/\s+/g, ' ').match(/上传中[^ ]{0,12}|\d{1,3}%|转码中|投稿完成|上传失败|重新上传/g)?.join(' ') ?? '')
      if (s) console.log(`  ${(i * 3)}s ${s}`)
      if (await formReady()) { console.log(`表单已出（第 ${i * 3}s）`); break }
    }
    console.log(JSON.stringify(await snap(), null, 1))
    await shot('feed')
  },
  async status() { console.log(JSON.stringify(await snap(), null, 1)); await shot('status') },
  // 38~49MB 要传几分钟，得等它到「上传完成」再填字——填早了会被上传器回调覆盖。
  // 只读正文文字、不截图：这页一重，截图就 20s 超时，别把等待卡在取证上。
  async wait() {
    for (let i = 0; i < 240; i++) {
      const s = await page.evaluate(() => {
        const t = document.body.innerText.replace(/\s+/g, ' ')
        return {
          done: /上传完成/.test(t) || (/100%/.test(t) && !/上传中/.test(t)),
          fail: /上传失败|重新上传/.test(t),
          up: t.match(/已经上传：[^ ]+\/[^ ]+|当前速度：[^ ]+|剩余时间：[^ ]+|\d{1,3}%|上传中|上传完成/g)?.join(' ') ?? '',
        }
      })
      if (s.done) { console.log(`  上传完成（约 ${i * 5}s）｜${s.up}`); return }
      if (s.fail) throw new Error(`上传失败：${s.up}`)
      if (i % 6 === 0) console.log(`  ${i * 5}s ${s.up}`)
      await page.waitForTimeout(5000)
    }
    throw new Error('等 20 分钟还没到「上传完成」，停手不猜')
  },
  // 表单控件的精确形状：简介到底是不是 textarea、标签 chip 怎么删、分区/声明是什么控件。
  // 不猜选择器——量出来再写 fill。
  async dump() {
    const d = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const T = (e) => (e.innerText || e.value || e.getAttribute('placeholder') || '').replace(/\s+/g, ' ').trim()
      const box = (e) => { const r = e.getBoundingClientRect(); return `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }
      const near = (label) => {
        const lab = [...document.querySelectorAll('*')].filter((e) => !e.children.length && vis(e) && T(e) === label)[0]
        if (!lab) return { label, found: false }
        const row = lab.closest('.upload-form-item, [class*=form-item], [class*=item]') ?? lab.parentElement?.parentElement
        return {
          label, found: true, 位置: box(lab),
          行文案: T(row ?? lab).slice(0, 120),
          行内控件: [...(row ?? lab).querySelectorAll('input,textarea,[contenteditable],[class*=tag],[class*=Tag],[class*=select],[class*=Select]')]
            .filter(vis).slice(0, 12).map((e) => `${e.tagName.toLowerCase()}[${String(e.className).split(' ')[0].slice(0, 22)}] ph="${e.placeholder || ''}" 值="${T(e).slice(0, 20)}" ${box(e)}`),
        }
      }
      return {
        字段: ['标题', '创作声明', '分区', '标签', '简介', '封面', '定时发布'].map(near),
        可编辑区: [...document.querySelectorAll('[contenteditable=true],textarea')].filter(vis)
          .map((e) => `${e.tagName.toLowerCase()} 值="${T(e).slice(0, 30)}" ${box(e)}`),
        全部按钮: [...document.querySelectorAll('button,[role=button]')].filter(vis).map((e) => `${T(e).slice(0, 14)} ${box(e)}`).slice(0, 30),
      }
    })
    console.log(JSON.stringify(d, null, 1))
    await shot('dump')
  },
  // 下拉是自定义控件，选项渲染在 body 末端的弹层里。先把「创作声明」「分区」的候选词
  // 和底部那几个勾选项原样抄下来，fill 才有得挑；只读，看完 Esc 收掉，不改任何值。
  async probe() {
    const out = {}
    // 「知道了」那条气泡压在声明/分区上面，点不动多半是它挡的。先收掉再量。
    await page.getByText('知道了', { exact: true }).first()
      .click({ timeout: 5000 }).then(() => console.log('  收掉了「知道了」'))
      .catch((e) => console.log('  没有「知道了」/点不掉：', String(e).slice(0, 50)))
    await page.waitForTimeout(800)
    // 不猜弹层的 class。点之前把 body 直属每一层的文案长度抄一份，点之后比长度：
    // 变长/新出现的那层就是刚开出来的选项浮层，把它的叶子文案全列出来。
    const lay = () => page.evaluate(() => [...document.querySelectorAll('body > *')]
      .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()))
    const grab = async (before) => {
      const now = await lay()
      let idx = -1, best = 0
      now.forEach((t, i) => { const d = t.length - (before[i]?.length ?? 0); if (d > best) { best = d; idx = i } })
      if (idx < 0) return { 变化层: '(body 直属各层文案都没变长——弹层可能挂在别的容器里)', 候选: [] }
      return await page.evaluate((n) => {
        const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
        const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
        const pop = [...document.querySelectorAll('body > *')][n]
        return {
          变化层: `${pop.tagName}.${String(pop.className).split(' ')[0]}`,
          全文: T(pop).slice(0, 600),
          候选: [...pop.querySelectorAll('*')].filter((e) => !e.children.length && vis(e) && T(e)).map(T).slice(0, 60),
        }
      }, idx)
    }
    const open = async (key, sel) => {
      const all = page.locator(sel)
      const n = await all.count()
      const target = all.first()
      await target.scrollIntoViewIfNeeded({ timeout: 8000 }).catch(() => {})
      await page.waitForTimeout(500)
      console.log(`  ${key}：${sel} 命中 ${n} 个，滚动后位置 ${JSON.stringify(await target.boundingBox().catch(() => null))}`)
      const before = await lay()
      await target.click({ timeout: 12000 }).catch((e) => console.log(`  ${key} 点不动：`, String(e).replace(/\n/g, ' ').slice(0, 400)))
      await page.waitForTimeout(1800)
      out[key] = await grab(before)
      // 点开了却比不出变化层：直接把整个 DOM 里"新出现的浮层"按类名抄出来，看它挂在哪。
      if (out[key].变化层?.startsWith?.('(') || out[key].变化层?.startsWith?.('DIV.app_wrap')) {
        out[key].浮层清单 = await page.evaluate(() => {
          const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
          const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
          return [...document.querySelectorAll('div,ul')]
            .filter((e) => vis(e) && /select|dropdown|popup|option|panel|cascader|tree|list/i.test(String(e.className)) && T(e))
            .map((e) => { const r = e.getBoundingClientRect()
              return `${e.tagName}.${String(e.className).split(' ')[0].slice(0, 40)} @${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)} :: ${T(e).slice(0, 300)}` })
            .slice(0, 25)
        })
      }
      await page.keyboard.press('Escape').catch(() => {})
      await page.waitForTimeout(600)
    }
    await open('分区', 'div.select-controller')
    await open('创作声明', 'input.bcc-select-input-inner')
    out.底部勾选 = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      return [...document.querySelectorAll('input[type=checkbox]')].filter(vis).map((e) => {
        const r = e.getBoundingClientRect()
        const row = e.closest('[class*=item],[class*=row],label') ?? e.parentElement?.parentElement
        return `${Math.round(r.y)}: ${T(row ?? e).slice(0, 80)}`
      })
    })
    console.log(JSON.stringify(out))
    await shot('probe')
  },
  // 分区点开的是几列？线上 c3 用的是 tid=231「计算机技术」（父 188 科技），
  // 网页表单到底给不给这一级，得看开出来的面板结构，不能拿"科技数码"就当答案。
  async tid() {
    const sel = 'p.select-item-cont'
    // Escape 关不掉这个自定义下拉——上一轮它一直张着，把分区的点击吞掉了。
    // 先把还开着的浮层逐个按回去：谁的列表可见，就再点它本体一次。
    const openOnes = () => page.evaluate(() => [...document.querySelectorAll('.bcc-select-list-wrap, [class*=select-list], [class*=dropdown]')]
      .filter((e) => e.offsetWidth || e.offsetHeight).length)
    for (let i = 0; i < 3; i++) {
      if (!(await openOnes())) break
      const which = await page.evaluate(() => {
        const vis = (e) => !!(e.offsetWidth || e.offsetHeight)
        const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
        const p = [...document.querySelectorAll('.bcc-select-list-wrap')].filter(vis)[0]
        return p ? T(p).slice(0, 40) : '?'
      })
      console.log(`  第 ${i} 次收浮层：还开着「${which}」`)
      await page.locator('.bcc-select-input-inner').first().click({ timeout: 5000 }).catch(() => {})
      await page.waitForTimeout(700)
    }
    console.log('  剩余可见浮层：', await openOnes())
    await page.locator(sel).first().scrollIntoViewIfNeeded({ timeout: 8000 }).catch(() => {})
    await page.locator(sel).first()
      .click({ timeout: 12000 }).catch((e) => console.log('  分区点不动：', String(e).replace(/\n/g, ' ').slice(0, 300)))
    await page.waitForTimeout(2000)
    const d = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      const box = (e) => { const r = e.getBoundingClientRect(); return `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }
      const panels = [...document.querySelectorAll('div,ul')].filter((e) => vis(e) &&
        /select|partition|category|cascade|dropdown/i.test(String(e.className)) && T(e).length > 8)
      const pick = (needle) => [...document.querySelectorAll('*')]
        .filter((e) => !e.children.length && vis(e) && T(e) === needle)
        .map((e) => { const chain = []; for (let p = e; p && p !== document.body; p = p.parentElement) chain.push(`${p.tagName}.${String(p.className).split(' ')[0]}`)
          return `${needle} @${box(e)} 层级 ${chain.slice(0, 5).join(' < ')}` })
      return {
        面板: panels.slice(-3).map((e) => `${e.tagName}.${String(e.className).split(' ')[0]} @${box(e)} :: ${T(e)}`.slice(0, 1200)),
        命中: ['科技', '计算机技术', '数码', '科技数码', '知识', '机械'].flatMap(pick),
      }
    })
    console.log(JSON.stringify(d))
    await shot('tid')
    await page.keyboard.press('Escape').catch(() => {})
  },
  // fill 之前把四个还不清楚的控件量干净：标签 chip 怎么删、简介的 Quill 怎么落字、
  // 封面点开后的本地上传入口、以及"加入合集"这个字段我们该不该动。
  async shape() {
    // 先点一个惰性 label 把还张着的自定义下拉收掉（Escape 对这个组件没用）
    await page.getByText('标题', { exact: true }).first().click({ timeout: 5000 }).catch(() => {})
    await page.waitForTimeout(600)
    const out = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      const box = (e) => { const r = e.getBoundingClientRect(); return `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }
      const chain = (e) => { const c = []; for (let p = e; p && p !== document.body; p = p.parentElement) c.push(`${p.tagName}.${String(p.className).split(' ')[0]}`); return c.slice(0, 4).join(' < ') }
      const wrp = [...document.querySelectorAll('.tag-pre-wrp')].filter(vis)[0]
      const ql = [...document.querySelectorAll('.ql-editor')].filter(vis)[0]
      const rest = {}
      for (const lab of ['加入合集', '商业推广', '定时发布', '封面']) {
        const n = [...document.querySelectorAll('*')].filter((e) => !e.children.length && vis(e) && T(e) === lab)[0]
        if (n) { const row = n.closest('[class*=form-item], [class*=upload-form-item]') ?? n.parentElement?.parentElement
          rest[lab] = { 位置: box(n), 行文案: T(row ?? n).slice(0, 200), 控件: [...(row ?? n).querySelectorAll('input,button,[class*=switch],[class*=checkbox],[class*=select]')].filter(vis).slice(0, 8).map((e) => `${e.tagName}.${String(e.className).split(' ')[0]} ${box(e)}`) } }
      }
      return {
        标签chip: wrp ? [...wrp.querySelectorAll('*')].filter((e) => vis(e)).slice(0, 20)
          .map((e) => `${e.tagName}.${String(e.className).split(' ').slice(0, 2).join('.')} 文本="${T(e).slice(0, 12)}" ${box(e)}`) : '(没找到 tag-pre-wrp)',
        简介: ql ? { 属性: [...ql.attributes].map((a) => `${a.name}=${a.value}`).join(' '), 内容HTML: ql.innerHTML.slice(0, 200), 层级: chain(ql) } : '(没找到 ql-editor)',
        其余: rest,
      }
    })
    console.log(JSON.stringify(out))
  },
  // 事实源只有 video/out/<ep>/bili-submit.yaml，脚本里一个字都不写。
  async want() {
    console.log(JSON.stringify({
      EP, title: cfg('title'), tid: cfg('tid'), copyright: cfg('copyright'),
      source: cfg('source'), tag: cfg('tag'), cover: F.cover, video: F.video,
      与episode_json的titles一致: (pub?.titles ?? []).includes(cfg('title')),
      desc行数: cfg('desc').split('\n').length, desc字数: cfg('desc').length,
      desc: cfg('desc'),
    }))
  },
  async fill() {
    const log = (...a) => console.log('  ', ...a)
    // 要填的标题必须是 episode.json 里 declared 的那几个之一：
    // yaml 和 episode.json 谁写错了，在这里就断掉，而不是发出去才发现。
    const title = cfg('title')
    if (!(pub?.titles ?? []).includes(title)) throw new Error(`标题不在 episode.json 的 titles 里：${title}`)
    // 自定义下拉 Escape 关不掉，点一个惰性 label 收场
    await page.getByText('标题', { exact: true }).first().click({ timeout: 4000 }).catch(() => {})
    await page.waitForTimeout(400)
    const ti = page.locator('input[placeholder="请输入稿件标题"]').first()
    await ti.fill('')
    await ti.fill(title)
    log(`标题 → ${await ti.inputValue()}（${(await ti.inputValue()).length} 字）`)
    // 创作声明：现值对就不动，不对才开下拉（见 setDecl 上面那段）
    await setDecl(log)
    await page.waitForTimeout(600)    // 这一格标着「分区」，实测它写进去的是 human_type2（科技数码=1012），不是 tid：
    // c2 点了它，线上 tid 仍是平台自己给的 201，而 human_type 发布后 API 改不回来。
    // 所以默认不碰它，tid 一律投稿后用 x/vu/web/edit 回传补（201→231 实测落地）。
    if (TID_NAME) {
      await page.locator('.select-controller').first().click({ timeout: 8000 })
      await page.waitForTimeout(1500)
      const it = page.locator('.drop-list-v2-item:visible', { hasText: TID_NAME })
      const m = await it.count()
      if (!m) throw new Error(`分区列表里没有「${TID_NAME}」，停手不猜`)
      await it.first().click({ timeout: 8000 })
      log(`分区那一格 → ${TID_NAME}（命中 ${m} 项）——注意它改的是 human_type 不是 tid`)
    } else log('分区那一格：不碰（它写 human_type，tid 投稿后走 API 补）')
    await page.waitForTimeout(600)
    // 标签归 tagsync 管（它敲完会读回比对），fill 不重复实现一遍。
    await page.waitForTimeout(400)
    // 简介：Quill 的 contenteditable，逐行 type + Enter（insertText 会把换行吃掉）
    const desc = cfg('desc').split('\n')
    await page.locator('.ql-editor').first().click({ timeout: 8000 })
    for (let i = 0; i < desc.length; i++) {
      if (desc[i]) await page.keyboard.type(desc[i], { delay: 0 })
      if (i < desc.length - 1) await page.keyboard.press('Enter')
    }
    log(`简介：敲了 ${desc.length} 行 / ${cfg('desc').length} 字，表单计数「${(await page.locator('.desc-text-wrp').first().innerText()).replace(/\s+/g, ' ').slice(0, 40)}」`)
    console.log(JSON.stringify(await snap()))
    await shot('fill')
  },
  // 简介超长被平台拒了（实测 2135 字 → /x/vu/web/add/v3 code=21010 描述信息不合法）之后用这个：
  // 视频这时已经上传完，重跑 fill 要连 46MB 一起重传。而 fill 是"点进编辑器直接逐行 type"，
  // 不清空——在填过的表单上再跑一次只会把新简介接在旧的后面变成 4117 字。
  // 所以这里显式擦一次，并且擦完必须量到"真的是空的"才往下敲。
  async redesc() {
    const log = (...a) => console.log('  ', ...a)
    const want = cfg('desc')
    if (want.length > 2000) throw new Error(`配置里的简介还是 ${want.length} 字，超过 2000，先去改 episode.json`)
    const emptied = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight)
      const ql = [...document.querySelectorAll('.ql-editor')].filter(vis)[0]
      if (!ql) return 'no-editor'
      ql.focus()
      const r = document.createRange()
      r.selectNodeContents(ql)
      const sel = window.getSelection()
      sel.removeAllRanges()
      sel.addRange(r)
      document.execCommand('delete')
      return JSON.stringify((ql.innerText || '').trim())
    })
    if (emptied !== '""') throw new Error(`擦完不是空的：${emptied.slice(0, 80)}，停手别往下敲`)
    log('清空确认：可见 .ql-editor 的 innerText 长度 0')
    await page.waitForTimeout(400)
    const lines = want.split('\n')
    for (let i = 0; i < lines.length; i++) {
      if (lines[i]) await page.keyboard.type(lines[i], { delay: 0 })
      if (i < lines.length - 1) await page.keyboard.press('Enter')
    }
    await page.waitForTimeout(800)
    const cnt = await page.locator('.desc-text-wrp').first().innerText().catch(() => '')
    log(`简介重敲：${lines.length} 行 / ${want.length} 字，表单计数「${cnt.replace(/\s+/g, ' ').slice(0, 40)}」`)
    await shot('redesc')
  },
  // 只改创作声明。fill() 会连标题简介一起重敲，为了换一格字去冒那个险不值。
  // 自定义下拉 Escape 关不掉，选完点一个惰性 label 收场。
  async decl() {
    // 逻辑和 fill 里那一格完全同一套，别在这儿再写一遍判据。
    const log = (...a) => console.log('  ', ...a)
    console.log('  改前：', JSON.stringify(await declNow()))
    await setDecl(log)
    console.log('  读回：', JSON.stringify(await declNow()))
    await shot('decl')
  },
  // 标签对齐：把 chip 集合改成配置里那组——多余的删掉（× 是 chip 里的 svg），
  // 缺的逐条真敲回车。B站会静默拒绝某些标签（实测「单片机」被吞，微控制器/MCU/单片机开发都收），
  // 所以敲完必须读回来对比，把没落地的报出来，不能假设配置里的都能上。
  async tagsync() {
    const want = cfg('tag').split(',').map((s) => s.trim()).filter(Boolean)
    const chips = page.locator('.tag-pre-wrp .label-item-v2-container')
    const readNow = () => page.evaluate(() => [...document.querySelectorAll('.tag-pre-wrp .label-item-v2-container')]
      .map((e) => (e.innerText || '').replace(/\s+/g, ' ').trim()))
    for (let i = 0; i < 20; i++) {
      const cur = await readNow()
      const junk = cur.findIndex((c) => !want.includes(c))
      if (junk < 0) break
      console.log(`  删多余标签「${cur[junk]}」`)
      await chips.nth(junk).locator('svg').click({ timeout: 5000 }).catch((e) => console.log('    删不动：', String(e).slice(0, 50)))
      await page.waitForTimeout(400)
    }
    const box = page.locator('input[placeholder="按回车键Enter创建标签"]').first()
    for (const t of want) {
      if ((await readNow()).includes(t)) continue
      await box.click({ timeout: 8000 })
      await page.waitForTimeout(300)
      await box.pressSequentially(t, { delay: 90 })
      await page.waitForTimeout(400)
      await page.keyboard.press('Enter')
      await page.waitForTimeout(900)
      console.log(`  敲「${t}」→ ${JSON.stringify(await readNow())}`)
    }
    const got = await readNow()
    console.log(JSON.stringify({ 配置: want, 页面: got, 没落地的: want.filter((t) => !got.includes(t)) }))
  },
  // 读回每个控件的显示，填对没填对以这里为准。
  // 简介到底落成了什么：逐字符比对页面 innerText 与配置里的 desc，
  // 空白差异单独报，别把"看起来填上了"当成"填对了"。
  async descdiff() {
    const txt = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight)
      const ql = [...document.querySelectorAll('.ql-editor')].filter(vis)[0]
      return ql ? (ql.innerText || '') : ''
    })
    const want = cfg('desc')
    const n = (s) => s.replace(/\r/g, '').split('\n').map((l) => l.trim()).filter(Boolean)
    const a = n(want), b = n(txt)
    const same = a.length === b.length && a.every((l, i) => l === b[i])
    const blocks = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight)
      const ql = [...document.querySelectorAll('.ql-editor')].filter(vis)[0]
      return { 块数: ql ? ql.children.length : -1, 空块: ql ? [...ql.children].filter((p) => !(p.textContent || '').trim()).length : -1,
        前6块: ql ? [...ql.children].slice(0, 6).map((p) => `${p.tagName}:${(p.textContent || '').slice(0, 24)}`) : [],
        HTML片段: ql ? ql.innerHTML.slice(0, 300) : '' }
    })
    console.log(JSON.stringify({ 配置字数: want.length, 页面字数: txt.length, ...blocks,
      非空行数: [a.length, b.length],
      逐行一致: same,
      首个不一致行: same ? null : (() => { const i = a.findIndex((l, k) => l !== b[k]); return { 行: i, 配置: a[i], 页面: b[i] } })(),
    }))
  },
  async check() {
    const r = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      const val = (ph) => [...document.querySelectorAll('input')].filter((e) => e.placeholder === ph)[0]?.value
      const ql = [...document.querySelectorAll('.ql-editor')].filter(vis)[0]
      const txt = ql ? (ql.innerText || '') : ''
      const chipRow = [...document.querySelectorAll('.tag-pre-wrp')].filter(vis)[0]
      const decl = [...document.querySelectorAll('.bcc-select-input-inner')].filter(vis)[0]
      return {
        标题: val('请输入稿件标题'),
        创作声明: [...document.querySelectorAll('input')].filter((e) => e.placeholder === '请选择符合您视频内容的创作声明')[0]?.value ?? '(没找到)',
        分区: T([...document.querySelectorAll('.select-controller')].filter(vis)[0] || {}),
        标签: chipRow ? [...chipRow.querySelectorAll('.label-item-v2-container')].map((e) => T(e)) : [],
        标签剩余名额: T([...document.querySelectorAll('p')].filter((e) => /还可以添加/.test(T(e)))[0] || {}),
        简介字数: txt.length,
        简介计数: T([...document.querySelectorAll('*')].filter((e) => !e.children.length && /^\d+\s*\/\s*2000$/.test(T(e)))[0] || {}),
        简介首40: txt.slice(0, 40).replace(/\n/g, '⏎'),
        简介末40: txt.slice(-40).replace(/\n/g, '⏎'),
        简介时间轴可点数: [...document.querySelectorAll('.ql-editor a, .ql-editor [class*=time], .ql-editor span[class*=link]')].length,
        封面按钮: T([...document.querySelectorAll('*')].filter((e) => !e.children.length && /添加封面|更换封面|重新选择/.test(T(e)) && vis(e))[0] || {}),
        封面图: [...document.querySelectorAll('img')].filter((e) => vis(e) && e.getBoundingClientRect().width > 100)
          .map((e) => `${Math.round(e.getBoundingClientRect().width)}×${Math.round(e.getBoundingClientRect().height)} ${String(e.src).replace(/^https?:\/\/[^/]+\//, '').slice(0, 60)}`)[0] || '(没有大图为封面)',
        // 设好封面后那一格常常不是 <img>，而是 div 的 background-image——只看 img 会把"已经换上图"
        // 量成"没有封面"（c5 的 check 就是这么报空的）。两样都读，别只信一个。
        封面背景: [...new Set([...document.querySelectorAll('[class*=cover],[class*=thumbnail],[class*=preview]')]
          .filter(vis).flatMap((e) => [e, ...e.children])
          .map((e) => (getComputedStyle(e).backgroundImage || '').match(/url\("?(blob:[^")]+|https?:[^")]+)"?\)/)?.[1])
          .filter(Boolean))].slice(0, 6),
        发布按钮可用: !![...document.querySelectorAll('*')].filter((e) => T(e) === '发布视频' && vis(e))[0],
      }
    })
    console.log(JSON.stringify(r))
    await shot('check')
  },
  // 封面：先只点开面板把里面的控件抄下来（--commit 才真的传图并落定）。
  // 传完通常有裁切框，得点确定/保存，否则等于没换。
  async cover() {
    const commit = process.argv.includes('--commit')
    await page.getByText('添加封面', { exact: false }).first()
      .click({ timeout: 10000 }).catch((e) => console.log('  「添加封面」点不动：', String(e).replace(/\n/g, ' ').slice(0, 120)))
    await page.waitForTimeout(2000)
    const panel = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const T = (e) => (e.innerText || e.getAttribute('placeholder') || '').replace(/\s+/g, ' ').trim()
      const box = (e) => { const r = e.getBoundingClientRect(); return `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }
      return {
        文件框: [...document.querySelectorAll('input[type=file]')].map((e, i) => `#${i} accept="${e.accept}" 可见=${vis(e)} ${box(e)}`),
        按钮: [...document.querySelectorAll('button,[role=button],.bcc-button,[class*=btn]')].filter((e) => vis(e) && T(e)).map((e) => `${T(e).slice(0, 16)} ${box(e)}`).slice(0, 25),
        文案: T(document.body).replace(/\s+/g, ' ').slice(0, 300),
      }
    })
    console.log('  面板：', JSON.stringify(panel))
    if (!commit) { console.log('  未加 --commit，只量不传'); return }
    const img = page.locator('input[type=file][accept*="png"], input[type=file][accept*="image"], input[type=file][accept*="jpg"]').first()
    if (!(await img.count())) { console.log('  面板里没有图片 input，停手'); await shot('cover-noinput'); return }
    await img.setInputFiles(F.cover, { timeout: 30000 })
    console.log(`  已喂 ${F.cover}`)
    await page.waitForTimeout(4000)
    // 4:3 用的是我们传的图，16:9 默认还是随机视频帧——「双比例同步改动」勾上才会两张都用它。
    // 实测这个开关在 DIV.operation 里，文案节点本身可点。
    const previews = () => page.evaluate(() => [...document.querySelectorAll('img')]
      .filter((e) => (e.offsetWidth || e.offsetHeight) && e.getBoundingClientRect().width > 60)
      .map((e) => `${Math.round(e.getBoundingClientRect().width)}×${Math.round(e.getBoundingClientRect().height)}@${Math.round(e.getBoundingClientRect().y)} ${String(e.src).slice(0, 46)}`))
    console.log('  勾选前预览图：', JSON.stringify(await previews()))
    await page.getByText('双比例同步改动', { exact: true }).first()
      .click({ timeout: 8000 }).catch((e) => console.log('  同步开关点不动：', String(e).slice(0, 80)))
    await page.waitForTimeout(2500)
    console.log('  勾选后预览图：', JSON.stringify(await previews()))
    await shot('cover-sync')
    const done = page.getByText('完成', { exact: true }).last()
    await done.click({ timeout: 10000 }).catch((e) => console.log('  「完成」点不动：', String(e).slice(0, 100)))
    await page.waitForTimeout(3000)
    console.log(JSON.stringify(await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight)
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      return {
        封面按钮: T([...document.querySelectorAll('*')].filter((e) => !e.children.length && /添加封面|更换封面|重新选择|修改封面/.test(T(e)) && vis(e))[0] || {}),
        大图: [...document.querySelectorAll('img')].filter((e) => vis(e) && e.getBoundingClientRect().width > 100)
          .map((e) => `${Math.round(e.getBoundingClientRect().width)}×${Math.round(e.getBoundingClientRect().height)} ${String(e.src).replace(/^https?:\/\/[^/]+\//, '').slice(0, 70)}`)[0] || '(无)',
      }
    })))
    await shot('cover')
  },
  // 「添加封面」这个文案只在没选封面时出现；选完之后那块换成封面预览，
  // 用文案判断封面到底设没设会误判。这里直接量封面区块本身：滚到「封面」标签，
  // 把它右边那一行里的 img 全抄出来（src + 尺寸），再截那张图给人看。
  async coverstate() {
    await page.evaluate(() => {
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      // 页面上「封面」这个纯文本节点不止一个（另一份在收起的表单里，零尺寸）。
      // 滚到第一个会把隐藏那个也算进来，接着按可见筛就找不到——两处必须用同一套判据。
      const lab = [...document.querySelectorAll('*')].filter((e) => !e.children.length && T(e) === '封面' && vis(e))[0]
      if (lab) lab.scrollIntoView({ block: 'center' })
    })
    await page.waitForTimeout(1200)
    const r = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      const lab = [...document.querySelectorAll('*')].filter((e) => !e.children.length && T(e) === '封面' && vis(e))[0]
      if (!lab) return { 错误: '页面上找不到「封面」标签' }
      const lr = lab.getBoundingClientRect()
      const near = (e) => { const q = e.getBoundingClientRect(); return Math.abs(q.y - lr.y) < 220 && q.x > lr.x - 20 }
      return {
        标签位置: `${Math.round(lr.x)},${Math.round(lr.y)}`,
        本行文案: T(lab.parentElement?.parentElement ?? lab.parentElement ?? lab).slice(0, 200),
        图: [...document.querySelectorAll('img')].filter((e) => vis(e) && near(e))
          .map((e) => { const q = e.getBoundingClientRect()
            return `${Math.round(q.width)}×${Math.round(q.height)}@${Math.round(q.x)},${Math.round(q.y)} 选中=${/active|selected|current/i.test(String(e.className)) || /active|selected|current/i.test(String(e.parentElement?.className))} ${String(e.src).replace(/^https?:\/\/[^/]+\//, '').slice(0, 60)}` }),
        按钮: [...document.querySelectorAll('button,[role=button],.bcc-button,[class*=btn]')].filter((e) => vis(e) && near(e) && T(e))
          .map((e) => T(e).slice(0, 14)),
      }
    })
    console.log(JSON.stringify(r, null, 1))
    await shot('coverstate')
  },
  // 给一个词，把页面里所有含它的可见节点原样列出来（tag/class/rect/父层），
  // 免得我在"到底哪个才是可点的那个"上瞎试。
  async find() {
    const needle = arg('--has') ?? ''
    if (!needle) throw new Error('没给 --has')
    // 封面弹窗比视口高，底部按钮根本没进可视区——先把所有能滚的容器滚到底再找。
    await page.evaluate(() => [...document.querySelectorAll('*')]
      .filter((e) => e.scrollHeight > e.clientHeight + 20 && (e.offsetWidth || e.offsetHeight))
      .forEach((e) => { e.scrollTop = e.scrollHeight }))
    await page.waitForTimeout(800)
    const r = await page.evaluate((nd) => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const T = (e) => (e.innerText || e.value || '').replace(/\s+/g, ' ').trim()
      const box = (e) => { const q = e.getBoundingClientRect(); return `${Math.round(q.x)},${Math.round(q.y)} ${Math.round(q.width)}×${Math.round(q.height)}` }
      const chain = (e) => { const c = []; for (let p = e; p && p !== document.body; p = p.parentElement) c.push(`${p.tagName}.${String(p.className).split(' ')[0]}`); return c.slice(0, 3).join(' < ') }
      const hits = [...document.querySelectorAll('*')].filter((e) => vis(e) && nd.split(',').includes(T(e)))
      return hits.filter((e) => !hits.some((o) => o !== e && o.contains(e)))
        .map((e) => `${e.tagName} ${box(e)} 「${T(e)}」 层级 ${chain(e)}`)
    }, needle)
    console.log(JSON.stringify(r, null, 1))
  },
  // 「更多设置」里才是原创声明/弹幕这些。它被一个 v-popover 新手提示压着点不动，
  // 所以先点空白处把浮层赶走，再展开，把里面的控件原文抄出来。
  async more() {
    for (let i = 0; i < 3; i++) {
      const n = await page.evaluate(() => [...document.querySelectorAll('.v-popover')].filter((e) => e.offsetWidth || e.offsetHeight).length)
      if (!n) break
      console.log(`  赶走 ${n} 个 v-popover`)
      await page.mouse.move(900, 200).catch(() => {})
      await page.waitForTimeout(700)
    }
    // 这一行压在底部吸附条（存草稿/立即投稿）下面，真实点击永远被吸附条吃掉。
    // 滚到底再用 JS 派发 click：绕开命中测试，但点的还是那个节点。
    const cand = await page.evaluate(() => {
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      return [...document.querySelectorAll('*')].filter((e) => T(e).startsWith('更多设置') && T(e).length < 40)
        .map((e) => `${e.tagName}.${String(e.className).split(' ')[0]} 子节点${e.children.length} 文本="${T(e)}" ${JSON.stringify(e.getBoundingClientRect())}`)
    })
    console.log('  「更多设置」候选节点：\n   ', cand.join('\n    '))
    await page.evaluate(() => {
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      const n = [...document.querySelectorAll('div.title, span.label')].filter((e) => T(e).startsWith('更多设置'))[0]
      if (n) n.scrollIntoView({ block: 'center' })
      return !!n
    })
    await page.waitForTimeout(1200)
    const clicked = await page.evaluate(() => {
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      // 「添加水印」这个节点在收起态也存在于 DOM 里（offsetWidth=0），
      // 只看文本会误判成"已展开"，于是永远不去点它——必须同时要求可见。
      if ([...document.querySelectorAll('*')].some((e) => !e.children.length && T(e) === '添加水印' && (e.offsetWidth || e.offsetHeight))) return '已是展开态，不再点'
      const n = [...document.querySelectorAll('div.title, span.label')].filter((e) => T(e).startsWith('更多设置'))[0]
      if (!n) return 'no-node'
      const fire = (el) => el.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }))
      fire(n)
      if (n.firstElementChild) fire(n.firstElementChild)
      return 'clicked'
    })
    console.log(`  更多设置：${clicked}`)
    await page.waitForTimeout(2500)
    const t = await page.evaluate(() => {
      const s = document.body.innerText.replace(/[ \t]+/g, ' ')
      const i = s.indexOf('更多设置')
      return s.slice(i, i + 2200)
    })
    console.log(t)
    // 展开后这些开关的现值才是关键：可见范围必须是"公开可见"，水印/关弹幕/关评论必须是我们想要的那档。
    // 判据和 setmore/publish 共用同一套（见 PICK），不然这里"没找到"、那边却点得动。
    console.log(JSON.stringify(await readTicks(['添加水印', '可见范围', '必火推广', '关闭弹幕', '关闭评论', '开启精选评论', '在个人空间-投稿中隐藏', '杜比音效', 'Hi-Res无损音质', '章节管理']), null, 1))
    await shot('more')
  },
  // 网页表单的默认值和 biliup 的不一样：实测「添加水印」默认勾着，而 API 通道发的 17 条都没有水印。
  // 只认 input.checked / class 里的真值，不用"文本看起来开着"下结论。
  async setmore() {
    // 收起态量不到，先展开（more() 自己会判断"已是展开态，不再点"）。
    await V.more().catch((e) => console.log('  展开更多设置失败：', String(e).replace(/\n/g, ' ').slice(0, 120)))
    console.log('  改前：', JSON.stringify(await readTicks(TICKLABS)))
    // 网页通道实测：添加水印、杜比音效、Hi-Res无损音质 默认是勾上的，而 API 通道发出去的
    // 17 条三项都是 0。这三项发布后 API 改不动（发 code=0 但值不变），只能投稿前点掉。
    console.log('  取消勾选：', JSON.stringify(await uncheckTicks(['添加水印', '杜比音效', 'Hi-Res无损音质'])))
    await page.waitForTimeout(1200)
    console.log('  改后：', JSON.stringify(await readTicks(TICKLABS)))
    await shot('setmore')
  },
  // 编辑接口里"创作声明/分区/版权"这些字段到底叫什么，我不猜。
  // 做法：在编辑页改一格，然后拦下提交请求读它的 body——route 里 abort，一发都不真发到线上。
  // 凭证脱敏：body 里若混进 cookie 样式字段，只打印键名和值类型，不打印值。
  async sniff() {
    const hits = []
    await ctx.route('**/bilibili.com/x/**', async (route) => {
      const rq = route.request()
      const pd = rq.postData()
      // 任何非 GET 一律拦下不发——这一趟只许读字段名，不许碰线上。
      if (pd && rq.method() !== 'GET') {
        let parsed = null
        try { parsed = JSON.parse(pd) } catch { parsed = Object.fromEntries(new URLSearchParams(pd)) }
        hits.push({ url: rq.url().replace(/^https:\/\//, '').split('?')[0], method: rq.method(), keys: Object.keys(parsed), sample: parsed })
        console.log('  拦下（未发出）：', rq.method(), rq.url().split('?')[0])
        console.log('  字段：', Object.keys(parsed).join(' '))
        for (const [k, v] of Object.entries(parsed)) {
          const s = typeof v === 'object' ? JSON.stringify(v) : String(v)
          if (/SESSDATA|bili_jct|access_token|refresh_token|cookie/i.test(k + s)) { console.log(`   ${k} = <含疑似凭证，值不打印>`); continue }
          console.log(`   ${k} = ${s.length > 90 ? `<${s.length}字>` : s}`)
        }
        await route.abort()
        return
      }
      await route.continue()
    })
    if (DECL) {
      const box = page.locator('input[placeholder="请选择符合您视频内容的创作声明"]').first()
      if (!(await box.count())) throw new Error('找不到创作声明那一格')
      console.log('  声明现值：', JSON.stringify(await box.inputValue()))
      await box.evaluate((e) => e.scrollIntoView({ block: 'center' }))
      await page.waitForTimeout(500)
      await box.click({ timeout: 8000 })
      await page.waitForTimeout(1500)
      const li = page.locator('.bcc-select-option-list li:visible', { hasText: DECL })
      if (!(await li.count())) {
        console.log('  下拉可见项：', JSON.stringify(await page.locator('.bcc-select-option-list li:visible').allInnerTexts()))
        throw new Error(`下拉里没有「${DECL}」`)
      }
      await li.first().click({ timeout: 8000 })
      await page.waitForTimeout(900)
      console.log('  声明改成：', JSON.stringify(await box.inputValue()))
    }
    const sub = page.locator('text=/^(立即投稿|投稿|提交)$/').last()
    console.log('  提交按钮：', JSON.stringify(await sub.innerText().catch((e) => String(e).slice(0, 60))))
    await sub.click({ timeout: 10000 }).catch((e) => console.log('  点提交失败：', String(e).replace(/\n/g, ' ').slice(0, 200)))
    await page.waitForTimeout(6000)
    await ctx.unroute('**/bilibili.com/x/**')
    console.log(JSON.stringify({ 拦到: hits.map((h) => ({ url: h.url, method: h.method, keys: h.keys })) }, null, 1))
    await shot('sniff')
  },
  // 唯一不可逆的一步。闸门文件只能由对话里用户点头后我来创建，脚本自己不生成、不绕过。
  // 判重：页面已经离开投稿表单（URL 里带 aid/bvid 或到了成功页）就报现状，绝不第二次点「立即投稿」。
  async publish() {
    const gate = `${RUN}/I_HAVE_USER_OK=${EP}`
    if (!existsSync(gate)) throw new Error(`没有闸门文件 ${gate} —— 用户对 ${EP} 这条稿件点头之前不投稿`)
    console.log(`  闸门：${gate} 存在，修改时间 ${readFileSync(gate, 'utf8').trim() || '(空)'}`)
    // 投稿后再改就晚了，实测这三类字段发布后 API 全改不动（回 code=0 但值不变）：
    // 创作声明、杜比音效、Hi-Res无损音质。所以点「立即投稿」之前必须逐条验一遍，不符就停手。
    if (!DECL) throw new Error('没给 --decl：创作声明发布后锁死（编辑页那一格是 disabled），不能留空赌默认值')
    // 水印/杜比/Hi-Res 都在「更多设置」里，收着就量不到——先展开，量不到值宁可停手也不放过。
    await V.more().catch((e) => console.log('  展开更多设置失败：', String(e).replace(/\n/g, ' ').slice(0, 120)))
    // 投稿前先看页面还在不在表单上：c2/c4 都是人在浏览器里按的「立即投稿」，
    // 这时页面已经换成「稿件投递成功」，那一格创作声明根本不存在——
    // 不先判这一条，preflight 会报成"核对不过"，看着像字段错了，其实是这条已经发过了。
    const onDone = await page.evaluate(() => /稿件投递成功/.test(document.body.innerText))
    if (onDone) { console.log('  页面已是「稿件投递成功」——这一条早发出去了，不重复投稿。'); await shot('publish-already'); return }
    const tickBox = await readTicks(['添加水印', '杜比音效', 'Hi-Res无损音质'])
    const pre = await page.evaluate(() => {
      const inp = [...document.querySelectorAll('input')].filter((e) => e.placeholder === '请选择符合您视频内容的创作声明')[0]
      return { 声明: inp ? inp.value : '(找不到那一格)' }
    })
    const isOff = (v) => v && v.控件 && v.控件.length > 0 && v.控件.every((s) => s.endsWith(':关'))
    console.log('  投稿前锁定项：', JSON.stringify({ ...pre, 水印: tickBox['添加水印'], 杜比: tickBox['杜比音效'], HiRes: tickBox['Hi-Res无损音质'] }))
    const bad = []
    if (pre.声明 !== DECL) bad.push(`创作声明是「${pre.声明}」不是「${DECL}」`)
    for (const [k, lab] of [['水印', '添加水印'], ['杜比', '杜比音效'], ['HiRes', 'Hi-Res无损音质']]) {
      if (!isOff(tickBox[lab])) bad.push(`${lab}没读到"关"：${JSON.stringify(tickBox[lab])}`)
    }
    if (bad.length) throw new Error(`投稿前核对不过（这三项发完就改不了）：${bad.join('；')}`)
    const now = page.url()
    if (!/\/upload\/video\/frame/.test(now)) {
      console.log('  页面已离开投稿表单，不重复投稿。当前 URL：', now)
      await shot('publish-already')
      return
    }
    const btn = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      const n = [...document.querySelectorAll('*')].filter((e) => !e.children.length && T(e) === '立即投稿' && vis(e))[0]
      if (!n) return null
      const r = n.getBoundingClientRect()
      return { 层级: (() => { const c = []; for (let p = n; p && p !== document.body; p = p.parentElement) c.push(`${p.tagName}.${String(p.className).split(' ')[0]}`); return c.slice(0, 3).join(' < ') })(), 位置: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`, 灰: /disabled/i.test(String(n.className)) || n.closest('[class*=disabled]') !== null }
    })
    if (!btn) throw new Error('页面上找不到「立即投稿」，停手不瞎点')
    console.log('  按钮：', JSON.stringify(btn))
    if (btn.灰) throw new Error('「立即投稿」是禁用态——表单没填满，先回去查 check')
    await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight)
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      const n = [...document.querySelectorAll('*')].filter((e) => !e.children.length && T(e) === '立即投稿' && vis(e))[0]
      n.scrollIntoView({ block: 'center' })
    })
    await page.waitForTimeout(800)
    // 点下去必须知道服务器到底答了什么：p4 那次点了、页面不动、也没拿到 BV，
    // 光看 URL 和正文分不出"前端自己拦下没发请求"还是"请求发了被平台拒"。
    // 只记状态码和 code/message，正文一个字都不落盘。
    const seen = []
    page.on('response', async (res) => {
      const rq = res.request()
      if (rq.method() === 'GET') return
      const u = res.url()
      if (!/member\.bilibili\.com\/x\//.test(u)) return
      let j = null
      try { j = await res.json() } catch {}
      seen.push(`${res.status()} ${u.replace(/^https:\/\/[^/]+/, '').split('?')[0]} code=${j?.code ?? '?'} ${String(j?.message ?? j?.msg ?? '').slice(0, 70)}`)
    })
    // s2-rcc 撞的坑：这一句 click 一路重试到超时，Playwright 报的是
    // 「div.cover-editor-button.cover-editor-content-right-bottom ... intercepts pointer events」。
    // 它宁可什么都不点，也不会替我们点到那个挡在前面的元素——所以遮挡必须自己看清再动手。
    // 这里按按钮中心做一次命中测试；挡着的是封面编辑器就试着收掉它，收不掉就停手，
    // 绝不 force click（force 只是跳过检查，事件照样落在挡住的那个元素上）。
    const hit = () => page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      const n = [...document.querySelectorAll('*')].filter((e) => !e.children.length && T(e) === '立即投稿' && vis(e))[0]
      if (!n) return { 找不到: true, 挡住: '' }
      const r = n.getBoundingClientRect()
      const top = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2)
      const covered = !!top && top !== n && !top.contains(n) && !n.contains(top)
      return {
        挡住: covered ? `${top.tagName}.${String(top.className).slice(0, 60)} 文案="${T(top).slice(0, 20)}"` : '',
        按钮: `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}`,
      }
    })
    let h = await hit()
    for (let i = 0; i < 8 && h.挡住; i++) {
      console.log(`  命中测试：「立即投稿」被 ${h.挡住} 盖住（按钮在 ${h.按钮}），第 ${i + 1} 次试着收掉封面编辑器`)
      const did = await page.evaluate(() => {
        const vis = (e) => !!(e.offsetWidth || e.offsetHeight)
        const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
        const box = [...document.querySelectorAll('[class*=cover-editor]')].filter(vis)[0]
        if (!box) return '没有可见的 cover-editor 容器'
        const b = [...box.querySelectorAll('button,span,div,a')]
          .filter((e) => !e.children.length && vis(e) && ['取消', '关闭', '完成', '确定', '保存'].includes(T(e)))
        if (!b.length) return '容器里没有收场按钮：' + [...box.querySelectorAll('button')].filter(vis).map((e) => T(e) || String(e.className).slice(0, 24)).slice(0, 6).join(' / ')
        b[0].dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }))
        return `点了「${T(b[0])}」`
      })
      console.log('  收场动作：', did)
      await page.waitForTimeout(1500)
      h = await hit()
    }
    if (h.挡住) {
      await shot('publish-blocked')
      throw new Error(`「立即投稿」仍被 ${h.挡住} 盖住，停手不硬点。截图：${RUN}/${EP}-publish-blocked.png`)
    }
    console.log('  命中测试：「立即投稿」中心点顶层就是它自己，可以点')
    await page.getByText('立即投稿', { exact: true }).last().click({ timeout: 15000 })
    console.log('  已点「立即投稿」，等结果……')
    for (let i = 0; i < 40; i++) {
      await page.waitForTimeout(3000)
      const u = page.url()
      const id = await page.evaluate(() => (document.body.innerText.match(/BV[0-9A-Za-z]{10}/) || [])[0] ?? '')
      if (/publish|success|aid=|bvid=/.test(u) || id) { console.log('  结果：', JSON.stringify({ url: u, bvid: id })); break }
      const err = await page.evaluate(() => {
        const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
        const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
        return [...document.querySelectorAll('*')].filter((e) => !e.children.length && vis(e) && /投稿失败|请检查|不能为空|超过|重新|失败/.test(T(e)) && T(e).length < 80).map(T).slice(0, 8)
      })
      if (err.length) { console.log('  报错文案：', JSON.stringify(err)); break }
      if (i === 39) console.log('  2 分钟没有可判定的结果，URL 仍是：', u)
    }
    console.log('  点下去之后的非 GET 应答：', JSON.stringify(seen))
    await shot('publish')
    let bvid = await page.evaluate(() => (document.body.innerText.match(/BV[0-9A-Za-z]{10}/) || [])[0] ?? '')
    if (!bvid) {
      // 投稿成功页不一定把 BV 号写在正文里。稿件管理按投稿时间倒序，第一条就是刚发的那条——
      // 但只认标题对得上的，对不上就当没拿到，绝不把别人的稿件号记到我们账上。
      const want = cfg('title')
      const mgr = await ctx.newPage()
      await mgr.goto('https://member.bilibili.com/platform/upload-manager/article', { waitUntil: 'domcontentloaded', timeout: 60000 })
      for (let i = 0; i < 20 && !bvid; i++) {
        await mgr.waitForTimeout(3000)
        bvid = await mgr.evaluate((t) => {
          const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
          const hit = [...document.querySelectorAll('a[href*="/video/BV"]')].find((e) => T(e) === t)
          return hit ? (hit.href.match(/BV[0-9A-Za-z]{10}/) || [])[0] ?? '' : ''
        }, want).catch(() => '')
      }
      await mgr.close().catch(() => {})
    }
    const fin = { ep: EP, at: new Date().toISOString(), bvid, url: page.url(), by: '脚本 publish 步点的「立即投稿」（闸门文件 I_HAVE_USER_OK 来自对话授权）' }
    appendFileSync(`${RUN}/published.jsonl`, JSON.stringify(fin) + '\n')
    console.log('  记账：', JSON.stringify(fin))
    // 单独落一个 .bvid：批量脚本接着拿它去跑 repair，不用再从日志里 grep——
    // 投稿成功页正文里不一定有 BV 号，只有这条账是最可靠的来源。
    if (bvid) writeFileSync(`${RUN}/${EP}.bvid`, `${bvid}\n`)
    if (!bvid) console.log('  ⚠ 没拿到 BV 号——投稿可能没成功，别接着跑下一条')
  },
}
if (!step || !V[step]) throw new Error(`未知步骤 "${step}"，可选：${Object.keys(V).join(' / ')}`)
await V[step]()
// 这里原来跟的是 browser.close()：CDP 连接上的 close 会把常驻浏览器连同三个平台的登录一起带走。
// 本进程退出 socket 就断了，浏览器和页面状态得留着——走通走错都一样。
process.exit(0)
