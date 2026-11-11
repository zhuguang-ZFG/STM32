import { test } from 'node:test'
import assert from 'node:assert/strict'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { loadConfigFromFile } from 'vite'
import { createMarkdownRenderer } from 'vitepress'

const REPO = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const { config } = await loadConfigFromFile(
  { command: 'build', mode: 'production' },
  path.join(REPO, 'docs/.vitepress/config.mts'),
  REPO,
)
const md = await createMarkdownRenderer(path.join(REPO, 'docs'), config.markdown, '/STM32/mcu/')
const TAG = '<AnimFigure src="/anim/toolchain-relay.svg" />'

function parse(source) {
  return md.parse(source, { relativePath: '__animation-regression.md' })
}

function animations(tokens) {
  return tokens.filter(t => t.type === 'html_block' && t.content.startsWith('<AnimFigure name='))
}

function assertAnimation(tokens, caption = '') {
  const figures = animations(tokens)
  assert.equal(figures.length, 1, '正文应生成一个带内联 SVG 的动画组件')
  assert.match(figures[0].content, /^<AnimFigure name="toolchain-relay" /)
  assert.match(figures[0].content, /markup="[^"]*&lt;svg\b[^"]*&lt;\/svg&gt;[^"]*"/)
  if (caption) assert.ok(figures[0].content.includes(`caption="${caption}"`), '图注应保持字面值并转义属性')
  assert.equal(tokens.some(t => t.type === 'paragraph_open'), false, '独立动画不应嵌在段落中')
}

for (const [name, open, close] of [
  ['反引号', '```vue', '```'],
  ['波浪号', '~~~vue', '~~~'],
  ['长围栏', '````vue', '````'],
]) {
  test(`动画标签在${name}代码围栏内保持原文`, () => {
    const body = `${TAG}\n![原图片语法](/anim/toolchain-relay.svg)\n`
    const tokens = parse(`${open}\n${body}${close}\n`)
    assert.equal(tokens[0].type, 'fence')
    assert.equal(tokens[0].content, body)
    assert.equal(animations(tokens).length, 0)
  })
}

for (const indent of ['    ', '\t']) {
  test(`动画标签在${indent === '\t' ? 'tab' : '四空格'}代码块内保持代码语义`, () => {
    const tokens = parse(`${indent}${TAG}\n`)
    assert.equal(tokens[0].type, 'code_block')
    assert.equal(tokens[0].content, `${TAG}\n`)
    assert.equal(animations(tokens).length, 0)
  })
}

for (const eol of ['\n', '\r\n']) {
  test(`独立动画标签支持${eol === '\n' ? 'LF' : 'CRLF'}与零到三空格缩进`, () => {
    for (let indent = 0; indent < 4; indent++) {
      assertAnimation(parse(`${' '.repeat(indent)}${TAG}${eol}`))
    }
  })
}

test('正文动画与相同代码示例混排时互不污染', () => {
  const tokens = parse(`${TAG}\n\n\`\`\`vue\n${TAG}\n\`\`\`\n\n    ${TAG}\n`)
  assert.equal(animations(tokens).length, 1)
  assert.equal(tokens.find(t => t.type === 'fence')?.content, `${TAG}\n`)
  assert.equal(tokens.find(t => t.type === 'code_block')?.content, `${TAG}\n`)
})

test('可选图注保留中文、Markdown 方括号及属性特殊字符', () => {
  assertAnimation(parse('<AnimFigure src="/anim/toolchain-relay.svg" caption="满]空 & <边界>" />\n'), '满]空 &amp; &lt;边界>')
})

test('既有图片动画继续内联 SVG 和图注', () => {
  assertAnimation(parse('![工具链接力](/anim/toolchain-relay.svg)\n'), '工具链接力')
})

test('与正文同行的组件不被提升为独立动画块', () => {
  const tokens = parse(`前文 ${TAG} 后文\n`)
  assert.equal(animations(tokens).length, 0)
  const inline = tokens.find(t => t.type === 'inline')
  assert.equal(inline.content, `前文 ${TAG} 后文`)
  assert.equal(tokens[0].type, 'paragraph_open')
})

test('HTML 注释中的组件示例保持注释内容', () => {
  const source = `<!--\n${TAG}\n-->\n`
  const tokens = parse(source)
  assert.equal(tokens[0].content, source)
  assert.equal(animations(tokens).length, 0)
})
