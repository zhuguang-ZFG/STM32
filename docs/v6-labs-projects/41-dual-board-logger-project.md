---
title: "双板综合项目"
platforms: [f407, esp32]
---

# 双板综合项目

同一份需求（周期采样、队列缓冲、串口上报、配置可存、断线必停），在 F407 与 ESP32-S3 上各做一遍——这是本章的教学设计：**公共部分只讲一遍，平台差异用对照表**。两份来源文档刻意互镜像（骨架逐字相同、五处按平台分叉），合并后的正文按「公共架构 → 平台差分 → 故障注入」组织。这是一个真实的工程载体：SAMPLE 载荷 64 B、线上 74 B、队列载荷 1 KiB、租约 500 ms、期限监督——每个数字都可复算。

证据先说清：本章零板级实测。两份来源的 `hardware_status: pending`，「上板记录请注明板版本、固件提交、接线、输入和原始日志，本页当前仍为待实测」；故障注入四命令的表是**预期逻辑结果（非实测）**，原文自带限定；`mcu/docs/lab/reports/j1-test-report.md` 是空白模板。工程实况：`mcu/code/projects/` 目录不存在——真实载体是 `code/projects.json` 登记的 `code/stm32/07-sensor-logger`、`code/esp32/08-sensor-logger` 与 `code/common/logger`（全部在库）。

> 版本口径：F407 侧 FreeRTOS V11.1.0、复位 HSI 16 MHz（[v3-rtos](../v3-rtos/22-tasks-tcb-scheduler.md) lab 同源）；S3 侧 ESP-IDF 5.5.2（[第 30 章](../v4-platforms/30-esp32s3-architecture-boot.md) 同源）。PRJ1《F407 logger》（`mcu/docs/projects/01-f407-logger.md`）、PRJ2《S3 logger》（`.../02-s3-logger.md`）。

## 本章罗盘

- **问题**：四层架构（外设适配/公共核心/RTOS 运行层/主机）怎么分，哪些东西两板共用？SAMPLE 载荷的 64 字节怎么拆、线上为什么是 74 B，队列满为什么丢新不丢旧？期限监督和心跳差在哪，「任务活着但进度停滞」怎么检出？配置的三个状态（改 RAM/持久化/重启加载）两板各怎么落？EEPROM 双槽提交标记与 NVS 单 blob 的取舍是什么？故障注入四命令各打什么、预期什么？两板的看门狗形态差在哪？
- **交付**：能画出四层架构与两板的 port 边界；能手算 64 B 载荷、74 B 线上帧、1 KiB 载荷与 1.6 s 队列账，以及 `samples` 的 1120 B RAM；能解释期限判据（采样/通信最近一次进展距现在 <2500/<1500 ms）；能写双槽提交标记的启动挑选逻辑；能按四命令跑故障注入（构建开关先开）；能把「断电押注」实验设计出来。
- **边界**：本章讲项目组织与双板对照；FreeRTOS 队列/任务机制归 [v3-rtos](../v3-rtos/22-tasks-tcb-scheduler.md)，TWDT 归 [第 32 章](../v4-platforms/32-esp32-wifi-ble-espnow.md) 的任务级契约段与 [v1 第 19 章](../v2-reliability/19-watchdog-reset-hardfault.md) 的看门狗语义；OTA 回滚细节归 [v1 第 17 章](../v1-drivers/17-flash-iap-ota.md)；QMI8658 与音频链路归 [第 31 章](../v4-platforms/31-esp32-drivers-audio.md)。全部实验待执行。
- **依据锚点**：PRJ1、PRJ2（`mcu/docs/projects/`）；工程 `mcu/code/stm32/07-sensor-logger`、`mcu/code/esp32/08-sensor-logger`、`mcu/code/common/logger`、`mcu/code/projects.json`（实存核对）。上游对账：RM0090（DMA2 向量表与 FreeRTOS 优先级规则沿 [v3-rtos 24 章](../v3-rtos/24-queue-semaphore-notification.md) 已核口径）；AT24C02（写周期 5 ms/页 8 B，datasheet）；ESP-IDF NVS/TWDT（v5.5.2 口径）。

## 先做出来

### 1. 一份协议，先算字节账

SAMPLE 载荷（固定 64 字节，全部小端）：

```text
sequence u32 + timestamp_ms u32 + generation u32
+ sensor_type u8 + valid_mask u8 + status u16
+ raw[6] i32 + filtered[6] i32
= 4+4+4+1+1+2+24+24 = 64 字节
```

64 B 只是 payload。`protocol_encode()` 在它前面加 6 B 头（version/type/sequence/length），后面加 2 B CRC，再做 COBS 并以 `0x00` 分隔：64 B SAMPLE 上线共 **74 B**。别把 64 B 当帧长。

队列 16 槽 × 64 B 有效载荷 = **1 KiB 载荷预算**；100 ms 采样周期下缓冲 **1.6 s** 的突发。`logger.h` 里实际是 `frame_t samples[16]`，每项带 type/sequence/length 与对齐：ARM 上 `sizeof(frame_t)=70`，`sizeof(samples)=1120 B`。RAM 预算按这个数组算，不能拿 64 B 充数（[第 42 章](./42-project-delivery-acceptance.md) 的「预算先行」纪律）。

### 2. 期限判据复算

监督周期 50 ms；判据是**最近一次进展距现在**是否超过期限：采样 2500 ms、通信 1500 ms。实现只保存 `last_ms[id]`，`health_evaluate()` 比较 `now - last_ms[id] >= deadline_ms[id]`，不累计窗口内次数。启动后有 3000 ms 宽限：宽限内允许喂狗；所有必需任务都上报过，或 3000 ms 到期，宽限才结束。100 ms 周期下 2500 ms 相当于 25 个周期的跨度（2500/100=25），但这是间隔上限的换算，不是「2500 ms 内至少采 25 次」的计数承诺。「任务还活着但进度停滞」要能检出——这就是**期限监督**与心跳的分工（机制段展开）。

## 机制

### 一、四层架构与 port 边界

```text
┌─ 主机（串口终端/上位机）
├─ RTOS 运行层（任务/队列/监督/租约）
├─ 公共核心（code/common/logger：协议、配置、滤波、期限监督）
└─ 外设适配 port（code/stm32/07/logger_port.c ｜ code/esp32/08/port.c）
```

公共核心不知道底下是哪颗芯片；port 把「传感器采样、存储读写、看门狗喂狗、控制台」四个动作翻译成平台 API。换平台的成本被压进 port 一层。

![双板 logger 架构：四层与 port 边界](/images/projects/logger-architecture.svg)

### 二、平台对照表：五处分叉

| 维度 | F407 | ESP32-S3 |
| --- | --- | --- |
| 传感器输入 | 电位器 → ADC PA0 + TIM2 TRGO 触发 + DMA2 搬运 | 板载 QMI8658（I2C，GPIO1/2） |
| 采样节奏 | TIM2 TRGO 硬件触发（周期与控制环解耦） | `xTaskDelayUntil` 软件节拍 |
| 配置存储 | EEPROM AT24C02 **双槽**（2×128 B，8 B 页边界写前 127 字节，最后写提交标记，启动挑最新有效 generation） | NVS **单 blob**（128 字节配置 + commit） |
| 看门狗 | 硬件 IWDG（喂狗点在监督任务） | **TWDT**（任务级订阅 + 进展上报；S3 无外部看门狗芯片——PRJ2 健康段旧稿照抄 F407 的「硬件 watchdog 名义 2s」是错的，已按 PRJ2:83 改写） |
| 控制台 | USART1 PA9/PA10 | UART1 GPIO10/11（USB 口只做烧录与日志） |

EEPROM 双槽与 NVS 单 blob 的取舍：双槽能在断电时回退到上一份有效配置（提交标记未写完就选中旧槽）；NVS 单 blob 靠自身的事务性保证不写坏，但回退语义弱——押注实验（[第 40 章](./40-lab-method-instruments.md) 教法）在两板上各做一次断电恢复。

![F407 接线：ADC/EEPROM/USART1](/images/projects/j1-f407-wiring.svg)

![S3 接线：板载传感器与 UART1](/images/projects/j2-s3-wiring.svg)

### 三、显式过载保护：满则丢新

16 槽队列满时的策略是**丢最新、计数上报**——STATUS 帧里带丢弃计数，上位机能看到「传感器产量 > 消费能力」。调大队列之前先看 STATUS 高水位：丢弃计数为 0 就别加内存。F407 的中断账顺带核一遍：DMA2 Stream0 = IRQ56，优先级 6 ≥ `configMAX_SYSCALL_INTERRUPT_PRIORITY` 对应的数值 5（[v3-rtos 24 章](../v3-rtos/24-queue-semaphore-notification.md) 的 FromISR 规则）；USART1 用 DMA2 Stream5，不与 Stream0 共用流。

![记录器数据流：两板采样输入经 sample、滤波封装成 64 B 载荷（线上 74 B），进入 16 槽队列；队列载荷 1 KiB、samples 数组 1120 B；满则丢新并计数，主机按 sequence 缺口发现丢帧](/arch/logger-flow.png)

![队列溢出动画：满则丢新与计数上报](/anim/logger-queue-overflow.svg)

### 四、期限监督 vs 心跳

心跳只回答「任务还活着」；期限监督回答「任务在 deadline 前做完了该做的事」。PRJ 的监督任务每 50 ms 比较 `now - last_ms[id]` 与 deadline：采样 2500 ms、通信 1500 ms，超过就置 overdue 并停止喂狗（启动 3000 ms 宽限内除外）——**活着但停滞**的任务被点名。`progress()` 只刷新时间戳，不累计次数；通信任务的 `progress(1)` 在接收轮询之后、发送之前调用，表示通信循环转了一圈，**不要求这一次发送成功**——UART 没有确认，监督也不该假装有。「心跳检测不到进度停滞」的完整论证：活锁的任务在喂心跳，却没产出一个样本。喂狗点在监督任务（F407 硬件 IWDG）；S3 的 TWDT 按任务订阅，Pro 核/App 核分开配置。

### 五、配置三态与双槽提交

配置有三个状态，两板都要分清：**configure** 只改 RAM（立刻生效但不持久）；**save** 才持久化；**重启加载**的是最近一次 save 的版本——改了没 save，重启就回到旧配置（两份来源的「断电押注」段）。EEPROM 双槽的实现账：2×128 B 槽，按 8 字节页边界写前 127 字节，最后写提交标记；启动时挑「最新且有效 generation」的槽——标记没写完（断电）就选旧槽。NVS 单 blob 一次 commit 原子生效；「单 blob 最大 1984 字节」是 IDF 版本相关常量，标待核。

### 六、故障注入：四命令

| 命令 | 注入 | 预期（**逻辑结果，非实测**） |
| --- | --- | --- |
| fault 1 | 停喂狗 | watchdog 复位，重启后配置还在 |
| fault 2 | 停发 STATUS | 主机侧超时；板侧监督不受影响 |
| fault 3 | 传感器失联 1 s | 保持健康（采样失败 ≠ 任务死亡）；valid_mask 置零 |
| fault 4 | TX 暂停 2 s | 队列积压至满，丢新计数增长 |

构建开关先开（F407 `FAULTS=1`、S3 `sdkconfig.defaults.faults`），普通固件对 fault 命令返回 UNSUPPORTED。应答入队后 200 ms 执行——注入也是被协议管理的动作。所有 fault 行保持「预期逻辑结果（非实测）」限定，真板验证待执行。

### 七、协议承诺的边界

一条必须保留的边界句：**无硬件流控的 UART 不能确认对端真正接收**——发送成功 ≠ 对端收到。STATUS 应答是应用层的确认，不是传输层保证；这条决定了「上报丢帧」在协议里是常态而非异常，主机端的序号连续性检查是发现手段。

## 测量与证据

| 结论 | 身份 | 判据 |
| --- | --- | --- |
| SAMPLE 载荷 64 B 字段账 | 文档推导 | 4+4+4+1+1+2+24+24 复算 |
| 线上 74 B | 代码核对 | 64 B payload + 6 B 头 + 2 B CRC + COBS 1 B + 分隔符 1 B；`protocol_encode()` 返回 74 |
| 队列 1 KiB 载荷 / samples 1120 B | 代码核对 | 16×64 B payload；ARM ABI 下 `sizeof(frame_t)=70`、`sizeof(samples)=1120` |
| 期限判据（2500/1500/50 ms） | 代码核对 | `health.c` 比较 `now-last_ms >= deadline`；2500/100=25 个周期，不是 20 次计数 |
| F407 中断账（IRQ56、优先级 6≥5） | 手册级 | [v3-rtos 24 章](../v3-rtos/24-queue-semaphore-notification.md) 已核规则 + 向量表 |
| EEPROM 双槽/页 8 B/提交标记 | 手册级 | AT24C02 datasheet（写周期 5 ms） |
| NVS blob 1984 B 上限 | 来源说法待核 | IDF 版本相关常量 |
| 姿态换算 ±4g→8192、±512dps→64 | 来源说法待核 | 两源一致；手册灵敏度表未逐项复核 |
| 「S3 有 512 KB SRAM」 | 来源说法待核 | S3 为 512 KB SRAM + PSRAM，说法可核未核 |
| fault 四命令 | 未实测（预期逻辑结果） | 原文自带限定 |
| 断电配置恢复 | 未实测 | 两页都要求「真拔一次电」 |

## 失败分支

| 症状 | 第一条假设 | 区分实验 |
| --- | --- | --- |
| 丢弃计数持续增长 | 消费端慢于生产端 | 查通信任务期限；调 period 或缩帧 |
| 断电后配置丢失 | save 没调（只 configure）；或双槽提交标记没写完就断电 | 三态检查；押注实验重做 |
| watchdog 复位但配置丢 | 双槽启动挑选逻辑错（选了标记未完成的槽） | 读 generation 与标记位；注入 fault 1 复现 |
| S3 任务被 TWDT 点名 | 长操作没喂进展上报 | 订阅与上报点核对；区分 Pro/App 核 |
| 监督点名但任务「活着」 | `last_ms` 长期不更新（活锁） | 期限监督 vs 心跳的分工——看最近进展不看心跳 |
| 两板行为不一致 | port 层语义漂移（同函数不同义） | 对照表逐行审 port |

## 离开检查

- 四层架构与 port 边界能画；「公共只讲一遍」的正文结构能落地。
- 64 B 载荷、74 B 线上、1120 B samples、1.6 s、2500 ms 五笔账当场复算。
- 平台对照表五栏能填；「S3 无外部看门狗芯片，用的是 TWDT」不再说错。
- 双槽提交标记与 NVS 单 blob 的取舍能讲；断电押注实验能设计。
- 故障注入四命令与构建开关能落；「预期逻辑结果（非实测）」限定全程保留。
