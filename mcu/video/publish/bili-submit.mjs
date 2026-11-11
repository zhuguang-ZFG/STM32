// 生成 biliup-rs 投稿配置：一条 master 一份 YAML，字段全部从既有事实源里取，不手抄。
//   标题 ← video/out/<ep>/发布-bilibili.md 的「## 标题」第 1 候选
//   简介 ← 同文件「## 简介」到「## 时间轴」之间
//   标签 ← 同文件「## 标签」的 #词（逗号拼接）
//   封面/成片 ← video/out/<ep>/bilibili-cover.png / bilibili.mp4
//   顺序与前缀 ← video/series.json 的 no / series
// 用法：node video/publish/bili-submit.mjs [--tid=171] [--title-style=punchy|series] [--desc=full|short] [--dry]
import { readFileSync, writeFileSync, existsSync, statSync } from 'node:fs'
import { episodePath } from '../src/spec.mjs'

const A = Object.fromEntries(process.argv.slice(2).filter((a) => a.startsWith('--') && a.includes('=')).map((a) => {
  const [k, ...v] = a.slice(2).split('=')
  return [k, v.join('=')]
}))
const flagOnly = new Set(process.argv.slice(2).filter((a) => a.startsWith('--') && !a.includes('=')).map((a) => a.slice(2)))
const tid = A.tid || '171'
const titleStyle = A['title-style'] || 'punchy'
const descMode = A.desc || 'full'
const dry = flagOnly.has('dry')
const ROOT = 'D:/Users/mcu'

const s = JSON.parse(readFileSync('video/series.json', 'utf8'))
const sec = (md, name) => {
  const m = md.match(new RegExp(`^## ${name}\\n([\\s\\S]*?)(?=^## |$(?![\\r\\n]))`, 'm'))
  return m ? m[1].trim() : ''
}
const yq = (v) => `"${String(v).replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, '\\n')}"`
// 发布稿是 markdown，但 B站简介区实测按 white-space:pre-line 的纯文本渲染（页面 pre/code 元素数 0）：
// ``` 围栏、`行内代码`、**粗体** 都会原样露给观众。投稿前脱掉标记，只留正文。
const plain = (t) => t
  .replace(/^[ \t]*```[a-zA-Z0-9_]*[ \t]*$/gm, '')
  .replace(/\*\*([^*\n]+?)\*\*/g, '$1')
  .replace(/`([^`\n]+?)`/g, '$1')
  .replace(/ {2,}\n/g, '\n')
  .replace(/\n{3,}/g, '\n\n')
  .trim()

const rows = []
for (const e of s.episodes) {
  const dir = `video/out/${e.id}`
  const mdPath = `${dir}/发布-bilibili.md`
  const mp4 = `${dir}/bilibili.mp4`
  const cover = `${dir}/bilibili-cover.png`
  if (!existsSync(mdPath) || !existsSync(mp4)) { rows.push({ e, miss: '缺发布稿或成片' }); continue }
  const md = readFileSync(mdPath, 'utf8')
  const punchy = (sec(md, '标题').match(/^\d+\.\s*(.+)$/m) || [, ''])[1].trim()
  const no = String(e.no).padStart(2, '0')
  const title = titleStyle === 'series' ? `${s.series} ${no}｜${e.title}` : punchy || `${s.series} ${no}｜${e.title}`
  const blurb = sec(md, '简介')
  const timeline = sec(md, '时间轴')
  const desc = plain(descMode === 'short' ? blurb : `${blurb}\n\n${timeline}`.trim())
  const tags = [...sec(md, '标签').matchAll(/#([^\s#]+)/g)].map((m) => m[1])
  const tl = JSON.parse(readFileSync(`${dir}/bilibili/timeline.json`, 'utf8'))
  const missing = []
  if (!existsSync(cover)) missing.push('封面')
  if (title.length > 80) missing.push('标题超 80 字')
  // 21010 描述信息不合法：p4 那次 2135 字撞上这一条，页面不报错、点「立即投稿」毫无反应，
  // 白跑一趟填表。上限在生成端就拦下来，别留给平台教育。
  if (desc.length > 2000) missing.push(`简介超 2000 字（${desc.length}）`)
  if (!tags.length) missing.push('无标签')
  rows.push({ e, no, title, desc, tags, mp4, cover, dur: tl.duration, mb: +(statSync(mp4).size / 1048576).toFixed(1), missing })

  if (dry) continue
  const yaml = `# 自动生成：node video/publish/bili-submit.mjs；事实源 = 发布-bilibili.md + series.json + timeline.json
limit: 3
streamers:
  "${ROOT}/${mp4}":
    copyright: 1
    source: ""
    tid: ${tid}
    cover: "${ROOT}/${cover}"
    title: ${yq(title)}
    desc_format_id: 0
    desc: ${yq(desc)}
    dolby: 0
    lossless_music: 0
    dynamic: ""
    subtitle:
      open: 0
      lan: ""
    tag: ${yq(tags.join(','))}
    dtime: ~
    open_subtitle: false
`
  writeFileSync(`${dir}/bili-submit.yaml`, yaml)
}
console.log(`tid=${tid} 标题=${titleStyle} 简介=${descMode}${dry ? '（dry-run，不落盘）' : ''}`)
for (const r of rows) {
  if (r.miss) { console.log(`  ⚠️ ${r.e.id}：${r.miss}`); continue }
  console.log(`${String(r.no)} ${r.e.id.padEnd(16)} ${String(r.dur.toFixed(0)).padStart(4)}s ${String(r.mb).padStart(5)}MB 简介${String(r.desc.length).padStart(4)}字 标签${r.tags.length} ${r.missing.length ? '⚠️' + r.missing.join('/') : '✓'}`)
  console.log(`      ${r.title}`)
}
console.log(`\n合计 ${rows.filter((r) => r.mp4).length} 条 / ${rows.length} 集，落盘 ${dry ? 0 : rows.filter((r) => r.mp4).length} 份 bili-submit.yaml`)
