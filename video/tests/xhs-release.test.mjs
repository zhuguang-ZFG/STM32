import test from 'node:test'
import assert from 'node:assert/strict'
import { existsSync, mkdtempSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { basename, join } from 'node:path'
import { writeRelease } from '../src/package.mjs'

// 小红书发布包的硬限制。base 与 brief 的验收用例同形，只是补上 topics——
// 发布包正常路径必须带话题数组（只打 # 不会成 chip，这条在 Task 9 里升成必填）。
const base = (over = {}) => ({
  id: 't', title: 't', voice: 'zh-CN-YunyangNeural', formatVersion: 2,
  platforms: { douyin: { targetSec: [45, 75] } },
  cover: { line1: '一', line2: '二' },
  publish: {
    xiaohongshu: {
      title: '标题',
      body: '正文',
      topics: ['单片机', 'STM32'],
      collection: '合集',
      repro: 'sh code/x/probe.sh',
      pinned: '复现 sh code/x/probe.sh',
    },
  },
  ...over,
})
const cfg = { size: [1080, 1920], fps: 30 }
const tl = { fps: 30, totalFrames: 1800, captions: [], sceneTexts: [] }

const run = (ep, over = {}) => writeRelease({
  ep,
  platform: 'xiaohongshu',
  outDir: mkdtempSync(join(tmpdir(), 'xhs-')),
  timeline: tl,
  cfg,
  videoPath: 'douyin.mp4',
  srtPath: 'douyin.srt',
  coverPath: 'xiaohongshu-cover.png',
  sceneTexts: [],
  ...over,
})

test('小红书标题 ≤20 字', () => {
  const ep = base(); ep.publish.xiaohongshu.title = '一'.repeat(21)
  assert.throws(() => run(ep), /20/)
})

test('小红书正文出现站外地址要拒绝', () => {
  const ep = base(); ep.publish.xiaohongshu.body = '见 https://example.com'
  assert.throws(() => run(ep), /站外/)
})

test('小红书缺合集要拒绝', () => {
  const ep = base(); delete ep.publish.xiaohongshu.collection
  assert.throws(() => run(ep), /合集/)
})

test('小红书正文 >1000 字要拒绝', () => {
  const ep = base(); ep.publish.xiaohongshu.body = '字'.repeat(1001)
  assert.throws(() => run(ep), /1000/)
})

test('小红书缺复现命令要拒绝', () => {
  const ep = base(); delete ep.publish.xiaohongshu.repro
  assert.throws(() => run(ep), /repro/)
})

test('置顶评论没写复现脚本要拒绝', () => {
  const ep = base(); ep.publish.xiaohongshu.pinned = '只有一句导流'
  assert.throws(() => run(ep), /复现脚本/)
})

test('小红书缺话题数组要拒绝', () => {
  const ep = base(); delete ep.publish.xiaohongshu.topics
  assert.throws(() => run(ep), /topics|话题/)
})

test('小红书发布包写全六段，并写明话题必须接弹层', () => {
  const ep = base()
  const out = run(ep)
  assert.ok(existsSync(out), `发布包没落盘：${out}`)
  assert.equal(basename(out), '发布-xiaohongshu.md')
  const md = readFileSync(out, 'utf8')
  for (const heading of ['## 标题', '## 正文', '## 话题', '## 置顶', '## 封面', '## 合集']) {
    assert.ok(md.includes(heading), `缺少段 ${heading}`)
  }
  // 话题必须逐条接弹层才会变成 chip；只打 # 只是普通文本。
  assert.match(md, /弹层/)
  assert.match(md, /chip/)
  // 封面路径与 4:3 尺寸必须写死，避免发布的人拿起抖音 3:4 那张。
  assert.ok(md.includes('xiaohongshu-cover.png'))
  assert.match(md, /1440×1080/)
  assert.match(md, /4:3/)
  // 母版视频也要给出路径，发布时不用回 video/out 里猜。
  assert.ok(md.includes('母版：`douyin.mp4`'), '封面段没列母版视频路径')
  // 合集名原样出现；正文/标题里没有站外地址。
  assert.ok(md.includes('合集'))
  assert.ok(md.includes('合集：`合集`'))
  assert.ok(!/https?:\/\//.test(md.split('## 置顶')[0]))
})
