# S5《SysTick：内核的心跳》独立审稿

Verdict: CHANGES_REQUIRED

## 硬检查

1. **数字账本 — FAIL。** `npm run video:numbers -- s5-systick` 报“78 个数字都有依据”，但 `numbers.mjs` 的 `SCENE_FIELDS` 不含 `codeLabel`，tokenizer 的负向后顾又会跳过 `bit16` 这类标识符内数字，所以绿勾不是全量。15 个必查 token 都能在本次日志找到行（见下表），另抽 0x00000007/0xF0（L12）、1512001/1512010（L7）、5.95ppm（L6）、10.3.1（L19）、3297（L22）、0x419f（L24）也都有行。缺口见 H3。
2. **分节结论 — PASS（结构）。** B 6/6：card-01/code-01/code-02→换 Cortex-M 同一份初始化；card-02/code-03/code-04→读一次存变量；card-03/code-05/code-06→忘减一亏相位；card-04/code-07/08/09→100ms 拒配、硬写 737×；card-05/code-10/11/12→先减再比；card-06/code-13/14→优先级 15 最低。D 5/5：card-01→四寄存器；code-03→读清；card-03+code-06→LOAD+1/相位；card-04+code-08→24 位/737×；code-11→回绕先减再比。每节末句都是结论；第 5 节结论本身被 C1 证伪。
3. **钩子 — PASS。** `hook-01` 8.9s（267 帧/30fps，timeline.json）；首句 0.22s“写 167999 还是 168000？”，无问候、无集号。
4. **抖音 — PASS（脚本层）。** 10 场；旁白 265 字；估算 265×0.1946+10×1.091=62.48s；末句“忘掉减一亏的是相位，标志只要读一次就没，所以超时只能先减再比。”；仅 `then=0xFFFFFC18  now=5000` 这一行 29 字与横版相同，没有 120 字取证行逐字复用。构建备注：`video/out/s5-systick/douyin/timeline.json` 还是 10-17 的 12 场旧稿，发布前必须重渲。
5. **平台限制 — PASS。** B 旁白 3221 字；3221×0.1955×1.049=660.6s≤720。XHS 标题 18 字、正文 773 字，无 URL/GitHub 字样，合集“通往单片机之路”非空，置顶含 `sh code/stm32/05-systick/probe.sh`。知乎有 titles/intro/domain/mark/original/markNote/tags/topics。
6. **表外断言 — FAIL（一处）。** `code-13` 的“probe 并没有打印它”不在 fact sheet，且被本次日志 [6]“4 位里的最低档”直接证伪；其余已知未取证项处理正确：card-07 不给百分数、不称板上复现，code-08 不给 HCLK/8 周期，全片无板上 ISR 延迟数字。
7. **TTS — PASS（有旗）。** 无 `ttsText` 覆盖；lexicon 覆盖 0xE000E010/0xFFFFFC18/0xF0、CTRL/LOAD/VAL/CALIB/SHP、SysTick/offsetof/ppm/ms/us/ns。未覆盖且可能误读：ARM（易读成英文 arm）、PATH、PF6、S4/S5/S9；建议抽听后补表。
8. **技术正确性 — FAIL。** 错：C1 的 5us 换算；H2 的“误报/漏报”；H1 的“probe 没打印 4”；“第 49 天必爆”（2^32 ms=49.71 天，实际在第 50 天）；“开时钟”把 CLKSOURCE 说成开关；“机身”实际是 `-c` 目标文件。对：偏移 0x0/4/8/C、基址 0xE000E010、周期=LOAD+1、24 位上限 16777215/99864us、4 位下优先级 15、COUNTFLAG 读清、100ms 拒配/737×/135.6us/514ms。
9. **结构 — PASS。** B 六节标题 5/8/9/7/5/11 字，均≤12；D 五节；B 52 个、D 13 个覆盖版 emphasis token 全部能在对应上屏文本中找到；beatMap 的 at 1–8 均在该场字幕序号内；B 25 场每场至少 2 句字幕。
10. **收尾 — PASS。** `cta`：“S5 是系列的最后一站……整章全文和代码都在开源书里……前面十七集也在同一个仓库”，无下一集预告；`series.json` 的 `next` 为空。小瑕：code-12 的“S9 的采样超时”指向 backlog 章节，但不在收尾。

### 抽检 token 与日志行

| token | 本次日志证据 |
|---|---|
| 514ms | L6“日漂移 514ms” |
| 167999 | L4“1ms → LOAD=167999”；L5 模型 |
| 168000 | L5“周期 = LOAD+1 = 168000 周期” |
| 1680000 | L5“跑 1680000 周期”；L6 同 |
| 0xE000E010 | L3 布局行 |
| 0x00010005 | L13 第一次读 |
| 0xFFFFFF / 16777215 / 99864us | L8 24 位上限行 |
| 22783 / 135.6us / 737 | L9 强行掩码行 |
| 0xFFFFFC18 / 6000ms | L11 回绕行 |
| 42 | L15 HOST_ASSERTS=42；L16 42/42 |
| 0x00000007 / 0xF0 | L12 Config 行 |
| 1512001 / 1512010 | L7 相位行 |
| 5.95ppm | L6 漂移率 |
| 10.3.1 / 3297 / 0x419f | L19 / L22 / L24 交叉段 |

## 必须修（pilot gate 前，4 项）

1. **[Critical] C1 — `bilibili/card-05` + `code-10`：把截断讲成无损。** 上屏“整数公式 ns=c*1000/168：c=1 → 5ns、c=1000 → 5us”；旁白“一千个周期算出 5 微秒”“整 us 时恰好无损”“这里没有任何四舍五入”。实际 1000 周期 = 5952ns = 5.952us；`5us` 是整数微秒截断，丢了 952ns。`probe.c:191` 自己的注释都写着“真值 5.952”。应改探针输出与旁白：用 c=168→1us 做无损例，或明说“5us 是截断值，真值 5.952us”。
2. **[High] H1 — `bilibili/code-13`：假称探针没打印 4。** 上屏“那个 4 在头文件里，没打印”；旁白“probe 并没有打印它”。本次日志 [6] 明写“（4 位里的最低档……）”。应改成“4 不是寄存器读数，是 `__NVIC_PRIO_BITS`；probe 只在说明文字里提了 4 位”。
3. **[High] H2 — `bilibili/code-11`、`douyin set code-11`、B 站简介：把漏报写成误报。** 上屏“在 now=2000 时误报未超时”；简介“会在回绕处误报未超时”；而同一场旁白说“这属于漏报而不是误报”。`now>=then+timeout` 是漏报（false negative），不是误报。统一改为“误判/漏报未超时”。
4. **[High] H3 — 数字账本与审计覆盖不足。** `card-02`“bit16 COUNTFLAG”与 `code-03`“bit16”的 16 无 evidence 行；`code-02` codeLabel“core_cm4.h:764-770”、`code-04` codeLabel“probe.c:247-255”是源码行号，无 exception 行；`code-09` 的 `ce9`、`cta`“前面十七集”的 17 也无行。另 `4` 行只引 [4]（“4 位”在 [6]），`5` 行只引 [5]（“5 个周期”在 [7]），语义对不上。补 evidence/exception，或把 `codeLabel` 与 `bit16` 纳入审计。

## 编辑建议（不阻塞 gate）

5. **[Medium] 49 天精度。** `punch`“第 49 天必爆”、旁白“第四十九天必定爆掉”。2^32 ms=49.71 天，绕回发生在第 50 天；建议“约 49.7 天”或“第 50 天”。
6. **[Medium] CLKSOURCE 措辞。** `card-02` 旁白“开时钟开中断还开计数”：bit2 是选时钟源，不是开时钟；ENABLE 才是开计数。建议“选内核时钟”。
7. **[Medium] “机身”过度。** `code-09` 标题“编进 Cortex-M4 的机身”、旁白“搬进了机身”；日志明确 `-c` 只编不链、没有链接地址。说“目标文件/机器码”更准确。
8. **[Low] TTS 词表。** 补 ARM、PATH、PF6、S4/S5/S9；目前无 `ttsText`，也没有需要辩护的局部覆盖。
9. **[Low] 收尾全称。** `cta`“屏幕上出现的每一个数……全部来自本机这一条命令”过宽：codeLabel 行号、`0x00C` 头文件写法和交叉段常数不是这条宿主命令的产物。改为“这些 probe 数”即可。
10. **[Low] 抖音 punch 是四条 recap。** 严格按“每场一个点”，punch 四句并列；作为收尾可接受，但若执行字面标准，应收成一句。
11. **[Low] 抖音母版未重渲。** `out/douyin/timeline.json` 是 10-17 的 12 场旧稿（hook-02/code-04/code-05/code-10/code-13/card-06），与新 10 场脚本不对应；发布前重渲并回读 62–69s。
12. **[Low] S9 前向引用。** `code-12`“S9 的采样超时”指向 backlog 章节；不在收尾，但与“系列最后一站”略有张力，可标“待建”或删。

## 结论

结构、平台限制、钩子、抖音脚本参数和收尾都过线；但一个 Critical 数学错误、两个证据/术语自相矛盾、一个账本覆盖漏洞，使本集还不能进 pilot gate。修完 C1/H1/H2/H3 后重跑 `video:numbers`、重录受影响旁白并重渲横竖母版。
