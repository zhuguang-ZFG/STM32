// Pages staging 组装：把 VitePress 产物装进「上传根含 mcu/ 子树」的结构。
//
// 为什么要独立成脚本而不是 workflow 内联 shell：回归测试要覆盖三种失败模式
// （缺 mcu/index、根入口被站点首页顶掉、资源落在 mcu/ 之外），脚本可以被
// 单测用 fixture 直接驱动，workflow 只负责传参。挂载语义见 plans/2026-11-11-mcu-merge。
//
// 用法（cwd=mcu/）：node scripts/assemble-pages.mjs --dist site --out ../.temp/pages-site
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { BASE, HOST } from './site-config.mjs'

export function parseArgs(argv) {
  const args = { dist: 'site', out: '../.temp/pages-site' }
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--dist') args.dist = argv[++i]
    else if (argv[i] === '--out') args.out = argv[++i]
    else throw new Error(`未知参数: ${argv[i]}`)
  }
  return args
}

const ROOT_INDEX = `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="0; url=./mcu/">
<link rel="canonical" href="${HOST}${BASE}">
<title>MCU 深入实战</title>
</head>
<body>
<p>站点入口已迁移至 <a href="./mcu/">${BASE}</a>。</p>
</body>
</html>
`

// 收集 html 中的本地资源引用并校验落位。
// 规则：站内绝对路径必须以 BASE 开头且文件存在于 staging/mcu/<rest>；
// 相对路径必须相对所在 html 存在。这两种之外的形态（http/data/#/mailto）不查。
export function checkAssetPlacement(mcuDir) {
  const problems = []
  let checked = 0
  const htmls = []
  const walk = (d) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const p = path.join(d, e.name)
      if (e.isDirectory()) walk(p)
      else if (e.name.endsWith('.html')) htmls.push(p)
    }
  }
  walk(mcuDir)
  const attr = /(?:src|href)="([^"]+)"/g
  for (const html of htmls) {
    const text = fs.readFileSync(html, 'utf8')
    const dir = path.dirname(html)
    for (const m of text.matchAll(attr)) {
      const url = m[1]
      if (/^(?:https?:|mailto:|data:|tel:)/.test(url) || url.startsWith('#')) continue
      checked += 1
      const [clean] = url.split(/[?#]/)
      if (url.startsWith('/')) {
        if (!clean.startsWith(BASE)) {
          problems.push(`${path.relative(mcuDir, html)}: 站内绝对路径 ${url} 不以 ${BASE} 开头——挂载后会指到 mcu/ 子树之外`)
          continue
        }
        // GitHub Pages 支持扩展名省略（/reference/faq → reference/faq.html），
        // 与 pages-check 的 cleanUrls 口径保持一致。
        const target = path.join(mcuDir, clean.slice(BASE.length))
        const hit = fs.existsSync(target) ||
          fs.existsSync(target + '.html') ||
          fs.existsSync(path.join(target, 'index.html'))
        if (!hit) problems.push(`${path.relative(mcuDir, html)}: ${url} 在 staging 中不存在（${clean.slice(BASE.length)}）`)
      } else {
        if (clean && !fs.existsSync(path.resolve(dir, clean))) {
          problems.push(`${path.relative(mcuDir, html)}: 相对引用 ${url} 不存在`)
        }
      }
    }
  }
  return { problems, checked, htmls: htmls.length }
}

export function assemble({ dist, out }) {
  const errors = []
  const distAbs = path.resolve(dist)
  const outAbs = path.resolve(out)
  const mcuDir = path.join(outAbs, 'mcu')
  const index = path.join(mcuDir, 'index.html')

  if (!fs.existsSync(distAbs)) {
    return { ok: false, errors: [`产物目录不存在: ${distAbs}`], out: outAbs }
  }
  fs.rmSync(outAbs, { recursive: true, force: true })
  fs.mkdirSync(outAbs, { recursive: true })
  fs.cpSync(distAbs, mcuDir, { recursive: true })

  // 失败模式 1：缺 MCU index。
  if (!fs.existsSync(index)) {
    errors.push(`staging 缺少 ${path.join('mcu', 'index.html')}——站点产物没有首页，禁止上传`)
  }

  // 根入口：脚本生成的重定向页是 staging 根的唯一 index。它若在复制前生成会被
  // 产物覆盖、复制后生成则天然防顶掉——这里显式再断言一次内容形态。
  const rootIndex = path.join(outAbs, 'index.html')
  fs.writeFileSync(rootIndex, ROOT_INDEX, 'utf8')
  const rootText = fs.readFileSync(rootIndex, 'utf8')
  if (!rootText.includes('url=./mcu/') || !rootText.includes(`${HOST}${BASE}`)) {
    errors.push('根入口重定向页内容异常（缺 ./mcu/ 跳转或 canonical）')
  }
  if (fs.existsSync(index) && fs.readFileSync(index, 'utf8') === rootText) {
    errors.push('根入口与站点首页内容相同——站点首页顶到了 staging 根，mcu/ 子树结构被破坏')
  }

  // 失败模式 3：资源必须在 mcu/ 下（base 前缀落位 + 无逃逸的站内绝对路径）。
  const placement = checkAssetPlacement(mcuDir)
  errors.push(...placement.problems)

  const fileCount = (() => {
    let n = 0
    const walk = (d) => {
      for (const e of fs.readdirSync(d, { withFileTypes: true })) {
        const p = path.join(d, e.name)
        if (e.isDirectory()) walk(p)
        else n += 1
      }
    }
    walk(mcuDir)
    return n
  })()

  return { ok: errors.length === 0, errors, out: outAbs, fileCount, ...placement }
}

const isMain = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
if (isMain) {
  const r = assemble(parseArgs(process.argv.slice(2)))
  if (r.ok) {
    console.log(`staging OK: ${r.fileCount} 文件, ${r.htmls} HTML, ${r.checked} 资源引用落位校验通过 → ${r.out}`)
  } else {
    for (const e of r.errors) console.error(`✖ ${e}`)
    console.error(`staging 组装失败（${r.errors.length} 个问题），禁止上传`)
    process.exit(1)
  }
}
