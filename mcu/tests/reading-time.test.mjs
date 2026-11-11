import { test } from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, writeFileSync, rmSync } from 'node:fs'
import { join } from 'node:path'
import { tmpdir } from 'node:os'
import { measure, modelMinutes, calibrate, stripAppendix } from '../scripts/reading-time.mjs'

const page = (body, minutes = 30) => `---\ntitle: T\nstatus: done\nminutes: ${minutes}\n---\n${body}`

test('正文与代码分开计数，空白不算字', () => {
  const m = measure(page('中文 正文\n\n```c\nint a = 1;\n```\n'))
  assert.equal(m.meta.minutes, '30')
  assert.equal(m.prose, 4)
  assert.equal(m.code, '```cinta=1;```'.length)
})

test('HTML 标签不跨行吞正文（曾把 <<< 到下一个 > 之间的整段当成标签）', () => {
  const m = measure(page('<AnimFigure name="x" />\n一二三\n<<< ./missing.c\n四五六 a > b'))
  assert.equal(m.prose, '一二三四五六a>b'.length)
})

test('<<< 引入的外部文件按代码计，读不到的文件记 0 而不是报错', () => {
  const dir = mkdtempSync(join(tmpdir(), 'rt-'))
  try {
    writeFileSync(join(dir, 'probe.c'), 'int main(void) { return 0; }\n')
    const file = join(dir, 'ch.md')
    const m = measure(page('正文\n\n<<< ./probe.c\n\n<<< ./nope.c\n'), file)
    assert.equal(m.code, 'intmain(void){return0;}'.length)
    assert.equal(m.prose, 2)
  } finally {
    rmSync(dir, { recursive: true, force: true })
  }
})

test('「## 附录…」整节不计，到下一个二级标题为止；代码块里的 ## 不当标题', () => {
  const body = '## 正文\n甲\n## 附录：工程完整源码\n乙乙乙\n```sh\n## 记忆锚点\n```\n丙\n## 记忆锚点\n丁'
  const kept = stripAppendix(body)
  assert.match(kept, /甲/)
  assert.doesNotMatch(kept, /乙|丙/)
  assert.match(kept, /丁/)
})

test('模型：正文/300 + 代码/150 + 10，取整到 5，最少 15', () => {
  assert.equal(modelMinutes({ prose: 0, code: 0 }), 15)
  assert.equal(modelMinutes({ prose: 6000, code: 1500 }), 40)
  assert.equal(modelMinutes({ prose: 9000, code: 0 }), 40)
})

test('偏离 ±40% 才算离群；building 与无 minutes 的页不参与', () => {
  const p = (minutes, status = 'done') => ({ meta: { status, minutes: String(minutes) }, prose: 6000, code: 1500 })
  const rows = calibrate([p(40), p(56), p(57), p(24), p(23), p(90, 'building'), p(0)])
  assert.deepEqual(rows.map((r) => r.outlier), [false, false, true, false, true])
})
