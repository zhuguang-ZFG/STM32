import { test, expect } from '@playwright/test'

for (const width of [390, 1440]) {
  test(`精排导读 ${width}px：入口真实载入、标题可读、目录可跳转`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1000 })
    await page.goto('reference/book.html')
    await page.getByRole('link', { name: '打开精排导读', exact: true }).click()
    await expect(page).toHaveURL(/\/mcu\/book-guide\/index\.html$/)
    // A VitePress 404 can retain the URL; assert the independent HTML itself.
    await expect(page.locator('html')).toHaveAttribute('data-medium', 'page')
    await expect(page.locator('main h1')).toBeVisible()
    const titleColor = await page.locator('main h1').evaluate(el => getComputedStyle(el).color)
    const background = await page.locator('.hero-overlay').evaluate(el => getComputedStyle(el).backgroundColor)
    expect(titleColor).not.toEqual(background)
    await expect(page.locator('[contenteditable="true"]')).toHaveCount(0)
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth)
    expect(overflow).toBeLessThanOrEqual(1)
    await page.locator('#toc-toggle').click()
    await page.locator('.toc-item').filter({ hasText: '参与校对与贡献' }).click()
    await expect(page).toHaveURL(/#s-04$/)
    if (width === 390) await expect(page.locator('#toc')).not.toHaveClass(/toc-open/)
  })
}
