import { chromium } from '@playwright/test'
const browser = await chromium.launch({args:['--force-color-profile=srgb','--font-render-hinting=none','--hide-scrollbars']})
const page = await browser.newPage({viewport:{width:1920,height:1080},deviceScaleFactor:1})
await page.goto('file:///D:/Users/mcu/video/jobs/ai4fw-16x9/inputs/images/src/cover169.svg')
await page.evaluate(() => document.fonts.ready)
await page.screenshot({path:'D:/Users/mcu/video/jobs/ai4fw-16x9/inputs/images/cover169.png',clip:{x:0,y:0,width:1920,height:1080}})
await browser.close()
console.log('done')
