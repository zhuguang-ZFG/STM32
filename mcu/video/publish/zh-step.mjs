// 知乎视频投稿：连 9223 那个常驻浏览器，按名字执行一步，打印这一步看到了什么。
// 每步只做一件可逆的事；唯一不可逆的 publish 要等闸门文件 .temp/zh-run/I_HAVE_USER_OK=<ep> 出现才动，
// 那个文件只能来自对话里的点头，脚本不自己造。
// 事实源：video/episodes/<ep>/episode.json 的 publish.zhihu 与 video/out/<ep>/，脚本里不写任何一集的字。
//
// 入口是实测出来的，不是猜的：/creator 的「发视频」开新标签 → www.zhihu.com/upload-video。
// （曾按 www.zhihu.com/bill 试过，那是软 404：知乎 404 页也回 HTTP 200，"没跳转"当不了"入口存在"。）
import { chromium } from 'playwright'
import { readFileSync, existsSync, mkdirSync, appendFileSync } from 'node:fs'

const RUN = 'D:/Users/mcu/.temp/zh-run'
mkdirSync(RUN, { recursive: true })
const step = process.argv[2]
function arg(name) { const i = process.argv.findIndex((a) => a === name || a.startsWith(`${name}=`)); if (i < 0) return null; const a = process.argv[i]; return a.includes('=') ? a.slice(a.indexOf('=') + 1) || null : process.argv[i + 1] ?? null }
// 缺 --ep 绝不回落到某个默认集：上一版 ?? 'c2-pointer' 会在手打错参数时拿着 c2 的 episode.json 去填当前稿件。
const EP = arg('--ep')
if (!EP) throw new Error('缺 --ep <episode-id>（--ep x 和 --ep=x 都认）——不猜这是哪一集')
const TI = Number(arg('--title') ?? 0)

const ep = JSON.parse(readFileSync(`D:/Users/mcu/video/episodes/${EP}/episode.json`, 'utf8'))
const pub = ep.publish?.zhihu
// 只读步骤（status/popup）不该因为这一集还没写 zhihu 文案就跑不动，所以把"必须有"推迟到真要填的步子。
const needPub = () => { if (!pub) throw new Error(`episode.json 里没有 publish.zhihu：${EP}`); return pub }
const F = {
  video: `D:/Users/mcu/video/out/${EP}/bilibili.mp4`,
  // 16:9 那份（COVER_SIZES.zhihu）。拿 bilibili-cover.png 去喂会被面板在底部切掉一条证据徽章。
  cover: `D:/Users/mcu/video/out/${EP}/zhihu-cover.png`,
}
// 知乎的横版片源就是 bilibili.mp4（1920×1080 以内，站内上限 1080P / 4h / 20GB）。
if (arg('--video')) F.video = arg('--video')
if (arg('--cover')) F.cover = arg('--cover')

const browser = await chromium.connectOverCDP('http://127.0.0.1:9223')
const ctx = browser.contexts()[0]
let page = ctx.pages().find((p) => p.url().includes('upload-video'))
if (!page) throw new Error('没找到 upload-video 页：先在 /creator 点「发视频」，或跑 open 步')
page.setDefaultTimeout(120_000)
page.on('dialog', async (d) => {
  const line = `${new Date().toISOString()} type=${d.type()} message=${d.message()}`
  appendFileSync(`${RUN}/dialogs.log`, `${line}\n`)
  console.log('DIALOG', line)
  if (d.type() === 'beforeunload') await d.accept().catch(() => {})
  else await d.dismiss().catch(() => {})
})

async function shot(name) {
  const p = `${RUN}/${EP}-${name}.png`
  try { await page.screenshot({ path: p, fullPage: true, timeout: 20000 }) }
  catch { await page.screenshot({ path: p, timeout: 20000 }).catch(() => {}); console.log('📷', p, '(整页超时，退回视口截图)'); return p }
  console.log('📷', p, '  URL:', page.url())
  return p
}

// 表单里能填的东西一次量全：标题、介绍、封面、标记、领域、原创、发布按钮的可点状态。
const snap = () => page.evaluate(() => {
  const box = (e) => { const r = e.getBoundingClientRect(); return `${Math.round(r.x)},${Math.round(r.y)} ${Math.round(r.width)}×${Math.round(r.height)}` }
  const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
  const T = (e) => (e.innerText || e.value || e.getAttribute('placeholder') || '').replace(/\s+/g, ' ').trim()
  const form = document.querySelector('.VideoUploadForm')
  return {
    url: location.href, title: document.title,
    videoInput: [...document.querySelectorAll('input[type=file]')].map((e, i) => `#${i} accept="${String(e.accept).slice(0, 18)}…" 可见=${!!e.offsetParent}`),
    titleVal: form?.querySelector('textarea')?.value ?? null,
    titleCounter: [...document.querySelectorAll('*')].map((e) => e.children.length ? '' : T(e)).find((s) => /^\d+\s*\/\s*\d+$/.test(s)) ?? null,
    introLen: form?.querySelector('[contenteditable=true]')?.innerText.replace(/\s+/g, '').length ?? null,
    introHead: (form?.querySelector('[contenteditable=true]')?.innerText || '').replace(/\s+/g, ' ').slice(0, 48),
    coverText: T([...document.querySelectorAll('*')].find((e) => vis(e) && /^(封面|选择视频封面)$/.test(T(e))) || document.body).slice(0, 30),
    // 「上传成功」写在左侧上传列表里，不在 .VideoUploadForm 内——上一版拿 formText 去测，永远为假。
    uploadOk: /上传成功/.test(document.body.innerText),
    // 封面传上去会变成知乎 CDN 的一张图，直接量它的原始尺寸，比"按钮文案变了没"硬得多。
    coverImg: (() => {
      const i = document.querySelector('.VideoUploadForm-image')
      return i ? { src: (i.currentSrc || i.src || '').slice(0, 60), nat: `${i.naturalWidth}×${i.naturalHeight}` } : { src: null, nat: null }
    })(),
    // 原创视频是 .VideoUploadForm-item 里的一个真 checkbox（实测 <input type=checkbox checked>）。
    originalChecked: (() => {
      const it = [...document.querySelectorAll('.VideoUploadForm-item')].find((e) => /原创视频/.test(e.innerText || ''))
      const c = it?.querySelector('input[type=checkbox]')
      return c ? !!c.checked : null
    })(),
    // 标记/领域/原创都是必填项，值就在表单里，一次量回来给 check 用。
    fields: [...document.querySelectorAll('.VideoUploadForm *')].filter((e) => !e.children.length && vis(e))
      .map((e) => T(e)).filter((s) => /^(个人观点仅供参考|内容无需标注|含 AI 生成内容|科学工程|原创视频|选择标记|选择领域)$/.test(s)),
    originalOn: (() => {
      const lab = [...document.querySelectorAll('.VideoUploadForm *')].find((e) => vis(e) && T(e) === '原创视频')
      const sw = lab?.parentElement?.querySelector('[role=switch],button[class*=Switch i],[class*=Switch],[class*=toggle i]')
        || lab?.nextElementSibling?.querySelector('[role=switch],[class*=Switch]')
      return sw ? { found: true, checked: sw.getAttribute('aria-checked') ?? sw.className.match(/checked/i) ? 'checked' : 'unclear', cls: String(sw.className).slice(0, 40) } : { found: false }
    })(),
    buttons: [...document.querySelectorAll('button,[role=button]')].filter(vis).map((e) => `${T(e).slice(0, 20) || '(空)'}[${e.disabled ? '禁用' : '可点'}] ${box(e)}`).filter((s) => s !== '(空)[可点] 0×0 0×0').slice(0, 26),
    formText: (form?.innerText || '(没有 .VideoUploadForm)').replace(/\n{2,}/g, '\n'),
    popup: [...document.querySelectorAll('[class*=Dropdown],[class*=dropdown],[class*=Popover],[class*=Menu],[class*=Modal]')]
      .filter(vis).map((e) => `class="${String(e.className).slice(0, 40)}" 文案="${T(e).slice(0, 120)}"`).slice(0, 6),
  }
})

const V = {
  async open() {
    page = await ctx.newPage()
    await page.goto('https://www.zhihu.com/upload-video', { waitUntil: 'domcontentloaded', timeout: 60000 })
    await page.waitForTimeout(8000)
    console.log(JSON.stringify(await snap(), null, 1))
    await shot('open')
  },
  async feed() {
    if (!existsSync(F.video)) throw new Error(`片源不存在：${F.video}`)
    const inp = page.locator('input[type=file][accept*=".mp4"]').first()
    await inp.setInputFiles(F.video, { timeout: 30000 })
    console.log(`已投喂 ${F.video}`)
    for (let i = 0; i < 60; i++) {
      await page.waitForTimeout(3000)
      const t = await page.evaluate(() => document.body.innerText)
      if (/上传成功/.test(t)) { console.log(`上传成功（第 ${i * 3}s）`); break }
      if (/上传失败|失败/.test(t) && !/上传成功/.test(t)) console.log(`…${i * 3}s 看到失败文案，继续等`)
      if (i % 5 === 0) console.log(`…${i * 3}s 还没成功`)
    }
    console.log(JSON.stringify(await snap(), null, 1))
    await shot('feed')
  },
  // 「替换视频」是实测存在的按钮（位置 298,191）。喂文件的 input 页面上有三个（两个 .mp4 一个 image），
  // 按 accept 去 .first() 完全可能喂错一个——所以不猜：拦截这次点击真正唤起的 filechooser，
  // 文件只交给它。这样"点的按钮"和"喂的 input"必然是同一个。
  async swap() {
    if (!existsSync(F.video)) throw new Error(`片源不存在：${F.video}`)
    const pick = async (label) => {
      const hop = page.waitForEvent('filechooser', { timeout: 6000 })
      await page.getByText(label, { exact: false }).first().click({ timeout: 15000 })
      const fc = await hop.catch(() => null)
      if (!fc) return null
      await fc.setFiles(F.video)
      console.log(`「${label}」→ filechooser，已喂 ${F.video}`)
      return true
    }
    if (!(await pick('替换视频'))) console.log('「替换视频」没唤起 filechooser（可能是弹层），下面按面板再量一次')
    for (let i = 0; i < 60; i++) {
      await page.waitForTimeout(3000)
      const t = await page.evaluate(() => document.body.innerText)
      if (/上传成功/.test(t)) { console.log(`上传成功（第 ${i * 3}s）`); break }
      if (i % 5 === 0) console.log(`…${i * 3}s 还没成功`)
    }
    console.log(JSON.stringify(await snap(), null, 1))
    await shot('swap')
  },
  async fill() {
    const p = needPub()
    const title = p.titles[TI]
    if (!title) throw new Error(`publish.zhihu.titles[${TI}] 不存在`)
    const ta = page.locator('.VideoUploadForm textarea').first()
    await ta.fill(title, { timeout: 20000 })
    // 介绍是 DraftEditor（contenteditable），fill() 对它无效；键入走 beforeinput，React 才认。
    const ed = page.locator('.VideoUploadForm [contenteditable=true]').first()
    await ed.click({ timeout: 20000 })
    await page.waitForTimeout(600)
    await page.keyboard.insertText(pub.intro)
    await page.waitForTimeout(2500)
    console.log(`标题=${title}`)
    console.log(JSON.stringify(await snap(), null, 1))
    await shot('fill')
  },
  async cover() {
    if (!existsSync(F.cover)) throw new Error(`封面不存在：${F.cover}`)
    // 上一步可能已经把面板开着就跑完了脚本（进程退出、浏览器还在）。已经开着就别再点一遍表头。
    const already = await page.evaluate(() => [...document.querySelectorAll('[class*=Modal],[role=dialog]')]
      .some((e) => (e.offsetWidth || e.offsetHeight) && /封面/.test((e.innerText || '').replace(/\s+/g, ' '))))
    if (already) console.log('封面面板已经开着，直接往里走')
    else await page.getByText(/选择视频封面|更改视频封面/).first().click({ timeout: 15000 })
    await page.waitForTimeout(3000)
    const panel = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const T = (e) => (e.innerText || e.value || '').replace(/\s+/g, ' ').trim()
      const root = [...document.querySelectorAll('[class*=Modal],[class*=modal],[role=dialog],[class*=Popover]')].filter(vis).find((e) => /封面/.test(T(e)))
      return {
        found: !!root,
        rootClass: root ? String(root.className).slice(0, 70) : null,
        text: root ? T(root).slice(0, 400) : null,
        tabs: root ? [...root.querySelectorAll('[role=tab],.Tabs *,[class*=tab i],[class*=Tab]')].filter(vis).map((e) => T(e).slice(0, 20)).filter(Boolean).slice(0, 12) : [],
        buttons: root ? [...root.querySelectorAll('button,[role=button]')].filter(vis).map((e) => T(e).slice(0, 24)).filter(Boolean).slice(0, 16) : [],
        imgInputs: [...document.querySelectorAll('input[type=file][accept^="image"]')].map((e, i) => { const r = e.getBoundingClientRect(); return `#${i} 可见=${!!e.offsetParent} 在面板内=${!!(root && root.contains(e))} 位置=${Math.round(r.x)},${Math.round(r.y)}` }),
      }
    })
    console.log(JSON.stringify(panel, null, 1))
    await shot('cover-panel')
    // 面板实测文案是「选择封面 / 本地上传 / 00:00 /08:55 / 确认选择」：本地上传是面板里的一个动作，
    // 不是页面上那个隐藏的 image input（#0 可见=false、也不在面板内）。点它并接住它唤起的 filechooser。
    // 「本地上传」是面板顶部的一个 tab。点完它，面板里才出现一个"可见且在面板内"的 image input
    // （实测 #1 可见=true 在面板内=true @463,236）——页面上另外那个 image input 是隔壁想法编辑器的，
    // 所以判据用"可见 + 在面板内"，而不是按 accept 取 first。
    await page.getByText('本地上传', { exact: false }).first().click({ timeout: 15000 }).catch(() => {})
    await page.waitForTimeout(2000)
    // 上一轮已经传过一张的话，面板会停在「重新上传 / 确认选择」——先按重新上传，回到可喂的状态。
    const again = page.getByText('重新上传', { exact: true }).first()
    if (await again.count()) { await again.click({ timeout: 10000 }).catch(() => {}); await page.waitForTimeout(2000); console.log('面板停在「重新上传」，已按一次') }
    const zone = page.getByText('点击上传或将文件拖入此区域', { exact: false }).first()
    console.log('拖拽区在不在=', await zone.count())
    const inPanel = page.locator('input[type=file][accept^="image"]')
    const n = await inPanel.count()
    let fed = false
    for (let i = 0; i < n; i++) {
      const e = inPanel.nth(i)
      const ok = await e.evaluate((el) => {
        const vis = !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length)
        const modal = el.closest('[class*=Modal],[role=dialog]')
        return vis && !!modal && /封面/.test(modal.innerText || '')
      })
      if (!ok) continue
      await e.setInputFiles(F.cover, { timeout: 30000 })
      console.log(`已喂封面 → 第 ${i} 个 image input（可见且在「封面」面板里）`)
      fed = true
      break
    }
    if (!fed) { console.log('面板里没有可见的 image input，停手不猜'); await shot('cover-local'); return }
    await page.waitForTimeout(9000)
    const after = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      const root = [...document.querySelectorAll('[class*=Modal],[role=dialog]')].filter(vis).find((e) => /封面/.test(T(e)))
      return { still: !!root, text: root ? T(root).slice(0, 260) : null, buttons: root ? [...root.querySelectorAll('button,[role=button]')].filter(vis).map((e) => T(e).slice(0, 20)).filter(Boolean) : [] }
    })
    console.log(JSON.stringify(after, null, 1))
    await shot('cover-local')
  },
  // 封面选完要在面板里点「确认选择」才落回表单——和抖音那次的教训一样：喂进去不等于选上了。
  async coverok() {
    const btn = page.getByText('确认选择', { exact: true }).first()
    if (!(await btn.count())) throw new Error('面板里没有「确认选择」')
    await btn.click({ timeout: 15000 })
    await page.waitForTimeout(7000)
    console.log(JSON.stringify(await snap(), null, 1))
    await shot('coverok')
  },
  // 标记/领域这些控件，文字只是个 <span>，真正能吃点击的是盖在它上面的
  // <button aria-label="选择视频标记" class="VideoUploadForm-videoTypeSelectOverlay">——
  // 按文案点会被 Playwright 的命中检查无限重试（实测 15s 超时）。所以一律按 aria-label 点。
  // 弹层开着的时候不能同时量下一个字段，所以留一个明确的收手动作：只点弹层里的「取消」。
  async close() {
    const c = page.locator('.Modal button, [role=dialog] button').filter({ hasText: /^取消$/ }).last()
    if (!(await c.count())) { console.log('没有「取消」可点'); return }
    await c.click({ timeout: 10000 })
    await page.waitForTimeout(2500)
    console.log('已点「取消」，残留模态=', await page.locator('.Modal').count())
  },
  async popup() {
    const which = arg('--which') ?? 'mark'
    const aria = arg('--aria') ?? (which === 'mark' ? '选择视频标记' : null)
    const css = arg('--css')
    if (!aria && !css) throw new Error('--aria|--css 没给')
    const labels = await page.evaluate(() => [...document.querySelectorAll('button[aria-label]')]
      .map((e) => e.getAttribute('aria-label')))
    console.log('页面上的 aria-label：', JSON.stringify([...new Set(labels)]))
    const btn = (css ? page.locator(css) : page.locator(`button[aria-label="${aria}"]`)).first()
    if (!(await btn.count())) throw new Error(`选择器没命中：${css || aria}，见上面清单`)
    await btn.click({ timeout: 15000 })
    await page.waitForTimeout(3500)
    const d = await page.evaluate(() => {
      const vis = (e) => !!(e.offsetWidth || e.offsetHeight || e.getClientRects().length)
      const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
      return {
        popups: [...document.querySelectorAll('[class*=Dropdown],[class*=dropdown],[class*=Popover],[class*=Modal],[class*=Dialog],[role=dialog]')]
          .filter(vis).map((e) => `class="${String(e.className).slice(0, 60)}"\n  文案="${T(e).slice(0, 400)}"`),
        options: [...document.querySelectorAll('[role=option],[role=listbox] *,li,.Tabs a,[class*=item i],[class*=Item]')]
          .filter((e) => vis(e) && e.children.length === 0 && T(e)).map((e) => T(e).slice(0, 30)).slice(0, 60),
        inputs: [...document.querySelectorAll('input')].filter((e) => vis(e)).map((e) => `type=${e.type} ph="${e.placeholder}" 位置=${Math.round(e.getBoundingClientRect().x)},${Math.round(e.getBoundingClientRect().y)}`),
      }
    })
    console.log(JSON.stringify(d, null, 1))
    await shot(`popup-${which}`)
  },
  // 在已经打开的弹层里按文案点一项。限定在 .Modal/[role=dialog] 里找，避免点到页面同名的别的文字。
  async pick() {
    const text = arg('--text')
    if (!text) throw new Error('--text 没给')
    // 领域这一层不是 .Modal，是 Select 的 Popover（标记那层才是 Modal）。所以先按"可见的弹层"找，
    // 找不到就直接点页面上唯一可见的同名文字——两条路都要求命中唯一，否则停手。
    const hosts = page.locator('.Modal:visible, [role=dialog]:visible, [class*=Popover]:visible').filter({ hasText: text })
    const nh = await hosts.count()
    const scope = nh ? hosts.last() : page
    const opt = (await scope.getByText(text, { exact: true }).count())
      ? scope.getByText(text, { exact: true }).locator('visible=true').last()
      : null
    if (!opt || !(await opt.count())) throw new Error(`找不到可见的「${text}」（弹层数=${nh}）`)
    await opt.click({ timeout: 10000 })
    await page.waitForTimeout(2500)
    const ok = scope.locator('button, [role=button]').filter({ hasText: /^(确认|确定)$/ }).last()
    if (await ok.count()) { await ok.click({ timeout: 10000 }).catch(() => {}); await page.waitForTimeout(2500); console.log('已点弹层的「确认」') }
    else console.log('这个弹层没有「确认」按钮（可能是选中即生效）')
    console.log(JSON.stringify(await snap(), null, 1))
    await shot(`pick-${text}`)
  },
  async status() { console.log(JSON.stringify(await snap(), null, 1)); await shot('status') },
  async check() {
    const s = await snap()
    const p = needPub()
    const want = { title: p.titles[TI], introChars: p.intro.replace(/\s+/g, '').length }
    const items = [
      ['片源已上传', s.uploadOk === true],
      ['标题一字不差', s.titleVal === want.title],
      ['标题长度', s.titleVal ? [...s.titleVal].length <= 100 : false],
      ['介绍非空', (s.introLen ?? 0) > want.introChars * 0.6],
      ['封面是 16:9 那张', s.coverImg?.nat === '1920×1080'],
      [`视频标记=${p.mark}`, s.fields?.includes(p.mark)],
      [`所属领域=${p.domain}`, s.fields?.includes(p.domain)],
      [`原创视频=${p.original ? '开' : '关'}`, s.originalChecked === !!p.original],
    ]
    for (const [k, ok] of items) console.log(`${ok ? '✅' : '❌'} ${k}`)
    console.log('  titleVal=' + JSON.stringify(s.titleVal), '\n  计数器=' + s.titleCounter, `  介绍字数=${s.introLen}（本地=${want.introChars}）`)
    console.log('  fields=' + JSON.stringify(s.fields), '\n  封面图=' + JSON.stringify(s.coverImg), `  原创=${s.originalChecked}  上传=${s.uploadOk}`)
    console.log('  发布按钮=', s.buttons.filter((b) => /发布/.test(b)).join(' | '))
    await shot('check')
    if (!items.every(([, ok]) => ok)) throw new Error('核对未过，不发布')
  },
  async publish() {
    const gate = `${RUN}/I_HAVE_USER_OK=${EP}`
    if (!existsSync(gate)) throw new Error(`没有闸门文件 ${gate}\n它只能来自对话里用户对这一条知乎投稿的点头`)
    console.log('闸门放行：' + readFileSync(gate, 'utf8').trim())
    const btn = page.getByRole('button', { name: '发布视频' }).first()
    await btn.click({ timeout: 15000 })
    await page.waitForTimeout(12000)
    console.log('点后 URL=', page.url())
    console.log(JSON.stringify(await snap(), null, 1))
    await shot('published')
  },
}
if (!step || !V[step]) throw new Error(`未知步骤 "${step}"，可选：${Object.keys(V).join(' / ')}`)
// 不写 browser.close()：这是 CDP 连接，close 会连带把常驻浏览器关掉（2026-10-16 杀过一次，登录态得重新验）。
// 本进程退出时 socket 跟着死，浏览器和它已选好的片源留着。
await V[step]()
process.exit(0)
