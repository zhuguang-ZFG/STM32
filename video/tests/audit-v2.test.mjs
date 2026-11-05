import test from 'node:test'
import assert from 'node:assert/strict'
import { validateBeats } from '../src/timeline.mjs'
import { openBrowser, openStage } from '../src/stage.mjs'
import { auditLayout } from '../src/cli.mjs'

test('v2 静止 9.0s 必须报错', () => {
  const scene = {
    id: 'code-01',
    kind: 'code',
    title: '代码',
    code: Array.from({ length: 10 }, (_, i) => `line ${i}`).join('\n'),
    duration: 10,
    beats: [
      { at: 0, targets: ['title', 'line:0', 'line:1', 'line:2', 'line:3', 'line:4'], kind: 'content', index: 0 },
      { at: 9.0, targets: ['line:5', 'line:6', 'line:7', 'line:8', 'line:9'], kind: 'content', index: 1 },
    ],
  }
  assert.throws(() => validateBeats({ fps: 30, totalFrames: 300, scenes: [scene], captions: [] }), /静止 9\.0s/)
})

const stageOpts = {
  platform: 'probe',
  size: [1080, 1920],
  safe: {},
  scenes: [{ id: 'h', kind: 'hook', title: '上电', sub: '一秒', code: 'A\nB', narration: 'x' }],
  kicker: 'x',
  badge: 'T',
  sections: null,
  formatVersion: 2,
  fps: 30,
}
const plan = {
  fps: 30,
  captions: [{ scene: 'h', start: 0, end: 1, text: '上电一秒' }],
  scenes: [{ id: 'h', index: 0, startFrame: 0, duration: 1, fps: 30, kind: 'hook', title: '上电', sub: '一秒', code: 'A\nB' }],
  beatStats: { beats: 5, pulses: 1, maxGap: 4, scenes: 1 },
}

test('v2 干净舞台通过排版审计（showAll 后无不可见目标）', async () => {
  const browser = await openBrowser()
  let stage
  const origLog = console.log
  const lines = []
  try {
    stage = await openStage(browser, stageOpts)
    console.log = (...args) => { lines.push(args.join(' ')); origLog(...args) }
    const rows = await auditLayout(stage, plan)
    assert.equal(rows.length, 1)
    assert.ok(
      lines.some((l) => l.includes('节拍审计：5 拍（含脉冲 1），最长静止 4.0s')),
      `节拍审计行缺失，实际日志：\n${lines.join('\n')}`,
    )
  } finally {
    console.log = origLog
    if (stage) await stage.close()
    await browser.close()
  }
})

test('v2 审计抓到 showAll 后仍不可见的节拍目标', async () => {
  const browser = await openBrowser()
  let stage
  try {
    stage = await openStage(browser, stageOpts)
    await stage.page.addStyleTag({ content: '[data-beat-target="sub"]{opacity:0!important}' })
    await assert.rejects(() => auditLayout(stage, plan), /审计时仍不可见/)
  } finally {
    if (stage) await stage.close()
    await browser.close()
  }
})

// 单场计划是 v2Reset 照不到的路径：setup(0) 之后 current 已是 0，
// renderFrames 再调 setup(0) 会直接早退，重置不会跑；审计的 showAll() 先把
// 金色 locked 底镀上去，回 0/1 相时只能靠 v2State 把 locked 摘掉。
const emphStageOpts = {
  platform: 'probe',
  size: [1080, 1920],
  safe: {},
  scenes: [{ id: 'h', kind: 'hook', title: '上电', sub: '一秒', narration: 'x', emphasis: ['上电'] }],
  kicker: 'x',
  badge: 'T',
  sections: null,
  formatVersion: 2,
  fps: 30,
}

test('v2 单场 showAll 后回 1 相必须摘掉 emph 锁定底色', async () => {
  const browser = await openBrowser()
  let stage
  try {
    stage = await openStage(browser, emphStageOpts)
    const page = stage.page
    const lockedCount = () => page.evaluate(() => document.querySelectorAll('.emph.locked').length)

    await page.evaluate(() => window.MCU.setup(0))
    await page.evaluate(() => window.MCU.showAll())
    assert.equal(await lockedCount(), 1)

    await page.evaluate(() => window.MCU.state({ index: 0, phase: 1, targets: ['title'], revealed: ['title'] }, -1))
    assert.equal(await lockedCount(), 0)
    assert.equal(
      await page.evaluate(() => getComputedStyle(document.querySelector('[data-beat-target="title"]')).opacity),
      '0.5',
    )

    await page.evaluate(() => window.MCU.state({ index: 0, phase: 2, targets: ['title'], revealed: ['title'] }, -1))
    assert.equal(await lockedCount(), 1)
  } finally {
    if (stage) await stage.close()
    await browser.close()
  }
})
