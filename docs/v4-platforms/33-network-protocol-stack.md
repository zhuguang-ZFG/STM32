---
title: "网络与协议栈"
platforms: [f407, esp32]
---

# 网络与协议栈

MCU 上网络的第一课不是 API，是**边界**：DMA 看见的内存与 CPU 看见的内存不同；lwIP 的 pbuf 是所有权不是指针；TCP 是字节流，帧边界要自己定义；三个平台的 DMA 禁区同名不同址不同原因。这一章把 F407 的以太网 + lwIP 与 ESP32 的 esp_netif→lwIP 摆在同一张解剖台上，按「先写需求、再选硬件」的顺序讲五条路径，把协议栈拆到 pbuf 不变式与 core-locking 边界。

证据先说清：本章零板级实测。lwIP 按 **2.2.1**（RELEASE）实取核对：`pbuf.h:186-203`（结构体与 `tot_len` 不变式逐字命中）、`opt.h:190,2168,2086`（core-locking 默认开、`LWIP_SOCKET_SELECT=1`、`LWIP_SO_SNDTIMEO=0`）、`init.h:53-61`（版本三段号）；lwIP 子模块 commit `07680c81…` 属 **ST fork `stm32-mw-lwip`**（lwip-tcpip/lwip 同 commit 是 404，curl 实取）。H7 的 DTCM 禁区按 AN4891 口径；F407 的 CCM 禁区沿 [v1 第 14 章](../v1-drivers/14-dma.md) 已冻结口径。四个递进实验（A–D）与 `labs/ethernet-24h` 的 localhost smoke 全部「未实测」，不冒充真板记录。ESP32 半场的 esp_netif 是 IDF 文档口径（来源说法待核），六步骨架已在 [第 32 章](./32-esp32-wifi-ble-espnow.md) 教过，本章只接手。

> 版本口径：lwIP **2.2.1**（STM32CubeH7 冻结 commit 的 LwIP 子模块，位于 ST fork `stm32-mw-lwip`，commit `07680c81…`；引用行号写 `LWIP@07680c81:文件:行`，禁写 `lwip-tcpip/lwip@07680c81`）；CubeH7 顶层 commit `8ec3113d…`；Mbed TLS 子模块 `cdadeb9b…`（本轮未核，来源说法未复核）。H7 侧按 AN4891/RM0433；F407 侧按 RM0090 与 [v1 第 14 章](../v1-drivers/14-dma.md)。

## 本章罗盘

- **问题**：五条网络路径（内置 MAC+PHY / SPI Ethernet / AT offload / PPP / OS 网络栈）各自适合什么，为什么「CubeMX 能勾选」不是上内置 Ethernet 的理由？RMII 六组信号是什么，link LED 亮为什么只是线索？H7 的 Ethernet DMA 为什么进不了 DTCM，F407 的对应禁区是什么，描述符与缓冲放哪、怎么用 map 核对？Cache 维护的方向表（TX clean / RX invalidate）为什么不能反，未对齐窄区间 invalidate 错在哪？pbuf 为什么是所有权不是指针，`tot_len` 不变式是什么，free 为什么恰好一次？lwIP 三套 API 的线程边界是什么，IRQ 里为什么禁调 `tcp_write`？TCP 字节流上的帧协议怎么定义，单截止点发送为什么依赖 `LWIP_SOCKET_SELECT` 而不依赖 `LWIP_SO_SNDTIMEO`？RAM_net 七项账怎么列？ESP32 的 esp_netif 与 GOT_IP 事件是什么角色？
- **交付**：能按需求走五路径决策表；能列出 RMII 六组信号并设计「link 灯亮但 ping 不通」的排查顺序；能写出三平台 DMA 禁区表（H7 DTCM / F407 CCM / ESP32 关 Cache 窗口）并配 map 核对动作；能画 Cache 交接方向表与 32 B 行对齐纪律；能用 `pbuf.h:198` 的不变式解释 pbuf 链与所有权；能按三套 API 的线程边界回答「IRQ 里能不能发网络包」；能定义 0x534E 帧格式并写出单截止点 `send_all_until`；能列 RAM_net 七项账与三本运行账（goodput/丢包恢复/重试率）。
- **边界**：单讲 lwIP 侧网络栈；Wi-Fi 连接层（事件循环、六步骨架）归 [第 32 章](./32-esp32-wifi-ble-espnow.md)，本章从 `IP_EVENT_STA_GOT_IP` 之后接手；DMA 机制与 CCM 禁区归 [v1 第 14 章](../v1-drivers/14-dma.md)；H7 的 Cache/双核语义归 [第 34 章](./34-multicore-cache.md)（本章只用「TX clean/RX invalidate」结论）；RTOS 堆策略归 [第 25 章](../v3-rtos/25-memory-management.md)。MQTT/TLS 只讲语义与前提，具体端口号与库细节不展开。
- **依据锚点**：D27《网络与协议栈》（`docs/27-网络与协议栈.md`）、E8《Wi-Fi》（`mcu/docs/esp32/08-wifi.md`，仅衔接段）。上游对账：lwIP `stm32-mw-lwip@07680c81` 的 [pbuf.h](https://github.com/STMicroelectronics/stm32-mw-lwip/blob/07680c81/src/include/lwip/pbuf.h)、[opt.h](https://github.com/STMicroelectronics/stm32-mw-lwip/blob/07680c81/src/include/lwip/opt.h)、[init.h](https://github.com/STMicroelectronics/stm32-mw-lwip/blob/07680c81/src/include/lwip/init.h)、[tcpip.h](https://github.com/STMicroelectronics/stm32-mw-lwip/blob/07680c81/src/include/lwip/tcpip.h)；AN4891（H7 系统架构）；CubeH7 `@8ec3113d`（lwIP 子模块 gitlink 已核）。

## 先做出来

### 1. 五条路径的决策表

| 路径 | 硬件前提 | 优势 | 代价 |
| --- | --- | --- | --- |
| 内置 MAC+PHY | 芯片带 MAC（F407/H7）+ 外置 PHY | 带宽最高、CPU 占用低 | RMII 六组信号 + PHY 驱动 |
| SPI Ethernet | 任意 MCU + W5500 类 | 移植最简、引脚少 | 带宽受 SPI 限制 |
| AT offload | 蜂窝/Wi-Fi 模组 | 协议栈在模组里 | URC 交错、状态机仍在 MCU |
| PPP | 任意串口 + 蜂窝 | 复用串口 | 带宽最低、CPU 最高 |
| OS 网络栈 | 跑 Linux 的芯 | 全栈现成 | 不在本章世界 |

「CubeMX 能勾选 ETH」只说明外设存在，不说明你有 PHY、有磁性件、有引脚预算——**先写需求（带宽/延迟/连接数），再选硬件**。

### 2. 三平台 DMA 禁区，一张表钉死

| 平台 | 禁区 | 原因 | 对策 |
| --- | --- | --- | --- |
| H7 | **DTCM `0x20000000`** | 只有 CPU 与 MDMA 能访问，ETH DMA 不可达（AN4891 口径） | 描述符/缓冲放 D1/D2 SRAM |
| F407 | **CCM `0x1000_0000`** | 总线矩阵对该区无 DMA 从机通路 | 同上，放普通 SRAM |
| ESP32-S3 | 无此概念 | 但写 Flash 期间关 Cache（[第 30 章](./30-esp32s3-architecture-boot.md)） | 写 Flash 的窗口里别跑网络 ISR |

同名不同址不同原因——「DTCM 不可达」这句话**不属于 F407**。写完分配后核对动作只有一个：打开链接 map，确认描述符与缓冲区的落点地址真的在允许区。

## 机制

### 一、RMII：六组信号与「link LED 只是线索」

内置 MAC + 外置 PHY 的最少信号六组：REF_CLK 50 MHz、TXD0/1 + TX_EN、RXD0/1 + CRS_DV、MDC/MDIO、NRST + strap（PHY 地址/模式由 strap 决定）、磁性件 + RJ45。排障顺序：MDIO 读不到 PHY ID → 停在硬件层（strap/接线/REF_CLK）；**link LED 亮只是线索**，不证明 MDIO 通、更不证明 IP 层通。

### 二、Cache 交接：方向表与 32 B 行

H7 的 D-Cache 使 DMA 一致性变成显式工作（M7 cache 行 **32 字节**，clean/invalidate 按整行生效）：

| 方向 | 交接前动作 | 原因 |
| --- | --- | --- |
| TX（CPU→DMA） | **clean**：把 cache 里改过的缓冲冲到内存 | DMA 只看内存 |
| RX（DMA→CPU） | **invalidate**：让 CPU 丢弃 cache 旧值，重读内存 | DMA 已写内存 |

两个纪律：缓冲**独占 cache 行**（32 B 对齐独占，不与别的变量共行）；**禁对未对齐窄区间直接 invalidate**——整行生效会把首尾邻位的脏变量一并丢掉。F407 无 cache，描述符 4 字对齐即可（RM0090 页码待核）。方向表与双核扩展归 [第 34 章](./34-multicore-cache.md)，此处只留结论。

### 三、pbuf：所有权不是指针

lwIP 的 `pbuf`（`pbuf.h@07680c81:186-203` 实取）：

```c
struct pbuf {
  struct pbuf *next;    /* :188 链 */
  void *payload;        /* :191 本段数据 */
  u16_t  tot_len;       /* :200 全链总长 */
  u16_t  len;           /* :203 本段长度 */
};
```

不变式（`:198` 原文）：`p->tot_len == p->len + (p->next ? p->next->tot_len : 0)`。三条推论：**pbuf 可能是链**——一次收到的包不保证连续，跨段要自己拼；**所有权唯一**——谁持有谁释放，`pbuf_free()` 恰好一次，多 free 是 use-after-free，漏 free 是泄漏；**zero-copy RX 的代价**——DMA 直接写进 pbuf，CPU 处理期间缓冲被驱动复用，想留数据就得 memcpy 走。

![pbuf 链拆图：HELLO/WORLD/123 三段与 tot_len 不变式](/images/ch27-pbuf-chain.png)

![网络包的旅程：从网卡到 socket 的分层](/anim/network-packet-journey.svg)

### 四、三套 API 与线程边界

lwIP 三套 API 的上下文边界（`opt.h:190,226-227`、`tcpip.h:83` 实取）：

| API 层 | 允许上下文 | 说明 |
| --- | --- | --- |
| raw（`tcp_*`/`udp_*` 回调式） | `NO_SYS` 主循环，或 `tcpip_thread` / `tcpip_callback()` 内 | 无 OS 时直接主循环 |
| netconn | 应用任务 | 带 OS 的中等抽象 |
| socket | 应用任务 | BSD 风格，最通用 |

**IRQ 里禁调 `tcp_write()`/`udp_send()`**：这些 API 要拿内核锁。开发期保留 `LWIP_ASSERT_CORE_LOCKED()`（`opt.h:226-227` 默认空定义，工程打开即抓违规）；`LWIP_TCPIP_CORE_LOCKING` 在 opt.h 源级默认开（`:190`），工程 lwipopts 常关——以目标工程配置为准。

### 五、TCP 字节流上的自定帧

TCP 只保证字节流顺序（RFC 9293 口径），**没有消息边界**。应用层自定帧（教学设计，0x534E 口径）：magic `0x534E`、ver+type、`payload_len`（网络序）、sequence、CRC32；长度超限/未知版本/超时即断链。发送侧单截止点（`opt.h:2168,2086` 实取的默认值是这段设计的地基）：

```c
/* 依赖默认开启的 LWIP_SOCKET_SELECT（opt.h:2168 =1），
   不依赖默认关闭的 LWIP_SO_SNDTIMEO（opt.h:2086 =0） */
int32_t deadline = sys_now() + budget_ms;          /* 唯一截止点 */
while (sent < total) {
    /* select() 等可写 → send(MSG_DONTWAIT) */
    int32_t remaining_ms = (int32_t)(deadline_ms - sys_now());
    if (remaining_ms <= 0) return ERR_TIMEOUT;      /* 回绕安全前提：budget < INT32_MAX */
}
```

所有重试共享同一个 `sys_now()` 单调截止点——每层各设一个超时的系统，端到端叠加远超预期（[第 27 章](../v3-rtos/27-rtos-comparison-selection.md) 的 R=B+C+S 口径）。帧图与 sendall 循环的手绘板：

![TCP 帧格式手绘板：magic/ver/len/seq/CRC 字段排布（原理示意）](/images/ch27-tcp-framing.png)

![手绘板：send_all 的单截止点循环（原理示意）](/images/ch27-sendall-loop.png)

![TCP 字节流示意：两段应用消息在流里连排](/figures/tcp-byte-stream.svg)

### 六、RAM_net：七项账与三本运行账

网络内存是 MCU 上最容易漏算的一块，七项一起列（各项数值留待工程实测）：描述符 + RX 池 + TX 池 + lwIP 堆 + socket 缓冲 + TLS 峰值 + 应用离线队列。运行期三本账：goodput（有效吞吐，不是链路速率）、丢包/重试率、故障恢复时间——**峰值不报平均值**（[第 27 章](../v3-rtos/27-rtos-comparison-selection.md) 的定量口径）。TLS 的内存峰值经常是七项里最大的一块，按固定配置实测后冻结。

![手绘板：网络系统四本账——内存、吞吐、丢包、恢复，各自记什么（原理示意）](/images/ch27-four-ledgers.png)

### 七、ESP32 半场：esp_netif 与 GOT_IP

ESP32 上 WiFi 的连接层归 [第 32 章](./32-esp32-wifi-ble-espnow.md)；从 socket 可用性看，`esp_netif` 是 WiFi 与 lwIP 的适配层，**`IP_EVENT_STA_GOT_IP` 是 socket 可用的唯一合法起点**——拿到 IP 前调 `connect` 是必败操作。WiFi 断开后 netif 与 lwIP 状态机仍在，重连后 IP 可能变化，绑定具体 IP 的代码要重新读。AT 模组的半场（offload 路径）：TCP/IP 移进模组后，MCU 端的 transaction id、deadline、URC 交错、离线队列上限一样不少——协议栈搬走了，状态机没有。

![API 上下文手绘板：raw/netconn/socket 各自的调用上下文与 IRQ 禁令（原理示意）](/images/ch27-api-context.png)

## 测量与证据

| 结论 | 身份 | 判据 |
| --- | --- | --- |
| lwIP 版本 2.2.1 与 ST fork 归属 | 手册级（上游已核） | `init.h:53-61` + GitHub gitlink/404 实取 |
| pbuf 结构与 `tot_len` 不变式 | 手册级（上游已核） | `pbuf.h:186-203` 逐字命中 |
| core-locking 默认 / SELECT=1 / SNDTIMEO=0 | 手册级（上游已核） | `opt.h:190,2168,2086` |
| H7 DTCM 禁区 | 手册级（AN4891 口径） | 只有 CPU/MDMA 可达 |
| F407 CCM 禁区 | 手册级 | [v1 第 14 章](../v1-drivers/14-dma.md) 已冻结口径 |
| M7 cache 行 32 B、整行生效 | 手册级（多源一致） | PM0214/TRM 口径 |
| F407 描述符 4 字对齐 | 来源说法待核 | RM0090 页码未取件 |
| Mbed TLS 子模块 `cdadeb9b` | 来源说法(未复核) | 本轮未核 |
| 实验四步 A–D 与 24 h 长跑 | 未实测 | `labs/ethernet-24h` 仅主机端 smoke，输出未入库 |
| esp_netif/GOT_IP 语义 | 来源说法待核 | IDF 文档口径，机制成立 |
| RAM_net 七项数值 | 未实测 | 各项留待工程实测 |

Wireshark 过滤器速查（实验 A–D 用）：`arp`、`icmp`、`bootp`（DHCP）、`dns`、`tcp.flags.syn==1`、`tls.handshake.type==1`（ClientHello）。

## 失败分支

| 症状 | 第一条假设 | 区分实验 |
| --- | --- | --- |
| MDIO 读不到 PHY ID | strap 地址错 / REF_CLK 停 / MDC 接线 | 读 PHY ID 寄存器对照 datasheet；量 50 MHz |
| link 亮但 ping 不通 | ARP 或 IP 配置层 | Wireshark 看 ARP 请求/应答是否成对 |
| ping 通但 TCP 不通 | 端口/防火墙/帧协议层 | `tcp.flags.syn==1` 看握手到第几步 |
| 大包必挂 | 描述符/缓冲落进 DMA 禁区 | 链接 map 对地址；H7 查 DTCM、F407 查 CCM |
| 偶发数据错乱（H7） | RX 后忘了 invalidate 或缓冲没独占行 | 检查 32 B 对齐独占与维护调用点 |
| free 后崩溃 | pbuf 双 free | 所有权表：谁持有谁释放，恰好一次 |
| IRQ 里死锁 | 调了 `tcp_write` | IRQ 只投递，任务里发 |
| 发送卡死无超时 | 每层各设超时叠加 / 没用单截止点 | 统一 `sys_now()` 截止点；select + MSG_DONTWAIT |
| 重连后连不上旧 IP | GOT_IP 后 IP 变了 | 事件里重新读 IP；不缓存旧值 |

## 跨平台边界

- Wi-Fi 连接层与事件循环：归 [第 32 章](./32-esp32-wifi-ble-espnow.md)；本章从 GOT_IP 接手。
- DMA 机制与 CCM 的完整语义：归 [v1 第 14 章](../v1-drivers/14-dma.md)。
- H7 双核、cache 细节与 AMP 契约：归 [第 34 章](./34-multicore-cache.md)。
- RTOS 堆与内存池策略：归 [第 25 章](../v3-rtos/25-memory-management.md)；本章的 RAM_net 账不与 heap_x 选型混排。

## 离开检查

- 五路径决策表能按需求走通，「先写需求再选硬件」不是口号。
- RMII 六组信号能列全，「link 灯亮」的三层排查顺序能设计。
- 三平台 DMA 禁区表（DTCM/CCM/关 Cache）能钉死，map 核对动作说得清。
- TX clean / RX invalidate 方向表与 32 B 独占纪律能落到代码顺序。
- pbuf 的链结构、`tot_len` 不变式、free 恰好一次能讲透。
- 三套 API 的线程边界与 IRQ 禁令能回答「中断里能不能发包」。
- 0x534E 帧 + 单截止点发送能写出可编译骨架；RAM_net 七项账能列全。
