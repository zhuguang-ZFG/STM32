# P4《Cache 一关，你的中断服务函数就不存在了：IRAM 纪律》事实底稿

本文件是 `video/episodes/p4-iram/episode.json` 的上屏/口播数字对账底稿。所有机器码、地址、段长和
体积数字都从**本次**运行 `.temp/v2-facts/p4-probe.log`（227 行，EXIT 0）原样摘出；`docs/esp32/04-irq-dualcore.md`
§一/§二/§三 只在「叙述前提」处出现，并逐条标明，不冒充 probe 读数。本集没有开发板，日志里没有
烧写、示波器、串口或 Cache 关闭窗口的运行时读数。

## 1. 取证信息

| 项 | 值 |
|---|---|
| 源文档 | `docs/esp32/04-irq-dualcore.md` §一（Cache 与取指）、§二（IRAM 纪律）、§三（中断分配器） |
| 取证脚本 | `code/esp32/09-iram-discipline/probe.sh`（八段：现挖宏、打印枚举、`idf.py build`、读 `.map`、`nm`、输入段、`objdump`、`idf.py size`、断言） |
| 本次日志 | `.temp/v2-facts/p4-probe.log`（227 行，EXIT 0） |
| 工具链 | ESP-IDF v5.5.2；目标 esp32s3；binutils `xtensa-esp-elf/esp-14.2.0_20251107`（L6、L121） |
| 构建 | `idf.py build` 完成（L120）；没有烧写，没有板级输出 |
| 反汇编 | 四个 ISR 全文 L149–L185；绝对地址引用计数 L186–L188、断言 L222–L224 |
| 数字审计 | `npm run video:numbers -- p4-iram` → `78 个数字都有依据`（§7） |

日志段落与本集用到的证据：

| 日志行 | 内容 | 本集用途 |
|---|---|---|
| L2–L5 | `esp_attr.h:23` 的 `IRAM_ATTR` 展开；`esp_intr_alloc.h:42` 的 `(1<<10)` | 两个宏、两个动作：改落址 / 改调度 |
| L6–L118 | 编译器打印的中断源枚举、保留位、同值别名、LEVEL1..6 与 NMI | 中断矩阵规模与级别约定 |
| L119–L121 | `idf.py build` 完成、binutils 目录 | 本次链接产物的来源 |
| L122–L130 | `.map` 的 Memory Configuration 八段 | 区间表，所有落址归类的判据 |
| L131–L138 | `nm` 七个符号与归类 | 两个地址、四种写法 |
| L139–L146 | 七个符号的输入段 | `.text.*` / `.iram1.N` / `.rodata.*` |
| L147–L188 | 四个 ISR 的反汇编 | `l32r`/`callx8` 断链、`call8` 同段、常量在 DROM |
| L189–L214 | `idf.py size` 整本账 | 16384/16384、15356+1028、DIRAM 与镜像总量 |
| L215–L227 | 八段断言逐条通过 | 落址、伸手次数、99 的收口 |

## 2. 本集必须回答的 6 个问题

1. **同一次链接，为什么两个 ISR 拿到两个地址，而且都编译通过、都进了镜像？**
   `isr_plain` 在 `0x42008f08`（`iram0_2_seg`，Flash 指令映射窗口）；`isr_tight` 在 `0x403766ac`
   （`iram0_0_seg`，内部 SRAM）。见 `hook-01`、`three-nums`、`regions`、`seven-syms`。
2. **为什么 `IRAM_ATTR` 只是入场券？** 它只把函数放进 `.iram1` 段（L2、L4、L139–L146）；
   断链在调用目标：`isr_leaky` 的 `l32r` 取出 `0x42008f1c` 的 `helper_far`，再 `callx8` 跳过去
   （L165–L169）。见 `two-macros`、`disasm-chain`、`plain-flash`、`reach-count`。
3. **为什么代码进了 IRAM，常量没跟着进？** `isr_rodata` 本体在 `0x40376668`，读的 `k_table` 在
   `0x3c028810`（DROM，L155、L221）。见 `rodata-link`、`section-names`。
4. **`ESP_INTR_FLAG_IRAM` 承诺什么？不声明与声明了没做到有什么区别？** 不声明：系统在写 Flash
   期间推迟中断，安全但延迟不可控；声明了却没做到：系统不再推迟，链上一环在 Flash 就是当场异常。
   见 `promise`、`anim-fate`、`anim-right`、`punch`。
5. **中断矩阵有多大？** `ETS_MAX_INTR_SOURCE = 99`，编号 0–98；98 个名字只覆盖 95 个编号；
   23/33/34/46 是保留位；57/58/59 各被两个同值名字占用（L104–L110）。见 `irq-sources`。
6. **IRAM 的账怎么算？** `idf.py size` 报 IRAM 16384/16384（100.0%），其中 `.text` 15356（93.73%）
   加 `.vectors` 1028（6.27%）（L205–L207）。见 `size-bill`、`budget-math`、`audit`。

## 3. 数字对账

### 3.1 中断矩阵：99、98、95 三个数各指什么

| 数 | 含义 | 证据 |
|---|---|---|
| `99` | `ETS_MAX_INTR_SOURCE` 的值，注释 "number of interrupt sources"；编号槽位是 0–98 | L105、L106、L226 |
| `98` | 枚举里有名字的条目数；最后一个有名字的编号是 98（`ETS_DMA_EXTMEM_REJECT_SOURCE`） | L104、L106 |
| `95` | 98 个名字覆盖的不同编号数；枚举里缺少 23/33/34/46 四个编号 | L106、L107 |

两条算术互相闭合：

- 按名字算：`98 − 3 组同值别名（57/58/59）= 95`；
- 按槽位算：`0–98 共 99 个编号 − 4 个保留位（23/33/34/46）= 95`。

`57/58/59` 的双名结构是 `ETS_SYSTIMER_TARGETn_INTR_SOURCE` 与
`ETS_SYSTIMER_TARGETn_EDGE_INTR_SOURCE` 同值（L108–L110），不是多出三个源。旁白因此说
"99 是槽位数，不是名字数"，没有把 98 或 95 说成 99。

### 3.2 IRAM 与 DIRAM 的账

```text
IRAM    Used 16384  Used[%] 100.0  Remain 0  Total 16384
  .text      15356  93.73%
  .vectors    1028   6.27%
DIRAM   Used 55463  Used[%] 16.23  Remain 286297  Total 341760
  .text      42191  12.35%
  .data      10992   3.22%
  .bss        2280   0.67%
Flash Code   78770
Flash Data   41324   (.rodata 41068 + .appdesc 256)
Total image size: 189693 bytes
```

对账：

| 关系 | 算式 | 结果 |
|---|---|---|
| IRAM 分量 | `15356 + 1028` | `16384`，与 IRAM Total 相等 |
| IRAM 百分比 | `15356 / 16384 = 93.7256%`；`1028 / 16384 = 6.2744%` | 分别四舍五入为 `93.73%`、`6.27%`，相加 `100.00%` |
| IRAM 的另一种写法 | `16384 / 1024` | `16 KiB`，只是单位换算 |
| DIRAM 分量 | `42191 + 10992 + 2280` | `55463`，与 DIRAM Used 相等 |
| DIRAM 剩余 | `341760 − 55463` | `286297` |
| DIRAM 百分比 | `55463 / 341760 = 16.2286%` | 四舍五入为 `16.23%` |
| DIRAM 总量与段长 | `dram0_0_seg` 长度 `0x53700` | `341760`，与 size 的 DIRAM Total 相等 |
| Flash Data | `41068 + 256` | `41324` |

**两个分母不能混**：`16384` 是 `idf.py size` 给本工程的 IRAM 桶；`iram0_0_seg` 的链接器区间长度是
`0x57700 = 358144`。本集在 `size-bill`、`budget-math`、`audit` 和发布文案里都明说这一点，并把
两个数都归为工具链/链接器输出，不是板测容量。

### 3.3 区间表与符号归类

`idf.py build` 的 `.map` 里 Memory Configuration 八段（L123–L130）：

| 段 | 起点 | 长度 | 长度（十进制） | 终点（起点+长度） | 本次落进来的符号 |
|---|---|---|---|---|---|
| `iram0_0_seg` | `0x40374000` | `0x57700` | 358144 | `0x403cb700` | `isr_rodata` `0x40376668`、`isr_leaky` `0x4037668c`、`helper_near` `0x40376698`、`isr_tight` `0x403766ac` |
| `iram0_2_seg` | `0x42000020` | `0x7fffe0` | 8388576 | `0x42800000` | `isr_plain` `0x42008f08`、`helper_far` `0x42008f1c` |
| `dram0_0_seg` | `0x3fc88000` | `0x53700` | 341760 | `0x3fcdb700` | `g_hits` `0x3fc95710`（按区间计算归入；`g_hits` 不在 nm 的七个符号里） |
| `drom0_0_seg` | `0x3c000020` | `0x1ffffe0` | 33554400 | `0x3e000000` | `k_table` `0x3c028810` |
| `rtc_iram_seg` | `0x600fe000` | `0x1fe8` | 8168 | `0x600fffe8` | 本集未使用 |
| `rtc_reserved_seg` | `0x600fffe8` | `0x18` | 24 | `0x60100000` | 本集未使用 |
| `rtc_slow_seg` | `0x50000000` | `0x2000` | 8192 | `0x50002000` | 本集未使用 |
| `extern_ram_seg` | `0x3c000020` | `0x1ffffe0` | 33554400 | `0x3e000000` | 本集未使用；日志里与 drom0_0 同区间，按原样记录，不解释用途 |

归类是"符号地址撞区间"，不是函数名猜的。`g_hits` 的 DRAM 归属是拿 `0x3fc95710` 与
`dram0_0_seg` 区间算出来的，日志没有单独打印"g_hits → dram0_0_seg"这一行，factsheet 在这里标明
推导来源；`k_table`、四个 ISR 和 `helper_far` 的归类则有 L132–L138 与 L216–L221 的直接断言。

### 3.4 四个 ISR 的落址、输入段与伸手次数

| 符号 | 地址 | 段 | 输入段 | 关键指令 | 伸手 |
|---|---|---|---|---|---|
| `isr_plain` | `0x42008f08` | `iram0_2_seg` | `.text.isr_plain` | `l32r` 取 `g_hits`，`retw.n`；八条指令 | 整段在 Flash 窗口 |
| `helper_far` | `0x42008f1c` | `iram0_2_seg` | `.text.helper_far` | 被 `isr_leaky` 的 `l32r` 取出 | 断链目标 |
| `isr_leaky` | `0x4037668c` | `iram0_0_seg` | `.iram1.0` | `entry` / `l32r` / `callx8` / `retw.n` | 往 Flash 伸手 1 处（L222） |
| `helper_near` | `0x40376698` | `iram0_0_seg` | `.iram1.1` | 被 `call8` 直接调用 | 同段 |
| `isr_tight` | `0x403766ac` | `iram0_0_seg` | `.iram1.2` | `entry` / `call8 40376698` / `retw.n`；三条指令 | 往 Flash 伸手 0 处（L223） |
| `isr_rodata` | `0x40376668` | `iram0_0_seg` | `.iram1.3` | 两次 `l32r`：`g_hits` 与 `k_table`；`addx4` 取表项 | 读 DROM 常量 1 处（L224） |
| `k_table` | `0x3c028810` | `drom0_0_seg` | `.rodata.k_table` | `l32r` 的目标 | 常量在 Flash 映射区 |

反汇编原文的关键行：

```text
4037668c <isr_leaky>:
  4037668c: entry   a1, 32
  4037668f: l32r    a8, 403746a0 ... (42008f1c <helper_far>)
  40376692: callx8  a8
  40376695: retw.n

403766ac <isr_tight>:
  403766ac: entry   a1, 32
  403766af: call8   40376698 <helper_near>
  403766b2: retw.n
```

`isr_leaky` 的四条指令都在 `iram0_0_seg`，但 `l32r` 从字面池取出的地址是 `0x42008f1c`，
`callx8` 跳过去就落进 `iram0_2_seg`。`isr_tight` 用 `call8` 直接调到同段的 `0x40376698`，
没有"先取地址再间接跳"那一步。`l32r`/`callx8` 的跨段跳转是反汇编事实；"Cache 关着时取指落空"
是 §一 的叙述前提，不是本次日志的运行时读数。

### 3.5 百分比与取整

- `15356 / 16384 = 93.7255859375` → 工具显示 `93.73`；`1028 / 16384 = 6.2744140625` → `6.27`。
- 两个显示值相加正好 `100.00`，所以 `budget-math` 的加法闭合；这是对工具已四舍五入显示值的复核，
  不是重新测量。
- `55463 / 341760 = 16.228639981...` → `16.23`。
- `16384 / 1024 = 16`，所以口播可以说 "16 KiB"，但 `16 KiB` 与 `16384` 是同一个量的两种写法，
  不是两个独立数字。

## 4. 不能删的技术断言

1. **同一次链接给出两个地址**：`isr_plain 0x42008f08` 在 `iram0_2_seg`，`isr_tight 0x403766ac`
   在 `iram0_0_seg`（L132、L134、L216、L219）。删掉这条，标题不成立。
2. **`IRAM_ATTR` 只改落址**：宏展开是 `_SECTION_ATTR_IMPL(".iram1", __COUNTER__)`（L2、L4）；
   输入段是 `.iram1.0/.1/.2/.3`（L141–L143、L145）。删掉这条，观众会把属性当加速或安全证明。
3. **断链在调用目标**：`isr_leaky` 的 `l32r → 0x42008f1c <helper_far>` 加 `callx8`
   （L167–L168）。删掉这条，"标了还会崩"没有现场。
4. **同段直接调用是反例**：`isr_tight` 的 `call8 40376698 <helper_near>`（L174），伸手 0 处
   （L223）。删掉这条，观众不知道正解长什么样。
5. **常量不跟着代码走**：`isr_rodata` 的 `l32r` 目标是 `0x3c028810` 的 `k_table`，归入
   `drom0_0_seg`（L155、L221）。删掉这条，第四环漏掉。
6. **`ESP_INTR_FLAG_IRAM` 是承诺不是能力**：`(1<<10)`（L3、L5）；不声明会被推迟、声明了没做到
   会崩，是 §二 的权责说明。删掉这条，第 10 位只剩一个数字。
7. **矩阵的三个数**：99 是 `ETS_MAX_INTR_SOURCE`（L105），98 个名字（L106），95 个不同编号
   （L106），4 个保留位与 3 组同值别名（L107–L110）。删掉这条，"99 个源"会重新变成行数。
8. **级别位号就是级别号**：`LEVEL1..6 = 1<<1..1<<6`（L112–L117），`NMI = 1<<7` 且注释写
   Level 7（L118）；第 10 位是 IRAM 特性（L3），不是第 10 级。删掉这条，位号会被读成级别。
9. **IRAM 账单闭合**：`15356 + 1028 = 16384`，`93.73% + 6.27% = 100.00%`（L205–L207）。
   删掉这条，100.0% 会被当成"芯片所有 SRAM 已满"。
10. **两个分母**：size 的 IRAM 桶 `16384` 与链接器 `iram0_0_seg` 的 `0x57700 = 358144`
    （L123、L205）不是同一本账。删掉这条，"100.0%"会被误读成物理容量。

## 5. 已知未取证项

| 项 | 状态 | 处理 |
|---|---|---|
| Cache 写 Flash 时关闭 | §一 的文档叙述，本次日志没有 Cache 控制器读数、没有关闭窗口实验 | 只作叙述前提；旁白明说本集没有板测、没有跑真正的 Cache 关闭窗口 |
| 不声明则中断被推迟 / 声明了没做到则崩 | §二 的机制说明，日志没有运行时崩溃或延迟数据 | 只讲机制与承诺；`promise` 场景用 `1<<10` 的源码注释作锚点 |
| `iram0_0_seg` 是内部 SRAM、`iram0_2_seg` 是 Flash 映射窗口 | 段名与 §一/§二 的语义；日志只给区间与地址 | 作叙述前提；不把段语义说成 probe 打印 |
| `g_hits → dram0_0_seg` | 由地址 `0x3fc95710` 与区间计算，日志无单独断言行 | 在 §3.3 标明推导；旁白说"按区间表落在 DRAM" |
| `__COUNTER__` 每展开一次加一 | C 预处理器语义；日志只展示 `.iram1.0/.1/.2/.3` 四个不同后缀 | 用输入段结果作证，不声称日志打印了计数器 |
| 编译器是否内联 | 本次日志没有内联报告 | 清单只说"别赌内联"，不报内联结果 |
| `IRAM_ATTR` 管不到被调函数与常量 | 由落址与反汇编证明（`helper_far`、`k_table`），不是编译器文档引用 | 作为结论讲，不补未打印的编译器行为 |
| v1 的 75 字节固定代码总量、`0xb/0x14/0x8/0x24` 分段大小 | 本次日志没有 `nm -S` 或分段尺寸 | 全部删除，不上屏 |
| v1 的 `-Wl,--gc-sections` 首版 nm 只剩两个符号 | 本次日志是最终构建，未复现该中间状态 | 删除 `gc-trap` 场景，不把源码注释当本次证据 |
| v1 的双核、`portMUX`、`tskNO_AFFINITY`、`volatile` | 不在 §一/§二/§三，也不在本次日志 | 删除 `dual-core`、`volatile-bill`、`pinned-core`，不补数字 |
| 板级烧写、串口、示波器、Cache 关窗实测 | 本集不需要开发板，日志没有这些输出 | 不上屏任何板级读数；发布文案明说不是板测 |

## 6. 与旧稿的关系

v1 是 25 场、3500 字、约 702.7 s，无分节，音色 `zh-CN-YunxiNeural`、rate `+4%`。v2 仍是 25 场，
3319 字，5 节，音色 `zh-CN-YunyangNeural`、rate `+2%`，按 v2 回归估算约 647 s。

### 6.1 场景 id

保留 21 个：`hook-01`、`three-nums`、`anim-normal`、`anim-window`、`anim-fate`、`two-macros`、
`regions`、`seven-syms`、`disasm-chain`、`rodata-link`、`section-names`、`anim-right`、`checklist`、
`size-bill`、`irq-sources`、`irq-levels`、`vs-nvic`、`audit`、`punch`、`cta`、`teaser`。

删除 4 个：

| v1 id | 删除原因 |
|---|---|
| `gc-trap` | 依赖 `-Wl,--gc-sections` 与"首版 nm 只剩 app_main 和 g_hits"的中间态；本次日志是最终构建，没有这段输出 |
| `dual-core` | 双核分工在 §四，不在本集指定的 §一/§二/§三，也不在本次日志 |
| `volatile-bill` | 共享数据的 `volatile`/屏障讨论在 §五，不在本次日志 |
| `pinned-core` | `tskNO_AFFINITY`、`0x7FFFFFFF`、`xTaskCreatePinnedToCore` 均不在本次日志 |

新增 4 个，全部由本次证据直接支撑：

| v2 id | 作用 |
|---|---|
| `plain-flash` | 把不标的 `isr_plain` 整段反汇编摆出来，补全"两个地址"的另一半 |
| `reach-count` | 用 L222–L224 的伸手次数（1/0/1）给四种写法做体检单 |
| `promise` | 把不声明与声明了没做到的后果单独成场，接第 4 个故事问题 |
| `budget-math` | 把 15356 + 1028 = 16384 与两个分母单独算一遍，接第 6 个故事问题 |

### 6.2 删除的旧数字与旧说法

- "应用钉进 IRAM 的代码共 75 字节"、输入段尺寸 `0xb/0x14/0x8/0x24`：本次日志没有 `nm -S`，
  也没有这些尺寸；v2 改用 `.iram1.0/.1/.2/.3` 段名与七个符号的地址，不报字节数。
- "iram0_0_seg 五十多万字节"：`0x57700 = 358144`，不是五十多万。v2 只写 `0x57700` / `358144`，
  并把 `16384` 与它并列成两个分母。
- `tskNO_AFFINITY = 0x7FFFFFFF`、`portMUX_TYPE`、`volatile`、`-Wl,--gc-sections`、初代 ESP32
  `0x400xxxxx` 对照：全部不属于本次日志，v2 不出现。
- v1 的 `0x29c` 等字面池偏移：v2 只保留 `40374698`、`4037469c`、`403746a0` 三个本次反汇编实际
  打印的地址；`0x29c` 只作为日志里的符号注释存在，不上屏。

### 6.3 句子复用检查

用 Python `difflib.SequenceMatcher` 对 v1/v2 的 bilibili 旁白（按场景顺序拼接）做比对：

- 相似度 `ratio = 0.4043`；
- 最长公共片段 28 字："进这个工程，一条脚本跑完八段取证和全部断言。不需要开发板"；
- 按中文句号/问号/感叹号切句后，**原样复用的完整句子 0 条**。

v2 没有沿用 v1 的整句；28 字片段是复现说明里的技术短语，不是叙事句。

## 7. 审计回填

### 7.1 两条命令

```text
$ npm run video:lint -- p4-iram
> mcu-road@0.1.0 video:lint
> node video/src/cli.mjs lint p4-iram

▶ p4-iram  Cache 一关，你的中断服务函数就不存在了：IRAM 纪律  [bilibili, douyin]
  ✅ 通过：bilibili 25 场，douyin 10 场

✅ 全部通过
```

```text
$ npm run video:numbers -- p4-iram
> mcu-road@0.1.0 video:numbers
> node video/src/cli.mjs numbers p4-iram

✅ p4-iram: 78 个数字都有依据
```

### 7.2 预算

| 平台 | 场景 | 节 | 旁白字数 | 目标 | 硬边界 | 估算时长 |
|---|---|---|---|---|---|---|
| bilibili | 25 | 5 | 3319 | 3000–3400 | 2087–3510 | 约 647 s |
| douyin | 10 | 4 | 276 | 240–280 | 141–311 | 约 65 s |

钩子：只有 `hook-01` 一个 `kind: "hook"`，旁白 69 字，按 v2 回归 `0.1955 s/字` 估算约 13.49 s，
低于 15.0 s；实际以构建时 TTS 时长为准。

节拍：本稿没有显式 `beatMap`，由 `deriveBeats` 在构建时按字幕自动分拍（`n = max(2, 字幕数)`），
并在每 6 s 静止处插 `pulse`；`validateBeats` 会在构建时强制"每场 ≥2 拍、时间递增、静止空档
≤6.05 s"。因为没有任何 `beatMap` 的 `at`/`reveal` 值，本稿不存在 0 基闭区间越界的输入；
按 brief 未跑 build/check，实际拍数以构建日志为准。用合成字幕（按标点均分场景时长）跑
`deriveBeats` + `validateBeats` 的本地演练通过：bilibili 25 场、douyin 10 场均 ≥2 拍，
最大空档约 3.2 s；这不是 TTS 实测，只证明无 `beatMap` 时自动路径不会产生单拍场景。

### 7.3 额外核查

- v1/v2 数字 token 对比：v1 宽松扫描 104 个 token；v2 的 numbers 审计口径是 78 个，全部有依据。
  v2 新增 `0x3fc95710`、`4037469`、`40374698`、`420009` 等本次反汇编/字面池 token，删除 v1 的
  75、`0x7fffffff`、`0xb/0x14/0x8/0x24` 等。
- 旧说法 grep（只查 `episode.json` 与 `p4-iram-numbers.json`）：`75 字节`、`0x7fffffff`、
  `tskNO_AFFINITY`、`portMUX`、`gc-sections`、`0x29c`、`0xb`、`0x14`、`0x24`、`五十多万`、
  `volatile`、`双核`、`0x400xxxxx` 均为 0 命中。
- 所有 `codeB` 场景都有显式 `codeBLabel`：`two-macros`（标志位改调度）、`disasm-chain`
  （`isr_tight` 三条指令）、`irq-levels`（同一批 flag）、`size-bill`（链接器同一份产物的段区间）。
  没有场景落到布局默认值 `-O2 编出来的汇编`。
- `emphasis` 全部是上屏文本的字面子串：`两个地址`、`99`、`窗口`、`推迟`、`搬家`、`0x42000020`、
  `helper_far`、`callx8`、`0x42008f08`、`0 处`、`k_table`、`.iram1`、`整条链`、`FromISR`、
  `1<<10`、`95`、`0–98`、`0x57700`、`16384`、`v5.5.2`、`入场券`、`一条命令`、`Cache`。
