// 常驻一个有头 chromium（持久 profile + 远程调试端口 9223），网页通道的驱动作为独立进程连上来逐步操作。
// profile 复用抖音那个：登录态存在 user-data-dir 里，一处登录，创作中心和 B站投稿页都认。
// 为什么要常驻：B站投稿表单的状态只在当前页面里，脚本一退、窗口一关，选好的视频和填好的字就全没了。
import { chromium } from 'playwright'

const DIR = 'D:/Users/mcu/.temp/douyin-profile'

const ctx = await chromium.launchPersistentContext(DIR, {
  headless: false,
  viewport: null,
  args: ['--disable-blink-features=AutomationControlled', '--remote-debugging-port=9223'],
})
console.log('常驻浏览器已起，调试端口 9223；关掉这个进程才会关窗口')

// 一直挂着，直到进程被停掉
await new Promise(() => {})
