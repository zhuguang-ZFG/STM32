# S5《SysTick：内核的心跳》v2 复核

Verdict: CHANGES_REQUIRED

## 四项必修复核

| 项 | 结论 | 证据 |
|---|---|---|
| C1 | **PASS** | `code-10` 上屏与旁白均写「c=1000 → 5952ns=5.952us，按整数 us 取 5us，丢 0.952us」，无损例改为「168 周期 → 1000ns=1us」；`card-05`、B 站简介同步。全片无「5us 无损」或「1000 周期=5us」残留。`probe.c:191-195` 与本次日志 L10 一致。 |
| H1 | **PASS** | `code-13` 上屏「那个 4 是 `__NVIC_PRIO_BITS`，不是寄存器读数」；旁白「probe 只在说明文字里提到四位优先级，并没有把它当读数打印」。`card-06` 用「4 位里的最低档」，与 probe `[6]`（L12）一致；无「probe 没打印 4」的相反说法。 |
| H2 | **PASS（成片/发行）** | `code-11` 上屏 L415、旁白 L417、抖音 set L688、B 站简介 L737 均为「漏报」；全片检索只剩「这属于漏报而不是误报」这一处正确的对比。**底稿残留**见下：factsheet L247 仍写「误报未超时」。 |
| H3 | **FAIL（未闭合）** | `codeLabel` 已进 `SCENE_FIELDS`（numbers.mjs:8）；247/255/764/770 已在 exceptions；`4` 指向 `[6]`、`5` 指向 `[5]/[7]`，均正确。但 `code-09` 的 3297/3305/0xce9 与本次日志 L22 的 3361/3369/d29 不符；`bit16` 仍被 tokenizer 的负向后顾跳过；`probe.c:247-255` 已过期（双读循环实际 249-257）。 |

## 新发现（按 Critical/High/Medium/Low）

**Critical — `code-09` 交叉段仍是修 C1 之前的旧二进制。** 本次 `.temp/v2-facts/s5-probe.log:22` 是 `3361 / 0 / 8 / 3369 / d29`；episode 的 `code-09` code 块与旁白仍写 `3297 / 3305 / 0xce9`、旁白读「三千二百九十七字节」；B 站简介（`publish.bilibili.intro`）也写 `text 3297`。factsheet §3.8 声称从「本次」日志复制，却同样写 3297/ce9；numbers.json 的 `3297`、`3305`、`0xce9` 三条 evidence 也是旧值。C1 改换算段（加长 `[5]` 的 printf、增加 `days10` 输出）后 text 从 3297 涨到 3361，作者只改了换算段，没有重取交叉段。于是「脚本打印什么，屏上就贴什么」「每个 probe 数都是那一次的输出」在这三个数上为假；`code-09` 的结论「不是我在这里算给你看」也被自己的旧输出证伪。必须改为当前值（hex 列原样是 `d29`，不是 `0xce9`；若要加 `0x` 需明示是改写），同步旁白、B 站简介、factsheet、numbers.json，并重录 code-09、重渲母版。

**High — H3 的审计盲区仍在。** `numbers.mjs` 的数字正则带 `(?<![0-9A-Za-z_])`，`bit16` 里的 16 不会成为 token；numbers.json 新增的 `16` 行因此从未被审计命中。factsheet L177 说 16 见 `docs/stm32/05-systick.md:94`，numbers L87 却说来自 probe `[7]`，两处互相矛盾。绿勾只证明「episode 的 token 能在 evidence 键里找到」，不证明 evidence 值等于本次日志——所以 3297 这类旧值能一路通过。建议把 `16` 列入 exceptions 或让 tokenizer 接受 `bit16`，并把 evidence 的语义统一。

**Medium — factsheet 仍把漏报写成误报。** `s5-systick-factsheet.md:247`「在 now=2000 时误报未超时」与同文件 L128、numbers.json L45、成片全部相反，是 H2 修复未落到证据底稿。

**Medium — `probe.c:247-255` 行号过期。** 当前双读循环在 249-257：第一循环 249-252，第二循环 253-257，`got_wrong` 的判断在 256，正好落在标注范围之外。`code-04` 的 codeLabel 与 exceptions 应改为 246-257 或 249-257。

**Medium — `cta` 旁白仍在全称。** 上屏 bullet 已改成「这些 probe 数全部来自这一条命令」，但旁白 L532 仍以「屏幕上出现的每一个数」开头；`0x00C`、源码行号、`0xce9` 等并非这条宿主命令的打印值。改成「屏幕上的这些 probe 数」即可。

**Low — `cta` 的 emphasis 还是 `"49"`。** L538 在「49.7 天」上只高亮「49」，应改为 `"49.7 天"`（或 `"49.7"`）；这是 49→49.7 修复的漏网。

**Low — S9 前向引用未软化成「待建」。** `code-12` 上屏 L441 与旁白 L443 仍说「书里 S9 的采样超时」；S9 在 `series.json.backlog`，尚未投放，和「S5 是系列最后一站」仍有张力。建议「书里待建的 S9」或删。

**Low — 新增口播词 `__NVIC_PRIO_BITS` 未进 TTS 词表。** H1 修复把它写进 code-13 旁白（L471），但 lexicon L58-63 只补了 ARM/PATH/PF6/S4/S5/S9；该标识符很可能被逐字母或按下滑线读。抽听，必要时加 `ttsText` 局部覆盖。

**Low — 母版仍旧。** `out/s5-systick/bilibili.mp4` 时间 20:02，早于当前 episode（20:05）与 timeline（20:09）；`out/s5-systick/douyin/timeline.json` 仍是 10-17 的 12 场旧稿（当前 pick 10 场）。修完后必须重跑音画并回读时长。

**Low — `code-14` 的 F3 让路链。** 「F3（第 14 集）把这条让路的链逐行搬过源码」在 F3 文档/脚本里找不到 UART 抢占或优先级 15 的逐行链（F3 讲的是 tick 三段与 PendSV）；建议改指 S4 或删。

## 抽检

| token | episode 位置 | 证据/例外 |
|---|---|---|
| 42 | route-01/code-01/cta | 日志 L15-16 `HOST_ASSERTS=42`、`42/42` |
| 167999 / 168000 | card-03/code-05/code-13 | 日志 L4-L5；probe `[2]/[3]` |
| 514ms / 5.95ppm / 1512001 / 1512010 | code-06 | 日志 L6-L7 |
| 16777215 / 99864us / 22783 / 135.6us / 737 | card-04/code-08 | 日志 L8-L9 |
| 5952ns / 5.952us / 0.952us / 1000ns / 1us | code-10 | 日志 L10；probe `[5]` |
| 49.7 / 0xFFFFFC18 / 6000ms / 漏报 | code-11/douyin set | 日志 L11；numbers `2000` |
| 0x00010005 / 0x00000005 | code-03 | 日志 L13-L14；probe `[7]` |
| 0x00000007 / 0xF0 / 15 | card-06/code-13 | 日志 L12；`4` 的语义指向 `[6]` |
| **3297 / 3305 / 0xce9** | **code-09 + B 站简介** | **日志 L22 实为 3361 / 3369 / d29（FAIL）** |
| 247 / 255 / 764 / 770 | codeLabel | exceptions 有，247-255 范围已过期 |
| 16 | card-02/code-03 的 `bit16` | tokenizer 不取；factsheet 指 docs:94，numbers 指 `[7]`，不一致 |
| 4 / 5 | code-07/card-06/code-13；code-03/code-04/code-10 | numbers 已分别指向 `[6]` 与 `[5]/[7]`，正确 |

**回归项：** 钩子 8.9s；B 站旁白 3355 字 / est 655.9s / ×1.049=688.0s≤720；抖音 267 字 / 10 场 / 5 节；B 站 6 节标题 5/8/9/7/5/11 字；B 站 25 场、抖音 10 场每场 ≥2 字幕；emphasis 全部能在上屏文本找到；无板上测量或逻辑分析仪百分数；XHS 18 字标题、782 字正文、无 URL、合集与置顶命令齐；知乎八字段齐。技术面（偏移/基址、周期=LOAD+1、24 位上限、COUNTFLAG 读清、优先级 15、737×、49.7 天）均正确。

## 结论

C1、H1 已成片层面修好，H2 的成片/发行文字也已统一，但 H3 没有闭合：`code-09` 还是修 C1 前的 3297/3305/0xce9，而本次日志是 3361/3369/d29，且 89 个数字的绿勾只校验 evidence 键存在、不校验值是否来自本次运行。这个旧值同时污染了旁白、B 站简介、factsheet 与 numbers.json，必须作为 P0 先改并重录/重渲；P1 再修 factsheet 的「误报」、247-255 行号、bit16 审计盲区。cta 旁白全称、`"49"` emphasis、S9 前向引用、`__NVIC_PRIO_BITS` 发音和双平台母版重渲可同批处理，不单独阻塞。
