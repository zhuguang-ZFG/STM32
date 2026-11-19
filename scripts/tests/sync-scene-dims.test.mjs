// 场景回退图尺寸必须来自 PNG 头本身，不能手填：手填会在换图后静默错位，
// 而无 JS 读者只会看到一块跳动的图。
import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

import { checkSceneDims, collectDims, pngSize, writeSceneDims } from '../sync-scene-dims.mjs'

/** 最小合法 PNG 头：签名 + IHDR，尺寸写在偏移 16/20。 */
function pngHeader(width, height) {
  const buf = Buffer.alloc(33)
  Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]).copy(buf, 0)
  buf.writeUInt32BE(13, 8)
  buf.write('IHDR', 12, 'ascii')
  buf.writeUInt32BE(width, 16)
  buf.writeUInt32BE(height, 20)
  return buf
}

function makeTree() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'scene-dims-'))
  fs.mkdirSync(path.join(root, 'images'), { recursive: true })
  fs.writeFileSync(path.join(root, 'images/a.png'), pngHeader(720, 460))
  fs.writeFileSync(path.join(root, 'images/b.png'), pngHeader(1000, 500))
  fs.writeFileSync(
    path.join(root, 'scenes.json'),
    JSON.stringify({
      a: { fallback: '/images/a.png' },
      b: { fallback: '/images/b.png' },
    }),
  )
  return root
}

test('pngSize reads the IHDR dimensions', () => {
  const root = makeTree()
  try {
    assert.deepEqual(pngSize(path.join(root, 'images/a.png')), [720, 460])
  } finally {
    fs.rmSync(root, { recursive: true, force: true })
  }
})

test('writeSceneDims fills sizes and checkSceneDims then passes', () => {
  const root = makeTree()
  try {
    const json = path.join(root, 'scenes.json')
    const publicDir = root
    assert.equal(checkSceneDims({ json, publicDir }).ok, false, '缺尺寸时不应通过')

    writeSceneDims({ json, publicDir })
    const scenes = JSON.parse(fs.readFileSync(json, 'utf8'))
    assert.equal(scenes.a.width, 720)
    assert.equal(scenes.b.height, 500)
    assert.deepEqual(checkSceneDims({ json, publicDir }), { ok: true, missing: [], drift: [], count: 2 })

    // 换图后尺寸漂移必须失败
    fs.writeFileSync(path.join(root, 'images/a.png'), pngHeader(800, 460))
    const drift = checkSceneDims({ json, publicDir })
    assert.equal(drift.ok, false)
    assert.match(drift.drift[0], /期望 800x460/)
  } finally {
    fs.rmSync(root, { recursive: true, force: true })
  }
})

test('collectDims reports a missing fallback instead of guessing', () => {
  const root = makeTree()
  try {
    const { dims, missing } = collectDims({ x: {} }, root)
    assert.deepEqual(dims, {})
    assert.match(missing[0], /没有 fallback/)
  } finally {
    fs.rmSync(root, { recursive: true, force: true })
  }
})