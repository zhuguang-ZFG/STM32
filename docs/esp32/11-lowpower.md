---
title: P11 低功耗：睡眠矩阵与 ULP
status: done
difficulty: 2
minutes: 35
---

# P11 低功耗：Deep Sleep 之后，谁还记得你

> 🎯 Wi-Fi 芯片谈低功耗，像让短跑运动员学睡觉。但只要回答三个问题——**睡多深、谁叫醒、醒来还剩什么**——电池供电的 ESP32 产品就成立。Deep Sleep 下电流做到 µA 级，ULP 协处理器替你站岗。

## 本章精髓

1. **两档睡眠**。Light sleep 只是 CPU 暂停，RAM 保持、外设可唤醒，毫秒级回神。Deep sleep 把数字域整个断电，只留 RTC 域，电流降到 µA 级。
   代价是：**Deep sleep 醒来 = 复位重启**，程序从 `app_main` 重新跑。对照 [S14](../stm32/14-pwr.md) 的 Sleep/Stop/Standby 三档，ESP 少一档、但把 RTC 域这场戏演得更重。
2. **唤醒源有五路**：定时器 `esp_sleep_enable_timer_wakeup`、GPIO（EXT0/EXT1）、触摸、UART、ULP。
   选哪一路，决定了产品怎么设计：定时上报就选定时器，按键唤醒就选 EXT。
3. **ULP 是守夜人**。主核睡死时，这颗超低功耗小核还在跑。它能读 ADC/I2C、能数脉冲，只有达到阈值才把主核叫醒。
   这是电池产品的终极省电手段（本章简介 FSM 与 RISC-V 两代 ULP）。

- **能理解**：为什么 Deep sleep 唤醒=复位重启（数字域断电，CPU/RAM 全没）；为什么 EXT0/EXT1 只能用 RTC GPIO（普通 GPIO 在数字域，断电就废）；为什么 Wi-Fi 没关就睡电流下不来（射频/协议栈还在跑）。
- **能用**：写出周期上报器的六步骨架（醒来→采→连→发→关 Wi-Fi→睡）。用 `RTC_DATA_ATTR` 跨复位保存计数，用 `esp_sleep_get_wakeup_cause` 判断这次为什么醒来。

## 先修

- [S14 低功耗](../stm32/14-pwr.md)（对照）、[P10 NVS](10-flash-nvs-ota.md)（持久化分工）。

## 先跑起来（10 分钟 quick win）

`esp_sleep_enable_timer_wakeup(5s)` + `esp_deep_sleep_start()`：5 秒后自动复位，串口打印 RTC 内存里的计数，睡-醒循环第一次跑通。

睡前先押份遗产：Deep Sleep 五秒醒来，普通全局变量还认得你吗？押认得或失忆，再看串口。这一觉的账单，比你想的重。

## 动画：睡眠矩阵与唤醒路径

Light 与 Deep 的四列差异、RTC 内存的“遗言”、ULP 守夜人：Deep 阶段数字域 CPU/SRAM 变灰断电，boot_count 跨复位累加，唤醒箭头周期射入。

![ESP32 睡眠矩阵：Light 眯一会 · Deep 睡死 · ULP 守夜](/anim/esp32-sleep-matrix.svg)

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 睡眠矩阵 | Light/Deep 四列对照；与 STM32 三档对表 | 配置 |
| RTC 内存与慢速内存 | RTC_DATA_ATTR/RTC_SLOW 的存放规则 | 代码分析 |
| 唤醒源配置 | 定时器/EXT0/EXT1/触摸/UART 逐个 | 配置 |
| 周期上报器 | 醒来→采数据→发 Wi-Fi→再睡的完整骨架 | 代码分析 |
| ULP 概念 | 两代 ULP 能力；适用场景与开发流程地图 | 库解析 |
| 电流实测 | 三档电流记录与续航估算（CR2032/18650 两例） | 代码分析 |

## 一、睡眠矩阵：Light vs Deep 四列对照

ESP32 的睡眠分两档：Light sleep 与 Deep sleep。它们大致对应 [S14 STM32](../stm32/14-pwr.md) 的 Stop 与 Standby。先看四列对照：

| 维度 | Light sleep | Deep sleep |
|---|---|---|
| CPU | 暂停（时钟门控） | 断电 |
| RAM | 保持 | 断电（数字域 RAM 全失） |
| 外设 | 大多保持，可配置 | 数字域外设断电，仅 RTC 域活 |
| 唤醒方式 | GPIO/定时器/UART 等任意外设 | 仅 RTC 域唤醒源（Timer/EXT0/EXT1/Touch/UART/ULP） |
| 唤醒后 | 从暂停点继续执行 | = 复位重启（setup() 从头） |
| 电流 | 几 mA 量级 | µA 级 |
| 回神时间 | ms 级 | ms 级（外加复位重启代价） |

哲学与 S14 一致：睡得越深，省得越多，但醒来代价越大。STM32 三档里，ESP 的 Light ≈ Stop（RAM 保持、外设部分活），ESP 的 Deep ≈ Standby（域断电、靠 RTC 留遗言）。差别在于 ESP 没有对应 STM32 Sleep 的那一档。STM32 的 Sleep 只停 CPU、外设全活；ESP 的"轻睡"默认连射频一起关（Modem sleep）。两者省电根本不是一个量级。

关键认知：**Deep sleep 唤醒 = 复位重启**。`setup()` 从头跑一遍，全局变量全丢（除非放 RTC 内存）。这是新手最大的认知颠覆："我刚才不是还在跑吗？怎么又 setup 了？"因为数字域 RAM 失电了，CPU 从复位向量重新启动。Light sleep 不一样：从 `esp_light_sleep_start()` 下一行继续跑，像 `vTaskDelay` 一样。

## 二、RTC 内存与慢速内存：跨 Deep sleep 的"遗言"

Deep sleep 会断掉整个数字域 RAM，但 RTC 域还活着。RTC 域里有一块 RTC slow memory，专门用来存"跨睡眠还想过夜"的状态。IDF 用属性宏把变量放进这块内存。只要给变量加个宏，它就住在 RTC 域里：

```c
RTC_DATA_ATTR int boot_count = 0;   /* 跨 Deep sleep 保持；仅上电冷启动才清零 */

void app_main(void) {
    boot_count++;
    printf("第 %d 次从 Deep sleep 醒来\n", boot_count);
    esp_sleep_enable_timer_wakeup(5 * 1000000ULL);  /* 5s */
    esp_deep_sleep_start();
    /* 不会到这里——Deep sleep 后复位 */
}
```

`RTC_DATA_ATTR`：变量放进 RTC slow memory。Deep sleep 期间保持；**只有上电（冷启动）才清零**，看门狗复位同样保持。所以 `boot_count` 每次 Deep sleep 醒来 +1，能跨复位累计。

存放规则速查：

| 属性 | 位置 | 跨 Deep sleep | 跨冷启动 |
|---|---|---|---|
| `RTC_DATA_ATTR` | RTC slow memory | 保持 | 复位为 0 |
| `RTC_NOINIT_ATTR` | RTC slow memory | 保持 | **不初始化**（脏值） |
| `RTC_SLOW_ATTR` | RTC slow memory（同 RTC_DATA） | 保持 | 复位为 0 |
| `RTC_FAST_ATTR` | RTC fast memory | 保持 | 复位为 0 |
| 普通全局变量 | 数字域 SRAM | **失电** | 复位为 0 |

`RTC_NOINIT_ATTR` 用途：调试时想看上一次 crash 时的变量值（不被复位清零），但脏值风险大：除非你确定要这个语义，否则用 `RTC_DATA_ATTR`。

容量注意：RTC slow memory 8 KB 量级（具体看 TRM），ULP 程序也住这里：ULP 用得多留给主核的就少，规划时要权衡。

## 三、唤醒源配置：五种主流唤醒

Deep sleep 只能被 RTC 域唤醒源叫醒（普通 GPIO 在数字域，断电就废了）。主流唤醒源有五种，逐个看：

**1. 定时器唤醒**（最常用，周期上报）：

```c
esp_sleep_enable_timer_wakeup(5 * 1000000ULL);  /* 5s = 5,000,000 µs */
esp_deep_sleep_start();
```

参数是微秒（`uint64_t`），常量要带 `ULL` 后缀防 32 位溢出（5s 在 32 位内没事，但 1 小时 = 3.6e9 µs 就溢出了）。

**2. EXT0 唤醒**（单 RTC GPIO，电平触发）：

```c
esp_sleep_enable_ext0_wakeup(GPIO_NUM_0, 0);  /* GPIO0 拉低唤醒（BOOT 键） */
```

一个 RTC GPIO，指定电平（0 或 1），到了就醒。适合"按键唤醒"单脚场景。

**3. EXT1 唤醒**（多 RTC GPIO，组合触发）：

```c
/* 位掩码：GPIO 0 | GPIO 2，任一高电平唤醒 */
esp_sleep_enable_ext1_wakeup(BIT64(GPIO_NUM_0) | BIT64(GPIO_NUM_2), ESP_EXT1_WAKEUP_ANY_HIGH);
```

位掩码用 `BIT64(n)`（GPIO 编号可能 ≥ 32，所以用 64 位掩码）。模式两种：`ESP_EXT1_WAKEUP_ANY_HIGH`（任一高）、`ESP_EXT1_WAKEUP_ALL_LOW`（全部低）。醒来后用 `esp_sleep_get_ext1_wakeup_status()` 查是哪只脚触发的。

**4. 触摸唤醒**（触摸传感器在 RTC 域）：

```c
touch_pad_init();
/* 配置触摸阈值... */
esp_sleep_enable_touchpad_wakeup();
```

触摸传感器是 RTC 域外设，Deep sleep 也能跑。适合"触摸按键唤醒"产品。

**5. UART 唤醒**（特定模式）。

```c
esp_sleep_enable_uart_wakeup(0);  /* UART0 收到一定数量字节唤醒 */
```

UART 唤醒主要用在 Light sleep。Deep sleep 下的 UART 唤醒能力有限，且因芯片而异（详见 TRM）。本章不展开，配置见 [E06](../lab/e06-lowpower-current.md)。

唤醒后分诊原因（任何低功耗产品必做）：

```c
esp_sleep_wakeup_cause_t cause = esp_sleep_get_wakeup_cause();
switch (cause) {
    case ESP_SLEEP_WAKEUP_TIMER:    printf("定时器叫醒\n"); break;
    case ESP_SLEEP_WAKEUP_EXT0:     printf("EXT0 GPIO 叫醒\n"); break;
    case ESP_SLEEP_WAKEUP_EXT1:     printf("EXT1 GPIO 叫醒，pin=0x%llx\n", esp_sleep_get_ext1_wakeup_status()); break;
    case ESP_SLEEP_WAKEUP_TOUCHPAD: printf("触摸叫醒\n"); break;
    case ESP_SLEEP_WAKEUP_UART:     printf("UART 叫醒\n"); break;
    case ESP_SLEEP_WAKEUP_ULP:      printf("ULP 叫醒\n"); break;
    case ESP_SLEEP_WAKEUP_UNDEFINED: printf("冷启动（首次上电）\n"); break;
}
```

`ESP_SLEEP_WAKEUP_UNDEFINED` 是冷启动（首次上电或外部复位），区别于"Deep sleep 醒来"，新设备首次跑要识别这个状态走不同分支。

## 四、周期上报器：醒来→采数据→发 Wi-Fi→再睡

电池 IoT 产品的经典骨架：每 N 分钟醒一次，采传感器、连 Wi-Fi、上报、断 Wi-Fi、再睡。完整代码骨架：

```c
RTC_DATA_ATTR int cycle = 0;   /* 跨 Deep sleep 累计周期数 */

void app_main(void) {
    /* ① 分诊：是不是 Deep sleep 醒来 */
    if (esp_sleep_get_wakeup_cause() == ESP_SLEEP_WAKEUP_TIMER) {
        printf("第 %d 次周期醒来\n", ++cycle);
    } else {
        printf("冷启动，cycle 复位\n");
        cycle = 0;
    }

    /* ② 采数据（这里读 ADC/传感器） */
    int sensor_val = read_sensor();

    /* ③ 连 Wi-Fi（用 P8 骨架六步，这里简化） */
    wifi_connect_blocking();   /* 阻塞等到 GOT_IP */

    /* ④ 上报（HTTP/MQTT/ESP-NOW 任选） */
    report_to_server(sensor_val);

    /* ⑤ 关 Wi-Fi（射频必须关，否则电流下不来） */
    esp_wifi_disconnect();
    esp_wifi_stop();           /* 协议栈停 */
    /* 可选：esp_wifi_deinit() 释放更多资源 */

    /* ⑥ 配置下次唤醒 + 睡 */
    esp_sleep_enable_timer_wakeup(10 * 60 * 1000000ULL);  /* 10 分钟 */
    esp_deep_sleep_start();    /* 不会返回 */
}
```

六步铁律：分诊→采→连→发→**关 Wi-Fi**→睡。第 ⑤ 步是新手最容易漏的：Wi-Fi 协议栈还在跑就 Deep sleep，射频/协议栈状态机乱了，电流也下不来（见常见坑）。`esp_wifi_stop()` 之后再睡，醒来重新 `esp_wifi_start()`（在 wifi_connect_blocking 里）。这是低功耗与 [P8 联网骨架](08-wifi.md) 的拼装点。

`wifi_connect_blocking()` 的实现：在 P8 事件骨架基础上用信号量等 `IP_EVENT_STA_GOT_IP`，主任务等信号量，事件 handler 给信号量。这是"事件驱动 + 同步等待"的标准拼装。

续航估算（只算量级）。假设活跃 200 mA 持续 2 秒（连接+发送），Deep sleep 10 µA 持续 600 秒，平均电流 ≈ 200mA·2s/602s + 10µA·600s/602s ≈ 0.68 mA。CR2032（约 220 mAh）续航 ≈ 220/0.68 ≈ 323 小时 ≈ 13 天。如果唤醒间隔拉到 1 小时，平均电流降到约 0.11 mA，续航约 90 天。**唤醒间隔越长，Deep sleep 占比越高，续航越长**：这是电池 IoT 产品的核心设计杠杆。具体数值以 datasheet §Power consumption 与 [E06 实测](../lab/e06-lowpower-current.md) 为准。

## 五、ULP 协处理器：守夜人

主核进入 Deep sleep 后，ULP 协处理器仍在 RTC 域里运行。这颗超低功耗小核就是电池产品的"守夜人"：周期性醒来读 ADC/I2C、数脉冲，达到阈值才唤醒主核。主核能睡得更久（不用频繁醒来轮询），ULP 的 µA 级功耗远低于主核频繁唤醒的 mA 级。

两代 ULP：

| 维度 | ULP（FSM，原始） | ULP-RISC-V（S2/S3） |
|---|---|---|
| 架构 | 有限状态机（汇编宏） | RISC-V 核心 |
| 编程 | `ulp_process_macros`（宏汇编） | C/RISC-V 工具链 |
| 算力 | 极弱（FSM 级指令集） | 弱但有 C 编译器 |
| 能访问 | RTC GPIO、ADC、I2C（专用指令） | RTC GPIO、ADC、I2C |
| 唤醒主核 | SW 中断 | SW 中断 |

ULP（FSM）的"程序"是一组宏汇编指令，编译后放进 RTC slow memory，主核睡后 ULP 周期性执行。开发流程地图（FSM 版）：

1. 用 `ulp_process_macros` 写宏汇编（读 ADC、比较、条件唤醒）
2. 程序加载到 RTC 内存（链接脚本与 `ulp_load_binary`）
3. 配置 ULP 唤醒周期（`ulp_set_wakeup_period`）
4. 主核 `esp_deep_sleep_start()`，ULP 自动接管

ULP-RISC-V（S2/S3）更现代：直接用 C 写，有 GCC 工具链，算力稍强，但还是"哨兵"定位，别拿它跑业务。

适用场景地图：

- **用 ULP**：主核要长时间睡、但有"阈值触发"需求（ADC 超阈值、按键长按、计数脉冲到 N），ULP 替你站岗，达到条件才叫醒主核。
- **不用 ULP**：周期性定时上报（用 Timer 唤醒即可）；唤醒条件简单（按键电平变化用 EXT0），ULP 开发复杂度不值得。
- **别让 ULP 干业务**：ULP 算力/内存极小（RTC slow memory 几 KB），它只适合"读-比-唤醒"哨兵循环，跑业务逻辑会爆。

## 六、电流实测：三档记录与续航估算

[P8 骨架](08-wifi.md) 拿到逻辑通了，但低功耗产品要拿电流表说话。[E06 实验](../lab/e06-lowpower-current.md) 用万用表 µA 档（或 Power Profiler）测三档电流：

| 档位 | 测点 | 量级 | 备注 |
|---|---|---|---|
| 活跃（连 Wi-Fi TX） | 工作电流峰值 | 数百 mA 峰值 | 射频突发，看示波器波形 |
| 活跃（待机，不连） | 平均电流 | 数十 mA | 主核在跑、射频待机 |
| Light sleep | 平均电流 | 几 mA | Modem sleep 关射频 |
| Deep sleep | 平均电流 | µA 级 | 仅 RTC 域 |
| Deep sleep + ULP | 平均电流 | 几十 µA 起 | ULP 周期活动 |

具体数值以 datasheet §Power consumption 与 E06 实测为准（不编造）。实测要点：

1. **量程切换**：活跃用 mA 档、Deep 用 µA 档，手动切换：直接用 µA 档测活跃会被瞬间电流冲爆（保险丝烧）。
2. **测点选电源脚**：测 3V3 进线电流，别测 USB（USB 走了板载 LDO/CP2102，漏电大，不准）。
3. **断掉 USB 调试**：USB CDC 跑着电流下不来：测 Deep sleep 要拔 USB，用电池/外部 3V3 供电。

续航估算两例（量级）：

- **CR2032 纽扣电池**（约 220 mAh）：唤醒间隔 1 小时、活跃 2s@200mA、Deep 10µA → 平均约 0.11 mA → 续航约 90 天。适合"低频上报"产品（环境监测、门磁）。
- **18650 锂电**（约 2500 mAh）：唤醒间隔 10 分钟、活跃 2s@200mA、Deep 10µA → 平均约 0.68 mA → 续航约 150 天。适合"中频上报"加较大体积产品。

注意：实测续航要打"折扣"：板载 LDO 漏电、传感器静态电流、外设未关都吃电。理论续航是上限，实际产品要逐项掐电（每颗芯片的使能脚、上拉电阻值、外设电源开关）。

## 记忆锚点

::: tip 一句话记住
**Light 眯一会（记忆在），Deep 睡死（靠 RTC 留遗言），ULP 守夜看门——唤醒即复位，状态藏 RTC。**
:::

**延伸**：ESP32 睡眠矩阵动画见 [P11 动画](/anim/esp32-sleep-matrix.svg)；STM32 低功耗对照见 [S14](../stm32/14-pwr.md)；RTC 与 NVS 数据保持见 [P10](10-flash-nvs-ota.md)。

## 实物实验

- 周期上报器 + 电流三档实测；进阶：GPIO 唤醒（用户键）与定时唤醒并存，分辨唤醒原因（esp_sleep_get_wakeup_cause）。

## 常见坑

- **Deep sleep 后找变量**：普通 RAM 已失电，跨 sleep 状态必须 RTC_DATA_ATTR 或 NVS。
- **Wi-Fi 没关就睡**：射频/协议栈在跑，电流下不来：睡前 esp_wifi_stop/disconnect。
- **GPIO 唤醒脚选错**：Deep sleep 只有 RTC GPIO 能唤醒，查 TRM 的 RTC 引脚清单。
- **ULP 当主核用**：ULP 算力/内存极小，它只适合做"阈值哨兵"，别让它干业务。

## 短自测

1. Light sleep 和 Deep sleep 在"RAM/外设/唤醒方式/唤醒后状态"四列的差异是什么？
<details><summary>看答案</summary>Light sleep：CPU 暂停（时钟门控）、RAM 保持、外设大多保持可配置、唤醒后从暂停点继续执行（像 vTaskDelay 醒来），电流几 mA。Deep sleep：CPU 断电、RAM 断电（数字域全失）、外设仅 RTC 域活、唤醒=复位重启（setup() 从头跑），电流 µA 级。本质区别是"RAM 保持还是断电"，决定了醒来是"继续"还是"重来"。</details>

2. 为什么 Deep sleep 唤醒=复位重启？普通全局变量为什么会丢？
<details><summary>看答案</summary>Deep sleep 把数字域（CPU、SRAM、大多数外设）电源全断了，只留 RTC 域。CPU 没时钟没电源，重新上电时从复位向量启动，等于一次冷复位，setup()/app_main() 从头跑。普通全局变量存在数字域 SRAM，断电即失电，醒来后 RAM 是"全新"的，变量全复位为 0。要跨 Deep sleep 保持状态，必须用 RTC_DATA_ATTR 把变量放进 RTC slow memory（RTC 域不断电），或写 NVS（Flash，永久）。</details>

3. EXT0/EXT1 唤醒为什么只能用 RTC GPIO？普通 GPIO 不行吗？
<details><summary>看答案</summary>Deep sleep 期间数字域断电，普通 GPIO 的输入检测电路也在数字域，断电就检测不了电平变化。只有 RTC GPIO（GPIO 多路复用器接到 RTC 域的引脚）在 Deep sleep 时还有电，能检测电平变化触发唤醒。所以选唤醒脚必须查 TRM 的 RTC GPIO 清单，不是任意 GPIO 都能 EXT0/EXT1 唤醒。</details>

4. 周期上报器的六步铁律里，"关 Wi-Fi"（esp_wifi_stop）这一步为什么不能省？
<details><summary>看答案</summary>Wi-Fi 协议栈和射频在 Deep sleep 前没停：状态机还在跑，射频可能还在 Beacon 唤醒周期。直接睡下去会有两个后果。其一，协议栈状态会乱，醒来 `start` 时报错或重连失败。其二，射频和协议栈的功耗会把 Deep sleep 的 µA 级拉高到 mA 级，省电效果全部作废。esp_wifi_disconnect 加 esp_wifi_stop 把协议栈停干净，醒来重新 start，干净利落。</details>

5. ULP 适合做什么、不适合做什么？为什么主核睡死时 ULP 还能跑？
<details><summary>看答案</summary>ULP 适合"阈值哨兵"，周期性读 ADC/I2C、数脉冲、比较阈值，达到条件才唤醒主核。主核能睡更久不用频繁醒来轮询，ULP 的 µA 级远低于主核频繁唤醒的 mA 级。不适合跑业务逻辑：ULP 算力/内存极小（RTC slow memory 几 KB），FSM 版只有有限指令集，RISC-V 版虽有 C 编译器但仍弱。主核睡着时 ULP 还能跑，原因在供电分区：ULP 在 RTC 域，数字域断电不影响它。ULP 周期性执行 RTC slow memory 里的程序，满足条件就通过 SW 中断唤醒主核（主核走复位重启）。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| Light/Deep 睡眠矩阵 | IDF `esp_sleep.h`；对照 [S14 STM32 低功耗](../stm32/14-pwr.md) 三档 |
| RTC 内存属性 | `RTC_DATA_ATTR`/`RTC_NOINIT_ATTR`/`RTC_SLOW_ATTR`/`RTC_FAST_ATTR`（IDF `esp_attr.h`） |
| 五种唤醒源 | `esp_sleep_enable_*_wakeup` 系列；唤醒原因 `esp_sleep_get_wakeup_cause` |
| 周期上报器骨架 | 本节第四节；与 [P8 Wi-Fi 骨架](08-wifi.md) 拼装 |
| ULP 协处理器 | IDF `ulp/` 目录；FSM（`ulp_process_macros`）+ RISC-V（S2/S3） |
| 电流实测 | [E06 实验](../lab/e06-lowpower-current.md)；datasheet §Power consumption |

## 你做到了

- 电池供电 ESP32 产品的全套低功耗工具到手；
- S/P 两篇低功耗观完成对照："睡觉"这门学问你现在是双学位。

遗产清点：醒来即复位，普通变量全体失忆，活下来的只有 RTC 域里那份记账。真做周期上报的产品，睁眼第一件事是问"昨晚谁叫的我"，把唤醒原因分诊清楚，再决定这一轮干什么。

<div class="achievement">
✅ 下一站：<a href="12-audio-path.html">P12 音频链路</a>：ES8311+ES7210，小智板的看家本领，从 I2S 时序到"hello 语音"。
</div>
