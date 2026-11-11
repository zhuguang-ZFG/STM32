// 置顶自己那条导流评论。默认只探不点；带 --go 才真置顶。
// 判据只认一条：置顶成功后，评论列表里出现「置顶」标记，且它挂在我们那条上。
import { readFileSync } from 'node:fs'
import { chromium } from 'playwright'

// 缺 --ep 不回落默认集：拿着 c3 的登记簿去置顶 f5 的评论，是"给别人家帖子做家务"。
const EP = arg('--ep')
if (!EP) throw new Error('缺 --ep <episode-id>（--ep x 和 --ep=x 都认）——不猜这是哪一集')
const RUN = 'D:/Users/mcu/.temp/douyin-run'
const go = process.argv.includes('--go')
function arg(name) { const i = process.argv.findIndex((a) => a === name || a.startsWith(`${name}=`)); if (i < 0) return null; const a = process.argv[i]; return a.includes('=') ? a.slice(a.indexOf('=') + 1) || null : process.argv[i + 1] ?? null }
const head = (s, n) => s.slice(0, n)

const md = readFileSync(`D:/Users/mcu/video/out/${EP}/发布-douyin.md`, 'utf8')
const want = md.split(/^## /m).find((s) => s.startsWith('②')).match(/```text\n([\s\S]*?)```/)[1].trim()
const line = readFileSync('D:/Users/mcu/.temp/douyin-submitted.txt', 'utf8').split('\n').find((l) => l.includes(`\t${EP}\t`))
if (!line) throw new Error(`登记簿里没有 ${EP}`)
const aweme = line.split('\t')[2]

const b = await chromium.connectOverCDP('http://127.0.0.1:9223', { timeout: 60_000 })
const ctx = b.contexts()[0]
// 和 douyin-comment.mjs 同一个坑：新开一页 + 固定等 12 秒，在这条 6.8~10.2 秒一个请求的上行上必然还没水合。
// 有现成的作品页就复用，没有再开；然后轮询等我们那条评论真的渲染出来。
let p = ctx.pages().find((x) => x.url().includes(aweme))
if (!p) {
  p = await ctx.newPage()
  p.setDefaultNavigationTimeout(240_000)
  await p.goto(`https://www.douyin.com/video/${aweme}`, { waitUntil: 'domcontentloaded' }).catch((e) => console.log('goto:', e.message.split('\n')[0]))
}
p.setDefaultTimeout(40_000)
for (let k = 0; k < 36; k++) {
  const hot = await p.evaluate((t) => [...document.querySelectorAll('div,span,p')]
    .some((e) => e.children.length === 0 && (e.innerText || '').includes(t.slice(0, 24))), want).catch(() => false)
  if (hot) { console.log(`我们那条评论已渲染（t+${k * 5}s）`); break }
  await p.waitForTimeout(5000)
}

const find = () => p.evaluate((t) => {
  const tx = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
  const vis = (e) => !!(e.offsetWidth || e.offsetHeight)
  const node = [...document.querySelectorAll('div,span,p')].filter((e) => e.children.length === 0 && (e.innerText || '').includes(t.slice(0, 24)))[0]
  if (!node) return null
  // 评论面板是内层滚动容器（document 的 scrollHeight 就等于 innerHeight），
  // 直接拿 rect 去点会点到视口外——上一版就是这么把 ⋯ 点没的。先滚进可视区再量。
  node.scrollIntoView({ block: 'center', behavior: 'instant' })
  const r = node.getBoundingClientRect()
  // 抖音的「⋯」是 hover 才出现的，所以把整条评论的容器也算出来，方便在附近找菜单
  const host = node.closest('[class*="comment"],[class*="Comment"]') || node.parentElement
  const ops = [...(host || document).querySelectorAll('*')].filter((e) => e.children.length === 0 && vis(e))
    .map((e) => { const q = e.getBoundingClientRect(); return { text: tx(e).slice(0, 8), icon: /^(⋯|…|\.\.\.)$/.test(tx(e)), x: Math.round(q.x + q.width / 2), y: Math.round(q.y + q.height / 2), w: Math.round(q.width) } })
    .filter((o) => o.text && o.w < 120)
  return { box: { x: Math.round(r.x + r.width / 2), y: Math.round(r.y + r.height / 2) }, inView: r.top > 0 && r.bottom < innerHeight, pinned: !![...document.querySelectorAll('*')].filter((e) => e.children.length === 0 && tx(e) === '置顶').length, ops: ops.slice(0, 12) }
}, want)

let st = await find()
console.log('初始：', JSON.stringify(st, null, 1))
if (!st) { console.log('没找到我们那条评论——可能列表没展开'); process.exit(1) }

await p.mouse.move(st.box.x, st.box.y)
await p.waitForTimeout(1500)
st = await find()
const dots = st.ops.find((o) => o.icon) || st.ops.find((o) => /⋯|…|\.\.\./.test(o.text))
console.log('hover 后 ops：', JSON.stringify(st.ops), '\n⋯ 位置：', JSON.stringify(dots ?? null))
if (!dots) { console.log('没有 ⋯ 菜单，先停'); process.exit(1) }

// 菜单项到底是哪几个，用「点之前 vs 点之后」的可见文本差集来认，比按坐标圈窗口可靠：
// ⋯ 那个弹层是 portal，坐标不一定落在 ⋯ 下方，而上一版就是被旁边的推荐卡片冒充成了菜单。
const leaf = () => p.evaluate(() => {
  const tx = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
  const vis = (e) => !!(e.offsetWidth || e.offsetHeight)
  return [...document.querySelectorAll('li,div,span,button,p')].filter((e) => e.children.length === 0 && vis(e))
    .map((e) => { const r = e.getBoundingClientRect(); return `${tx(e).slice(0, 12)}@${Math.round(r.x + r.width / 2)},${Math.round(r.y + r.height / 2)}` })
    .filter((s) => s.length > 1)
})
const before = new Set(await leaf())
await p.mouse.move(dots.x, dots.y)
await p.waitForTimeout(800)
await p.mouse.click(dots.x, dots.y)
await p.waitForTimeout(2500)
// ⋯ 在评论条最右，靠屏幕右缘，往左留出 560 宽的视野
// connectOverCDP 拿不到 viewportSize()（返回 null），所以视口尺寸从页面里量
const { VW, VH, SY } = await p.evaluate(() => ({ VW: innerWidth, VH: innerHeight, SY: scrollY }))
const cx = Math.max(0, Math.min(dots.x - 460, VW - 560))
const cy = Math.max(0, Math.min(dots.y - 60 + SY, VH - 460))
await p.screenshot({ path: `${RUN}/${EP}-pin-menu.png`, clip: { x: cx, y: cy, width: Math.min(560, VW - cx), height: Math.min(460, VH - cy) } })
const added = (await leaf()).filter((s) => !before.has(s))
const menu = added.map((s) => {
  const [text, at] = [s.slice(0, s.indexOf('@')), s.slice(s.indexOf('@') + 1)]
  const [x, y] = at.split(',').map(Number)
  return { text, x, y }
})
console.log('新出现的项：', JSON.stringify(menu))
// 上一版截图截到了播放器区，说明 ⋯ 的 rect 和实际渲染位置对不上。
// 这里不猜坐标：整页截图 + 把所有高 z-index 可见层原样打出来，弹层在不在、写的什么，一眼定死。
console.log('视口/滚动：', JSON.stringify(await p.evaluate(() => ({ w: innerWidth, h: innerHeight, sy: scrollY, sh: document.documentElement.scrollHeight }))))
console.log('高 z 可见层：', JSON.stringify(await p.evaluate(() => {
  const tx = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
  return [...document.querySelectorAll('body *')].filter((e) => {
    const s = getComputedStyle(e), r = e.getBoundingClientRect()
    return s.position === 'fixed' && Number(s.zIndex || 0) > 10 && r.width > 40 && r.height > 20 && tx(e)
  }).map((e) => { const r = e.getBoundingClientRect(); return { cls: e.className.toString().slice(0, 40), z: getComputedStyle(e).zIndex, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), text: tx(e).slice(0, 40) } }).slice(0, 10)
})))
await p.screenshot({ path: `${RUN}/${EP}-pin-full.png`, fullPage: true })
const pin = menu.find((m) => m.text === '置顶') || menu.find((m) => m.text === '取消置顶')
if (!pin) { console.log('菜单里没有置顶项'); process.exit(1) }
if (!go) { console.log('（只探不点；加 --go 才真置顶）'); await p.close(); process.exit(0) }

await p.mouse.click(pin.x, pin.y)
await p.waitForTimeout(5000)
const after = await find()
console.log('点完「' + pin.text + '」后 pinned 标记：', after?.pinned)
await p.screenshot({ path: `${RUN}/${EP}-pin-done.png` })
process.exit(0)
