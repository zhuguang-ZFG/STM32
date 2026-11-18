# 00-blink：最小寄存器点灯工程（霸天虎 PF6 红灯）

配套现行章节：[ch06 链接与启动](../../../../docs/v0-foundations/06-linker-startup-map.md)、[ch09 GPIO](../../../../docs/v1-drivers/09-gpio.md)。完整接线、安全、测量、判据和待填记录见 [点灯取证协议](../../../../labs/gpio-blink/README.md)。

| 文件 | 角色 |
| --- | --- |
| startup_stm32f407xx.s | F407ZGT6向量表、FPU使能、data搬移、bss清零、进main |
| stm32f407xx.ld | Flash1MB、SRAM128KB，段与栈边界 |
| main.c | GPIOF时钟、PF6推挽、BSRR低亮高灭、软件忙等 |
| Makefile | 默认-O0 -g3，Cortex-M4 hard float，构建和OpenOCD入口 |

实际板型/芯片与供电仍待核实；代码按霸天虎共阳LED设计。冷复位HSI名义16MHz，程序未配置PLL。delay(2000000)是软件循环，源码约0.5秒/“实测校准”的注释无附带原始证据，不能承诺精确1Hz；应量十个完整周期后登记。

## 后续构建烧录（本轮未执行）

在本目录、已有兼容Make环境中执行：

```bash
make          # build/blink.elf/.bin/.hex/.map
make flash    # OpenOCD + ST-Link，program/verify/reset
```

先按取证协议核身份、单一供电和SWD，构建失败不烧录；环境要求与日志/哈希见协议。现有make debug/make gdb为调试入口，gdb目标含load也会写板。

状态：`hardware_status: pending`，未实测。尚缺板卡身份、构建与烧录日志、冷复位现象、PF6波形、十周期原始计时及复测记录；本轮仅文档与源码核对，不改变固件。
