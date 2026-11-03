import test from 'node:test'
import assert from 'node:assert/strict'
import { matchPublished } from '../publish/repost/xhs-match.mjs'

const old = { id: 'old1', title: 'SysTick 一天漂 514 毫秒', createTime: '2026-09-01T10:00:00Z' }
const neu = { id: 'new1', title: 'SysTick 一天漂 514 毫秒', createTime: '2026-10-22T10:00:00Z' }

test('只有旧笔记 + since 在旧之后 → 0 条', () => {
  assert.equal(matchPublished([old], { title: old.title, since: '2026-10-22T00:00:00Z' }).length, 0)
})

test('新旧同标题 + since 在中间 → 只命中新', () => {
  assert.deepEqual(
    matchPublished([old, neu], { title: old.title, since: '2026-10-22T00:00:00Z' }).map((x) => x.id),
    ['new1'],
  )
})

test('noteId 精确命中', () => {
  assert.deepEqual(matchPublished([old, neu], { title: old.title, noteId: 'new1' }).map((x) => x.id), ['new1'])
})

test('只给标题必须抛错', () => {
  assert.throws(() => matchPublished([old, neu], { title: old.title }), /noteId 或 since/)
})

test('标题命中多条且都在 since 之后 → 抛错，不猜', () => {
  const neu2 = { id: 'new2', title: old.title, createTime: '2026-10-23T10:00:00Z' }
  assert.throws(() => matchPublished([old, neu, neu2], { title: old.title, since: '2026-10-22T00:00:00Z' }), /2 条/)
})

test('标题为空时抛错，不拿 since 去捞任意一条', () => {
  assert.throws(() => matchPublished([old, neu], { title: '  ', since: '2026-10-22T00:00:00Z' }), /标题/)
})
