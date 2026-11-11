// 简介去 markdown 残留。B站简介区实测是 white-space:pre-line 的纯文本（页面 pre/code 元素数 0），
// 所以 ``` 围栏、行内反引号、** 星号都会原样露给观众。
// 事实源 = 编辑框现状 x/vupre/web/archive/view 里的 archive.desc；改动只落在 desc 一个字段。
// 默认 dry，只算不发；post <ep> 才走 bili-cover-edit.mjs 那一发全量回传（一发一条，逐条核对）。
import { readFileSync, writeFileSync, existsSync, mkdirSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
const ckfile = ['C:/Users/zhugu/tools/biliup-rs/biliupR-v0.2.4-x86_64-windows/cookies.json', 'C:/Users/zhugu/tools/biliup-rs/cookies.json'].find((p) => existsSync(p))
const ck = JSON.parse(readFileSync(ckfile, 'utf8')).cookie_info.cookies
const jar = ck.map((c) => `${c.name}=${c.value}`).join('; ')
const csrf = ck.find((c) => c.name === 'bili_jct').value
const view = async (bvid) => {
  // vupre 连打会 -702「请求频率过高」，这不是权限问题，间隔开重打就能过。
  for (let i = 0; i < 5; i++) {
    const r = await fetch(`https://member.bilibili.com/x/vupre/web/archive/view?bvid=${bvid}&csrf=${csrf}`, {
      headers: { cookie: jar, 'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36', referer: 'https://member.bilibili.com/platform/' } })
    const t = await r.text()
    if (/SESSDATA|bili_jct|access_token|refresh_token/.test(t)) throw new Error('响应含疑似凭证字段，整段丢弃')
    const j = JSON.parse(t)
    if (j.code === 0) return j.data
    if (j.code !== -702) throw new Error(`view code=${j.code} ${j.message}`)
    await new Promise((res) => setTimeout(res, 3000 * (i + 1)))
  }
  throw new Error('view -702 重打五次仍限频')
}
// 围栏整行删（时间轴正文照旧逐行显示）；**x** 与 `x` 只脱标记不动字；多余空行收成一个。
const clean = (s) => s
  .replace(/^[ \t]*```[a-zA-Z0-9_]*[ \t]*$/gm, '')
  .replace(/\*\*([^*\n]+?)\*\*/g, '$1')
  .replace(/`([^`\n]+?)`/g, '$1')
  .replace(/ {2,}\n/g, '\n')
  .replace(/\n{3,}/g, '\n\n')
  .trim()
const residue = (s) => ({
  围栏: (s.match(/^[ \t]*```[a-zA-Z0-9_]*[ \t]*$/gm) || []).length,
  反引号: (s.match(/`/g) || []).length,
  星号: (s.match(/\*\*/g) || []).length,
})
const bvidOf = (ep) => {
  const p = `.temp/bili-web-run/${ep}.bvid`
  return existsSync(p) ? readFileSync(p, 'utf8').trim() : null
}
// c3b 是 C3 的抖音 A/B 变体（27s，note 写明不上 B站），没稿件是设计如此，不算漏。
const list = JSON.parse(readFileSync('video/series.json', 'utf8')).episodes
const eps = list.filter((e) => e.variant !== 'ab-test' && e.status !== 'ab-test').map((e) => e.id)
const skips = list.filter((e) => e.variant === 'ab-test' || e.status === 'ab-test').map((e) => e.id)
const [mode, epArg] = process.argv.slice(2)
mkdirSync('.temp/desc-clean', { recursive: true })

if (mode === 'post') {
  const bv = bvidOf(epArg)
  if (!/^BV[0-9A-Za-z]{10}$/.test(bv || '')) { console.log(`‼️ ${epArg} 没有 bvid 留痕，停手`); process.exit(1) }
  const f = `.temp/desc-clean/${epArg}.txt`
  if (!existsSync(f)) { console.log(`‼️ 先跑 dry 生成 ${f}`); process.exit(1) }
  // 参数按数组传，不过 shell，正文里的反引号/星号/$ 都不会被解释。
  execFileSync('node', ['video/publish/bili-editbox.mjs', bv], { stdio: 'inherit' })
  execFileSync('node', ['video/publish/bili-cover-edit.mjs', 'edit', bv, '-', 'full', `desc=@${f}`], { stdio: 'inherit' })
  await new Promise((res) => setTimeout(res, 2500))
  const d = await view(bv)
  const live = (d.archive || {}).desc || ''
  const r = residue(live)
  console.log(`核对 ${epArg} ${bv}：现简介 ${live.length} 字｜残留 围栏=${r.围栏} 反引号=${r.反引号} 星号=${r.星号}｜state=${d.archive?.state ?? '?'}｜与本地目标${live === readFileSync(f, 'utf8') ? '逐字一致' : '不一致'}`)
  process.exit(r.围栏 + r.反引号 + r.星号 ? 1 : 0)
}

const rows = []
for (const ep of eps) {
  await new Promise((res) => setTimeout(res, 1500))
  const bv = bvidOf(ep)
  if (!/^BV[0-9A-Za-z]{10}$/.test(bv || '')) { rows.push({ ep, bv, skip: '无 bvid 留痕' }); continue }
  let d
  try { d = await view(bv) } catch (e) { rows.push({ ep, bv, skip: `读不到：${e.message}` }); continue }
  const a = d.archive || {}
  const src = a.desc || ''
  const dst = clean(src)
  mkdirSync('.temp/desc-live', { recursive: true })
  writeFileSync(`.temp/desc-live/${ep}.txt`, src)   // 改前原文留底，改坏了能逐字回滚
  writeFileSync(`.temp/desc-clean/${ep}.txt`, dst)
  const rs = residue(src), rd = residue(dst)
  // 只许脱标记：把标记以外的差异全部当异常，宁可不发。
  const bare = (x) => x.replace(/[`*\s]/g, '')
  const onlyMarkers = bare(dst) === bare(src)
  rows.push({ ep, bv, 前: src.length, 后: dst.length, 前残留: `${rs.围栏}/${rs.反引号}/${rs.星号}`, 后残留: `${rd.围栏}/${rd.反引号}/${rd.星号}`, 纯标记差: onlyMarkers, 超2000: dst.length > 2000, skip: src ? '' : '现简介为空' })
}
console.log(`共 ${eps.length} 条上过 B站（另有 ${skips.length} 条不走 B站：${skips.join(',') || '无'}），逐条（围栏/反引号/星号）：`)
for (const r of rows) {
  if (r.skip) { console.log(`   ${r.ep.padEnd(16)} ${r.bv || '-'}  ‼️ ${r.skip}`); continue }
  console.log(`   ${r.ep.padEnd(16)} ${r.bv} ${String(r.前).padStart(4)}→${String(r.后).padStart(4)}字 残留 ${r.前残留}→${r.后残留} 纯标记差=${r.纯标记差 ? '✓' : '‼️否'}${r.超2000 ? ' ‼️超2000' : ''}`)
}
const bad = rows.filter((r) => r.skip || r.后残留 !== '0/0/0' || !r.纯标记差 || r.超2000)
console.log(bad.length ? `‼️ ${bad.length} 条不干净，别批量发` : `✓ 全部可发：残留归零且只动了标记字符。逐条跑 node video/publish/bili-desc-fix.mjs post <ep>`)
