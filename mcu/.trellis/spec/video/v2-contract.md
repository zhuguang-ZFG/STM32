# v2 成片合同：schema、节拍、相位与状态键

Task 3–8 的共同依据。改 `video/src/spec.mjs`、`timeline.mjs`、`layout.mjs`、`stage.mjs`、`render.mjs`、`tts.mjs`，
或给某一集加 `formatVersion: 2` 之前读这份。schema 由 Task 2 落地（`video/src/spec.mjs` + `video/tests/spec-v2.test.mjs`），
节拍模型、DOM、状态键分别由 Task 3–5 落地；本合同先把字段名、取值范围和判据固定下来，任务之间不许各写一套。

## 1. formatVersion 语义

下游统一从 `video/src/spec.mjs` 取这三个符号，不要在本文件之外另立常量：

```js
import { FORMAT_VERSIONS, V2_VOICES, validateEpisode } from '../src/spec.mjs'
// FORMAT_VERSIONS = [1, 2]
// V2_VOICES = ['zh-CN-YunyangNeural']
```

- `episode.json` 顶层整数 `formatVersion`，**缺席或 `null` 等价于 1**；允许值只有 `FORMAT_VERSIONS = [1, 2]`。
  其它值（`0`、`3`、`"2"` 等）一律 lint 报错：`formatVersion=<值> 不在 1/2`。
- 版本是**整集**属性，不是平台属性，也不是 scene 属性。一集的两个平台共用同一个 `formatVersion`。
- `formatVersion` 缺席或为 `1`：**不执行任何 v2 校验**。`beatMap`/`emphasis`/`ttsText`/`ttsLexicon`
  即使写了、写坏了也不进入 v2 分支（v1 渲染也不读它们）。
- `formatVersion: 2` 时新增以下校验，全部在 `validateEpisode(ep, id)` 内：

| 层级 | 字段 | 规则 | 报错原文（节选） |
|---|---|---|---|
| episode | `voice` | 必须在 `V2_VOICES = ['zh-CN-YunyangNeural']` 内 | `v2 音色必须是 zh-CN-YunyangNeural，当前 "<voice>"` |
| episode | `ttsLexicon` | 可选；对象；键 ≥2 字符；值非空字符串 | `ttsLexicon["x"] 的键至少 2 字符` |
| platform | `sections` | 必填 3–6 节（按平台各自声明） | `平台 bilibili: v2 需要 3–6 节，当前 2 节` |
| scene | `beatMap` | 可选；非空数组，每项为非 null 对象；首项 `at: 1`，其后为 ≥1 的严格递增整数；`reveal` 在允许形状内且不越界 | `...beatMap[0]: 第一拍 at 必须是 1（场景基线）` |
| scene | `emphasis` | 可选；字符串数组；每项必须是本场上屏文本的**原样子串** | `...: emphasis "0xDEADBEEF" 不在这一场的上屏文本里` |
| scene | `ttsText` | 可选；非空字符串 | `...: ttsText 必须是非空字符串` |

v2 episode 的最小骨架（只示范字段形状；`sections` 实际必须 3–6 条，这里没展开）：

```json
{
  "id": "<目录名>",
  "formatVersion": 2,
  "voice": "zh-CN-YunyangNeural",
  "ttsLexicon": { "0x": "零 x " },
  "platforms": {
    "bilibili": {
      "sections": [{ "at": "<scene id>", "title": "<=12 字" }],
      "scenes": [{ "id": "<scene id>", "kind": "code", "narration": "...", "beatMap": [{ "at": 1, "reveal": "title" }] }]
    }
  }
}
```

## 2. v1 兼容线（硬性）

`formatVersion` 缺席/为 1 的集必须与改版前完全一致（2026-11-05 当前是 `ai4fw` 与 `c3b-volatile` 两份）：

- `pageHtml` 不传 `formatVersion`（或传 1）时，输出与 Task 0 金样例**逐字节相同**：
  `video/tests/fixtures/page-v1-s5-bilibili.html`、`page-v1-s5-douyin.html`。禁止改夹具，
  也禁止为 v2 改 `video/src/layout.mjs` 的 v1 分支（v2 分支只能新增、不能重排 v1 输出）。
- `stateKey(frame, opacity, reveal)` 的 v1 串一字不变，见 §7。
- `audioFilter` 的 v1 滤镜串一字不变（Task 8 的硬回归）。
- `npm run video:lint` 对 v1 集的通过文案与场次数不变（行数按当时 episode 集计，不写死历史总数）；`npm run video:check` 的 v1 逐场读数不变。
- v2 的 DOM/CSS/客户端方法只能由 `formatVersion === 2` 分支注入；v1 页面多一个 `data-beat-target`
  都会让 Task 4 的 `layout-v1.test.mjs` 变红。
- v1 集**不要**为了“先试试”写 v2 字段：lint 不查，build 也不读，只会留下会腐烂的死数据。

## 3. v2 `sections`：每平台 3–6 节

```json
"platforms": {
  "<platform>": {
    "sections": [
      { "at": "<该平台 resolveScenes 后真实存在的 scene id>", "title": "<非空，<= 12 字>" }
    ]
  }
}
```

- 数量按**该平台原始配置**的 `cfg.sections.length` 计；`reuseFrom + pick` 的竖版也必须自己声明，
  不能只依赖横版（竖版 pick 是横版子集，同一份边界表常命不中 id）。
- `at` 必须是该平台 `resolveScenes(ep, platform)` 结果里的真实 scene id；重复、乱序（按 scene 下标不严格递增）
  都报错。第一条 `at` 之前允许有未归节的片头场，页头在那几场保持空 chip。
- `title` 非空且 ≤ `SECTION_TITLE_MAX`（12）字；超了先减字，不许缩字号。
- v2 的数量下限是 3：少于 3 节（包括 `sections` 缺失或空数组）报 `v2 需要 3–6 节`；
  多于 6 节同样报错。v1 份的 `sections` 不设数量上下限，仍只走原有五条判据。

## 4. scene 级 v2 字段

### 4.1 `beatMap`

只给需要精确控制的场；缺席时 Task 3 自动分拍（见 §5）。形状：

```json
"beatMap": [
  { "at": 1, "reveal": "title" },
  { "at": 3, "reveal": "line:0-4" },
  { "at": 6, "reveal": "line:5-9" }
]
```

- 每一项必须是非 null 对象（数组也不行）；写坏成 `null`/标量/数组时只报
  `...beatMap[i]: beatMap 项必须是对象`，校验继续跑完、不抛异常。
- `at`：**本场字幕列表内的 1-based 序号**（不是全局字幕号、不是秒、不是 scene 下标）。
  首个条目的 `at` 必须是 `1`：它是场景基线，对应 caption 1 / 0 s；首拍写 `at > 1` 会被
  Task 3 错位或静默退回场首，schema 直接报 `第一拍 at 必须是 1（场景基线）`。
  首项之后必须是 ≥1 且严格递增的整数；`at: 0` 和重复值都报错。
- Task 3 的落点：第 0 拍固定在该场 0 s（首帧定格）；第 i 拍（i ≥ 1）落在
  `captions[beatMap[i].at - 1].start - sceneStart`。`at` 的上限是本场字幕条数；
  i ≥ 1 的 `at` 超出时 `deriveBeats` 直接构建失败（不再静默退回 0 s），报错形如
  `beatMap[1].at=3 超出本场字幕数 2`——写稿时保证 `at <= 本场字幕数`（schema 只查 ≥1/严格递增，
  这条上限由 Task 3 兜底；首项 `at: 1` 是 0 s 基线，不参与该上限检查）。
- `reveal` 允许形状（完整正则）：

```text
title | sub | note | kicker | url
code:<a>-<b> | codeB:<a>-<b> | line:<a>-<b> | bullets:<a>-<b>
```

- 带范围的形状是**闭区间、0-based**：`line:0-4` 揭示代码第 0–4 行，共 5 行；`bullets:0-1` 揭示前两条。
  `a > b` 报“起止倒置”；`b >= 总数` 报“越界（共 N 行/条）”。
- 行数口径：`lineCount(src) = src ? String(src).replace(/\n$/, '').split('\n').length : 0`
  （只去掉一个末尾换行；空/缺省为 0）。
- 越界上限按前缀取：`line:` → `sc.code` 行数；`code:` → `sc.code` 行数；
  `codeB:` → `sc.codeB` 行数；`bullets:` → `sc.bullets.length`。
  `code:` 与 `line:` 同指主代码列，Task 3 把 `code:` 展开成 `line:` 目标。
- 原子目标 `title/sub/note/kicker/url` 不查存在性；Task 3 只揭示该场 `sceneTargets` 里真实存在的目标，
  多出来的 target 不会造成 lint 失败，但也不会有 DOM 元素可揭示——按场次实际字段写。
- 允许 `beatMap` 不覆盖全部目标：Task 3 会把未覆盖目标补到最后一个 content 拍（保证“永远不揭示”不成立）。
- v2 不强制有 `beatMap`；强制的是 Task 3 的节拍审计（每场 ≥2 拍、每句字幕有拍、code/card 静止 ≤6.05 s、
  钩子段总时长 ≤15 s）。首句字幕的 0.05 s 对拍有豁免、静止判据含 0.05 s 容差，见 §5。

### 4.2 `emphasis`

```json
"emphasis": ["514 ms", "0xE000E010"]
```

- 必须是数组；每项是非空字符串，且是该场**上屏文本**的原样子串。上屏文本的判定集合只有：
  `title`、`sub`、`note`、`kicker`、`code`、`codeB`、`bullets[*]`；**旁白 `narration` 不算**（它不上屏）。
- 用途：Task 4/5 把 `sc.emphasis` 以 `emph` 字段放进 v2 的 `window.PAYLOAD`（`emph` 是页面内部名，
  episode 里仍写 `emphasis`），在 `setup(i)` 里把这些 token 包成 `<span class="emph">`（最长 token 优先，
  包完再 `fitAll`），节拍相位到 2 时加 `.locked`。只做行内标记，不新增块级布局。
- `emphasis: []` 合法但无意义；不要写不存在的 token，也不要写跨行的大段文本。

### 4.3 `ttsText`

- 每场可选的非空字符串，**只替换送去 TTS 的文本**。字幕、时间轴、`captions`、上屏文本仍用 `narration`。
- 取值顺序（Task 7）：`(sc.ttsText || sc.narration).trim()` → `applyLexicon(...)`。发音表替换在
  `ttsText` 覆盖之后，两者可叠加。
- 只给“这一句会被读错”的场做局部覆盖；不要拿它当第二份旁白维护。改 `ttsText` 会改变音频缓存键
  （assemble.py 的 sha1 用 spoken text），触发该场重合成。
- schema 只查“非空字符串”，不查它与 `narration` 的字数/语义对应；对账靠 Task 11 的抽听。

### 4.4 `ttsLexicon`

episode 顶层对象，只影响 TTS，不影响字幕与上屏：

```json
"ttsLexicon": { "0x": "零 x ", "offsetof": "offset of", "MHz": "兆赫" }
```

- 键 ≥2 字符，值非空字符串；`applyLexicon` 按**键长从长到短**做全局子串替换（`split/join`，非正则）。
- 键至少 2 字符是为了避免单字符键把正文里的普通字一起改掉；`0x`、`ms`、`us`、`LR` 这类短键是下限附近的常用项。
- 同一个字符串既在 `ttsText` 又在发音表里时，先 `ttsText` 覆盖，再整串过发音表。

## 5. 节拍模型（Task 3 产出，Task 4–8 消费）

常量：`MAX_STATIC_GAP = 6` 秒、`BEAT_FADE = 0.18` 秒。

每场的目标集合（`sceneTargets(sc)`）：

| kind | targets |
|---|---|
| `code` | `title`、`line:0..N-1`（`sc.code`）、`codeB:0..M-1`（`sc.codeB`）、`note` |
| `hook` | `title`、`sub`、`line:0..N-1` |
| `card` | `kicker`、`title`、`bullets:0..N-1`、`sub` |
| `anim` | `title`、`bullets:0..N-1`、`note` |
| `outro` | `title`、`bullets:0..N-1`、`sub`、`url` |

拍对象：`{ index, at, kind, targets, captionIdx }`；`kind ∈ content | caption | pulse`；
`at` 是相对本场开头的秒数（不是 frame）。`plan.scenes[*].beats` 由 `deriveBeats` 生成：

- 有 `beatMap`：按 §4.1 落点，`targets = expandTargets(reveal)`；为没有对应 content 拍的字幕补
  `kind: 'caption'` 拍（空 targets，用于字幕同步）。
- 无 `beatMap`：拍数 = `max(2, 本场字幕数)`；lead 目标（`title`/`kicker`/hook 的 `sub`）放第 0 拍，
  正文目标按均分塞进后续拍，tail 目标（`sub`/`url`/`note`）放最后一拍；每拍按位置带 `captionIdx`。
- 只有一拍时拆成两拍；所有未揭示 target 补到最后一个 content 拍。
- 相邻两拍间隔超过 6 s 时插入 `kind: 'pulse'` 空拍（从上一拍 +6 s 起，每 6 s 一个；插入判据是
  `t < 下一拍.at - 0.05`），pulse 目标始终是 6 s 网格。6.00–6.05 s 的贴边空档因此不会插入 pulse。
- `beatAt(beats, rel)` 返回 `{ index, at, kind, phase, targets, revealed }`；
  `revealed` 是前 i 拍 targets 的并集（去重）。

`validateBeats(plan)` 在 v2 build 时必跑，失败即 throw，覆盖：

- 每场至少 2 拍（0 拍、1 拍都报错），拍时间严格递增。
- `code`/`card` 场最长静止 ≤ `MAX_STATIC_GAP + 0.05`（6.05 s）：与 pulse 插入共用 0.05 s 容差，
  6.00–6.05 s 的空档不插 pulse 也不判失败；超过 6.05 s 仍报 `静止 6.1s > 6s`。
- 每个 `sceneTargets` 至少被揭示一次。
- 每句字幕 0.05 s 内必须有拍，但**首句字幕豁免**：第 0 拍锚定场景 0 s，首句字幕常在 TTS 起播留白
  （实测约 0.22 s）之后才开始，不要求它与 0 s 对齐；第 2 句起每句都必须落在某拍 ±0.05 s 内。
- 开场连续 `hook` 场总时长 ≤15 s。

通过后 `plan.beatStats = { beats, pulses, maxGap, scenes }`，供 Task 6 的审计行与 Task 8 的 SFX 使用。

`iterateFrames` 的每帧新增 `beat`（v1 为 `null`）与 `transitionPhase`（v1 为 `-1`）。

## 6. 节拍相位（0 / 1 / 2）

相位只描述“当前拍”的入场进度，`dt = 当前帧秒 - 当前拍.at`，`BEAT_FADE = 0.18`：

| phase | 条件 | v2 画面（Task 4 的 `MCU.state`） |
|---|---|---|
| 2 | `dt >= 0.36`，或本场第 0 拍（首拍） | 当前 targets 全亮（opacity 1），加 `.cur`；`.emph` 加 `.locked` |
| 0 | `0 <= dt < 0.18` | 当前 targets opacity 0（隐藏），无位移 |
| 1 | `0.18 <= dt < 0.36` | 当前 targets opacity 0.5，`translateY(6px)` |

- 本场第一拍**直接 phase 2**（首帧定格，不再做目标淡入）；入场统一交给转场相位。
- `phase` 只影响 `beat.targets` 里的元素；`beat.revealed` 里更早的目标保持 opacity 1。
- `kind: 'pulse'` 的拍 targets 为空，只让游标跳到新位置（`index % 5` 决定纵向位置）。
- 转场相位是另一套数：`transitionPhase(f) = f < 4 ? f : -1`（`f` 是场内帧号）。
  `0/1/2/3` 时扫描层 opacity 依次 `1/0.72/0.38/0`、`translateY` 依次 25%/50%/75%/100%；
  `-1` 时扫描层隐藏。只有每场前 4 帧有转场。

## 7. 状态键格式

`stateKey` 是逐帧去重的键：键相同 ⇒ 复用上一帧 PNG。v1 原串（必须逐字符保持）：

```text
<scene.index>|<smil>|<captionIdx>|<opacity>|<reveal>
```

- `smil`：`frame.smilTime === null` 时为 `-`；否则量化到 1/60 s 再 `toFixed(4)`，例如 `1.2000`。
- `opacity`：四舍五入到 2 位小数。
- 例：`7|1.2000|3|0.5|0.75`。

v2 在**有 beat 或有转场**时追加两段（`beat` 为 null 且 `transition < 0` 时仍是 v1 原串）：

```text
...|b<beat.index>:<beat.phase>|t<transitionPhase 或 ->
```

- 例：`stateKey(frame, 1, 1, { index: 2, phase: 1 }, -1)` → `7|1.2000|3|1|1|b2:1|t-`
- 例：同一帧带转场 3 → `7|1.2000|3|1|1|b2:1|t3`
- 任何会改变画面的 v2 变量都必须进键；反之不要把不影响画面的量塞进来，否则去重失效、渲染变慢。

## 8. 审计命令

```bash
npm run video:test                                    # 跑 video/tests/**/*.test.mjs
node --test video/tests/spec-v2.test.mjs              # 只跑一个文件（不要用 npm run video:test -- <file>）
npm run video:lint                                    # 当时 episode 集的全量契约校验（只读）
npm run video:check -- <id> [--platform <p>]          # 舞台 + 排版审计，不渲帧、不写 video/out/
npm run video:build -- <id> [--stills]                # 会写 video/out/：只在 Task 0 归档校验通过后用
```

- `video:test` 脚本用 glob（`node --test "video/tests/**/*.test.mjs"`）而不是目录参数：本机 Node 24.14.0
  的 `--test` 会把目录位置参数当模块去 require，报 `Cannot find module ...\video\tests`。
  新增测试只要放在 `video/tests/` 下、命名 `*.test.mjs` 就会被自动收进来。
- `video:lint` 的期望：当前所有 `episode.json` 各一行通过；v1 夹具所在的 `s5-systick` 仍按 v1 基线，不把 2026-10 的 19 行当成永久数字。2026-11-05 实跑为 19/20：`ai4fw` 缺 `voice`/`platforms`/`cover.line1`，属存量内容缺口，补齐前不得写"全绿"。
- `video:check` 的期望：通过行数 = 目标集里实际声明且已有时间轴的平台数，`跳过` 计数 0。2026-10 的历史样本是 19 集 37 个平台配置；当前集数从 `video/episodes/*/episode.json` 计算。
- `npm run video:test -- <文件>` 会先执行脚本自带的 glob，再追加该文件；Node 只对同一路径去重，所以它**不是**单文件模式。单文件必须直接 `node --test <文件>`。

## 9. 校验失败原文（Task 2 已落地）

| 输入 | 报错（包含以下原文） |
|---|---|
| `formatVersion: 3` | `formatVersion=3 不在 1/2` |
| v2 `voice` 不是云扬 | `v2 音色必须是 zh-CN-YunyangNeural，当前 "zh-CN-YunxiNeural"` |
| v2 `sections` 只有 2 节 | `平台 bilibili: v2 需要 3–6 节，当前 2 节` |
| `beatMap: []` / 非数组 | `...: beatMap 必须是非空数组` |
| `beatMap[0].at = 0` | `...beatMap[0]: at 必须是 ≥1 的整数（1-based 字幕序号）` |
| 首拍 `at: 2` | `...beatMap[0]: 第一拍 at 必须是 1（场景基线）` |
| `beatMap: [null]` | `...beatMap[0]: beatMap 项必须是对象` |
| `beatMap[1].at` 不大于上一拍 | `...beatMap[1]: at=1 必须大于上一拍 1` |
| `reveal: "line:x-y"` | `...beatMap[0]: reveal="line:x-y" 不在允许形状内` |
| `reveal: "line:3-1"` | `...: line:3-1 起止倒置` |
| `reveal: "line:5-9"` 但只有 5 行 | `...: line:5-9 越界（共 5 行/条）` |
| `emphasis` 非数组 | `...: emphasis 必须是数组` |
| `emphasis` 有空项 | `...: emphasis 里有空值` |
| `emphasis` 不在上屏文本 | `...: emphasis "0xDEADBEEF" 不在这一场的上屏文本里` |
| `ttsLexicon` 非对象 | `ttsLexicon 必须是对象` |
| 键只有 1 字符 | `ttsLexicon["x"] 的键至少 2 字符` |
| 值为空/非字符串 | `ttsLexicon["x"] 的值必须是非空字符串` |
| `ttsText` 为空/非字符串 | `...: ttsText 必须是非空字符串` |

## 10. 边界与纪律

- Task 2 只加 schema，不加任何内容：上屏文字只能来自 `episode.json` 与 `video/out/` 产物，不能写进
  `layout.mjs`/`render.mjs` 常量。
- 不改 `video/out/`、不改 `video/src/layout.mjs` 的 v1 路径、不改 Task 0 的两份 HTML 夹具。
- v2 判据只挂在 `fv === 2` 分支；任何“顺手也给 v1 查一下”的改动都违反兼容线。
- 字段命名在 Task 2–14 之间保持同名同义：`formatVersion`、`beatMap`、`emphasis`、`ttsLexicon`、`ttsText`、
  `stateKey`。不要用 `beats`/`emph`/`lexicon` 之类的别名写进 `episode.json`（`emph` 只是 DOM 标记名）。
