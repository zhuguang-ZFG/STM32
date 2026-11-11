import fs from 'node:fs'
import path from 'node:path'

const dir = 'docs/public/anim'
const files = fs.readdirSync(dir).filter((f) => f.endsWith('.svg'))
const apply = process.argv.includes('--write')

function heading(s) {
  const t = [...s.matchAll(/<text\b([^>]*)>([^<]*)<\/text>/g)]
  const h = t.find((m) => /font-size="1[678]"/.test(m[1]) && m[2].trim())
  const sub = t.find(
    (m) => /font-size="1[123]"/.test(m[1]) && m[2].trim().length > 20 && m[2] !== h?.[2],
  )
  return { h: h && h[2].trim(), sub: sub && sub[2].trim() }
}

for (const f of files) {
  const p = path.join(dir, f)
  let s = fs.readFileSync(p, 'utf8')
  const before = s

  // SVG 文本里的 markdown 星号会被原样画出来
  s = s.replace(/\*\*([^<>*]{1,20})\*\*/g, '$1')

  if (!s.includes('<title>')) {
    const { h, sub } = heading(s)
    if (!h) {
      console.log(`跳过 ${f}：找不到标题行`)
      continue
    }
    const desc = sub ? `${h}。${sub}` : h
    const m = s.match(/<svg\b[^>]*>/)
    s = s.slice(0, m.index + m[0].length) + `\n  <title>${h}</title>\n  <desc>${desc}</desc>` + s.slice(m.index + m[0].length)
    console.log(`补元数据 ${f}：${h}`)
  }

  if (s !== before) {
    if (apply) fs.writeFileSync(p, s)
    else console.log(`  （未写入，加 --write 生效）${f}`)
  }
}
console.log(apply ? '已写入' : '试运行：未改动文件')
