// 换线上稿件的封面。四步分开、可单独重跑：
//   snapshot <bvid>            读公开 view+tag，存 .temp/bili-<bvid>-before.json（diff 的基准）
//   upload   <png>             把封面推到 biliimg，打印新 URL
//   （另需 node video/publish/bili-editbox.mjs <bvid> 先取编辑框现状，见下）
//   edit     <bvid> <url> full  POST 编辑接口；全字段照编辑框原样回传，只把 cover 换成新 URL
//   diff     <bvid>            再读一次，和快照逐字段比，任何一项变了都标红
// 编辑是覆盖式提交：videos[].filename 缺 → 21015，videos[] 缺 → 21011，tag 写成 tags → 21001。
// 能给出 filename 与各开关现值的只有 x/vupre/web/archive/view，所以编辑前必须先取编辑框现状。
// 凭证只进 cookie 头与 csrf 参数，任何输出都不含 cookie 值；响应里混进凭证字段整段丢弃。
import { readFileSync, writeFileSync, existsSync } from 'node:fs'
const CAND = ['C:/Users/zhugu/tools/biliup-rs/biliupR-v0.2.4-x86_64-windows/cookies.json', 'C:/Users/zhugu/tools/biliup-rs/cookies.json']
const file = CAND.find((p) => existsSync(p))
if (!file) { console.log('‼️ 找不到 cookies.json'); process.exit(1) }
const ck = JSON.parse(readFileSync(file, 'utf8')).cookie_info.cookies
const jar = ck.map((c) => `${c.name}=${c.value}`).join('; ')
const csrf = ck.find((c) => c.name === 'bili_jct')?.value || ''
if (!csrf) { console.log('‼️ cookie 里没有 bili_jct'); process.exit(1) }
const UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
const [cmd, ...A] = process.argv.slice(2)
const clean = (t) => (/SESSDATA|bili_jct|access_token|refresh_token|bili_jct=/.test(t) ? '‼️响应含疑似凭证字段，整段丢弃' : t)
async function reqOnce(u, { method = 'GET', json, form } = {}) {
  const headers = { 'user-agent': UA, referer: 'https://member.bilibili.com/platform/upload-manager/', cookie: jar }
  let body
  if (json) { headers['content-type'] = 'application/json'; body = JSON.stringify(json) }
  if (form) { headers['content-type'] = 'application/x-www-form-urlencoded'; body = new URLSearchParams(form).toString() }
  const r = await fetch(u, { method, headers, body })
  const t = clean(await r.text())
  try { return { http: r.status, j: JSON.parse(t) } } catch { return { http: r.status, raw: t.slice(0, 200) } }
}
// s2-rcc 那次：稿件已经投出去了，repair 第一条 API 调用被代理掐断（UND_ERR_SOCKET / other side closed），
// 这个异常没人接，进程直接崩，批次把"已投稿"误判成"失败"停住。socket 层断线重跑同一条是安全的：
// 这一层全是全量状态提交（edit 传整套字段、cover 传整张图），发两次落在同一个终态上。
// 只重 socket 级错误；平台返回 code!=0 不在这儿重试，那是内容问题，重试没用。
const SOCKET_ERR = (e) => /UND_ERR_SOCKET|other side closed|ECONNRESET|ETIMEDOUT|socket hang up|ECONNREFUSED|fetch failed/i
  .test(`${e?.cause?.code ?? ''} ${e?.cause?.message ?? ''} ${e?.message ?? ''}`)
async function req(u, opt) {
  for (let i = 0; ; i++) {
    try { return await reqOnce(u, opt) } catch (e) {
      if (!SOCKET_ERR(e) || i >= 2) throw e
      console.log(`  ↻ 连接被断（${String(e.message).slice(0, 30)}），2 秒后重跑第 ${i + 1} 次：${u.replace(/^\w+:\/\/[^/]+/, '')}`)
      await new Promise((r) => setTimeout(r, 2000))
    }
  }
}
// 快照 = 之后 diff 的基准，也是还原时的唯一事实源，所以字段取全，不留"当时没读"的死角
const snap = async (bvid) => {
  const v = (await req(`https://api.bilibili.com/x/web-interface/view?bvid=${bvid}`)).j?.data
  if (!v) { console.log('‼️ view 读不到'); process.exit(1) }
  const tags = ((await req(`https://api.bilibili.com/x/tag/archive/tags?bvid=${bvid}`)).j?.data || []).map((t) => t.tag_name)
  return {
    bvid, aid: v.aid, tid: v.tid, title: v.title, desc: v.desc, pic: v.pic, source: v.source ?? '', dynamic: v.dynamic || '',
    copyright: v.copyright ?? v.rights?.copyright, no_reprint: v.rights?.no_reprint, tags, parts: v.pages.map((p) => ({ cid: p.cid, part: p.part })),
    argue_msg: v.argue_msg || '', state: v.state, duration: v.duration,
  }
}
// 覆盖项写进嵌套字段用 a.b=c 这种路径；值一律先当字符串，JSON 能解析就按 JSON 塞。
const put = (obj, key, val) => { const path = key.split('.'); let t = obj
  for (let i = 0; i < path.length - 1; i++) t = t[path[i]] ??= {}
  t[path[path.length - 1]] = val }
// 编辑接口是覆盖式提交：少一个字段就撞 21011/21015，所以整份载荷只能从编辑框现状拼，
// 再按 over 逐字段掰。dolby/lossless_music/human_type/creation_statement 不在这里出现——
// 实测它们发布后回传要么 21001 要么 code=0 但值不变，带上只会把上一次的修复顶掉。
const buildFull = (bvid, d, cover, over = {}) => {
  const a = d.archive || {}
  const num = (v, dflt) => (v === undefined || v === null || v === '' ? dflt : +v)
  const full = {
    aid: +a.aid,
    bvid,
    videos: (d.videos || []).map((v) => ({ filename: v.filename, title: v.title, desc: v.desc || '', cid: v.cid })),
    title: a.title,
    cover,
    cover43: a.cover43 || '',
    copyright: num(a.copyright),
    source: a.source || '',
    tid: num(a.tid),
    tag: a.tag,
    desc_format_id: num(a.desc_format_id, 9999),
    desc: a.desc || '',
    recreate: num(a.recreate?.switch, -1),
    dynamic: a.dynamic || '',
    interactive: num(a.interactive, 0),
    act_reserve_create: num(d.act_reserve_create, 0),
    no_disturbance: num(d.no_disturbance, 0),
    no_reprint: num(a.no_reprint),
    subtitle: { open: d.subtitle?.allow === false ? 0 : 1, lan: d.subtitle?.lan || '' },
    web_os: 1,
    mission_id: num(a.mission_id, 0),
    is_360: num(a.is_360, -1),
    is_only_self: num(a.is_only_self, 0),
    new_web_edit: 1,
  }
  for (const [k, v] of Object.entries(over)) put(full, k, v)
  const miss = ['aid', 'tid', 'title', 'cover', 'tag', 'copyright', 'no_reprint', 'desc_format_id', 'recreate']
    .filter((k) => full[k] === undefined || full[k] === null || Number.isNaN(full[k]) || full[k] === '')
  if (miss.length) throw new Error(`编辑框现状里缺必要字段，不发：${miss.join(',')}`)
  if (!full.videos.length || full.videos.some((v) => !v.cid || !v.filename)) throw new Error('分P 缺 cid/filename，不发（21011/21015 就是它们）')
  return full
}
const postEdit = async (full, tag) => {
  console.log(`   回传：标题 ${full.title.length} 字｜简介 ${full.desc.length} 字｜标签 ${full.tag.split(',').length} 个｜分P ${full.videos.map((v) => v.filename.slice(0, 8) + '…/' + v.cid).join(',')}｜tid ${full.tid}｜copyright ${full.copyright}｜no_reprint ${full.no_reprint}｜recreate ${full.recreate}｜desc_format_id ${full.desc_format_id}`)
  const r = await req(`https://member.bilibili.com/x/vu/web/edit?ts=${Date.now()}&csrf=${csrf}`, { method: 'POST', json: full })
  console.log(`edit(${tag}): http=${r.http} code=${r.j?.code} ${r.j?.message || r.j?.msg || r.raw || ''}`)
  if (r.j?.code !== 0) process.exit(1)
  console.log('   data:', JSON.stringify(r.j.data || {}).slice(0, 160))
}
// bili-submit.yaml 是缩进固定的流式条目，取 4 空格那一层的标量字段够用
const yf = (txt, k) => {
  const m = txt.match(new RegExp(`^ {4}${k}: (.*)$`, 'm'))
  if (!m) throw new Error(`yaml 里没有 ${k}`)
  return m[1].replace(/^"(.*)"$/, '$1')
}
if (cmd === 'snapshot') {
  const s = await snap(A[0])
  writeFileSync(`.temp/bili-${A[0]}-before.json`, JSON.stringify(s, null, 1))
  console.log(`快照：aid=${s.aid} tid=${s.tid} 标题 ${s.title.length} 字 简介 ${s.desc.length} 字 标签 ${s.tags.length} 个 分P ${s.parts.length} 个`)
  console.log('  当前封面', s.pic)
} else if (cmd === 'upload') {
  const b64 = readFileSync(A[0]).toString('base64')
  const mime = /\.(jpe?g)$/i.test(A[0]) ? 'image/jpeg' : 'image/png'
  const r = await req(`https://member.bilibili.com/x/vu/web/cover/up?ts=${Date.now()}&csrf=${csrf}`, { method: 'POST', form: { cover: `data:${mime};base64,${b64}` } })
  const j = r.j || {}
  console.log(`cover/up: http=${r.http} code=${j.code} ${j.message || r.raw || ''}`)
  if (j.code === 0) console.log('NEWURL', j.data.url)
  else process.exit(1)
} else if (cmd === 'edit') {
  const [bvid, coverArg, mode, ...sets] = A
  if (mode !== 'full') { console.log('‼️ 不再支持只回传 {bvid,aid,cover}：缺 videos[] 会撞 21011，缺 filename 会撞 21015'); process.exit(1) }
  // 覆盖项 --set k=v：值一律先当字符串，JSON 能解析就按 JSON 塞（数字/对象/数组/null 都要能表达）。
  // 为什么要能覆盖：网页通道发出去的稿子实测把 tid 落成 201、copyright 落成 3、杜比/Hi-Res 勾成 1，
  // 事实源要的是 231/1/0，只能在这一发按字段掰回来。
  // v 以 @ 开头时按文件读：简介是上千字带换行的正文，走命令行必然被 shell 掰断，只认文件。
  const over = {}
  for (const s of sets) {
    const m = s.match(/^([A-Za-z0-9_.]+)=(.*)$/)
    if (!m) { console.log(`‼️ 覆盖项写法不对：${s}（要 k=v）`); process.exit(1) }
    let v
    if (m[2].startsWith('@')) {
      const p = m[2].slice(1)
      if (!existsSync(p)) { console.log(`‼️ ${m[1]} 的取值文件不存在：${p}`); process.exit(1) }
      v = readFileSync(p, 'utf8')
    } else {
      try { v = JSON.parse(m[2]) } catch { v = m[2] }
    }
    over[m[1]] = v
    console.log(`   覆盖 ${m[1]} = ${typeof v === 'object' ? JSON.stringify(v) : `${String(v).length} 字`}`)
  }
  // cover 传 '-' 表示沿用编辑框现值（只改别的字段时不动封面）
  const EB = `.temp/bili-${bvid}-editbox.json`
  if (!existsSync(EB)) { console.log(`‼️ 先跑 node video/publish/bili-editbox.mjs ${bvid} 取编辑框现状`); process.exit(1) }
  const d = JSON.parse(readFileSync(EB, 'utf8'))
  const cover = coverArg === '-' ? (d.archive || {}).cover : coverArg
  if (!cover) { console.log('‼️ 没有封面 URL'); process.exit(1) }
  await postEdit(buildFull(bvid, d, cover, over), mode)
} else if (cmd === 'repair') {
  // 网页通道的表单会自己决定一批字段：tid 落 201、copyright 落 3、封面转成 jpg 还配一张
  // 4:3、像「单片机」这种标签被静默吞掉。这几项投稿后 edit 都能改，所以一条命令做完：
  // 读 yaml 事实源 → 取编辑框现状（标题必须逐字相同才认）→ 传 PNG → 回传 → 复读逐字段核对。
  const [bvid, yamlPath] = A
  if (!bvid || !yamlPath) { console.log('‼️ 用法：repair <bvid> <bili-submit.yaml>'); process.exit(1) }
  const y = readFileSync(yamlPath, 'utf8')
  const want = { tid: +yf(y, 'tid'), copyright: +yf(y, 'copyright'), tag: yf(y, 'tag'), source: yf(y, 'source'), cover43: '' }
  const png = yf(y, 'cover')
  if (!existsSync(png)) { console.log(`‼️ 封面不存在：${png}`); process.exit(1) }
  const v = (await req(`https://member.bilibili.com/x/vupre/web/archive/view?bvid=${bvid}&csrf=${csrf}`)).j?.data
  if (!v) { console.log('‼️ 编辑框现状读不到，不发'); process.exit(1) }
  // 认错稿件就是往别人的视频上改字，这一道必须过。
  if (v.archive?.title !== yf(y, 'title')) {
    console.log(`‼️ 标题对不上，停手：\n   稿件=${v.archive?.title}\n   yaml=${yf(y, 'title')}`)
    process.exit(1)
  }
  console.log(`   ${bvid} 标题逐字一致，现状 tid=${v.archive.tid} copyright=${v.archive.copyright} 标签=${String(v.archive.tag).split(',').length} 个`)
  if (A[2] === 'dry') { console.log(`   dry：只核对不写。将回传 tid=${want.tid} copyright=${want.copyright} cover43='' tag=${want.tag}｜封面 ${png}`); process.exit(0) }
  const b64 = readFileSync(png).toString('base64')
  const mime = /\.(jpe?g)$/i.test(png) ? 'image/jpeg' : 'image/png'
  const up = (await req(`https://member.bilibili.com/x/vu/web/cover/up?ts=${Date.now()}&csrf=${csrf}`, { method: 'POST', form: { cover: `data:${mime};base64,${b64}` } })).j || {}
  if (up.code !== 0) { console.log(`‼️ cover/up code=${up.code} ${up.message || ''}`); process.exit(1) }
  console.log(`   封面已传 ${up.data.url}`)
  await postEdit(buildFull(bvid, v, up.data.url, want), 'repair')
  const chk = (await req(`https://member.bilibili.com/x/vupre/web/archive/view?bvid=${bvid}&csrf=${csrf}`)).j?.data || {}
  const after = chk.archive || {}
  const img = (u) => String(u || '').replace(/^https?:\/\/[^/]+\//, '')
  const rows = [['tid', +after.tid, want.tid], ['copyright', +after.copyright, want.copyright],
    ['标签数', String(after.tag || '').split(',').length, want.tag.split(',').length],
    ['cover43', after.cover43 || '', ''], ['封面后缀', img(after.cover).split('.').pop(), 'png'],
    ['声明', after.creation_statement?.content ?? '', '内容无需标注'], ['dolby', after.is_dolby, '0'],
    ['Hi-Res', after.lossless_music, '0'], ['水印', chk.watermark?.id, 0]]
  for (const [k, got, exp] of rows) console.log(`  ${String(got) === String(exp) ? '✓' : '⚠'} ${k} = ${got}${String(got) === String(exp) ? '' : `（事实源 ${exp}）`}`)
  console.log(`  状态 ${after.state}（0=开放浏览，-6=修改待审核）`)
} else if (cmd === 'diff') {
  const s = JSON.parse(readFileSync(`.temp/bili-${A[0]}-before.json`, 'utf8'))
  const n = await snap(A[0])
  const keys = ['aid', 'tid', 'title', 'desc', 'source', 'dynamic', 'copyright', 'no_reprint', 'argue_msg', 'state', 'duration']
  for (const k of keys) if (JSON.stringify(s[k]) !== JSON.stringify(n[k])) console.log(`⚠ 变了 ${k}：${JSON.stringify(s[k]).slice(0, 60)} → ${JSON.stringify(n[k]).slice(0, 60)}`)
  // tags 接口每次返回的顺序不同（实测同一篇稿件两次读数互换 STM32/Cortex-M4），
  // 所以比集合不比顺序；否则编辑没动标签也会被这里报成"变了"。
  const set = (x) => [...x].sort().join()
  if (set(s.tags) !== set(n.tags)) console.log(`⚠ 标签集合变了：${set(s.tags)} → ${set(n.tags)}`)
  if (s.parts.map((p) => p.part).join() !== n.parts.map((p) => p.part).join()) console.log('⚠ 分P 标题变了')
  // 同一张图会从 i0/i1/i2 不同子域返回，比路径里的 sha 不比整个 URL
  const img = (u) => String(u || '').replace(/^https?:\/\/[^/]+\//, '')
  console.log(`封面：${img(s.pic) === img(n.pic) ? '没变（POST 可能没生效）' : '已换 → ' + n.pic}`)
  console.log(`状态：${n.state}（0=开放浏览，-6=审核中）｜ 标题 ${n.title.length} 字 ｜ 简介 ${n.desc.length} 字 ｜ 标签 ${n.tags.length} 个`)
} else if (cmd === 'recent') {
  // 网页通道投稿成功后页面只写「稿件投递成功」，不一定把 BV 号留在正文里。
  // 稿件管理那个接口按 list_type 分栏，实测新投的在 arc_audits（archives 是 null），
  // 而且每条还包了一层 Archive——直接读 it.bvid 会全是 undefined。
  const n = +(A[0] || 8)
  const now = (s) => { const d = new Date(s * 1000); return Number.isNaN(+d) ? String(s) : d.toISOString().replace('T', ' ').slice(0, 19) }
  for (const lt of ['30', '11', '71']) {
    const j = (await req(`https://member.bilibili.com/x/web/archives?list_type=${lt}&pagesize=${n}&page=1&order=ctime&platform=pc&status=&term=`)).j || {}
    if (j.code !== 0) { console.log(`list_type=${lt}: ‼️ code=${j.code} ${j.message || j.msg || ''}`); continue }
    const d = j.data || {}
    const rows = [...(d.archives || []), ...(d.arc_audits || []).map((x) => x.Archive || x)]
    console.log(`list_type=${lt}：archives=${(d.archives || []).length} arc_audits=${(d.arc_audits || []).length}`)
    for (const it of rows.slice(0, n)) {
      console.log(`  ${it.bvid} ctime=${now(+it.ctime)} state=${it.state} tid=${it.tid} ${(it.status_desc || '').slice(0, 12)}｜${String(it.title).slice(0, 30)}`)
    }
  }
} else console.log('用法：snapshot|upload|edit|diff|recent|repair')
