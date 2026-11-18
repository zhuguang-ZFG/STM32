// 站点配置不变量：base / 侧栏全覆盖 / 锚点 slug 与 Python 逐字一致。
// 这些值一旦漂移，旧链存根与正文里的 .md#anchor 会在无声中失效。
import test from 'node:test'
import assert from 'node:assert/strict'

import {
  BASE,
  SITE_URL,
  buildNav,
  buildSidebar,
  cjkTokenize,
  manifest,
  slugify,
} from '../../docs/.vitepress/book.mts'

test('base is the documented Pages mount', () => {
  assert.equal(BASE, '/STM32/')
  assert.equal(SITE_URL, 'https://zhuguang-zfg.github.io/STM32/')
})

// 侧栏链接不带 .html：cleanUrls=false 时 VitePress 在渲染阶段补扩展名
// （构建产物已验证为 /STM32/v1-drivers/09-gpio.html）。
test('sidebar covers every chapter and appendix', () => {
  const sidebar = buildSidebar()
  const links = sidebar.flatMap((group) => group.items.map((item) => item.link))
  const chapters = manifest.parts.flatMap((part) => part.chapters)
  const appendices = manifest.appendices
  assert.equal(chapters.length, 47)
  assert.equal(appendices.length, 6)
  assert.equal(links.length, 53)
  const files = new Set([
    ...chapters.map((chapter) => '/' + chapter.file.replace(/\.md$/, '')),
    ...appendices.map((appendix) => '/' + appendix.file.replace(/\.md$/, '')),
  ])
  for (const link of links) assert.ok(files.has(link), `sidebar link not in manifest: ${link}`)
})

test('nav exposes parts, appendix and source', () => {
  const nav = buildNav()
  assert.equal(nav.length, 4)
  assert.equal(nav[0].text, '首页')
  const volumes = nav.find((item) => item.text === '卷册')
  assert.equal(volumes.items.length, manifest.parts.length)
  assert.ok(nav.some((item) => item.text === '附录'))
  assert.equal(nav.at(-1).link, 'https://github.com/zhuguang-ZFG/STM32')
})

// 期望值来自 book/checks.py:cjk_slugify（同一组输入跑 Python 得到），
// 锚点由 checks.py 校验，所以两边必须逐字相同。
test('slugify matches book/checks.py cjk_slugify', () => {
  const cases = [
    ['3.2 卷册与章目（46 章）', '32-卷册与章目46-章'],
    ['机制', '机制'],
    ['栈帧：push {r4, lr} … pop {r4, pc}', '栈帧push-r4-lr-pop-r4-pc'],
    ['__init__', '__init__'],
    ['1.5V 供电', '15v-供电'],
    ['   ', 'section'],
  ]
  for (const [input, expected] of cases) {
    assert.equal(slugify(input), expected, `slugify(${JSON.stringify(input)})`)
  }
})

test('search tokenizer segments Chinese and keeps latin words', () => {
  const tokens = cjkTokenize('中断处理与 NVIC 优先级')
  assert.ok(tokens.includes('中'))
  assert.ok(tokens.includes('断'))
  assert.ok(tokens.includes('nvic') || tokens.includes('NVIC'), tokens.join(','))
  assert.ok(tokens.includes('优先级') || tokens.includes('优'), tokens.join(','))
})