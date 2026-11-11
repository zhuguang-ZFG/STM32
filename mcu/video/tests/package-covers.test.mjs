import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, readFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { COVER_SIZES, buildAllCovers, coverHtml, coverV2Html, packJobs, pngSize, writeRelease } from '../src/package.mjs'
import { openBrowser } from '../src/stage.mjs'

// ------------------------------------------------------------------ 小红书发布限制
// 这三条是 brief 里逐字给出的验收用例：写发布包时先拦标题/正文/合集，
// 不让发布的人到编辑页里才发现被截尾或漏选。
const base = (over = {}) => ({
  id: 't', title: 't', voice: 'zh-CN-YunyangNeural', formatVersion: 2,
  platforms: { douyin: { targetSec: [45, 75] } },
  cover: { line1: '一', line2: '二' },
  publish: { xiaohongshu: { title: '标题', body: '正文', repro: 'sh code/x/probe.sh', collection: '合集', pinned: '复现 sh code/x/probe.sh' } },
  ...over,
})
const cfg = { size: [1080, 1920], fps: 30 }
const tl = { fps: 30, totalFrames: 1800, captions: [], sceneTexts: [] }

test('小红书标题 ≤20 字', () => {
  const ep = base(); ep.publish.xiaohongshu.title = '一'.repeat(21)
  assert.throws(() => writeRelease({ ep, platform: 'xiaohongshu', outDir: mkdtempSync(join(tmpdir(), 'xhs-')), timeline: tl, cfg, videoPath: 'v', srtPath: 's', coverPath: 'c', sceneTexts: [] }), /20/)
})

test('小红书正文出现站外地址要拒绝', () => {
  const ep = base(); ep.publish.xiaohongshu.body = '见 https://example.com'
  assert.throws(() => writeRelease({ ep, platform: 'xiaohongshu', outDir: mkdtempSync(join(tmpdir(), 'xhs-')), timeline: tl, cfg, videoPath: 'v', srtPath: 's', coverPath: 'c', sceneTexts: [] }), /站外/)
})

test('小红书缺合集要拒绝', () => {
  const ep = base(); delete ep.publish.xiaohongshu.collection
  assert.throws(() => writeRelease({ ep, platform: 'xiaohongshu', outDir: mkdtempSync(join(tmpdir(), 'xhs-')), timeline: tl, cfg, videoPath: 'v', srtPath: 's', coverPath: 'c', sceneTexts: [] }), /合集/)
})

// ------------------------------------------------------------------ 四尺寸与模板
test('COVER_SIZES 四个平台各自一档', () => {
  assert.deepEqual(COVER_SIZES.xiaohongshu, [1440, 1080])
  assert.deepEqual(COVER_SIZES.bilibili, [1920, 1200])
  assert.deepEqual(COVER_SIZES.douyin, [1080, 1440])
  assert.deepEqual(COVER_SIZES.zhihu, [1920, 1080])
})

const coverArgs = {
  kicker: '通往单片机之路 · T9',
  line1: '四个尺寸',
  line2: '一次出齐',
  tag: '本机实跑',
  proof: '![1] 336px 下先读标题\n![2] 红圈圈住 514 ms\n![3] 42 条断言全绿',
  num: '514 ms',
  numNote: '一天欠的相位',
  badge: 'T9',
  vs: { left: '看着是四张', right: '其实一套' },
  size: [1440, 1080],
}

test('v2 封面标签可覆盖：文档口径不再标 MEASURED', () => {
  const html = coverV2Html({
    ...coverArgs,
    variant: 'vs',
    vs: { left: '-O0 灯在闪', right: '-O2 灯灭了', labels: ['DOCUMENTED', 'DOCUMENTED'] },
    siteNote: '寄存器级 · 代码可复现',
  })
  assert.ok(html.includes('DOCUMENTED'))
  assert.ok(!html.includes('MEASURED'))
  assert.ok(!html.includes('EXPECTED'))
  assert.ok(html.includes('代码可复现'))
  assert.ok(!html.includes('每句话都能复现'))
})

test('v2 HTML 带齐 fitCover 认的元素与 EXPECTED/MEASURED', () => {
  const html = coverV2Html({ ...coverArgs, variant: 'vs' })
  for (const need of [
    'class="pad v2"',
    'class="head"',
    'class="mid"',
    'class="num"',
    'class="numnote"',
    'class="vslab l"',
    'class="vslab r"',
    'EXPECTED',
    'MEASURED',
    'CH1',
  ]) {
    assert.ok(html.includes(need), `缺少 ${need}`)
  }
  // 横版（1440×1080）的 typography 档位与 data-want 必须一致（u=10.8）。
  for (const want of [(10.8 * 10.4).toFixed(2), (10.8 * 11.5).toFixed(2), (10.8 * 4.6).toFixed(2), (10.8 * 2.4).toFixed(2)]) {
    assert.ok(html.includes(`data-want="${want}"`), `缺少 data-want=${want}`)
  }
  // 336px 下读不清的证据卡在横版撤掉；标题里的英文/数字段不拆行。
  assert.ok(!html.includes('class="code"'), '横版不该再有证据卡')
  assert.ok(html.includes('.tk{white-space:nowrap}'), 'v2 丢了 token nowrap')
  // 红圈必须挂在 .num 的 ::before 上，且不与布局/溢出测量纠缠。
  // .num 立成层叠上下文、环放 z-index:-1，红笔才画在黄字后面。
  assert.match(html, /\.num\{[^}]*isolation:isolate/)
  assert.match(html, /\.num::before\{[^}]*position:absolute[^}]*z-index:-1[^}]*inset:0/)
})

test('v2 竖版保留证据卡并优先 proofShort', () => {
  const arg = { ...coverArgs, size: [1080, 1440], proofShort: '![3] 短版证据', variant: 'vs' }
  const html = coverV2Html(arg)
  assert.ok(html.includes('class="code"'), '竖版丢了证据卡')
  assert.ok(html.includes('短版证据'), '竖版没用 proofShort')
  assert.ok(!html.includes('336px 下先读标题'), '竖版误用了长版 proof')
  // 竖版字号档位维持 8.8/10/3.2/1.8。
  for (const want of [(10.8 * 8.8).toFixed(2), (10.8 * 10).toFixed(2), (10.8 * 3.2).toFixed(2), (10.8 * 1.8).toFixed(2)]) {
    assert.ok(html.includes(`data-want="${want}"`), `缺少竖版 data-want=${want}`)
  }
  // 证据行首的 "!" 是结构标记：走 codeHtml 后应变成 .ln.ev，而不是把 "![3]" 原样印上屏。
  assert.ok(html.includes('class="ln ev"'), '证据行没走 codeHtml 的红底行')
  assert.ok(!html.includes('![3]'), '证据标记被当成正文印出来了')
})

test('packJobs 按 publish 平台解析母版与各自封面', () => {
  const jobs = packJobs({ publish: { bilibili: {}, douyin: {}, zhihu: {}, xiaohongshu: {} } }, 'x')
  assert.deepEqual(jobs.map((j) => j.platform), ['bilibili', 'douyin', 'zhihu', 'xiaohongshu'])
  const by = Object.fromEntries(jobs.map((j) => [j.platform, j]))
  assert.deepEqual(by.bilibili, {
    platform: 'bilibili', base: 'bilibili', video: 'bilibili.mp4',
    srt: 'bilibili.srt', cover: 'bilibili-cover.png', timeline: join('bilibili', 'timeline.json'),
  })
  assert.deepEqual(by.zhihu, {
    platform: 'zhihu', base: 'bilibili', video: 'bilibili.mp4',
    srt: 'bilibili.srt', cover: 'zhihu-cover.png', timeline: join('bilibili', 'timeline.json'),
  })
  assert.deepEqual(by.xiaohongshu, {
    platform: 'xiaohongshu', base: 'douyin', video: 'douyin.mp4',
    srt: 'douyin.srt', cover: 'xiaohongshu-cover.png', timeline: join('douyin', 'timeline.json'),
  })
})

test('packJobs 遇到未知平台或无 publish 直接抛错（不碰磁盘）', () => {
  assert.throws(() => packJobs({ publish: { bilibili: {}, weibo: {} } }, 'x'), /未知平台 "weibo"/)
  assert.throws(() => packJobs({ publish: {} }, 'x'), /没有 publish/)
})

test('panel 变体也保留 .head/.mid/.num 且不摆对撞两列', () => {
  const html = coverV2Html({ ...coverArgs, variant: 'panel' })
  for (const need of ['class="head"', 'class="mid"', 'class="num"', 'class="numnote"']) {
    assert.ok(html.includes(need), `缺少 ${need}`)
  }
  assert.ok(!html.includes('class="vslab'), 'panel 不该有 vslab 元素')
  assert.ok(!html.includes('EXPECTED'))
})

test('v1 coverHtml 不掺任何 v2 结构', () => {
  const html = coverHtml({
    kicker: '通往单片机之路 · C2',
    line1: '你抄的点灯公式',
    line2: '只有三件事',
    proof: '! sizeof: uint8_t=1',
    num: '8 字节',
    numNote: '指针自身',
    badge: 'C2',
    vs: { left: '看着是魔数', right: '其实是三件事' },
    size: [1920, 1200],
  })
  assert.ok(!html.includes('pad v2'))
  assert.ok(!html.includes('.pad.v2'))
  assert.ok(!html.includes('EXPECTED'))
})

// ------------------------------------------------------------------ 真浏览器出图
// 一次把四张封面真排出来，用 PNG 头的 IHDR 读回尺寸；contact sheet 也从这里落盘。
// 浏览器是本用例自己的，finally 里关掉，不碰别人的 share 页面。
test('v2 四平台封面按 1080×1440 / 1440×1080 出图并拼 contact sheet', async () => {
  const dir = mkdtempSync(join(tmpdir(), 'covers-'))
  const ep = {
    id: 't9-cover',
    formatVersion: 2,
    badge: 'T9',
    cover: { ...coverArgs, variant: 'vs' },
    platforms: {},
  }
  const browser = await openBrowser()
  try {
    await buildAllCovers(browser, ep, dir)
    const read = (name) => pngSize(readFileSync(join(dir, name)))
    assert.deepEqual(read('douyin-cover.png'), { width: 1080, height: 1440 })
    assert.deepEqual(read('xiaohongshu-cover.png'), { width: 1440, height: 1080 })
    assert.deepEqual(read('bilibili-cover.png'), { width: 1920, height: 1200 })
    assert.deepEqual(read('zhihu-cover.png'), { width: 1920, height: 1080 })
    // 抖音 4:3 备选必须是小红书那张的逐字节拷贝
    assert.deepEqual(
      readFileSync(join(dir, 'douyin-cover-1440x1080.png')),
      readFileSync(join(dir, 'xiaohongshu-cover.png')),
    )
    assert.deepEqual(read('cover-contact-336.png'), { width: 1440, height: 460 })
  } finally {
    await browser.close()
  }
})
