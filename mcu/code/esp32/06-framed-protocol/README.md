# 06-framed-protocol —— S3 UART1 上的二进制帧协议（INFO/STATUS）

与 STM32F407 侧 `code/stm32/05-framed-protocol` 共用同一公共 codec
（`code/common/reliability`，按源文件编译复用，不复制），同一主机 CLI
`scripts/device-console.py` 解析两板。

## 拓扑（立创·实战派 S3，多功能扩展口）

| 连接 | 说明 |
|---|---|
| USB-TTL TX → GPIO11 | UART1 RX |
| USB-TTL RX → GPIO10 | UART1 TX |
| GND ↔ GND | 3.3V 电平，共地 |
| 115200 8N1 | 无硬件流控 |

文本日志走默认 UART0 控制台（ESP_LOG），与 UART1 二进制协议完全分离。

## 运行

```sh
idf.py set-target esp32s3        # 换 target 会重置 sdkconfig，永远第一步
idf.py build
idf.py -p COMx flash monitor     # 有板时；monitor 会占用 UART0 不影响 UART1
python3 scripts/device-console.py info  --port COMy
python3 scripts/device-console.py status --port COMy --output frames.csv
```

## 与 02-uart-events 的差异（教学要点）

- **事件不是数据**：UART_DATA.size 只是元数据。任务每轮等待事件 ≤5ms，
  之后无论有没有事件都周期调用 `uart_get_buffered_data_len` 分块取数——
  驱动内部事件队列满时可能丢通知（uart.c:1321-1325 只记日志），周期取数兜底。
- **错误路径**：FIFO_OVF/BUFFER_FULL/FRAME_ERR/PARITY_ERR → flush 输入、
  清事件积压、对解析器调用失步（DISCARD）；下一个 0x00 重新同步。
- **TX 有界**：TX ring=0（uart.c:1940 允许），`uart_tx_chars` 返回实际
  接受的字节数；4 帧 TX 队列满时丢新帧并计 `tx_drop`，不覆盖在发帧。
- **时钟**：`esp_timer_get_time()/1000` 截为 uint32 毫秒；不把 FreeRTOS
  tick 当毫秒。

## 测试构建（故障注入）

默认构建返回 UNSUPPORTED。测试构建启用 `CONFIG_RELIABILITY_TEST_FAULTS`
（见 `main/Kconfig`、`sdkconfig.defaults.faults`）：

- `fault --fault 1 --task 0`：uart 任务停止服务（喂帧/解析全停）→
  主机端表现为请求超时（模拟任务卡死，watchdog 工程会用 TWDT 捕捉它）。
- `fault --fault 2 --task 0`：TX 步进暂停，RX 解析照常 → 主机能看到
  STATUS 里 rx_ok 继续增长而响应停发。

故障必须由显式命令触发，上电不自动卡死；恢复通过复位。

## 待上板实测

- [ ] 与 device-console.py 实际收发（info/status 解析正确）
- [ ] UART0 日志与 UART1 协议互不干扰
- [ ] 拔线/噪声后的失步恢复（坏段→分隔符→合法帧可收）
- [ ] 测试构建 fault 1/2 的两种可区分行为
