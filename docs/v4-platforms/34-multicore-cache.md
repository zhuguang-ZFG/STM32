---
title: "多核、Cache 与内存一致性"
platforms: [esp32, f407]
---

# 多核、Cache 与内存一致性

「多核」这个词在 MCU 世界里藏着两种完全不同的形态：ESP32-S3 是 SMP——一个 FreeRTOS 内核同时管两颗 LX7；STM32H745 是 AMP——两颗核各跑一个内核，共享内存加 HSEM 交换数据。「Cache」则是另一个正交的雷：F407 根本没有 cache，H7 的 M7 带 16+16 KB，S3 靠 cache 窗口执行外部 Flash。这一章把三平台的内存模型排上同一张解剖台，把「DMA 看见的内存 ≠ CPU 看见的内存」讲成一张可执行的方向表，再把 H745 的五层双核契约从旁注展开成契约书。

证据先说清：本章零板级实测。上游核对按 **ESP-IDF v5.5.2** 实取（`soc_caps.h:140,145` 的 writeback 支持位与核数、`esp_cache.h:25-38,54-57` 的 msync 方向宏与「经典 ESP32 无 writeback」原话、`cache_ll.h:401-403,501,514`）；H7 侧按 AN4891/AN5557/RM0433 口径（cache 行 32 B、CM7@D1/CM4@D2 的核域归属、DTCM 只有 CPU/MDMA 可达）；H745 五层契约是**设计与验收协议**（D28:336 自认非实测），故障注入列是验收要求不是记录；MPU 配置写法属设计口径（仓库无 H7 MPU 实例）。

> 版本口径：ESP-IDF **v5.5.2**（行号绑定 `$IDF_PATH`，换版本重核）；H7 按 AN4891（系统架构）、AN5557（双核）、RM0433、ES0392；F407 口径沿 [v1 第 14 章](../v1-drivers/14-dma.md) 与 RM0090。中断分配、`esp_intr_alloc`、`portMUX`、`volatile` 边界的机制本体已在 [v1 第 10 章](../v1-drivers/10-interrupts-nvic-exti.md) 冻结，本章只回链。

## 本章罗盘

- **问题**：三平台的 cache 有无与取指路径差在哪，为什么 F407「原地执行」而 S3 要 Cache 窗口？Cache/DMA 的所有权交接方向（TX clean/RX invalidate）为什么不能反，32 B 行对齐与「禁对未对齐窄区间 invalidate」的机制是什么？「D1 有 Cache」这句简称错在哪，核与域的归属链怎么读？H7 的 DTCM 为什么只有 CPU/MDMA 能访问，F407 的 CCM 与它差在哪？D1/D2/D3 各归属什么，「是电源/时钟域不是三条电源轨」什么意思？H745 为什么是 AMP 不是 SMP，HSEM 只管什么不管什么？五层契约各冻结什么、注入什么？S3 支持 writeback 吗，「S3 是 write-through」错在哪？esp_cache 的 C2M/M2C 与 STM32 的 clean/invalidate 怎么对照？MPU 的两条解法与 M7 的 16 区上限是什么？
- **交付**：能画出三平台内存模型对照表（无 cache/带 cache/Cache 映射执行）；能把 Cache/DMA 交接方向表落到 `SCB_CleanDCache_by_Addr`/`SCB_InvalidateDCache_by_Addr` 的调用顺序；能把「cache 在核内、CM7 在 D1」的归属链说清；能写 DTCM/CCM 禁区表并配 map 核对动作；能把 H745 五层契约按层冻结、按层注入；能用 `soc_caps.h:140` 纠正「S3 write-through」的说法；能用 esp_cache 方向宏做跨平台对照；能给出 MPU 两条解法的设计口径并标注「仓库无实例」。
- **边界**：中断/临界区/`portMUX`/`volatile` 的机制归 [v1 第 10 章](../v1-drivers/10-interrupts-nvic-exti.md)（含 S3 的 SMP 半场：`ESP_INTR_FLAG_IRAM`、`xTaskCreatePinnedToCore`、`tskNO_AFFINITY`），本章只回链；DMA 的通道/_fifo/CCM 机制归 [v1 第 14 章](../v1-drivers/14-dma.md)；网络路径的禁区应用归 [第 33 章](./33-network-protocol-stack.md)（本章是主讲位，那里引用）；H7 的时钟/VOS/480 MHz 归 [第 28 章](./28-chip-migration-differences.md)。D28 五层契约的故障注入列是验收要求，不是已完成的实测。
- **依据锚点**：D25《H7 引脚》（`docs/25-STM32H7引脚.md` 的 Cache/电源域段）、E4《中断与双核》（`mcu/docs/esp32/04-irq-dualcore.md`，mapping 为 partial：双核半已迁 ch10，本章接 Cache 半场）、D28《嵌入式系统与 RTOS 生态》（`docs/28-嵌入式系统与RTOS生态.md:317-341` 的 H745 契约段）。上游对账：ESP-IDF v5.5.2 的 [soc_caps.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/soc/esp32s3/include/soc/soc_caps.h)、[esp_cache.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/esp_hw_support/include/esp_cache.h)、[cache_ll.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/hal/cache_ll.h)；AN4891、AN5557、PM0214。Cache 所有权图见 `D25:336-341`（自绘机制示意）。

## 先做出来

### 1. 三平台内存模型，一张表

| 平台 | CPU cache | 取指路径 | DMA 一致性 |
| --- | --- | --- | --- |
| F103/F407（M4F） | **无 cache** | 片内 Flash 原地执行 | 无 cache 维护义务；只有 DMA 禁区（CCM） |
| H743（M7） | **16 KB I + 16 KB D**（行 32 B） | 片内 Flash 原地执行 + cache 加速 | 显式 clean/invalidate + MPU 可选 |
| ESP32-S3（LX7×2） | cache 窗口映射 | **代码在外部 Flash，经 cache 窗口取指** | 写 Flash 关 Cache 窗口（[第 30 章](./30-esp32s3-architecture-boot.md)）；S3 支持 writeback（见机制段） |

三种模型三种义务：F4 只背「禁区表」；H7 要背「方向表 + 行对齐」；S3 要背「窗口纪律 + writeback 能力」。

### 2. 方向表纸上推演一次

任务：CPU 有一块 1 KB 缓冲，先填数据交给 DMA 发出去，再由 DMA 收回来 1 KB。两步的正确动作：

1. 交给 DMA **前**：`SCB_CleanDCache_by_Addr(buf, 1024)`——CPU 改的数据还在 cache 里，DMA 只看内存，不 clean 它读到旧值。
2. DMA 写完**后**：`SCB_InvalidateDCache_by_Addr(buf, 1024)`——cache 里是旧值，invalidate 让 CPU 重读内存。

反方向照抄就全错：TX 前 invalidate 会把 CPU 刚写好的数据从 cache 里丢掉（内存里还是旧值）；RX 后 clean 会把 cache 旧值冲回内存，覆盖 DMA 刚写的新数据。

## 机制

### 一、cache 行 32 B：整行生效与对齐纪律

M7 的 cache 行是 **32 字节**，clean/invalidate **按整行生效**——地址必须 32 B 对齐，且**缓冲独占整数行**。未对齐的窄区间 invalidate 是危险操作：invalidate 的范围向上/向下取整到行边界，**首尾行的邻位变量被一起丢掉**——邻位是别的脏变量，它的更新就丢了。所以「对未对齐窄区间 invalidate」不是效率问题，是正确性问题。ESP32 侧同一条纪律以运行期 API 存在：`Cache_Get_ICache_Line_Size()`/`Cache_Get_DCache_Line_Size()`（`cache_ll.h:501,514` 实取）；「S3 cache 行 32 B」本身属 TRM 层，标待核。

![手绘板：Cache 与 DMA 的所有权交接——TX clean、RX invalidate、32 B 行对齐独占（原理示意）](/images/ch27-cache-dma.png)

### 二、核与域：cache 在核内，不在域上

「D1 有 Cache」是简称，准确读法是一条归属链：**cache 在 Cortex-M7 核内；CM7 核属 D1 域**（AN5557 口径）。三域归属：D1 = CM7 + AXI 总线（Flash、AXI SRAM、FMC、QSPI）；D2 = 多数外设 + D2 SRAM +（双核型的）CM4；D3 = 低功耗域（BDMA/LPTIM/备份域）。域是**电源/时钟域**——不是三条可以随意分开断电的 VDD 电源轨（D25:126 原口径）。域断电与 cache 维护是两件事：域断了，cache 维护无从谈起；域没断，跨 DMA 的维护照样要做。

![手绘板：H7 电源域 D1/D2/D3 与核的归属（原理示意）](/images/ch25-power-domains.png)

### 三、可达性矩阵：DTCM 与 CCM 不是一回事

| 平台 | 禁区地址 | 谁能访问 | 谁不能 | 手册 |
| --- | --- | --- | --- | --- |
| H7 | **DTCM `0x20000000`** | CPU、MDMA | ETH/DMA1/DMA2 | AN4891 / RM0433 |
| F407 | **CCM `0x1000_0000`**（64 KB） | CPU 数据总线 | 所有 DMA | RM0090 / [v1 第 14 章](../v1-drivers/14-dma.md) |
| ESP32-S3 | 无此概念 | — | — | 写 Flash 关 Cache 窗口 |

地址不同（`0x20000000` vs `0x1000_0000`）、原因不同（DTCM 是「只有 CPU/MDMA 挂在总线上」vs CCM 是「总线矩阵对该区无 DMA 从机通路」）、手册不同（AN4891/RM0433 vs RM0090）。对策相同：描述符与 DMA 缓冲放可达区（H7 放 D1 AXI SRAM 或 D2 SRAM），**写完 section 不算完成——打开链接 map 确认落点地址**（[第 33 章](./33-network-protocol-stack.md) 的 RAM_net 账也在同一动作里）。

### 四、MPU：两条解法与 16 区上限

H7 上让 DMA 缓冲与 cache 和平共处的两条路：

1. **Non-Cacheable 区**：用 MPU 把 DMA 缓冲区配成非缓存属性——代价是该区 CPU 访问也变慢；M7 的 MPU 区上限是 **16**（M3/M4 是 8，ARM PMSAv7 架构事实）。
2. **显式维护**：保持 cacheable，搬运前后按方向表调用 `SCB_CleanDCache_by_Addr`/`SCB_InvalidateDCache_by_Addr`（CMSIS 真实函数）——零内存代价，调用点纪律要进评审。

仓库没有 H7 MPU 区配置实例——写法属**设计口径**（文档推导），落地时把 MPU 配置代码、维护调用点、链接 map 三样一起进评审记录。

### 五、H745：AMP，不是一个内核管两颗核

H745 的 M7+M4 双核常见形态是 **AMP**：两颗核各跑一个内核固件，通过共享内存交换数据、用 HSEM 完成核间同步。这与 S3 的 SMP 是两种世界——「有两颗核」推不出「一个内核管两个核」（[第 27 章](../v3-rtos/27-rtos-comparison-selection.md) 的旁注在本章展开）。S3 半场的 SMP 机制（单内核双核、`xTaskCreatePinnedToCore`、`portMUX`、`tskNO_AFFINITY`）已在 [v1 第 10 章](../v1-drivers/10-interrupts-nvic-exti.md) 冻结，本章不重教。

HSEM 只提供两件事：**原子占用/释放**与**给另一核发中断通知**。它不搬 payload、不替 M7 维护 data cache——「锁解决谁先来，不解决货到没到」。

### 六、五层契约：从旁注展开成契约书

双核通道的评审核五层，每层冻结一组字段并带最小故障注入（`D28:328-334` 的设计与验收协议；**非实测**——`:336` 自认）：

| 层 | 必须冻结 | 最小故障注入 |
| --- | --- | --- |
| 共享存储 | 两核可访问的 SRAM 起始/长度/对齐/结构体布局；不得藏进某核私有栈或链接段 | 注入越界长度/错误对齐/非法状态，接收端必须拒绝 |
| 所有权与可见性 | 单写者/读者切换；交接边界建立发布/获取顺序并执行内存屏障——**HSEM 释放不替代屏障** | 连续更新序号与 payload，读端只接受同代数据 |
| 同步 | HSEM ID 分配、持有者、最长持有时间、超时与降级动作 | 占住一个 HSEM 或丢一次通知，另一核必须限时超时并留原因 |
| 消息协议 | magic/版本/长度/序号/兼容规则（共享 C 结构体也算线上协议） | 注入未知版本/截断长度/重复序号，接收端给出可区分拒绝 |
| 启动与恢复 | 哪核先初始化共享区、ready/代际号、心跳、单核复位后的重同步 | 分别冻结 M7/M4，存活核进预定降级态，不无限等待 |

![手绘板：H745 双核五层契约——每层冻结什么、注入什么，HSEM 只管「谁先来」不管「货到没到」（原理示意）](/images/ch28-h745-contracts.png)

### 七、S3 的 writeback：纠正一个流行说法

「ESP32-S3 的 cache 是 write-through」**是错的**：v5.5.2 实取 `soc_caps.h:140` 的 `SOC_CACHE_WRITEBACK_SUPPORTED=1`——S3 **支持 writeback**；经典 ESP32 才不支持（`esp_cache.h:57` 原话：msync「will do nothing on ESP32」）。S3 的**默认写策略**（write-back 还是 write-through）属 TRM 层，本轮未取，只能写「TRM 层待核」。

esp_cache 的方向宏与 STM32 侧一一对应（`esp_cache.h:25-38` 逐行实取），跨平台对照表：

| ESP32（esp_cache_msync） | STM32（CMSIS） | 语义 |
| --- | --- | --- |
| `DIR_C2M`（默认） | clean | CPU→内存 |
| `DIR_M2C` | invalidate | 内存→CPU |
| `DIR_C2M|INVALIDATE` | clean + invalidate | 两个动作 |
| `FLAG_UNALIGNED` | （无等价：STM32 要求对齐） | 未对齐块自担风险 |

行大小运行期可查（`cache_ll.h:501,514`）；S3 取指的两条路与关 Cache 窗口的内存模型读法，机制本体在 [v1 第 10 章](../v1-drivers/10-interrupts-nvic-exti.md) 的 IRAM 纪律段，本章只用其结论。

![ESP32 中断分配与核间结构：SMP 单实例的两颗核](/figures/esp32-04-int-alloc.svg)

![网络 DMA 与 cache 所有权：交接边界的归属图](/figures/network-cache-ownership.svg)

## 测量与证据

| 结论 | 身份 | 判据 |
| --- | --- | --- |
| 三平台 cache 有无与取指路径 | 手册级 | ARM 架构事实 + DS12110 封面行 |
| cache 行 32 B、整行生效 | 手册级（多源一致） | PM0214/TRM 口径 |
| CM7@D1/CM4@D2/D3 低功耗 | 手册级（AN5557） | 核归属已核；域内外设逐项清单未取 RM0433 原表 |
| DTCM 只有 CPU/MDMA 可达 | 手册级（AN4891） | RM0433 访问矩阵同口径 |
| S3 writeback 支持位 | 手册级（上游已核） | `soc_caps.h:140` 逐行实取 |
| 经典 ESP32 无 writeback | 手册级（上游已核） | `esp_cache.h:57` 原话 |
| msync 方向宏 | 手册级（上游已核） | `esp_cache.h:25-38` |
| S3 默认写策略 | 来源说法待核 | TRM 层未取；只写「TRM 待核」 |
| S3 cache 行 32 B | 来源说法待核 | TRM 层；运行期 API 已核 |
| H745 五层契约 | 设计与验收协议（未实测） | `D28:336` 自认非实测；故障注入列是验收要求 |
| MPU 两条解法 | 文档推导（设计口径） | 仓库无 H7 MPU 实例，落地三样进评审 |
| HSEM 寄存器层 | 来源说法待核 | RM0399 未取件 |

## 失败分支

| 症状 | 第一条假设 | 区分实验 |
| --- | --- | --- |
| DMA 发出的数据是旧值 | TX 前 没 clean（或缓冲不独占行） | 检查方向表与 32 B 对齐 |
| DMA 收到的数据偶发错乱 | RX 后没 invalidate；或未对齐 invalidate 丢邻位 | 检查调用顺序；对齐改独占整行 |
| ETH/SDMMC 挂死在 DTCM 地址 | 描述符落进 `0x20000000`（H7） | 链接 map 对落点；挪 D1/D2 SRAM |
| 同样的 DMA 代码 F4 好使 H7 坏 | cache 有无差异（不是外设坏了） | 对照两平台的维护义务 |
| 双核数据「互相看不见」 | 少了发布/获取屏障（以为 HSEM 释放就够了） | 五层契约第 2 层；加屏障与序号回读 |
| 双核一核复位后通道死掉 | 没有代际号/重同步设计 | 第 5 层注入实验：分别复位看存活核行为 |
| msync 对经典 ESP32 无效果 | 那颗芯不支持 writeback（原话 will do nothing） | 换 S3 或改软件维护 |
| MPU 配完更慢 | Non-Cacheable 区把 CPU 访问也拖慢 | 权衡两解法；热数据移出该区 |

## 跨平台边界

- S3 的 SMP 半场（中断分配、IRAM 纪律、`portMUX`、双核自旋锁）：归 [v1 第 10 章](../v1-drivers/10-interrupts-nvic-exti.md)，本章只回链。
- F407 的 DMA 通道与 CCM 机制：归 [v1 第 14 章](../v1-drivers/14-dma.md)。
- 网络场景的禁区应用与 RAM_net 账：归 [第 33 章](./33-network-protocol-stack.md)。
- H7 的时钟树/VOS/revision 门禁：归 [第 28 章](./28-chip-migration-differences.md)。
- H745 双核的启动交接与 OTA 场景：归 [v1 第 17 章](../v1-drivers/17-flash-iap-ota.md) 的 IAP/双槽口径，本章只讲通信契约。

## 离开检查

- 三平台内存模型（无 cache/带 cache/Cache 映射）一张表能画，各自义务说得清。
- 方向表（TX clean/RX invalidate）与 32 B 独占纪律能落到 CMSIS 调用顺序；未对齐 invalidate 的危害能讲。
- 「cache 在核内、CM7 在 D1」的归属链与三域分工能白板画。
- DTCM/CCM 禁区表（地址/原因/手册三列）能钉死，map 核对动作记得住。
- H745 的 AMP 语义与五层契约能按层冻结、按层注入；「HSEM 不替代屏障」说得清。
- 「S3 支持 writeback」能用 `soc_caps.h:140` 定谳；msync 与 CMSIS 的方向对照表能互译。
- MPU 两条解法的取舍与「仓库无实例、设计口径」的诚实边界守得住。
