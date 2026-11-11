import { test } from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'
import { assemble, checkAssetPlacement, parseArgs } from '../scripts/assemble-pages.mjs'

const mk = () => fs.mkdtempSync(path.join(os.tmpdir(), 'assemble-pages-'))

function fixtureDist(files) {
  const root = mk()
  const dist = path.join(root, 'dist')
  for (const [rel, content] of Object.entries(files)) {
    const p = path.join(dist, rel)
    fs.mkdirSync(path.dirname(p), { recursive: true })
    fs.writeFileSync(p, content)
  }
  return { root, dist, out: path.join(root, 'staging') }
}

test('正常组装：根含 mcu/ 子树 + 重定向根入口 + 资源落位校验通过', () => {
  const { dist, out } = fixtureDist({
    'index.html': '<html><head><link rel="stylesheet" href="/STM32/mcu/assets/app.css"><script src="/STM32/mcu/assets/app.js"></script></head><body><div id="app">home</div></body></html>',
    'assets/app.css': 'body{color:red}',
    'assets/app.js': 'console.log(1)',
    'guide/index.html': '<html><a href="/STM32/mcu/assets/app.js">x</a><img src="../assets/app.css"></html>',
  })
  const r = assemble({ dist, out })
  assert.equal(r.ok, true, r.errors.join('; '))
  assert.ok(fs.existsSync(path.join(out, 'mcu', 'index.html')))
  assert.ok(fs.existsSync(path.join(out, 'mcu', 'assets', 'app.css')))
  const root = fs.readFileSync(path.join(out, 'index.html'), 'utf8')
  assert.ok(root.includes('url=./mcu/'), '根入口必须是重定向页')
  assert.ok(root.includes('https://zhuguang-zfg.github.io/STM32/mcu/'), '根入口 canonical 指向新 base')
  assert.notEqual(root, fs.readFileSync(path.join(out, 'mcu', 'index.html'), 'utf8'), '站点首页不得顶到 staging 根')
  assert.ok(r.checked >= 4, `资源引用应全部被校验（实际 ${r.checked}）`)
})

test('失败模式 1：缺 mcu/index.html 必须失败', () => {
  const { dist, out } = fixtureDist({ 'assets/app.js': 'x', '404.html': '<html>404</html>' })
  const r = assemble({ dist, out })
  assert.equal(r.ok, false)
  assert.ok(r.errors.some((e) => e.includes('mcu') && e.includes('index.html')), `应点名缺首页，实际: ${r.errors.join('; ')}`)
})

test('失败模式 2：根入口是重定向页，绝不允许与站点首页同内容', () => {
  // 根入口必须始终是可跳转的重定向页，与站点首页内容相异（防"首页顶到根"回归）
  const { dist, out } = fixtureDist({
    'index.html': '<html><body>站点首页</body></html>',
  })
  const r = assemble({ dist, out })
  assert.equal(r.ok, true, r.errors.join('; '))
  assert.notEqual(fs.readFileSync(path.join(out, 'index.html'), 'utf8'), fs.readFileSync(path.join(out, 'mcu', 'index.html'), 'utf8'))
})

test('失败模式 3a：站内绝对路径不以 /STM32/mcu/ 开头（逃逸到子树外）必须失败', () => {
  const { dist, out } = fixtureDist({
    'index.html': '<html><link rel="stylesheet" href="/assets/legacy.css"></html>',
    'assets/legacy.css': 'x',
  })
  const r = assemble({ dist, out })
  assert.equal(r.ok, false)
  assert.ok(r.errors.some((e) => e.includes('mcu/ 子树之外')), `应点名资源逃逸，实际: ${r.errors.join('; ')}`)
})

test('失败模式 3b：base 前缀资源在 staging 中缺失必须失败', () => {
  const { dist, out } = fixtureDist({
    'index.html': '<html><script src="/STM32/mcu/assets/missing.js"></script></html>',
  })
  const r = assemble({ dist, out })
  assert.equal(r.ok, false)
  assert.ok(r.errors.some((e) => e.includes('missing.js') && e.includes('不存在')), `应点名缺失资源，实际: ${r.errors.join('; ')}`)
})

test('外部与锚点引用不参与落位校验', () => {
  const { dist, out } = fixtureDist({
    'index.html': '<html><a href="https://example.com/x">a</a><a href="#sec">b</a><a href="mailto:x@y.z">c</a><img src="data:image/svg+xml,<svg/>"></html>',
  })
  const r = assemble({ dist, out })
  assert.equal(r.ok, true, r.errors.join('; '))
  assert.equal(r.checked, 0, `外部/锚点/data 引用不应计入（实际 ${r.checked}）`)
})

test('checkAssetPlacement 单独驱动：相对引用缺失也要报', () => {
  const mcuDir = mk()
  fs.mkdirSync(mcuDir, { recursive: true })
  fs.writeFileSync(path.join(mcuDir, 'index.html'), '<html><img src="img/nope.png"></html>')
  const r = checkAssetPlacement(mcuDir)
  assert.ok(r.problems.some((e) => e.includes('img/nope.png')), r.problems.join('; '))
})

test('parseArgs 默认值与覆盖', () => {
  assert.deepEqual(parseArgs([]), { dist: 'site', out: '../.temp/pages-site' })
  assert.deepEqual(parseArgs(['--dist', 'a', '--out', 'b']), { dist: 'a', out: 'b' })
  assert.throws(() => parseArgs(['--bogus']))
})
