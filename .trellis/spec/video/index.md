# video 规范索引

`video/` 这条线：`episodes/*.json` → `src/{spec,layout,stage,cli}.mjs` → `out/<id>/<platform>/` → `publish/` 四平台投放（B站/抖音/知乎/小红书）。
投放侧的台账与不可逆点在 `.agents/skills/video-release/SKILL.md`，本目录只管"怎么改才不弄坏已发布的那些集"。

| 文件 | 内容 |
|---|---|
| [layout-contract.md](layout-contract.md) | 常驻页头 `sections` 契约、按场进度唯一性、纵向填充的两条杠杆与"填充比当不了闸"的实测依据、`video:check` 回归口径 |
| [v2-contract.md](v2-contract.md) | `formatVersion: 2` 的 schema、节拍/相位、状态键、v1 兼容线；改 `spec/timeline/layout/stage/render/tts` 前必读 |
| [build-package-contract.md](build-package-contract.md) | lint/check/cover/pack/build/numbers/calib 的签名、产物、读写副作用、四平台封面与母版映射、错误矩阵 |

## 动手前必读

- 改 `video/src/`：先看 [v2-contract.md](v2-contract.md) 的 `formatVersion` 语义与 v1 兼容线；`formatVersion`、节拍、相位、状态键四处不许各写一套。
- 改 `episode.json`：先跑 `npm run video:lint`。v2 集的 `sections`/`beatMap`/`emphasis` 判据以 `spec.mjs` 为准，不在文档里另立规则。
- 改封面或发布包：读 [build-package-contract.md](build-package-contract.md)。`cover` 会写文件，`pack` 会重排发布包，`build` 会重新产生音视频；`lint`/`numbers`/`check` 不写成片。
- 要动平台"准备/发布/删除"：进入 `.agents/skills/video-release/SKILL.md` 与其台账流程；本目录的命令不能授权任何平台动作。

## 快速命令

```bash
npm run video:lint                                   # 全量 episode.json 契约校验（只读）
npm run video:check -- <id> --platform <p>           # 舞台 + 排版审计（不渲帧、不写 out/；缺 timeline 会跳过并 exit 0）
npm run video:cover -- <id> [--platform <p>] [--out <dir>] [--variant vs|panel]
                                                     # 只重画封面；--out 把候选写到隔离目录
npm run video:pack -- <id>                           # 只重排发布包，不重渲；缺母版/封面/时间轴直接 throw
npm run video:build -- <id> [--platform …] [--stills] [--force-audio] [--no-bgm] [--variant …]
                                                     # 会渲帧写 out/：只对未发布集用
npm run video:numbers -- <id>                        # 上屏数字与 research/<id>-numbers.json 对账
npm run video:calib -- --anims a,b                   # seek 门限双向标定（改过 stage.mjs 常量后跑）
```

单文件测试不要用 `npm run video:test -- <file>`：npm 脚本本身带
`node --test "video/tests/**/*.test.mjs"` 的 glob，追加文件只会把全套再跑一遍。单文件用
`node --test video/tests/spec-v2.test.mjs`，全量仍用 `npm run video:test`。

## 四平台封面与母版（当前实现）

- `buildCover` 的四档尺寸来自 `package.mjs` 的 `COVER_SIZES`：B站 1920×1200、抖音 1080×1440、知乎 1920×1080、小红书 1440×1080。
- `formatVersion: 2` 的 `video:build` 在进入平台循环前一次出齐四张封面 + `cover-contact-336.png`，并把小红书 4:3 复制成 `douyin-cover-1440x1080.png`；`buildOne` 只断言四张存在，避免第二个平台把第一张覆盖成另一套文案。
- v1 集仍按平台各出一张 `<platform>-cover.png`。知乎/小红书是派生投放平台：`pack` 用 `PACK_MAP` 复用 B站横版与抖音竖版母版，只重排各自封面，不重渲。
- 封面候选统一写到 `--out .temp/spec-covers/` 之类的隔离目录；不要把半成品写进 `video/out/`，那里正被投稿队列读取。

## 三处顺序闸（都是跑出来的，不是推的）

1. **`lint → build → check`，不能反。** 新集在没有 `video/out/<id>/<平台>/timeline.json` 时跑 `video:check`，
   `cli.mjs` 打 `⏭️ … 还没有时间轴，跳过（check 不合成配音）` 并 **exit 0**。那叫假绿：看到 `跳过` 就是没跑。
   全量 check 的期望值是「`🔍 排版审计通过` 的行数 = 目标集里实际声明且已有时间轴的平台数」，且 `跳过` 计数 **0**。
   不要写死某个历史平台总数：2026-10 的样本是 19 集 37 个平台配置，2026-11-05 当前是 20 个 episode 目录（18 个 v2 + 2 个 v1，`ai4fw` 无常驻 `platforms` 配置），新增/变体集后必须重算。
   2026-11-05 实跑 `video:lint` 的基线是 19/20 通过：`ai4fw` 报缺 `voice`/`platforms`/`cover.line1`（存量内容缺口，不是规范改动）；
   补齐前不得把"lint 全绿"写成当前事实。
2. **`series.json` 登记排在 `video:build` 之后。** `publish/douyin-release.mjs` 对片单里每个条目硬取
   `video/out/<id>/douyin/timeline.json`，缺了就 throw「这条还没渲过，别造文案」——先登记会让那份清单生成器整支红。
   反过来 `video:build` 全程不读 `series.json`（`src/` 里只有 `package.mjs` 那句文案提到它），
   `bili-ledger.mjs` 也自带「没有横版 master 就归 noMaster、不算漏投」的分支。渲完再登记还有一好处：
   `masters` 直接写实测时长，不落脚本占位符。
3. **时长不许贴着 `targetSec` 上沿写。** `lint` 用 `SEC_PER_CHAR` 估（bilibili 0.1955 s/字、
   douyin 0.1946 s/字 + 1.091 s/场），`build` 拿**实际秒数**过硬门；两者之间有一族实测离散度：
   2026-10 的 17 集 × 双平台样本里 `act/est` 落在 **bilibili 0.951–1.049 / douyin 0.947–1.060**
   （复算脚本读 `video/out/*/*/timeline.json` 与实际 duration 对比）。这是历史样本，不是当前门禁值；
   判据本身不变：**`est × 该平台上沿比值 ≤ targetSec[1]`**，超了就裁旁白，不放宽阈值、不砍场。
   S5 就是这么落地的：横版 3545 字（est 693.0s）裁 23 处到 3382 字、竖版 312 字裁 3 处到 279 字，
   成片实测 629.167s / 67.933s，`act/est` = 0.951 / 1.008。

## 金样例

- 页头分节夹具：`.trellis/tasks/archive/2026-10/10-16-video-layout-header-fill/research/f5-sections.json`（测量夹具，故意不进 `episodes/`）
- 版式改版的完整证据链：`.trellis/tasks/archive/2026-10/10-16-video-layout-header-fill/research/baseline-20261017.md`
- **`sections` 的第一个真集**：`video/episodes/s5-systick/episode.json`（横版 6 节 / 竖版另配 5 节，两平台各一份边界表）
- 屏上数字对账的写法：`video/research/<id>-numbers.json`（把两平台含 `pick`/`set`/`narration` 覆写的所有上屏字段展平，
  逐 token 回本机 probe 留档找；未命中的必须逐个定性成"行号 / 原文写法 / 同值短写法"并带明示）

## 质量检查

- 改 schema/版式/封面：`npm run video:test`；单文件用 `node --test <file>`。
- 改 episode 配置：`npm run video:lint`。
- 改上屏数字：`npm run video:numbers -- <id>`；缺 `research/<id>-numbers.json` 本身就是失败。
- 改版式/页头：`npm run video:check -- <id> --platform <p>`；只对已有 timeline 的集有效，`跳过` 不算通过。
- 改封面/发布包：`npm run video:cover` / `npm run video:pack`，并核对 `发布-*.md` 里的母版与封面路径；平台动作另走 release skill。
