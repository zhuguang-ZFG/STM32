import { join } from 'node:path'
import { pathToFileURL } from 'node:url'
import { loadEpisode } from '../../src/spec.mjs'
import {
  UnknownError,
  appendEvent,
  consumeGate,
  exitAfterFlush,
  parseArgs,
  readJson,
  requireEp,
  requireGate,
  requirePlatform,
  requirePlatformGate,
  runDirFor,
  runNode,
  writeJson,
} from './common.mjs'
import { verifyAfter } from './verify.mjs'

const COMMANDS = {
  bilibili: (ep, args) => ['bili-web.mjs', ['publish', `--ep=${ep}`, `--decl=${args.decl || ''}`]],
  douyin: (ep) => ['douyin-step.mjs', ['publish', `--ep=${ep}`]],
  // zh-one 的 arg 只认空格形式（--ep x），传 --ep=x 会被当成没给集号。
  zhihu: (ep) => ['zh-one.mjs', ['--ep', ep, '--publish']],
  xiaohongshu: (ep) => ['xhs-step.mjs', ['publish', `--ep=${ep}`, '--go']],
}

async function main() {
  const args = parseArgs()
  const ep = requireEp(args)
  const platform = requirePlatform(args)
  const [script, scriptArgs] = COMMANDS[platform](ep, args)
  const dir = runDirFor(ep, args.date)

  if (!args.go) {
    console.log('只读：未给 --go，不点任何平台按钮。')
    console.log(`  repost 闸门：${join(dir, `I_HAVE_USER_OK_PUBLISH_${ep}`)}`)
    console.log(`  平台闸门：见 .temp/*-run/I_HAVE_USER_OK=${ep}`)
    console.log(`  将执行：node video/publish/${script} ${scriptArgs.join(' ')}`)
    return
  }

  if (platform === 'bilibili' && !args.decl) {
    throw new UnknownError('B站发布必须给 --decl（创作声明发布后锁死，不能赌默认值）')
  }
  const gate = requireGate('publish', ep, dir)
  requirePlatformGate(platform, ep, gate)
  console.log(`闸门：${JSON.stringify(gate)}`)
  console.log(`▶ node video/publish/${script} ${scriptArgs.join(' ')}`)

  let publishCode = null
  let verify = null
  let verifyError = null
  try {
    publishCode = runNode(script, scriptArgs)
    try {
      verify = await verifyAfter(ep, platform, { date: args.date })
    } catch (e) {
      verifyError = e.message
    }
  } finally {
    consumeGate('publish', ep, dir)
  }

  const row = verify?.row
  if (row?.id) {
    const newPath = join(dir, 'new.json')
    const doc = readJson(newPath) || { ep, archivedAt: new Date().toISOString(), platforms: {} }
    doc.platforms[platform] = {
      ...row,
      verified: !!verify.ok,
      unknown: verify?.unknown || [],
      publishedAt: new Date().toISOString(),
    }
    writeJson(newPath, doc)
    appendEvent(dir, {
      action: 'publish',
      platform,
      gate,
      exit: publishCode,
      newId: row.id,
      verified: !!verify.ok,
      unknown: verify?.unknown || [],
    })
    if (!verify.ok) {
      console.log(`⚠ 平台命令 exit=${publishCode}，已回读到新 ID ${row.id}，但核对未全绿：${verify.unknown.join(' / ') || '见 checks'}`)
    }
    if (publishCode !== 0) console.log(`⚠ 平台命令 exit=${publishCode}，但已回读到新 ID——按已发布处理，不重投`)
    return
  }

  appendEvent(dir, {
    action: 'publish',
    platform,
    gate,
    exit: publishCode,
    unknown: verifyError || '没有回读到新 ID',
  })
  throw new UnknownError(
    `发布未确认：命令 exit=${publishCode}${verifyError ? `；回读失败：${verifyError}` : '；回读没有新 ID'}——不要重投，先人工核`,
  )
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  main()
    .then(() => exitAfterFlush(process.exitCode || 0))
    .catch((e) => {
      console.error(`✗ ${e.message}`)
      return exitAfterFlush(e.exitCode || 1)
    })
}
