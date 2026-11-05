import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import {
  saveOld,
  loadOld,
  ArchiveConflict,
  isBvid,
  isAwemeId,
  isNoteId,
  isZhihuId,
  extractId,
  normalizeTitle,
  matchUnique,
} from '../publish/repost/archive.mjs'

const sample = (over = {}) => ({
  ep: 's5-systick',
  archivedAt: '2026-10-29T00:00:00.000Z',
  platforms: {
    bilibili: {
      id: 'BV1ZoJy66E6d',
      title: 'SysTick 是谁在给 RTOS 数那一毫秒？',
      duration: 653.5,
      cover: 'https://i0.hdslb.com/x.jpg',
      collection: '通往单片机之路',
      publishedAt: '2026-10-15T09:37:39Z',
      evidence: 'manager row text',
      unavailable: [],
    },
  },
  ...over,
})

test('首次归档写入 old.json', () => {
  const dir = mkdtempSync(join(tmpdir(), 'archive-'))
  assert.equal(saveOld(dir, sample()), 'created')
  assert.equal(loadOld(dir).platforms.bilibili.id, 'BV1ZoJy66E6d')
  assert.match(readFileSync(join(dir, 'old.json'), 'utf8'), /BV1ZoJy66E6d/)
})

test('旧档已存在且一致时不覆盖 archivedAt', () => {
  const dir = mkdtempSync(join(tmpdir(), 'archive-'))
  saveOld(dir, sample())
  const again = sample({ archivedAt: '2026-10-30T00:00:00.000Z' })
  assert.equal(saveOld(dir, again), 'unchanged')
  assert.equal(loadOld(dir).archivedAt, '2026-10-29T00:00:00.000Z')
})

test('旧档与现读不一致时停止', () => {
  const dir = mkdtempSync(join(tmpdir(), 'archive-'))
  saveOld(dir, sample())
  const changed = sample()
  changed.platforms.bilibili.id = 'BV1aaaaaaaaa'
  assert.throws(() => saveOld(dir, changed), ArchiveConflict)
})

test('只追加新平台时合并，已有平台保持原样', () => {
  const dir = mkdtempSync(join(tmpdir(), 'archive-'))
  saveOld(dir, sample({ archivedAt: '2026-10-29T00:00:00.000Z' }))
  const next = sample({ archivedAt: '2026-10-30T00:00:00.000Z' })
  delete next.platforms.bilibili
  next.platforms.douyin = {
    id: '7697617004848532787',
    title: '谁在给 RTOS 数那一毫秒',
    duration: 68,
    cover: 'https://p11-sign.douyinpic.com/x.webp',
    collection: null,
    publishedAt: '2026-10-17T20:45+08:00',
    evidence: 'row text',
    unavailable: [],
  }
  assert.equal(saveOld(dir, next), 'merged')
  const got = loadOld(dir)
  assert.equal(got.archivedAt, '2026-10-29T00:00:00.000Z')
  assert.equal(got.platforms.bilibili.id, 'BV1ZoJy66E6d')
  assert.equal(got.platforms.douyin.id, '7697617004848532787')
})

test('旧档里未完成的平台可以补全，已完成平台仍不许改', () => {
  const dir = mkdtempSync(join(tmpdir(), 'archive-'))
  const first = sample()
  first.platforms.bilibili.unavailable = ['login', 'row']
  first.platforms.bilibili.id = null
  saveOld(dir, first)
  const fixed = sample({ archivedAt: '2026-10-30T00:00:00.000Z' })
  assert.equal(saveOld(dir, fixed), 'merged')
  assert.equal(loadOld(dir).platforms.bilibili.id, 'BV1ZoJy66E6d')

  const changedAgain = sample()
  changedAgain.platforms.bilibili.id = 'BV1bbbbbbbbb'
  assert.throws(() => saveOld(dir, changedAgain), ArchiveConflict)
})

test('ID 形状只认实测格式', () => {
  assert.equal(isBvid('BV1ZoJy66E6d'), true)
  assert.equal(isBvid('bv1ZoJy66E6d'), false)
  assert.equal(isBvid('BV1ZoJy66E6'), false)
  assert.equal(isAwemeId('7321234567890123456'), true)
  assert.equal(isAwemeId('123'), false)
  assert.equal(isNoteId('6ad6165d000000002900e7a9'), true)
  assert.equal(isNoteId('6ad6165d000000002900e7a'), false)
  assert.equal(isZhihuId('2094070885703480096'), true)
  assert.equal(isZhihuId('abc'), false)
})

test('从链接里抽各平台 ID', () => {
  assert.equal(extractId('bilibili', 'https://www.bilibili.com/video/BV1ZoJy66E6d?x=1'), 'BV1ZoJy66E6d')
  assert.equal(extractId('douyin', 'https://www.douyin.com/video/7321234567890123456'), '7321234567890123456')
  assert.equal(extractId('douyin', 'https://creator.douyin.com/creator-micro/content/manage'), '')
  assert.equal(extractId('zhihu', 'https://www.zhihu.com/pin/2094070885703480096'), '2094070885703480096')
  assert.equal(extractId('xiaohongshu', 'https://creator.xiaohongshu.com/publish/update?id=6ad6165d000000002900e7a9'), '6ad6165d000000002900e7a9')
  assert.equal(extractId('xiaohongshu', 'https://creator.xiaohongshu.com/new/note-manager'), '')
})

test('标题匹配剥零宽、压空白，且只认唯一命中', () => {
  assert.equal(normalizeTitle('\u200b SysTick   一天漂\n514 毫秒 '), 'SysTick 一天漂 514 毫秒')
  const rows = ['SysTick 一天漂 514 毫秒', '别的笔记']
  assert.deepEqual(matchUnique(rows, 'SysTick 一天漂 514 毫秒'), { count: 1, row: rows[0] })
  assert.deepEqual(matchUnique(rows, '不存在'), { count: 0, row: null })
  assert.deepEqual(matchUnique([...rows, 'SysTick 一天漂 514 毫秒'], 'SysTick 一天漂 514 毫秒'), {
    count: 2,
    row: null,
  })
})
