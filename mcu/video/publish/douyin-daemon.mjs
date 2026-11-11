// 常驻一个有头 chromium（持久 profile + 远程调试端口），上传驱动作为独立小进程连上来逐步操作。
// 为什么要常驻：抖音发布表单的状态只在当前页面里，脚本一退、浏览器一关，选好的视频和填好的字就全没了。
// 之前一次次 launch→close 探结构，每探一次就得重传一遍 6 MB，就是这个原因。
import { chromium } from 'playwright'
import { mkdirSync } from 'node:fs'

const DIR = 'D:/Users/mcu/.temp/douyin-profile'
mkdirSync(DIR, { recursive: true })

const ctx = await chromium.launchPersistentContext(DIR, {
  headless: false,
  viewport: null,
  args: ['--disable-blink-features=AutomationControlled', '--remote-debugging-port=9223'],
})
const page = ctx.pages()[0] ?? (await ctx.newPage())
// 上行只有 6.8~10.2 秒一个请求，playwright 默认 30 秒的导航预算会在这一步直接炸掉（进程一炸窗口就跟着关，
// 于是又得重开一次、再等一次登录态）。给足预算，并且打不开页面也别退——窗口挂着就是有用的。
page.setDefaultNavigationTimeout(240_000)
page.setDefaultTimeout(240_000)
await page.goto('https://creator.douyin.com/creator-micro/content/upload', { waitUntil: 'domcontentloaded' })
  .then(() => console.log('常驻浏览器已起，调试端口 9223；关掉这个进程才会关窗口'))
  .catch((e) => console.log(`常驻浏览器已起，调试端口 9223；首页没打开（${e.message.split('\n')[0]}），驱动脚本会自己重新导航`))

// 一直挂着，直到进程被停掉
await new Promise(() => {})
