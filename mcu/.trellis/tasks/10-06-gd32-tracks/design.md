# 设计：GD32 双系路线

## 章节设计

### G 篇（GD32F4xx，对照 STM32F407）

| 章 | 文件 | 核心差异点（已核事实加粗） |
|---|---|---|
| G0 环境与工具链 | `docs/gd32/g0-env.md` | 复用 xPack GCC 15.2.1；官方库 V3.3.3 目录解剖 |
| G1 RCU 时钟树 | `docs/gd32/g1-rcu-clock.md` | **官方默认档 200M_PLL_25M_HXTAL**（system_gd32f4xx.c:54-67）；RCU_CFG0 位域待 UM 核验 |
| G2 GPIO/AF 对照 | `docs/gd32/g2-gpio.md` | 与 STM32 七大寄存器同构点名 |
| G3 USART 增强点 | `docs/gd32/g3-usart.md` | 从头文件 `gd32f4xx_usart.h` 比出增强清单，禁凭印象 |
| G4 差异点合集 | `docs/gd32/g4-diff.md` | USBHS/EXMC/Canal（CAN）等逐项"有没有/一不一样" |

### V 篇（GD32VF103，RISC-V）

| 章 | 文件 | 核心点 |
|---|---|---|
| V0 工具链与启动 | `docs/gd32/v0-riscv-boot.md` | riscv-none-elf-gcc 安装、启动文件与 ARM 的差异、链接脚本 |
| V1 Bumblebee 与 CLIC | `docs/gd32/v1-clic.md` | 从 Bumblebee_Core_Brief_Manual.pdf 提取：无 NVIC，中断挂载与向量 |
| V2 RCU 与 108MHz | `docs/gd32/v2-rcu.md` | 预设档 48/72/108M（system_gd32vf103.c:48-57）平移 G1 知识 |
| V3 MTIME 延时 | `docs/gd32/v3-mtime.md` | 替代 SysTick 的裸机时基 |
| V4 最小系统点灯 | `docs/gd32/v4-minimum.md` | GPIO + 工程，闭环 |

## 工程设计（code/gd32/）

- `code/gd32/01-rcu-clock/`：G1 配套，xPack ARM GCC + 官方库源码，目标芯片宏 `GD32F450`（可先无硬件构建验收）。
- `code/gd32/vf103-blink/`：V4 配套，前置 = 安装 riscv-none-elf-gcc（xPack），Makefile 复用 stm32 三工程模板改前缀与 flags（`-march=rv32imac -mabi=ilp32`）。

## 动画设计

- 复用现有骨架换事实：`rcu-clock-tree` 的 G 篇版（200M、RCU 命名、25M HXTAL 默认档）。
- 新图：`clic-vs-nvic.svg`（NVIC 查表响应 vs CLIC 向量直跳）、`mtime-vs-systick.svg`。
- 规范沿用：SMIL discrete、viewBox 720、values/keyTimes 计数一致、CONTRIBUTING.md 登记。

## 风险

- UM PDF 不可得 → 位域细节只能引用库头文件，所有敏感数字标"待 UM 核验"；上板后回填。
- RISC-V 工具链安装失败 → V 篇工程验收顺延，章节成稿不受影响。
- GD32F4xx 与 STM32F4 相似度极高 → 写作时逐字段点名"一样/不一样"，防止写成复制粘贴。
