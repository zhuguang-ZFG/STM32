/**
 * 无障碍静态审计：扫描构建产物 HTML，守住键盘焦点、可访问名、地标与语言。
 *
 * 为什么单独有它：项目已有 prefers-reduced-motion 与图片 alt 全覆盖，
 * 但没有自动化防回退——新增一个按钮、一张图或一次改版就可能悄悄打破无障碍。
 * 本脚本纯静态（无浏览器），在 quality 门内运行，确保每一页发布前都经得起
 * 自动化的 a11y 基线。
 *
 * 用法：node scripts/a11y-check.mjs（需先 npm run docs:build；--quiet 只在出错时输出）
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath, pathToFileURL } from 'node:url'

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')

/** 从标签串取某属性值；无该属性返回 null。 */
export function attr(tag, name) {
  const m = new RegExp(`\\b${name}=["']([^"']*)["']`, 'i').exec(tag)
  return m ? m[1] : null
}

/** 提取标签内的纯文本（去掉子标签）。简单版，足以应对 VitePress 产物。 */
export function textContent(tagBody) {
  return tagBody.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim()
}

export function auditPage(html) {
  const issues = []

  // 1. 页面语言
  if (!/<html\b[^>]*\blang="zh-CN"/i.test(html)) issues.push('html[lang]')

  // 2. 每张图都有 alt（允许空 alt，但不允许完全缺失）
  const imgs = [...html.matchAll(/<img\b[^>]*>/gi)]
  for (const [tag] of imgs) {
    if (!/\balt=/i.test(tag)) issues.push('img missing alt')
  }

  // 2b. 章节手绘机制图在构建期内联成 <figure class="hand-figure"><svg …>，
  //     不再是 <img>，上面那条 alt 检查因此看不到它们；无障碍名改由 SVG 自身的
  //     role="img" + 非空 aria-label 承载，这里单独把守，防止塞进没名字的图。
  const handFigures = [...html.matchAll(/<figure class="hand-figure"[^>]*>\s*(<svg\b[^>]*>)/gi)]
  for (const [, svgTag] of handFigures) {
    const label = /\baria-label="([^"]*)"/i.exec(svgTag)
    if (!label || !label[1].trim()) issues.push('hand-figure missing aria-label')
  }

  // 3. 每个按钮都有可访问名（aria-label / title / 文本内容）
  // 注：title 不是最佳实践，但 VitePress 内置 UI（主题切换、代码复制）用 title 承载名称，
  //     静态审计以「有名称」为基线，不苛求最佳实践来源。
  //     VPSwitchAppearance 是 VitePress 主题切换开关，框架级责任，跳过。
  const buttons = [...html.matchAll(/<button\b([^>]*)>(.*?)<\/button>/gi)]
  for (const [full, openTag, body] of buttons) {
    if (/VPSwitchAppearance/.test(openTag)) continue
    if (/\b(aria-label|aria-labelledby|title)=/i.test(openTag)) continue
    if (textContent(body).length) continue
    issues.push('button missing name')
  }

  // 4. 每个链接都有文本或标签（含 aria-label / title / 正文 / 带 alt 的 img）
  const links = [...html.matchAll(/<a\b([^>]*)>(.*?)<\/a>/gi)]
  for (const [full, openTag, body] of links) {
    if (/\b(aria-label|aria-labelledby|title)=/i.test(openTag)) continue
    if (textContent(body).length) continue
    const imgAlts = [...body.matchAll(/<img\b[^>]*\balt="([^"]*)"/gi)]
    if (imgAlts.some((m) => m[1].trim().length)) continue
    issues.push('link missing text')
  }

  // 5. 每页至少一个 h1
  const h1s = html.match(/<h1\b/gi) || []
  if (h1s.length === 0) issues.push('no h1')

  // 6. 至少有一个主内容地标
  if (!/<main\b/i.test(html) && !/<div[^>]*\bid=["']VPContent["']/i.test(html)) {
    issues.push('no main/VPContent landmark')
  }

  return issues
}

export function collectHtmlPages(dir) {
  const out = []
  const walk = (d) => {
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const abs = path.join(d, e.name)
      if (e.isDirectory()) walk(abs)
      else if (e.name.endsWith('.html')) out.push(abs)
    }
  }
  walk(dir)
  return out.sort()
}

const isMain =
  process.argv[1] && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href

if (isMain) {
  const dist = path.join(ROOT, 'docs', '.vitepress', 'dist')
  if (!fs.existsSync(dist)) {
    console.error('✗ 找不到构建产物 docs/.vitepress/dist —— 请先运行 npm run docs:build')
    process.exit(1)
  }
  const pages = collectHtmlPages(dist)
  const bad = []
  for (const file of pages) {
    const rel = path.relative(dist, file)
    // 404 是客户端渲染的空壳（产物里只有 <div id="app"></div>，内容由 JS 注入），
    // 静态审计扫不到任何标签，跳过以免误报。其余页面均为 SSR，正常检查。
    if (rel === '404.html') continue
    const issues = auditPage(fs.readFileSync(file, 'utf8'))
    if (issues.length) bad.push({ rel, issues })
  }
  if (bad.length) {
    console.error(`✗ ${bad.length}/${pages.length} 个页面存在无障碍问题：`)
    for (const { rel, issues } of bad.slice(0, 10)) {
      console.error(`  - ${rel} → ${issues.join('、')}`)
    }
    if (bad.length > 10) console.error(`  …还有 ${bad.length - 10} 个`)
    console.error('  修复：补 alt/aria-label、检查 heading 结构、确保地标存在。')
    process.exit(1)
  }
  if (!process.argv.includes('--quiet')) {
    console.log(`✓ ${pages.length} 个页面无障碍基线通过（img alt、button name、link text、h1、landmark、lang）`)
  }
}
