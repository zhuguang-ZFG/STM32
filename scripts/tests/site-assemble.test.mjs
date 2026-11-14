import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

import { assemble, parseArgs } from '../site-assemble.mjs'

test('assemble asserts root index and stub coverage', async () => {
  const dist = await mkdtemp(join(tmpdir(), 'b5-dist-'))
  const stubs = await mkdtemp(join(tmpdir(), 'b5-stubs-'))
  const out = await mkdtemp(join(tmpdir(), 'b5-out-'))
  try {
    await assert.rejects(
      async () => assemble({ dist, stubs, out }),
      (err) => err.message.includes('根 index.html 不存在') && err.message.includes('覆盖率不足')
    )
    await mkdir(dist, { recursive: true })
    await writeFile(join(dist, 'index.html'), '<html><body>book home</body></html>')
    await mkdir(join(stubs, 'mcu'), { recursive: true })
    for (let i = 0; i < 10; i += 1) {
      await writeFile(join(stubs, 'mcu', `page-${i}.html`), '<meta http-equiv="refresh" content="0; url=/STM32/">')
    }
    await assert.rejects(
      async () => assemble({ dist, stubs, out }),
      (err) => err.message.includes('覆盖率不足')
    )
    for (let i = 10; i < 132; i += 1) {
      await writeFile(join(stubs, 'mcu', `page-${i}.html`), '<meta http-equiv="refresh" content="0; url=/STM32/">')
    }
    const { stubCount } = assemble({ dist, stubs, out })
    assert.equal(stubCount, 132)
    const staged = await readFile(join(out, 'index.html'), 'utf8')
    assert.match(staged, /book home/)
    const stubHtml = await readFile(join(out, 'mcu', 'page-0.html'), 'utf8')
    assert.match(stubHtml, /meta http-equiv="refresh"/)
  } finally {
    await rm(dist, { recursive: true, force: true })
    await rm(stubs, { recursive: true, force: true })
    await rm(out, { recursive: true, force: true })
  }
})

test('assemble rejects non-stub pages under mcu/', async () => {
  const dist = await mkdtemp(join(tmpdir(), 'b5-dist2-'))
  const stubs = await mkdtemp(join(tmpdir(), 'b5-stubs2-'))
  const out = await mkdtemp(join(tmpdir(), 'b5-out2-'))
  try {
    await mkdir(dist, { recursive: true })
    await writeFile(join(dist, 'index.html'), '<html><body>book home</body></html>')
    await mkdir(join(stubs, 'mcu', 'rtos'), { recursive: true })
    for (let i = 0; i < 131; i += 1) {
      const sub = i % 2 === 0 ? '' : 'rtos/'
      await writeFile(join(stubs, 'mcu', sub, `page-${i}.html`), '<meta http-equiv="refresh" content="0; url=/STM32/">')
    }
    await writeFile(join(stubs, 'mcu', 'rtos', 'real.html'), '<html><body>real body</body></html>')
    await assert.rejects(
      async () => assemble({ dist, stubs, out }),
      (err) => err.message.includes('非存根页面')
    )
  } finally {
    await rm(dist, { recursive: true, force: true })
    await rm(stubs, { recursive: true, force: true })
    await rm(out, { recursive: true, force: true })
  }
})

test('parseArgs defaults', () => {
  const args = parseArgs([])
  assert.equal(args.dist, 'book/dist/site')
  assert.equal(args.out, '.temp/pages-site')
})
