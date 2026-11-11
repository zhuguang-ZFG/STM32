import { join } from 'node:path'
import { pathToFileURL } from 'node:url'
import { loadEpisode } from '../../src/spec.mjs'
import { publishTitle } from './archive.mjs'
import {
  UnknownError,
  appendEvent,
  consumeGate,
  dayDir,
  exitAfterFlush,
  parseArgs,
  readJson,
  requireEp,
  requireGate,
  requirePlatform,
  runDirFor,
  withPage,
  writeJson,
} from './common.mjs'

async function adapterFor(platform) {
  return (await import(`./adapters/${platform}.mjs`)).default
}

async function main() {
  const args = parseArgs()
  const ep = requireEp(args)
  const platform = requirePlatform(args)
  const adapter = await adapterFor(platform)
  const old = readJson(join(runDirFor(ep, args.date), 'old.json'))
  const oldPlatform = old?.platforms?.[platform] || null
  const title = args.title || oldPlatform?.title || publishTitle(loadEpisode(ep), platform)
  if (!title) throw new UnknownError(`${ep} 没有 ${platform} 标题，无法按标题锁定行`)

  if (!args.go) {
    const dir = dayDir(ep, args.date)
    const found = await withPage(
      (page) => adapter.probeOld(page, { ep, title, hint: oldPlatform }),
      { url: adapter.managerUrl, waitMs: platform === 'xiaohongshu' ? 9000 : 6000 },
    )
    writeJson(join(dir, `delete-probe-${platform}.json`), { at: new Date().toISOString(), ep, platform, title, ...found })
    console.log(`只读探针：找到 ${found.rows?.length ?? 0} 行；未点击删除。`)
    console.log(`  ${join(dir, `delete-probe-${platform}.json`)}`)
    return
  }

  const dir = runDirFor(ep, args.date)
  const gate = requireGate('delete', ep, dir)
  if (!args.manual && !oldPlatform?.id) {
    throw new UnknownError('old.json 没有旧 ID——先补归档，不能凭标题猜着删')
  }

  try {
    const res = args.manual
      ? await withPage((page) => adapter.confirmManualDeleted(page, { ep, title, old: oldPlatform }), {
          url: adapter.managerUrl,
          waitMs: platform === 'xiaohongshu' ? 9000 : 6000,
        })
      : await withPage((page) => adapter.deleteOld(page, { ep, title, old: oldPlatform }), {
          url: adapter.managerUrl,
          waitMs: platform === 'xiaohongshu' ? 9000 : 6000,
        })
    if (res.verified === false) throw new UnknownError('删除后回读仍能看到旧行')
    writeJson(join(dir, `delete-${platform}.json`), { at: new Date().toISOString(), ep, platform, gate, ...res })
    appendEvent(dir, { action: 'delete', platform, gate, ...res })
    consumeGate('delete', ep, dir)
    console.log(`✓ 删除完成：${JSON.stringify(res)}`)
  } catch (e) {
    appendEvent(dir, { action: 'delete', platform, gate, unknown: e.message })
    consumeGate('delete', ep, dir)
    throw e
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
