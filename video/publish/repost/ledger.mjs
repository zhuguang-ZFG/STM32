import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { pathToFileURL } from 'node:url'
import {
  exitAfterFlush,
  parseArgs,
  readJson,
  requireEp,
  runDirFor,
} from './common.mjs'

function events(dir) {
  const p = join(dir, 'events.jsonl')
  if (!existsSync(p)) return []
  return readFileSync(p, 'utf8')
    .split('\n')
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line)
      } catch {
        return { malformed: line }
      }
    })
}

function main() {
  const args = parseArgs()
  const ep = requireEp(args)
  const dir = runDirFor(ep, args.date)
  const old = readJson(join(dir, 'old.json'))
  const fresh = readJson(join(dir, 'new.json'))
  const evs = events(dir)

  console.log(`ep=${ep}  dir=${dir}`)
  console.log('\n旧稿：')
  if (!old?.platforms) console.log('  (缺 old.json)')
  else {
    for (const [p, v] of Object.entries(old.platforms)) {
      console.log(`  ${p.padEnd(12)} id=${v.id || '(null)'}  ${v.title || ''}`)
      if (v.unavailable?.length) console.log(`  ${''.padEnd(12)} 未完成：${v.unavailable.join(',')}`)
    }
  }

  console.log('\n新稿：')
  if (!fresh?.platforms) console.log('  (缺 new.json——未完成)')
  else {
    for (const [p, v] of Object.entries(fresh.platforms)) {
      const state = v.verified ? '✓' : `未全绿[${(v.unknown || []).join(',') || 'checks'}]`
      console.log(`  ${p.padEnd(12)} id=${v.id || '(null)'}  ${state}`)
      console.log(`  ${''.padEnd(12)} old=${old?.platforms?.[p]?.id || '(无)'} → new=${v.id || '(无)'}`)
    }
  }

  console.log('\n事件：')
  if (!evs.length) console.log('  (无)')
  for (const e of evs) {
    const tail = e.unknown ? `unknown=${e.unknown}` : e.newId ? `new=${e.newId}` : e.deleted ? 'deleted' : ''
    console.log(`  ${e.at || '(无时间)'} ${e.action || '?'} ${e.platform || ''} ${tail}`)
  }

  const missing = Object.keys(old?.platforms || {}).filter((p) => !fresh?.platforms?.[p])
  if (missing.length) console.log(`\n未完成：${missing.join(' / ')}`)
  else if (!fresh) console.log('\n未完成：整集')
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    main()
    exitAfterFlush(0)
  } catch (e) {
    console.error(`✗ ${e.message}`)
    exitAfterFlush(e.exitCode || 1)
  }
}
