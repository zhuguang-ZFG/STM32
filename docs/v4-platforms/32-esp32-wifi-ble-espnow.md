---
title: "Wi-Fi、蓝牙与 ESP-NOW"
platforms: [esp32]
---

# Wi-Fi、蓝牙与 ESP-NOW

Wi-Fi 与 BLE 在 ESP32 上是「预编译巨人」：协议栈不开放源码、以库形态链接，你写的是事件回调与状态机——所以这一章的世界观是**事件循环**：`esp_event` 三件套把 Wi-Fi 的状态变化送进你的 handler，handler 不能阻塞。ESP-NOW 是一条旁路：不走 AP、不建 socket，peer 互发小包，适合低延迟的控制面。本章把三条链路拆到 API 行：六步骨架、reason 分诊、退避序列、NVS 依赖、BLE 双栈选择、ESP-NOW 的边界数字。

证据先说清：本章零板级实测。上游核对按 **ESP-IDF v5.5.2** 实取（`esp_wifi_types_generic.h:1062-1065,1154-1160,117,131,166-168`、`esp_netif_types.h:99-100`、`esp_now.h:19-37,118-127,224`、`bt/Kconfig:12-27`、`soc_caps.h:45,594-596` 全部命中；`esp_event_base.h:22-24` 的 handler 四参签名实取）。重连耗时、双板互传、测距丢包全部「未实测」；`wifi:state:` 之类的日志字样是示意口径，待上板回填；NimBLE 省内存的方向性说法标待核。

> 版本口径：ESP-IDF **v5.5.2**。事件枚举的实体头是 **`esp_wifi_types_generic.h`**（v5.5 的 `esp_wifi_types.h` 是壳，引用出处写 generic 版）；ESP-NOW 回调是 v5.x 的 **info 结构体版**签名。BLE 双栈的符号名带 `_ENABLED` 后缀。

## 本章罗盘

- **问题**：`esp_event` 三件套是什么，handler 跑在谁的上下文、为什么不能阻塞？STA 骨架六步的顺序铁律是什么，`esp_wifi_start` 为什么是异步的？DISCONNECTED 事件的 reason code 怎么分诊，4 号码的旧解释错在哪？指数退避的序列怎么复算，为什么重连逻辑不能写在 handler 里？NVS 为什么是 Wi-Fi/BT 的第一依赖，两个自愈报错怎么处理？S3 的蓝牙为什么是单模 BLE，Controller/Host/HCI 三层怎么分？NimBLE 与 Bluedroid 怎么二选一，默认是谁，S3 选 NimBLE 的真实理由是什么？GATT 三级容器与 CCC 订阅机制是什么？ESP-NOW 的三步、peer 结构、上限数字（250/1470/6/20）、双回调签名、信道规则各是什么？
- **交付**：能画出 Wi-Fi 状态机与事件循环的关系图；能写六步骨架并说出每步失败后果；能把 reason 201/15/202/203 分诊到具体物理原因，指出 4 号码是弃用码；能复算退避序列（1→2→4→8→16→32→60 封顶）；能处理 NVS 的 `NO_FREE_PAGES`/`NEW_VERSION_FOUND` 自愈；能按 `bt/Kconfig` 的 choice 机制选栈并写对符号名；能画 GATT 的 service→characteristic→descriptor 三级与 CCC(0x2902) 订阅；能写 ESP-NOW 三步与 v5.x 回调签名，背出四个上限数字并分诊 `ESP_ERR_ESPNOW_CHAN`。
- **边界**：单平台 ESP32-S3（单模 BLE）；TCP/IP 协议栈与 socket 语义归[第 33 章](./33-network-protocol-stack.md)（esp_netif→lwIP 的衔接在那里讲）；NVS 的存储机制归 [第 30 章](./30-esp32s3-architecture-boot.md) 的分区表段；FreeRTOS 队列/任务机制回 [v3-rtos](../v3-rtos/22-tasks-tcb-scheduler.md)；经典蓝牙（SPP/A2DP）在 S3 上不存在，本章不写。示例日志字样是示意口径。
- **依据锚点**：E8《Wi-Fi》（`mcu/docs/esp32/08-wifi.md`）、E9《BLE 与 ESP-NOW》（`.../09-bt-espnow.md`）。上游对账：ESP-IDF v5.5.2 的 [esp_wifi_types_generic.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/esp_wifi/include/esp_wifi_types_generic.h)、[esp_netif_types.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/esp_netif/include/esp_netif_types.h)、[esp_now.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/esp_wifi/include/esp_now.h)、[esp_event_base.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/esp_event/include/esp_event_base.h)、[bt/Kconfig](https://github.com/espressif/esp-idf/blob/v5.5.2/components/bt/Kconfig)、[soc_caps.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/soc/esp32s3/include/soc/soc_caps.h)。

## 先做出来

### 1. 六步骨架，纸上走一遍

STA 连接的最小骨架六步，顺序是铁律（`esp_wifi_start` 是异步的——它立即返回，`WIFI_EVENT_STA_START` 事件到了才能 connect）：

```c
nvs_flash_init();                                  /* ① NVS：校准数据+MAC 都住那 */
esp_netif_create_default_wifi_sta();               /* ② netif（默认 STA 形态） */
esp_event_loop_create_default();                   /* ③ 事件循环（默认任务） */
esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID,
                           &handler, NULL);        /* ④ 注册回调（ANY_ID 收全部） */
esp_wifi_init(&cfg);                               /* ⑤ wifi_init（WIFI_INIT_CONFIG_DEFAULT） */
esp_wifi_start();                                  /* ⑥ start（异步） */
/* handler 里收到 WIFI_EVENT_STA_START 后才 esp_wifi_connect() */
```

事件全表（`esp_wifi_types_generic.h:1062-1065` 实取）：`WIFI_EVENT_STA_START` → `STA_CONNECTED` → `STA_DISCONNECTED`（带 reason 字段，`:1154-1160`）；IP 层的 `IP_EVENT_STA_GOT_IP`/`LOST_IP` 在另一个基上（`esp_netif_types.h:99-100`）。每步失败后果：①失败 Wi-Fi/BT 都起不来（见 NVS 段）；②③不建则收不到任何事件；④漏注册 = 世界静默；⑤失败查内存与参数；⑥后立刻 connect 是新手最常见错——start 还没完成。

### 2. reason 分诊表

`wifi_event_sta_disconnected_t.reason` 的分诊（码值上游实取）：

| 码 | 宏 | 物理原因 | 处置 |
| --- | --- | --- | --- |
| 201 | `WIFI_REASON_NO_AP_FOUND`（`:166`） | 扫不到这个 SSID | 查名字/信号/路由器 |
| 15 | `WIFI_REASON_4WAY_HANDSHAKE_TIMEOUT`（`:131`） | **四次握手超时**——密码错的典型现场 | 改密码重试 |
| 202 | `WIFI_REASON_AUTH_FAIL`（`:167`） | 认证失败 | 查认证方式 |
| 203 | `WIFI_REASON_ASSOC_FAIL`（`:168`） | 关联失败 | 查 AP 容量/黑名单 |
| 4 | `WIFI_REASON_ASSOC_EXPIRE`（`:117`） | **已标 Deprecated** | 别当「关联被拒」用 |

旧材料「4=关联被拒」是错的：4 是 ASSOC_EXPIRE 且上游已弃用；关联失败是 203、认证失败是 202。「15=认证超时」也要说准：是**四次握手**超时，密码错的典型现场。

## 机制

### 一、事件循环：handler 不能阻塞

`esp_event` 三件套：事件循环任务（`esp_event_loop_create_default` 创建的默认任务）、事件基（`WIFI_EVENT`/`IP_EVENT`）、注册的回调。handler 的四参签名（`esp_event_base.h:22-24` 实取）：

```c
void handler(void *arg, esp_event_base_t base, int32_t id, void *data);
```

handler 跑在**事件循环任务**的上下文里——所有事件的 handler 是单线程串行的。**handler 里阻塞，整个事件系统停摆**：Wi-Fi 内部事件、你的其他 handler 全部排队。「handler 里 vTaskDelay 会丢事件」不是实测结论，是单线程机制的推论；长操作（重连等待、日志刷写）交给 esp_timer 回调或独立任务。重连的**指数退避**：`delay_ms = retry_count < 6 ? (1000 << retry_count) : 60000`——序列复算 1/2/4/8/16/32 s，第七档起 60 s 封顶（封顶值是产品权衡，来源说法待核）；退避计时用 esp_timer，不在 handler 里睡。

![Wi-Fi 状态机与事件循环动画：六步骨架与断线重连](/anim/tcp-handshake.svg)

### 二、NVS：Wi-Fi/BT 的第一依赖

射频校准数据与 MAC 都存 NVS——`nvs_flash_init` 失败的话 Wi-Fi/BT 初始化都没有意义。两个可自愈报错：`ESP_ERR_NVS_NO_FREE_PAGES`（分区被旧版本写满）与 `ESP_ERR_NVS_NEW_VERSION_FOUND`（NVS 格式升级）——标准做法是 `nvs_flash_erase()` 后重新 init。这也解释了分区表里 `nvs` 区（[第 30 章](./30-esp32s3-architecture-boot.md) 的 0x6000）为什么是默认表第一个 data 区。

### 三、BLE：单模、双栈、预编译巨人

S3 是**单模 BLE**（无经典蓝牙控制器）且支持 BLE 5.0——`soc_caps.h:594-596` 实取 `SOC_BLE_SUPPORTED=1`、`SOC_BLE_50_SUPPORTED=1`（`:45` 的 `SOC_BT_SUPPORTED=1` 是总开关）。协议栈三层：Controller（预编译库）/ Host（可选）/ HCI——S3 内部用 VHCI 虚拟接口对接，不用外接串口 HCI。「协议栈是预编译巨人」的意思：Controller 的代码不开放，你调的是 Host API，出了无线层的问题能查的只有日志与现象。

**Host 二选一**（`bt/Kconfig:12-27` 实取的 choice `BT_HOST`）：

| 栈 | 符号（写对，带 `_ENABLED`） | 默认 | 适用 |
| --- | --- | --- | --- |
| Bluedroid | `CONFIG_BT_BLUEDROID_ENABLED` | **是（choice 默认）** | 双模（含经典蓝牙的芯片） |
| NimBLE | `CONFIG_BT_NIMBLE_ENABLED` | 否 | BLE only，省 RAM |

choice 机制保证互斥；**「NimBLE 是 S3 默认」是错的**——默认是 Bluedroid，S3 选 NimBLE 的真实理由是「没有经典蓝牙可跑，Bluedroid 的双模代码白背」（省内存的幅度数字标待核）。旧材料写的 `CONFIG_BT_NIMBLE`/`CONFIG_BT_BLUEDROID`（无 `_ENABLED`）查不到，照抄是坑。

GATT 的三级容器：service → characteristic → descriptor。订阅 notify 的机制在 CCC 描述符（UUID **0x2902**）：客户端写 0x0001 开通知，服务端在值变化时推送。GAP 的广播：legacy 广播 31 字节 + scan response 31 字节（蓝牙核心规范值）；广播间隔是「省电 vs 被发现速度」的权衡。

![BLE 三层与 GATT 容器：Controller/Host/HCI 与 service/characteristic/descriptor](/arch/wifi-stack.png)

### 四、ESP-NOW：旁路直连

ESP-NOW 复用 Wi-Fi 的 PHY/MAC，不走 AP、不建 socket，peer 互发小包。三步顺序铁律：

```c
esp_now_init();                                  /* wifi init 之后 */
esp_now_peer_info_t peer = { .peer_addr = {..6 字节..},
    .channel = 0, .encrypt = false };            /* channel=0 跟随当前 STA 信道 */
esp_now_add_peer(&peer);
esp_now_send(peer.peer_addr, data, len);
```

四个边界数字（`esp_now.h:29-37` 实取）：MAC 地址 6 字节（`ESP_NOW_ETH_ALEN`）、lmk 密钥 16 字节、单包载荷 **250** 字节（`ESP_NOW_MAX_IE_DATA_LEN`，vendor IE 口径；v2.0 的 **1470** 走 `ESP_NOW_MAX_DATA_LEN_V2`）、**加密 peer ≤6、总 peer ≤20**。混用长度会截断或丢弃。

双回调是 v5.x 的 **info 结构体版**签名（`:120,127` 逐字核对）：`recv_cb(const esp_now_recv_info_t *info, const uint8_t *data, int len)`、`send_cb(const esp_now_send_info_t *info, esp_now_send_status_t status)`——旧版 `(mac_addr, data, len)` 两参签名禁抄。`recv_info`（含 rx_ctrl 与 src_addr）是**回调内临时变量**，头文件原话「it can only be used in the callback」——要存数据先 memcpy。

错误码分诊（`:19,23,27`）：未 init → `ESP_ERR_ESPNOW_NOT_INIT`；peer 没登记 → `ESP_ERR_ESPNOW_NOT_FOUND`；**信道不一致 → `ESP_ERR_ESPNOW_CHAN`**（`:224` 文档实取）。信道规则：没连网走默认信道；连了路由器，信道被锁死，两块板必须同信道（`esp_wifi_get_channel` 对比两板）；初始化顺序 wifi 在前、esp_now 在后。

![ESP-NOW 直连旁路：peer 互发与 Wi-Fi 共存](/anim/esp32-espnow-direct.svg)

![手绘板：Wi-Fi 六步骨架与退避刻度、ESP-NOW 旁路对照（原理示意）](/images/mc32-wifi-espnow.png)

## 测量与证据

| 结论 | 身份 | 判据 |
| --- | --- | --- |
| reason 码值（201/15/202/203/4 弃用） | 手册级（上游已核） | `esp_wifi_types_generic.h:117,131,166-168` |
| 退避序列 1→60 封顶 | 文档推导 | `1000<<n` 序列复算；封顶权衡标待核 |
| Host choice 与默认 Bluedroid | 手册级（上游已核） | `bt/Kconfig:12-27` |
| S3 单模 BLE + BLE 5.0 | 手册级（上游已核） | `soc_caps.h:594-596` |
| ESP-NOW 上限（250/1470/6/20）与 info 签名 | 手册级（上游已核） | `esp_now.h:29-37,118-127` |
| 广播 31+31、CCC 0x2902 | 手册级（规范值） | 蓝牙核心规范 |
| handler 四参签名 | 手册级（上游已核） | `esp_event_base.h:22-24` |
| NimBLE 省 RAM 的幅度 | 来源说法待核 | IDF 文档方向一致，数字未取 |
| 重连耗时/双板互传/测距丢包 | 未实测 | 待回填 |
| `wifi:state:` 日志字样 | 示意口径 | 待上板回填 |

## 失败分支

| 症状 | 第一条假设 | 区分实验 |
| --- | --- | --- |
| `nvs_flash_init` 报错 | 页面写满或格式升级 | 按报错走 erase+reinit 自愈路径 |
| start 后永远收不到 STA_START | 事件循环没建或 handler 没注册 | 检查六步顺序；换 `ESP_EVENT_ANY_ID` 验证 |
| connect 立即失败 | start 是异步的，connect 调早了 | 挪进 STA_START 事件分支 |
| 连不上且 reason=15 | 密码错（四次握手超时） | 重输密码；换认证方式对照 |
| connect 不上 reason=201 | SSID 不存在或信号弱 | 手机热点对照；看路由器列表 |
| BLE 起不来 | 双栈 choice 冲突或符号写错 | `idf.py menuconfig` 查 `BT_HOST`；符号带 `_ENABLED` |
| ESP-NOW 报 CHAN | 两板信道不同 | `esp_wifi_get_channel` 对比；连网的板以路由器为准 |
| recv 回调里取 info 崩溃或数据错 | 把临时变量存下来了 | 回调内 memcpy |
| 发送 1.5 KB 丢一半 | 超 250B 未按 v2 长帧口径 | 对齐 `ESP_NOW_MAX_DATA_LEN(_V2)`；分片 |

## 离开检查

- 六步骨架与「start 异步、connect 等 STA_START」能落到代码顺序。
- reason 201/15/202/203 分诊表能背，4 号码的弃用身份说得清。
- 退避序列能复算，重连逻辑外置到 esp_timer 的理由能讲。
- NVS 自愈路径（erase+reinit）与「校准+MAC 住 NVS」的依赖关系说得清。
- 双栈 choice 的符号名（带 `_ENABLED`）与「默认 Bluedroid」的事实分得清。
- ESP-NOW 三步、四个上限数字、info 版回调签名、临时变量纪律与 CHAN 分诊全部落得到代码。
