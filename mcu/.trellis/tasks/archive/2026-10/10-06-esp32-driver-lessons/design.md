# ESP32-S3 批次设计

## 版本与来源

- 框架：本机 ESP-IDF v5.5.x。实施第一步读取版本宏/`git describe` 确认实际版本并记入研究记录；`idf.py --version` 返回的是启动器版本，不能当 IDF 版本。
- 芯片能力：`components/soc/esp32s3/include/soc/soc_caps.h`（已核实 `SOC_LEDC_CHANNEL_NUM=8`、`SOC_LEDC_TIMER_BIT_WIDTH=14`、`SOC_UART_FIFO_LEN=128`）。
- 驱动源码路径：IDF 5.5.x UART 实现在 `components/esp_driver_uart/src/uart.c`（不是 4.x 的 `driver/uart.c`）；正文引用路径必须与本机实际目录一致。
- 板卡：立创实战派 ESP32-S3 N16R8。引脚取官方 wiki/原理图；取不到则不写默认值。

## 引脚策略

正文与工程把引脚集中在工程顶部一处定义，并在 README 写清“按你的板卡原理图核对后修改”。在没有一手资料之前，工程不使用看似常见的开发板默认引脚作为“板上事实”；能由 SoC 能力说明的约束（如仅某些脚支持特定驱动、模组已占用脚不可用）单独成段讲清。

## 三个工程

### 01-gpio-matrix

- 对照实验：同一外设信号（如 UART TX / LEDC 输出 / SPI CLK）经不同 GPIO 输出，比较波形；展示 IO_MUX 选功能、GPIO Matrix 选信号来源这两级各自的自由度与约束。
- 引脚矩阵测试与 `esp_intr`/GPIO 中断计数一起演示，说明“任意信号可路由到任意 GPIO”的真实前提。

### 02-uart-events

- 事件驱动接收：`uart_event_t` 回调 + 事件循环/队列，说明“字节负载在 `rx_buffer` 里、事件描述在结构体里、事件本身经队列交给任务”三者的分工。
- 与批次一 STM32 DMA 环形接收形成对照：ES3 这里有 FIFO 与 ring buffer 两级，STM32 侧是 NDTR 环形与半满/全满中断。
- 打印实测字节率与事件到达顺序，验证是否合并/分裂。

### 03-ledc-fade

- 一个 timer + 一个 channel 输出 LEDC PWM，S3 只有低速模式；duty 用 `ledc_set_duty` + `ledc_update_duty`；fade 用 `ledc_set_duty_and_update`/fade API，并说明 fade 在硬件/软件上的实际行为。
- 与批次一 STM32 的 TIM PWM 对照：频率/分辨率由 timer 决定、GPIO 与占空比由 channel 决定这一分工是共通的，S3 的差别是 14 位位宽与低速模式限制。
- `idf.py size` 与实际输出频率、占空比范围留证。

## 事实修复落点

| 编号 | 落点 | 处置 |
|---|---|---|
| P-F1 | P2 | “任意引脚”改写为：仅限芯片有效焊脚、该脚支持的输入/输出能力、模组已占用脚、板卡实际接线四项约束下的自由度 |
| P-F2 | P5 | 源码路径更新到 `esp_driver_uart`；区分事件描述与字节负载 |
| P-F3 | P7 | 删除经典 ESP32 的 16 通道/高速模式套用；写 S3 的 8 通道、14 位位宽、低速模式限制，并给多任务操作同一通道的线程安全条件 |

## 动画

沿用父任务动画合同。三张图的数字（通道数、位宽、FIFO 长度、缓冲大小）必须与 `soc_caps.h` 及工程实际配置一致。

## 上板实测

立创 S3 板上可做：GPIO Matrix 路由示波对照、UART 事件顺序与字节率、LEDC 频率/占空比/fade 曲线。LEDC 实测频率与占空比写入实验小节，注明测量工具与误差来源。