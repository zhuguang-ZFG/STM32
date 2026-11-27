# uart-dma-idle：从 AT 到 OK

> 难度：★★★☆　｜　外设：USART + DMA + 环形缓冲　｜　对应章节：[第 13 章 UART](../../docs/v1-drivers/13-uart-framed-protocol.md) / [第 14 章 DMA](../../docs/v1-drivers/14-dma.md)

这是一套可独立构建的 STM32F103C8T6 工程：同一份生产 `main.c` 先通过宿主 HAL 替身测试，再通过 `arm-none-eabi-gcc` 构建并核对 ELF、向量表和内存边界。硬件下载、串口波形和连续流压力仍须在真实板上完成，不能用 CI 代替。

## 一、接线与首次构建

| BluePill | USB-TTL | 说明 |
| --- | --- | --- |
| PA9 USART1_TX | RX | 交叉连接 |
| PA10 USART1_RX | TX | 交叉连接 |
| GND | GND | 必须共地 |
| PC13 | 板载 LED | 低电平点亮 |

USB-TTL 选择 3.3 V 逻辑；PA13/PA14 接 ST-Link 的 SWDIO/SWCLK，`BOOT0=0`。工程按 HSE 8 MHz、PLL ×9、HCLK/PCLK2 72 MHz、PCLK1 36 MHz 和 Flash 两等待周期配置。

工具需要 Git、GNU Arm 工具链（含 newlib）、CMake ≥3.21、Ninja、Python 3 和 OpenOCD。在仓库根目录执行：

```text
git clone --depth 1 --branch v1.8.6 https://github.com/STMicroelectronics/STM32CubeF1.git .temp/STM32CubeF1
git -C .temp/STM32CubeF1 submodule update --init Drivers/STM32F1xx_HAL_Driver Drivers/CMSIS/Device/ST/STM32F1xx
cd examples/uart-dma-idle
cmake --preset bluepill "-DCUBEF1_PATH=../../.temp/STM32CubeF1"
cmake --build --preset bluepill
python tests/check_firmware.py build/bluepill/uart-dma-idle.elf build/bluepill/uart-dma-idle.bin
```

如果已经构建过 `gpio-blink`，可复用同一个 `.temp/STM32CubeF1`。工程锁定 CubeF1、HAL 和 CMSIS 提交，并检查 SHA；输出包括 `.elf`、`.hex`、`.bin`、`.map` 与许可证文件，链接脚本按 64 KiB Flash / 20 KiB SRAM 配置。

下载命令从本目录执行：

```text
openocd -f interface/stlink.cfg -f target/stm32f1x.cfg -c "program build/bluepill/uart-dma-idle.elf verify reset exit"
```

本轮没有执行真实下载。终端设为 `115200 8N1`、无流控、关闭本地回显，发送行尾选择 `CRLF`。输入不是证据，只有板上启动行、回显字节和错误计数的原始记录才算完成闭环。

## 二、命令与可观察结果

可打印 ASCII 命令最多 95 个字符；DMA 的 64 字节只是一次硬件交付段，不能当成命令长度。

| 指令 | 作用 |
| --- | --- |
| `AT` | 握手，返回 `OK` |
| `AT+LED=0/1` | 设置 LED，0 点亮 |
| `AT+LED?` | 查询 LED |
| `AT+ECHO=0/1` | 关闭或开启回显 |
| `AT+INFO` | 返回版本与平台信息 |
| `AT+STATS` | 返回接收、丢失、缺口、错误和发送计数 |
| `AT+RESET` | 返回 `OK` 后软件复位 |

`LED=2`、空参数、尾随垃圾、嵌入 NUL、超过 95 字符的命令都会进入丢弃态，直到收到 `CR` 或 `LF`；长行后面的 `AT+RESET` 不会作为新命令执行。`CRLF` 只执行一次。

`AT+STATS` 的字段边界如下：`rx_bytes` 是 IDLE/TC 交付给软件环的字节数，不是线路总字节数；`dropped_bytes` 是软件已知丢失量，不代表物理线路的全部错误；`stream_gaps` 是缺口通知次数；`uart_errors` 和 `last_uart_error` 来自 HAL；`rearm_failures` 表示重装失败并会停机；`tx_failures` 表示发送函数未返回 `HAL_OK`。计数器为 32 位会回绕，整行不是事务性快照；停止输入并等响应后再比较，且 `AT+STATS` 自身会改变接收计数。

## 三、一条命令怎样穿过两种缓冲

数据路径是：64 字节普通 DMA 区 → IRQ 中复制 → 512 项软件环 → 主循环按 `CR/LF` 组行。它不是零拷贝。

- 半传输事件 `HT` 只表示进度，忽略 `Size=32`，不复制、不重装。
- `IDLE` 交付当前前缀一次；`TC` 交付完整的 64 字节一次，然后重装 DMA。
- `HT=32` 后 `IDLE=40`，软件得到 40 字节，不是 72 字节。
- `AT+LE` 和 `D=1\r` 可以来自不同 DMA 段，主循环仍会拼成一条命令。
- 环中保留一个空槽，最多容纳 511 个 `uint16_t` 项；0–255 是数据，256 是内部缺口标记。

生产者只由两个同优先级的接收 IRQ 驱动，消费者是主循环；`head/tail` 用 C11 acquire/release 发布和获取。构建还检查目标短整型原子操作无锁，避免 ARM 固件偷偷链接 `libatomic`。

## 四、丢字节后，先等行结束

软件环满时，生产者统计已知丢失的剩余字节，并在下一字节之前放入缺口标记。消费者看到标记后清掉半行，进入 `DISCARD`，直到行尾才恢复；缺口标记本身也占一个环槽。如果连标记或后续换行也丢了，下一行可能被保守地一起丢弃。缺口前已经完整排队的命令仍可执行。

UART 错误回调保存错误码，调用 `HAL_UART_AbortReceive`，按 F1 规定清除接收错误，再检查 DMA 重装结果；任何失败都进入终止错误处理。错误发生时 DMA 中尚未交付的部分会被丢弃，重试前先单独发送换行。

普通 DMA 的重装间隙、阻塞发送占用 CPU、软件环溢出和线路本身的错误都可能造成缺口。要做产品级连续无损传输，还需要流控、CRC、序号或循环 DMA 等协议设计；本工程的计数和重同步机制用于让失败可见、让解析器回到已知边界。

## 五、自动检查与上板练习

宿主测试覆盖 10 个边界：HT/IDLE/TC、重装失败、UART 错误恢复、环操作、跨段组行、非法输入、溢出丢弃、启动状态和统计响应。测试使用完整生产 `main.c` 与显式 HAL 边界，证明代码路径可运行，不证明真实线路已经通过。

上板时按三组证据推进：

1. 发送 `AT`、跨 DMA 段发送一条命令，保存原始 TX/RX 字节、启动行和 `AT+STATS`。
2. 发送长行与非法参数，再发送合法命令；确认没有执行长行后缀，解析器能在行尾恢复。
3. 在受控负载下制造环满或 ORE，记录丢失字节、缺口、错误码和波形；把板卡身份、构建 SHA、下载结果和串口日志放进实验记录。

失败时先按最短路径查：没有启动行看复位、下载和端口；乱码核对共地、3.3 V 电平、时钟和 `BRR=0x271`；只收到一次看 IDLE/TC 后是否成功重装；缺口后命令粘连看换行与 `DISCARD`；计数不一致看输入是否在响应完成前继续发送。

## 六、来源与迁移

- HAL 与 CMSIS 固定来自官方 `STM32CubeF1` v1.8.6；F103 的 USART1_RX 请求固定为 DMA1 Channel5，TX 为 Channel4，依据 RM0008 的映射。
- MaJerle 的 USART DMA 示例用于比较循环 DMA、HT/TC/IDLE 的事件边界；其循环缓冲实现不能直接证明本普通 DMA 工程连续无损。
- AN4031 面向 F2/F4 DMA 控制器，只用于解释双缓冲等概念，F103 的寄存器和请求映射以 RM0008 为准。
- 本 README 的图和书中手绘图是原理示意，不是测量截图。迁移到 F407 时必须重查 DMA 控制器、流/通道、缓存一致性和链接内存布局；F407 的循环字节回显实验与这里的 AT 命令协议是两条独立路线。
