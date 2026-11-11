import { test } from 'node:test'
import assert from 'node:assert/strict'
import { attr, textContent, auditPage } from '../scripts/a11y-check.mjs'

const page = (extra = '') => `<!doctype html><html lang="zh-CN"><head><title>T</title></head>
<body><div id="VPContent"><h1>Title</h1>
<img src="/a.png" alt="desc">
<button aria-label="ok">Go</button>
<a href="/b">Link text</a>
${extra}</div></body></html>`

test('attr 命中与缺失', () => {
  assert.equal(attr('<img alt="x" src="y">', 'alt'), 'x')
  assert.equal(attr('<img src="y">', 'alt'), null)
})

test('textContent 去标签与空白归一', () => {
  assert.equal(textContent('  hello <b>world</b>  '), 'hello world')
})

test('完整页面通过审计', () => {
  assert.deepEqual(auditPage(page()), [])
})

test('缺 lang、img alt、button name、link text、h1、landmark 均被点名', () => {
  assert.deepEqual(auditPage(page().replace(' lang="zh-CN"', '')), ['html[lang]'])
  assert.deepEqual(auditPage(page().replace('alt="desc"', '')), ['img missing alt'])
  assert.deepEqual(auditPage(page() + '<button> </button>'), ['button missing name'])
  assert.deepEqual(auditPage(page() + '<a href="/x"></a>'), ['link missing text'])
  assert.deepEqual(auditPage(page().replace('<h1>', '<h2>')), ['no h1'])
  assert.deepEqual(
    auditPage(page().replace('id="VPContent"', 'id="Other"').replace('<main', '<div')),
    ['no main/VPContent landmark'],
  )
})

test('VPSwitchAppearance 按钮被跳过（框架级责任）', () => {
  const html = page() + '<button class="VPSwitch VPSwitchAppearance" type="button" role="switch" title></button>'
  assert.deepEqual(auditPage(html), [])
})

test('aria-label 与 title 均可作为按钮/链接的可访问名', () => {
  const html = page() + '<button title="Copy">x</button><a href="/" title="Home"></a>'
  assert.deepEqual(auditPage(html), [])
})
