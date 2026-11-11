// 用不登录的公开 view 接口复核：状态码只在我们自己的 cookie 通道里看得到，
// 观众能不能真看到这条，得用无凭证的请求量一次。
for (const id of process.argv.slice(2)) {
  try {
    const r = await fetch(`https://api.bilibili.com/x/web-interface/view?bvid=${id}`, { headers: { 'User-Agent': 'Mozilla/5.0' } })
    const j = await r.json()
    const d = j.data || {}
    console.log(`${id} http=${r.status} code=${j.code} ｜${d.title ? d.title.slice(0, 24) : j.message}｜state=${d.state} owner=${d.owner?.name} pv=${d.stat?.view}`)
  } catch (e) {
    console.log(`${id} 请求失败：${String(e.message).slice(0, 60)}`)
  }
}
