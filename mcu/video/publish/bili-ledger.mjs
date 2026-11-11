// 汇总：series.json 的 16 集 × 我们账上已投稿的记录，一次看清谁在线上、谁还缺。
// BV 号只认 .temp/bili-web-run/published.jsonl（publish 步拿到 code=0 才落的那条账），
// 不拿日志里的字符串当数——日志里出现过 BV 字样不代表投稿成功。
import { readFileSync, existsSync } from 'node:fs'

const s = JSON.parse(readFileSync('video/series.json', 'utf8'))
const lines = readFileSync('.temp/bili-web-run/published.jsonl', 'utf8').trim().split('\n')
const byEp = {}
for (const l of lines) {
  const r = JSON.parse(l)
  if (r.bvid) byEp[r.ep] = { ...byEp[r.ep], bvid: r.bvid, at: r.at }
}
console.log(`published.jsonl ${lines.length} 行，其中带 BV 号 ${Object.keys(byEp).length} 集\n`)
const done = [], missing = [], noMaster = []
for (const e of s.episodes) {
  const r = byEp[e.id]
  // 没有 bilibili.mp4 的集（c3b 只有抖音版）不该混进"还缺"里——那会让人以为还有稿要投。
  if (!existsSync(`video/out/${e.id}/bilibili.mp4`)) { noMaster.push(`${String(e.no).padStart(2)} ${e.id}`); continue }
  if (r) done.push(`${String(e.no).padStart(2)} ${e.id.padEnd(16)} ${r.bvid}  ${r.at.slice(11, 16)}`)
  else missing.push(`${String(e.no).padStart(2)} ${e.id}`)
}
for (const d of done.sort()) console.log('  ✅ ' + d)
console.log(`\n横版 master ${done.length + missing.length} 条，账上有 BV ${done.length} 条，还缺 ${missing.length} 条`)
console.log(`账上没有 BV 号的：${missing.length ? '\n  ⚠ ' + missing.join('\n  ⚠ ') : '（无）'}`)
if (noMaster.length) console.log(`没有 B站横版 master、本就不该有 BV 的：${noMaster.join(', ')}`)
const extra = Object.keys(byEp).filter((k) => !s.episodes.some((e) => e.id === k))
if (extra.length) console.log(`series.json 里没有但账上有：${extra.join(', ')}`)
