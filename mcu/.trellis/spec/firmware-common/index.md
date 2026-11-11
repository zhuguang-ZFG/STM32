# firmware-common 规范索引

`code/common/` 的**跨板公共代码**：可靠性协议、健康监测、传感器 logger、纯逻辑取证工具，
以及 `code/c/`、`code/toolchain/` 里"不需要开发板"的宿主机/交叉取证脚本。
STM32F407 与 ESP32-S3 按源文件复用这些模块，不复制。

| 文件 | 内容 |
|---|---|
| [reliability-contract.md](reliability-contract.md) | 74B 线上帧、CRC/COBS、状态码、RX/TX 队列、健康监测、故障记录、`device-console.py` 的 CLI 与退出码 |
| [probe-contract.md](probe-contract.md) | 宿主机/交叉/芯片取证脚本的工具变量、产物、跳过语义与"退出码 0 ≠ 上板通过" |
| [../docs-site/logger-contract.md](../docs-site/logger-contract.md) | 共享传感器 logger 的 SAMPLE/TLV、配置恢复与运行期并发合同（保留原路径，不搬移、不复制） |

## 适用范围

- 改 `code/common/reliability/`、`code/common/logger/`、`code/common/behavior/`、`scripts/device-console.py`。
- 改 `code/c/`、`code/toolchain/` 的 probe 脚本或它们的产物。
- 改 `code/projects.json` 中 `common-*` 与 `host-probe` 工程的登记：字段规则归 [quality-contract](../docs-site/quality-contract.md)，本层只说明取证语义。

## 动手前必读

- 改协议字节、状态码或超时：读 [reliability-contract.md](reliability-contract.md)；C 与 Python 必须互核，不能只改一边。
- 改 logger：先读 [logger-contract](../docs-site/logger-contract.md)，再读本层；SAMPLE 64B 与 TLV 布局不在本层重复。
- 改 probe/取证：读 [probe-contract.md](probe-contract.md)。先写清这次结论属于宿主机、交叉反汇编、芯片编译还是上板实测。
- 平台适配：板级 port/中断/时钟规则归 [firmware-stm32](../firmware-stm32/index.md) 与 [firmware-esp32](../firmware-esp32/index.md)，本层不复制。

## 快速命令

```bash
sh code/common/reliability/probe.sh      # C 断言 + C/Python 双向向量；Linux 额外 ASan/UBSan
sh code/common/logger/probe.sh           # logger 生产函数 + EEPROM 恢复；Linux 额外 sanitizer
sh code/common/behavior/probe.sh         # capture/时钟/DMA 环形缓冲行为
python scripts/device-console.py self-test   # 离线 codec 自测，不碰串口
npm run firmware:check                   # 非 ESP 全工程：host-probe/host-make/arm-make + 登记 probe
npm run test                             # 含 tests/device-cli.test.mjs、tests/logger-cli.test.mjs
```

## 质量检查

| 改动 | 检查 |
|---|---|
| 协议编解码/状态机 | `sh code/common/reliability/probe.sh` + `python scripts/device-console.py self-test` |
| CLI 参数/退出码 | `node --test tests/device-cli.test.mjs`；真实串口命令另需硬件 |
| logger 核心 | `sh code/common/logger/probe.sh` + `node --test tests/logger-cli.test.mjs` |
| 纯逻辑取证 | 对应 `probe.sh`；只证明宿主机语义时在提交说明里写清，不冒充芯片/上板 |
| 工程登记 | `npm run projects:check`；`probe` 只允许 arm-make 且文件真实存在 |

## 金样例

- 协议向量与镜像实现：`code/common/reliability/tests.c`（全切分点、时间回绕、背压、饱和计数）与 `codec-tool.c`。
- CLI 契约：`scripts/device-console.py` 文件头（线上格式、命令、退出码）与 `tests/device-cli.test.mjs`。
- 行为取证：`code/common/behavior/capture.h`、`circular.h`（捕获频率与 DMA 环形消费的边界判定）。
