# 资料来源与致谢

本仓库的目标是**把散落的知识整理成一条可执行的路径**，因此内容大量参考了官方手册与公开资料。
下面把来源说清楚，也方便你顺着这些链接深入。

## 一、图片与动画的来源（重要）

| 类型 | 位置 | 来源 |
| --- | --- | --- |
| SVG 原理动画（21 个） | `assets/animations/` | **本仓库作者用代码绘制**，脚本见 `tools/anim_*.py`，采用 CC BY 4.0 |
| 板卡实物结构图（7 张） | `assets/boards/` | **本仓库作者依据官方数据手册/开源原理图绘制的矢量结构图**，脚本见 `tools/gen_boards.py`。**不是厂商实拍照片** |
| 静态框图（4 张） | `assets/diagrams/` | 同上，脚本见 `tools/gen_diagrams.py` |
| 光栅动画（6 个 GIF） | `assets/gif/` | **本仓库作者用纯 Python 渲染并手写 GIF 编码器生成**，脚本见 `tools/minigfx.py`、`tools/gen_gifs.py` |

> 因此本仓库**没有**再分发任何第三方图片，也不存在图片版权风险。
> 想查看真实照片、官方原理图与 Gerber，请看下面的官方链接。

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
