import test from 'node:test'
import assert from 'node:assert/strict'
import { audioFilter, loudnessProbeFilter, loudnormSecondPass, parseLoudnormJson } from '../src/mux.mjs'

// v1 的滤镜串在这一个测试里冷冻。任何字符变化都必须先解释清楚为什么老集不需要重验。
const V1_NO_BGM = 'loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[out]'
const V1_BGM_DUCK =
  '[1:a]aresample=44100,asplit=2[narr][narrSC];' +
  '[2:a]aresample=44100,volume=-16dB[bg];' +
  '[bg][narrSC]sidechaincompress=threshold=0.03:ratio=6:attack=25:release=350[ducked];' +
  '[narr][ducked]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mix];' +
  '[mix]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[out]'
const V1_BGM_NO_DUCK =
  '[1:a]aresample=44100[narr];' +
  '[2:a]aresample=44100,volume=-16dB[bg];' +
  '[narr][bg]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mix];' +
  '[mix]loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[out]'
const LOUDNORM = 'loudnorm=I=-14:TP=-1.5:LRA=11,aresample=44100[out]'

// 无悬挂标签：链首的标签是输入（[1:a] 是流，不要求先定义），链内其余标签都是输出；
// 中间标签必须恰好定义一次并在下游被消费。
function assertClosedGraph(filter) {
  const defined = new Set()
  const used = new Set()
  for (const chain of filter.split(';')) {
    const m = chain.match(/^((?:\[[^\]]+\])*)(.*)$/)
    const inputs = [...m[1].matchAll(/\[([^\]]+)\]/g)].map((x) => x[1])
    const outputs = [...m[2].matchAll(/\[([^\]]+)\]/g)].map((x) => x[1])
    assert.ok(outputs.length >= 1, `链缺少输出标签：${chain}`)
    for (const input of inputs) {
      if (input.includes(':')) continue
      used.add(input)
      assert.ok(defined.has(input), `引用了未定义标签：${input}`)
    }
    for (const out of outputs) {
      assert.ok(!defined.has(out), `标签重复定义：${out}`)
      defined.add(out)
    }
  }
  for (const label of defined) {
    if (label === 'out') continue
    assert.ok(used.has(label), `标签悬空未消费：${label}`)
  }
  assert.ok(filter.endsWith(LOUDNORM), `末链不是 loudnorm：${filter}`)
}

test('sfx:false 的四种 bgm/duck 组合与当前 v1 串逐字一致', () => {
  // 无 BGM 时 duck 不再有输入可压，两种组合必须同串。
  assert.equal(audioFilter({ bgm: false, duck: true }), V1_NO_BGM)
  assert.equal(audioFilter({ bgm: false, duck: false }), V1_NO_BGM)
  assert.equal(audioFilter({ bgm: true, duck: true }), V1_BGM_DUCK)
  assert.equal(audioFilter({ bgm: true, duck: false }), V1_BGM_NO_DUCK)
  for (const f of [V1_NO_BGM, V1_BGM_DUCK, V1_BGM_NO_DUCK]) assertClosedGraph(f)
})

test('bgm + duck + sfx：SFX 取 [3:a]，三路 amix，标签闭合', () => {
  const f = audioFilter({ bgm: true, duck: true, sfx: true, sfxIdx: 3 })
  assert.ok(f.includes('[3:a]aresample=44100,volume=-24dB[sfx]'))
  assert.ok(
    f.includes('[narr][ducked][sfx]amix=inputs=3:duration=first:dropout_transition=0:normalize=0[mix]'),
  )
  assert.ok(f.includes('[bg][narrSC]sidechaincompress='))
  assertClosedGraph(f)
  assert.equal(f.includes('[2:a]aresample=44100,volume=-24dB'), false)
})

test('bgm + no duck + sfx：旁白/BGM/SFX 三路直混', () => {
  const f = audioFilter({ bgm: true, duck: false, sfx: true, sfxIdx: 3 })
  assert.ok(f.includes('[3:a]aresample=44100,volume=-24dB[sfx]'))
  assert.ok(
    f.includes('[narr][bg][sfx]amix=inputs=3:duration=first:dropout_transition=0:normalize=0[mix]'),
  )
  assert.ok(!f.includes('sidechaincompress'))
  assertClosedGraph(f)
})

test('no bgm + sfx：SFX 取 [2:a]，旁白与 SFX 两路 amix', () => {
  const f = audioFilter({ bgm: false, duck: true, sfx: true, sfxIdx: 2 })
  assert.ok(f.includes('[1:a]aresample=44100[narr]'))
  assert.ok(f.includes('[2:a]aresample=44100,volume=-24dB[sfx]'))
  assert.ok(f.includes('[narr][sfx]amix=inputs=2:duration=first:dropout_transition=0:normalize=0[mix]'))
  assert.ok(!f.includes('[3:a]'))
  assert.ok(!f.includes('[bg]'))
  assertClosedGraph(f)
  // duck 在没有 BGM 时没有可压对象，不能留下 sidechain 残链。
  assert.equal(f, audioFilter({ bgm: false, duck: false, sfx: true, sfxIdx: 2 }))
})

test('sfx:true 缺 sfxIdx 直接报错，不生成坏滤镜', () => {
  assert.throws(() => audioFilter({ bgm: true, duck: true, sfx: true }), /sfxIdx/)
})

test('v2 第一遍只测量：混音链不变，loudnorm 打印 JSON', () => {
  const f = loudnessProbeFilter({ bgm: true, duck: true, sfx: true, sfxIdx: 3 })
  assert.ok(f.includes('[narr][ducked][sfx]amix=inputs=3:duration=first:dropout_transition=0:normalize=0[mix]'))
  assert.ok(f.endsWith('[mix]loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json[out]'))
  assert.equal(f.includes('measured_I'), false)
})

test('v2 第二遍带实测值线性校正，拒绝 -inf', () => {
  const measured = { input_i: '-15.80', input_tp: '-0.40', input_lra: '7.30', input_thresh: '-26.05', target_offset: '0.10' }
  const f = audioFilter({ bgm: true, duck: true, sfx: true, sfxIdx: 3, measured })
  assert.ok(
    f.endsWith(
      '[mix]loudnorm=I=-14:TP=-1.5:LRA=11:measured_I=-15.8:measured_TP=-0.4' +
        ':measured_LRA=7.3:measured_thresh=-26.05:offset=0.1:linear=true:print_format=summary' +
        ',aresample=44100[out]',
    ),
  )
  assert.throws(() => loudnormSecondPass({ ...measured, input_i: '-inf' }), /input_i/)
})

test('loudnorm JSON 取 stderr 最后一个花括号块', () => {
  const stderr = [
    '[Parsed_loudnorm_0 @ 0000] {',
    '\t"input_i" : "-15.80",',
    '\t"target_offset" : "0.10"',
    '}',
    'frame= 10 fps=0.0 q=-0.0 size=N/A time=00:00:00.00 bitrate=N/A speed=0x',
  ].join('\n')
  assert.deepEqual(parseLoudnormJson(stderr), {
    input_i: '-15.80',
    target_offset: '0.10',
  })
  assert.throws(() => parseLoudnormJson('no json here'), /没有输出 JSON/)
})
