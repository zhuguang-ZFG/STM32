// 合集控件在 Lv2 才出现（#42 实测第 7 条：等级不够时「加入合集」整块不存在）。
// 16 条发完了，等级可能已经翻上去——只读这一格，不打印任何凭证。
import { readFileSync, existsSync } from 'node:fs'
const CAND = ['C:/Users/zhugu/tools/biliup-rs/biliupR-v0.2.4-x86_64-windows/cookies.json', 'C:/Users/zhugu/tools/biliup-rs/cookies.json']
const file = CAND.find((p) => existsSync(p))
const ck = JSON.parse(readFileSync(file, 'utf8')).cookie_info.cookies
const jar = ck.map((c) => `${c.name}=${c.value}`).join('; ')
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
const get = async (u, referer) => {
  const t = await (await fetch(u, { headers: { Cookie: jar, 'User-Agent': UA, Referer: referer } })).text()
  // 和这条线其它脚本同规矩：响应里混进凭证字段就整段丢弃，绝不落到 stdout。
  return /SESSDATA|bili_jct|access_token|refresh_token/.test(t) ? '{"code":-1,"message":"响应含疑似凭证字段，整段丢弃"}' : t
}
// x/member/web/exp 无头直连经常回风控 HTML（不带 buvid 时天天如此），拿它当硬依赖就会整脚本崩。
const asJson = (t, tag) => { try { return JSON.parse(t) } catch { console.log(`${tag}: 非 JSON（风控页），跳过`); return null } }
const j = asJson(await get('https://api.bilibili.com/x/member/web/exp', 'https://www.bilibili.com/'), 'exp')
if (j && j.code !== 0) console.log(`exp code=${j.code} ${j.message}`)
if (j?.code === 0) {
  const l = j.data.level_info
  // 合集门槛看的是「权益中心等级 Lv2」，不是这里的用户经验等级——两者不同源。
  // 上一版拿 current_level>=2 判「能否建合集」，实测本账号用户等级 Lv4 仍建不了集（season=false），那句推断作废。
  console.log(`用户等级 Lv${l.current_level}｜经验 ${j.data.current_exp}｜本级下限 ${l.current_min}｜下一级下限 ${l.current_max}`)
}
// csrf 只进查询参数，值本身任何一路都不打印。
const CSRF = ck.find((c) => c.name === 'bili_jct')?.value || ''
const w = asJson(await get(`https://member.bilibili.com/x/vupre/web/archive/white?csrf=${CSRF}`, 'https://member.bilibili.com/platform/'), 'white')
if (!w) process.exit(0)
if (w.code !== 0) { console.log(`white code=${w.code} ${w.message}`); process.exit(0) }
const d = w.data || {}
console.log(`合集权限位：season=${d.season} new_season=${d.new_season} season_scope=${d.season_scope} season_add_multip=${d.season_add_multip}`)
console.log(d.season || d.new_season ? '→ 已解锁，可以跑 video/publish/bili-collection.mjs create' : '→ 未解锁：建集接口会回 code=20082「合集个数太多」，那是权限位的伪装文案，不是额度')
