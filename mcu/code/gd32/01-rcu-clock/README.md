# gd32/01-rcu-clock：GD32F4xx RCU 时钟树（寄存器级）

对照章节 [G1 RCU 时钟树](/gd32/01-rcu-clock.md)。寄存器位定义全部引自官方库
V3.3.3（GitHub `GigaDevice-GD32-MCU/GD32F4xx_Firmware_Library` @ `10d02f4`），
源码存 `.trellis/ref/gd32/`。

## 它做了什么

1. HXTAL（25MHz）起振，超时回退 IRC16M（官方 demo 是 while(1) 死等，本工程不抄）；
2. 电压档三件套握手：PMUEN → LDOVS → HDEN 等 `HDRF` → HDS 等 `HDSRF`；
3. 显式设置 FMC 等待周期（`FMC_WS_VALUE`，官方 system 文件不设——这是留白）；
4. 官方 200M 档 PLL：PSC=25 / N=400 / P=2 / Q=9 → CK_SYS 200MHz；
5. 总线分频 AHB/1、APB2/2、APB1/4，SCS=PLLP 后等 SCSS 回执；
6. CK_OUT0（PA8, AF0）输出 PLLP/4 = **理论 50MHz**（待上板实测对账）。

调试观察点：`g_clock_status`（0=PLL 档，1/2/3/4=各级回退）与 `g_clock_tree[]`
（CK_SYS/CK_AHB/CK_APB1/CK_APB2）。`clock_tree_readback()` 按 **SCSS 如实解码**
当前时钟源、按 RCU_PLL 参数重算频率——回退路径也报真值（例如 PLL 未锁定即为
IRC16M 16MHz，而不是"以为的 25MHz"）。

## 构建

```sh
# 需要 xPack arm-none-eabi-gcc 15.2.1（与 STM32 工程同一套）+ mingw32-make + Git usr/bin
# Windows cmd：
set PATH=D:\zhugu-home\tools\armgcc\xpack-arm-none-eabi-gcc-15.2.1-1.1\bin;C:\Program Files\Git\usr\bin;%PATH%
cd code/gd32/01-rcu-clock && mingw32-make
```

## 待核验清单（事实纪律）

- `FMC_WS_VALUE=6` 是保守超配值：官方库未给出"频率↔等待"对照表（system 文件
  不设 FMC 等待），需求方拿到用户手册（UM）后回填精确值。
- 链接脚本按 GD32F450ZG 1MB Flash / 256KB SRAM 写，**待 UM 核验**；
- CK_OUT0 实际频率待上板实测（理论 50MHz）。