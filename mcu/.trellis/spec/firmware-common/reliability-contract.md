# 可靠性协议与健康监测合同

## 1. 适用范围与触发

- 改 `code/common/reliability/protocol.[ch]`、`transport.[ch]`、`health.[ch]`、`service.[ch]`、`query.c`、`record.[ch]` 时读这份。
- 改 `scripts/device-console.py` 的帧编解码、命令、退出码或超时行为时读这份。
- 改 `code/common/logger/` 时：先读 [logger-contract](../docs-site/logger-contract.md)（SAMPLE/TLV/配置/并发），
  本层只覆盖它复用的底层帧与队列。
- 平台 port（UART/USB/中断）归 [firmware-stm32](../firmware-stm32/index.md) / [firmware-esp32](../firmware-esp32/index.md)；本层不定义板级引脚。

## 2. 签名与产物

### 2.1 C API（`code/common/reliability/*.h`）

```c
/* protocol.h */
uint16_t protocol_crc(const uint8_t *, size_t);
size_t protocol_cobs_encode(const uint8_t *, size_t, uint8_t *, size_t);
size_t protocol_cobs_decode(const uint8_t *, size_t, uint8_t *, size_t);
size_t protocol_encode(const frame_t *, uint8_t *wire, size_t capacity);
protocol_error_t protocol_decode(const uint8_t *encoded, size_t, frame_t *);
bool protocol_rx_init(protocol_rx_t *, uint32_t timeout_ms);
void protocol_rx_poll(protocol_rx_t *, uint32_t now);
void protocol_rx_loss(protocol_rx_t *);
bool protocol_rx_feed(protocol_rx_t *, uint8_t, uint32_t now, frame_t *);
uint32_t protocol_errors(const protocol_stats_t *);

/* transport.h */
void protocol_tx_init(protocol_tx_t *);
bool protocol_tx_enqueue(protocol_tx_t *, const frame_t *);
void protocol_tx_step(protocol_tx_t *, uint32_t now, tx_write_fn, void *);
void byte_queue_loss(byte_queue_t *);
bool byte_queue_push(byte_queue_t *, uint8_t);
bool byte_queue_pop(byte_queue_t *, uint8_t *, bool *);

/* health.h */
bool health_init(health_t *, uint32_t required, const uint32_t deadlines[8], uint32_t grace, uint32_t now);
bool health_progress(health_t *, uint8_t id, uint32_t now);
health_result_t health_evaluate(health_t *, uint32_t now);
bool health_supervise(health_supervisor_t *, health_result_t);

/* service.h / record.h */
void device_service_init(device_service_t *, uint8_t platform, uint32_t reset, bool health, fault_fn, void *);
void device_service_feed(device_service_t *, uint8_t, uint32_t now);
bool device_service_query(const device_service_t *, const frame_t *, frame_t *, uint32_t now);
void fault_record_save(volatile fault_record_t *, uint32_t mask);
bool fault_record_read(const volatile fault_record_t *, bool warm_watchdog_reset, uint32_t *mask);
bool fault_record_take(volatile fault_record_t *, bool warm, uint32_t *mask);
```

### 2.2 主机 CLI（`scripts/device-console.py`）

```text
self-test [--c-helper PATH]
info | status | log | start | stop | save
command --type N [--payload HEX]
fault --fault N [--task N]
configure --period 100 --filter-shift 2
record --seconds 10 --output FILE
公共参数：--port / --baud 115200 / --timeout 1.0 / --output
```

退出码：`0` 成功，`1` 自测/用法失败，`2` 设备拒绝（status≠OK），`3` 超时，`4` 串口错误。

## 3. 数据与环境契约

### 3.1 线上帧

```text
wire = COBS(raw) + 0x00                 # 最大 74 字节
raw  = version:u8=1 | type:u8 | sequence:u16LE | length:u16LE
       | payload[0..64] | crc:u16LE     # 最大 72 字节
CRC-16/CCITT-FALSE（poly=0x1021, init=0xffff, 不反射），覆盖 CRC 之前的全部 raw 字节
检查串 "123456789" -> 0x29b1
```

- 上限：`PAYLOAD_MAX=64`、`RAW_MAX=72`、`ENCODED_MAX=73`、`WIRE_MAX=74`；任何越界在编码前拒绝，不做截断。
- 响应 `type = 请求 type | 0x80`，回显 `sequence`，payload 首字节是状态码：
  `0 OK / 1 UNSUPPORTED / 2 BAD_PAYLOAD / 3 BUSY / 4 INTERNAL_ERROR`。
- `INFO(0x01)` 成功响应 payload 5 字节：status、schema=1、platform（1=STM32F407，2=ESP32-S3）、capabilities u16
  （bit0 protocol、bit1 health、bit2 test_fault、bit3 logger）。
- `STATUS(0x02)` 成功响应固定 25 字节：status、schema=1、uptime u32、reset_reason u32、required u8、overdue u8、flags u8、
  ok u32、errors u32、tx_dropped u32。
- `TEST_FAULT(0x7f)` 仅在测试固件且入队成功时执行副作用；参数非法返回 `BAD_PAYLOAD`，无 fault 回调返回 `UNSUPPORTED`。
  其它未实现命令返回 `UNSUPPORTED`；不得为未知 type 编造成功响应。

### 3.2 RX 状态机与队列

- 状态只有 `EMPTY / COLLECT / DISCARD`；`protocol_rx_init(timeout_ms)` 要求 `0 < timeout_ms < 0x80000000`。
- 字节在分隔符 `0x00` 处成帧；解码失败计入对应错误计数（COBS/version/length/CRC/oversize），不抛出。
- `protocol_rx_poll` 在 COLLECT 超时后转 DISCARD、清空缓冲并累加 `timeout`；下一次分隔符后重新同步。
- `protocol_rx_loss` 用于上层检测到丢字节时主动失步；恢复前不得把半帧当完整帧。
- RX 字节队列 512 字节；溢出时丢弃整个不确定段并置 `loss`，损失计数先于新字节交付。
- 所有计数用饱和加法，除有意设计的 sequence/timestamp 回绕外不自然回绕。

### 3.3 TX

- 发送队列 4 帧；满时丢弃新帧并累加 `dropped`，返回 false。
- 每帧 100 ms 截止期；超时丢弃当前帧、置 `sync=true`。同步中的下一次发送先写一个 `0x00` 分隔符，再写帧。
- 平台写函数短写时，剩余字节留在当前帧继续写；不得把半帧当已发送。

### 3.4 健康监测

- `required_mask` 只能使用低 8 位；每位的 `deadline_ms` 必须非零且 `< 0x80000000`；`grace_ms` 同样有上限。
- `health_progress(id, now)` 只接受 required 中的位；记录 `last_ms` 并置 `seen_mask`。
- `health_evaluate`：宽限期内 `may_feed=true`；宽限期在"所有 required 都见过"或"到达 grace"时永久结束。
  结束后，未见过或 `now - last_ms >= deadline` 的位进入 `overdue_mask`，`may_feed = overdue_mask == 0`。
- `health_supervise` 首次 `may_feed=false` 时锁存 `restart_latched` 与首个 overdue 掩码；锁存后不再返回可喂狗。
- 公共模块自身不加锁；平台层用短临界区串行化 `progress/evaluate`。不拥有硬件看门狗。

### 3.5 故障记录

- 12 字节、无 ABI padding：magic `0x57444731`（"WDG1"）、version=1、保留字节=0、mask u32、CRC u16（覆盖前 10 字节）。
- 写入顺序：先把前 4 字节清零使旧记录失效，再写 4..11，最后发布 magic；写到一半复位不会留下"看似有效"的记录。
- 读取只在 `warm_watchdog_reset=true` 时成立；冷启动/掉电保存不做承诺。
- `fault_record_take` 读取后清 magic，避免下一次无关暖复位复用旧证据。

### 3.6 CLI 行为

- 串口子命令必须显式 `--port`；不做端口自动探测。
- `command` 默认单次尝试、不自动重试；`fault` 绝不自动重试。
- 重试前先补发 `0x00` 同步分隔符；响应必须同时匹配 `sequence` 与 response type；无关帧只记日志、不延长等待期限。
- 打开串口不主动拉 RTS/DTR，但部分 USB 转串口驱动仍有毫秒级瞬态；上电/复位行为以上板实测为准。
- `record` 只收不发，持续解码 `0x10` SAMPLE 并落 CSV；零条样本返回 `3`（超时），不是成功。
- `self-test` 为纯离线；`--c-helper` 时与 C codec 双向交叉验证。

## 4. 校验与错误矩阵

| 输入/事件 | 结果 |
|---|---|
| payload > 64 / raw > 72 / wire > 74 | 编码前拒绝（`FrameError`/失败返回），不截断 |
| version ≠ 1 / length 与 raw 不符 / CRC 不符 | 解码失败并计入对应错误计数 |
| COBS code 块非法 / 块内出现 0 | `cobs: code block` / `cobs: zero inside block` |
| RX 半帧超时 | 转 DISCARD、清缓冲、`timeout++`；后续字节重新同步 |
| TX 队列满 | 丢新帧、`dropped++`、返回 false |
| TX 单帧超过 100 ms | 丢帧、`dropped++`、置同步态 |
| RX 队列溢出 | 丢整个不确定段、`loss=true`、`dropped++` |
| `health_init` 的 required=0、越界位、deadline=0/过大 | 返回 false，不进入"总是健康" |
| 未见过 required 位或超过 deadline | 对应位进 `overdue_mask`，`may_feed=false` |
| 暖复位标志为 false | `fault_record_read` 返回 false，不读取记录 |
| 记录 magic/version/CRC 不符 | 返回 false |
| CLI 未给 `--port` | 打印"串口子命令需要 --port（不做自动探测）"，退出 1 |
| CLI 响应 sequence/type 不匹配 | 继续等；无关帧不延长期限 |
| CLI 设备 status ≠ OK | 退出 2 |
| CLI 超时 / 串口异常 | 退出 3 / 4 |

## 5. 正常、边界与失败案例

- 正常：`self-test` 离线跑 C/Python 双向量；`status` 先发 INFO 取平台号，再发 STATUS 解析 25 字节。
- 边界：`0x00` 既是分隔符又是合法负载字节；编码器必须用 COBS 转义，解码器按 code 块恢复，不能按字节 `split(0)`。
- 边界：sequence 回绕是合法的；不要把"新 sequence 小于旧 sequence"判为错误。
- 边界：暖复位记录只对同镜像成立；换镜像/冷启动必须视为无记录。
- 失败：在 ISR 里调用阻塞式 TX 或动态分配。公共层无动态分配，TX 是显式 `step` 推进；ISR 只喂字节/入队，平台层决定锁。
- 失败：把 `STATUS` 的 25 字节按旧版 24 字节解析，或把 INFO 的 capability 位顺序猜反；以 `query.c` 与 `device-console.py` 两侧为准。

## 6. 测试与断言

| 来源 | 已覆盖 |
|---|---|
| `code/common/reliability/tests.c` | CRC/COBS 向量、全切分点、RX 超时/失步、时间回绕、宽限关闭、TX 背压、饱和计数、守护式模糊 |
| `code/common/reliability/probe.sh` | 编译 `tests.c` 并执行；构建 `codec-tool`；调用 `device-console.py self-test --c-helper` 做 C↔Python 双向交叉；Linux ASan/UBSan |
| `scripts/device-console.py` 的 `self_test()` | 编码/解码/截断/坏 CRC/坏 COBS/边界长度；`--c-helper` 时逐向量对拍 |
| `tests/device-cli.test.mjs` | CLI 公共参数可放在子命令前后 |
| `tests/logger-cli.test.mjs` | logger payload、TLV 解析与非法配置拒绝（离线，不碰串口） |

未覆盖：真实串口的 RTS/DTR 瞬态、驱动丢字节、平台临界区实现没有自动测试；这些只能上板或按平台记录，不得写成"协议层已验证"。

## 7. 错误与正确做法

- 错误：C 侧改了状态码/长度，只改 C 测试。正确：`query.c`、`device-console.py` 与 `tests.c` 三处同步；`self-test --c-helper` 必须过。
- 错误：RX 超时后直接把旧缓冲接上新字节。正确：转 DISCARD，等分隔符重新同步；半帧永远不成帧。
- 错误：TX 队列满时覆盖最旧帧。正确：丢新帧并计数；覆盖会让请求与响应 sequence 错配。
- 错误：把暖复位记录当掉电持久化。正确：明确"仅同镜像暖复位"，冷启动按无记录处理。
- 错误：CLI 超时后无限重试，或把无关帧当响应。正确：单次尝试、显式重试、sequence+type 双匹配，重试前补 `0x00`。
- 错误：在公共模块里加 RTOS 锁/动态内存。正确：保持纯 C11 + 标准库；锁与内存由平台层负责。
