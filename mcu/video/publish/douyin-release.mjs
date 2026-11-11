// 只重写"发布文案"，不重渲任何一帧：读 video/out/<ep>/douyin/timeline.json（产线 mux 时已断言过
// 它和 mp4 实际时长差 < 1/fps），直接喂给 package.mjs 的 writeRelease。
// 顺手产出 video/publish/douyin-plan.generated.md：投稿顺序、绝对路径、描述、置顶评论、封面，一张表抄完。
// 用法：node video/publish/douyin-release.mjs
import { readFileSync, writeFileSync, existsSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { loadEpisode, platformConfig, resolveScenes } from '../src/spec.mjs'
import { writeRelease } from '../src/package.mjs'
import { fmtClock } from '../src/util.mjs'

const ROOT = 'D:/Users/mcu'
const series = JSON.parse(readFileSync(join(ROOT, 'video/series.json'), 'utf8'))
const ORDER = series.episodes.map((e) => e.id)
const byId = new Map(series.episodes.map((e) => [e.id, e]))
const COLLECTION = '通往单片机之路 · 屏上每个数都是本机跑的'

const rows = []
const OFFSITE_SEE = /站内|全文免费|有全篇|通往单片机之路|克隆仓库|仓库里|那个目录/
// 扫的是竖版**真的会给观众看到/听到**的字段：pick 选中的场 + douyin 自己的覆写。
// 分两类：把人往站外带的是导流；"站内那张选型表原本这么写"这种是交代出处，不是导流。
function scanOffsite(ep) {
  const dy = ep.platforms.douyin
  if (!dy) return []
  // 竖版有两种写法：pick（从 B站那套场里挑 id，f5/s2…）和 scenes（自己带场定义，f0/c3b——
  // c3b 根本没有 platforms.bilibili）。只认 pick 就在 f0 上 TypeError，只查 bilibili 就在 c3b 上崩。
  const sids = dy.pick || (dy.scenes || []).map((s) => s.id)
  const byId = new Map((ep.platforms.bilibili?.scenes || dy.scenes || []).map((s) => [s.id, s]))
  const out = []
  for (const sid of sids) {
    const s = byId.get(sid)
    if (!s) continue
    // 竖版旁白是 `platforms.douyin.narration[sceneId]` 覆写的，不是 set 里的字段——
    // 只并 set 就会扫到 B站那句长版，把"站内 X 全文免费"这种竖版收尾句整个漏掉。
    const merge = { ...s, ...(dy.set?.[sid] || {}), ...(dy.narration?.[sid] ? { narration: dy.narration[sid] } : {}) }
    const flds = { narration: merge.narration, title: merge.title, sub: merge.sub, note: merge.note, bullets: (merge.bullets || []).join(' | ') }
    for (const [k, v] of Object.entries(flds)) {
      if (typeof v === 'string' && OFFSITE_SEE.test(v)) out.push({ sid, k, v: v.match(/.{0,14}(站内|全文免费|有全篇|通往单片机之路|克隆仓库|仓库里|那个目录).{0,10}/)[0].replace(/\n/g, ' ⏎ ') })
    }
  }
  return out
}
const offsite = []
for (const id of ORDER) {
  const ep = loadEpisode(id)
  for (const h of scanOffsite(ep)) offsite.push({ id, badge: ep.badge, ...h })
}
const ctaLeads = offsite.filter((h) => h.sid === 'cta' && /站内|全文免费|有全篇|通往单片机之路/.test(h.v))
const ctaKeys = new Set(ctaLeads.map((h) => h.id + '/' + h.sid + '.' + h.k))
const repoLeads = offsite.filter((h) => /克隆仓库|仓库里|那个目录/.test(h.v) && !ctaKeys.has(h.id + '/' + h.sid + '.' + h.k))
const repoKeys = new Set(repoLeads.map((h) => h.id + '/' + h.sid + '.' + h.k))
const attrib = offsite.filter((h) => !ctaKeys.has(h.id + '/' + h.sid + '.' + h.k) && !repoKeys.has(h.id + '/' + h.sid + '.' + h.k))
const epSet = (arr) => [...new Set(arr.map((h) => h.badge))].join('、')
const digest = [
  `- 收尾那句明说"站内 X 有全篇/全文免费"的：**${new Set(ctaLeads.map((h) => h.id)).size} 集、${ctaLeads.length} 个字段**（${epSet(ctaLeads)}）`,
  `- 说"仓库里跑一遍 / 克隆仓库进那个目录"的：**${new Set(repoLeads.map((h) => h.id)).size} 集、${repoLeads.length} 个字段**（${epSet(repoLeads)}）`,
  `- 只是交代出处、不算导流的（如 F6"站内那张选型表原本这么写"）：**${attrib.length} 个字段**（${epSet(attrib)}）`,
  `- 合计 ${offsite.length} 个字段，分布在 ${new Set(offsite.map((h) => h.id)).size} / ${ORDER.length} 集`,
]
for (const id of ORDER) {
  const ep = loadEpisode(id)
  const cfg = platformConfig(ep, 'douyin')
  const tFile = join(ROOT, 'video/out', id, 'douyin/timeline.json')
  if (!existsSync(tFile)) throw new Error(`${id} 缺 douyin/timeline.json——这条还没渲过，别造文案`)
  const timeline = JSON.parse(readFileSync(tFile, 'utf8'))
  const distDir = join(ROOT, 'video/out', id)
  const mp4 = join(distDir, 'douyin.mp4')
  const cover = join(distDir, 'douyin-cover.png')
  const srt = join(distDir, 'douyin.srt')
  for (const f of [mp4, cover, srt]) if (!existsSync(f)) throw new Error(`${id} 缺文件：${f}`)
  // 文案里的时长必须是真的那个文件，不是 timeline.json 单方声明
  const rel = writeRelease({
    ep, platform: 'douyin', outDir: distDir, timeline, cfg,
    videoPath: mp4, srtPath: srt, coverPath: cover, sceneTexts: resolveScenes(ep, 'douyin'),
  })
  const pub = ep.publish.douyin
  rows.push({
    no: byId.get(id).no, id, badge: ep.badge, title: ep.title,
    secs: timeline.totalFrames / timeline.fps,
    mb: statSync(mp4).size / 1024 / 1024,
    cap: pub.caption, pin: pub.pinned, repro: pub.repro, rel,
  })
}

rows.sort((a, b) => a.no - b.no)
const [lo, hi] = [45, 75]
const bad = rows.filter((r) => !(r.secs >= lo && r.secs <= hi))
const lines = [
  `# 抖音投稿清单 · ${rows.length} 条`,
  '',
  `合集名（16 条共用，抖音里叫"合集"，第一条发布时建）：**${COLLECTION}**`,
  '',
  '投稿顺序 = `video/series.json` 的 `no`，和 B站 那条序列一致——同一集在两个平台是同一个编号，',
  '评论区对得上，不用维护第二套映射。',
  '',
  '每条三步：① 传 `douyin.mp4` → ② 粘下面的**作品描述** → ③ 发完立刻在评论区贴**置顶评论**并长按置顶。',
  '',
  '| # | 集 | 时长 | 体积 | 视频 | 封面 |',
  '|---|---|---|---|---|---|',
  ...rows.map((r) => `| ${r.no} | ${r.badge} ${r.id} | ${r.secs.toFixed(1)}s | ${r.mb.toFixed(1)} MB | \`video/out/${r.id}/douyin.mp4\` | \`video/out/${r.id}/douyin-cover.png\` |`),
  '',
  '## 逐条文案（可直接粘贴）',
  '',
]
for (const r of rows) {
  lines.push(
    `### ${r.no}. ${r.badge} · ${r.title}`,
    '',
    `- 视频：\`${join(ROOT, 'video/out', r.id, 'douyin.mp4')}\`（${r.secs.toFixed(1)}s / ${r.mb.toFixed(1)} MB）`,
    `- 封面：\`${join(ROOT, 'video/out', r.id, 'douyin-cover.png')}\``,
    '',
    '作品描述：',
    '',
    '```text',
    r.cap,
    '```',
    '',
    '置顶评论：',
    '',
    '```text',
    r.pin,
    '```',
    '',
  )
}
lines.push(
  '## 发布节奏与红线',
  '',
  `- 时长全部落在 ${lo}–${hi}s：${bad.length ? '‼️ 越界 ' + bad.map((b) => b.id).join(', ') : `16/16 通过（最短 ${Math.min(...rows.map((r) => r.secs)).toFixed(1)}s，最长 ${Math.max(...rows.map((r) => r.secs)).toFixed(1)}s）`}`,
  '- 描述里没有任何站外字样，导流只在置顶评论（口径由用户 2026-10-14 定：描述不提，全进置顶评论）。',
  '- 置顶评论要等片子发出去之后、在自己的作品下评论再置顶；发完就置顶，别拖到第二天补。',
  '- 抖音一账号一天连发多条容易进低质池，建议 1 天 1 条、最多 2 条，先发前 3 号看数据再定后面的节奏。',
  '',
  '## 已知的一条红线：片子里的导流句没有改（需要你决定）',
  '',
  '描述改干净了，但**竖版成片本身**还在说"站内 X 全文免费"。这句既有口播也有画面，',
  '下面的数是从 `episode.json` 的 douyin 可见字段里现扫的，不是估的：',
  '',
  ...digest.map((l) => '  ' + l),
  '',
  '要么改这些 `cta` 场（旁白 + 屏上 sub/bullets）重渲受影响的那几条竖版，要么先发 3 条看是否被限流再决定。',
  '这一轮没有替你改：改旁白 = 重合成 + 重渲，是要点头的动作。',
  '',
)
writeFileSync(join(ROOT, 'video/publish/douyin-plan.generated.md'), lines.join('\n'))
console.log(`✅ 重写 ${rows.length} 份 发布-douyin.md`)
console.log(`✅ 清单 → video/publish/douyin-plan.generated.md（合集名：${COLLECTION}）`)
if (bad.length) { console.log(`‼️ ${bad.length} 条时长越界`); process.exitCode = 1 }
