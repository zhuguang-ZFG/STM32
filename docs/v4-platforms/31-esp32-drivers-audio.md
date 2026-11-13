---
title: "ESP32 外设、驱动框架与音频链路"
platforms: [esp32]
---

# ESP32 外设、驱动框架与音频链路

ESP32 的外设 API 与 STM32 最大的差别不在功能，在**形态**：驱动是事件驱动的框架层（UART 的事件队列、SPI 的事务队列、I2C 的句柄模型），GPIO 有两条路由（IO_MUX 专线与 GPIO Matrix 总机），LEDC 是两级配置的 PWM 专职外设。本章按「GPIO→UART→SPI/I2C→LEDC→音频链路」的顺序拆，每个驱动给「三层缓冲/事务队列/句柄」这类结构性的东西，板级常数（引脚号、器件地址）全部标注来源。

证据先说清：本章零板级实测。上游核对按 **ESP-IDF v5.5.2** 实取（`uart.h:71-95,121`、`spi_master.h:42,75,82,84`、`spi_common.h:78`、`i2c_master.h:31,50,118,131,208`、`ledc.h:181,295,480,494,520`、`hal/ledc_types.h:139-142`、`soc_caps.h:177,242-248,425` 全部命中）；工程实例 `mcu/code/esp32` 的 `04main`/`05main` 行号逐字核对（QMI8658 六轴链路、I2S 音频链路的全部行号精确命中）。器件细节（ES7210 通道占用、ST7789 引脚、esp_codec_dev 1.3.4）来自立创 wiki 与 managed component 注册表，逐项标待核。`hardware_status: pending`，实验全部「未实测」。

> 版本口径：ESP-IDF **v5.5.2**；板卡立创实战派 S3（扩展口、SDA=GPIO1/SCL=GPIO2 等以工程代码为准）；esp_codec_dev 是 managed component，版本钉 1.3.4（构建期自动下载，来源待核）。

## 本章罗盘

- **问题**：IO_MUX 与 GPIO Matrix 怎么分工，「任意引脚」的四个前提是什么，45=22+23 与 `SOC_GPIO_PIN_COUNT=49` 的口径差在哪？哪些脚被 PSRAM 与 strapping 占了？UART 事件驱动的三层缓冲在哪三层，三个溢出点是什么，事件与数据的边界在哪，`timeout_flag` 是什么？SPI 的两级模型与事务队列怎么用，异步事务的 buffer 生命周期谁管？I2C 新驱动为什么是句柄模型，`transmit_receive` 末参是什么单位，7 位地址要不要左移？LEDC 两级配置怎么配，S3 的边界（通道数/位宽/模式）与经典 ESP32 差在哪，改占空比为什么要 update？音频为什么分控制面与数据面，MCLK=256×fs 怎么算，三笔账（码率/MCLK/信封）各是多少，缓冲容量怎么定？
- **交付**：能用「有效焊盘+能力+未占用+板卡引出」判断一个脚能不能用；能背 S3 的占用脚清单；能按 v5.5.2 签名写出 `uart_driver_install` 六参数并解释事件≠数据；能写出 SPI 总线/设备两级配置与 I2C 句柄三步；能算 LEDC 的分辨率×频率跷跷板并指出 S3 的 8 通道/14 位/仅低速边界；能复算音频三笔账（512 kbps、4.096 MHz、10 ms）并给出缓冲容量算法；能把「学时序手写、做产品用框架」落到一个对照表上。
- **边界**：单平台 ESP32-S3；UART 的协议帧设计归 [v1 第 13 章](../v1-drivers/13-uart-framed-protocol.md)，SPI/I2C 的时序原理归 [v1 第 16 章](../v1-drivers/16-i2c-spi.md)，PWM 的占空比语义归 [v1 第 12 章](../v1-drivers/12-timers-pwm.md)——本章只讲 ESP32 驱动框架与它们的差异。器件级常数（屏/六轴/编解码器）都是「那块板+那颗器件」的具体值，不是通用常数。启动与工程归 [第 30 章](./30-esp32s3-architecture-boot.md)；无线归第 32 章。
- **依据锚点**：E2《GPIO 矩阵》（`mcu/docs/esp32/02-gpio-matrix.md`）、E5《UART 驱动》（`.../05-uart-driver.md`）、E6《SPI/I2C 驱动》（`.../06-spi-i2c-driver.md`）、E7《Timer 与 LEDC》（`.../07-timer-ledc.md`）、E12《音频链路》（`.../12-audio-path.md`）、LAB8《音频播放》（`mcu/docs/lab/e08-audio-play.md`）。上游对账：ESP-IDF v5.5.2 的 [uart.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/esp_driver_uart/include/driver/uart.h)、[spi_master.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/esp_driver_spi/include/driver/spi_master.h)、[spi_common.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/esp_driver_spi/include/driver/spi_common.h)、[i2c_master.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/esp_driver_i2c/include/driver/i2c_master.h)、[ledc.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/esp_driver_ledc/include/driver/ledc.h)、[i2s_std.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/esp_driver_i2s/include/driver/i2s_std.h)、[soc_caps.h](https://github.com/espressif/esp-idf/blob/v5.5.2/components/soc/esp32s3/include/soc/soc_caps.h)。工程实例：`mcu/code/esp32` 的 `04main`（QMI8658）、`05main`（音频：`:18` SAMPLE_RATE 16000、`:19` BLOCK_FRAMES 160、`:92` 引脚、`:95` MCLK 多倍、`:126` MCLK 值）。

## 先做出来

### 1. 任意引脚的四个前提

「ESP32 任意 IO 都能当 UART TX」这句话有四个前提，缺一个就不成立：

1. **有效焊盘**：S3 的物理 GPIO 是 0~21 + 26~48 共 **45 个**（22~25 不存在）；`SOC_GPIO_PIN_COUNT=49` 是**编号上限**不是个数——45=22+23 的算术与 49 的编号口径并存。
2. **能力**：该信号在该脚有路由（IO_MUX 专线或 GPIO Matrix 可达）。
3. **未占用**：IO35/36/37 被八线 PSRAM 占用（N16R8 模组）；GPIO0/45/46 是 strapping 脚（上电采样，GPIO0 还兼任 BOOT）。
4. **板卡引出**：扩展口只引出部分脚——工程实例里扩展口用的是 GPIO10/11。

「一碰就崩」的物理层失败发生在第 3 条：碰了 PSRAM 占用脚不是驱动报错，是总线翻转、系统崩——这种错没有异常可抓。

### 2. 三秒换脚（LEDC quick win）

`ledc_set_pin` 把 PWM 从 GPIO10 挪到 GPIO11，旧脚用 `gpio_reset_pin` 归位：ESP32 的引脚是路由表里的软配置，不像 STM32 换脚要动 AF 复用选择器。板级现象待记录（未实测）。

## 机制

### 一、两条路由与焊盘属性

S3 的 GPIO 有两条路由：**IO_MUX 专线**（高速外设直连，如 Flash/PSRAM 的专属脚）与 **GPIO Matrix 总机**（任意脚互连，走一拍开关矩阵）。高速信号走专线，普通外设走总机。**焊盘属性是独立的一维**：上下拉、驱动强度、开漏、（S3 的）毛刺过滤由焊盘电路管，与路由无关——API 全部存在（`gpio.h:82,172,199,365` 实取 `gpio_reset_pin`/`gpio_set_direction`/`gpio_set_pull_mode`/`gpio_set_drive_capability`）；「毛刺过滤是 S3 新增」属手册层说法，标待核。

![GPIO 矩阵路由动画：IO_MUX 专线与 GPIO Matrix 总机的分工](/anim/gpio-matrix-routing.svg)

![焊盘属性：路由之外还有一维](/figures/esp32-02-pad-attrs.svg)

### 二、UART：三层缓冲、三个溢出点、事件≠数据

ESP32 的 UART 驱动是「ISR 搬运 + 事件队列 + 任务处理」的闭环。`uart_driver_install` 按 v5.5.2 签名六参数（`uart.h:121`）：

```c
uart_driver_install(UART_NUM_1,
    2048,   /* rx_buffer_size：驱动 ring buffer */
    0,      /* tx_buffer_size：0=同步发送 */
    20,     /* queue_size：事件队列深度 */
    &uart_queue,          /* 事件队列句柄 */
    0);     /* intr_alloc_flags */
```

数据走**三层**：硬件 FIFO（S3 是 128 字节，`soc_caps.h:425`）→ 驱动 ring buffer → 用户 buffer。三个溢出点对应两类事件：FIFO 满未搬 → `UART_BUFFER_FULL`；FIFO 溢出（硬件丢字节）→ `UART_FIFO_OVF`；ring buffer 满 → 数据被拒收。**事件≠数据**：`UART_DATA` 事件只带元数据（`uart_event_t` 的 `size` 与 `timeout_flag`，`uart.h:91-95`），字节躺在 ring buffer 里，`uart_read_bytes` 才取走。`timeout_flag` 是「RX TOUT 时间内没有新数据」的标志——**IDF 版的 IDLE 判帧**：协议帧边界靠它，与 [v1 第 13 章](../v1-drivers/13-uart-framed-protocol.md) 的 IDLE 判帧同构，只是这边用软件超时实现。

![UART 事件驱动动画：ISR 搬运、事件队列、任务处理](/anim/idf-uart-events.svg)

![UART 配置三层：硬件 FIFO、驱动 ring、用户缓冲](/figures/esp32-05-uart-config.svg)

### 三、SPI：两级模型与事务队列

SPI 驱动分**总线**与**设备**两级：总线用 `spi_bus_initialize`（MOSI/MISO/SCLK + `SPI_DMA_CH_AUTO=3` 自动 DMA 通道，`spi_common.h:78`——注意总线配置结构在 `spi_common.h` 不是 spi_master.h），每设备一个 `spi_device_interface_config_t`（`spi_master.h:75,82,84`：`clock_speed_hz`、`spics_io_num`、`queue_size`）。`queue_size` 是**事务队列深度**：把多个 `spi_transaction_t` 提交进队列，驱动按序执行，轮询 `spi_device_get_trans_result` 收结果——半双工/异步事务的 buffer 生命周期必须覆盖传输期（提交的 buffer 在事务完成前不许动）。DC 与 CS 是两条线：DC（数据/命令）对屏类设备是 `pre_cb` 里翻的电平，CS 由 `spics_io_num` 交给驱动。ST7789 的刷屏账：320×240×2=153600 B/帧，40 MHz→5 MB/s（40e6/8 的**算术**，不是实测）→ 约 30.72 ms/帧，60 fps（16.7 ms）吃紧——引脚与初始化序列是屏级常数，标 wiki 待核。

### 四、I2C：句柄模型与「末参是毫秒」

v5.x 的新 I2C 驱动是句柄模型三步（`i2c_master.h:118,131,208` 实取）：

```c
i2c_master_bus_config_t bus_cfg = { .i2c_port = 0, .sda_io_num = 1,
    .scl_io_num = 2, .clk_source = I2C_CLK_SRC_DEFAULT,
    .glitch_ignore_cnt = 7,          /* 典型值 7 */
    .flags.enable_internal_pullup = false };  /* 内部上拉高速不够强，建议外部上拉 */
i2c_new_master_bus(&bus_cfg, &bus_handle);
i2c_device_config_t dev_cfg = { .dev_addr_length = I2C_ADDR_BIT_LEN_7,
    .device_address = 0x6a, .scl_speed_hz = 100000 };
i2c_master_bus_add_device(bus_handle, &dev_cfg, &dev_handle);
i2c_master_transmit_receive(dev_handle, reg, 1, buf, 6, -1);  /* 末参 xfer_timeout_ms */
```

两个易错：**末参是毫秒超时**（`xfer_timeout_ms`，`:208`），不是标志；**7 位地址不左移**——8 位手册地址先右移一位（0xD4>>1=0x6A），工程 `04main:44-45` 的 0x6a 就是这么来的。QMI8658 六轴链路（`04main` 全行号核对）：WHO_AM_I(0x00)=0x05 验身份 → CTRL 链配置量程 → 状态位 0x2e 就绪 → AX_L(0x35) 连读 12 字节；灵敏度算术 ±4g→32768/4=8192 LSB/g、±512 dps→32768/512=64 LSB/(°/s) 成立；寄存器键值是器件手册级常数，标待核。

### 五、LEDC：两级配置与 S3 边界

LEDC 是**定时器→通道**两级：timer 定频率与分辨率，channel 绑 GPIO 与占空比。S3 的边界（`soc_caps.h:242-248` 实取）：**8 通道、4 定时器、14 位位宽、仅低速模式**——经典 ESP32 的 16 通道/高速模式结论不能搬。分辨率×频率跷跷板：`f = 时钟 / 2^位数`，80 MHz APB 下 5 kHz/10 位、50 Hz/14 位、>20 kHz/≤10 位三档代数可行。**改占空比要 update**：`ledc_set_duty` 与 `ledc_update_duty` 是两个 API（`ledc.h:181,295`）——set 写影子寄存器，update 才生效（双缓冲）；硬件 fade 不占 CPU（`ledc_fade_func_install`→`ledc_set_fade_with_time`→`ledc_fade_start`，`:480,494,520`；`LEDC_FADE_NO_WAIT/WAIT_DONE` 枚举在 `hal/ledc_types.h:139-142`，**不是 driver/ledc.h**）。

![LEDC 定时器与通道两级动画](/anim/ledc-timer-channel.svg)

### 六、音频链路：控制面 + 数据面 + 三笔账

「能出声」是两面的合成：**控制面走 I2C**（ES8311 编解码器、ES7210 ADC 的寄存器配置，经 esp_codec_dev 组件），**数据面走 I2S**（样本流）。工程 `05main` 的行号表（全部实读命中）：

| 事实 | 行号 | 值 |
| --- | --- | --- |
| 采样率/块 | `:18-19` | 16000 Hz、BLOCK_FRAMES=160 |
| I2C 引脚 | `:72` | SDA=GPIO1、SCL=GPIO2 |
| 扩展器/PA | `:78,81` | PCA9557@0x19、PA_EN 在扩展器 bit1——**不在 ESP32 的 GPIO** |
| I2S 引脚 | `:92` | mclk=38/bclk=14/ws=13/dout=45 |
| MCLK 多倍/值 | `:95,:126` | `I2S_MCLK_MULTIPLE_256` → MCLK=256×16000=**4096000 Hz** |

三笔账一起算：码率 16k×16×2 = **512 kbps**（stereo 双槽）；MCLK = 256×fs = **4.096 MHz**；10 ms 信封 = 16000×0.01 = **160 帧**（=BLOCK_FRAMES）。ES8311 是单声道 DAC——单声道内容走 stereo 双槽位，两槽填同一份样本。**纪律三段：先静音（写 codec mute），再发声（I2S 送数据），后放开 PA（扩展器位）**——顺序反了就是爆音。延迟账：BLOCK_FRAMES/fs × 2 = 10 ms×2 = 往返约 20 ms + codec 内部几 ms；缓冲容量 = 采样率 × 容忍延迟 × 2（16 kHz×50 ms=800 样本，双倍余量 1600）；「150 ms 觉察回声感/300 ms 没法说话」是心理声学经验口径，标待核。

![ESP32 音频链路动画：控制面 I2C + 数据面 I2S](/anim/esp32-audio-path.svg)

![I2S 时钟账：MCLK/BCLK/LRCLK 的倍数关系](/figures/esp32-12-i2s-clock.svg)

![手绘板：音频双面范式——控制面 I2C、数据面 I2S、三笔账一起算、先静音再发声后放开 PA（原理示意）](/images/mc31-matrix-audio.png)

E08 的完整播放链（1 kHz 滴声 + 八音符、缓冲减小出现断音）代码就绪（`code_status: ready`），板上现象待实测（`hardware_status: pending`）——测量与证据的完整登记归第 40 章的实验方法（B4 卷 6，此处只挂账不占位）。

![E08 音频链路：扩展板上的器件与接法](/images/labs/e08-audio-chain.svg)

### 七、学时序手写，做产品用框架

E6 收尾的对照表，落进本章收束：

| 场景 | 手写时序（学原理） | 框架（做产品） |
| --- | --- | --- |
| I2C | GPIO 翻转 SCL/SDA，一位一位走 | `i2c_master_*` 句柄 API |
| UART 帧 | 直接读 FIFO + 软件超时 | 事件队列 + `timeout_flag` |
| PWM | 定时器手动翻转 | LEDC 两级 + fade |

手写的价值在「知道框架底下是什么」；框架的价值在「缓冲、超时、错误码都被别人踩过」。与 [v1 第 16 章](../v1-drivers/16-i2c-spi.md) 的手写 I2C 对照着读，两边的分工就清楚了。

## 测量与证据

| 结论 | 身份 | 判据 |
| --- | --- | --- |
| UART 事件枚举/六参签名 | 手册级（上游已核） | `uart.h:71-95,121@v5.5.2` |
| FIFO 128 字节 | 手册级（上游已核） | `soc_caps.h:425` |
| SPI 两级/事务队列/DMA_AUTO | 手册级（上游已核） | `spi_master.h:75,82,84` + `spi_common.h:78` |
| I2C 句柄三步/毫秒超时/7 位不左移 | 手册级（上游已核） | `i2c_master.h:31,50,118,131,208` |
| S3 LEDC 8 通道/14 位/仅低速 | 手册级（上游已核） | `soc_caps.h:242-248` |
| fade API 链与枚举落点 | 手册级（上游已核） | `ledc.h:480,494,520` + `hal/ledc_types.h:139-142` |
| 音频三笔账（512kbps/4.096MHz/160 帧） | 文档推导（算术全复算） | 16k×16×2、256×16k、16k×0.01 |
| 04main/05main 行号表 | 手册级（工程实读命中） | 仓库逐行核对 |
| ST7789/FT6336G/ES7210 器件细节 | 来源说法待核 | 立创 wiki + 器件手册 |
| 「150ms/300ms」延迟阈值 | 来源说法待核 | 心理声学经验口径 |
| esp_codec_dev 1.3.4 | 来源说法(未复核) | managed component，构建期下载 |
| PWM 换脚/UART 压测/刷屏帧率/E08 放音 | 未实测 | `hardware_status: pending` |

## 失败分支

| 症状 | 第一条假设 | 区分实验 |
| --- | --- | --- |
| 碰某脚系统崩 | 撞了 PSRAM 占用脚（IO35/36/37） | 对模组占用清单；换脚 |
| UART 收不到事件 | 事件队列没建（queue_size=0）或没轮询 | 检查 `uart_driver_install` 第 4/5 参 |
| UART 丢字节 | FIFO_OVF：任务处理太慢 | 加大 ring buffer；任务里尽快 `uart_read_bytes` |
| SPI 异步事务数据错乱 | buffer 生命周期短于传输期 | 事务完成前不动 buffer；用 `spi_device_get_trans_result` 收尾 |
| I2C 地址不通 | 8 位地址没右移 | 0xD4>>1=0x6A；对照器件手册位号 |
| I2C 高速不稳 | 内部上拉太弱 | 外部上拉 4.7k/2.2k |
| 改 duty 不生效 | 只 set 没 update | `ledc_set_duty` + `ledc_update_duty` 成对 |
| fade 报错 | 没装 fade 服务或枚举头文件找错 | `ledc_fade_func_install` 先行；`LEDC_FADE_*` 在 `hal/ledc_types.h` |
| 音频爆音 | PA 先开、数据后到 | 三段纪律：静音→数据→放开 PA |
| 回声明显 | 缓冲超过容忍延迟 | 缓冲容量=采样率×容忍延迟×2 重算 |

## 离开检查

- 「任意引脚四前提」能背，45=22+23 与 `SOC_GPIO_PIN_COUNT=49` 的口径差能讲。
- 三层缓冲、三个溢出点、事件≠数据、timeout_flag 判帧能画成一张图。
- SPI 两级与事务队列、I2C 句柄三步与毫秒超时、7 位不左移能落到代码。
- S3 的 LEDC 边界（8/4/14/仅低速）与双缓冲 update 纪律记得住。
- 音频三笔账（512 kbps / 4.096 MHz / 160 帧）当场复算；三段纪律（静音→数据→PA）能说出为什么。
- 板级常数与通用常数的边界分得清：引脚号、器件地址、阈值各自标什么来源。
