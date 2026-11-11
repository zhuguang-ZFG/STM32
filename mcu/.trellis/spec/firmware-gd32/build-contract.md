# GD32 构建与事实边界合同

## 1. 适用范围与触发

- 改 `code/gd32/01-rcu-clock/` 的 `Makefile`、`main.c`、`startup_gd32f4xx.s`、`gd32f4xx.ld` 时读这份。
- 改 `docs/gd32/` 的 G 篇寄存器/时钟结论时，按本合同的"事实来源/待核验"口径写。
- 改 V 篇（GD32VF103）时只适用 §3.4 的文档边界；当前没有可构建的 VF 工程。

## 2. 签名与产物

| 入口 | 输入 | 产物/副作用 |
|---|---|---|
| `mingw32-make` / `make`（`code/gd32/01-rcu-clock`） | xPack `arm-none-eabi-gcc` 15.2.1、`mingw32-make`、Git `usr/bin` | `build/gd32-rcu-clock.elf`、`.bin`、`.map` |
| `npm run firmware:check` | 同上（ARM 工具链在 PATH） | 编译该工程并断言 ELF/Flash 起点/初始 SP/复位向量；写 `build/` |
| GDB/OpenOCD（使用者自备） | ELF 与目标板 | 观察 `g_clock_status`、`g_clock_tree[]`；本工程没有 `flash` 目标 |

编译参数（以 Makefile 为准）：`-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard -O1 -Wall -Wextra -std=c11 -ffreestanding -fno-builtin -DGD32F450 -Wa,--noexecstack`；
链接 `-T gd32f4xx.ld -nostartfiles -Wl,--gc-sections`。`-Wa,--noexecstack` 是对齐 C 目标与启动 `.s` 的 `.note.GNU-stack`，不是关闭检查。

## 3. 数据与环境契约

### 3.1 目标与官方库

- 目标芯片：**GD32F450**；链接脚本按 **GD32F450ZG = 1MB Flash + 256KB SRAM** 写，容量口径**待 UM 核验**。
- 官方库：GD32F4xx Firmware Library **V3.3.3**，GitHub `GigaDevice-GD32-MCU/GD32F4xx_Firmware_Library` @ `10d02f4`；源码缓存 `.trellis/ref/gd32/`（不随仓库分发）。
- 寄存器位定义/行号以 `gd32f4xx_rcu.h` 与 `system_gd32f4xx.c` 注释为准；手册取 GD32F4xx User Manual Rev3.0。无法回到来源的位不写。

### 3.2 时钟与回退

- HXTAL 25MHz 起振，超时回退 IRC16M；不抄官方 demo 的 `while(1)` 死等。
- 电压档：`PMUEN → LDOVS → HDEN`，等 `HDRF` 与 `HDSRF` 回执。
- `FMC_WS_VALUE=6`：保守超配。官方 system 文件不设 FMC 等待，手册未给"频率↔等待"表；这是本工程的显式选择，不是官方推荐值。
- PLL 官方 200M 档：`PSC=25 / N=400 / P=2 / Q=9` → `CK_SYS=200MHz`；总线 AHB/1、APB2/2、APB1/4。
- 切钟后等 `SCSS` 回执为 PLLP；`clock_tree_readback()` 按 SCSS 如实解码当前源，并按 `RCU_PLL` 参数重算频率——回退路径也报真值，不拿"以为的 25MHz"充数。
- `g_clock_status`：`0` PLL 档，`1` HXTAL 起振失败回退 IRC16M，`2` PMU 电压档握手失败，`3` PLL 启动失败，`4` 切钟失败。`g_clock_tree[]` 依次 CK_SYS/CK_AHB/CK_APB1/CK_APB2。
- CK_OUT0：PA8、AF0，源 PLLP、4 分频，**理论 50MHz**；未上板测频前只能写"理论/待实测"。

### 3.3 链接与启动

- Flash `0x08000000` 1MB、RAM `0x20000000` 256KB；`.text` 起始 `KEEP(*(.isr_vector))`，允许 GD32 把向量表并入 `.text`。
- `.data` 用 `AT(__text_end__)` 存放加载地址；`.bss` 清到 `__bss_end__`；丢弃 `.ARM.exidx/.ARM.extab/.comment/.note*`。
- 启动文件提供 `Reset_Handler` 与栈顶符号；`firmware:check` 读 ELF 符号与 bin 前两个字，断言初始 SP 与复位向量（最低位 1）。
- 容量溢出不一定编译报错，只会运行踩雷；改链接脚本必须同时核对实际料号与 UM。

### 3.4 GD32VF103（V 篇）的文档边界

- V 篇是 RISC-V（Bumblebee 内核，RV32IMAC，108MHz）教学线，覆盖 `docs/gd32/05-riscv-toolchain.md` 至 `09-gpio-minimal.md`。
- 已写事实：`riscv-none-elf-gcc` 三元组与 `-march/-mabi`、无 FPU/CPACR、`sp` 软件设置、CLIC 两维优先级与 `shv` 向量模式、MTIME 取代 SysTick、RCU 108MHz 档、64 位 MTIME 读写纪律。
- **没有**对应的 `code/gd32/` 可构建工程、Makefile、链接脚本或 `projects.json` 登记。不得写 `make`/`idf.py`/烧录命令，也不得声称已编译或上板。
- 新增 VF 工程必须单独立项：工具链、启动文件、链接脚本、证据链都要有，不能把 F4 的构建器改一个宏就宣称支持 RISC-V。

## 4. 校验与错误矩阵

| 事件 | 结果 |
|---|---|
| 缺 `arm-none-eabi-gcc` | 编译失败；提示装 xPack 15.2.1 并加 PATH |
| 项目代码有警告 | `-Wall -Wextra` 下必须零警告；不关警告换通过 |
| HXTAL 不起振 | `g_clock_status=1`，回退 IRC16M，继续运行 |
| PMU 握手失败 | `g_clock_status=2`，回退 |
| PLL 未锁定 | `g_clock_status=3`，回退 |
| 切 PLLP 失败 | `g_clock_status=4`，回退 |
| `FMC_WS_VALUE` 欠配 | 可能取指跑飞；改小必须有手册/实测依据 |
| 链接容量与料号不符 | 可能编译通过但运行踩雷；容量待 UM 核验 |
| `firmware:check` 的 SP/复位向量不符 | 非零退出并点名工程 |
| 把 CK_OUT0 理论值写成实测 | 违规；补测频记录或改写结论 |
| 给 V 篇写构建/烧录命令 | 违规；当前无 VF 工程 |

## 5. 正常、边界与失败案例

- 正常：`cd code/gd32/01-rcu-clock && mingw32-make` → 零警告 → `build/gd32-rcu-clock.bin`；GDB 看 `g_clock_status=0`、`g_clock_tree=[200M,200M,50M,100M]`（按分频计算）。
- 边界：HXTAL 故障时 `g_clock_status=1`，`clock_tree_readback` 报 IRC16M 16MHz；这不是"PLL 失败"，不要把状态码混用。
- 边界：`--bleed` 之类参数不属于本工程；GD32 构建没有场景/变体，`firmware:check` 只跑一次 `make -B`。
- 失败：直接改 `gd32f4xx.ld` 的 LENGTH 让链接通过，却不核对料号/UM。正确：先确认容量来源，再改脚本并记录。
- 失败：把 F450 的 PLL 参数套到 F470 240MHz 档。正确：F470 档位与参数另查官方 system 文件，章节里分开写。
- 失败：因为 V 篇有 RISC-V 章节，就在 `code/gd32/` 造一个空壳工程充数。正确：没有可复现工程就只写文档事实。

## 6. 测试与断言

| 来源 | 已覆盖 |
|---|---|
| `npm run firmware:check` | 编译、ELF 存在、`.isr_vector|.text` 起于 `0x08000000`、`Reset_Handler`/栈符号、bin 初始 SP 与 Thumb 复位向量 |
| `code/gd32/01-rcu-clock/README.md` | 时钟步骤、调试观察点、FMC/容量/CK_OUT0 待核验清单 |
| `docs/gd32/` G 篇 | 寄存器位/库行号对照；章节里的"手册留白"标注 |

未覆盖：FMC 等待周期的精确值、F450ZG 实际容量、CK_OUT0 实际频率、V 篇任何构建都没有自动测试；必须上板/查 UM 后回填，未回填保持待核验。

## 7. 错误与正确做法

- 错误：把 `FMC_WS_VALUE=6` 写成"官方要求 6 等待"。正确：官方 system 不设，手册无表；这是保守超配，待 UM 回填。
- 错误：`g_clock_status` 只定义 0/1，忽略 PMU/PLL/切钟失败。正确：0–4 五个状态，回退路径都报真值。
- 错误：CK_OUT0 理论 50MHz 直接写"实测 50MHz"。正确：上板测频并记录仪器/条件。
- 错误：把 G 篇的 ARM 启动/中断规则套到 V 篇 RISC-V。正确：V 篇按 CLIC/MTIME/软件 `sp` 单独写。
- 错误：为让 `firmware:check` 通过而改链接脚本容量或关警告。正确：先核对料号/UM 与源码，再改构建。
