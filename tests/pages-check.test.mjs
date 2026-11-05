import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import {
  collectDistAnchors,
  checkDistAnchors,
  resolveHref,
} from '../scripts/pages-check.mjs'

/** 用临时目录造假 dist：键是 posix 相对路径，值是 html 原文。 */
function makeDist(files) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'pages-check-'))
  for (const [rel, html] of Object.entries(files)) {
    const abs = path.join(dir, ...rel.split('/'))
    fs.mkdirSync(path.dirname(abs), { recursive: true })
    fs.writeFileSync(abs, html)
  }
  return dir
}

const rm = (dir) => fs.rmSync(dir, { recursive: true, force: true })

const PAGE = (body, ids = []) =>
  `<!doctype html><html><head></head><body>${ids.map((i) => `<h2 id="${i}">t</h2>`).join('')}${body}</body></html>`

test('collectDistAnchors 收集每页 id，键为 posix 相对路径', () => {
  const dir = makeDist({
    'index.html': PAGE('', ['top', '首页']),
    'sub/page.html': PAGE('', ['sec-一']),
  })
  try {
    const anchors = collectDistAnchors(dir)
    assert.deepEqual([...anchors.keys()].sort(), ['index.html', 'sub/page.html'])
    assert.ok(anchors.get('index.html').has('首页'))
    assert.ok(anchors.get('sub/page.html').has('sec-一'))
    assert.equal(anchors.get('sub/page.html').has('不存在'), false)
  } finally {
    rm(dir)
  }
})

test('resolveHref：外链 / 协议相对 / 纯# / 空锚点 / 无锚点 / 非 html 资产都不查', () => {
  const from = 'stm32/03-gpio.html'
  assert.equal(resolveHref('https://a.com/x.html#f', from), null)
  assert.equal(resolveHref('http://a.com/#f', from), null)
  assert.equal(resolveHref('mailto:a@b.c', from), null)
  assert.equal(resolveHref('//a.com/x.html#f', from), null)
  assert.equal(resolveHref('#', from), null)
  assert.equal(resolveHref('', from), null)
  assert.equal(resolveHref('a.html#', from), null) // 空锚点
  assert.equal(resolveHref('a.html', from), null) // 无锚点
  assert.equal(resolveHref('/mcu/anim/x.svg#v', from), null) // 资产内部语义，不是页面锚点
})

test('resolveHref：同页锚点、base 绝对路径、裸 base、目录、相对路径、query', () => {
  const from = 'stm32/03-gpio.html'
  assert.deepEqual(resolveHref('#vp', from), { target: from, fragment: 'vp' })
  assert.deepEqual(resolveHref('/mcu/c/01.html#栈', from), { target: 'c/01.html', fragment: '栈' })
  assert.deepEqual(resolveHref('/mcu/#hero', from), { target: 'index.html', fragment: 'hero' })
  assert.deepEqual(resolveHref('/mcu#hero', from), { target: 'index.html', fragment: 'hero' })
  assert.deepEqual(resolveHref('/mcu/guide/#开始', from), {
    target: 'guide/index.html',
    fragment: '开始',
  })
  assert.deepEqual(resolveHref('./02-rcc.html#pll', from), {
    target: 'stm32/02-rcc.html',
    fragment: 'pll',
  })
  assert.deepEqual(resolveHref('../c/01-memory.html#模型', from), {
    target: 'c/01-memory.html',
    fragment: '模型',
  })
  assert.deepEqual(resolveHref('04-nvic.html?x=1#中断', from), {
    target: 'stm32/04-nvic.html',
    fragment: '中断',
  })
})

test('checkDistAnchors：同页 / 跨页 / base / 目录 / query 全过', () => {
  const dir = makeDist({
    'index.html': PAGE(
      [
        '<a href="#top">x</a>',
        '<a href="sub/page.html#sec-一">x</a>',
        '<a href="/mcu/sub/page.html#sec-一">x</a>',
        '<a href="/mcu/#首页">x</a>',
        '<a href="sub/page.html?q=1#sec-一">x</a>',
        '<a href="https://a.com/x.html#whatever">x</a>',
        '<a href="#">x</a>',
        '<a href="sub/page.html">x</a>',
      ].join(''),
      ['top', '首页'],
    ),
    'sub/page.html': PAGE('<a href="/mcu/index.html#top">x</a>', ['sec-一']),
  })
  try {
    const { problems, checked, pages } = checkDistAnchors(dir)
    assert.deepEqual(problems, [])
    assert.equal(checked, 6) // 外链 / 纯# / 无锚点不计
    assert.equal(pages, 2)
  } finally {
    rm(dir)
  }
})

test('checkDistAnchors：目标文件不存在被逐条点名', () => {
  const dir = makeDist({
    'index.html': PAGE('<a href="ghost.html#x">x</a>\n<a href="sub/page.html#ok">x</a>'),
    'sub/page.html': PAGE('', ['ok']),
  })
  try {
    const { problems, checked } = checkDistAnchors(dir)
    assert.equal(checked, 2)
    assert.equal(problems.length, 1)
    assert.match(problems[0], /^index\.html:1 → href "ghost\.html#x"/)
    assert.match(problems[0], /ghost\.html.*不存在/)
  } finally {
    rm(dir)
  }
})

test('checkDistAnchors：锚点 id 缺失报「期望 vs 实际」', () => {
  const dir = makeDist({
    'index.html': PAGE('<a href="sub/page.html#旧锚点">x</a>'),
    'sub/page.html': PAGE('', ['新锚点']),
  })
  try {
    const { problems } = checkDistAnchors(dir)
    assert.equal(problems.length, 1)
    assert.match(problems[0], /期望 sub\/page\.html 含 id="旧锚点"，实际不存在/)
  } finally {
    rm(dir)
  }
})

test('checkDistAnchors：base 外的绝对路径直接判错（不许映射进站内当巧合通过）', () => {
  const dir = makeDist({
    'index.html': PAGE('<a href="/other/x.html#f">x</a>'),
    // 故意让同名文件存在：早期实现会把 "/other/x.html#f" 当站内路径查到它，从而假绿
    'other/x.html': PAGE('<h2 id="f">f</h2>'),
  })
  try {
    const { problems } = checkDistAnchors(dir)
    assert.equal(problems.length, 1)
    assert.match(problems[0], /BASE/)
    assert.match(problems[0], /other\/x\.html/)
  } finally {
    rm(dir)
  }
})

test('checkDistAnchors：脚本与样式里的 href 选择器不计链接，真实错误保持原行号', () => {
  const dir = makeDist({
    'index.html': PAGE([
      '<script>',
      `const active = panel.querySelector('a[href="#'+entry.target.id+'"]');`,
      '</script>',
      '<style>a[href="#style-only"] { color: blue }</style>',
      '<a href="#real">真实链接</a>',
      '<a href="#missing">真实错误</a>',
    ].join('\n'), ['real']),
  })
  try {
    const { problems, checked } = checkDistAnchors(dir)
    assert.equal(checked, 2)
    assert.equal(problems.length, 1)
    assert.match(problems[0], /^index\.html:6 → href "#missing"/)
  } finally {
    rm(dir)
  }
})
