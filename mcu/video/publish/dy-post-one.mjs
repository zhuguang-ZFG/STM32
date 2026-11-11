// 一条命令投完一集抖音竖版：复用 video/publish/douyin-step.mjs 里那套已验证过的选择器，
// 自己不重写任何 DOM 逻辑（重写一次就多踩一次坑）。
// 硬闸门：verify 读回来的六项不对，就不写放行标记、不点发布，直接非零退出。
// --from=<步> 从断掉那步接着走：常驻浏览器里视频和已填的字都还在，重跑 nav 等于白传一遍片源
// （B站那边 p4 撞 21010 之后就是靠 redesc 补简介才没重传 46 MB）。
import { execFileSync } from 'node:child_process'
import { rmSync, existsSync, appendFileSync, readFileSync } from 'node:fs'

const EP = process.argv[2]
if (!EP) throw new Error('用法：node video/publish/dy-post-one.mjs <episode-id> [--from=<步>]')
const RUN = 'D:/Users/mcu/.temp/douyin-run'
const ORDER = ['nav', 'pick', 'retxt', 'cover', 'coveredit', 'coverup-v', 'coverset-v', 'coverup-h', 'coverset-h', 'seasonpick', 'declare', 'title', 'verify', 'publish']
const argVal = (n) => { const a = process.argv.find((x) => x.startsWith(`${n}=`)); return a ? a.slice(n.length + 1) : null }
const FROM = argVal('--from') ?? 'nav'
const fi = ORDER.indexOf(FROM)
if (fi < 0) throw new Error(`--from 只认：${ORDER.join(' | ')}`)
const step = (name, extra = []) => {
  const out = execFileSync('node', ['video/publish/douyin-step.mjs', name, '--ep', EP, ...extra], {
    cwd: 'D:/Users/mcu', encoding: 'utf8', maxBuffer: 32 * 1024 * 1024,
  })
  console.log(`── ${name} ──\n${out.split('\n').slice(0, 3).join('\n')}`)
  return out
}
const at = (tag, name, extra = []) => {
  if (ORDER.indexOf(tag) < fi) { console.log(`── ${tag} ── 跳过（--from=${FROM}）`); return null }
  return step(name, extra)
}

// 重跑一次就是再传一遍视频、再发一份重复稿——抖音不会像 B站那样回一个已存在的号。
// published.txt 只在点完发布后落，所以它是"这条已经在线"的凭据；要强制重投自己说清楚。
if (existsSync(`${RUN}/${EP}-published.txt`) && !process.env.FREE_RESUBMIT) {
  console.log(`‼️ ${EP} 已经投过（${RUN}/${EP}-published.txt：${readFileSync(`${RUN}/${EP}-published.txt`, 'utf8').slice(0, 70)}）\n   确实要再发一条，自己确认后 FREE_RESUBMIT=1 node video/publish/dy-post-one.mjs ${EP}`)
  process.exit(1)
}

const ep = JSON.parse(readFileSync(`D:/Users/mcu/video/episodes/${EP}/episode.json`, 'utf8'))
const pub = ep.publish.douyin

at('nav', 'nav', ['--url', 'https://creator.douyin.com/creator-micro/content/upload'])
at('pick', 'pick')
at('retxt', 'retxt')
at('cover', 'cover', ['--slot', '0'])
// slot 那条喂的是 input[type=file] 的 .last()，而 douyin-step.mjs 早就写明这类 input 左边那个是
// 「生成参考图」——线上六条的竖封面全退回成视频第 0 帧就是这么来的。竖封面必须和横封面一样走模态流。
at('coveredit', 'coveredit', ['--which', 'v'])
at('coverup-v', 'coverup', ['--which', 'v'])
at('coverset-v', 'coverset', ['--which', 'v'])
at('coverup-h', 'coverup', ['--which', 'h'])
at('coverset-h', 'coverset', ['--which', 'h'])
at('seasonpick', 'seasonpick')
at('declare', 'declare')
at('title', 'title')
// verify 永远跑，不吃 --from。上一版它是 at('verify',…)：--from=publish 时返回 null，
// 下一行的 .match 当场 TypeError，f3 连着两次就是这么在发布前 0 秒崩掉的——
// 而它是不可逆动作前的最后一道闸，跳过它的理由一个都不成立（它只读页面，不写任何东西）。
const v = JSON.parse(step('verify').match(/^\{[\s\S]*?^\}/m)[0])

const series = JSON.parse(readFileSync('D:/Users/mcu/video/series.json', 'utf8')).series
const want = {
  title: pub.titles[0],
  season: series,
  declare: pub.declare,
  needDetect: ['封面效果检测通过', '作品未见异常'],
}
const bad = []
if (v.title !== want.title) bad.push(`标题不符：${JSON.stringify(v.title)}`)
if (!v.desc?.includes(pub.caption.split('\n')[0])) bad.push(`描述缺首句：${JSON.stringify(v.desc?.slice(0, 40))}`)
if (!v.coverV || !v.coverH) bad.push(`封面缺失 v=${!!v.coverV} h=${!!v.coverH}`)
if (v.season !== want.season) bad.push(`合集不符：${JSON.stringify(v.season)}`)
for (const d of want.needDetect) if (!(v.detect || []).includes(d)) bad.push(`检测项缺失：${d}`)
if (v.visibility !== '公开') bad.push(`可见性：${JSON.stringify(v.visibility)}`)
// 自主声明没选的话，点「发布」既不弹窗也不报错，页面就原地不动——上一版正是被它静默卡住的。
if (!want.declare) bad.push('episode.json 缺 publish.douyin.declare：自主声明是必填项，不替这一集猜')
else if (!v.declare?.includes(want.declare)) bad.push(`自主声明不符：${JSON.stringify(v.declare)}`)
if (bad.length) {
  console.log('✗ 发布前核对未过，已停手：\n  ' + bad.join('\n  '))
  process.exit(2)
}
console.log(`✓ 七项核对全过（标题 ${v.titleCnt} / 描述 ${v.descCnt} / 合集 ${v.episodeNo} / 声明 ${v.declare}）`)

// 放行标记只能来自对话里的点头，脚本不自己造。
// 上一版这里自己 writeFileSync 一个"由某某指令放行"——那等于脚本给自己开了张通行证，
// 六项核对再严也还是"我信我自己"。现在缺这个文件就停手，谁点的发布谁负责写它。
const gate = `${RUN}/I_HAVE_USER_OK=${EP}`
if (!existsSync(gate)) {
  console.log(`✗ 七项核对全过，但没有 ${gate}——不点发布。\n   用户在对话里点头之后由我写这个文件，再跑一次 --from=publish（不会重传视频）`)
  process.exit(3)
}
console.log(`✓ 放行标记在：${gate}\n   ${readFileSync(gate, 'utf8').trim()}`)
at('publish', 'publish')
rmSync(gate, { force: true })
appendFileSync(`${RUN}/posted.txt`, `${new Date().toISOString()}\t${EP}\n`)
console.log('已投：', EP)
