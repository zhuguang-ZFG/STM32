# 第 18 集 S5 SysTick：从取证复核到两平台成片

## Goal

把 `docs/stm32/05-systick.md` 做成第 18 集：B站 16:9 完整版 + 抖音 9:16 短版，
屏上每一个数都能由观众在本机 `sh probe.sh` 复现。选题于 2026-10-17 定档，
已写进 `video/series.json` 的 `next`。

## Why This Chapter

- 先修 S4（NVIC/EXTI）已投，S4→S5 是这条线上第一条不断链的顺接；
- 接住刚投完的 FreeRTOS 弧欠下的那句：F3 调度器靠 tick 走，tick 到底谁给的；
- 本集全部取证不需要开发板——这是当前 80 章里少数几条「今天这台机器就能拍全」的。

## Requirements

- 唯一事实源：`video/episodes/s5-systick/episode.json`（`id: s5-systick`、`badge: S5`、`no: 18`），
  产线六阶段顺序固定 `lint → tts → timeline → stage → mux → package`，入口是
  `npm run video:lint / video:check / video:build -- s5-systick`。
- 屏上数字一律取本机实跑（`video/series.json` 的 `format.rule`）。已验证前提：
  2026-10-17 本跑 `code/stm32/05-systick/probe.sh` → **宿主断言 42/42 全绿**，
  交叉段 `arm-none-eabi-gcc 10.3.1` 出 `probe-arm.o`（text 3297 / data 0 / bss 8），
  机身可见 `movw r2,#16799`、`movw r1,#22783`、`movw r6,#6000`。
- 交叉编译那一段要求 `arm-none-eabi-gcc` 在 PATH；没进 PATH 时脚本只跑宿主段，
  屏上就不许出现目标文件里的常数（读不到就是没有，不许从旧日志里搬）。
- 钩子候选（都已在本次实跑里读到具体值，不是推算）：
  1. COUNTFLAG 读清——周期到后第一次读 CTRL=`0x00010005`、第二次=`0x00000005`；
     5 个周期里单读法数到 5 次、「先偷看再查」双读法数到 **0 次**，延时死等（probe [7]）；
  2. 忘减一的代价不在次数在相位——同跑 1680000 周期两边都重载 10 次，
     但每 tick 慢 1/168000（5.95ppm）、**日漂移 514ms**（probe [3]）；
  3. 24 位上限装不下 100ms——`SysTick_Config` 返回 1 拒配；强行 `&0xFFFFFF` 得 LOAD=22783，
     tick 变 135.6µs、**ISR 快 737 倍**（probe [4]）；
  4. `SysTick_Config(168000)` → LOAD=167999 / VAL=0 / CTRL=0x00000007 / SHP[11]=0xF0
     即逻辑优先级 15，正好接 S4 那套优先级账（probe [6]）。
- 竖版短版按 F5 那条集的先例独立重排（钩子前置、每幕一句、金句收尾），不是横版缩放；
  横版图动画进竖屏前先量等比缩放后标题与字幕挤不挤得下。
- 发布稿由产线 `writeRelease` 生成，投放走 `video-release` 技能那**四**条线（B站/抖音/知乎/小红书——2026-10-17 小红书开线，
  原文写的"三条"已过期），本任务不出投放动作。

## 硬约束

- **文档「实物实验」那两节（逻辑分析仪测 PF6 的 500ms±0.1%、调试器 watch 触发双读坑）需要上板，
  当前板子不在位。** 没有本集实拍的串口/逻辑分析仪留档，就不许把 ±0.1% 这类数当实测放上屏，
  也不许拿理论周期冒充测量值；要么整段不拍，要么标成「这一步要板子，屏上给的是命令而不是数」。
- 已发布的 18 条成片与发布稿不许回炉：本任务不得改动 `video/out/` 既有目录与 `video/episodes/` 既有集。
- **渲染顺序**：`video:build` 要排在 `10-16-video-layout-header-fill` 落地之后。
  那两条版式改造（常驻页头带小节信息、内容块纵向铺满）只对未发布新集生效，
  S5 是第一个载体；先渲后改就等于改版再拖一轮。
  排版审计（越界/裁切/压字幕/相叠/字号/顶穿/孤字）必须在改版后的版式上跑到 0。
- 片尾 CTA（2026-10-17 复核已定）：**转本集的复现路径**——收在「本机一条命令、42/42」，
  不接 F5 那句板子悬念（那条悬念留在平台侧的置顶评论里导流，不进成片）。
  无论怎么措辞，都不许在 CTA 里把 E04 的模型值说成已有实测。
- 标题体例（同次复核已定）：品牌线是 `series.json` 的 `series`＝「通往单片机之路」，系列身份由**合集**承载
  （抖音合集名就取这个字段；小红书那条合集是「STM32 零基础自学」）。所以四平台标题**继续走句子钩子、不带编号**，
  与已投 17 集同口径。

## Acceptance Criteria

- [x] `video/episodes/s5-systick/episode.json` 存在，~~`no: 18`~~、`badge: S5` ✓，
      ~~每场 `kicker` 带小节信息~~ → **这条 AC 的两处写法按实际契约改判**（2026-10-17 收口时核对产线）：
      ① `no: 18` 归 `video/series.json` 的条目，episode.json 顶层没有这个字段（18 集实测 `no` 0 处，design §2 已钉）；
      ② 页头的小节信息不吃"每场 kicker"，吃的是 `platforms.<平台>.sections[]` + `at` 锚点
      （`spec.mjs:sceneSections()` 算，`layout.mjs:479` 写成 `第 i/n 节 · title`）。
      实测：横版 6 节 / 竖版 5 节，`badge` = `S5`，`.temp/s5-header-probe.mjs` 逐场验过（见下条）。
- [x] `npm run video:lint -- s5-systick` 通过（`✅ 通过：bilibili 28 场，douyin 12 场`），
      且全量 19 集绿（跨集话题/首行查重只有全量才生效）；
      `video:check` 排版审计全 0——本集两平台 `28 场 / 12 场` 各八项 0，
      全量 37 个平台审计 `🔍 排版审计通过` 37 条、`跳过` 0 条、exit 0。
      最小字号横版 21.1px、竖版 26.9px，都在 `MIN_FONT=16` 之上；字幕字族真解析到 Microsoft YaHei，无「字体审计降级」。
- [x] 两平台成片时长落在 `targetSec` 区间内：bilibili **629.167s**（10:29，目标 480–720）、
      douyin **67.933s**（01:07，目标 45–75）；两版都是 h264(High)/yuv420p/**30fps** + **aac/44100Hz/2ch**；
      实测响度 **-15.0 / -15.0 LUFS**（真峰值 -0.9 / -1.4 dBTP），与 F5 的 -15.0/-15.1 同口径。
      页头两条版式实测（本集是 `sections` 的首个真集）：横版 `.secchip` 逐场推进到「第 6/6 节 · Config 与优先级」、
      `.ticks` 可见且同屏只 1 根进度杠；竖版 `.secbar` `display:flex`、段数 = 5、`cur` 跟着节走、
      `.ticks` `display:none`；40 场 DOM 文案与 `sceneSections()` 逐场一致，0 处不符。
- [x] 屏上每个具体数都能在本次 `probe.sh` 输出里逐字找到：`.temp/s5-numbers.mjs` 把两平台 188 个上屏字段
      （含 douyin `pick`/`set`/`narration` 覆写）的数字 token 全量回对 `probe-20261017-1705.md`，
      未命中 15 个逐个定性为「源码行号 / 头文件原文写法 / 同值短写法」且都带明示；
      deny 表 15 项在终稿上以读数身份命中 **0**（`±0.1%` 那个需要板子的百分数整段不上屏，
      由 `card-07` 明说「板子上那两个数，今天不上屏」）。结论列见 `research/whitelist-20261017.md` 第四节。
- [x] `video/series.json` 的 `episodes` 补第 18 条（现 19 条）、`next` 清空为 `[]`、`backlog` 4 条不动；
      `git diff` 只有「新增那 15 行」+「删掉 next 那 3 行」，既有 18 条一字段未动；
      `series` 实测值 `"通往单片机之路"` **无尾空格**（`10-16-bili-season-after-unlock` 那条说法已过期）。
      顺序上登记排在渲染之后：`douyin-release.mjs:69` 对没渲过的条目硬 throw，而 `video:build` 不读 `series.json`。
- [x] 既有 `video/out/*` 与既有发布稿的 md5 与开工前一致：
      `md5sum -c research/out-md5-20261017-1300.txt` → **exit 0**（1220 项，零失败输出）。
      本任务全程只对 `s5-systick` 跑过 `video:build`，⛔ 那条没破。


## Notes

- 交叉工具链 PATH 例：`/d/zhugu-home/tools/armgcc/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin`
  （probe.sh 头部注释里写的那条），本次实跑用的是 10.3.1。
- `code/**/build/` 与 `.trellis/ref/` 都在 `.gitignore` 里：屏上引用产物只能给命令 + 现场读数，不能给站内链接。
- 站内这一章有现成动画 `/anim/systick-tick.svg`（倒数与 COUNTFLAG），与 F5 那两张横图的竖屏问题同一类，用前量一次。

## 归档后核对（2026-10-17 深夜补记）

归档前只有 AC 全勾 + grep 结论；这里补上"目标已完成"的实物证据（避免仅凭清单误退）：

- 两份成片在位：`video/out/s5-systick/bilibili.mp4` **629.1667s**（ffprobe 实测，目标 480–720）、
  `douyin.mp4` **67.9333s**（目标 45–75）；封面、srt、发布稿同目录。
- B站：`.temp/bili-web-run/s5-systick.bvid` = **`BV1uEJi6vEnc`**（与 commit `a26d3a4` 记的一致）。
- 抖音：`.temp/douyin-run/s5-systick-published.txt` 在位（回读 `status_code=0` + 作品管理 URL）。
- 小红书（本任务之后开的那条线）：已发布 + 已挂合集「通往单片机之路」（见 10-17-xhs-series-collection/upload）。
- 结论：目标「两平台成片」已达成，归档维持。
