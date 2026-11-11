# 00-blink：最小寄存器点灯工程（霸天虎 PF6 红灯）

四个文件，一个不多一个不少——这就是一颗芯片跑起来需要的全部：

| 文件 | 角色 | 详解章节 |
|---|---|---|
| `startup_stm32f407xx.s` | 向量表 + 复位后第一批指令（使能 FPU → .data 搬家 → .bss 清零 → 跳 main） | [B4 启动过程](../../../docs/build/04-startup.md) |
| `stm32f407xx.ld` | 链接脚本：代码/数据在 Flash 与 RAM 里的落位规则 | [B3 链接脚本](../../../docs/build/03-linker-script.md) |
| `main.c` | 业务：开时钟 → 配 GPIO → BSRR 闪烁 | [S3 GPIO](../../../docs/stm32/03-gpio.md) |
| `Makefile` | 把四步构建摆在明面上 | [B7 构建系统](../../../docs/build/07-build-system.md) |

## 构建

```bash
make            # 产出 build/blink.elf / .bin / .hex / .map 并打印体积
```

预期输出（体积随手一版， -O0 无库）：

```text
   text    data     bss     dec
   ~200       0       0    ~200   build/blink.elf
```

## 烧录（OpenOCD + ST-Link）

```bash
make flash      # program + verify + reset，复位后红灯以约 1Hz 闪烁
```

## 调试

```bash
make debug      # 终端1：OpenOCD 常驻，监听 3333
make gdb        # 终端2：GDB 连上、复位、烧录、断在 main
```

GDB 里试这两行，亲眼看到"点灯=往地址写字"：

```gdb
x/wx 0x40023830    # RCC_AHB1ENR，bit5 应为 1
set *(unsigned int*)0x40021418 = (1<<22)   # BSRR BR6：灯亮（先 main 跑过配置）
```

> 状态：代码经静态审查并与 RM0090 核对（GPIOF=0x40021400、RCC_AHB1ENR=0x40023830、BSRR 偏移 0x18）；**待上板实测**——欢迎你烧录后把现象/问题提到 Issue。
