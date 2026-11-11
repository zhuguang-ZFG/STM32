import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import MiniSearch from 'minisearch'
import {
  harvestEntries,
  checkSearchHits,
  plainHeading,
  pageHrefPaths,
} from '../scripts/search-check.mjs'
import { tokenizeForSearch } from '../scripts/search-tokenize.mjs'

/** 用临时目录造假 docs：键是 posix 相对路径，值是 markdown 原文。 */
function makeDocs(files) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'search-check-'))
  for (const [rel, md] of Object.entries(files)) {
    const abs = path.join(dir, rel)
    fs.mkdirSync(path.dirname(abs), { recursive: true })
    fs.writeFileSync(abs, md)
  }
  return dir
}

const rm = (dir) => fs.rmSync(dir, { recursive: true, force: true })

/** 造一个「产物索引」：tokenize 传 null 表示用 MiniSearch 默认分词（模拟 config 被改坏）。 */
function makeIndex(docs, { tokenize = tokenizeForSearch } = {}) {
  const ms = new MiniSearch({
    fields: ['title', 'titles', 'text'],
    storeFields: ['title', 'titles'],
    ...(tokenize ? { tokenize } : {}),
  })
  ms.addAll(docs)
  return ms.toJSON()
}

test('plainHeading 对齐渲染后词面：自定义锚点 / 链接 / 行内标记 / html', () => {
  assert.equal(plainHeading('自定义锚点 {#my-id}'), '自定义锚点')
  assert.equal(plainHeading('代码 `BSRR` 与 **加粗**'), '代码 BSRR 与 加粗')
  assert.equal(plainHeading('看 [术语页](./glossary.md) 再回来'), '看 术语页 再回来')
  assert.equal(plainHeading('比较 A <B> 与 C'), '比较 A  与 C')
})

test('pageHrefPaths：普通页用 .html，index 页用目录式 URL 与 index.html 双形态', () => {
  assert.deepEqual(pageHrefPaths('stm32/12-spi.md'), ['/mcu/stm32/12-spi.html'])
  assert.deepEqual(pageHrefPaths('build/index.md'), ['/mcu/build/', '/mcu/build/index.html'])
  assert.deepEqual(pageHrefPaths('index.md'), ['/mcu/', '/mcu/index.html'])
})

test('checkSearchHits：目录页不能被同目录下的子页面冒充（全等而非前缀）', () => {
  const index = makeIndex([
    { id: '/mcu/build/00-toolchain.html#学习目标', title: '工具链', titles: ['学习目标'], text: '章节路线导览' },
  ])
  const { missing } = checkSearchHits(index, [{ term: '章节路线导览', page: 'build/index.md' }])
  assert.equal(missing.length, 1, '命中的是 build/00-toolchain.html，不是导览页本身，必须判红')
})

test('checkSearchHits：排在很后面也算可达（本门判可达性，不判排序）', () => {
  // 通用标题（「小节结构」这类）的目标页常常排在第 20 名之外；设截断会把它判成缺陷（实测 715/2147 噪声）
  const docs = []
  for (let i = 0; i < 5; i++) {
    docs.push({ id: `/mcu/x/page${i}.html#s`, title: '共同词 目标', titles: ['共同词'], text: '共同词 共同词' })
  }
  const index = makeIndex(docs)
  assert.deepEqual(checkSearchHits(index, [{ term: '共同词', page: 'x/page4.md' }]).missing, [])
})

test('harvestEntries：采 title + H2/H3，跳过围栏/四级/空子树/无 H1 的 title', () => {
  const dir = makeDocs({
    'demo.md': [
      '---',
      'title: 演示页',
      '---',
      '',
      '# 演示页',
      '',
      '## 有正文的小节',
      '正文',
      '',
      '## 只嵌套标题',
      '### 子标题有正文',
      '正文',
      '',
      '#### 四级不进',
      '',
      '```md',
      '## 围栏里的假标题',
      '```',
      '',
      '## 真空白小节',
      '',
      '',
    ].join('\n'),
    'home.md': ['---', 'title: 首页', 'layout: home', '---', '', '没有一级标题'].join('\n'),
  })
  try {
    const entries = harvestEntries(dir)
    const terms = entries.map((e) => e.term)
    assert.ok(terms.includes('演示页'), 'H1 存在的页面 title 要采')
    assert.ok(terms.includes('有正文的小节'))
    assert.ok(terms.includes('只嵌套标题'), '子树里有正文时，父标题随标题链进索引')
    assert.ok(!terms.includes('真空白小节'), '整棵子树无正文的小节不在索引里，采了必误报')
    assert.ok(!terms.includes('四级不进'), '只采 H2/H3')
    assert.ok(!terms.includes('围栏里的假标题'))
    assert.ok(!terms.includes('首页'), '无 H1 的页面 title 不在索引里')
    assert.deepEqual(entries.find((e) => e.term === '有正文的小节').page, 'demo.md')
  } finally {
    rm(dir)
  }
})

test('harvestEntries：frontmatter search:false 的页面整体跳过', () => {
  const dir = makeDocs({
    'skip.md': ['---', 'title: 不索引页', 'search: false', '---', '', '# 不索引页', '', '## 小节', '正文'].join('\n'),
    'keep.md': ['---', 'title: 索引页', '---', '', '# 索引页', '', '## 小节', '正文'].join('\n'),
  })
  try {
    const pages = new Set(harvestEntries(dir).map((e) => e.page))
    assert.ok(!pages.has('skip.md'))
    assert.ok(pages.has('keep.md'))
  } finally {
    rm(dir)
  }
})

test('checkSearchHits：索引与查询同口径时，标题都能翻到自己那一页', () => {
  const index = makeIndex([
    {
      id: '/mcu/stm32/12-spi.html#移位艺术',
      title: 'S12 SPI',
      titles: ['S12 SPI', '四根线的全双工移位'],
      text: '全双工的移位艺术',
    },
    { id: '/mcu/rtos/index.html#章节路线', title: 'RTOS', titles: ['RTOS', '章节路线'], text: '章节路线' },
  ])
  const { missing, checked } = checkSearchHits(index, [
    { term: '四根线的全双工移位', page: 'stm32/12-spi.md' },
    { term: '章节路线', page: 'rtos/index.md' },
  ])
  assert.deepEqual(missing, [])
  assert.equal(checked, 2)
})

test('checkSearchHits：翻不到自己那页必须点名（页面串到别处也算失败）', () => {
  const index = makeIndex([
    { id: '/mcu/other.html#x', title: '别页', titles: ['别页'], text: '全双工的移位艺术' },
  ])
  const { missing } = checkSearchHits(index, [{ term: '四根线的全双工移位', page: 'stm32/12-spi.md' }])
  assert.equal(missing.length, 1)
  assert.equal(missing[0].page, 'stm32/12-spi.md')
})

test('checkSearchHits：索引被默认分词建过（config 少 tokenize）时必须判红', () => {
  const docs = [
    {
      id: '/mcu/stm32/12-spi.html#x',
      title: 'S12 SPI',
      titles: ['S12 SPI'],
      text: '全双工的移位艺术，中文整段会成为单个 token',
    },
  ]
  const good = checkSearchHits(makeIndex(docs), [{ term: '全双工的移位艺术', page: 'stm32/12-spi.md' }])
  assert.deepEqual(good.missing, [], '同口径时应当命中')

  const broken = checkSearchHits(makeIndex(docs, { tokenize: null }), [
    { term: '全双工的移位艺术', page: 'stm32/12-spi.md' },
  ])
  assert.equal(broken.missing.length, 1, '索引与查询口径不一致时必须判红')
})