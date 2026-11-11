import { test } from 'node:test'
import assert from 'node:assert/strict'
import {
  metaContent,
  canonicalHref,
  checkPageHtml,
  checkSitemap,
  checkRobots,
  HOST,
} from '../scripts/seo-check.mjs'

const page = (extra = '') => `<!doctype html><html lang="zh-CN"><head>
<meta property="og:title" content="S3 GPIO">
<meta property="og:description" content="寄存器级 GPIO 教学">
<meta property="og:url" content="${HOST}/mcu/stm32/03-gpio.html">
<meta property="og:image" content="${HOST}/mcu/og-cover.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="${HOST}/mcu/stm32/03-gpio.html">
${extra}</head><body></body></html>`

test('metaContent 命中并去空白，缺失或空值返回 null', () => {
  assert.equal(metaContent(page(), 'property', 'og:title'), 'S3 GPIO')
  assert.equal(metaContent(page(), 'property', 'og:type'), null)
  assert.equal(metaContent('<meta property="og:title" content="">', 'property', 'og:title'), null)
})

test('canonicalHref 命中', () => {
  assert.equal(canonicalHref(page()), `${HOST}/mcu/stm32/03-gpio.html`)
  assert.equal(canonicalHref('<html></html>'), null)
})

test('完整页面通过检查', () => {
  assert.deepEqual(checkPageHtml(page()), [])
})

test('缺 lang / canonical / og 标签均被点名', () => {
  const noLang = page().replace(' lang="zh-CN"', '')
  assert.deepEqual(checkPageHtml(noLang), ['html[lang="zh-CN"]'])

  const noCanonical = page().replace(/<link rel="canonical"[^>]*>/, '')
  assert.deepEqual(checkPageHtml(noCanonical), ['canonical'])

  const noTwitter = page().replace(/<meta name="twitter:card"[^>]*>/, '')
  assert.deepEqual(checkPageHtml(noTwitter), ['twitter:card'])
})

test('og:image / og:url 必须是绝对 URL', () => {
  const rel = page().replace(`${HOST}/mcu/og-cover.png`, '/mcu/og-cover.png')
  const missing = checkPageHtml(rel)
  assert.equal(missing.length, 1)
  assert.match(missing[0], /og:image.*绝对 URL/)
})

test('sitemap 校验：合法、缺根、丢 base、无条目', () => {
  const ok = `<urlset><url><loc>${HOST}/mcu/</loc></url><url><loc>${HOST}/mcu/a.html</loc></url></urlset>`
  assert.deepEqual(checkSitemap(ok).problems, [])
  assert.equal(checkSitemap(ok).count, 2)
  assert.match(checkSitemap('<urlset></urlset>').problems.join(), /loc/)
  // 关键回归：hostname 忘带 base → 所有 URL 丢 /mcu/ 前缀（线上收录会全错）
  assert.match(
    checkSitemap(`<urlset><url><loc>${HOST}/a.html</loc></url></urlset>`).problems.join(),
    /前缀/,
  )
  assert.match(checkSitemap('<feed></feed>').problems.join(), /urlset/)
})

test('robots 校验：合法与缺项', () => {
  assert.deepEqual(checkRobots(`User-agent: *\nAllow: /\n\nSitemap: ${HOST}/mcu/sitemap.xml\n`), [])
  assert.match(checkRobots('User-agent: *\n').join(), /Allow/)
  assert.match(checkRobots('User-agent: *\nAllow: /\nSitemap: /mcu/sitemap.xml\n').join(), /绝对 URL/)
})
