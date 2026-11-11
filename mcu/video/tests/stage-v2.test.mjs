import test from 'node:test'
import assert from 'node:assert/strict'
import { openBrowser, openStage } from '../src/stage.mjs'
import { decodeRgba, diffRgba } from '../src/util.mjs'

test('v2 节拍相位真的改变画面', async () => {
  const browser = await openBrowser()
  let stage
  try {
    const scenes = [{ id: 'h', kind: 'hook', title: '上电', sub: '一秒', code: 'A\nB', narration: 'x' }]
    stage = await openStage(browser, { platform: 'probe', size: [1080, 1920], safe: {}, scenes, kicker: 'x', badge: 'T', sections: null, formatVersion: 2, fps: 30 })
    const base = { index: 1, at: 0.5, kind: 'content', targets: ['sub'], revealed: ['title', 'sub'] }
    const a = await stage.capture(0, null, null, 1, 1, { ...base, phase: 0 }, -1)
    const b = await stage.capture(0, null, null, 1, 1, { ...base, phase: 2 }, -1)
    const d = diffRgba(await decodeRgba(a), await decodeRgba(b))
    assert.ok(d.strong > 64, `strong=${d.strong}`)
  } finally {
    if (stage) await stage.close()
    await browser.close()
  }
})
