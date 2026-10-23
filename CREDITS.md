# 资料来源与致谢

本仓库的目标是**把散落的知识整理成一条可执行的路径**，因此内容大量参考了官方手册与公开资料。
下面把来源说清楚，也方便你顺着这些链接深入。

## 一、图片与动画的来源（重要）

| 类型 | 位置 | 来源 |
| --- | --- | --- |
| SVG 原理动画（22 个） | `assets/animations/` | **本仓库作者用代码绘制**，脚本见 `tools/anim_*.py`，采用 CC BY 4.0 |
| 板卡结构图（7 张）+ 芯片引脚图（3 张） | `assets/boards/` | **本仓库作者依据官方数据手册/开源原理图绘制的矢量图**，脚本见 `tools/gen_boards.py`、`tools/gen_pinouts.py`。**不是厂商实拍照片** |
| Nucleo-64 实拍（2 张） | `assets/photos/` | Ordercrazy / Thomas Springer 摄影，Wikimedia Commons，[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)；F411RE [原图页](https://commons.wikimedia.org/wiki/File:Embedded_World_2016,_Stm32_Nucleo.jpg)、F401RE [原图页](https://commons.wikimedia.org/wiki/File:Embedded_World_2016,_STM_Nucleo_401.jpg)；处理尺寸与校验和见 `assets/photos/README.md` |
| 静态框图（5 张） | `assets/diagrams/` | 本仓库作者用代码绘制，脚本见 `tools/gen_diagrams.py`，采用 CC BY 4.0 |
| 光栅动画（6 个 GIF） | `assets/gif/` | **本仓库作者用纯 Python 渲染并手写 GIF 编码器生成**，脚本见 `tools/minigfx.py`、`tools/gen_gifs.py` |

> 除 `assets/photos/` 中明确列出的两张 CC0 实拍外，本仓库图形资产均为自绘或程序生成。实拍在正文中按真实型号标注，不将 F401RE/F411RE 冒充 NUCLEO-L476RG。
> 真实板卡的官方照片、原理图与 Gerber 仍以对应厂商产品页为准。

## 二、官方手册（本仓库反复引用）

| 文档 | 适用系列 | 说明 |
| --- | --- | --- |
| **RM0008** | STM32F101/102/103/105/107 | F1 参考手册（寄存器、外设、时钟树） |
| **RM0383** | STM32F411xC/E | F411 参考手册 |
| **RM0090** | STM32F405/407/415/417 | F4 参考手册 |
| **PM0214** | Cortex-M4 | 内核编程手册（NVIC、SysTick、SCB、MPU） |
| **PM0056** | Cortex-M3 | 内核编程手册 |
| **DS5319** | STM32F103x8/B | F103C8T6 数据手册（引脚定义、电气特性） |
| **DS10314** | STM32F411xC/E | F411 数据手册 |
| **AN2606** | 全系列 | 出厂 Bootloader 与启动模式说明 |
| **AN3965/AN4657** | F1/F4 | IAP 应用笔记 |
| **UM1724** | Nucleo-64 | Nucleo 用户手册（跳线、SB 电阻、引脚映射） |
| **UM1472** | STM32F4DISCOVERY | Discovery 用户手册 |

ST 官网文档中心：<https://www.st.com/resource/en/>

## 三、社区与开源项目

- **ST 官方社区**：<https://community.st.com/> —— 官方工程师会回答，比搜索更可靠
- **libopencm3**：<https://github.com/libopencm3/libopencm3> —— 开源固件库，适合看寄存器级实现
- **ChibiOS / RT-Thread / Zephyr / FreeRTOS**：主流开源 RTOS，源码本身就是最好的教材
- **PlatformIO**：<https://docs.platformio.org/page/platforms/ststm32.html> —— 跨平台工具链与板卡定义
- **Wokwi / Renode**：在线与本地仿真，可以在没有硬件时验证逻辑
- **中文社区**：正点原子、野火、硬汉嵌入式、电子发烧友、B 站相关课程（仅作索引，不转载内容）

## 四、数据准确性说明

- 所有寄存器位、公式、时序参数均标注了来源手册章节，便于核对；
- 不同型号（F1/F4/H7）寄存器位定义可能不同，遇到差异以对应系列手册为准；
- 如果你发现错误，欢迎提 Issue 或 PR（见 [CONTRIBUTING.md](CONTRIBUTING.md)），
  附上手册页码或实测截图，我们会尽快修正。

## 五、致谢

感谢 STMicroelectronics 提供详尽的公开文档，感谢所有开源固件库与社区作者 —— 
正是因为这些资料是公开的，学习嵌入式才不需要任何门槛。
