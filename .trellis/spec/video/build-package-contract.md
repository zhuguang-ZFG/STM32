# 视频生产与发布包合同

## 1. 适用范围与触发

- 改 `video/src/cli.mjs`、`package.mjs`、`spec.mjs`、`timeline.mjs`、`tts.mjs`、`mux.mjs`、`numbers.mjs` 时读这份。
- 给某集改 `episode.json` 的 `publish`/封面字段、重排 `video/out/<id>/`、生成 `发布-*.md` 时读这份。
- 平台"准备/发布/删除"不在这里：入口是 `.agents/skills/video-release/SKILL.md` 与 `video/publish/` 台账。
  本合同的任何命令都不授权平台动作。

## 2. 签名与产物

所有命令经 `npm run <script> -- <args>`；`cli.mjs` 自己解析 `--k v` 与 `--k=v`，未知子命令直接报错。

| 命令 | 参数 | 读写与产物 |
|---|---|---|
| `video:lint [id…]` | 无 flag | 只读；校验 `episode.json`；跨集抖音文案重复检查始终看全集 |
| `video:check [id…] [--platform bilibili|douyin]` | 默认两平台 | 只读；开 Chromium 做舞台 + 排版审计；缺 `timeline.json` 打印 `⏭️ … 跳过` 并 `exit 0` |
| `video:cover [id…] [--platform p] [--out DIR] [--variant vs|panel]` | 默认 `bilibili`+`douyin` | 写 `<out>/<platform>-cover.png`；不传 `--out` 时写 `video/out/<id>/`；一个 id 时 `--out` 是目录本身，多个 id 时是父目录（内部再拼 id） |
| `video:pack [id…]` | 无 flag | 只重排发布包；写 `video/out/<id>/发布-<platform>.md`；先全量预检再统一写盘 |
| `video:build [id…] [--platform bilibili|douyin|both] [--force-audio] [--stills] [--no-bgm] [--variant vs|panel]` | 默认 both | 会合成音频、渲帧、合流；写 `video/out/<id>/<platform>/` 与 `video/out/<id>/`；v2 先出齐四张封面 |
| `video:numbers [id…]` | 不接受 flag | 只读；要求 `video/research/<id>-numbers.json`；未命中非零退出 |
| `video:calib [--anims a,b]` | 校准动画列表 | 开浏览器跑 seek 标定；不改 `out/`（临时产物除外） |

## 3. 数据与环境契约

### 3.1 封面尺寸与母版映射

`package.mjs` 的当前导出（改尺寸只改这里，不在文档/脚本里另写一套）：

```js
COVER_SIZES = {
  bilibili: [1920, 1200],
  douyin: [1080, 1440],
  zhihu: [1920, 1080],
  xiaohongshu: [1440, 1080],
}
PACK_MAP = {
  bilibili:    { base: 'bilibili', video: 'bilibili.mp4', cover: 'bilibili-cover.png',    srt: 'bilibili.srt' },
  douyin:      { base: 'douyin',   video: 'douyin.mp4',   cover: 'douyin-cover.png',      srt: 'douyin.srt' },
  zhihu:       { base: 'bilibili', video: 'bilibili.mp4', cover: 'zhihu-cover.png',       srt: 'bilibili.srt' },
  xiaohongshu: { base: 'douyin',   video: 'douyin.mp4',   cover: 'xiaohongshu-cover.png', srt: 'douyin.srt' },
}
```

- 知乎没有自己的成片，复用 B站横版；小红书复用抖音竖版。只有封面按目标平台重排，不重渲。
- 小红书 4:3 封面不能拿抖音 3:4 裁；抖音的 4:3 备选是 `xiaohongshu-cover.png` 的逐字节拷贝（`douyin-cover-1440x1080.png`）。
- v2 集的 `video:build` 在平台循环前调用 `buildAllCovers`：四张 + `cover-contact-336.png` + 抖音 4:3 备选。
  `buildOne` 只断言四张存在，避免第二个平台把第一张覆盖成另一套文案。
- v1 集仍按平台各出一张；`video:cover` 默认只出 B站/抖音，知乎/小红书要显式 `--platform`。

### 3.2 构建顺序与目标门

固定顺序：`lint → tts/timeline → stage/audit → render → mux → package`。

- `build` 用 `cfg.targetSec` 的 `[lo, hi]` 卡实际成片秒数，超出直接 throw；`lint` 的估算是软判据，两者不可互相替代。
- 有动画场时先跑 seek 自检（前进/后退可复现 + 跨时刻确实在动）；`--skip-selftest` 只用于已知夹具。
- `auditLayout` 在渲帧前跑：越界、裁切、压字幕、版式相叠、字号不可读、顶穿容器、标题孤字、进度杠重复；失败即 throw。
- 渲完校验 SRT：字幕条数 = timeline captions、时间单调、末句不越片尾；再合流。
- v2 合流带节拍 SFX，SFX 事件数必须等于 `plan.beatStats.beats`；BGM 走 ducking + loudnorm。
- 成片时长与渲帧数偏差 > 1/fps 直接 throw；不静默接受漂移。
- 成功后才 `writeRelease` 生成 `发布-<platform>.md`。

### 3.3 发布包的预检与写入

- `packJobs(ep, id)` 只按 `ep.publish` 的平台生成 job；未知平台（如 `weibo`）直接 throw，无 `publish` 也 throw；这一步不读磁盘。
- `cmdPack` 第一趟对**所有目标集**解析时间轴、母版 cfg、场景文本，并检查母版视频/字幕/封面/时间轴四件存在；
  第二趟才统一写盘。任何缺失都在写盘前失败，避免留下半套新发布包。
- `writeRelease` 对小红书先拦：标题 ≤20 字、正文 ≤1000 字、标题/正文不含站外地址、必须有 collection/topics/repro/pinned；
  违反直接 throw。抖音/B站写标题、简介、标签、时间轴等字段。
- 发布包只是**文案与文件路径**；平台动作、置顶评论、合集选择仍由 release skill 与人工执行。

### 3.4 数字证据

- `numbers` 把两平台 `pick`/`set`/`narration` 覆写后的所有上屏字段展平，逐 token 对照 `video/research/<id>-numbers.json`。
- evidence 键与 token 做单位/逗号/下划线/大小写归一化；行号等非实测值必须在 `exceptions` 显式说明。
- 缺 evidence 文件本身是失败（不是跳过）；`numbers` 不接受任何 flag。

## 4. 校验与错误矩阵

| 事件 | 结果 |
|---|---|
| 未知子命令 | `未知子命令 "…"，可用：lint / check / cover / pack / build / numbers / calib` |
| `--k=v` 写错被当布尔量 | 解析器专门支持 `--k=v`；仍写错会得到缺值/未知参数错误 |
| `check` 缺 `timeline.json` | 打印 `⏭️ … 还没有时间轴，跳过（check 不合成配音）`，`exit 0`；**不是通过** |
| `check` 版式失败 | 逐条打印并以 1 退出；轮询继续检查其它平台 |
| `cover` 某张装不下 | 该张报错、继续其它张，最终 `exit 1`；`fitCover` 的"装不下就 throw"是护栏 |
| `pack` 缺母版/字幕/封面/时间轴 | 在写盘前 throw，点名 `id/platform: 缺…` |
| `pack` 的 `publish` 为空/未知平台 | `没有 publish` / `未知平台 "…"` |
| 小红书标题 >20 / 正文 >1000 / 站外地址 / 缺合集/话题/复现 | `writeRelease` 直接 throw |
| `build` 成片不在 `targetSec` | throw，不产出发布包 |
| `build` SFX 事件数 ≠ 节拍数 | throw |
| `build` 帧时长与成片偏差 > 1/fps | throw |
| v2 `build` 缺任一封面 | throw，提示先跑 `video:build`（或 `video:cover`） |
| `numbers` 缺 evidence / 未命中 | 缺文件或 `N 个数字未命中`，非零退出 |
| `numbers` 带 flag | `numbers 不认识参数 …（只接受 episode id）` |

## 5. 正常、边界与失败案例

- 正常：新集 `video:lint` → 补 `research/<id>-numbers.json` → `video:numbers` → `video:build` → `video:check` → `video:pack`。
- 边界：只改封面文案：`video:cover --out .temp/spec-covers/` 出候选，人检后再覆盖正式文件；不要直接改 `out/` 里排队资产的半成品。
- 边界：只改发布文案：`video:pack` 不重渲；但母版/封面/时间轴缺失会整批失败，先补齐再跑。
- 边界：`check` 的 `跳过` 计数必须是 0 才算全量通过；单个平台缺时间轴时 exit 0 是工具契约，不是验收结论。
- 失败：在 `video:cover` 默认命令里期待四张封面齐活。默认只有 B站/抖音；四平台要逐平台指定，或走 v2 `build` 的统一出图。
- 失败：把 `pack` 当成"跨平台原子写入"的保证。它只保证在写盘前完成全部预检；磁盘写入中途失败仍可能留下部分文件。
- 失败：在 `episode.json` 写 `publish.weibo` 期待 `pack` 兼容。`PACK_MAP` 只认四个平台，未知平台直接 throw。

## 6. 测试与断言

| 文件 | 已覆盖 |
|---|---|
| `video/tests/spec-v2.test.mjs` | v2 schema：sections、voice、beatMap、emphasis、ttsText/ttsLexicon、v1 不受影响 |
| `video/tests/layout-v1.test.mjs` / `layout-v2.test.mjs` | v1 夹具逐字节、v2 DOM/版式 |
| `video/tests/package-covers.test.mjs` | `COVER_SIZES` 四档、v2/v1 封面 HTML、`packJobs` 母版映射与未知平台、真浏览器四张出图 + contact sheet + 4:3 拷贝 |
| `video/tests/numbers.test.mjs` | token 归一化、evidence 命中、exceptions 放行、`cmdNumbers` 行为 |
| `video/tests/mux-filter.test.mjs` | v1/v2 音频滤镜串 |
| `video/tests/sfx.test.mjs` / `timeline-beats.test.mjs` | 节拍/SFX 事件与静止门 |
| `video/tests/xhs-release.test.mjs` | 小红书标题/正文/合集/话题/置顶约束 |
| `video/tests/repost-gates.test.mjs` / `repost-archive.test.mjs` | 投放门与归档（发布边界） |

未覆盖：`video:check` 对真实 Chromium 字体的判定依环境；`video:build` 的整集渲染没有单测。改这两处必须本机跑目标集并记录输出。

## 7. 错误与正确做法

- 错误：`video:test -- <file>` 当单文件模式。正确：`node --test video/tests/<file>.test.mjs`；npm 脚本自带 glob 会跑全套。
- 错误：看到 `check` 的 `⏭️ 跳过` 就认为通过。正确：跳过 = 没验；先 `build` 出 timeline，再要求跳过计数 0。
- 错误：为了赶发布直接 `video:build` 已发布的集。正确：已发布集只跑 `check`/`cover`/`pack`；`build` 会重渲并覆盖 `out/`。
- 错误：把知乎/小红书封面塞进抖音模板裁切。正确：按 `COVER_SIZES` 各排一版；小红书 4:3 不能裁 3:4。
- 错误：缺 `research/<id>-numbers.json` 时删掉数字或放宽 `numbers`。正确：补证据或显式 `exceptions` 定性。
- 错误：把 `pack` 成功当成平台已发布。正确：`pack` 只写本地发布包；平台动作另走 release skill。
