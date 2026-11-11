import test from 'node:test'
import assert from 'node:assert/strict'
import { applyLexicon, narrationJobs } from '../src/tts.mjs'

test('发音表最长键优先', () => {
  const lex = { '0x': '零 x ', '0x40021418': '零 x 四零零二一四一八' }
  assert.equal(applyLexicon('地址 0x40021418', lex), '地址 零 x 四零零二一四一八')
})

test('scene.ttsText 覆盖 narration，但 narration 原样保留', () => {
  const ep = { voice: 'zh-CN-YunyangNeural', platforms: { bilibili: { scenes: [
    { id: 'a', kind: 'card', title: 't', narration: '写 0x40021418', ttsText: '写 零 x 四零零二一四一八' },
  ] } } }
  const [job] = narrationJobs(ep, 'bilibili')
  assert.equal(job.narration, '写 0x40021418')
  assert.equal(job.ttsText, '写 零 x 四零零二一四一八')
})

test('lexicon 为 null/undefined 时原样返回', () => {
  for (const lex of [null, undefined]) {
    assert.equal(applyLexicon('写 0x40021418', lex), '写 0x40021418')
  }
})

test('短键是长键前缀时，长键先替换', () => {
  const lex = { PC: 'P C', PC13: 'P C 十三' }
  assert.equal(applyLexicon('PC13 和 PC0', lex), 'P C 十三 和 P C0')
})

test('ttsText 已是发音文时不二次展开；残留键仍会被替换', () => {
  const lex = { GPIOF: 'G P I O F', '0x': '零 x ' }
  const mk = (ttsText) => ({ voice: 'zh-CN-YunyangNeural', ttsLexicon: lex, platforms: { bilibili: { scenes: [
    { id: 'a', kind: 'card', title: 't', narration: 'GPIOF 的 0x40021018', ttsText },
  ] } } })
  // 已展开的发音文里不再含有键，纯字符串替换不会重复动它
  const [ok] = narrationJobs(mk('G P I O F 的 零 x 四零零二一零一八'), 'bilibili')
  assert.equal(ok.ttsText, 'G P I O F 的 零 x 四零零二一零一八')
  // 但词表是纯字符串语义：ttsText 里若还残留 "GPIOF"/"0x"，照样会被替换（不静默放过）
  const [raw] = narrationJobs(mk('GPIOF 的 0x40021018'), 'bilibili')
  assert.equal(raw.ttsText, 'G P I O F 的 零 x 40021018')
})

test('场景没有 ttsText 时用 episode 词表展开 narration', () => {
  const ep = { voice: 'zh-CN-YunyangNeural', ttsLexicon: { SysTick: 'Sys tick' }, platforms: { bilibili: { scenes: [
    { id: 'a', kind: 'card', title: 't', narration: 'SysTick 每毫秒一跳。' },
  ] } } }
  const [job] = narrationJobs(ep, 'bilibili')
  assert.equal(job.narration, 'SysTick 每毫秒一跳。')
  assert.equal(job.ttsText, 'Sys tick 每毫秒一跳。')
})

test('v1 风格 episode 仍产出原有字段，narration/ttsText 均已 trim', () => {
  const ep = { voice: 'zh-CN-YunxiNeural', platforms: { bilibili: { scenes: [
    { id: 'h', kind: 'hook', narration: '  开场白。  ' },
    { id: 'c', kind: 'code', narration: '看代码。', head: 0.1, tail: 0.2, minSec: 3 },
  ] } } }
  assert.deepEqual(narrationJobs(ep, 'bilibili'), [
    { id: 'h', narration: '开场白。', ttsText: '开场白。', head: 0.22, tail: 0.5, minSec: 2.2 },
    { id: 'c', narration: '看代码。', ttsText: '看代码。', head: 0.1, tail: 0.2, minSec: 3 },
  ])
})

test('替换不破坏 emoji 与组合字符', () => {
  const text = '🚀 e\u0301 0x1F 和 👨‍👩‍👧'
  assert.equal(applyLexicon(text, { '0x': '零 x ' }), '🚀 e\u0301 零 x 1F 和 👨‍👩‍👧')
})

// 抖音短版复用 B 站画面、只改旁白：源 scene 的 ttsText 是照着长旁白写的，
// 换旁白后必须一起失效，否则字幕是短句、耳朵里还是长句的发音。
function reuseEpisode(douyin) {
  return {
    voice: 'zh-CN-YunyangNeural',
    ttsLexicon: { GPIOF: 'G P I O F' },
    platforms: {
      bilibili: {
        size: [1920, 1080],
        scenes: [
          {
            id: 'hook',
            kind: 'hook',
            title: '开场',
            narration: '长句：先读 GPIOF。',
            ttsText: '长句：先读 G P I O F。',
          },
          { id: 'code', kind: 'code', title: '代码', narration: '再看代码。' },
        ],
      },
      douyin: { size: [1080, 1920], reuseFrom: 'bilibili', ...douyin },
    },
  }
}

test('reuseFrom 改旁白后，源 ttsText 不残留，按新旁白重新展开词表', () => {
  const ep = reuseEpisode({ narration: { hook: '短句：GPIOF。' } })
  const hook = narrationJobs(ep, 'douyin').find((j) => j.id === 'hook')
  assert.equal(hook.narration, '短句：GPIOF。')
  // 源 ttsText 已删，narrationJobs 从新旁白展开词表
  assert.equal(hook.ttsText, '短句：G P I O F。')
  assert.equal(ep.platforms.bilibili.scenes[0].ttsText, '长句：先读 G P I O F。')
})

test('reuseFrom 改旁白且平台显式给 ttsText 时，平台的值优先', () => {
  const ep = reuseEpisode({
    narration: { hook: '短句：GPIOF。' },
    set: { hook: { ttsText: '短句专用发音' } },
  })
  const hook = narrationJobs(ep, 'douyin').find((j) => j.id === 'hook')
  assert.equal(hook.narration, '短句：GPIOF。')
  assert.equal(hook.ttsText, '短句专用发音')
})

test('reuseFrom 不改旁白时，源 ttsText 原样继承', () => {
  const ep = reuseEpisode({})
  const hook = narrationJobs(ep, 'douyin').find((j) => j.id === 'hook')
  assert.equal(hook.narration, '长句：先读 GPIOF。')
  assert.equal(hook.ttsText, '长句：先读 G P I O F。')
})
