# 03-uart-dma：串口两级缓冲与“可写≠发完”

现行配套章节：[ch13 UART](../../../../docs/v1-drivers/13-uart-framed-protocol.md)、[ch14 DMA](../../../../docs/v1-drivers/14-dma.md)。完整安全接线、构建步骤、位宽与跨圈判据、证据表见 [UART取证协议](../../../../labs/uart-dma/README.md)。

## 当前工程事实

- 启动目标STM32F407ZGT6、Flash1MB/SRAM128KB；PF6/PF8低亮LED对应霸天虎源码口径，实际板卡/芯片仍待核实。
- USART1：PA9 TX/PA10 RX、AF7；115200、8N1、OVER8=0、无流控。使用3.3V TTL交叉接TX/RX并共地，适配器VCC不接，不接RS-232或5V。
- clocks_read()按RCC推导HCLK/PCLK2，程序未主动配置PLL；冷复位HSI名义16MHz条件下，四舍五入得到BRR139，理论约115107.91baud（−0.07994%）、位宽8.6875µs。不是所有F407都用84MHz/BRR729；寄存器推导不等于仪器实测。
- DMA2 Stream5 Channel4、64字节循环，HT/TC和IDLE推动消费。流寄存器地址与IRQ68也是固定配置，不能只改stream宏迁移；实际映射须按芯片RM0090核对。源码旧头注释中的“换IDF”不适用于这个裸机F407工程。
- IDLE是空闲服务通知，**不是应用消息边界**。TXE表示可继续写DR，TC才表示停止位已发完。
- 启动发`uart-dma ready\r\n`，随后主循环非阻塞原样回显；不是AT→OK应答或带CRC协议。

| 变量 | 按当前实现解读 |
| --- | --- |
| g_rx_bytes | 成功消费进发送队列的字节总数，不保证包含所有线上字节 |
| g_frames | 历史名称，实际计IDLE通知次数，不是应用帧数 |
| g_overruns | USART ORE/FE/NE、DMA丢弃、发送队列满、流重启等路径累计 |
| g_half_events/g_full_events | HT/TC计数，取每次试验增量 |
| g_hclk/g_pclk2/g_brr | 回读推导的时钟与实际写入BRR；读数仍待采集 |

## 后续构建烧录（本轮未执行）

保留common/behavior相对目录，在本目录及既有兼容Make环境执行：

```bash
make          # build/uart-dma.elf/.bin/.hex/.map
make flash    # OpenOCD/ST-Link verify reset
```

先核身份、供电、SWD及后续写板授权，构建失败停止，不用旧ELF代替。工具版本、固件哈希、构建/verify/冷复位日志见取证协议；make gdb含load，会写板。

最小自检先捕获启动行，再单字节0x55/0x41量双方向位宽并核回显；通过后再做63/64/65与256字节跨圈测试，记录字节比对、rx/IDLE/HT/TC/overruns增量。IDLE次数不必等于应用包数，零接收也不唯一证明stream配置错，应查PA10/AF7/DMAR/NDTR/DMA时钟/映射/IRQ完整链。

64字节缓冲在115200 8N1下半区约2.778ms，属于服务预算，不是无限吞吐或上板通过证据。宿主消费逻辑测试不能替代真实串口与波形。

状态：`hardware_status: pending`，本轮未构建、未烧录、未实测。身份、双方向位宽、构建/verify日志、跨圈原始字节与计数、误差预算和复测仍待完成。
