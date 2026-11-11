import { fileURLToPath } from 'node:url'
const MCU_ROOT = fileURLToPath(new URL('../../', import.meta.url)).replace(/[\\/]$/, '')
// B站创作中心「合集」客户端。接口取自 bilibili-API-collect/docs/creativecenter/season.md：
//   列表 GET  member.bilibili.com/x2/creative/web/seasons
//   封面 POST member.bilibili.com/x/vu/web/cover/up        （base64，返回 biliimg URL）
//   新建 POST member.bilibili.com/x2/creative/web/season/add（title/desc/cover/season_price/csrf）
//   加集 POST member.bilibili.com/x2/creative/web/season/section/episodes/add?csrf=（JSON: episode/section_id）
// 凭证只进请求头与表单体，任何子命令都不打印 cookie 值；响应里若混进凭证字段整段丢弃。
// 用法：node video/publish/bili-collection.mjs <seasons|cover|create|join|resolve> [参数…]
import { readFileSync, existsSync, writeFileSync } from 'node:fs'

const CAND = [
  'C:/Users/zhugu/tools/biliup-rs/biliupR-v0.2.4-x86_64-windows/cookies.json',
  'C:/Users/zhugu/tools/biliup-rs/cookies.json',
  `${MCU_ROOT}/cookies.json`,
]
const file = CAND.find((p) => existsSync(p))
if (!file) { console.log('‼️ 找不到 cookies.json'); process.exit(1) }
const j = JSON.parse(readFileSync(file, 'utf8'))
const pick = (o) => (Array.isArray(o) ? o : Array.isArray(o?.cookies) ? o.cookies : [])
const cookies = pick(j.cookie_info)
if (!cookies.length) { console.log('‼️ cookie_info 解析不出 cookies 数组'); process.exit(1) }
const jar = cookies.map((c) => `${c.name}=${c.value}`).join('; ')
const csrf = cookies.find((c) => c.name === 'bili_jct')?.value || ''
console.log(`   凭证：${cookies.length} 项，csrf=${csrf ? '有' : '无'}`)

const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
const M = 'https://member.bilibili.com/x2/creative/web'
async function call(url, { method = 'GET', form, json, qs } = {}) {
  const headers = { 'user-agent': UA, referer: 'https://member.bilibili.com/platform/', cookie: jar }
  let body
  if (form) { headers['content-type'] = 'application/x-www-form-urlencoded'; body = new URLSearchParams({ ...form, csrf }).toString() }
  else if (json) { headers['content-type'] = 'application/json'; body = JSON.stringify(json) }
  const u = qs ? `${url}?${new URLSearchParams(qs)}` : url
  const r = await fetch(u, { method, headers, body })
  const t = await r.text()
  if (/SESSDATA|bili_jct|access_token|refresh_token/.test(t)) return { http: r.status, code: null, msg: '‼️ 响应含疑似凭证字段，整段丢弃' }
  try { const v = JSON.parse(t); return { http: r.status, code: v.code, msg: v.message ?? v.msg, data: v.data } }
  catch { return { http: r.status, code: null, msg: t.slice(0, 160) } }
}
const ST = { 0: '正常', '-6': '审核中' }
const [cmd, ...A] = process.argv.slice(2)
const out = { printed: false }
const show = (tag, r) => {
  console.log(`${tag}: http=${r.http} code=${r.code} message=${r.msg}`)
  if (r.code !== 0 && r.data !== undefined) console.log('   data:', JSON.stringify(r.data).slice(0, 400))
  return r
}

if (cmd === 'seasons') {
  const r = show('seasons', await call(`${M}/seasons`, { qs: { pn: 1, ps: 30 } }))
  for (const s of r.data?.seasons || []) {
    const se = s.season || {}
    // 2026-10-28 实测 sections 有两态：裸数组或 { sections: […] } 包裹——两种都认。
    const secs = Array.isArray(s.sections) ? s.sections : (s.sections?.sections || [])
    console.log(`   合集 ${se.id} 「${se.title}」 状态=${ST[se.state] ?? se.state} 视频=${(s.part_episodes || []).length} 小节=${secs.map((x) => x.id).join(',')} 简介 ${(se.desc || '').length} 字`)
    console.log(`        封面 ${se.cover}`)
  }
  console.log(`   合计 ${r.data?.total ?? '?'}`)
} else if (cmd === 'resolve') {
  const r = await call(`https://api.bilibili.com/x/web-interface/view?bvid=${A[0]}`, {})
  const d = r.data || {}
  console.log(`${A[0]}: aid=${d.aid} cid=${d.pages?.[0]?.cid} title=${d.title} state=${d.state}`)
} else if (cmd === 'cover') {
  const b64 = readFileSync(A[0]).toString('base64')
  const mime = /\.(jpe?g)$/i.test(A[0]) ? 'image/jpeg' : 'image/png'
  const r = show('cover/up', await call('https://member.bilibili.com/x/vu/web/cover/up', { method: 'POST', form: { cover: `data:${mime};base64,${b64}` }, qs: { ts: String(Date.now()) } }))
  if (r.code === 0) console.log('   URL:', r.data.url)
  else process.exit(1)
} else if (cmd === 'create') {
  const [title, desc, cover] = A
  const r = show('season/add', await call(`${M}/season/add`, { method: 'POST', form: { title, desc, cover, season_price: 0 } }))
  if (r.code === 0) { writeFileSync('.temp/bili-season.json', JSON.stringify({ season_id: r.data, title, cover }, null, 1)); console.log('   新合集 id =', r.data) }
  else process.exit(1)
} else if (cmd === 'join') {
  // 实测契约（biliup/DanmakuRender 同款）：body 用 camelCase 的 sectionId + episodes；
  // snake_case 的 section_id/episode 会被服务端静默忽略并返回 code=0。
  const [sectionId, ...rest] = A
  const episodes = rest.map((s) => { const [aid, cid, ...t] = s.split(':'); return { aid: +aid, cid: +cid, title: t.join(':'), charging_pay: 0 } })
  const r = show('section/episodes/add', await call(`${M}/season/section/episodes/add`, { method: 'POST', qs: { csrf }, json: { sectionId: +sectionId, episodes } }))
  if (r.code !== 0) process.exit(1)
} else { console.log('未知子命令') }
export default out
