---
title: B6 烧录与调试：SWD 与断点的真相
status: done
difficulty: 2
minutes: 30
---

# B6 烧录与调试：两根线如何统治一颗芯片

> 🎯 烧录和调试看起来像两个功能，其实是同一件事：通过 SWD 两根线，直接读写芯片的内存、寄存器，甚至让它停下来。OpenOCD 和 GDB 只是这对"超能力"的两个客户端。

## 本章精髓

1. SWD 只有三根线（SWDIO/SWCLK/GND）：一套请求-响应协议，读写一个叫 DP（调试端口）的家伙，再由 AP（访问端口）摸到整个地址空间，**CPU 跑不跑都能摸**。
2. 烧录=主机帮你执行擦写：OpenOCD 把一小段"擦写算法"灌进 RAM，让它替自己干活（所以 program 命令要选对 target 配置）。
3. 断点有两副面孔：硬件断点（FPB 比较器，数量有限，Flash 里也能下）vs 软件断点（改写成 BKPT 指令，RAM 才行，数量不限）；GDB 的 `hbreak` 与 `break` 由此分家。

- **能理解**：为什么烧录要把"擦写算法"灌进 RAM 代劳；为什么 Flash 里的代码用 `break` 有时失败而 `hbreak` 总能成。
- **能用**：OpenOCD 常驻 + GDB 连上，完成 halt/load/读写内存/单步/断点一整套调试流。

## 先修

- [B4 启动过程](04-startup.md)；[S0](../stm32/00-env.md)（环境已就绪）。

## 先跑起来（10 分钟 quick win）

连上之前先押一题：调试器往 RAM 里写一个新值，芯片必须先停下来配合吗？还是边跑边改？押一个答案，连上后当场试。

```bash
make debug &        # OpenOCD 常驻
make gdb            # 连上即：reset halt → load → break main → continue
```

GDB 里再玩三招：`x/4xw 0x20000000`（读 RAM）、`set {int}0x20000000 = 0x1234`、`hbreak main`。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 链路全图 | PC/OpenOCD/ST-Link/SWD/DP/AP 逐环讲 | 配置 |
| program 拆解 | OpenOCD 日志逐行：halt→擦→写→verify→reset | 库解析 |
| GDB 十命令 | target remote/load/monitor/x/set/si/break/hbreak/info reg/continue | 代码分析 |
| 断点的硬件 | FPB 比较器 vs BKPT 改写；各 6 个的限额从哪来 | 库解析 |
| Semihosting 一瞥 | 让 printf 走调试通道回 PC——原理与代价（S7 的替代方案） | 库解析 |

## 一、链路全图：从 GDB 命令到芯片内存

<AnimFigure src="/anim/swd-debug-chain.svg" />

一条命令（如 `x/4xw 0x20000000` 读 RAM）走过的链路：

```
GDB ──(TCP 3333)──> OpenOCD ──(USB)──> ST-Link ──(SWD)──> 芯片 DP ──> AP ──> 总线矩阵 ──> 0x20000000
                       调试服务器      调试探针      调试端口   访问端口    AHB
```

每一环的职责：

- **GDB**：人机界面+命令调度，把 `x` 命令翻成 JTAG/SWD 包发给 OpenOCD；
- **OpenOCD**：调试服务器，把 GDB 协议翻成 SWD 请求，常驻在 PC 上监听 3333 端口；
- **ST-Link**：USB 转 SWD 的硬件探针（板载调试器），把 USB 包翻成 SWDIO/SWCLK 电平；
- **SWD**：两根线（SWDIO 双向数据、SWDCK 时钟，加 GND 共三根）的请求-响应协议；
- **DP（Debug Port）**：芯片上的调试端口，SWD 请求先进它，它再通过 AP 访问内部总线；
- **AP（Access Port）**：访问端口，把 DP 的请求转成 AHB 总线读写，**直通整个 4GB 地址空间**。

关键性质：**AP 访问总线不经过 CPU**。CPU 在跑代码也好、停在断点也好、甚至睡死，AP 都能读写任意地址。这就是"烧录和调试是同一件事"的物理基础：读写 Flash 寄存器就是烧录，读写 RAM/寄存器就是调试，读写 PC/MSP 就是控制 CPU，全走同一条 SWD 链路。

## 二、program 拆解：烧录的本质是请 RAM 里的算法代劳

`make flash` 或 GDB 的 `load` 触发 OpenOCD 的 `program` 命令，日志逐行（以 00-blink 烧录为例）：

```text
> reset halt                    # ① 复位并停住 CPU（不然它在乱跑，写 Flash 会冲突）
> flash probe 0                 # ② 探测 Flash：读 ID、容量、扇区布局
> flash write_image erase build/blink.bin 0x08000000   # ③ 擦+写
> verify_image build/blink.bin 0x08000000              # ④ 校验
> reset run                     # ⑤ 复位运行（PC 指向复位向量）
```

第 ③ 步"擦+写"最绕：OpenOCD 不能直接从 USB 往 Flash 寄存器写：Flash 编程有严格时序（解锁→擦→写→等 BSY，[S13](../stm32/13-flash-iap.md)）。OpenOCD 的办法是**把一段"擦写算法"（几十行 ARM 机器码）灌进芯片 RAM**，让 CPU 自己跑这段算法去操作 Flash 控制器；CPU 跑算法比 OpenOCD 从 USB 逐个寄存器写，更快也更可靠。OpenOCD 只负责传数据、发"开始执行算法"的命令。这就是 program 必须选对 target 配置的原因：不同芯片的擦写算法不同，配错了算法跑错寄存器，Flash 写不进去，甚至写坏。

> **【注】** 这也解释了 [S13](../stm32/13-flash-iap.md) 的"擦写关键路径放 RAM 执行"为什么是工业标准：OpenOCD 的烧录本身就是这么干的。你的 IAP bootloader 跳转函数（关中断→MSP→VTOR→跳）做的事和 OpenOCD 的"灌算法进 RAM 再让它跑"同构。

## 三、GDB 十命令：调试的日常

连上 OpenOCD 后（`target remote :3333`），GDB 十命令覆盖 90% 调试场景：

| 命令 | 干什么 | 本站用到处 |
|---|---|---|
| `target remote :3333` | 连 OpenOCD | 每次 `make gdb` |
| `load` | 烧 elf 进 Flash | 改完代码重新烧 |
| `monitor reset halt` | 复位并停 CPU | 烧前/调试前必做 |
| `x/4xw 0x20000000` | 读 4 个字（RAM/寄存器） | [C6](../c/06-abi-stack.md) 看栈帧、[S16](../stm32/16-debug-hardfault.md) 挖 PC |
| `set {int}0x20000000 = 0x1234` | 写内存（改寄存器/变量） | 不重新编译快速试值 |
| `si` / `ni` | 单步指令/指令步过 | [C6](../c/06-abi-stack.md) 走 prologue |
| `break main` | 软件断点 | RAM 代码或 Flash 代码（占 FPB） |
| `hbreak main` | 硬件断点 | Flash 代码（独占 FPB 比较器） |
| `info registers` | 看所有寄存器 | 崩溃现场、调用约定核对 |
| `continue` | 继续跑 | 单步完放它走 |

`monitor` 前缀是发给 OpenOCD 的命令（reset/flash/sleep）；不带 monitor 是发给 GDB 自己的（break/x/continue）。区分这条线：`monitor reset halt` 是 OpenOCD 让芯片复位停住，`break main` 是 GDB 设断点。

## 四、断点的硬件：FPB 比较器 vs BKPT 改写

断点两副面孔，硬件实现完全不同：

- **硬件断点（`hbreak`）**：Cortex-M4 内置 **FPB（Flash Patch and Breakpoint）单元**，6 个比较器。CPU 取指时 FPB 比对地址，命中就把 PC 停住，**不改 Flash 内容**，所以 Flash 代码能下。代价是只有 6 个（Cortex-M4 标配），超了报错。
- **软件断点（`break`）**：GDB 把目标地址的指令**改写成 `BKPT #imm`**（0xBE00 系列），CPU 执行到 BKPT 触发调试异常停下。**要能改写指令**：RAM 代码随便改，Flash 代码改不动（Flash 写要先擦整扇区），所以 `break` 在 Flash 代码上经常悄悄退回硬件断点或失败。

实战纪律：**Flash 里的代码用 `hbreak`，RAM 里的代码用 `break`**。00-blink 这种全 Flash 代码，6 个硬件断点够用；当代码大到断点多于 6 个，要么清旧断点，要么把要调试的函数搬进 RAM（`__attribute__((section(".ramfunc")))`，[S13](../stm32/13-flash-iap.md)）用软件断点。

> **【注】** 6 这个数字来自 Cortex-M4 的 FPB 设计（RM0090 调试章节）：FPB 有 6 个比较器，可配代码断点或数据字面量补丁。Cortex-M0/M0+ 只有 2 个，调试大固件时更紧张。选芯片时，这是个常被忽略的调试资源约束。

## 五、Semihosting 一瞥：printf 走调试通道

[S7 USART](../stm32/07-usart.md) 把 printf 接到串口靠 newlib 的 `_write` 钩子。Semihosting 是另一条路：让 `_write` 触发一条 `BKPT` 指令，OpenOCD 捕获后把字节通过 USB 送回 PC 的 GDB 控制台。**不用接串口，调试器一条线搞定输出**。

代价：CPU 执行 BKPT 会停住等 OpenOCD 处理，每次 printf 都要付出几十 µs 的调试通道往返，比串口慢一个数量级。适合调试期临时输出，不适合量产（量产要把 Semihosting 关掉，否则没接调试器时 BKPT 直接 HardFault）。

OpenOCD 开 Semihosting：`monitor arm semihosting enable`；newlib 链接加 `--specs=rdimon.specs`。两条配齐，printf 就走调试通道回 PC。

## 记忆锚点

::: tip 一句话记住
**SWD 两线通天，CPU 停不停都能读写；烧录是请 RAM 里的算法代劳，断点分软硬——Flash 用硬，RAM 随意。**
:::

**延伸**：SWD 链路完整解剖（DP/AP/内存访问）在本章正文展开；FreeRTOS 任务级 GDB 调试见 [F2](../rtos/freertos/02-context-switch.md)；硬件断点 FPB 与中断调试配合见 [S4 NVIC](../stm32/04-nvic-exti.md)。

## 实物实验

- `monitor flash erase_sector 0 0 0` 擦掉首扇区再复位：板子不闪了（固件没了）；重新 `make flash` 救回，亲手体验"烧录的本质是改内存"。

## 常见坑

- **GDB 连不上 3333**：OpenOCD 没常驻/防火墙拦/上一个 GDB 没退（`target remote` 是 TCP 连接）。
- **load 之后跑飞**：忘了 `monitor reset halt` 就 continue，芯片可能已在乱跑。
- **硬件断点用完**：`break` 在 Flash 区域悄悄占用 FPB 槽位（通常 6 个），超了报错，得清旧断点或换软件断点思路。
- **ST-Link 固件过旧**：OpenOCD 报 SWD/JTAG 错误，用 ST 官方工具升级固件。
- **Semihosting 没关量产**：没接调试器时 BKPT 触发 HardFault，量产构建必须关 `--specs=rdimon.specs`。

## 短自测

1. SWD 只有几根线？AP 访问总线为什么不需要 CPU 配合？
<details><summary>参考答案</summary>三根：SWDIO（双向数据）、SWDCK（时钟）、GND。AP（访问端口）直挂 AHB 总线矩阵，读写请求由 AP 发起、走总线到目标地址，不经 CPU。CPU 在跑代码、停断点、睡觉都不影响 AP 读写。这就是"烧录和调试是同一件事"的物理基础：读写 Flash 寄存器=烧录，读写 RAM/寄存器=调试，全走同一条 AP 路径。</details>

2. `program` 命令为什么要把"擦写算法"灌进 RAM？直接从 USB 写 Flash 寄存器不行吗？
<details><summary>参考答案</summary>Flash 编程有严格时序（解锁→擦→写→等 BSY），不是简单的"写寄存器就生效"。OpenOCD 把一段几十行 ARM 机器码的擦写算法灌进芯片 RAM，让 CPU 自己跑这段算法去操作 Flash 控制器：CPU 跑算法比 OpenOCD 从 USB 逐个寄存器写，更快也更可靠。不同芯片擦写算法不同，所以 target 配置必须选对。</details>

3. Flash 里的代码为什么推荐 `hbreak` 而非 `break`？两者硬件实现有何不同？
<details><summary>参考答案</summary>软件断点 `break` 要把目标指令改写成 BKPT：RAM 代码能改，Flash 代码改不动（写 Flash 要先擦整扇区），所以 break 在 Flash 上常失败或退回硬件断点。硬件断点 `hbreak` 用 FPB 比较器比对取指地址，命中就停，不改 Flash 内容，Flash 代码能下。代价是 FPB 只有 6 个（Cortex-M4 标配），超了报错。RAM 代码用 break（不限量），Flash 代码用 hbreak（6 个限额）。</details>

4. Semihosting 的 printf 比串口 printf 慢一个数量级，原因是什么？量产为什么要关？
<details><summary>参考答案</summary>Semihosting 的 printf 触发 BKPT 指令，CPU 停住等 OpenOCD 捕获、通过 USB 把字节送回 PC，每次输出都有几十 µs 的调试通道往返，比串口直接写 UART 寄存器慢一个数量级。量产要关是因为：没接调试器时 BKPT 指令没人捕获，直接触发 HardFault 系统挂掉。量产构建去掉 `--specs=rdimon.specs`，printf 走真实串口或彻底去掉。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| SWD/DP/AP 链路 | RM0090 调试章节；OpenOCD target 配置 |
| 擦写算法灌 RAM | OpenOCD `program` 实现；[S13 IAP](../stm32/13-flash-iap.md) 跳转函数同构 |
| GDB 十命令 | 00-blink 的 `make debug`/`make gdb`（Makefile target） |
| FPB 6 个比较器 | Cortex-M4 TRM / RM0090 调试章节 |
| Semihosting | OpenOCD `monitor arm semihosting enable`；对比 [S7](../stm32/07-usart.md) 串口 printf |

## 你做到了

- 烧录/调试从魔法变成一条讲得通的链路；
- GDB 十命令上手，软硬断点知道何时切换。

开场那对「超能力」现在拆开了：烧录是往 Flash 写，断点是往指令上改，窥视是读寄存器与内存，走的都是同一条两根线的链路。所谓统治一颗芯片，凭的就是这份直通内存的读写权。

<div class="achievement">
✅ 下一站：<a href="07-build-system.html">B7 构建系统</a>：手写 Makefile 已经上手，接着看 CMake/Ninja 和 ESP-IDF、RT-Thread(scons) 怎么把它规模化。
</div>
