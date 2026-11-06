---
title: P9 蓝牙与 ESP-NOW：协议栈的另一种打开方式
status: done
difficulty: 2
minutes: 40
---

# P9 蓝牙与 ESP-NOW：无路由直连

> 🎯 Wi-Fi 要路由器，蓝牙要配对——而 ESP-NOW 说：两块板子，加电就通。乐鑫自研的这个"轻量直连协议"是遥控器、传感器组网的秘密武器；蓝牙（BLE）则是手机互联的正道。本章把两条路都铺出来。

## 本章精髓

1. 协议栈是"预编译巨人"：Wi-Fi/BT 协议栈以库形式链接，经 **hci/phy** 层与射频硬件对话：你调的是 API，跑的是几 MB 的固件级状态机（这是 ESP 与纯 MCU 的本质差异）。
2. BLE 的主角是 GATT：服务（Service）→ 特征（Characteristic，读/写/通知三种属性）：手机"订阅通知"= 设备主动推送的通道；NimBLE vs Bluedroid 两套主机栈的取舍（体积 vs 功能全）。
3. ESP-NOW 极简模型：无连接、配对靠 MAC、单包 250 字节、动作帧（action frame）传输：**先 esp_now_init 再 add_peer 最后 send**，回调收发送回执；与 Wi-Fi 可共存（同信道协商）。

- **能理解**：为什么 S3 上 NimBLE 比 Bluedroid 更省内存；为什么 ESP-NOW 必须先 add_peer 再 send；为什么连了路由器的板子跑 ESP-NOW 会卡在信道不一致。
- **能用**：两块板完成"按键→灯"隔空互传，看懂 send_cb 的回执计数，能用错误码分诊链路问题。

## 先修

- [P8 Wi-Fi](08-wifi.md)（事件模型复用）、[F4 队列](../rtos/freertos/04-queue.md)（接收回调→任务）。

## 先跑起来（10 分钟 quick win）

两块板各烧本章示例：A 板按用户键，B 板灯翻转，100 行代码内完成"隔空点灯"，成就感拉满。

加电之前先押个没省掉的：免路由直连省掉了路由器和配对，没省掉的是哪一步？押一个再往下读，三步直发里一步都躲不开它。

## 动画：ESP-NOW 三步直发

init → add_peer → send 的顺序铁律、动作帧在两板之间直发、回执包反向飞回，无路由器无握手的"加电即通"，回执失败计数就是链路质量的第一手感。

![ESP-NOW 三步：init → add_peer → send](/anim/esp32-espnow-direct.svg)

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 协议栈架构 | 控制器/主机/hci 分层；NimBLE vs Bluedroid | 库解析 |
| GAP 与广播 | 广播包结构；手机发现设备的全过程 | 配置 |
| GATT 模型 | 服务/特征/描述符；notify 订阅机制 | 库解析 |
| ESP-NOW 三步 | init/peer/send 骨架；发送回调回执 | 代码分析 |
| 双板互传 | 按键→灯完整链路（E07 姊妹实验） | 代码分析 |
| 共存与信道 | ESP-NOW 与 Wi-Fi 同频共存的规则 | 配置 |

## 一、协议栈架构：控制器、主机与 hci 分层

ESP32-S3 的蓝牙是**单模 BLE**（不支持经典蓝牙 Classic BT），符合 BLE 5.0 规范。和 Wi-Fi 一样，协议栈是个"预编译巨人"，分三层：

- **Controller（控制器）**：跑在射频硬件 + ROM/IRAM 固件里，管链路层（打广播、跳频、加密连接），你看不到源码。
- **Host（主机）**：以库形式链接进你的固件，管上层协议（GAP/GATT/L2CAP），**这一层你有两套选**：
  - **NimBLE**（Apache Mynewt 开源）：BLE 专用、轻量，运行时 RAM 占用小，S3 上的首选；
  - **Bluedroid**：历史栈，功能全（在支持 Classic BT 的芯片上能跑经典蓝牙），体积大、API 偏底层。
  二者在 menuconfig 里互斥：`Component config → Bluetooth → Host → NimBLE` 或 `Bluedroid`（Kconfig 符号 `CONFIG_BT_NIMBLE` vs `CONFIG_BT_BLUEDROID`，同启会报错）。S3 既然没有 Classic BT，选 NimBLE 即可——除非你要复用老 Bluedroid 例程。
- **HCI**：SoC 内部 Controller 与 Host 都在同一颗芯片，没有物理 UART HCI 线，走的是 **VHCI**（virtual HCI，软件回调对接）。所以代码里看不到 `/dev/hci0`，调 `esp_bt_controller_init`/`enable` 就把控制器拉起来。

板卡与版本前提（本章事实基准）：立创·实战派 ESP32-S3、ESP-IDF **v5.5.2**；ESP-NOW 头在 `components/esp_wifi/include/esp_now.h`，BT 协议栈在 `components/bt/`。和 [P8 Wi-Fi](08-wifi.md) 一样，蓝牙初始化也要 `nvs_flash_init`：校准数据与 MAC 都存 NVS（同 P8 第一坑）。

## 二、GAP 与广播：手机怎么发现你的板子

GAP（Generic Access Profile）管"发现与连接"，是 BLE 的门面。四个角色：broadcaster（只广播）、observer（只扫描）、peripheral（被连接，板子常当这个）、central（发起连接，手机常当这个）。你的板子要被手机看到，就是当 peripheral 广播。

广播包（advertising packet）是设备在三个广播信道上周期性发的"小名片"，legacy 广播包有效负载 31 字节，另可附 31 字节的 scan response（扫描请求回来再补一份）。BLE 5.0 的扩展广播可以更大，但手机端兼容性以 legacy 为准。名片里塞什么：

| 字段 | 内容 |
|---|---|
| Flags | LE general discoverable 等模式标志 |
| Complete/Incomplete Service UUID | 暴露的服务（让 nRF Connect 这类 app 识别） |
| Local Name | 设备名（如 "My-Bulb"） |
| Manufacturer Data | 厂商自定义（iBeacon 的 UUID 就塞这里） |

广播间隔是个 tradeoff：间隔短→被很快发现但费电；间隔长→省电但手机要扫更久才看到。电池设备常 1s 级，插电设备 100ms 级。手机扫到广播→发连接请求→进入 GATT 阶段（下一节）。这一步和 [P8](08-wifi.md) 的"AP 扫描→关联"是对偶：Wi-Fi 找路由器，BLE 找手机。

## 三、GATT 模型：服务、特征与订阅通知

GATT（Generic Attribute Profile）管"连上之后的数据"，规定了一个**层级容器**：

```
Profile
  └─ Service（UUID 标识）
       └─ Characteristic（UUID + 值 + 属性）
            └─ Descriptor（如 CCC，订阅开关）
```

- **Service**：一组相关特征的集合，用 UUID（16 位如 `0x180F` 电池服务，或 128 位自定义）标识。
- **Characteristic**：数据单元，有 value + properties（读 `READ`、写 `WRITE`/`WRITE_NR`、通知 `NOTIFY`、指示 `INDICATE`）。
- **Descriptor**：特征的元数据，最关键的是 **CCC**（Client Characteristic Configuration，UUID `0x2902`）：手机往这个描述符写 `0x0001` 就开了 notify，写 `0x0000` 关掉。

**notify 是 BLE 的"主动推送"**：设备侧值变了，直接把数据包推给已订阅的手机，手机不用轮询读。这就是本章精髓说的"手机订阅通知=设备主动推送通道"。心率传感器每秒推一次心跳、键盘按下即推键值，都走 notify。

NimBLE 和 Bluedroid 的 GATT API 表面不同（NimBLE 用 `ble_svc_*` 系列声明属性表，Bluedroid 用 `esp_ble_gatts_*` 运行时注册），但**模型完全一样**：服务/特征/描述符三级 + 属性位 + CCC 订阅。学透模型，换栈只是换 API 名。GATT 回调（连接事件、读写请求）也跑在蓝牙任务上下文，**不能阻塞**，长操作入队回任务处理（[F4 队列](../rtos/freertos/04-queue.md) 范式，复用 P5/P8 纪律）。

## 四、ESP-NOW 三步：init / add_peer / send

ESP-NOW 是乐鑫自研的无连接 Wi-Fi 协议，把应用数据塞进 802.11 的 vendor-specific action frame 直发：**不要路由器、不要握手、加电即通**。最小骨架三步（顺序铁律）：

```c
#include "esp_now.h"
#include "esp_wifi.h"

/* ① init：开启 ESP-NOW（依赖 esp_wifi 已 init/start） */
ESP_ERROR_CHECK(esp_now_init());
ESP_ERROR_CHECK(esp_now_register_recv_cb(on_recv));   /* 收 */
ESP_ERROR_CHECK(esp_now_register_send_cb(on_send));   /* 发送回执 */

/* ② add_peer：把对板 MAC 登记进 peer 列表（不登记，send 直接 NOT_FOUND） */
esp_now_peer_info_t peer = {0};
peer.channel = 0;                        /* 0 = 跟随当前 Wi-Fi 信道 */
peer.ifidx   = WIFI_IF_STA;              /* 走 STA 接口 */
peer.encrypt = false;                    /* 不加密；true 时填 lmk[16] */
memcpy(peer.peer_addr, peer_mac, 6);     /* 对板 MAC */
ESP_ERROR_CHECK(esp_now_add_peer(&peer));

/* ③ send：发到指定 peer；peer_addr=NULL 广播给所有 peer */
uint8_t payload = 0x01;
esp_now_send(peer_mac, &payload, sizeof(payload));
```

`esp_now_peer_info_t` 字段（v5.5.2 `esp_now.h` 实测）：`peer_addr[6]`、`lmk[16]`（加密密钥）、`channel`、`ifidx`、`encrypt`、`priv`。两个回调签名也是头里写死的：

```c
typedef void (*esp_now_recv_cb_t)(const esp_now_recv_info_t *info,
                                  const uint8_t *data, int data_len);
typedef void (*esp_now_send_cb_t)(const esp_now_send_info_t *tx_info,
                                  esp_now_send_status_t status);  /* SUCCESS / FAIL */
```

`send_cb` 给你**发送回执**，这正是 ESP-NOW 比"发了就忘"的 UDP 强的地方：回执失败计数 = 链路质量的第一手感（实物实验里"边走边看丢包率"就靠它）。`recv_cb` 里的 `esp_now_recv_info_t` 是栈上临时变量（头文件原话："it can only be used in the callback"），回调返回即失效，要存数据就 memcpy 走，别存指针。

**单包上限**：`ESP_NOW_MAX_DATA_LEN = 250`（v1.0，即动作帧 vendor IE 上限）；v2.0 协议 `ESP_NOW_MAX_DATA_LEN_V2 = 1470`。混网时 v1.0 收 v2.0 长包会截断或丢弃，大文件请自己在应用层分片重组，ESP-NOW 定位是"小数据快通道"不是流。加密 peer 上限 6 个（`ESP_NOW_MAX_ENCRYPT_PEER_NUM`），总 peer 上限 20（`ESP_NOW_MAX_TOTAL_PEER_NUM`）。

## 五、双板互传：按键→灯的完整链路

两块 S3（或一块 S3 + 一块 ESP32）互传，完整链路是 ESP-NOW 的"hello world"，也是姊妹实验 E07 的内容：

1. 两板各自 `esp_wifi_init` + `esp_now_init`，先 `esp_wifi_get_mac(WIFI_IF_STA, mac)` 打印自身 MAC，**人工把对板 MAC 填进 add_peer**（ESP-NOW 认 MAC 不认网，没有 DHCP 自动发现）。
2. A 板：GPIO 按键中断（[P4](04-irq-dualcore.md) 范式）→ 中断里发任务通知 → 任务里 `esp_now_send(B_mac, &toggle, 1)`。
3. B 板：`recv_cb` 收到 1 字节 → memcpy 进队列（[F4 队列](../rtos/freertos/04-queue.md)，回调不办事）→ 任务出队翻转 GPIO 灯。
4. A 板 `send_cb` 记 `ESP_NOW_SEND_FAIL` 次数，这就是你"隔空点灯"失败几次的客观度量。

为什么 recv_cb 要入队、不在回调里直接点灯？和 [P5 UART](05-uart-driver.md) 的中断礼仪同构：回调跑在 esp_now 任务上下文（系统任务），直接 `vTaskDelay` 或长操作会堵住后续收包。回调只 memcpy + 入队，处理交给自己的任务，这是全篇反复出现的"记账不办事"纪律。

整套链路 100 行内能写完，成就感拉满，但更重要的是它把"物联网的网"字第一次具象化：你写的不是 `LED=!LED`，而是 `LED_on_board_B = !LED_on_board_B`，跨空间、无线、可观测回执。

## 六、共存与信道：和 Wi-Fi 同频不打架

ESP-NOW 不另起射频，它复用 Wi-Fi 的 PHY/MAC，所以**和 Wi-Fi 同信道**是它和路由器共存的前提，也是最常见的失败根因。规则：

- **未连 Wi-Fi 时**：ESP-NOW 仍能跑（无连接模式），用默认信道；两块都没连路由器、信道一致即可互通。
- **连了路由器时**：板子的 Wi-Fi 信道被路由器锁死（比如路由器在 6 信道）。这时 `peer.channel = 0` 让对板"跟随当前 STA 信道"，但**对板也得在同一信道**，否则 `esp_now_send` 返回 `ESP_ERR_ESPNOW_CHAN`（头里明确列了这个错误码）。常见坑第二坑就是这个：A 板连了路由器在信道 6，B 板没连、停在信道 1，互相发不出去。
- **STA + ESP-NOW 同启**：照 [P8](08-wifi.md) 骨架六步初始化 Wi-Fi，再 `esp_now_init`，两者共用底层。初始化顺序是 wifi_init/start 在前、esp_now_init 在后（ESP-NOW 依赖 Wi-Fi 已 start）。

排查信道不一致：`esp_wifi_get_channel(&primary, &second)` 打印两板当前信道对比；不一致就调整让对板跟随，或干脆两板都不连路由器走默认信道。这套分诊思路和 P8 的 reason code 分诊同构：错误码是入口，不是终点。

## 记忆锚点

::: tip 一句话记住
**BLE 靠 GATT 立服务，订阅通知主动推；ESP-NOW 认 MAC 不认网，加电即通 250 字节。**
:::

**延伸**：ESP-NOW 三步动画见 [P9 动画](/anim/esp32-espnow-direct.svg)；Wi-Fi 联网在 [P8](08-wifi.md) 展开；BLE 与 Wi-Fi 功耗对比见 [P11 低功耗](11-lowpower.md)。

## 实物实验

- quick win 双板互传 + 测距粗实验：边走边看丢包率（回执失败计数），无线链路质量的第一手感。

## 常见坑

- **NVS 没初始化**：BT 校准/MAC 存储也要 NVS，同 P8 的第一坑。
- **ESP-NOW 与 Wi-Fi 信道不一致**：连了路由器的板子信道被路由器锁死：peer 板要跟随同信道。
- **GATT 回调里做长操作**：蓝牙任务被堵断连：事件入队回任务处理（P5 范式复用）。
- **250 字节上限忘分包**：大图片/文件传输要自分片重组，ESP-NOW 定位是"小数据快通道"。
- **recv_cb 里存 esp_now_recv_info 指针**：头文件原话该结构是回调内局部变量，返回即失效，要存数据 memcpy 走，别存 `info` 指针跨调用用。

## 短自测

1. S3 上蓝牙协议栈为什么要选 NimBLE 而不是 Bluedroid？两套栈的 Kconfig 怎么配？
<details><summary>参考答案</summary>S3 是单模 BLE、没有 Classic BT，Bluedroid"同时支持经典蓝牙"的优势用不上，反而体积大、RAM 占用高。NimBLE 专为 BLE 设计、轻量，是 S3 的首选。menuconfig 走 Component config → Bluetooth → Host，选 NimBLE 或 Bluedroid，对应 Kconfig 符号 CONFIG_BT_NIMBLE / CONFIG_BT_BLUEDROID，二者互斥，同启会报错。要复用老 Bluedroid 例程才切 Bluedroid。</details>

2. BLE 的 GAP 和 GATT 各管什么？手机"订阅通知"具体是往哪个描述符写了什么？
<details><summary>参考答案</summary>GAP 管"发现与连接"：广播、扫描、建立连接、角色（peripheral/central 等）。GATT 管"连上之后的数据"：Service → Characteristic → Descriptor 三级容器。订阅通知是手机往 Characteristic 的 CCC 描述符（UUID 0x2902）写 0x0001 开 notify（0x0000 关），之后设备值变化就主动推给手机，不用轮询。</details>

3. ESP-NOW 的三步顺序为什么必须是 init→add_peer→send？把 add_peer 漏了会怎样？
<details><summary>参考答案</summary>esp_now_init 开启协议栈并建好 peer 列表；add_peer 把对板 MAC 登记进列表（带信道/接口/加密参数）；send 只能给列表里的 peer 发。漏了 add_peer 直接 send，返回 ESP_ERR_ESPNOW_NOT_FOUND（peer 不存在）；顺序倒了（send 在 init 前）返回 ESP_ERR_ESPNOW_NOT_INIT。ESP-NOW 认 MAC 不认网，没有 DHCP 自动发现，必须先登记。</details>

4. ESP-NOW 单包上限是多少？v2.0 有什么变化？要传一张 2KB 的图片怎么办？
<details><summary>参考答案</summary>v1.0 上限 ESP_NOW_MAX_DATA_LEN = 250 字节（vendor action frame IE 上限）；v2.0 提升到 1470 字节。混网时 v1.0 设备收 v2.0 长包会截断或丢弃，所以跨版本别假设对端能收长包。2KB 图片要在应用层自分片（每片不超过 250 字节）+ 序号 + 重组，并处理丢片重传：ESP-NOW 定位是"小数据快通道"，不是文件传输。</details>

5. （开放）A 板连了路由器在信道 6，B 板没连路由器，两板用 ESP-NOW 互发数据失败，从信道角度怎么排查？
<details><summary>参考答案</summary>根因大概率是信道不一致：A 板被路由器锁在信道 6，B 板没连 Wi-Fi 停在默认信道（常为 1），两边不在同一信道，esp_now_send 返回 ESP_ERR_ESPNOW_CHAN。排查：用 esp_wifi_get_channel 打印两板当前 primary 信道对比。解法三选一：① 把 peer.channel 设为对板实际信道；② 两板都不连路由器，走同一默认信道；③ 让 B 板也连同一路由器，自然同信道。和 P8 的 reason code 分诊同构：错误码是入口不是终点。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| 协议栈三层 + NimBLE/Bluedroid | ESP-IDF v5.5.2 `components/bt/`；Kconfig `CONFIG_BT_NIMBLE`/`CONFIG_BT_BLUEDROID` |
| GAP 广播 / GATT 服务模型 | Bluetooth Core Spec 5.0；IDF `bt_host` 层（NimBLE `ble_svc_*` / Bluedroid `esp_ble_gatts_*`） |
| ESP-NOW 全套 API + 错误码 | `components/esp_wifi/include/esp_now.h`（v5.5.2 实测） |
| 单包上限 250 / 1470 | 同上 `ESP_NOW_MAX_DATA_LEN` / `ESP_NOW_MAX_DATA_LEN_V2` |
| peer 结构与加密 | `esp_now_peer_info_t`（lmk[16]/channel/ifidx/encrypt）；加密 peer 上限 6、总 peer 上限 20 |
| 双板互传姊妹实验 | E07（本章实物实验）；IDF `examples/wifi/esp_now/` |
| 共存信道与 ESP_ERR_ESPNOW_CHAN | `esp_now.h` 错误码；与 [P8](08-wifi.md) 信道锁定对偶 |
| 回调入队范式 | [F4 队列](../rtos/freertos/04-queue.md)、[P5 UART](05-uart-driver.md) 中断礼仪 |

## 你做到了

- 无线世界的两条主干道都走过：正规军（Wi-Fi/BLE）与轻骑兵（ESP-NOW）；
- 双板实验成就感达成，物联网的"网"字第一次在你手里具象化。

没省掉的是 add_peer：直发不等于盲发，先把对端的 MAC 登记在册，再开口说话。send 之后也别急着走，回执是链路质量的第一手感，丢包多少它都记着。

<div class="achievement">
✅ 下一站：<a href="10-flash-nvs-ota.html">P10 Flash/分区/NVS/OTA</a>，16MB 的版图管理与永不翻车的升级。
</div>
