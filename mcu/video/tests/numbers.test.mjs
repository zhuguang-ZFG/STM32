import test from 'node:test'
import assert from 'node:assert/strict'
import { extractTokens, flattenEpisode, auditNumbers } from '../src/numbers.mjs'
import { cmdNumbers } from '../src/cli.mjs'

test('抽 hex 与十进制，归一化逗号/单位空格', () => {
  const t = extractTokens('0x4002_1418 / 1,680,000 周期 / 514 ms')
  assert.ok(t.includes('0x40021418'))
  assert.ok(t.includes('1680000'))
  assert.ok(t.includes('514ms'))
})

test('未命中要报 unresolved', () => {
  const ep = { platforms: { bilibili: { scenes: [{ id: 'a', kind: 'card', title: '514 ms', narration: '一天欠 514 毫秒' }] } }, cover: {}, publish: {} }
  const r = auditNumbers(ep, { evidence: { '0xE000E010': 'probe' }, exceptions: {} })
  assert.ok(r.unresolved.some((u) => u.token === '514ms' || u.token === '514'))
})

test('exceptions 可以显式放行行号', () => {
  const ep = { platforms: { bilibili: { scenes: [{ id: 'a', kind: 'card', title: '第 4 行', narration: 'x' }] } }, cover: {}, publish: {} }
  const r = auditNumbers(ep, { evidence: {}, exceptions: { '4': '行号，不是实测值' } })
  assert.equal(r.unresolved.length, 0)
})

const cardEp = (title, narration = 'x') => ({
  platforms: { bilibili: { scenes: [{ id: 'a', kind: 'card', title, narration }] } },
  cover: {},
  publish: {},
})

test('hex 下划线/大小写归一化，evidence 键大写也命中', () => {
  assert.deepEqual(extractTokens('0X4002_1418'), ['0x40021418'])
  const r = auditNumbers(cardEp('0X4002_1418'), {
    evidence: { '0X4002_1418': 'RM 0x40021418' },
    exceptions: {},
  })
  assert.equal(r.unresolved.length, 0)
  assert.deepEqual(r.resolved.map((x) => x.token), ['0x40021418'])
})

test('514 ms 的 token 与 evidence 键双向归一化', () => {
  assert.deepEqual(extractTokens('514 ms'), ['514ms'])
  assert.equal(auditNumbers(cardEp('514 ms'), { evidence: { '514ms': 'probe' }, exceptions: {} }).unresolved.length, 0)
  assert.equal(auditNumbers(cardEp('514ms'), { evidence: { '514 ms': 'probe' }, exceptions: {} }).unresolved.length, 0)
})

test('1,680,000 与 1680000 收敛为同一个 token', () => {
  assert.deepEqual(extractTokens('1,680,000 / 1680000'), ['1680000'])
})

test('exceptions 键归一化后能放行 514ms', () => {
  const r = auditNumbers(cardEp('514ms'), { evidence: {}, exceptions: { '514 ms': '展示值' } })
  assert.equal(r.unresolved.length, 0)
  assert.deepEqual(r.resolved.map((x) => x.token), ['514ms'])
})

test('平台 cover 覆写也要展开并逐项审数字', () => {
  const ep = {
    platforms: {
      bilibili: {
        scenes: [{ id: 'a', kind: 'card', title: '开局', narration: 'x' }],
        cover: { num: '999 ms', vs: { left: '514 ms', right: '1000 ms' } },
      },
    },
    cover: { num: '514 ms' },
    publish: {},
  }
  const rows = flattenEpisode(ep)
  assert.ok(rows.some((r) => r.scene === 'cover' && r.field === 'num' && r.text === '514 ms'))
  assert.ok(rows.some((r) => r.scene === 'cover.bilibili' && r.field === 'num' && r.text === '999 ms'))
  assert.ok(rows.some((r) => r.scene === 'cover.bilibili' && r.field === 'vs.left' && r.text === '514 ms'))
  assert.ok(rows.some((r) => r.scene === 'cover.bilibili' && r.field === 'vs.right' && r.text === '1000 ms'))

  const r = auditNumbers(ep, { evidence: { '514 ms': 'probe', '1000ms': 'probe' }, exceptions: {} })
  assert.deepEqual(r.unresolved, [
    { token: '999ms', scene: 'cover.bilibili', field: 'num', text: '999 ms' },
  ])
})

test('evidence/exceptions 形状不对要抛清晰错误', () => {
  const ep = cardEp('x')
  assert.throws(() => auditNumbers(ep, {}), /缺 evidence/)
  assert.throws(() => auditNumbers(ep, { evidence: [] }), /不是对象/)
  assert.throws(() => auditNumbers(ep, { evidence: 'x' }), /不是对象/)
  assert.throws(() => auditNumbers(ep, null), /不是对象/)
  assert.throws(() => auditNumbers(ep, { evidence: {}, exceptions: [] }), /不是对象/)
  assert.throws(() => auditNumbers(ep, { evidence: { '1': 2 } }), /不是字符串/)
})

test('resolved 行带 scene/field/text', () => {
  const r = auditNumbers(cardEp('514 ms'), { evidence: { '514ms': 'probe' }, exceptions: {} })
  assert.deepEqual(r.tokens, ['514ms'])
  assert.deepEqual(r.resolved, [{ token: '514ms', scene: 'bilibili:a', field: 'title', text: '514 ms' }])
  assert.deepEqual(r.unresolved, [])
})

test('extractTokens 去重', () => {
  assert.deepEqual(extractTokens('514 ms 514 ms 1680000'), ['514ms', '1680000'])
})

test('codeLabel 纳入审计，源码行号可用 exceptions 放行', () => {
  const ep = {
    platforms: { bilibili: { scenes: [{ id: 'a', kind: 'code', code: 'x', codeLabel: 'probe.c:247-255', narration: 'x' }] } },
    cover: {},
    publish: {},
  }
  const rows = flattenEpisode(ep)
  assert.ok(rows.some((r) => r.scene === 'bilibili:a' && r.field === 'codeLabel' && r.text === 'probe.c:247-255'))

  const miss = auditNumbers(ep, { evidence: {}, exceptions: {} })
  assert.deepEqual(miss.unresolved.map((x) => x.token), ['247', '255'])

  const ok = auditNumbers(ep, { evidence: {}, exceptions: { '247': '行号', '255': '行号' } })
  assert.equal(ok.unresolved.length, 0)
  assert.deepEqual(ok.tokens, ['247', '255'])
})

test('publish 上屏字段被展开，topics/tags/notes 不审', () => {
  const ep = {
    platforms: { bilibili: { scenes: [{ id: 'a', kind: 'card', narration: 'x' }] } },
    cover: {},
    publish: {
      douyin: {
        caption: '514 ms',
        pinned: '1680000 周期',
        repro: '0xE000E010',
        title: '第 4 行',
        body: '737 倍速',
        intro: '1,680,000',
        titles: ['42/42'],
        topics: ['#514ms#'],
        tags: ['1680000'],
        notes: '2026-10-22',
      },
    },
  }
  const rows = flattenEpisode(ep).filter((r) => r.scene === 'publish.douyin')
  assert.deepEqual(rows.map((r) => r.field), [
    'caption', 'pinned', 'repro', 'title', 'body', 'intro', 'titles[0]',
  ])
  const tokens = extractTokens(rows.map((r) => r.text).join(' '))
  assert.ok(tokens.includes('514ms'))
  assert.ok(tokens.includes('1680000'))
  assert.ok(tokens.includes('0xe000e010'))
  assert.ok(!tokens.includes('2026'), 'notes 里的日期不应被当成数字主张')
})

test('C 后缀 hex 抽到真实常量，不残留开头的 0', () => {
  assert.deepEqual(extractTokens('0xFFFFFC18UL'), ['0xfffffc18'])
  assert.deepEqual(extractTokens('0x40021418ull'), ['0x40021418'])
  assert.ok(!extractTokens('0xFFFFFC18UL').includes('0'))
  assert.equal(extractTokens('SysTick LOAD = 0x00FFFFFFUL;').includes('0'), false)

  const r = auditNumbers(cardEp('0xFFFFFC18UL'), {
    evidence: { '0XFFFFFC18U': 'RM 0xFFFFFC18' },
    exceptions: {},
  })
  assert.equal(r.unresolved.length, 0)
  assert.deepEqual(r.tokens, ['0xfffffc18'])
})

test('正负号进入 token，数字后的减号不粘连', () => {
  assert.deepEqual(extractTokens('-14 dB'), ['-14db'])
  assert.deepEqual(extractTokens('−14 dB'), ['-14db'])
  assert.deepEqual(extractTokens('12-14'), ['12', '14'])
  assert.deepEqual(extractTokens('a-14'), ['14'])

  const r = auditNumbers(cardEp('−14 dB'), {
    evidence: { '-14 dB': 'spec' },
    exceptions: {},
  })
  assert.equal(r.unresolved.length, 0)
  assert.deepEqual(r.tokens, ['-14db'])
})

test('全角数字/逗号/句号/空格归一化', () => {
  assert.deepEqual(extractTokens('１６８０'), ['1680'])
  assert.deepEqual(extractTokens('1，680，000'), ['1680000'])
  assert.deepEqual(extractTokens('3.3　s'), ['3.3s'])
  assert.equal(
    auditNumbers(cardEp('１６８０ 周期'), { evidence: { '1680 周期': 'RM' }, exceptions: {} })
      .unresolved.length,
    0,
  )
})

test('下划线分组、科学计数、二进制与八进制', () => {
  assert.deepEqual(extractTokens('1_680_000'), ['1680000'])
  assert.deepEqual(extractTokens('1e6'), ['1e6'])
  assert.deepEqual(extractTokens('0b1010'), ['0b1010'])
  assert.deepEqual(extractTokens('0o755'), ['0o755'])
  assert.deepEqual(extractTokens('0b1010UL / 0o755u'), ['0b1010', '0o755'])
})

test('单位表扩展，单位后必须是非字母', () => {
  assert.deepEqual(extractTokens('3.3 s'), ['3.3s'])
  assert.deepEqual(extractTokens('3.3s'), ['3.3s'])
  assert.deepEqual(extractTokens('3.3 seconds'), ['3.3'])
  assert.deepEqual(extractTokens('168MHz'), ['168mhz'])
  assert.deepEqual(extractTokens('500 mAh'), ['500mah'])
  assert.deepEqual(extractTokens('10 GHz'), ['10ghz'])
  assert.deepEqual(extractTokens('25 °C'), ['25°c'])
  assert.deepEqual(extractTokens('70 dBm'), ['70dbm'])
  assert.deepEqual(extractTokens('1 GiB'), ['1gib'])
  assert.deepEqual(extractTokens('100 Mbps'), ['100mbps'])
  assert.equal(
    auditNumbers(cardEp('100 kΩ'), { evidence: { '100 kΩ': 'datasheet' }, exceptions: {} })
      .unresolved.length,
    0,
  )
})

test('evidence 键按 token 抽取，日期键与上屏对称', () => {
  const r = auditNumbers(cardEp('2026-10-17 开播'), {
    evidence: { '发布日期 2026-10-17': '发布记录' },
    exceptions: {},
  })
  assert.deepEqual(r.tokens, ['2026', '10', '17'])
  assert.equal(r.unresolved.length, 0)
})

test('标识符里的数字与伪 hex 不产生 token', () => {
  assert.deepEqual(extractTokens('GPIOF2 S5 foo0x1234'), [])
})

test('numbers 拒绝未知 flag', async () => {
  await assert.rejects(() => cmdNumbers(['s5-systick'], { bogus: true }), /--bogus/)
})
