import test from 'node:test'
import assert from 'node:assert/strict'
import { deriveBeats, beatAt, validateBeats, sceneTargets, MAX_STATIC_GAP } from '../src/timeline.mjs'

const sc = (over = {}) => ({
  id: 'code-01', kind: 'code', title: '代码', code: Array.from({ length: 10 }, (_, i) => `line ${i}`).join('\n'),
  narration: 'x', startFrame: 0, duration: 20, ...over,
})
const caps = (times) => times.map((t, i) => ({ scene: 'code-01', start: t, end: t + 2, text: `c${i}` }))
const plan = (scenes, captions, fps = 30) => ({ fps, totalFrames: 1200, scenes, captions })

test('自动节拍覆盖所有 target，且最大静止 ≤ 6s', () => {
  const scene = { ...sc(), beats: deriveBeats(sc(), caps([0.2, 4, 8, 12, 16])) }
  const beats = scene.beats
  assert.ok(beats.length >= 4)
  const shown = new Set(beats.flatMap((b) => b.targets))
  for (const t of sceneTargets(sc())) assert.ok(shown.has(t), `${t} 未揭示`)
  let max = 0
  for (let i = 0; i < beats.length; i++) max = Math.max(max, (beats[i + 1]?.at ?? scene.duration) - beats[i].at)
  assert.ok(max <= MAX_STATIC_GAP + 1e-6, `max gap ${max}`)
  validateBeats(plan([scene], caps([0.2, 4, 8, 12, 16])))
})

test('相位：第一拍定格，后续 0/1/2 三档', () => {
  const beats = deriveBeats(sc(), caps([0.2, 4]))
  assert.equal(beatAt(beats, 0).phase, 2)
  const b = beatAt(beats, 4 + 0.01)
  assert.equal(b.phase, 0)
  assert.equal(beatAt(beats, 4 + 0.19).phase, 1)
  assert.equal(beatAt(beats, 4 + 0.37).phase, 2)
  assert.ok(beatAt(beats, 4 + 0.37).revealed.includes('title'))
})

test('beatMap 按字幕序号落点，未覆盖的 target 归最后一拍', () => {
  const s = sc({ beatMap: [{ at: 1, reveal: 'line:0-4' }, { at: 3, reveal: 'line:5-9' }] })
  const beats = deriveBeats(s, caps([0.2, 3, 6]))
  assert.equal(beats[0].at, 0)
  assert.equal(beats.find((b) => b.targets.includes('line:5')).at, 6)
  assert.equal(beats.find((b) => b.targets.includes('line:9')).at, 6)
  for (const at of [0.2, 3]) {
    const filler = beats.find((b) => b.at === at)
    assert.equal(filler.kind, 'caption')
    assert.deepEqual(filler.targets, [])
  }
  const shown = new Set(beats.flatMap((b) => b.targets))
  const titleBeat = beats.find((b) => b.targets.includes('title'))
  assert.ok(shown.has('title'))
  assert.equal(titleBeat.at, 6)
  assert.equal(titleBeat.kind, 'content')
  assert.ok(shown.has('note') === false) // 本场没有 note
})

test('beatMap.at 超出本场字幕数必须报错', () => {
  const s = sc({ beatMap: [{ at: 1, reveal: 'title' }, { at: 3, reveal: 'line:5-9' }] })
  assert.throws(() => deriveBeats(s, caps([0.2, 3])), /beatMap\[1\]\.at=3 超出本场字幕数 2/)
  assert.throws(() => deriveBeats(s, caps([0.2, 3])), /超出本场字幕数/)
})

test('不足两拍时补到两拍', () => {
  const s = sc({ kind: 'card', title: '一句', bullets: ['一'], code: undefined, duration: 4 })
  const beats = deriveBeats(s, [{ scene: 'code-01', start: 0.3, end: 2, text: 'c' }])
  assert.ok(beats.length >= 2)
})

test('13s 空档自动在 6s / 12s 补 pulse 拍', () => {
  const beats = deriveBeats(sc({ duration: 14 }), caps([0.2, 13]))
  const pulses = beats.filter((b) => b.kind === 'pulse')
  assert.deepEqual(pulses.map((b) => b.at), [6, 12])
  for (const p of pulses) assert.deepEqual(p.targets, [])
})

test('静止 6.04s 在 0.05s 容差内不报错', () => {
  const scene = {
    ...sc({ code: undefined, duration: 12.08 }),
    beats: [
      { at: 0, targets: ['title'], kind: 'content', index: 0 },
      { at: 6.04, targets: [], kind: 'content', index: 1 },
    ],
  }
  assert.doesNotThrow(() => validateBeats(plan([scene], [])))
})

test('静止 9s 必须报错', () => {
  const scene = { ...sc({ duration: 10 }), beats: [{ at: 0, targets: ['title'], kind: 'content', index: 0 }, { at: 9.5, targets: ['line:0'], kind: 'content', index: 1 }] }
  assert.throws(() => validateBeats(plan([scene], [])), /静止/)
})

test('永远不揭示必须报错', () => {
  const scene = { ...sc(), beats: [{ at: 0, targets: ['title'], kind: 'content', index: 0 }, { at: 2, targets: [], kind: 'content', index: 1 }] }
  assert.throws(() => validateBeats(plan([scene], [])), /永远不会揭示/)
})

test('钩子超过 15s 必须报错', () => {
  const a = { id: 'h1', kind: 'hook', title: 'h', narration: 'x', startFrame: 0, duration: 8, beats: [{ at: 0, targets: ['title'], kind: 'content', index: 0 }, { at: 4, targets: [], kind: 'pulse', index: 1 }] }
  const b = { ...a, id: 'h2', startFrame: 240, duration: 8, beats: [{ at: 0, targets: ['title'], kind: 'content', index: 0 }, { at: 4, targets: [], kind: 'pulse', index: 1 }] }
  assert.throws(() => validateBeats(plan([a, b], [])), /钩子/)
})
