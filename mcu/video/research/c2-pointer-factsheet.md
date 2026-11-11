# C2《指针：地址、宽度、纪律》事实底稿

本文件是 `video/episodes/c2-pointer/episode.json` 的上屏/口播数字对账底稿。所有输出行都从**本次**运行
`.temp/v2-facts/c2-probe.log` 原样摘出，不转述旧结论；旧稿 `.trellis/tasks/...` 与 `docs/c/02-pointer.md`
只在「例外」一节用来解释源码位号，不作为本次读数。

## 1. 取证信息

| 项 | 值 |
|---|---|
| 源文档 | `docs/c/02-pointer.md` |
| 取证脚本 | `code/c/02-pointer/probe.sh`（调用 `probe.c`） |
| 本次日志 | `.temp/v2-facts/c2-probe.log`（121 行） |
| 运行方式 | 脚本内三段：`arm-none-eabi-gcc -O2 -S` 看汇编；宿主 `gcc -O2` 真跑 `main()`；最后 `-DBAD_*` 三次反例 |
| 宿主工具链 | `gcc 16.1.0`（日志 L103） |
| 交叉工具链 | `arm-none-eabi-gcc 15.2.1`（日志 L2，本次在 PATH 中，交叉段真的跑了） |
| 宿主断言 | 日志 L110 只写 `全部断言通过`，**没有打印条数**；本集因此不写「多少条断言」 |
| 数字审计 | `npm run video:numbers -- c2-pointer` → 30 个数字都有依据（§7） |

## 2. 本集必须回答的 5 个问题

1. `0x40021418` 这个地址从哪来？为什么说它是 `0x40021400 + 0x18` 算出来的？
2. 同一个 `*p`，`uint8_t*` / `uint16_t*` / `uint32_t*` 为什么会编出 `ldrb` / `ldrh` / `ldr` 三条指令？
3. `p + 1` 到底加几？为什么偏移会直接印在指令里（`#1` / `#2` / `#4`）？
4. 为什么 `6 * sizeof(uint32_t) == 0x18` 能写成编译期静态断言，它和外设寄存器块是什么关系？
5. `const` 在星号左边、右边、两边，各锁谁？三个违规版本为什么一条都跑不起来？

## 3. 上屏数字逐项对账

> 场景写法：`B:` = bilibili，`D:` = douyin，`封面` = 主封面，`发行` = publish 文案。
> 同一行日志里的多个 token 共用一个证据行；每个 token 都列出它实际出现的场景。

### 3.1 交叉工具链与命令行（日志 L1–L3）

```text
== 交叉工具链 ==
arm-none-eabi-gcc.exe (xPack GNU Arm Embedded GCC x86_64) 15.2.1 20251203
== 命令行: arm-none-eabi-gcc -std=c11 -Wall -Wextra -O2 -mcpu=cortex-m4 -mthumb -S probe.c -o build/probe.m4.s ==
```

| 上屏 token | 场景 |
|---|---|
| `15.2.1` | B: cta；D: cta；发行（B站） |
| `2` | B: addr-03、step-01、step-05、disc-01、punch；D: step-01、step-05、punch；封面；发行（B站/小红书） |

注：`-O2` / `Cortex-M4` 里的 2/4 前面紧贴字母，审计不会把它们切成独立数字 token；它们只随
`width-01/codeBLabel` 原样显示，不单独构成数字主张。`-O0` 本集没有上屏。

### 3.2 现场 1：读方向三种宽度（日志 L5–L25）

```text
-- 现场1 读：uint8_t*/uint16_t*/uint32_t* 解引用 --
read8:
	ldrb	r0, [r0]	@ zero_extendqisi2
	bx	lr

read16:
	ldrh	r0, [r0]
	bx	lr

read32:
	ldr	r0, [r0]
	bx	lr
```

| 上屏 token | 场景 |
|---|---|
| `ldrb` | B: width-01、width-02、width-04、step-01、sum-03、punch；D: width-01、step-01、punch；封面 proof/proofShort；发行（B站/知乎/小红书） |
| `ldrh` | B: width-01、width-02、step-01、sum-03、punch；D: width-01、step-01、punch；封面 proof/proofShort；发行（B站/知乎/小红书） |
| `ldr` | B: width-01、width-02、step-01、step-04、step-05、sum-03、punch；D: width-01、step-01、step-04、step-05、punch；封面 proof/proofShort；发行（B站/知乎/小红书） |

注：横版 v2 封面不渲染 `proof`，竖版渲染 `proofShort`；两处都含读方向三条指令。`ldr` 还以
`ldr r3, ...` 的形式出现在现场 3 的两份汇编里。

### 3.3 现场 1：写方向三种宽度（日志 L27–L47）

```text
-- 现场1 写：三种宽度的赋值 --
write8:
	strb	r1, [r0]
	bx	lr

write16:
	strh	r1, [r0]	@ movhi
	bx	lr

write32:
	str	r1, [r0]
	bx	lr
```

| 上屏 token | 场景 |
|---|---|
| `strb` | B: width-03；发行（B站）；封面不渲染 proof，proofShort 也不含写方向 |
| `strh` | B: width-03；发行（B站）；封面不渲染 proof，proofShort 也不含写方向 |
| `str` | B: width-03、step-04、step-05；D: step-04、step-05；发行（B站）；封面不渲染 proof，proofShort 也不含写方向 |

注：`str` 还以 `str.w` 的形式出现在 step-05 的 objdump 原文里。

### 3.4 现场 2：`p[1]` 的地址增量（日志 L49–L69）

```text
-- 现场2：p[1]（= *(p+1)）的地址增量 --
next8:
	ldrb	r0, [r0, #1]	@ zero_extendqisi2
	bx	lr

next16:
	ldrh	r0, [r0, #2]
	bx	lr

next32:
	ldr	r0, [r0, #4]
	bx	lr
```

| 上屏 token | 场景 |
|---|---|
| `#1` / `1` | B: hook-01、addr-02、addr-03、step-01、step-06、sum-01、punch；D: hook-01、step-01、punch；封面；发行（B站/抖音/知乎/小红书） |
| `#2` / `2` | B: addr-03、step-01、step-05、disc-01、punch；D: step-01、step-05、punch；封面；发行（B站/小红书） |
| `#4` / `4` | B: addr-03、addr-04、step-01、punch；D: addr-04、step-01、punch；封面；发行（B站/抖音/小红书） |

注：`#N` 是 objdump 的立即数写法，审计把它们规范成 `1/2/4`；与 `sizeof` 的 1/2/4 是同一组数。

### 3.5 现场 3：索引 vs 宏、静态断言、字面量池（日志 L71–L100）

```text
-- 现场3：BSRR 两种写法（索引 vs 宏）--
led_on_indexed:
	ldr	r3, .L12
	mov	r2, #4194304
	str	r2, [r3, #1048]
	bx	lr

led_on_macro:
	ldr	r3, .L15
	mov	r2, #4194304
	str	r2, [r3, #1048]
	bx	lr

（_Static_assert 已随上面编译通过：6*sizeof(uint32_t)==0x18）

-- 现场3 补一刀：那个 .L12 里装的到底是什么（-c + objdump）--
== 命令行: arm-none-eabi-gcc -std=c11 -Wall -Wextra -O2 -mcpu=cortex-m4 -mthumb -ffunction-sections -c probe.c -o build/probe.o ==
00000000 <led_on_indexed>:
   0:	ldr	r3, [pc, #8]	@ (c <led_on_indexed+0xc>)
   2:	mov.w	r2, #4194304	@ 0x400000
   6:	str.w	r2, [r3, #1048]	@ 0x418
   a:	bx	lr
   c:	.word	0x40021000
（两条都到位：0x40021000 + 0x418 = 0x40021418，就是片头那个地址）
```

| 上屏 token | 场景 |
|---|---|
| `4194304` | B: step-04、step-05、step-06；D: step-04、step-05；发行（B站/抖音） |
| `1048` | B: step-04、step-05；D: step-04、step-05 |
| `0x400000` | B: step-05、step-06；D: step-05 |
| `0x418` | B: step-05；D: step-05；封面；发行（B站/知乎/小红书） |
| `0x40021000` | B: step-05；D: step-05；封面；发行（B站/知乎/小红书） |
| `0x40021418` | B: hook-01、addr-03、addr-04、step-05、sum-01、punch；D: hook-01、addr-04、step-05、punch；封面；发行（B站/抖音/知乎/小红书） |
| `6` | B: addr-03、addr-04、step-03、step-05；D: addr-04、step-05；封面；发行（B站/抖音/小红书） |
| `0x18` | B: addr-03、addr-04、step-03、punch；D: addr-04、punch；封面；发行（B站/抖音/知乎/小红书） |
| `0xc` | B: step-05（`@ (c <led_on_indexed+0xc>)`） |

注：`step-05` 里的 `6` 来自 objdump 的地址列 `6:`，与 `6*sizeof` 的 6 是同一数字 token；
`addr-03` 里的 `6` 来自 `[6]` 与 `6*4`。

### 3.6 宿主 `main()`：sizeof、步长、寄存器索引（日志 L102–L110）

```text
== 宿主工具链 ==
gcc.exe (x86_64-posix-seh-rev1, Built by MinGW-Builds project) 16.1.0
== 命令行: gcc -std=c11 -Wall -Wextra -O2 probe.c -o build/probe_host.exe && ./build/probe_host.exe ==
sizeof: uint8_t=1 uint16_t=2 uint32_t=4  指针自身=8 字节
p+1 字节增量: uint8_t* +1  uint16_t* +2  uint32_t* +4
寄存器索引: &((uint32_t*)0x40021400)[6] = 0x40021418 (= 基址 + 6*4 = +0x18)
const 三组合(合法半边): *pc=2 *cp=42 *cpc=2
驱动惯用法: volatile uint32_t * const gpiof = 0x40021400（指针锁死，目标可被硬件改）
全部断言通过
```

| 上屏 token | 场景 |
|---|---|
| `16.1.0` | B: cta；D: cta；发行（B站） |
| `1` | B: hook-01、addr-02、addr-03、step-01、step-06、sum-01、punch；D: hook-01、step-01、punch；封面；发行（B站/抖音/知乎/小红书） |
| `2` | B: addr-03、step-01、step-05、disc-01、punch；D: step-01、step-05、punch；封面；发行（B站/小红书） |
| `4` | B: addr-03、addr-04、step-01、punch；D: addr-04、step-01、punch；封面；发行（B站/抖音/小红书） |
| `8` | B: addr-03、step-05；D: step-05；封面；发行（B站/小红书） |
| `0x40021400` | B: addr-03、addr-04、disc-04、punch；D: addr-04、punch；发行（B站/抖音/知乎/小红书） |
| `0x40021418` | 见 §3.5 |
| `0x18` | 见 §3.5 |
| `42` | B: disc-01 |

注：`指针自身=8 字节` 是**宿主**口径，旁白与 codeLabel 都明写「本机/宿主 gcc」，不冒充开发板读数。
`0x40021400` 不在封面文案里，封面的基址是字面量池里的 `0x40021000`。

### 3.7 const 三个反例（日志 L112–L121）

```text
-- const int *p：*p = 1：如期编译失败 --
probe.c:50:52: error: assignment of read-only location '*p'

-- int * const p：p = &b：如期编译失败 --
probe.c:52:58: error: assignment of read-only variable 'p'

-- const int * const p：*p = 1：如期编译失败 --
probe.c:54:59: error: assignment of read-only location '*(const int *)p'

（以上三条全是编译期拦截：const 不要钱，跑都不用跑）
```

| 上屏 token | 场景 |
|---|---|
| `50` | B: disc-02（`probe.c:50:52`）；D: disc-02 |
| `52` | B: disc-02（`probe.c:50:52` 与 `probe.c:52:58`）；D: disc-02 |
| `54` | B: disc-02（`probe.c:54:59`）；D: disc-02 |
| `58` | B: disc-02（`probe.c:52:58`）；D: disc-02 |
| `59` | B: disc-02（`probe.c:54:59`）；D: disc-02 |

注：这五个数是编译器报错原文里的**源码行号/列号**，不是测量值；放 `exceptions`。

### 3.8 编号/路径/源码位置类 token

| 上屏 token | 场景与含义 |
|---|---|
| `02` | 复现路径 `code/c/02-pointer` 的章节号；B: cta；D: cta；发行（B站/抖音/知乎/小红书）；`exceptions` |
| `22` | BSRR 的寄存器位号：`probe.c:40` 源码 `1UL << (6U + 16U)`，`docs/c/02-pointer.md:82` 写作 `1UL << 22`；probe 日志只打印常量 `4194304`，不打印 `22`；B: hook-01、step-06、sum-01；D: hook-01；发行（四平台）；`exceptions` |
| `35` / `36` | codeLabel `probe.c:35-36` 的源码行号；B: step-03；`exceptions` |

## 4. 不能删的技术断言（删了会让章节断链）

1. **地址是算出来的**：`0x40021418 = 0x40021400 + 0x18`；下标 `6 × 4 = 0x18`。
   删掉这条，片头那行就退回「魔数」。
2. **类型定宽度**：读 `ldrb/ldrh/ldr`、写 `strb/strh/str`；`p[1]` 的偏移直接是 `#1/#2/#4`。
   删掉这条，「类型不是装饰」没有硬件证据。
3. **编译期锁等式**：`_Static_assert(6U * sizeof(uint32_t) == GPIOF_BSRR_OFFSET)` 随编译通过。
   删掉这条，结构体罩寄存器块的地基就只剩口头。
4. **两种写法同一份机器码**：`led_on_indexed` 与 `led_on_macro` 的 `ldr/mov/str` 逐条相同。
   删掉这条，「语法糖只是糖」不成立。
5. **地址被拆成两段**：字面量池 `0x40021000` + 指令偏移 `1048`（`0x418`）= `0x40021418`。
   删掉这条，「常数是两段拼出来的」没有现场。
6. **const 三组合**：左边锁目标、右边锁指针、两边都锁；三个违规版本全部编译期拦下。
   删掉这条，纪律那一节只剩口号。

## 5. 已知未取证项（明确「不上屏」或只作源码说明）

| 项 | 状态 | 处理 |
|---|---|---|
| `1UL << 22` 里的 `22` | probe 日志只打印常量 `4194304` / `0x400000`，不打印位号 22 | 上屏保留片头原码；`22` 放 `numbers.exceptions`，注明来自 `probe.c:40` 的 `6U + 16U` 与 `docs/c/02-pointer.md:82`，不是 probe 读数 |
| BSRR 高/低半区的 `16` | 日志不打印 `16`；源码是 `6U + 16U` | 旁白只说「低半区管置位、高半区管复位」，不写 `16` 这个数；`16` 不进 numbers |
| 类型位宽 `8/16/32` | 日志只打印 sizeof 字节数 `1/2/4`，不打印位宽 | 只作为类型名本身的位宽说明（bit-width 例外）；旁白不据此声称任何测量值 |
| `zero_extendqisi2` 具体清了多少位 | 日志只有指令注释，没有位宽读数 | 旁白只说「高位由硬件清零」，不写 24 位 |
| 开发板实测 | 本集全程不需要板子；`sizeof` 的 8 字节是宿主口径 | 旁白与 codeLabel 明写「本机/宿主」，不冒充板子 |
| 断言条数 | 日志 L110 只写「全部断言通过」 | 不写「多少条断言」；cta 只说「三句报错原文」等可数的屏上对象 |
| `-O0` / `-O2` 点灯行为差异 | 属于 C3 的取证范围，本集 probe 没跑 | C2 只在 disc-05 作交接，不写具体现象，不当成本集读数 |

## 6. 与旧对账的关系

- 起点：v1 `episode.json` 里的 `0x5A / 0x96`、`MODER 0x00 / OTYPER 0x04 / IDR 0x10 / ODR 0x14` 等数字，
  本次 probe 没有打印，已从 v2 上屏文本移除或改成不带数字的说法。
- v1 的 `1UL << 22` 与 `0x40021400` 是旧结论；`0x40021400` 本次日志 L107/L109 有原文，升级为 evidence；
  `22` 日志没有，按 §5 放 `exceptions`。
- v1 的 `42` 不是断言条数，是 `const` 合法半边 `*cp=42` 的读数；本次日志 L108 有原文，evidence。
- v1 的「四千一百九十四万零三十四」把 `4194304` 写错了；v2 改为「四百一十九万四千三百零四」，
  数字本身来自日志 L77/L86/L96 的 `#4194304`。

## 7. 审计回填

- `npm run video:numbers -- c2-pointer`：✅ 30 个数字都有依据（0 未命中）。
- `npm run video:lint -- c2-pointer`：✅ bilibili 27 场，douyin 10 场。
- 旁白字数（实测）：bilibili 3071 字；douyin 280 字（均在预算内）。
- `npm run video:check -- c2-pointer`：✅ 通过；bilibili 27 场 + douyin 10 场，排版/节拍审计 0 问题。
- `npm run video:pack -- c2-pointer`：✅ 4 平台发布包（共享 SVG 重制后重新生成）。
- 母版：bilibili 618.766667s / 18563 帧 / -15.0 LUFS / 311 拍 / 最长静止 4.2s；
  douyin 67.566667s / 2027 帧 / -14.8 LUFS / 29 拍 / 最长静止 5.3s。
- 漂移：bilibili 0.000000；douyin 0.000000（`|ffprobe − timeline.duration|`）。
- 闸门日志：`.temp/v2-facts/c2-gates-final.log`；重制日志 `.temp/v2-facts/c2-build-shared-svg.log`。
- stills：B站 13 张、抖音 13 张，全部由本次终版母版抽取；旧帧已移至 `.temp/c2-stale-stills/`。
- step-02 抽帧（270.5s）已确认共享 SVG 新文案：`前面 6 格 × 4 字节 = 0x18`、`板上结果待回填`。
