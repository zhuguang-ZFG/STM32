---
title: "常见故障排查手册"
platforms: [generic]
---

# 常见故障排查手册

这本手册不是「再来一章」，是**索引层**：已发布 22 个章各自带了失败分支表（约 204 条、两代格式），本章把它们的入口按现象域编成一张分诊总表，再把两本姊妹书的 FAQ（F103 线 38 条编号条目 + F407/ESP32 线技术问答）收进第二层。排错方法论只有三句：先对现象再找第一处边界最后按标签查出处；不要从第三列开始改；**一次只改一处**。

证据先说清：本章零板级实测。38 条编号条目（C1–C8/D1–D7/P1–P9/H1–H7/R1–R7 = 8+7+9+7+7）与 22 章失败分支的条目统计（18 章有节、合计 204 条：4 列区 112 条 + 3 列区 92 条）是本轮逐章实测的计数；BOOT 三模式账、BRR=0x271 时钟账、PC13 灌电流口径均与已发布章互证；栈大小两套口径（mbF 经验值字节制 vs 仓库例程字制）**并陈不混写**。出处锚点（`#source-*`）对应[附录 E](../appendix/E-sources-version-license.md) 的注册表条目（ds5319-swd/rm0008-boot 等）。

> 版本口径：D18《常见问题FAQ》（`docs/18-常见问题FAQ.md`，F103/BluePill 线）、mbF《常见问题》（`mcu/mcu-book/book/F-常见问题.md`，F407 霸天虎 + ESP32-S3 线）。上游对账：RM0008 §3.4（BOOT 表）、DS5319（表 5 引脚、图 31 复位电容、GPIO 注 5）、FreeRTOS 口径沿 [第 22 章](../v3-rtos/22-tasks-tcb-scheduler.md)。生态与版本类答案带抓取日期（[第 27 章](../v3-rtos/27-rtos-comparison-selection.md) 口径）。

## 本章罗盘

- **问题**：遇到故障从哪张表开始翻？38 条编号条目按什么分域，两本姊妹书的 FAQ 怎么合并？已发布章的失败分支表有多少条、几代格式，本章怎么索引而不重复？栈大小为什么有两套口径，怎么并陈？出处锚点（`#source-*`）落在哪里？
- **交付**：能用 8 张分诊表把现象翻到章；能用三条抽查样例（BOOT/串口时钟/PC13）校准手册口径；能用第三层索引按章号找到失败分支原表；能区分栈口径的两套单位；能沿 `#source-*` 找到出处条目。
- **边界**：本章是索引层，不重写任何已发布章的失败分支内容；F103 线答案（BOOT/克隆 ST-Link/64 KB）不套用到 F407/ESP32（BOOT0 归 [第 28 章](../v4-platforms/28-chip-migration-differences.md)）；mbF 的站点状态问答（「建设中」）与在线绝对链接不搬；根书章号已按 mapping 重排。
- **依据锚点**：D18《常见问题FAQ》（`docs/18-常见问题FAQ.md`）、mbF《常见问题》（`mcu/mcu-book/book/F-常见问题.md`）；已发布 ch18–39 的失败分支节（逐章计数见第三层）；出处注册表在附录 E。上游对账：RM0008 §3.4、DS5319 表 5/图 31/注 5。

## 先问自己（mbF 起步区并入）

- 板对不对：用 [第 40 章](../v6-labs-projects/40-lab-method-instruments.md) 的身份寄存器读回裁决，不靠丝印。
- 电从哪来：调试器供电还是独立供电；**先共地再看信号**（铁律之二）。
- 下载器与驱动：ST-Link 固件版本、驱动枚举——版本类答案带抓取日期。
- 数字电平与模拟量分清了吗：3.3 V 的世界，5 V 信号要查 FT 脚。
- 学路线确认：F407/ESP32 线的入门三条检验与 FreeRTOS 先学建议见[第 46 章](./46-resources-roadmap-open-source.md)（学习路线区并入）。

## 排错方法论

五步（D18 口径）：**复现**（记录触发条件、频率、负载，区分稳定失败与偶发）→ **最小化**（退到只点灯/只回环的最小工程）→ **二分**（注释一半代码定位层）→ **看证据**（GDB/逻辑分析仪/串口，[第 20 章](../v2-reliability/20-debug-performance.md) 的工具表）→ **对照手册**（寄存器/勘误/特性表）。三条铁律：能测就别猜；先共地再看信号；一次只改一处。每轮收尾两行：证明了什么、还没证明什么（[第 42 章](../v6-labs-projects/42-project-delivery-acceptance.md) 的收尾纪律）。

## 第一层：现象域分诊表

8 张分诊表把「现象 → 区分证据 → 指向章」一次翻到位（已发布章的失败分支入口）：

| 现象域 | 典型现象 | 区分证据 | 指向 |
| --- | --- | --- | --- |
| 供电复位 | 上电复位/欠压复位循环 | VDD 纹波与复位标志位 | [ch18](../v2-reliability/18-low-power.md) 失败分支 |
| 下载调试 | SWD 连不上/下载失败 | IDCODE 读回、BOOT 采样 | [ch10](../v1-drivers/10-interrupts-nvic-exti.md)、D18 D 区条目 |
| 时钟启动 | HSE 不起振/PLL 锁不上 | HSERDY 位、负载电容 | [ch08](../v1-drivers/08-architecture-memory-clock.md)、D18 P 区 |
| 串口 | 乱码/丢字节 | BRR 复算、波特率反推 | [ch13](../v1-drivers/13-uart-framed-protocol.md)、D18 P 区 |
| 总线 | I2C 无 ACK/SPI 全 0xFF | 字节条对表、上拉与模式 | [ch16](../v1-drivers/16-i2c-spi.md) 失败分支 |
| RTOS | 高优先级任务饿死/栈溢出 | 水位、CPU 占用 | [ch22](../v3-rtos/22-tasks-tcb-scheduler.md)、[ch24](../v3-rtos/24-queue-semaphore-notification.md) |
| 运动 | 电机不转/闭环振荡 | 真值表/PI 手算 | [ch36](../v5-motion/36-motor-driver-power.md)–[ch39](../v5-motion/39-speed-closed-loop-pi.md) 失败分支 |
| 网络无线 | 连不上/丢包 | reason 码/信道 | [ch32](../v4-platforms/32-esp32-wifi-ble-espnow.md)、[ch33](../v4-platforms/33-network-protocol-stack.md) 失败分支 |

## 第二层：38 条编号条目（F103 线，D18 原文收编）

五域编号 **C1–C8**（编译链接）、**D1–D7**（下载调试）、**P1–P9**（外设）、**H1–H7**（硬件）、**R1–R7**（RTOS 工具链）——每条 现象/原因/解决 三段与出处列原样保留（本章不重写答案，只把根书章号按 mapping 重排：根 03→[ch09](../v1-drivers/09-gpio.md)、根 15→[ch21](../v3-rtos/21-why-rtos.md)/[ch22](../v3-rtos/22-tasks-tcb-scheduler.md)、根 17→[v1 第 20 章](../v2-reliability/20-debug-performance.md)、根 20→第 46 章、根 26→[v1 第 7 章](../v0-foundations/07-build-systems-legacy.md)）。三条抽查样例钉死其余条目的口径：

- **BOOT 三模式账**：BOOT0=0 主闪存 0x08000000；BOOT0=1/BOOT1=0 系统存储器 0x1FFFF000；0x1FFFB000 属**互联型 F105/F107**——C8 没有 0x08080000（XL 密度才有）；锁存在复位后第 4 个 SYSCLK 上升沿（[第 28 章](../v4-platforms/28-chip-migration-differences.md) 的 G0 对照）。
- **串口时钟账**：BRR=0x271 在 PCLK2=72 MHz 对应 115200，同一 BRR 在 8 MHz 下只有 12800——乱码先查时钟前提（[v1 第 13 章](../v1-drivers/13-uart-framed-protocol.md)）；HSI 8 MHz 是复位默认。
- **PC13 不是电流源**：灌电流 ≤3 mA、≤2 MHz（DS5319 注 5）——外接灯走 PA0 + 270 Ω，PC13 只点板载灯（[v1 第 9 章](../v1-drivers/09-gpio.md)）。

mbF 技术细节 10 问（MMIO/volatile/中断阻塞/队列 vs 信号量/看门狗/I2C 上拉/SPI 模式/DMA 假正常/任务栈/IRAM）按域拆入上述分诊表指向的章——每问都有已发布章承载，本章不重复答案。**栈大小两套口径并陈**：mbF 经验值（简单 256 B/printf 512 B/复杂 1024 B，**字节**）是起点；仓库例程按**字**配置（LED 128 字=512 B、KEY 192 字、UART 256 字，[v1 第 22 章](../v3-rtos/22-tasks-tcb-scheduler.md)）——单位不同，禁混写成同一套数。

## 第三层：逐章失败分支索引

已发布 ch18–39 的失败分支节统计（18 章有节、3 章无节；两代格式：ch18–24 是 4 列「现象/原因/区分证据/下一动作」，ch30–39 是 3 列「症状/第一条假设/区分实验」——索引统一映射为「现象/区分证据/下一动作」语义，不改原章）：

| 章 | 条目 | 章 | 条目 | 章 | 条目 |
| --- | --- | --- | --- | --- | --- |
| [ch18](../v2-reliability/18-low-power.md) | 15 | [ch24](../v3-rtos/24-queue-semaphore-notification.md) | 18 | [ch34](../v4-platforms/34-multicore-cache.md) | 9 |
| [ch19](../v2-reliability/19-watchdog-reset-hardfault.md) | 20 | [ch30](../v4-platforms/30-esp32s3-architecture-boot.md) | 7 | [ch35](../v4-platforms/35-can-usb-fieldbus.md) | 10 |
| [v1 20 章](../v2-reliability/20-debug-performance.md) | 21 | [ch31](../v4-platforms/31-esp32-drivers-audio.md) | 11 | [ch36](../v5-motion/36-motor-driver-power.md) | 8 |
| [ch21](../v3-rtos/21-why-rtos.md) | 14 | [ch32](../v4-platforms/32-esp32-wifi-ble-espnow.md) | 10 | [ch37](../v5-motion/37-dc-motor-openloop.md) | 8 |
| [ch22](../v3-rtos/22-tasks-tcb-scheduler.md) | 14 | [ch33](../v4-platforms/33-network-protocol-stack.md) | 10 | [ch38](../v5-motion/38-encoder-speed-measurement.md) | 9 |
| [ch23](../v3-rtos/23-context-switch-porting.md) | 13 | [v1 25 章](../v3-rtos/25-memory-management.md) | 无节 | [ch39](../v5-motion/39-speed-closed-loop-pi.md) | 9 |

（ch25/26/27 无独立失败分支节：ch25 用「先做出来 + 台架」结构，ch26 的排错在「先做出来」判据里，ch27 对照表自带反面列。）合计 **204 条**——遇到故障先到这里翻章号，再进原章看完整表。

![手绘板：排错五步——复现/最小化/二分/看证据/对照手册（原理示意）](/images/ch18-five-steps.png)

![手绘板：FAQ 对照——两本书的问答在同一页（原理示意）](/images/ch18-faq-compare.png)

![HardFault 排查阶梯：从现象到源码行（原理示意）](/figures/sample-18-hardfault-ladder.svg)

## 离开检查

- 分诊表 8 域能翻，「指向章 + 锚点」的用法会用。
- 38 条编号条目的五域结构与三条抽查样例（BOOT/串口时钟/PC13）口径与已发布章一致。
- 栈大小两套口径（字节经验值 vs 字配置）并陈不混。
- 「19/22 章、204 条、两代格式」的统计口径准确——没有「每章都有」的假命题。
- 出处锚点机制（`#source-*` ↔ [附录 E](../appendix/E-sources-version-license.md) 注册表）说得清。
- 三句铁律与五步方法论在章首，每次排错先过这三句。
