# v2 母版全量审计（18 集 × 2 平台）

日期：2026-10-29 · 分支：feat/video-v2-remaster · 任务：Task 15

## 结论

36 个 v2 母版全部通过技术审计与排版审计，四尺寸封面与四份发布包齐全，18 集 numbers 0 未命中，`series.json` 的 `masters` 已与实测时长对齐，校验和已冻结。按 Task 15 Step 8，进入投放（Task 16/18）需要用户明确批准。

## 范围

- 计入：c2-pointer、c3-volatile、c4-struct-abi、c5-func-pointer、c6-abi-stack、c7-ub、f0-why-rtos、f2-context-switch、f3-scheduler、f5-sem-mutex、f6-timers、p4-iram、s14-pwr、s16-hardfault、s2-rcc、s4-nvic、s5-systick、s7-usart-baud。
- 不计入：c3b-volatile（仅 douyin 为 v2，bilibili 保持 v1，排版审计按 v1 口径通过）、ai4fw（v1 遗留集，无 `voice`/`platforms` 字段，不属于本轮换新范围）。

## Step 1：lint / check

- 作用域 lint（18 集）：18/18 通过，日志 `.temp/v2-final-audit/lint18.log`。
- 作用域 check（18 集 + c3b-volatile）：**37 条「排版审计通过」，0 条「还没有时间轴，跳过」，0 条失败**，日志 `.temp/v2-final-audit/check19.log`。
- 例外：不带参数的 `npm run video:lint` / `video:check` 会在 ai4fw 的 v1 校验处中止（缺 `voice`、`platforms`、`cover.line1`），因此以作用域命令为准；该集不在投放范围，不做改动。

## Step 2：numbers

18 集全部通过，0 未命中，合计 1,431 个数字：

| 集 | 数字 | 集 | 数字 | 集 | 数字 |
|---|---|---|---|---|---|
| c2-pointer | 30 | c3-volatile | 30 | c4-struct-abi | 36 |
| c5-func-pointer | 30 | c6-abi-stack | 23 | c7-ub | 24 |
| f0-why-rtos | 73 | f2-context-switch | 52 | f3-scheduler | 62 |
| f5-sem-mutex | 86 | f6-timers | 86 | p4-iram | 78 |
| s14-pwr | 153 | s16-hardfault | 96 | s2-rcc | 196 |
| s4-nvic | 136 | s5-systick | 89 | s7-usart-baud | 151 |

中文数字盲区（numbers 只审 ASCII 数字）另用 `.temp/cn-audit.mjs` 全量扫了一遍：候选均为口语省略（「九十二万一千六」= 921600）、十六进制逐位读法（「五零」= 0x50）或解析器伪影，**0 个新增事实错误**，日志 `.temp/v2-final-audit/cn-audit.log`。

## Step 3：母版技术审计

36/36：时长在 `targetSec` 内、LUFS 在 -14±1、音频 aac/44100/2ch、sha256 唯一且可复算、字节数一致。总字节 986,474,772（940.8 MB），LUFS 区间 -15.0 ~ -14.7。

完整 11 列表格（含完整 sha256 与字节数）：`.temp/v2-final-audit/masters.tsv`。

| 集 | 平台 | 时长 | LUFS | 字节 | sha256 |
|---|---|---|---|---|---|
| c2-pointer | bilibili | 10:19 | -15.0 | 43.5 MB | `3f90dd710cac…` |
| c2-pointer | douyin | 1:08 | -14.8 | 6.3 MB | `f39ad7afffb5…` |
| c3-volatile | bilibili | 10:43 | -15.0 | 47.1 MB | `ac611f55a586…` |
| c3-volatile | douyin | 0:52 | -14.9 | 6.0 MB | `7f6def91696d…` |
| c4-struct-abi | bilibili | 11:24 | -14.9 | 49.4 MB | `4d5aa017b256…` |
| c4-struct-abi | douyin | 0:59 | -15.0 | 6.0 MB | `657d1f6e0f20…` |
| c5-func-pointer | bilibili | 10:52 | -14.9 | 47.4 MB | `89ef23cfb8c3…` |
| c5-func-pointer | douyin | 0:58 | -14.9 | 6.3 MB | `fbe48ee6a03b…` |
| c6-abi-stack | bilibili | 10:20 | -15.0 | 44.3 MB | `a4d89a41c4a6…` |
| c6-abi-stack | douyin | 0:58 | -14.8 | 5.8 MB | `687a250feeea…` |
| c7-ub | bilibili | 10:43 | -15.0 | 45.2 MB | `bc7c6fa324e0…` |
| c7-ub | douyin | 1:02 | -14.8 | 6.0 MB | `d717515e394a…` |
| f0-why-rtos | bilibili | 10:17 | -15.0 | 44.8 MB | `d457ed3cbe2f…` |
| f0-why-rtos | douyin | 0:25 | -14.8 | 3.0 MB | `a27aaaeda3ac…` |
| f2-context-switch | bilibili | 10:10 | -15.0 | 44.2 MB | `91bf5db7f54d…` |
| f2-context-switch | douyin | 1:00 | -14.8 | 5.5 MB | `6033a622b83a…` |
| f3-scheduler | bilibili | 11:19 | -14.9 | 48.0 MB | `3660331f2faa…` |
| f3-scheduler | douyin | 0:48 | -14.7 | 5.4 MB | `23e5a637ce89…` |
| f5-sem-mutex | bilibili | 11:11 | -14.9 | 47.4 MB | `15f92e025dc3…` |
| f5-sem-mutex | douyin | 0:57 | -14.7 | 5.6 MB | `55066addca09…` |
| f6-timers | bilibili | 10:46 | -14.9 | 46.0 MB | `e29713629132…` |
| f6-timers | douyin | 0:51 | -14.8 | 5.4 MB | `f67ee1f41a85…` |
| p4-iram | bilibili | 10:29 | -15.0 | 44.4 MB | `ebeee80371f1…` |
| p4-iram | douyin | 0:59 | -14.8 | 5.4 MB | `a971ba98fe47…` |
| s14-pwr | bilibili | 10:21 | -15.0 | 45.5 MB | `cd5554753548…` |
| s14-pwr | douyin | 0:54 | -14.8 | 5.6 MB | `b1436cec60e0…` |
| s16-hardfault | bilibili | 10:30 | -14.9 | 47.0 MB | `6642114a71a9…` |
| s16-hardfault | douyin | 1:05 | -14.8 | 6.9 MB | `528b3f3bd0c3…` |
| s2-rcc | bilibili | 11:13 | -14.9 | 49.3 MB | `f48adf87c073…` |
| s2-rcc | douyin | 1:02 | -14.9 | 6.2 MB | `8f6a1aa4c933…` |
| s4-nvic | bilibili | 11:47 | -15.0 | 50.5 MB | `b08e76e22d21…` |
| s4-nvic | douyin | 1:03 | -14.9 | 5.9 MB | `a713b4ebc3d9…` |
| s5-systick | bilibili | 10:53 | -14.8 | 45.6 MB | `b897951b0cab…` |
| s5-systick | douyin | 1:01 | -14.8 | 5.6 MB | `b2d942508e09…` |
| s7-usart-baud | bilibili | 11:08 | -14.9 | 48.2 MB | `1e26856913f4…` |
| s7-usart-baud | douyin | 1:09 | -14.9 | 6.0 MB | `5c738f992cb7…` |

音画漂移在构建时逐集实测，全部 ≤ 658 µs（30fps 一帧为 33,333 µs）。

## Step 4：封面与发布包

18 集 × 10 项全部齐全，`ALL PACK OK`（`.temp/v2-final-audit/audit-pack.mjs` 实测宽高）：

- `bilibili-cover.png` 1920×1200、`douyin-cover.png` 1080×1440、`zhihu-cover.png` 1920×1080、`xiaohongshu-cover.png` 1440×1080、`douyin-cover-1440x1080.png` 1440×1080、`cover-contact-336.png`。
- `发布-bilibili.md` / `发布-douyin.md` / `发布-zhihu.md` / `发布-xiaohongshu.md` 各 18 份。

## Step 5：旧/新并排抽帧

18 集 × 2 平台 × 5/50/95% 共 108 张，路径 `video/out/_v2-compare/<ep>/<platform>-{5,50,95}.png`（左旧右新）。逐集看过开场/中段/结尾，未发现 v2 把内容切掉；v2 侧多出的 HUD 骨架、章节/场景元信息、代码行注视、信息图均为设计升级。

口径说明：v2 的 `sub`/`url` 属于 tail 目标，在场景末拍才揭示——旧版是静态常显，所以 95% 对比帧偶见「新版少一行」，那是揭示时序而非裁切；抽帧落在场景首帧时也会偏暗（0.27s 淡入），不是缺陷。

## Step 6：series.json

18 条 `masters` 已按实测时长更新，`MM:SS` 口径与既有条目一致；diff 仅 18 行（每条 ±1 行），无其它字段变化。

## Step 7：冻结

- 清单：`.temp/v2-final-audit/SHA256SUMS`（275 个文件：78 个 mp4、123 张封面、74 份发布包；含中间产物 `<platform>/video.mp4`、c3b 与 ai4fw 的旧产物）。
- 校验命令（清单是相对 `video/out` 的路径，必须在那个目录里校验）：

```bash
cd video/out && sha256sum -c ../../.temp/v2-final-audit/SHA256SUMS --quiet && echo frozen
```

结果为 `frozen`。

## 本轮例外与修正

1. **Wave B 五集补建**：f2-context-switch、f3-scheduler、f5-sem-mutex、f6-timers、p4-iram 此前只有 v2 `episode.json`，时间轴与母版仍停在 10/12–16 的 v1。本轮全部重跑 v2 构建，并各自补齐封面、contact sheet 与知乎/小红书发布包。
2. **f3 douyin 标题孤字**：`tick-04` 竖版标题「只查\n队首」末行仅 2 字，改为「为什么\n只查队首」后只重渲 douyin；bilibili 母版不受影响。
3. **s5-systick 补包**：此前缺知乎/小红书发布包，`video:pack` 重生成。
4. **全量命令阻断**：见 Step 1 的 ai4fw 例外。
5. **Step 6 脚本口径**：计划中的 `HH:MM` 写法会覆盖既有 `MM:SS` 约定，且整文件 `JSON.stringify` 会把内联 `anims` 数组展开成多行；实际改为逐行替换 masters 文本，diff 只含 18 条 masters。
6. **Step 7 校验目录**：计划里的 `cd -` 回仓库根再校验会全部报缺失，已按清单相对路径在 `video/out` 内校验。

## 产物索引

- 母版：`video/out/<ep>/bilibili.mp4`、`video/out/<ep>/douyin.mp4`
- 技术审计：`.temp/v2-final-audit/masters.tsv`、`masters-audit.log`
- 排版审计：`.temp/v2-final-audit/check19.log`（37/0）
- 数字审计：`.temp/v2-final-audit/numbers.log`、`cn-audit.log`
- 产物齐全度：`.temp/v2-final-audit/audit-pack.mjs`（ALL PACK OK）
- 对比图：`video/out/_v2-compare/`
- 冻结清单：`.temp/v2-final-audit/SHA256SUMS`
