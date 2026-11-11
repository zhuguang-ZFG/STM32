# 设计：视频 v2 重制

## 0. 设计原则

- **证据先于表达**：旁白和画面上的每个数字先有 fact sheet 和本机实跑输出，再写句子。
- **离散动效**：只在字幕节拍上产生离散画面状态，不做连续动画；保住逐帧去重与可复现截图。
- **旧路径不动**：`formatVersion` 缺省时，旧集的 DOM、渲染路径、审计输出逐字节保持。
- **不可逆动作逐集放行**：删除与发布默认只读；`--go` + 逐集闸门才执行。
- **先产后排**：18 集母版全部验收前，不碰线上作品。

## 1. 总体架构

```
episode.json (formatVersion:2)
  → fact sheet / 重写稿
  → tts.mjs + assemble.py（云扬 + 发音表 + 逐句时长）
  → timeline.mjs（场景时间轴 + 字幕 + 节拍）
  → layout.mjs / stage.mjs（实验室仪器风 + 节拍 DOM）
  → render.mjs（离散状态截图 → PNG pipe → x264）
  → mux.mjs（旁白 + BGM + 程序化音效 → -14 LUFS）
  → package.mjs（三/四尺寸封面 + 发布包）
  → publish/repost/*（归档 → 准备 → 核对 → 删除 → 发布 → 回读 → 台账）
```

新增 `formatVersion: 2` 作为分叉点；`1` 或缺省走现有路径。

## 2. 内容重写管线

### 2.1 Fact sheet

每集在 `research/<ep>-factsheet.md` 落一张表，至少包含：

- 源文档路径、`probe.sh` 路径与运行命令。
- 现有场景 id/kind/旁白/上屏 code/文案。
- 每个上屏数字：值、出现场景、证据命令与输出行。
- 本期必须回答的 3–5 个问题。
- 不能删掉的技术断言（删了会让章节论证断链的）。

Fact sheet 是重写与审稿的唯一事实源；旁白不能引入表外数字。

### 2.2 v2 脚本模板

横版 8–12 分钟：

1. **冷开场 0–15s**：先给异常/结果，不寒暄，不报集号。
2. **成本与路线 15–30s**：要不要板子、要看哪几屏、这一集回答什么。
3. **正文 3–6 节**（每节 60–150s，`:sections` 显式声明）：
   - 问题：这一节要解释什么。
   - 证据：屏上先出本机输出/寄存器值/波形。
   - 机制：为什么是这样。
   - 结论：一句话可复述。
4. **回收 20–30s**：三句话总结，回到开场那个异常。
5. **下集钩子 10s**：只给一个问题，不预告未完成的内容。

竖版 60–75 秒：10–12 场，钩子前置、每场一个点、最后一句金句；沿用 `reuseFrom + pick`，旁白单独重写。

### 2.3 写法约束

- 一句一个意思；字幕 10–24 字；不用「接下来我们」「众所周知」「话不多说」。
- 英文、十六进制、寄存器名按屏上原样读；TTS 单独走发音替换表，字幕不改写。
- 每个数字要么在 fact sheet 里，要么删掉；新增实测必须先跑脚本并落盘。
- 竖版不复用横版的 120 字取证行；需要时用 `platforms.douyin.set` 给短版专用 `code/title`。

### 2.4 审稿

- 每集重写后跑 `numbers-audit`：把横竖两版所有上屏字段（`code`/`codeB`/`title`/`sub`/`bullets`/`note`/`narration` 中的数字 token）展平，逐个回 fact sheet 找依据；未命中的必须定性为「行号/同值短写法/待实测」并显式标注。
- 独立审稿代理逐条对 fact sheet、模板、字数与平台限制；输出 `research/<ep>-review.md`。
- 每一波抽 1–2 集给用户终审；试点集必须用户终审。

## 3. Schema 与兼容

### 3.1 `formatVersion`

- 顶层 `formatVersion: 2` 表示 v2；缺省按 v1 处理。
- c3b 不迁移；旧集未迁移前 `video:build` 仍走旧路径。
- `validateEpisode` 对 v2 追加：每平台必须有 `sections`；每场必须有可生成的节拍；`voice` 必须是云扬（或显式允许的 v2 音色）。

### 3.2 场景字段增量

```jsonc
{
  "id": "code-03",
  "kind": "code",
  "title": "…",
  "code": "…",
  "beatMap": [                      // 可选；缺省按字幕自动分组
    { "at": 1, "reveal": "line:0-4" },
    { "at": 3, "reveal": "line:5-9" }
  ],
  "emphasis": ["0x40021418"]        // 可选；出现时触发一次锁定动效
}
```

- `beatMap` 只用于需要精确控制的场；大部分场走自动映射。
- `emphasis` 里的 token 必须在 fact sheet 中；渲染时匹配到的文本加一次 scope-lock。
- `sections` 沿用现有契约（`at`/`title`，≤12 字），但 v2 每平台必须提供。

## 4. 视觉引擎

### 4.1 实验室仪器风

- 调色板：石墨蓝黑底 `#0b0f14`、面板 `#10161d`、网格 `rgba(120,160,200,.06)`、磷光绿 `#7ee787`、琥珀 `#f2b84b`、告警红 `#ff5d5d`、青 `#56d4dd`。
- 常驻仪器层（伪元素/静态 SVG，不随帧变）：
  - 四角测量框与细网格；
  - 顶部读数：`CH1 · SCENE 03/28 · 30fps` 与当前小节；
  - 底部时基刻度；
  - 右侧纵向量程刻度。
- code 场增加行号 gutter；当前行组加扫描高亮；证据行保留红边。
- card 场保留面板，但加仪器标签（`MEASURED` / `EXPECTED` / `WARNING`）。
- hook 场标题用离散通电/扫描入场，不做打字机逐字（逐字会产生过多状态）。
- 所有装饰不得进入内容安全区；`video:check` 的越界/相叠/字号地板继续生效。

### 4.2 节拍模型

时间轴已有每句字幕的绝对起止时间。对每一场：

1. 场景内字幕起点 `at = max(0, caption.start - scene.start)`。
2. 生成节拍 `{ at, captionIdx, target }`；`target` 由 kind 决定：
   - `hook`：title=0、sub=1、code=2；不足则用固定 0.8s 间隔补齐。
   - `code`：head=0；把 `code`/`codeB` 的行按字幕数分组，逐组揭示；`note` 最后一拍。
   - `card`：kicker/title=0；bullets 按字幕逐条；sub 最后一拍。
   - `anim`：side title/bullets 逐条；SVG 继续走 SMIL。
   - `outro`：title=0；bullets 逐条；url 最后一拍。
3. 若相邻节拍间隔 >6s，插入 `pulse` 节拍（只改变当前行高亮/游标，不揭示新内容），保证最长静止段 ≤6s。
4. 若整场只有 0–1 句字幕，按 1.2s/2.4s 补足到至少 2 拍。

### 4.3 状态与去重

- `stage.capture(index, smilTime, caption, opacity, reveal, beat)`；`beat = { index, phase }`。
- `phase` 三档：`0` 隐藏、`1` 半透明/位移中、`2` 定格。渲染器按 `(sceneTime - beatAt)/0.18s` 量化到 0/1/2。
- `stateKey` 增加 `beat.index|beat.phase`。同一拍内 `phase=2` 后状态不再变化，继续命中缓存。
- 转场：每场前 4 帧用 `.scan` 覆盖层（位置/透明度四档），状态键含 `transitionPhase`；第 5 帧起撤销。
- 预期截图数：比 v1 增加 2–4 倍；S5 试点先量，再决定 wave 规模。

### 4.4 DOM 契约

- 页头/进度杠仍只随场次号变；节拍只改 `.body` 内元素。
- 揭示元素用 `opacity/visibility`，不用 `display:none`，保持布局稳定，避免每拍重跑 `fitAll`。
- `MCU.setup(i)` 重置到 beat 0；`MCU.beat(k, phase)` 更新揭示；`MCU.showAll()` 给审计用（全部揭示后的几何）。
- 审计在 `showAll()` 后量越界/相叠/字号；另跑一遍逐拍检查「揭示元素在结束时全部可见」。

## 5. 音频

### 5.1 配音

- `voice: zh-CN-YunyangNeural`；先试 `rate: +2%`。Phase 1 用 `+0/+2/+4` 三版同句抽听，按实测字/秒与听感定稿。
- `tts.mjs` 支持 `ep.ttsLexicon`（全局）与 `scene.ttsText`（逐场覆盖）：
  - TTS 用替换后的文本合成；
  - 字幕/时间轴仍用 `narration` 原文；
  - 时长以合成音频为准。
- 初始发音表：`0x…` 按位读、`offsetof`、`BSRR`、`PendSV`、`SysTick`、`GPIOF`、`MHz`、`ms`、`us`、`LR`、`PC`、`SP`。逐集抽听后再补。

### 5.2 音效与 BGM

- 新增 `video/src/audio/sfx.mjs`：从 `timeline.json` 的节拍生成一条 `sfx.wav`。
  - 点击：8ms 滤波噪声 + 1kHz 衰减正弦；
  - 扫描 whoosh：180ms 带通噪声扫频；
  - 继电器：30ms 方波咔哒；
  - 片头/片尾：1.2s 双音提示。
  - 全部用确定性 PRNG 合成，不引入外部版权素材。
- BGM：保留 `ambient-pad.m4a` 作为 fallback；试点新增 `lab-ambient.m4a`（低频 drone + 慢脉冲），抽听后再定。
- 混音：旁白为主；BGM -16dB 后 sidechain ducking；SFX -24dB；`loudnorm=I=-14:TP=-1.5:LRA=11`；输出 aac 192k/44.1kHz/立体声。
- 断言：成片时长差 ≤0.15s；音频流 aac/44.1kHz/2ch；`ebur128` 读数落在 -14±1 LUFS。

## 6. 封面与文案

- 新模板 `coverV2Html`，与正片同一套字体/配色：
  - 仪器面板：网格、四角框、通道/时基读数；
  - 一句钩子 + 一张物证 + 一个数字；
  - 数字用红色游标圈选；物证卡保留红边；
  - VS 结构保留为「预期 vs 实测」的上下/左右读数，不强塞撞色对切。
- 尺寸：B站 1920×1200、抖音 1080×1440、知乎 1920×1080、小红书 1440×1080。
- 生成 336px 缩略图 contact sheet；读不到的元素不上封面。
- 标题/简介逐集重写；B站用 `plain()` 脱 markdown；抖音 30 字硬上限；小红书标题 ≤20、正文 ≤1000；知乎按现有表单。
- Phase 1 出两版封面（A：仪器面板 + VS 读数；B：纯仪器面板），用户选一版后再批量。

## 7. 平台替换

### 7.1 Phase 0 只读探针

对每个平台用常驻浏览器打开已发布作品的管理页，只读检查：

- B站：稿件编辑页是否有「更换视频/换源/重新上传」；若有，记录入口与网络请求。
- 抖音：内容管理的单条/批量「删除」入口；不点最终确认。
- 知乎：创作中心内容管理的「删除」入口。
- 小红书：笔记管理行菜单、笔记详情「⋯」菜单是否有删除；记录入口。

产出 `research/platform-replace-probe.md`：有/无、入口路径、判据、风险。没有入口的平台不硬造自动化。

### 7.2 新工具

`video/publish/repost/`：

- `archive.mjs`：从现有台账/公开页读旧 ID、标题、时长、封面、合集、时间；写 `old.json`。只读。
- `prepare.mjs`：按平台准备新稿；知乎走真草稿；B站/抖音/小红书把表单填好并停住，浏览器保持在位。
- `verify.mjs`：新稿标题/时长/封面/合集/声明逐项核对；不通过就停。
- `delete.mjs`：按旧 ID/标题精确匹配行；默认 probe；`--go` + `I_HAVE_USER_OK_DELETE_<ep>` 才点删除；删后回读列表确认消失。
- `publish.mjs`：默认只读；`--go` + `I_HAVE_USER_OK_PUBLISH_<ep>` 才点发布；发布后回读新 ID。
- `ledger.mjs`：写 `events.jsonl` 与 `new.json`；旧/新 ID 必须同时可查。
- `bili-replace.mjs`（仅当 Phase 0 探到换源）：上传新源 → 等转码 → 核对 cid/时长 → 提交；失败回退删重发。

### 7.3 单集替换顺序

**有真草稿（知乎）**

1. 归档旧稿；
2. 准备新稿并保存草稿；
3. 核对；
4. 删除旧稿（逐集闸门）；
5. 发布草稿（逐集闸门）；
6. 回读新 ID/状态。

**无持久草稿（B站/抖音/小红书）**

1. 归档旧稿；
2. 同一浏览器开新稿表单，上传/填写/核对，保持标签页；
3. 另开标签删除旧稿（逐集闸门）；
4. 回到新稿标签发布（逐集闸门）；
5. 回读新 ID/状态。

**B站换源**（若实测存在）

1. 归档旧 BV/元数据；
2. 换源上传新片；
3. 等转码并核对 cid/时长/封面；
4. 提交（逐集闸门）；
5. 回读 BV 仍存在、时长/封面/简介正确。

### 7.4 幂等与台账

- 旧台账先归档到 `.temp/repost/<date>/<ep>/old/`，再动线上。
- 新发布必须写 `<ep>-published.txt`、消费闸门、写 `new.json`。
- `xhs-verify` 改为接受期望 note id 或 `create_time` 下限，不能只按标题匹配。
- 任何平台回读失败都停在「未知」状态，不重发；未知状态按旧稿仍在处理。

## 8. 阶段与门

| 阶段 | 产出 | 出口 |
|---|---|---|
| Phase 0 | 平台探针报告、v2 合同、S5 fact sheet | 你确认 B站/小红书方案 |
| Phase 1 | S5 v2 横竖母版、封面 A/B、审计报告 | 你看片 + 选封面，确认 v2 标准 |
| Phase 2 | 17 集分 3 波（6/6/5）重写/渲染/检查/封面 | 每波抽检通过 |
| Phase 3 | 18×2 母版全量审计、发布包冻结 | 全绿、`series.json` 对齐 |
| Phase 4 | 替换工具实测 + 逐集投放 | 每集旧/新台账齐全 |
| Phase 5 | 文档/spec/journal/提交 | 收口 |

## 9. 测试与审计

- 现有：`npm run video:lint`、`npm run video:check`（18 集 × 双平台）。
- 新增 v2 审计：
  - 节拍：每场 ≥2 拍；code/card 最长静止 ≤6s；节拍不越场尾；结束时揭示元素全可见。
  - 节拍映射：每个字幕至少对应一拍；`beatMap` 的 `at` 必须是该场真实字幕序号。
  - 转场：每场前 4 帧状态键互异；第 5 帧起不再变化。
  - 音效：每个节拍有且只有一条 SFX；SFX 时间与节拍差 ≤1 帧。
- 故意失败：
  - 删掉一场的 `sections` → lint 报错；
  - 把某场节拍间隔改成 9s → v2 审计报「静止超限」；
  - 让某元素永不揭示 → 审计报「结束时不可见」；
  - 封面塞 42 字 → package 报溢出；
  - 无闸门跑 delete/publish → exit 3。
- 视觉：每集抽 6 帧（开场/每节首帧/回收/结尾）做 contact sheet；试点与每波样本给用户看。
- 音频：`ebur128`、时长差、音画漂移、3 场/集抽听。
- 发布：旧/新 ID、标题、时长、封面、合集逐项回读；小红书新旧笔记必须能区分。

## 10. 风险与回滚

- **内容漂移**：fact sheet + numbers-audit + 独立审稿 + 每波抽检；未取证的新句子直接删。
- **重写体量大**：59,274 字横版旁白；分 wave，每波 5–6 集，不与投放交叉。
- **删稿不可逆**：先归档元数据/母版；删除默认 probe；逐集闸门；绝不批量放行；未知状态不重发。
- **小红书无网页删除**：Phase 0 确认；没有就 App 手动删或该平台不换视频。
- **B站换源未知**：Phase 0 确认；没有就删重发。
- **渲染时间上涨**：离散节拍 + 状态去重；S5 先量截图数与耗时，再定 wave。
- **平台频控**：母版全产后按抖音 1 天 1 条、知乎滚动窗口、B站队列间隔排期。
- **TTS 错读**：发音表 + 逐集抽听；错读句用 `ttsText` 局部替换。
- **浏览器草稿态丢失**：无持久草稿的平台按「新稿表单在位 → 删旧 → 发新」顺序，标签页不关；崩溃则按未知状态停手。

## 11. 文件触点

- `video/src/spec.mjs`：`formatVersion`、v2 校验、`sections`/`beatMap`/`emphasis`。
- `video/src/timeline.mjs`：字幕 → 节拍；`pulse` 补齐；`iterateFrames` 输出 beat。
- `video/src/layout.mjs`：实验室仪器风、`data-beat`、`MCU.beat/showAll`、行号 gutter。
- `video/src/stage.mjs`：`capture(..., beat)`；转场相位。
- `video/src/render.mjs`：状态键、截图报告、静态段报告。
- `video/src/tts.mjs` + `video/src/audio/assemble.py`：云扬、发音表、`ttsText`。
- `video/src/audio/sfx.mjs`（新）：节拍音效合成。
- `video/src/mux.mjs`：SFX/BGM/旁白混音、响度与漂移断言。
- `video/src/package.mjs`：`coverV2Html`、四尺寸、缩略图 contact sheet。
- `video/src/cli.mjs`：v2 审计、`--stills`、构建报告。
- `video/publish/repost/*`（新）：归档/准备/核对/删除/发布/台账。
- `video/publish/xhs-step.mjs`、`xhs-verify.mjs`：幂等与新旧区分。
- `.trellis/spec/video/v2-contract.md`（新）：节拍、状态键、审计、兼容线。
- `video/series.json`：v2 母版时长/状态。

## 12. Phase 0/1 收口项

以下每一项都有固定的判定方式与截止阶段，不是留在设计里的占位符：

- B站换源是否存在：Phase 0 只读探针；有入口记路径，无入口回退删重发。
- 小红书网页删除是否存在：Phase 0 只读探针；无入口则 App 手动删或该平台不换视频。
- 云扬语速 `+0/+2/+4`：Phase 1 同句三版实测字/秒 + 用户抽听，选一档写回 episode。
- 封面 A/B：Phase 1 各出一张同集封面，用户选一版后批量。
- 新 BGM 是否替换现有 ambient pad：Phase 1 抽听对比，保留胜者。
