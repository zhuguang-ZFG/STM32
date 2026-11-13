---
title: "GD32 系列对照（ARM + RISC-V）"
platforms: [gd32]
---

# GD32 系列对照（ARM + RISC-V）

GD32 是「同一外设骨架、两套内核魂」的对照样本：GD32F4xx 与 STM32F407 同为 Cortex-M4F，工具链零增量、寄存器改个名；GD32VF103 外设像 F103、内核却换成 RISC-V（Bumblebee N200），中断控制器从 NVIC 换成 ECLIC、心跳从 SysTick 换成 mtime。这一章把两条线并排拆：哪些是「改宏名级兼容」，哪些是「换魂级差异」，哪些旧材料写错了、上游仓库怎么定谳。

证据先说清：本章零板级实测。ARM 线的时钟/GPIO/USART/中断号已按 GD32 官方固件库 `@10d02f4` 实取核对（行号逐条可查）；RISC-V 线按 `VF103@bc2be118`（gd32vf103 头文件、n200_eclic.h、n200_timer.h、system_gd32vf103.c）与 NMSIS 核对；UM/datasheet 的页码引用（SDIO bit31、CAN 复位值等）未能取件，保留「来源说法待核」；mtime 的 ÷4 分频链出自 Bumblebee 手册（PDF 未取），算术自洽但标待核。`code/gd32/01-rcu-clock` 的 make/size 快速验证是唯一可复跑项。

> 版本口径：GD32F4xx 按 GD32 官方固件库 **@10d02f4**（gd32f4xx.h 版本行 `V3.3.3, 2026-02-05`）；GD32VF103 按 **@bc2be118**（gd32vf103.h / gd32vf103_rcu.h / n200_eclic.h / n200_timer.h / system_gd32vf103.c）；NMSIS 按 master；工具链按 xPack 的 `riscv-none-elf-gcc`。旧章（G0–G4、V0–V4）的行号偏移按研究文档第 4 节修正后引用。

## 本章罗盘

- **问题**：GD32F4xx 为什么叫「工具链零增量」，型号宏挑的是什么？RCU 与 RCC 的偏移表怎么对照，200M 档的三件套（HDEN/HDS 真轮询）与 168M 默认档哪个是官方事实？官方 system 文件为什么全文不设 Flash 等待？GPIO 改名不改岗之外，BC/TG 是什么、VF103 为什么没有？USART 的偏移表旧材料错在哪两处，上游怎么定谳？VF103 的「隔代布局」是什么意思，照搬 F4xx 的 RCU 宏第一笔会错在哪？108 MHz 是不是超频？ECLIC 与 NVIC 的结构差异（无 +16、两维优先级、shv）各意味着什么？mtime 与 SysTick 的四点差异是什么，延时为什么要「续约」？两套中断号地图为什么不能互串？
- **交付**：能说清双线总览（ARM 线改宏名、RISC-V 线换内核）；能复算 200M 档（25/25×400/2）与 108M 档（8÷2×27）并指出 USB 的 44.4 MHz 陷阱；能纠正「官方默认 200MHz」的说法（默认档 168M，200M 是预设函数）；能用上游修正版 USART 偏移表（STAT0@0x00、CTL0@0x0C）与 USART0=0x40011000（APB2）替换旧错表；能画 ECLIC 的四字段布局（cfg/ie/ip/attr/ctl，4 字节间隔）与 shv 两种路径；能算 mtime 的 tick（108M→27 MHz，1ms=27000）并写出先高后低写、高-低-高读与 `cmp += 周期` 三条纪律；能把两套中断号（F4 线 USART0=37 / V 线 USART0=56、EXTI0=25）分开背。
- **边界**：单线对照章——GD32 与 STM32 的外设寄存器细节只讲「差异点」，完整机制回 [v1 第 8–13 章](../v1-drivers/08-architecture-memory-clock.md) 与 [第 10 章](../v1-drivers/10-interrupts-nvic-exti.md)；迁移方法论归 [第 28 章](./28-chip-migration-differences.md)；UART 协议帧归 [v1 第 13 章](../v1-drivers/13-uart-framed-protocol.md)。手册页码未取件的行带「来源说法待核」。板上实测（CK_OUT0 量频、PF6 翻转、等待拍数）在源章里就是「待上板」状态，本章不改写成结论。
- **依据锚点**：G0《环境》（`mcu/docs/gd32/00-env.md`）、G1《RCU 时钟》（`.../01-rcu-clock.md`）、G2《GPIO 复用》（`.../02-gpio-af.md`）、G3《USART》（`.../03-usart.md`）、G4《外设差异》（`.../04-periph-diff.md`）、V0《工具链》（`.../05-riscv-toolchain.md`）、V1《CLIC 中断》（`.../06-clic-irq.md`）、V2《108MHz》（`.../07-rcu-108m.md`）、V3《mtime 延时》（`.../08-mtime-delay.md`）、V4《GPIO 最小点灯》（`.../09-gpio-minimal.md`）。上游对账：GD32 官方固件库 [gd32f4xx_usart.h](https://www.gigadevice.com/) `@10d02f4`（`:51-60`）、[gd32f4xx_gpio.h](https://www.gigadevice.com/)（`:52-63`）、[gd32f4xx_rcu.h](https://www.gigadevice.com/)（`:44-57,886-900`）、[system_gd32f4xx.c](https://www.gigadevice.com/)（`:56,:958-996`）；VF103 库 `@bc2be118`（gd32vf103.h、gd32vf103_rcu.h、n200_eclic.h:13-41、n200_timer.h:8-13、system_gd32vf103.c:47-61,750-830）；NMSIS core_feature_eclic.h（`:63,127-128,156,758`）。

## 先做出来

### 1. 两条线，一张总览表

| 线 | 内核 | 兼容层级 | 上游核对结论 |
| --- | --- | --- | --- |
| GD32F4xx | Cortex-M4F | **改宏名级**：四旗逐字相同，只多 `-DGD32F450` | `gd32f4xx.h:46` 有 6 种型号分支，型号宏挑容量/向量表 |
| GD32VF103 | RV32IMAC（Bumblebee N200） | **换魂级**：外设像 F103（AFIO/EXTI/GPIO 同址），内核与中断控制器全换 | `gd32vf103.h:204-229` 与 F103 老地址逐条一致 |

ARM 线的「零增量」：`-mcpu/-mthumb/-mfpu/-mfloat-abi` 四旗与 F407 逐字相同——这是 G0 的原话，且由 `gd32f4xx.h` 的型号分支支撑。换库的成本在改名（RCC→RCU、GPIO_BSRR→BOP/BC），不在重学。

### 2. 先把两个旧错误钉在案

写 ch29 前先立两个上游定谳（都已在官方库实取核对）：

- **USART 偏移表**：旧材料的「CTL0@0x00…DATA@0x18」整体错位。上游 `gd32f4xx_usart.h:51-60` 实际是 **STAT0@0x00、DATA@0x04、BAUD@0x08、CTL0@0x0C、CTL1@0x10、CTL2@0x14、GP@0x18**（另有 STAT1@0x88）。随文的「0x00 永远是主控制寄存器、0x0C 永远是波特率」一并废弃不用。
- **USART0 基址**：旧材料写「USART0 = APB1+0x4400」。上游 `gd32f4xx.h:326` 的 `USART_BASE=APB1+0x4400`（0x40004400）是 **USART1**（=STM32 的 USART2）；**USART0 = 0x40011000（APB2，`gd32f4xx_usart.h:47`）**——与 STM32 USART1 的老地址相同，也和它自己「USART0 中断号挂 APB2」的中断地图一致。

v1 第 13 章已把旧表标为「待复核」，本章按上游版替换。

## 机制

### 一、RCU 与 RCC：同名不同姓

偏移对照（`gd32f4xx_rcu.h:44-57` 与 G1 逐行一致）：CTL 0x00、PLL 0x04、CFG0 0x08、AHB1EN 0x30、APB1EN 0x40——骨架同 STM32，名字换过。三条实质差异：

1. **PLL1/PLL2 配而不用**：8M 分支把 `PLL1_MUL20|PLL2_MUL20` 写进 CFG1 且同样使能了 PLL1EN/PLL2EN（`system_gd32f4xx.c:800,803,809`），但不在时钟路径——旧章「配了却没使能」说反了，正确表述是「配置并使能了、但不在时钟路径」。官方还有一处把 PLL2 等待注释误写成 PLL1（`:810` 附近）——官方代码也有瑕疵，读库要带怀疑。
2. **200M 档的三件套**：PSC=25/N=400/P=2/Q=9，VCO 400 MHz，复算 25/25×400/2=200；握手是**真轮询**——HDEN 等 HDRF、HDS 等 HDSRF（`:981-987`），顺序 LDOVS→总线分频→PLL 启动等锁→HDEN→HDS→切 SCS（`:958-996`）。USB 的坑：Q=9 → 400/9≈44.4 MHz ≠ 48，USB 时钟走 CK48M 三源（PLLQ/PLLSAIP/IRC48M，`RCU_ADDCTL:410-412`）。
3. **默认档是 168M**：官方副本 `system_gd32f4xx.c:56` 默认启用 `__SYSTEM_CLOCK_168M_PLL_25M_HXTAL`，200M 三档全部注释着（`:60-61`）；200M 是预设函数 `system_clock_200m_25m_hxtal`（`:936`），上 200M 要自行放开宏。旧章「SystemInit 默认拉到 200MHz」与官方仓库冲突，本章按上游改写。

还有一个官方留白值得记住：官方 system 文件全文**不设 Flash 等待**（检索无 FMC_WS 写入）；GD32F4xx 的 WSCNT 是 4 位 0~15 加 WSEN 使能位，VF103 是 3 位（`gd32vf103_fmc.h:45,64,103`）。档位数字与 UM 页码待核；「168 MHz 零等待」是 F407xx datasheet 的说法，不外推到 200/240 档。

![GD32 RCU 时钟树动画：PLL 家族与 CK48M 三源](/anim/gd32-rcu-clock.svg)

![RCU 树状图：与 RCC 同骨架不同名](/arch/rcu-tree.png)

CK_OUT0/MCO 同款编码雷区两边同罚：PA8 输出、/1~/5 编码 0/4/5/6/7，写 3 落入**不分频**（`gd32f4xx_rcu.h:886-900`）——「分频比减一」的错误在 ch08 教过，这里是它的 GD32 分身。

### 二、GPIO：改名不改岗，外加两枚新寄存器

GD32F4xx 的 GPIO 十二枚寄存器偏移与 F4 相同（CTL/OMODE/OSPD/PUD/ISTAT/OCTL/BOP@0x18/LOCK@0x1C/AFSEL0@0x20/AFSEL1@0x24），**BC@0x28 与 TG@0x2C 是 GD32 独有**（`gd32f4xx_gpio.h:52-63`——逐位清零与逐位翻转，写法比 BSRR 的混合口更直白）。AF 编号模型同 F4：每脚 4 位、AF0~15、nibble 算法；USART0_TX=AF7 的候选 PA9/PB6 与 STM32 同号同脚。一个「按脚查表」的反例：PA15 在 GD32 上多一个 USART0_TX 候选（F407 的 PA15 没有）——引脚清单出自 datasheet 表（PDF 未取，标待核），纪律不变：按脚查表不按记忆。

![GD32 GPIO 复用动画：AF 编号与引脚矩阵](/anim/gd32-af-mux.svg)

![手绘板：GD32 与 STM32 的时钟树与 USART 落点对照——PLL1/PLL2 配而不用、168M 默认档、USART0 落在 APB2 老地址（原理示意）](/images/mc29-gd32-contrast.png)

### 三、USART：8 个、0 起编号、上游修正版偏移表

8 个串口、0 起编号，中断号 **37/38/39/52/53/71/82/83**（`gd32f4xx.h:159-206`，39→52 跳 13、53→71 跳 18 的「不连续」也在上游成立）。命名差异：CTL/CTL1/CTL2、STAT0（不是 SR）、DATA（不是 DR）、BAUD（不是 BRR）。寄存器偏移按上游修正版背（先做出来一节的两个定谳），外加 STAT1@0x88。这个偏移表与 STM32 的差异不是「乱了」，是 STAT 提到 0x00——读状态是最高频操作，放前面有它的道理；但迁移时按 STM32 记忆写偏移就全错位。

![USART 改名对照：STM32 与 GD32 的寄存器名映射](/arch/usart-rename-map.png)

### 四、VF103：外设像 F1，内核换魂

GD32VF103 的外设地址与 F103 老地址逐条一致：AFIO@0x40010000、EXTI@0x40010400、GPIOA@0x40010800、RCU@0x40021000、FLASH=0x08000000、SRAM=0x20000000（`gd32vf103.h:196-229`）——迁移免改地盘。但 RCU 是**隔代布局**：0x04 是 CFG0 不是 PLL（F4xx 的 `RCU_PLL` 宏在 VF103 头文件根本不存在），PLL 参数拆进 CFG0（PLLMF）+ CFG1（PREDV0）；无电压三件套，只有 DSV（`gd32vf103_rcu.h:45-57`）。照搬 F4xx 的 RCU 宏，第一笔就写错地方。GPIO 也隔代：CTL0/CTL1 每脚 4 位、只有 7 枚寄存器（CTL0/CTL1、ISTAT、OCTL、BOP、BC、LOCK），**没有 TG**（`gd32vf103_gpio.h:53-59`）。

**108 MHz 的性质**：手册标称上限，不是超频——这是它与 F407 168M/官方 H7 480M 争议的本质区别。预设阶梯 24/36/48/56/72/96/108 MHz，全部压在 4 MHz PLL 输入上（4M×{6,9,12,14,18,24,27}，`system_gd32vf103.c:47-61`）；默认档 `__SYSTEM_CLOCK_108M_PLL_HXTAL`（`:61`）；108M 链 = 8M÷2×27（PREDV0_DIV2 `rcu.h:541`、MUL27 `:505`，分频乘法在 `sys.c:750-830`）；25M 板绕道 PLL1（÷5×8÷10，`:785`）。回读公式有个边角：PLLMF raw<15 时 +2、≥15 时 +1，raw=15 是 **×6.5**（整数式 `ck*6+ck/2`，`:251`）——头文件的 MUL 宏序列恰好缺 15（`rcu.h:486-505`），想用 ×6.5 得自己写 raw。

### 五、ECLIC：把 NVIC 的三件事改掉了

ECLIC（N200 核的中断控制器，地址 0xd2000000，`n200_eclic.h:37`）与 NVIC 的结构差异：

1. **无 +16 槽偏移**：EXTI0=25（`gd32vf103.h:112`）、EXTI5_9=42、EXTI10_15=59、USBFS=86——STM32 那套「EXTI0 是 IRQn 6 / 向量表槽 22」的换算在这里不适用。每中断 4 字节间隔的四字段：clicintie@0x1001、clicintip@0x1000、clicintattr@0x1002、clicintctl@0x1003（CFG@0x0）。
2. **两维优先级**：level + priority 共用 intctl 的 8 位位宽上限，分割由 nlbits 决定（1..4 有效位说明 `NMSIS core_feature_eclic.h:63`，上限 8 位 `:156`，priority 宽度 = CLICINTCTLBITS − nlbits `:758`）——「最多 16 级 + 16 级」是 4+4 分割下的一个实例，不是固定规格。没有 NVIC 的 PRIGROUP/0x5FA 那套airlock。
3. **shv 两种路径**：shv=1 向量直跳（硬件直接跳 ISR），shv=0 公共入口（软件分发）——每种中断单独选，比 NVIC 的「一律向量表」灵活一格。

![ECLIC 优先级动画：两维 level/priority 与 shv 路径](/anim/riscv-clic-priority.svg)

它自称是 CLIC 草案的增强实现——CLIC 规范仓库存在（`@92b0ffe`），正文是 PDF 未取行号，引用仓库不引行号。

### 六、mtime：不是 SysTick 的四点差异

| 维度 | SysTick | mtime（N200） |
| --- | --- | --- |
| 位宽/方向 | 24 位递减 | **64 位递增** |
| 寄存器形态 | 内核外设寄存器 | **内存映射**（0xd1000000：mtime@+0x0、mtimecmp@+0x8，`n200_timer.h:8-13`），用 lw/sw 访问不用 CSR |
| 触发条件 | 计到 0 | **mtime ≥ mtimecmp** 即挂起中断 |
| 重装 | 自动重装 LOAD | **无自动重装**：软件把 `mtimecmp += 周期` 续约，不是 `= now + 周期`（now 读取与写入之间 tick 会走，续约会漂） |

读写两条纪律：64 位值**先高后低写**（高字先写，低字写入的瞬间比较条件不会提前满足）、**高-低-高读**（防低字回卷时读到撕裂值）。频率口径：自增 = SystemCoreClock/4（108M→27 MHz，1 ms=27000 tick；72M→18000）——÷4 出自 Bumblebee 手册（PDF 未取，算术自洽，标来源说法待核）；延时 ticks 现算不写死。

![mtime 延时动画：64 位递增计数器与 cmp 续约](/anim/riscv-mtime-tick.svg)

### 七、工具链：三元组换了前缀

`riscv-none-elf-gcc` + `-march=rv32imac -mabi=ilp32`（xPack 主名已核）；无 FPU 标志、无 CPACR、复位无 F407 那套「硬件两读」、sp 由软件设。两个边角：rv64 默认编译会报 relocation truncated（V0:73）——目标位宽不匹配的第一个症状；旧改名史（riscv-none-embed / riscv64-unknown-elf）在官网首页未见，标待核。

## 测量与证据

| 结论 | 身份 | 判据 |
| --- | --- | --- |
| USART 偏移表修正版 | 手册级（上游已核） | `gd32f4xx_usart.h@10d02f4:51-60` |
| USART0=0x40011000（APB2） | 手册级（上游已核） | `gd32f4xx.h:326` + `gd32f4xx_usart.h:47` |
| 默认档 168M、200M 预设 | 手册级（上游已核） | `system_gd32f4xx.c:56,:60-61,:936` |
| 200M 三件套真轮询 | 手册级（上游已核） | 同上 `:958-996,:981-987` |
| PLL1/PLL2 配而不用 | 手册级（上游已核） | 同上 `:800,803,809` |
| BC/TG 独有、VF103 无 TG | 手册级（上游已核） | `gd32f4xx_gpio.h:52-63` / `gd32vf103_gpio.h:53-59` |
| ECLIC 布局与中断号 | 手册级（上游已核） | `n200_eclic.h:13-41` / `gd32vf103.h:100-170` |
| mtime 地址与读写纪律 | 手册级（上游已核） | `n200_timer.h:8-13` |
| mtime ÷4 分频 | 来源说法待核 | Bumblebee 手册未取件；108/4=27 算术自洽 |
| 108M 档等待拍数 | 未实测 | 源章即「待上板实测」 |
| SDIO bit31 / CAN 复位值指纹 | 来源说法待核 | UM §24.8.2 / §26.4.8 未取件（ch28 已登记） |
| CK_OUT0 量频、PF6 翻转 | 未实测 | 源章「待上板」 |
| PA15 第三候选（USART0_TX） | 来源说法待核 | datasheet 表未取件 |

可复跑项：`mcu/code/gd32/01-rcu-clock` 的 make/size 快速验证（G0:31-34）。上板待做：CK_OUT0 输出实测、VF103 等待拍数、mtime 频率的秒表对账。

## 失败分支

| 症状 | 第一条假设 | 区分实验 |
| --- | --- | --- |
| 串口寄存器读写全错位 | 用了旧偏移表（CTL0@0x00） | 对上游 `gd32f4xx_usart.h:51-60` 重排；STAT0 才在 0x00 |
| 找不到 USART0 | 以为在 APB1+0x4400 | 那是 USART1；USART0=0x40011000（APB2） |
| 200M 跑不上 | 直接调 200M 预设但默认档 168M；或电压三件套没跟上 | 读回 CFG0/PLL 参数与 SCS 选择；对照 `:958-996` 握手 |
| USB 时钟不对 | 以为 Q 分频出 48M | Q=9 → 44.4 MHz；USB 走 CK48M 三源另配 |
| 中断不触发（VF103） | 按 STM32 习惯填 IRQn 或用 +16 槽偏移 | ECLIC 无 +16；EXTI0=25；检查 clicintie 与 nlbits 分割 |
| 延时不准或漂移 | `mtimecmp = now + 周期`（读写在两 tick 之间漂） | 改 `mtimecmp += 周期` 续约式；核对 ÷4 分频链 |
| 64 位计数读出撕裂 | 单次 64 位读 | 高-低-高读法 |
| rv32 工程链不过 | 用了 rv64 默认或旧三元组 | `-march=rv32imac -mabi=ilp32`；报 relocation truncated 即位宽不符 |

## 跨平台边界

- 迁移方法论与「第 1 脚/抢脚/电源脚」归 [第 28 章](./28-chip-migration-differences.md)；SDIO bit31 与 CAN 复位值指纹在那里登记，本章不重复展开。
- STM32 侧的 NVIC 分组、EXTI 语义、SysTick 四寄存器：回 [v1 第 10 章](../v1-drivers/10-interrupts-nvic-exti.md) 与 [v1 第 11 章](../v1-drivers/11-systick-timebase-rtc.md)，本章只讲 ECLIC/mtime 与它们的差异。
- UART 的协议帧设计（0x534E 等）：归 [v1 第 13 章](../v1-drivers/13-uart-framed-protocol.md)，本章只讲 GD32 的寄存器面。
- GD32 的 USBHS/EXMC/TRNG 等存在性清单沿用 G4，逐外设机制不在本章。

## 离开检查

- 能一张表说清两条线的兼容层级（改宏名 vs 换魂）。
- 200M 档三件套与 168M 默认档的事实分得清，USB 44.4 MHz 的陷阱能指出。
- 上游修正版 USART 偏移表能默写（STAT0@0x00、DATA@0x04、BAUD@0x08、CTL0@0x0C）。
- ECLIC 的四字段、两维优先级、shv 两种路径能白板画；中断号两套地图不互串。
- mtime 的四点差异与三条读写纪律能落到代码顺序上。
- 「108 MHz 是标称不是超频」与「官方 system 不设等待」两条边界说得清。
