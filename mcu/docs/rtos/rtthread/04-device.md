---
title: R4 设备框架：驱动与应用的解耦术
status: done
difficulty: 2
minutes: 55
---

# R4 设备框架：RT-Thread 最灵魂的一章

> 🎯 裸机写应用，`uart_send()` 里全是寄存器；换块板子，应用层推倒重来。设备框架说：应用只跟"设备句柄"说话：`rt_device_open/read/write`，底下是 USART1 还是 UART5，应用不关心。**这就是驱动与应用解耦**，也是 RT-Thread 区别于"裸内核"的核心资产。

## 本章精髓

1. 设备=对象+操作表：`struct rt_device` 继承对象头，挂一张 ops 表（init/open/close/read/write/control）：驱动作者实现这张表，应用作者按统一 API 调用（与 Linux 字符设备的 file_operations 一脉相承）。
2. 注册与查找两分离：驱动 `rt_device_register(dev, "uart1")` 挂进对象容器；应用 `rt_device_find("uart1")` 按名取柄：**名字是接口，实现可替换**。
3. 框架之上的"设备类型"再封装：PIN（GPIO）、UART（串口带缓冲/回调）、I2C/SPI bus，越往上层，应用越无感；finsh 的 `list_device` 一屏看全家。

- **能理解**：为什么 register 和 find 要两分离而不是"创建即用"；为什么 PIN 不直接用 `rt_device_read/write` 而单独一套 `rt_pin_*`；为什么 UART 的 `rx_indicate` 在中断上下文而不是线程。
- **能用**：PIN 三行点灯、UART 中断接收回显、把蜂鸣器封成一个能被 `list_device` 看见的 `rt_device`。

## 先修

- [R0 对象模型](00-arch.md)、[S7 USART](../../stm32/07-usart.md)、[F4 队列](../freertos/04-queue.md)。

## 先跑起来（10 分钟 quick win）

标准版工程上 `list_device` 找到 "pin"，三行代码点 RGB 灯：

```c
rt_pin_mode(LED_R, PIN_MODE_OUTPUT);
rt_pin_write(LED_R, PIN_LOW);   /* 共阳：低电平亮 */
```

不用查任何一个寄存器，体会封装的甜。

先押个翻译官：应用那一行调用落到板上，变成谁的动作？寄存器直写在哪个环节被换的手？押完看下一节的调用链动画。

## 动画：设备框架调用链

一次 `rt_device_write` 从应用出发，穿过框架 API、ops 表、驱动，最终落到寄存器：四层各司其职，换板只换 ops 表，应用纹丝不动。

![R4 设备框架调用链：应用 → 框架 → 驱动 → 寄存器](/anim/rtt-device-chain.svg)

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 调用链全图 | 应用/框架/驱动/寄存器四层解剖 | 库解析 |
| rt_device 解剖 | ops 表逐字段；register/find/open 源码路径 | 库解析 |
| PIN 设备 | 编号体系（GET_PIN 宏）；点灯对照实验 | 配置 |
| UART 设备 | 接收回调+缓冲模型；与手写环形缓冲对照 | 代码分析 |
| I2C/SPI bus | 总线设备与"挂在总线上的从设备"两级模型 | 配置 |
| 自己写一个设备 | 把蜂鸣器封装成 rt_device 的全流程 | 代码分析 |

## 一、调用链全图：四层各司其职

调用链先收进一张图：应用喊名、对象调表、驱动执行。

![设备框架调用链：应用 rt_device_find、rt_device 调 ops 表、驱动落到硬件](/arch/device-ops.png)

一次 `rt_device_write` 从应用到寄存器，穿过四层：

```
应用层   rt_device_find("uart1") → rt_device_write(uart, 0, buf, n)
   ↓ 名字是契约
框架层   device.c：rt_device_write 查 ops->write，分发到底
   ↓ ops 表是契约
驱动层   BSP uart 驱动：ops->write 把字节塞进 USART_DR，等 TXE
   ↓ 寄存器是契约
寄存器层 USART1->DR / SR / BRR —— 硬件真相
```

每一层只认识**下一层的接口**，不关心再往下：应用不知道是 USART1 还是 UART5，框架不知道驱动写的是哪个寄存器，驱动知道寄存器但不关心应用在哪个任务里。**这就是解耦的物理实现：一张 ops 表 + 一个名字。**

把这张图和 Linux 字符设备并排看：`file->f_op` 就是 ops 表，`register_chrdev` 就是 register，`/dev/uart1` 就是 find 的名字：**RT-Thread 把 Linux 那套搬到了单片机上，只是尺度小了一档**。

## 二、rt_device 解剖：ops 表 + register/find

5.x 主线里 `struct rt_device` 继承 `rt_object`（[R0](00-arch.md) 的对象头），核心字段：

```c
struct rt_device
{
    struct rt_object parent;            /* 继承对象头：名字、类型、链表节点 */
    enum rt_device_class_type type;     /* 字符/块/网口/MTD/... */
    rt_uint16_t flag;                   /* 能力标志：可读/可写/可中断... */
    rt_uint16_t open_flag;               /* 当前打开标志 */
    rt_uint8_t  ref_count;               /* 打开计数 */
    rt_uint8_t  device_id;
    rt_err_t (*rx_indicate)(rt_device_t dev, rt_size_t size);  /* 收到数据回调 */
    rt_err_t (*tx_complete)(rt_device_t dev, void *buffer);    /* 发完回调 */
    const struct rt_device_ops *ops;    /* 操作表：解耦的载体 */
    void *user_data;
};
```

操作表（与 Linux `file_operations` 一一对应）：

```c
struct rt_device_ops
{
    rt_err_t  (*init)   (rt_device_t dev);
    rt_err_t  (*open)   (rt_device_t dev, rt_uint16_t oflag);
    rt_err_t  (*close)  (rt_device_t dev);
    rt_size_t (*read)   (rt_device_t dev, rt_off_t pos, void *buffer, rt_size_t size);
    rt_size_t (*write)  (rt_device_t dev, rt_off_t pos, const void *buffer, rt_size_t size);
    rt_err_t  (*control)(rt_device_t dev, int cmd, void *args);
};
```

三个动作看清生命周期：

- **register**（`rt_device_register(dev, "uart1", flag)`）：把设备按 type 挂进对象容器（[R0](00-arch.md) 的容器链表），名字写进 `parent.name`：**从此全局可见**。
- **find**（`rt_device_find("uart1")`）：在容器链表上线性比对名字，返回 `rt_device_t`：**名字是契约**，所以 BSP 与应用必须用同一套命名惯例（`uart1`/`i2c1`/`spi10`）。
- **open/read/write/control/close**：`rt_device_open` 让 `ref_count++` 并调 `ops->open`；`rt_device_read` 直接转发 `ops->read`，框架本身不搬数据，只分发。

**为什么 register/find 两分离而不是"创建即用"**：register 是驱动侧的事（板子启动时调一次），find 是应用侧的事（任意时刻按名取柄）。两分离意味着驱动可以晚于应用加载、应用可以不知道驱动在哪，这正是软件包"即插即用"的根基。

## 三、PIN 设备：编号体系与点灯对照

PIN 是设备框架之上的一层"便捷壳"：底层仍是一个 char 设备，但 `rt_pin_*` 这套 API 走的是 `struct rt_pin_ops`，比通用 `rt_device_read/write` 更贴近 GPIO 语义：

```c
struct rt_pin_ops
{
    void (*pin_mode) (rt_device_t dev, rt_base_t pin, rt_uint8_t mode);
    void (*pin_write)(rt_device_t dev, rt_base_t pin, rt_uint8_t value);
    int  (*pin_read) (rt_device_t dev, rt_base_t pin);
    rt_err_t (*pin_attach_irq)(rt_device_t dev, rt_int32_t pin, rt_uint8_t mode,
                               void (*hdr)(void *), void *args);
    rt_err_t (*pin_detach_irq)(rt_device_t dev, rt_int32_t pin);
    rt_err_t (*pin_irq_enable)(rt_device_t dev, rt_base_t pin, rt_uint8_t en);
    rt_base_t (*pin_get)(const char *name);
};
```

编号体系是关键：所有引脚被压平成一个 `rt_base_t`，公式 `pin = port * 16 + pin_in_port`，由 `GET_PIN` 宏在编译期算出：

```c
#define GET_PIN(PORTx, PIN)   (RT_PIN_##PORTx * 16 + RT_PIN_##PORTx##_##PIN)
/* 板级 board.h 里：RT_PIN_A=0, RT_PIN_B=1, ... */
/* GET_PIN('A', 5) = 0*16 + 5 = 5；GET_PIN('B', 0) = 1*16 + 0 = 16 */
```

`port*16` 而非 `port*32`：因为 STM32 一组最多 16 个脚（F407 是 PA0~PA15），4 bit 够存脚号，余下高位存组号：一个 32 位 int 装下全部引脚，便宜又够用。

点灯对照 [S3](../../stm32/03-gpio.md) 手写版：

```c
/* S3 寄存器版：你得知道 LED 在哪个 GPIO、哪一位、怎么配时钟 */
RCC->AHB1ENR |= RCC_AHB1ENR_GPIOBEN;
GPIOB->MODER |= GPIO_MODER_MODER5_0;
GPIOB->BSRR   = GPIO_BSRR_BR5;

/* R4 PIN 设备版：只知道一个编号 */
rt_pin_mode (GET_PIN('B', 5), PIN_MODE_OUTPUT);
rt_pin_write(GET_PIN('B', 5), PIN_LOW);
```

封装的甜是"不用查寄存器"；代价是多一次函数调用 + 一次 ops 分发，在 168MHz 的 F4 上是纳秒级，点灯完全无所谓；但在纳秒级脉冲生成（如 WS2812 时序）这种"每一拍都要抠"的场合，该走 RT 路径（`rt_pin_write` 的 fast 版或直接寄存器，常见坑第 4 条会再提）。

## 四、UART 设备：中断接收 + 回调 + 缓冲

UART 是设备框架的"招牌菜"：`serial.c` 把它注册成 char 设备，应用一套 `rt_device_*` 通吃。中断接收的标准管道：

```c
static rt_device_t serial;
static struct rt_ringbuffer ring;        /* 环形缓冲 */
static rt_sem_t rx_sem;

/* 1. 接收回调（中断上下文！）——只搬运，不干活 */
static rt_err_t rx_ind(rt_device_t dev, rt_size_t size)
{
    rt_uint8_t tmp[32];
    while (size) {
        rt_size_t n = rt_device_read(dev, 0, tmp, size > 32 ? 32 : size);
        rt_ringbuffer_put(&ring, tmp, n);
        size -= n;
    }
    rt_sem_release(rx_sem);              /* 通知消费者：有货了 */
    return RT_EOK;
}

/* 2. 消费者任务 */
void uart_task(void *p)
{
    rt_uint8_t buf[64];
    rt_device_set_rx_indicate(serial, rx_ind);
    rt_device_open(serial, RT_DEVICE_FLAG_INT_RX);   /* 中断接收模式 */
    while (1) {
        rt_sem_take(rx_sem, RT_WAITING_FOREVER);
        while (rt_ringbuffer_data_len(&ring) > 0)
            rt_ringbuffer_get(&ring, buf, sizeof(buf));  /* 取出来处理 */
    }
}
```

**为什么回调只搬运不干活**：`rx_indicate` 在接收中断里被调（serial.c 里 RXNE 中断 → `dev->rx_indicate`），上下文是 ISR，在中断里跑业务逻辑等于"在中断里干活"，长任务会把中断延迟顶爆。标准做法是 ISR 搬数据 + 释放信号量，业务在任务里做。

三方对照同一件事"串口收数据回显"：

| 方案 | ISR 做什么 | 通信机制 | 缓冲 |
|---|---|---|---|
| [S7](../../stm32/07-usart.md) 手写 | DMA 搬 + IDLE 判帧 | 无（主循环查 DMA 指针） | DMA 环形 |
| [F4](../freertos/04-queue.md) 队列 | xQueueSendFromISR | 队列（带阻塞） | 队列本身就是 |
| R4 UART 设备 | rx_indicate 释放 sem | 信号量 + 环形缓冲 | rt_ringbuffer |

三者本质同构：**ISR 只做有界搬运，业务在任务里**。R4 的不同是这套管道被框架标准化了：你不用每次手写中断 + 环形缓冲，驱动作者已经填好 ops 表，你只管 `set_rx_indicate` + 取数据。

## 五、I2C/SPI bus：总线设备 + 从设备两级

I2C/SPI 比 PIN/UART 多一层"总线"：**总线本身是一个设备，挂在总线上的从设备是另一类对象**。因为一条 I2C 总线上有多个从设备，共用同一对 SCL/SDA，必须由总线统一调度（谁占用、谁释放、谁的消息）。

两级模型：

```
应用     rt_i2c_transfer(bus, msgs, n)   /  rt_spi_transfer(spi_dev, ...)
   ↓
总线设备 rt_i2c_bus_device / rt_spi_bus
         - ops: master_xfer / acquire / release   ← 总线锁，防多任务抢总线
   ↓
从设备   rt_i2c_client / rt_spi_device
         - bus 指针 + 7-bit 地址(或 CS)           ← 数据带"我是谁"
```

应用调 `rt_i2c_transfer(bus, msg, n)`，传的是"总线 + 一组消息（带从设备地址）"，总线驱动负责起停条件、地址帧、ACK 收发：**应用不碰 SCL/SDA 寄存器**。`rt_i2c_bus_acquire/release` 是总线锁，多任务共用一条总线时由框架保证串行化。

这层抽象的价值：换一颗传感器（同总线、不同地址）只改一个从设备指针；换一块板（同芯片、不同引脚）只改总线驱动的寄存器部分，**应用层的 `rt_i2c_transfer` 一行不动**。

## 六、自己写一个设备：蜂鸣器封装

把一个无源蜂鸣器（PWM 驱动）封成 `rt_device` 的最小骨架，体验"驱动作者"视角：

```c
struct buzzer_dev
{
    struct rt_device parent;     /* 继承设备头 */
    rt_uint32_t channel;          /* 哪路 PWM */
    rt_uint32_t freq;             /* 当前频率 */
};

static rt_err_t buz_init(rt_device_t dev)                      { /* 配 PWM 通道 */ return RT_EOK; }
static rt_err_t buz_open(rt_device_t dev, rt_uint16_t oflag)   { return RT_EOK; }
static rt_err_t buz_control(rt_device_t dev, int cmd, void *args)
{
    struct buzzer_dev *b = (struct buzzer_dev *)dev;
    switch (cmd) {
    case BUZZER_CMD_SET_FREQ:  b->freq = *(rt_uint32_t *)args; /* 改 PWM 分频 */ break;
    case BUZZER_CMD_OFF:       /* 关 PWM 输出 */ break;
    }
    return RT_EOK;
}

static const struct rt_device_ops buz_ops = {
    buz_init, buz_open, RT_NULL, RT_NULL, RT_NULL, buz_control
};

void buzzer_register(void)
{
    static struct buzzer_dev buz = { .channel = 1 };
    buz.parent.type = RT_Device_Class_Miscellaneous;
    buz.parent.ops  = &buz_ops;
    rt_device_register(&buz.parent, "buzzer", RT_DEVICE_FLAG_RDWR);
}
INIT_DEVICE_EXPORT(buzzer_register);   /* 文件作用域：自动初始化，回 [R0](00-arch.md) */
```

应用侧：

```c
rt_device_t buz = rt_device_find("buzzer");
rt_device_open(buz, RT_DEVICE_FLAG_WRONLY);
rt_uint32_t f = 4000;  rt_device_control(buz, BUZZER_CMD_SET_FREQ, &f);
```

驱动写一次，全工程受益，这就是生态。**填表（ops）+ 喊名（find）+ 注册进容器**，三步闭环。

## 记忆锚点

::: tip 一句话记住
**驱动填表（ops），应用喊名（find），换板只换表，应用纹丝不动：解耦的代价是一张表，回报是整个生态。**
:::

**延伸**：RTT 设备框架调用链动画见 [R4 动画](/anim/rtt-device-chain.svg)；ESP-IDF 驱动模型对照见 [P6](../../esp32/06-spi-i2c-driver.md)；FreeRTOS 无设备框架的设计差异见 [F0](../freertos/00-why-rtos.md)。

## 实物实验

- PIN 设备点灯 vs [E01](../../lab/e01-blink.md) 寄存器版：同一块板两种世界观，GDB 里追一次 `rt_pin_write` 到 BSRR 的完整下钻，封装在你眼前逐层剥落。

## 常见坑

- **忘了 register 就 find**：设备不在容器里，find 返回空，先查驱动入口函数与 INIT_DEVICE_EXPORT。
- **把设备名当字符串随便起**：命名是 BSP 与应用的契约（"uart1"/"i2c1" 惯例），乱起名上层软件包找不到。
- **UART 回调里干重活**：回调在中断/线程上下文因配置而异，查清 RX indicate 的调用上下文再写代码。
- **绕过框架直接摸寄存器**：绕过框架=破坏解耦契约，除非性能论证（RT 路径），否则别拆自己家地基。
- **open 时 oflag 与设备能力不符**：只读传感器用 `RT_DEVICE_FLAG_WRONLY` 打开，规范的 `ops->open` 应拒绝；但有些驱动不查 oflag，写到只读设备返回的是驱动作者的良心，读 spec 确认能力标志，别靠"能 open 就能写"的错觉。

## 短自测

1. 为什么"register 和 find 两分离"是解耦的关键？如果合并成"创建即可用"会丢失什么？
<details><summary>参考答案</summary>register 是驱动侧（板级启动调一次），find 是应用侧（任意时刻按名取柄）。合并意味着应用必须在驱动创建时就在场、且要知道设备指针，驱动晚加载或软件包热插拔就废了。两分离让"名字"成为契约，驱动和应用解耦到只剩一个字符串，软件包才能即插即用。</details>

2. GET_PIN('C', 12) 的编号是多少？为什么用 port*16+pin 而不是直接传 (port, pin) 两个参数？
<details><summary>参考答案</summary>port C 是第 3 组（A=0,B=1,C=2），C12 = 2*16 + 12 = 44。压平成一个整数是因为 rt_pin_mode 等接口形参是 rt_base_t 单值：一个 32 位 int 装下全部引脚（16 组 × 16 脚 = 256，8 bit 够），调用约定简单、可作数组下标、可存表，比二元组好调度。</details>

3. UART 的 rx_indicate 回调为什么不能直接在里面处理完所有业务？标准做法是什么？
<details><summary>参考答案</summary>rx_indicate 在接收中断里被调，上下文是 ISR。在里面干长活会顶爆中断延迟、可能喂不上 watchdog、错过下一帧。标准做法：ISR 里只把字节搬进环形缓冲、释放一个信号量；业务逻辑在消费者任务里 sem_take 醒来后处理：ISR 只做有界搬运，业务在任务里。</details>

4. rt_device_ops 和 Linux 的 file_operations 有哪些对应关系？为什么说"一脉相承"？
<details><summary>参考答案</summary>对应：init/open/read/write/close/control 一一映射 file_operations 的 init/open/read/write/release/ioctl；register 对应 register_chrdev；find 按名取柄对应 open(/dev/xxx) 拿到 file 的 f_op。一脉相承指"对象持一张 ops 表 + 按名分发"的同一套解耦哲学，RT-Thread 只是把 Linux 那套搬到单片机，尺度小一档。</details>

5. PIN 设备为什么不用 rt_device_read/write 而单独一套 rt_pin_* API？这套 API 走的还是 rt_device 吗？
<details><summary>参考答案</summary>PIN 语义是"引脚模式/电平/中断"，用 read/write 这种"流"语义不顺手，所以单独一套 pin_mode/pin_write/pin_attach_irq。但它底层仍是一个 char 设备：rt_pin_* 内部 find 出 pin 设备、调它挂的 rt_pin_ops，是设备框架之上的便捷壳，不是另起炉灶。</details>

## 对照表：本章概念 → 源码落点

| 概念 | 落点（RT-Thread 5.x） |
|---|---|
| rt_device 结构 + ops 表 | `include/rtdef.h`（struct rt_device / rt_device_ops） |
| register/find/open/read 分发 | `src/device.c`（rt_device_register/find/open/read） |
| PIN 设备 + GET_PIN | `components/drivers/misc/pin.c` + BSP `board.h` |
| UART 设备 + rx_indicate | `components/drivers/serial/serial.c` |
| I2C/SPI 总线两级模型 | `components/drivers/i2c/i2c_core.c` / `spi/spi_core.c` |
| list_device 命令 | `components/finsh/msh_cmd.c` |

## 你做到了

- 驱动模型从"Linux 那套很高级"变成"我也写得出的 ops 表"；
- RT-Thread 的生态逻辑打通：软件包为什么能即插即用，答案就在这层框架。

翻译官是 ops 表：应用那行调用跳进表里，落到谁家的函数就是谁的动作。换块板子，动的只是表后面那层实现，应用一行不改。

<div class="achievement">
✅ 下一站：<a href="05-finsh.html">R5 finsh 控制台</a>，在板子上跑 shell：list、ps、help 的背后。
</div>
