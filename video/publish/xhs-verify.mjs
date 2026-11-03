// 只读核验：小红书「已发布」列表里有没有给定的这条笔记。
// 为什么不用搜索框：2026-10-17 实测它会**偶发返回空结果**（同一前缀换个时刻能命中），不能当判据。
// 为什么不用单滚轮：笔记管理是**虚拟列表**（只渲染可视区约 10 条），PageDown/滚轮/scrollTop 单用都不动——
// 得先 Ctrl+Minus 缩小、再三种滚动齐上，才收得全（当晚 43/43 就是这么收的）。
// 2026-10-29 改：判据从「标题包含」换成 noteId / since。新旧同标题（换新或重发）时，
// 只按标题会把旧笔记当成新笔记，回读就成了假证据。匹配规则统一走 repost/xhs-match.mjs。
// 用法：
//   node video/publish/xhs-verify.mjs --ep s5-systick [--note-id <24位id>] [--since <ISO 时间>]
//   node video/publish/xhs-verify.mjs [--eps=a,b,c]     # 只核有 noteId/since 的集
// marker 读取顺序：命令行 --note-id > 命令行 --since > marker 的 noteId > marker 的 since。
// marker 格式见 xhs-step.mjs publish 步：noteId=… url=… at=… gate=…（或 noteId=null since=…）。
// 退出码：0=每条都命中；1=有命中不了的；2=连不上/页面没开出来；4=缺 noteId/since，拒绝标题-only 判定。
import { chromium } from 'playwright'
import { readFileSync, readdirSync, existsSync } from 'node:fs'
import { matchPublished } from './repost/xhs-match.mjs'

const ROOT = 'D:/Users/mcu'
const RUN = `${ROOT}/.temp/xhs-run`
const arg = (name) => {
  const i = process.argv.findIndex((a) => a === name || a.startsWith(`${name}=`))
  if (i < 0) return null
  const a = process.argv[i]
  return a.includes('=') ? a.slice(a.indexOf('=') + 1) : process.argv[i + 1] ?? null
}
const epArg = arg('--ep')
const epsArg = arg('--eps')
const noteIdFlag = arg('--note-id')
const sinceFlag = arg('--since')
if ((noteIdFlag || sinceFlag) && !epArg) {
  console.log('--note-id / --since 只能配合 --ep 使用：一次核一条，别把凭据套到别的集上')
  process.exit(2)
}

function titleOf(ep) {
  const f = `${ROOT}/video/episodes/${ep}/episode.json`
  if (!existsSync(f)) return '(没有 episode.json)'
  try {
    return JSON.parse(readFileSync(f, 'utf8')).publish?.xiaohongshu?.title || '(没有 xhs 标题)'
  } catch {
    return '(episode.json 读不了)'
  }
}

function readMarker(ep) {
  const p = `${RUN}/${ep}-published.txt`
  if (!existsSync(p)) return null
  const raw = readFileSync(p, 'utf8')
  const field = (k) => {
    const m = raw.match(new RegExp(`(?:^|[\\t ])${k}=([^\\t\\n]*)`))
    return m ? m[1].trim() : ''
  }
  const named = field('noteId')
  // 旧 marker 是给人读的台账（没有 noteId= 字段），但可能留着带 id= 的链接。
  const fromLink = (raw.match(/(?:[?&]id=|noteId["'=:\s]+)([0-9a-f]{24})/) || [])[1] || ''
  const noteId = named && named !== 'null' ? named : fromLink
  return { noteId, since: field('since') }
}

function allEps() {
  return readdirSync(`${ROOT}/video/episodes`).filter((d) => existsSync(`${ROOT}/video/episodes/${d}/episode.json`))
}

let targets
if (epArg) {
  const marker = readMarker(epArg)
  targets = [
    {
      ep: epArg,
      title: titleOf(epArg),
      noteId: noteIdFlag || (sinceFlag ? '' : marker?.noteId || ''),
      since: sinceFlag || marker?.since || '',
      source: noteIdFlag ? '--note-id' : sinceFlag ? '--since' : marker?.noteId ? 'marker noteId' : marker?.since ? 'marker since' : '',
    },
  ]
} else {
  const eps = epsArg ? epsArg.split(',').filter(Boolean) : allEps()
  targets = eps.map((e) => {
    const marker = readMarker(e)
    return {
      ep: e,
      title: titleOf(e),
      noteId: marker?.noteId || '',
      since: marker?.since || '',
      source: marker ? 'marker' : '',
    }
  })
}
if (!targets.length) {
  console.log('没有可核的集')
  process.exit(0)
}
console.log(`要核 ${targets.length} 条：${targets.map((t) => t.ep).join(', ')}`)
if (!targets.some((t) => t.noteId || t.since)) {
  console.log('❌ 这些集都没有 noteId/since：只按标题核对会把旧笔记认成新笔记，拒绝开跑')
  process.exit(4)
}

const b = await chromium.connectOverCDP('http://127.0.0.1:9223').catch(() => null)
if (!b) {
  console.log('❌ 连不上 9223——先把 xhs-daemon 起起来')
  process.exit(2)
}
const ctx = b.contexts()[0]
const p = await ctx.newPage()
p.setDefaultTimeout(60_000)
p.on('dialog', (d) => d.accept().catch(() => {}))
try {
  await p.goto('https://creator.xiaohongshu.com/new/note-manager', { waitUntil: 'domcontentloaded' })
  for (let i = 0; i < 40 && !(await p.locator('.note-card').count()); i++) await p.waitForTimeout(1000)
  // 不点「已发布」标签：页面上卡片自带的状态字也是「已发布」，text 选择器会先命中状态字；
  // 2026-10-29 实测点中它后列表清空为 0。默认「全部」列表本就包含已发布笔记，按 noteId/since 认人，不需要切标签。
  const head = await p.evaluate(() => (document.body.innerText.match(/全部\s*\d+/) || [''])[0])
  console.log(`列表头：${head}`)
  for (let i = 0; i < 4; i++) {
    await p.keyboard.press('Control+Minus')
    await p.waitForTimeout(300)
  }
  await p.waitForTimeout(1200)
  const seen = new Map()
  let stall = 0
  // 上限给足：44 张时实测 43 张后还剩 1 张在收尾几轮里才渲染出来（stall 太小会漏尾卡并误报）
  for (let round = 0; round < 50 && stall < 10; round++) {
    const cards = await p.evaluate(() => {
      const norm = (v) => (v || '').replace(/[\u200B-\u200D\uFEFF]/g, '').replace(/\s+/g, ' ').trim()
      const out = []
      for (const card of document.querySelectorAll('.note-card')) {
        const text = norm(card.innerText)
        const impression = card.getAttribute('data-impression') || ''
        const d = text.match(/(\d{4}[-/]\d{2}[-/]\d{2})(?:[ T](\d{2}:\d{2}))?/)
        out.push({
          id: (impression.match(/"noteId":"([0-9a-f]{24})"/) || [])[1] || '',
          title: norm(card.querySelector('.note-card__title')?.innerText),
          createTime: d ? `${d[1].replace(/\//g, '-')} ${d[2] || ''}`.trim() : '',
        })
      }
      return out
    })
    let grew = false
    for (const c of cards) {
      const key = `${c.id}|${c.title}|${c.createTime}`
      if (!seen.has(key)) {
        seen.set(key, c)
        grew = true
      }
    }
    if (!grew) stall++
    else stall = 0
    await p.keyboard.press('PageDown')
    await p.mouse.move(700, 600)
    await p.mouse.wheel(0, 1400)
    await p.evaluate(() => {
      const box = document.querySelector('.content')
      if (box) box.scrollTop = box.scrollHeight
    })
    await p.waitForTimeout(1300)
  }
  const all = [...seen.values()]
  // 总数是动态的：2026-10-17 深夜实测列表头 43→44→45 边跑边涨（ops 线在并发补发 ch24/ch25）——
  // 所以只记录"收下多少 / 列表头此刻报多少"，**不据此断言漏卡**；结论一律只看目标命中与否。
  console.log(`收下 ${all.length} 张卡片；列表头此刻报「${head}」（动态数，收尾渲染与并发写入都会让它对不齐，别当完整性基准）`)
  const miss = []
  let unknown = 0
  for (const t of targets) {
    if (!t.noteId && !t.since) {
      console.log(`❔ ${t.ep}  ${t.title}`)
      console.log('    没有 noteId/since（marker 里也没有）——拒绝只按标题判定')
      unknown++
      continue
    }
    let hits
    try {
      hits = matchPublished(all, { title: t.title, noteId: t.noteId, since: t.since })
    } catch (e) {
      console.log(`❔ ${t.ep}  ${t.title}`)
      console.log(`    判定不了：${e.message}`)
      unknown++
      continue
    }
    const hit = hits[0]
    if (hit) {
      console.log(`✅ ${t.ep}  ${t.title}`)
      console.log(`    noteId=${hit.id || '(卡片没带 id)'}  createTime=${hit.createTime || '(卡片没读到时间)'}  依据=${t.source || '?'}`)
    } else {
      console.log(`❌ ${t.ep}  ${t.title}`)
      console.log(`    没命中：noteId=${t.noteId || '-'}  since=${t.since || '-'}`)
      miss.push(t.ep)
    }
  }
  const ok = targets.length - miss.length - unknown
  console.log(`\n命中 ${ok}/${targets.length}${miss.length ? `；未命中：${miss.join(', ')}` : ''}${unknown ? `；判定不了：${unknown} 条` : ''}`)
  await p.screenshot({ path: `${RUN}/xhs-verify-published.png` })
  console.log(`截图：${RUN}/xhs-verify-published.png`)
  process.exitCode = unknown ? 4 : miss.length ? 1 : 0
} finally {
  // 缩放是 origin 级的：先把这一页还原回 100% 再关，免得影响共用窗口里别的页
  await p.keyboard.press('Control+0').catch(() => {})
  await p.close().catch(() => {})
}
process.exit(process.exitCode || 0)
