// 站点产物剪枝：public/ 里有些早期命名的手绘图已不再被任何章节引用，
// 但 VitePress 会把 public/ 整目录拷进 dist 并随 Pages 一起上传。
//
// 只剪 dist、不碰仓库源文件；只剪确定未被引用的资源（位图与 SVG），且永不触碰
// assets/（VitePress 打包产物）、scenes/（运行时 JSON + canvas 脚本）。
//
// 引用来源必须齐全，否则会把运行时图片误删：
//   1. 所有构建出的 HTML（src/href/figure-zoom 都在这里）
//   2. CSS 里的 url(...)
//   3. scenes.json 与 scenes/*.json（StickScene 回退图）
//   4. public/scenes/*.js（canvas 运行时）
//
// 用法（cwd=仓库根，在 docs:build 之后）：
//   node scripts/prune-site-assets.mjs --dist docs/.vitepress/dist --dry-run
//   node scripts/prune-site-assets.mjs --dist docs/.vitepress/dist
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const PRUNABLE_EXT = /\.(png|jpe?g|gif|webp|svg)$/i
/** 永不剪：打包产物与运行时目录。 */
const KEEP_DIRS = new Set(['assets', 'scenes'])

export function parseArgs(argv) {
  const args = { dist: 'docs/.vitepress/dist', publicDir: 'docs/public', dryRun: false }
  for (let i = 0; i < argv.length; i += 1) {
    const key = argv[i]
    if (key === '--dist') args.dist = argv[++i]
    else if (key === '--public-dir') args.publicDir = argv[++i]
    else if (key === '--dry-run') args.dryRun = true
    else throw new Error(`未知参数: ${key}`)
  }
  return args
}

function walk(dir, out = []) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) walk(full, out)
    else out.push(full)
  }
  return out
}

/**
 * 汇总所有可能引用资源名的文本：HTML、CSS、VitePress 打包出的 JS
 * （`scenes.json` 会整份嵌进 bundle，905 条资源路径在那里）、
 * 以及 public 下的运行时 JSON 与脚本。
 * 用「文件名出现」而不是精确路径，宁可少剪也不要剪掉被引用的图。
 */
export function collectReferences(dist, publicDir) {
  const parts = []
  for (const file of walk(dist)) {
    if (/\.(html|css|js|mjs)$/i.test(file)) parts.push(fs.readFileSync(file, 'utf8'))
  }
  for (const file of walk(publicDir)) {
    if (/\.(json|js|mjs)$/i.test(file)) parts.push(fs.readFileSync(file, 'utf8'))
  }
  return parts.join('\n')
}

/** 返回可删除的资源：PRUNABLE_EXT 且文件名未在任何引用文本中出现。 */
export function findOrphans(dist, references) {
  const orphans = []
  for (const file of walk(dist)) {
    const rel = path.relative(dist, file).split(path.sep)
    if (KEEP_DIRS.has(rel[0])) continue
    if (!PRUNABLE_EXT.test(file)) continue
    if (references.includes(path.basename(file))) continue
    orphans.push(file)
  }
  return orphans
}

export function pruneSiteAssets({ dist, publicDir, dryRun = false }) {
  if (!fs.existsSync(dist)) throw new Error(`${dist}: 构建产物不存在，先跑 npm run docs:build`)
  const references = collectReferences(dist, publicDir)
  const orphans = findOrphans(dist, references)
  let bytes = 0
  for (const file of orphans) {
    bytes += fs.statSync(file).size
    if (!dryRun) fs.rmSync(file)
  }
  return { removed: orphans.length, bytes, dryRun }
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
if (isMain) {
  const args = parseArgs(process.argv.slice(2))
  const { removed, bytes, dryRun } = pruneSiteAssets(args)
  const mb = (bytes / 1048576).toFixed(1)
  console.log(
    `site prune: ${dryRun ? '将删除' : '删除'} ${removed} 个未被引用的资源（${mb} MB）`,
  )
}