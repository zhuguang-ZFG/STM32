/**
 * 搜索可达性门：章节标题用站点自己的搜索应当能翻到它所在的那一页。
 *
 * 为什么这么判（而不是查索引的 term 表）：
 * 最初的写法是「标题的每个二元片段都必须是索引里的一个 term」，实测被否证——
 * 索引里确实缺 `位艺` 这类**跨词边界**的二元组（`移位艺术` → 有 `移位`/`艺术`，没有 `位艺`），
 * 但用构建产物真跑一次检索，「移位艺术」能正确翻到 `stm32/12-spi.html`。
 * 也就是说 term 表不是用户可见口径，真正的承诺是「正文里有的词，搜得到那一页」。
 * 这个门就按承诺判：拿 MiniSearch 载入产物索引，逐个标题真查一次，要求命中该标题所在的页面。
 *
 * 这样也守住了它本来的目的：一旦 config.mts 的
 * `themeConfig.search.options.miniSearch.options.tokenize` 被删回默认分词，
 * 索引与查询口径不一致，标题整句查不到任何页面 —— 门会红。
 *
 * 依赖：`minisearch` 必须与站点用的是同一个库（站点由 VitePress 间接安装），
 * 所以 package.json 里显式钉住同一大版本，避免门与站点跑在两套实现上。
 *
 * 用法：node scripts/search-check.mjs [--dist <dir>]（默认 docs/.vitepress/dist）
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'
import MiniSearch from 'minisearch'
import { loadSearchIndex } from './seo-check.mjs'
import { tokenizeForSearch } from './search-tokenize.mjs'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const DEFAULT_DIST = path.join(ROOT, 'docs', '.vitepress', 'dist')
const SKIP_DIRS = new Set(['.vitepress', 'node_modules', 'public'])

/** 递归收集 docs 里的 .md（跳过主题/配置/静态资产目录）。 */
function collectMarkdown(dir) {
  const out = []
  const walk = (d) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      if (e.isDirectory() && SKIP_DIRS.has(e.name)) continue
      const abs = path.join(d, e.name)
      if (e.isDirectory()) walk(abs)
      else if (e.name.endsWith('.md')) out.push(abs)
    }
  }
  walk(dir)
  return out.sort()
}

/**
 * 标题词面 → 渲染后纯文本口径。
 * 索引器拿到的是 markdown 渲染成 html 再 clearHtmlTags 之后的词面，
 * 这里在源码侧对齐同一口径，否则带行内标记的标题两边对不上。
 */
export function plainHeading(text) {
  return text
    .replace(/\s*\{#[^}\s]+\}\s*$/, '') // 自定义锚点 {#id} 只决定 id，不进正文
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1') // 链接只留文字
    .replace(/[`*~]/g, '') // 反引号/加粗/删除线标记渲染后消失
    .replace(/<[^>]*>/g, '') // 与索引器的 clearHtmlTags 同口径
    .trim()
}

/**
 * 产物里属于「这一页」的 URL 形态（不含 fragment；检索结果 id 形如 `/mcu/stm32/12-spi.html#段`）。
 *
 * 必须**全等**比较而不是前缀：目录页 `/mcu/build/` 当前缀会把
 * `/mcu/build/00-toolchain.html#…` 也算成"翻到了导览页"——那是这一门最容易出的伪绿，
 * 2147 全绿不能建立在这上面。
 */
export function pageHrefPaths(docsRel, base = '/mcu/') {
  const noExt = docsRel.replace(/\.md$/, '')
  if (noExt === 'index') return [base, `${base}index.html`]
  if (noExt.endsWith('/index')) {
    const dir = `${base}${noExt.slice(0, -'index'.length)}`
    return [dir, `${dir}index.html`]
  }
  return [`${base}${noExt}.html`]
}

/** 结果 id → 页面路径（去掉 fragment 与 query）。 */
function idPath(id) {
  return String(id).split('#')[0].split('?')[0]
}

/**
 * 采集必中条目：页面 H1 + H2/H3 标题（去代码块、去行内标记）。
 * 与建索引口径一致地跳过三类标题：无 H1 的页面（首页/404 这类 layout:home）、
 * 整棵子树无正文的小节，以及 frontmatter 声明 `search: false` 的页面（VitePress 不索引它们）。
 *
 * 页面标题采**正文的 H1 行**，不采 frontmatter title：两者经常不是一个词
 * （`docs/stm32/index.md` 是 `title: S 篇导览`、H1 是「STM32F407 寄存器主线…」），
 * 而索引拿到的是渲染后的正文——按 frontmatter 采必误报（实测 1 例：
 * 搜「S 篇导览」123 条命中里没有这一页，因为它压根不在索引里）。
 * @returns {{ term: string, page: string }[]} page 为 docs 相对 posix 路径
 */
export function harvestEntries(docsDir) {
  const entries = new Map()
  const add = (term, page) => {
    if (term && !entries.has(`${page}\u0000${term}`)) entries.set(`${page}\u0000${term}`, { term, page })
  }

  for (const file of collectMarkdown(docsDir)) {
    const page = path.relative(docsDir, file).replace(/\\/g, '/')
    const lines = fs.readFileSync(file, 'utf8').split(/\r?\n/)

    let bodyStart = 0
    if (lines[0] === '---') {
      const end = lines.indexOf('---', 1)
      if (end > 0) {
        const front = lines.slice(1, end)
        // 页面被排除出搜索时，标题查不到是正常的，不是缺陷
        if (front.some((l) => /^search:\s*false\s*$/.test(l))) continue
        bodyStart = end + 1
      }
    }

    // 去代码块：围栏里的「标题」是示例文本，不是章节结构
    const body = []
    let inCode = false
    for (const line of lines.slice(bodyStart)) {
      if (/^\s*```/.test(line)) {
        inCode = !inCode
        continue
      }
      if (!inCode) body.push(line)
    }

    // 页面标题 = 正文第一条 H1（渲染后它才是被索引的那个 title 字段）
    const h1 = body.find((l) => /^#\s+\S/.test(l))
    if (h1) add(plainHeading(h1.replace(/^#\s+/, '')), page)

    for (let i = 0; i < body.length; i++) {
      const h = /^(#{2,3})\s+(.+?)\s*$/.exec(body[i])
      if (!h) continue
      const level = h[1].length
      // 索引器跳过「空小节」（标题到下个标题之间没有任何文字），
      // 但子小节的标题链里仍会带上父标题——所以只有「整棵子树都没文字」的标题
      // 才真的不在索引里，与建索引口径保持一致。
      let hasText = false
      for (let j = i + 1; j < body.length && !hasText; j++) {
        const sub = /^(#{1,6})\s/.exec(body[j])
        if (sub && sub[1].length <= level) break
        const text = body[j]
          .replace(/<[^>]*>/g, '')
          .replace(/!\[[^\]]*\]\([^)]*\)/g, '')
          .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
        if (/[\p{L}\p{N}]/u.test(text)) hasText = true
      }
      const term = plainHeading(h[2])
      if (hasText && term) add(term, page)
    }
  }
  return [...entries.values()]
}

/** 用站点同一套 tokenizer 载入产物索引 —— 与 VPLocalSearchBox 的反序列化口径一致。 */
export function loadSearchable(indexJson) {
  return MiniSearch.loadJSON(JSON.stringify(indexJson), {
    fields: ['title', 'titles', 'text'],
    storeFields: ['title', 'titles'],
    tokenize: tokenizeForSearch,
  })
}

/**
 * 对账：每个标题真查一次，要求结果里出现该标题所在页面（页面路径**全等**比较）。
 *
 * 刻意**不截断**结果，也不改 MiniSearch 的默认检索参数：
 *   · 这一门判的是可达性——"正文里有的标题，搜得到那一页"，排序质量不是它管的事；
 *   · 实测证据：给结果设前 20 条截断后，715/2147 判红全部来自「小节结构」「实物实验」
 *     这类通用标题（目标页排在第 20 名之外），那是噪声而不是缺陷；
 *   · MiniSearch 的 SearchOptions 里也**没有 limit**，传了不生效——要截断只能自己 slice，
 *     所以这个决定必须写在这里，而不是靠一个不存在的参数默认值。
 * @returns {{ missing: {term: string, page: string, hits: number}[], checked: number }}
 */
export function checkSearchHits(indexJson, entries, { base = '/mcu/' } = {}) {
  const ms = loadSearchable(indexJson)
  const missing = []
  for (const { term, page } of entries) {
    const paths = pageHrefPaths(page, base)
    const hits = ms.search(term)
    if (!hits.some((h) => paths.includes(idPath(h.id)))) {
      missing.push({ term, page, hits: hits.length })
    }
  }
  return { missing, checked: entries.length }
}

const isMain =
  process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href

if (isMain) {
  const at = process.argv.indexOf('--dist')
  const dist = at >= 0 && process.argv[at + 1] ? path.resolve(process.argv[at + 1]) : DEFAULT_DIST

  const index = loadSearchIndex(dist)
  if (!index) {
    console.error(`✗ 产物里找不到本地搜索索引 chunk（${dist}）—— 请先运行 npm run docs:build`)
    process.exit(1)
  }
  if (!Array.isArray(index.index)) {
    console.error('✗ 搜索索引结构异常：没有 index term 表')
    process.exit(1)
  }

  const entries = harvestEntries(path.join(ROOT, 'docs'))
  const { missing, checked } = checkSearchHits(index, entries)

  if (missing.length) {
    console.error(`✗ ${missing.length}/${checked} 个标题在自己的页面里搜不到：`)
    for (const m of missing.slice(0, 20)) {
      console.error(`  - 「${m.term}」（${m.page}）检索返回 ${m.hits} 条，其中没有这一页`)
    }
    if (missing.length > 20) console.error(`  …还有 ${missing.length - 20} 个`)
    console.error(
      '  排查：config.mts 的 themeConfig.search.options.miniSearch.options.tokenize 是否被改回默认分词' +
        '（索引与查询口径不一致时，整句标题会一条都搜不到）',
    )
    process.exit(1)
  }
  console.log(`✓ ${checked} 个章节/小节标题都能被站内搜索翻到自己那一页（${index.index.length} 个 term）`)
}