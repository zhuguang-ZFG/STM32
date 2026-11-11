# C7《未定义行为：编译器不欠你一个答案》事实底稿

本文件是 `video/episodes/c7-ub/episode.json` 的上屏/口播数字对账底稿。所有读数、汇编、警告原文都从**本次**运行
`.temp/v2-facts/c7-probe.log`（107 行）原样摘出；`docs/c/07-ub-misra.md`、`probe.c` 源码与 v1 旧稿只在
「叙述前提」和「与旧稿的关系」两节出现，并逐条标明，不冒充本次读数。

## 1. 取证信息

| 项 | 值 |
|---|---|
| 源文档 | `docs/c/07-ub-misra.md`（只作章节前提，不是读数来源） |
| 取证脚本 | `code/c/07-ub-misra/probe.sh` |
| 本次日志 | `.temp/v2-facts/c7-probe.log`（107 行） |
| 宿主工具链 | `gcc 16.1.0`（日志 L2） |
| 交叉工具链 | `15.2.1`（日志 L49） |
| 宿主三档读数 | `-O0`、`-O2`、`-fwrapv` 各四个值（L4–L7、L10–L13、L17–L20） |
| 宿主断言 | 每档 `== 断言通过 2/2（只断言非 UB 铁事实）==`（L8、L14、L21） |
| 警告现场 | 三条 warning + 三条 note（L26、L31、L34、L38、L41；L25/L30/L37 是函数上下文） |
| UBSan | 第 4 步**跳过**：本工具链没有 UBSan 运行库，没有任何运行期输出（L45–L46） |
| 交叉汇编 | `is_bigger_after_inc` 两段：`-O2`（L50–L53）与 `-fwrapv -O2`（L54–L60） |
| 宿主汇编 | `-O0` 两个函数体（L63–L83）与 `-O2 main`（L84–L107） |
| 板级输出 | 日志**没有** LED、串口、GDB 或任何板上读数；本集没有开发板 |
| 地址 / 寄存器现场 | 日志只有汇编里的寄存器名与栈偏移，没有运行时地址；本集不写地址 |

## 2. 本集必须回答的 5 个问题

1. 同一行 `1u << 33`，为什么宿主 `-O0` 得 2、`-O2` 得 0？这两个数分别是谁给的？
2. `x + 1 > x` 为什么在 `-O0` 也已经折叠成 1？`-fwrapv` 改的是哪条合同？交叉 `-O2` 与 `-fwrapv` 两段汇编差在哪？
3. 宿主 `-O2 main` 里那四个立即数各是什么？为什么说 0 不是算出来的？「四个 call 消失」的边界在哪？
4. 三条警告各抓什么、位置在哪？为什么警告抓不全？UBSan 这一步为什么没有输出？
5. 合法位读为什么 `union` 与 `memcpy` 都得到 `0x3F800000`？这份日志能证明什么、不能证明什么？

## 3. 上屏数字逐项对账

> 场景写法：`B:` = bilibili，`D:` = douyin，`封面` = 主封面，`发行` = publish 文案。
> 数字审计按 token 对齐，不区分同一 token 在不同语境里的含义；本节的「场景」列给出主要落点。

### 3.1 宿主三档读数（日志 L2–L21）

```text
宿主工具链：gcc 16.1.0
-O0            is_bigger_after_inc(INT_MAX) = 1
               shift_oob(1u, 33u)          = 2
               bits_union(1.0f)            = 0x3F800000
               bits_memcpy(1.0f)           = 0x3F800000
               == 断言通过 2/2 ==
-O2            is_bigger_after_inc(INT_MAX) = 1
               shift_oob(1u, 33u)          = 0
               bits_union(1.0f)            = 0x3F800000
               bits_memcpy(1.0f)           = 0x3F800000
               == 断言通过 2/2 ==
-O2 -fwrapv    is_bigger_after_inc(INT_MAX) = 0
               shift_oob(1u, 33u)          = 0
               bits_union(1.0f)            = 0x3F800000
               bits_memcpy(1.0f)           = 0x3F800000
               == 断言通过 2/2 ==
```

`bigger-readout` 的三行读数是这张表的整理稿（`codeLabel` 明写「整理」），不是日志里连续打印的一张表：
`-O0` 与 `-O2` 在 L4/L10，`-fwrapv` 在 L17。`2/2` 也不是一次读数，而是每档各自的断言行（L8/L14/L21）。

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `1` | L4/L10 `is_bigger_after_inc(INT_MAX) = 1`；L52 `movs r0, #1`；L68 `movl $1, %eax`；L6/L7 的 `1.0f` | B: hook-01、hook-02、bigger-src、bigger-readout、bigger-arm、bigger-host-o0、bigger-host-o2、bigger-wrapv、shift-asm、shift-fold、safe-mask、punch；D: 多场；封面；发行 |
| `2` | L5 `-O0` 下 `shift_oob(1u, 33u) = 2`；L8/L14/L21 `2/2`；L101/L102 `movl $2` | B: hook-01、hook-02、bigger-readout、shift-asm、punch；D: hook-01、shift-asm、punch；封面；发行 |
| `0` | L11/L18 `shift_oob = 0`；L17 `is_bigger = 0`；L85/L93 `$0`（`xorl %edx,%edx`） | B: hook-01、hook-02、bigger-readout、trap-4、shift-fold、wrapv-norescue、punch；D: hook-01、shift-fold、punch；封面；发行 |
| `0x3F800000` | L6/L7/L12/L13/L19/L20：三档的 `bits_union` 与 `bits_memcpy` 均为 `0x3F800000` | B: bigger-host-o2、alias-legal；封面；发行（四平台） |
| `1065353216` | L95/L98 `movl $1065353216, %edx`；L85 注释说明它等于 `0x3F800000` | B: bigger-host-o2（代码、codeB、旁白） |
| `1.0` | L6/L7 `bits_union(1.0f)` 与 `bits_memcpy(1.0f)` 的输入常量 | B: alias-legal 的 codeB |
| `-2147483648` | L56 `mvn r3, #-2147483648` | B: bigger-wrapv 的代码 |
| `16.1.0` | L2 `宿主工具链：gcc 16.1.0` | B: 多场 codeLabel、hook-01、cta；D: 多场；发行（B站/知乎/小红书） |
| `15.2.1` | L49 `交叉工具链：15.2.1` | B: bigger-arm、bigger-wrapv、cta；D: bigger-arm、cta；发行（四平台） |

注：`1.0` 是源码里的输入字面量；日志打印的是两个函数的**返回值** `0x3F800000`，没有单独打印 `1.0f` 的四个字节。
v2 因此只说「两种位读都给 `0x3F800000`」，不声称「`1.0f` 的内存里逐字节是 00 00 80 3F」。

### 3.2 三条警告现场（日志 L23–L43）

```text
alias-violate.c:13:13: warning: dereferencing type-punned pointer will break strict-aliasing rules [-Wstrict-aliasing]
   13 |     return *(uint32_t *)&f;

oob-static.c:19:14: warning: 'x' is used uninitialized [-Wuninitialized]
   19 |     return x + 1;
oob-static.c:18:9: note: 'x' was declared here

oob-static.c:12:10: warning: array subscript 7 is above array bounds of 'int[4]' [-Warray-bounds=]
   12 |     table[7] = 1;
oob-static.c:8:12: note: while referencing 'table'
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `13` | L26/L27 `alias-violate.c:13:13` 与源码行 13 | B: alias-src、alias-warn、warns3；D: alias-warn；发行（B站/抖音/知乎/小红书） |
| `19` | L31/L32 `oob-static.c:19:14`、`return x + 1` | B: warns3；发行（B站/抖音/知乎/小红书） |
| `14` | L31 `oob-static.c:19:14` 的列号 | B: warns3；发行（B站/抖音/知乎/小红书） |
| `18` | L34/L35 `oob-static.c:18:9: note: 'x' was declared here` | B: warns3（代码与旁白） |
| `9` | L34 `18:9` 的行列号 | B: warns3（代码与旁白） |
| `12` | L38 `oob-static.c:12:10` 的列号；L41 `oob-static.c:8:12` 的行号 | B: warns3；发行（B站/抖音/知乎/小红书） |
| `8` | L41 `oob-static.c:8:12: note: while referencing 'table'` | B: warns3（代码与旁白） |
| `7` | L38 `array subscript 7 is above array bounds of 'int[4]'` | B: warns3；发行（B站/知乎/小红书） |
| `10` | L38 `oob-static.c:12:10` 的列号 | B: warns3；发行（B站/抖音/知乎/小红书） |
| `4` | L38 `int[4]`；L45 第 4 步 UBSan | B: warns3、ubsan-honest；发行（B站/知乎/小红书） |

注：`alias-warn` 场把第一条警告连同源码行、波浪线一起上屏；`warns3` 场是三条警告的**节选**，
换行位置按画面调整，警告文字、文件名、行列号与标志都没有改写。日志只证明这三条会被警告，
没有证明「所有 UB 都会被警告」；旁白明确说「警告是网，不是墙」。

### 3.3 交叉汇编与宿主汇编（日志 L48–L107）

#### 交叉 `-O2`：只剩两行（L50–L53）

```text
is_bigger_after_inc:
	movs	r0, #1
	bx	lr
```

#### 交叉 `-fwrapv -O2`：真算（L54–L60）

```text
is_bigger_after_inc:
	mvn	r3, #-2147483648
	subs	r0, r0, r3
	it	ne
	movne	r0, #1
	bx	lr
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `1` | L52 `movs r0, #1`；L59–L60 `movne r0, #1` | B: bigger-arm；D: bigger-arm |
| `-2147483648` | L56 `mvn r3, #-2147483648` | 见 3.1 |

注：`-O2` 段只有两条指令；`-fwrapv` 段用 `mvn` 造出 `INT_MAX`，再用 `subs` 与条件执行算出比较结果。
两段都是 `15.2.1` 的输出，版本行在 L49；日志没有打印 10.3.1 或第三套交叉工具链。

#### 宿主 `-O0` 的 `is_bigger_after_inc`（L64–L70）

```text
is_bigger_after_inc:
	pushq	%rbp
	movq	%rsp, %rbp
	movl	%ecx, 16(%rbp)
	movl	$1, %eax
	popq	%rbp
	ret
```

#### 宿主 `-O0` 的 `shift_oob`（L72–L83）

```text
shift_oob:
	pushq	%rbp
	movq	%rsp, %rbp
	movl	%ecx, 16(%rbp)
	movl	%edx, 24(%rbp)
	movl	24(%rbp), %eax
	movl	16(%rbp), %edx
	movl	%eax, %ecx
	sall	%cl, %edx
	movl	%edx, %eax
	popq	%rbp
	ret
```

#### 宿主 `-O2` 的 `main`（节选，L84–L107）

```text
	subq	$40, %rsp
	call	__main
	movl	$1, %edx
	leaq	.LC0(%rip), %rcx
	call	printf
	leaq	.LC1(%rip), %rcx
	xorl	%edx, %edx
	call	printf
	movl	$1065353216, %edx
	leaq	.LC2(%rip), %rcx
	call	printf
	movl	$1065353216, %edx
	leaq	.LC3(%rip), %rcx
	call	printf
	movl	$2, %r8d
	movl	$2, %edx
	leaq	.LC4(%rip), %rcx
	call	printf
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `16` | L67/L75/L78 `16(%rbp)` 的栈偏移 | B: bigger-host-o0、shift-asm；D: bigger-host-o0、shift-asm |
| `1` | L68 `movl $1, %eax`；L89 `movl $1, %edx` | B: bigger-host-o0、bigger-host-o2；D: bigger-host-o0 |
| `0` | L93 `xorl %edx, %edx` | B: bigger-host-o2、shift-fold |
| `1065353216` | L95/L98 | B: bigger-host-o2 |
| `2` | L101/L102 `movl $2, %r8d` / `movl $2, %edx`（打印 `2/2`） | 见 3.1 |

注：`-O2 main` 里消失的是被探的**四个函数调用**（`is_bigger_after_inc`、`shift_oob`、`bits_union`、`bits_memcpy`）；
`call __main` 与五条 `call printf` 仍在。v2 的旁白写「那四个函数的 call 全没了」，不写「main 里一个 call 都不剩」。
`movl %ecx, 16(%rbp)` 为什么用 `%ecx` 而不是 `%edi`，日志没有解释，v2 只照录，不推断 ABI 原因。

### 3.4 派生量、常量与例外 token

| token | 来源 / 口径 | 处理 |
|---|---|---|
| `31` | x86 32 位移位器只取计数低 5 位，等价于 `33 & 31`；日志只打印「33 被移位器截成 1 → 结果 2」（L71），没有打印 31 | `numbers.exceptions`；上屏只出现在 `shift-asm` 的算式 `33 & 31 = 1` 和 `shift-fold` 的 `(int)1 << 31` |
| `32` | 32 位操作数的位宽，也是移位计数的合法上限；语言与指令集常量，不是 probe 读数 | `numbers.exceptions`；上屏出现在 `shift-fold` 的「计数 >= 32」、`shift-asm` 旁白的「32 位」、`safe-mask` 的 `n < 32u` |
| `07` | 复现路径 `code/c/07-ub-misra` 的章节号 | `numbers.exceptions` |
| `4` | 两重语境：`int[4]` 的数组长度（L38）与 UBSan「第 4 步」（L45） | 一个 token 同时有实测与步骤号两种语境，审计只按 token 对齐 |
| `1` / `2` | 除读数外，也出现在 `probe.sh 第 1、2 步` 的 codeLabel | 同上；不把步骤号冒充成测量值 |
| `2/2` | 每档断言行（L8/L14/L21） | 旁白说「每组 2/2 断言只核对非 UB 的事实」 |

日志没有单独的「33 & 31」行，这个等式是 x86 指令语义的推导：`sall` 的 32 位操作数使用 5 位计数，
日志的注释只给出「33 被截成 1」。v2 在 `shift-asm` 的 codeB 上屏这个算式，同时用 `numbers.exceptions` 登记 31，
并在旁白里说明「这个二是硬件顺手兜的，不是 C 标准给的」。

### 3.5 封面与发行文案

- 封面按 v2 合同使用 `variant: "vs"` 与四尺寸：bilibili 1920×1200、douyin 1080×1440、zhihu 1920×1080、
  xiaohongshu 1440×1080。
- 对撞两列：左「-O0：shift_oob = 2」，右「-O2：shift_oob = 0」；两侧都是宿主实测（L5、L11），
  `vs.labels: ["MEASURED", "MEASURED"]`，没有任何一侧标成 `EXPECTED`。
- 封面 `proof` / `proofShort` 只用 L71 的 `sall` 与「33 被截成 1」、L85 的 `xorl`/「UB 之后编译器爱给什么给什么」、
  L6/L7/L12/L13 的 `0x3F800000`；`num: "2 / 0"`；`numNote` 明写这是 `shift_oob(1u, 33u)` 在 `-O0` 与 `-O2` 的本机读数。
- 发行文案（B站/抖音/知乎/小红书）只写三档读数、三条警告的位置与标志、两段交叉汇编、`0x3F800000` 与两个工具链版本；
  **没有**写 10.3.1、MISRA 条数、`-Wall`/`-Werror`/`-Wconversion`、HardFault 现场，也没有写任何 UBSan 输出。
- 抖音的 11 个 pick 与 v1 完全一致，`narration` 全部走 `platforms.douyin.narration` 顶层映射；
  `set` 只做画面字段覆盖，不携带旁白文本。

## 4. 不能删的技术断言（删了会让章节断链）

1. **同一行两个答案**：`shift_oob(1u, 33u)` 在宿主 `-O0` 得 2、`-O2` 得 0；源码相同，答案相反，且都不是标准答案。
   删掉这条，整集的钩子没有现场。
2. **`-O0` 也折叠**：宿主 `-O0` 的 `is_bigger_after_inc` 函数体里只有 `movl $1, %eax` 这一条计算；
   加法和比较已经没了。删掉这条，观众会以为「关掉优化就照源码走」。
3. **`-fwrapv` 只改有符号溢出的合同**：同一函数 `-fwrapv` 后读 0，交叉汇编从 `movs/bx lr` 变成
   `mvn/subs/it/movne/bx lr`；但它不救移位，`shift_oob` 仍是 0（L18）。
4. **交叉 `-O2` 的形状**：`is_bigger_after_inc` 只剩 `movs r0, #1` 与 `bx lr`；这是 15.2.1 对 Cortex-M4 的输出。
   删掉这条，「编译器按合同折叠」只剩形容词。
5. **宿主 `-O2 main` 的四个立即数**：`$1`（恒真）、`xorl` 的 0（移位）、两份 `$1065353216`（两种位读）；
   同时 `call __main` 与五条 `call printf` 仍在。删掉后半句，就会把「四个函数调用消失」夸成「main 里没有 call」。
6. **2 是硬件兜的**：`-O0` 真发 `sall %cl, %edx`；x86 32 位移位器把 33 截成 1，`1u << 1 = 2`。
   这个 2 不是 C 标准给的，换机器可能不同。删掉这条，会把硬件行为冒充成语言规定。
7. **0 是编译器挑的**：`-O2` 用 `xorl %edx, %edx` 把 0 递给 `printf`；日志注释原话是
   「UB 之后编译器爱给什么给什么」。0 不是移位算出来的，也不是唯一可能值。删掉这条，会把「这次给 0」误当「UB 返回 0」。
8. **三条警告的位置与边界**：严格别名 `13:13`、未初始化 `19:14`（声明 `18:9`）、数组下标 7 越过 `int[4]`
   在 `12:10`（表在 `8:12`）。警告不是错误，编译仍会产出二进制；警告也抓不到运行期才出现的移位计数。
9. **UBSan 缺席**：本工具链没有 UBSan 运行库，第 4 步跳过，没有输出。删掉这条，就会伪造一份运行期报告。
10. **合法位读**：`union` 双关与 `memcpy` 都得到 `0x3F800000`；跨类型取位以 `memcpy` 为锚，不用指针强转。
    删掉这条，「合法写法」没有正面证据。

## 5. 已知未取证项（明确「不上屏」或只作叙述前提）

| 项 | 状态 | 处理 |
|---|---|---|
| UBSan 的运行期输出 | 日志只有 L46 的跳过说明，没有运行库、没有任何报告 | 全集只说「跳过、没有输出」；不写 `-fsanitize=undefined` 会报什么 |
| 板上现象 / HardFault / 寄存器现场 | 日志没有开发板、GDB、串口或异常记录 | v1 的 `hardfault-link` 改为「合同条款」的通用提醒，不列寄存器、不写板上现象 |
| 10.3.1 交叉工具链 | 本次日志只有 15.2.1（L49），没有 10.3.1 的汇编 | v1 的 10.3.1 段删除；v2 只写 15.2.1 两段 |
| MISRA-C 条数与十条清单 | 日志没有 MISRA 文本或规则编号 | v1 的「三百多条 / 十条」删除；v2 改成 5 条与现场一一对应的检查表 |
| `-Wall` / `-Wextra` / `-Werror` / `-Wconversion` | 本次日志没有这些旗标的运行输出 | v2 不写这些旗标；只写实际出现的 `-Wstrict-aliasing`、`-Wuninitialized`、`-Warray-bounds=` |
| `31` | 日志没有打印 31，只打印「33 被截成 1」 | 作为 `numbers.exceptions`；上屏算式注明是 ISA 掩码 |
| `32` | 语言与指令集常量，不是 probe 读数 | 作为 `numbers.exceptions`；只用于「位宽 / 合法上限」语境 |
| `%ecx` 而不是 `%edi` | 日志只给汇编，不解释调用约定或参数落位原因 | 照录 `movl %ecx, 16(%rbp)`，不推断 ABI |
| `call __main` 的作用 | 日志只显示这条调用仍在 | 只说它仍在，不解释 MinGW 运行时初始化 |
| `movl $2, %r8d` / `movl $2, %edx` | 日志 L101–L102 是打印 `2/2` 的参数 | 旁白只说「每组 2/2 断言」，不引申为其他读数 |
| 运行时长 / TTS 实测 | 本任务不做长构建，没有音频 | 只给字数与估算，不声称实际时长 |
| 具体栈地址 / 返回地址 | 日志没有运行期地址 | 全集不写地址 |
| 「UB 总是返回 0」 | 日志恰好两次读 0，但标准不保证 | 不写；旁白明确「它给零只是这次最省，不是规定」 |
| 「警告能抓全部 UB」 | 日志只有三条警告 | 不写；旁白明确「警告是网，不是墙」 |

## 6. 与 v1 旧稿的关系

- **音色与语速**：v1 是 `zh-CN-YunxiNeural` / `+4%`；v2 按合同改为 `zh-CN-YunyangNeural` / `+2%`。
- **场次骨架保留**：32 个 bilibili 场景 id 与顺序完全保留；抖音 11 个 pick 及顺序也完全保留。
  只重写画面字段、旁白与发行文案，没有为了改稿而重命名场景。
- **钩子收缩**：v1 的 `hook-01` 与 `hook-02` 两场都是 `kind: "hook"`；v2 只有 `hook-01` 是 hook
  （62 字），`hook-02` 改为 code、`hook-03` 保持 card，避免连续钩子超过 15 秒。
- **10.3.1 整段删除**：v1 的 `bigger-wrapv` 并排了 15.2.1 与 10.3.1 两套交叉汇编；本次日志只有 15.2.1，
  v2 删掉 10.3.1 的 `adds/cmp/ite/movle/movgt`，只保留有日志依据的 `mvn/subs/it/movne`。
- **UBSan 说法收紧**：v1 写「有 Linux 环境的话，同一段代码会直接报出有符号溢出」；这是假设性输出，
  v2 删掉，改为「本工具链没有运行库，第 4 步跳过，没有输出」。
- **MISRA 说法删除**：v1 的 `misra-a` / `misra-b` 写「MISRA-C 全本三百多条，取自用十条」，并列出十条规则；
  日志没有 MISRA 依据。v2 保留两个 id，但改成 5 条与前面现场一一对应的检查表，不声称任何标准条数。
- **警告旗标收紧**：v1 的 `warns3` 推荐 `-Wall -Wextra -Werror -Wconversion`；这些旗标本次没有运行输出。
  v2 只写日志里真正出现的三条 warning 与三个 `-W...` 标志，并保留「警告是网，不是墙」的边界。
- **HardFault 改为合同视角**：v1 的 `hardfault-link` 声称「越界、空指针、未对齐访问在 ARM 上会直接把 CPU 打进异常」；
  本次没有板上证据，v2 改为「编译器只是把合同执行到底，危险的是你没读过的 UB 条款」，不写具体异常与寄存器。
- **封面补齐合同字段**：v1 只有 bilibili 与 douyin 两个尺寸，`vs` 两列没有 `labels`；v2 按 v2 合同补上
  `variant: "vs"`、zhihu 1920×1080、xiaohongshu 1440×1080 与 `["MEASURED", "MEASURED"]`，两侧都不标 `EXPECTED`。
- **读数表标注「整理」**：v1 的 `bigger-readout` 把三档读数排成一张表，容易看成一次连续输出；
  v2 的 `codeLabel` 明写「probe.sh 第 1、2 步读数（整理）」，旁白也说明这是现场记录、不是标准答案。
- **`memcpy` 不再声称代码生成**：v1 说 `memcpy` 写法「编译器会把它优化成一条访存指令」；日志只证明返回值。
  v2 改为「标准保证合法，位模式一个不差」，不声称优化器生成几条指令。
- **零句复用**：v1 与 v2 逐句比对，完整句子复用 0 条（按 `。！？` 与换行切句，长度 ≥6 字的句子无一相同）；
  最长公共片段 19 字符，是技术行文「同一行 1u 左移 33 位：-O0 」，不是叙述句。

## 7. 审计回填

- `npm run video:lint -- c7-ub`：

```text
▶ c7-ub  未定义行为：编译器不欠你一个答案  [bilibili, douyin]
  ✅ 通过：bilibili 32 场，douyin 11 场

✅ 全部通过
```

- `npm run video:numbers -- c7-ub`：`✅ c7-ub: 24 个数字都有依据`。
- 旁白字数（实测）：bilibili 3252 字（目标 3000–3400，硬区间 2087–3510）；
  douyin 277 字（目标 240–280，硬区间 135–305）。
- 估算时长：bilibili 3252 × 0.1955 ≈ 636 s（目标 480–720 s）；
  douyin 277 × 0.1946 + 11 × 1.091 ≈ 66 s（目标 45–75 s）。
- 开场连续 `kind: "hook"` 只有 `hook-01`，实测 bilibili 11.966667 s、douyin 8.900000 s，均低于 15 s 上限。
- 节与场次：

| 节 | 起止场次 | 场数 |
|---|---|---:|
| 片头 | hook-01 → hook-03 | 3 |
| 恒真与折叠 | bigger-src → bigger-wrapv | 6 |
| 链条四幕 | trap-1 → sneak-card | 5 |
| 移位红线 | shift-src → wrapv-norescue | 5 |
| 别名与警告 | alias-src → ubsan-honest | 6 |
| 收束 | misra-a → teaser | 7 |

### 7.1 最终母版实测（2026-10-23 修复后重建）

| 项 | bilibili | douyin |
|---|---|---|
| 场景 / 帧 | 32 / 19293 | 11 / 1848 |
| 时长（timeline = ffprobe） | 643.100000 s | 61.600000 s |
| 漂移 | 0.000001 s | 0 |
| 响度（两遍 loudnorm） | -15.0 LUFS（首遍 -25.6） | -14.8 LUFS（首遍 -25.6） |
| 节拍（含脉冲） | 317（0） | 32（0） |
| 最长静止 | 4.2 s | 3.6 s |
| 排版审计 | 32 场 0 问题，最小字号 21.1px | 11 场 0 问题，最小字号 25.3px |
| 成片大小 | 47,429,396 B | 6,271,393 B |
| stills | 13 | 13 |

- `video:check -- c7-ub --platform both`：两平台全绿（见 `.temp/v2-facts/c7-gates-final2.log`）。
- 封面：bilibili 1920×1200、douyin 1080×1440、zhihu 1920×1080、xiaohongshu/douyin-4:3 1440×1080、接触表 1440×460。
- `video:pack -- c7-ub`：四平台发布包 + 四份 `发布-*.md` + `bili-submit.yaml`（v2 标题、简介、32 条时间轴、7 标签）。
- `video:test`：100/100（`.temp/v2-facts/c7-video-test-final.log`）。
- 抖音代码场（bigger-src / bigger-arm / bigger-host-o0 / shift-asm / shift-fold / alias-warn）用 `beatMap` 把 `code` 放到首拍、`codeB` 放到第二拍：首句字幕时主代码框已有内容，第二句字幕补右栏对照；各场停留 2.5–4 s，未出现 c6 `sum-caller` 那种不足 1 s 的空窗病态。
- 抖音 `alias-warn` 已补源码行 `13 | return *(uint32_t *)&f;` 与 `^~~~~~~~~~~~~~` 波浪线，标题「压在解引用上」与画面一致；`warns3` 的 B 站标签写明「警告原文（节选）」，与旁白「原文节选，没有补写」一致。
- `bili-submit.yaml` 复评：标题「同一行 1u<<33：-O0 得 2、-O2 得 0，两个答案都不是标准答案」，简介含 32 条章节；生成前快照 18 份，生成后除 c7-ub 外 17 份逐字节复原（`s5-systick` 仍是既有陈旧 desc，生成器会改写它，已复原；留 Task 15 统一重生成）。

## 8. 证据行索引

| 行 | 内容 |
|---|---|
| L1–L2 | 第 1 步标题；宿主 `gcc 16.1.0` |
| L3–L8 | `-O0` 四条读数与 `2/2` 断言 |
| L9–L14 | `-O2` 四条读数与 `2/2` 断言 |
| L16–L21 | `-fwrapv` 四条读数与 `2/2` 断言 |
| L23–L28 | 严格别名警告与源码行、波浪线 |
| L29–L36 | 未初始化警告、声明 note 与源码行 |
| L37–L43 | 常量下标越界警告、`table` note 与源码行 |
| L45–L46 | UBSan 第 4 步跳过说明 |
| L48–L53 | 交叉 `15.2.1`、`-O2` 的 `movs` / `bx lr` |
| L54–L60 | 交叉 `-fwrapv -O2` 的 `mvn` / `subs` / `it` / `movne` / `bx lr` |
| L62–L70 | 宿主 `-O0` 的 `is_bigger_after_inc` 函数体 |
| L71–L83 | 宿主 `-O0` 的 `shift_oob` 函数体与 `sall` |
| L84–L85 | 宿主 `-O2 main` 标题与立即数注释 |
| L86–L107 | 宿主 `-O2 main` 的 `$1`、`xorl`、两份 `$1065353216` 与 `2/2` 打印 |
