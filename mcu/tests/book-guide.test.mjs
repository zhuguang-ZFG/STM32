import { test } from 'node:test'
import assert from 'node:assert/strict'
import { checkGuide, sha } from '../scripts/book-guide/contract.mjs'

const page = body => `<!doctype html><html lang="zh-CN"><head><link rel="canonical" href="https://example.com/mcu/reference/book.html"><meta property="og:title" content="书籍导读"><meta property="og:description" content="导读"><meta property="og:url" content="https://example.com/mcu/book-guide/"><meta property="og:image" content="https://example.com/mcu/cover.png"><meta name="twitter:card" content="summary_large_image"></head><body><main><h1>书籍导读</h1>${body}</main></body></html>`
const input = (html = page('')) => ({ html, sourceHash: 'source', generatorHash: 'generator', manifest: { sourceHash: 'source', generatorHash: 'generator', htmlHash: sha(html) } })

test('book guide accepts valid output and external GitHub Markdown links', () => {
  assert.deepEqual(checkGuide(input(page('<a href="https://github.com/owner/project/blob/main/README.md">源文</a>'))), [])
})
test('book guide refuses stale source and generator independently', () => {
  for (const field of ['sourceHash', 'generatorHash']) {
    const fixture = input()
    fixture[field] = 'changed'
    assert.match(checkGuide(fixture).join('\n'), /stale/)
  }
})
test('book guide refuses an HTML edit even if source did not change', () => {
  const fixture = input()
  fixture.html = fixture.html.replace('书籍导读</h1>', '过期副本</h1>')
  assert.match(checkGuide(fixture).join('\n'), /differs/)
})
test('book guide refuses local Markdown URLs and external font/image dependencies', () => {
  const fixture = input(page('<a href="../reference/book.md#x">入口</a><img src="https://example.com/default.jpg" alt="板卡">'))
  const errors = checkGuide(fixture)
  assert.ok(errors.includes('unresolved Markdown link'))
  assert.ok(errors.includes('external image/font dependency'))
})
test('book guide refuses editable published text and missing metadata or landmark', () => {
  const fixture = input(page('<p contenteditable="true">内容</p>').replace('<main>', '<div>').replace('</main>', '</div>').replace('property="og:title"', 'property="other"'))
  const errors = checkGuide(fixture)
  assert.ok(errors.includes('published content is editable'))
  assert.ok(errors.includes('no main/VPContent landmark'))
  assert.ok(errors.includes('og:title'))
})
