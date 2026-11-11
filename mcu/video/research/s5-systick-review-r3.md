# S5《SysTick：内核的心跳》v2 复核 r3

Verdict: APPROVED

Open findings: 2 Low (non-blocking), 0 blocking.

复核范围：r2 的 P0/P1/P2 与 Low 项；当前 `video/episodes/s5-systick/episode.json`、factsheet、numbers；20:36-20:48 的 build/check/numbers 日志；20:47/20:48 母版；四平台封面。只读复核，未改任何产线文件。

## 1. r2 关闭表

| r2 发现 | 当前证据 | 结论 |
|---|---|---|
| **P0 / Critical — code-09 仍是旧二进制 3297/3305/0xce9** | `episode.json:374` 屏上表为 `3361 / 0 / 8 / 3369 / d29`，下一行明写「size 的 hex 列原样不带 0x：d29 就是 0xd29」；`:375` 旁白「代码三千三百六十一字节」；`:738` B 站简介「text 3361 / data 0 / bss 8」。`factsheet:187-208` 与 `numbers:46-47, 86` 均为 3361/3369/d29。`.temp/v2-facts/s5-probe.log:22` 原文 `3361 0 8 3369 d29`。母版 361.5s 抽帧复核：表内是裸 `d29`，紧跟一行 `d29 就是 0xd29`，没有把 `0x` 偷塞进原表。 | **PASS** |
| **P1 / H3 — codeLabel 行号 247-255 过期** | `episode.json:260` 为 `probe.c:249-257，两个循环只差一行`；`probe.c` 实测 249/253 两个 `for`，256 判断、257 收尾，范围正好 249-257。`numbers:93-94` 的 exceptions 为 249/257；`factsheet:275-276` 同步。code-04 抽帧 label 为 `probe.c:249-257`。 | **PASS** |
| **P1 / H2 — factsheet 把漏报写成误报** | `factsheet:128` 与 `:249` 均为「漏报未超时」；全文件检索无「误报」；`numbers:45` 同步。code-11 母版抽帧为「漏报未超时」。 | **PASS** |
| **P1 — 16 的审计语义矛盾** | `numbers:92` 已把 `16` 放进 exceptions，写明「COUNTFLAG 的寄存器位号（bit16）……probe [7] 只打印 0x00010005，不打印 16，不是测量值」；`factsheet:178` 同义；`docs/stm32/05-systick.md:94` 确为 bit16 行。tokenizer 仍不切 `bit16`（负向后顾），但按 r2 给的二选一，已走「显式 exception」路径，不再冒充 probe 读数。 | **PASS** |
| **P2 — cta 旁白全称「每一个数」** | `episode.json:534` 已改为「屏幕上这些 probe 数：四个偏移和三个 LOAD……全部来自这一条命令」；母版 652.5s 抽帧上屏 bullet 与旁白一致。 | **PASS** |
| **P2 — cta emphasis 只高亮「49」** | `episode.json:540` 为 `"49.7 天"`；母版 652.5s 抽帧黄底完整覆盖「49.7 天」。 | **PASS** |
| **P2 / Low — S9 前向引用** | `episode.json:443-444` code-12 已改为「延时的超时、RTOS 篇的事件等待」，无 S9；全片旁白/上屏检索无 S9。仅 `:63` 的 `ttsLexicon` 还留着一个不再命中的 `S9` 键（见备注，不影响发音）。 | **PASS** |
| **P2 / Low — `__NVIC_PRIO_BITS` 未进 TTS 词表** | `episode.json:64` 已有 `"__NVIC_PRIO_BITS": "N V I C 优先级位数"`；`:473` 旁白使用该词；母版 534.5s 抽帧上屏第 10 行为「那个 4 是 __NVIC_PRIO_BITS，不是寄存器读数」。音频 stamp 与当前旁白重算哈希一致，确认最终母版用的是当前文本。 | **PASS** |
| **P2 / Low — code-14 无依据的 F3 让路链** | `episode.json:484-485` 已改为「S4 那套数：数字越小越优先，15 是最低档」「S4 讲过这套优先级数」；母版 564.8s 抽帧确认上屏为 S4，无 F3/第 14 集的让路链表述。`publish.bilibili.intro:738` 仅保留「第 14 集讲 FreeRTOS 调度器」的集号引用，F3 确为调度器集，成立。 | **PASS** |
| **Low — 母版/时间轴仍旧** | `bilibili.mp4` 653.466667s / 19604 帧 / 30fps；`douyin.mp4` 60.966667s / 1829 帧 / 30fps。两者帧数/30 与容器时长完全相等，drift 0。`bilibili/timeline.json` 25 场、653.466667s；`douyin/timeline.json` 10 场、60.966667s。两条 timeline 的 mtime 20:18/20:32 早于 episode 20:35 的最终保存，但 audio-stamp 哈希按当前旁白重算与两条 timeline 完全一致，最终 build 日志也报「旁白未改动」；母版 20:47/20:48，且 534.5s 已含当前 episode 的 code-13 第 10 行，证明画面用的是当前 episode。`ffmpeg ebur128` 实测两个母版均 -14.8 LUFS。 | **PASS** |
| **Low — factsheet 误报残留** | 同 H2；`factsheet:249` 已是「漏报」。 | **PASS** |
| **Low — code-09 重录/重渲** | 母版 361.5s 抽帧为当前 3361/d29 版；B 站简介 `发布-bilibili.md:32` 为 text 3361。 | **PASS** |

## 2. 新发现

**Low（非阻塞，证据底稿清理项）— factsheet 对 `0xd29` 的发行场景多标了一处。**
`video/research/s5-systick-factsheet.md:199` 把 `0xd29` 标为「B: code-09……；发行（B站）」，但当前 B 站简介（`video/out/s5-systick/发布-bilibili.md:32`）只写 `text 3361 / data 0 / bss 8`，没有 hex 列 `d29/0xd29`。同表的 `3361`、`8` 标「发行（B站）」是对的，`0xd29` 应只保留 `B: code-09`。

**Low（同一处证据措辞）— `numbers.json` 把 `dec` 说成文件字节数。**
`video/research/s5-systick-numbers.json:86` 写「hex 列原样为 d29（目标文件 3369 字节）」。3369 是 size 的 `dec` 列（3361+0+8），不是 `.o` 文件大小；`code/stm32/05-systick/build/probe-arm.o` 实际 5040 字节。建议改为「dec 列为 3369」，不影响上屏与审计。

**备注（非发现）**
- 提供的 `.temp/v2-pilot/frames/bilibili/code-13.png` 是 20:34 的样张，未显示第 10 行；最终母版 534.5s 抽帧已包含「那个 4 是 __NVIC_PRIO_BITS」整行，不是成片缺行。样张 mtime 早于 episode 20:35 的最终保存，建议下次重抽。
- `episode.json:63` 的 `S9` 词表键已无命中文本；`numbers:90` 的 `14` exception 仍引用「F3（第 14 集）」旧措辞，而当前只有 B 站简介的「第 14 集」。均为无上屏影响的残留。

## 3. 抽检（日志 vs 上屏）

| token | 证据 | 结论 |
|---|---|---|
| 3361 / 3369 / d29 | `s5-probe.log:22`；母版 361.5s 抽帧 | 一致 |
| 16799 | 日志 L4、L24；code-09 抽帧 `movw r2, #16799 ; 0x419f` | 一致 |
| 22783 | 日志 L9、L26；code-09 抽帧 `movw r1, #22783 ; 0x58ff` | 一致 |
| 6000 | 日志 L11、L27；code-09 抽帧 `movw r6, #6000 ; 0x1770` | 一致 |
| 0x00010005 / 0x00000005 | 日志 L13；code-03 抽帧 | 一致 |
| 514ms | 日志 L6；封面与 CTA 抽帧 | 一致 |

## 4. 回归检查

- **钩子**：B 站 8.90s、抖音 7.10s，均 ≤15s。
- **章节**：B 站 6 节（寄存器版图 / CTRL 四个位 / 周期=LOAD+1 / 24 位装不下 / 换算与回绕 / Config 与优先级），标题 5/8/9/7/5/11 字；抖音 5 节，场次均在 pick 内且按时间递增。
- **平台时长**：B 站 653.47s 在 480-720s；抖音 60.97s 在 45-75s。
- **场次/字幕**：B 站 25 场 262 条字幕，抖音 10 场 21 条，每场 ≥2 条；`s5-check.log` 两个平台均「0 问题」。
- **数字审计**：`s5-numbers.log` 为 `89 个数字都有依据`，0 报错；codeLabel 已纳入。
- **无屏外读数**：card-07 明说 PF6 逻辑分析仪百分数「本集没拍，屏上一个数都不给」；code-08 明说参考时钟「数据手册写的，本集没测」；双读只声明本机 5 次/0 次。未见板上实测或百分数被当成读数。
- **技术面**：偏移/基址、周期=LOAD+1、24 位上限、COUNTFLAG 读清、优先级 15、737 倍速、49.7 天均与本次日志和 probe 模型一致。
- **封面**：四平台 PNG + `cover-contact-336.png` 齐全；主视觉 514 ms / 24 位倒数，proof 与当前数字一致。
- **残留旧值**：episode、factsheet、numbers、发布文案、SRT 文本均无 `3297 / 3305 / 0xce9 / 247-255`。仅历史复核记录 `s5-systick-review.md`、`s5-systick-review-r2.md` 与 `v2-audit-failures.md` 的故意失败样本保留旧值；SRT 里的 `247/255` 是 cue 序号/时间码，不是主张。

## 5. 结论

r2 的 P0、P1、P2 与 Low 项均已闭合；两个母版、四平台封面、check/numbers 日志与当前 episode 对得上；未发现阻塞性回归。批准。开放项只有上面两条 Low 级证据底稿清理（`0xd29` 的 B 站发行标注、`3369` 的「文件字节」措辞），不影响本集发布。
