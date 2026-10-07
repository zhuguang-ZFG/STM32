# 22 仿真实验：Wokwi 与 Renode

> 没有板子也能把灯点亮、把按键按下去。仿真是预习，不是代替焊接。

<p align="center">
  <img src="../assets/animations/toolchain-flow.svg" width="760" alt="编译烧录运行的数据流">
  <br><sub>▲ 动画：固件从编译走到运行（作者自绘矢量动画，非实拍）</sub>
</p>

<!-- video:ch22 -->
<p align="center">
  <img src="../assets/video/ch22-sim.gif" width="640" alt="第 22 章讲解幻灯">
  <br><sub>▲ 本章讲解幻灯：程序生成的 GIF（tools/gen_videos.py，可复现，不是实拍）。旁白与五帧一一对应。</sub>
</p>

**旁白（跟着画面读，大约一分钟）**

1. 仿真分两家：Wokwi 在浏览器里接线，Renode 在命令行里跑同一颗 Cortex-M3。
2. 每个核心示例目录里有 diagram.json 和 wokwi.toml。引脚名跟 Wokwi 板定义走，A0 就是 PA0。
3. Renode 脚本加载官方平台 platforms/cpus/stm32f103.repl，USART1 在 PA9/PA10。
4. 当前 Wokwi 的 BluePill 模型没有 DMA。串口空闲帧和 ADC 搬运要上真板，或只看接线。
5. 口诀：仿真看现象，真板对时序。自测：PC13 的灯在 Wokwi 里要不要再外接一颗？
<!-- /video:ch22 -->

## 📌 学习目标

- [ ] 能在 Wokwi 里打开本仓库的 BluePill 图，并说清引脚别名。
- [ ] 能用 Renode 加载 `stm32f103.repl` 和一份 ELF。
- [ ] 知道哪些示例在当前仿真器里能跑完，哪些只能看接线。

## 🧠 先选哪一家

**结论**：想看灯、按键、PWM、OLED，用 Wokwi。想在终端里单步、看 USART1 字节流，用 Renode。两家都吃你自己编译出来的 ELF，仓库里没有预编译固件。

| | Wokwi | Renode |
| --- | --- | --- |
| 在哪跑 | 浏览器或 VS Code 插件 | 本机命令行 |
| 配置 | 示例目录里的 `diagram.json` + `wokwi.toml` | `sim/renode/*.resc` |
| 板子 | `board-stm32-bluepill`（STM32F103C8） | `platforms/cpus/stm32f103.repl` |
| 适合 | 接线、GPIO、EXTI、定时器、I2C | 加载 ELF、USART1 终端、外设访问日志 |
| 官方说明 | [Blue Pill 零件页](https://docs.wokwi.com/parts/board-stm32-bluepill)、[wokwi.toml](https://docs.wokwi.com/vscode/project-config) | Renode 仓库里的 `platforms/cpus/stm32f103.repl` |

口诀：**浏览器里看灯，命令行里看字节。**

## 🛠️ Wokwi：图怎么读

引脚名字不是 `PA0`，而是 Wokwi 板文件里的键。出处是
[wokwi-boards 的 `boards/stm32-bluepill/board.json`](https://github.com/wokwi/wokwi-boards/blob/main/boards/stm32-bluepill/board.json)：

| 图里的名字 | 接到芯片的脚 | 本仓库谁在用 |
| --- | --- | --- |
| `C13` | PC13（板载灯，原理图里已接好，低电平亮） | gpio-blink |
| `A0` | PA0 | gpio-blink 外接灯、exti-key 按键、adc 通道 0 |
| `A1` / `A4` | PA1 / PA4 | adc-dma |
| `A6` | PA6 = TIM3_CH1 | timer-pwm |
| `A9` / `A10` | PA9 / PA10 = USART1 | uart-dma-idle（串口监视器） |
| `B6` / `B7` | PB6 / PB7 = I2C1 | i2c-oled |
| `GND.1` `3V3.1` | 地 / 3.3 V | 所有外接零件 |

板载灯已经焊在 PC13 上，点灯实验不用再画一颗灯也能看到闪。`gpio-blink` 的图额外画了 PA0 那颗外接灯，对应示例里的第二盏。

### 核心示例各有一份图

| 示例 | 图里有什么 | 当前 Wokwi 模型能不能跑完 |
| --- | --- | --- |
| [gpio-blink](../examples/gpio-blink/diagram.json) | 板子 + PA0 经 270Ω 到红色 LED | 能。GPIO 在支持列表里 |
| [exti-key](../examples/exti-key/diagram.json) | PA0 对地按键 | 能。EXTI 在支持列表里 |
| [timer-pwm](../examples/timer-pwm/diagram.json) | PA6 经 270Ω 到绿色 LED | 能。TIM1–TIM4 在支持列表里 |
| [i2c-oled](../examples/i2c-oled/diagram.json) | `board-ssd1306`，地址 `0x3c`，SCL/SDA 各 4.7 kΩ 上拉 | I2C 在支持列表里。屏要等固件按 SSD1306 时序写 |
| [uart-dma-idle](../examples/uart-dma-idle/diagram.json) | 只有板子，字节走串口监视器 | **DMA 未实现**，空闲帧收包跑不完 |
| [adc-dma](../examples/adc-dma/diagram.json) | 三只电位器接到 A0/A1/A4 | ADC1 基本转换有，**DMA 搬运没有** |

支持情况以 Wokwi 文档那张表为准（GPIO、USART、I2C、SPI、TIM、EXTI 有；DMA、RTC、IWDG 没有）。表会改，以你打开文档的那一版为准。

`wokwi.toml` 里固件路径写成 `build/firmware.elf`。STM32 在 Wokwi 接受 `.elf`、`.hex`、`.bin`。先在 CubeIDE 或 PlatformIO 里编出来，再把 `firmware` / `elf` 两行改成你的真实路径。Wokwi 不负责编译。

## 🛠️ Renode：两条脚本

脚本在 [`sim/renode/`](../sim/renode/)。它们做的事只有四件：建机器、加载官方 F103 平台描述、加载 ELF、启动。

| 脚本 | 做什么 |
| --- | --- |
| [gpio-blink.resc](../sim/renode/gpio-blink.resc) | 打开 USART1 分析器，并把 `gpioPortC` 的访问打到日志。板载灯是 PC13 |
| [uart-usart1.resc](../sim/renode/uart-usart1.resc) | 把 `usart1` 接到本机 3456 端口，另开终端 `telnet localhost 3456` |

```bash
# 默认找当前目录的 firmware.elf，可用 -e 换路径
renode -e '$bin=@/path/to/firmware.elf' sim/renode/gpio-blink.resc
renode -e '$bin=@/path/to/firmware.elf' sim/renode/uart-usart1.resc
```

`usart1` 这个名字和地址 `0x40013800` 写在 Renode 的 `stm32f103.repl` 里，对应参考手册里的 USART1，也就是 PA9/PA10。不要把它说成 USART2。

uart 示例走 DMA。Renode 的 `stm32f103.repl` 里挂了 DMA 节点，但是否能完整搬完「空闲线 + 环形缓冲」，取决于你装的 Renode 版本。对不上时，先用第 06 章的轮询收发确认字节，再回到 DMA。

## ⚠️ 仿真替不了的事

| 现象 | 原因 | 怎么办 |
| --- | --- | --- |
| Wokwi 提示找不到固件 | `wokwi.toml` 的路径是占位 | 改成你刚编出来的 ELF |
| 灯不闪但图是对的 | 固件时钟或 BOOT 和仿真模型不一致 | 先在真板确认，再对照模型支持表 |
| 串口一个字节都没有 | 示例在等 DMA 空闲中断 | 换轮询，或上真板 |
| OLED 一片黑 | 地址写成了 0x78 但零件默认 0x3c | 图里 `i2cAddress` 是 7 位地址 `0x3c`，和 HAL 左移后的 0x78 是同一个从机 |
| Renode 报平台找不到 | 版本里没有这份 repl | 在 Renode 提示符里 `ls @platforms/cpus` 看实际文件名 |

## 🧪 动手实验

1. **只看板载灯**：用 gpio-blink 编出 ELF，丢进 Wokwi。预期：板子上的 PC13 灯按代码节奏闪，PA0 那颗外接灯慢得多。
2. **按一下**：exti-key 的图里按下按钮（它把 A0 接到 GND）。预期：板载灯翻转。按键在固件里是上拉输入，所以图里不用再画上拉电阻。
3. **听 USART1**：Renode 跑 `uart-usart1.resc`，telnet 到 3456。若固件还是 DMA 版且没有字节，把结论记下来：这是模型边界，不是波特率算错。

自测：

1. Wokwi 图里的 `A6` 是芯片的哪只脚？
2. 为什么 uart-dma-idle 的图只有一块板子？
3. Renode 脚本加载的平台文件叫什么？

## 🔗 相关资源

- Wokwi：[STM32 Blue Pill](https://docs.wokwi.com/parts/board-stm32-bluepill)、[diagram.json](https://docs.wokwi.com/diagram-format)、[wokwi.toml](https://docs.wokwi.com/vscode/project-config)、[SSD1306 板](https://docs.wokwi.com/parts/board-ssd1306)、[电位器](https://docs.wokwi.com/parts/wokwi-potentiometer)
- 板脚定义原文：[wokwi-boards `board.json`](https://github.com/wokwi/wokwi-boards/blob/main/boards/stm32-bluepill/board.json)
- Renode 平台原文：`platforms/cpus/stm32f103.repl`（`usart1` @ `0x40013800`，`gpioPortC` @ `0x40011000`）
- 示例索引：[examples/README.md](../examples/README.md)
- 免责声明：这里没有仿真器截图。接线以 JSON 为准，能力以两家文档的支持表为准。
