---
title: J1 STM32F407 传感器记录器
status: done
difficulty: 3
minutes: 60
code_status: ready
hardware_status: pending
code_note: 真实外设驱动与完整运行路径已提供；物理板卡结果待测。
projects: ["stm32-07-sensor-logger"]
---

# J1 STM32F407 传感器记录器

> 🎯 数据能打印一次不难；让它在传感器失联、队列积压和配置写入中断后仍有明确状态，才是一套完整记录器。

## 本章精髓

采集、滤波、队列、通信、配置保存与监督各有一个职责。两平台共享协议和纯 C 核心，驱动差异留在 port 适配层。健康判据是完成有界工作，传感器错误不自动等于任务卡死。

## 先修

必需：[C8 协议](../c/08-framed-protocol.md)、[S17 看门狗](../stm32/17-watchdog-reset.md)、[P13 健康监督](../esp32/13-watchdog-health.md)；板卡路线补 [S9 ADC](../stm32/09-adc.md) 或 [P6 I2C](../esp32/06-spi-i2c-driver.md)。另一平台作为并行对照。

## 工程信息

<LabStatus />

## 配置与接线

PA0 为 ADC1_IN0：外接电位器中间脚，另外两端接 3.3V 和 GND；先移除旧 PA6→PA0 测频跳线。PB6/PB7 接 AT24C02 SCL/SDA、各 4.7k 上拉至 3.3V，A0–A2 和 WP 接地。模块 256 字节全部作为配置双槽使用，会覆盖旧 EEPROM 实验数据。USART1 PA9 TX/PA10 RX 接 3.3V USB-TTL。

![J1 接线与配置双槽：电位器滑片接 PA0，PB6/PB7 接 AT24C02 并上拉，PA9/PA10 接 USB-TTL；EEPROM 两个 128 字节槽的四步保存顺序](/images/projects/j1-f407-wiring.svg)

F407 基准为复位 HSI16+FreeRTOS V11.1.0；S3 为 IDF5.5.2。共地、TX/RX 交叉，COMx 换实际端口，绝不把 5V 信号直接接入 3.3V GPIO。

## 先跑起来

在已激活工具链环境执行：

~~~sh
cd code/stm32/07-sensor-logger
make MODE=0 FAULTS=0
make MODE=0 FAULTS=0 flash
~~~

随后回仓库根，在主机执行：

~~~sh
python3 -m pip install -r scripts/device-console-requirements.txt
python3 scripts/device-console.py info --port COMx
python3 scripts/device-console.py status --port COMx
python3 scripts/device-console.py configure --period 200 --filter-shift 2 --port COMx
python3 scripts/device-console.py save --port COMx
python3 scripts/device-console.py record --seconds 10 --output samples.csv --port COMx
python3 scripts/device-console.py stop --port COMx
python3 scripts/device-console.py start --port COMx
~~~

断电之前先押个记性：如果刚才只跑到 configure、还没 save 就断了电，重启之后记录器会用哪个周期干活？新改的、原来的，还是配置干脆丢掉？押完再往下读；不服，就真拔一次电，答案在重启后的 status 里。

record 写入新的 CSV 文件；请使用新的输出路径，避免覆盖之前的数据。默认周期 100ms；period 允许 100–1000ms 且为 10ms 倍数，filter-shift 允许 0–6，0 为直通。configure 只改变运行配置，save 成功才持久化；旧 generation 的在途采样会丢弃计数，防止误标新配置。

## 四层实现

五站数据流先收进一张图：采样主路之外，还有一条影子拷贝的配置通路。

![数据记录器五站接力：ADC→DMA→采样任务→样本队列→USART，配置走 EEPROM 影子拷贝](/arch/logger-flow.png)

![记录器架构：采样输入经 sample 任务、滤波与 16 槽队列、comm 任务和串口到主机；supervisor 按期限检查进度并喂硬件看门狗；save 在锁外写配置存储](/images/projects/logger-architecture.svg)

| 层 | 实际职责 | 验证 |
|---|---|---|
| 外设适配 | ADC或I2C、串口、存储、硬件watchdog | 平台编译与待上板日志 |
| 公共核心 | 滤波、配置镜像、16槽样本队列 | 生产C函数的宿主断言 |
| RTOS运行层 | 采样/通信/监督任务，短时状态互斥 | 故障注入和期限预算 |
| 主机 | 独立编解码、序号匹配、CSV | C/Python交叉向量 |

## 系统设计决策

**为什么选四层架构而非单体？** 嵌入式项目常见诱惑是"反正就这几个功能，全塞 main.c"。但当我们需要在 F407 和 S3 两个平台复用核心逻辑时，单体结构会让代码分叉难以维护。四层分离让公共核心（滤波、协议、队列）在两个平台共享同一份 C 代码，平台适配层只处理寄存器差异。代价是多了一层间接调用，但换来的是：①主机断言可以在 PC 上验证核心逻辑；②新增平台（如 GD32）只需写适配层；③代码审查时能清晰区分"平台 bug"和"逻辑 bug"。

**为什么配置保存不持有采样锁？** EEPROM 页写需要 5-10ms，如果在此期间持有采样状态锁，采样任务会被阻塞至少一个周期（100ms 默认周期下就是 10% 的数据丢失）。设计原则是"保存用影子拷贝"：先把当前配置 memcpy 到临时缓冲区（<1μs），释放锁，再慢慢写 EEPROM。采样任务继续用原始配置运行，不受影响。锁的粒度应该覆盖"读取-修改"的原子性，而不覆盖"写入慢速外设"的等待。这个决策的代价是需要额外的 128 字节栈空间存放影子拷贝，但换来的是采样连续性。

**为什么样本队列只有 16 槽？** 理论上队列越大越不容易丢数据，但每个槽是 64 字节，16 槽就是 1KB RAM。F407 有 192KB RAM 看似充裕，但 FreeRTOS 任务栈、DMA 缓冲、协议栈都在抢这块空间。16 槽在 100ms 采样周期下能缓冲 1.6 秒数据，足够覆盖通信任务短暂阻塞（如 USB 转串口芯片的流控）。如果通信持续失败，队列满后丢新样本并计数，这是显式的"过载保护"，而非隐式的内存溢出。调大队列前应先用 STATUS 命令查高水位，确认是否真的需要。

**为什么健康监督用期限而非心跳？** 心跳模式（任务定期报告"我还活着"）的问题是：任务卡死在某个阻塞调用上时，仍可能在超时前最后一次报告心跳。期限模式要求任务在固定窗口内完成固定工作（采样任务 2500ms 内至少完成 20 次采样），未完成即视为卡死。这能检测到"任务还活着但进度停滞"的隐性故障。代价是需要为每个任务定义"合理工作量"，但这迫使开发者思考任务的时间约束，而非假设"只要不崩就行"。

## 定时采样与滤波

TIM2 TRGO 以毫秒分频定时触发 ADC1，DMA2 Stream0 Channel0 使用两个半字缓冲，IRQ56 发通知唤醒采样任务。IRQ 优先级 6，满足本项目 MAX_SYSCALL=5 的限制；USART1 使用 DMA2 Stream5，不共用流。原始数据是 12 位 ADC 码值，不能未测 VDDA 就声称是校准电压。

默认整数 IIR 每次走向新值的 1/4，使用 64 位中间差值避免溢出；整数舍入会产生小死区，滤波延迟不是零。有效位清除的通道不更新滤波，恢复后第一样本重新初始化。STOP 停止采样服务，但通信和监督仍执行，不应该触发看门狗。

## 协议与缓冲

SAMPLE 固定 64 字节：sequence/u32、timestamp_ms/u32、generation/u32、sensor_type/u8、valid_mask/u8、status/u16、raw[6]/i32、filtered[6]/i32，全部 LE。ADC 仅 bit0 有效；IMU 最多六位有效。INFO 给原码比例，STATUS 的 TLV 给运行配置、保存代次、丢弃/传感器/存储错误和队列高水位。

样本队列 16 槽，满则丢新记录并计数。TX 另有 4 帧槽和 100ms 发送期限，部分帧失败后先发零同步。无硬件流控的 UART 不能确认对端真正接收，也不能可靠检测接收线断开；主机用序号发现缺口，不承诺无限离线缓存。

## 配置保存与恢复

AT24C02 两个 128 字节槽。写目标槽前使提交标记无效；按 8 字节页边界写前 127 字节，回读校验后最后写提交标记。旧槽在整个过程中保留，启动挑选最新有效 generation。每个写步骤的中断都用生产存储逻辑测试；硬件断电/时序仍待实测。

配置代次用有界模序号比较；不同 schema 不能直接按新结构解释。保存发生在状态锁之外，采样优先级高于通信，避免慢存储长期阻塞采样。重复保存相同代次不额外写入。

## 健康与故障实验

采样服务期限 2500ms、通信 1500ms，监督每 50ms 评估；硬件 watchdog 名义 2s。无流量、已 STOP、传感器返回错误但工作循环仍前进，都不属于卡死。首次超时锁存停喂狗，故障记录只辅助暖复位诊断，不能代替真实上板观测。

测试构建才开放以下显式命令，普通固件返回 UNSUPPORTED：

| 输入 | 预期逻辑结果（非实测） |
|---|---|
| fault 1 / task 0或1 | 指定任务停止上报，随后watchdog复位 |
| fault 2 | 监督停止喂狗，注册的watchdog仍保留 |
| fault 3 | 1秒模拟传感器失联，有效位清零，系统保持健康 |
| fault 4 | TX暂停2秒，队列积压/丢弃可观察，随后同步恢复 |

命令示例：`python3 scripts/device-console.py fault --fault 3 --port COMx`。应答入队后 200ms 执行，不自动重试故障。F407 以 FAULTS=1 构建；S3 用独立 sdkconfig 合并 sdkconfig.defaults.faults。断电配置试验先使用专用存储，不对有重要数据的模块做实验。

## 短自测

1. CRC 校验正确的报文，为什么仍不能信任"无效位"为 0 的通道数据？
<details><summary>参考答案</summary>CRC 只保证报文字节在传输中没有被检测出损坏，它不验证传感器是否真正完成了采样。如果传感器失联或处于错误状态，驱动可能返回全零或上一次缓存值，CRC 仍然正确（因为 CRC 算的是报文本身，不是传感器状态）。有效位（valid bit）是驱动层对传感器健康状态的判断，独立于 CRC。只看 CRC 不看有效位，等于把"信封没破"当成"信的内容正确"。</details>

2. 配置保存到 EEPROM 时，为什么不持有采样状态锁？
<details><summary>参考答案</summary>EEPROM 的页写入需要 5-10ms 等待（AT24C02 的页写周期），如果在此期间持有采样锁，采样任务会被阻塞至少一个周期。设计原则是"保存用影子拷贝"：先把当前配置 memcpy 到临时缓冲区，释放锁，再慢慢写 EEPROM。采样任务继续用原始配置运行，不受影响。锁的粒度应该覆盖"读取-修改"的原子性，而不覆盖"写入慢速外设"的等待。</details>

3. 什么情况下重启后仍加载旧参数？
<details><summary>参考答案</summary>两种情况：①只调了 `configure` 修改运行时参数但没调 `save`：新参数只活在 RAM 里，断电即失；②调了 `save` 但 EEPROM 写入失败（总线忙、页写未完成就断电、WP 引脚意外拉高）。健壮的做法是 save 后立即 readback 校验，不匹配则重试或报警。旧有效配置应保留在 EEPROM 的另一槽（双槽轮转），直到新配置校验通过才切换。</details>

无数据先查 START 状态和端口/交叉接线，再查 STATUS 有效性与错误计数；无响应查看 RX 错误和 TX 丢弃；意外复位检查 reset_reason、过期 mask、调试器冻结设置。不要先加长看门狗掩盖卡死。

## 附录：完整运行路径

公共任务层：

<<< ../../code/common/logger/runtime.c

平台适配：

<<< ../../code/stm32/platform/logger_port.c

## 你做到了

可追踪一条记录从外设到 CSV，能分清配置应用、保存和恢复，也能把故障从静默错误变成明确状态。上板记录请注明板版本、固件提交、接线、输入和原始日志，本页当前仍为待实测。
