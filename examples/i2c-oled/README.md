# i2c-oled —— 硬件 I2C 驱动 SSD1306 OLED

> 难度：★★★☆　｜　涉及外设：I2C + SSD1306　｜　对应章节：[07 I2C 总线](../../docs/07-I2C总线.md)

<p align="center">
  <img src="../../assets/animations/i2c-transaction.svg" width="760" alt="I2C 完整事务时序">
  <br><sub>▲ 动画：I2C 完整事务 START / 地址 / ACK / 数据 / STOP（作者自绘矢量图）</sub>
</p>

## 一、功能说明

用 STM32F103 的**硬件 I2C1**（PB6=SCL、PB7=SDA）驱动 0.96 寸 **SSD1306（128×64）** OLED：

- 完整初始化命令表（电荷泵、多路复用比、对比度等）；
- **软件显存（framebuffer 1024 字节）** + 页寻址一次性刷屏，避免逐点写 I2C 太慢；
- 内置 5×7 点阵字库，可显示字符串；每秒刷新计数器与进度条；
- 每个 I2C 传输都带**超时**判断，并提供**总线死锁恢复**函数（9 个时钟脉冲解锁）。

## 二、硬件接线表

| 开发板 | 外设 | 引脚 | 接法 | 备注 |
| --- | --- | --- | --- | --- |
| BluePill | OLED VCC | 3.3V | 接 3.3V | 勿接 5V（部分模块无 LDO） |
| BluePill | OLED GND | GND | 共地 | — |
| BluePill | OLED SCL | PB6 (I2C1_SCL) | 直连 | 模块一般已带 4.7kΩ 上拉 |
| BluePill | OLED SDA | PB7 (I2C1_SDA) | 直连 | 同上 |

> I2C 是**开漏总线**，SCL/SDA 必须有上拉电阻。大多数 OLED 模块板上已焊 4.7kΩ，
> 若没有需外接；上拉太大（>10kΩ）会导致边沿变缓、通信不稳。

## 三、CubeMX 关键配置

| 配置项 | 取值 | 说明 |
| --- | --- | --- |
| I2C1 → I2C | I2C（不是 SMBus） | 标准模式 |
| I2C1 → Clock Speed | 100000 Hz | 标准模式 100kHz |
| GPIO PB6/PB7 | I2C1_SCL / I2C1_SDA，AF Open Drain | 复用开漏 |
| RCC → HSE | Crystal/Ceramic Resonator | 8MHz 晶振 |
| 地址 | 0x3C（7 位） | HAL 用 `0x3C<<1 = 0x78` |

## 四、关键代码解读

**1) 初始化命令表（节选）**

```c
static const uint8_t g_ssd1306_init_cmds[] = {
    0xAE,               /* 关显示 */
    0x20, 0x00,         /* 水平寻址模式 */
    0x81, 0x7F,         /* 对比度 */
    0xA1,               /* 段重映射：左右不颠倒 */
    0xC8,               /* COM 扫描方向：上下不颠倒 */
    0xA8, 0x3F,         /* 多路复用比 = 64 行 */
    0x8D, 0x14,         /* 使能电荷泵（关键：不使能屏幕不亮） */
    0xAF,               /* 开显示 */
};
```

**2) 写命令 / 写数据（控制字节区分）**

```c
static uint8_t ssd1306_write_cmd(uint8_t cmd) {
    uint8_t buf[2] = { 0x00, cmd };      /* 0x00 = 后续是命令 */
    return HAL_I2C_Master_Transmit(&hi2c1, 0x78, buf, 2, 100);
}
/* 0x40 = 后续是显存数据；这里把整页 128 字节一次性发出 */
```

**3) 显存组织与刷屏（页寻址）**

```c
/* 显存：每字节 = 同一页(8 行)中的一列，bit0 顶部、bit7 底部 */
static void ssd1306_draw_pixel(uint8_t x, uint8_t y, uint8_t on) {
    uint16_t idx = x + (y / 8) * OLED_WIDTH;
    uint8_t  bit = 1 << (y % 8);
    if (on) g_oled_buf[idx] |= bit; else g_oled_buf[idx] &= ~bit;
}
/* 刷屏：逐页设页地址 + 列地址，再写 128 字节 */
ssd1306_write_cmd(0xB0 + page);
ssd1306_write_cmd(0x00);  ssd1306_write_cmd(0x10);
ssd1306_write_data(&g_oled_buf[page * OLED_WIDTH], OLED_WIDTH);
```

**4) 总线死锁恢复（从机拉低 SDA 时的救命函数）**

```c
static void i2c_bus_recovery(void) {
    HAL_I2C_DeInit(&hi2c1);
    /* SCL/SDA 切成开漏 GPIO，发 9 个时钟脉冲 */
    for (int i = 0; i < 9; i++) { SCL=0; delay; SCL=1; delay; }
    /* 补一个 STOP，再重新初始化 I2C */
    SDA=0; delay; SCL=1; delay; SDA=1;
    i2c_init();
}
```

当主机在从机发数据途中被复位，从机会一直拉低 SDA，导致下次 `START` 失败——此时手动补时钟即可解锁。

## 五、编译烧录步骤

1. CubeMX 生成 F103C8 工程，按上表配 I2C1，覆盖 `Core/Src/main.c`。
2. 编译下载；若用生成的 `MX_I2C1_Init`，删除本文件里的 `i2c_init()` 以免重复。
3. 上电观察 OLED 显示。

## 六、预期现象

- OLED 点亮，显示外框 + `STM32 OLED` / `I2C SSD1306` 标题；
- 第 3 行 `TIME:` 后的秒数每秒 +1；
- 底部进度条每 8 秒走满一轮后回零。

## 七、常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 屏幕全黑 | 未使能电荷泵 / 地址错 | 发 `0x8D,0x14`；确认地址 0x3C |
| 花屏/错位 | 显存列/页映射写错 | 检查 `x + (y/8)*128` 与 bit 顺序 |
| 通信超时 | 没上拉 / 上拉太大 | 接 4.7kΩ 上拉，缩短走线 |
| 偶发失败后彻底卡死 | 总线被从机拉低 | 调 `i2c_bus_recovery()` |
| 显示上下颠倒 | COM 扫描方向 | 改 `0xC8`↔`0xC0` |
| 显示左右颠倒 | 段重映射 | 改 `0xA1`↔`0xA0` |
| 刷新很慢闪烁 | 逐点写 I2C | 用显存 + 整页一次性刷 |

## 八、相关资源

- 参考手册 **RM0008** 第 26 章（I2C，含 SR/DR/CCR/TRISE）
- SSD1306 数据手册（Solomon Systech，命令表与页寻址说明）
- 相关图：[`assets/animations/i2c-transaction.svg`](../../assets/animations/i2c-transaction.svg)
- 免责声明：本示例配图为作者自绘矢量图/程序生成动画，非厂商实拍照片。
