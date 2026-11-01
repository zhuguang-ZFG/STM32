# 18 常见问题 FAQ

> English: [FAQ](en/18-faq.md)

> 把新手最常踩的坑按「编译链接 / 下载调试 / 外设 / 硬件 / RTOS 与工具链」分类，给出**现象 / 原因 / 解决**，遇到问题先来这里搜关键词。

<p align="center">
  <img src="../assets/animations/toolchain-flow.svg" width="760" alt="编译 → 链接 → 烧录 → 运行的工具链数据流">
  <br><sub>▲ 动画：编译 → 链接 → 烧录 → 运行的数据流（作者自绘矢量图，非实拍）</sub>
</p>

<!-- video:ch18 -->
<p align="center">
  <video width="640" controls poster="../assets/video/ch18-faq.png">
    <source src="../assets/video/ch18-faq.mp4" type="video/mp4">
  </video>
  <br><sub>▲ 本章讲解视频（2.5 分钟）。<a href="../assets/video/ch18-faq.mp4">MP4</a> · <a href="../assets/video/ch18-faq.srt">字幕</a></sub>
</p>

<details>
<summary>旁白文字稿</summary>

1. 排错不要从改代码开始。先让现象稳定复现，再退到只点灯或只回环的最小工程。最小工程是好的，问题就在你后来加的那一块里。
2. 这一章的五步是：复现，最小化，二分，看证据，对照手册。前两步能解决大多数问题。一上来就二分一大坨新代码，你会把时间花在来回编译上。
3. 编译报一长串时，先看第一处真正的错误。找不到头文件，多半是包含路径，不是语法突然坏了。链接报未定义的符号，再去看你有没有把对应的源文件加进工程。
4. 这一帧是仓库画的分层。现象在引脚上，就同时怀疑引脚模式和接线。现象在 HAL 返回值里，就打印那个状态码，再对照它碰过的寄存器。不要每一层同时盲改。
5. 下载失败时，先看供电、地、SWD 两根线和复位。芯片认不出，就不要查优化等级。BOOT0 被拉高时，它跑的是系统存储器，你的程序看起来像没烧进去。
6. 外设完全没反应，老三样：时钟开了没有，引脚复用对不对，该清的标志清了没有。这三样过完，再去看波特率、过滤器和采样时间。顺序反了，会在细节里耗掉一个晚上。
7. 三条铁律：能测就别猜，先共地再看信号，一次只改一处。猜测式修改会让两个错误叠在一起，最后谁也不认领。
8. 这一章建议你故意制造一次错误，比如删掉一个头文件路径，看编译器怎么说，再改回来。见过真实报错的人，下次不会从最后一行开始慌。
9. 口诀：先复现，再缩到最小。前两步走完还不知道范围，再去二分和看证据。能测就别猜。
10. 合上书，三问。排错五步的前两步是什么？调试器认不出芯片时，先查代码还是先查线和 BOOT？为什么一次只改一处？

</details>
<!-- /video:ch18 -->

## 学习目标

读这一章之前：读过第 01 章，会编译、下载、连调试器。条目里提到的外设，回到对应的章节去看细节。十六进制、寄存器位这些基础不熟的话，先读第 00 章的「零基础预备」。

- [ ] 按「复现、最小化、二分、看证据、对照手册」五步排错，说出每一步要拿到什么结果
- [ ] 从现象判断该去五类条目（C、D、P、H、R）里的哪一类找
- [ ] 下载器认不出芯片时，按顺序查供电、共地、第 34 脚和第 37 脚、NRST、BOOT0，查完再碰代码
- [ ] 说出 BOOT0 和 BOOT1 的三种组合各从哪里启动，以及改了跳线为什么要复位
- [ ] 外设没反应时，先查「时钟开了没有、引脚复用对不对、标志清了没有」三样
- [ ] 读懂编译器的第一条错误，分清「找不到头文件」和「未定义的符号」
- [ ] 用最小工程打印 SYSCLK，判断 HSE 有没有起振

## 排错方法论（先做这 5 步）

**一句话结论：出了问题先让现象稳定复现，再退到只点灯、只回环的最小工程，然后才二分和看证据，每次只改一处。**

### 先打个比方

排错像看病。医生先问清楚什么时候疼、怎么疼，这是复现；再量体温、量血压，先排除大问题，这是最小化；然后分部位检查，缩小范围，这是二分；看化验单，而不是凭感觉，这是看证据；最后对照医学资料确认判断，这是对照手册。好医生不会一次开五种药，因为病好了也不知道是哪一种起的作用。排错一次只改一处，道理一样。

比方到这里为止。人的身体各不相同，芯片却是确定的电路：同样的接线、同样的程序、同样的输入，结果一定相同。所谓「偶尔出错」，多半是接触不良、供电不稳或者变量没有初始化，不是芯片在闹脾气。

### 1. 五步，按顺序走

下表从上往下做。前两步最便宜，也最容易被跳过，所以排在最前面。

| 步 | 动作 | 目的 |
| --- | --- | --- |
| 1 | **复现**：确认现象能稳定出现，记下触发条件 | 复现不了的问题，先怀疑硬件和接触 |
| 2 | **最小化**：退回到「只点灯、只回环」的最小工程 | 分清是板子、时钟的问题，还是后加的代码的问题 |
| 3 | **二分**：注释掉一半代码，或者一次只启用一个外设 | 快速找到引入问题的那一块 |
| 4 | **看证据**：串口日志、逻辑分析仪波形、HAL 返回值、`CFSR`/`BFAR` | 用数据代替猜测 |
| 5 | **对照手册**：查参考手册（RM）和数据手册（DS）里的寄存器与时序 | 确认「以为对」的地方是不是真的对 |

几个词先说清：**最小工程**是只剩时钟、一个灯和一路串口的程序，它能跑，打印出的 SYSCLK 又是 72000000，就说明芯片、供电、下载和时钟都没问题。**二分**是每次去掉一半可疑的东西，看问题还在不在；每一步排除一半，4096 行代码 12 步就能缩到 1 行。**证据**指能重复看到的东西：一行打印、一段波形、一个寄存器值。

> [!TIP]
> 三条铁律：**能测就别猜**，**先共地再看信号**，**一次只改一处**。一次改两处，两个错误会叠在一起，最后谁也说不清是哪一处起的作用。

### 2. 最小工程：只点灯、只回环

下面这段程序就是第 2 步要退回去的那个工程。它做三件事：上电打印一次 SYSCLK 和 PCLK2 的频率，PC13 的板载灯不停地闪，串口收到什么就回什么。HSE 没起振时，它不停在错误处理里，而是留在 HSI 上继续跑，并把这件事打印出来。

```c
/* main.c —— 最小验证工程：打印时钟 + PC13 闪灯 + USART1 回环（STM32F103C8T6）
 * SysTick_Handler 在 CubeMX 生成的 stm32f1xx_it.c 里，它调用 HAL_IncTick()，
 * HAL 的超时都靠它计时。 */
#include "stm32f1xx_hal.h"
#include <stdio.h>
#include <string.h>

#define LED_PORT    GPIOC
#define LED_PIN     GPIO_PIN_13         /* 板载 LED，低电平点亮 */
#define RX_WAIT_MS  500U                /* 每次最多等 500 ms 收一个字节 */

UART_HandleTypeDef huart1;

static HAL_StatusTypeDef SystemClock_Config(void);
static void bsp_init(void);
static void error_handler(void);

int main(void)
{
    char              msg[80];
    uint8_t           ch;
    HAL_StatusTypeDef clock_ok;

    HAL_Init();
    clock_ok = SystemClock_Config();    /* 失败时留在复位后的 HSI 8 MHz */
    bsp_init();                         /* HAL 按当前的 PCLK2 计算 BRR */

    (void)snprintf(msg, sizeof(msg), "SYSCLK=%lu Hz PCLK2=%lu Hz HSE %s\r\n",
                   (unsigned long)HAL_RCC_GetSysClockFreq(),
                   (unsigned long)HAL_RCC_GetPCLK2Freq(),
                   (clock_ok == HAL_OK) ? "ok" : "FAILED");
    (void)HAL_UART_Transmit(&huart1, (uint8_t *)msg, (uint16_t)strlen(msg), 100U);

    for (;;)
    {
        HAL_GPIO_TogglePin(LED_PORT, LED_PIN);                       /* 灯在闪：程序在跑 */
        if (HAL_UART_Receive(&huart1, &ch, 1U, RX_WAIT_MS) == HAL_OK)
        {
            (void)HAL_UART_Transmit(&huart1, &ch, 1U, 10U);          /* 收到什么回什么 */
        }
    }
}

static HAL_StatusTypeDef SystemClock_Config(void)   /* 成功：HSE 8 MHz × 9 = 72 MHz */
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState       = RCC_HSE_ON;
    osc.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    osc.PLL.PLLState   = RCC_PLL_ON;
    osc.PLL.PLLSource  = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLMUL     = RCC_PLL_MUL9;
    if (HAL_RCC_OscConfig(&osc) != HAL_OK)
    {
        return HAL_ERROR;               /* HSE 或 PLL 没起来：不切换时钟 */
    }

    clk.ClockType      = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                         RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider  = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2;
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    return HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2);
}

static void bsp_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_GPIOC_CLK_ENABLE();
    __HAL_RCC_USART1_CLK_ENABLE();

    io.Pin   = LED_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(LED_PORT, &io);

    io.Pin   = GPIO_PIN_9;              /* USART1_TX */
    io.Mode  = GPIO_MODE_AF_PP;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &io);

    io.Pin  = GPIO_PIN_10;              /* USART1_RX */
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &io);

    huart1.Instance          = USART1;
    huart1.Init.BaudRate     = 115200U;
    huart1.Init.WordLength   = UART_WORDLENGTH_8B;
    huart1.Init.StopBits     = UART_STOPBITS_1;
    huart1.Init.Parity       = UART_PARITY_NONE;
    huart1.Init.Mode         = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl    = UART_HWCONTROL_NONE;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;
    if (HAL_UART_Init(&huart1) != HAL_OK)
    {
        error_handler();
    }
}

static void error_handler(void)
{
    __disable_irq();
    for (;;) { }
}
```

逐段看：

- `SystemClock_Config()` 失败时直接返回，不进错误处理。复位后 SYSCLK 本来就是 HSI（RM0008 Rev 21 第 7.2.6 节），程序留在 8 MHz 上继续跑，最小工程照样能闪灯、能打印。
- `bsp_init()` 放在时钟设置之后。`HAL_UART_Init()` 每次都按当时的 PCLK2 重算波特率寄存器 BRR，所以就算掉在 8 MHz 上，115200 的打印也是对的，第一行会写 `SYSCLK=8000000 Hz ... HSE FAILED`。
- 灯在闪，说明程序在跑、SysTick 在走：`HAL_UART_Receive()` 的 500 ms 超时靠 SysTick 计时，SysTick 不走，灯翻转一次就停住。灯不闪、串口也没字，问题在更前面：供电、下载、启动模式，回到 D 类和 H 类条目。
- 串口回环用来确认接线：你打一个字，它回一个字。不打字时灯 1 s 闪一次（`RX_WAIT_MS` 是例程设定）。

不靠 HAL，直接读寄存器也能确认时钟和波特率。HAL 打印出来的数字和下面两个寄存器对不上，就说明某一步没按你以为的那样执行：

```c
uint32_t sws = RCC->CFGR & RCC_CFGR_SWS;   /* 0x0 = HSI，0x4 = HSE，0x8 = PLL（RM0008 Rev 21 第 7.3.2 节，位 3:2） */
uint32_t brr = USART1->BRR;                /* 72 MHz、115200 时 HAL 写的是 0x271；8 MHz 时是 0x45 */
```

### 3. 怎么用下面 38 条

38 条分五类，编号前缀是类别：`C` 是编译与链接，`D` 是下载与调试，`P` 是外设，`H` 是硬件，`R` 是 RTOS 与工具链。每一条都按「现象、原因、解决」写。原因一栏常常列了几种可能，先查最容易验证的那一种。

拿到一个问题，先按现象挑类别：电脑上就报错的看 C 类；板子连不上、程序下不进去看 D 类；程序在跑、某个外设不动作看 P 类；冒烟、发烫、灯不亮、反复复位看 H 类；用了 FreeRTOS 或者换了工具以后才出现的看 R 类。找到条目以后，仍然按上面的五步去验证，不要直接照抄「解决」那一行就改代码。

## 一、编译与链接

这一类的问题都发生在电脑上，板子还没参与。编译器常常一口气报几十行，先看第一条真正的 error，后面的多半是它连带出来的。

**C1 找不到 `stm32f1xx_hal.h`**
- **现象**：编译报 `fatal error: stm32f1xx_hal.h: No such file or directory`。
- **原因**：头文件搜索路径（Include Paths）里没有 HAL 的 `Inc` 目录。不是语法突然坏了。
- **解决**：在工程设置或 `CMakeLists.txt` 的 include 路径里加入 `Drivers/STM32F1xx_HAL_Driver/Inc` 和 `Core/Inc`。

**C2 链接报 `undefined reference to HAL_GPIO_Init`**
- **现象**：编译通过，链接时报未定义的符号。
- **原因**：编译只看声明，链接要找到定义。对应的源文件 `stm32f1xx_hal_gpio.c` 没有加入编译，或者 `stm32f1xx_hal_conf.h` 里没打开 `HAL_GPIO_MODULE_ENABLED`。
- **解决**：把用到的 HAL 源文件加入工程，并打开对应模块的宏。CubeMX 工程里在外设页启用这个外设，它会替你生成。

**C3 `region FLASH overflowed by N bytes`**
- **现象**：链接报 ROM 区（闪存）放不下。
- **原因**：代码和常量超出了芯片的闪存容量。F103C8 只有 64 KB（DS5319 Rev 20 第 7 节订货号说明）。
- **解决**：打开 `-Os` 优化，去掉 `printf` 的浮点支持，删掉没用的库；还放不下就换闪存更大的型号。

**C4 `region RAM overflowed`**
- **现象**：链接报 RAM 不够。
- **原因**：全局数组太大，或者链接脚本里给栈和堆预留得太多。F103C8 只有 20 KB SRAM（DS5319 Rev 20 表 2）。
- **解决**：缩小全局缓冲区；减小链接脚本里的 `_Min_Heap_Size` 和 `_Min_Stack_Size`。这两个数是链接时检查用的最小预留量。

**C5 重定义错误 `multiple definition of 'xxx'`**
- **现象**：链接报同一个符号定义了不止一次。
- **原因**：变量直接定义在头文件里，没有加 `static` 或 `extern`，被几个 `.c` 文件同时包含。
- **解决**：头文件里只写 `extern` 声明，定义放在某一个 `.c` 文件里。

**C6 `printf` 输出乱码或没有输出**
- **现象**：串口收到乱码，或者什么都没有。
- **原因**：没有输出，多半是 `printf` 没有重定向到串口（`_write` 或 `__io_putchar` 没实现），或者字符串末尾没有 `\n`，C 库把它留在缓冲区里还没发出去。乱码多半不是 `printf` 的问题，而是波特率或时钟不对，按 P3 查。
- **解决**：实现 `__io_putchar`，在里面调用 `HAL_UART_Transmit`；每行末尾带 `\r\n`，或者在开头调用 `setvbuf(stdout, NULL, _IONBF, 0)` 关掉缓冲；用 newlib-nano 时要打印浮点数，链接选项加 `-u _printf_float`。

**C7 编译报 `arm-none-eabi-gcc: not found`**
- **现象**：命令行编译失败。
- **原因**：工具链没有安装，或者没有加入 PATH 环境变量。
- **解决**：安装 Arm GNU Toolchain（旧名 GNU Arm Embedded Toolchain），把它的 `bin` 目录加入 PATH；或者直接用 CubeIDE 自带的工具链。

**C8 生成的 bin/hex 大得异常**
- **现象**：固件文件远超预期。
- **原因**：先分清看的是哪个文件。调试信息只在 `.elf` 里，不进 `.bin` 和 `.hex`；`.hex` 是文本格式，每个字节写成两个字符再加上记录头，本来就比 `.bin` 大两倍多。`.bin` 本身大得离谱（几百 MB），多半是某个段被放到了 RAM 地址，`.bin` 把闪存和 RAM 之间的空洞也填满了。真正的代码偏大，才是没用的库和完整版 `printf`。
- **解决**：用 `arm-none-eabi-size` 看 `text`、`data`、`bss` 三个数；打开 `-Os`、`-ffunction-sections -fdata-sections`，链接时加 `--gc-sections` 去掉没用到的代码。

## 二、下载与调试

这一类发生在电脑和芯片之间。先确认电和线，再怀疑软件：芯片都认不出来的时候，查优化等级没有意义。

**D1 `No target connected` / 连不上目标**
- **现象**：下载器报找不到目标。
- **原因**：板子没供电；没有共地；SWD 线接错（SWDIO 在 PA13，SWCLK 在 PA14）；程序把调试口关掉了。
- **解决**：逐根核对 SWDIO、SWCLK、GND、3.3 V；板子单独供电再试；按住复位再连接（工具里叫 Connect under reset）。

**D2 烧录后板子像「变砖」，再也连不上**
- **现象**：程序下载进去以后，SWD 再也连不上。
- **原因**：程序把 PA13、PA14 配成了普通 GPIO，或者用 AFIO 关掉了 SWD。芯片一复位就执行这段代码，调试器来不及接管。
- **解决**：两种救法任选一种。一是按住 NRST，在工具里选 Connect under reset，连上后再松开，然后整片擦除。二是把 BOOT0 拉高再上电，芯片从系统存储器启动，你的程序不会运行，SWD 就能连上，用 STM32CubeProgrammer 整片擦除后把 BOOT0 放回 0。

**D3 `Flash Download failed - Target DLL has been cancelled`**
- **现象**：下载到一半失败（这是 Keil 的提示）。
- **原因**：Flash 算法和型号不匹配，或者芯片开了读保护。
- **解决**：核对工程里选的 Flash 算法和芯片型号；读保护要在选项字节里把 RDP 改回无保护。改回去的同时，芯片会先整片擦除主闪存，程序会被清掉（PM0075 Rev 2 第 2.4.1 节）。

**D4 调试时断点不生效**
- **现象**：断点被跳过，或者工具提示断点数量超限。
- **原因**：用 ST-Link 调试 Flash 里的代码，只能用硬件断点，这颗 M3 只有 6 个（RM0008 Rev 21 第 31.12 节，FPB 的 6 个指令比较器）。软件断点要把那条指令改写成断点指令，Flash 里的指令不能这样随手改写。另一个原因是那一行被优化掉了。
- **解决**：删到 6 个以内；调试版本把优化改成 `-O0` 或 `-Og`。

**D5 单步执行「乱跳」**
- **现象**：单步时行号跳来跳去。
- **原因**：编译器优化把指令重排了，或者把函数内联了。
- **解决**：调试配置改成 `-O0` 或 `-Og`。

**D6 ST-Link 提示固件过旧**
- **现象**：连接时提示升级 ST-Link 固件。
- **原因**：旧固件和新版工具不兼容。
- **解决**：用 STM32CubeProgrammer 或 CubeIDE 里的 ST-Link 升级功能升级。克隆的 ST-Link 升级要慎重，可能升完就不能用了。

**D7 程序一进调试就停在 `HardFault_Handler`**
- **现象**：调试一启动就进 HardFault。
- **原因**：链接脚本或启动文件是按别的型号写的，栈顶初值超出了 20 KB SRAM，或者向量表不对；栈太小；访问了不存在的地址。
- **解决**：先读 `CFSR`。`BFAR` 只有在 `CFSR` 的 bit 15（BFARVALID）为 1 时才是这一次出错的地址（见第 17 章）。再核对链接脚本里的 RAM 大小和启动文件的型号。

## 三、外设

这一类是程序在跑、某个外设不动作。先查老三样：时钟开了没有，引脚复用对不对，该清的标志清了没有。三样都过了，再去看波特率、过滤器、采样时间这些细节。

**P1 GPIO 写了不动作**
- **现象**：调用 `HAL_GPIO_WritePin` 以后引脚没有变化。
- **原因**：忘了打开这个 GPIO 端口的时钟。没有时钟，寄存器写不进去。
- **解决**：先调用 `__HAL_RCC_GPIOx_CLK_ENABLE()`（x 换成端口字母），再初始化引脚。

**P2 按键按一次却进好几次中断**
- **现象**：按一下打印好几行。
- **原因**：机械触点接触的瞬间会弹跳几毫秒，产生好几个边沿，没有消抖。
- **解决**：软件消抖，在中断里记下时间，和上一次相差不到 10–20 ms（经验值）的边沿丢掉；或者在按键上加 RC 硬件消抖。

**P3 串口乱码**
- **现象**：收到的全是乱码。
- **原因**：两端波特率不一致；没有共地；芯片的时钟不是你以为的频率。最后一种最隐蔽：HSE 没起来时 SYSCLK 是 HSI 8 MHz，按 72 MHz 写死的 USART1 `0x271` 在这只时钟上是 12800，不是 115200。用 HAL 初始化时，HAL 会按当时的时钟重算 BRR，这种情况多出现在寄存器写死 BRR，或者运行中被时钟安全系统（CSS）切回 HSI 的程序里。`HSE_VALUE` 和板上晶振的频率不一致，HAL 也会算错。
- **解决**：两端统一波特率；共地；用上面的最小工程打印 SYSCLK，确认它是 72000000。

**P4 I2C 通信卡在 `HAL_I2C_Master_Transmit`**
- **现象**：程序卡住，或者返回超时。
- **原因**：没有上拉电阻；地址写错；总线被某个从机拉死在低电平。
- **解决**：SCL、SDA 各接一只上拉电阻到 3.3 V，4.7 kΩ 是常用值（经验值，DS5319 Rev 20 表 42 列 SCL 频率时也用它做条件）；核对 7 位地址，HAL 要的是左移一位后的值；总线被拉死时，把 SCL 当普通引脚手动打 9 个时钟脉冲，让从机释放 SDA（NXP UM10204 Rev 6 第 3.1.16 节）。

**P5 SPI 读 Flash 全是 FF**
- **现象**：读回来的数据全是 0xFF。
- **原因**：片选 CS 没有拉低；CPOL、CPHA 组成的 SPI 模式不对；MISO 没接上。
- **解决**：核对模式，W25Q 系列支持模式 0 和模式 3（Winbond W25Q 数据手册）；核对片选时序和接线；先读 JEDEC ID，读对了再读数据。

**P6 ADC 读数跳动大**
- **现象**：采样值不稳定。
- **原因**：参考电压不稳，LQFP48 封装没有单独的 VREF+ 脚，参考就是 VDDA（DS5319 Rev 20 表 47 注 3）；采样时间太短；信号源内阻太高。
- **解决**：VDDA 按 DS5319 Rev 20 图 14 加 10 nF + 1 µF 去耦；把采样时间加长；输入端加一只小电容做缓冲。

**P7 定时器 PWM 没有输出**
- **现象**：示波器上看不到波形。
- **原因**：没有调用 `HAL_TIM_PWM_Start` 启动 PWM；引脚的复用功能没配；通道选错。用 TIM1 这只高级定时器时，还要置 `TIMx_BDTR` 的 MOE 位（位 15），否则输出一直关着。
- **解决**：调用 `HAL_TIM_PWM_Start`（对 TIM1 它会顺带置 MOE），核对复用引脚和通道。寄存器写法要自己置 MOE。

**P8 DMA 只搬一次**
- **现象**：DMA 传完一次就停了。
- **原因**：通道配成了普通模式，你期待的却是循环模式。
- **解决**：改成 `DMA_CIRCULAR`；或者在传输完成回调里重新启动一次。

**P9 RTC 上电归零或者不走**
- **现象**：断电后时间丢了，或者 RTC 根本不走。
- **原因**：LSE 没有起振；VBAT 没接电池；负载电容选错；程序每次上电都重新初始化了 RTC，把计数器清零了。
- **解决**：接 32.768 kHz 晶振，负载电容在 5 pF 到 15 pF 里按晶振选，6 pF 不是必须值；晶振本身选负载电容 CL 不大于 7 pF 的，不要用 12.5 pF 的（DS5319 Rev 20 第 5.3.6 节表 23 下面的说明）；VBAT 接电池；上电先读备份寄存器里的标记，配过就跳过初始化。第 3 脚和第 4 脚、PRL = 32767，见第 11 章。

## 四、硬件

这一类先用万用表。量电压、量通断，比改代码快得多。

**H1 LED 不亮**
- **现象**：接上 LED 没有反应。
- **原因**：极性接反；限流电阻太大；引脚驱动能力不够。
- **解决**：核对阳极和阴极（长脚是阳极）。外接灯用第 03 章的第 10 脚和 270 Ω。第 2 脚 PC13 不能当电流源。大电流负载用三极管或 MOSFET 驱动。

**H2 芯片发热严重**
- **现象**：手摸上去发烫。
- **原因**：引脚短路；5 V 直接加到了不耐 5 V 的引脚上；电源接反。
- **解决**：立刻断电。查短路、量电压、核对电源极性，查清楚之前不要再上电。

**H3 上电没反应、电流为 0**
- **现象**：板子完全不取电流。
- **原因**：电根本没进来：电源没接好、线断了、保险丝或防反接二极管开路、稳压芯片坏了。电流为 0 和 BOOT0 无关，BOOT0 接错时芯片照样取电流，只是跑的不是你的程序。
- **解决**：从电源入口开始，沿着供电路径一路量到芯片的 VDD 脚，找到电压消失的那一段。有电流但程序不跑，再去查 BOOT0（D 类和下面的深入部分）。

**H4 复位一直在抖**
- **现象**：芯片反复复位。
- **原因**：NRST 上没有电容，受干扰；看门狗在复位芯片。
- **解决**：按 DS5319 图 31 在第 7 脚 NRST 加 0.1 µF 到地。看门狗的超时计算见第 11 章，这里不重复。

**H5 外部晶振不起振**
- **现象**：HSE 或 LSE 等待超时，芯片退回内部时钟。
- **原因**：负载电容不匹配；晶振虚焊；走线太长。
- **解决**：按晶振的规格书选负载电容，HSE 的 CL1、CL2 一般在 5 pF 到 25 pF 之间，估算时把引脚和板子的杂散电容按 10 pF 左右算进去（DS5319 Rev 20 第 5.3.6 节）；晶振和电容尽量贴近芯片；换一颗质量好的晶振试。

**H6 面包板接触不良**
- **现象**：时好时坏，碰一下就复位。
- **原因**：杜邦线和面包板的接触电阻大，线又太长。
- **解决**：换线、缩短连线，关键信号焊牢。

**H7 串口、下载的「共地」问题**
- **现象**：不共地时串口乱码，或者调试器连不上。
- **原因**：两套电源的地电位不同，信号的「0」和「1」没有共同的参考。
- **解决**：把两边的 GND 连在一起。这一条没有例外。

## 五、RTOS 与工具链

这一类多在加了 FreeRTOS、换了 IDE 或者重新生成代码以后出现。原理在第 15 章。

**R1 上了 RTOS 后 `HAL_Delay` 卡死**
- **现象**：调用 `HAL_Delay` 不返回。
- **原因**：HAL 的毫秒计数停了。一种是 SysTick 中断整个交给了内核，没人再调用 `HAL_IncTick()`；另一种是在调度器启动之前、调用过内核函数之后用了 `HAL_Delay`，这时内核挡住了优先级数值 5–15 的中断，HAL 的节拍中断也在里面。
- **解决**：仓库例程把 HAL 时基放在 TIM4，SysTick 留给内核，一个节拍 1 ms。调度器启动前，不要在内核调用之后用 `HAL_Delay`。

**R2 停在 `configASSERT` 的死循环里**
- **现象**：程序停在断言里。
- **原因**：看停在哪一行。停在 `port.c` 的 `vPortValidateInterruptPriority` 里，是调用 FromISR 的中断优先级数值太小（优先级过高）；停在队列或信号量的函数里，多半是传进去的句柄是空指针，对象创建失败了。
- **解决**：调用 FromISR 的中断，优先级数值要大于等于 5。`5 << 4 = 0x50`。数值更小的中断不得调用 FromISR。创建对象后检查返回值是不是 `NULL`。

**R3 任务创建返回失败**
- **现象**：`xTaskCreate` 返回的不是 `pdPASS`。
- **原因**：`configTOTAL_HEAP_SIZE` 不够，放不下这个任务的栈和 TCB。
- **解决**：加大堆，或者减少任务数、减小栈。栈的单位是字，128 字就是 512 字节。

**R4 中断里调用普通 API 出错**
- **现象**：在中断里调用 `xQueueSend`，程序停在断言里，或者随机 HardFault。
- **原因**：中断里只能用 FromISR 版本。普通版本会进内核的临界区，FreeRTOS 的 Cortex-M3 移植在那里检查当前是不是在中断里，是就断言。
- **解决**：改成 `xQueueSendFromISR`，结尾调用 `portYIELD_FROM_ISR`。

**R5 用了 RTOS 以后莫名进 HardFault**
- **现象**：随机 HardFault。
- **原因**：某个任务的栈溢出了，写坏了别的内存。
- **解决**：把 `configCHECK_FOR_STACK_OVERFLOW` 设成 2（不写时是 0，什么都不查），实现 `vApplicationStackOverflowHook()` 找出是哪个任务，再加大它的栈。

**R6 工具链报 `cannot open linker script`**
- **现象**：链接时找不到 `.ld` 脚本。
- **原因**：链接脚本的路径或文件名写错，或者复制工程以后没跟着改。
- **解决**：核对 `-T` 后面的 `.ld` 路径。CubeIDE 和 Keil 各自管理链接脚本，换工具时要重新指定。

**R7 CubeMX 重新生成代码，覆盖了自己的修改**
- **现象**：重新生成以后，手写的代码不见了。
- **原因**：代码写在了 `USER CODE BEGIN` 和 `USER CODE END` 之外。
- **解决**：所有自己的代码都放进 `/* USER CODE BEGIN xxx */ ... /* USER CODE END xxx */` 区间。

## 动手实验（排错训练）

下面每个实验都是故意制造一个错误，看清楚它的样子，再按条目修好。见过真实报错的人，下次不会从最后一行开始慌。

1. **实验一：故意制造 C1。** 在工程设置里删掉 `Core/Inc` 这条 include 路径，编译一次，再恢复。
   - 预期现象：编译报 `fatal error: main.h: No such file or directory`（或者别的头文件名），后面跟着一串连带的错误。
   - 怎么确认：只看第一条 error，它指出了缺的是哪个文件；路径恢复后，整串错误一起消失。
   - 没成功先查：删掉的路径没被用到时不会报错，换一条试；CubeIDE 要先 Clean 再 Build，否则用的是旧的编译结果。
2. **实验二：故意制造 P4。** 拔掉 I2C 总线上的上拉电阻，调用一次 `HAL_I2C_Master_Transmit`，把返回值打印出来。
   - 预期现象：返回 `HAL_ERROR`、`HAL_BUSY` 或 `HAL_TIMEOUT`，不是 `HAL_OK`。
   - 怎么确认：万用表量 SCL、SDA 的空闲电压。有上拉时接近 3.3 V，拔掉以后掉到接近 0 V 或者飘忽不定。
   - 没成功先查：很多传感器模块板上自带上拉，拔了外接的还有板上的，对照模块的原理图找。
3. **实验三：故意制造 D2，再救回来。** 在初始化里调用 `__HAL_AFIO_REMAP_SWJ_DISABLE()` 关掉 SWD，下载一次，然后按 D2 的两种办法各救一次。
   - 预期现象：下载成功后，下一次连接报找不到目标。
   - 怎么确认：用 Connect under reset，或者 BOOT0 拉高后上电，都能重新连上；整片擦除、BOOT0 放回 0 以后，板子恢复正常。
   - 没成功先查：ST-Link 的 NRST 线有没有接到板子的 NRST 上；BOOT0 跳线改完要复位或重新上电才生效，因为 BOOT 脚只在复位后锁存。
4. **实验四：故意制造 R1。** HAL 时基留在 SysTick，在 `xQueueCreate` 之后、`vTaskStartScheduler()` 之前加一句 `HAL_Delay(100)`。
   - 预期现象：程序停在这一句，调度器起不来，任务的灯一直不闪。
   - 怎么确认：调试器暂停，停在 `HAL_Delay` 的等待循环里；观察变量 `uwTick`，它不再增加。
   - 没成功先查：SysTick 的优先级数值小于 5 时不会被挡住，看 CubeMX 里它的优先级；`HAL_Delay` 放在了所有内核调用之前时也不会卡。改好的办法：时基换到 TIM4，并让它的优先级数值小于 5，或者干脆不在这段时间里延时。
5. **实验五：在最小工程里看 HSE 没起振的证据。** 把最小工程里的 `osc.HSEState` 改成 `RCC_HSE_OFF`，模拟晶振不起振，下载运行；再在 `bsp_init()` 之后加一句 `USART1->BRR = 0x271;`，模拟按 72 MHz 写死的波特率。
   - 预期现象：第一步串口打印 `SYSCLK=8000000 Hz PCLK2=8000000 Hz HSE FAILED`，字是对的；第二步串口助手在 115200 下只看到乱码，改成 12800 再按一下复位，字又对了。
   - 怎么确认：12800 = 8 000 000 / (16 × 39.0625)，`0x271` 拆开是整数部分 39、小数部分 1/16。
   - 没成功先查：有的 USB-TTL 芯片不支持 12800 这种非标准波特率，换一个支持自定义波特率的；改完记得把 `HSEState` 改回 `RCC_HSE_ON`。

做完这几个实验，把你在自己项目里遇到的新问题也按「现象、原因、解决」补进一张自己的表，每一行只写一个原因，并写上你是用什么证据确认的。

## 自测

1. BOOT1 = 0、BOOT0 = 1 时上电，CPU 从哪里开始执行？Flash 里的程序还在吗？要让它重新运行，需要做什么？
2. 一段寄存器代码把 USART1 的 BRR 写死成 `0x271`，可是 HSE 没起振，系统停在 HSI 8 MHz。实际波特率是多少？换成 HAL 初始化，还会这样吗？
3. 一颗 32.768 kHz 晶振标称负载电容 CL = 6 pF，引脚和板子的杂散电容按 2 pF 估，两只电容取一样大，各取多少皮法？
4. 程序在 Flash 里，调试时打了 8 个断点，有两个从来不停。为什么？
5. 程序加了 SPI 屏、I2C 传感器和 CAN 三样以后偶尔死机。按五步，第 2 步和第 3 步分别怎么做？

参考答案：

1. 从系统存储器启动，这颗芯片的系统存储器在 `0x1FFFF000`，里面是出厂的 Bootloader（RM0008 Rev 21 第 3.4 节表 9）。Flash 里的程序还在 `0x08000000`，没有被擦掉，只是没被执行。把 BOOT0 放回 0，再复位或重新上电；BOOT 脚在复位后 SYSCLK 的第 4 个上升沿才锁存，只改跳线不复位不生效。
2. `0x271` 的整数部分是 0x27 = 39，小数部分是 1/16 = 0.0625，USARTDIV = 39.0625。波特率 = 8 000 000 / (16 × 39.0625) = 8 000 000 / 625 = 12800。在 72 MHz 下是 72 000 000 / 625 = 115200。换成 HAL 初始化，`HAL_UART_Init()` 按当时的 PCLK2（8 MHz）重算 BRR，写成 `0x45`，波特率仍接近 115200，不会出现 12800；除非 HAL 初始化之后时钟又变了，比如 CSS 把系统切回了 HSI。
3. 两只电容相等时 CL = C / 2 + Cstray（DS5319 Rev 20 第 5.3.6 节的公式），6 = C / 2 + 2，C = 8 pF。这正是数据手册里的例子：6 pF 是晶振的负载电容，不是要焊的电容值。8 pF 落在 5 pF 到 15 pF 的范围里。
4. 用 ST-Link 调试 Flash 里的代码只能用硬件断点，这颗 M3 的 FPB 只有 6 个指令比较器（RM0008 Rev 21 第 31.12 节），第 7 个、第 8 个没有比较器可用。删掉两个，或者等前面的用完再打。
5. 第 2 步：退回只点灯、只回环的最小工程，确认芯片、供电、时钟和串口都正常，最小工程不死机。第 3 步：在最小工程上一次只加一样，先加 SPI 屏跑一段时间，再加 I2C，再加 CAN；死机出现在加了哪一样之后，问题就在那一样，或者在它和前面几样的配合里（共用的 DMA 通道、中断优先级、栈空间）。

## 原理与适用范围

> [!NOTE]
> 从这一节到「常见坑与出处」是深入部分，把前面的结论落到具体订货号、手册章节和能复算的数字上。第一次读可以先跳过，做完动手实验再回来对照。

这一章是索引，不是第二套外设教程，订货号仍是 STM32F103C8T6。下面把最容易查错的几条结论钉到手册上。

**38 条。**C1 到 C8 是 8 条，D1 到 D7 是 7 条，P1 到 P9 是 9 条，H1 到 H7 是 7 条，R1 到 R7 是 7 条：`8 + 7 + 9 + 7 + 7 = 38`。

**认不出芯片时先看的脚。**下载器报没有目标时，先看第 34 脚 PA13 = SWDIO、第 37 脚 PA14 = SWCLK、共地、3.3 V，以及第 7 脚 NRST。第 35 脚是 VSS_2，不是 SWCLK。这些都核对过，再看代码和优化等级；线还没核对就去改 `-O2`，是走错了方向。SWD 的接线图在第 01 章，这里不重画。见 [DS5319 SWD](#source-ds5319-swd)。

**复位电容。**第 7 脚 NRST 按 DS5319 图 31 接 0.1 µF 到地，也就是 100 nF。片内上拉的阻值这里不写。见 [DS5319 NRST](#source-ds5319-nrst)。

**启动模式。**RM0008 Rev 21 第 3.4 节表 9 规定了三种组合。第 44 脚 BOOT0 = 0 时（BOOT1 任意）从主闪存启动，主闪存在 `0x08000000`。BOOT1 = 0 且 BOOT0 = 1 时从系统存储器启动，这颗芯片的系统存储器在 `0x1FFFF000`，里面是出厂的 Bootloader。BOOT1 = 1 且 BOOT0 = 1 时从内置 SRAM 启动。`0x1FFFB000` 是互联型（STM32F105/107）的系统存储器地址，在这颗 C8 上不适用。BOOT 脚在复位后 SYSCLK 的第 4 个上升沿锁存，第 00 章也讲过；从待机模式醒来时还会重新采样。BOOT1 和 PB2 共用第 20 脚（DS5319 Rev 20 表 5）。见 [RM0008 启动](#source-rm0008-boot)。

**容量。**STM32F103x8 的闪存是 64 KB，SRAM 是 20 KB；xB 的 128 KB 不适用于 C8T6。链接报放不下时按这两个数估。见 [DS5319 SWD](#source-ds5319-swd)。

**掉回 HSI 的串口。**HSE 没起来时 SYSCLK 是 HSI 8 MHz。USART1 的 `0x271` 按 72 MHz 算是 115200，在 8 MHz 上是 12800，第 16 章也用了这组数，这一章不另画位帧。HAL 初始化时按当时的 PCLK2 重算 BRR，所以 12800 多出现在写死 BRR 的寄存器代码里。见 [RM0008 USART](#source-rm0008-usart)。

**LSE 电容。**LSE 仍是 32.768 kHz，接第 3 脚和第 4 脚，第 1 脚是 VBAT，PRL = 32767。负载电容按 5 pF 到 15 pF 的范围跟晶振一起选。数据手册例子里的 6 pF 是晶振的负载电容 CL，不是电容值，也不是必须值；CL = 6 pF、杂散电容 2 pF 时，算出来每只电容是 8 pF。见 [DS5319 LSE](#source-ds5319-lse)。

**RTOS 的两条。**仓库例程把 HAL 时基放在 TIM4，SysTick 留给内核，一个节拍 1 ms。见 [本仓库例程](#source-project-examples)。调用 FromISR 的中断，优先级数值要大于等于 5，`5 << 4 = 0x50`。推导在第 15 章，这里不重画那张优先级图。见 [FreeRTOS](#source-freertos-syscall)。

**外接灯。**跟第 03 章一样，外接灯接第 10 脚，串 270 Ω。第 2 脚 PC13 不拿来当电流源。见 [DS5319 GPIO](#source-ds5319-gpio)。

**换芯片时。**脚号、启动地址和容量只对 STM32F103C8T6（LQFP48）成立。换封装要重新查脚位表；换成互联型，系统存储器地址变成 `0x1FFFB000`；XL 密度器件还多一个从闪存第二个 Bank 启动的选项，C8 没有。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-18-boot-triage.svg" width="760" alt="认不出芯片时先看第 34 脚、第 37 脚和第 44 脚。BOOT0 为 1 且 BOOT1 为 0 时跑的是 0x1FFFF000">
  <br><sub>▲ 自绘。正常路径是第 44 脚 BOOT0 = 0，从 0x08000000 启动，探针接在第 34 脚 PA13 和第 37 脚 PA14。第 7 脚 NRST 上是图 31 的 0.1 µF。失败路径是 BOOT0 = 1 且 BOOT1 = 0，CPU 在 0x1FFFF000；或者还没看这四只脚就改优化等级。第 35 脚是 VSS_2，指向第 01 章。出处是 [DS5319](#source-ds5319-swd) 图 31 和表 5，以及 [RM0008 启动](#source-rm0008-boot)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/boot0-low.gif" width="640" alt="第 44 脚为 0，探针接在第 34 脚和第 37 脚，目标出现">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：第 44 脚为 0，探针接在第 34 脚和第 37 脚，目标出现。印刷以静态主图为准。BOOT0 为 1 和「先改优化等级」不在这条 GIF 上。</sub>
</p>

静态图从上往下读。顶上三行是第一眼要看的四只脚：第 34 脚 PA13 = SWDIO，第 37 脚 PA14 = SWCLK，第 7 脚 NRST 上的 0.1 µF，第 44 脚 BOOT0。中间「正常路径」一栏是 BOOT0 = 0，CPU 从 `0x08000000` 启动，探针接在第 34 脚和第 37 脚，共地，3.3 V。往下「失败路径」一栏是 BOOT0 = 1 且 BOOT1 = 0，CPU 在系统存储器 `0x1FFFF000`，Flash 里的程序看起来像没烧进去；另一种失败是没查这几只脚就去改 `-O2`。最下面的「旁注」提醒第 35 脚是 VSS_2。GIF 只演正常路径。章首的 `toolchain-flow.svg` 画的是编译、链接、烧录、运行这条数据流，对应 C 类和 D 类条目；编译箭头不进这张静态主图。

## 时序与状态

芯片认不出来或者程序不跑时，按下表从上往下查，前一行没过就不看下一行。脚号来自 [DS5319 SWD](#source-ds5319-swd)，启动地址来自 [RM0008 启动](#source-rm0008-boot)：

| 先看什么 | 值 | 下一步 |
| --- | --- | --- |
| 第 34 脚和第 37 脚 | PA13 = SWDIO，PA14 = SWCLK，共地，3.3 V | 没接好之前不要改代码 |
| NRST | 第 7 脚，0.1 µF | 按图 31；这一行不写上拉的阻值 |
| BOOT，正常 | BOOT0 = 0，主闪存 `0x08000000` | 从你的程序启动 |
| BOOT，出错 | BOOT0 = 1 且 BOOT1 = 0，`0x1FFFF000` | 跑的是出厂 Bootloader，程序看起来像没烧进去；`0x1FFFB000` 不适用于 C8 |
| 优化等级 | 线还没核对就改 `-O2` | 方向错了，回到第一行 |
| 容量 | 闪存 64 KB，SRAM 20 KB | 链接报不够时按这两个数估 |
| 串口 | HSI 8 MHz，`0x271` 没改 | 实际是 12800 |
| 时基 | TIM4，1 ms | SysTick 留给内核 |
| 优先级 | 数值大于等于 5 | `5 << 4 = 0x50` |
| 晶振 | 5 pF 到 15 pF，按晶振选 | 6 pF 不是必须值 |

复位以后，芯片按下面的顺序走到你的第一行代码（RM0008 Rev 21 第 3.4 节和第 7.2.6 节）。BOOT0 接错，坏在第 3 步：

| 步骤 | 发生了什么 |
| --- | --- |
| 1 | 复位释放，SYSCLK 是 HSI 8 MHz |
| 2 | 在 SYSCLK 的第 4 个上升沿锁存 BOOT0 和 BOOT1 |
| 3 | 按表 9 选启动存储器：主闪存或系统存储器映射到 `0x0000 0000`，原来的地址照样能访问；选 SRAM 时，SRAM 只在 `0x2000 0000` |
| 4 | 从 `0x0000 0000` 取栈顶初值，从 `0x0000 0004` 取复位向量，开始执行 |

## 常见坑与出处

每一行从左往右读：先认现象，再看原因和处理；最后两列写这条结论出自哪里，以及那份出处能证明到哪一步。

| 现象 | 原因 | 处理 | 出处 | 出处能证明的部分 |
| --- | --- | --- | --- | --- |
| 下载器报没有目标 | 线还没核对 | 先看第 34 脚、第 37 脚、地和 3.3 V | [DS5319 SWD](#source-ds5319-swd) | 第 34 脚 PA13 是 SWDIO，第 37 脚 PA14 是 SWCLK，第 35 脚是 VSS_2 |
| 程序像没烧进去 | 第 44 脚 BOOT0 被拉高 | 把 BOOT0 放回 0，再复位 | [RM0008 启动](#source-rm0008-boot) | BOOT1 = 0 且 BOOT0 = 1 时进 `0x1FFFF000`；C8 不是互联型 |
| 板子自己反复复位 | NRST 上没有图 31 的电容 | 按图 31 加 0.1 µF | [DS5319 NRST](#source-ds5319-nrst) | 图 31 的外部复位电容是 0.1 µF；这一行不写上拉的阻值 |
| 链接说 Flash 或 RAM 不够 | 按更大的型号在估 | 按 C8 的 64 KB 和 20 KB 估 | [DS5319 SWD](#source-ds5319-swd) | xB 的 128 KB 在 C8T6 上不适用 |
| 串口乱码，时钟却没核对 | 掉回了 HSI，BRR 还是按 72 MHz 写的 | 确认 SYSCLK 没有停在 8 MHz | [RM0008 USART](#source-rm0008-usart) | `0x271` 在 72 MHz 下是 115200，在 8 MHz 下是 12800 |
| LSE 的两只电容焊成了 6 pF | 把例子里晶振的 CL 当成了电容值 | 电容按晶振在 5 pF 到 15 pF 里选 | [DS5319 LSE](#source-ds5319-lse) | 6 pF 不是 LSE 一节规定的必须值；32.768 kHz 和 PRL = 32767 以第 11 章为准 |
| 上了 FreeRTOS 之后 `HAL_Delay` 不返回 | HAL 的节拍还挂在 SysTick 上 | 时基换到 TIM4 | [本仓库例程](#source-project-examples) | `examples/freertos-task` 的时基是 TIM4 |
| 一进中断就停在 `configASSERT` | 优先级数值太小 | 写成 5 到 15 之间的数 | [FreeRTOS](#source-freertos-syscall) | `5 << 4 = 0x50`；数值更小的中断不得调用 FromISR |
| 外接灯不亮，电阻值在一个范围里乱试 | 脚和电阻都没定下来 | 外接灯用第 03 章的第 10 脚和 270 Ω | [DS5319 GPIO](#source-ds5319-gpio) | 第 2 脚 PC13 不能当电流源；这一行不另选电阻 |
| 打了 8 个断点，有两个不停 | 硬件断点只有 6 个 | 删到 6 个以内 | [PM0056 DWT](#source-pm0056-dwt) | 这颗 M3 有 6 个硬件断点 |
| 解除读保护以后程序没了 | 把 RDP 改回无保护时会先整片擦除 | 动手前确认程序有备份 | [PM0075 RDP](#source-pm0075-rdp) | RDP 编程回读允许键 0xA5 时，先整片擦除主闪存 |
| TIM1 的 PWM 脚没有输出 | BDTR 的 MOE 没置 | 置 MOE，或用 `HAL_TIM_PWM_Start` | [RM0008 TIM](#source-rm0008-tim) | `TIMx_BDTR` 偏移 0x44，位 15 是 MOE |

这张表只收出处卡能直接证明的条目。I2C 的 9 个时钟总线恢复（NXP UM10204）、W25Q 的 SPI 模式（Winbond 数据手册）和按键消抖时间（经验值）不在附录 E 的出处卡里，所以只留在正文条目中，不进这张表。

## 相关资源

- 本仓库各章「常见坑与排查」小节：第 03~17 章逐外设覆盖。
- RM0008 / RM0090 参考手册：寄存器位定义与时序，是排错的最终依据。
- 数据手册 DS：电气参数（电压/电流/时钟），判断「是不是硬件超规格」。
- 官方工具：STM32CubeProgrammer（读保护/选项字节）、STM32CubeMX（配置核对）。
- 相关章节：第 01 章开发环境搭建、第 17 章调试与性能优化、第 20 章学习资源与工具链。
- 配图：`../assets/animations/toolchain-flow.svg`（作者自绘矢量图）。



- 手机阅读版：[第 18 章 · 常见问题FAQ（公众号图文）](https://mp.weixin.qq.com/s/sbFdlK69-8L85F2KzWdTjg)
