---
title: "设备框架、shell 与配置系统"
platforms: [f407]
---

# 设备框架、shell 与配置系统

FreeRTOS 把内核之外的一切留给你；RT-Thread 在内核之上叠了三层公共设施：设备框架管「应用怎么碰硬件」，finsh shell 管「人怎么碰固件」，Kconfig 加 scons 管「固件怎么长出来」。这三层是 RT-Thread 与裸内核 RTOS 拉开差距的地方，也是它移植成本比 FreeRTOS 高的地方——三层各有自己的配置宏、初始化级别与内存账。本章把三层拆开：对象模型、分发路径、真实宏名、真实默认值，每条都按 v5.3.0 源码核对。

证据先说清：本章没有一条实测读数。六份源材料零板级日志；「168 MHz 上纳秒级的调用开销」「整套 msh 约 10–20 KB Flash」是来源说法（未复核），本章不写成测量值。仓库里的 RT-Thread 实验工程 `mcu/code/rtos/02-rt-thread-lab` 是 Nano 式裁剪（`rtconfig.h` 只要内核，没有 `RT_USING_DEVICE` 与 `RT_USING_FINSH`），设备与 shell 的实验必须切到标准 BSP 或显式打开组件，不能拿该 lab 固件冒充「已跑通」。

> 版本口径：RT-Thread 按 **v5.3.0** 对账（`include/rtdef.h`、`components/drivers/`、`components/finsh/`、`src/`）；默认 F407 BSP 指 `bsp/stm32/stm32f407-atk-explorer`。旧材料里的 `bsp/stm32f407-zeo` 在 v5.3.0 不存在，本章所有 BSP 路径按真实目录写。

## 本章罗盘

- **问题**：`struct rt_device` 的 ops 表是无条件成员吗，`RT_USING_DEVICE_OPS` 开与关差在哪？`rt_device_read` 的返回类型是 `rt_size_t` 还是 `rt_ssize_t`，为什么这事重要？`rt_device_register` 把设备挂进哪个容器，`rt_device_find` 怎么找，`open` 的 init/open/`ref_count++` 顺序是什么？`GET_PIN(A,5)` 的宏参数是记号还是字符，`GET_PIN('A',5)` 能不能编译，`port×16` 在所有 STM32 上成立吗？UART 的中断接收是 v1 还是 v2 管道，`rx_indicate` 回调里 `while(size)` 为什么会死循环？I2C 总线锁是 ops 的 acquire/release 还是 `rt_mutex`？在默认 F407 BSP 上写自定义设备，`parent.ops` 能不能编译？`MSH_CMD_EXPORT` 展开成什么结构，命令查找是线性还是二分，`list_thread` 的真实原型是什么？finsh 的栈、优先级、参数与命令行长度默认值各是多少，5.3.0 有没有 `FINSH_USING_MSH_ONLY`？menuconfig 与 scons 谁写 `.config` 谁生成 `rtconfig.h`，`RT_USING_I2C` 是带 1 的宏还是无值宏？
- **交付**：能画出 `rt_device` 的字段分区，说出 ops 表的两套接口形态与各自的编译条件；能走读 `rt_device_open` 的 init→open→`ref_count++` 顺序，解释 `rt_ssize_t` 负值错误码的用途；能写出编译期压平引脚号的公式与三个变体（普通 GPIO、MP1、GPIOZ）；能按 v1/v2/DMA 三种模式分别说清 UART 接收管道与回调的正确写法（`n==0` 退出）；能写出在默认 BSP 下可编译的自定义设备（条件编译与内联函数指针两种）；能用真实的 `finsh_syscall` 结构与 `__fsym_` 前缀讲 FSymTab 机制，纠正「少时线性、多时二分」与 `list_thread(int,char**)` 的错误；能背出 finsh 四个默认值并说清裁剪总开关是 `RT_USING_MSH`；能画出 Kconfig→`.config`→`rtconfig.h` 的两段分工，指出 `depend` 是 Kconfig 与 scons 的接合点。
- **边界**：单平台 F407；RT-Thread 结论按 v5.3.0，旧章的 `msh_cmd_entry`、`FINSH_USING_MSH_ONLY`、`msh_cmd.c`、两参 `list_thread` 均不采用。FreeRTOS 侧不展开内核机制（[第 22 章](./22-tasks-tcb-scheduler.md)、[第 23 章](./23-context-switch-porting.md) 已讲），只对照「为什么没有设备框架」。设备驱动内部的 UART DMA 细节、I2C 时序寄存器归外设章（[v1 第 16 章](../v1-drivers/16-i2c-spi.md)、[v1 第 13 章](../v1-drivers/13-uart-framed-protocol.md)），本章只讲框架层。实验设计与判据可写，「已经量到」不可写——本章零实测。
- **依据锚点**：R4《设备框架》（`mcu/docs/rtos/rtthread/04-device.md`）、R5《finsh 控制台》（`.../05-finsh.md`）、R6《Env 与 menuconfig》（`.../06-env-menuconfig.md`）。lab 实况见 `mcu/code/rtos/02-rt-thread-lab/rtconfig.h:2-5`。上游对账：RT-Thread v5.3.0 的 [rtdef.h](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/include/rtdef.h)、[device.c](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/components/drivers/core/device.c)、[drv_gpio.h](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/bsp/stm32/libraries/HAL_Drivers/drivers/drv_gpio.h)、[dev_i2c.h](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/components/drivers/include/drivers/dev_i2c.h)、[finsh.h](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/components/finsh/finsh.h)、[msh.c](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/components/finsh/msh.c)、[cmd.c](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/components/finsh/cmd.c)、[finsh Kconfig](https://github.com/RT-Thread/rt-thread/blob/v5.3.0/components/finsh/Kconfig)。线程与优先级语义见 [第 22 章](./22-tasks-tcb-scheduler.md)；ISR 到任务的边界见 [第 23 章](./23-context-switch-porting.md)；ring+sem 管道的手写版见 [第 24 章](./24-queue-semaphore-notification.md)；NVIC 配置见 [v1 第 10 章](../v1-drivers/10-interrupts-nvic-exti.md)。

## 先做出来

标准 BSP 上两件小事，都是实验设计（未实测，判据写明）：

### 1. 开机就能敲的 shell

在 `bsp/stm32/stm32f407-atk-explorer` 的 Env 控制台里确认 `RT_USING_FINSH` 与 `RT_USING_MSH` 都开着（默认开），编译烧录，串口终端回车应出现 `msh />`。判据：敲 `help` 列出命令清单；敲 `list_device` 看到已注册设备；若 `help` 为空或 `command not found`，先查链接脚本有没有 `KEEP(*(FSymTab))`，再查 finsh 线程栈有没有给够。这套现象是「命令在不在」的自检路径，不是本文的实测记录。

### 2. 引脚号压平算一遍

`GET_PIN(C,12)` 的值：C 是第 3 组（A=0），12 是组内脚号，得 2×16+12=44。展开宏你会发现它不是按「组号×16」写的，而是按 GPIO 基地址差算的——两者在普通 GPIO 上等价，为什么写法要绕这一道，见 PIN 一节。

## 设备框架：对象、ops 表与名字契约

### rt_device 的对象模型

`struct rt_device` 继承 `rt_object`：名字、类型、链表节点都在对象头里。关键分歧在 ops 表怎么挂——v5.3.0 有**两套接口形态**，由 `RT_USING_DEVICE_OPS` 决定（`rtdef.h:1408-1424`）：

```c
#ifdef RT_USING_DEVICE_OPS
    const struct rt_device_ops *ops;      /* 开：一张共享的 ops 表 */
#else
    /* 关：函数指针内联进结构体 */
    rt_err_t (*init)   (rt_device_t dev);
    rt_err_t (*open)   (rt_device_t dev, rt_uint16_t oflag);
    rt_err_t (*close)  (rt_device_t dev);
    rt_ssize_t (*read) (rt_device_t dev, rt_off_t pos, void *buffer, rt_size_t size);
    rt_ssize_t (*write)(rt_device_t dev, rt_off_t pos, const void *buffer, rt_size_t size);
    rt_err_t (*control)(rt_device_t dev, int cmd, void *args);
#endif
```

开了宏，多个设备共享一张 ops 表，省 RAM；关了宏，每个设备实例自带一份函数指针，调用少一次解引用。默认 F407 BSP（atk-explorer）的 `rtconfig.h` **没有** `RT_USING_DEVICE_OPS`——旧材料把 ops 画成无条件成员，在默认 BSP 上照抄 `dev->ops->write = ...` 编译不过。画结构图先看这个宏开没开。

注意 read/write 的返回类型：**`rt_ssize_t`**（`rtdef.h:1332-1344`），带符号。正数是字节数，负数是错误码——「读了 -1 个字节」不是 bug，是驱动的返回。旧材料写 `rt_size_t`（无符号）丢掉了这条错误通道。

### register、find、open 的生命周期

![设备框架调用链动画：应用按名找设备，框架分发到 ops 或内联函数指针，驱动落到寄存器](/anim/rtt-device-chain.svg)

![设备框架调用链：应用 rt_device_find、rt_device 分发、驱动落到硬件](/arch/device-ops.png)

三个动作各归其位（`components/drivers/core/device.c`）：

- **register**（`device.c:67-93`）：`rt_device_register(dev, "uart1", flag)` 把设备挂进 **`RT_Object_Class_Device` 一个容器**——不是每种设备类一个容器。设备类枚举（Char/Block/NetIf/MTD/Pin/ADC/DAC/Bus/…，`rtdef.h:1255-1290`）只是分类标签，查找不按它。
- **find**（`device.c:122-126`）：在该容器链表上**线性比对名字**，命中返回 `rt_device_t`。名字是 BSP 与应用的契约，`uart1`/`i2c1` 这类惯例名别乱改。设备就几十个，线性足够。
- **open**（`device.c:222-283`）：顺序是 `ops->init`（若未初始化）→ `ops->open`，**两者都成功才 `ref_count++`**。旧材料「open 让 `ref_count++` 并调 `ops->open`」把顺序说反了——顺序错，打开失败的设备也会留下一个假引用计数，close 的对称逻辑就乱了。

`rt_device_read/write/control` 是纯分发：框架不搬数据、不做缓冲，检查 open 状态后直接转发给驱动。缓冲、DMA、阻塞语义全在驱动里，且**各驱动不一致**——`read` 的阻塞行为不能跨设备统一假设。

## PIN：编号压平与真实宏

PIN 设备把全部引脚压平成一个 `rt_base_t` 编号。真实宏在 BSP 驱动层（`bsp/stm32/libraries/HAL_Drivers/drivers/drv_gpio.h:80-82`）：

```c
#define GET_PIN(PORTx, PIN)                                    \
    (rt_base_t)(16 * ( ((rt_base_t)(GPIO##PORTx##_BASE)        \
                        - (rt_base_t)(GPIOA_BASE)) / 0x400 ) + PIN)
```

三个要点：

- **宏参数是记号**：`GET_PIN(A,5)` 正确，`GET_PIN('A',5)` 编译不过——`'A'` 是字符字面量，拼不进 `GPIOA_BASE`。旧材料写成 `GET_PIN('A',5)`，照抄必炸。
- **公式按基地址差**：`(GPIOC_BASE − GPIOA_BASE) / 0x400` 得组号，乘 16 加组内脚号。普通 STM32 上 GPIO 组基地址间隔 0x400，所以**等价于** `port×16 + pin`；这不是巧合，是寄存器布局的推论。`GET_PIN(C,12)` = 2×16+12 = 44。
- **有变体**：MP1 系列组间距是 `0x1000`；某些封装有 GPIOZ，特判为 `176 + PIN`。`port×16` 是普通 GPIO 的规律，不是全家族通则。

`rt_pin_mode/write/read` 之外还有 `rt_pin_attach_irq`：把引脚中断回调挂到框架，底层仍是 EXTI+NVIC（[v1 第 10 章](../v1-drivers/10-interrupts-nvic-exti.md)），框架只是把「引脚号 → EXTI 线」的映射收进驱动。

## UART：三种接收模式与回调的正确写法

串口在框架里注册成 char 设备，接收管道按模式分三种（v5.3.0 默认走 **V1**，`components/drivers/serial/Kconfig:5-14`）：

| 模式 | 打开标志 | 管道 | 回调上下文 |
| --- | --- | --- | --- |
| V1 中断接收 | `RT_DEVICE_FLAG_INT_RX`（0x100） | ISR 搬字节进驱动 ring → `rx_indicate` 通知 | ISR |
| V1 DMA 接收 | `RT_DEVICE_FLAG_DMA_RX`（0x200） | DMA 填环形缓冲 → 回调 | ISR（或下半部，随驱动） |
| V2 非阻塞 | `RT_DEVICE_FLAG_RX_NON_BLOCKING`（0x2000） | 仅 V2 serial 定义，V1 没有这个宏 | 线程 |

`RT_DEVICE_FLAG_RX_NON_BLOCKING` 只在 `dev_serial_v2.h:172-175` 定义；默认 F407 BSP 用 V1，代码里用 0x2000 编译不过。

**回调的正确写法**。`rx_indicate` 在 ISR 里被调（V1 中断接收），标准管道是「ISR 搬运、任务干活」：

```c
static rt_err_t rx_ind(rt_device_t dev, rt_size_t size)
{
    rt_sem_release(rx_sem);      /* 只发信号量，不搬数据 */
    return RT_EOK;
}

void uart_task(void *p)
{
    rt_uint8_t buf[64]; rt_size_t n;
    rt_device_set_rx_indicate(serial, rx_ind);
    rt_device_open(serial, RT_DEVICE_FLAG_INT_RX);
    while (1) {
        rt_sem_take(rx_sem, RT_WAITING_FOREVER);
        while ((n = rt_device_read(serial, 0, buf, sizeof(buf))) > 0) {
            handle(buf, n);      /* 业务在任务里 */
        }
    }
}
```

旧材料给的反例值得记取：回调里 `while (size)` 循环调 `rt_device_read`，若某轮 `read` 返回 0，`size` 不减，**ISR 里死循环**。两个修法：循环条件对 `n==0` 退出（如上面任务侧写法），或者干脆回调只释放信号量、数据留给任务读。推荐后者——ISR 里调 `rt_device_read` 的锁与上下文语义随版本变化，能不进就不进。

与手写管道对照（[第 24 章](./24-queue-semaphore-notification.md) 的 ring+sem）：结构同构——ISR 有界搬运、信号量唤醒、任务处理。框架化的差别只是这条管道被驱动作者预填好了，应用只剩 `set_rx_indicate` 与取数据。

## I2C/SPI：总线设备与从设备两级

一条 I2C 总线挂多个从设备，共享同一对 SCL/SDA，于是多一层「总线」对象：

- **总线设备** `rt_i2c_bus_device`：持有 `struct rt_mutex lock` 作为总线锁（`dev_i2c.h:257-268`），API 是 `rt_i2c_bus_lock/unlock`（`:416-423`）；ops 是 `master_xfer`/`slave_xfer`/`i2c_bus_control`（`:226-237`）。
- **从设备** `rt_i2c_client`：只带总线指针与 7 位地址——数据自带「我是谁」。

应用调 `rt_i2c_transfer(bus_dev, msgs, num)`：消息数组里每条带从设备地址、读写方向、缓冲与长度；总线驱动负责起始/停止条件、地址帧与 ACK，总线锁保证多任务串行。旧材料把总线锁写成 ops 的 `acquire/release`——那是别的 RTOS 的形态；RT-Thread 5.x 的锁是总线对象里的 `rt_mutex`，不是 ops 表项。SPI 同构：`rt_spi_bus` + `rt_spi_device`（CS 归从设备），`rt_spi_transfer` 语义一致。

价值在换型成本：换同总线不同地址的传感器，只改从设备对象的地址；换板子，只改总线驱动的寄存器层；应用层的 `rt_i2c_transfer` 一行不动。

## 自己写一个设备：默认 BSP 下必须能编译

把蜂鸣器封成设备，骨架三步：继承 `rt_device`、填行为、注册。**默认 F407 BSP 没开 `RT_USING_DEVICE_OPS`**，`parent.ops` 与 `struct rt_device_ops` 都不存在——示例必须按关宏形态写：

```c
struct buzzer_dev
{
    struct rt_device parent;      /* 对象头：名字/类型/链表节点 */
    rt_uint32_t channel;          /* PWM 通道 */
};

static rt_err_t buz_init(rt_device_t dev)    { return RT_EOK; }  /* 配 PWM */
static rt_err_t buz_open (rt_device_t dev, rt_uint16_t oflag) { return RT_EOK; }
static rt_err_t buz_close(rt_device_t dev)   { return RT_EOK; }
static rt_err_t buz_ctrl (rt_device_t dev, int cmd, void *args)
{
    struct buzzer_dev *b = (struct buzzer_dev *)dev;
    if (cmd == BUZZER_SET_FREQ) { /* 按 args 改分频 */ }
    return RT_EOK;
}

void buzzer_register(void)
{
    static struct buzzer_dev buz;
    buz.parent.type        = RT_Device_Class_Miscellaneous;
    buz.parent.init        = buz_init;       /* 关宏形态：内联函数指针 */
    buz.parent.open        = buz_open;
    buz.parent.close       = buz_close;
    buz.parent.control     = buz_ctrl;
    rt_device_register(&buz.parent, "buzzer", RT_DEVICE_FLAG_RDWR);
}
INIT_DEVICE_EXPORT(buzzer_register);   /* 开机自动注册 */
```

要在开了 `RT_USING_DEVICE_OPS` 的工程里用同一份代码，就得条件编译：

```c
#ifdef RT_USING_DEVICE_OPS
static const struct rt_device_ops buz_ops = {
    buz_init, buz_open, buz_close, RT_NULL, RT_NULL, buz_ctrl };
#endif
/* 注册处：#ifdef 里 buz.parent.ops = &buz_ops; #else 逐个内联赋值 */
```

三个纪律：注册名全局唯一（find 按名线性比对，重名先到先得）；设备类枚举只作分类标签，选 `RT_Device_Class_Miscellaneous` 表达「杂项」即可；`INIT_DEVICE_EXPORT` 让注册在开机自动执行，应用侧 `rt_device_find("buzzer")` 直接取柄。

![手绘板：v5.3.0 设备框架生命周期边界——find/open/失败路径本章代码可覆盖，串口 DMA、接收回调、缓冲模式要回对应 BSP 驱动核对，每启用一个组件都增加 Flash/RAM 与初始化依赖](/images/ch28-rtthread-lifecycle.png)

这张手绘板把生命周期章节的边界画出来：本章讲的 register/find/open 是框架层契约；各驱动 read 的阻塞与超时语义、DMA 细节、缓冲模式，要到对应 BSP 驱动里核对，不能统一假设。

## finsh/MSH：把函数名编进链接段

### FSymTab 与真实的结构

`MSH_CMD_EXPORT(name, desc)` 是**可变参数宏**（`finsh.h:153-155`），展开把一条 `struct finsh_syscall`（`finsh.h:182-194`）放进 `FSymTab` 链接段（宏生成符号 `__fsym_##name`，`finsh.h:82`）：

```c
struct finsh_syscall
{
    const char *name;               /* 命令名：查找的 key */
    const char *desc;               /* 描述：help 显示 */
#ifdef FINSH_USING_OPTION_COMPLETION
    syscall_option_t *opt;          /* 可选：参数补全 */
#endif
    syscall_func_t func;            /* 函数指针 */
};
```

32 位平台上带 option 补全是 16 B/条，关掉是 12 B；名字与描述字符串另存 rodata。「每条 16–24 B」「整套 msh 10–20 KB Flash」是来源说法，没有版本与裁剪条件，别当预算用——要账自己在 map 文件里量 FSymTab 段与 finsh 相关节。

链接脚本用 `KEEP` 钉住段：

```text
. = ALIGN(4);
__fsymtab_start = .;
KEEP(*(FSymTab))
__fsymtab_end = .;
```

`KEEP` 不可省：命令函数没有被任何代码直接调用（只靠按名查找），`--gc-sections` 会把整个段当垃圾回收——编译通过、烧进去 `help` 空空如也，就是它。

### 查找、调用与真实原型

命令执行走 `msh_get_cmd`（`msh.c:232-248`）：**线性遍历** FSymTab 区间比对名字，命中后以 `func(argc, argv)` 调用（`msh.c:325-352`）。旧材料「命令少时线性、多时二分」没有对应实现——5.3.0 就是线性，命令规模几十条，线性足够。

切词只按空白分段（`msh_split`），**argv 全是字符串**；数字转整型是命令自己的事（`atoi`/`strtol`），解析器不做类型转换。「finsh 自动把参数转 int」与「命令里自己 atoi」在旧章里前后矛盾，真相是后者。

`list_thread` 的真实原型是 `long list_thread(void)`（`cmd.c:215`），不是 `int list_thread(int, char**)`——它没有参数，按 msh 命令导出时宏替它适配。`list_device` 在 `cmd.c:927`，`list` 别名在 `:1188`。旧章的 `msh_cmd.c` 文件在 5.3.0 不存在，落点在 `components/finsh/cmd.c` 与 `msh.c`。

### 自定义命令

```c
static rt_base_t leds[] = { GET_PIN(B,0), GET_PIN(B,1), GET_PIN(B,5) };

static int led(int argc, char **argv)
{
    if (argc < 3) { rt_kprintf("usage: led <0..2> <on|off>\n"); return -1; }
    int idx = atoi(argv[1]);                    /* 数字自己转 */
    if (idx < 0 || idx > 2) { rt_kprintf("index out of range\n"); return -2; }
    rt_pin_write(leds[idx], strcmp(argv[2], "on") == 0 ? PIN_HIGH : PIN_LOW);
    return 0;
}
MSH_CMD_EXPORT(led, control onboard RGB leds);
```

`argc` 含命令名本身（`led` 是 `argv[0]`，`led 1 on` 的 argc=3）。命令名别撞内核自带的 `help`/`list`/`ps`。

### 默认值与裁剪开关

finsh 的真实默认值（`components/finsh/Kconfig`）：

| 项 | 默认值 | 落点 |
| --- | --- | --- |
| `FINSH_THREAD_STACK_SIZE` | 4096 | Kconfig:27-29 |
| `FINSH_THREAD_PRIORITY` | 20（32 级制） | Kconfig:21-25 |
| `FINSH_ARG_MAX` | 10（参数个数上限） | Kconfig:57-59 |
| `FINSH_CMD_SIZE` | 80（命令行长度） | Kconfig:91-93 |
| history | 5 行 | Kconfig:35-39 |

裁剪规则：5.3.0 **没有** `FINSH_USING_MSH_ONLY` 这个符号；总开关是 `RT_USING_MSH`（其下 `FINSH_USING_MSH` 默认 y）。关 finsh 关的是 `RT_USING_MSH`，不是 `RT_DEBUG`——后者是调试断言级别，与 shell 无关。要不要保留：量产固件串口若对外，shell 是攻击面（改优先级、翻内存都做得到），工程版保留、量产版按产品安全边界裁。

finsh 线程是独立线程，栈单独预算（表里 4096 默认）：list 系列带格式化打印，栈消耗波动大。它默认优先级 20 在 32 级制里偏低——有意为之，敲命令不该抢业务任务的实时性（优先级方向见 [第 22 章](./22-tasks-tcb-scheduler.md)：数值越小越高）。

![finsh 命令分发动画：编译期宏把命令钉进 FSymTab 段，链接期 KEEP 圈地，运行期切词、查表、调用](/anim/rtt-finsh-dispatch.svg)

## 配置与构建：Kconfig、scons 与 BSP

### 两条命令的分工

![menuconfig 点单流水线动画：Kconfig 菜单定义经 menuconfig 写出 .config，scons 再生成 rtconfig.h，C 代码按宏走分支](/anim/menuconfig-flow.svg)

链路是**两段**，两段的主人不同：

1. `menuconfig` 收集所有 Kconfig 文件拼出菜单树，**把选择写进 `.config`**；
2. `scons`（构建系统）读 `.config`，**生成 `rtconfig.h`**——C 代码 `#include` 的是它。

旧材料里「menuconfig 生成 `.config`→`rtconfig.h`」把两段并成一段，与同章后文自相矛盾。记忆法：菜单管「编什么」的选择结果，构建管「把结果翻译成宏」。`rtconfig.h` 是生成物，手改必被下次 menuconfig 冲掉；要改默认值改 Kconfig 的 `default` 或直接改 `.config`。

### depend：Kconfig 与 scons 的接合点

每个组件目录的 SConscript 声明「哪些宏开了才编我」：

```python
src = Glob('*.c')
group = DefineGroup('Drivers', src, depend=['RT_USING_DEVICE'], CPPPATH=[cwd])
```

`depend=['RT_USING_DEVICE']` 就是 Kconfig 与 scons 的接合点：Kconfig 决定宏开不开，SConscript 决定宏开了才进构建。灰着选不上的菜单项是 `depends on` 的父依赖没开；勾选后自动带开的依赖是 `select`。

一个容易记错的细节：Kconfig bool 生成的是**无值宏**——`rtconfig.h` 里是 `#define RT_USING_I2C`，不是 `#define RT_USING_I2C 1`。判存在用 `#ifdef`，判数值才有意义。

工具链路径由 BSP 的 `rtconfig.py` 提供（`EXEC_PATH`/`PREFIX`）。旧材料里 `Environment(tools=['gccarm'], ARM_GCC_PATH=...)` 的写法不是 5.x 的标准 SConstruct 形态，按你手上的 BSP 复核后再改。

### BSP 三区与真实路径

标准 BSP 目录（以真实存在的为例：`bsp/stm32/stm32f407-atk-explorer`、`stm32f407-st-discovery`）：

```text
bsp/stm32/stm32f407-atk-explorer/
├── board/            # 板级：时钟/堆/初始化、链接脚本
├── libraries/        # HAL_Drivers：把 STM32 HAL 包装成 rt_device
├── applications/     # 业务代码：main.c 在这里
├── Kconfig           # 本 BSP 的菜单项
├── rtconfig.py       # 工具链路径与前缀
└── rtconfig.h        # 裁剪配置（生成物）
```

三区纪律：板级知识（时钟、堆、引脚、链接脚本）进 `board/`；HAL 包装进 `libraries/`；应用只进 `applications/`。在 `applications/` 里改驱动，换 BSP 时改动全丢——板级与应用解耦靠设备框架做接合层，这是 RT-Thread 工程化的核心纪律。

`pkgs --update` 按 `.config` 拉选中的软件包源码进 `packages/`，版本可在 menuconfig 里钉死（生产固件建议钉版本防上游漂移）。

## lab 实况：这份固件没有设备框架

`mcu/code/rtos/02-rt-thread-lab/rtconfig.h:2-5` 明确只要内核：无 `RT_USING_DEVICE`、无 `RT_USING_FINSH`、无 DFS 与软件包。它验证的是调度与 IPC（[第 22–24 章](./22-tasks-tcb-scheduler.md)），验证不了设备框架与 shell。要在板上跑本章的东西，两条路：

1. 直接用标准 BSP（atk-explorer 等），设备框架、finsh、Kconfig 全默认开；
2. 在现有工程显式打开 `RT_USING_DEVICE` 与 `RT_USING_MSH` 并接上对应驱动文件——等于把框架层补进来。

两条路的判据都写在「先做出来」：`msh />` 出现、`list_device` 有货。没做到之前，本章代码只处于「可编译、未实测」状态。

## 短自测

1. ops 表是无条件成员吗？开与关 `RT_USING_DEVICE_OPS` 各是什么形态？
<details><summary>参考答案</summary>不是。开：`const struct rt_device_ops *ops` 一张共享表，省 RAM、多一次解引用；关：函数指针内联进 `struct rt_device`（`rtdef.h:1408-1424`），每实例一份、少一次间接。默认 F407 BSP 没开，`dev->ops->xxx` 在默认配置下编译不过。</details>

2. `rt_device_read` 返回什么类型？为什么不能用无符号？
<details><summary>参考答案</summary>`rt_ssize_t`（`rtdef.h:1332-1344`）。负值表达错误码——「读取失败」需要一条与「读了 0 字节」「读了 n 字节」并列的返回通道，无符号类型给不了。</details>

3. register 挂进哪个容器？find 怎么找？open 的顺序是什么？
<details><summary>参考答案</summary>`RT_Object_Class_Device` 一个容器，设备类枚举只是分类标签；find 在该容器线性比对名字（`device.c:122-126`）；open 是 init（若未初始化）→ open → 成功才 `ref_count++`（`device.c:222-283`）。顺序反了会让打开失败的设备留下假引用计数。</details>

4. `GET_PIN(C,12)` 等于多少？宏参数能不能带引号？
<details><summary>参考答案</summary>44：C 组号 2（按基地址差 (GPIOC_BASE−GPIOA_BASE)/0x400），2×16+12。不能带引号——宏按记号拼接 `GPIOC_BASE`，`GET_PIN('C',12)` 是字符字面量，编译不过。`port×16` 只对普通 STM32 GPIO 成立，MP1 组间距 0x1000、GPIOZ 特判 176+pin。</details>

5. UART 接收的默认模式是哪个？回调里 `while(size)` 为什么会死循环？
<details><summary>参考答案</summary>默认 V1 中断接收（`serial/Kconfig:5-14`，标志 0x100）。回调若写 `while (size) { n = rt_device_read(...); ring_put(...); size -= n; }`，当 `read` 返回 0 时 size 不减、循环退不出去，而回调在 ISR 里——整个中断被卡死。修法：判 `n==0` 退出，或回调只释放信号量、数据留给任务读。</details>

6. `RT_DEVICE_FLAG_RX_NON_BLOCKING` 在默认 BSP 上能用吗？
<details><summary>参考答案</summary>不能。它只在 V2 serial（`dev_serial_v2.h:172-175`）定义，值 0x2000；默认 F407 BSP 用 V1，宏不存在，编译报错。</details>

7. I2C 总线锁在哪？ops 里有没有 acquire/release？
<details><summary>参考答案</summary>锁是总线对象里的 `struct rt_mutex lock`，API 是 `rt_i2c_bus_lock/unlock`（`dev_i2c.h:257-268,416-423`）；ops 只有 `master_xfer`/`slave_xfer`/`i2c_bus_control`（`:226-237`）。把锁写成 ops 表项是别的框架的形态。</details>

8. 在默认 F407 BSP 上注册自定义设备，示例代码要满足什么条件？
<details><summary>参考答案</summary>按关宏形态写：不碰 `parent.ops` 与 `struct rt_device_ops`，直接给 `parent.init/open/close/read/write/control` 赋内联函数指针；要兼容开宏的工程就条件编译。注册名唯一、类型选 `RT_Device_Class_Miscellaneous`、用 `INIT_DEVICE_EXPORT` 自动注册。</details>

9. `MSH_CMD_EXPORT` 展开成什么？为什么链接脚本必须 KEEP？
<details><summary>参考答案</summary>可变参数宏（`finsh.h:153-155`），生成 `__fsym_##name` 符号并把一条 `struct finsh_syscall`（name/desc/opt?/func）放进 FSymTab 段（`finsh.h:82,182-194`）。命令函数没有直接调用点，`--gc-sections` 会把整段当垃圾回收，`KEEP(*(FSymTab))` 钉住段——少了它就是「编译通过、help 为空」。</details>

10. 命令查找是线性还是二分？`list_thread` 的真实原型是什么？
<details><summary>参考答案</summary>线性遍历（`msh_get_cmd`，`msh.c:232-248`）——「少时线性、多时二分」没有对应实现。`list_thread` 是 `long list_thread(void)`（`cmd.c:215`），无参数；`list_device` 在 `cmd.c:927`，`list` 别名在 `:1188`。</details>

11. 解析器会把参数自动转 int 吗？
<details><summary>参考答案</summary>不会。`msh_split` 只按空白切词，argv 全是字符串；数字转整型是命令自己的事（`atoi`/`strtol`）。解析器做隐式类型转换的说法没有对应实现。</details>

12. finsh 的栈、优先级、参数上限、命令行长度默认值各是多少？
<details><summary>参考答案</summary>栈 4096（`FINSH_THREAD_STACK_SIZE`）、优先级 20（32 级制，偏低是有意的：不抢业务实时性）、`FINSH_ARG_MAX=10`（参数个数）、`FINSH_CMD_SIZE=80`（命令行长度）、history 5 行（`components/finsh/Kconfig`）。</details>

13. 5.3.0 怎么关 finsh？`RT_DEBUG` 管这件事吗？
<details><summary>参考答案</summary>关 `RT_USING_MSH`（总开关；其下 `FINSH_USING_MSH` 默认 y）。`FINSH_USING_MSH_ONLY` 在 5.3.0 不存在，`RT_DEBUG` 是调试断言级别、与 shell 无关——用它关 shell 是记错了开关。</details>

14. menuconfig 与 scons 谁写 `.config`、谁生成 `rtconfig.h`？
<details><summary>参考答案</summary>menuconfig 把选择写进 `.config`；scons 读 `.config` 生成 `rtconfig.h`。两段分工，旧材料「menuconfig 生成 rtconfig.h」吞了 scons 的一步。`rtconfig.h` 是生成物，手改必被覆盖；改默认值去 Kconfig 的 `default` 或 `.config`。</details>

15. `RT_USING_I2C` 在 rtconfig.h 里长什么样？
<details><summary>参考答案</summary>无值宏：`#define RT_USING_I2C`。Kconfig bool 的产物是「定义/不定义」，不是 0/1 数值——判存在用 `#ifdef`，写 `#if RT_USING_I2C` 对无值宏是错的（未定义时是 0，定义了无值展开也是 0）。</details>

16. `depend` 参数接的是什么？
<details><summary>参考答案</summary>Kconfig 与 scons 的接合点：`DefineGroup(..., depend=['RT_USING_DEVICE'])` 表示只有该宏开了这组源码才进构建。Kconfig 决定宏的开与不开，SConscript 的 depend 决定开了才编。</details>

17. 仓库里的 RT-Thread lab 能验证本章内容吗？为什么？
<details><summary>参考答案</summary>不能。`mcu/code/rtos/02-rt-thread-lab/rtconfig.h:2-5` 是 Nano 式裁剪：无 `RT_USING_DEVICE`、无 `RT_USING_FINSH`，只够验证调度与 IPC。设备框架与 shell 要切标准 BSP 或显式打开这两个组件，判据是 `msh />` 与 `list_device` 有输出。</details>

18. 本章哪些说法是来源说法、哪些是未实测？
<details><summary>参考答案</summary>来源说法（未复核）：「168 MHz 上纳秒级的调用开销」「整套 msh 约 10–20 KB Flash」「每条命令 16–24 B」。未实测：全部实验（msh 出现、led 命令、软件包点单、GDB 下钻）。文档推导：ops 两套接口、open 顺序、GET_PIN 公式与变体、FSymTab/KEEP 机制、Kconfig→.config→rtconfig.h 分工、BSP 三区。</details>
