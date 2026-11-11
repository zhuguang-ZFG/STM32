// B站合集封面：与抖音那张同源（同配色/字体/自适应缩字），只换比例——
// B站封面原生 1920×1200（16:10），拿 1080 方图过去会被上下各裁一条。
import { chromium } from 'playwright'
import { readFileSync } from 'node:fs'
import { buildCover } from '../src/package.mjs'

const series = JSON.parse(readFileSync('D:/Users/mcu/video/series.json', 'utf8'))
const base = JSON.parse(readFileSync('D:/Users/mcu/video/episodes/c3-volatile/episode.json', 'utf8'))
const ep = {
  ...base,
  id: 'season',
  badge: '合集',
  cover: {
    kicker: series.series.trim(),
    line1: '屏上每个数',
    line2: '都是本机跑的',
    vs: { left: '背下来的结论', right: '本机跑出来的' },
    sizes: { bili: [1920, 1200] },
  },
}

const browser = await chromium.launch()
try {
  await buildCover(browser, ep, 'bili', 'D:/Users/mcu/video/out/season-cover-bili.png')
  console.log('✅ B站合集封面 → D:/Users/mcu/video/out/season-cover-bili.png')
} finally {
  await browser.close()
}
