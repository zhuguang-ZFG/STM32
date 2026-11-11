// 读创作中心「编辑框」现状：GET x/vupre/web/archive/view。这是编辑接口 videos[].filename 与各开关现值的唯一事实源。
// 存 .temp/bili-<bvid>-editbox.json；只打印键名与标量，不打印正文大段、不打印凭证。
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
const ck = JSON.parse(readFileSync(['C:/Users/zhugu/tools/biliup-rs/biliupR-v0.2.4-x86_64-windows/cookies.json','C:/Users/zhugu/tools/biliup-rs/cookies.json'].find((p) => existsSync(p)), 'utf8')).cookie_info.cookies
const jar = ck.map((c) => `${c.name}=${c.value}`).join('; ')
const csrf = ck.find((c) => c.name === 'bili_jct').value
const bvid = process.argv[2] || 'BV14gpq66Eri'
const r = await fetch(`https://member.bilibili.com/x/vupre/web/archive/view?bvid=${bvid}&share_rec=jump_from_del&csrf=${csrf}`, {
  headers: { cookie: jar, 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36', referer: 'https://member.bilibili.com/platform/' } })
const t = await r.text()
if (/SESSDATA|bili_jct|access_token|refresh_token/.test(t)) { console.log('‼️ 响应含疑似凭证字段，整段丢弃'); process.exit(1) }
const j = JSON.parse(t)
console.log(`http=${r.status} code=${j.code} ${j.message}`)
if (j.code !== 0) process.exit(1)
writeFileSync(`.temp/bili-${bvid}-editbox.json`, JSON.stringify(j.data, null, 1))
const d = j.data
console.log('顶层：', Object.keys(d).join(' '))
console.log('archive：', Object.keys(d.archive || {}).join(' '))
;(d.arcs || []).forEach((a, i) => console.log(`arcs[${i}]：`, Object.keys(a).join(' '), '｜pages', (a.pages || []).length))
;(d.pages || []).forEach((p, i) => console.log(`pages[${i}] 键：`, Object.keys(p).join(' ')))
for (const k of ['no_disturbance', 'act_reserve_create', 'act_reserve_binded', 'in_season', 'has_appeal', 'can_edit_delay', 'add_season', 'up_mn_auto_reply', 'is_hey', 'is_cheating', 'is_opus']) if (k in d) console.log(`  ${k} =`, JSON.stringify(d[k]))
const a = d.archive || {}
for (const k of Object.keys(a)) {
  const v = a[k]
  if (v === null || typeof v === 'object') { console.log(`  archive.${k}: ${Array.isArray(v) ? `数组${v.length}` : v === null ? 'null' : '{' + Object.keys(v).slice(0, 8).join(',') + '}'}`); continue }
  console.log(`  archive.${k} =`, JSON.stringify(String(v).slice(0, 70)))
}
const pg = (d.pages || [])[0] || {}
console.log('pages[0]：', JSON.stringify(Object.fromEntries(Object.entries(pg).map(([k, v]) => [k, typeof v === 'string' && v.length > 40 ? `<${v.length}字>` : v]))).slice(0, 600))
console.log('tags：', (d.tags || []).map((x) => x.tag_name ?? x).join(','))
