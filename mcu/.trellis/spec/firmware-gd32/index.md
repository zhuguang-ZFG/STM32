# firmware-gd32 规范索引

`code/gd32/` 与 `docs/gd32/` 的 GD32 线：**GD32F4xx（ARM Cortex-M4F）寄存器级工程** +
**GD32VF103（RISC-V）迁移章节**。两条线共享"对照 STM32 学差异"的方法，但可构建产物只有 G 篇一个工程。

| 文件 | 内容 |
|---|---|
| [build-contract.md](build-contract.md) | GD32F4 工程的工具链、时钟/PLL、FMC 等待、链接脚本、调试观察点、待核验清单与 GD32VF 的文档边界 |

## 适用范围

- 改 `code/gd32/01-rcu-clock/` 的 `Makefile`、`main.c`、启动文件、链接脚本时读 [build-contract.md](build-contract.md)。
- 改 `docs/gd32/` 的 G 篇（00–04）时，寄存器/位域结论必须能回到 `main.c` 注释里的库版本与行号。
- 改 V 篇（05–09，GD32VF103）时，只写现有章节与工具链事实；**不要虚构可构建的 RISC-V 工程**。
- 共享 ARM 启动/向量表规则见 [firmware-stm32](../firmware-stm32/index.md)；本层只写 GD32 差异，不复制一套通用启动规范。

## 动手前必读

- 先确认结论属于哪一类：官方库位定义、官方手册、理论推算、上板实测。README 的"待核验清单"必须保持可见。
- G 篇工程目标是 **GD32F450**（`-DGD32F450`），不是 F407；链接脚本按 F450ZG 1MB Flash / 256KB SRAM 写，但容量待 UM 核验。
- `FMC_WS_VALUE=6` 是保守超配值；官方 system 文件不设 FMC 等待，手册也未给出"频率↔等待"对照表。不要把它写成官方推荐值。
- CK_OUT0（PA8/AF0）输出 PLLP/4 = 理论 50MHz；未上板实测前只能写"理论值/待实测"。
- V 篇是 RISC-V（Bumblebee、CLIC、MTIME），与 G 篇的 ARM 启动/中断模型不同；不要把 G 篇的 Makefile 套到 V 篇。

## 快速命令

```bash
# 需要 xPack arm-none-eabi-gcc 15.2.1（与 STM32 工程同一套）+ mingw32-make + Git usr/bin
cd code/gd32/01-rcu-clock && mingw32-make
# 产物：build/gd32-rcu-clock.{elf,bin,map}

npm run firmware:check     # 会编译该 arm-make 工程并校验 SP/复位向量/ELF
```

本工程没有 `flash` 目标；烧录方式与目标板由使用者按 G0/G1 章节自行接。不要从 Makefile 推断已支持某款下载器。

## 质量检查

| 改动 | 检查 |
|---|---|
| 时钟/PLL/分频 | `make` 零警告；对照 `system_gd32f4xx.c` 与 `gd32f4xx_rcu.h` 的行号；GDB 看 `g_clock_status` 与 `g_clock_tree[]` |
| 链接脚本/启动 | `npm run firmware:check` 的 Flash 起点、初始 SP、Thumb 复位向量断言；GD32 允许向量表并入 `.text` |
| FMC 等待/容量 | 保持"待 UM 核验"标注；拿到手册后回填并记录页码/表号 |
| CK_OUT0 | 上板测频并记录仪器/条件；未测保持 theory/pending |
| V 篇 | 只核对现有章节的寄存器名/工具链三元组；没有工程就不写构建命令 |

## 金样例

- 工程事实与待核验清单：`code/gd32/01-rcu-clock/README.md`。
- 位域/回退路径：`code/gd32/01-rcu-clock/main.c`（HXTAL 超时回退、PMU 三件套、SCSS 回读、`clock_tree_readback`）。
- 链接与容量：`code/gd32/01-rcu-clock/gd32f4xx.ld` 顶部注释。
- 章节对照：`docs/gd32/00-env.md` 至 `04-periph-diff.md`（G 篇）、`05-riscv-toolchain.md` 至 `09-gpio-minimal.md`（V 篇）。
