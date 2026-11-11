import { test, expect } from '@playwright/test'

test('both complete logger chapters expose actual source and pending hardware status', async ({ page }) => {
  await page.setViewportSize({width:390,height:844})
  for(const route of ['projects/01-f407-logger.html','projects/02-s3-logger.html']){
    await page.goto(route)
    await expect(page.locator('.mcu-lab-status')).toContainText('工程已提供')
    await expect(page.locator('.mcu-lab-status')).toContainText('待上板实测')
    await expect(page.locator('.vp-doc')).toContainText('logger_create_tasks')
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1)).toBe(true)
  }
})
import { readdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

// 磁盘上有多少张动画，演示中心页就必须一张不少地陈列出来——
// anim-lint 管源文件登记，这里管的是构建后的真实页面。
const animDir = join(dirname(dirname(dirname(fileURLToPath(import.meta.url)))), 'docs', 'public', 'anim')
const svgNames = readdirSync(animDir).filter(f => f.endsWith('.svg')).map(f => f.slice(0, -4))

test('search loads its index on demand and returns tutorial results', async ({ page }) => {
  const requests=[]
  page.on('request', r=>requests.push(r.url()))
  await page.goto('./', { waitUntil: 'networkidle' })
  expect(requests.filter(u=>u.includes('@localSearchIndex'))).toHaveLength(0)
  await page.locator('.VPNavBarSearch button').click()
  await page.locator('#localsearch-input').fill('I2C')
  await expect(page.locator('#localsearch-list [role=option]').first()).toBeVisible({timeout:15000})
  expect(requests.some(u=>u.includes('@localSearchIndex'))).toBeTruthy()
  await page.locator('#localsearch-list a.result').first().click()
  await expect(page.locator('.vp-doc h1')).toBeVisible()
})
// 暂停/播放是否真落到了 SMIL 上，只认 svg.animationsPaused()。
// 用轮询而不是 waitForFunction 的 rAF：满页 SMIL 的慢机器上一帧要几百毫秒，
// 靠 rAF 等结果等于在最堵的路上排队。
const svgPaused = (figure) => figure.evaluate((el) => el.querySelector('svg').animationsPaused())

test('animation controls and reduced motion work in both themes', async ({ page }) => {
  const errors=[]
  page.on('pageerror', e=>errors.push(e.message))
  await page.goto('stm32/02-rcc-clock.html')
  const figure=page.locator('.anim-figure').first()
  const button=figure.locator('.anim-figure__btn')
  await expect(button).toHaveText('暂停')
  await button.click()
  await expect(button).toHaveText('播放')
  await expect.poll(() => svgPaused(figure)).toBe(true)
  await button.click()
  await expect(button).toHaveText('暂停')
  await expect.poll(() => svgPaused(figure)).toBe(false)
  await page.emulateMedia({ reducedMotion:'reduce',colorScheme:'dark' })
  await page.reload()
  await expect(button).toHaveText('播放')
  await expect(page.locator('html')).toHaveClass(/dark/)
  await expect.poll(() => svgPaused(figure)).toBe(true)
  expect(errors).toEqual([])
})
test('animation gallery lists every svg with working controls', async ({ page }) => {
  // 画廊页一次加载全部 SMIL 动画（60+ 张）。视口外的图由 AnimFigure 自动停，
  // 否则 CI 共享 runner 上帧率掉到个位数，任何靠 rAF 的等待都会耗尽预算。
  test.slow()
  await page.goto('animations.html')
  const figures = page.locator('.anim-figure')
  await expect(figures).toHaveCount(svgNames.length)
  const listed = await page.evaluate(() => [...document.querySelectorAll('.anim-figure')].map(el => el.dataset.anim))
  expect([...new Set(listed)].sort()).toEqual([...new Set(svgNames)].sort())
  await expect(page.locator('.anim-figure__btn')).toHaveCount(svgNames.length)
  // 页尾的图离视口很远：SMIL 必须已被自动停，但按钮仍是「暂停」——这不是用户意图。
  const last = figures.last()
  await expect(last).toHaveClass(/is-offscreen/)
  await expect(last.locator('.anim-figure__btn')).toHaveText('暂停')
  await expect.poll(() => svgPaused(last)).toBe(true)
  // 视口内的图：按钮真能停、真能续。
  const first = figures.first()
  const button = first.locator('.anim-figure__btn')
  await first.scrollIntoViewIfNeeded()
  await expect(first).not.toHaveClass(/is-offscreen/)
  await expect(button).toHaveText('暂停')
  await button.click()
  await expect(button).toHaveText('播放')
  await expect.poll(() => svgPaused(first)).toBe(true)
  await button.click()
  await expect(button).toHaveText('暂停')
  await expect.poll(() => svgPaused(first)).toBe(false)
})
test('lab states and metadata are visible on mobile', async ({ page }) => {
  await page.setViewportSize({width:390,height:844})
  await page.goto('lab/')
  await expect(page.locator('.vp-doc')).toContainText('实验')
  await page.goto('lab/e07-qmi8658.html')
  await expect(page.locator('.mcu-lab-status')).toContainText('60 分钟')
  await expect(page.locator('.mcu-lab-status')).toContainText('工程已提供')
  await expect(page.locator('.mcu-lab-status')).toContainText('待上板实测')
  expect(await page.evaluate(()=>document.documentElement.scrollWidth <= window.innerWidth+1)).toBe(true)
})
