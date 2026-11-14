---
title: "构建系统与遗留栈"
platforms: [f103, esp32]
---

# 构建系统与遗留栈

> 第 5 章把一行 C 送过四步，第 6 章把 `.elf` 拆到段、符号与 map。这一章往回退一步，问每次敲下 `make` 时，谁决定哪些文件要重来；再往前走一步，翻老 F1 工程的 SPL：它没有 Handle，也没有 CubeMX，只把寄存器写包进结构体和函数。构建系统的依赖图与 SPL 的封装术看似无关，判读方法却是同一条：先看清谁依赖谁，再谈抽象有没有漏掉一条边。

## 本章罗盘

- **问题**：Make 靠哪三样东西画图，`make -n` 看到的到底是什么？改头文件不重建，缺的是哪条边？CMake 为什么不直接构建，而要先“生成”？ESP-IDF 的 `idf_component_register` 与 RT-Thread 的 `SConscript` 为什么是同一副骨架？Kconfig 为什么说与构建系统正交？SPL 点灯最小闭环少一个文件会怎样？`GPIO_Init` 逐行动了哪几个寄存器、哪几位？SPL 三层怎样把一个字段翻译成位段？
- **交付**：能用 `make -n` 与 `touch` 观察局部重建；能写出最小裸机 CMake 骨架并说清工具链文件为何必须在 `project()` 之前；能读懂 IDF 组件声明与 SConscript 的对应；能为 F103 工程钉死 SPL 版本、宏、启动文件与驱动源文件；能按“先清后置、按位段移位”逐行讲 `GPIO_Init`；能用“API → 寄存器”反推法拆任意库函数。
- **边界**：双平台章。构建系统一侧来自 B7，与芯片无关；SPL 一侧限定 STM32F10x SPL V3.5.0，`GPIO_Init` 的逐行解剖来自 S15 对 F4 版 SPL V1.8.0 的取证，寄存器名逐版本标注，不把 F4 的 `MODER` 套到 F103 的 `CRL/CRH` 上。ESP32 一侧只使用 B7 记录的 ESP-IDF 工作流事实（CMake 组件、Kconfig、`idf.py`），ESP32-S3 的地址、时钟与外设留给卷 4。时钟树、NVIC 与 DMA 通道细节分别留给[第 8 章][ch08]、[第 10 章][ch10]、[第 14 章][ch14]。
- **依据锚点**：B7《构建系统：从手写 Makefile 到 CMake 与 scons》（`mcu/docs/build/07-build-system.md`）、根书第 26 章《STM32F10x 标准外设库（SPL）》（`docs/26-STM32F10x标准外设库SPL.md`）、S15《SPL 标准库解剖：库是怎么封装寄存器的》（`mcu/docs/stm32/15-spl-anatomy.md`）；[第 5 章](./05-toolchain-four-steps.md)的四步构建与[第 6 章](./06-linker-startup-map.md)的链接脚本。命令、版本、字节数与可见现象转引自上述来源；本机没接板的部分在“测量与证据”里标为未跑。

## 先做出来

不用开发板，只要有 `make` 和一个带 Makefile 的工程。进入来源书里的 `00-blink`（芯片是 F407，依赖图的形状与芯片无关，`mcu/code/stm32/00-blink/`），先押一个判断：真构建一次，再只 `touch` 一下 `main.c` 干跑，会列出整张图，还是只列出受 `main.c` 影响的那几个目标？

```bash
cd mcu/code/stm32/00-blink
make clean && make          # 先真构建，让 build/ 里每个目标都有产物
touch main.c && make -n     # 只动 main.c，再干跑
```

顺序不能省：来源书只记了 `make clean && make -n` 接 `touch main.c && make -n` 两条连跑的干跑，但 `make clean` 刚删掉 `build/`，`make -n` 又不产出文件，第二次干跑看到每个目标都缺失，仍会打印全量命令；那不是局部重建失效，而是实验里没有可比较的旧产物，读者复现这个观察应先跑一次真的 `make`。干跑输出要按“出现了哪些目标”读，而不是按行数读：`build/main.o` 因 `main.c` 变新而重建，`build/blink.elf` 与由它派生的 `build/blink.bin`、`build/blink.hex` 沿依赖边跟着重建，启动文件对应的 `build/startup_stm32f407xx.o` 不再重新编译；`all` 是伪目标，末尾那条 `$(SIZE)` 每次都会打印。如果改一个文件后所有 `.o` 都重新出现，说明依赖写成了“所有目标依赖所有源文件”，局部重建已经失效。`make -n` 不执行命令，只按同一套 mtime 比对把将执行的命令打印出来；`touch` 只改时间、不改内容，Make 仍然认为文件变了——它不读源码，只比较时间。这个观察留下一条判断标准：**构建系统不是“猜你改了什么”，而是“沿图上写明的边，比较两边的时间”。** 后面 CMake、IDF 与 scons 再花哨，也都在维护同一张图。

## 机制

### Make：目标、依赖、规则

Make 的世界只有三样东西：**目标**（要产出的文件）、**依赖**（产出它需要的文件）、**规则**（怎么从依赖造目标）。三者用 `:` 连起来就是一条规则：

```makefile
blink.elf: main.o startup.o
	$(CC) $(LDFLAGS) -o $@ $^
```

第二行开头必须是一个 Tab。自动变量 `$@` 是目标名，`$^` 是所有依赖，`$<` 是第一个依赖；模式规则 `%.o: %.c` 让每个 `.c` 自动对应一个 `.o`，不必逐文件手写。Make 的核心算法只有一条：目标比所有依赖都新就不重建，有任何依赖比目标新就重建。`00-blink` 的 Makefile 把这张图画成五个节点：`blink.elf` 依赖 `main.o`、`startup_stm32f407xx.o` 与 `linker.ld`，`blink.bin` 依赖 `blink.elf`，`flash`、`debug`、`gdb` 是伪目标。伪目标用 `.PHONY` 声明，不产出文件，不参与 mtime 比对；`linker.ld` 直接喂给 `ld`，它的入口、`KEEP` 与 `.data` 双地址在第 6 章拆过，这里只把它当成图上一份输入。

![构建系统依赖图：变化沿图上的边传播，局部重建由此发生](/anim/build-dep-graph.svg)

### 局部重建：只碰一个文件会发生什么

`touch main.c` 之后，`main.o` 因依赖变新而重建，`blink.elf` 跟着重建，`blink.bin` 再跟着重建；启动文件对应的目标不在链上，保持原样。变化沿图上的边传播，不沿目录传播。图上没有的边，变化就不会传播。来源点名的第一名嫌疑人是头文件：`main.o` 的依赖只写了 `main.c`，没写 `stm32f407.h`。改了头文件，`main.c` 的 mtime 没动，Make 认为 `main.o` 仍是最新的，固件里还是旧编译结果。补边的标准做法是让编译器自己登记：

```makefile
CFLAGS += -MMD -MP
-include $(OBJS:.o=.d)
```

`-MMD` 让 gcc 编译时顺带生成 `.d` 文件，把头文件依赖写进去；`-MP` 给每个头文件补一条空规则，头文件被删时不连带报错；`-include` 把这些 `.d` 读进 Make。手写的图会漏，编译器生成的图不会。

### CMake：先生成，再构建

CMake 不直接构建，它**生成** Makefile 或 Ninja 构建文件，多一层抽象，换来跨平台与组件化。最小裸机工程：

```cmake
cmake_minimum_required(VERSION 3.13)
set(CMAKE_TOOLCHAIN_FILE arm-none-eabi.cmake)   # 必须在 project() 之前
project(blink C)
add_executable(blink main.c startup.s)
target_compile_options(blink PRIVATE -mcpu=cortex-m4 -mthumb -Os)
target_link_options(blink PRIVATE -Tlinker.ld)
add_custom_command(TARGET blink POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE:blink> blink.bin)
```

```cmake
# arm-none-eabi.cmake
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR cortex-m4)
set(CMAKE_C_COMPILER arm-none-eabi-gcc)
set(CMAKE_ASM_COMPILER arm-none-eabi-gcc)
set(CMAKE_OBJCOPY arm-none-eabi-objcopy)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)   # 不试链接
```

两条铁律。第一，工具链文件必须在 `project()` 之前设置，否则 CMake 已经用主机 gcc 探测完环境，编出 x86 的东西。第二，`CMAKE_TRY_COMPILE_TARGET_TYPE` 设成 `STATIC_LIBRARY`，让探测停在编译，不去链接和运行一个 PC 上跑不了的交叉产物。生成层带来两段式命令：`cmake -B build` 生成，`make -C build` 构建。Ninja 只是换一个执行器，依赖图和命令行由生成物决定，人的工作方式不变。CMake 的价值在规模：两百个文件分在二十个目录，用 `add_subdirectory` 递归管理；代价是多一步生成，换了工具链文件不重新生成，构建还在用旧配置。

### IDF 与 scons：同一副骨架的两套剪裁

ESP-IDF 在 CMake 之上加了“组件”抽象。一个组件是一个目录，含 `CMakeLists.txt`、源码与 `Kconfig`，用 `idf_component_register` 声明自己：

```cmake
idf_component_register(
    SRCS "my_driver.c"
    INCLUDE_DIRS "include"
    REQUIRES driver          # 依赖其他组件
    PRIV_REQUIRES freertos   # 仅实现层依赖，不暴露给依赖我的组件
)
```

`REQUIRES` 把依赖组件的头文件传递给“依赖我的组件”，`PRIV_REQUIRES` 只给本组件实现用，这是接口与实现分离在构建层的体现。A `REQUIRES` B、B `REQUIRES` A 的循环依赖，标准解法是抽出公共部分进 C，A 和 B 都只依赖 C。IDF 的三层分工是：CMake 管组件，Kconfig 管配置，`idf.py` 负责调度；底层仍然是第 5 章那四步。

RT-Thread 用 scons，一套 Python 写的构建系统，配合同源的 Kconfig：

| 维度 | ESP-IDF | RT-Thread |
| --- | --- | --- |
| 构建系统 | CMake（生成 Ninja/Makefile） | scons（Python 脚本） |
| 配置系统 | Kconfig → sdkconfig | Kconfig → .config（同源） |
| 组件声明 | `idf_component_register` | `SConscript`（Python 函数） |
| 调度入口 | `idf.py build/flash` | `scons` / `scons -j4` |

差别只在构建脚本的语言：一边是 CMake 的 DSL，一边是 Python。底层都是依赖图加配置层两件事，会读一种就能读另一种。

### Kconfig：与构建系统正交的一维

Kconfig 把“编不编这个组件、开不开这个功能”变成菜单，`menuconfig` 打开，选择结果存进 `sdkconfig`，构建时生成 `sdkconfig.h` 供 C 代码包含：

```text
Kconfig（菜单定义）─menuconfig─> sdkconfig（选择结果）─生成─> sdkconfig.h（宏）
                                                                     │
                                                                     ▼
                                                          C 代码 #include，#ifdef 走分支
```

同一套机制，IDF 叫 `sdkconfig`，RT-Thread 叫 `.config`。**Kconfig 是独立的一维**：构建系统管“怎么编”，依赖图与命令行都在这一维；Kconfig 管“编什么”，哪些组件进、哪些宏开在另一维。两维各自演化，不互相绑死。由此带出一条仓库纪律：`sdkconfig` 是本地构建产物，不该提交；该提交的是 `sdkconfig.defaults`，它是默认值的种子，新人第一次 `idf.py build` 时由它生成本地 `sdkconfig`。

### 版本先钉死：只认 V3.5.0

本章只讲 **STM32F10x Standard Peripheral Library V3.5.0**，ST 的官方产品入口是 **STSW-STM32054**。源码镜像冻结在 commit `afa743577f2784e95be2d5003380fdb84a702519`，它只用于稳定定位文件与目录，不是新的规范来源；寄存器行为仍以 RM0008 和数据手册为准。

| 问题 | 本章结论 |
| --- | --- |
| SPL 适合哪些芯片 | 仅 STM32F10x；不要把 F1 的 `stm32f10x_*` 文件复制到 G0、L4、H7 |
| 新项目是否优先 SPL | 不优先；新系列用 HAL/LL，SPL 用于读懂、维护和迁移旧 F1 工程 |
| SPL 是否等于 CMSIS | 不等于；CMSIS 给内核与设备寄存器定义，SPL 在其上提供外设结构体与函数 |
| 能否在同一外设混用 SPL 与 HAL | 技术上都写同一组寄存器，但各自维护状态；同一外设只能有一个所有者 |

### 工程骨架：少一个文件就是链接错

```text
Libraries/
├── CMSIS/                              内核、设备定义、启动与 system 文件
└── STM32F10x_StdPeriph_Driver/
    ├── inc/                            stm32f10x_gpio.h、usart.h、dma.h …
    └── src/                            与头文件一一对应的 .c 驱动
Project/STM32F10x_StdPeriph_Template/   main.c、stm32f10x_conf.h、stm32f10x_it.c、system_stm32f10x.c
```

两个编译宏必须进入真实编译命令，写在 IDE 截图里不影响预处理：

| 宏 | 作用 | 配错时的现象 |
| --- | --- | --- |
| `STM32F10X_MD` | 选择 F103C8/B 一类中容量器件定义 | 中断号、外设能力或启动文件与芯片不匹配 |
| `USE_STDPERIPH_DRIVER` | 让 `stm32f10x.h` 引入 `stm32f10x_conf.h` | `GPIO_InitTypeDef`、`RCC_APB2PeriphClockCmd` 等声明不可见 |

工程还要同时满足五件事：头文件搜索路径包含 CMSIS、设备头与 `StdPeriph_Driver/inc`；实际编译用到的 `StdPeriph_Driver/src/*.c` 进了构建，不是只加 `inc`；`stm32f10x_conf.h` 只包含需要的驱动头文件，或明确接受全量模块的开销；启动文件、链接脚本、密度宏和目标芯片属于同一容量档；`system_stm32f10x.c` 的系统时钟假设与板上晶振一致。`assert_param()` 是开发期参数体检，打开 `USE_FULL_ASSERT` 时参数错误进入 `assert_failed()`，发布版关闭后通常不再执行；它替代不了通信超时、传感器离线、DMA 错误或 Flash 写失败的运行时处理。

### 调用模型：时钟、默认值、配置、使能

```c
RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
GPIO_InitTypeDef io;
GPIO_StructInit(&io);                 /* 先取得库定义的默认值 */
io.GPIO_Pin   = GPIO_Pin_9;
io.GPIO_Mode  = GPIO_Mode_AF_PP;
io.GPIO_Speed = GPIO_Speed_50MHz;
GPIO_Init(GPIOA, &io);
```

四步对应四个边界：开时钟，没有时钟时外设寄存器写入不会按预期生效；填默认值，结构体局部变量未初始化时，未赋值字段是随机值；覆盖目标字段，每个字段都要与接线、时钟和协议对上；显式使能，`USART_Cmd()`、`SPI_Cmd()`、`TIM_Cmd()`、`DMA_Cmd()` 通常在配置完成后调用。函数名不保证每个外设都一样，判断顺序要回到头文件原型和 RM0008，不能凭“其他外设也是这样”补一个不存在的 `*_Cmd`。

### SPL 最小闭环：一次能编译能链接的点灯

下面这段面向 STM32F103C8 BluePill，PC13 板载 LED 低电平点亮；工程预定义 `STM32F10X_MD` 与 `USE_STDPERIPH_DRIVER`，`stm32f10x_conf.h` 至少包含 RCC 和 GPIO 头文件。

```c
#include "stm32f10x.h"

volatile uint32_t g_ms;                 /* main.c：时基状态只有这一处定义 */
/* stm32f10x_it.c：替换模板文件，不与模板同时编译 */
extern volatile uint32_t g_ms;
void SysTick_Handler(void) { g_ms++; }

static void delay_ms(uint32_t delay)
{
    uint32_t start = g_ms;
    while ((uint32_t)(g_ms - start) < delay) { }
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
    GPIO_SetBits(GPIOC, GPIO_Pin_13);   /* 低电平点亮，先熄灭 */
}

int main(void)
{
    SystemCoreClockUpdate();
    if (SysTick_Config(SystemCoreClock / 1000U) != 0U) {
        while (1) { }
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

这段代码已用冻结 commit 的真实 CMSIS 设备头、RCC/GPIO 驱动、medium-density 启动文件和 F103C8 链接脚本完成编译链接，可复验工程在 `examples/spl-f1-blink/`。GNU Arm 10.3.1 的实测 ELF 是 text 1976 B、data 20 B、bss 1028 B，符号表里只有一个 `SysTick_Handler`。一个容易踩的坑：V3.5.0 模板的 `stm32f10x_it.c` 已经定义了非 weak 的空 `SysTick_Handler`，必须把这个文件替换成上面的计数实现，不能在 `main.c` 再定义一个同名函数，否则链接报重复定义。链接通过只证明接口和链接闭合，不证明板级行为；验收仍是下载后 PC13 约 1 Hz 闪烁，调试器里的 `SystemCoreClock` 等于真实主频。

### 中断与 DMA：SPL 不替你分发

HAL 的常见写法是 IRQHandler 调 HAL，再进入 `HAL_GPIO_EXTI_Callback()`。SPL 工程没有这层回调，通常直接在 `stm32f10x_it.c` 的 IRQHandler 里检查来源、清标志、交接事件：

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

逐项对账：`EXTI_Init()` 只配 EXTI 线，GPIO 到 EXTI 的端口映射还要 `GPIO_EXTILineConfig()`；NVIC 分组由 `NVIC_PriorityGroupConfig()` 设定，通道由 `NVIC_Init()` 使能；多个事件可能共用向量，每个 IRQHandler 都要检查真实来源；清除规则按外设不同，USART 的 ORE 仍遵守“读 SR 再读 DR”；ISR 不做阻塞发送、I2C 完整事务、Flash 擦除或长延时，只保存最小证据并交给主循环。NVIC 的仲裁与优先级在[第 10 章][ch10]展开。

DMA 同样不替你接线。USART1 TX 至少三件事：给 DMA1 开时钟，按 RM0008 请求映射选 DMA1 Channel 4；`DMA_Init()` 配地址、方向、项数、增量和宽度；`USART_DMACmd()` 打开 USART 的 DMA 请求，再 `DMA_Cmd()` 启动通道。关键调用是：

```c
RCC_AHBPeriphClockCmd(RCC_AHBPeriph_DMA1, ENABLE);
DMA_Init(DMA1_Channel4, &dma);          /* dma 已按外设地址、缓冲区、方向、项数、宽度填好 */
USART_DMACmd(USART1, USART_DMAReq_Tx, ENABLE);
DMA_Cmd(DMA1_Channel4, ENABLE);
```

两个边界：缓冲区在传输完成前必须继续存在；循环接收时 `DMA_GetCurrDataCounter()` 给的是**剩余项数**，不是新增长度，写入位置要用“总项数减剩余项数”算并处理回卷。F1 没有 D-Cache，不代表这段代码能原样搬到 H7；通道映射、DMA 控制器与缓存一致性都要按目标芯片重查，细节在[第 14 章][ch14]。

轮询也一样。`USART_SendData()` 只写数据寄存器，不会像 `HAL_UART_Transmit(..., timeout)` 那样替你组织完整发送与超时。安全的写法是在 `while` 等 TXE 时递减一个 `spin_limit`，到 0 返回错误；`spin_limit` 只是教学上的有界等待，产品里应换成由可靠时基计算的截止时间，并定义超时后的恢复动作。串口最后一字节被截，常见原因就是只等了 TXE、没等 TC；帧协议与错误恢复在[第 13 章][ch13]。

### SPL 三层：基址宏、结构体、位掩码

SPL 的封装术拆成三层基础设施：基址宏把地址变成名字，结构体把一串地址掰成命名字段，位掩码把第 N 位的值变成可读宏；函数只是把三层翻译成寄存器写。

![SPL 三层基础设施：基址宏给名字、结构体收字段、位掩码给位号](/figures/stm32-15-spl-tiers.svg)

这一节的取证对象是 F4 版 SPL V1.8.0 的 `stm32f4xx_gpio.c` / `stm32f4xx_rcc.c`，寄存器名是 F4 的。F103 的 V3.5.0 走同一套方法，但落点是 `GPIOx_CRL/CRH`（根书第 26 章的对照表），不是 `MODER`。

```c
#define AHB1PERIPH_BASE  (PERIPH_BASE + 0x00020000UL)   /* = 0x40020000 */
#define GPIOA_BASE       (AHB1PERIPH_BASE + 0x0000UL)
#define GPIOA            ((GPIO_TypeDef *) GPIOA_BASE)  /* 结构体指针，不是魔法 */

typedef struct {
  __IO uint32_t MODER;    /* 0x00：模式（2 位/引脚 × 16 引脚） */
  __IO uint32_t OTYPER;   /* 0x04：输出类型（1 位/引脚） */
  __IO uint32_t OSPEEDR;  /* 0x08：输出速度（2 位/引脚） */
  __IO uint32_t PUPDR;    /* 0x0C：上下拉（2 位/引脚） */
  __IO uint32_t IDR;      /* 0x10：输入数据（只读） */
  __IO uint32_t ODR;      /* 0x14：输出数据 */
  __IO uint32_t BSRR;     /* 0x18：位设置/复位（写 1 触发） */
  __IO uint32_t LCKR;     /* 0x1C：配置锁 */
  __IO uint32_t AFR[2];   /* 0x20-0x24：复用功能 */
} GPIO_TypeDef;

#define GPIO_MODER_MODER0_Msk   (0x3UL)   /* 2 位；枚举值即寄存器位段值 */
```

`__IO` 就是 `volatile`，寄存器访问每次都要真访存，否则连续两次写可能被合并（第 2 章）。成员顺序与偏移就是 RM0090 的寄存器布局，读 CMSIS 结构体等于读手册的寄存器表，偏移用第 3 章的 `offsetof` 断言核。关键设计是枚举值等于位段值：`GPIO_Mode_IN=0x00`、`GPIO_Mode_OUT=0x01`、`GPIO_Mode_AF=0x02`、`GPIO_Mode_AN=0x03`，所以翻译本质是把枚举值左移到对应引脚的位段，没有查表，只有移位。根书第 26 章按所有权把同一件事分成四层：`stm32f10x.h` 给设备与寄存器定义，外设头给结构体与声明，外设 `.c` 把字段写进寄存器，而时钟、引脚、调用顺序、中断边界、超时和业务状态机归你的工程。三层封装术到第四层收口。

### GPIO_Init 逐行：四段寄存器的位操作

![GPIO_Init 解剖：结构体打包、逐 pin 循环、位偏移、四段寄存器写入](/anim/spl-gpio-init.svg)

```c
void GPIO_Init(GPIO_TypeDef* GPIOx, GPIO_InitTypeDef *init)
{
  uint32_t pinpos, pos, currentpin;
  assert_param(IS_GPIO_ALL_PERIPH(GPIOx));
  assert_param(IS_GPIO_PIN(init->GPIO_Pin));
  assert_param(IS_GPIO_MODE(init->GPIO_Mode));

  for (pinpos = 0; pinpos < 16; pinpos++) {
    pos = ((uint32_t)0x01) << pinpos;
    currentpin = init->GPIO_Pin & pos;
    if (currentpin == pos) {                       /* 这个引脚被选中 */
      GPIOx->MODER &= ~(GPIO_MODER_MODER0_Msk << (pinpos * 2));
      GPIOx->MODER |= ((uint32_t)init->GPIO_Mode << (pinpos * 2));
      if (init->GPIO_Mode == GPIO_Mode_OUT || init->GPIO_Mode == GPIO_Mode_AF) {
        GPIOx->OTYPER &= ~((uint16_t)0x01 << pinpos);
        GPIOx->OTYPER |= (uint16_t)((uint16_t)init->GPIO_OType << pinpos);
        GPIOx->OSPEEDR &= ~(GPIO_OSPEEDR_OSPEEDR0_Msk << (pinpos * 2));
        GPIOx->OSPEEDR |= ((uint32_t)init->GPIO_Speed << (pinpos * 2));
      }
      GPIOx->PUPDR &= ~(GPIO_PUPDR_PUPDR0_Msk << (pinpos * 2));
      if (init->GPIO_Mode != GPIO_Mode_AN) {
        GPIOx->PUPDR |= ((uint32_t)init->GPIO_PuPd << (pinpos * 2));
      }
    }
  }
}
```

四个翻译要点：

1. **逐 pin 循环**：`GPIO_Pin` 是 16 位掩码，一次调用可能配多个引脚；循环逐位检测“这个引脚在不在掩码里”，在就走翻译。
2. **先清后置**：`MODER &= ~(mask << shift)` 先把这一位段清 0，`|=` 再置新值。直接赋值会覆盖其他引脚的配置，这是按位段操作的基本功。
3. **移位量由寄存器布局决定**：MODER、OSPEEDR、PUPDR 是 2 位/引脚，移 `pinpos * 2`；OTYPER 是 1 位/引脚，移 `pinpos`。
4. **枚举值即位段值**：`init->GPIO_Mode` 直接左移，没有查表，因为头文件把枚举定义成了与硬件编码相同的值。

库没有魔法，只有更周全的边界处理：循环多引脚、清旧值、断言。手写版是 `GPIOA->MODER |= (0x01 << (5 * 2))` 这样一行；库版把同一件事包进函数，代价是循环与分支。时钟使能也有一个容易被当成“就一句 `|=`”的细节。`RCC_AHB1PeriphClockCmd()` 在写 `AHB1ENR` 之后还补了一句 `(void)RCC->AHB1ENR;` 的读回。RM0090 有一条“外设时钟使能后，访问外设寄存器前需等几个时钟周期生效”。刚 `|=` 完立刻访问外设，可能在时钟还没真正喂到外设的那几个周期里读/写落空，现象是“配置了但没生效”。读回 `RCC->AHB1ENR` 强制一次总线往返，等流水线把写落地再继续；手写时要自己补 `(void)RCC->AHB1ENR;` 或 `__DSB();`。`assert_param` 则是 Debug 版的参数体检：打开 `USE_FULL_ASSERT` 时参数错误进入 `assert_failed()`，关闭时展开为 `((void)0)`，编译期完全消失。看到程序“卡死”在 `assert_failed` 的死循环，不是硬件挂了，是库在喊参数错了，看调用栈找传错的调用方。

把“GPIO_Init 反推法”带到别的函数上，方法不变：列结构体字段，查手册每个字段对应哪个寄存器位，再对照库源码核对翻译逻辑。`USART_Init` 的 `USART_BaudRate` 落 BRR，`WordLength` 落 CR1.M，`StopBits` 落 CR2.STOP，`Parity` 落 CR1.PCE 与 PS，`Mode` 落 CR1.TE/RE，`HardwareFlowControl` 落 CR3 的 CTSE/RTSE。HAL、LL、RT-Thread 驱动只是换皮，结构体字段名变了、断言宏变了，“结构体打包 + 位操作翻译 + 断言”这三板斧不变。至于什么时候用库、什么时候手写：初始化代码启动时跑一次，用库换可读性与防错；中断与性能热路径直接位操作；量产可以混合，配 `-ffunction-sections -fdata-sections` 与 `--gc-sections` 把没用到的库函数在链接时剔除（第 6 章）。

## 测量与证据

本章数字与方法来自 B7、根书第 26 章、S15 与第 5、6 章，工具链版本随来源标注。构建系统的命令输出与芯片无关；SPL 的数字来自 GNU Arm 10.3.1 的冻结工程。换版本、换板子，具体读数会变，判读方法不变。

| 取证项 | 来源命令 | 来源记录里的读数 |
| --- | --- | --- |
| Make 干跑 | `make clean && make`；`touch main.c && make -n` | 干跑列出将执行命令但不执行；真构建后再 `touch main.c`，干跑只出现 `main.o` 及依赖它的链接产物，启动文件目标不出现；按目标判读，不按输出长度（来源只记两条连跑的旧干跑序列，本章补一次真构建；未附逐行输出） |
| 00-blink 依赖图 | 读 `mcu/code/stm32/00-blink/Makefile` | `blink.elf`、`blink.bin`、`flash`、`debug`、`gdb` 五个节点，后三个是伪目标 |
| 头文件依赖 | 删掉依赖边后 `touch` 头文件 | `main.o` 只写 `main.c`，缺 `stm32f407.h` 的边；解法 `-MMD -MP` 生成 `.d` |
| CMake 生成 | `cmake -B build`，再 `make -C build` | 两段式：先生成构建文件，再构建 |
| IDF 组件 | `idf.py build` | `idf_component_register` 的 `SRCS`/`INCLUDE_DIRS`/`REQUIRES`/`PRIV_REQUIRES` |
| Kconfig | `menuconfig` | `Kconfig → sdkconfig/.config → 宏头`；提交 `sdkconfig.defaults` |
| SPL 版本 | 包与镜像 | V3.5.0；STSW-STM32054；镜像 commit `afa743577f2784e95be2d5003380fdb84a702519` |
| SPL 编译 | GNU Arm 10.3.1 | text 1976 B、data 20 B、bss 1028 B；符号表只有一个 `SysTick_Handler` |
| GPIO_Init 解剖 | S15 的 F4 V1.8.0 取证 | 16 次循环；MODER/OTYPER/OSPEEDR/PUPDR 四段；2 位/引脚移 `pinpos*2`，1 位/引脚移 `pinpos` |
| assert 开关 | `USE_FULL_ASSERT` | Debug 进 `assert_failed`；Release 展开 `((void)0)`，零开销 |
| 板级验收 | PC13 约 1 Hz、`SystemCoreClock` | 来源要求真板复核；本机未接板，本章只到构建闭合 |

判断“真的会了”：给你一个“改了头文件不重建”的工程，你能先用 `make -n` 证明图上有缺口，再用 `-MMD -MP` 补边；给你一个 CMake 交叉工程，你能从日志里的编译器路径判断工具链文件有没有生效；给你一个旧 F1 工程，你能列出 SPL 版本、两个宏、启动文件、链接脚本和实际参与编译的驱动源文件；给你一个库函数，你能说出它写哪几个寄存器、哪几位，再翻手册核对。

## 失败分支

| 现象 | 原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| 改了头文件，固件行为还是旧的 | 依赖图缺头文件边，`main.o` 没重建 | `touch` 头文件后 `make -n` 不列 `main.o`；工程里没有 `.d` 文件 | 加 `-MMD -MP` 并 `-include *.d` |
| CMake 编出 x86 的目标文件 | 工具链文件在 `project()` 之后才设，CMake 已用主机 gcc 探测 | 构建日志里的编译器路径是宿主 gcc | 把 `set(CMAKE_TOOLCHAIN_FILE ...)` 移到 `project()` 之前，删掉旧构建目录 |
| 交叉编译在探测阶段报“无法运行” | CMake 试链接并运行交叉产物 | 错误出现在 `project()` 的编译器检查 | 设 `CMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY` |
| IDF 组件互相 `REQUIRES`，配置报循环 | A 依赖 B、B 依赖 A | 组件依赖图成环 | 抽出公共组件 C，A、B 都只依赖 C |
| 同事拉下代码后配置全变 | `sdkconfig` 被提交，覆盖了本地选择 | 仓库里有 `sdkconfig`，没有 `sdkconfig.defaults` | 删掉 `sdkconfig`，提交 `sdkconfig.defaults` |
| `GPIO_InitTypeDef` 未定义 | `USE_STDPERIPH_DRIVER` 没进编译命令，或 `conf.h` 没包含 GPIO 头 | 预处理输出里找不到 `stm32f10x_conf.h` | 检查预定义宏与 `stm32f10x_conf.h` |
| 函数有声明，链接报 undefined | 只加了 `inc`，没编译对应的 `StdPeriph_Driver/src/*.c` | `nm` 里符号是 `U` | 把需要的驱动源文件加入构建 |
| IRQ 名字正确但不进入 | 启动文件、密度宏或 NVIC 配置不匹配 | 向量表里的名字与 `NVIC_Init` 的通道对不上 | 按目标料号统一启动文件、密度宏与 NVIC 配置 |
| `multiple definition of SysTick_Handler` | 模板 `stm32f10x_it.c` 与自己的实现同时编译 | 链接器点名两个目标文件 | 用自定义 `stm32f10x_it.c` 替换模板，不同时编译 |
| 串口最后一字节被截 | 只等 TXE，没等 TC | 发送完成边界与 `USART_FLAG_TC` 未对上 | 关发送或切方向前等待 TC |
| DMA 一启动就 TE | 通道映射、地址、时钟或宽度错误 | 从 RM0008 请求表核对 CPAR/CMAR/CNDTR | 重查通道映射与数据宽度 |
| 加入 HAL 后偶发失灵 | 同一外设被 SPL 与 HAL 重复初始化 | 两套初始化代码都还在，状态互不知情 | 明确所有权，迁完删除旧初始化与 IRQ 路径 |
| 编译报找不到 `core_cm3.h` | 冻结镜像把文件存成了 `core_cm3.h.old` | 文件列表里有 `.old` 后缀 | 由构建脚本复制到构建目录，不改上游检出 |

## 跨平台边界

构建系统这一层与芯片无关，但“两平台共用同一副骨架”要按维度拆开说。依赖图这一维确实共用：一张图按 mtime 决定重建，Make 的三要素、缺头文件边与 `-MMD -MP` 的补法，在 F103 与 ESP32 的工程里都按同一套问题去读。生成器这一维只对 CMake/IDF 成立：CMake 先产出构建文件再构建，ESP-IDF 在 CMake 之上用 `idf_component_register` 圈组件，这些事实都来自 B7 对 CMake 与 IDF 的记录，本章没有把它们写成 F103 一侧的机制。配置层这一维按平台各算各的：F103 的 SPL 工程用 `stm32f10x_conf.h` 选择包含哪些驱动头文件，用 `STM32F10X_MD` 与 `USE_STDPERIPH_DRIVER` 两个宏进入真实编译命令；ESP32 的 IDF 工程用 Kconfig 菜单把选择写进 `sdkconfig`，构建时生成 `sdkconfig.h`。同样是“配置决定编什么”，两套机制不同，不能互相搬。两条栈的所有权也不同。F103 侧的遗留栈是 SPL V3.5.0：版本、`STM32F10X_MD`、`USE_STDPERIPH_DRIVER`、启动文件、链接脚本和 `system_stm32f10x.c` 必须成套；ESP32 侧的工程单位是 ESP-IDF 组件，配置走 Kconfig 与 `sdkconfig`，调度入口是 `idf.py`。把 `stm32f10x_*` 文件搬到 ESP32，或把 ESP-IDF 的组件宏搬到 F1，都不是移植，只是把两套所有权混在一起。`GPIO_Init` 的逐行解剖也必须按版本读：S15 的取证对象是 F4 V1.8.0，寄存器是 `MODER/OTYPER/OSPEEDR/PUPDR`；F103 的 V3.5.0 走同一套“结构体 + 移位 + 断言”的方法，但落点是 `GPIOx_CRL/CRH`。方法可以带走，寄存器名、位段和时钟使能寄存器不能跨版本搬运。生成器与配置机制之外还有别的平台差异，本章没有逐项取证，留给卷 4 的[第 28 章](../v4-platforms/28-chip-migration-differences.md)与[第 29 章](../v4-platforms/29-gd32-arm-riscv.md)。

| 事项 | 本章的证据范围 | 跨平台时的处理 |
| --- | --- | --- |
| 依赖图、生成器、配置层 | 依赖图来自 B7 且与芯片无关；生成器记录属 CMake/IDF；配置层 F103 为 `stm32f10x_conf.h` + `STM32F10X_MD`/`USE_STDPERIPH_DRIVER`，ESP32 为 Kconfig → `sdkconfig` | 依赖图共用同一套读法；生成器只按 CMake/IDF 读，不外推到 F103；配置机制各按各的读，不互相搬 |
| ESP-IDF 工作流 | B7 记录的组件、Kconfig、`idf.py` | ESP32 侧按此读工程；ESP32-S3 的地址、启动与分区见[第 30 章](../v4-platforms/30-esp32s3-architecture-boot.md) |
| SPL 版本与宏 | 仅 STM32F10x V3.5.0 | 不复制到其它系列；ESP32 没有 SPL |
| GPIO 解剖 | S15 的 F4 V1.8.0；F1 的落点是 `GPIOx_CRL/CRH` | 方法复用，寄存器名逐版本对账 |
| 时钟、引脚、DMA 通道 | 本章不展开 | 见第 8、10、14 章；系列差异与迁移检查表见[第 28 章](../v4-platforms/28-chip-migration-differences.md)与[第 29 章](../v4-platforms/29-gd32-arm-riscv.md) |
| 板级行为 | 来源要求真板复核，本机未接板 | 两平台都只到构建闭合，烧录与波形待上板 |

## 离开检查

1. Make 的三要素是什么？`$@`、`$<`、`$^` 各指什么？`make -n` 为什么能看到依赖图？
2. `touch main.c` 之后，哪些目标会重建、哪些不会？如果改了头文件却没重建，缺的是哪条边，怎么补？
3. CMake 为什么说“不构建、只生成”？工具链文件为什么必须在 `project()` 之前设置？`CMAKE_TRY_COMPILE_TARGET_TYPE` 解决什么问题？
4. `REQUIRES` 与 `PRIV_REQUIRES` 的区别是什么？组件循环依赖的标准解法是什么？Kconfig 为什么是独立的一维？
5. SPL 点灯最小闭环至少要哪些文件与宏？少一个会出现什么现象？
6. `GPIO_Init` 为什么逐 pin 循环、为什么先清后置、移位量由什么决定？SPL 三层各把什么变成什么？

<details>
<summary>对照答案</summary>

1. 目标、依赖、规则。`$@` 是目标名，`$<` 是第一个依赖，`$^` 是所有依赖。`make -n` 不执行命令，只按同一套 mtime 比对把将执行的命令打印出来，所以能看到哪些节点会重建、按什么顺序执行。
2. `main.c` 变新让 `main.o` 重建，`main.o` 再让 `blink.elf` 与 `blink.bin` 重建；启动文件对应的目标不受影响。改头文件不重建，是因为 `main.o` 的依赖只写了 `main.c`，缺 `stm32f407.h` 这条边；用 `-MMD -MP` 让 gcc 生成 `.d` 依赖文件，再 `-include` 进 Make。
3. CMake 生成 Makefile 或 Ninja 构建文件，真正的编译链接由生成物执行。工具链文件必须在 `project()` 之前设，否则 CMake 已经用主机 gcc 探测完环境；`CMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY` 让探测停在编译，不去链接和运行 PC 上跑不了的交叉产物。
4. `REQUIRES` 把依赖组件的头文件传递给依赖我的组件，`PRIV_REQUIRES` 只给本组件实现用。循环依赖的标准解法是抽出公共部分进组件 C，A 与 B 都只依赖 C。构建系统管“怎么编”，Kconfig 管“编什么”，两维正交，同一份 Kconfig 可以喂给 CMake 或 scons。
5. 至少要有 CMSIS 设备头、`system_stm32f10x.c`、启动文件、链接脚本、`stm32f10x_conf.h`、实际参与编译的 `StdPeriph_Driver/src/*.c`，并定义 `STM32F10X_MD` 与 `USE_STDPERIPH_DRIVER`。缺头文件搜索路径或宏，声明不可见；只加 `inc` 不加 `.c`，链接 undefined；启动文件或密度宏错，中断号与向量表对不上；缺 `SystemInit`，时钟假设不成立。
6. 逐 pin 循环是因为 `GPIO_Pin` 是 16 位掩码，一次调用可能配多个引脚；先清后置是为了只改目标引脚的位段，保留其他引脚配置；移位量由寄存器布局决定，2 位/引脚移 `pinpos*2`，1 位/引脚移 `pinpos`。三层：基址宏把地址变成名字，结构体把地址掰成字段，位掩码把第 N 位变成可读宏；函数把三层翻译成寄存器写。

</details>

动作验收：在一个本地 Makefile 工程里用 `make -n` 与 `touch` 写下“哪些目标会重建”的预测，再实测对照；把一次交叉 CMake 配置的日志留下来，指出工具链文件的生效位置与编译器路径；最后打开一份 SPL 工程，列出 SPL 版本、两个宏、启动文件、链接脚本与参与编译的驱动源文件，并挑一个 `GPIO_Init` 调用，用“API → 寄存器”表写出它最终改了哪几个寄存器。

[ch08]: ../v1-drivers/08-architecture-memory-clock.md
[ch10]: ../v1-drivers/10-interrupts-nvic-exti.md
[ch13]: ../v1-drivers/13-uart-framed-protocol.md
[ch14]: ../v1-drivers/14-dma.md
