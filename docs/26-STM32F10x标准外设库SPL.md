# 26 STM32F10x 标准外设库（SPL）

> 标准外设库不是 HAL 的另一种拼写。它是 STM32F1 时代的独立驱动体系：没有 Handle、没有 CubeMX 生成流程，也不会替你完成超时、状态机和回调管理。

<!-- video:ch26 -->
<p align="center">
  <video width="640" controls poster="../assets/video/ch26-spl.png">
    <source src="../assets/video/ch26-spl.mp4" type="video/mp4">
  </video>
  <br><sub>▲ 本章讲解 2.9 分钟。配音是微软 Edge 在线神经语音「晓晓」（zh-CN-XiaoxiaoNeural），经 edge-tts 调用。edge-tts 大部分源码为 LGPLv3，srt_composer.py 为 MIT；声线模型是微软在线服务，不是开放模型。这里提交的是合成后的 MP4，离线可看。重新生成需要联网。画面用文泉驿微米黑绘制，插图是本仓库 SVG，不是实拍。 字幕：<a href="../assets/video/ch26-spl.srt">SRT</a>。由 <code>python3 tools/gen_narrated.py --speak</code> 用 ffmpeg 合成。</sub>
</p>

**旁白（与字幕、配音同一份稿）**

1. 本章只认 STM32F10x SPL V3.5.0。F103C8、CB 使用中容量设备宏，启动文件和链接脚本也要匹配。只复制 main，工程不会一致。
2. SPL 工程至少包含 CMSIS、设备头、驱动、启动文件、SystemInit 和应用。缺 SystemInit，时钟假设不成立；缺启动文件，向量表和初始栈没有入口。
3. USE_STDPERIPH_DRIVER 载入标准库配置，STM32F10X_MD 选择中容量设备。两者必须进入真实编译命令，写在 IDE 截图里不会影响预处理。
4. 这一帧是仓库画的启动路径。复位后取栈顶，进入 Reset Handler，搬数据并清 BSS，调用 SystemInit，再到 main。SPL 不改变 Cortex-M 启动链。
5. SPL 常见顺序是先用 RCC 打开外设和 GPIO 时钟，再填初始化结构体，最后使能外设。时钟没开时，后面的寄存器写入不会形成你期待的硬件状态。这个规则和 HAL 工程完全相同。
6. USART SendData 只把一个数据写进数据寄存器。它不帮你发送整个缓冲，也不替你定义 TXE、TC 和超时。任何轮询等待都要有单调时钟截止点，超时后把原因交给上层策略。
7. 中断不来时按三张表排查：启动文件里的向量名字是否匹配，NVIC 是否使能且优先级合法，外设状态位和中断使能位是否同时成立。不要先把所有优先级都改成零。
8. SPL 和 HAL 会写同一组寄存器，却各自维护状态。双重初始化会覆盖波特率、DMA 和中断。迁移时一次只换一个外设，用同一波形对照。
9. 仓库示例在固定的 GNU Arm 工具链和冻结源码上编译。编译通过只证明接口和链接闭合；还要从 map 文件核对存储边界，再在真板上观察引脚、时钟和故障路径。
10. 合上书，三问。USE STDPERIPH DRIVER 和 STM32F10X MD 各管什么？USART SendData 到底保证什么？同一个串口为什么不能先用 SPL 初始化、再让 HAL 接管？
<!-- /video:ch26 -->
## 📌 学习目标

- [ ] 说清 SPL V3.5.0 的适用范围、工程目录和两个关键编译宏。
- [ ] 看懂 `RCC_*ClockCmd → *_StructInit → *_Init → *_Cmd` 的统一初始化顺序。
- [ ] 能把 GPIO、EXTI、TIM、USART、I2C、SPI、ADC、DMA、Flash、CAN 的 HAL 调用映射到 SPL API。
- [ ] 知道 SPL 中断没有 HAL 回调，必须在 IRQHandler 中检查并清除标志。
- [ ] 能判断旧 SPL 工程应该维护、局部迁移还是整体迁到 HAL/LL。

## 🧭 1. 先钉死版本与边界

本章只讲 **STM32F10x Standard Peripheral Library V3.5.0**。ST 的官方产品入口是 **STSW-STM32054**；API 名称和目录结构按 V3.5.0 源码核对。源码镜像冻结在 commit `afa743577f2784e95be2d5003380fdb84a702519`，它用于稳定定位文件，**不是新的规范来源**。寄存器行为仍以目标芯片参考手册 RM0008 和数据手册为准。

| 问题 | 本章结论 |
| --- | --- |
| SPL 适合哪些芯片 | 本章限定 STM32F10x；不要把 F1 的 `stm32f10x_*` 文件复制到 G0、L4、H7 |
| 新项目是否优先 SPL | 不优先。新系列和 CubeMX 工作流使用 HAL/LL；SPL 主要用于读懂、维护和迁移旧 F1 工程 |
| SPL 是否等于 CMSIS | 不等于。CMSIS 给内核与设备寄存器定义；SPL 在其上提供外设结构体和函数 |
| SPL 是否比 HAL “更底层” | 通常更薄，但仍是函数封装；是否更快必须看编译结果和测量，不能只看 API 名字 |
| 能否在同一外设混用 SPL 与 HAL | 技术上都写同一组寄存器，但状态假设互不知情；同一外设应由一个驱动体系负责 |

SPL 的价值不是背函数名，而是看清四层：

1. `stm32f10x.h` 提供设备、寄存器地址和位定义。
2. `stm32f10x_gpio.h` 等头文件提供配置结构体、常量与函数声明。
3. `stm32f10x_gpio.c` 等源文件把结构体字段写进寄存器。
4. 你的工程负责时钟、引脚、调用顺序、中断边界、超时和业务状态机。

## 🗂️ 2. 工程骨架：少一个文件都可能“函数有声明、链接没实现”

V3.5.0 包的关键目录如下：

```text
Libraries/
├── CMSIS/                              内核、设备定义、启动与 system 文件
└── STM32F10x_StdPeriph_Driver/
    ├── inc/                            stm32f10x_gpio.h、usart.h、dma.h …
    └── src/                            与头文件一一对应的 .c 驱动
Project/
├── STM32F10x_StdPeriph_Template/
│   ├── main.c
│   ├── stm32f10x_conf.h
│   ├── stm32f10x_it.c / .h
│   └── system_stm32f10x.c
└── STM32F10x_StdPeriph_Examples/       按外设分类的官方示例
```

### 两个必须显式确认的编译宏

| 宏 | 作用 | 配错时的现象 |
| --- | --- | --- |
| `STM32F10X_MD` | 选择 F103C8/B 一类中容量器件定义 | 中断号、外设能力或启动文件与芯片不匹配 |
| `USE_STDPERIPH_DRIVER` | 让 `stm32f10x.h` 引入 `stm32f10x_conf.h` | `GPIO_InitTypeDef`、`RCC_APB2PeriphClockCmd` 等声明不可见 |

密度宏必须按确切料号选，不能因为教程用了 BluePill 就永远写 `STM32F10X_MD`。工程还要同时满足：

- 头文件搜索路径包含 CMSIS、设备头文件和 `StdPeriph_Driver/inc`；
- 工程实际编译用到的 `StdPeriph_Driver/src/*.c`，不是只把 `inc` 加进去；
- `stm32f10x_conf.h` 只包含需要的驱动头文件，或明确接受全部模块带来的编译开销；
- 启动文件、链接脚本、密度宏和目标芯片属于同一容量档；
- `system_stm32f10x.c` 的系统时钟假设与板上晶振一致。

### `assert_param` 不是产品故障处理

SPL 用 `assert_param()` 检查函数参数。开发期可把 `USE_FULL_ASSERT` 打开，错误会进入 `assert_failed()`；发布版关闭后，这些检查通常不再执行。它不能替代通信超时、传感器离线、DMA 传输错误或 Flash 写失败的运行时处理。

## 🔁 3. 统一调用模型：时钟、默认值、配置、使能

大多数 SPL 外设都遵循同一顺序：

```c
RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

GPIO_InitTypeDef io;
GPIO_StructInit(&io);                 /* 先取得库定义的默认值 */
io.GPIO_Pin   = GPIO_Pin_9;
io.GPIO_Mode  = GPIO_Mode_AF_PP;
io.GPIO_Speed = GPIO_Speed_50MHz;
GPIO_Init(GPIOA, &io);
```

这四步分别对应四个边界：

1. **开时钟**：没有时钟，外设寄存器写入不会按预期生效。
2. **填默认值**：结构体局部变量未初始化时，未赋值字段是随机值。
3. **覆盖目标字段**：每个字段都要与接线、时钟和协议对上。
4. **显式使能**：`USART_Cmd()`、`SPI_Cmd()`、`TIM_Cmd()`、`DMA_Cmd()` 通常在配置完成后调用。

不是每个外设都有完全相同的函数名。判断顺序要回到头文件原型和 RM0008，不要凭“其他外设也是这样”补一个不存在的 `*_Cmd`。

## 💡 4. 一份实际编译链接的 SPL 点灯最小闭环

下面代码面向常见 STM32F103C8 BluePill：PC13 板载 LED 低电平点亮。工程预定义 `STM32F10X_MD` 与 `USE_STDPERIPH_DRIVER`，`stm32f10x_conf.h` 至少包含 RCC 和 GPIO 驱动头文件。**V3.5.0 模板的 `stm32f10x_it.c` 已经定义了非 weak 的空 `SysTick_Handler`；必须把模板中的空处理器替换为下面的计数实现，不能在 `main.c` 再定义一个同名函数。**

```c
#include "stm32f10x.h"

/* main.c：时基状态只有这一处定义。 */
volatile uint32_t g_ms;

/* stm32f10x_it.c：本文件替换模板文件，不与模板同时编译。 */
extern volatile uint32_t g_ms;
void SysTick_Handler(void)
{
    g_ms++;
}

static void delay_ms(uint32_t delay)
{
    uint32_t start = g_ms;
    while ((uint32_t)(g_ms - start) < delay) {
        /* 等待 SysTick；产品代码可改成事件或 RTOS 延时 */
    }
}

static void led_init(void)
{
    GPIO_InitTypeDef io;

    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOC, ENABLE);
    GPIO_StructInit(&io);
    io.GPIO_Pin   = GPIO_Pin_13;
    io.GPIO_Mode  = GPIO_Mode_Out_PP;
    io.GPIO_Speed = GPIO_Speed_2MHz;
    GPIO_Init(GPIOC, &io);
    GPIO_SetBits(GPIOC, GPIO_Pin_13);       /* 低电平点亮，先熄灭 */
}

int main(void)
{
    SystemCoreClockUpdate();
    if (SysTick_Config(SystemCoreClock / 1000U) != 0U) {
        while (1) { /* 时基配置失败 */ }
    }

    led_init();
    while (1) {
        GPIO_ResetBits(GPIOC, GPIO_Pin_13);
        delay_ms(500);
        GPIO_SetBits(GPIOC, GPIO_Pin_13);
        delay_ms(500);
    }
}
```

这段代码已用冻结 commit `afa743577f2784e95be2d5003380fdb84a702519` 的真实 CMSIS 设备头、RCC/GPIO 驱动、medium-density 启动文件和 F103C8 链接脚本完成编译链接；对应可复验工程在 [`examples/spl-f1-blink/`](../examples/spl-f1-blink/)，同时给出命令行、CLion 和 VS Code 三条共用 CMake 的开发入口。冻结镜像把 `core_cm3.h` 保存为 `core_cm3.h.old`，工程仅在缺少正式文件名时复制到构建目录。GNU Arm 10.3.1 实测 ELF 为 text 1976 B、data 20 B、bss 1028 B，并且符号表只有一个 `SysTick_Handler`。硬件验收仍不是“链接通过”：下载后 LED 应以约 1 Hz 闪烁，调试器里的 `SystemCoreClock` 应等于真实主频；把系统时钟改掉后，闪烁周期也必须重新对账。

## 🧩 5. HAL、SPL 与寄存器怎样对上

下面不是机械替换表。HAL 往往维护 Handle 和状态，SPL 多数函数直接操作外设寄存器；把函数名换掉但保留旧状态机，最容易得到“能跑一会儿”的工程。

| 目标 | HAL 常见入口 | SPL V3.5.0 入口 | 最终硬件边界 |
| --- | --- | --- | --- |
| GPIO 时钟 | `__HAL_RCC_GPIOA_CLK_ENABLE()` | `RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE)` | `RCC_APB2ENR` |
| GPIO 配置 | `HAL_GPIO_Init()` | `GPIO_Init()` | `GPIOx_CRL/CRH` |
| GPIO 输出 | `HAL_GPIO_WritePin()` | `GPIO_SetBits()` / `GPIO_ResetBits()` / `GPIO_WriteBit()` | `GPIOx_BSRR/BRR` |
| EXTI 映射 | HAL GPIO EXTI 初始化 | `GPIO_EXTILineConfig()` + `EXTI_Init()` | `AFIO_EXTICR`、EXTI 寄存器 |
| NVIC | `HAL_NVIC_SetPriority/EnableIRQ()` | `NVIC_Init()`（`misc.c`） | NVIC ISER/IPR |
| 定时器时基 | `HAL_TIM_Base_Init()` | `TIM_TimeBaseInit()` | `TIMx_PSC/ARR/CR1` |
| PWM 通道 | `HAL_TIM_PWM_ConfigChannel()` | `TIM_OC1Init()` 等通道函数 | `TIMx_CCMR/CCER/CCR` |
| USART 配置 | `HAL_UART_Init()` | `USART_Init()` + `USART_Cmd()` | `USARTx_BRR/CR1/CR2/CR3` |
| USART 收发 | `HAL_UART_Transmit/Receive()` | `USART_SendData()` / `USART_ReceiveData()` + 标志轮询 | `USARTx_SR/DR` |
| I2C 事务 | `HAL_I2C_Mem_Read/Write()` | `I2C_GenerateSTART()`、`I2C_Send7bitAddress()`、事件/标志检查 | I2C 事件状态机 |
| SPI 收发 | `HAL_SPI_TransmitReceive()` | `SPI_I2S_SendData()` / `SPI_I2S_ReceiveData()` + 标志轮询 | `SPIx_SR/DR` |
| ADC 通道 | `HAL_ADC_ConfigChannel()` | `ADC_RegularChannelConfig()` | `ADCx_SQR/SMPR` |
| ADC 校准 | `HAL_ADCEx_Calibration_Start()` | Reset calibration → `ADC_StartCalibration()` → 等完成 | `ADCx_CR2` |
| DMA 配置 | `HAL_DMA_Init()` | `DMA_Init()` + `DMA_Cmd()` | `DMA_CCR/CNDTR/CPAR/CMAR` |
| DMA 剩余项 | `__HAL_DMA_GET_COUNTER()` | `DMA_GetCurrDataCounter()` | `DMA_CNDTR` |
| Flash 擦写 | `HAL_FLASHEx_Erase()` / `HAL_FLASH_Program()` | `FLASH_ErasePage()` / `FLASH_ProgramHalfWord()` | Flash 控制器状态机 |
| CAN 收发 | `HAL_CAN_AddTxMessage()` / `HAL_CAN_GetRxMessage()` | `CAN_Transmit()` / `CAN_Receive()` | bxCAN mailbox/FIFO |

### 轮询必须自己带超时

SPL 的 `USART_SendData()` 只写数据寄存器，不会像 `HAL_UART_Transmit(..., timeout)` 一样替你组织完整阻塞发送与超时。安全写法要把等待边界写出来：

```c
static int usart1_send_byte(uint8_t byte, uint32_t spin_limit)
{
    while (USART_GetFlagStatus(USART1, USART_FLAG_TXE) == RESET) {
        if (spin_limit-- == 0U) return -1;
    }
    USART_SendData(USART1, byte);
    return 0;
}
```

`spin_limit` 只是教学上的有界等待；产品里应换成由可靠时基计算的截止时间，并定义超时后的恢复动作。

## ⚡ 6. 中断模型：没有 HAL 回调替你分发

HAL 常见写法是 IRQHandler 调 HAL，再进入 `HAL_GPIO_EXTI_Callback()`。SPL 工程通常直接在 `stm32f10x_it.c` 的 IRQHandler 中检查来源、清标志、投递事件：

```c
static volatile uint8_t g_key_event;

void EXTI0_IRQHandler(void)
{
    if (EXTI_GetITStatus(EXTI_Line0) != RESET) {
        EXTI_ClearITPendingBit(EXTI_Line0);   /* 先确认来源，再清挂起 */
        g_key_event = 1U;                     /* ISR 只交接事件 */
    }
}
```

必须逐项对账：

- `EXTI_Init()` 只配 EXTI 线；GPIO 到 EXTI 的端口映射还要 `GPIO_EXTILineConfig()`。
- NVIC 分组由 `NVIC_PriorityGroupConfig()` 设定，通道由 `NVIC_Init()` 使能。
- 每个 IRQHandler 必须检查真实来源，因为多个事件可能共用向量。
- 清除规则按外设不同：有的写专用清除位，有的要求读状态再读数据。USART 的 ORE 仍遵守“读 SR 再读 DR”，不能用一个看起来相似的 Clear 函数代替。
- ISR 不做阻塞发送、I2C 完整事务、Flash 擦除或长延时；只保存最小证据并交给主循环/任务。

## 🚚 7. DMA 模型：SPL 不会自动把两个驱动绑在一起

以 USART1 TX 为例，至少要完成三件事：

1. 给 DMA1 开时钟，按 RM0008 请求映射选择 DMA1 Channel 4。
2. `DMA_Init(DMA1_Channel4, ...)` 配地址、方向、项数、增量和宽度。
3. `USART_DMACmd(USART1, USART_DMAReq_Tx, ENABLE)` 打开 USART 的 DMA 请求，再 `DMA_Cmd()` 启动通道。

```c
DMA_InitTypeDef dma;

RCC_AHBPeriphClockCmd(RCC_AHBPeriph_DMA1, ENABLE);
DMA_DeInit(DMA1_Channel4);
DMA_StructInit(&dma);
dma.DMA_PeripheralBaseAddr = (uint32_t)&USART1->DR;
dma.DMA_MemoryBaseAddr     = (uint32_t)tx_buffer;
dma.DMA_DIR                = DMA_DIR_PeripheralDST;
dma.DMA_BufferSize         = tx_length;
dma.DMA_PeripheralInc      = DMA_PeripheralInc_Disable;
dma.DMA_MemoryInc          = DMA_MemoryInc_Enable;
dma.DMA_PeripheralDataSize = DMA_PeripheralDataSize_Byte;
dma.DMA_MemoryDataSize     = DMA_MemoryDataSize_Byte;
dma.DMA_Mode               = DMA_Mode_Normal;
dma.DMA_Priority           = DMA_Priority_Low;
dma.DMA_M2M                = DMA_M2M_Disable;
DMA_Init(DMA1_Channel4, &dma);

USART_DMACmd(USART1, USART_DMAReq_Tx, ENABLE);
DMA_Cmd(DMA1_Channel4, ENABLE);
```

边界与 HAL 相同：缓冲区在完成前必须继续存在；方向、宽度和增量必须与真实寄存器匹配；循环接收用 `DMA_GetCurrDataCounter()` 得到的是**剩余项数**，不是新增长度。F1 无 D-Cache，不代表这段代码能原样搬到 H7。

## 🧰 8. 各外设最小调用链

| 外设 | SPL 最小调用链 | 最容易漏的边界 |
| --- | --- | --- |
| GPIO | RCC → `GPIO_StructInit` → `GPIO_Init` → Set/ResetBits | F1 复用重映射还要 AFIO 时钟 |
| EXTI | GPIO 输入 → AFIO → `GPIO_EXTILineConfig` → `EXTI_Init` → `NVIC_Init` | 挂起位不清会反复进中断 |
| TIM PWM | RCC/GPIO → `TIM_TimeBaseInit` → `TIM_OCxInit` → `TIM_Cmd` | TIM1/TIM8 还要 `TIM_CtrlPWMOutputs` |
| USART | RCC/GPIO → `USART_Init` → `USART_Cmd` → 标志+Send/ReceiveData | TXE 与 TC 不是同一个完成边界 |
| I2C | RCC/GPIO 开漏 → `I2C_Init` → `I2C_Cmd` → START/地址/事件/数据/STOP | 库不替你定义事务超时和总线恢复 |
| SPI | RCC/GPIO/CS → `SPI_Init` → `SPI_Cmd` → TXE/RXNE/BSY 对账 | 每发一字节也会收到一字节；结束前等 BSY 清零 |
| ADC | RCC/模拟脚 → `ADC_Init` → 通道 → Cmd → 复位校准/校准 → 启动 | F1 校准顺序与采样时间 |
| DMA | RCC → `DMA_DeInit/StructInit/Init` → 外设 DMA 请求 → `DMA_Cmd` | 请求映射固定、计数单位由宽度决定 |
| Flash | Unlock → ClearFlag → Erase/Program → 检查状态 → Lock | 页对齐、半字对齐、掉电恢复 |
| CAN | RCC/GPIO → `CAN_Init` → `CAN_FilterInit` → IRQ/NVIC → Transmit/Receive | 单节点正常模式无人 ACK |

这张表只给顺序，不替代对应章节：时钟看第 2 章，GPIO 看第 3 章，NVIC 看第 4 章，TIM 看第 5 章，USART/I2C/SPI/ADC/DMA/CAN 分别看第 6–10、13 章。

## 🔀 9. 维护旧工程：先冻结，再迁移

不要把迁移理解成全局搜索函数名。按下面顺序做：

1. **冻结能复现的旧基线**：芯片完整料号、SPL 版本、密度宏、编译器、启动文件、晶振、链接脚本和板卡丝印。
2. **画外设所有权表**：每个外设当前由 SPL、裸寄存器还是第三方组件负责。
3. **一次迁一个外设**：保留接线、时钟、输入数据和仪器条件，只改驱动层。
4. **对比可见结果**：GPIO 电平、PWM 周期、UART 帧、DMA 缓冲位置、Flash 校验值。
5. **清掉旧所有权**：迁到 HAL 后，删除该外设对应的 SPL 初始化和 IRQ 处理，不能双初始化。

### 什么时候保留 SPL

- 已量产 F1 产品，工具链、测试和故障记录都围绕 V3.5.0 建立；
- 改动范围小，重新认证或全量回归的成本高；
- 团队能继续锁定编译器、库包和构建环境。

### 什么时候迁到 HAL/LL

- 新系列没有对应 SPL；
- 需要 CubeMX、现代中间件或同一套跨系列 BSP；
- 旧工程混用了多个来源不明的 SPL 副本，已经无法确认版本；
- 需要持续获得当前工具链与生态支持。

## ⚠️ 10. 常见坑与排查

| 现象 | 第一处边界 | 处理 |
| --- | --- | --- |
| `GPIO_InitTypeDef` 未定义 | `USE_STDPERIPH_DRIVER` / conf 头 | 检查预定义宏和 `stm32f10x_conf.h` |
| 函数能编译但链接 undefined | 只有头文件，没有编译对应 `.c` | 把需要的 `StdPeriph_Driver/src` 加入工程 |
| IRQ 名称正确但不进入 | 启动文件、密度宏或 NVIC 配置不匹配 | 对照向量表、目标料号和 `NVIC_Init` |
| 点灯电平相反 | BluePill PC13 LED 为低有效 | 先查原理图，再决定 Set/Reset |
| 串口最后一字节被截 | 只等 TXE，没等 TC | 改方向/关发送前等待 `USART_FLAG_TC` |
| I2C 卡死在 while | SPL 事件轮询没有超时 | 每个等待加截止时间，并实现总线恢复 |
| ADC 第一批结果偏 | 未按 F1 顺序校准 | 复位校准、等待、启动校准、等待，再转换 |
| DMA 一启动就 TE | 通道映射、地址、时钟或宽度错误 | 从 RM0008 请求表和 CPAR/CMAR/CNDTR 开始查 |
| 加入 HAL 后偶发失灵 | 同一外设被 SPL/HAL 重复初始化 | 明确所有权，迁完删除旧初始化与 IRQ 路径 |
| 换到 H7 后“同名函数”找不到 | SPL 不是跨代统一 API | 重新按 H7 HAL/LL、内存域和 Cache 设计 |

## 🧪 动手实验

1. **SPL 点灯**：用本章最小代码让 PC13 约 1 Hz 闪烁。记录 `SystemCoreClock`、实测周期和误差。
2. **三层对照**：把一次 `GPIO_ResetBits(GPIOC, GPIO_Pin_13)` 单步进去，记录最终改变的寄存器；再与第 3 章 HAL 写法对照。
3. **USART 有界发送**：实现带截止时间的 `usart1_send_byte`，拔掉或错误配置时钟后确认函数能返回错误，而不是永久卡死。
4. **DMA 位置账**：循环接收时每次记录 `DMA_GetCurrDataCounter()`，用“缓冲总项数 − 剩余项数”计算写入位置，并处理回卷。
5. **迁移练习**：任选一个 SPL GPIO 或 USART 小工程，只迁一个外设到 HAL；验收波形不变，再删除旧驱动所有权。

自测：

1. `USE_STDPERIPH_DRIVER` 和 `STM32F10X_MD` 各决定什么？
2. SPL 的 USART 发送为什么不能只把 `USART_SendData()` 当成 `HAL_UART_Transmit()` 的同义词？
3. 同一 USART 为什么不应同时由 SPL 与 HAL 初始化？

## 🔗 相关资源

- ST 官方产品入口：[STSW-STM32054 — STM32F10x standard peripheral library](https://www.st.com/en/embedded-software/stsw-stm32054.html)。
- V3.5.0 冻结源码镜像：[commit `afa743577f2784e95be2d5003380fdb84a702519`](https://github.com/wajatimur/stm32f10x-stdperiph-lib/commit/afa743577f2784e95be2d5003380fdb84a702519)。镜像仅用于稳定定位 API/目录，不替代 ST 产品页和 RM0008。
- [第 0 章](00-如何学习STM32.md)：寄存器 / SPL / HAL+LL 的路线选择。
- [第 3 章](03-GPIO与LED.md)、[第 4 章](04-中断与NVIC.md)、[第 6 章](06-串口UART.md)、[第 10 章](10-DMA.md)：同一硬件边界的 HAL 与寄存器讲解。
