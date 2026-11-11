// B站 17 条公开数据体检：播放/互动、合集归属、分区、标题/简介长度、标签数
import { execSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
const UA = 'Mozilla/5.0'
const get = (u) => {
  try { return JSON.parse(execSync(`curl -s -m 15 -A "${UA}" "${u}"`, { encoding: 'utf8', maxBuffer: 9e7 })) } catch { return null }
}
const s = JSON.parse(readFileSync('video/series.json', 'utf8'))
const rows = []
for (const e of s.episodes) {
  let bv = null
  try { bv = readFileSync(`.temp/bili-web-run/${e.id}.bvid`, 'utf8').trim() } catch { continue }
  if (!/^BV[0-9A-Za-z]{10}$/.test(bv)) { rows.push({ e, bv: String(bv).slice(0, 16), err: 'bvid 格式不对' }); continue }
  const j = get(`https://api.bilibili.com/x/web-interface/view?bvid=${bv}`)
  const d = j?.data
  if (!d) { rows.push({ e, bv, err: `view code=${j?.code}` }); continue }
  const tg = get(`https://api.bilibili.com/x/tag/archive/tags?bvid=${bv}`)
  const tags = (tg?.data || []).map((t) => t.tag_name)
  const season = d.ugc_season ? `${d.ugc_season.title}` : '⚠️ 不在任何合集'
  let seasonEp = ''
  if (d.ugc_season) {
    for (const sec of d.ugc_season.sections || []) {
      const i = (sec.episodes || []).findIndex((x) => x.bvid === bv)
      if (i >= 0) { seasonEp = `第${i + 1}/${sec.episodes.length}条`; break }
    }
  }
  rows.push({
    e, bv, title: d.title, tl: d.title.length, desc: (d.desc || '').length,
    view: d.stat.view, dm: d.stat.danmaku, reply: d.stat.reply, coin: d.stat.coin,
    fav: d.stat.favorite, share: d.stat.share, like: d.stat.like,
    tname: `${d.tname_v2 || d.tname}`, dur: Math.round(d.duration), p: d.pages?.length || 1,
    season, seasonEp, tags: tags.length, tagList: tags.join(','),
    pub: new Date(d.pubdate * 1000).toISOString().slice(0, 10)
  })
}
for (const r of rows) {
  if (r.err) { console.log(`${String(r.e.no).padStart(2)} ${r.e.id.padEnd(17)} ${r.bv}  ${r.err}`); continue }
  console.log(`${String(r.e.no).padStart(2)} ${r.e.id.padEnd(17)} ${r.bv} 播放${String(r.view).padStart(5)} 赞${String(r.like).padStart(4)} 藏${String(r.fav).padStart(4)} 币${String(r.coin).padStart(3)} 评${String(r.reply).padStart(3)} 弹${String(r.dm).padStart(3)} 享${r.share} | ${r.dur}s ${r.p}P | 标${r.tl}字 简${r.desc}字 | ${r.tags}标签 | ${r.tname} | ${r.season}${r.seasonEp ? ' ' + r.seasonEp : ''} | ${r.pub}`)
}
console.log('\n=== 标签样例（F5 与最早一条）===')
for (const r of rows.filter((x) => x.tagList).slice(-1).concat(rows.filter((x) => x.tagList).slice(0, 1))) console.log(r.e.id, '→', r.tagList)
