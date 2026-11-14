// B5 站点组装：合并书构建产物（根）+ 旧 /mcu/** 跳转存根 → Pages staging。
//
// 与 mcu 时代的 assemble-pages 区别：合并书本身就是站点根，不再组装 mcu/
// 子树真实内容——mcu/ 下只有跳转存根（meta-refresh + canonical）。
// 用法（cwd=仓库根）：node scripts/site-assemble.mjs --dist book/dist/site --stubs <stubs-root> --out .temp/pages-site
//
// 断言（任一失败即非 0 退出）：
// 1. 根 index.html 存在（合并书首页直接当站点入口，不再重定向到 ./mcu/）；
// 2. mcu/ 目录下只有 .html 存根（不含真实正文，即旧站点内容已清场）；
// 3. 存根数 ≥131（94 个 mapping 章节 + 37 个非章节旧页）。
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

export function parseArgs(argv) {
  const args = { dist: 'book/dist/site', stubs: '', out: '.temp/pages-site' }
  for (let i = 0; i < argv.length; i += 1) {
    if (argv[i] === '--dist') args.dist = argv[++i]
    else if (argv[i] === '--stubs') args.stubs = argv[++i]
    else if (argv[i] === '--out') args.out = argv[++i]
    else throw new Error(`未知参数: ${argv[i]}`)
  }
  return args
}

function copyTree(src, dest) {
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const s = path.join(src, entry.name)
    const d = path.join(dest, entry.name)
    if (entry.isDirectory()) {
      fs.mkdirSync(d, { recursive: true })
      copyTree(s, d)
    } else {
      fs.copyFileSync(s, d)
    }
  }
}

export function assemble({ dist, stubs, out }) {
  const errors = []
  const distRoot = path.resolve(dist)
  if (!fs.existsSync(path.join(distRoot, 'index.html'))) {
    errors.push('根 index.html 不存在：合并书首页必须直接当站点入口')
  }
  let stubCount = 0
  const stubsRoot = stubs ? path.resolve(stubs) : null
  if (stubsRoot && fs.existsSync(stubsRoot)) {
    function countStubs(dir) {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        if (entry.isDirectory()) countStubs(path.join(dir, entry.name))
        else if (entry.name.endsWith('.html')) stubCount += 1
      }
    }
    countStubs(stubsRoot)
  }
  if (stubCount < 131) {
    errors.push(`旧链存根数 ${stubCount} < 131：覆盖率不足 100%`)
  }
  if (errors.length > 0) {
    throw new Error(errors.join('; '))
  }

  fs.rmSync(out, { recursive: true, force: true })
  fs.mkdirSync(out, { recursive: true })
  copyTree(distRoot, out)
  if (stubsRoot) copyTree(stubsRoot, out)

  // 组装后再验一次 mcu/ 下没有真实正文：所有 .html 都是存根（含 meta-refresh）。
  const mcuDir = path.join(out, 'mcu')
  let nonStub = 0
  if (fs.existsSync(mcuDir)) {
    function scanNonStub(dir) {
      for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
        const full = path.join(dir, entry.name)
        if (entry.isDirectory()) scanNonStub(full)
        else if (entry.name.endsWith('.html')) {
          const head = fs.readFileSync(full, 'utf8').slice(0, 400)
          if (!head.includes('http-equiv="refresh"')) nonStub += 1
        }
      }
    }
    scanNonStub(mcuDir)
  }
  if (nonStub > 0) {
    throw new Error(`mcu/ 下发现 ${nonStub} 个非存根页面：旧站点内容未清场`)
  }
  return { stubCount }
}

export function main(argv) {
  const args = parseArgs(argv)
  const { stubCount } = assemble(args)
  console.log(`assembled pages site: root=${path.resolve(args.out)} stubs=${stubCount}`)
}

const isMain = process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1]
if (isMain) {
  main(process.argv.slice(2))
}
