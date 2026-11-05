import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { pathToFileURL } from 'node:url'
import { auditNumbers } from '../../src/numbers.mjs'
import { loadEpisode } from '../../src/spec.mjs'
import { OUT_DIR, REPO_ROOT, VIDEO_ROOT, probeStreams } from '../../src/util.mjs'
import {
  UnknownError,
  dayDir,
  exitAfterFlush,
  parseArgs,
  pngSize,
  readJson,
  requireEp,
  requirePlatform,
  runDirFor,
  seriesName,
  normalizeText,
  today,
  withPage,
  writeJson,
} from './common.mjs'
import { publishTitle } from './archive.mjs'

const MASTER = {
  bilibili: 'bilibili.mp4',
  douyin: 'douyin.mp4',
  zhihu: 'bilibili.mp4',
  xiaohongshu: 'douyin.mp4',
}
const COVERS = {
  bilibili: [['bilibili-cover.png', 1920, 1200]],
  douyin: [
    ['douyin-cover.png', 1080, 1440],
    ['douyin-cover-1440x1080.png', 1440, 1080],
  ],
  zhihu: [['zhihu-cover.png', 1920, 1080]],
  xiaohongshu: [['xiaohongshu-cover.png', 1440, 1080]],
}
const TITLE_MAX = { bilibili: 80, douyin: 62, zhihu: 100, xiaohongshu: 20 }

function targetSec(ep, platform) {
  if (platform === 'zhihu') return ep.platforms.bilibili?.targetSec || null
  if (platform === 'xiaohongshu') return ep.platforms.douyin?.targetSec || null
  return ep.platforms[platform]?.targetSec || null
}

function push(checks, name, ok, detail) {
  checks.push({ name, ok, detail })
}

export async function verifyBefore(epId, platform) {
  const ep = loadEpisode(epId)
  const out = join(OUT_DIR, epId)
  const checks = []
  const unknown = []

  const master = join(out, MASTER[platform])
  if (!existsSync(master)) {
    push(checks, '母版存在', false, master)
    return { ok: false, unknown, checks }
  }
  const { duration } = await probeStreams(master)
  const range = targetSec(ep, platform)
  const durOk = duration > 0 && range && duration >= range[0] && duration <= range[1]
  push(checks, '母版时长', durOk, `${duration.toFixed(3)}s，目标 ${range ? `${range[0]}–${range[1]}s` : '(无 targetSec)'}`)
  if (!range) unknown.push('targetSec')

  for (const [file, w, h] of COVERS[platform]) {
    const p = join(out, file)
    if (!existsSync(p)) {
      push(checks, `封面 ${file}`, false, '缺文件')
      continue
    }
    const got = pngSize(p)
    push(checks, `封面 ${file}`, got.width === w && got.height === h, `${got.width}×${got.height}，期望 ${w}×${h}`)
  }

  const release = join(out, `发布-${platform}.md`)
  if (!existsSync(release)) {
    push(checks, '发布包', false, release)
  } else {
    const text = readFileSync(release, 'utf8')
    const title = publishTitle(ep, platform)
    const wordOk = text.length > 500 && normalizeText(text).includes(normalizeText(title))
    push(checks, '发布包', wordOk, `${text.length} 字，标题${title ? '在' : '缺'}包内`)
  }

  const title = publishTitle(ep, platform)
  const max = TITLE_MAX[platform]
  const len = [...title].length
  push(checks, '标题长度', !!title && len <= max, `${len} 字，上限 ${max}`)

  if (platform === 'xiaohongshu') {
    const xs = ep.publish?.xiaohongshu || {}
    const bodyLen = [...(xs.body || '')].length
    push(checks, '小红书正文', bodyLen > 0 && bodyLen <= 1000, `${bodyLen} 字，上限 1000`)
    const bad = []
    for (const [k, v] of Object.entries({ title: xs.title, body: xs.body, pinned: xs.pinned })) {
      if (/https?:\/\//.test(v || '')) bad.push(`${k} 有站外链接`)
      if (/github/i.test(v || '')) bad.push(`${k} 有 GitHub 字样`)
    }
    push(checks, '小红书无站外地址', bad.length === 0, bad.join('；') || '干净')
  }
  if (platform === 'douyin') {
    const dy = ep.publish?.douyin || {}
    const capLen = [...(dy.caption || '')].length
    push(checks, '抖音描述', capLen > 0 && capLen <= 62, `${capLen} 字，自限 62`)
    push(checks, '抖音置顶含复现命令', /probe\.(sh|py)|code\//.test(dy.pinned || ''), dy.pinned ? '有' : '缺 pinned')
  }

  const evFile = join(VIDEO_ROOT, 'research', `${epId}-numbers.json`)
  if (!existsSync(evFile)) {
    push(checks, '数字证据', false, `缺 ${evFile}`)
  } else {
    try {
      const r = auditNumbers(ep, JSON.parse(readFileSync(evFile, 'utf8')))
      push(checks, '数字证据', r.unresolved.length === 0, `未命中 ${r.unresolved.length} / 共 ${r.tokens.length}`)
    } catch (e) {
      push(checks, '数字证据', false, e.message)
    }
  }

  return { ok: checks.every((c) => c.ok) && unknown.length === 0, unknown, checks }
}

export async function verifyAfter(epId, platform, { date, replace = false } = {}) {
  const dir = runDirFor(epId, date)
  const oldDoc = readJson(join(dir, 'old.json'))
  const old = oldDoc?.platforms?.[platform]
  if (!old) throw new UnknownError(`old.json 里没有 ${platform} 这一栏，无法判定新旧`)
  // 首发布（知乎 s5）：平台上从来没有旧稿，old.id 就是 null。此时判据只能是「按标题回读到唯一一条」，
  // 不能拿「新旧不同」当门槛——否则发布成功后反而会抛错，重演「发了但系统说没发」。
  const firstPublish = !old.id
  const { default: adapter } = await import(`./adapters/${platform}.mjs`)
  const epDoc = loadEpisode(epId)
  const newTitle = publishTitle(epDoc, platform)
  if (!newTitle) throw new UnknownError(`${epId} 没有 ${platform} 新标题，无法回读新稿`)
  // 知乎管理卡不显示标题：发布时 zh-one 把 pin URL 写进 marker，回读从这里取 id 锁行。
  let expectId = ''
  if (platform === 'zhihu') {
    const marker = join(REPO_ROOT, '.temp', 'zh-run', `${epId}-published.txt`)
    if (existsSync(marker)) {
      expectId = (readFileSync(marker, 'utf8').split('\t')[0].match(/\/pin\/(\d{10,25})/) || [])[1] || ''
    }
  }
  const got = await withPage(
    (page) => {
      page.on('dialog', (d) => d.dismiss().catch(() => {}))
      return adapter.verifyNew(page, {
        ep: epId,
        title: newTitle,
        old,
        expectId,
        replace,
        intro: epDoc.publish?.zhihu?.intro || '',
      })
    },
    { url: adapter.managerUrl, waitMs: platform === 'xiaohongshu' ? 9000 : 6000 },
  )
  const checks = []
  const unknown = []
  if (firstPublish) push(checks, '首发布（旧 ID 为空）', !!got.id, `old=(无) new=${got.id}`)
  else if (replace) push(checks, 'BV 不变（换源）', !!got.id && got.id === old.id, `old=${old.id} new=${got.id}`)
  else push(checks, '新 ID ≠ 旧 ID', !!got.id && got.id !== old.id, `old=${old.id} new=${got.id}`)
  push(checks, '标题精确匹配', normalizeText(got.title) === normalizeText(newTitle), got.title)
  push(checks, '封面 URL', !!got.cover, got.cover || '(空)')
  if (!got.cover) unknown.push('cover')

  if (platform === 'xiaohongshu') {
    push(checks, 'noteId 存在', !!got.id, 'Task 17 noteId/since 规则')
    unknown.push('duration', 'collection')
  } else {
    // 重制稿的时长本来就会变（旧 68s → 新 61s），拿旧稿做基准永远不过。
    // 要判的是「平台上的片子 ≈ 这次投上去的母版」，旧稿时长只留在细节里当参照。
    const master = join(OUT_DIR, epId, MASTER[platform])
    const masterDur = existsSync(master) ? (await probeStreams(master)).duration : null
    const durOk = got.duration != null && masterDur != null && Math.abs(got.duration - masterDur) <= 1
    push(
      checks,
      '时长 ±1s（对本集新母版）',
      durOk,
      `master=${masterDur != null ? `${masterDur.toFixed(3)}s` : '(缺母版)'} new=${got.duration ?? '(未回读)'}s old=${old.duration ?? '(未知)'}s`,
    )
    if (got.duration == null || masterDur == null) unknown.push('duration')
    // 知乎视频投稿没有合集这一步（zh-one 的 8 项核对里也没有），把合集记成 unknown 只会永远挡住全绿。
    if (platform !== 'zhihu') {
      const want = seriesName()
      const colOk = !!want && normalizeText(got.collection) === normalizeText(want)
      push(checks, '合集正确', colOk, `got=${got.collection ?? '(未回读)'} want=${want}`)
      if (got.collection == null) unknown.push('collection')
    }
  }

  return { ok: checks.every((c) => c.ok) && unknown.length === 0, unknown, checks, row: got }
}

async function main() {
  const args = parseArgs()
  const ep = requireEp(args)
  const platform = requirePlatform(args)
  if (!args.before && !args.after) throw new Error('必须给 --before 或 --after')
  const dir = args.after ? runDirFor(ep, args.date) : dayDir(ep, args.date || today())

  const result = args.after
    ? await verifyAfter(ep, platform, { date: args.date, replace: !!args.replace })
    : await verifyBefore(ep, platform)
  const file = join(dir, `verify-${args.after ? 'after' : 'before'}-${platform}.json`)
  writeJson(file, { at: new Date().toISOString(), ep, platform, ...result })
  for (const c of result.checks) console.log(`${c.ok ? '✅' : '❌'} ${c.name}：${c.detail}`)
  if (result.unknown.length) console.log(`⚠ 未回读：${result.unknown.join(' / ')}——按 unknown 处理，不重发`)
  console.log(`\n${result.ok ? '✓ 通过' : '✗ 未通过'} → ${file}`)
  if (!result.ok) process.exitCode = result.unknown.length ? 4 : 1
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main()
    .then(() => exitAfterFlush(process.exitCode || 0))
    .catch((e) => {
      console.error(`✗ ${e.message}`)
      return exitAfterFlush(e.exitCode || 1)
    })
}
