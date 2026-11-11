import test from 'node:test'
import assert from 'node:assert/strict'
import { validateEpisode } from '../src/spec.mjs'

const scene = (id, extra = {}) => ({
  id, kind: 'card', title: '标题', narration: '旁白一句。', bullets: ['一', '二'], ...extra,
})
const ep = (over = {}) => ({
  id: 't', title: 't', voice: 'zh-CN-YunyangNeural', formatVersion: 2, fps: 30,
  platforms: {
    bilibili: {
      scenes: [scene('a'), scene('b'), scene('c')],
      sections: [{ at: 'a', title: '一' }, { at: 'b', title: '二' }, { at: 'c', title: '三' }],
      targetSec: [1, 200],
    },
  },
  ...over,
})
const errs = (x) => validateEpisode(x, 't').errs
const codeEp = (code, codeB, reveal) => {
  const x = ep()
  x.platforms.bilibili.scenes[0] = scene('a', { kind: 'code', code, codeB, beatMap: [{ at: 1, reveal }] })
  return x
}

test('v2 需要 3–6 节', () => {
  const x = ep(); x.platforms.bilibili.sections = x.platforms.bilibili.sections.slice(0, 2)
  assert.ok(errs(x).some((e) => e.includes('3–6 节')))
})

test('v2 音色必须是云扬', () => {
  assert.ok(errs(ep({ voice: 'zh-CN-YunxiNeural' })).some((e) => e.includes('音色')))
})

test('beatMap.at 必须从 1 开始且递增', () => {
  const x = ep(); x.platforms.bilibili.scenes[0].beatMap = [
    { at: 0, reveal: 'title' }, { at: 1, reveal: 'bullets:0-1' },
  ]
  assert.ok(errs(x).some((e) => e.includes('beatMap[0]')))
})

test('第一拍 at 必须是 1', () => {
  const x = ep(); x.platforms.bilibili.scenes[0].beatMap = [{ at: 2, reveal: 'title' }]
  assert.ok(errs(x).some((e) => e.includes('第一拍 at 必须是 1')))
})

test('beatMap 项必须是对象', () => {
  const x = ep(); x.platforms.bilibili.scenes[0].beatMap = [null]
  assert.ok(errs(x).some((e) => e.includes('beatMap 项必须是对象')))
})

test('reveal 形状不对要报错', () => {
  const x = ep(); x.platforms.bilibili.scenes[0].beatMap = [{ at: 1, reveal: 'line:x-y' }]
  assert.ok(errs(x).some((e) => e.includes('reveal')))
})

test('emphasis 必须在场上文本里', () => {
  const x = ep(); x.platforms.bilibili.scenes[0].emphasis = ['0xDEADBEEF']
  assert.ok(errs(x).some((e) => e.includes('emphasis')))
})

test('v1 不校验 v2 字段', () => {
  for (const formatVersion of [undefined, 1]) {
    const x = ep({ formatVersion })
    x.platforms.bilibili.scenes[0].beatMap = [{ at: 0, reveal: 'nope' }]
    x.platforms.bilibili.sections = []
    assert.equal(errs(x).length, 0)
  }
})

test('ttsLexicon 键至少 2 字符', () => {
  assert.ok(errs(ep({ ttsLexicon: { x: '叉' } })).some((e) => e.includes('ttsLexicon')))
})

test('code: 越界按 sc.code 行数，不看 sc.codeB', () => {
  const longB = 'b1\nb2\nb3\nb4\nb5\nb6\nb7\nb8'
  assert.equal(errs(codeEp('l1\nl2\nl3', longB, 'code:1-2')).length, 0)
  assert.ok(errs(codeEp('l1', longB, 'code:1-2')).some((e) => e.includes('越界')))
})

test('codeB: 越界按 sc.codeB 行数，不看 sc.code', () => {
  const longCode = 'l1\nl2\nl3\nl4\nl5\nl6\nl7\nl8'
  assert.equal(errs(codeEp(longCode, 'b1\nb2', 'codeB:0-1')).length, 0)
  assert.ok(errs(codeEp(longCode, 'b1', 'codeB:0-1')).some((e) => e.includes('越界')))
})
