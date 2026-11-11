# C6《一次调用的四笔账》事实底稿

本文件是 `video/episodes/c6-abi-stack/episode.json` 的上屏/口播数字对账底稿。所有输出行都从**本次**运行
`.temp/v2-facts/c6-probe.log`（75 行）原样摘出；`docs/c/06-abi-stack.md`、`probe.c` 源码与 v1 旧稿只在
「叙述前提」和「与旧稿的关系」两节出现，并逐条标明，不冒充本次读数。

## 1. 取证信息

| 项 | 值 |
|---|---|
| 源文档 | `docs/c/06-abi-stack.md` |
| 取证脚本 | `code/c/06-abi-stack/probe.sh`（宿主段跑 `probe.c`；交叉段用 `arm-none-eabi-gcc -O2 -S`） |
| 本次日志 | `.temp/v2-facts/c6-probe.log`（75 行） |
| 宿主工具链 | `gcc 16.1.0`（日志 L2） |
| 交叉工具链 | `10.3.1`（日志 L16） |
| 宿主输出 | sp 实差、buf 实址、`sum6` / `add64` / `mix` / `non_leaf` 四个返回值（L3–L11） |
| 宿主断言 | `== 断言通过 9/9 ==`（L12） |
| 交叉输出 | `add2`、`sum6`、`sum6` 调用方、`add64`、`mix`、`non_leaf` 六段摘录，加四项计数（L18–L75） |
| 板级输出 | 日志**没有** LED、串口、GDB 或任何板上读数；本集没有开发板 |
| UBSan / sanitizer | 日志**没有** UBSan、ASan 或任何 sanitizer 行；本集不写 |
| 浮点实验 | `probe.c` 里有 `add_d`，但**本次日志没有打印 `add_d` 的函数体**；v2 不写硬浮点 |

## 2. 本集必须回答的 5 个问题

1. 宿主那 64 字节的帧是怎么量出来的？buf 为什么在 sp+32？
2. `sum6` 前四个参数在哪？第 5、6 个从哪读回来？调用方用哪条指令把它们写上栈？
3. 64 位参数为什么占一对寄存器？`mix` 为什么跳过 r1？返回值又从哪里回来？
4. 叶子函数与非叶子函数在 lr 上差什么？`push {r4, lr}` 与 `pop {r4, pc}` 各做了什么？
5. 64 与 24 的口径差在哪？四项计数能证明什么、不能证明什么？

## 3. 上屏数字逐项对账

> 场景写法：`B:` = bilibili，`D:` = douyin，`封面` = 主封面，`发行` = publish 文案。

### 3.1 宿主：活的栈与四个返回值（日志 L2–L13）

```text
宿主工具链：gcc 16.1.0
sp(main, 调用前)      = 0x511f3ffa50
sp(non_leaf 体内)     = 0x511f3ffa10
一帧吃掉的栈          = 64 字节（两次 sp 之差，含返回地址+保存寄存器+buf）
buf 地址              = 0x511f3ffa30
buf 距 sp(non_leaf)   = 32 字节
sum6(1,2,3,4,5,6)     = 21（第 5、6 个参数 5、6 是走栈送进去的）
add64(0x100000000, 0x200000001) = 0x300000001（64 位结果走寄存器对回来）
mix(7, 0x100000000)   = 0x100000007
non_leaf(40)          = 81
== 断言通过 9/9 ==
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `64` | L5 `一帧吃掉的栈 = 64 字节` | B: hook-01、bytes-host、bytes-both、pit-isr、punch；封面；发行（四平台） |
| `32` | L7 `buf 距 sp(non_leaf) = 32 字节` | B: bytes-host；封面；发行（B站/知乎/小红书） |
| `21` | L8 `sum6(1,2,3,4,5,6) = 21` | B: sum-host；发行 |
| `9` | L12 `== 断言通过 9/9 ==` | B: sum-host、cta；D: cta；发行 |
| `0x100000000` | L9 `add64(0x100000000, 0x200000001)`；L10 `mix(7, 0x100000000)` | B: a64-asm、mix-caller；发行 |
| `0x200000001` | L9 `add64(0x100000000, 0x200000001)` | B: a64-asm；发行 |
| `0x300000001` | L9 `= 0x300000001（64 位结果走寄存器对回来）` | B: a64-asm；发行 |
| `0x100000007` | L10 `mix(7, 0x100000000) = 0x100000007` | B: mix-caller；发行 |
| `81` | L11 `non_leaf(40) = 81` | 不上屏；只作本底稿核对，episode 未使用 |
| `40` | L11 `non_leaf(40)` 的输入 | 不上屏；episode 未使用 |

注：日志里的三个 sp 地址（`0x511f3ffa50` / `0x511f3ffa10` / `0x511f3ffa30`）是本次运行的活地址，
每次运行都会变，episode 只上屏两次 sp 的差值与 buf 的距离，不搬具体地址。`81` 与 `40` 没有进 episode，
numbers 审计只统计 episode 里真正出现的 token。

### 3.2 交叉汇编：六段摘录（日志 L16–L75）

#### `add2`：叶子不存 lr（L18–L22）

```text
add2:
	@ link register save eliminated.
	add	r0, r0, r1
	bx	lr
	.size	add2, .-add2
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| 无数字 token | `@ link register save eliminated.` | B: leaf-vs、pit-lr；D: leaf-vs |

#### `sum6`：前四个在 r0–r3，第 5、6 个读栈（L24–L36）

```text
sum6:
	@ args = 8, pretend = 0, frame = 0
	@ frame_needed = 0, uses_anonymous_args = 0
	@ link register save eliminated.
	add	r1, r1, r0
	add	r2, r2, r1
	add	r3, r3, r2
	ldr	r2, [sp]
	ldr	r0, [sp, #4]
	add	r3, r3, r2
	add	r0, r0, r3
	bx	lr
	.size	sum6, .-sum6
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `8` | L25 `@ args = 8`；L41 `strd` 两个 32 位寄存器 | B: sum-callee、sf-1、sf-3、nl-asm、nl-asm 标题、bytes-both；D: nl-asm；封面；发行 |
| `0` | L25 `pretend = 0, frame = 0`；L48 同形；L62 `movs r2, #0` | B: sum-callee、a64-asm、mix-caller |
| `5` | L39 `movs r3, #5`；L8 第 5 个参数 5 | B: sum-callee 注释、sum-caller、counts；封面；发行 |
| `6` | L40 `movs r2, #6`；L8 第 6 个参数 6 | B: 同上；封面；发行 |
| `4` | L32 `ldr r0, [sp, #4]`；L44 `movs r3, #4` | B: sum-callee、sum-caller；封面；发行 |

注：`sum6` 的 `frame = 0` 表示它自己没有局部变量；`args = 8` 指调用方在栈上放了 8 字节入参。
`bx lr` 与 `link register save eliminated` 一起说明它不需要保存返回地址。

#### `sum6` 调用方：一条 strd 写两个栈参数（L38–L45）

```text
	bl	add2
	movs	r3, #5
	movs	r2, #6
	strd	r3, r2, [sp]
	movs	r2, #3
	subs	r4, r0, r2
	movs	r3, #4
	movs	r0, #1
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `5` / `6` | L39 / L40 `movs r3, #5` / `movs r2, #6` | B: sum-caller；D: sum-caller |
| `4` | L44 `movs r3, #4` | B: sum-caller |
| `3` | L42 `movs r2, #3` | B: sum-caller |
| `1` | L45 `movs r0, #1`；L72–L75 四项计数均为 1 | B: sum-caller、counts；发行 |
| `0` | L62 `movs r2, #0`（下一段 mix 调用方） | B: mix-caller |

注：这 8 条是 `bl sum6` 之前的窗口，第一行 `bl add2` 是上一笔调用，`subs r4, r0, r2` 是探针在核对
上一个返回值，不是传参准备。**窗口里没有一条指令写 r1**；第二个参数在更早的指令里已经就位，日志没有
截到那一段，所以 v2 不声称「r1 里就是 2」。

#### `add64`：64 位占一对（L47–L54）

```text
add64:
	@ args = 0, pretend = 0, frame = 0
	@ frame_needed = 0, uses_anonymous_args = 0
	@ link register save eliminated.
	adds	r0, r0, r2
	adc	r1, r1, r3
	bx	lr
	.size	add64, .-add64
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `0x100000000` / `0x200000001` / `0x300000001` | L9 `add64(0x100000000, 0x200000001) = 0x300000001` | B: a64-asm；发行 |
| `32 位` / `64 位` | 字长语义，非本次测量；`adds` / `adc` 各处理一半 | B: a64-asm、mix-asm、mix-caller、arg-order、pair-rule、punch |

注：`adds` 加低 32 位并更新进位，`adc` 把高 32 位连进位一起加；`r0:r1` 是 x，`r2:r3` 是 y，
返回值也从 `r0:r1` 回来。`frame = 0` 与 `link register save eliminated` 说明这个函数没有局部帧、
也不保存 lr。

#### `mix(int, long long)`：r1 被跳过（L56–L64）

```text
  [被调方] 只读 r0（tag）与 r2:r3（v），从没读入参 r1；r1 只作 64 位返回值的高半：
	mov	r1, r0
	adds	r0, r0, r2
	adc	r1, r3, r1, asr #31
	bx	lr
  [调用方] r0=tag，r2:r3=v（注意 r1 压根没被赋值）——这就是「跳过 r1」：
	movs	r2, #0
	movs	r3, #1
	movs	r0, #7
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `31` | L59 `adc r1, r3, r1, asr #31` | B: mix-asm（代码注释外，指令里的立即数） |
| `7` | L64 `movs r0, #7`；L10 `mix(7, ...)` | B: mix-caller；发行 |
| `1` | L63 `movs r3, #1` | B: mix-caller |
| `0` | L62 `movs r2, #0` | B: mix-caller |
| `0x100000007` | L10 `mix(7, 0x100000000) = 0x100000007` | B: mix-caller；发行 |

注：`mov r1, r0` 是给 64 位返回值的高半让位，不是读入参 r1；调用方只写 r2、r3、r0。v2 只声称
「这 4 条调用方指令里 r1 没有赋值」，不声称 r1 里具体是什么。

#### `non_leaf`：push、sub、两次 bl、pop（L66–L70）

```text
	push	{r4, lr}
	sub	sp, sp, #16
	bl	sink
	bl	add2
	pop	{r4, pc}
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `8` | `push {r4, lr}` 两个 32 位寄存器 = 8 字节（按寄存器宽度算术） | B: nl-asm、bytes-both、封面；D: nl-asm |
| `16` | L67 `sub sp, sp, #16`；源码 `char buf[16]` | B: hook-02、sf-3、nl-asm、bytes-both；D: hook-02、nl-asm；发行 |
| `24` | `push` 8 + `sub` 16 = 24，按两条指令的立即数算术 | B: bytes-both；封面 numNote；发行 |

注：这段摘录是 `probe.sh` 用 `grep -E "push|pop|sub[[:space:]]+sp|bl[[:space:]]"` 筛出来的，
**没有打印 `add sp, sp, #16`**。v2 因此只说「收尾 pop 把 r4 与返回地址带回」，不补写完整的收尾序列，
也不声称这条摘录就是 `non_leaf` 的全部指令。`push {r4, lr}` 里 lr 是返回地址的备份，`pop {r4, pc}`
把返回地址直接弹进 pc；两条 `bl` 都会覆盖 lr，所以开头必须存。

#### 四项计数（L72–L75）

```text
  push {r4, lr} 出现次数 = 1
  pop  {r4, pc}  出现次数 = 1
  调用方把第 5、6 个入参写上栈：strd , [sp] 次数 = 1
  str 落盘到 [sp…] 总次数 = 1（含编译器溢出暂存，不都等于栈传参）
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `1` | L72–L75 四项计数均为 1 | B: counts；D: 无（抖音不选 counts） |

注：最后一行是日志自己的警告。`str` 计数包含编译器溢出暂存，**不能把每一条落到 [sp] 的 str 都当成
栈传参**；v2 在 counts 场把这句话原样上屏，并让旁白复述这一限制。

### 3.3 派生量与两个易混 token

| 量 | 来源 | 口径 |
|---|---|---|
| `24` | `push {r4, lr}` = 8 字节 + `sub sp, sp, #16` = 16 字节 | **算术**，不是本次实测；封面右列标 `FROM ASM`，不标 `MEASURED` |
| `8`（push 那半边） | 两个 32 位寄存器 × 4 字节 | 按寄存器宽度算术；日志只打印 `push {r4, lr}` 这一条指令 |
| `64` | L5 两次 sp 之差 | **宿主本次构建的实测帧**；不是 Cortex-M4 的帧，也不是通用常数 |
| `32` | L7 buf 距 sp | 宿主本次运行的实测值；同时被用作「32 位字长」的文字 token，场景上下文区分 |
| `64 位` | 数据宽度 | 架构常量；与 L5 的 64 字节帧不是同一件事，只共用 token |
| `16.1.0` / `10.3.1` | L2 / L16 | 工具链版本，不是测量值 |
| `06` | 路径 `code/c/06-abi-stack` | 章节号，放 `numbers.exceptions` |

`sum-host` 的 C 结果行在 episode 里写成 `sum6(1, 2, 3, 4, 5, 6) = 21`（逗号后加空格），
是为了避开数字审计把 `1,2,3,4,5,6` 当成一个千位分隔数 `123456`；日志原文无空格，语义相同。
同理，publish 里的 `21；9/9`、`#16；8+16` 用分号断开，避免中文逗号归一化后把相邻数字并成一个 token。

### 3.4 封面与发行文案

- 封面保留 `variant: "vs"` 与四尺寸：bilibili 1920×1200、douyin 1080×1440、zhihu 1920×1080、
  xiaohongshu 1440×1080。
- 对撞两列：左「宿主实测：一帧 64 字节」，右「M4 摘录：push 8 + sub 16」；
  `vs.labels: ["MEASURED", "FROM ASM"]`。左列有 L5 实测，右列是 L66–L67 的指令算术，
  没有把任何一侧标成 `EXPECTED`。
- 封面 `proof` / `proofShort` 只用 L5 的 64、L7 的 32、L25 的 `args = 8`、L32 的 `[sp,#4]`
  和 mix 调用方「r1 没赋值」，都在 §3.1/§3.2 有日志行。
- `num: "64 字节"` 指宿主 non_leaf 的 sp 实差；`numNote` 明写「M4 那段是 8+16 的反汇编算术」。
- 发行文案（B站/抖音/知乎/小红书）只写 64（实测）、32（实测）、8/16/24（摘录与算术）、21、9/9、
  四个十六进制结果与工具链版本；**没有**写「24 字节实测」「40 字节差」「板上灯态」「UBSan」。
- 抖音描述首行「一次调用四笔账：参数、归途、栈帧、返回值」与话题组 `#汇编 #调用约定 #栈帧`
  在现有 19 份 episode 中唯一，未触发跨集重复检查。

## 4. 不能删的技术断言（删了会让章节断链）

1. **宿主 64 字节是实测帧**：两次读 sp 相减，且日志注明含返回地址、保存寄存器与 buf；buf 在 sp+32。
   删掉这条，片头的「64 字节买了什么」没有现场。
2. **sum6 的 args = 8、frame = 0**：前四个参数在 r0–r3，第 5、6 个从 `[sp]`/`[sp,#4]` 读回；
   调用方一条 `strd` 写两个栈参数；宿主结果 21。删掉这条，「寄存器不够时栈接得住」讲不成。
3. **add64 的偶数对**：x = r0:r1、y = r2:r3，`adds`/`adc` 分上下半加，宿主得 0x300000001，
   返回值也走 r0:r1。删掉这条，64 位落位没有正面证据。
4. **mix 跳过 r1**：被调方只读 r0 与 r2:r3；调用方 4 条指令只写 r0、r2、r3，r1 一次赋值都没有；
   宿主得 0x100000007。删掉这条，「r1 可以是空的」只剩形容词。
5. **叶子函数不存 lr**：add2 有 `link register save eliminated`，全身 add + bx lr；非叶子 non_leaf
   的 prologue 是 `push {r4, lr}`，epilogue 是 `pop {r4, pc}`。删掉这条，归途对比没有落点。
6. **24 是算术**：push 8 + sub 16；日志筛出的 5 行里没有 `add sp`，不能补写成完整尾声。
   删掉这个限定，就会把 24 冒充成板上实测。
7. **计数各 1 次，但含溢出暂存**：`str` 总数不等于栈传参条数；日志自己写了这句警告。
   删掉这条，counts 场会变成「一条 str 就是一个参数」的错误示范。
8. **64 不是通用常数**：它只是宿主本次构建的帧；M4 段是另一本账（8+16 的算术），
   目标/编译器/优化档一换就会变。删掉这条，整集会变成「所有 Cortex-M 都是 24 字节」的伪结论。

## 5. 已知未取证项（明确「不上屏」或只作叙述前提）

| 项 | 状态 | 处理 |
|---|---|---|
| M4 的 24 字节帧 | 日志只打印 `push {r4, lr}` 与 `sub sp, sp, #16`，没有板上 sp 读数 | 只作 8+16 的算术；封面右列标 `FROM ASM`，旁白明说「不是跑出来的读数」 |
| 64 字节是否通用 | 只是宿主本次构建的帧 | 旁白与 bytes-both 明写「不是常数」，不推广到 Cortex-M |
| `add sp, sp, #16` | `probe.sh` 的 grep 没筛出这一条 | 只说 `pop {r4, pc}` 把 r4 与返回地址带回；不补写完整 epilogue |
| 调用方 r1 的具体值 | 8 条窗口里没有写 r1 的指令 | 只声称「这个窗口没赋值」；不声称 r1=2 或 r1 是垃圾 |
| `add_d` / 硬浮点 / d0、d1 | 源码有 `add_d`，本次日志没有打印它的函数体 | v2 删掉 v1 的 fpu-asm/fpu-link 两场，改为 arg-order/pair-rule；不写浮点寄存器 |
| 板上 GDB 单步 | 日志没有 GDB、OpenOCD 或板上输出 | v1 的 lab-gdb 改为 lab-log：只读本机 probe 日志，不上板 |
| UBSan / ASan | 日志没有 sanitizer 行 | 全集不提 |
| `non_leaf(40) = 81` | 日志 L11 有，但 episode 不用 | 留在本底稿作核对；不上屏、不进 numbers 审计范围 |
| 具体 sp 地址 | 每次运行都变 | 只上屏差值与 buf 距离，不搬 `0x511f...` |
| `arg-order` 的「long long 放前面」 | 规则推导，没有对应的 mix 反汇编 | 只讲 ABI 落位规则，不声称本次跑过另一种顺序 |
| `pit-isr` 的栈预算 | 架构常识，不在本次日志 | 不写具体寄存器、字节数或板上现象；只提醒「一帧不是整机预算」 |
| `buf[0] = (char)x` 的掩码 | 源码是 `(char)(x & 0xFF)`；`0xFF` 不在日志 | episode 的 codeLabel 明写「略去掩码细节」，不把 `0xFF` 当证据 |
| 计数中的每条 `str` | 日志明说含编译器溢出暂存 | counts 场上屏原警告；旁白不把每条 str 解释成参数 |

## 6. 与 v1 旧稿的关系

- **音色与语速**：v1 是 `zh-CN-YunxiNeural` / `+4%`；v2 按合同改为 `zh-CN-YunyangNeural` / `+2%`。
- **浮点整段删除**：v1 的 `fpu-asm`（`add_d`、`vmov`、`__aeabi_dadd`）与 `fpu-link`（hard/soft 混链）
  没有本次日志依据；`probe.c` 里虽有 `add_d`，但日志没有打印它。v2 把这两个 id 改为 `arg-order` 与
  `pair-rule`，讲 64 位参数顺序与偶数对规则，不写任何浮点寄存器或链接错误。
- **上板步骤删除**：v1 的 `lab-gdb` 写 OpenOCD + GDB 单步、`pit-isr` 写 ISR 硬件压栈清单；
  本次日志没有板级输出，也没有 GDB。v2 把 `lab-gdb` 改为 `lab-log`（只读本机日志），
  `pit-isr` 只保留「一帧不是整机预算」的通用提醒，不列寄存器、不写板上现象。
- **24 字节的口径改正**：v1 把「Cortex-M4 24 字节」当成实测写进封面与发行文案；v2 把它改为
  `push 8 + sub 16` 的**指令算术**，封面右列标 `FROM ASM`，旁白明说不是跑出来的读数。
- **64 与 24 的对比保留但加限定**：v1 的「差 40 字节」不再上屏；v2 只并排两本账，
  并明写「目标、编译器、优化档一换就会变」。
- **r1 的说法收紧**：v1 的 `mix-caller` 说「r1 里躺的是上一个调用留下的垃圾」；v2 只声称
  「这 4 条调用方指令没有给 r1 赋值」，不猜 r1 的具体内容。
- **sum6 调用方的说法收紧**：v1 说「r1 从头到尾没被重写，它里面还是二」；本次 8 条窗口没有
  设置 r1 的指令，v2 改为「窗口里没有写 r1，第二个参数在更早的指令里已经就位」。
- **计数警告保留并前置**：v1 在 counts 场最后一行提过「含编译器溢出暂存」；v2 把它上屏，
  并在旁白里复述，避免观众把 `str` 计数当成栈参数计数。
- **旧行号删除**：v1 的 `probe.c 第 41–44 行`、`build/probe.s 第 217–224 行`、`probe.sh 第 66–70 行`
  等行号没有本次日志依据，v2 不再写具体源码行号。
- **保留的骨架**：v1 的 `hook-01`、`sum-*`、`sf-*`、`a64-asm`、`mix-*`、`nl-*`、`leaf-vs`、`counts`、
  `bytes-*`、`punch`、`cta`、`teaser` 等 id 保留；抖音的 11 个 pick 也保留原顺序，只重写旁白与 set。
- **零句复用**：v1 与新稿逐句比对，完整句子复用 0 条；最长公共片段是汇编注释
  `link register save eliminated`（29 字符），属于被引用的指令注释，不是叙述句。

## 7. 审计回填

- `npm run video:lint -- c6-abi-stack`：`✅ 通过：bilibili 31 场，douyin 11 场`。
- `npm run video:numbers -- c6-abi-stack`：`✅ c6-abi-stack: 23 个数字都有依据`。
- 旁白字数（实测）：bilibili 3313 字（目标 3000–3400，硬区间 2087–3510）；
  douyin 258 字（目标 240–280，硬区间 135–305）。
- 估算时长：bilibili 3313 × 0.1955 ≈ 648 s（目标 480–720 s）；
  douyin 255 × 0.1946 + 11 × 1.091 ≈ 62 s（目标 45–75 s）。
- 开场连续 `kind: "hook"` 只有 `hook-01`，实测 bilibili 11.333333 s、douyin 5.567 s，均低于 15 s 上限。
- 节与场次：

| 节 | 起止场次 | 场数 |
|---|---|---:|
| 片头 | hook-01 → hook-03 | 3 |
| 参数落位 | reg-table → sum-host | 5 |
| 64 位与返回值 | a64-asm → pair-rule | 5 |
| 栈帧与回家路 | sf-1 → leaf-vs | 7 |
| 字节账 | counts → pit-64 | 5 |
| 坑与收束 | pit-isr → teaser | 6 |

### 构建与闸门（bilibili `c6-build5.log`；douyin `c6-build6-douyin.log`）

| 项 | bilibili | douyin |
|---|---|---|
| 成片 | 620.100000 s / 18603 帧 | 57.833333 s / 1735 帧 |
| 响度 | -15.0 LUFS（首遍 -25.1） | -14.8 LUFS（首遍 -25.1） |
| 字幕 | 322 条 | 28 条 |
| 节拍 | 322 拍，最长静止 4.5 s | 33 拍，最长静止 4.0 s |
| 排版审计 | 31 场，0 问题，最小字号 21.1px | 11 场，0 问题，最小字号 26.9px |
| 构建用时 | 918 s（渲染 819.7 s） | 133 s（渲染 115.9 s） |

- `video:lint`：31 / 11 场通过；`video:check --platform both`：31 + 11 场，0 越界/裁切/压字幕/相叠/不可读；`video:numbers`：23 个数字全部有依据；`video:pack`：四平台发布包（`c6-gates-final3.log`）。
- 时间轴漂移：bilibili `|620.100000 − 620.100000| = 0`；douyin `|57.833333 − 57.833333| = 0`。
- 抽帧：bilibili 13 张（`c6-build5`）、douyin 13 张（`c6-build6`）；七张旧帧（1 张 bilibili + 6 张 douyin，含 `teaser`/`nl-asm`/`leaf-vs`/`cta`）已移到 `.temp/c6-stale-stills/`。
- `bili-submit.yaml` 在 `video:pack` 后重生成：v2 标题、简介、31 条章节（每场一条）；生成器同时动了 `s5-systick`，已按快照逐字节复原，实际只有 c6 的 YAML 更新。
- 封面四尺寸接触表检查：标题两行、`64 字节` 主数字、MEASURED / FROM ASM 两栏均正常；右栏改为「M4 摘录：8 + 16 = 24」，XHS 的 `16` 孤行已消除。

复核后的修正（`task-12-c6-review.md`）：

1. **P1** douyin `sum-caller` 四行代码直到约 21.1 s 才出现、21.633 s 切场，可读窗口约 0.5 s。处理：五场抖音代码场加单拍 `beatMap`（`at: 1`，首句字幕即全量揭示），`sum-caller` 的四行从 17.2 s 起可见并停留到切场；`sum-callee`/`mix-caller`/`nl-asm`/`leaf-vs` 同步修复。抽帧 17.2 / 18.5 / 21.4 s 确认。
2. **P2** `mix-caller` 的「没有一条指令碰 r1」超出画面四行证据（完整 caller 还有 `movs r1,#1` 与 `mov r9,r1`）。处理：标题改「这四条不写 r1」、`codeLabel` 标「节选」、旁白改「没有一条给 r1 赋值」；发布简介/知乎/小红书正文同步改为「这四条…这四条里 r1 没有赋值」。
3. **P2** CTA「五段摘录」与日志六段不一致。处理：屏上 bullet、旁白、`lab-log` 列表统一为六段（`add2`、`sum6`、`sum6 调用方`、`add64`、`mix`、`non_leaf`），四项计数不变；585 s 抽帧确认。

4. **Low 10** 抖音旁白 `mix-caller` 原句「调用方只写 r0、r2、r3」仍可读成全函数（完整 caller 有 `movs r1,#1`、`mov r9,r1`）。处理：改为「调用方这四条只写 r0、r2、r3，r1 不装参数」，`publish.douyin.intro` 与 `cover.proof` 同步限定到四条；抖音母版重建为 57.833333 s / 1735 帧，33 拍，最长静止 4.0 s，-14.8 LUFS，排版 11 场 0 问题；三张旧时刻帧移入 `.temp/c6-stale-stills/`。

更早构建中修的两处仍有效：douyin `sum-caller` 的四行节选替代 9 行继承代码（最小字号 12.7px → 26.9px）；置顶评论补《通往单片机之路》C6。

## 8. 证据行索引

| 行 | 内容 |
|---|---|
| L2 | 宿主 `gcc 16.1.0` |
| L3–L7 | 宿主 sp、64 字节帧差、buf 地址与 32 字节距离 |
| L8–L11 | `sum6` / `add64` / `mix` / `non_leaf` 四个返回值 |
| L12 | `9/9` 断言 |
| L16 | 交叉工具链 `10.3.1` |
| L18–L22 | `add2` 叶子函数 |
| L24–L36 | `sum6` 被调方 |
| L38–L45 | `sum6` 调用方 8 条 |
| L47–L54 | `add64` |
| L56–L64 | `mix` 被调方与调用方 |
| L66–L70 | `non_leaf` 五行摘录 |
| L72–L75 | 四项计数与 `str` 警告 |
