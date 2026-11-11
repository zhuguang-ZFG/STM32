# Wave A 复盘：c2 / c3 / c4 / c5 / c6 / c7

- 任务：`.trellis/tasks/10-22-video-v2-remaster` · Task 12
- 范围：6 集 v2 重制，双平台母版（bilibili 横版 + douyin 竖版），四平台发布包
- 时间：2026-10-22 至 2026-10-23
- 结论：6 集均通过 lint / check / numbers / pack / test；c2–c7 均完成独立复核与定向复核，c7 在 7 个 P2 修复后重建，定向复核 APPROVED（0 P0/P1/P2，5 Low 接受）

## 总表

| 集 | bilibili | douyin | 场次 B/D | 旁白 B/D | 节拍 B/D | 最长静止 B/D | LUFS B/D | 数字 | 复核 |
|---|---|---|---|---|---|---|---|---|---|
| c2-pointer | 618.766667s / 18563f | 67.566667s / 2027f | 27 / 10 | 3071 / 280 | 311 / 29 | 4.2 / 5.3s | -15.0 / -14.8 | 30 | APPROVED |
| c3-volatile | 642.533333s / 19276f | 51.866667s / 1556f | 39 / 14 | 3393 / 288 | 335 / 31 | 4.1 / 2.5s | -15.0 / -14.9 | 30 | APPROVED |
| c4-struct-abi | 684.3s / 20529f | 59.166667s / 1775f | 40 / 14 | 3391 / 280 | 335 / 33 | 4.2 / 4.0s | -14.9 / -15.0 | 36 | APPROVED |
| c5-func-pointer | 651.8s / 19554f | 57.733333s / 1732f | 39 / 14 | 3232 / 278 | 325 / 32 | 4.1 / 3.4s | -14.9 / -14.9 | 30 | APPROVED |
| c6-abi-stack | 620.1s / 18603f | 57.833333s / 1735f | 31 / 11 | 3313 / 258 | 322 / 33 | 4.5 / 4.0s | -15.0 / -14.8 | 23 | APPROVED（定向复核） |
| c7-ub | 643.1s / 19293f | 61.6s / 1848f | 32 / 11 | 3252 / 277 | 317 / 32 | 4.2 / 3.6s | -15.0 / -14.8 | 24 | APPROVED（定向复核 0 P0/P1/P2，5 Low） |

漂移：c2–c7 双平台均 0（c7 bilibili 为 1µs 舍入，闸门内）。

## 逐集

### c2-pointer

- 内容：`ldr/str` 的基址 + 偏移，`strb/strh/str` 的宽度，`ldr` 的方向；共享 SVG 的 6 格 × 4 = 0x18。
- 修复：复核 Low #1–#9 全部处理；共享 SVG 的箭头/标签和 `step-02` 旁白「下标六的元素」在全量重建中落地。
- 复核：APPROVED，0 阻断，10 Low；`probe.c` 的 `static_assert` 文案仍是「第 6 个元素」（1-based 说法，算术正确），留到 Task 15。
- 产物：13+13 抽帧、封面、四平台发布包、`bili-submit.yaml`。

### c3-volatile

- 内容：`volatile` 的有无、编译器优化、`testb` 形状、BSRR 读改写、屏障。
- 失败 1：douyin 首建响度 -15.1 LUFS，超出 -14±1。根因是 loudnorm 线性增益在 TP -1.5 约束下无法到 -14，动态模式停在 -15.1。
- 修复 1：mux 增加有界音频修正分支（`|I+14| > 1` 时两次重封音轨，视频流复制，重测响度/漂移），失败母版验证为 -14.8 LUFS / -1.6 dBTP；硬闸门保留。
- 失败 2：XHS 标题 21 字 > 20；改为「一条 testb 后…」20 字。
- 复核：CHANGES REQUESTED（2 P1 / 2 P2 / 8 Low）→ 全部处理 → 定向复核 APPROVED；288 字 douyin 旁白与「在 Cortex-M4 上编」措辞按裁决保留。
- 产物：13+13 抽帧、封面（DOCUMENTED/DOCUMENTED）、发布包、YAML。

### c4-struct-abi

- 内容：基址、偏移、访存纪律；`WithReserved_t` 的 `static_assert` 首次真正补进 `broken.c` 并由 probe 跑出。
- 失败 1：hook-01 + hook-02 连续 29.1s > 15s。修复：hook-01 收短、hook-02 改 `kind: code`、合同映射移到 hook-04，保留 40 场。
- 失败 2：douyin `bitfield-says` 标题孤字「义」；改为「位域怎么排 / 实现定义」。
- 失败 3：XHS 标题超长；改为「漏一对方括号，整块缩成 0x24」。
- 复核：两轮定向复核 APPROVED；共享 SVG 的原始反引号问题影响 c2+c4，留到 Task 15。
- 产物：13+13 抽帧、封面、发布包、YAML。

### c5-func-pointer

- 内容：函数指针、`blx`、状态机跳转、弱符号、向量表。
- 失败 1：独立复核 5 P0 / 6 P1 / 8 P2 / 6 Low，全部按条处理（`0x98` 六指令分派、`0x22` 证据只引 L40、`fsm-asm-a` 不声称分支可见、`rb` 摘录披露 volatile/barrier、douyin 单拍 `beatMap`、状态切片顺序等）。
- 失败 2：全量重建 hook-01 16.4s > 15s；收短最后一句后重建。
- 复核：定向复核 APPROVED；7/8 注释时机与 `fsm-asm-a` 的 `ite` 省略按设计保留。
- 产物：13+13 抽帧、封面、发布包、YAML；`fd-4` 共享 SVG 的 FSM[3][4] 标注已在 factsheet 限定为 probe 示意。

### c6-abi-stack

- 内容：AAPCS 参数落位、64 位参数空洞、栈帧返回地址、M4 前导算术、宿主实测帧。
- 失败 1：douyin `sum-caller` 继承 9 行带注释汇编 + 4 行 `codeB`，最小字号 12.7px；改为四行节选、单列、`codeB: null`。
- 失败 2：douyin 置顶评论缺站名；补《通往单片机之路》C6。
- 失败 3：独立复核 P1：四行代码直到 21.1s 才出现、21.633s 切场，可读窗口约 0.5s；五场 douyin 代码场加单拍 `beatMap`，17.2s 起四行常驻。
- 失败 4：P2 `mix-caller` 的「没有一条指令碰 r1」超出画面四行；标题/`codeLabel`/旁白/三份发布文案全部限定到「这四条」；CTA「五段」改「六段」并补 `sum6 调用方`。
- 失败 5：修复后全量重建 `c6-build4` 遇 edge-tts 连续 5 次网络失败；重跑 `c6-build5` 成功。
- 定向复核：APPROVED（0 P0/P1/P2，7 Low）；Low 10 的抖音旁白又加「这四条」，`publish.douyin.intro` 与 `cover.proof` 同步收口，douyin 重建为 57.833333s / 1735 帧；`c6-gates-final3.log` 31+11/0、numbers 23、pack 4。
- 产物：13+13 抽帧（7 张旧帧移入 `.temp/c6-stale-stills/`）、封面右栏「M4 摘录：8 + 16 = 24」、32 场 31 章 YAML。

### c7-ub

- 内容：同一行 `1u<<33` 在 -O0 得 2、-O2 得 0；有符号溢出、移位越界、严格别名；MISRA 与 UBSan 的边界。
- 独立复核（内容）：APPROVED，5 P2 / 2 Low。核心数字与 probe 证据成立；P2 为：
  1. 抖音 hook 8 秒内「两个答案都不算错」缺少 UB 限定；
  2. `warns3` 旁白称「原文摘录，没有补写」，但第三条警告删了 `dereferencing`；
  3. 抖音 `alias-warn` 标题说「压在解引用上」，画面却没有源码行和波浪线；
  4. 右栏固定抬头「-O2 编出来的汇编」与算术/读数/`-O0` 内容不符；
  5. 抖音 `bigger-arm` / `shift-asm` 首句字幕时两个代码框为空。
- 独立复核（包装）：APPROVED，2 P2 / 2 Low。P2 为 `video:test` 缺日志、YAML 02:40 重写后缺 17 份复原 diff；Low 为报告引文标点与抽帧 mtime 措辞。
- 修复：douyin hook 明说「这是未定义行为」；B 站标题/两份简介改「都不是标准答案」；`warns3` 旁白改「原文节选」；抖音 `alias-warn` 补源码行 + 波浪线；9 处 `codeB` 增加逐场 `codeBLabel`；六场抖音代码场加 `beatMap`（`code` 首拍、`codeB` 第二拍，因 `at` 必须严格递增）；测试日志 `c7-video-test-final.log` 与 YAML 快照 diff `c7-yaml-diff-final.log` 补齐。
- 重建：`c7-build2.log` EXIT 0。bilibili 643.100000s / 19293f / -15.0 LUFS（首遍 -25.6）/ 317 拍 / 4.2s / 32 场 0 问题 / 最小 21.1px / 渲染 766.1s（25.2 fps）/ 构建 867s；douyin 61.600000s / 1848f / -14.8 LUFS（首遍 -25.6）/ 32 拍 / 3.6s / 11 场 0 问题 / 最小 25.3px / 渲染 94.1s（19.6 fps）/ 构建 118s。漂移 1µs / 0。
- 闸门：lint 32/11、check 32+11/0、numbers 24/0、pack 4/4、test 100/100（`c7-gates-final2.log`、`c7-video-test-final.log`）。
- 产物：13+13 抽帧（bilibili 1 张、douyin 11 张旧时刻帧移入 `.temp/c7-stale-stills/`；douyin 两张 hook 帧时刻未变故直接覆盖）；封面四尺寸 + 接触表；YAML 32 章 / 7 标签 / 新标题；`s5-systick` 及另外 16 份非 c7 YAML 逐字节复原。
- 帧检：抖音 1/9.5/15.5/21/23.5/27/29.5/32.5/34.5/42.5/44/57.5/60.5s、B 站 5/105/160/305/310/330/420/479/600/620/624.5s；UB 限定、alias 波浪线、`codeBLabel`、CTA 命令均确认。残留 Low：抖音左栏标签跨字断行、窄栏代码 gutter 压行号、B 站 SRT「低五/位」切分、CTA 命令仅约 2.6s、置顶「三条警告原文」无时码，全部接受，留 Task 15。
- 定向复核：APPROVED，0 P0/P1/P2，5 Low 接受（`task-12-c7-rereview.md`）。7 个 P2 均按最终产物关闭；回归检查时长/帧/LUFS/漂移/闸门/发布稿/stills/封面全部通过。

## 横向问题

1. **`groupTargets` 晚揭示**：只有两条字幕时，默认把全部代码压到第二条，代码场首帧为空。c6 五场、c7 六场已用 `beatMap` 兜底；Wave B/C 应在抽帧时检查「代码场首帧是否为空」，必要时批量加 `beatMap`。
2. **`codeB` 默认抬头**：`layout.mjs` 的 `'-O2 编出来的汇编'` 只适用于 -O2 汇编；算术、读数、-O0 汇编都会被误标。c7 已逐场加 `codeBLabel`；其他集在 Task 15 全量审计时统一检查。
3. **响度修正分支**：c3 首次触发 `|I+14| > 1` 的 mux 修正；分支在 c3 验证，但缺合成单测，Task 15 补。
4. **YAML 生成器副作用**：`bili-submit.mjs` 每次生成都会顺带改写 `s5-systick`——s5 的 YAML 描述仍是旧版，与当前发布稿不同步，生成器按发布稿重写它。每次生成前快照 18 份、生成后逐字节复原，并留 diff 日志；最终 `c7-yaml-diff-final.log` 显示只有 `c7-ub`（目标）与 `s5-systick`（旧账）DIFF，16 份 SAME，非 c7 全部 `RESTORED-OK`，c7 二次生成幂等。s5 的 YAML 更新留 Task 15 统一做。
5. **抽帧残留**：重建后按场首时间命名的旧帧会残留；每次重建后清点 13+13，把旧时刻帧移到 `.temp/<ep>-stale-stills/`。注意 `--stills` 是渲染前 step③ 生成的，不是成片后抽帧；交付说明写「同一构建预渲染帧」。
6. **字数口径**：`package.mjs` 的「实测 N 字」是去空白计数，与原始长度不同；c6/c7 都遇到，Task 15 统一改文案。
7. **SRT 字边界切分**：edge-tts 会在词中间切字幕（c7 B 站 305s「低五 / 位，」）；不是裁切，但读起来断。Task 15 评估是否按标点合并短字幕。

## 裁决与延期（Task 15）

- c2 `probe.c:35-36` 的 `static_assert` 文案「第 6 个元素」（1-based），不改。
- c3 mux 修正分支缺合成单测，Task 15 补。
- c3 288 字 douyin 旁白与「在 Cortex-M4 上编」措辞保留。
- c4 共享 SVG 的原始反引号（影响 c2+c4），Task 15 统一修。
- c5 `7/8` 注释时机、`fsm-asm-a` 的 `ite` 省略，按设计保留。
- c6 Low 1（省略标记）与 Low 5（「bl sum6 之前的八条」标签）接受；Low 4/7（字数口径、旧 YouTube 缩略图）Task 15。
- c7 Low 6（CTA 旁白「三条警告原文」与屏上三条 bullet 的口径）与 Low 7（dy-34.5 右栏顶行紧贴边框）暂接受，留 Task 15 统一看；新增 Low：抖音左栏标签跨字断行、B 站 SRT 字边界切分、B 站 CTA 复现命令仅约 2.6s。
- 所有集旧 YouTube 缩略图仍为 2026-10-14 legacy，未被发布稿引用。

## Step 5 样本

- c2：`video/out/c2-pointer/bilibili.mp4`、`video/out/c2-pointer/douyin.mp4`、`video/out/c2-pointer/bilibili-cover.png`、`video/out/c2-pointer/douyin-cover.png`、`video/out/c2-pointer/cover-contact-336.png`
- c7：`video/out/c7-ub/bilibili.mp4`、`video/out/c7-ub/douyin.mp4`、`video/out/c7-ub/bilibili-cover.png`、`video/out/c7-ub/douyin-cover.png`、`video/out/c7-ub/cover-contact-336.png`
- 本报告：`video/research/wave-a-report.md`

Wave A 只到 Step 5 为止；未经用户点头，不进入 Wave B，不删除、不发布任何平台稿件。
