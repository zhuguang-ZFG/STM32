---
title: P13 看门狗与健康监督：不要喂反了
status: done
difficulty: 3
minutes: 45
---

# P13 看门狗与健康监督：不要喂反了

> 🎯 FreeRTOS 的任务都还在被调度，但采集任务已经半分钟没交过一份结果。TWDT 默认只盯空闲任务，它看得出来吗？

## 本章精髓

1. **调度正常不等于工作完成**：TWDT 默认只订阅每个核的空闲任务，只能发现"有任务霸占 CPU 不让出"。任务按时让出 CPU、却一直没完成工作，它发现不了。本例额外注册一个名为 health 的 user，只有 [S17](../stm32/17-watchdog-reset.md) 的那份 health 模块判定全部按期，监督任务才替它 reset。
2. **条件写反就是没装狗**：`health_supervise` 返回 true 才 `reset_user`；返回 false 表示"该停喂了"。停止监督也不能 `delete_user`，删掉被监视的对象等于取消了超时来源。
3. **跨核共享要真正的锁**：worker、通信、监督三个任务可能在两个核上跑。C 的 volatile 不提供互斥，也不保证一致的快照。`portMUX` 自旋锁保护 health 状态，而且要**拿到锁之后再读时间**。

- **能理解**：为什么注册一个 user 而不是把每个任务都 `esp_task_wdt_add`；为什么 `init` 返回 `ESP_ERR_INVALID_STATE` 时要改用 `reconfigure`；为什么用 OpenOCD 调过的板子要重新上电才能测看门狗。
- **能用**：分别构建普通固件和故障固件；用 `fault` 命令停掉 worker 或监督，按时间预算预测复位时刻，用默认控制台的复位日志核对。

## 先修

- 必需：[P4 中断与双核](04-irq-dualcore.md)、[F8 FreeRTOS F407 移植](../rtos/freertos/08-port-f407.md)、[C8 串口协议](../c/08-framed-protocol.md)。
- 建议先读 [S17 看门狗](../stm32/17-watchdog-reset.md)：health 模块的期限、宽限期和锁存在那里讲过，本章直接复用。

## 先跑起来（10 分钟 quick win）

在 IDF 5.5.2 环境里：

```sh
cd code/esp32/07-watchdog-health
idf.py set-target esp32s3
idf.py build flash monitor -p COMx      # 端口必须显式指定
```

flash 之前先押个盲区：worker 任务回回都乖乖让出 CPU，调度器无可挑剔，可它半分钟没交过一份数据，默认的 TWDT 会叫吗？押会或不会，第一屏日志见分晓。

默认控制台第一屏会打出一行 `reset=… retained=0 overdue=0`：普通上电时没有有效的历史记录。接着在仓库根用数据口（GPIO10/11）查状态：

```sh
python3 scripts/device-console.py status --port COMy
```

隔几秒再查一次，运行毫秒在涨、过期 mask 为 0。主机一个字节都不发，系统也应保持健康。

## 动画：TWDT 订阅、喂狗与超时链条

worker 上报进展、supervisor 巡检确认、reset_user 喂狗、TWDT 两秒倒数——喂狗脉冲还在闪就没有超时；fault 注入后链条断在哪一环，一图看完。

![ESP32 任务看门狗：TWDT 的订阅、喂狗与超时链条](/anim/esp32-twdt-chain.svg)

## 板卡事实

- 立创实战派 S3 的 GPIO2 是板载 I2C 的 SCL。本例不驱动 GPIO2 做"心跳灯"，免得和板上 I2C 器件打架。
- 数据口 UART1：GPIO10 TX、GPIO11 RX，和 [C8](../c/08-framed-protocol.md) 相同。文本日志走默认控制台，不混入数据口。
- TWDT 基于定时器组 0 的 MWDT，IWDT 基于定时器组 1 的 MWDT（IDF 5.5.2 Watchdogs 文档）。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、S3 的四种看门狗 | RTC_WDT / IWDT / TWDT / XTWDT 各管什么 | 配置 |
| 二、订阅模型 | 订阅任务 vs 注册 user；本例为什么只要一个 user | 库解析 |
| 三、跨核共享 | portMUX、锁内读时间、锁外 reset | 代码分析 |
| 四、初始化 | init / reconfigure、三个配置字段、panic 行为 | 配置 |
| 五、故障注入与时间预算 | 两种故障、两条时间线 | 代码分析 |
| 六、复位原因与 RTC 记录 | `esp_reset_reason` + `RTC_NOINIT_ATTR` | 代码分析 |
| 七、OpenOCD 与看门狗 | 断点会关掉看门狗，而且不再打开 | 引脚 |

## 一、S3 的四种看门狗

![S3 四种看门狗：RTC/IWDT/TWDT/XTWDT 各管一段](/figures/esp32-13-four-wdt.svg)

| 看门狗 | 监督什么 | 谁喂 | 本例 |
|---|---|---|---|
| RTC_WDT | 上电到用户 `app_main` 之前的启动过程 | 引导代码；默认在进入用户主函数前关闭 | 不动 |
| IWDT（中断看门狗） | 中断是不是被长时间屏蔽、ISR 是不是跑太久 | 每个核的 FreeRTOS tick 中断 | 保持默认开启 |
| **TWDT（任务看门狗）** | 订阅的任务/用户是否在期限内报到 | 被订阅者自己调 `reset` / `reset_user` | **本章主角** |
| XTWDT | 外部 32kHz 晶振是否停振 | 硬件 | 未启用 |

（依据：IDF 5.5.2 *Watchdogs* 文档。）

IWDT 和 TWDT 的分工要分清。IWDT 管的是"中断还能不能及时跑"：临界区太长、ISR 里死等，都会让 tick 中断进不来，触发 IWDT。TWDT 管的是"任务有没有按时完成"。本例故意让故障任务**继续调用 `vTaskDelay` 让出 CPU**，这样触发的一定是 TWDT 的 health user，而不是空闲任务饿死或 IWDT。

## 二、订阅模型：一个 user，而不是三个任务

TWDT 有两种订阅方式：

- `esp_task_wdt_add(task)`：订阅一个任务，这个任务自己调 `esp_task_wdt_reset()`；
- `esp_task_wdt_add_user("health", &handle)`：注册一个用户，拿到句柄，由谁调 `esp_task_wdt_reset_user(handle)` 都行。

最省事的写法是把 worker 和通信任务直接 `add`，各自 reset。本例没这么做，原因有三个：

1. **每个任务一个期限。** TWDT 只有一个全局超时（这里是 2000ms）。health 模块给每个任务单独设期限（这里都是 500ms，可以各不相同），还有上电宽限期和锁存。
2. **能说出是谁超时。** STATUS 的过期 mask 和 RTC 记录都能告诉主机"是 worker 还是通信"。只靠 TWDT，复位前打出的 backtrace 里才有这个信息。
3. **和 F407 共用一份代码。** `health.c` 在 S17 里驱动 IWDG/WWDG，在这里驱动 TWDT，判定逻辑完全相同，主机上测一次就够了。

那监督任务自己卡死了怎么办？它不再调 `reset_user`，health user 的超时照样到期。所以必须**单独注册一个由监督任务负责的 user**：主管自己出问题时，也要有一个没人刷新的超时来源。

停止监督的故障（`fault 2`）也不能写成 `esp_task_wdt_delete_user`。删掉 user，TWDT 就不再等它，超时来源没了，系统反而不会复位。正确的表现是：user 保持注册，但没人再 reset 它。

## 三、跨核共享：锁内读时间，锁外喂狗

三个任务都用 `xTaskCreate` 创建，没有绑核，调度器可能把它们放到两个核上同时跑。共享的东西有 `health`、`supervisor`、`service` 和几个故障标志，全部用一个 `portMUX_TYPE` 保护：

```c
static portMUX_TYPE mux=portMUX_INITIALIZER_UNLOCKED;
static void progress(uint8_t id){
    portENTER_CRITICAL(&mux);
    health_progress(&health,id,now_ms());   /* 先拿锁，再读时间 */
    portEXIT_CRITICAL(&mux);
}
```

S3 上的 `portENTER_CRITICAL` 做两件事：关掉**当前核**的中断，然后自旋等另一个核释放锁。所以有两条规矩。

**锁内要短。** 临界区关中断，正好是 IWDT 要抓的东西（"Critical Sections (also disables interrupts)"）。本例最长的一段是通信任务：一轮最多喂 128 字节给接收状态机，再做一次超时检查。这是有界的；不能在锁里调 `uart_read_bytes`、`vTaskDelay` 或任何会阻塞的函数。

**时间要在锁里读。** 假设 supervisor 写成先读时间、再拿锁：`uint32_t now=now_ms(); portENTER_CRITICAL(&mux); health_evaluate(&health,now);`。读时间和拿锁之间，另一个核可能插进来：

1. supervisor 在核 1 读到 now=1000，还没拿到锁；
2. worker 在核 0 拿到锁，读到 1001，写入 `last[0]=1001`，释放锁；
3. supervisor 拿到锁，算 `now-last[0]` = 1000−1001，无符号减法回绕成 4294967295，大于 500，判成过期；
4. 锁存，停止喂狗，2 秒后一次莫名其妙的复位。

规则是：**所有一方都在拿到锁之后才读时间**。这样锁内的先后顺序就是时间戳的先后顺序：评估时看到的每个 `last` 都不晚于它自己的 `now`，减法不会倒过来。上报进展的一方同样遵守这条，免得被同核更高优先级的任务抢占之后，才把一个早就过时的时间戳写进去。

supervise 循环把"判定"和"喂狗"拆在锁的两边：

```c
portENTER_CRITICAL(&mux);
/* 到点的故障生效；判定；更新 STATUS 字段；算出要记录的 mask */
health_result_t r=health_evaluate(&health,now_ms());
bool allowed=!stop_supervisor&&health_supervise(&supervisor,r);
portEXIT_CRITICAL(&mux);
if(allowed)ESP_ERROR_CHECK(esp_task_wdt_reset_user(health_user));
else if(!recorded){fault_record_save(&retained,mask);recorded=true;}
```

`esp_task_wdt_reset_user` 内部有自己的锁，放在我们的临界区里会嵌套自旋，还会拉长关中断的时间，所以放到锁外。锁内算好的 `allowed` 是一个局部快照，出锁后再用它不会有竞争。`ESP_ERROR_CHECK` 包住它：句柄无效之类的错误不能静默忽略。

至于 volatile：它只保证编译器每次都真的去内存读写，不提供互斥，也不保证几个字段一起读出来是同一时刻的值。本例的共享状态都在锁内访问，不需要 volatile；只有 RTC 记录用 volatile，因为它要在复位前后"真的写进 RTC 内存"。

## 四、初始化：init 失败不一定是错

```c
esp_task_wdt_config_t wdt={
    .timeout_ms=2000,
    .idle_core_mask=(1U<<portNUM_PROCESSORS)-1U,   /* S3 双核：0b11 */
    .trigger_panic=true,
};
esp_err_t err=esp_task_wdt_init(&wdt);
if(err==ESP_ERR_INVALID_STATE)err=esp_task_wdt_reconfigure(&wdt);
ESP_ERROR_CHECK(err);
ESP_ERROR_CHECK(esp_task_wdt_add_user("health",&health_user));
```

| 字段 | 本例 | 含义 |
|---|---|---|
| `timeout_ms` | 2000 | 所有订阅者共用的超时 |
| `idle_core_mask` | 0b11 | 两个核的空闲任务都订阅，保留"有人霸占 CPU"的检测 |
| `trigger_panic` | true | 超时进入 panic；默认 false 时只打印警告和回溯，程序**继续运行** |

`CONFIG_ESP_TASK_WDT_INIT` 默认开启，IDF 启动时已经初始化过 TWDT。这时再调 `esp_task_wdt_init` 会返回 `ESP_ERR_INVALID_STATE`，意思是"已经初始化了"，不是硬件坏了。正确的处理是改用 `esp_task_wdt_reconfigure` 换成我们的配置。其他错误码一律交给 `ESP_ERROR_CHECK`。

`trigger_panic=true` 之后的动作由 panic 配置决定。本例 `sdkconfig.defaults` 设了 `CONFIG_ESP_SYSTEM_PANIC_PRINT_REBOOT=y`：打印寄存器和回溯，然后重启。生产环境一般就是这个选项；调试时可以改成停住等 GDB。

初始化顺序也有讲究：先 `health_init`（宽限期 1000ms 从这一刻算），再配 TWDT、注册 user，最后才创建三个任务。user 注册到监督任务第一次 reset 之间有一小段空档，2000ms 的超时足够覆盖。

## 五、故障注入与时间预算

故障命令只在测试固件里存在。故障固件用独立的构建目录和 sdkconfig，合并 `sdkconfig.defaults.faults`（打开 `CONFIG_RELIABILITY_TEST_FAULTS`）：

```sh
idf.py -B build-faults -D SDKCONFIG=build-faults/sdkconfig \
  -D "SDKCONFIG_DEFAULTS=sdkconfig.defaults;sdkconfig.defaults.faults" build
idf.py -B build-faults -p COMx flash monitor
```

普通固件收到 TEST_FAULT 会回"不支持"，不会因为一个误发的命令重启。

**`fault --fault 1 --task 0`：worker 停止上报进展。** 设主机发出命令的时刻为 t0，各任务周期：worker 100ms、supervisor 50ms、TWDT 2000ms。

| 时刻 | 事件 |
|---|---|
| t0 | 服务层先把应答排队，再记下 `fault_at=now+200` |
| t0+200～250ms | supervisor 的下一轮发现到点，置 `pause_mask` bit0 |
| t0+100～250ms | worker 最后一次成功上报（取决于它的 100ms 周期落在哪） |
| t0+600～800ms | `now-last[0] >= 500`，判定过期，锁存，停止 `reset_user`，写 RTC 记录 |
| 约 t0+2.6～2.8s | 距最后一次 `reset_user` 满 2000ms，TWDT 超时 → panic → 重启 |

这里的数字是按代码周期推的模型，实际值待上板记录。两个时间尺度要叠加着看：500ms 期限决定"多快判定"，2000ms TWDT 超时决定"判定后多久复位"。想让复位更快，该缩短的是 TWDT 超时，而不是任务期限。

**`fault --fault 2`：监督任务自己停止喂狗。** 生效后 `allowed` 恒为 false，记录的 mask 是 0x80（不是任何任务位，表示"监督被停"）。最后一次 reset 发生在生效前的那一轮，复位大约在 t0+2.15～2.25s。这个故障模拟的是"主管自己出问题"：没有任何任务过期，TWDT 照样复位。

STATUS 里 `required` 恒为 0x03，`overdue` 单独一个字节。主机看到 `overdue=0x01` 就知道是 worker；复位后 `retained=1 overdue=0x1` 是同一个结论在复位后的回放。

最后分清两类错误：串口上收到坏帧、CRC 不对、帧超时，是协议层的事，由 [C8](../c/08-framed-protocol.md) 的重同步和计数器处理，不该让系统重启。看门狗只处理"失去进展"。

## 六、复位原因与 RTC 记录

`app_main` 一开头读 `esp_reset_reason()`，然后决定要不要信 RTC 里的记录：

```c
uint32_t reset=(uint32_t)esp_reset_reason(),previous=0;
bool valid=fault_record_take(&retained,
    reset==ESP_RST_TASK_WDT||reset==ESP_RST_INT_WDT||reset==ESP_RST_PANIC,&previous);
```

`RTC_NOINIT_ATTR` 把 `retained` 放进 RTC 内存里不被启动代码清零的区域。软件复位和看门狗复位后内容还在；**冷上电后内容是随机的**。所以记录的有效性要过三关：

1. **复位原因对得上**：只有 TWDT、IWDT、panic 这三类暖复位才去读，冷上电直接不信；
2. **格式和校验对得上**：magic `0x57444731`、版本 1、CRC-16 全部正确（和 [S17](../stm32/17-watchdog-reset.md) 是同一份 `record.c`）；
3. **读完就作废**：`fault_record_take` 读完立刻把 magic 第一个字节清零，下一次无关的暖复位不会把旧证据再报一遍。

写入顺序也是为复位准备的：先清 magic，再写内容和 CRC，最后写 magic。写到一半复位，读出来的 magic 不对，记录就当不存在。

TWDT 触发 panic 后，`esp_reset_reason()` 在这块板上到底报 `ESP_RST_TASK_WDT` 还是 `ESP_RST_PANIC`，日志里的原始数值待上板记录；代码对两种都接受。日志打印的是原始枚举值，便于对照 `esp_system.h`。

## 七、OpenOCD 与看门狗

IDF 文档写得很明确：用 OpenOCD 调试时，每次停在断点，OpenOCD 都会**关掉 IWDT 和 TWDT 的硬件定时器**，离开断点后**也不会再打开**。只要通过 JTAG 连过 OpenOCD，这两个看门狗就等于没装，不会有任何警告或 panic。

和 F407 的冻结位是一个道理：用调试器连过的板子上测"会不会复位"，"不复位"说明不了任何问题。固定流程是：烧录 → 关掉 OpenOCD → 板子重新上电 → 再发故障命令。

## 附录：工程完整源码

<<< ../../code/esp32/07-watchdog-health/main/main.c

## 记忆锚点

::: tip 一句话记住
**TWDT 默认只看空闲任务；注册一个 health user，判定通过才 reset，停喂不删 user；锁里读时间、锁外喂狗；init 报已初始化就 reconfigure；连过 OpenOCD 必须重新上电。**
:::

## 实物实验

- **装备**：立创实战派 S3、USB 线（默认控制台）、3.3V USB-TTL 接 GPIO10/11。
- **实验 1（worker 过期）**：故障固件，重新上电后执行 `fault --fault 1 --task 0 --port COMy`，在默认控制台记录 panic 打印的时刻和复位后的 `reset=… retained=1 overdue=1`，和第五节的 t0+2.6～2.8s 对照。
- **实验 2（监督停喂）**：`fault --fault 2`，复位后 overdue 应为 0x80，复位时刻应比实验 1 早约 0.5s。
- **实验 3（冷上电）**：拔掉 USB 再插上，日志应为 `retained=0`，证明冷上电不会误用 RTC 里的旧内容。

## 实验记录

模型/编译验证不等于上板实测。当前待上板；请记录日期、板版本、固件版本、接线、输入、原始输出与结论。

| 日期 | 板卡/版本 | 故障输入 | 原始结果 | 结论 |
|---|---|---|---|---|
| 待实测 | | | | |

## 常见坑

- **只靠默认的空闲任务订阅**：任务按时 `vTaskDelay`、却一直没完成工作，TWDT 永远不叫（第二节）。
- **`trigger_panic` 没开**：TWDT 超时只打印一行警告，程序接着跑，以为看门狗复位过了（第四节）。
- **把 `ESP_ERR_INVALID_STATE` 当致命错误**：IDF 已经自动初始化过 TWDT，应该 reconfigure（第四节）。
- **停止监督时 `delete_user`**：超时来源没了，系统永远不复位（第二节）。
- **锁外读时间**：跨核插队后无符号减法回绕，误判过期（第三节）。
- **临界区里阻塞**：关中断太久，触发的是 IWDT 而不是你想测的 TWDT（第三节）。
- **连着 OpenOCD 测复位**：看门狗已被关掉（第七节）。

## 短自测

1. 把 worker 和通信任务直接 `esp_task_wdt_add`、各自 `esp_task_wdt_reset()`，能不能替代本例的设计？丢了什么？
<details><summary>参考答案</summary>能发现"任务卡死"，但丢了三样：每个任务各自的期限（只剩 2000ms 一个全局超时）、上电宽限期和锁存、以及复位后"是哪个任务"的记录（STATUS 的过期 mask 和 RTC 记录）。也没法和 F407 共用 health.c。</details>

2. 监督任务里把 `if(allowed)` 写成 `if(!allowed)`，会发生什么？
<details><summary>参考答案</summary>健康时不喂，系统上电约 2 秒就复位，反复重启；真出故障时反而一直在喂，永远不复位。条件写反等于把看门狗反着装。</details>

3. 为什么 fault 2 记录的 mask 是 0x80，而不是 0？
<details><summary>参考答案</summary>0 会和"没有任何任务过期"混在一起。0x80 不对应任何任务位，专门表示"监督自己被停"，主机复位后看到它就知道不是 worker 或通信任务的问题。</details>

4. 冷上电后 RTC 里的随机内容恰好 magic 和 CRC 都对，会被误报吗？
<details><summary>参考答案</summary>不会。第一关是复位原因：冷上电的原因不是 TWDT/IWDT/panic，`fault_record_take` 直接返回 false，根本不看内容。CRC 是第二道防线，防的是暖复位时写到一半的记录。</details>

## 对照表：本章概念 → 仓库与文档落点

| 概念 | 落点 |
|---|---|
| 进展、期限、宽限期、锁存 | `code/common/reliability/health.c` |
| 三个任务、portMUX、supervise 循环 | `code/esp32/07-watchdog-health/main/main.c` |
| TWDT 配置与 user 接口 | IDF 5.5.2 `esp_task_wdt.h`：`esp_task_wdt_init/reconfigure/add_user/reset_user` |
| 四种看门狗、OpenOCD 行为 | IDF 5.5.2 *Watchdogs* 文档（API Reference → System） |
| 暖复位记录 | `code/common/reliability/record.c`；`RTC_NOINIT_ATTR`（`esp_attr.h`） |
| panic 后重启 | `sdkconfig.defaults`：`CONFIG_ESP_SYSTEM_PANIC_PRINT_REBOOT=y` |
| 故障固件 | `sdkconfig.defaults.faults`：`CONFIG_RELIABILITY_TEST_FAULTS=y` |

## 延伸阅读

- **[\[D12\]](../reference/bibliography.md#papers)** Ganssle《Great Watchdog Timers for Embedded Systems》：任务看门狗该由谁喂、喂狗条件怎么写，才能真的反映"系统健康"。

## 你做到了

- 能说清 TWDT 默认看什么、看不到什么，以及为什么要加一个 health user；
- 跨核共享状态会用 portMUX，知道时间戳为什么要在锁里读；
- 能按 500ms + 2000ms 两段预算预测复位时刻，并用 RTC 记录在复位后回放原因。

不叫的原因：TWDT 默认看的是出勤，不是产出。任务按时让位它就满意，活干没干完它管不着；所以这章给 health 单写了一条新规矩：按期交结果，才有人替它 reset。狗要盯的是产出，这把尺子比默认配置严得多。

<div class="achievement">
✅ 下一站：<a href="../projects/02-s3-logger.html">J2 S3 数据记录器</a>——把协议、健康监督和看门狗装进一个完整的采集项目。
</div>
