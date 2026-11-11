# 05-framed-protocol —— USART1 二进制帧协议（INFO/STATUS）

寄存器级实现与公共模块 `code/common/reliability` 的对接示例：同一套 codec
同时喂 STM32F407 与 ESP32-S3，主机用同一个 CLI 解析。

## 拓扑

| 连接 | 说明 |
|---|---|
| USB-TTL TX → PA10 | USART1_RX（AF7） |
| USB-TTL RX → PA9  | USART1_TX（AF7） |
| GND ↔ GND | 3.3V 电平，共地 |
| 115200 8N1 | 无硬件流控 |

协议口只发二进制帧，**不混任何文本日志**；调试走 SWD 读 `g_*` 观测量。
S3 侧默认 UART0 的文本日志与本工程无关。

## 运行

```sh
make                      # 构建；arm-none-eabi-gcc + mingw32-make 在 PATH
make flash                # OpenOCD + ST-Link（有板时）
python3 scripts/device-console.py info   --port COMx
python3 scripts/device-console.py status --port COMx --output frames.csv
```

INFO 能力位只有 `protocol`（bit0）：本工程不接 health、不开故障注入；
`fault` 命令按合同返回 UNSUPPORTED。

## 实现要点（与 03-uart-dma 的差异）

- 帧边界由协议定界（COBS + 0x00），**IDLE 只是"该搬积压了"的通知**，不再判帧。
- DMA 错误（TEIF）、UART 错误（ORE/FE/NE）、字节队列溢出都会把解析器推入
  DISCARD：丢掉不确定的残段，下一个 0x00 重新同步，之后的合法帧照常收。
- 响应经 4 帧 TX 队列 + TXE 轮询发送；写满/超时丢帧并计数 `tx_drop`，
  队列满时新响应直接丢弃（不覆盖正在发送的帧）。
- 复位原因取自 RCC_CSR 的原因位（bit25..31，stm32f407xx.h:10320-10333），
  在 main 开头读取；本工程不清 RMVF，证据留给下一次复位。

## 待上板实测

- [ ] 与 device-console.py 实际收发（info/status 解析正确）
- [ ] 波特率实测（HSI 16MHz 下 BRR=139 的实际线速）
- [ ] 噪声注入后的失步恢复（坏段→分隔符→合法帧可收）
- [ ] TX 队列满时的 tx_drop 计数与恢复
