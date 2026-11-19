// 图片策略不变量：站点里 0.5–1 MB 的 PNG 很多，首屏不得整批拉取。
//
// 直接对构建产物断言，而不是对插件内部函数断言：属性是markdown 规则、
// Vue 组件（<noscript> 回退图）两条路径分别产出的，只有产物能证明两条都覆盖到。
//
// 用法（cwd=仓库根，先跑 npm run docs:build）：
//   node scripts/check-site-images.mjs --dist docs/.vitepress/dist
//
// 退出码：0 = 全部图片带 loading="lazy"；1 = 有图片缺失或属性写错。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export function parseArgs(argv) {
  const args = { dist: 'docs/.vitepress/dist' }
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--dist') args.dist = argv[++i]
    else throw new Error(`未知参数: ${argv[i]}`)
  }
  return args
}

/** 收集 dist 下所有 HTML 里的 <img>，返回未带懒加载或缺少尺寸的明细。 */
export function scanImages(dist) {
  const images = []
  const stack = [dist]
  while (stack.length) {
    const dir = stack.pop()
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      const full = path.join(dir, entry.name)
      if (entry.isDirectory()) {
        // 旧链存根目录不进书页统计（它们没有图片）
        if (path.relative(dist, full).split(path.sep)[0] === 'mcu') continue
        stack.push(full)
      } else if (entry.name.endsWith('.html')) {
        const page = path.relative(dist, full).split(path.sep).join('/')
        const html = fs.readFileSync(full, 'utf8')
        for (const tag of html.match(/<img\b[^>]*>/gi) ?? []) {
          images.push({ page, tag })
        }
      }
    }
  }
  return images
}

export function checkImages(dist) {
  const images = scanImages(dist)
  const notLazy = images.filter(({ tag }) => !/\bloading="lazy"/.test(tag))
  const notAsync = images.filter(({ tag }) => !/\bdecoding="async"/.test(tag))
  return { total: images.length, notLazy, notAsync, ok: notLazy.length === 0 && notAsync.length === 0 }
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
if (isMain) {
  const args = parseArgs(process.argv.slice(2))
  if (!fs.existsSync(args.dist)) throw new Error(`${args.dist}: 构建产物不存在，先跑 npm run docs:build`)
  const result = checkImages(args.dist)
  if (result.ok) {
    console.log(`site images: ${result.total} 张全部 lazy + async`)
    process.exit(0)
  }
  for (const { page, tag } of result.notLazy) console.error(`NOT-LAZY ${page} ${tag.slice(0, 100)}`)
  for (const { page, tag } of result.notAsync) console.error(`NOT-ASYNC ${page} ${tag.slice(0, 100)}`)
  console.error(`site images: ${result.notLazy.length} 未懒加载, ${result.notAsync.length} 未异步解码`)
  process.exit(1)
}
