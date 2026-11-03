# C4《结构体与 ABI：一行箭头，三份合同》事实底稿

本文件是 `video/episodes/c4-struct-abi/episode.json` 的上屏/口播数字对账底稿。所有输出行都从**本次**运行
`.temp/v2-facts/c4-probe.log`（55 行）原样摘出；`docs/c/04-struct-abi.md` 与源码常量只在「基址、引脚位、
视图刻度」处出现，逐条标明，不冒充 probe 读数。

## 1. 取证信息

| 项 | 值 |
|---|---|
| 源文档 | `docs/c/04-struct-abi.md` |
| 取证脚本 | `code/c/04-struct-abi/probe.sh`（调用 `probe.c`）；`code/c/04-struct-abi/broken.sh`（调用 `broken.c`，并临时生成 `assert-fail.c` 演示失败） |
| 本次日志 | `.temp/v2-facts/c4-probe.log`（55 行；L1–L26 为 broken.sh，L28–L55 为 probe.sh） |
| 宿主工具链 | `gcc`（L2、L30 只打印 `CC: gcc`，**没有版本号**） |
| 编译选项 | `-std=c11 -Wall -Wextra -O0`（L3、L31） |
| 宿主输出 | probe：GPIO_TypeDef 九个偏移 + sizeof、Padded_t / Packed_t、端序、两个位域的 sizeof；broken：Short_t、NoReserved_t / WithReserved_t、Padded_t stride、Packed1_t、一次故意失败的编译原文 |
| 板级 / GDB | 日志**没有**开发板输出，也**没有** GDB 输出；`board-check` 的板上结果状态是「待回填」 |
| 编译失败证据 | L24–L26 是一次真实的失败编译，含编译器原话；不是转述 |
| 数字审计 | `npm run video:numbers -- c4-struct-abi` → `36 个数字都有依据`（§7） |

## 2. 本集必须回答的 5 个问题

1. `GPIOF->BSRR = (1U << 6)` 这一行为什么等于「基址 + 偏移 + volatile」三份合同？展开后的地址怎么来的？
2. `GPIO_TypeDef` 的九个成员、十个寄存器，编译器给出的偏移和大小是否与手册一致？怎样让编译期替人核对？
3. 少写一对方括号与漏补空洞，为什么一个被断言接住、一个编译一声不吭？它们分别改的是偏移还是整块大小？
4. 对齐和尾部填充怎样决定 `sizeof` 与数组 stride？重排、`pack(1)` 各买到什么、赔掉什么？
5. 位域和端序为什么不能直接拿来罩寄存器？可移植的替代写法是什么？收束的五步是什么？

## 3. 上屏数字逐项对账

> 场景写法：`B:` = bilibili，`D:` = douyin，`封面` = 主封面，`发行` = publish 文案。
> 同一行日志里的多个 token 共用一个证据行；每个 token 都列出它实际出现的场景。
> 审计会把十六进制前导零归一化：`0x00` 记为 `0x0`，`0x04` 记为 `0x4`，`0x08` 记为 `0x8`，
> `0x0C` 记为 `0xc`。

### 3.1 官方地图与大小（probe.sh L36–L45）

```text
offsetof(MODER)   = 0x00
offsetof(OTYPER)  = 0x04
offsetof(OSPEEDR) = 0x08
offsetof(PUPDR)   = 0x0C
offsetof(IDR)     = 0x10
offsetof(ODR)     = 0x14
offsetof(BSRR)    = 0x18  <-- target: 0x18
offsetof(LCKR)    = 0x1C
offsetof(AFR)     = 0x20
sizeof(GPIO_TypeDef) = 0x28  <-- target: 0x28
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `0x18` | L42 `offsetof(BSRR) = 0x18`；L8 Short_t 的 BSRR 仍是 `0x18` | B: hook-03、sa-1、cmsis-def、expand、probe-run、static-assert、break-short、board-check；D: hook-03、probe-run、break-short；封面；发行 |
| `0x28` | L45 `sizeof = 0x28`；L8/L9「应为 0x28」；L26 断言原文 | B: cmsis-def、probe-run、static-assert、break-short、break-short-err；D: probe-run、break-short、break-short-err；封面；发行 |
| `0x24` | L8 `Short_t ... sizeof = 0x24`（**不是** GPIO_TypeDef 的大小） | B: cmsis-def、break-short；D: break-short；封面；发行 |
| `0x20` | L44 `offsetof(AFR) = 0x20` | B: sa-1、cmsis-def、probe-run；D: probe-run；发行 |
| `0x1C` | L43 `offsetof(LCKR) = 0x1C` | B: cmsis-def、probe-run、break-short；D: probe-run、break-short |
| `0x14` | L41 `offsetof(ODR) = 0x14` | B: cmsis-def、probe-run；D: probe-run |
| `0x10` | L40 `offsetof(IDR) = 0x10` | B: cmsis-def、probe-run；D: probe-run |
| `0x0C` / `0xc` | L39 `offsetof(PUPDR) = 0x0C`；`howto-assert` 里的 `0x0C` 是 broken.c 的静态断言（见 §3.2） | B: cmsis-def、probe-run、howto-assert；D: probe-run |
| `0x08` / `0x8` | L38 `offsetof(OSPEEDR) = 0x08`；L13 `WithReserved_t DR = 0x8`；L48 `c=8`；L49 `sizeof=8`；掩码左移 8 | B: cmsis-def、probe-run、break-hole、padded-calc、howto-assert；D: probe-run、break-hole；发行 |
| `0x04` / `0x4` | L37 `offsetof(OTYPER) = 0x04`；L12 `NoReserved_t DR = 0x4`；L48 `b=4`；L49 `a=4`；L52 位域 `sizeof=4` | B: cmsis-def、probe-run、break-hole；D: probe-run、break-hole；发行 |
| `0x00` / `0x0` | L36 `offsetof(MODER) = 0x00`；L48 `a=0`；L49 `b=0`；L22 `a=0` | B: cmsis-def、probe-run、break-hole；D: probe-run、break-hole；发行 |
| `10` | L26 断言原文 `(10 x uint32)`；probe.c L36 注释「10 个寄存器 × 4 字节」 | B: static-assert、break-short-err、padded-picture；D: break-short-err、padded-picture |

注：源码注释写「40 = 0x28」，口播只说「四十字节，即 0x28」，没有把 `40` 当独立测量值上屏。

### 3.2 两种错法与断言原文（broken.sh L8–L13、L24–L26）

```text
Short_t: offsetof(BSRR) = 0x18  sizeof = 0x24   (GPIO_TypeDef 应为 0x28)
offsetof(GPIO_TypeDef) 的正确写法见 probe.c：sizeof = 0x28

NoReserved_t:  offsetof(DR) = 0x4   (手册说 0x08)
WithReserved_t: offsetof(DR) = 0x8

编译失败，编译器原话：
assert-fail.c:6:1: error: static assertion failed: "GPIO_TypeDef size must be 0x28 (10 x uint32)"
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `0x24` | L8 `sizeof = 0x24` | B: break-short；D: break-short；封面 `num`；发行 |
| `0x18` | L8 `offsetof(BSRR) = 0x18` | B: break-short；D: break-short；封面；发行 |
| `0x28` | L8/L9「应为 0x28」；L26 断言原文 | B: break-short、break-short-err；D: break-short、break-short-err；封面；发行 |
| `0x04` / `0x4` | L12 `NoReserved_t offsetof(DR) = 0x4` | B: break-hole；D: break-hole；发行 |
| `0x08` / `0x8` | L12「手册说 0x08」；L13 `WithReserved_t DR = 0x8` | B: break-hole、howto-assert；D: break-hole；发行 |
| `0x0C` / `0xc` | **日志没有打印** `sizeof(WithReserved_t)`；`0x0C` 来自 `broken.c` L46 的 `_Static_assert(sizeof(WithReserved_t) == 0x0C, ...)`，该文件在 broken.sh 里编译通过 | B: howto-assert（显示断言源码，不声称是打印值） |
| `6` | L26 报错行号 `assert-fail.c:6:1`；`1U << 6` 的引脚位来自源码/文档 | B: hook-01、hook-02、hook-03、expand、break-short-err、padded-picture、pack-right；D: hook-03、break-short-err、padded-picture、pack-right；封面 |
| `10` | L26 断言原文 `10 x uint32` | B: break-short-err；D: break-short-err；发行 |

注：`broken.c` 的 `Short_t` 与 `assert-fail.c` 里临时写的 `Short_t` 都是「九个 `uint32_t`、AFR 少一对方括号」，
所以大小是 `0x24`；`broken.sh` 最后故意用 `0x28` 断言去压它，失败原文就是 L26。日志只给出报错行，
没有把 `broken.c` 的编译命令行重新打印一遍。

### 3.3 对齐、stride 与 pack（broken.sh L16–L22；probe.sh L48–L49）

```text
Padded_t: sizeof = 12  a=0 b=4 c=8
arr[1] - arr[0] = 12 字节
arr[0].b 距基址 4 字节，arr[1].b 距基址 16 字节
若 sizeof 只算到 c 结束的 9，arr[1].b 就会落在 13 —— 不再是 4 的倍数

Packed1_t: sizeof = 6  a=0 b=1 c=5   (b 落在 1 = 非对齐访问)

Padded_t: sizeof=12, offsets a=0 b=4 c=8
Packed_t: sizeof=8, offsets a=4 b=0 c=5
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `12` | L16 `Padded_t sizeof = 12`；L17 数组间距 `12`；L51 端序最后一字节 `12` | B: sa-3、padded-picture、padded-calc、packed-calc、stride、endian；D: padded-picture、stride；封面；发行 |
| `0` / `4` / `8`（对齐语境） | L16 `a=0 b=4 c=8`；L48 同值；L49 `a=4 b=0 c=5` | B: padded-calc、padded-picture、packed-calc、stride；D: padded-picture；封面；发行（同一 token 在 §3.4 的其他场景另列） |
| `9` | L19「sizeof 只算到 c 结束的 9」 | B: padded-picture、stride；D: padded-picture；发行 |
| `13` | L19「arr[1].b 就会落在 13」 | B: stride；D: stride；发行 |
| `16` | L18 `arr[1].b 距基址 16 字节` | B: stride；D: stride；发行 |
| `6` | L22 `Packed1_t sizeof = 6` | B: pack-right；D: pack-right；封面；发行 |
| `1` | L22 `b=1`（非对齐）；源码 `#pragma pack(push, 1)` | B: pack-right、pack-wrong；D: pack-right；封面；发行 |
| `5` | L22 `c=5`；L49 `c=5`；位域 `c : 5` | B: padded-picture、packed-calc、bitfield-intro、bitfield-rev、pack-right、howto-steps；D: padded-picture |
| `2` | `probe.c` L59 注释「尾部 2 字节填充」；位域 `b : 2`；与打印的 `Packed_t` 总长 8、偏移 0/4/5 一致 | B: cmsis-def、break-short、padded-picture、packed-calc、stride、bitfield-intro、bitfield-rev、howto-steps；D: break-short、padded-picture、stride；发行 |
| `3` | `probe.c` L45/L48 注释「插 3 字节」「尾部再填 3 字节」；`3UL << 1` 掩码 | B: padded-calc、padded-picture、packed-calc、mask-fix、howto-steps；D: padded-picture、mask-fix |
| `7` / `11` | `padded-picture` 的字节刻度 `0..11` 的第 8、12 格；刻度是视图标注，不是 probe 读数 | B: padded-picture；D: padded-picture；`exceptions` |

注：`padded-picture` 的整条刻度 `0 1 2 3 4 5 6 7 8 9 10 11` 都是内存画像的视图标注；其中 `7`、`11`
没有别的出处，已列进 `numbers.exceptions`。其余刻度虽然同时被 `a=0 b=4 c=8`、`sizeof=12` 等读数覆盖，
在画面上仍是刻度用途，不当作独立测量。

### 3.4 位域、端序与掩码（probe.sh L51–L53；probe.c L74–L92）

```text
endian: 0x12345678 stored as 78 56 34 12 -> little-endian
bitfield_1 sizeof=4, bitfield_2 sizeof=4
bitfield layout is implementation-defined; use mask macros for hardware registers
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `0x12345678` | L51 | B: endian；发行 |
| `78` / `56` / `34` / `12` | L51 的四个字节，依次为 `78 56 34 12` | B: endian（`12` 另见 §3.3）；D: 无；发行 |
| `4` | L52 两个位域的 `sizeof=4`；L16/L48 的偏移 4 | B: bitfield-rev、padded-calc、padded-picture、packed-calc、stride、reorder-lesson、howto-steps；D: padded-picture；发行 |
| `1` | `probe.c` L75 `a : 1`；L89 `1UL << 0`；`pack(1)` | B: hook-01、hook-02、hook-03、expand、break-short-err、padded-picture、padded-calc、stride、bitfield-intro、bitfield-rev、mask-fix、pack-right、pack-wrong、howto-steps；D: hook-03、break-short-err、padded-picture、stride、mask-fix、pack-right；封面；发行 |
| `2` | `probe.c` L76 `b : 2`；L90 `3UL << 1` 的位宽 2 | B: cmsis-def、break-short、padded-picture、packed-calc、stride、bitfield-intro、bitfield-rev、howto-steps；D: break-short、padded-picture、stride；发行 |
| `5` | `probe.c` L77 `c : 5`；L22/L49 的 `c=5` | B: padded-picture、packed-calc、bitfield-intro、bitfield-rev、pack-right、howto-steps；D: padded-picture；发行 |
| `24` | `probe.c` L78 / L84 `d : 24`；日志只打印 sizeof，**不打印位序** | B: bitfield-intro、bitfield-rev；D: 无 |
| `3` | `probe.c` L90 `REG_FIELD_B_MASK (3UL << 1)` | B: mask-fix；D: mask-fix |
| `31` | `probe.c` L91 `REG_FIELD_C_MASK (31UL << 3)` | B: mask-fix |
| `0xFFFFFF` | `probe.c` L92 `REG_FIELD_D_MASK (0xFFFFFFUL << 8)` | B: mask-fix |
| `8` | `probe.c` L92 左移 8；L48 `c=8` | B: mask-fix；D: padded-picture（`c=8`，见 §3.3）；发行 |

注：`24`（十进制位宽）与 `0x24`（Short_t 大小）是两个 token，审计也分开记；画面上一处写 `d : 24`，
另一处写 `sizeof = 0x24`。位域的位序、跨单元行为没有打印，本集只用「实现定义」和「日志不打印」来限定。

### 3.5 基址、派生地址与路径（源码常量）

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `0x40021400` | GPIOF 基址，来自 STM32F407 参考手册与 `docs/c/04-struct-abi.md`（`#define GPIOF ... GPIOF_BASE = 0x40021400`，L84）；**probe 只打印偏移，不打印基址** | B: hook-03、gpiof-macro、expand、board-check；D: hook-03；发行 |
| `0x40021418` | 派生值：基址 `0x40021400` + L42 的 `offsetof(BSRR) 0x18`；`docs/c/04-struct-abi.md` L90 同样写法。`board-check` 里它写作「期望」，不是板上读数 | B: expand、board-check；发行 |
| `6` | `1U << 6` 的引脚位，来自 `docs/c/04-struct-abi.md` L90 与源码；不是 probe 输出 | B: hook-01、hook-02、hook-03、expand、break-short-err、padded-picture、pack-right；D: hook-03、break-short-err、padded-picture、pack-right；封面 |
| `1` | `1U << 6`、`1UL << 0`、位宽 `a:1`、`pack(1)` 的源码常量 | B: hook-01、hook-02、hook-03、expand、break-short-err、padded-picture、stride、bitfield-intro、bitfield-rev、mask-fix、pack-right、pack-wrong、howto-steps；D: hook-03、break-short-err、padded-picture、stride、mask-fix、pack-right；封面；发行 |
| `04` | 复现路径 `code/c/04-struct-abi` 的章节号，不是测量值 | B: cta；D: cta；发行；`exceptions` |

注：`board-check` 的 GDB 行显示的是「打印 BSRR 地址应得 `0x40021418`」这一**期望**；本集没有运行 GDB，
所以场景标题与日志都写「待回填」。`0x40021418` 不能被读成 probe 或板上测量值。

### 3.6 封面与发行文案

封面 `proof` / `proofShort` 只用了 `offsetof(BSRR) = 0x18`、`sizeof = 0x28`、Short_t 的 `0x24`，
以及 `Padded 12 / Packed 8 / pack(1) 6`；这些分别落在 §3.1、§3.2、§3.3 的日志行。`num: "0x24"` 指的是
**Short_t** 的大小；`numNote`「少一对方括号，整块短了四字节」里的「四字节」是 `0x28 - 0x24` 的差，
口播与文案没有把它写成独立测量值。

发行文案（B站 / 抖音 / 知乎 / 小红书）出现的 token 组：`0x40021400`、`0x40021418`、`0x18`、`0x28`、
`0x24`、`0x00`、`0x20`、`0x04`、`0x08`、`0`、`1`、`2`、`4`、`5`、`6`、`8`、`9`、`12`、`13`、`16`、
`0x12345678`、`78`、`56`、`34`、`04`。除 `04` 是路径章节号（进 `exceptions`）外，全部落在
§3.1–§3.5 的证据行。发行文案没有出现「板上实测」「GDB 输出」「42 条断言」这类没有日志依据的说法；
GDB 那一行明确写「待回填」。口播 cta 与 B 站简介的「都来自两条脚本」均已限定为**测量值**，并逐项
列出例外（手册基址、引脚位、视图刻度、源码断言），不再声称屏上所有数字都是实测；B 站简介开头也已把
「三份合同摊到本机日志上逐条核对」改为「偏移、对齐、端序摊到本机日志上核对，基址与引脚位对照手册」。

## 4. 不能删的技术断言（删了会让章节断链）

1. **三份合同**：`GPIOF->BSRR` = 基址 `0x40021400` + 结构体偏移 `0x18` + 成员上的 `volatile`。删掉这条，
   片头的「一行箭头」没有拆解对象。
2. **九个成员、十个寄存器**：`AFR[2]` 占两格，九个成员共十个 `uint32_t`，合计四十字节 = `0x28`。删掉这条，
   `10 x uint32` 与大小断言没有落点。
3. **偏移与大小都被机器核对**：L42 打印 `BSRR = 0x18`，L45 打印 `sizeof = 0x28`；`probe.c` 的两条
   `_Static_assert` 把这两个值钉在编译期。删掉这条，「别信打印」讲不成。
4. **少写数组的后果**：`Short_t` 的 `BSRR` 仍在 `0x18`，整块从 `0x28` 掉到 `0x24`，断言接住。删掉这条，
   「偏移对、总大小错」这一型没有现场。
5. **漏补空洞的后果**：`NoReserved_t` 的 `DR` 在 `0x04`，补 `RESERVED` 后回到 `0x08`；这种错编译通过。
   删掉这条，「静默」与「断言接住」的对照消失。
6. **对齐与重排**：`Padded_t` 为 `sizeof=12, a=0 b=4 c=8`；`Packed_t` 为 `sizeof=8, a=4 b=0 c=5`。
   删掉这条，填充差额和「重排买大小」没有数据。
7. **尾部填充买 stride**：数组间距 `12`，`arr[1].b` 在 `16`；若只算到 `9` 就落在 `13`。删掉这条，
   「尾部三字节不是浪费」只剩形容词。
8. **pack(1) 的代价**：`Packed1_t sizeof=6`、`b=1`，非对齐访问。删掉这条，「pack 不能罩寄存器」没有证据。
9. **位域是不可移植的**：两个位域 `sizeof` 都是 `4`，但日志明确说布局是实现定义、位序不打印。删掉这条，
   掩码方案就没有对手。
10. **端序是事实**：`0x12345678` 存成 `78 56 34 12`，判为小端。删掉这条，字节序一节没有现场。
11. **端序与位序分开**：端序可测，位域位序不可测；两者不能互相代替。删掉这条，容易把「小端」误当成
    「位域也按小端排」。
12. **板上待回填**：日志没有 GDB / 板级输出，`0x40021418` 只是期望值。删掉这条，会把派生值冒充实测。

## 5. 已知未取证项（明确「不上屏」或只作叙述前提）

| 项 | 状态 | 处理 |
|---|---|---|
| 板上 GDB 的 BSRR 地址 | 日志没有 GDB，也没有开发板；本集没有跑 | `board-check` 标题与状态写「待回填」；旁白、cta、发行文案都明说「没有板子、没有 GDB 输出」 |
| `gcc` 版本 | L2/L30 只打印 `CC: gcc`，没有版本号 | cta 只说「本机 gcc，C11，O0」，不写任何版本号 |
| `sizeof(WithReserved_t) == 0x0C` | broken.sh 的运行输出没有这一行；`0x0C` 只来自 `broken.c` L46 的静态断言 | `howto-assert` 显示的是断言源码，不声称是打印值；对账表单列说明 |
| ARM / Cortex-M4 的实测 | 日志是宿主 gcc 的输出，没有交叉编译段，也没有 ARM 汇编 | 只讲 C 布局规则；`pack` 的后果说「可能直接报错」，不指定 UsageFault，不冒充实测 |
| `GPIOF_BASE = 0x40021400` | 来自 STM32F407 参考手册与 `docs/c/04-struct-abi.md`，probe 不打印基址 | 归入源码常量；发行文案与 `gpiof-macro` 的 codeLabel 都把它标成手册基址 |
| `0x40021418` | `0x40021400 + 0x18` 的派生值；GDB 行只是期望 | 不写成测量值；`board-check` 明确「期望」与「待回填」 |
| 引脚位 `6` | `1U << 6` 来自文档/源码，不是 probe 输出 | 归入源码常量；口播只说「置位第六位」与地址计算 |
| `Packed_t` 尾部 2 字节、`Padded_t` 的 3 字节填充 | 来自源码注释与总大小/偏移的算术，不是额外打印 | 只作解释；上屏的硬数字仍是 `sizeof` 与 `offsetof` |
| 位域的具体位序 | 日志只打印 `sizeof=4`，明确说布局实现定义 | 不说「本机从高到低/从低到高」；只说「日志不打印，标准不规定」 |
| 内存画像刻度 `7` / `11` | `padded-picture` 的视图刻度，不是 probe 读数 | 进 `numbers.exceptions`；刻度仅用于画洞 |
| `assert-fail.c` 全文 | 脚本临时生成，日志只留一行报错 | 画面只引用编译器原话那一行，不还原整个文件 |

## 6. 与旧对账的关系

- v1 封面 `proof` 写 `sizeof = 0x24 (GPIO_TypeDef 应为 0x28)`，容易被读成 GPIO_TypeDef 自己的大小；
  v2 改成「`Short_t`：BSRR 仍在 `0x18`，sizeof 只剩 `0x24`」，并把 `num` 的语义在 `numNote` 里说清。
- v1 标题问「凭什么是 0x40021418」，把派生地址放在最前面；v2 改成「凭什么落在 0x18」——`0x18` 是 L42
  的打印值，`0x40021418` 只在展开与「期望」里出现，板上状态仍待回填。
- v1 把三条规则说成「焊在 ARM 的调用标准里」；本次日志只有宿主 gcc，没有 ARM 输出。v2 改成「三份合同」
  （基址、偏移、volatile）加 C 布局三规则，不声称本次验证了 ARM ABI。
- v1 `board-check` 说「编译期核实过」，但代码给的是 `&((GPIO_TypeDef *)0)->BSRR` 的 GDB 写法；v2 把
  编译期核实落到 `probe.c` 的两条 `_Static_assert`，GDB 行只保留期望地址与「待回填」。
- v1 `pack-wrong` 说 Cortex-M4 上「可能直接触发 UsageFault」；本次没有 ARM 实测，v2 降为「可能直接报错」，
  不再指定异常类型。
- v1 发行文案说「所有数字都来自本机实测」；v2 把基址、引脚位、派生地址单独标成手册/源码常量，并明说
  板上那格待回填。
- v1 的 40 个场景 id 全部保留；旁白逐场重写。逐句比对（≥6 字的完整句）v1 与 v2 的重合数为 0；
  复核发现的两句短开头「第二条管间隔。」「最后说 pack。」已分别改为「第二条规则管间隔。」「最后看 pack。」
- 共享动画 `docs/public/anim/struct-alignment.svg` 同步修正：删掉伪造的「GDB 板上验证」，改成
  「手册期望 + 板上待回填」；`7 × 4` 的错算改为「前面 6 格 × 4 = 0x18」；删掉把布局规则说成
  AAPCS 的措辞；端序标注为本机 gcc 宿主实测；pack(1) 的 `UsageFault` 绝对断言降为「某些配置下可能访问出错」。

## 7. 审计回填

- `npm run video:lint -- c4-struct-abi`：✅ 通过：bilibili 40 场，douyin 14 场；B 站 6 节，抖音 5 节。
- `npm run video:numbers -- c4-struct-abi`：✅ 36 个数字都有依据（0 未命中）；B 站简介修订后复跑仍为 36/0。
- 旁白字数（实测，逐场景 `narration` 求和）：bilibili 3391 字（Low-2 补条件句后）；douyin 280 字（均落在 3000–3400 / 240–280 目标内，B站余量 9 字）。
- `npm run video:check -- c4-struct-abi`：✅ 通过；bilibili 40 场 + douyin 14 场，排版/节拍审计 0 问题。
- `npm run video:pack -- c4-struct-abi`：✅ 4 平台发布包（简介修订后重新生成）。
- 母版（build4，`.temp/v2-facts/c4-build4.log`）：bilibili 684.3s / 20529 帧 / -14.9 LUFS / 335 拍 / 最长静止 4.2s；
  douyin 59.166667s / 1775 帧 / -15.0 LUFS / 33 拍 / 最长静止 4.0s。
- 漂移：bilibili 0.000000；douyin 0.000000（`|ffprobe − timeline.duration|`）。
- 闸门日志：`.temp/v2-facts/c4-gates-final.log`；`video:test` 100/100 见 `.temp/v2-facts/c4-video-test.log`。
- stills：B站 13 张、抖音 13 张，全部由 build4 终版母版抽取；旧帧已移至 `.temp/c4-stale-stills/`。
