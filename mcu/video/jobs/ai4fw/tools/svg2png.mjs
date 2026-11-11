// SVG → PNG：仓库 stage.mjs 的 Chromium 截图模式（srgb、无字体渲染干预、禁 LCD 文本）
import { chromium } from '@playwright/test'
import { readdirSync } from 'node:fs'
import { resolve, join, basename } from 'node:path'

const [srcDir, outDir] = process.argv.slice(2)
const browser = await chromium.launch({
  args: ['--force-color-profile=srgb', '--font-render-hinting=none', '--hide-scrollbars',
         '--disable-lcd-text', '--disable-features=PaintHolding'],
})
for (const f of readdirSync(srcDir).filter((f) => f.endsWith('.svg'))) {
  const page = await browser.newPage({
    viewport: { width: 1080, height: 1920 },
    deviceScaleFactor: 1,
    reducedMotion: 'reduce',
  })
  await page.goto('file:///' + resolve(srcDir, f).replaceAll('\\', '/'))
  await page.evaluate(() => document.fonts.ready)
  await page.screenshot({
    path: join(outDir, basename(f, '.svg') + '.png'),
    clip: { x: 0, y: 0, width: 1080, height: 1920 },
  })
  await page.close()
  console.log('PNG', f)
}
await browser.close()
