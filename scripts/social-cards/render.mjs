import fs from 'node:fs'
import path from 'node:path'
import { createHash } from 'node:crypto'
import { fileURLToPath, pathToFileURL } from 'node:url'
import { chromium } from 'playwright'

const here = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(here, '../..')
const output = path.join(root, 'video/assets/social-cards/book')
const scratch = path.join(root, '.temp/skill-closeout/cards')
const check = process.argv.includes('--check')
const cards = JSON.parse(fs.readFileSync(path.join(here, 'cards.json'), 'utf8'))
const sha = value => createHash('sha256').update(value).digest('hex')
const sourceHash = sha(['cards.json', 'cards.css', 'cover.html', 'render.mjs'].map(name => fs.readFileSync(path.join(here, name), 'utf8').replace(/\r\n/g, '\n')).join('\n'))
const html = `<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>书籍金句卡</title><link rel="stylesheet" href="${pathToFileURL(path.join(here, 'cards.css')).href}"></head><body>${cards.map(c => `<article class="poster" id="${c.id}" style="--title-size:${c.fontSize}px;--mark-width:${c.markWidth}px"><header><div class="kicker">${c.kicker}</div><div class="hr"></div></header><div class="content">${c.blocks.join('\n')}</div><footer class="foot">${c.footer}</footer></article>`).join('\n')}</body></html>`
fs.mkdirSync(scratch, { recursive: true })
fs.writeFileSync(path.join(scratch, 'preview.html'), html)
const browser = await chromium.launch({ headless: true })
const results = []
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, deviceScaleFactor: 2 })
  await page.goto(pathToFileURL(path.join(scratch, 'preview.html')).href)
  await page.evaluate(() => document.fonts.ready)
  for (const c of cards) {
    const poster = page.locator(`#${c.id}`)
    const measured = await poster.evaluate(el => {
      const box = node => { const r = node.getBoundingClientRect(); return { x: r.x, y: r.y, right: r.right, bottom: r.bottom, width: r.width, height: r.height } }
      const frame = box(el)
      const blocks = Array.from(el.querySelector('.content').children).map(box)
      const errors = []
      const footer = box(el.querySelector('.foot'))
      if (blocks.at(-1).bottom > footer.y - 24) errors.push('body touches footer')
      const gaps = blocks.slice(1).map((b, i) => b.y - blocks[i].bottom)
      if (gaps.some(g => g > 100 || g < 20)) errors.push(`content gaps: ${gaps}`)
      for (const node of el.querySelectorAll('.giant,.quote,.mark,.t,.d,.foot span')) {
        const r = box(node)
        if (r.x < frame.x + 55 || r.right > frame.right - 55 || r.bottom > frame.bottom - 40 || r.y < frame.y + 45) errors.push(`outside safe area: ${node.textContent}`)
        const range = document.createRange()
        range.selectNodeContents(node)
        for (const line of range.getClientRects()) {
          if (line.left < r.x - 1 || line.right > r.right + 1) errors.push(`text exceeds column: ${node.textContent}`)
        }
      }
      return { text: el.textContent.replace(/\s+/g, ' ').trim(), errors, gaps, bodyHeight: blocks.at(-1).bottom - blocks[0].y }
    })
    if (measured.text.replace(/\s/g, '') !== c.text.replace(/\s/g, '')) measured.errors.push('card text differs from intake baseline')
    // Existing cards use layout separators (B1: E · S · c · T); preserve the
    // card exactly while matching the chapter's E、S、c、T punctuation.
    const sentenceKey = s => s.replace(/[`*_\s、·，,：:；;（）()。]/g, '')
    const original = sentenceKey(fs.readFileSync(path.join(root, c.source), 'utf8'))
    // G1's original sentence contains a parenthetical after 三件套; its two
    // verbatim fragments must remain in source order. The card text stays exact.
    const fragments = c.id === 'card-g1-rcu' ? ['先电压三件套', '再 FMC 等待、后切钟'] : [c.giant]
    let cursor = 0
    for (const fragment of fragments) {
      const found = original.indexOf(sentenceKey(fragment), cursor)
      if (found < 0) measured.errors.push('main sentence absent from chapter')
      cursor = found + sentenceKey(fragment).length
    }
    if (measured.errors.length) throw new Error(`${c.id}: ${measured.errors.join('; ')}`)
    if (!check) await poster.screenshot({ path: path.join(scratch, `${c.id}.png`) })
    results.push({ id: c.id, source: c.source, gaps: measured.gaps, bodyHeight: measured.bodyHeight })
  }
  if (!check) {
    await page.goto(pathToFileURL(path.join(here, 'cover.html')).href)
    await page.evaluate(() => document.fonts.ready)
    await page.locator('#cover-c3-bili').screenshot({ path: path.join(scratch, 'cover-c3-bili.png') })
    fs.mkdirSync(output, { recursive: true })
    const files = [...cards.map(c => `${c.id}.png`), 'cover-c3-bili.png']
    const manifest = { sourceHash, cards: results, files: {} }
    for (const name of files) {
      fs.copyFileSync(path.join(scratch, name), path.join(output, name))
      manifest.files[name] = sha(fs.readFileSync(path.join(output, name)))
    }
    fs.writeFileSync(path.join(output, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n')
    fs.writeFileSync(path.join(output, 'index.html'), `<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>书籍金句卡 · 30 张</title><style>body{margin:0;padding:32px;font-family:"Microsoft YaHei",sans-serif;background:#f7f8fa;color:#16213a}h1{font-weight:400}main{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:24px}figure{margin:0}img{width:100%;height:auto}figcaption{padding:12px 0;font-size:14px}a{color:#3451b2}</style><header><h1>书籍金句卡</h1><p>29 张小红书 3:4 金句卡 · 1 张 B站 16:9 封面。主句保留章节原文。</p></header><main>${files.map((name, i) => `<figure><a href="${name}"><img src="${name}" alt="${i < cards.length ? cards[i].giant : '你的 volatile 白加了？'}" loading="lazy"></a><figcaption>${i < cards.length ? cards[i].source : 'B站推广封面'}</figcaption></figure>`).join('\n')}</main></html>`)
  }
  const manifest = JSON.parse(fs.readFileSync(path.join(output, 'manifest.json'), 'utf8'))
  if (manifest.sourceHash !== sourceHash) throw new Error('Sources changed; regenerate cards')
  const expectedNames = [...cards.map(c => `${c.id}.png`), 'cover-c3-bili.png'].sort()
  if (JSON.stringify(Object.keys(manifest.files).sort()) !== JSON.stringify(expectedNames)) throw new Error('Manifest must contain every card and the cover')
  for (const [name, expected] of Object.entries(manifest.files)) {
    const bytes = fs.readFileSync(path.join(output, name))
    if (sha(bytes) !== expected) throw new Error(`${name}: PNG hash differs`)
    if (name.startsWith('card-') && (bytes.readUInt32BE(16) !== 1500 || bytes.readUInt32BE(20) !== 2000)) throw new Error(`${name}: expected 1500×2000`)
    if (name.startsWith('cover-') && (bytes.readUInt32BE(16) !== 2560 || bytes.readUInt32BE(20) !== 1440)) throw new Error(`${name}: expected 2560×1440`)
  }
  console.log(`PASS: ${cards.length} cards, baseline text, chapter sentences, safe area, gaps and 30 PNG hashes`)
} finally {
  await browser.close()
}
