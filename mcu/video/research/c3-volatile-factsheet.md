# C3《volatile：跟编译器约法三章》事实底稿

本文件是 `video/episodes/c3-volatile/episode.json` 的上屏/口播数字对账底稿。所有输出行都从**本次**运行
`.temp/v2-facts/c3-probe.log`（153 行）原样摘出；旧稿与 `docs/c/03-volatile.md` 只在「叙述前提」与
「例外」两处出现，并逐条标明，不冒充本次读数。

## 1. 取证信息

| 项 | 值 |
|---|---|
| 源文档 | `docs/c/03-volatile.md` |
| 取证脚本 | `code/c/03-volatile/probe.sh`（宿主段调用 `opt_probe.c`；条件段调用 `blink-variants.sh`） |
| 本次日志 | `.temp/v2-facts/c3-probe.log`（153 行） |
| 宿主工具链 | `gcc 16.1.0`（日志 L2） |
| 交叉工具链 | 本日志**没有打印版本号**；六个变体的汇编已输出，说明 `arm-none-eabi-gcc` / `objdump` 在 PATH 中且该段真的跑了 |
| 宿主输出 | 七个函数体（`poll_plain` / `poll_volatile` / `delay_plain` / `delay_volatile` / `cfg_plain` / `cfg_volatile` / `isr_toggle`）加三行现场结论 |
| 宿主断言 | 本日志**没有**「断言通过」「42 条断言」这类行；`42` 是 `poll_*` 的返回值 |
| 板级灯态 | 日志**没有** LED 闪灭的实测输出。片头「-O0 灯在闪 / -O2 灯灭了」来自 `docs/c/03-volatile.md` 开头记录的说法，本集只当叙述前提 |
| 数字审计 | `npm run video:numbers -- c3-volatile` → `30 个数字都有依据`（§7） |

## 2. 本集必须回答的 5 个问题

1. `poll_plain` 为什么只读一次就原地空转？`volatile` 加回去以后，循环里多了什么？
2. `delay_plain` 为什么整条只剩 `ret`？参数上的 `volatile` 和循环体里的 `nop` 各挡哪一刀？
3. 三次 `|=` 为什么能被并成一条 `orl $7`？`volatile` 版为什么一条都并不掉？
4. `volatile` 保证了访存，为什么仍然不是锁？共享标志的读-改-写还缺什么？
5. 六个变体里，A 与 B/C/D 的 `main` 开头为什么同形？F 和 E 的顺序是怎么倒的？

## 3. 上屏数字逐项对账

> 场景写法：`B:` = bilibili，`D:` = douyin，`封面` = 主封面，`发行` = publish 文案。
> 同一行日志里的多个 token 共用一个证据行；每个 token 都列出它实际出现的场景。

### 3.1 宿主七个函数体（日志 L4–L63，制表符按空格显示）

```text
poll_plain:
	testb	$1, g_status(%rip)
	je	.L3
	movl	$42, %eax
	ret
.L3:
	jmp	.L3

poll_volatile:
	.p2align 4
.L6:
	testb	$1, v_status(%rip)
	je	.L6
	movl	$42, %eax
	ret

delay_plain:
	ret

delay_volatile:
	movl	%ecx, 8(%rsp)
.L11:
	movl	8(%rsp), %eax
	leal	-1(%rax), %edx
	testl	%eax, %eax
	movl	%edx, 8(%rsp)
	jne	.L11
	ret

cfg_plain:
	orl	$7, (%rcx)
	ret

cfg_volatile:
	orl	$1, (%rcx)
	orl	$2, (%rcx)
	orl	$4, (%rcx)
	ret

isr_toggle:
	xorl	$1, shared_flag(%rip)
	ret
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `1` | L6/L20 `testb $1`；L54 `orl $1`；L62 `xorl $1` | B: poll-x86、poll-m4、poll-vol、rmw-x86、rmw-m4、isr-m4、fix-bsrr、fix-barrier、fix-critical；D: poll-m4、rmw-m4、isr-m4、fix-bsrr、fix-barrier；封面 |
| `42` | L8/L22 `movl $42, %eax` | B: poll-x86、poll-m4、poll-vol；D: poll-m4 |
| `7` | L48 `orl $7, (%rcx)` | B: rmw-x86；D: rmw-m4；封面；发行（B站/抖音/知乎/小红书） |
| `2` | L55 `orl $2, (%rcx)` | B: rmw-x86、rmw-m4；D: rmw-m4 |
| `4` | L65 `4 次 xor`；L56 `orl $4` | B: poll-vol、rmw-x86、rmw-m4、isr-m4；D: rmw-m4、isr-m4 |
| `0` | L65 `shared_flag = 0` | B: isr-m4、fix-barrier；D: isr-m4、fix-barrier |
| `-1` | L39 `leal -1(%rax), %edx` | B: delay-m4、var-D；D: delay-m4 |
| `8` | L33/L38/L41 `8(%rsp)` | B: delay-m4、var-D；D: delay-m4 |

注：`poll_plain` 全文只有一条 `testb` 读 `g_status`，之后 `.L3:` 只有 `jmp .L3`；封面 `num: "1 次"`
就是按这两行数的，不是额外测量。`42` 是函数返回值，**不是断言条数**——v1 发行文案里的「42 条断言」在
本日志没有依据，v2 已删。

### 3.2 三行现场结论（日志 L65–L67）

```text
现场4：4 次 xor 之后 shared_flag = 0（值对，但每一步都不是原子的）
现场2：delay_volatile(1000000) 真的耗了时间
现场3：cfg_plain 与 cfg_volatile 的差别只能从汇编看——make asm O=2
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `4` | L65「4 次 xor」 | B: isr-m4；D: isr-m4 |
| `0` | L65 `shared_flag = 0` | B: isr-m4；D: isr-m4 |
| `1000000` | L66 `delay_volatile(1000000)` | 旁白只说「真的耗了时间」，不把 1000000 上屏；numbers 未收这个 token |

注：`isr_toggle` 在宿主上被编成一条 `xorl $1, shared_flag(%rip)`；模型结论说「值对，但每一步都不是
原子的」。旁白据此只说「宿主看着像一步，换到要分几条指令完成的机器上，中断插在中间就会丢更新」，
**没有**声称本日志打印了 Cortex-M4 的 `ldr/eor/str`。

### 3.3 六个变体的 `main` 开头（日志 L69–L151）

每个变体只打印 **12 条指令**（`blink-variants.sh` 的 `sed -n '2,13p'`），不是完整 `main`，也没有函数
尾部。下面只引用日志实际出现的行；本集**不根据没打印的尾部推断指令条数**，也不写「后面还有几条」。
A/B/C/D/E 的 `codeB` 都省掉了取基址的两条 `ldr [pc, #...]`，并在 codeLabel 明写「取基址的两条 ldr 略」。

#### A（L70–L81）

```text
ldr.w	r3, [r2, #2096]	; 0x830
orr.w	r3, r3, #32
str.w	r3, [r2, #2096]	; 0x830
ldr.w	r3, [r1, #1024]	; 0x400
bic.w	r3, r3, #12288	; 0x3000
str.w	r3, [r1, #1024]	; 0x400
ldr.w	r3, [r1, #1024]	; 0x400
orr.w	r3, r3, #4096	; 0x1000
str.w	r3, [r1, #1024]	; 0x400
ldr.w	r3, [r1, #1028]	; 0x404
```

#### B（L84–L95）

```text
ldr.w	r3, [r1, #2096]	; 0x830
orr.w	r3, r3, #32
str.w	r3, [r1, #2096]	; 0x830
ldr.w	r3, [r2, #1024]	; 0x400
bic.w	r3, r3, #12288	; 0x3000
str.w	r3, [r2, #1024]	; 0x400
ldr.w	r3, [r2, #1024]	; 0x400
orr.w	r3, r3, #4096	; 0x1000
str.w	r3, [r2, #1024]	; 0x400
ldr.w	r3, [r2, #1028]	; 0x404
```

注：B 与 A 的前十行逐条同形，只是两个基址寄存器编号对调；参数 `volatile` 的差别在 `delay` 里，本日志
没有截 `delay` 的 ARM 函数体。板级「灯照闪」来自文档记录，不是本次 probe 输出。

#### C（L98–L109）

```text
ldr.w	r2, [r0, #2096]	; 0x830
orr.w	r2, r2, #32
str.w	r2, [r0, #2096]	; 0x830
ldr.w	r0, [r3, #1024]	; 0x400
bic.w	r0, r0, #12288	; 0x3000
str.w	r0, [r3, #1024]	; 0x400
ldr.w	r0, [r3, #1024]	; 0x400
orr.w	r0, r0, #4096	; 0x1000
str.w	r0, [r3, #1024]	; 0x400
ldr.w	r0, [r3, #1028]	; 0x404
```

注：C 的 `main` 开头仍与 A 同形；本集讲「延时消失」时，用的是宿主 `delay_plain` 只剩 `ret` 的同类
形状（L28），没有伪造 C 的 ARM `delay` 尾部。

#### D（L112–L123）

D 的 `main` 开头与 A 逐条同形（寄存器编号也相同），本集因此改用宿主 `delay_volatile` 的循环形状
（L31–L43）讲「参数还带 volatile，循环留得住」；没有声称 D 的 ARM `main` 有额外指令。

#### F（L126–L137）

```text
ldr.w	r3, [r1, #1024]	; 0x400
ldr.w	r4, [r2, #2096]	; 0x830
ldr.w	r0, [r1, #1028]	; 0x404
orr.w	r4, r4, #32
bic.w	r3, r3, #12288	; 0x3000
str.w	r4, [r2, #2096]	; 0x830
orr.w	r3, r3, #4096	; 0x1000
ldr.w	r2, [r1, #1032]	; 0x408
str.w	r3, [r1, #1024]	; 0x400
ldr.w	r3, [r1, #1036]	; 0x40c
```

注：F 的头三条读依次是 `0x400`、`0x830`、`0x404`，而写 `0x830` 落在第 6 条——读被提到开时钟之前，
这是日志实际行，不靠推断。板级「可能照常、也可能换芯片就配不上」来自文档记录。

#### E（L140–L151）

```text
ldr.w	r3, [r2, #1024]	; 0x400
ldr.w	r0, [r4, #2096]	; 0x830
ldr.w	r1, [r2, #1028]	; 0x404
bic.w	r3, r3, #12288	; 0x3000
orr.w	r0, r0, #32
orr.w	r3, r3, #4096	; 0x1000
bic.w	r1, r1, #64	; 0x40
str.w	r0, [r4, #2096]	; 0x830
str.w	r3, [r2, #1024]	; 0x400
str.w	r1, [r2, #1028]	; 0x404
```

注：E 的前三条全是读，后三条全是写；读提前、写推后都能在日志里逐行对上。

### 3.4 偏移与常量

| 上屏 token | 日志行 | 场景 |
|---|---|---|
| `2096` / `0x830` | L72、L86、L100、L129、L143 | B: var-A/B/C/F/E；D: var-F；封面；发行 |
| `1024` / `0x400` | L75、L89、L103、L128、L142 | B: var-A/B/C/F/E；D: var-F；封面；发行 |
| `1028` / `0x404` | L81、L95、L109、L130、L144 | B: var-A/B/C/F/E；D: var-F |
| `1032` / `0x408` | L135 | B: var-F |
| `1036` / `0x40c` | L137 | B: var-F |
| `32` | L73、L87、L101、L131、L146 | B: var-A/B/C/F/E；D: var-F |
| `12288` / `0x3000` | L76、L90、L104、L132、L145 | B: var-A/B/C/F/E；D: 无（抖音 var-F 只留 5 行） |
| `4096` / `0x1000` | L79、L93、L107、L134、L147 | B: var-A/B/C/F/E；D: 无（抖音 var-F 只留 5 行） |
| `64` / `0x40` | L148 | B: var-E |

注：`0x830` 是时钟使能寄存器偏移、`0x400` 是 MODER、`0x404` 是 OTYPER、`0x408` / `0x40c` 是同一组
寄存器块的后两个字；这些语义来自 STM32 文档与 `docs/c/03-volatile.md`，日志只负责打印偏移。`32`、
`12288`、`4096`、`64` 的语义（开时钟、清两位、置输出位、清 OTYPER）同理，不当作测量值。

### 3.5 工具链与路径

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `16.1.0` | L2 `gcc.exe ... 16.1.0` | B: cta；D: cta；发行（B站） |
| `03` | 路径 `code/c/03-volatile` 的章节号 | B: var-howto、cta；D: cta；发行（四平台）；`exceptions` |
| `00` | 路径 `../../stm32/00-blink/main.c` 的工程号 | B: var-howto；`exceptions` |
| `6` | `GPIOF_BSRR = 1UL << 6` 的源码常量 | B: fix-bsrr、fix-barrier；D: fix-bsrr、fix-barrier；`exceptions` |
| `16` | `(6 + 16)` 的源码常量（只出现在 B 站 fix-bsrr） | B: fix-bsrr；`exceptions` |

### 3.6 发行文案与封面

封面 `proof` / `proofShort` 只用了 `testb $1`、`orl $7`、`0x830`、`0x400`，均在 §3.1/§3.4 有日志行。
对撞两列（`-O0 灯在闪` / `-O2 灯灭了`）标 `DOCUMENTED`，页脚写「文档灯态 · 代码实跑 / 寄存器级 · 代码可复现」；
灯态不标 `MEASURED`，因为 probe 没有板级输出。
发行文案里的 `0x830` / `0x400` / `orl $7` / `16.1.0` 同样落在上述证据行；`03` 是路径章节号，进
`exceptions`。发行文案没有出现 `42 条断言`、`delay 的 1000000`、ARM 函数尾部或灯态测量值。

## 4. 不能删的技术断言（删了会让章节断链）

1. **`poll_plain` 只读一次**：`testb` 一次后 `.L3: jmp .L3`；`volatile` 版 `testb` 回到 `.L6` 循环。
   删掉这条，片头的「1 次」与轮询死等没有现场。
2. **`delay_plain` 只剩 `ret`**：没有副作用、没有 `volatile` 的计数循环可以被整个删掉；参数带
   `volatile` 后 `delay_volatile` 每圈读、减、存、比较。删掉这条，延时消失讲不成。
3. **三次写并一次**：`cfg_plain` 一条 `orl $7`，`cfg_volatile` 三条 `orl`。删掉这条，「写次数=源码
   次数」没有对照。
4. **`volatile` 不是锁**：`isr_toggle` 在宿主上一条 `xorl`，模型结论「值对，但每一步都不是原子的」。
   删掉这条，后文临界区与原子性没有落点。
5. **A 的顺序**：先写 `0x830` 开时钟，再读 `0x400` 配引脚。删掉这条，F 的「读被提前」没有参照。
6. **F 的重排**：头三条读是 `0x400`、`0x830`、`0x404`，写 `0x830` 在第 6 条。删掉这条，最阴的变体
   只剩形容词。
7. **E 的读写分离**：三条读在前、三条写在后。删掉这条，「读提前、写推后」没有现场。
8. **两层合同的边界**：`volatile` 管访存次数，屏障管顺序，临界区/原子指令管打断。删掉这条，补法
   三条会互相冒充。

## 5. 已知未取证项（明确「不上屏」或只作叙述前提）

| 项 | 状态 | 处理 |
|---|---|---|
| 板上 `-O0` / `-O2` 灯态 | 日志没有 LED 输出；本集没有开发板 | 只作 `docs/c/03-volatile.md` 的叙述前提；片头 sub 写「这句话先当传闻」，cta 与发行文案明写「灯的现象来自文档，不是本次 probe」 |
| 六个变体的完整 `main` | 每个只打印 12 条指令，尾部没打印 | 只描述日志实际出现的 10–12 行；不推断函数总指令数，不写「后面还有几条」 |
| B/C/D 的 ARM `delay` 函数体 | 日志只打印 `main` 开头，没有 `delay` | C 用宿主 `delay_plain` 的同类形状说明机制；D 用宿主 `delay_volatile`；不说「C/D 的 ARM delay 就是这样」 |
| ARM `poll_plain` / `poll_volatile` / `isr_toggle` | 日志的 ARM 段只有六个 `main` 变体 | v1 的 `poll-m4` / `isr-m4` 的 ARM 汇编已改成宿主日志实际打印的形态；不冒充实测 |
| 交叉工具链版本 | `blink-variants.sh` 不打印版本 | 不写 `15.2.1` 等版本号；只说「交叉段真的跑了」 |
| 断言条数 | 日志没有断言计数 | 不写「42 条断言」；`42` 只当 `poll_*` 返回值 |
| `delay_volatile(1000000)` 的实际耗时 | 日志只说「真的耗了时间」，没有毫秒数 | 不上屏具体耗时，只讲循环还在 |
| BSRR 位号 `6` / 高半区 `16` | 日志不打印，来自源码常量 | 放 `numbers.exceptions`，不冒充 probe 读数 |
| 灯全黑 / 偶尔不对 | 文档的板级记录，不是本次测量 | 旁白用「文档记录的板级现象」限定 |

## 6. 与旧对账的关系

- v1 的 `poll-m4`、`delay-m4`、`isr-m4` 展示过 ARM 的 `poll_plain` / `delay` / `isr_toggle` 汇编；
  本次 `c3-probe.log` 的 ARM 段只打印六个 `main` 变体，**没有**这些函数体。v2 已把这三场改成宿主
  日志实际打印的形态（`poll-m4` 仍讲同一条 `jmp` 循环，`delay-m4` 讲宿主 `delay_plain` / `delay_volatile`，
  `isr-m4` 讲宿主 `xorl` 加模型结论），并在 codeLabel 明写宿主口径。
- v1 的 `var-C` 声称「delay 被优化成空函数、调用点内联、两条 BSRR 写挤在一起」；本次日志没有打印
  C 的 ARM `delay` 尾部，也没有打印两条 BSRR 写。v2 改用宿主 `delay_plain` 的 `ret` 说明同类机制，
  不再声称 C 的尾部逐条可见。
- v1 的 `42 条断言` 没有本次日志依据；v2 已删，`42` 还原为 `poll_*` 返回值。
- v1 的 `-O0 灯在闪 / -O2 灯灭了` 保留为片头钩子，但明确是文档叙述前提；本集新增 B/C/E 的纠正，
  避免把「-O2 一开灯就灭」当成无条件结论。
- v1 的 `1 次` 封面数字保留：`poll_plain` 全文只有一条 `testb`，与日志 L6/L11 对得上。

## 7. 审计回填

- `npm run video:lint -- c3-volatile`：✅ bilibili 39 场，douyin 14 场，5 节。
- `npm run video:numbers -- c3-volatile`：✅ 30 个数字都有依据（0 未命中）。
- 旁白字数（实测）：bilibili 3393 字；douyin 288 字（硬预算 119–288，落在上沿内）。
- `npm run video:check -- c3-volatile`：bilibili 39 场、douyin 14 场，0 问题；最长静止 4.1s / 2.5s。
