/**
 * 导航可达性检查：每一章都要能从 nav / sidebar 到达。
 *
 * 为什么单独有它：VitePress 的死链门禁只查「链接 → 页面」一个方向（页面不存在就报错），
 * 查不出「页面 → 入口」这个方向——页面写好了却忘了登记进 sidebar，读者在站上根本翻不到，
 * 而构建、死链、元数据三道门全都不会响。项目历史上就漏过一整组 GD32 章节
 * （docs/gd32 有 10 章，侧边栏只列了 1 章），只能靠肉眼发现。
 * 这个脚本把「新页面必须同步进 sidebar」（structure.md 的「四处同步」纪律）从口头约定
 * 变成可执行门禁，方向正好补上死链检查的反面。
 *
 * 用法：node scripts/nav-check.mjs（--quiet 只在出错时输出）
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

/** 从 config.mts 源码抽取所有 link: '<path>'，去锚点/查询串、统一尾斜杠。 */
export function extractLinks(src) {
  const set = new Set()
  const re = /link:\s*'([^']+)'/g
  let m
  while ((m = re.exec(src))) {
    let p = m[1]
    if (/^(https?:|mailto:)/.test(p)) continue
    p = p.split('#')[0].split('?')[0]
    if (p.length > 1) p = p.replace(/\/+$/, '')
    if (p) set.add(p)
  }
  return set
}

/** 递归收集 docs 下所有 .md，归一为路由（index.md → 所在目录；docs/index.md → '/'）。 */
export function collectPages(docsDir) {
  const out = []
  const walk = (dir) => {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const abs = path.join(dir, e.name)
      if (e.isDirectory()) {
        if (e.name === '.vitepress' || e.name === 'public') continue
        walk(abs)
      } else if (e.name.endsWith('.md')) {
        let rel = path.relative(docsDir, abs).replace(/\\/g, '/').replace(/\.md$/, '')
        // 404 是错误兜底页：读者不会从导航进入它，也不该要求它有导航入口。
        if (rel === '404') continue
        if (rel === 'index') rel = ''
        else if (rel.endsWith('/index')) rel = rel.slice(0, -'/index'.length)
        out.push('/' + rel)
      }
    }
  }
  walk(docsDir)
  return out
}

/** 返回 { links, all, missing }：missing 是没有任何 nav/sidebar 入口的页面路由。 */
export function findUnreachable({ docsDir, configFile }) {
  const links = extractLinks(fs.readFileSync(configFile, 'utf8'))
  const all = collectPages(docsDir)
  const missing = all.filter((r) => r !== '/' && !links.has(r) && !links.has(r + '/'))
  return { links, all, missing }
}

const isMain =
  process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href

if (isMain) {
  const { all, missing } = findUnreachable({
    docsDir: path.join(ROOT, 'docs'),
    configFile: path.join(ROOT, 'docs', '.vitepress', 'config.mts'),
  })

  if (missing.length) {
    console.error(`✗ ${missing.length} 个页面不在任何 nav/sidebar 链接中（读者翻不到）：`)
    for (const r of [...missing].sort()) console.error(`  - docs${r}.md`)
    console.error('  修复：登记进 docs/.vitepress/config.mts 的 sidebar，见 structure.md「新页面必须同步四处」。')
    process.exit(1)
  }
  if (!process.argv.includes('--quiet')) {
    console.log(`✓ 全站 ${all.length} 个页面均可从导航到达（nav + sidebar）`)
  }
}
