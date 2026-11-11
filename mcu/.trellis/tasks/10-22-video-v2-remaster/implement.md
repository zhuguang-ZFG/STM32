# 视频 v2 重制 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use `- [ ]` checkboxes for tracking. Do not mark a task complete without the verification command shown in that task actually passing.

**Goal:** 把现有 18 集视频重制为 v2（实验室仪器风画面、云扬配音、节拍驱动的离散动效与音效、全量重写旁白、四尺寸封面），全部母版验收后再逐集替换线上作品。

**Architecture:** `episode.json` 用 `formatVersion: 2` 分叉。v1 路径（DOM、stateKey、滤镜串、封面模板）逐字节不动；v2 才生成仪器层、节拍 DOM、节拍状态键、SFX 与四尺寸封面。节拍由字幕起止时间推导，只在离散状态截图，保住逐帧去重。投放侧新增 `video/publish/repost/` 编排层，删除/发布默认只读，`--go` + 逐集闸门才执行。

**Tech Stack:** Node 26 ESM、Playwright Chromium（CDP 9223 常驻浏览器）、ffmpeg-static、Python edge-tts、Trellis task 系统、Node 内置 test runner。

**Spec:** `.trellis/tasks/10-22-video-v2-remaster/design.md`
**PRD:** `.trellis/tasks/10-22-video-v2-remaster/prd.md`

## Global Constraints

- **v1 逐字节兼容**：`formatVersion` 缺省/为 1 时，`pageHtml`、`stateKey`、`audioFilter` 的旧调用必须产生与改动前完全相同的字符串；Task 0 的金样例是唯一裁判。
- **先归档再构建**：任何 `video:build` 覆盖 `video/out/` 之前，Task 0 的母版归档与校验必须完成。18 集横竖共 37 个 mp4 都要有 sha256。
- **顺序闸**：`lint → build → check`，不能反。`check` 输出里「还没有时间轴，跳过」计数必须为 0，否则是假绿。
- **时长上沿**：`est × 1.049 ≤ targetSec[1]`（bilibili 0.1955 s/字；douyin 0.1946 s/字 + 1.091 s/场）。超了裁旁白，不放宽阈值、不砍场。
- **`series.json` 登记排在 `video:build` 之后**，`masters` 写实测时长，不写占位符。
- **逐集放行**：删除与发布都是不可逆动作。授权 18 集重制 ≠ 授权删任何一集。闸门文件只能来自对话里对这一条的点头，内容是人类那句原话；脚本不许自己造，也不许用「上次同意过批量」推断。
- **`FORCE_RESUBMIT=1` / `FREE_RESUBMIT=1`** 只在用户明说之后用。
- **上屏文字只来自** `video/episodes/<ep>/episode.json` 与 `video/out/<ep>/`，脚本里不写字幕/标题字面量。
- **凭证不进 stdout、不进仓库**；cookie 文件留在仓库外。共享浏览器绝不 `browser.close()`；只 `page.close()`，小红书常驻页不关。
- **不改 c3b**；`c3b-volatile` 保持 v1，不迁移、不重制。
- **每条新审计都要有一次故意的失败样例**，并把报错原文写进 `video/research/v2-audit-failures.md`。没有失败样例的判据视为死代码。
- **用户复核门**：S5 试点、每波抽检、全量母版冻结、每次删除/发布，都必须得到对话里的明确点头。计划步骤不能代替点头。
- **提交**：本计划不自动 commit。只有用户明确要求时才提交；提交时按文件名逐个 `git add`，禁止 `git add -A`。
- **不删除任何线上作品**，除非 Task 18 的单集流程走到位，且该集删除闸门已由用户原话创建。

---

## Execution Map

| Task | 阶段 | 产出 | 出口 |
|---|---|---|---|
| 0 | Phase 0 | 旧母版/元数据/抽帧归档、v1 金样例 | 37 个母版 sha256 可校验 |
| 1 | Phase 0 | 四平台只读能力探针报告 | 用户确认 B站/小红书方案 |
| 2 | Phase 1 前 | v2 schema 校验 + 合同 | `video:lint` 全绿 |
| 3 | Phase 1 前 | 节拍模型 | 节拍单测 + 故意失败 |
| 4 | Phase 1 前 | 仪器风 DOM/CSS + v1 金样对比 | v1 fixture 逐字节相同 |
| 5 | Phase 1 前 | stage/render 节拍态 | stateKey v1 原串不变 |
| 6 | Phase 1 前 | v2 审计接入 CLI | 失败样例报错原文留档 |
| 7 | Phase 1 前 | 云扬 + 发音表 + ttsText | 三档语速实测表 |
| 8 | Phase 1 前 | SFX + 混音 + 响度断言 | -14±1 LUFS、漂移 ≤0.15s |
| 9 | Phase 1 前 | 四尺寸封面 + XHS 发布包 | 336px contact sheet |
| 10 | Phase 1 前 | 上屏数字审计 CLI | 未命中 exit 1 |
| 11 | Phase 1 | S5 端到端样板 | 用户看片 + 选封面 |
| 12 | Phase 2 | Wave A 6 集 | 双平台 check 全绿 + 抽检 |
| 13 | Phase 2 | Wave B 6 集 | 双平台 check 全绿 + 抽检 |
| 14 | Phase 2 | Wave C 5 集 | 双平台 check 全绿 + 抽检 |
| 15 | Phase 3 | 18×2 母版全量审计、`series.json`、冻结 | 用户批准进入投放 |
| 16 | Phase 4 | repost 归档/核对/删除/发布/台账 | 无闸门 exit 3 |
| 17 | Phase 4 | 小红书幂等与新旧区分 | 标题-only 回读必须失败 |
| 18 | Phase 4 | 逐集换新执行 | 每集旧/新 ID 台账齐全 |
| 19 | Phase 5 | spec/journal/最终验证 | 文档与验证输出齐全 |

---

### Task 0: 基线归档与 v1 金样例

**Files:**
- Create: `.temp/v2-baseline-20261022/`（归档、抽帧、校验和，gitignored）
- Create: `video/research/v2-baseline-20261022.md`
- Create: `video/tests/fixtures/page-v1-s5-bilibili.html`
- Create: `video/tests/fixtures/page-v1-s5-douyin.html`
- Read: `video/out/*/{bilibili,douyin}.mp4`、`video/out/*/{timeline.json,*cover.png,发布-*.md,*.srt}`、`video/series.json`

**Interfaces:**
- Consumes: 当前 `video/src/layout.mjs`、`video/src/spec.mjs`、`video/src/stage.mjs` 的 v1 输出。
- Produces: `BASE` 目录、`masters.sha256`、`masters.tsv`、旧抽帧、两份 v1 `pageHtml` fixture。后续所有兼容测试都以这两个 fixture 为准。

- [ ] **Step 1: 建归档目录并复制 37 个母版**

```bash
BASE=.temp/v2-baseline-20261022
mkdir -p "$BASE/masters" "$BASE/stills" "$BASE/out-meta"
find video/out -maxdepth 2 -type f \( -name bilibili.mp4 -o -name douyin.mp4 \) -print0 |
while IFS= read -r -d '' f; do
  ep=$(basename "$(dirname "$f")")
  plat=$(basename "$f" .mp4)
  mkdir -p "$BASE/masters/$ep"
  cp -p "$f" "$BASE/masters/$ep/$plat.mp4"
done
find "$BASE/masters" -name '*.mp4' | wc -l   # 期望 37
```

- [ ] **Step 2: 复制时间轴、封面、字幕、发布文案**

```bash
find video/out -maxdepth 3 -type f \( -name timeline.json -o -name '*-cover.png' -o -name '发布-*.md' -o -name '*.srt' \) -print0 |
xargs -0 -I{} cp --parents "{}" "$BASE/out-meta/"
cp -p video/series.json "$BASE/out-meta/series.json"
```

- [ ] **Step 3: 生成 sha256 与时长清单**

```bash
cd "$BASE/masters"
find . -type f -name '*.mp4' -print0 | sort -z | xargs -0 sha256sum > ../masters.sha256
cd - >/dev/null
: > "$BASE/masters.tsv"
for f in $(find "$BASE/masters" -name '*.mp4' | sort); do
  ep=$(basename "$(dirname "$f")"); plat=$(basename "$f" .mp4)
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
  printf '%s\t%s\t%s\t%s\n' "$ep" "$plat" "$dur" "$(stat -c %s "$f")" >> "$BASE/masters.tsv"
done
sha256sum -c "$BASE/masters.sha256" --quiet && echo "checksums OK"
```

- [ ] **Step 4: 每个母版抽 3 帧（5% / 50% / 95%）**

```bash
while IFS=$'\t' read -r ep plat dur bytes; do
  mkdir -p "$BASE/stills/$ep"
  for pct in 5 50 95; do
    t=$(awk -v d="$dur" -v p="$pct" 'BEGIN{printf "%.3f", d*p/100}')
    ffmpeg -hide_banner -loglevel error -ss "$t" -i "$BASE/masters/$ep/$plat.mp4" \
      -frames:v 1 -y "$BASE/stills/$ep/$plat-$pct.png"
  done
done < "$BASE/masters.tsv"
find "$BASE/stills" -name '*.png' | wc -l   # 期望 111
```

- [ ] **Step 5: 记录 v1 check 基线**

```bash
npm run video:check > "$BASE/check-before.log" 2>&1; echo $? > "$BASE/check-before.exit"
grep -c '🔍 排版审计通过' "$BASE/check-before.log"      # 期望 37
grep -c '还没有时间轴，跳过' "$BASE/check-before.log"   # 期望 0
```

若 `check-before.exit` 非 0 或计数不符，停止：先修好 v1 基线，再动 v2。

- [ ] **Step 6: 生成 v1 `pageHtml` 金样例**

```bash
mkdir -p video/tests/fixtures
node --input-type=module -e "
import { writeFileSync } from 'node:fs'
import { readAnim } from './docs/.vitepress/anim-decorate.mjs'
import { loadEpisode, platformConfig, resolveScenes } from './video/src/spec.mjs'
import { animMarkup, pageHtml, setAnimSourceReader } from './video/src/layout.mjs'
setAnimSourceReader(readAnim)
const ep = loadEpisode('s5-systick')
for (const p of ['bilibili','douyin']) {
  const cfg = platformConfig(ep, p)
  const scenes = resolveScenes(ep, p)
  const anims = {}
  scenes.forEach((sc,i) => { if (sc.anim) anims[p+'-'+i] = animMarkup(sc.anim, p+'-'+i) })
  const html = pageHtml({ platform:p, size:cfg.size, safe:cfg.safe, scenes, anims,
    kicker: ep.cover?.kicker || '通往单片机之路', badge: ep.badge || 'S5', sections: cfg.sections })
  writeFileSync('video/tests/fixtures/page-v1-s5-'+p+'.html', html)
}
"
```

- [ ] **Step 7: 写基线报告**

`video/research/v2-baseline-20261022.md` 必须写明：37 个母版、总字节数、37/0 的 check 计数、`masters.sha256` 路径、111 张抽帧路径、两份 fixture 的 sha256，以及一句「任何 v2 构建前先确认本归档存在且校验通过」。

- [ ] **Step 8: 验证**

```bash
sha256sum -c .temp/v2-baseline-20261022/masters.sha256 --quiet
test -s video/tests/fixtures/page-v1-s5-bilibili.html
test -s video/tests/fixtures/page-v1-s5-douyin.html
git status --short video/out   # 期望：没有 v2 构建造成的改动
```

---

### Task 1: 四平台只读能力探针（B站换源 / 抖音删除 / 知乎删除 / 小红书删除）

**Files:**
- Create: `video/publish/repost/probe-platforms.mjs`
- Create: `video/research/platform-replace-probe.md`

**Interfaces:**
- Consumes: 常驻 Chromium `http://127.0.0.1:9223` 的登录态；各平台管理页。
- Produces: `.temp/v2-probe/report.json` 与 `video/research/platform-replace-probe.md`。报告是 Task 16 删除适配器的入口契约。

- [ ] **Step 1: 写只读探针**

`probe-platforms.mjs` 只用 `connectOverCDP('http://127.0.0.1:9223')` 与 `ctx.newPage()`；结束只 `page.close()`，不 `browser.close()`。每个平台打开下列页面，等待 6 秒，扫描**可见文本**里是否出现「删除 / 更换视频 / 换源 / 重新上传」；如果菜单默认收起，只点 `更多`/`⋯` 这类展开按钮，**绝不点最终删除/确认**。

```js
const TARGETS = {
  bilibili: 'https://member.bilibili.com/platform/upload-manager/article',
  douyin: 'https://creator.douyin.com/creator-micro/content/manage',
  zhihu: 'https://www.zhihu.com/creator/manage/creation/zvideo',
  xiaohongshu: 'https://creator.xiaohongshu.com/new/note-manager',
}
```

扫描逻辑：

```js
const scan = () => page.evaluate(() => {
  const vis = (e) => { const r = e.getBoundingClientRect(); return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden' }
  const T = (e) => (e.innerText || '').replace(/\s+/g, ' ').trim()
  return [...document.querySelectorAll('button,a,[role=menuitem],li,span,div')]
    .filter((e) => vis(e) && T(e).length < 80 && /删除|更换视频|换源|重新上传/.test(T(e)))
    .map((e) => ({ tag: e.tagName, text: T(e), cls: String(e.className || '').slice(0, 80), href: e.href || '' }))
    .slice(0, 30)
})
```

对 B站额外记录：稿件编辑页 URL、是否有「更换视频/换源」入口、入口附近的网络请求名（只读 Performance 条目里含 `replace|source|upload` 的 URL）。对小红书额外记录：笔记行菜单里「编辑」链接是否带 `id=`、是否有删除项。对知乎记录已发布页与草稿页分别有没有删除。对抖音记录单条作品菜单有没有删除。

- [ ] **Step 2: 运行并落 JSON**

```bash
node video/publish/repost/probe-platforms.mjs > .temp/v2-probe/report.txt 2>&1
cat .temp/v2-probe/report.txt
```

脚本同时写 `.temp/v2-probe/report.json`，结构：

```json
{
  "at": "2026-10-22T...",
  "platforms": {
    "bilibili": { "status": "yes|no|not-logged-in", "entries": [], "evidence": "", "risk": "" },
    "douyin": {},
    "zhihu": {},
    "xiaohongshu": {}
  }
}
```

`status` 只能是 `yes` / `no` / `not-logged-in`，不允许写“可能”。

- [ ] **Step 3: 写报告并做 Phase 0 决策**

`video/research/platform-replace-probe.md` 每平台一节，必须包含：

- 有/无入口、入口的页面路径与可见文案；
- 判定证据（`report.json` 里的 `entries` 原文，不转述）；
- 风险（例如「删除会同时删评论」「换源可能重置 cid」）；
- 决议：B站有换源则优先换源还是仍删重发；小红书无网页删除则 App 手动删或该平台不换视频。

- [ ] **Step 4: 用户确认门**

把报告给用户，等待用户对 B站/小红书方案点头。未点头前不进入 Task 16 的任何删除适配器实现，也不开始 Phase 4。

- [ ] **Step 5: 验证**

```bash
test -s .temp/v2-probe/report.json
test -s video/research/platform-replace-probe.md
grep -c '"status"' .temp/v2-probe/report.json   # 4
```

---

### Task 2: v2 schema 与合同

**Files:**
- Modify: `video/src/spec.mjs`
- Test: `video/tests/spec-v2.test.mjs`
- Create: `.trellis/spec/video/v2-contract.md`
- Modify: `package.json`（加 `video:test`）

**Interfaces:**
- Consumes: `validateEpisode(ep,id)`、`resolveScenes`、`SECTION_TITLE_MAX`。
- Produces: `FORMAT_VERSIONS`、`V2_VOICES`、v2 的 `sections` 3–6 校验、`beatMap`/`emphasis`/`ttsLexicon`/`ttsText` 结构校验；`npm run video:test`。

- [ ] **Step 1: 先写失败测试**

`video/tests/spec-v2.test.mjs`：

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { validateEpisode } from '../src/spec.mjs'

const scene = (id, extra = {}) => ({
  id, kind: 'card', title: '标题', narration: '旁白一句。', bullets: ['一', '二'], ...extra,
})
const ep = (over = {}) => ({
  id: 't', title: 't', voice: 'zh-CN-YunyangNeural', formatVersion: 2, fps: 30,
  platforms: {
    bilibili: {
      scenes: [scene('a'), scene('b'), scene('c')],
      sections: [{ at: 'a', title: '一' }, { at: 'b', title: '二' }, { at: 'c', title: '三' }],
      targetSec: [1, 200],
    },
  },
  ...over,
})
const errs = (x) => validateEpisode(x, 't').errs

test('v2 需要 3–6 节', () => {
  const x = ep(); x.platforms.bilibili.sections = x.platforms.bilibili.sections.slice(0, 2)
  assert.ok(errs(x).some((e) => e.includes('3–6 节')))
})

test('v2 音色必须是云扬', () => {
  assert.ok(errs(ep({ voice: 'zh-CN-YunxiNeural' })).some((e) => e.includes('音色')))
})

test('beatMap.at 必须从 1 开始且递增', () => {
  const x = ep(); x.platforms.bilibili.scenes[0].beatMap = [
    { at: 0, reveal: 'title' }, { at: 1, reveal: 'bullets:0-1' },
  ]
  assert.ok(errs(x).some((e) => e.includes('beatMap[0]')))
})

test('reveal 形状不对要报错', () => {
  const x = ep(); x.platforms.bilibili.scenes[0].beatMap = [{ at: 1, reveal: 'line:x-y' }]
  assert.ok(errs(x).some((e) => e.includes('reveal')))
})

test('emphasis 必须在场上文本里', () => {
  const x = ep(); x.platforms.bilibili.scenes[0].emphasis = ['0xDEADBEEF']
  assert.ok(errs(x).some((e) => e.includes('emphasis')))
})

test('v1 不校验 v2 字段', () => {
  const x = ep({ formatVersion: undefined })
  x.platforms.bilibili.scenes[0].beatMap = [{ at: 0, reveal: 'nope' }]
  x.platforms.bilibili.sections = []
  assert.equal(errs(x).length, 0)
})

test('ttsLexicon 键至少 2 字符', () => {
  assert.ok(errs(ep({ ttsLexicon: { x: '叉' } })).some((e) => e.includes('ttsLexicon')))
})
```

- [ ] **Step 2: 跑测试确认失败**

```bash
npm run video:test -- video/tests/spec-v2.test.mjs
```

期望：因 `FORMAT_VERSIONS`/v2 校验尚不存在而失败（至少 3 条）。

- [ ] **Step 3: 实现 spec.mjs 增量**

```js
export const FORMAT_VERSIONS = [1, 2]
export const V2_VOICES = ['zh-CN-YunyangNeural']
const V2_SECTION_RANGE = [3, 6]
const REVEAL_RE = /^(title|sub|note|kicker|url|code:\d+-\d+|codeB:\d+-\d+|bullets:\d+-\d+|line:\d+-\d+)$/
```

```js
function lineCount(src) {
  return src ? String(src).replace(/\n$/, '').split('\n').length : 0
}
function rangeOf(spec) {
  const m = String(spec).match(/:(\d+)-(\d+)$/)
  return m ? [Number(m[1]), Number(m[2])] : null
}
function validateBeatMap(sc, at, errs) {
  if (sc.beatMap === undefined) return
  if (!Array.isArray(sc.beatMap) || !sc.beatMap.length) {
    errs.push(`${at}: beatMap 必须是非空数组`)
    return
  }
  let last = 0
  for (const [i, b] of sc.beatMap.entries()) {
    const p = `${at}.beatMap[${i}]`
    if (!Number.isInteger(b.at) || b.at < 1) errs.push(`${p}: at 必须是 ≥1 的整数（1-based 字幕序号）`)
    else if (b.at <= last) errs.push(`${p}: at=${b.at} 必须大于上一拍 ${last}`)
    else last = b.at
    if (typeof b.reveal !== 'string' || !REVEAL_RE.test(b.reveal)) {
      errs.push(`${p}: reveal="${b.reveal}" 不在允许形状内`)
      continue
    }
    const range = rangeOf(b.reveal)
    if (!range) continue
    const [a, c] = range
    if (a > c) errs.push(`${p}: ${b.reveal} 起止倒置`)
    const kind = b.reveal.split(':')[0]
    const max = kind === 'bullets' || kind === 'line' ? (kind === 'line' ? lineCount(sc.code) : sc.bullets?.length || 0)
      : lineCount(sc.codeB)
    if (c >= max) errs.push(`${p}: ${b.reveal} 越界（共 ${max} 行/条）`)
  }
}
function validateEmphasis(sc, at, errs) {
  if (sc.emphasis === undefined) return
  if (!Array.isArray(sc.emphasis)) { errs.push(`${at}: emphasis 必须是数组`); return }
  const hay = [sc.title, sc.sub, sc.note, sc.kicker, sc.code, sc.codeB, ...(sc.bullets || [])].filter(Boolean).join('\n')
  for (const e of sc.emphasis) {
    if (typeof e !== 'string' || !e.trim()) errs.push(`${at}: emphasis 里有空值`)
    else if (!hay.includes(e)) errs.push(`${at}: emphasis "${e}" 不在这一场的上屏文本里`)
  }
}
function validateLexicon(lex, errs) {
  if (lex === undefined) return
  if (!lex || typeof lex !== 'object' || Array.isArray(lex)) { errs.push('ttsLexicon 必须是对象'); return }
  for (const [k, v] of Object.entries(lex)) {
    if (k.length < 2) errs.push(`ttsLexicon["${k}"] 的键至少 2 字符`)
    if (typeof v !== 'string' || !v.trim()) errs.push(`ttsLexicon["${k}"] 的值必须是非空字符串`)
  }
}
```

在 `validateEpisode` 里：

```js
const fv = ep.formatVersion ?? 1
check(FORMAT_VERSIONS.includes(fv), `formatVersion=${ep.formatVersion} 不在 1/2`, errs)
if (fv === 2) {
  check(V2_VOICES.includes(ep.voice), `v2 音色必须是 ${V2_VOICES.join('/')}，当前 "${ep.voice}"`, errs)
  validateLexicon(ep.ttsLexicon, errs)
}
```

每个平台配置里：

```js
if (fv === 2) {
  const n = cfg.sections?.length || 0
  check(n >= V2_SECTION_RANGE[0] && n <= V2_SECTION_RANGE[1], `平台 ${name}: v2 需要 3–6 节，当前 ${n} 节`, errs)
}
```

每场里：

```js
if (fv === 2) {
  validateBeatMap(sc, at, errs)
  validateEmphasis(sc, at, errs)
  if (sc.ttsText !== undefined) check(typeof sc.ttsText === 'string' && sc.ttsText.trim(), `${at}: ttsText 必须是非空字符串`, errs)
}
```

- [ ] **Step 4: 加测试脚本**

`package.json` 增加：

```json
"video:test": "node --test video/tests"
```

- [ ] **Step 5: 写 v2 合同**

`.trellis/spec/video/v2-contract.md` 必须包含：`formatVersion` 语义、`beatMap`/`emphasis`/`ttsLexicon`/`ttsText` 字段、v2 `sections` 3–6、v1 兼容线、节拍相位（0/1/2）、状态键格式、审计命令。合同是 Task 3–8 的共同依据。

- [ ] **Step 6: 验证**

```bash
npm run video:test -- video/tests/spec-v2.test.mjs
npm run video:lint
```

期望：单测全绿；18 集 v1 lint 不变。

---

### Task 3: 节拍模型（字幕 → 离散节拍）

**Files:**
- Modify: `video/src/timeline.mjs`
- Test: `video/tests/timeline-beats.test.mjs`

**Interfaces:**
- Consumes: `buildRenderPlan` 产出的 `plan.scenes`（含 `startFrame`/`duration`/`kind`/`code`/`codeB`/`bullets`）、`plan.captions`。
- Produces: `MAX_STATIC_GAP=6`、`BEAT_FADE=0.18`、`sceneTargets`、`expandTargets`、`deriveBeats`、`beatAt`、`validateBeats`；`plan.beatStats`；`iterateFrames` 每帧带 `beat` 与 `transitionPhase`。

- [ ] **Step 1: 先写失败测试**

`video/tests/timeline-beats.test.mjs`：

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { deriveBeats, beatAt, validateBeats, sceneTargets, MAX_STATIC_GAP } from '../src/timeline.mjs'

const sc = (over = {}) => ({
  id: 'code-01', kind: 'code', title: '代码', code: Array.from({ length: 10 }, (_, i) => `line ${i}`).join('\n'),
  narration: 'x', startFrame: 0, duration: 20, ...over,
})
const caps = (times) => times.map((t, i) => ({ scene: 'code-01', start: t, end: t + 2, text: `c${i}` }))
const plan = (scenes, captions, fps = 30) => ({ fps, totalFrames: 1200, scenes, captions })

test('自动节拍覆盖所有 target，且最大静止 ≤ 6s', () => {
  const scene = { ...sc(), beats: deriveBeats(sc(), caps([0.2, 4, 8, 12, 16])) }
  const beats = scene.beats
  assert.ok(beats.length >= 4)
  const shown = new Set(beats.flatMap((b) => b.targets))
  for (const t of sceneTargets(sc())) assert.ok(shown.has(t), `${t} 未揭示`)
  let max = 0
  for (let i = 0; i < beats.length; i++) max = Math.max(max, (beats[i + 1]?.at ?? scene.duration) - beats[i].at)
  assert.ok(max <= MAX_STATIC_GAP + 1e-6, `max gap ${max}`)
  validateBeats(plan([scene], caps([0.2, 4, 8, 12, 16])))
})

test('相位：第一拍定格，后续 0/1/2 三档', () => {
  const beats = deriveBeats(sc(), caps([0.2, 4]))
  assert.equal(beatAt(beats, 0).phase, 2)
  const b = beatAt(beats, 4 + 0.01)
  assert.equal(b.phase, 0)
  assert.equal(beatAt(beats, 4 + 0.19).phase, 1)
  assert.equal(beatAt(beats, 4 + 0.37).phase, 2)
  assert.ok(beatAt(beats, 4 + 0.37).revealed.includes('title'))
})

test('beatMap 按字幕序号落点，未覆盖的 target 归最后一拍', () => {
  const s = sc({ beatMap: [{ at: 1, reveal: 'line:0-4' }, { at: 3, reveal: 'line:5-9' }] })
  const beats = deriveBeats(s, caps([0.2, 3, 6]))
  assert.equal(beats[0].at, 0)
  assert.equal(beats[1].at, 6)
  const shown = new Set(beats.flatMap((b) => b.targets))
  assert.ok(shown.has('title'))
  assert.ok(shown.has('note') === false) // 本场没有 note
})

test('不足两拍时补到两拍', () => {
  const s = sc({ kind: 'card', title: '一句', bullets: ['一'], code: undefined, duration: 4 })
  const beats = deriveBeats(s, [{ scene: 'code-01', start: 0.3, end: 2, text: 'c' }])
  assert.ok(beats.length >= 2)
})

test('静止 9s 必须报错', () => {
  const scene = { ...sc({ duration: 10 }), beats: [{ at: 0, targets: ['title'], kind: 'content', index: 0 }, { at: 9.5, targets: ['line:0'], kind: 'content', index: 1 }] }
  assert.throws(() => validateBeats(plan([scene], [])), /静止/)
})

test('永远不揭示必须报错', () => {
  const scene = { ...sc(), beats: [{ at: 0, targets: ['title'], kind: 'content', index: 0 }, { at: 2, targets: [], kind: 'content', index: 1 }] }
  assert.throws(() => validateBeats(plan([scene], [])), /永远不会揭示/)
})

test('钩子超过 15s 必须报错', () => {
  const a = { id: 'h1', kind: 'hook', title: 'h', narration: 'x', startFrame: 0, duration: 8, beats: [{ at: 0, targets: ['title'], kind: 'content', index: 0 }, { at: 4, targets: [], kind: 'pulse', index: 1 }] }
  const b = { ...a, id: 'h2', startFrame: 240, duration: 8, beats: [{ at: 0, targets: ['title'], kind: 'content', index: 0 }, { at: 4, targets: [], kind: 'pulse', index: 1 }] }
  assert.throws(() => validateBeats(plan([a, b], [])), /钩子/)
})
```

- [ ] **Step 2: 跑测试确认失败**

```bash
npm run video:test -- video/tests/timeline-beats.test.mjs
```

- [ ] **Step 3: 实现节拍模型**

在 `timeline.mjs` 顶部加常量：

```js
export const MAX_STATIC_GAP = 6
export const BEAT_FADE = 0.18
```

```js
const lineCount = (src) => (src ? String(src).replace(/\n$/, '').split('\n').length : 0)
const lineTargets = (src, prefix = 'line') => Array.from({ length: lineCount(src) }, (_, i) => `${prefix}:${i}`)

export function sceneTargets(sc) {
  const title = sc.title ? ['title'] : []
  const kicker = sc.kicker ? ['kicker'] : []
  const sub = sc.sub ? ['sub'] : []
  const note = sc.note ? ['note'] : []
  const bullets = (sc.bullets || []).map((_, i) => `bullets:${i}`)
  switch (sc.kind) {
    case 'code': return [...title, ...lineTargets(sc.code), ...lineTargets(sc.codeB, 'codeB'), ...note]
    case 'hook': return [...title, ...sub, ...lineTargets(sc.code)]
    case 'card': return [...kicker, ...title, ...bullets, ...sub]
    case 'anim': return [...title, ...bullets, ...note]
    case 'outro': return [...title, ...bullets, ...sub, 'url']
    default: return []
  }
}

export function expandTargets(sc, reveal) {
  const m = String(reveal).match(/^(line|code|codeB|bullets):(\d+)-(\d+)$/)
  if (!m) return [reveal]
  const prefix = m[1] === 'code' ? 'line' : m[1]
  const a = Number(m[2]), b = Number(m[3])
  return Array.from({ length: b - a + 1 }, (_, i) => `${prefix}:${a + i}`)
}
```

分组与推导：

```js
function groupTargets(sc, n) {
  const lead = [], body = [], tail = []
  for (const t of sceneTargets(sc)) {
    if (t === 'title' || t === 'kicker' || (sc.kind === 'hook' && t === 'sub')) lead.push(t)
    else if (t === 'sub' || t === 'url' || t === 'note') tail.push(t)
    else body.push(t)
  }
  const beats = Array.from({ length: n }, () => ({ at: 0, kind: 'content', targets: [], captionIdx: -1 }))
  beats[0].targets.push(...lead)
  const slots = Math.max(1, n - 1)
  const per = Math.ceil(body.length / slots)
  body.forEach((t, i) => beats[Math.min(n - 1, 1 + Math.floor(i / per))].targets.push(t))
  beats[n - 1].targets.push(...tail)
  return beats
}

export function deriveBeats(sc, captions) {
  const sceneStart = sc.startFrame / (sc.fps || 30)
  const starts = captions.map((c) => Math.max(0, c.start - sceneStart))
  let beats
  if (sc.beatMap?.length) {
    beats = sc.beatMap.map((b, i) => ({
      at: i === 0 ? 0 : Math.max(0, (captions[b.at - 1]?.start ?? sceneStart) - sceneStart),
      kind: 'content', targets: expandTargets(sc, b.reveal), captionIdx: b.at - 1,
    }))
    for (const [i, at] of starts.entries()) {
      if (!beats.some((b) => Math.abs(b.at - at) <= 0.05)) beats.push({ at, kind: 'caption', targets: [], captionIdx: i })
    }
  } else {
    const n = Math.max(2, starts.length)
    beats = groupTargets(sc, n).map((b, i) => ({
      ...b, at: i === 0 ? 0 : (starts[i] ?? Math.min(sc.duration, 1.2 * i)), captionIdx: i < starts.length ? i : -1,
    }))
  }
  beats.sort((a, b) => a.at - b.at)
  if (beats.length === 1) {
    const targets = beats[0].targets
    beats[0].targets = targets.slice(0, Math.max(1, Math.ceil(targets.length / 2)))
    beats.push({ at: Math.min(Math.max(0.8, sc.duration * 0.6), Math.max(0.8, sc.duration - 0.1)), kind: 'caption', targets: targets.slice(beats[0].targets.length), captionIdx: -1 })
  }
  const shown = new Set(beats.flatMap((b) => b.targets))
  const missing = sceneTargets(sc).filter((t) => !shown.has(t))
  if (missing.length) {
    const last = [...beats].reverse().find((b) => b.kind === 'content')
    if (last) last.targets.push(...missing)
  }
  const out = []
  for (const b of beats.sort((a, b) => a.at - b.at)) {
    if (out.length && Math.abs(out[out.length - 1].at - b.at) < 0.001) {
      out[out.length - 1].targets.push(...b.targets)
      continue
    }
    out.push(b)
  }
  for (let i = 0; i < out.length; i++) {
    const b = out[i]
    const next = i + 1 < out.length ? out[i + 1].at : sc.duration
    let t = b.at + MAX_STATIC_GAP
    const pulses = []
    while (t < next - 0.05) {
      pulses.push({ at: +t.toFixed(3), kind: 'pulse', targets: [], captionIdx: -1 })
      t += MAX_STATIC_GAP
    }
    if (pulses.length) out.splice(i + 1, 0, ...pulses)
  }
  out.forEach((b, i) => { b.index = i })
  return out
}
```

```js
export function beatAt(beats, rel) {
  let i = 0
  while (i + 1 < beats.length && beats[i + 1].at <= rel) i++
  const b = beats[i]
  const dt = rel - b.at
  const phase = i === 0 ? 2 : Math.min(2, Math.floor(Math.max(0, dt) / BEAT_FADE))
  return {
    index: i, at: b.at, kind: b.kind, phase,
    targets: b.targets,
    revealed: [...new Set(beats.slice(0, i + 1).flatMap((x) => x.targets))],
  }
}
```

`validateBeats`：

```js
export function validateBeats(plan) {
  const issues = []
  let hookSecs = 0, inHook = true, beats = 0, pulses = 0, maxGap = 0
  for (const sc of plan.scenes) {
    const list = sc.beats || []
    if (!list.length) { issues.push(`${sc.id}: 没有节拍`); continue }
    if (list.length < 2) issues.push(`${sc.id}: 节拍 ${list.length} < 2`)
    beats += list.length
    pulses += list.filter((b) => b.kind === 'pulse').length
    let last = -1
    for (const b of list) {
      if (!(b.at > last)) issues.push(`${sc.id}: 节拍时间不递增 ${b.at}`)
      last = b.at
    }
    let gap = 0
    for (let i = 0; i < list.length; i++) gap = Math.max(gap, (list[i + 1]?.at ?? sc.duration) - list[i].at)
    maxGap = Math.max(maxGap, gap)
    if ((sc.kind === 'code' || sc.kind === 'card') && gap > MAX_STATIC_GAP + 1e-6) {
      issues.push(`${sc.id}: 静止 ${gap.toFixed(1)}s > ${MAX_STATIC_GAP}s`)
    }
    const shown = new Set(list.flatMap((b) => b.targets))
    for (const t of sceneTargets(sc)) if (!shown.has(t)) issues.push(`${sc.id}: ${t} 永远不会揭示`)
    for (const cap of plan.captions.filter((c) => c.scene === sc.id)) {
      const at = cap.start - sc.startFrame / plan.fps
      if (!list.some((b) => Math.abs(b.at - at) <= 0.05)) issues.push(`${sc.id}: 字幕 ${at.toFixed(2)}s 没有对应节拍`)
    }
    if (inHook && sc.kind === 'hook') hookSecs += sc.duration
    else inHook = false
  }
  if (hookSecs > 15.0001) issues.push(`钩子 ${hookSecs.toFixed(1)}s > 15s`)
  if (issues.length) throw new Error(`节拍审计未通过:\n${issues.map((e) => `  - ${e}`).join('\n')}`)
  return { beats, pulses, maxGap, scenes: plan.scenes.length }
}
```

在 `buildRenderPlan` 构造完 `plan.scenes` 后：

```js
plan.formatVersion = ep.formatVersion ?? 1
if (plan.formatVersion === 2) {
  for (const sc of plan.scenes) {
    sc.fps = plan.fps
    sc.beats = deriveBeats(sc, plan.captions.filter((c) => c.scene === sc.id))
  }
  plan.beatStats = validateBeats(plan)
}
```

`iterateFrames` yield 增量：

```js
const beat = sc.beats ? beatAt(sc.beats, f / plan.fps) : null
const transitionPhase = sc.beats ? (f < 4 ? f : -1) : -1
```

把 `beat`/`transitionPhase` 放进 yield 对象。v1 的 `beat` 为 `null`。

- [ ] **Step 4: 跑测试并修到全绿**

```bash
npm run video:test -- video/tests/timeline-beats.test.mjs
```

- [ ] **Step 5: 记录故意失败原文**

新建 `video/research/v2-audit-failures.md`，先写三条：静止 9s、未揭示 target、钩子 16s 的完整报错文本（从测试运行输出复制，不手写大意）。

- [ ] **Step 6: 验证 v1 不回归**

```bash
npm run video:lint
npm run video:check -- s5-systick
```

---

### Task 4: 实验室仪器风 DOM/CSS（v2 分支）

**Files:**
- Modify: `video/src/layout.mjs`
- Test: `video/tests/layout-v1.test.mjs`
- Create: `video/tests/layout-v2.test.mjs`

**Interfaces:**
- Consumes: `pageHtml({..., formatVersion, fps})`、`sceneHtml`、`codeHtml`、`bulletsHtml`。
- Produces: v2 的 `.rig`/`.cursor`/`.readout`/`.scan`、`data-beat-target`、`data-ln`、`MCU.state(beat, transition)`、`MCU.showAll()`；v1 输出逐字节不变。

- [ ] **Step 1: 写 v1 金样对比测试（必须先绿）**

`video/tests/layout-v1.test.mjs`：

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { readAnim } from '../../docs/.vitepress/anim-decorate.mjs'
import { animMarkup, pageHtml, setAnimSourceReader } from '../src/layout.mjs'
import { loadEpisode, platformConfig, resolveScenes } from '../src/spec.mjs'

setAnimSourceReader(readAnim)

test('S5 v1 双平台 pageHtml 与金样例逐字节相同', () => {
  const ep = loadEpisode('s5-systick')
  for (const p of ['bilibili', 'douyin']) {
    const cfg = platformConfig(ep, p)
    const scenes = resolveScenes(ep, p)
    const anims = {}
    scenes.forEach((sc, i) => { if (sc.anim) anims[`${p}-${i}`] = animMarkup(sc.anim, `${p}-${i}`) })
    const html = pageHtml({ platform: p, size: cfg.size, safe: cfg.safe, scenes, anims,
      kicker: ep.cover?.kicker || '通往单片机之路', badge: ep.badge || 'S5', sections: cfg.sections })
    assert.equal(html, readFileSync(`video/tests/fixtures/page-v1-s5-${p}.html`, 'utf8'), p)
  }
})
```

运行：`npm run video:test -- video/tests/layout-v1.test.mjs`。此刻应全绿；它就是后续所有改动的护栏。

- [ ] **Step 2: 写 v2 结构测试（先失败）**

`video/tests/layout-v2.test.mjs`：

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { pageHtml } from '../src/layout.mjs'

const scenes = [{
  id: 'a', kind: 'card', title: '上电', kicker: 'BOOT', bullets: ['一', '二'], sub: '一秒',
  narration: 'x', code: 'A\nB', emphasis: ['A'],
}]

test('v2 生成仪器层、节拍属性和客户端方法', () => {
  const html = pageHtml({ platform: 'douyin', size: [1080, 1920], safe: {}, scenes, anims: {}, kicker: 'k', badge: 'T', sections: null, formatVersion: 2, fps: 30 })
  assert.match(html, /class="rig"/)
  assert.match(html, /data-beat-target="title"/)
  assert.match(html, /data-beat-target="bullets:0"/)
  assert.match(html, /data-ln="1"/)
  assert.match(html, /MCU\.state/)
  assert.match(html, /showAll/)
})

test('v1 不产生任何 v2 属性', () => {
  const html = pageHtml({ platform: 'douyin', size: [1080, 1920], safe: {}, scenes, anims: {}, kicker: 'k', badge: 'T', sections: null })
  assert.doesNotMatch(html, /data-beat-target/)
  assert.doesNotMatch(html, /class="rig"/)
})
```

- [ ] **Step 3: 实现 v2 分支**

`pageHtml` 签名加默认参数，保证 v1 调用不变：

```js
export function pageHtml({ platform, size, safe, scenes, anims, kicker, badge, sections, formatVersion = 1, fps = 30 }) {
  const v2 = formatVersion === 2
```

`sceneHtml(sc, ctx)` 增加 `v2`；`codeHtml(src, { v2 = false, prefix = 'line' } = {})`；`colHtml(..., v2, prefix)`；`bulletsHtml(items, v2)`。只有 `v2 === true` 才输出：

```html
data-beat-target="title|sub|note|kicker|url|line:N|codeB:N|bullets:N"
data-ln="N"
```

v1 的所有调用不传 `v2`，输出与 fixture 相同。

`LAB_CSS` 只通过 `${v2 ? LAB_CSS : ''}` 注入。核心片段：

```css
:root{--bg:#0b0f14;--bg2:#10161d;--anim-bg:#0e141b;--card:#121a22;--panel:#0d131a;
  --line:#273340;--ink:#dbe7f3;--sub:#9fb0c2;--muted:#6f8296;--brand:#7ee787;
  --accent:#56d4dd;--accent-deep:#a5f3b6;--warn:#f2b84b;--warn-deep:#ffd58a;
  --gold:#f2b84b;--danger:#ff5d5d;--wash-blue:rgba(86,212,221,.12);
  --wash-green:rgba(126,231,135,.12);--wash-amber:rgba(242,184,75,.12)}
body{background:#05080b}
.frame{background:radial-gradient(120% 100% at 50% 0%,#10161d 0%,#0b0f14 62%,#05080b 100%)}
.rig{position:absolute;inset:0;pointer-events:none;z-index:0}
.rig .grid{position:absolute;inset:calc(var(--u)*5);opacity:.55;
  background-image:linear-gradient(rgba(120,160,200,.06) 1px,transparent 1px),
    linear-gradient(90deg,rgba(120,160,200,.06) 1px,transparent 1px);
  background-size:calc(var(--u)*4) calc(var(--u)*4)}
.rig .corner{position:absolute;width:calc(var(--u)*3);height:calc(var(--u)*3);
  border:0 solid rgba(126,231,135,.55)}
.rig .corner.tl{left:calc(var(--sw)*4);top:calc(var(--u)*4);border-left-width:2px;border-top-width:2px}
.rig .corner.tr{right:calc(var(--sw)*4);top:calc(var(--u)*4);border-right-width:2px;border-top-width:2px}
.rig .corner.bl{left:calc(var(--sw)*4);bottom:calc(var(--u)*4);border-left-width:2px;border-bottom-width:2px}
.rig .corner.br{right:calc(var(--sw)*4);bottom:calc(var(--u)*4);border-right-width:2px;border-bottom-width:2px}
.rig .ruler{position:absolute;right:calc(var(--sw)*2.4);top:calc(var(--u)*18);bottom:calc(var(--u)*18);
  width:calc(var(--sw)*1.2);opacity:.5;
  background:repeating-linear-gradient(to bottom,rgba(126,231,135,.5) 0 1px,transparent 1px calc(var(--u)*2))}
.readout{position:absolute;left:calc(var(--sw)*6);bottom:calc(var(--u)*4.2);z-index:3;
  font-family:var(--mono);font-size:calc(var(--u)*1.35);color:var(--accent);letter-spacing:.12em}
.cursor{position:absolute;left:calc(var(--sw)*6);right:calc(var(--sw)*6);height:1px;z-index:4;
  background:linear-gradient(90deg,transparent,rgba(242,184,75,.9),transparent);opacity:0;pointer-events:none}
.cursor span{position:absolute;right:0;top:-.7em;font-family:var(--mono);font-size:calc(var(--u)*1.2);color:var(--gold)}
.scan{position:absolute;inset:0;z-index:20;pointer-events:none;opacity:0;
  background:linear-gradient(180deg,rgba(5,8,11,.92),rgba(5,8,11,.35) 45%,rgba(86,212,221,.12))}
.body{position:relative;z-index:2}
.topbar,.caps,.ticks{position:absolute;z-index:3}
pre.code .ln{position:relative}
pre.code .ln::before{content:attr(data-ln);position:absolute;left:calc(var(--sw)*-1.1);width:calc(var(--sw)*1.4);
  text-align:right;color:var(--muted);font-size:.72em}
pre.code .ln.cur{background:rgba(86,212,221,.10);box-shadow:inset calc(var(--u)*.35) 0 0 var(--accent)}
.bullets li.cur{color:var(--accent)}
.emph{font-style:normal;color:var(--gold);font-weight:700;border-bottom:1px solid rgba(242,184,75,.5)}
.emph.locked{background:rgba(242,184,75,.18);box-shadow:0 0 0 2px rgba(242,184,75,.28);border-radius:2px}
[data-beat-target]{will-change:opacity,transform}
```

竖版覆盖：

```css
.readout{left:calc(var(--sw)*8);top:calc(var(--u)*8.8);bottom:auto}
```

v2 DOM 只在 `v2` 时插入：

```html
<div class="rig" aria-hidden="true">
  <div class="grid"></div><div class="corner tl"></div><div class="corner tr"></div>
  <div class="corner bl"></div><div class="corner br"></div><div class="ruler"></div>
</div>
<div class="readout" id="readout"></div>
<div class="cursor" id="cursor"><span>CURSOR</span></div>
<div class="scan" id="scan"></div>
```

v2 客户端方法只通过 `${v2 ? v2Client : ''}` 注入，v1 一个字符都不多。方法契约：

```js
function v2Targets() { return body.querySelectorAll('[data-beat-target]') }
function v2Reset() {
  v2Targets().forEach(function (el) {
    el.style.opacity = 0; el.style.transform = 'none'; el.classList.remove('cur', 'locked')
  })
  if (scan) { scan.style.opacity = 0; scan.style.transform = 'none' }
  if (cursor) cursor.style.opacity = 0
}
function v2MarkEmph(tokens) { /* 见下 */ }
function v2State(beat, transition) {
  var phase = beat ? beat.phase : 2
  var cur = (beat && beat.targets) || []
  var shown = (beat && beat.revealed) || []
  v2Targets().forEach(function (el) {
    var t = el.getAttribute('data-beat-target')
    var isCur = cur.indexOf(t) >= 0
    var isShown = shown.indexOf(t) >= 0
    el.style.opacity = isShown ? (isCur ? [0, 0.5, 1][phase] : 1) : 0
    el.style.transform = isCur && phase === 1 ? 'translateY(6px)' : 'none'
    el.classList.toggle('cur', isCur && phase === 2)
    if (isShown && phase === 2) el.querySelectorAll('.emph').forEach(function (m) { m.classList.add('locked') })
  })
  var el = cur.length ? body.querySelector('[data-beat-target="' + cur[0] + '"]') : null
  if (cursor && el) {
    var r = el.getBoundingClientRect(), f = document.querySelector('.frame').getBoundingClientRect()
    cursor.style.top = (r.top - f.top + r.height / 2) + 'px'; cursor.style.opacity = 1
  } else if (cursor && beat && beat.kind === 'pulse') {
    var fb = document.querySelector('.frame').getBoundingClientRect()
    cursor.style.top = (fb.height * (0.16 + (beat.index % 5) * 0.15)) + 'px'; cursor.style.opacity = .85
  }
  if (scan) {
    if (transition < 0) { scan.style.opacity = 0; scan.style.transform = 'none' }
    else { scan.style.opacity = [1, .72, .38, 0][transition] ?? 0; scan.style.transform = 'translateY(' + ((transition + 1) * 25) + '%)' }
  }
}
function v2ShowAll() {
  v2Targets().forEach(function (el) {
    el.style.opacity = 1; el.style.transform = 'none'; el.classList.remove('cur')
    el.querySelectorAll('.emph').forEach(function (m) { m.classList.add('locked') })
  })
  if (scan) scan.style.opacity = 0
  if (cursor) cursor.style.opacity = 0
}
function v2Readout(i, kind) {
  var el = document.getElementById('readout')
  if (!el) return
  var pad = function (n) { return String(n).padStart(2, '0') }
  el.textContent = 'CH1 · ' + String(kind || '').toUpperCase() + ' · SCENE ' + pad(i + 1) + '/' + pad(window.PAYLOAD.length) + ' · ' + FPS + 'fps'
}
```

`v2MarkEmph` 在 `setup(i)` 里对 `item.emph` 生效一次：TreeWalker 找文本节点，最长 token 优先，包 `<span class="emph">`。包完再 `fitAll`。它只改行内标记，不改变布局。

`MCU.setup(i)` 里 v2 追加：

```js
v2Reset(); if (item.emph) v2MarkEmph(item.emph); v2Readout(i, item.kind)
```

返回值 v2 追加 `state: v2State, showAll: v2ShowAll`。

- [ ] **Step 4: 跑 v1 金样与 v2 结构测试**

```bash
npm run video:test -- video/tests/layout-v1.test.mjs video/tests/layout-v2.test.mjs
```

- [ ] **Step 5: 跑 v1 全量审计**

```bash
npm run video:lint
npm run video:check
```

期望：37 通过、0 跳过；与 `check-before.log` 的逐场读数一致（只允许通过行文案因后续新增判据而变化，Task 4 本身不允许改任何读数）。

---

### Task 5: stage/render 接入节拍与转场

**Files:**
- Modify: `video/src/stage.mjs`
- Modify: `video/src/render.mjs`
- Test: `video/tests/render-state.test.mjs`
- Test: `video/tests/stage-v2.test.mjs`

**Interfaces:**
- Consumes: `openStage(..., formatVersion, fps)`、`frame.beat`/`frame.transitionPhase`。
- Produces: `capture(..., beat, transitionPhase)`、`stateKey(..., beat, transitionPhase)`、`transitionPhase(f)`；v1 stateKey 原串不变。

- [ ] **Step 1: 先写 stateKey 测试**

`video/tests/render-state.test.mjs`：

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { stateKey, transitionPhase } from '../src/render.mjs'

const frame = { scene: { index: 7 }, smilTime: 1.2, captionIdx: 3 }

test('v1 stateKey 原串不变', () => {
  assert.equal(stateKey(frame, 0.5, 0.75), '7|1.2000|3|0.5|0.75')
})

test('v2 追加拍号/相位/转场', () => {
  assert.equal(stateKey(frame, 1, 1, { index: 2, phase: 1 }, -1), '7|1.2000|3|1|1|b2:1|t-')
  assert.equal(stateKey(frame, 1, 1, { index: 2, phase: 1 }, 3), '7|1.2000|3|1|1|b2:1|t3')
})

test('转场只在前 4 帧', () => {
  assert.equal(transitionPhase(0), 0)
  assert.equal(transitionPhase(3), 3)
  assert.equal(transitionPhase(4), -1)
})
```

- [ ] **Step 2: 实现 stateKey / transitionPhase**

```js
export function transitionPhase(frameInScene) {
  return frameInScene < 4 ? frameInScene : -1
}

export function stateKey(frame, opacity, reveal, beat = null, transition = -1) {
  const smil = frame.smilTime === null ? '-' : (Math.round(frame.smilTime * QUANT) / QUANT).toFixed(4)
  const op = Math.round(opacity * 100) / 100
  const base = `${frame.scene.index}|${smil}|${frame.captionIdx}|${op}|${reveal}`
  if (!beat && transition < 0) return base
  const b = beat ? `${beat.index}:${beat.phase}` : '-'
  return `${base}|b${b}|t${transition < 0 ? '-' : transition}`
}
```

- [ ] **Step 3: 改 stage.capture**

`openStage` 签名加 `formatVersion = 1, fps = 30`，传给 `pageHtml`。`capture` 加两个可选参数：

```js
async capture(index, smilTime, caption, opacity, reveal, beat = null, transition = -1) {
  await page.evaluate((a) => {
    window.MCU.frame(a.index, a.smilTime, a.caption, a.opacity, a.reveal)
    if (window.MCU.state) window.MCU.state(a.beat, a.transition)
  }, { index, smilTime, caption: caption ?? null, opacity: opacity ?? 1, reveal: reveal ?? 1, beat, transition })
  return page.screenshot({ type: 'png' })
}
```

v1 页面没有 `MCU.state`，这个 `if` 不改变 v1 截图。

- [ ] **Step 4: 改 renderFrames / captureStills**

`renderFrames` 循环：

```js
const beat = frame.beat || null
const tp = frame.transitionPhase ?? -1
const key = stateKey(frame, opacity, reveal, beat, tp)
if (key !== lastKey || !lastBuf) {
  lastBuf = await stage.capture(frame.scene.index, frame.smilTime, frame.caption?.text ?? null, opacity, reveal, beat, tp)
  ...
}
```

`captureStills` 同样传 `frame.beat` 与 `frame.transitionPhase`。

- [ ] **Step 5: 写 v2 截图集成测试**

`video/tests/stage-v2.test.mjs`：用 Playwright 启动浏览器、开一个最小 v2 hook 场，分别截 `phase 0` 与 `phase 2`，断言差异像素数 > 64。

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { openBrowser, openStage } from '../src/stage.mjs'
import { decodeRgba, diffRgba } from '../src/util.mjs'

test('v2 节拍相位真的改变画面', async () => {
  const browser = await openBrowser()
  try {
    const scenes = [{ id: 'h', kind: 'hook', title: '上电', sub: '一秒', code: 'A\nB', narration: 'x' }]
    const stage = await openStage(browser, { platform: 'probe', size: [1080, 1920], safe: {}, scenes, kicker: 'x', badge: 'T', sections: null, formatVersion: 2, fps: 30 })
    const base = { index: 1, at: 0.5, kind: 'content', targets: ['sub'], revealed: ['title', 'sub'] }
    const a = await stage.capture(0, null, null, 1, 1, { ...base, phase: 0 }, -1)
    const b = await stage.capture(0, null, null, 1, 1, { ...base, phase: 2 }, -1)
    await stage.close()
    const d = diffRgba(await decodeRgba(a), await decodeRgba(b))
    assert.ok(d.strong > 64, `strong=${d.strong}`)
  } finally {
    await browser.close()
  }
})
```

> 这是测试自己的浏览器，允许 `browser.close()`；投放脚本仍禁止。

- [ ] **Step 6: 验证**

```bash
npm run video:test -- video/tests/render-state.test.mjs video/tests/stage-v2.test.mjs
npm run video:check
```

---

### Task 6: v2 审计接入 CLI

**Files:**
- Modify: `video/src/cli.mjs`
- Modify: `video/src/stage.mjs`（如需把 `formatVersion` 传入 `openStage` 的所有调用）
- Test: `video/tests/audit-v2.test.mjs`

**Interfaces:**
- Consumes: `plan.beatStats`、`MCU.showAll()`。
- Produces: `auditLayout` 的 v2 分支（showAll 后量几何、检查未揭示）、`cmdBuild`/`cmdCheck` 传 `formatVersion` 与节拍；v1 输出不变。

- [ ] **Step 1: 给 auditLayout 加 showAll 与 v2 检查**

在 `stage.page.evaluate` 开头：

```js
window.MCU.setup(index)
if (window.MCU.showAll) window.MCU.showAll()
window.MCU.caption(capText || null, 1)
```

在返回对象里加：

```js
const hidden = []
for (const el of document.querySelectorAll('[data-beat-target]')) {
  const cs = getComputedStyle(el)
  if (parseFloat(cs.opacity) < 0.99) hidden.push(`${el.tagName.toLowerCase()} "${el.getAttribute('data-beat-target')}" opacity=${cs.opacity}`)
}
```

Node 侧：

```js
for (const h of r.hidden) issues.push(`${sc.id}: 审计时仍不可见 ${h}`)
if (plan.beatStats) log(`  🎛️ 节拍审计：${plan.beatStats.beats} 拍（含脉冲 ${plan.beatStats.pulses}），最长静止 ${plan.beatStats.maxGap.toFixed(1)}s`)
```

**不要**改 v1 的通过行文案；v2 信息单独一行。这样 `video:check` 的 v1 输出与基线 diff 仍为空。

- [ ] **Step 2: build/check 传 v2 参数**

`buildOne` 与 `cmdCheck` 的 `openStage` 调用加：

```js
formatVersion: ep.formatVersion ?? 1,
fps: cfg.fps,
```

`buildOne` 里 `const v2 = (ep.formatVersion ?? 1) === 2`，为 Task 8 的 SFX 与 Task 9 的封面分支预留。

- [ ] **Step 3: 写审计失败测试**

`video/tests/audit-v2.test.mjs` 只测纯函数可达的部分：用 Task 3 的坏 plan 断言 `validateBeats` 抛错；用 `video:check` 跑一个临时 v2 夹具（不写进 `episodes/`）验证 `未揭示` 分支。临时夹具放在 `.temp/v2-check-fixture/`，通过 `openStage` 直接构造，不进入全量 lint。

- [ ] **Step 4: 记录失败样例**

在 `video/research/v2-audit-failures.md` 追加：

- 把一场的节拍改成 9 秒间隔 → `静止 9.0s > 6s`；
- 删掉一个 `data-beat-target` 的末拍 → `审计时仍不可见 ...`；
- 钩子两场共 16 秒 → `钩子 16.0s > 15s`。

- [ ] **Step 5: 验证**

```bash
npm run video:test
npm run video:check
```

期望：v1 37 通过、0 跳过；v2 单测全绿。

---

### Task 7: 云扬配音、发音替代表与 ttsText

**Files:**
- Modify: `video/src/tts.mjs`
- Modify: `video/src/audio/assemble.py`
- Test: `video/tests/tts-lexicon.test.mjs`

**Interfaces:**
- Consumes: `narrationJobs(ep, platform)`、`buildAudio` manifest、`assemble.py`。
- Produces: `applyLexicon(text, lexicon)`；manifest 每场带 `ttsText`；合成用 `ttsText`、字幕/时间轴用 `narration`；缓存键含 `ttsText`。

- [ ] **Step 1: 先写测试**

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { applyLexicon, narrationJobs } from '../src/tts.mjs'

test('发音表最长键优先', () => {
  const lex = { '0x': '零 x ', '0x40021418': '零 x 四零零二一四一八' }
  assert.equal(applyLexicon('地址 0x40021418', lex), '地址 零 x 四零零二一四一八')
})

test('scene.ttsText 覆盖 narration，但 narration 原样保留', () => {
  const ep = { voice: 'zh-CN-YunyangNeural', platforms: { bilibili: { scenes: [
    { id: 'a', kind: 'card', title: 't', narration: '写 0x40021418', ttsText: '写 零 x 四零零二一四一八' },
  ] } } }
  const [job] = narrationJobs(ep, 'bilibili')
  assert.equal(job.narration, '写 0x40021418')
  assert.equal(job.ttsText, '写 零 x 四零零二一四一八')
})
```

- [ ] **Step 2: 实现 tts.mjs**

```js
export function applyLexicon(text, lexicon) {
  if (!lexicon) return text
  let out = String(text)
  for (const k of Object.keys(lexicon).sort((a, b) => b.length - a.length)) {
    out = out.split(k).join(lexicon[k])
  }
  return out
}
```

`narrationJobs` 每场返回：

```js
{
  id: sc.id,
  narration: sc.narration.trim(),
  ttsText: applyLexicon((sc.ttsText || sc.narration).trim(), ep.ttsLexicon),
  head: sc.head ?? 0.22,
  tail: sc.tail ?? TAIL[sc.kind] ?? 0.45,
  minSec: sc.minSec ?? MIN_SEC[sc.kind] ?? 2,
}
```

manifest 的 `scenes` 自动带上 `ttsText`，`audioStamp` 已哈希 `scenes`，所以改发音表会触发重合成。

- [ ] **Step 3: 改 assemble.py**

加：

```python
def spoken_text(sc):
    return (sc.get("ttsText") or sc["narration"]).strip()
```

替换：

```python
if not sc["narration"].strip():
```
→
```python
if not sc["narration"].strip() or not spoken_text(sc):
```

缓存键：

```python
sha1_of(f"{manifest['voice']}|{manifest['rate']}|{spoken_text(sc)}")
```

`synth_all.one` 与 `synth` 的文本参数用 `spoken_text(scene)`；`plausible` 用 `spoken_text(sc)`；重合成错误里的字数也用 `len(spoken_text(...))`。`split_captions(sc["narration"])` 保持不变。

- [ ] **Step 4: 云扬语速探针**

写 `.temp/v2-voice-probe.mjs`（一次性，gitignored），对同一句 40–60 字文本跑 `+0% / +2% / +4%`：

```bash
python -m edge_tts --voice zh-CN-YunyangNeural --rate=+2% --text "……" --write-media .temp/voice/+2.mp3
ffprobe -v error -show_entries format=duration -of csv=p=0 .temp/voice/+2.mp3
```

记录三档的秒数与字/秒；把三份音频路径给用户抽听。把结果写进 Task 11 的 `s5-pilot-report.md`。最终 `rate` 由用户听感 + 实测字/秒定，脚本不替用户选。

- [ ] **Step 5: 初始发音表**

在 S5 的 `episode.json` 加 `ttsLexicon`（Task 11 落地），至少覆盖：`0x…`（按位读）、`offsetof`、`BSRR`、`PendSV`、`SysTick`、`GPIOF`、`MHz`、`ms`、`us`、`LR`、`PC`、`SP`。字幕仍用原文，只有 TTS 替换。

- [ ] **Step 6: 验证**

```bash
npm run video:test -- video/tests/tts-lexicon.test.mjs
npm run video:lint
```

---

### Task 8: 程序化 SFX、BGM 与混音断言

**Files:**
- Create: `video/src/audio/sfx.mjs`
- Modify: `video/src/mux.mjs`
- Modify: `video/src/cli.mjs`（buildOne 生成 SFX）
- Test: `video/tests/sfx.test.mjs`
- Test: `video/tests/mux-filter.test.mjs`
- Create: `video/assets/lab-ambient.m4a`（仅在用户试听后选它时提交）

**Interfaces:**
- Consumes: `plan.scenes[].beats`、`timeline.duration`。
- Produces: `buildSfxEvents(plan)`、`renderSfx(events,{duration,outPath})`、`mux({..., sfxPath, assertLoudness})`；v1 滤镜串不变。

- [ ] **Step 1: 先写 SFX 测试**

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { buildSfxEvents, renderSfxBuffer } from '../src/audio/sfx.mjs'

const plan = { fps: 30, scenes: [
  { id: 'a', kind: 'hook', startFrame: 0, duration: 5, beats: [
    { index: 0, at: 0, kind: 'content', targets: ['title'] },
    { index: 1, at: 2, kind: 'pulse', targets: [] },
  ] },
] }

test('每个节拍恰好一条 SFX，时间落在场内', () => {
  const ev = buildSfxEvents(plan)
  assert.equal(ev.length, 2)
  assert.deepEqual(ev.map((e) => e.kind), ['sting', 'relay'])
  assert.ok(ev.every((e) => e.t >= 0 && e.t <= 5))
})

test('合成确定性 + WAV 参数', () => {
  const a = renderSfxBuffer([{ t: 0, kind: 'click' }], { duration: 0.5, sampleRate: 44100, channels: 2 })
  const b = renderSfxBuffer([{ t: 0, kind: 'click' }], { duration: 0.5, sampleRate: 44100, channels: 2 })
  assert.deepEqual(a.pcm, b.pcm)
  assert.equal(a.sampleRate, 44100)
  assert.equal(a.channels, 2)
  assert.equal(a.pcm.length, 22050 * 2)
})
```

- [ ] **Step 2: 实现 sfx.mjs**

```js
const RATE = 44100
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6D2B79F5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
function tone(kind, n, sr, rnd) {
  const out = new Float32Array(n)
  let phase = 0
  for (let i = 0; i < n; i++) {
    const t = i / sr
    if (kind === 'click') {
      out[i] = Math.sin(2 * Math.PI * 1000 * t) * Math.exp(-t / 0.02) * 0.7 + (rnd() * 2 - 1) * Math.exp(-t / 0.004) * 0.25
    } else if (kind === 'whoosh') {
      const f = 400 + 1600 * (i / n)
      phase += (2 * Math.PI * f) / sr
      out[i] = (Math.sin(phase) * 0.35 + (rnd() * 2 - 1) * 0.15) * Math.sin((Math.PI * i) / n)
    } else if (kind === 'relay') {
      out[i] = Math.sign(Math.sin(2 * Math.PI * 180 * t)) * 0.35 * Math.exp(-t / 0.01) + (rnd() * 2 - 1) * 0.1 * Math.exp(-t / 0.01)
    } else {
      const a = Math.min(1, i / (n * 0.02))
      out[i] = (Math.sin(2 * Math.PI * 660 * t) * 0.5 + Math.sin(2 * Math.PI * 990 * t) * 0.3) * Math.exp(-t / 0.35) * a
    }
  }
  return out
}
const LEN = { click: 0.08, whoosh: 0.18, relay: 0.03, sting: 1.2 }
const GAIN = { click: 0.35, whoosh: 0.25, relay: 0.3, sting: 0.4 }

export function buildSfxEvents(plan) {
  const out = []
  for (const sc of plan.scenes) {
    const start = sc.startFrame / plan.fps
    for (const b of sc.beats || []) {
      const kind = b.kind === 'pulse' ? 'relay'
        : sc.kind === 'anim' ? 'whoosh'
        : sc.kind === 'code' || sc.kind === 'card' ? 'click'
        : b.index === 0 ? 'sting' : 'whoosh'
      out.push({ t: +(start + b.at).toFixed(3), kind, scene: sc.id, beat: b.index })
    }
  }
  return out.sort((a, b) => a.t - b.t)
}

export function renderSfxBuffer(events, { duration, sampleRate = RATE, channels = 2 }) {
  const frames = Math.round(duration * sampleRate)
  const pcm = new Float32Array(frames * channels)
  const rnd = mulberry32(0x5f3759df)
  for (const ev of events) {
    const n = Math.min(Math.round((LEN[ev.kind] || 0.1) * sampleRate), frames - Math.round(ev.t * sampleRate))
    if (n <= 0) continue
    const sig = tone(ev.kind, n, sampleRate, rnd)
    const at = Math.round(ev.t * sampleRate)
    for (let i = 0; i < n; i++) {
      const v = sig[i] * (GAIN[ev.kind] || 0.3)
      for (let c = 0; c < channels; c++) pcm[(at + i) * channels + c] += v
    }
  }
  for (let i = 0; i < pcm.length; i++) pcm[i] = Math.max(-1, Math.min(1, pcm[i]))
  return { pcm, sampleRate, channels }
}

export function wavFromBuffer({ pcm, sampleRate, channels }) {
  const data = Buffer.alloc(44 + pcm.length * 2)
  data.write('RIFF', 0); data.writeUInt32LE(36 + pcm.length * 2, 4); data.write('WAVE', 8)
  data.write('fmt ', 12); data.writeUInt32LE(16, 16); data.writeUInt16LE(1, 20); data.writeUInt16LE(channels, 22)
  data.writeUInt32LE(sampleRate, 24); data.writeUInt32LE(sampleRate * channels * 2, 28)
  data.writeUInt16LE(channels * 2, 32); data.writeUInt16LE(16, 34)
  data.write('data', 36); data.writeUInt32LE(pcm.length * 2, 40)
  for (let i = 0; i < pcm.length; i++) data.writeInt16LE(Math.round(pcm[i] * 32767), 44 + i * 2)
  return data
}

export function renderSfx(events, opts) {
  const wav = wavFromBuffer(renderSfxBuffer(events, opts))
  return { write: (p) => require('node:fs').writeFileSync(p, wav), wav }
}
```

> `renderSfx` 里的 `require` 改为文件顶部 `import { writeFileSync } from 'node:fs'`；计划执行时按 ESM 写。

- [ ] **Step 3: 改 mux.mjs（v1 滤镜串逐字不变）**

`audioFilter` 增加 `sfx = false` 参数；`sfx === false` 时每个分支的返回字符串与现在完全相同。`sfx === true` 时：

```js
const head = duck
  ? [
      '[1:a]aresample=44100,asplit=2[narr][narrSC]',
      '[2:a]aresample=44100,volume=-16dB[bg]',
      '[3:a]aresample=44100,volume=-24dB[sfx]',
      '[bg][narrSC]sidechaincompress=threshold=0.03:ratio=6:attack=25:release=350[ducked]',
      '[narr][ducked][sfx]amix=inputs=3:duration=first:dropout_transition=0:normalize=0[mix]',
    ]
  : [
      '[1:a]aresample=44100[narr]',
      '[2:a]aresample=44100,volume=-16dB[bg]',
      '[3:a]aresample=44100,volume=-24dB[sfx]',
      '[narr][bg][sfx]amix=inputs=3:duration=first:dropout_transition=0:normalize=0[mix]',
    ]
```

无 BGM 但有 SFX 的分支也要写全；`mux` 参数加 `sfxPath = null`、`assertLoudness = false`，按顺序 `-i video -i narration [-i bgm] [-i sfx]`。v1 调用不传新参数，输出不变。

- [ ] **Step 4: 响度断言**

```js
import { execFile } from 'node:child_process'
import { promisify } from 'node:util'
const execFileP = promisify(execFile)

export async function probeLoudness(file) {
  const r = await execFileP(FFMPEG, ['-hide_banner', '-i', file, '-af', 'ebur128=peak=true', '-f', 'null', '-']).catch((e) => ({ stderr: e.stderr }))
  const tail = String(r.stderr || '').split('Summary:').pop()
  const m = tail.match(/I:\s*(-?\d+(?:\.\d+)?)\s*LUFS/)
  if (!m) throw new Error(`读不到响度：${file}`)
  return Number(m[1])
}
```

`mux` 末尾：始终 `log` 响度；仅当 `assertLoudness` 时断言 `Math.abs(lufs + 14) <= 1`。v1 保持不抛。

- [ ] **Step 5: buildOne 接入**

```js
const v2 = (ep.formatVersion ?? 1) === 2
let sfxPath = null
if (v2) {
  sfxPath = join(workDir, 'sfx.wav')
  const events = buildSfxEvents(plan)
  writeFileSync(sfxPath, renderSfxBufferToWav(events, { duration: timeline.duration }))
  if (events.length !== plan.beatStats.beats) throw new Error(`SFX 事件 ${events.length} ≠ 节拍 ${plan.beatStats.beats}`)
}
await mux({ ..., sfxPath, assertLoudness: v2, bgm: flags['no-bgm'] ? null : (v2 ? LAB_BGM_PATH : BGM_PATH) })
```

- [ ] **Step 6: BGM 候选（A/B 用）**

```bash
ffmpeg -hide_banner -loglevel error -y \
  -f lavfi -i "sine=frequency=55:sample_rate=44100:duration=60" \
  -f lavfi -i "sine=frequency=110:sample_rate=44100:duration=60" \
  -filter_complex "[0:a]volume=0.18[a];[1:a]tremolo=f=0.08:d=0.7,volume=0.06[b];[a][b]amix=inputs=2,lowpass=f=220,afade=t=in:d=2,afade=t=out:st=58:d=2" \
  -c:a aac -b:a 128k video/assets/lab-ambient.m4a
```

在 S5 试点分别用 `ambient-pad.m4a` 与 `lab-ambient.m4a` 出一版，给用户抽听。用户选旧的就删掉候选、`LAB_BGM_PATH` 指回旧文件；选新的才提交该资产。

- [ ] **Step 7: 滤镜串回归测试**

`video/tests/mux-filter.test.mjs` 断言 `audioFilter({bgm:true,duck:true})` 等于当前源码里的旧串（把旧串硬编码进测试），以及 `sfx:true` 时含 `[3:a]`、`volume=-24dB`、`amix=inputs=3`。

- [ ] **Step 8: 验证**

```bash
npm run video:test -- video/tests/sfx.test.mjs video/tests/mux-filter.test.mjs
npm run video:check
```

---

### Task 9: 四尺寸封面、contact sheet、小红书发布包

**Files:**
- Modify: `video/src/package.mjs`
- Modify: `video/src/cli.mjs`（`buildAllCovers`、`pack` 命令）
- Modify: `package.json`（`video:pack`）
- Test: `video/tests/package-covers.test.mjs`
- Test: `video/tests/xhs-release.test.mjs`

**Interfaces:**
- Consumes: `ep.cover`、`ep.formatVersion`、`buildCover`、`fitCover`。
- Produces: `COVER_SIZES.xiaohongshu=[1440,1080]`、`coverV2Html`、`buildAllCovers`、`buildContactSheet`、`writeRelease` 的 xiaohongshu 分支、`video:pack`。

- [ ] **Step 1: 先写发布包限制测试**

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, existsSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { writeRelease } from '../src/package.mjs'

const base = (over = {}) => ({
  id: 't', title: 't', voice: 'zh-CN-YunyangNeural', formatVersion: 2,
  platforms: { douyin: { targetSec: [45, 75] } },
  cover: { line1: '一', line2: '二' },
  publish: { xiaohongshu: { title: '标题', body: '正文', repro: 'sh code/x/probe.sh', collection: '合集', pinned: '复现 sh code/x/probe.sh' } },
  ...over,
})
const cfg = { size: [1080, 1920], fps: 30 }
const tl = { fps: 30, totalFrames: 1800, captions: [], sceneTexts: [] }

test('小红书标题 ≤20 字', () => {
  const ep = base(); ep.publish.xiaohongshu.title = '一'.repeat(21)
  assert.throws(() => writeRelease({ ep, platform: 'xiaohongshu', outDir: mkdtempSync(join(tmpdir(), 'xhs-')), timeline: tl, cfg, videoPath: 'v', srtPath: 's', coverPath: 'c', sceneTexts: [] }), /20/)
})

test('小红书正文出现站外地址要拒绝', () => {
  const ep = base(); ep.publish.xiaohongshu.body = '见 https://example.com'
  assert.throws(() => writeRelease({ ep, platform: 'xiaohongshu', outDir: mkdtempSync(join(tmpdir(), 'xhs-')), timeline: tl, cfg, videoPath: 'v', srtPath: 's', coverPath: 'c', sceneTexts: [] }), /站外/)
})

test('小红书缺合集要拒绝', () => {
  const ep = base(); delete ep.publish.xiaohongshu.collection
  assert.throws(() => writeRelease({ ep, platform: 'xiaohongshu', outDir: mkdtempSync(join(tmpdir(), 'xhs-')), timeline: tl, cfg, videoPath: 'v', srtPath: 's', coverPath: 'c', sceneTexts: [] }), /合集/)
})
```

- [ ] **Step 2: 四尺寸与 v2 封面模板**

```js
export const COVER_SIZES = {
  bilibili: [1920, 1200],
  douyin: [1080, 1440],
  zhihu: [1920, 1080],
  xiaohongshu: [1440, 1080],
}
```

`coverV2Html({ kicker, line1, line2, tag, proof, num, numNote, badge, vs, size, variant })` 必须复用 `fitCover` 认的类名：`.pad`、`.head`、`.mid`、`pre.code > .ln`、`.vslab`、`.num`、`.numnote`、`.foot`。结构：

```html
<div class="pad v2">
  <div class="top"><span>CH1 · <b>${badge}</b></span><span>${kicker}</span></div>
  <div class="head" data-want="${(u * 8.8).toFixed(2)}">${headline(line1)}<br>${headline(line2)}</div>
  <div class="mid">
    ${variant === 'panel' ? '' : vsHtml}
    <pre class="code">${proof.split('\n').map((l) => `<span class="ln">${esc(l)}</span>`).join('')}</pre>
  </div>
  <div class="bottom">
    <div class="num" data-want="${(u * 10).toFixed(2)}">${esc(num)}</div>
    <div class="numnote" data-want="${(u * 1.8).toFixed(2)}">${esc(numNote)}</div>
  </div>
  <div class="foot"><span class="chip">${esc(tag || '本机实跑')}</span><span>${esc(siteNote(size))}</span></div>
</div>
```

样式要点：石墨底、细网格、四角框、`pre.code` 红左边、`.num` 外圈红色游标（`::before` 椭圆，不改变布局）、`vslab` 顶部 `EXPECTED`/`MEASURED`。`variant === 'vs'` 与 `'panel'` 都保留 `.head`/`.mid`/`.num`，保证 `fitCover` 两条路径都量得到。

`buildCover` 在 `formatVersion === 2` 时用 `coverV2Html`，否则用 `coverHtml`。v1 封面逐字节不变。

- [ ] **Step 3: buildAllCovers + contact sheet**

```js
export async function buildAllCovers(browser, ep, distDir, { variant } = {}) {
  const jobs = [
    ['bilibili', join(distDir, 'bilibili-cover.png')],
    ['douyin', join(distDir, 'douyin-cover.png')],
    ['zhihu', join(distDir, 'zhihu-cover.png')],
    ['xiaohongshu', join(distDir, 'xiaohongshu-cover.png')],
  ]
  for (const [p, out] of jobs) await buildCover(browser, ep, p, out, { variant })
  copyFileSync(join(distDir, 'xiaohongshu-cover.png'), join(distDir, 'douyin-cover-1440x1080.png'))
  await buildContactSheet(browser, jobs.map(([p, out]) => ({ p, out })), join(distDir, 'cover-contact-336.png'))
}
```

`buildContactSheet` 用 Playwright 打开一个 1440×460 页面，四列，每列图片宽 336px，带平台名与尺寸标签，截图落盘。它是人检产物，不是自动判据；336px 读不清就回改封面文案。

- [ ] **Step 4: xiaohongshu 发布包**

`writeRelease` 增加分支：

```js
if (platform === 'xiaohongshu') {
  const pub = ep.publish?.xiaohongshu || {}
  const die = (m) => { throw new Error(`发布文案 ${ep.id}/xiaohongshu：${m}`) }
  if (!pub.title?.trim()) die('缺 publish.xiaohongshu.title')
  if (!pub.body?.trim()) die('缺 publish.xiaohongshu.body')
  if ([...pub.title].length > 20) die(`标题 ${[...pub.title].length} 字 > 20`)
  if (pub.body.length > 1000) die(`正文 ${pub.body.length} 字 > 1000`)
  if (/(https?:\/\/|github|www\.)/i.test(`${pub.title}\n${pub.body}`)) die('标题/正文出现站外地址')
  if (!pub.collection?.trim()) die('缺 collection：小红书必须在发布前选合集')
  if (!pub.repro?.trim()) die('缺 repro（复现命令）')
  if (!pub.pinned?.includes(pub.repro.split(' ').pop())) die('置顶评论没写复现脚本')
  // 写 标题/正文/话题/置顶/封面/合集 六段
}
```

发布包写明：封面是 `xiaohongshu-cover.png`（1440×1080，4:3），话题必须逐条接弹层，正文不出现站外地址，合集在发布前选好。

- [ ] **Step 5: `pack` 命令**

`cli.mjs` 增加 `pack <id…>`：按平台映射复用母版：

```js
const MAP = {
  bilibili: { base: 'bilibili', video: 'bilibili.mp4', cover: 'bilibili-cover.png', srt: 'bilibili.srt' },
  douyin: { base: 'douyin', video: 'douyin.mp4', cover: 'douyin-cover.png', srt: 'douyin.srt' },
  zhihu: { base: 'bilibili', video: 'bilibili.mp4', cover: 'zhihu-cover.png', srt: 'bilibili.srt' },
  xiaohongshu: { base: 'douyin', video: 'douyin.mp4', cover: 'xiaohongshu-cover.png', srt: 'douyin.srt' },
}
```

对 `Object.keys(ep.publish)` 逐个 `writeRelease`。`video:pack` 脚本加入 `package.json`。

- [ ] **Step 6: buildOne 的封面分工**

v2 在 `cmdBuild` 每集平台循环前调一次 `buildAllCovers`；`buildOne` 里 v2 跳过自己的 `buildCover`，只断言四张封面存在。v1 保持现有逻辑。

- [ ] **Step 7: 故意失败样例**

跑一次 42 字封面的 `buildCover`，记录 `封面装不下：head 超出 ...` 原文到 `v2-audit-failures.md`。同时记录小红书标题 21 字的报错原文。

- [ ] **Step 8: 验证**

```bash
npm run video:test -- video/tests/package-covers.test.mjs video/tests/xhs-release.test.mjs
npm run video:lint
```

---

### Task 10: 上屏数字审计 CLI

**Files:**
- Create: `video/src/numbers.mjs`
- Modify: `video/src/cli.mjs`（`numbers` 命令）
- Modify: `package.json`（`video:numbers`）
- Test: `video/tests/numbers.test.mjs`

**Interfaces:**
- Consumes: `episode.json` 双平台解析后的场景、`cover`、`publish`；`video/research/<ep>-numbers.json`。
- Produces: `flattenEpisode`、`extractTokens`、`auditNumbers`、`video:numbers`（未命中 exit 1）。

- [ ] **Step 1: 先写测试**

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { extractTokens, auditNumbers } from '../src/numbers.mjs'

test('抽 hex 与十进制，归一化逗号/单位空格', () => {
  const t = extractTokens('0x4002_1418 / 1,680,000 周期 / 514 ms')
  assert.ok(t.includes('0x40021418'))
  assert.ok(t.includes('1680000'))
  assert.ok(t.includes('514ms'))
})

test('未命中要报 unresolved', () => {
  const ep = { platforms: { bilibili: { scenes: [{ id: 'a', kind: 'card', title: '514 ms', narration: '一天欠 514 毫秒' }] } }, cover: {}, publish: {} }
  const r = auditNumbers(ep, { evidence: { '0xE000E010': 'probe' }, exceptions: {} })
  assert.ok(r.unresolved.some((u) => u.token === '514ms' || u.token === '514'))
})

test('exceptions 可以显式放行行号', () => {
  const ep = { platforms: { bilibili: { scenes: [{ id: 'a', kind: 'card', title: '第 4 行', narration: 'x' }] } }, cover: {}, publish: {} }
  const r = auditNumbers(ep, { evidence: {}, exceptions: { '4': '行号，不是实测值' } })
  assert.equal(r.unresolved.length, 0)
})
```

- [ ] **Step 2: 实现 numbers.mjs**

```js
import { readFileSync, existsSync } from 'node:fs'
import { join } from 'node:path'
import { resolveScenes } from './spec.mjs'
import { VIDEO_ROOT } from './util.mjs'

export function flattenEpisode(ep) {
  const out = []
  const push = (scene, field, text) => {
    if (typeof text === 'string' && text.trim()) out.push({ scene, field, text })
  }
  for (const p of Object.keys(ep.platforms || {})) {
    if (!['bilibili', 'douyin'].includes(p)) continue
    for (const sc of resolveScenes(ep, p)) {
      for (const f of ['title', 'sub', 'note', 'kicker', 'code', 'codeB', 'narration']) push(`${p}:${sc.id}`, f, sc[f])
      ;(sc.bullets || []).forEach((b, i) => push(`${p}:${sc.id}`, `bullets[${i}]`, b))
    }
  }
  const c = ep.cover || {}
  for (const f of ['line1', 'line2', 'num', 'numNote', 'proof', 'proofShort']) push('cover', f, c[f])
  if (c.vs) for (const f of ['left', 'right']) push('cover', `vs.${f}`, c.vs[f])
  for (const [p, pub] of Object.entries(ep.publish || {})) {
    for (const f of ['caption', 'pinned', 'repro', 'title', 'body', 'intro']) push(`publish.${p}`, f, pub[f])
    ;(pub.titles || []).forEach((t, i) => push(`publish.${p}`, `titles[${i}]`, t))
  }
  return out
}
```

归一化：

```js
const canonHex = (h) => '0x' + BigInt(h).toString(16)
const canonNum = (s) => s.replace(/[,_\s]/g, '')
export function extractTokens(text) {
  const out = new Set()
  for (const m of String(text).matchAll(/\b0x[0-9a-fA-F_]+\b/g)) out.add(canonHex(m[0].replace(/_/g, '')))
  for (const m of String(text).matchAll(/(?<![0-9A-Za-z_])\d+(?:[.,]\d+)*(?:\s*(?:%|ms|us|µs|ns|MHz|kHz|Hz|V|mA|µA|dB|ppm|KB|MB|GB))?/g)) {
    out.add(canonNum(m[0]).toLowerCase())
  }
  return [...out]
}
```

`auditNumbers` 把 evidence/exceptions 的键也归一化（hex 用 `canonHex`，数字用 `canonNum`），逐个 token 找精确命中；没命中的进 `unresolved`，带 `scene/field/text` 片段。返回 `{ tokens, resolved, unresolved }`。

- [ ] **Step 3: CLI**

```js
async function cmdNumbers(ids) {
  let bad = 0
  for (const id of pickEpisodes(ids)) {
    const ep = loadEpisode(id)
    const p = join(VIDEO_ROOT, 'research', `${id}-numbers.json`)
    if (!existsSync(p)) { log(`❌ ${id}: 缺 ${p}`); bad++; continue }
    const r = auditNumbers(ep, JSON.parse(readFileSync(p, 'utf8')))
    if (r.unresolved.length) {
      bad++
      log(`❌ ${id}: ${r.unresolved.length} 个数字未命中`)
      for (const u of r.unresolved.slice(0, 40)) log(`   - ${u.token}  @${u.scene}/${u.field}「${u.text.slice(0, 60)}」`)
    } else log(`✅ ${id}: ${r.tokens.length} 个数字都有依据`)
  }
  return bad ? 1 : 0
}
```

`main` 加 `if (cmd === 'numbers') return cmdNumbers(pos)`，`package.json` 加 `"video:numbers": "node video/src/cli.mjs numbers"`。

- [ ] **Step 4: 验证**

```bash
npm run video:test -- video/tests/numbers.test.mjs
```

S5 的 evidence 文件在 Task 11 落地；此任务只保证工具可跑、失败可判。

---

### Task 11: S5 端到端样板

**Files:**
- Modify: `video/episodes/s5-systick/episode.json`
- Create: `video/research/s5-systick-factsheet.md`
- Create: `video/research/s5-systick-numbers.json`
- Create: `video/research/s5-systick-review.md`
- Create: `video/research/s5-pilot-report.md`
- Read: `code/stm32/05-systick/probe.sh`、`.temp/s5-numbers.mjs`、`.temp/s5-header-probe.mjs`

**Interfaces:**
- Consumes: Task 2–10 的全部机制。
- Produces: 一集可复制的 v2 样板——重写稿、云扬音轨、节拍画面、四尺寸封面、数字证据、用户认可的封面版本与语速。

- [ ] **Step 1: 跑取证并写 fact sheet**

```bash
mkdir -p .temp/v2-facts
(cd code/stm32/05-systick && sh probe.sh) > .temp/v2-facts/s5-probe.log 2>&1
echo $? > .temp/v2-facts/s5-probe.exit
```

`video/research/s5-systick-factsheet.md` 必须包含：

- 源文档 `docs/stm32/05-systick.md`、取证脚本 `code/stm32/05-systick/probe.sh`、运行命令、退出码；
- 每个上屏数字：值、场景、证据命令、输出行（从 `.temp/v2-facts/s5-probe.log` 复制，不转述）；
- 本集必须回答的 3–5 个问题；
- 不能删掉的技术断言（删了会让章节断链的）；
- 已知未取证项（例如需要逻辑分析仪的百分比），明确写「不上屏」。

以 `.temp/s5-numbers.mjs` 的既有对账为起点，但每个 token 都要重新从本次 probe 日志里找到，不能直接抄旧结论。

- [ ] **Step 2: 写 numbers evidence**

`video/research/s5-systick-numbers.json`：

```json
{
  "ep": "s5-systick",
  "source": "code/stm32/05-systick/probe.sh",
  "evidence": {
    "0xE000E010": "probe.sh 寄存器版图输出",
    "514ms": "probe.sh 日漂移输出",
    "167999": "probe.sh 周期=LOAD+1 输出"
  },
  "exceptions": {
    "42": "断言总数，probe.sh 末行 42/42"
  }
}
```

每个键都要能在 fact sheet 里找到对应行。跑 `npm run video:numbers -- s5-systick`，未命中为 0 才继续。

- [ ] **Step 3: 重写横版旁白（8–12 分钟）**

按 v2 模板改 `platforms.bilibili.scenes`：

1. 冷开场 0–15s：先给「167999 还是 168000」的异常，不寒暄、不报集号。
2. 成本与路线 15–30s：不要开发板，宿主 gcc 跑断言。
3. 正文 3–6 节，沿用现有 6 个 `sections` 边界，但每节按「问题 → 证据 → 机制 → 一句话结论」重写。
4. 回收 20–30s：回到 514 ms。
5. 下集钩子 10s：读 `video/series.json` 的 `next`；若 S5 是最后一集，改成系列收束 + 开源书全文，不预告未完成内容。

硬预算：旁白总字数 **3000–3400 字**（est 587–665s），不得让 `est × 1.049 > 720`。钩子场总时长 ≤15s。字幕 10–24 字一句；不用「接下来我们」「众所周知」「话不多说」。

- [ ] **Step 4: 重写竖版旁白（60–75 秒）**

`platforms.douyin` 保持 `reuseFrom + pick`，10–12 场；旁白总字数 **250–290 字**（est 62–69s），钩子前置、每场一个点、最后一句金句。需要短版专用代码/标题时用 `platforms.douyin.set`，不复用横版 120 字取证行。

- [ ] **Step 5: 加 sections / beatMap / emphasis / ttsLexicon**

- `platforms.bilibili.sections` 保持 6 节（≤12 字）；`platforms.douyin.sections` 保持 5 节。
- `beatMap` 只给需要精确控制的场（例如 code 场按行组揭示）；其余走自动映射。
- `emphasis` 给关键数字 token（514 ms、167999、0xE000E010 等），必须在场上文本里。
- `ttsLexicon` 覆盖 Task 7 的初始词表；`ttsText` 只看错读句局部覆盖。
- `voice: "zh-CN-YunyangNeural"`、`formatVersion: 2`、`rate` 按 Task 7 抽听结果定。

- [ ] **Step 6: 补 `publish.zhihu` 与更新小红书文案**

以 `c2-pointer` 的 `publish.zhihu` 为模板补齐：`titles`、`intro`、`domain`、`mark`、`original`、`markNote`、`tags`、`topics`。小红书 `title` ≤20 字、`body` ≤1000 字、无站外地址、`collection` 非空、`pinned` 含复现命令。

- [ ] **Step 7: lint → build**

```bash
npm run video:lint -- s5-systick
npm run video:build -- s5-systick --stills
```

build 会覆盖 S5 旧母版；Task 0 的归档必须已校验通过。记录 build 日志到 `.temp/v2-pilot/s5-build.log`。

- [ ] **Step 8: check 与硬指标**

```bash
npm run video:check -- s5-systick
npm run video:numbers -- s5-systick
```

期望：bilibili/douyin 两行「排版审计通过」，0 跳过；numbers 0 未命中。再验：

```bash
ffprobe -v error -show_entries format=duration -of csv=p=0 video/out/s5-systick/bilibili.mp4
ffprobe -v error -show_entries format=duration -of csv=p=0 video/out/s5-systick/douyin.mp4
ffmpeg -hide_banner -i video/out/s5-systick/bilibili.mp4 -af ebur128=peak=true -f null - 2>&1 | tail -20
```

记录时长、LUFS、音画漂移、截图数/复用率、build 用时。

- [ ] **Step 9: 看截图**

用 Read 打开 `video/out/s5-systick/stills/*.png` 与四张封面；至少检查：开场首帧、每个 section 首帧、code 场行号/高亮、回收场、结尾。发现孤字、压字、行号压代码、readout 压内容，回改重跑 `check`。

- [ ] **Step 10: 封面 A/B 与 BGM/语速 A/B**

```bash
node video/src/cli.mjs cover s5-systick --variant vs --out .temp/v2-cover-ab/A
node video/src/cli.mjs cover s5-systick --variant panel --out .temp/v2-cover-ab/B
```

把 A/B 封面、`ambient-pad`/`lab-ambient` 两版混音、`+0/+2/+4` 三档语速给用户。用户选封面版本、BGM、语速；把选择写回 `episode.json`（`cover.variant`、`rate`）并记录到 `s5-pilot-report.md`。

- [ ] **Step 11: 独立审稿**

派一个独立审稿代理（或第二遍人工复核），输入：`s5-systick-factsheet.md`、`episode.json`、`s5-numbers.json`、`prd.md` 的 R1/R3。输出 `video/research/s5-systick-review.md`，逐条检查：每个数字有据、每个 section 有结论、钩子 ≤15s、竖版每场一个点、平台字数限制、没有表外断言。发现问题回改并重跑 Step 7–9。

- [ ] **Step 12: 用户看片门**

给用户：横版/竖版成片路径、四尺寸封面、contact sheet、review 结论、build/check/numbers 输出。明确问「这版 v2 标准是否通过」。未通过就改；未得到明确点头不进 Wave A。

- [ ] **Step 13: 写试点报告**

`s5-pilot-report.md`：实测时长、LUFS、漂移、截图数/总帧、build 用时、节拍统计、封面选择、语速/BGM 选择、用户结论。它是后续 wave 的产能与阈值基线。

---

### Task 12: Wave A（c2 / c3 / c4 / c5 / c6 / c7）

**Files:**
- Modify: `video/episodes/{c2-pointer,c3-volatile,c4-struct-abi,c5-func-pointer,c6-abi-stack,c7-ub}/episode.json`
- Create: `code/c/03-volatile/probe.sh`
- Create: `video/research/<ep>-factsheet.md`、`<ep>-numbers.json`（6 集）
- Create: `video/research/wave-a-report.md`

**Interfaces:**
- Consumes: S5 已批准的 v2 标准、Task 0 归档。
- Produces: Wave A 6 集双平台母版、四尺寸封面、发布包、数字证据、抽检报告。

- [ ] **Step 1: 补 c3 的取证脚本**

`code/c/03-volatile/probe.sh`：

```sh
#!/bin/sh
set -eu
cd "$(dirname "$0")"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
CC=${CC:-gcc}
echo "== host gcc =="
$CC --version | head -1
$CC -std=c11 -Wall -Wextra -O2 -S opt_probe.c -o "$TMP/opt_probe.s"
for fn in poll_plain poll_volatile delay_plain delay_volatile cfg_plain cfg_volatile isr_toggle; do
  echo "-- $fn --"
  sed -n "/<$fn>:/,/^[[:space:]]*\\.size/p" "$TMP/opt_probe.s" | head -20
done
$CC -std=c11 -Wall -Wextra -O2 opt_probe.c -o "$TMP/opt_probe"
"$TMP/opt_probe"
echo "== arm cross (optional) =="
if command -v arm-none-eabi-gcc >/dev/null 2>&1 && command -v arm-none-eabi-objdump >/dev/null 2>&1; then
  sh blink-variants.sh
else
  echo "~arm-none-eabi-gcc/objdump 不在 PATH，交叉段不跑"
fi
```

跑一次，把输出存 `.temp/v2-facts/c3-probe.log`。屏幕上只允许出现本次输出里有的数字；ARM 段没跑就不许上 ARM 常数。

- [ ] **Step 2: 每集先 fact sheet 与 numbers**

按 Task 11 Step 1–2 的同一格式，为 6 集各写 fact sheet 与 numbers JSON。每集的 `probe.sh` 路径：

| ep | probe |
|---|---|
| c2-pointer | `code/c/02-pointer/probe.sh` |
| c3-volatile | `code/c/03-volatile/probe.sh`（本任务新建） |
| c4-struct-abi | `code/c/04-struct-abi/broken.sh` + 正文引用的 probe |
| c5-func-pointer | `code/c/05-func-pointer/probe.sh` |
| c6-abi-stack | `code/c/06-abi-stack/probe.sh` |
| c7-ub | `code/c/07-ub/probe.sh` |

- [ ] **Step 3: 重写旁白并迁移 v2**

每集：`formatVersion: 2`、`voice: zh-CN-YunyangNeural`、双平台 `sections` 3–6、横版旁白 3000–3400 字、竖版按预算表。硬上限：

| ep | bilibili 场 | douyin 场 | 横版硬预算（字） | 竖版硬预算（字） | 竖版建议 |
|---|---:|---:|---:|---:|---:|
| c2-pointer | 27 | 10 | 2087–3510 | 141–311 | 240–280 |
| c3-volatile | 39 | 14 | 2087–3510 | 119–288 | 240–280 |
| c4-struct-abi | 40 | 14 | 2087–3510 | 119–288 | 240–280 |
| c5-func-pointer | 39 | 14 | 2087–3510 | 119–288 | 240–280 |
| c6-abi-stack | 31 | 11 | 2087–3510 | 135–305 | 240–280 |
| c7-ub | 32 | 11 | 2087–3510 | 135–305 | 240–280 |

横版按 3000–3400 字写；不要贴 3510 上沿。

- [ ] **Step 4: 每集构建与检查**

对每集依次：

```bash
npm run video:lint -- <id>
npm run video:build -- <id> --stills
npm run video:check -- <id>
npm run video:numbers -- <id>
npm run video:pack -- <id>
```

期望：两平台 check 通过、0 跳过；numbers 0 未命中；四尺寸封面 + `cover-contact-336.png` + 四份发布包齐全。build 前确认 `.temp/v2-baseline-20261022/masters/<id>/` 存在。

- [ ] **Step 5: 抽检与报告**

抽 c2 与 c7 给用户看片、看封面。`wave-a-report.md` 记录 6 集的时长、LUFS、漂移、节拍统计、numbers 计数、抽检结论、失败与回改。未通过不进 Wave B。

---

### Task 13: Wave B（f0 / f2 / f3 / f5 / f6 / p4）

**Files:**
- Modify: `video/episodes/{f0-why-rtos,f2-context-switch,f3-scheduler,f5-sem-mutex,f6-timers,p4-iram}/episode.json`
- Create: `video/research/<ep>-factsheet.md`、`<ep>-numbers.json`（6 集）
- Create: `video/research/wave-b-report.md`

**Interfaces:**
- Consumes: Wave A 已通过、同一套 v2 标准。
- Produces: Wave B 6 集母版/封面/发布包/证据/抽检。

- [ ] **Step 1: 每集 fact sheet 与 numbers**

probe 路径沿用各集 `series.json` 的 `hookRef` 与 `code/**/probe.sh`。f5 已有 `.temp` 的发布记录，但数字审计仍以本次 probe 输出为准。

- [ ] **Step 2: 重写与迁移**

预算表：

| ep | bilibili 场 | douyin 场 | 横版硬预算（字） | 竖版硬预算（字） | 竖版建议 |
|---|---:|---:|---:|---:|---:|
| f0-why-rtos | 20 | 4 | 2087–3510 | 65–149 | 90–130 |
| f2-context-switch | 29 | 11 | 2087–3510 | 135–305 | 240–280 |
| f3-scheduler | 34 | 12 | 2087–3510 | 130–300 | 240–280 |
| f5-sem-mutex | 35 | 12 | 2087–3510 | 130–300 | 240–280 |
| f6-timers | 34 | 12 | 2087–3510 | 130–300 | 240–280 |
| p4-iram | 25 | 10 | 2087–3510 | 141–311 | 240–280 |

横版 3000–3400 字。f0 竖版 4 场，按 20–35s 目标写 90–130 字，不要硬凑到 45s。

- [ ] **Step 3: 构建/检查/打包**

同 Task 12 Step 4。

- [x] **Step 4: 抽检与报告**

抽 f3 与 p4 给用户看片、看封面；写 `wave-b-report.md`。未通过不进 Wave C。

---

### Task 14: Wave C（s14 / s16 / s2 / s4 / s7）

**Files:**
- Modify: `video/episodes/{s14-pwr,s16-hardfault,s2-rcc,s4-nvic,s7-usart-baud}/episode.json`
- Create: `video/research/<ep>-factsheet.md`、`<ep>-numbers.json`（5 集）
- Create: `video/research/wave-c-report.md`

**Interfaces:**
- Consumes: Wave B 已通过。
- Produces: Wave C 5 集母版/封面/发布包/证据/抽检。

- [x] **Step 1: 每集 fact sheet 与 numbers**

s2/s4 当前旁白 3640–3679 字（est 712–719s），重写时必须**减少**，不能贴 720 上沿。目标 3000–3400 字。

- [x] **Step 2: 重写与迁移**

预算表：

| ep | bilibili 场 | douyin 场 | 横版硬预算（字） | 竖版硬预算（字） | 竖版建议 |
|---|---:|---:|---:|---:|---:|
| s14-pwr | 19 | 9 | 2087–3510 | 147–316 | 240–280 |
| s16-hardfault | 20 | 10 | 2087–3510 | 141–311 | 240–280 |
| s2-rcc | 25 | 11 | 2087–3510 | 135–305 | 240–280 |
| s4-nvic | 24 | 9 | 2087–3510 | 147–316 | 240–280 |
| s7-usart-baud | 33 | 11 | 2087–3510 | 135–305 | 240–280 |

- [x] **Step 3: 构建/检查/打包**

同 Task 12 Step 4。

- [ ] **Step 4: 抽检与报告**

抽 s4 与 s14 给用户看片、看封面；写 `wave-c-report.md`。全部通过后进 Task 15。

---

### Task 15: 18×2 母版全量审计、series.json、冻结

**Files:**
- Modify: `video/series.json`
- Create: `video/research/v2-final-audit.md`
- Create: `.temp/v2-final-audit/`（TSV、SHA256SUMS、对比图）
- Read: 18 集 `video/out/<ep>/{bilibili,douyin}.mp4`

**Interfaces:**
- Consumes: 三轮 wave 产物。
- Produces: 可冻结的 36 个 v2 母版 + 四尺寸封面 + 发布包；`series.json` 的 `masters` 与实测一致。

- [x] **Step 1: 全量 lint/check**

```bash
npm run video:lint > .temp/v2-final-audit/lint.log 2>&1
npm run video:check > .temp/v2-final-audit/check.log 2>&1
grep -c '🔍 排版审计通过' .temp/v2-final-audit/check.log   # 37（含 c3b v1）
grep -c '还没有时间轴，跳过' .temp/v2-final-audit/check.log  # 0
```

- [x] **Step 2: 全量 numbers**

```bash
npm run video:numbers -- c2-pointer c3-volatile c4-struct-abi c5-func-pointer c6-abi-stack c7-ub \
  f0-why-rtos f2-context-switch f3-scheduler f5-sem-mutex f6-timers p4-iram \
  s14-pwr s16-hardfault s2-rcc s4-nvic s5-systick s7-usart-baud
```

期望 18 集全部 0 未命中。

- [x] **Step 3: 母版技术审计**

对 36 个 v2 母版逐条记录：时长、targetSec 区间、LUFS、音频 codec/采样率/声道、sha256、字节数。TSV 表头：

```text
ep	platform	duration	lo	hi	lufs	codec	sampleRate	channels	sha256	bytes
```

断言：时长在 `targetSec` 内；LUFS -14±1；aac/44100/2ch；sha256 唯一且可复算。

- [x] **Step 4: 封面与发布包齐全检查**

每集必须有：

```text
video/out/<ep>/bilibili-cover.png        1920×1200
video/out/<ep>/douyin-cover.png          1080×1440
video/out/<ep>/zhihu-cover.png           1920×1080
video/out/<ep>/xiaohongshu-cover.png     1440×1080
video/out/<ep>/douyin-cover-1440x1080.png
video/out/<ep>/cover-contact-336.png
video/out/<ep>/发布-bilibili.md
video/out/<ep>/发布-douyin.md
video/out/<ep>/发布-zhihu.md
video/out/<ep>/发布-xiaohongshu.md
```

用 `ffprobe` 校验四张封面的宽高；contact sheet 人工看 336px 是否可读。

- [x] **Step 5: 旧/新并排抽帧**

对 18 集 × 2 平台，用 Task 0 的旧抽帧与 v2 同时间点抽帧做 `hstack`，存 `video/out/_v2-compare/<ep>/<platform>-<pct>.png`。每集至少看开场/中段/结尾三张，确认 v2 没有把内容切掉。

- [x] **Step 6: 同步 series.json**

用脚本读实测时长写 `masters`，保持 2 空格 JSON：

```bash
node --input-type=module -e "
import { readFileSync, writeFileSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
const p='video/series.json'; const s=JSON.parse(readFileSync(p,'utf8'))
const fmt=(x)=>{const m=Math.round(x/60); return String(Math.floor(m/60)).padStart(2,'0')+':'+String(m%60).padStart(2,'0')}
for(const e of s.episodes){
  if(!['c2-pointer','c3-volatile','c4-struct-abi','c5-func-pointer','c6-abi-stack','c7-ub','f0-why-rtos','f2-context-switch','f3-scheduler','f5-sem-mutex','f6-timers','p4-iram','s14-pwr','s16-hardfault','s2-rcc','s4-nvic','s5-systick','s7-usart-baud'].includes(e.id)) continue
  const d=(f)=>Number(execFileSync('ffprobe',['-v','error','-show_entries','format=duration','-of','csv=p=0',f],{encoding:'utf8'}).trim())
  e.masters='video/out/'+e.id+'/bilibili.mp4（'+fmt(d('video/out/'+e.id+'/bilibili.mp4'))+'）· douyin.mp4（'+fmt(d('video/out/'+e.id+'/douyin.mp4'))+'）'
}
writeFileSync(p, JSON.stringify(s,null,2)+'\n')
"
git diff --stat video/series.json
```

检查 diff：只允许 18 条的 `masters` 变化（以及用户要求的状态字段），不改其它条目。

- [x] **Step 7: 冻结**

```bash
cd video/out
find . -maxdepth 3 -type f \( -name '*.mp4' -o -name '*-cover*.png' -o -name 'cover-contact-336.png' -o -name '发布-*.md' \) -print0 |
sort -z | xargs -0 sha256sum > ../../.temp/v2-final-audit/SHA256SUMS
cd - >/dev/null
sha256sum -c .temp/v2-final-audit/SHA256SUMS --quiet && echo frozen
```

写 `video/research/v2-final-audit.md`：36 个母版的表、37/0 的 check 计数、18 集 numbers 0 未命中、封面齐全、对比图路径、冻结校验和路径、任何例外。

- [ ] **Step 8: 用户批准门**

把审计摘要给用户，明确问「是否批准进入投放」。未批准不进入 Task 16 的删除适配器实测与 Task 18。

---

### Task 16: repost 编排层（归档 / 准备 / 核对 / 删除 / 发布 / 台账）

**Files:**
- Create: `video/publish/repost/common.mjs`
- Create: `video/publish/repost/archive.mjs`
- Create: `video/publish/repost/prepare.mjs`
- Create: `video/publish/repost/verify.mjs`
- Create: `video/publish/repost/delete.mjs`
- Create: `video/publish/repost/publish.mjs`
- Create: `video/publish/repost/ledger.mjs`
- Create: `video/publish/repost/adapters/{bilibili,douyin,zhihu,xiaohongshu}.mjs`
- Test: `video/tests/repost-gates.test.mjs`
- Test: `video/tests/repost-archive.test.mjs`

**Interfaces:**
- Consumes: Task 1 探针报告、现有平台脚本（`bili-web.mjs`、`douyin-step.mjs`、`zh-one.mjs`、`zh-step.mjs`、`xhs-step.mjs`）、Task 0 旧母版/台账。
- Produces: 单集、单平台、默认只读的换新流程。删除/发布必须 `--go` + 逐集闸门。

- [x] **Step 1: 写闸门测试（先失败）**

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { requireGate, GateError, consumeGate } from '../publish/repost/common.mjs'

test('无闸门 exit 3', () => {
  const dir = mkdtempSync(join(tmpdir(), 'gate-'))
  assert.throws(() => requireGate('delete', 'ep', dir), (e) => e instanceof GateError && e.exitCode === 3)
})

test('闸门内容原样返回，消费后不可复用', () => {
  const dir = mkdtempSync(join(tmpdir(), 'gate-'))
  writeFileSync(join(dir, 'I_HAVE_USER_OK_DELETE_ep'), '我确认删除这一集的旧稿\n')
  assert.equal(requireGate('delete', 'ep', dir), '我确认删除这一集的旧稿')
  consumeGate('delete', 'ep', dir)
  assert.throws(() => requireGate('delete', 'ep', dir))
})
```

- [x] **Step 2: 实现 common.mjs**

```js
import { existsSync, mkdirSync, readFileSync, writeFileSync, appendFileSync, unlinkSync } from 'node:fs'
import { join } from 'node:path'
import { REPO_ROOT } from '../../src/util.mjs'

export const CDP = 'http://127.0.0.1:9223'
export const RUN_ROOT = join(REPO_ROOT, '.temp', 'repost')

export class GateError extends Error {
  constructor(message) { super(message); this.exitCode = 3 }
}

export function dayDir(ep, date = new Date().toISOString().slice(0, 10)) {
  const d = join(RUN_ROOT, date, ep)
  mkdirSync(d, { recursive: true })
  return d
}
export function gateName(kind, ep) {
  return kind === 'delete' ? `I_HAVE_USER_OK_DELETE_${ep}` : `I_HAVE_USER_OK_PUBLISH_${ep}`
}
export function requireGate(kind, ep, dir = dayDir(ep)) {
  const p = join(dir, gateName(kind, ep))
  if (!existsSync(p)) throw new GateError(`没有闸门 ${p}——这一步只能在对话里拿到这一集的明确点头后创建`)
  return readFileSync(p, 'utf8').trim()
}
export function consumeGate(kind, ep, dir = dayDir(ep)) {
  unlinkSync(join(dir, gateName(kind, ep)))
}
export function writeJson(p, obj) { writeFileSync(p, JSON.stringify(obj, null, 2) + '\n') }
export function appendEvent(dir, ev) { appendFileSync(join(dir, 'events.jsonl'), JSON.stringify({ at: new Date().toISOString(), ...ev }) + '\n') }
```

`parseArgs` 必须拒绝 `--all`：一次只处理一集。

- [x] **Step 3: 写 archive.mjs（只读）**

对每平台：

- B站：优先读 `.temp/bili-web-run/<ep>.bvid` 与 `published.jsonl` 的 `at/note`；再开管理页按标题精确匹配，记录行文本、封面 URL、状态。ID 只认 `BV[0-9A-Za-z]{10}`。
- 抖音：管理页按标题精确匹配，取行内 `/video/<id>` 链接或作品详情里的 aweme id；取不到就 `id: null` + `unavailable: ["id"]`，不猜。
- 知乎：`creator/manage/creation/zvideo` 按标题匹配，取 `/zvideo/<id>` 或 `/pin/<id>`；已有 `.temp/zh-run/<ep>-published.txt` 的作为佐证。
- 小红书：`note-manager` 按标题匹配，点「编辑」只读取 `id=`；不点发布、不点删除。取不到 noteId 就 `id: null`，但标题+发布时间仍记录。

`old.json` 结构：

```json
{
  "ep": "s5-systick",
  "archivedAt": "2026-10-22T...",
  "platforms": {
    "bilibili": { "id": "BV...", "title": "...", "duration": 629.2, "cover": "https://...", "collection": "...", "publishedAt": "...", "evidence": "manager row text", "unavailable": [] }
  }
}
```

已存在 `old.json` 时不得覆盖：读出来对比，不一致就停止。

- [x] **Step 4: 写 prepare.mjs（准备新稿，不发布）**

`--ep <id> --platform <p>` 默认打印步骤并检查产物；`--run` 才依次调用现有脚本。步骤表：

```js
const FLOWS = {
  bilibili: ['open', 'feed', 'wait', 'fill', 'check'],
  douyin: ['status', 'pick', 'text', 'topicprobe', 'click', 'links', 'cover', 'title', 'verify'],
  zhihu: [], // 用 zh-one.mjs --ep <id>，停在发布前
  xiaohongshu: ['open', 'upload', 'fill', 'topics', 'cover', 'coverset', 'coverapply', 'attach', 'collection', 'collectioncheck'],
}
```

抖音/小红书的步骤名以各自 `video/publish/*-plan.md` 最近一次成功链路为准；实现时把该链路复制进 `FLOWS`，不要自己发明新步骤。`prepare` 结束只打印「表单已就位，先删旧稿；不要关这个标签页」。

- [x] **Step 5: 写 delete.mjs（默认 probe）**

```js
const args = parseArgs()
if (!args.ep || !args.platform) throw new Error('必须 --ep <id> --platform <p>；不支持批量')
if (args.all) throw new Error('禁止批量删除')
const adapter = adapters[args.platform]
if (!args.go) {
  const found = await adapter.probeOld(ctx, ep)
  writeJson(join(dayDir(ep), 'delete-probe.json'), found)
  console.log('只读探针：找到入口/行如下，未点击删除')
  return
}
const gate = requireGate('delete', args.ep)
const old = readJson(join(dayDir(args.ep), 'old.json'))
if (!old?.platforms?.[args.platform]?.id && !args.manual) throw new Error('old.json 没有旧 ID，先补归档')
const res = args.manual
  ? await adapter.confirmManualDeleted(ctx, ep, old.platforms[args.platform])
  : await adapter.deleteOld(ctx, ep, old.platforms[args.platform])
appendEvent(dayDir(args.ep), { action: 'delete', platform: args.platform, gate, ...res })
consumeGate('delete', args.ep)
```

删除适配器规则：按旧 ID 精确匹配行；0 行或 >1 行都停止；点击「删除」后必须看到二次确认，再点「确认」；删除后重读列表，确认行消失。任何一步不确定就写 `unknown` 并停，不重试。

- [x] **Step 6: 写 publish.mjs（默认只读）**

`--go` + `requireGate('publish', ep)` 后，编排现有脚本：

| 平台 | 发布命令 | 平台闸门 |
|---|---|---|
| B站 | `node video/publish/bili-web.mjs publish --go` | `.temp/bili-web-run/I_HAVE_USER_OK=<ep>` |
| 抖音 | `node video/publish/douyin-step.mjs publish --go` | `.temp/douyin-run/I_HAVE_USER_OK=<ep>` |
| 知乎 | `node video/publish/zh-one.mjs --ep <ep> --publish` | `.temp/zh-run/I_HAVE_USER_OK=<ep>` |
| 小红书 | `node video/publish/xhs-step.mjs publish --go` | `.temp/xhs-run/I_HAVE_USER_OK=<ep>` |

`publish.mjs` 本身不点任何平台按钮，只调用这些脚本。调用前检查平台闸门存在且内容与 repost 闸门一致；不一致就停。发布后调 `verify.mjs --after` 回读新 ID。

- [x] **Step 7: 写 verify.mjs**

`--before`：检查母版时长/封面尺寸/发布包字数/numbers 证据，全部通过才允许进入删除。
`--after`：新 ID 必须存在且 ≠ 旧 ID；标题精确匹配；时长与母版差 ≤1s；封面 URL 存在；合集正确；小红书用 `xhs-match.mjs` 的 noteId/since 规则。任何一项拿不到就写 `unknown`，不重发。

- [x] **Step 8: 写 ledger.mjs**

`--ep <id>` 打印 `old.json`、`new.json`、`events.jsonl` 的合并视图；缺 `new.json` 就标「未完成」。旧/新 ID 必须同时可查。

- [x] **Step 9: 验证**

```bash
npm run video:test -- video/tests/repost-gates.test.mjs video/tests/repost-archive.test.mjs
node video/publish/repost/delete.mjs --ep s5-systick --platform bilibili   # 只读探针，必须没有点击删除
echo $?   # 0
node video/publish/repost/delete.mjs --ep s5-systick --platform bilibili --go  # 无闸门
echo $?   # 3
```

**完成记录（2026-10-29，s5-systick 实测）**

- 测试 113/113 通过；`delete.mjs --go` 无闸门 exit 3；B站只读探针 exit 0、0 行、未点击；repost 全部文件 `node --check` 通过。
- `verify.mjs --before` 四平台全绿（抖音 60.970s / 小红书 60.970s / B站 653.470s / 知乎 653.470s，数字证据 89 项 0 未命中）。
- 归档实测：抖音 `id=7697617004848532787`（68s，2026-10-17 20:45，封面齐全）；小红书 `id=6ad36ed80000000013019283`（2026-10-17 20:49，状态「未通过」）；B站仅台账线索 `BV1uEJi6vEnc`，页面重定向登录，`unavailable:[login,row]`；知乎**从未发过 s5**（API 84 条无此标题、`.temp/zh-run/` 无 s5 记录），`id:null`，按「首发布」而非换新对待。
- 适配器实测口径：抖音标题非叶节点、列表虚拟化，需滚 `.list-scroll` 并按 `video-card-info` 前缀匹配，ID 只能经详情弹层 `work-detail/<awemeId>` 取得；小红书状态文字在标题前，须用 `.note-card__title` 精确匹配，滚动容器是 `.content`。
- `saveOld` 改为逐平台合并：完整记录不可改，未完成记录允许补全（TDD 两条新测试）。
- `verify.mjs --after` 改用 `publishTitle(loadEpisode(ep))` 回读新标题，旧标题只用于定位归档。

### Task 17: 小红书发布幂等与新旧区分

**Files:**
- Create: `video/publish/repost/xhs-match.mjs`
- Modify: `video/publish/xhs-step.mjs`（publish 步写 marker、消费闸门、取 noteId）
- Modify: `video/publish/xhs-verify.mjs`（必须用 noteId 或 since）
- Test: `video/tests/xhs-match.test.mjs`

**Interfaces:**
- Consumes: `xhs-step.mjs` 的 publish 成功判据、`NOTE_MANAGER_URL`。
- Produces: `<ep>-published.txt` 含 noteId/url/at/gate；`matchPublished` 拒绝标题-only；发布后闸门被消费。

- [x] **Step 1: 先写测试**

```js
import test from 'node:test'
import assert from 'node:assert/strict'
import { matchPublished } from '../publish/repost/xhs-match.mjs'

const old = { id: 'old1', title: 'SysTick 一天漂 514 毫秒', createTime: '2026-09-01T10:00:00Z' }
const neu = { id: 'new1', title: 'SysTick 一天漂 514 毫秒', createTime: '2026-10-22T10:00:00Z' }

test('只有旧笔记 + since 在旧之后 → 0 条', () => {
  assert.equal(matchPublished([old], { title: old.title, since: '2026-10-22T00:00:00Z' }).length, 0)
})

test('新旧同标题 + since 在中间 → 只命中新', () => {
  assert.deepEqual(matchPublished([old, neu], { title: old.title, since: '2026-10-22T00:00:00Z' }).map((x) => x.id), ['new1'])
})

test('noteId 精确命中', () => {
  assert.deepEqual(matchPublished([old, neu], { title: old.title, noteId: 'new1' }).map((x) => x.id), ['new1'])
})

test('只给标题必须抛错', () => {
  assert.throws(() => matchPublished([old, neu], { title: old.title }), /noteId 或 since/)
})
```

- [x] **Step 2: 实现 xhs-match.mjs**

```js
const norm = (s) => String(s || '').replace(/\s+/g, '').trim()
export function matchPublished(cards, { title, noteId, since }) {
  if (noteId) return cards.filter((c) => String(c.id) === String(noteId))
  if (!since) throw new Error('xhs 回读必须给 noteId 或 since：只按标题会把旧笔记认成新笔记')
  const t = Date.parse(since)
  const hits = cards.filter((c) => norm(c.title).includes(norm(title)) && Date.parse(c.createTime) >= t)
  if (hits.length > 1) throw new Error(`标题命中 ${hits.length} 条，无法判定新笔记：${hits.map((h) => h.id).join(',')}`)
  return hits
}
```

- [x] **Step 3: 改 xhs-step.mjs publish**

- 记录 `runStartedAt` 在 publish 步开始时；
- 成功后从当前 URL 或 note-manager 的「编辑」入口拿 noteId；
- 写 `<ep>-published.txt`：

```text
noteId=<id>\turl=<url>\tat=<iso>\tgate=<用户原话>
```

- 拿不到 noteId：写 `noteId=null`，同时写 `since=<runStartedAt>`，不伪造 ID；
- 确认成功后才 `unlinkSync(gate)`；失败/不确定不消费闸门。

- [x] **Step 4: 改 xhs-verify.mjs**

删除标题-only 匹配；增加 `--note-id`、`--since`；用 `matchPublished`。读 marker 时优先 noteId，其次 since。验证输出必须打印命中的 noteId 与 createTime。

- [x] **Step 5: 验证**

```bash
npm run video:test -- video/tests/xhs-match.test.mjs
npm run video:lint
```

在真实浏览器上跑一次 `xhs-step.mjs status` 与 `xhs-verify.mjs --ep s5-systick --since <本次运行时间>`（只读）；确认旧笔记不会被当成新笔记。

**完成记录（2026-10-29）**

- 测试 119/119（xhs-match 6 条：noteId 精确、since 窗口、只给标题抛错、多条命中抛错、空标题抛错）。
- `xhs-step.mjs publish`：进分支即记 `runStartedAt`；URL `published=true` 后用新开的笔记管理页按 `.note-card__title` 逐字找卡、从 `data-impression` 取 noteId；取不到写 `noteId=null` + `since=<runStartedAt>`，不伪造；写 `<ep>-published.txt` 后才 `unlinkSync` 发布闸门。
- `xhs-verify.mjs` 重写：判定只认 noteId/since（`matchPublished`），命令行 > marker；缺凭据 exit 4，拒绝标题-only。实测发现并移除「已发布」tab 点击——`text=已发布` 会先命中卡片上的状态字，点后列表清空为 0；默认「全部」列表本就包含已发布笔记。
- 真实浏览器只读实测（75 张卡片全收）：`--since 2026-10-29T00:00:00+08:00` → 0/1（旧笔记不被当新笔记）；`--note-id 6ad36ed80000000013019283` → 命中，createTime=2026-10-17 20:49；`--ep s5-systick`（marker 无 noteId）→ exit 4。
- `npm run video:lint`：仅 `ai4fw` 未通过（未跟踪、10-28 另一条任务、formatVersion 1，不在本轮范围）；本轮改动未引入新 lint 错误。

---

### Task 18: 逐集换新执行（gated，一次一集）

**Files:**
- Create: `.temp/repost/<date>/<ep>/old.json`、`new.json`、`events.jsonl`、`delete-probe.json`
- Read: Task 15 冻结的母版/封面/发布包

**Interfaces:**
- Consumes: Task 16/17 工具、Task 1 平台决议、Task 15 用户批准。
- Produces: 每集旧/新 ID 台账；线上新稿回读证据。

- [ ] **Step 1: 平台与集顺序**

先按平台频控排期，不按集号硬排：抖音 1 天 1 条、最多 2 条；知乎按滚动窗口；B站投稿队列约 30 分钟。把排期写进 `.temp/repost/plan-<date>.md`，给用户确认。**一次只处理一集一个平台**。

- [ ] **Step 2: 归档**

```bash
node video/publish/repost/archive.mjs --ep <ep>
cat .temp/repost/<date>/<ep>/old.json
```

若旧 ID 缺失或匹配到多条，停止；不进入删除。

- [ ] **Step 3: 准备新稿**

```bash
node video/publish/repost/prepare.mjs --ep <ep> --platform <p> --run
node video/publish/repost/verify.mjs --ep <ep> --platform <p> --before
```

表单必须在位；若浏览器崩溃/标签页丢失，按未知状态停手，重新归档，不删旧稿。

- [ ] **Step 4: 请求删除授权**

把 `old.json`、删除探针结果、新稿核对结果给用户，明确说「要删的是 <平台> 的 <旧 ID>，标题 <标题>，删除不可逆」。只有用户回复明确授权后，才创建：

```bash
printf '%s\n' '<用户原话>' > .temp/repost/<date>/<ep>/I_HAVE_USER_OK_DELETE_<ep>
```

不得代写、不得复用上一次授权、不得一次写多集。

- [ ] **Step 5: 删除旧稿**

```bash
node video/publish/repost/delete.mjs --ep <ep> --platform <p> --go
```

删后必须回读列表确认旧行消失；不确定就写 `unknown` 并停。

- [ ] **Step 6: 请求发布授权**

把删除回读、新稿表单截图/字段核对给用户；用户明确授权后创建 `I_HAVE_USER_OK_PUBLISH_<ep>`，同时把同一句原话写入该平台自己的闸门（`.temp/<平台>-run/I_HAVE_USER_OK=<ep>`）。两个文件都必须是用户原话。

- [ ] **Step 7: 发布并回读**

```bash
node video/publish/repost/publish.mjs --ep <ep> --platform <p> --go
node video/publish/repost/verify.mjs --ep <ep> --platform <p> --after
node video/publish/repost/ledger.mjs --ep <ep>
```

新 ID 必须 ≠ 旧 ID；标题/时长/封面/合集逐项回读；小红书必须用 noteId 或 since。任何未知状态不重发。

- [ ] **Step 8: 节奏与收口**

按平台频控等待下一条；每集写 `events.jsonl` 与 `new.json`。全部完成后更新 `video/research/repost-final.md`：18 集 × 平台旧/新 ID、删除时间、发布顺序、任何手工删除记录。

**进展记录（2026-10-29，s5-systick × 小红书 / 抖音）**

- 小红书旧稿已删除：门禁原话「确认删除 s5-systick 小红书旧稿 6ad36ed80000000013019283」；
  `delete-xiaohongshu.json` 记录 confirmText「…取消 确定」；`xhs-verify --ep --note-id` 复核列表 75→74、旧 noteId 查无。
- 适配器修正（小红书）：二次确认按钮原先只在 `.d-modal-content`（正文）里找，实际按钮在同级 footer；
  改为从正文上溯到同时包住按钮的容器，按「确认删除 > 删除 > 确定/确认」排序；失败时输出可点元素/HTML。
- 抖音旧稿已删除：门禁原话「删除抖音旧稿」；`delete-douyin.json` 记录 oldId 7697617004848532787、
  确认按钮「确定」、列表回读旧卡消失；随后只读复探标题「谁在给 RTOS 数那一毫秒」0 行，证据留在 `delete-probe-douyin*.json`。
- 适配器修正（抖音）：弹窗容器类名不含 modal/dialog，按钮外层有带 `btn` 的包裹层，全页「只留最内层」
  会把 `取消/确定` 一起筛掉；改为以页面唯一可见「取消」为锚点上溯定位 footer，再按
  「确认删除 > 删除 > 确定/确认」取唯一按钮，并保留 ID/日期双重锁行。
- 进程事故：早前一次删除尝试触发两个 Playwright 客户端争抢原生对话框，守护进程崩溃、持久浏览器连同
  XHS/抖音草稿表单一起关闭；重启后先只读复探确认旧稿仍在，再执行删除。删除成功后守卫已消费，无残留闸门。
- 抖音已换新上线：用户原话「发布 s5 抖音新稿」（repost 闸门与平台闸门内容一致，均已用掉）。
  新稿 **7701997489129295154**，2026-10-29 16:03 发布，平台回 `status_code=0` 并离开投稿页。
  回读：新 ID ≠ 旧 ID、标题精确、封面 URL、时长 61s（对新母版 60.970s ±1s）全过。
  合集不在作品卡上渲染 → `verifyAfter` 记 unknown；独立只读探针查服务端：「通往单片机之路」总集数
  16→17、列表含新标题（`collection-evidence-douyin.json`）。
- publish.mjs 首次写 new.json 失败：详情弹层先以 about:blank 出现、随后才导航到 `work-detail/<id>`，
  `readDetailId` 只等 domcontentloaded 读到空 URL → 「抖音回读没有作品 id」。已改为
  `popup.waitForURL(DETAIL_ID, 15s)`；重跑 `verify --after` 拿到 ID 后按核实结果补录
  `new.json`（verified=false，unknown=[collection]；发布本身已由 status_code=0 确认），**未重投**。
- `verify.mjs` 时长核对修正：原以旧稿时长为基准（68s），重制稿（61s）必然失败；改为对本集新母版
  `video/out/<ep>/<platform master>` ±1s，旧时长只留在细节里参照。
- 接线修正：`publish.mjs` 知乎分支改空格形式 `--ep`（zh-one 只认这种）；`verifyAfter` 支持首发布
  （old.id 为空不再抛错，改为按标题回读唯一 id 判定），否则知乎发布会「成功了却报未确认」。
- prepare 修正：XHS 流程里的 `collection`/`collectioncheck` 认领的是**已发布笔记**，旧稿在时会误挂旧笔记，
  删稿后必失败；已从发布前 FLOWS 移除，发布后再跑。
- 抖音集号：合集（删旧稿后「共16个作品」）下拉只到 1..17，表单落 **第17集**；删稿前显示的「第18集」是
  按当时 17 条算的空格。合集编号是平台插入顺序，不跟 series.json（c3b-volatile 系列第 1 集、合集第 5 集），
  所以抖音要**先删旧稿再 prepare**。
- 待发布：只剩 XHS——新稿表单已重新备好并复核齐全（视频/标题 18 字/正文 793/1000/话题/竖封面/合集），
  留在常驻浏览器；`I_HAVE_USER_OK_PUBLISH_s5-systick` 已随抖音、知乎各消费一次——**一次授权只覆盖一个平台**，
  XHS 需用户新的原话。
- 平台闸门残留（**不得复用**）：`.temp/douyin-run/I_HAVE_USER_OK=s5-systick`（「发布 s5 抖音新稿」，已用掉）、
  `.temp/zh-run/I_HAVE_USER_OK=s5-systick`（「发布 s5 知乎首稿」，已用掉）、
  `.temp/xhs-run/I_HAVE_USER_OK=s5-systick`（10-17 旧授权）。
- 知乎已首发布：用户原话「发布 s5 知乎首稿」（repost 闸门已消费）。zh-one 续传中断的上传会话（不重传 45MB），
  8 项核对全绿后发布：弹窗「发布成功」、`/api/v4/content/publish` 200，新稿 **pin 2099155587959465367**，
  2026-10-29 16:24，状态「审核中」。回读全绿：首发布、标题精确、封面 1920×1080、时长 654s（母版 653.470s）。
- 知乎回读根因与修正：管理页作品卡显示**介绍正文，不显示标题**，按标题找行永远 0 行（首次 verify 因此失败，
  publish.mjs 没写 new.json）。已改为 zh-one 发布后把 pin URL 写成 `.temp/zh-run/<ep>-published.txt`，
  `verifyNew` 按 pin id 锁卡、开公开 pin 页核对标题/封面/发布时间；知乎无合集环节，collection 不再记 unknown。
  new.json 按核实结果补录（verified=true），**未重投**。
- 草稿箱口径更正：知乎视频稿不在「草稿箱→视频草稿」（该列表「暂无内容」），而是以「中断上传会话」
  挂在 upload-video 页（「继续发布 / 忽略」）。
- B站 10-29 复探仍未登录（0 行，passport 重定向）——停在闸门前，等登录后重探。
- 10-29 16:2x 全平台只读复核（`probe-platforms.mjs`）：bilibili not-logged-in；douyin/zhihu/xiaohongshu 已登录。
  小红书表单逐项复核齐全（视频/标题 18 字/正文 793/1000/话题 3 个/竖封面已应用/合集已挂，截图在
  `.temp/repost/2026-10-29/s5-systick/xhs-form-*.png`），可随时按授权发布。
- B站已登录并**换源完成**（用户原话「换源 s5 到 B站」；repost 闸门与 `.temp/bili-web-run/I_HAVE_USER_OK=s5-systick`
  均已消费）。两次 replace：09:43:09 首次只落元数据与 4:3 封面（喂错隐藏 mp4 input，视频仍旧源）；
  09:51:24Z 走真入口「上传完成 更换视频→确定→filechooser」挂 v2 母版后重新提交，`200 /x/vu/web/edit code=0 OK`
  + 页面「稿件投递成功」。BV1uEJi6vEnc 不变，stat/合集/发布时间沿用；成员侧 `videos[0]` cid 43150806979 / 654s，
  `archive.state=-60 审核中`；公开侧已先切新源（duration 654、state 0）；旧 cid 42822141657 / 630s 已不在。
  标题/简介（yaml 1966 + 尾注 24 = 1990）/tag 7 个/tid=231/copyright 全保留；合集 ugc_season 9435811 ep_count=18。
- B站封面：4:3 换 v2 `4f5d8c…`（1600×1200）；16:9 仍是旧 `96bd9f…`，与 v2 母版 16:9 中心裁切 SSIM 0.9957 /
  YAVG 差 0.679（JPEG 噪声级）→ 同一版美术，判定已换，不对 -60 稿件重复提交。
- B站审核已通过：2026-10-29T10:09Z 复核成员侧 `archive.state=0「开放浏览」`、公开 view state=0 / 654s /
  cid 43150806979；重跑 `verify --after --replace` **5/5 全绿**（BV 不变/标题/封面/时长/合集），
  写 `verify-after-bilibili.json`，09:56 提交现场存档 `verify-after-bilibili-0956.json`；
  `events.jsonl` 追加 `review-cleared`，`new.json` verified=true。
- B站已知差异：分P 标题 `videos[0].title` / `pages[0].part` = `bilibili`（上传文件名）。单 P 稿面基本不显示，
  修它要再走 edit 触发新一轮审核，**未授权不做**。
- B站适配器修正（只读干跑验证，`ok=true`，未写回记录）：管理页先填「搜索稿件」+ 回车精确锁行；
  行取 `.article-card`、封面取卡内 `bfs/archive` 图（不再抓到页头头像/图标）；合集改从公开 view
  `ugc_season` 回读；`verifyNew` 增 `replace` 分支（换源 BV 本就该相同）；发布日期兼容「2026年10月17日 20:43:45」。
- B站记录：`verify-after-bilibili.json`（unknown=[part-title]，pending=[review]）、`new.json`（verified=false）、
  `events.jsonl`（replace-verify、cover-check）。审核通过前只读复核，不重投、不再提交 edit。

---

### Task 19: 文档、spec、journal 与最终验证

**Files:**
- Modify: `.trellis/spec/video/v2-contract.md`
- Modify: `.trellis/spec/video/index.md`
- Modify: `.agents/skills/video-release/SKILL.md`
- Modify: `video/research/v2-baseline-20261022.md`（如路径/校验和更新）
- Modify: `video/research/v2-final-audit.md`
- Modify: `video/research/v2-audit-failures.md`
- Modify: `.trellis/workspace/zhuguang-ZFG/journal-1.md`

**Interfaces:**
- Consumes: 全部实现与实测结果。
- Produces: 下一次会话能直接复用的 v2 spec、命令、失败样例、journal。

- [ ] **Step 1: 写最终 v2 合同**

`v2-contract.md` 增加实测值：S5 节拍数/最长静止、截图数/总帧、build 用时、SFX 事件数、四尺寸封面、-14 LUFS 实测、漂移。合同只写已验证的事实。

- [ ] **Step 2: 更新视频规范索引**

`.trellis/spec/video/index.md` 增加：

```bash
npm run video:test
npm run video:numbers -- <id…>
npm run video:pack -- <id…>
```

并写清 v2 构建顺序仍是 `lint → build → check`，`numbers`/`pack` 在 build 之后；check 跳过数必须为 0。

- [ ] **Step 3: 更新投放 skill**

`.agents/skills/video-release/SKILL.md` 增加 repost 入口、两种逐集闸门、`xhs` 的 noteId/since 判据、无网页删除时的手工路径、未知状态不重发。保留原有五条红线，不放松。

- [ ] **Step 4: 汇总失败样例**

`v2-audit-failures.md` 必须包含每条新审计的失败命令与原文：节拍静止、未揭示、钩子超时、封面 42 字、小红书标题 21 字、无闸门 delete/publish exit 3、xhs 标题-only 回读。缺一条就补跑一次。

- [ ] **Step 5: 写 journal**

按 `.trellis/workspace/zhuguang-ZFG/journal-1.md` 现有格式追加本次会话：目标、完成/未完成、关键判据、踩坑、给下一次会话的入口。不要贴凭证、cookie、平台 token。

- [ ] **Step 6: 最终验证**

```bash
npm run video:test
npm run video:lint
npm run video:check > .temp/v2-final-audit/check-final.log 2>&1
grep -c '🔍 排版审计通过' .temp/v2-final-audit/check-final.log   # 37
grep -c '还没有时间轴，跳过' .temp/v2-final-audit/check-final.log  # 0
npm run video:numbers -- $(node -e "console.log(require('./video/series.json').episodes.filter(e=>e.id!=='c3b-volatile').map(e=>e.id).join(' '))")
sha256sum -c .temp/v2-final-audit/SHA256SUMS --quiet
```

期望：全绿；冻结校验通过；`git diff --stat` 只包含预期文件。若重建过任何母版，重跑 Task 15 的审计与冻结。

- [ ] **Step 7: 任务收口（经用户同意）**

```bash
python .trellis/scripts/task.py validate video-v2-remaster
python .trellis/scripts/task.py finish
```

只在用户明确同意完成后执行；未完成前保持 `in_progress`。提交同样只在用户明确要求时执行，且逐个文件 `git add`。

---

## Self-Review 摘要

- **Spec 覆盖**：R1 内容重写（Task 10–14 + fact sheet）、R2 视听引擎（Task 2–8）、R3 封面与文案（Task 9、15）、R4 平台替换（Task 1、16–18）均有对应任务；18 集与 c3b 排除写在 Global Constraints 与 wave 表中。
- **兼容线**：Task 0 生成金样例；Task 4/5 的测试直接比字符串；Task 6 明确 v1 日志不改；Task 8 的 v1 滤镜串有硬编码回归测试。
- **不可逆动作**：Task 16 的 `GateError` exit 3、Task 17 的 noteId/since、Task 18 的「一次一集」和「用户原话写闸门」构成三层防线。
- **失败样例**：节拍、封面、小红书回读、无闸门四类都在任务里要求把报错原文落盘；缺样例视为未完成。
- **类型/命名一致**：`formatVersion`、`beatMap`、`emphasis`、`ttsLexicon`、`ttsText`、`stateKey`、`requireGate`、`matchPublished` 在任务间保持同名同义。
