import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { pathToFileURL } from 'node:url'
import { loadEpisode } from '../../src/spec.mjs'
import { REPO_ROOT } from '../../src/util.mjs'
import {
  UnknownError,
  dayDir,
  exitAfterFlush,
  normalizeText,
  parseArgs,
  readJson,
  requireEp,
  today,
  withPage,
  writeJson,
} from './common.mjs'

export class ArchiveConflict extends Error {}

const BV_RE = /^BV[0-9A-Za-z]{10}$/
const AWEME_RE = /^\d{15,25}$/
const NOTE_RE = /^[0-9a-f]{24}$/
const ZHIHU_RE = /^\d{10,25}$/

export function normalizeTitle(s) {
  return normalizeText(s)
}

export function isBvid(s) {
  return BV_RE.test(String(s || ''))
}

export function isAwemeId(s) {
  return AWEME_RE.test(String(s || ''))
}

export function isNoteId(s) {
  return NOTE_RE.test(String(s || ''))
}

export function isZhihuId(s) {
  return ZHIHU_RE.test(String(s || ''))
}

export function extractId(platform, text) {
  const s = String(text || '')
  if (platform === 'bilibili') return (s.match(/BV[0-9A-Za-z]{10}/) || [''])[0]
  if (platform === 'douyin') {
    const m = s.match(/(?:video\/|aweme_id["'=:\s]+)(\d{15,25})/)
    return m ? m[1] : ''
  }
  if (platform === 'zhihu') {
    const m = s.match(/(?:zvideo|pin)\/(\d{10,25})/)
    return m ? m[1] : ''
  }
  if (platform === 'xiaohongshu') {
    const m = s.match(/(?:[?&]id=|noteId["'=:\s]+)([0-9a-f]{24})/)
    return m ? m[1] : ''
  }
  return ''
}

export function matchUnique(rows, want, textOf = (r) => r) {
  const w = normalizeTitle(want)
  const hits = rows.filter((r) => normalizeTitle(textOf(r)) === w)
  return { count: hits.length, row: hits.length === 1 ? hits[0] : null }
}

export function oldPath(dir) {
  return join(dir, 'old.json')
}

export function loadOld(dir) {
  return readJson(oldPath(dir))
}

// old.json 是删除前的事实快照，一旦写过就不许被后来的读数悄悄改写。
export function saveOld(dir, data) {
  const p = oldPath(dir)
  if (!existsSync(p)) {
    writeJson(p, data)
    return 'created'
  }
  const prev = readJson(p)
  const prevP = prev.platforms || {}
  const nextP = data.platforms || {}
  for (const [platform, value] of Object.entries(nextP)) {
    // 未完成的旧记录只是“没读到”，不是快照；允许补全，完整记录才不可改。
    if (prevP[platform] && !isIncomplete(prevP[platform]) && JSON.stringify(prevP[platform]) !== JSON.stringify(value)) {
      throw new ArchiveConflict(
        `old.json 里 ${platform} 的存档与本次读数不一致：${p}\n  已存=${JSON.stringify(prevP[platform])}\n  本次=${JSON.stringify(value)}\n  先手工核对，不覆盖`,
      )
    }
  }
  const merged = { ...prev, platforms: { ...prevP, ...nextP } }
  if (JSON.stringify(merged) === JSON.stringify(prev)) return 'unchanged'
  writeJson(p, merged)
  return 'merged'
}

export function publishTitle(ep, platform) {
  const p = ep.publish?.[platform]
  if (platform === 'xiaohongshu') return p?.title || ''
  return p?.titles?.[0] || p?.title || ''
}

function readText(p) {
  return existsSync(p) ? readFileSync(p, 'utf8') : ''
}

function lastJsonl(p, ep) {
  const lines = readText(p).split('\n').filter(Boolean)
  let hit = null
  for (const line of lines) {
    try {
      const j = JSON.parse(line)
      if (j.ep === ep) hit = j
    } catch {
      /* 坏行不参与匹配 */
    }
  }
  return hit
}

export function collectHints(ep) {
  const root = join(REPO_ROOT, '.temp')

  const bvidFile = readText(join(root, 'bili-web-run', `${ep}.bvid`)).trim()
  const biliLine = lastJsonl(join(root, 'bili-web-run', 'published.jsonl'), ep)
  const biliId = isBvid(bvidFile) ? bvidFile : isBvid(biliLine?.bvid) ? biliLine.bvid : ''

  const dyText = readText(join(root, 'douyin-run', `${ep}-published.txt`))
  const dyId = extractId('douyin', dyText)

  const zhText = readText(join(root, 'zh-run', `${ep}-published.txt`))
  const zhId = extractId('zhihu', zhText)

  const xhsText = readText(join(root, 'xhs-run', `${ep}-published.txt`))
  const xhsId = extractId('xiaohongshu', xhsText)
  const xhsAt = (xhsText.match(/^published_at:\s*(.+)$/m) || [])[1]?.trim() || ''

  return {
    bilibili: {
      id: biliId,
      at: biliLine?.at || '',
      source: biliId ? 'bili-web-run/(.bvid|published.jsonl)' : '',
      note: biliLine?.note || '',
    },
    douyin: {
      id: dyId,
      at: '',
      source: dyId ? 'douyin-run/<ep>-published.txt' : '',
      note: dyText.split('\n')[0]?.slice(0, 160) || '',
    },
    zhihu: {
      id: zhId,
      at: '',
      source: zhId ? 'zh-run/<ep>-published.txt' : '',
      note: zhText.split('\n')[0]?.slice(0, 160) || '',
    },
    xiaohongshu: {
      id: xhsId,
      at: xhsAt,
      source: xhsId ? 'xhs-run/<ep>-published.txt' : '',
      note: xhsText.split('\n')[0]?.slice(0, 160) || '',
    },
  }
}

export function isIncomplete(p) {
  return !p || !p.id || (Array.isArray(p.unavailable) && p.unavailable.length > 0)
}

async function readPlatform(platform, ep, title, hint, dir) {
  const { default: adapter } = await import(`./adapters/${platform}.mjs`)
  try {
    return await withPage(
      (page) => {
        page.on('dialog', (d) => d.dismiss().catch(() => {}))
        return adapter.readOld(page, { ep, title, hint, dir })
      },
      { url: adapter.managerUrl, waitMs: platform === 'xiaohongshu' ? 9000 : 6000 },
    )
  } catch (e) {
    return {
      id: hint?.id || null,
      title,
      duration: null,
      cover: '',
      collection: '',
      publishedAt: hint?.at || '',
      evidence: hint?.source ? `台账线索：${hint.source}；页面读取失败：${e.message.split('\n')[0]}` : `页面读取失败：${e.message.split('\n')[0]}`,
      unavailable: ['row', `error:${e.message.split('\n')[0]}`],
    }
  }
}

async function main() {
  const args = parseArgs()
  const ep = requireEp(args)
  const epData = loadEpisode(ep)
  const date = args.date || today()
  const dir = dayDir(ep, date)
  const platforms = args.platform ? [args.platform] : ['bilibili', 'douyin', 'zhihu', 'xiaohongshu']
  const hints = collectHints(ep)

  const platformsOut = {}
  for (const platform of platforms) {
    const title = publishTitle(epData, platform)
    if (!title) throw new Error(`${ep} 的 episode.json 没有 ${platform} 发布标题——不猜`)
    const data = await readPlatform(platform, ep, title, hints[platform], dir)
    platformsOut[platform] = data
    const missing = isIncomplete(data) ? ` 未完成[${(data.unavailable || []).join(',')}]` : ''
    console.log(`${platform.padEnd(12)} id=${data.id || '(null)'}${missing}`)
  }

  const old = { ep, archivedAt: new Date().toISOString(), platforms: platformsOut }
  const state = saveOld(dir, old)
  console.log(`\nold.json: ${state} → ${oldPath(dir)}`)

  const incomplete = platforms.filter((p) => isIncomplete(platformsOut[p]))
  if (incomplete.length) {
    console.log(`\n⚠ 未完成：${incomplete.join(' / ')}——缺 id 或页面读不到。先补归档，不进入删除。`)
    process.exitCode = 4
  } else {
    console.log('\n✓ 归档齐全。')
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main()
    .then(() => exitAfterFlush(process.exitCode || 0))
    .catch((e) => {
      console.error(`✗ ${e.message}`)
      return exitAfterFlush(e.exitCode || 1)
    })
}
