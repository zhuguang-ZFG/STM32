# GD32 双系路线：基线、一手来源与缺口

## 范围（用户确认 2026-10-06）

- 双系并行：**G 篇 = GD32F4xx**（ARM Cortex-M4F，寄存器级对照 STM32F4）；**V 篇 = GD32VF103**（RISC-V Bumblebee 内核）。
- 先不定基准板卡，按芯片官方资料写；板卡接线节待用户指定后回填。

## 已取到的一手来源（存 `.trellis/ref/gd32/`）

| 来源 | 版本 / SHA | 文件（字节数） |
|---|---|---|
| `GigaDevice-GD32-MCU/GD32F4xx_Firmware_Library`（GitHub 官方组织） | main @ `10d02f4c8a7e1d79da8b2a9ad67b534f187ec936`（2026-10-06 拉取） | system_gd32f4xx.c 39,318 / gd32f4xx_rcu.h 94,588 / gd32f4xx.h 28,547 |
| `GigaDevice-Semiconductor/GD32VF103_Firmware_Library`（GitHub 官方组织） | master @ `7ab0521e96461b8833f2f4974cf6bdd1f80a7101`（2026-10-06 拉取） | system_gd32vf103.c 31,040 / gd32vf103_rcu.h 54,661 / gd32vf103.h 15,774 |
| `nucleisys/Bumblebee_Core_Doc` | master | Bumblebee_Core_Brief_Manual.pdf 472,730 |

## 已核实事实（含出处，写作直接引用）

1. GD32F4xx 标准外设库版本 **V3.3.3**（`gd32f4xx.h:93-96` 版本宏 MAIN/SUB1/SUB2/RC = 0x03/0x03/0x03/0x00）；芯片头文件覆盖 GD32F450、GD32F470（F450 200MHz / F470 240MHz 档位于下条坐实）。
2. `system_gd32f4xx.c:54-67`：官方系统时钟预设档含 **168M / 200M / 240M**（PLL 源可选 IRC16M 或 HXTAL 8M/25M）；当前生效默认档 = `__SYSTEM_CLOCK_200M_PLL_25M_HXTAL`——**官方 demo 默认 25MHz 晶振上 200MHz**。
3. `system_gd32vf103.c:48-57`：GD32VF103 预设档 **48M / 72M / 108M**（PLL 源 IRC8M）及 HXTAL 直供 / 24M / 36M。
4. GD32F4xx 外设库命名 **RCU**（`gd32f4xx_rcu.h`，不是 RCC）；CMSIS 内核头为标准 `core_cm4.h`——ARM 系与 STM32 同工具链（xPack GCC 可直接编译）。

## 资料缺口（写作时标注"待 UM 核验"）

- GD32F4xx / GD32VF103 **用户手册（UM）PDF 未取到**（gigadevice.com 可达性未测）；RCU_CFG0 位域编码、Flash 等待周期表、向量表布局在拿到 UM 前以官方库头文件+源码为准。
- RISC-V 工具链本机缺失：`riscv-none-elf-gcc` 未安装——V 篇工程构建是前置任务（建议 xPack riscv-none-elf-gcc，与现有 xPack ARM 工具链同管理器）。
- Bumblebee 手册 PDF 在手未读：CLIC 中断模型、MTIME 参数、性能计数器待提取。
- GD32F4xx 与 STM32F4 的具体外设差异点清单（USART 增强、USBHS、EXMC 等）需从库头文件 `gd32f4xx_*.h` 逐一比对后成文，禁凭印象。

## 路线设计原则

- G 篇与 S 篇同构对照：每章开头给"同名不同姓"对照表（RCC↔RCU、168↔200/240MHz），动画复用现有骨架换数字与配色。
- V 篇讲迁移：从 ARM 知识出发量 RISC-V——启动文件/链接脚本/CLIC/MTIME 四件事，不重复讲已会的 C 与外设概念。
- 事实纪律沿用主站规范：数值双来源，章节 title 与 H1 一致，动画 `![](/anim/x.svg)` 引用。

## 实施期补记（2026-10-06，G1 成稿）

新增一手来源：
- `gd32f4xx_pmu.h`（11,675B）/ `gd32f4xx_fmc.h`（27,907B 头 + 33,902B 源）/ `gd32f4xx_gpio.h`（28,758B）/ `Examples/RCU/Ckout_pin_clock_output/main.c`（5,919B），均 @ `10d02f4`。

G1 成稿坐实的事实（行号 = 上述文件）：
- RCU_CTL 0x00 / RCU_PLL 0x04 / RCU_CFG0 0x08 / AHB1EN 0x30 / APB1EN 0x40（gd32f4xx_rcu.h:44-56）；
- 官方 200M 档 PLL 参数与全序列：HXTALEN+STB（超时！失败 while(1)）→ PMUEN → LDOVS → AHB/1 APB2/2 APB1/4 → RCU_PLL=PSC25|N400<<6|((P>>1)-1)<<16|HXTAL|Q9<<24 → PLLEN+PLLSTB → HDEN 等 HDRF → HDS 等 HDSRF → SCS=PLLP 等 SCSS（system_gd32f4xx.c:936-1003）；
- **官方 system 文件不设 FMC 等待周期**（全文检索无 FMC_WS 写入；CKOUT 示例同样不设）——FMC_WS 是应用责任，WSCNT[3:0] 0~11 档（gd32f4xx_fmc.h:150-161）；
- PMU 挂 APB1（RCU_APB1EN bit28）；LDOVS[14:15]、HDEN[16]、HDS[17]，回执 HDRF[16]/HDSRF[17]（gd32f4xx_pmu.h:59-73）——与 STM32F4 无 VOSRDY 相反；
- CK_OUT0：PA8 AF0（example_ckout_main.c:135），源 IRC16M/LXTAL/HXTAL/PLLP，分频 /1~/5 含 /3 /5（rcu.h:886-901）；PC9 = CK_OUT1；
- AHB 预分频无 /32 档（编码 12 直接 = /64，rcu.h:822-833）——与 STM32 同款怪癖；
- GPIO：CTL 0x00（2bit/脚）、OCTL 0x14、BOP 0x18、AFSEL0 0x20（0-7）、AFSEL1 0x24（8-15）（gpio.h:52-61）；
- 基准：GD32F450ZG 1MB Flash / 256KB SRAM 口径为产品选型表，**待 UM 核验**；FMC 等待对照表**待 UM 核验**（工程以 FMC_WS_VALUE=6 保守超配并已标注）。
- IRQn 0..81（82 个外设向量，FPU_IRQn=81，gd32f4xx.h:279-284）。

## 实施期补记（2026-10-06，勘误批次）

1. **FMC 等待官方留白升级为全库证据**：浅克隆官方库（`git clone --depth 1` → 3295 文件）后全量检索 `fmc_wscnt_set` / `FMC_WS`，Examples/ 树**零命中**——官方示例从不设置 Flash 等待。原因（硬件自适应 or 示例跑低频）待 UM/上板核验，页面上明确标"不猜"。
   工具教训：Windows git.exe 不认 MSYS 路径 `/d/tmp/...`，会写到 `D:\d\tmp\...`（与 curl -o 同类）；克隆命令须用 `D:/tmp/...` 或先 cd。
2. **MCO1/CK_OUT0 编码两面坐实**（写章节时曾误称"STM32 是 2 的幂"）：
   - ST HAL 头 `stm32f4xx_hal_rcc.h:314-318` @1f6451c：`RCC_MCODIV_1..5 = 0/4/5/6/7` → 0xx=不分频、100=/2、101=/3、110=/4、111=/5；
   - GD32 `rcu.h:897-901` 同款 /1~/5，编码相同。**两边一致**，/4 编码均为 6。
   - 发现并修复 S2 工程真 bug：`code/stm32/01-rcc-clock/main.c` 原以 `div-1` 编码，/4 写成 3（0b011）→ 落入"不分频"区，PA8 实为 168MHz，S2 的 42MHz 对账不成立。已改显式映射表（1/2/3/4/5 → 0/4/5/6/7）。
3. **官方库空转 bug 坐实**：`system_gd32f4xx.c:208-210` 的 `while(0 != (RCU_CFG0 & RCU_SCSS_IRC16M))` 恒假（`RCU_SCSS_IRC16M = CFG0_SCSS(0) = 0`，rcu.h:817）——一次都不等，与 S2 中 HAL 轮询 SWS（hal_rcc.c:681）形成对照，已写入 G1 章节。
4. **G1 工程回读改造**：`clock_tree_readback()` 改为按 SCSS 解码实际源 + 按 RCU_PLL 参数重算频率；此前三个故障分支传 `HXTAL_VALUE_HZ` 而 SCS 从未切 HXTAL，属确定性报假账（已修，全部调用点无参）。
