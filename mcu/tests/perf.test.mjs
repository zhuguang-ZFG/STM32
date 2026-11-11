import { test } from 'node:test'
import assert from 'node:assert/strict'
import { sizeOf, shellAssets, evaluate, BUDGETS } from '../scripts/perf-budget.mjs'

test('sizeOf 返回原文与压缩体积', () => {
  const s = sizeOf(Buffer.from('a'.repeat(1000)))
  assert.equal(s.raw, 1000)
  assert.ok(s.gzip > 0 && s.gzip < s.raw)
  assert.ok(s.brotli <= s.gzip)
})

test('shellAssets 抽取首屏 js/css 并去重', () => {
  const html = `
    <script type="module" src="/mcu/assets/app.abc.js"></script>
    <link rel="modulepreload" href="/mcu/assets/chunks/theme.def.js">
    <link rel="stylesheet" href="/mcu/assets/style.ghi.css">
    <link rel="modulepreload" href="/mcu/assets/chunks/theme.def.js">`
  assert.deepEqual(shellAssets(html).sort(), [
    'assets/app.abc.js',
    'assets/chunks/theme.def.js',
    'assets/style.ghi.css',
  ])
})

const mk = (file, raw, brotli) => ({ file, raw, gzip: brotli, brotli })
const wide = { shellBr: 1e9, cssBr: 1e9, largestChunkBr: 1e9, searchIndexRaw: 1e9 }

test('预算内不报错', () => {
  const assets = [mk('assets/app.a.js', 10, 10), mk('assets/style.b.css', 20, 20)]
  const { breaches } = evaluate({ assets, shell: ['assets/app.a.js', 'assets/style.b.css'], budgets: wide })
  assert.deepEqual(breaches, [])
})

test('超预算被逐项点名（外壳与 CSS 各自独立）', () => {
  const assets = [mk('assets/app.a.js', 10, 10), mk('assets/style.b.css', 500, 500)]
  const { breaches } = evaluate({
    assets,
    shell: ['assets/app.a.js', 'assets/style.b.css'],
    budgets: { shellBr: 100, cssBr: 100, largestChunkBr: 1000, searchIndexRaw: 1e9 },
  })
  const keys = breaches.map((b) => b.key)
  assert.ok(keys.includes('cssBr'), 'CSS 超限应被点名')
  assert.ok(keys.includes('shellBr'), '外壳总量超限应被点名')
})

test('搜索索引原文单独设限', () => {
  const assets = [mk('assets/@localSearchIndexroot.x.js', 5000, 10)]
  const { breaches } = evaluate({ assets, shell: [], budgets: { ...wide, searchIndexRaw: 1000 } })
  assert.deepEqual(breaches.map((b) => b.key), ['searchIndexRaw'])
})

test('预算常量齐备且为正数', () => {
  for (const [k, v] of Object.entries(BUDGETS)) assert.ok(v > 0, `${k} 应为正数`)
})
