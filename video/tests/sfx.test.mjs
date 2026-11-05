import test from 'node:test'
import assert from 'node:assert/strict'
import { buildSfxEvents, renderSfxBuffer } from '../src/audio/sfx.mjs'

const plan = { fps: 30, scenes: [
  { id: 'a', kind: 'hook', startFrame: 0, duration: 5, beats: [
    { index: 0, at: 0, kind: 'content', targets: ['title'] },
    { index: 1, at: 2, kind: 'pulse', targets: [] },
  ] },
] }

test('每个节拍恰好一条 SFX，时间落在场内', () => {
  const ev = buildSfxEvents(plan)
  assert.equal(ev.length, 2)
  assert.deepEqual(ev.map((e) => e.kind), ['sting', 'relay'])
  assert.ok(ev.every((e) => e.t >= 0 && e.t <= 5))
})

test('合成确定性 + WAV 参数', () => {
  const a = renderSfxBuffer([{ t: 0, kind: 'click' }], { duration: 0.5, sampleRate: 44100, channels: 2 })
  const b = renderSfxBuffer([{ t: 0, kind: 'click' }], { duration: 0.5, sampleRate: 44100, channels: 2 })
  assert.deepEqual(a.pcm, b.pcm)
  assert.equal(a.sampleRate, 44100)
  assert.equal(a.channels, 2)
  assert.equal(a.pcm.length, 22050 * 2)
})

test('跨场取绝对时间，按时间排序，无 beats 的场不产事件', () => {
  const multi = { fps: 30, scenes: [
    { id: 'silent', kind: 'hook', startFrame: 0, duration: 1 },
    { id: 'late', kind: 'code', startFrame: 45, duration: 2, beats: [
      { index: 1, at: 0.5, kind: 'pulse', targets: [] },
      { index: 0, at: 0, kind: 'content', targets: ['title'] },
    ] },
  ] }
  const ev = buildSfxEvents(multi)
  assert.equal(ev.length, 2)
  assert.deepEqual(ev.map((e) => e.t), [1.5, 2])
  assert.deepEqual(ev.map((e) => e.kind), ['click', 'relay'])
  assert.deepEqual(ev.map((e) => e.scene), ['late', 'late'])
  assert.deepEqual(ev.map((e) => e.beat), [0, 1])
})

test('不同事件集各自确定，噪声分支也不漂移', () => {
  const setA = [
    { t: 0, kind: 'whoosh' },
    { t: 0.1, kind: 'relay' },
    { t: 0.2, kind: 'click' },
    { t: 0.3, kind: 'sting' },
  ]
  const setB = [
    { t: 0, kind: 'click' },
    { t: 0.05, kind: 'sting' },
  ]
  const a1 = renderSfxBuffer(setA, { duration: 1 })
  const a2 = renderSfxBuffer(setA, { duration: 1 })
  const b1 = renderSfxBuffer(setB, { duration: 1 })
  const b2 = renderSfxBuffer(setB, { duration: 1 })
  assert.deepEqual(a1.pcm, a2.pcm)
  assert.deepEqual(b1.pcm, b2.pcm)
  assert.notDeepEqual(a1.pcm, b1.pcm)
})

test('尾巴按 duration 截断，起点在片尾之后则整条丢弃', () => {
  const duration = 0.1
  const frames = Math.round(duration * 44100)
  const clipped = renderSfxBuffer([{ t: 0.05, kind: 'sting' }], { duration, sampleRate: 44100, channels: 2 })
  assert.equal(clipped.pcm.length, frames * 2)
  // 1.2s 的 sting 只允许写后半段 0.05s；片尾仍有能量，证明是截断而不是整条没写。
  const tail = clipped.pcm.subarray((frames - 10) * 2)
  assert.ok(tail.some((v) => v !== 0))

  const past = renderSfxBuffer([{ t: duration, kind: 'sting' }], { duration, sampleRate: 44100, channels: 2 })
  assert.equal(past.pcm.length, frames * 2)
  assert.ok(past.pcm.every((v) => v === 0))
})

test('立体声逐帧交错，左右声道同源同值', () => {
  const mono = renderSfxBuffer([{ t: 0, kind: 'click' }], { duration: 0.1, sampleRate: 44100, channels: 1 })
  const stereo = renderSfxBuffer([{ t: 0, kind: 'click' }], { duration: 0.1, sampleRate: 44100, channels: 2 })
  assert.equal(mono.pcm.length, 4410)
  assert.equal(stereo.pcm.length, 8820)
  for (let i = 0; i < mono.pcm.length; i++) {
    assert.equal(stereo.pcm[i * 2], mono.pcm[i])
    assert.equal(stereo.pcm[i * 2 + 1], mono.pcm[i])
  }
})

test('空事件全静音，叠加事件不越 ±1 满刻度', () => {
  const silent = renderSfxBuffer([], { duration: 0.25 })
  assert.equal(silent.pcm.length, Math.round(0.25 * 44100) * 2)
  assert.ok(silent.pcm.every((v) => v === 0))

  const dense = renderSfxBuffer(
    [
      { t: 0, kind: 'sting' },
      { t: 0, kind: 'sting' },
      { t: 0, kind: 'sting' },
      { t: 0, kind: 'sting' },
      { t: 0, kind: 'whoosh' },
      { t: 0, kind: 'click' },
    ],
    { duration: 1, sampleRate: 44100, channels: 2 },
  )
  let max = 0
  for (const v of dense.pcm) {
    assert.ok(Number.isFinite(v), `出现非有限值 ${v}`)
    assert.ok(v >= -1 && v <= 1, `样本 ${v} 越出 ±1`)
    max = Math.max(max, Math.abs(v))
  }
  assert.equal(max, 1)
})
