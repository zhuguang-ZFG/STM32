---
title: P8 Wi-Fi 精髓：事件循环与连接状态机
status: done
difficulty: 3
minutes: 50
---

# P8 Wi-Fi 精髓：从 esp_wifi_init 到拿到 IP

> 🎯 新手写 Wi-Fi：`esp_wifi_connect()` 之后 `while(1);` 干等，连上了靠运气，断线了干瞪眼。高手只信一件事：**Wi-Fi 是个状态机，事件循环是它的语音播报**。听懂播报（WIFI_EVENT/IP_EVENT），就掌握了联网的第一性原理。

## 本章精髓

1. esp_event 是 IDF 的"神经系统"：事件循环任务（默认 loop）+ 事件基（WIFI_EVENT/IP_EVENT）+ 注册回调：驱动/协议栈出事件，你的代码只响应，不轮询（这就是"事件驱动架构"，与 [P5](05-uart-driver.md) 的驱动事件同思想）。
2. 连接状态机就六个状态：init→config→start→connect→(SCAN_DONE/AUTH/DISASSOC 中间态)→GOT_IP。`WIFI_EVENT_STA_DISCONNECTED` 必须处理**重连策略**，否则路由器一重启设备就永远离线。
3. LwIP 在幕后：拿到 IP 后才有 socket：`IP_EVENT_STA_GOT_IP` 是"网络可用"的唯一合法起点，之前调 connect() 都是空气。

- **能理解**：为什么 handler 运行在事件任务上下文、不能阻塞；为什么断线重连要用任务/定时器外置而不是在 handler 里 sleep。
- **能用**：写出"教科书骨架"六步初始化 + 带指数退避的重连，看懂 `idf.py flash monitor` 日志里的状态迁移。

## 先修

- [F6 事件思想](../rtos/freertos/06-notify-event-timer.md)、[P3 Kconfig](03-idf-anatomy.md)（Wi-Fi 配置项）。

## 先跑起来（10 分钟 quick win）

menuconfig 填上 Wi-Fi 账号密码（示例工程惯例），`idf.py flash monitor`：观察日志从 `wifi:state: init` 到 `got ip` 的完整旅程，把日志与状态机逐条对号入座。

monitor 之前先押趟车：日志从 init 一路走到拿到 IP，这条旅程要停几个大站？押个整数，跑完拿事件全表对号。

## 动画：从 WiFi 握手到 TCP 三次握手

先拿"小区门禁卡"（关联+DHCP 得 IP），再和服务器对暗号：SYN(seq=100) → SYN+ACK(seq=300,ack=101) → ACK(ack=301)。**三次才能证明双向耳聪目明**：序号是防迟到旧报文骗开门的。

![TCP 握手动画](/anim/tcp-handshake.svg)

## 配套视频

<VideoEmbed type="bilibili" id="BV1kV411j7hA" title="一条视频讲清楚 TCP 与 UDP：三次握手与四次挥手（65 万播放，和上图逐帧对照）" />

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 事件循环 | esp_event 架构；默认 loop vs 自建 loop | 库解析 |
| 骨架六步 | 教科书代码逐行；每步的错误码含义 | 代码分析 |
| 事件全表 | WIFI_EVENT_*/IP_EVENT_* 速查与触发时机 | 配置 |
| 重连策略 | DISCONNECTED 的原因码；退避算法实现 | 代码分析 |
| NVS 与校准 | Wi-Fi 为什么需要 NVS（射频校准数据） | 配置 |
| 状态机对照 | 日志级别调高看协议栈内部状态迁移 | 库解析 |

## 一、事件循环：IDF 的"神经系统"

esp_event 是 IDF 所有"异步事务"的统一通道：Wi-Fi、IP、BLE、UART 驱动等都在这里发事件，你的代码注册回调接收：**只响应，不轮询**。这是事件驱动架构（EDA）在 IDF 的落地，与 [P5 UART 驱动](05-uart-driver.md) 的"驱动事件→任务处理"同思想，与 [F6 任务通知/事件组](../rtos/freertos/06-notify-event-timer.md) 同源。

三件套：

- **事件循环任务**（event loop task）：默认 loop 由 `esp_event_loop_create_default()` 创建，跑在一个 FreeRTOS 任务里，所有 handler 在这个任务的上下文执行。
- **事件基**（event base）：`WIFI_EVENT`、`IP_EVENT`、`BLUETOOTH_EVENT` 等，是一组相关事件的"姓氏"。
- **注册回调**：`esp_event_handler_register(WIFI_EVENT, WIFI_EVENT_STA_DISCONNECTED, handler, arg)`，指定"什么基的什么事件"由谁处理。

handler 签名：`void handler(void *arg, esp_event_base_t base, int32_t id, void *data)`，`data` 携带事件特有数据（如 `wifi_event_sta_disconnected_t` 含 reason code）。

**关键纪律**：handler 跑在事件任务上下文，**不能阻塞**。事件任务是单线程的，一个 handler 阻塞（`vTaskDelay(1000)`、等信号量），后续所有事件（别的 handler）都堵在队列里。Wi-Fi 断线了你的重连 handler 睡 1 秒，这 1 秒里 IP 事件、BLE 事件全丢。骨架坑列表第一名的"handler 里阻塞重连"就是这么翻车的。重连等长操作要外置到独立任务或定时器（第四节）。

## 二、骨架六步：教科书初始化

六步长什么样、事件怎么回流，先看图再读代码；顺序铁律就画在实线上。

![Wi-Fi 骨架六步与两条事件回流](/arch/wifi-stack.png)

STA 模式连路由器的标准初始化（六步，每步失败后果列在注释里）：

```c
/* ① NVS：Wi-Fi 校准数据存储（不初始化，esp_wifi_init 直接报错） */
esp_err_t ret = nvs_flash_init();
if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
    ESP_ERROR_CHECK(nvs_flash_erase());   /* NAND 布局变了，擦了重来 */
    ret = nvs_flash_init();
}
ESP_ERROR_CHECK(ret);

/* ② netif：创建默认网络接口（STA 模式） */
ESP_ERROR_CHECK(esp_netif_init());               /* 没有 it，esp_wifi 没有接口可绑 */

/* ③ 事件循环：默认 loop（handler 跑在这） */
ESP_ERROR_CHECK(esp_event_loop_create_default());
esp_netif_create_default_wifi_sta();             /* STA 接口实例 */
wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();

/* ④ 注册回调：在 wifi_init 之前注册，防止漏掉 init/start 事件 */
ESP_ERROR_CHECK(esp_event_handler_register(WIFI_EVENT, ESP_EVENT_ANY_ID, &wifi_handler, NULL));
ESP_ERROR_CHECK(esp_event_handler_register(IP_EVENT, IP_EVENT_STA_GOT_IP, &ip_handler, NULL));

/* ⑤ Wi-Fi 初始化 + 配置 STA */
ESP_ERROR_CHECK(esp_wifi_init(&cfg));
wifi_config_t wifi_cfg = { .sta = { .ssid = CONFIG_WIFI_SSID, .password = CONFIG_WIFI_PASSWORD } };
ESP_ERROR_CHECK(esp_wifi_set_mode(WIFI_MODE_STA));
ESP_ERROR_CHECK(esp_wifi_set_config(WIFI_IF_STA, &wifi_cfg));

/* ⑥ 启动 + 连接 */
ESP_ERROR_CHECK(esp_wifi_start());   /* 触发 WIFI_EVENT_STA_START，handler 里再 connect */
/* connect 不在这调——等 STA_START 事件再调，防止"start 还没好就 connect" */
```

六步的顺序铁律：NVS → netif → event loop → 注册回调 → wifi_init → start。调换任一步，前面那步的依赖没就位：比如 event loop 没建就注册回调，注册直接报错。

SSID/password 用 `CONFIG_WIFI_SSID`（Kconfig 宏）而非硬编码。骨架坑列表的"凭据泄漏事故"靠 menuconfig 注入（[P3](03-idf-anatomy.md) 的 Kconfig 自定义项）。

## 三、事件全表：WIFI_EVENT / IP_EVENT 速查

连接链路上的关键事件（按时间顺序）：

| 事件 | 触发时机 | 典型处理 |
|---|---|---|
| `WIFI_EVENT_STA_START` | esp_wifi_start 完成 | 调 esp_wifi_connect（启动连接） |
| `WIFI_EVENT_STA_CONNECTED` | 关联路由器成功 | 等 DHCP（不直接调 socket） |
| `WIFI_EVENT_STA_DISCONNECTED` | 关联失败/断线 | reason code 判断 + 重连策略 |
| `IP_EVENT_STA_GOT_IP` | DHCP 拿到 IP | 网络可用，可以 socket |
| `IP_EVENT_STA_LOST_IP` | IP 丢失 | 停止网络业务 |

最容易漏的：`WIFI_EVENT_STA_DISCONNECTED` 在**关联失败、认证失败、路由器重启、信号弱**时都会触发：reason code 区分原因（如 201=未找到 AP、15=认证超时、4=关联被拒）。新手只处理 GOT_IP 不处理 DISCONNECTED，路由器一重启设备就永远离线，因为 `esp_wifi_connect` 失败后不会自动重试。

## 四、重连策略：DISCONNECTED 的退避算法

handler 里的重连必须**外置**到定时器或任务，不能 `vTaskDelay` 在 handler 里等（第一节纪律）。指数退避标准写法：

```c
static int retry_count = 0;
static esp_timer_handle_t reconnect_timer;

static void reconnect_now(void *arg) {
    esp_wifi_connect();   /* 定时器回调里调，不在事件 handler 里 */
}

static void wifi_handler(void *arg, esp_event_base_t base, int32_t id, void *data) {
    if (id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();   /* 首次连接 */
    } else if (id == WIFI_EVENT_STA_DISCONNECTED) {
        wifi_event_sta_disconnected_t *e = (wifi_event_sta_disconnected_t *)data;
        ESP_LOGW(TAG, "disconnected, reason=%d", e->reason);
        /* 指数退避：1s/2s/4s/.../60s 上限 */
        int delay_ms = retry_count < 6 ? (1000 << retry_count) : 60000;
        retry_count++;
        esp_timer_start_once(reconnect_timer, delay_ms * 1000);  /* 外置定时器 */
    }
}
```

退避算法：1s→2s→4s→8s→16s→32s→60s（上限），路由器重启期间不会狂重连把 AP 打爆。`reconnect_timer` 用 `esp_timer`（IDF 软件定时器），回调在 esp_timer 任务上下文执行，不堵事件任务。

## 五、NVS 与校准：Wi-Fi 为什么需要 NVS

`nvs_flash_init` 是骨架第一步，不只是存 Wi-Fi 凭据：**射频校准数据**也存 NVS。每颗 ESP32 的射频特性略有差异，出厂时校准数据写进 NVS，Wi-Fi 协议栈启动时读取校准数据补偿射频；没 NVS，Wi-Fi 初始化直接报错（新手第一条报错信息）。

NVS 满了或版本不匹配的处理（骨架第 ① 步）：`ESP_ERR_NVS_NO_FREE_PAGES`（页满了）/`ESP_ERR_NVS_NEW_VERSION_FOUND`（NAND 布局变了，可能是别的固件写的）→ 擦了重来 `nvs_flash_erase()`。擦 NVS 会丢校准数据和凭据，但校准数据会重新生成（首次连时重新校准）。这是 NVS 的"自愈"机制，对照 [S13](../stm32/13-flash-iap.md) 手写 Flash 的"半擦"防御，NVS 把这套防御做进了库。

## 六、状态机对照：日志级别调高看协议栈内部

`idf.py menuconfig` → Component config → Wi-Fi → Log verbosity 调到 Debug/Verbose，连一次路由器看日志：

```text
wifi:state: init                              ← ⑥ start 之前
wifi:state: sta_start                         ← STA_START 事件
wifi:scan:start                               ← 关联前扫描
wifi:state: associate                         ← AUTH 阶段
wifi:state: associated                        ← STA_CONNECTED
wifi:state: got ip:192.168.x.x                ← GOT_IP（网络可用）
```

每行对应状态机一个状态。把日志与第三节的"事件全表"逐行对号入座，Wi-Fi 从"玄学调用"变成"可推理的状态机"。断线时日志会打印 `reason=` 加 reason code，与第四节退避算法的 `e->reason` 对上，这就是分诊的入口。

## 记忆锚点

::: tip 一句话记住
**Wi-Fi 是状态机，事件循环是播报员；GOT_IP 才算联网，DISCONNECTED 必须安排后路。**
:::

**延伸**：TCP 握手动画见 [P8 动画](/anim/tcp-handshake.svg)；Wi-Fi 与低功耗配合见 [P11 低功耗](11-lowpower.md)；ESP-NOW 无网直连见 [P9](09-bt-espnow.md)。

## 实物实验

- 重连实测：连上后重启路由器，日志记录断连检测耗时与重连成功耗时，"可用性"第一次被量化。

## 常见坑

- **handler 里阻塞重连**：事件任务被堵，后续事件全丢，重连用任务/定时器外置。
- **忘 nvs_flash_init**：Wi-Fi 校准数据无处安放，初始化直接报错（新手第一条报错信息）。
- **ssid/password 硬编码进仓库**：凭据泄漏事故，menuconfig/构建注入（P3 的 Kconfig 自定义）。
- **多网卡混淆**：STA+AP 双模时 netif 选错，esp_netif 句柄按模式分清。
- **connect 在 start 后立即调**：start 还没完成，connect 失败，等 STA_START 事件再调。

## 短自测

1. esp_event 的"三件套"是什么？handler 为什么不能阻塞？
<details><summary>参考答案</summary>三件套：事件循环任务（默认 loop，跑在独立 FreeRTOS 任务）、事件基（WIFI_EVENT/IP_EVENT 等一组相关事件）、注册回调（指定基+事件+handler）。handler 跑在事件任务上下文，这个任务是单线程的，一个 handler 阻塞（vTaskDelay/等信号量），后续所有事件（别的 handler）全堵在队列里：Wi-Fi 断线的重连 handler 睡 1 秒，这 1 秒里 IP/BLE 事件全丢。长操作必须外置到独立任务或定时器。</details>

2. 骨架六步的顺序为什么是 NVS→netif→event loop→注册回调→wifi_init→start？
<details><summary>参考答案</summary>每步依赖前面那步：netif 要 event loop（绑接口需要 loop）；event loop 要在注册回调之前建（否则注册报错）；注册回调要在 wifi_init 之前（防止漏掉 init/start 事件）；wifi_init 要 NVS（校准数据）；start 要 wifi_init 完成。顺序错了，前面那步的依赖没就位，直接报错或漏事件。</details>

3. `WIFI_EVENT_STA_DISCONNECTED` 不处理会怎样？reason code 干什么用？
<details><summary>参考答案</summary>不处理则路由器重启/信号弱/关联失败后设备永远离线，esp_wifi_connect 失败后不自动重试。reason code 区分断线原因（201=未找到 AP、15=认证超时、4=关联被拒等），分诊用：找不到 AP 可能是 SSID 错或 AP 没开，认证超时可能是密码错或信号弱，关联被拒可能是 AP 黑名单。</details>

4. 指数退避重连为什么上限设 60s？为什么不直接 1s 固定重连？
<details><summary>参考答案</summary>1s 固定重连在 AP 长时间宕机时会狂打 AP（路由器重启可能要 30s+），且耗电（射频反复唤醒）。指数退避 1→2→4→8→16→32→60 让重连间隔越来越长，AP 恢复后第一次成功重连就复位 retry_count 回到 1s。上限 60s 是"用户可接受的检测延迟"与"省电省 AP"的平衡：产品可调，但别无限退（永远不重连）也别太短（狂打 AP）。</details>

5. 为什么 `esp_wifi_connect` 要在 `WIFI_EVENT_STA_START` 的 handler 里调，而不是 start 之后立即调？
<details><summary>参考答案</summary>esp_wifi_start 是异步的：它启动 Wi-Fi 协议栈后立即返回，但协议栈真正就绪要等 STA_START 事件。start 后立即 connect，协议栈还没就绪，connect 失败或静默无效。在 STA_START handler 里调，保证协议栈就绪后再发起连接，这是事件驱动架构的纪律：每步等事件确认而非等固定延时。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| esp_event 三件套 | IDF `esp_event.h`；与 [P5 UART 驱动](05-uart-driver.md) 事件模型同思想 |
| 骨架六步初始化 | IDF Wi-Fi example `wifi/getting_started/station`；本节第二节 |
| 事件全表 + reason code | IDF `esp_wifi_types.h` WIFI_EVENT_*；ESP-IF WiFi reason codes |
| 指数退避重连 | 本节第四节；esp_timer 外置 |
| NVS 射频校准 | [P10 NVS](10-flash-nvs-ota.md) 机制；nvs_flash_init 第五节 |
| TCP 三次握手 | 动画 [tcp-handshake.svg](/anim/tcp-handshake.svg) + 配套视频 |

## 你做到了

- 联网从"玄学调用"变成"状态机+事件"的可推理系统；
- 断线重连这个 99% 教程跳过的生产问题，你有了解法。

大站点完名：从 init 到拿到 IP 一共六站，日志里一站都不缺席。断线那一站最考验人：默认没人替你重连，路由器一重启，设备就安静掉线。

<div class="achievement">
✅ 下一站：<a href="09-bt-espnow.html">P9 蓝牙与 ESP-NOW</a>：无路由直连的另一种可能。
</div>
