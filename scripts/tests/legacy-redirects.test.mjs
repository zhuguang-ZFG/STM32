import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtemp, readFile, rm } from 'node:fs/promises'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { fileURLToPath } from 'node:url'

import { generate, oldUrlFor } from '../legacy-redirects.mjs'

const ROOT = fileURLToPath(new URL('../../', import.meta.url))
const mappingPath = join(ROOT, 'plans/2026-11-12-merged-book/mapping.json')
const manifestPath = join(ROOT, 'docs/manifest.json')

test('old URL keeps mcu prefix and .html suffix', () => {
  assert.equal(oldUrlFor('mcu/docs/stm32/03-gpio.md'), '/mcu/stm32/03-gpio.html')
})

test('generates one stub per legacy page with canonical target', async () => {
  const outDir = await mkdtemp(join(tmpdir(), 'legacy-redirects-'))
  try {
    const count = await generate({ mappingPath, manifestPath, outDir })
    assert.equal(count, 131)
    const html = await readFile(join(outDir, 'mcu/stm32/03-gpio.html'), 'utf8')
    assert.match(html, /rel="canonical" href="https:\/\/zhuguang-zfg\.github\.io\/STM32\/v1-drivers\/09-gpio\.html"/)
    assert.match(html, /http-equiv="refresh" content="0; url=\/STM32\/v1-drivers\/09-gpio\.html"/)
    assert.match(html, /location\.replace\("\/STM32\/v1-drivers\/09-gpio\.html" \+ location\.hash\)/)
  } finally {
    await rm(outDir, { recursive: true, force: true })
  }
})
