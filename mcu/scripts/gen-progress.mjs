/**
 * 章节进度事实源生成器：扫描 docs/ 各板块章节的 frontmatter，
 * 产出 docs/.vitepress/data/progress.json 供首页学习地图与统计数字使用。
 *
 * 为什么要有这个脚本：成稿数/动画数/实验数曾经靠手写，结果 README、
 * CONTRIBUTING 与站内三处数字各说各话。数字一律由本脚本从文件算出来。
 *
 * 用法：node scripts/gen-progress.mjs（docs:dev / docs:build 已自动前置执行）
 */
import fs from 'node:fs'
import path from 'node:path'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { loadCurriculum } from './curriculum.mjs'
import { loadProjects } from './project-catalog.mjs'
import { readMetadata, readLabMetadata } from './content-metadata.mjs'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const DOCS = path.join(ROOT, 'docs')
const OUT = path.join(DOCS, '.vitepress', 'data', 'progress.json')

const TRACKS = [
  { key:'projects', name:'双板综合项目', dir:'projects' },
  { key: 'c', name: 'C 语言精髓', dir: 'c' },
  { key: 'build', name: '构建与运行全过程', dir: 'build' },
  { key: 'stm32', name: 'STM32F407 寄存器主线', dir: 'stm32' },
  // rtos 三个子路线共用 rtos/index.md 导览，没有各自的板块首页
  { key: 'freertos', name: 'FreeRTOS 精讲', dir: 'rtos/freertos', landing: '/rtos/index.html' },
  { key: 'rtthread', name: 'RT-Thread 精讲', dir: 'rtos/rtthread', landing: '/rtos/index.html' },
  { key: 'compare', name: '双 OS 对照与选型', dir: 'rtos/compare', landing: '/rtos/index.html' },
  { key: 'esp32', name: 'ESP32-S3 + ESP-IDF', dir: 'esp32' },
  { key: 'gd32', name: 'GD32 双系对照', dir: 'gd32' },
  { key: 'ai', name: 'AI 辅助开发', dir: 'ai' },
  { key: 'lab', name: '实物实验中心', dir: 'lab', prefix: 'e' },
]

const chapterPattern = (t) => (t.prefix ? new RegExp(`^${t.prefix}\\d\\d-`) : /^\d\d-/)

const catalog = loadProjects(ROOT)
const curriculum = loadCurriculum(ROOT)
function readFrontmatter(file) { return readMetadata(fs.readFileSync(file, 'utf8'), path.relative(ROOT, file)) }

const tracks = TRACKS.map((t) => {
  const dir = path.join(DOCS, t.dir)
  const pattern = chapterPattern(t)
  const files = fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => pattern.test(f) && f.endsWith('.md')) : []
  const chapters = files.map((f) => {
    const fm = readFrontmatter(path.join(dir, f))
    const rel = `${t.dir}/${f.replace(/\.md$/, '')}`
    return {
      id: curriculum.find(e => e.path === `docs/${rel}.md`)?.id || rel,
      title: fm.title,
      route: `/${rel}.html`,
      status: fm.status === 'done' ? 'done' : 'building',
      difficulty: fm.difficulty,
      minutes: fm.minutes,
      ...((t.key === 'lab' || fm.hardware_status) ? readLabMetadata(fm, catalog, DOCS, rel) : {}),
    }
  })
  const built = chapters.length
  for (const e of curriculum.filter(e => e.track === t.key && !e.path)) chapters.push({ id:e.id, title:e.title, route:null, status:'planned', difficulty:0, minutes:0 })
  for (const c of chapters.filter(c => c.route)) if(t.key !== 'lab' && !curriculum.some(e => e.path === `docs${c.route.replace(/\.html$/, '.md')}`)) throw Error(`课程未登记: ${c.route}`)
  const done = chapters.filter((c) => c.status === 'done').length
  return { ...t, chapters, done, built, total: chapters.length }
})

const listFiles = (dir, filter = () => true) =>
  fs.existsSync(dir) ? fs.readdirSync(dir).filter(filter) : []

const animations = listFiles(path.join(DOCS, 'public', 'anim'), (f) => f.endsWith('.svg')).length
const projects = catalog.length

const chapters = tracks.filter((t) => t.key !== 'lab')
const experiments = tracks.find((t) => t.key === 'lab')
const totals = {
  chapters: chapters.reduce((n, t) => n + t.total, 0),
  chaptersDone: chapters.reduce((n, t) => n + t.done, 0),
  experiments: experiments.total,
  experimentsDone: experiments.done,
  experimentsReady: experiments.chapters.filter(c => c.codeStatus === 'ready').length,
  experimentsVerified: experiments.chapters.filter(c => c.hardwareStatus === 'verified').length,
  animations,
  projects,
  minutes: chapters.reduce((n, t) => n + t.chapters.filter((c) => c.status === 'done').reduce((s, c) => s + c.minutes, 0), 0),
}

fs.mkdirSync(path.dirname(OUT), { recursive: true })
fs.writeFileSync(OUT, JSON.stringify({ totals, tracks }, null, 2) + '\n', 'utf8')

console.log(
  `成稿章节 ${totals.chaptersDone}/${totals.chapters} · 实验 ${totals.experimentsDone}/${totals.experiments} · ` +
    `动画 ${totals.animations} · 示例工程 ${totals.projects}`
)

/* ---------------- 最近更新流：从 git 历史取最近改动的章节页，供首页"最近更新"板块 ---------------- */
// 与进度数字同一个道理——"最近更新了什么"也不能靠手写，手写的第一版就会开始说谎。
// 无 .git（如源码包构建）或 git 失败时降级为空列表，首页板块自动隐藏，不阻断构建。
const UPDATES_OUT = path.join(DOCS, '.vitepress', 'data', 'updates.json')
const UPDATE_LIMIT = 8

const trackOf = (rel) => {
  const t = TRACKS.map((x) => (rel === x.dir || rel.startsWith(x.dir + '/') ? x : null)).find(Boolean)
  if (t) return t
  return rel.startsWith('video/') ? { name: '视频脚本' } : null
}

function collectUpdates() {
  // 合并进 STM32 单仓后，本站历史分两段、路径形态不同：
  //  - post-import 提交：mcu/docs/**
  //  - subtree 导入的 pre-import MCU 历史：路径仍是 docs/**，且与 STM32 书自己的
  //    旧 docs/** 混在同一个 git 对象库里——所以 pre-import 段必须沿 MCU 血统
  //    （导入 merge 的第二父）走，不能按路径前缀猜；漏网路径由存在性过滤挡掉。
  const run = (args) => {
    try {
      return execFileSync('git', ['log', ...args], { cwd: ROOT, encoding: 'utf8', maxBuffer: 8 << 20, stdio: ['ignore', 'pipe', 'ignore'] })
    } catch {
      return ''
    }
  }
  const merges = run(['--merges', '--format=%H', '--', ':(top)mcu']).trim().split('\n').filter(Boolean)
  const importMerge = merges[merges.length - 1] || null
  const sources = importMerge
    ? [
        ['-n', '300', '--no-merges', '--name-only', '--date=short', '--pretty=format:@%ad', 'HEAD', '--', ':(top)mcu/docs'],
        ['-n', '300', '--no-merges', '--name-only', '--date=short', '--pretty=format:@%ad', `${importMerge}^2`, '--', ':(top)docs'],
      ]
    : [['-n', '300', '--no-merges', '--name-only', '--date=short', '--pretty=format:@%ad', '--', ':(top)docs']]
  const entries = []
  for (const raw of sources.map(run)) {
    let date = ''
    for (const line of raw.split(/\r?\n/)) {
      if (line.startsWith('@')) { date = line.slice(1).trim(); continue }
      const f = line.trim()
      let rel = null
      if (f.startsWith('mcu/docs/')) rel = f.slice('mcu/docs/'.length)
      else if (f.startsWith('docs/')) rel = f.slice('docs/'.length)
      else continue
      if (!rel.endsWith('.md') || rel.includes('/public/') || rel.includes('/.vitepress/')) continue
      // 只收子目录章节页；根目录 index.md / 404.md 属于站点外壳，不是"内容更新"
      if (!rel.includes('/')) continue
      // 非本站章节（如 STM32 书自己的旧 docs/**）不挂"最近更新"
      if (!fs.existsSync(path.join(DOCS, rel))) continue
      entries.push({ date, rel })
    }
  }
  entries.sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0))
  const seen = new Set()
  const items = []
  for (const { date, rel } of entries) {
    const id = rel.replace(/\.md$/, '')
    if (seen.has(id)) continue
    seen.add(id)
    let title
    try {
      title = readFrontmatter(path.join(DOCS, rel)).title
    } catch {
      // 非章节页（如视频分镜）没有 frontmatter，取正文首个一级标题
      const body = fs.readFileSync(path.join(DOCS, rel), 'utf8')
      title = body.match(/^#\s+(.+)$/m)?.[1]?.trim() || path.basename(id)
    }
    const t = trackOf(id)
    items.push({
      route: '/' + id + '.html',
      title,
      track: t ? t.name : '站点',
      date,
    })
    if (items.length >= UPDATE_LIMIT) break
  }
  return items
}

fs.writeFileSync(UPDATES_OUT, JSON.stringify({ items: collectUpdates() }, null, 2) + '\n', 'utf8')

/* ---------------- README 进度块：与首页同源，杜绝"数字三处各说各话"复发 ---------------- */
// README 里的成稿数/动画数/工程数与"现在能读到哪些章"必须由同一份扫描结果渲染。
// 上一版 README 手写数字，结果写成 21/66 与 11 个工程，脚本算出来是 23/66 与 13 个。
const MARK_START = '<!-- readme:progress:start -->'
const MARK_END = '<!-- readme:progress:end -->'

const shortTitle = (t) => t.split(/[：:]/)[0].trim()

function renderProgressBlock(trk, tot) {
  const rows = trk.map((t) => {
    const landing = t.landing ? t.landing.replace(/^\//, 'docs/').replace(/\.html$/, '.md') : `docs/${t.dir}/index.md`
    const doneList = t.chapters.filter((c) => c.status === 'done')
    const links = doneList.length
      ? doneList.map((c) => `[${shortTitle(c.title)}](docs${c.route.replace(/\.html$/, '.md')})`).join(' · ')
      : '_骨架页已建档，正文待补_'
    return `| [${t.name}](${landing}) | ${t.done} / ${t.total}（${t.built}） | ${links} |`
  })
  const hours = (tot.minutes / 60).toFixed(1)
  return [
    '| 板块 | 成稿 / 规划（已建档） | 现在就能点进去读 |',
    '|---|---|---|',
    ...rows,
    '',
    `- 成稿章节 **${tot.chaptersDone} / ${tot.chapters}**（上表「实物实验」那一行的 ${tot.experimentsDone} 篇另计，不进章节数），通读约 **${tot.minutes} 分钟**（≈ ${hours} 小时）；`,
    `- 实物实验 **${tot.experimentsDone} / ${tot.experiments}**（文稿成稿；完整配套工程 ${tot.experimentsReady} 项，上板验证 ${tot.experimentsVerified} 项）；`,
    `- 机制动画 **${tot.animations}** 张，在 \`docs/public/anim/\`，动效与版式规范见 \`.trellis/spec/docs-site/animation.md\`；`,
    `- 示例工程 **${tot.projects}** 个，在 \`code/\`，与章节同构；`,
    '- 章节 frontmatter 元数据校验已通过（缺项或非法值会阻止构建）。',
  ].join('\n')
}

const readmePath = path.join(ROOT, 'README.md')
const start = process.argv.indexOf('--readme')
if (start > -1) {
  const src = fs.readFileSync(readmePath, 'utf8')
  const i = src.indexOf(MARK_START)
  const j = src.indexOf(MARK_END)
  if (i < 0 || j < 0) {
    console.error(`README.md 缺少 ${MARK_START} … ${MARK_END} 标记块`)
    process.exit(1)
  }
  const body = renderProgressBlock(tracks, totals)
  const next = src.slice(0, i + MARK_START.length) + '\n' + body + '\n' + src.slice(j)
  if (next !== src) {
    if (process.argv.includes('--check')) {
      console.error('README.md 的进度块与扫描结果不一致，跑 `npm run readme:sync` 再提交。')
      process.exit(1)
    }
    fs.writeFileSync(readmePath, next, 'utf8')
    console.log('README.md 进度块已同步')
  } else {
    console.log('README.md 进度块已是最新')
  }
}
