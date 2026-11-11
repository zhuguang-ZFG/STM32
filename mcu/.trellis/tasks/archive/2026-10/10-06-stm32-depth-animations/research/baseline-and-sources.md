# 规划研究：基线、事实缺陷与资料

日期：2026-10-06。基线提交 60f9597，规划开始前工作区干净。原始行号均对应该基线，后续修改应保留本记录作为追踪。

## 仓库证据与修复归属

| 编号 | 归属 | 证据 | 判断/所需修复 |
|---|---|---|---|
| S-F1 | S2 | docs/stm32/02-rcc-clock.md:11、13 | 1MHz 是示例选择；Flash 等待周期须附电压/频率条件；HSE 真实值未核实 |
| S-F2 | S6 | docs/stm32/06-tim.md:27 | TIM3 CH1→PF6 写法待实查；不可把“若不支持则换脚”留作可运行方案 |
| S-F3 | S7/E02 | docs/stm32/07-usart.md:54；docs/lab/e02-logic-uart.md:7、43 | 'A'=0x41 与 0x55 混用；115200×16=1843200，1MHz 不满足该文同句给定条件 |
| S-F4 | S8 | docs/stm32/08-dma.md:12 | DIR 不是一位；官方 CMSIS 确认位宽为 2、位置从 bit6 开始 |
| S-F5 | S8/旧动画 | docs/stm32/08-dma.md:13；docs/public/anim/dma-pingpong.svg | “永不打架”遗漏处理期限；环形/双缓冲不能自动防止消费者落后 |
| F-F1 | F6 | docs/rtos/freertos/06-notify-event-timer.md:27 | xTaskNotifyTake 名字错误；上游头文件为 ulTaskNotifyTake |
| F-F2 | F6 | 同页:7、11、12、52 | 无条件“快45%”、全替代、一对一/容量一、固定24位的表述须按版本、配置及语义限定 |
| F-F3 | F6 | 同页:53 | 事件组清位不能表述为先唤醒者独占；需按等待列表与汇总清位逻辑解释 |
| F-F4 | F7 | docs/rtos/freertos/07-heap.md:13、27、43 | 动态任务栈来自堆与“不在堆里”自相矛盾；历史最小空闲量不是碎片率；heap_2 指标 API 要逐文件核对 |
| P-F1 | P2 | docs/esp32/02-gpio-matrix.md:11、18 | “任意引脚”要加芯片有效脚、输入输出能力、模组占用和板卡接线条件 |
| P-F2 | P5 | docs/esp32/05-uart-driver.md:5、7 | IDF 5.5.x UART 源码路径已拆到 components/esp_driver_uart/src/uart.c；事件元数据不是串口字节负载 |
| P-F3 | P7 | docs/esp32/07-timer-ledc.md:12、54 | S3 不能套经典 ESP32 的16通道/高速模式；已核实8通道、仅低速模式 |
| X-F1 | 共同规范 | .trellis/spec/docs-site/structure.md 与 CONTRIBUTING.md | 前者 raw img 指示过时；以贡献指南的 Markdown 图片方式为准，集成时消歧 |

## 已访问的一手来源

1. ST CMSIS 头文件： https://raw.githubusercontent.com/STMicroelectronics/cmsis-device-f4/master/Include/stm32f407xx.h
   - 本轮直接读取确认 DMA_SxCR_DIR_Pos=6、掩码0x3<<6，DBM=bit18、CT=bit19，USART TC=bit6/TXE=bit7。
   - master 非固定提交，实施前锁定提交和摘要；此来源不能替代 datasheet 的逐引脚 AF 表或板卡原理图。
2. FreeRTOS V11.1.0： https://github.com/FreeRTOS/FreeRTOS-Kernel/tree/V11.1.0
   - 已直接读取 include/task.h、event_groups.c、portable/MemMang/heap_4.c。
   - 确认 xTaskNotifyGive/ulTaskNotifyTake；事件组遍历收集 uxBitsToClear 再清除；heap_4 的相邻空闲块合并入口为 prvInsertBlockIntoFreeList。
3. ESP-IDF v5.5 S3 LEDC 文档： https://docs.espressif.com/projects/esp-idf/en/v5.5/esp32s3/api-reference/peripherals/ledc.html
   - 明确 S3 只配置低速模式；多任务操作同一通道要考虑 API 线程安全条件。
4. ESP-IDF v5.5 SoC 能力： https://github.com/espressif/esp-idf/blob/v5.5/components/soc/esp32s3/include/soc/soc_caps.h
   - 本轮读取确认 SOC_LEDC_CHANNEL_NUM=8、SOC_LEDC_TIMER_BIT_WIDTH=14、SOC_UART_FIFO_LEN=128。
5. 本机 IDF：D:/zhugu-home/.espressif/v5.5.2/esp-idf/
   - components/soc/esp32s3/include/soc/soc_caps.h:246–247 与上述 LEDC 能力一致。
   - components/esp_driver_uart/CMakeLists.txt 确认 uart.c 在 src 下及组件依赖。
   - components/freertos/FreeRTOS-Kernel/include/freertos/task.h:2 标记“V10.5.1 (ESP-IDF SMP modified)”；不与上游 V11.1.0 混读。
   - 目录名不是完整版本证明，实施时读取版本宏/git describe。idf.py.exe --version 返回 v1.0.3 是本机启动器版本，不能当 IDF 框架版本。

## 资料与环境缺口

- Web 搜索工具本轮返回服务端404；直接抓取官方 GitHub 和 Espressif 文档成功。
- ST datasheet/RM0090 下载端点返回HTTP567，尚未读取 PDF；PF6 通道、DMA 请求映射、PLL 范围、Flash/VOS 条件仍需正式资料核验。
- ~~上游 RCC/UART 源未取到~~ → HAL 已补齐：2026-10-06 从 ST 官方仓库 `STMicroelectronics/stm32f4xx_hal_driver`（master @ `1f6451c`）拉取 `stm32f4xx_hal_rcc.c`（42,493 B）/ `stm32f4xx_hal_uart.c`（136,921 B），存 `.trellis/ref/st-hal/`（含 PROVENANCE.txt）。SPL（StdPeriph）未随 ST 官方 GitHub 分发，RCC/TIM/DMA/SYSTEM 仍为缺口，不能从函数名猜实现。
- .trellis/ref/freertos 当前是上一轮片段：tasks.c、queue.c、semphr.h、port.c、portmacro.h、list.c；不足以直接构建完整 V11.1.0。
- PATH 没发现 arm-none-eabi-gcc、objdump 或 make。实施先查本机安装路径；确实缺失则按权限安装/准备，不能降低构建验收标准。
- IDF、CMake、Ninja 启动器存在；环境能否构建、板卡是否可访问本轮尚未验证。
- 立创实战派 S3 扩展口与背光真实 GPIO 未确认。先取得对应原理图，示例不填写猜测引脚。
- 原有 SVG 存在10/11px文字；新图执行 >=12px，S8 被修改旧图一并修正。其他旧动画整批翻新不在当前范围。


## 方案选择

- STM32 先补时钟/PWM/UART/DMA；FreeRTOS 补 F1/F6/F7，与已成稿 F2–F5 连起来；ESP32 补 P2/P5/P7，与 STM32 同机制对照。
- 采用独立SVG；暂不引入交互组件。每图配阶段解说与结论，便于静态阅读。
- 三条路线同时属于总目标，按子任务顺序实施，避免把独立交付混成一个无法验收的大改动。
- 七个配套工程及入口同步用于兑现 quick win；F8 只补指向真实基础工程的入口，不宣称本轮将 F8 全章成稿。

## 实施期追加（2026-10-06，批次一开始后）

### 工具链

| 项 | 值 |
|---|---|
| 编译器 | xPack GNU Arm Embedded GCC 15.2.1 20251203（arm-none-eabi-gcc） |
| 获取 | scoop 官方 Arm 10.3-2021.10 包下载中断（传输流 EOF），改用 xpack GitHub Release `v15.2.1-1.1` 的 `win32-x64.zip`，解压到 `D:/zhugu-home/tools/armgcc/`（仓库外，不入库） |
| make | GNU Make 4.4.1（winlibs，`D:\zhugu-home\mingw64\mingw64\bin\mingw32-make.exe`） |
| 附加 | Makefile 用了 `mkdir -p`/`rm -rf`，需要 Git 的 `usr\bin` 也在 PATH 上 |

### 构建期发现的新缺陷：链接脚本的 MEMORY 区域属性

`code/stm32/*/stm32f407xx.ld` 原写 `RAM (xrwah)`。GNU ld 的区域属性合法字母只有
`r w x a i l`，`h` 非法；旧 binutils 容忍，新版 ld 直接报
`invalid character 104 in flags`，链接失败且不指向脚本行号。已把四份脚本
（00-blink/01/02/03）统一改为 `RAM (xrw)` 并加注释说明来由。此前该工程从未在本机
构建过，所以这个错误一直没暴露。

### 寄存器事实（来源已锁定）

ST CMSIS 头文件 `cmsis_device_f4` commit `9192c7b9df75a142f2027ab266601fe061fc00b3`，
`Include/stm32f407xx.h`，本地缓存 `.trellis/ref/cmsis/`（sha256 前缀 `ae1ab57d8ab750f64f04fd73`）。
已逐条核对并用于工程：RCC_CR(HSION/HSIRDY/HSEON/HSERDY/PLLON/PLLRDY)、RCC_PLLCFGR
(PLLM[5:0]/PLLN[14:6]/PLLP[17:16]/PLLSRC/PLLQ[27:24])、RCC_CFGR(SW/SWS/HPRE/PPRE1/PPRE2/MCO1PRE[26:24])、
FLASH_ACR(LATENCY/PRFTEN)、PWR_CR(VOS)、TIM_CCMR1/TIM_CCER/TIM_EGR/DIER/SR、
USART_CR1/SR/DR、DMA_SxCR(CHSEL[28:25]/CT/DBM/DIR[7:6]/CIRC/MINC/PINC/PS/PL)。

### 引脚复用（DS8626 Rev 9，Table 9，p.62/63/66）

| 用途 | 引脚 | AF | 备注 |
|---|---|---|---|
| MCO1 | PA8 | AF0 | |
| TIM3_CH1 PWM 输出 | PA6 | AF2 | |
| TIM3_CH2 输入捕获 | PA7 | AF2 | |
| USART1_TX / RX | PA9 / PA10 | AF7 | |
| USART2_TX / RX | PA2 / PA3 | AF7 | 批次三对照用 |
| SPI1_SCK | PA5 | AF5 | |

**S-F2 结论**：F407 的 Port F 完全没有 TIM3 通道——PF6/PF7/PF8 在 AF3 上分别是
TIM10_CH1 / TIM11_CH1 / TIM13_CH1，AF2 列为空。原 quick win “TIM3 CH1 输出到 PF6”
在复用表层面就是错的，正确示例应改用 PA6（AF2）。

### Flash 等待周期（RM0090 Rev 18，Table 10，p.80）

该表按 **VDD 电压范围**分列，不是按 VOS 分档：

| VDD | 0WS | 1WS | 2WS | 3WS | 4WS | 5WS | 6WS | 7WS |
|---|---|---|---|---|---|---|---|---|
| 2.7~3.6V | ≤30 | ≤60 | ≤90 | ≤120 | ≤150 | ≤168 | — | — |
| 2.4~2.7V | ≤24 | ≤48 | ≤72 | ≤96 | ≤120 | ≤144 | ≤168 | — |
| 2.1~2.4V | ≤22 | ≤44 | ≤66 | ≤88 | ≤110 | ≤132 | ≤154 | ≤168 |
| 1.8~2.1V（预取关） | ≤20 | ≤40 | ≤60 | ≤80 | ≤100 | ≤120 | ≤140 | ≤160 |

VOS 只决定 HCLK 天花板：同章注明 F405/407 在 VOS='0' 时 fHCLK 上限 144MHz，VOS='1' 时 168MHz。
`01-rcc-clock/main.c` 的 `flash_latency_ws_3v3()` 按 2.7~3.6V 列实现，VOS 单独处理。

### PLL 约束（RM0090 Rev 18，§7.2.3 RCC_PLLCFGR，p.155/164）

- `f(VCO) = f(PLL 输入) × PLLN / PLLM`；`f(SYSCLK) = f(VCO)/PLLP`；`f(48M) = f(VCO)/PLLQ`
- PLLM ∈ [2,63]，VCO 输入必须在 1~2MHz，原文推荐 2MHz 以限制抖动
- PLLN ∈ [50,432]，VCO 输出必须在 100~432MHz
- USB OTG FS 需要正好 48MHz，PLLQ ∈ [2,15]
- F407 的主 PLL 输出上限为 168MHz

### 仍缺一手来源

- **DMA2 请求映射（RM0090 Table 43，p.308）**：多次尝试未取得正文表（st.com 567、
  镜像文本层只到约 229 页、扫描件需 OCR）。处置：`03-uart-dma` 用集中宏
  `USART1_RX_STREAM/CHANNEL` 给出常用取值（DMA2 Stream5/Ch4），并在代码、
  README、本记录中显式标注"待上板实测确认"，同时给出不接表也能判对的自检路径
  （`g_rx_bytes`/`g_frames` 不动即映射错）。

### DMA 控制器修正（实施期补记）

USART1 的 DMA 请求在 **DMA2**（Table 43），不在 DMA1。工程初版误用 DMA1，
编译期不会报错——引脚/时钟都对，就是数据永远不会来。修正为
DMA2 Stream5 Channel4（RX）/ DMA2 Stream6 Channel4（TX），与既有章节表述一致，
另以 Zephyr 等工程惯例交叉核对。同时补了两处此前漏掉的纪律：
- 必须开 `RCC_AHB1ENR.DMA2EN`（bit22），否则流配置写了也白写；
- DMA 标志清除要写 `HIFCR`/`LIFCR`，`HISR` 是只读状态寄存器。

### ESP-IDF 环境修复（批次三实施期）

本机有两个 `.espressif` 根：真正可用的是 `C:\Users\zhugu\.espressif`；
`D:\zhugu-home\.espressif\python_env` 与 C 盘那份是 junction 同一目录。
踩过的坑：
- `idf5.5_py3.12_env` 的 venv 基座 python 已被卸载 → 用 scoop 的 python 3.13
  重建为 `idf5.5_py3.13_env`（idf_tools 按解释器版本找环境名）；
- `pip install -r requirements.core.txt` 必须带 `-c espidf.constraints.v5.5.txt`，
  否则拉到 esptool 5.x 等不满足 v5.5 约束的新版本；
- v5.5.2 只认 xtensa-esp-elf `esp-14.2.0_20251107`，不是更新的 20260121；
- Windows 批处理必须 CRLF 行尾，LF 会让 set 语句解析错位。
验证：`idf.py set-target esp32s3` + `idf.py build` 三个工程全部通过。
