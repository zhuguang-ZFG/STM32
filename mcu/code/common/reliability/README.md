# code/common/reliability —— 协议与健康监测公共模块

双板（STM32F407 / ESP32-S3）共用的无动态分配 C 模块：帧编解码、错误计数、
健康监测与故障记录。平台工程按源文件复用（不复制），Python CLI 与这里的
C codec 互为交叉验证。

## 文件

| 文件 | 职责 |
|---|---|
| `protocol.h/.c` | 帧格式（COBS + CRC-16/CCITT-FALSE）、逐字节接收状态机（EMPTY/COLLECT/DISCARD）、错误计数 |
| `health.h/.c` | 任务进展监督 API（required_mask/deadline/宽限，evaluate 永久结束宽限） |
| `transport.h/.c` | 4 帧 TX 队列（100ms 截止期、失败后补同步分隔符）+ 512 字节 RX 字节队列（溢出即失步） |
| `service.h/.c` | 最小命令服务：INFO(0x01)/STATUS(0x02)/TEST_FAULT(0x7f)，START/STOP 等返回 UNSUPPORTED |
| `record.h/.c` | 12 字节 .noinit/RTC 保留段故障记录（magic WDG1/version/mask/CRC，写序先失效后发布） |
| `tests.c` | 生产代码行为断言：全切分点、时间回绕、宽限关闭、背压、饱和计数、守护式模糊 |
| `codec-tool.c` | 交叉验证工具：`encode type seq payload_hex` / `decode wire_hex` |

## 线上格式

```
wire = COBS(raw) + 0x00          # 最大 74 字节
raw  = version:u8=1 | type:u8 | sequence:u16LE | length:u16LE
       | payload[0..64] | crc:u16LE
CRC-16/CCITT-FALSE（poly=0x1021, init=0xffff, 不反射），覆盖 CRC 之前的全部 raw 字节
检查串 "123456789" -> 0x29b1
```

响应 type = 请求 type|0x80，回显 sequence，payload 首字节为状态码
（0=OK 1=UNSUPPORTED 2=BAD_PAYLOAD 3=BUSY 4=INTERNAL_ERROR）。
STATUS 成功响应固定 25 字节（uptime/reset_reason/掩码/计数）。

## 运行测试（干净环境）

```sh
cd code/common/reliability
sh probe.sh          # 编译执行全部 C 断言 + CLI 交叉验证；Linux 上额外跑 ASan/UBSan
```

- 依赖：任意 C11 编译器（`HOSTCC` 覆盖，默认 `gcc`）、`python3`。
- `probe.sh` 调 `../../../scripts/device-console.py self-test --c-helper …`，
  完成 C↔Python 双向向量交叉验证；串口依赖仅 `pyserial==3.5`
  （`scripts/device-console-requirements.txt`），离线测试不需要。

## 主机 CLI

```sh
python3 scripts/device-console.py self-test                       # 离线自测
python3 scripts/device-console.py info  --port COM3               # INFO
python3 scripts/device-console.py status --port COM3 --output log.csv
python3 scripts/device-console.py command --port COM3 --type 1
python3 scripts/device-console.py fault  --port COM3 --fault 1 --task 0   # 仅测试固件
```

退出码：0 成功 / 1 自测失败 / 2 设备拒绝 / 3 超时 / 4 串口错误。
不做端口自动探测；开口不主动拉 RTS/DTR（驱动瞬态见 CLI 文件头说明）。

## 边界

- 纯 C11 + 标准库；不含 RTOS/芯片头文件；无动态分配。
- 公共模块自身不加锁：平台层用短临界区串行化 progress/evaluate。
- 故障记录只对"同镜像暖复位"有效，掉电保存不做承诺（见 record.c 注释）。
