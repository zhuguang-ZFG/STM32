# 取证合同：宿主机、交叉反汇编、芯片编译与上板

## 1. 适用范围与触发

- 改 `code/c/`、`code/toolchain/` 的 `probe.sh`，或改 `code/common/*/probe.sh`、`scripts/check-firmware.mjs` 时读这份。
- 在正文/README/任务记录里写"已验证""可复现""通过"之前，先按本合同标明证据等级。
- 本合同不规定某条指令的语义；它只规定"什么证据能支持什么结论"。

## 2. 签名与产物

每个 probe 都是普通 shell 脚本，直接 `sh <path>`。本仓库实际接受的变量（以各脚本源码为准，不要外推成全局约定）：

| 脚本（手动 `sh` 运行） | 变量 | 行为/产物 |
|---|---|---|
| `code/c/01-memory-model/probe.sh` | `ARM_PREFIX`（默认 `arm-none-eabi-`） | 宿主段归属 + 交叉反汇编；缺工具链时报错退出 |
| `code/c/02-pointer/probe.sh` | `ARM_PREFIX`、`HOST_CC`（默认 `gcc`） | 宿主断言 + 交叉对照 |
| `code/c/03-volatile/probe.sh` | `CC`（默认 `gcc`） | 宿主 `-S` 对照；**可选**交叉段：`arm-none-eabi-gcc`/`objdump` 不在 PATH 时打印 `~… 交叉段不跑`，仍 exit 0 |
| `code/c/04-struct-abi/probe.sh` | `CC`（默认 `gcc`） | 宿主 ABI/布局断言 |
| `code/c/05-func-pointer/probe.sh` | `CC`、`ARMPREFIX`（默认 `arm-none-eabi-`） | 宿主断言；缺交叉链时打印"跳过反汇编"，宿主部分仍有效 |
| `code/c/06-abi-stack/probe.sh` | `CC`、`ARMPREFIX` | 宿主栈帧断言；缺交叉链时跳过汇编核对 |
| `code/c/07-ub-misra/probe.sh` | `CC`、`ARMPREFIX`、`XPACK` | 宿主 UBSan/优化行为；缺 UBSan 运行库时明确打印跳过 |
| `code/toolchain/01-four-steps/probe.sh` | `ARM_PREFIX` | 四步构建产物解剖；缺 `arm-none-eabi-gcc` 直接失败 |
| `code/toolchain/02-elf/probe.sh` | `ARM_PREFIX` | ELF 段/符号/大小端取证 |
| `code/toolchain/03-linker/probe.sh` | `ARM_PREFIX`、`CCM_GAP`（默认 1） | 六刀链接取证；`CCM_GAP=0` 不落 128MB 中间 bin，改跑换算式；写 `build/` |
| `code/common/reliability/probe.sh` | `HOSTCC`（默认 `gcc`）、`PYTHON`（默认 `python3`） | C 断言 + `codec-tool` ↔ Python 交叉验证；Linux 追加 ASan/UBSan |
| `code/common/logger/probe.sh` | `HOSTCC` | logger/store 生产函数 + protocol；Linux 追加 sanitizer |
| `code/common/behavior/probe.sh` | `HOSTCC` | capture/时钟/DMA 环形行为 |
| `npm run firmware:check` | `MAKE`（Windows 默认 `mingw32-make`，其它 `make`） | 遍历非 ESP 工程；host-probe 跑 entry、host-make 跑 `-B run asm-arm`、arm-make 逐场景/变体构建并跑登记 probe；写各工程 `build/`，不烧录 |

`firmware:check` 对每个 arm-make 工程还断言：ELF 存在、`.isr_vector|.text` 起于 `0x08000000`、`Reset_Handler`/栈符号存在、
bin 前两个字的初始 SP 与复位向量（最低位为 1）；多场景还做"相邻场景不同 + 切回首场景字节一致 + 非法场景非零退出"。
ESP-IDF 工程不在该脚本内，芯片编译证据只来自 CI 的 `esp32` job 或本机 `idf.py`。

**`firmware:check` 不是"逐个跑所有 probe.sh"**：`host-probe` 才执行 `entry`；`host-make` 执行 `make -B run asm-arm`
（`code/c/03-volatile` 属于这一类，`asm-arm` 硬依赖 `arm-none-eabi-gcc`），不会执行它的 `probe.sh`；
只有 `arm-make` 且显式登记 `probe` 的工程才追加 `sh probe.sh`。所以 `c-03-volatile/probe.sh` 里"缺交叉工具只跳过交叉段"
的语义只在手动 `sh` 时成立；`probe` 钩子也只允许 arm-make。

## 3. 数据与环境契约

### 3.1 四级证据，不许越级

| 等级 | 能证明 | 不能证明 |
|---|---|---|
| 宿主机语义 | C 语言/编译器/ABI 在该机器上的行为、算法边界 | 目标芯片的时序、寄存器副作用、板上电平 |
| 交叉反汇编/链接 | 目标 ISA 的指令选择、段归属、链接脚本、向量表落位 | 芯片实际执行、Flash/RAM 容量、外设 |
| 芯片编译 | 目标工程能过编译/链接、体积、符号 | 运行时行为、外设、时钟、功耗 |
| 上板实测 | 真实硬件上的输出/时序/波形 | 换板、换批次、换温度仍成立（需注明条件） |

- `exit 0` 只表示脚本自己没失败；若脚本打印了"跳过/不跑/降级"，被跳过的那一段没有证据。
- 报告用"已执行/失败/跳过/未执行"四态；不得把"跳过"写成"通过"。

### 3.2 工具链与缓存

- ARM 工程默认 `arm-none-eabi-gcc`；`code/c/07-ub-misra/probe.sh` 另有 `XPACK` 路径回退。
- `code/toolchain/03-linker/probe.sh` 的六刀会 `sed` 出候选链接脚本到 `build/`，原文不动；每刀先打 diff，结果可复跑。
  第 5 刀的中间态会写出约 128MB 的 bin，量完删除；不想落盘用 `CCM_GAP=0`。
- `firmware:check` 的 probe 头文件对账依赖 `.trellis/ref/cmsis`；CI 固定 cmsis-device-f4 `v2.6.11` + CMSIS_5 `5.9.0` 并校验 sha256。
  本机没有该缓存时，相关对账分支要么明确失败，要么在报告里记"未执行"，不能静默变绿。
- 交叉反汇编的判定只对当前钉住的工具链版本负责；换版本必须重新记录版本号与输出差异。

## 4. 校验与错误矩阵

| 事件 | 结果 |
|---|---|
| `code/toolchain/03-linker/probe.sh` 找不到 `${ARM_PREFIX}gcc` | 打印"找不到 … 先把工具链加进 PATH"并非零退出 |
| `code/c/03-volatile/probe.sh` 缺交叉工具 | 只跳过交叉段，打印 `~arm-none-eabi-gcc/objdump 不在 PATH，交叉段不跑`；宿主断言仍必须通过 |
| `code/c/05/06/07` 缺交叉链 | 打印"跳过反汇编/汇编核对"，宿主断言仍有效；报告中必须写"仅宿主" |
| `code/c/07` 缺 UBSan 运行库 | 明确打印跳过，不把编译期防线冒充运行期证据 |
| `firmware:check` 的 arm 工程产不出 ELF | 非零退出；不继续用旧 `build/` 充数 |
| 初始 SP/复位向量与符号不符 | 非零退出并点名工程 |
| 场景切换产物相同/切回首场景不可复现/非法场景零退出 | 非零退出 |
| 变体 normal/faults 产物相同 | 非零退出 |
| 登记了 `probe` 但文件不存在 | `projects:check` 先失败，`firmware:check` 不会跑到 |
| 只跑了宿主段就宣称"板上验证" | 违规；必须补上板证据或改写结论 |

## 5. 正常、边界与失败案例

- 正常：改 `volatile` 章节 → 跑 `sh code/c/03-volatile/probe.sh`（宿主必过），有交叉链时再记录反汇编差异；
  提交说明写"宿主机 + 交叉反汇编"，不写"上板"。
- 边界：`CCM_GAP=0` 只影响第 5 刀是否落盘，换算式与结论不变；不能拿"没落盘"当"没跑"。
- 边界：`firmware:check` 写各工程 `build/`，不是只读命令；在共享工作区跑之前先确认没有别的会话正在用同一目录。
- 失败：把 `exit 0` 当"全部证据通过"。脚本内部有跳过分支时，exit 0 只覆盖它实际跑到的段。
- 失败：用宿主机 GCC 的优化结果解释 ARM 目标代码。两者 ISA/ABI 不同，只能作教学对照，不能作芯片结论。

## 6. 测试与断言

| 来源 | 已覆盖 |
|---|---|
| `code/common/reliability/probe.sh` + `tests.c` | C 断言、CRC/COBS 向量、RX 全切分点、时间回绕、队列背压、饱和计数、守护式模糊；Linux sanitizer |
| `code/common/logger/probe.sh` | SAMPLE/TLV、配置校验、EEPROM 两槽恢复、故障注入 |
| `code/common/behavior/probe.sh` | 捕获周期边界、DMA 环形消费与不确定数据丢弃 |
| `tests/device-cli.test.mjs` | CLI 公共参数可放在子命令前后 |
| `tests/catalog.test.mjs` | `probe` 钩子只允许 arm-make 且文件真实存在 |
| `.github/workflows/quality.yml` | CMSIS 固定版本 + sha256、`firmware:check`、ESP32 变体矩阵 |

未覆盖：各 probe 的"跳过分支"没有自动断言；新增/修改跳过条件时必须手工跑一次缺工具场景并记录输出。

## 7. 错误与正确做法

- 错误：`command -v arm-none-eabi-gcc || true` 后继续，最后打印"全部通过"。正确：明确打印跳过段，并让报告只声明实际执行的证据。
- 错误：用 `make` 成功证明中断能进、时钟正确。正确：编译只证明链接与符号；运行时结论要上板或明确标为模型/理论。
- 错误：为让脚本在 CI 变绿而删掉 `-Werror` 或把交叉段整段删除。正确：保留跳过语义，另在 CI 装工具链；确要放宽必须写明理由与影响面。
- 错误：把 `firmware:check` 说成"全固件验证"。正确：它只覆盖非 ESP 工程；ESP32 归 IDF 矩阵，上板归实测。
