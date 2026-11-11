import fs from 'node:fs'
import path from 'node:path'
import os from 'node:os'
import { execFileSync } from 'node:child_process'
import { fileURLToPath } from 'node:url'
import { HOST, BASE } from '../site-config.mjs'
import { sha, checkGuide } from './contract.mjs'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, '../..')
const sourcePath = path.join(root, 'docs/reference/book.md')
const output = path.join(root, 'docs/public/book-guide')
const raw = fs.readFileSync(sourcePath, 'utf8').replace(/\r\n/g, '\n')
const sourceHash = sha(raw)
const generatorHash = sha(['generate.mjs', 'contract.mjs', 'site.css'].map(name => fs.readFileSync(path.join(here, name), 'utf8').replace(/\r\n/g, '\n')).join('\n'))
const manifestPath = path.join(output, 'manifest.json')
const htmlPath = path.join(output, 'index.html')

function verify() {
  const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'))
  const html = fs.readFileSync(htmlPath, 'utf8')
  const errors = checkGuide({ sourceHash, generatorHash, manifest, html })
  if (errors.length) throw new Error(errors.join('; '))
  console.log('PASS: book guide source/generator/output hashes, SEO, a11y and local assets')
}

if (process.argv.includes('--check')) {
  verify()
} else {
  // Rendering uses the installed skill; checking the committed HTML needs only Node.
  const candidates = [process.env.GUIZANG_PAGE_SKILL, path.join(os.homedir(), '.agents/skills/guizang-page-skill'), path.join(os.homedir(), '.codex/skills/guizang-page-skill')].filter(Boolean)
  const skill = candidates.find(p => fs.existsSync(path.join(p, 'scripts/render.mjs')))
  if (!skill) throw new Error('Install guizang-page-skill or set GUIZANG_PAGE_SKILL to its directory')
  const scratch = path.join(root, '.temp/skill-closeout/guide')
  fs.mkdirSync(scratch, { recursive: true })
  // The alternate guide links back to its canonical source, avoiding a self-link.
  const input = raw.replace(/^<a href="\.\.\/book-guide\/index\.html".*$/m, `[返回站点书籍入口](${BASE}reference/book.html)`)
  const lines = input.split('\n')
  const start = lines.findIndex(line => line === '## 参与校对与贡献')
  const checklist = []
  for (let i = start + 1; i < lines.length && !lines[i].startsWith('## '); i++) {
    if (lines[i].startsWith('- ')) checklist.push(i + 1)
  }
  const title = lines.find(line => line.startsWith('# ')).slice(2)
  const anno = {
    meta: { title, author: '御舆 MCU 书', date: '2026.11.05', reading_time: '约 3 分钟', tags: ['离线书', 'PDF', '自出版'], subtitle: '网页适合跳读，书适合通读。', hero_image: `${BASE}images/boards/stm32f407-board.jpg`, lang: null, autospace: false },
    upgrades: [{ type: 'checklist', lines: checklist }],
  }
  fs.writeFileSync(path.join(scratch, 'book.md'), input)
  fs.writeFileSync(path.join(scratch, 'annotations.json'), JSON.stringify(anno, null, 2))
  const result = execFileSync(process.execPath, [path.join(skill, 'scripts/render.mjs'), path.join(scratch, 'book.md'), path.join(scratch, 'annotations.json'), path.join(scratch, 'index.html'), '--style', 'swiss', '--brand', '#3451b2'], { encoding: 'utf8' })
  if (/⚠|warning|警告/i.test(result)) throw new Error(result)
  console.log(result.trim())
  let html = fs.readFileSync(path.join(scratch, 'index.html'), 'utf8').replace(/\r\n/g, '\n')
  const canonical = `${HOST}${BASE}reference/book.html`
  const description = '整书离线版精排导读：与站点同源的 HTML、16 开印前 PDF、构建与校对入口。'
  const siteCss = fs.readFileSync(path.join(here, 'site.css'), 'utf8')
  const head = `<meta name="description" content="${description}"><link rel="canonical" href="${canonical}"><meta property="og:title" content="${title}"><meta property="og:description" content="${description}"><meta property="og:url" content="${canonical}"><meta property="og:image" content="${HOST}${BASE}og-cover.png"><meta name="twitter:card" content="summary_large_image"><style>${siteCss}</style>`
  html = html.replace('</head>', `${head}</head>`)
    .replace(/<link\b[^>]*(?:fonts\.googleapis\.com|fonts\.gstatic\.com)[^>]*>/g, '')
    .replace('<div class="container">', '<main class="container">')
    .replace(/<\/div>(\s*<script>)/, '</main>$1')
    .replace("el.setAttribute('contenteditable', 'true');", "// Published guide is read-only; edit docs/reference/book.md.")
    .replace('<span>归藏 Page</span>', '<span>通往单片机之路</span>')
  fs.mkdirSync(output, { recursive: true })
  fs.writeFileSync(htmlPath, html)
  fs.writeFileSync(manifestPath, JSON.stringify({ source: 'docs/reference/book.md', sourceHash, generatorHash, htmlHash: sha(html), renderer: 'guizang-page-skill/scripts/render.mjs', rendererHash: sha(fs.readFileSync(path.join(skill, 'scripts/render.mjs'))), canonical, base: BASE }, null, 2) + '\n')
  verify()
}
