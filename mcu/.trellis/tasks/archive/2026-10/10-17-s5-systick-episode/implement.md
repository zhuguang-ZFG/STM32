# 执行计划：第 18 集 S5 SysTick

顺序是硬的：**先立护栏 → 先取证再写字 → 横版 → 竖版 → 发布文案 → 才渲**。
每步的验证命令直接可跑；标 ⛔ 的是**不过就不许往下走**的闸。设计依据见同目录 `design.md`（§x 指向它的节）。

## 0. 前置确认（三件没定就不许动 `video/episodes/`）

- [x] 版式改版任务已落地：`10-16-video-layout-header-fill` 已归档，`spec.mjs:72 SECTION_TITLE_MAX=12` 与
      `validateSections` 在位、`layout.mjs` 的 `.secchip`/`.secbar` 在位。——S5 是这套新页头的第一个观众，顺序反了就白渲一版。
- [x] `design.md` §10 那三件开放决策**已点头**（2026-10-17 复核）：CTA 转本集复现路径 / 竖版动画先量再定 /
      标题走句子钩子不带编号（「不是通往单片机之路吗」）。原文与依据记在 design §10，脚本与写稿都不再猜这三件。
- [x] `video:lint` 当前全绿（18 集），作为改动前的基线：**没单独留"改前"那一份**——补记等价证据：加完 s5 后那次全量
      `npm run video:lint`（2026-10-17，19 集）里既有 18 集逐集 `✅ 通过`、末行 `✅ 全部通过`，
      说明这一集写进去没碰坏任何旧集（跨集判据也在同一次跑里生效）。

## 1. 护栏（改任何东西之前）

- [x] 既有产物清单：**没有新拍**，直接复用上一任务 13:00 那份 1220 项清单
      （拷成 `research/out-md5-20261017-1300.txt`），`md5sum -c` → **exit 0**。
      这比新拍一份强：它同时证明"自版式任务收尾至今 `video/out/` 一字节未动"，中间没有任何一步偷偷重渲过。
- [x] 参照审计输出留档：`npm run video:check -- f5-sem-mutex > research/check-before-f5.txt 2>&1` → **exit 0**，
      末行 `🔍 排版审计通过：12 场，越界/裁切/压字幕/版式相叠/字号不可读/顶穿容器/标题孤字/进度杠重复 0` + `✅ 全部通过`，
      全文 `跳过` 计数 **0**（两平台 35 + 12 场真跑了）。这条只为证明旧集现在仍全绿，S5 不拿它当闸。
- [ ] ⛔ 本任务全程禁止对既有 17 个 id 跑 `video:build`。`video:check` 允许（它不写 `video/out/`）。

## 2. 当天取证（屏上数字的唯一来源）

- [x] 工具链确认在 PATH：`/c/Users/zhugu/tools/gcc-arm-none-eabi-10.3-2021.10/bin/arm-none-eabi-gcc`（10.3.1，
      与 12:10 那次同版本）→ **交叉段可拍**，`code-11` 保留。
- [x] 重跑并留档：`sh probe.sh` → **exit=0**，落 `research/probe-20261017-1705.md`（`HOST_ASSERTS=42`、`断言通过 42/42` 都在文件里）。
      与 12:10 那份**换行归一后逐字相同**；唯一差异是旧文件末尾那行 `EXIT=0` 不在脚本输出里（`grep EXIT probe.sh` 无命中），
      是上次手工抄的回执，不是读数。
- [x] 上屏白名单：`research/whitelist-20261017.md`。allow 35 项逐个 `grep -c` **全部命中**；
      deny 15 项（`4294966796`、`3000`、`335999`、`168001`、`22784`、`86400000`、`2^32`、`16777216`、`5000ns`、
      `HCLK/8`/`约 800ms`、`__NVIC_PRIO_BITS`/`SysTick_IRQn`、`bit0..bit16`、`SCS_BASE+0x0010`、`±0.1%`）
      **命中数全为 0**，每条都写了处置（删 / 改推导句式 / 标"头文件里写的"）。
- [x] 陈旧产物：`build/probe_host.exe`（10-07 02:20，现在的脚本产出 `probe.exe`）**挪到** `.temp/s5-stale-probe_host.exe`（没删），
      `build/` 现在只剩 `probe.exe` 与 `probe-arm.o`，录屏 `ls build/` 不会多出一个文件。

## 3. episode.json 骨架（先让 lint 认这个集）

- [x] 建 `video/episodes/s5-systick/episode.json`：顶层 `id:"s5-systick"`（与目录名逐字相同）、`badge:"S5"`、
      `title`、`voice`（沿用 F5 的 `zh-CN-YunxiNeural`）、`rate:"+4%"`、`fps:30`、`sampleRate:44100`、`channels:2`、
      `cover.line1`、`platforms`、`publish`。⛔ 顶层**不写** `no`（`no:18` 属于 `series.json`）。
      ——实测：顶层只有 id/title/badge/voice/rate/fps/sampleRate/channels/cover/platforms/publish 十项，`no` 缺席。
- [x] `platforms.bilibili`：`size:[1920,1080]`、`targetSec:[480,720]`、`scenes:[]`；
      `platforms.douyin`：`size:[1080,1920]`、`targetSec:[45,75]`、`reuseFrom:"bilibili"`、`pick:[]`、`set:{}`、`narration:{}`。
      ——实测：两平台 size/targetSec 与上面逐字一致；douyin 走 reuseFrom，没有第二份 scenes。
- [x] 验证：`npm run video:lint -- s5-systick` —— 骨架阶段那三条（`id 与目录名不一致`/`缺 cover.line1`/`缺 publish`）为零；
      写完终稿后同一条命令输出 `✅ 通过：bilibili 28 场，douyin 12 场`。

## 4. 横版 30 场（写字的唯一一轮）

- [x] 按 design §4 的场次表逐场写：`kind ∈ hook/anim/code/card/outro`；`card` 必填 `title`、`code` 必填 `code`、
      `anim` 必填 `anim` 且 `t1 > t0`；行内记号 `{{黄}}` `[[红]]` `**粗**`、代码行首 `!`=证据行、`~`=弱化行。
      ——实测落成 **28 场**（比计划少 2：design 那张表把两场合写过），顺序
      `hook-01, hook-02, card-01, code-01..05, card-02, code-04..05, anim-01, card-03, code-06..08, card-04, code-09..11, card-05, code-12..14, card-06, code-15..16, card-07, punch, cta`。
      证据行一律 `!`；未打印的头文件常量（`SCS_BASE+0x0010`、`bit0..bit16`、`__NVIC_PRIO_BITS=4`、`SysTick_IRQn=-1`）
      用 `~` 弱化并在 codeLabel 明写「头文件里写的，没打印」。
- [x] ⛔ 每场代码 ≤13 行（`maxLines`，warn 线是 19 行，别拿 warn 当许可）。
      ——实测：`.temp/s5-budget.mjs` 的超长清单为空（横竖两版都没有 >13 行、也没有超宽的：横版 ≤78 列、竖版 ≤44 列）。
- [x] 旁白字数落在 **2087–4123 字**（目标 ~3070），否则 lint 的 est 判据直接 error。
      ——实测 **3382 字 / 28 场**，est=661.2s。第一版是 3545 字（est 693.0s），按 17 集实测回归的最坏比值 ×1.049
      推到 727s 已破 720 硬门，于是**裁旁白 23 处**而不是放宽阈值（回归口径见 `.temp/s5-dur-calib.mjs`：
      bilibili act/est ∈ [0.951, 1.049]）。裁后最坏 693.6s，留 26s 余量。
- [x] `sections`（横版一份）：`at` 命中该平台真实 id、不重复、下标严格递增、`title` ≤12 字（design §3 那六节）。
      ——实测六节锚点 `card-01 寄存器版图 / card-02 CTRL 四个位 / card-03 周期=LOAD+1 / card-04 24 位装不下 /
      card-05 换算与回绕 / card-06 Config 与优先级`，最长 11 字（`CTRL 四个位` 按 `trim().length` 计）。
- [x] 验证：`npm run video:lint -- s5-systick` 全绿；再 `npm run video:lint` 全量绿（19 集逐集 ✅，末行 `✅ 全部通过`）。

## 5. 竖版短版（重排，不是缩放）

- [x] `pick` 选 12 场（钩子前置、每幕一句、金句收尾），`set` 与 `narration` 的 key **与 pick 同集合**。
      ——实测 pick = `hook-01, hook-02, card-01, code-04, code-05, card-03, code-08, card-04, code-10, code-13, card-06, punch`；
      `set` 12 处、`narration` 12 句，key 与 pick 逐字同集合（lint 那两条专门抓对不上的判据均未触发）。
- [x] 竖版旁白 **130–363 字**（目标 240–290，12 场固定留白 13.1s）。
      ——实测 **279 字**，est=67.4s；douyin 最坏比值 ×1.06（c4-struct-abi 实测）→ 71.4s，落在 [45,75] 内不贴线。
      初版 312 字 est=73.8s 的最坏值 78.2s 会破 75，裁了 card-01 / card-03 / code-05 三句旁白。
- [x] 竖版 `sections` 自己一份（3–4 节，`at` 用竖版真实 id）——横版那份在竖版命不中，整集页头会全空。
      ——实测 **5 节**（比计划多 1，因为竖版把「回绕」和「优先级」拆成两场）：
      `四寄存器 / 标志一读就没 / 减一亏相位 / 24 位装不下 / 回绕与优先级`，全部 ≤12 字。
- [x] 动画：按 §0 点头结果决定挂不挂 `systick-tick`；不挂就在 `note` 里写明理由。
      ——实测**不挂**（`systick-tick` 未进 pick），理由照 F5 那句的写法进 note：横图竖屏等比缩放后标题与字幕挤不下。
- [x] 验证：`npm run video:lint -- s5-systick` 全绿。

## 6. `publish` 块（只写 bilibili / douyin）

- [x] 标题体例（design §10 第 3 条已定）：**句子钩子、不带编号**，与已投 17 集同口径（系列身份交给合集，不交给标题）。
- [x] `publish.bilibili`：`titles[]`（3 条，均 ≤80 字）、`intro`（约 1900 字，六节逐节给出处 +
      ⚠️ 明写「实物实验这一轮没拍」）、`tags[7]`、`topics[科技数码/知识/校园学习]`。
- [x] `publish.douyin`：`titles[]`（3 条 ≤30 字）、`caption`（首行 wlen 15 / 次行 8 / 话题行 27，共 50 ≤62；
      话题 3 个；无 `*` 行首；`OFFSITE_RE` 无命中）、`pinned`（含「通往单片机之路」+ `code/stm32/05-systick/probe.sh`）、
      `repro:"sh code/stm32/05-systick/probe.sh"`。
- [x] ⛔ `declare`：**没写**。它是 `publish/douyin-step.mjs` 投稿时那步「自主声明」的唯一凭据，只能来自对话点头；
      实测它不影响 `build`（`writeRelease` 不 gate 它），所以留空并把理由写进 `declareNote`，把点头动作推到投稿前。
- [x] 跨集查重：话题组、描述首行都不与已投集重复（全量 lint 那两条判据未触发）。
- [x] ⛔ 本任务没写 `publish.zhihu` / `publish.xiaohongshu`（出口是"不出投放动作"）。
- [x] 验证：`npm run video:lint` 全量绿（跨集判据只有全量跑才生效）。

## 7. `series.json` 补条目（⚠️ 实际执行顺序 = 在步骤 8 之后，理由见下）

- [x] `episodes` 追加第 18 条：`no:18`、`id:"s5-systick"`、`title`、`source:"docs/stm32/05-systick.md"`、
      `status:"done"`、`anims:["systick-tick"]`、`hook`、`hookRef`、`punchline`、`masters`（已写实测：
      `video/out/s5-systick/bilibili.mp4（10:29）· douyin.mp4（01:07）`）、`script`、`note`（取证 + 白名单对账 +
      页头首集实测 + 裁旁白余量 + 两处顺序/前置发现，全段落成一个 `note` 字段）。
- [x] `next` 清空 → `"next": []`；`backlog` 4 条一字未动。
- [x] ⛔ 既有 18 条字段一个都不顺手改。——实测 `git diff video/series.json` = **15 insertions / 3 deletions**，
      删的那 3 行正是 `next` 那三行，其余全是新增；`series` 值读回 `"通往单片机之路"`，无尾空格（10-16 那句已过期）。
- [x] 验证：`node -e "JSON.parse(...)"` 通过，`episodes.length = 19`、`no` 最大 18、id 唯一。

> **执行期发现的顺序冲突（本文件原来把 7 排在 8 前面，是错的）**：
> `video/publish/douyin-release.mjs:69` 对 `series.json` 里每一集硬取
> `video/out/<id>/douyin/timeline.json`，缺了就
> `throw ${id} 缺 douyin/timeline.json——这条还没渲过，别造文案`。
> 所以「先登记再渲」会让那份投稿清单生成器整支报错——而且报的还是正确的话。
> 反过来 `video:build` 完全不读 `series.json`（`src/` 全仓 grep 只有 `package.mjs:377` 那一行文案里提到它），
> `bili-ledger.mjs:17` 也自带「没有横版 master 就归进 noMaster、不算漏投」的分支。
> 结论：**第 8 步渲完 → 再补 `series.json`**，正好让 `masters` 当场写成实测时长，不落脚本占位符。

## 8. 渲染（第一次真正写 `video/out/`）

- [x] 渲前最后一遍全量对账（`.temp/s5-numbers.mjs`，把两平台 `pick`/`set`/`narration` 覆写后的
      **每一个上屏字段**里的数字 token 逐个回当天留档）：188 条字段、未命中 15 个 token，逐个定性为
      ①源码行号（`core_cm4.h:764/1550/1555/2022/2027/2029/2034`、`probe.c:247/255` —— 全部 `sed -n` 打开那一行核对过，
      引的就是那句）②头文件原文里的写法（`0x004/0x008/0x00C/0xE000E000/0x0010` —— 所在的 `~` 弱化行已标
      「脚本不打印它」，`code-02` 还专门并排给了实测的 `0x0/0x4/0x8/0xC`）③同值的短写法（`0x7` = 留档里的 `0x00000007`）。
      deny 表 17 项命中 4 处，其中 `SCS_BASE`/`0xE000E000`/`__NVIC_PRIO_BITS`/`SysTick_IRQn` 都在
      「引用头文件原文并明说没打印」的场里，符合白名单处置。
      **改了一处**：`code-15` 那句 `→ 0x7 = bit0|bit1|bit2：…` 原来没带出处，补一行
      「位定义在 probe.c:37-40，脚本不打印它」（该文件 37–40 行确实是那四个 `#define`）。
- [x] `npm run video:build -- s5-systick`（六阶段固定顺序：旁白+时间轴 → seek 自检 → 舞台+审计 → 渲帧 → 合流 → 封面+发布稿）。
      实跑日志 `.temp/s5-build.log`（后台任务 b7f4symib）——只点名这一个 id，⛔ 不带别的 id、不跑全量。
      **exit 0**：bilibili 新合成 28 句 / 命中缓存 0 句，`narration.wav 629.14s / 18875 帧 / 字幕 298 条`，
      渲帧「截图 3110 / 复用 15765，省 84%，27.9 fps，675.8s」，合流 `成片 629.17s`，`✅ bilibili 完成：10:29，用时 767s`；
      douyin `67.91s / 2038 帧 / 字幕 27 条`，`成片 67.93s`，`✅ douyin 完成：01:07，用时 101s`。
- [x] ⛔ 两道硬门都过（日志里 `不在目标` / `与成片…差` 两条 0 命中）：629.167s ∈ [480,720]、67.933s ∈ [45,75]；
      两版规格 `h264 (High) (avc1) yuv420p @30fps` + `aac/44100Hz/2ch`。改稿时是裁旁白让的余量，没动阈值、没砍场。
- [x] 音频缓存判据：本次 `新合成 28 句，命中缓存 0 句` —— 裁过旁白所以整集重合成，符合预期；
      `--force-audio` 没用上（manifest 键含 `scenes[]`，改字自己失效）。
- [x] 字体闸门：两平台都解析到真字族（横版 `🔤 字幕字族：Microsoft YaHei(20)`、竖版 `Microsoft YaHei(8)`），
      全文 `字体审计降级` 0 命中。——渲前查过 `openBrowser()`（`stage.mjs:28`）是 `chromium.launch` 自己起实例、
      `cli.mjs:545` 那个 `browser.close()` 关的是自己刚起的那个，**不是**连到小红书那条常驻 CDP 会话，所以不会把登录现场关掉。

## 9. 排版审计（改版后的版式上必须跑到 0）

- [x] `npm run video:check -- s5-systick`（不带 `--platform`，两平台一次收全）→ 逐字：
      `🔍 排版审计通过：28 场，越界/裁切/压字幕/版式相叠/字号不可读/顶穿容器/标题孤字/进度杠重复 0` +
      `🔍 排版审计通过：12 场，…0`，末行 `✅ 全部通过`。
- [x] ⛔ 不是假绿：`跳过` 计数 **0**（时间轴已由第 8 步生成），两平台 28 + 12 场真跑了。
- [x] 页头两条实测（`.temp/s5-header-probe.mjs`，逐场把 DOM 与 `sceneSections()` 对账，40 场 0 处不符）：
      横版 chip 逐场推进、最后一场读到「第 6/6 节 · Config 与优先级」，6 种文案 = 声明 6 节；`.ticks` = `flex`；
      竖版 `.secbar` `display:flex`、段数 5 = 节数、`.cur` 跟着节走（1→5）、`.ticks` = `none`；两平台同屏进度杠都是 1 根。
      片头 `hook-01/hook-02`（未归节）chip 为空且不占宽。
- [x] 字号地板：横版最小 21.1px（`pre.fit.code`）、竖版最小 26.9px，地板 16px 之上；
      全程没为过审缩过字号，越界与孤字都在写稿层用「减字 / 补 `\n`」解决（竖版 12 场 `标题孤字 0`）。

## 10. 封面与发布稿

- [x] 封面：build 的第⑥阶段已用当前这份稿画过（`bilibili-cover.png` 241KB / `douyin-cover.png` 187KB，19:36–19:38），
      与渲帧同一份 episode.json，**没有再单独跑 `video:cover`**——同输入重跑只产出同一张图，不额外作证。
- [x] 两份发布稿核对：`发布-bilibili.md`（3 条标题、六节简介 + ⚠️ 那段没拍实物的说明、28 行时间轴、7 标签、3 话题）、
      `发布-douyin.md`（描述首行 15 字 / 次行 8 字 / 4 个话题，实测 50 字；竖屏 1080×1920 67.9s 落在 45–75；
      置顶评论含「通往单片机之路」与 `sh code/stm32/05-systick/probe.sh`）。两文件由 `writeRelease` 生成，无 markdown 残留。
- [x] 发布前置的两张补图已补（19:54）：`douyin-cover-1440x1080.png` 204KB / `zhihu-cover.png` 230KB。
      **上一句里「全仓库只有消费方没有生成方」是错的**——生成方在 `.temp/`：
      `node .temp/douyin-cover43.mjs s5-systick 1440 1080`（给 cover 塞临时键 `sizes.h43`，走同一个 `buildCover`，
      coverU 取短边 ⇒ 3:4 与 4:3 字号尺度一致）与 `node .temp/zh-cover.mjs s5-systick`（`COVER_SIZES.zhihu=1920×1080`）。
      两张都零报错零缩字 ⇒ `fitCover` 的"装不下就报错"护栏没被绕过；目视与 f5 同形（4:3 与 16:9 都不带代码卡，是固有版式）。
      只往 `video/out/s5-systick/` 新增文件，`md5sum -c` 复跑仍 **exit 0**；发布稿里只登记竖封面那行，与 f5 一字不差，不重生成。
      补图≠投放：这四张图投稿脚本会读，本任务仍然一条都不发。
      ⚠️ 顺带发现一处**生成器里的过期数字**（不属于本集，未动）：`package.mjs:377` 与 `douyin-release.mjs:92`
      硬写「合集名 16 条共用」，而片单早已不是 16 条；那句是要改生成器、不是给某一集补字。

## 11. 收尾核对

- [x] `npm run video:lint` 全量绿（19 集逐集 `✅ 通过`，末行 `✅ 全部通过`）；
      `npm run video:check` 全量绿：日志 `.temp/s5-check-all.log`，`🔍 排版审计通过` **37 条**
      （19 集 × 2 平台 − c3b 无横版 = 37）、`跳过` **0 条**、末行 `✅ 全部通过`、`EXIT=0`。
- [x] `md5sum -c research/out-md5-20261017-1300.txt --quiet` → **exit 0**（1220 项，失败输出 0 行）。
      这证的是"第 8 步只写了 `video/out/s5-systick/`，别的集一字节没动"；本任务全程只点名 s5 跑过 build。
- [x] PRD 的 Acceptance Criteria 按**实测**逐条勾完（六条全勾，其中两条按实际契约改判：`no` 不进 episode.json、
      页头吃 `sections` 而不是"每场 kicker"）。实测值：629.167s / 67.933s、h264(High)/yuv420p/30fps + aac/44100/2ch、
      响度 **-15.0 / -15.0 LUFS**（真峰值 -0.9 / -1.4 dBTP，`ffmpeg -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=summary`
      读的是成片本身，不是 `mux.mjs` 的目标值）——已写进 `series.json` 的 `masters` / `note`。
- [x] 屏上每个数回对白名单：不止抽 5 场——渲前用 `.temp/s5-numbers.mjs` 对**两平台 188 个上屏字段**全量对账
      （结论 + 15 个未命中 token 的逐个定性 + 当场补的 `code-15` 位定义出处）；收尾再抽 5 场逐字比：
      `code-01` 10/10、`code-06` 8/8、`code-11` 14/14、`code-14` 4/4、`code-09` 2/4（未中那两个是行号 2022/2027）。
      全部写进 `research/whitelist-20261017.md` 新增的第四节。
- [x] spec 回写（走 `trellis-update-spec` 的口径，改的是 spec 不是判据文案）：
      ① `.trellis/spec/video/layout-contract.md` §3 加"首个真集实测"那条（40 场 DOM 与 `sceneSections()` 一字不差、
      未归节的场 chip 必须空且不占宽）；§6 加一条**审计查不出"页头说的是不是真话"**——`validateSections` 只管稿子自洽，
      DOM 侧要单独对账，范本 `.temp/s5-header-probe.mjs`。
      ② `.trellis/spec/video/index.md` 新增「三处顺序闸」：`lint → build → check` 不能反（check 对未渲集假绿 exit 0）、
      `series.json` 登记必须排在 build 之后（`douyin-release.mjs:69` 硬 throw，而 build 不读片单）、
      时长按 17 集 `act/est` 离散度留余量（判据 `est × 平台上沿比值 ≤ targetSec[1]`）；
      金样例补 s5 为 `sections` 第一个真集，并把顶部"已发布的 18 条"改成不随集数漂移的说法。

## 回滚点

- 步骤 3–7 全在 `video/episodes/s5-systick/` 与 `video/series.json`，一集一个 commit，`git revert` 即回；
  没碰 `video/out/`，旧集零风险。
- 步骤 8 是唯一写 `video/out/s5-systick/` 的地方，出问题删该目录即可（⛔ 不许删或覆写别的 id 的目录）。
- 步骤 4/5 的旁白字数与 §2 的白名单是两处最可能返工的地方：先过 lint 再写字，别反过来。

## 出口条件

第 18 集两平台成片 + 发布稿 + 审计全 0 + 既有产物 md5 未变，才算完。投放另起动作（本任务不做），
且**每次公开投稿都要单独点头**——一集一次授权，同一条重跑不算第二次授权。

## 12. 投放（2026-10-17 20:35 用户点头：「你继续发啊，小红书抖音b站」——知乎本轮不投）

闸门三张都写的这句原话：`.temp/{bili-web,douyin,xhs}-run/I_HAVE_USER_OK=s5-systick`。

- [x] **B站已投：BV1uEJi6vEnc**（`sh video/publish/bili-one.sh s5-systick`，填表→点投稿→API 补字段，回读核对 9 项 ✓）。
      投前 `bili-ledger` 账上只有 17 个 bvid、没有 s5（「没有留痕就当没投过」），投后 18/18、缺 0、无重复稿。
      公开 view 暂时 `-404`＝审核期未建索引，不是失败。
- [x] **抖音已投**（`dy-post-one.mjs`，`status_code=0` + `s5-systick-published.txt`）。
      七项核对全过：标题 14/30、描述 59/1000、双封面 v+h、合集、两项检测、可见性=公开、自主声明。
      `publish.douyin.declare` 这一格是当场问出来的——**「内容为个人观点或见解」**，与 C3/C4/F5 同口径；
      没问之前脚本走不到发布那步（`douyin-step.mjs:538` 直接 throw）。
      合集序号显示「第17集」不是错：F5 在我们账上是 17、抖音合集里是 16，恒定差一格，说明有条集没进合集。
- [x] **小红书草稿齐了，停在人点「发布」**：`fill`（标题 18/20、正文 817/1000）→ `topics`（STM32/SysTick/单片机
      三个都成 `a.tiptap-topic` 真 chip）→ `coverset`+`coverapply`（封面条是我们的 PNG，平台回「封面效果评估通过」）。
      这条线的发布没有自动化（`xhs-step publish` 在闸门后主动抛错），`<xhs-publish-btn>` 是 closed shadow，脚本够不到。
- [x] **S5 原本没有 `publish.xiaohongshu` 块**——产线 `writeRelease` 只出 bilibili/douyin 两份，小红书那块每集手写的。
      已补进 `episode.json`（标题/正文/话题/置顶/复现命令/合集名「STM32 零基础自学」+ 三条 note），
      插法是先断言锚点全文唯一再替换，lint 仍绿。**下一集别忘：开小红书这条线之前要先写这块，否则 `fill` 停在半张草稿上。**
- [x] B站简介超线：`bili-submit.mjs` 报「简介超 2000 字（2467）」不给落盘（p4 当年 1974 是贴着过的）。
      裁的是 `publish.bilibili.intro`（1855→1346），①–⑥ 压从句和屏上已演过的细节，
      **⚠️ 那段「没拍实物」一字未删**；只重跑 package 一步（`.temp/s5-release-only.mjs`，直接调 `writeRelease`）
      重生成发布稿，不重渲两万帧。终值 1966 字 ✓。
- [ ] ⚠️ **本任务自曝一处越界**：为量简介长度跑了不带 `--dry` 的 `bili-submit.mjs`，它**没有单集模式**，
      一次写了全部 18 份 yaml，而它默认 `tid=171` 与全系列线上实际用的 **231** 不符 → 17 份已发布稿件的投稿配置
      被刷成分区错的（将来谁拿它跑 `repair` 就把视频挪分区）。平台侧零写入（全程只 GET）。
      修法：逐条 GET `vupre/web/archive/view` 比回来——简介/标题与线上逐字一致，只有 tid 被刷错——
      `--tid=231` 重生成后 17 条全 ✓，`md5sum -c` 的 17 处 FAILED 也全部收敛在 `bili-submit.yaml` 这一类文件上，
      成片/字幕/封面/发布稿一字节没动。判据已写进 `video-release` 技能 §6。
