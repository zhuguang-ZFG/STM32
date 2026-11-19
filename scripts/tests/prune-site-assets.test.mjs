// 剪枝必须保守：只删确定未被引用的位图，且永不碰 assets/ 与 scenes/。
// 误删会让页面静默丢图，所以这里钉住三类边界。
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

import { findOrphans, pruneSiteAssets } from '../prune-site-assets.mjs'

function makeTree(spec) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'prune-'))
  for (const [rel, content] of Object.entries(spec)) {
    const full = path.join(root, rel)
    fs.mkdirSync(path.dirname(full), { recursive: true })
    fs.writeFileSync(full, content)
  }
  return root
}

test('only unreferenced bitmaps are pruned', () => {
  const root = makeTree({
    'index.html': '<img src="/images/used.png"><img src="/images/inline-only.png">',
    'styles.css': '.hero{background:url(/images/from-css.png)}',
    'images/used.png': 'x',
    'images/inline-only.png': 'x',
    'images/from-css.png': 'x',
    'images/dead.png': 'x',
    'images/dead.svg': '<svg/>',
    'images/notes.txt': 'txt is never pruned',
  })
  try {
    const refs = '<img src="/images/used.png"><img src="/images/inline-only.png">.hero{background:url(/images/from-css.png)}'
    const orphans = findOrphans(root, refs).map((f) => path.relative(root, f).split(path.sep).join('/')).sort()
    assert.deepEqual(orphans, ['images/dead.png', 'images/dead.svg'])
  } finally {
    fs.rmSync(root, { recursive: true, force: true })
  }
})

test('assets/ and scenes/ are never pruned even when unreferenced', () => {
  const root = makeTree({
    'index.html': '<html></html>',
    'assets/bundled.png': 'x',
    'scenes/frame.png': 'x',
    'images/dead.png': 'x',
  })
  try {
    const { removed } = pruneSiteAssets({ dist: root, publicDir: root })
    assert.equal(removed, 1)
    assert.ok(fs.existsSync(path.join(root, 'assets/bundled.png')))
    assert.ok(fs.existsSync(path.join(root, 'scenes/frame.png')))
    assert.ok(!fs.existsSync(path.join(root, 'images/dead.png')))
  } finally {
    fs.rmSync(root, { recursive: true, force: true })
  }
})

test('runtime json and js references protect their images', () => {
  const root = makeTree({
    'index.html': '<html></html>',
    'scenes/stick.json': '{"fallback":"images/scene-fallback.png"}',
    'stick.js': 'const f="images/runtime-frame.png"',
    'images/scene-fallback.png': 'x',
    'images/runtime-frame.png': 'x',
    'images/dead.png': 'x',
  })
  try {
    // publicDir 指向同一棵树，scenes/*.json 与 *.js 都会被读入引用文本
    const { removed, dryRun } = pruneSiteAssets({ dist: root, publicDir: root, dryRun: true })
    assert.equal(removed, 1)
    assert.equal(dryRun, true)
    assert.ok(fs.existsSync(path.join(root, 'images/dead.png')), 'dry-run 不删文件')
  } finally {
    fs.rmSync(root, { recursive: true, force: true })
  }
})
test('bundled dist JS protects the images it builds URLs for', () => {
  const root = makeTree({
    'index.html': '<html></html>',
    'assets/app.abc123.js': 'const src="/STM32/anim/runtime-only.svg"',
    'anim/runtime-only.svg': '<svg/>',
    'images/dead.png': 'x',
  })
  try {
    const orphans = findOrphans(root, '').map((f) => path.relative(root, f))
    // 空引用文本时两者都算孤儿；接入 collectReferences 后只剩真正没人提的那个
    assert.equal(orphans.includes(path.join('images', 'dead.png')), true)
    const { removed } = pruneSiteAssets({ dist: root, publicDir: root })
    assert.equal(removed, 1)
    assert.ok(fs.existsSync(path.join(root, 'anim/runtime-only.svg')), 'bundle 引用的 svg 必须保留')
    assert.ok(!fs.existsSync(path.join(root, 'images/dead.png')))
  } finally {
    fs.rmSync(root, { recursive: true, force: true })
  }
})
