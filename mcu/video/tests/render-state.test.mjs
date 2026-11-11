import test from 'node:test'
import assert from 'node:assert/strict'
import { stateKey, transitionPhase } from '../src/render.mjs'
import { iterateFrames } from '../src/timeline.mjs'

const frame = { scene: { index: 7 }, smilTime: 1.2, captionIdx: 3 }

test('v1 stateKey 原串不变', () => {
  assert.equal(stateKey(frame, 0.5, 0.75), '7|1.2000|3|0.5|0.75')
})

test('v2 追加拍号/相位/转场', () => {
  assert.equal(stateKey(frame, 1, 1, { index: 2, phase: 1 }, -1), '7|1.2000|3|1|1|b2:1|t-')
  assert.equal(stateKey(frame, 1, 1, { index: 2, phase: 1 }, 3), '7|1.2000|3|1|1|b2:1|t3')
})

test('转场只在前 4 帧', () => {
  assert.equal(transitionPhase(0), 0)
  assert.equal(transitionPhase(3), 3)
  assert.equal(transitionPhase(4), -1)
})

test('iterateFrames 仅在 v2 前 4 帧发转场', () => {
  const scene = (over = {}) => ({ id: 's', index: 0, startFrame: 0, frames: 6, duration: 0.2, ...over })
  const beats = [
    { at: 0, kind: 'content', targets: ['title'], index: 0 },
    { at: 0.1, kind: 'content', targets: [], index: 1 },
  ]
  const v2 = [...iterateFrames({ fps: 30, totalFrames: 6, scenes: [scene({ beats })], captions: [] })]
  assert.deepEqual(v2.map((f) => f.transitionPhase), [0, 1, 2, 3, -1, -1])
  assert.ok(v2.every((f) => f.beat !== null))

  const v1 = [...iterateFrames({ fps: 30, totalFrames: 6, scenes: [scene()], captions: [] })]
  assert.ok(v1.every((f) => f.transitionPhase === -1))
  assert.ok(v1.every((f) => f.beat === null))
})
