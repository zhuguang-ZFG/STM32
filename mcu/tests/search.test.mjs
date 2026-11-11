import { test } from 'node:test'
import assert from 'node:assert/strict'
import { renderSearch } from '../scripts/search-render.mjs'
import { tokenizeForSearch, isCjk } from '../scripts/search-tokenize.mjs'
import { checkSearchIndex, parseSearchIndexChunk } from '../scripts/seo-check.mjs'
import { createHighlighter } from 'shiki'
import { codeLanguages } from '../docs/.vitepress/code-languages.mjs'

test('search preserves explanatory text and inline names but omits source dumps', () => {
  const md = { render: () => '<h2>I2C</h2><p>Call <code>read_reg</code></p><pre><code>long source</code></pre>' }
  const result = renderSearch('', {}, md)
  assert.match(result, /read_reg/)
  assert.doesNotMatch(result, /long source/)
  assert.equal(renderSearch('', {frontmatter:{search:false}}, md), '')
})
// —— 中文分词 ——
// 回归背景：MiniSearch 默认按空白/标点切词，整段中文被当成 1 个 token，
// 只有段首词能靠 prefix 命中——实测搜「优先级反转」「上下文切换」0 结果。
test('纯 ASCII 片段整体保留，不破坏标识符', () => {
  assert.deepEqual(tokenizeForSearch('GPIO FreeRTOS MODER'), ['GPIO', 'FreeRTOS', 'MODER'])
  assert.deepEqual(tokenizeForSearch('0x40021418'), ['0x40021418'])
})

test('连续中文切成二元组：句中的词也能被检索到', () => {
  assert.deepEqual(tokenizeForSearch('优先级反转'), ['优先', '先级', '级反', '反转'])
  const toks = tokenizeForSearch('GPIO 有七个寄存器')
  assert.ok(toks.includes('寄存') && toks.includes('存器'), toks.join(','))
})

test('中英混排按语种切分', () => {
  const toks = tokenizeForSearch('S2 RCC 时钟树')
  assert.ok(toks.includes('RCC') && toks.includes('时钟'), toks.join(','))
})

test('单字片段保留单字，空值不炸', () => {
  assert.deepEqual(tokenizeForSearch('栈'), ['栈'])
  assert.deepEqual(tokenizeForSearch(null), [])
})

test('isCjk 边界', () => {
  assert.equal(isCjk('时'), true)
  assert.equal(isCjk('A'), false)
  assert.equal(isCjk(''), false)
})

test('索引闸门：二元组不足即报错（防 tokenize 被误删）', () => {
  const ok = { index: [['时钟', {}], ['寄存', {}], ['存器', {}]] }
  assert.deepEqual(checkSearchIndex(ok, 3).problems, [])
  assert.equal(checkSearchIndex(ok, 3).bigram, 3)
  // 反例：退回默认分词——整段中文是 1 个超长 token，没有二元组
  const broken = { index: [['时钟树是晶振经分频倍频分配', {}], ['GPIO', {}]] }
  assert.match(checkSearchIndex(broken, 3).problems.join(), /静默失效/)
})

test('解析索引 chunk：取得到 JSON，非该形态返回 null', () => {
  const src = `const t='{"index":[["时钟",{"2":{"1":1}}]],"documentCount":1}';export{t as default};`
  assert.equal(parseSearchIndexChunk(src).documentCount, 1)
  assert.equal(parseSearchIndexChunk('export default 42'), null)
})

test('linker and gdb code have actual highlighted tokens', async () => {
  const h = await createHighlighter({themes:['github-light'],langs:codeLanguages})
  for (const [lang, code] of [['ld','SECTIONS { .text : { *(.text*) } }'],['gdb','break main\nx/4wx 0x08000000']]) {
    const html=h.codeToHtml(code,{lang,theme:'github-light'})
    assert.match(html, /style="color:/)
  }
  h.dispose()
})
