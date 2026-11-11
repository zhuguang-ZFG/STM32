import { existsSync } from 'node:fs'
import { join } from 'node:path'
import { pathToFileURL } from 'node:url'
import { REPO_ROOT } from '../../src/util.mjs'
import { OUT_DIR } from '../../src/util.mjs'
import { parseArgs, requireEp, requirePlatform, runNode, exitAfterFlush } from './common.mjs'

// 抖音链路照 dy-post-one.mjs 的发布前段落抄，不要用诊断步（status/topicprobe/links）凑：
// 冷启动时没有盖章页，status 会直接拒绝；封面也必须走模态流（cover/coveredit/coverup/coverset），
// 只喂 input[type=file] 会让竖封面退回视频首帧（线上六条就是这么坏的）。
const FLOWS = {
  bilibili: ['open', 'feed', 'wait', 'fill', 'check'],
  douyin: [
    ['nav', '--url', 'https://creator.douyin.com/creator-micro/content/upload'],
    ['pick'],
    ['retxt'],
    ['cover', '--slot', '0'],
    ['coveredit', '--which', 'v'],
    ['coverup', '--which', 'v'],
    ['coverset', '--which', 'v'],
    ['coverup', '--which', 'h'],
    ['coverset', '--which', 'h'],
    ['seasonpick'],
    ['declare'],
    ['title'],
    ['verify'],
  ],
  zhihu: [],
  // 合集在发布表单里由 attach 选中；collection/collectioncheck 认领的是**已发布笔记**的编辑页，
  // 只能发布后跑。旧稿在时它们会误挂到旧笔记上，删稿后则直接找不到卡片——不要放回发布前。
  xiaohongshu: ['open', 'upload', 'fill', 'topics', 'cover', 'coverset', 'coverapply', 'attach'],
}

const SCRIPT = {
  bilibili: 'bili-web.mjs',
  douyin: 'douyin-step.mjs',
  xiaohongshu: 'xhs-step.mjs',
}

function artifacts(ep, platform) {
  const dir = join(OUT_DIR, ep)
  const video = {
    bilibili: 'bilibili.mp4',
    douyin: 'douyin.mp4',
    zhihu: 'bilibili.mp4',
    xiaohongshu: 'douyin.mp4',
  }[platform]
  const cover = {
    bilibili: 'bilibili-cover.png',
    douyin: 'douyin-cover.png',
    zhihu: 'zhihu-cover.png',
    xiaohongshu: 'xiaohongshu-cover.png',
  }[platform]
  const files = [join(dir, video), join(dir, cover), join(dir, `发布-${platform}.md`)]
  if (platform === 'bilibili') files.push(join(dir, 'bili-submit.yaml'))
  return files
}

function check(ep, platform) {
  const missing = artifacts(ep, platform).filter((p) => !existsSync(p))
  if (missing.length) {
    throw new Error(`产物不齐，先跑 build/cover/pack：\n${missing.map((p) => `  - ${p}`).join('\n')}`)
  }
}

function stepsFor(ep, platform) {
  if (platform === 'zhihu') {
    // zh-one.mjs 的 arg 只认空格形式（process.argv.indexOf('--ep')），传 --ep=x 会当场报「--ep 没给」。
    return [{ script: 'zh-one.mjs', args: ['--ep', ep], label: `zh-one.mjs --ep ${ep}（填到发布前）` }]
  }
  return FLOWS[platform].map((s) => {
    const [name, ...extra] = Array.isArray(s) ? s : [s]
    return {
      script: SCRIPT[platform],
      args: [name, ...extra, `--ep=${ep}`],
      label: `${SCRIPT[platform]} ${[name, ...extra].join(' ')} --ep ${ep}`,
    }
  })
}

function main() {
  const args = parseArgs()
  const ep = requireEp(args)
  const platform = requirePlatform(args)
  check(ep, platform)
  const steps = stepsFor(ep, platform)

  console.log(`▶ ${ep} / ${platform}：${steps.length} 步（不含发布）`)
  for (const [i, s] of steps.entries()) console.log(`  ${i + 1}. ${s.label}`)

  if (!args.run) {
    console.log('\n只打印步骤；加 --run 才依次执行。执行完停在发布前。')
    return
  }

  for (const [i, s] of steps.entries()) {
    console.log(`\n▶ [${i + 1}/${steps.length}] ${s.label}`)
    const code = runNode(s.script, s.args)
    if (code !== 0) throw new Error(`第 ${i + 1} 步失败（exit ${code}），停在这里，不带着半填表单往下走`)
  }
  console.log('\n表单已就位，先删旧稿；不要关这个标签页。')
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
