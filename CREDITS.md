# 资料来源与致谢

本仓库的目标是**把散落的知识整理成一条可执行的路径**，因此内容大量参考了官方手册与公开资料。
下面把来源说清楚，也方便你顺着这些链接深入。

## 一、图片与动画的来源（重要）

| 类型 | 位置 | 来源 |
| --- | --- | --- |
| SVG 原理动画（25 个） | `assets/animations/` | **本仓库作者用代码绘制**，脚本见 `tools/anim_*.py`，采用 CC BY 4.0 |
| 板卡结构图（7 张）+ 芯片引脚图（3 张） | `assets/boards/` | **本仓库作者依据官方数据手册/开源原理图绘制的矢量图**，脚本见 `tools/gen_boards.py`、`tools/gen_pinouts.py`。**不是厂商实拍照片** |
| Nucleo-64 实拍（2 张） | `assets/photos/` | Ordercrazy / Thomas Springer 摄影，Wikimedia Commons，[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)；F411RE [原图页](https://commons.wikimedia.org/wiki/File:Embedded_World_2016,_Stm32_Nucleo.jpg)、F401RE [原图页](https://commons.wikimedia.org/wiki/File:Embedded_World_2016,_STM_Nucleo_401.jpg)；处理尺寸与校验和见 `assets/photos/README.md` |
| 静态框图（10 张） | `assets/diagrams/` | **本仓库作者用代码绘制**，脚本见 `tools/gen_diagrams.py` 与 `tools/gen_sample_figures.py`，采用 CC BY 4.0 |
| 光栅动画（6 个 GIF） | `assets/gif/` | **本仓库作者用纯 Python 渲染并手写 GIF 编码器生成**，脚本见 `tools/minigfx.py`、`tools/gen_gifs.py` |

> 除 `assets/photos/` 中明确列出的两张 CC0 实拍外，本仓库图形资产均为自绘或程序生成。实拍在正文中按真实型号标注，不将 F401RE/F411RE 冒充 NUCLEO-L476RG。
> 真实板卡的官方照片、原理图与 Gerber 仍以对应厂商产品页为准。

## 二、官方手册（本仓库反复引用）

| 文档 | 适用系列 | 说明 |
| --- | --- | --- |
| **RM0008** | STM32F101/102/103/105/107 | F1 参考手册（寄存器、外设、时钟树） |
| **RM0383** | STM32F411xC/E | F411 参考手册 |
| **RM0090** | STM32F405/407/415/417 | F4 参考手册 |
| **RM0399** | STM32H745/755、STM32H747/757 | 双核架构、共享存储、HSEM、启动与复位 |
| **RM0433** | STM32H742/H743/H750/H753 | H7 总线矩阵与 Ethernet MAC/MTL/DMA |
| **PM0214** | Cortex-M4 | 内核编程手册（NVIC、SysTick、SCB、MPU） |
| **PM0056** | Cortex-M3 | 内核编程手册 |
| **DS5319** | STM32F103x8/B | F103C8T6 数据手册（引脚定义、电气特性） |
| **DS10314** | STM32F411xC/E | F411 数据手册 |
| **AN2606** | 全系列 | 出厂 Bootloader 与启动模式说明 |
| **AN3965/AN4657** | F1/F4 | IAP 应用笔记 |
| **AN4839** | Cortex-M7 / STM32F7/H7 | L1 Cache、MPU 属性与 DMA 一致性 |
| **UM1724** | Nucleo-64 | Nucleo 用户手册（跳线、SB 电阻、引脚映射） |
| **UM2407** | STM32H7 Nucleo-144 (MB1364) | H743ZI2 Ethernet PHY、RJ45 与板级配置 |
| **UM1713** | STM32Cube + lwIP | Ethernet HAL、lwIP 与有/无 RTOS 应用结构 |
| **UM1472** | STM32F4DISCOVERY | Discovery 用户手册 |

ST 官网文档中心：<https://www.st.com/resource/en/>

协议语义优先查 [IETF RFC Editor](https://www.rfc-editor.org/)（TCP/UDP/DHCP/DNS/TLS）与 [OASIS MQTT 5.0](https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html)；库的执行上下文与 API 边界查 [lwIP upstream](https://www.nongnu.org/lwip/2_1_x/) 和 [Mbed TLS 官方文档](https://mbed-tls.readthedocs.io/)。

系统与 RTOS 章节冻结到官方发布：

- [FreeRTOS Kernel V11.3.2](https://github.com/FreeRTOS/FreeRTOS-Kernel/releases/tag/V11.3.2)；
- [RT-Thread v5.3.0](https://github.com/RT-Thread/rt-thread/releases/tag/v5.3.0)；
- [Zephyr v4.4.2](https://github.com/zephyrproject-rtos/zephyr/releases/tag/v4.4.2)；
- [CMSIS 6.4.0 / CMSIS-RTOS2 2.3.0](https://github.com/ARM-software/CMSIS_6/releases/tag/v6.4.0)；
- [STM32H745 CMSIS device header](https://github.com/STMicroelectronics/cmsis_device_h7/blob/81db1ec63cdc191fae1565b772da3ea5aa29a683/Include/stm32h745xx.h)，由 STM32CubeH7 commit `8ec3113d4039d30ba9dc2bf0cb6eefc756b48d06` 冻结到子模块 commit `81db1ec63cdc191fae1565b772da3ea5aa29a683`。

以上来源用于核对调度、IPC、设备模型、构建配置和 API 边界；本书不再分发其源码或文档。

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

## 六、样本章的改写吸收（v1.1.0）

第 00 章和第 03 章用改写吸收补了四块：原理与边界、关键插图、时序或状态、坑与出处卡。吸收的是事实，用本书的句子重写，并配上自绘静态图。手册正文、官方插图和 PDF 不放进仓库。社区原文这一对样本没有吸收；GPL、LGPL 和未写许可的材料仍只留在上面的索引里。

| 作品 | 许可证 | 用在 | 链接 |
| --- | --- | --- | --- |
| RM0008 Rev 21（2021-02），第 3.4 节表 9，以及第 9.2.7 节、第 9.3.5 节表 36 | ST 文档条款；只链接并改写事实，不转载手册 | 第 00 章启动状态；第 03 章 LCKR 与 SWD 脚 | https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf |
| DS5319 Rev 20（2025-07），表 5、图 8、注 5 | ST 文档条款；只链接并改写事实，不转载手册 | 第 03 章 LQFP48 的 PA0 第 10 脚、PC13 第 2 脚，以及 3 mA / 2 MHz / 30 pF | https://www.st.com/resource/en/datasheet/stm32f103c8.pdf |

### 第 04 章与第 06 章（v1.1.1）

第 04 章和第 06 章用改写吸收补了同样的四块。吸收的是事实，用本书的句子重写，并配上自绘静态图。手册正文、官方插图、社区原文和 MaJerle 的函数不放进仓库。论坛帖只留链接。

| 作品 | 许可证 | 用在 | 链接 |
| --- | --- | --- | --- |
| RM0008 Rev 21（2021-02），第 9.4.3 到 9.4.6 节、第 10.3.6 节，以及第 27.3.3 节、第 27.6.3 节、第 27.6.4 节 | ST 文档条款；只链接并改写事实，不转载手册 | 第 04 章 EXTI 与 EXTICR；第 06 章 16 倍采样、BRR `0x271` 误差 0、FE 的清除顺序 | https://www.st.com/resource/en/reference_manual/rm0008-stm32f101xx-stm32f102xx-stm32f103xx-advanced-arm-based-32-bit-mcus-stmicroelectronics.pdf |
| PM0056 Rev 7（2024-12），第 2.3.6 节、第 2.3.7 节，以及第 2.1.3 节 Table 7 | ST 文档条款；只链接并改写事实，不转载手册 | 第 04 章 8 寄存器入栈、尾链不改变抢占权、PRIMASK 挡不住 NMI | https://www.st.com/resource/en/programming_manual/pm0056-stm32f10xxx-cortex-m3-programming-manual-stmicroelectronics.pdf |
| DS5319 Rev 20（2025-07），图 8 与表 5 | ST 文档条款；只链接并改写事实，不转载手册 | 第 06 章 LQFP48 第 30 脚 PA9、第 31 脚 PA10 | https://www.st.com/resource/en/datasheet/stm32f103c8.pdf |
| MaJerle stm32-usart-uart-dma-rx-tx | MIT | 第 06 章坑卡：持续 DMA 接收时读到写位置为止，缓冲区不是一条拍平的帧 | https://github.com/MaJerle/stm32-usart-uart-dma-rx-tx/commit/c242589d766eada3ad1d795630f2b1c2482a2af8 |
| STM32CubeF4 v1.28.3 的 UART_ReceptionToIdle_CircularDMA | BSD-3-Clause | 第 06 章坑卡：循环 DMA 的 Size 是写位置。范围停在这个 F446 例程，不把它的引脚说成 F103 | https://github.com/STMicroelectronics/STM32CubeF4/tree/v1.28.3/Projects/STM32446E-Nucleo/Examples/UART/UART_ReceptionToIdle_CircularDMA |
