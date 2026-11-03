---
title: P6 SPI/I2C 驱动框架：板载外设当教材
status: done
difficulty: 3
minutes: 50
---

# P6 SPI/I2C 驱动框架：拿 ST7789 与 QMI8658 当活教材

> 🎯 立创实战派 S3 板载一块 ST7789 彩屏（SPI）和一颗 QMI8658 姿态传感器（I2C）。学驱动框架最好的方式就是：**让屏幕亮起来，让姿态数据流出来**。本章用 IDF 的新版主机驱动框架（spi_master / i2c_master）打通这两件事。

## 本章精髓

1. 总线与设备两级模型：`spi_bus_config_t` 先配"哪条线"（MOSI/MISO/SCLK），`spi_device_interface_config_t` 再配"跟谁说话"（CS/速率/模式/队列深度）：总线可复用，设备可挂多个（与 [R4](../rtos/rtthread/04-device.md) 的总线模型异曲同工）。
2. 事务（transaction）是 SPI 的灵魂：`spi_transaction_t` 描述一次"命令+地址+数据"的完整交互，队列化异步执行，屏刷带宽就靠"队列里永远有事务在飞"。
3. 新 I2C 驱动的对象化：`i2c_new_master_bus` 出总线句柄，`i2c_master_bus_add_device` 出设备句柄，`i2c_master_transmit_receive` 一把梭"写寄存器地址+读数据"。对比 S11 的逐拍寄存器级，框架把"时序礼仪"全部代劳。

- **能理解**：为什么 SPI 屏要用 DC 引脚区分命令/数据；为什么异步事务的 buffer 生命周期必须覆盖传输期。
- **能用**：读通 E07 工程的 I2C 链路（QMI8658 WHO_AM_I + 六轴），把 ST7789 点亮流程画出来。

## 先修

- [S11 I2C](../stm32/11-i2c.md)、[S12 SPI](../stm32/12-spi.md)（硬件时序）、[P2 引脚矩阵](02-gpio-matrix.md)。

## 先跑起来（10 分钟 quick win）

I2C 先通：读 QMI8658 WHO_AM_I（寄存器 0x00），串口打印出期望的 ID 值 0x05，一次事务就能证明整条链路。E07 工程已提供完整源码，`idf.py flash monitor` 即可。

flash 之前先押个分家人：MOSI 上命令和像素排同一条队，谁在路口把两队分开？押完翻 SPI 事务那一节，点亮屏幕时对一眼那根线。

## 动画：两级模型与事务队列

先配线再认人的两级配置、SPI 事务在队列里连续飞向屏幕、I2C 一句 transmit_receive 走完全部时序礼仪：事务方块从 CPU 飞到 ST7789 的过程，就是屏刷带宽的来源。

![IDF 总线驱动两级模型：先配线，再认人](/anim/esp32-driver-layers.svg)

## 板卡事实

- 立创实战派 S3（N16R8 模组）板载：ST7789 彩屏（SPI，320×240）、触摸 FT6336G（I2C，INT=IO17）、姿态 QMI8658（I2C）、音频 ES8311/ES7210（I2C+I2S）。**全部 GPIO 分配与 I2C 地址以立创 wiki 原理图页为准**（wiki.lckfb.com/zh-hans/szpi-esp32s3/）。
- QMI8658 事实（E07 工程已核实，`code/esp32/04-qmi8658/main/main.c`）：SDA=GPIO1、SCL=GPIO2、7 位地址 **0x6a**、WHO_AM_I 寄存器 0x00 回 **0x05**、六轴数据从 `AX_L(0x35)` 起连读 12 字节。
- ST7789 事实（以立创 wiki 原理图为准）：SPI 接口、支持 mode 0/3、DC 引脚区分命令/数据、CS 引脚选片，具体 GPIO 编号查板卡 wiki 原理图页，成稿时按你手上板子核对标注。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 两级模型 | 总线配置 vs 设备配置逐字段 | 配置 |
| SPI 事务 | transaction 结构与队列化；DC 线的 GPIO 角色 | 库解析 |
| ST7789 点亮 | 初始化序列逐条；开窗/写像素 DMA 路径 | 代码分析 |
| I2C 新驱动 | master_bus/device 句柄模型；transmit_receive 组合事务 | 库解析 |
| QMI8658 数据 | WHO_AM_I→量程配置→六轴读取→换算 | 代码分析 |
| 与 S 篇对照 | 手写时序 vs 框架事务：各自的适用场景 | 库解析 |

## 一、两级模型：先配线，再认人

IDF 的新版 SPI/I2C 驱动都把"总线"和"设备"分成两层配置：这与 [S11](../stm32/11-i2c.md)/[S12](../stm32/12-spi.md) 手写寄存器时"外设实例+引脚+模式"一把配的思路不同，但更贴合"一条总线挂多个设备"的现实。

**SPI 两级**（`driver/spi_master.h`）：

```c
/* 第一级：总线——配"哪条线" */
spi_bus_config_t bus_cfg = {
    .mosi_io_num = MOSI_PIN, .miso_io_num = MISO_PIN, .sclk_io_num = SCLK_PIN,
    .max_transfer_sz = 4096, .flags = SPICOMMON_BUSFLAG_MASTER,
};
ESP_ERROR_CHECK(spi_bus_initialize(SPI2_HOST, &bus_cfg, SPI_DMA_CH_AUTO));

/* 第二级：设备——配"跟谁说话" */
spi_device_interface_config_t dev_cfg = {
    .clock_speed_hz = 40 * 1000 * 1000,  /* 40MHz */
    .mode = 0,                            /* CPOL=0/CPHA=0（ST7789 支持 0/3） */
    .spics_io_num = CS_PIN,               /* 片选引脚 */
    .queue_size = 7,                      /* 事务队列深度：屏刷带宽靠它 */
    .flags = SPI_DEVICE_HALFDUPLEX,
};
spi_device_handle_t spi;
ESP_ERROR_CHECK(spi_bus_add_device(SPI2_HOST, &dev_cfg, &spi));
```

总线配一次（MOSI/MISO/SCLK 固定），设备可挂多个（每个设备自己的 CS/速率/模式）。共享 SPI 总线挂屏+挂 Flash 就是这么来的。`SPI_DMA_CH_AUTO` 让 IDF 自动分配 DMA 通道（[S8 DMA](../stm32/08-dma.md) 的"外设侧请求"由框架代劳）。

**I2C 两级**（`driver/i2c_master.h`，E07 工程实测版 `code/esp32/04-qmi8658/main/main.c`）：

```c
/* 第一级：总线 */
i2c_master_bus_config_t bus_cfg = {
    .i2c_port = I2C_NUM_0, .sda_io_num = 1, .scl_io_num = 2,
    .clk_source = I2C_CLK_SRC_DEFAULT, .glitch_ignore_cnt = 7,
    .flags.enable_internal_pullup = true,
};
ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &bus));

/* 第二级：设备 */
i2c_device_config_t dev_cfg = {
    .dev_addr_length = I2C_ADDR_BIT_LEN_7, .device_address = 0x6a, .scl_speed_hz = 100000,
};
ESP_ERROR_CHECK(i2c_master_bus_add_device(bus, &dev_cfg, &imu));
```

对比 [S11](../stm32/11-i2c.md) 的寄存器级：那里你手写 CR2.FREQ/CCR/TRISE、自己拆 START/ADDR/数据/STOP 的事件链；这里 IDF 把整套时序包成 `i2c_new_master_bus` + `i2c_master_bus_add_device`，你只管"总线+设备"两个结构体。**框架的价值在规模**：挂 5 个 I2C 设备，寄存器版要管 5 套地址+5 套事件链，框架版只是 5 次 `add_device`。

## 二、SPI 事务：队列化异步执行 + DC 引脚

SPI 屏刷的核心数据结构是 `spi_transaction_t`，它描述一次完整交互：

```c
spi_transaction_t t = {
    .length = 8 * n,            /* 位数 = 字节数 × 8 */
    .tx_buffer = buf,           /* 发送缓冲（NULL = 只收） */
    .rx_buffer = NULL,          /* 接收缓冲（NULL = 只发） */
    .flags = 0,                  /* 可配 SPI_TRANS_USE_RXDATA 等 */
};
ESP_ERROR_CHECK(spi_device_polling_transmit(spi, &t));  /* 同步等完成 */
/* 或异步：spi_device_queue_trans + spi_device_get_trans_result */
```

队列化的精髓（`queue_size = 7`）：你可以连续投 7 个事务进队列，CPU 不必等每个完成，SPI 外设+DMA 自己从队列里取事务飞，CPU 投完就去准备下一批。屏刷 60fps 的带宽就靠"队列里永远有事务在飞"，CPU 不会卡在 `while(TXE)` 上（[S12](../stm32/12-spi.md) 的寄存器版要自己等每个标志）。

**DC 引脚**：ST7789 这类屏的 SPI 帧不只是数据，还有命令（开窗、设显示模式等）。DC 引脚电平区分当前帧是命令（DC=0）还是数据（DC=1）。这就是 [S12](../stm32/12-spi.md) 提到的"SPI 没有地址阶段，靠应用层约定"的屏版实现。`spi_device_interface_config_t` 里 `.spics_io_num` 是 CS，DC 一般另配一个 GPIO，每次发事务前按命令/数据拉低/拉高。

骨架坑列表的"CS 与 DC 搞反"：DC 是数据/命令选择（每帧切），CS 是片选（整段事务期间低）；接错或配置错位，症状是"全屏噪声"（命令被当数据、数据被当命令，初始化序列全乱）。

## 三、ST7789 点亮：初始化序列→开窗→刷像素

点亮流程三步（伪代码，完整初始化序列以屏手册 + 立创 wiki 为准）：

```c
/* ① 初始化序列：一串命令+参数，每条走一次 SPI 事务（DC=0 命令、DC=1 参数） */
static const uint8_t init_cmds[] = { /* SLPOUT=0x11, DISPON=0x29, ... 以屏手册为准 */ };
for (each cmd in init_cmds) {
    gpio_set_level(DC_PIN, 0);  spi_send(cmd);
    gpio_set_level(DC_PIN, 1);  spi_send(params);
}

/* ② 开窗：CASET=0x2A（列地址）+ RASET=0x2B（行地址）设定刷写区域 */
gpio_set_level(DC_PIN, 0); spi_send(0x2A);           /* 命令 */
gpio_set_level(DC_PIN, 1); spi_send(col_start, col_end);  /* 数据：4 字节 */

/* ③ 写像素：RAMWR=0x2C 后连续发 RGB565 数据，DC=1 */
gpio_set_level(DC_PIN, 0); spi_send(0x2C);
gpio_set_level(DC_PIN, 1); spi_send(pixel_buf, n * 2);  /* 每像素 2 字节 RGB565 */
```

刷一帧 320×240×2 = 153600 字节。40MHz SPI 理论带宽 5MB/s，一帧约 30ms。60fps（16.7ms/帧）吃紧，所以屏刷常用 DMA + 队列化事务（第二节）让 CPU 不卡在传输上。

## 四、I2C 新驱动：transmit_receive 一把梭

E07 工程读 QMI8658 寄存器的完整代码（`code/esp32/04-qmi8658/main/main.c` 第 19–27 行）：

```c
static esp_err_t read_reg(uint8_t reg, uint8_t *bytes, size_t count)
{
    return i2c_master_transmit_receive(imu, &reg, 1, bytes, count, 100);
}
static void write_reg(uint8_t reg, uint8_t value)
{
    const uint8_t bytes[] = {reg, value};
    ESP_ERROR_CHECK(i2c_master_transmit(imu, bytes, sizeof(bytes), 100));
}
```

对照 [S11](../stm32/11-i2c.md) 的寄存器级写 EEPROM：那里你手写 `CR1 |= START`→等 SB→`DR = 地址`→等 ADDR→清 ADDR（先 SR1 后 SR2）→`DR = 数据`→等 TXE/BTF→`CR1 |= STOP`，六步事件链一步不能错；这里 `i2c_master_transmit_receive(imu, &reg, 1, bytes, count, 100)` 一句把"写寄存器地址 + 重复 START + 读 N 字节 + STOP"全套礼仪代劳。100 是超时 ms。

**地址处理的坑**（骨架坑列表）：IDF 用 7 位地址（`device_address = 0x6a`，不左移）；手册给 8 位地址（如 0xD4）要先 `>>1`（[S11](../stm32/11-i2c.md) 的"0x50 上线变 0xA0"在 IDF 这边自动处理）。QMI8658 手册标 7 位地址 0x6a，直接填；若某器件手册给 8 位 0xD4，填 `(0xD4 >> 1) = 0x6a`。

## 五、QMI8658 数据：WHO_AM_I → 量程 → 六轴读取

E07 工程的完整初始化与读取流程（`code/esp32/04-qmi8658/main/main.c`）：

```c
/* ① 链路自检：读 WHO_AM_I */
uint8_t id;
ESP_ERROR_CHECK(read_reg(0x00, &id, 1));
if (id != 0x05) { ESP_LOGE(TAG, "WHO_AM_I=0x%02x (expected 0x05)", id); return; }

/* ② 量程配置（寄存器地址以 QMI8658 手册为准） */
write_reg(0x60, 0xb0);             /* RESET */
vTaskDelay(pdMS_TO_TICKS(20));
write_reg(0x08, 0x00);             /* CTRL7：先关闭采样 */
write_reg(0x02, 0x40);             /* CTRL1：地址递增 */
write_reg(0x03, 0x15);             /* CTRL2：±4g、250Hz */
write_reg(0x04, 0x55);             /* CTRL3：±512dps、250Hz */
write_reg(0x08, 0x03);             /* CTRL7：加速度+角速度使能 */

/* ③ 周期读取：状态位 + 连读 12 字节 */
for (;;) {
    vTaskDelay(pdMS_TO_TICKS(100));   /* 10Hz */
    uint8_t status, bytes[12];
    if (read_reg(0x2e, &status, 1) == ESP_OK && (status & 0x03) == 0x03) {
        read_reg(0x35, bytes, sizeof(bytes));   /* AX_L 起 12 字节 */
        /* 换算：32768/4=8192 LSB/g；32768/512=64 LSB/(deg/s) */
    }
}
```

三个要点对应 [S11](../stm32/11-i2c.md) 的纪律：

1. **WHO_AM_I 先行**：和 S12 读 W25Q 的 JEDEC ID 同理，链路自检的第一步，ID 错就停（E07 的 `return` 不无限等待）。
2. **量程与灵敏度换算**：±4g → 8192 LSB/g（32768/4），±512dps → 64 LSB/(deg/s)（32768/512）。这是 [S9 ADC](../stm32/09-adc.md) "分辨率/量程"在 IMU 上的同构。
3. **状态位等数据就绪**：`status & 0x03 == 0x03` 表示加速度+角速度都完成了一次采样，再连读 12 字节，避免读到半新半旧的样本。E07 的教学口径是"每 100ms 取最新样本，不声称无丢样采集"（main.c 第 5 行注释），诚实标注。

字节组装（main.c 第 29–33 行）显式小端 + 符号扩展，不依赖宿主字节序和指针别名。这是 [C7](../c/07-ub-misra.md) 严格别名纪律的实战：用 `p[0] | (p[1] << 8)` 而非 `*(int16_t*)p`，避免别名违规。

## 六、与 S 篇对照：手写时序 vs 框架事务

| 维度 | S 篇手写寄存器 | P 篇 IDF 框架 |
|---|---|---|
| 配置粒度 | 每个寄存器位手填 | 结构体字段 → 框架翻译 |
| 时序礼仪 | 逐拍等事件（SB/ADDR/TXE/BTF） | `transmit_receive` 一句代劳 |
| 多设备 | 每设备一套事件链 | `add_device` 复用总线 |
| DMA | 手配流/通道/请求映射 | `SPI_DMA_CH_AUTO` 自动分配 |
| 调试 | 看寄存器位即知状态 | 看 ESP_LOG + 协议分析仪 |
| 适用 | 学习时序/极致性能 | 快速接入器件/多设备 |

选型很朴素：**学时序手写，做产品用框架**。S 篇让你懂"框架在替你做什么"，P 篇让你"用框架快速接入器件"。两层能力都备，才是嵌入式工程师的完整武器库。

## 记忆锚点

::: tip 一句话记住
**先配线再认人（总线/设备两级），SPI 靠事务排队飞，I2C 一句 transmit_receive 走完礼仪；屏要 DC 分令数，传感器先问 WHO_AM_I。**
:::

**延伸**：IDF 总线驱动两级模型动画见 [P6 动画](/anim/esp32-driver-layers.svg)；STM32 SPI/I2C 对照见 [S11](../stm32/11-i2c.md) 和 [S12](../stm32/12-spi.md)；GD32 外设编号差异见 [G4](../gd32/04-periph-diff.md)。

## 实物实验

- [E07 读 QMI8658](../lab/e07-qmi8658.md)：摇板子看三轴数据跳变；
- ST7789 刷屏：纯色→色带→帧率粗测（改 SPI 时钟 40M/80M 对比）。

## 常见坑

- **SPI 模式配错**：ST7789 用 mode0/3（以屏手册为准），模式错白屏花屏。
- **CS 与 DC 搞反**：DC 是数据/命令选择不是片选，接线/配置错位症状为"全屏噪声"。
- **I2C 地址左移忘处理**：IDF 用 7 位地址（不左移），手册给 8 位地址要先 >>1（S11 复训）。
- **事务缓冲用局部变量做异步传输**：函数返回后缓冲失效：异步事务的 buffer 生命周期必须覆盖传输期（C1 复训）。
- **I2C 总线未上拉**：`enable_internal_pullup = true` 适合原型；高速/多设备时外接 4.7k 上拉更稳（[S11](../stm32/11-i2c.md) 上拉节）。

## 短自测

1. SPI/I2C 的"两级模型"分别配什么？为什么总线只配一次、设备可挂多个？
<details><summary>参考答案</summary>第一级配总线（SPI: MOSI/MISO/SCLK；I2C: SDA/SCL+时钟源），第二级配设备（SPI: CS/速率/模式/队列深度；I2C: 地址/速率）。总线是物理线，一条线只有一个引脚分配，配一次就够；设备是挂在总线上的器件，每个有自己的 CS（SPI）或地址（I2C）+速率+模式，所以可挂多个、各配各的。共享总线是"线复用"的实现。</details>

2. ST7789 的 DC 引脚干什么？为什么 CS 和 DC 搞反会"全屏噪声"？
<details><summary>参考答案</summary>DC 是数据/命令选择引脚：DC=0 当前 SPI 帧是命令（如开窗命令 0x2A），DC=1 是数据（如像素 RGB565）。CS 是片选，整段事务期间低。搞反后：命令被当数据写入像素 RAM、数据被当命令送进命令解释器，初始化序列全乱，屏不知道显示什么，全屏随机噪声。</details>

3. E07 读 QMI8658 为什么先读 WHO_AM_I？ID 错为什么直接 return 而不是重试？
<details><summary>参考答案</summary>WHO_AM_I 是链路自检：读对说明 I2C 总线+设备地址+寄存器地址全对，链路可用；读错说明接线/地址/上拉有问题，继续写配置无意义（写进错误的器件）。return 而非重试是教学工程的诚实口径：ID 错先看硬件，不在软件层无限等待掩盖问题。产品代码可加重试+日志，但自检失败仍要停。</details>

4. IDF 的 7 位地址 `0x6a`，手册给 8 位地址 `0xD4`，怎么填？
<details><summary>参考答案</summary>IDF 用 7 位地址（device_address 字段不左移），手册给 8 位地址要先 >>1：0xD4 >> 1 = 0x6a。QMI8658 手册直接标 7 位 0x6a 就直接填。判断方法：8 位地址最低位通常是 0（写）或 1（读），7 位地址最低位是 0；或者看手册"7-bit address"字段直接拿。</details>

5. 异步 SPI 事务为什么不能用局部变量做 tx_buffer？
<details><summary>参考答案</summary>异步事务投进队列后，SPI 外设+DMA 会在"未来的某个时刻"才读 buffer 内容。如果 buffer 是局部变量，函数返回后栈帧释放，那块内存被复用，DMA 读到的是垃圾。异步事务的 buffer 生命周期必须覆盖整个传输期：用全局变量、堆分配（直到 get_trans_result 后释放）、或静态缓冲池。同步事务（polling_transmit）等完成才返回，局部变量安全。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| I2C 两级模型 + transmit_receive | `code/esp32/04-qmi8658/main/main.c` 36–47、19–27 行（E07 工程实测） |
| QMI8658 WHO_AM_I + 量程 + 六轴 | 同上 48–80 行；寄存器地址以 QMI8658 手册为准 |
| SPI 两级模型 + 事务队列化 | IDF `driver/spi_master.h`；ST7789 初始化以屏手册+立创 wiki 为准 |
| DC 引脚命令/数据区分 | 本节第二、三节；[S12 SPI](../stm32/12-spi.md) 无地址阶段 |
| 7 位地址 vs 8 位地址 | [S11 I2C](../stm32/11-i2c.md) 地址节 + 本节第四节 |
| 字节组装避免别名违规 | E07 main.c 29–33 行；[C7](../c/07-ub-misra.md) 严格别名 |

## 你做到了

- 两块板载外设听你调遣：屏会亮，姿态会报数；
- 总线/设备/事务的框架语言成型，以后接任何 SPI/I2C 器件都是同一套流程。

分家人是 DC：一根线的高低电平，替屏幕省掉"这笔是命令还是像素"的猜谜。这也是它和 CS 一样必须进设备配置的原因。总线只管送，听懂不听懂，是设备端自己的事。

<div class="achievement">
✅ 下一站：<a href="07-timer-ledc.html">P7 定时器与 LEDC</a>：GPTimer 和 LEDC 的分工，呼吸灯与背光调光。
</div>

## 可独立运行的最小实验

[QMI8658 六轴读取](../lab/e07-qmi8658.md) 已提供独立工程、配置说明和完整源码。板上现象待实测。
