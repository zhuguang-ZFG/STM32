// 小红书创作平台的常驻浏览器：复用 video/publish/douyin-daemon.mjs 那个持久 profile 与 9223 端口，
// 只是首页换成创作者中心。为什么复用同一个 profile：另外三条线已经共用这一个有头窗口，
// 同一 user-data-dir 起第二个实例会被"profile 正在使用"直接挡掉。
// 窗口挂着就是有用的——没登录时人要在这个窗口里扫码，扫码态只有留在这个 profile 里才认得。
import { chromium } from 'playwright'

const DIR = 'D:/Users/mcu/.temp/douyin-profile'
// /creator/home 实测回「你访问的页面不见了」；/new/home 才是创作者中心真正落地的首页（笔记管理在它下面 /new/note-manager）
const URL = 'https://creator.xiaohongshu.com/new/home'

const ctx = await chromium.launchPersistentContext(DIR, {
  headless: false,
  viewport: null,
  args: ['--disable-blink-features=AutomationControlled', '--remote-debugging-port=9223'],
})
const page = ctx.pages()[0] ?? (await ctx.newPage())
page.setDefaultNavigationTimeout(240_000)
page.setDefaultTimeout(240_000)
await page
  .goto(URL, { waitUntil: 'domcontentloaded' })
  .then(() => console.log('常驻浏览器已起（小红书创作者中心），调试端口 9223；关掉这个进程才会关窗口'))
  .catch((e) => console.log(`常驻浏览器已起，调试端口 9223；首页没打开（${e.message.split('\n')[0]}），探针会自己重新导航`))

// 挂进程靠一个自己的定时器，不靠 page 对象：探针按纪律只关它自己新开的那一页，
// 可万一有人（或上一版探针）把这个常驻页关了，unsettled top-level await 会让 node 直接以 13 退出、窗口跟着没，
// 登录态就得重来。常驻进程的命不能握在别人的 page 上。
setInterval(() => {}, 1 << 30)
