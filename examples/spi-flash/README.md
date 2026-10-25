# spi-flash —— 硬件 SPI 驱动 W25Q64

> 难度：★★★☆　｜　涉及外设：SPI + W25Q64　｜　对应章节：[08 SPI 总线](../../docs/08-SPI总线.md)

<p align="center">
  <img src="../../assets/animations/spi-transfer.svg" width="760" alt="SPI 全双工移位与四种模式时序">
  <br><sub>▲ 动画：SPI 全双工移位 CPOL/CPHA 四种模式时序（作者自绘矢量图）</sub>
</p>

## 一、功能说明

用硬件 SPI1 驱动 **W25Q64**（8MB SPI NOR Flash），完整走一遍 **读 ID → 擦除 → 写入 → 读回校验**：

- 读 **JEDEC ID**（`0xEF 0x40 0x17`）确认芯片在位；
- **4KB 扇区擦除** → **页编程（≤256B）** → **读数据**；
- **轮询状态寄存器 BUSY 位**等待擦写完成；
- `w25x_write()` 自动**跨页拆分**（一次写 300 字节，跨两页）。

## 二、硬件接线表

| 开发板 | 外设 | 引脚 | 接法 | 备注 |
| --- | --- | --- | --- | --- |
| BluePill | W25Q64 VCC | 3.3V | 接 3.3V | **W25Q64 是 3.3V 器件** |
| BluePill | W25Q64 GND | GND | 共地 | — |
| BluePill | W25Q64 CLK | PA5 (SPI1_SCK) | 直连 | — |
| BluePill | W25Q64 DO | PA6 (SPI1_MISO) | 直连 | DO = 从机输出 |
| BluePill | W25Q64 DI | PA7 (SPI1_MOSI) | 直连 | DI = 从机输入 |
| BluePill | W25Q64 CS | PA4 | 软件片选 | 低电平选中 |

> **DO/DI 别接反**：MCU 的 MOSI 接 Flash 的 DI，MCU 的 MISO 接 Flash 的 DO。
> 若模块带 `HOLD`/`WP` 引脚，接 3.3V（不使用时不要悬空）。

## 三、CubeMX 关键配置

| 配置项 | 取值 | 说明 |
| --- | --- | --- |
| SPI1 → Mode | Full-Duplex Master | 主机全双工 |
| SPI1 → Data Size | 8 Bits | — |
| SPI1 → Clock Polarity | Low（CPOL=0） | W25Q 用模式 0 或 3 |
| SPI1 → Clock Phase | 1 Edge（CPHA=0） | 模式 0 |
| SPI1 → NSS | Software | 用 PA4 软件片选 |
| SPI1 → Prescaler | 8（9MHz） | W25Q64 支持到 104MHz |
| GPIO PA4 | Output Push Pull | 片选 |

> SPI 模式：W25Q 支持 **模式 0（CPOL=0,CPHA=0）** 和 **模式 3（CPOL=1,CPHA=1）**，
> 本示例用模式 0。模式配错会读到全 0x00 或全 0xFF。

## 四、关键代码解读

**1) 读 JEDEC ID 确认芯片**

```c
static void w25x_read_jedec_id(uint8_t id[3]) {
    CS_LOW;
    w25x_spi_txrx(0x9F);          /* 命令：读 JEDEC ID */
    id[0] = w25x_spi_txrx(0xFF);  /* 厂商 0xEF */
    id[1] = w25x_spi_txrx(0xFF);  /* 存储器类型 0x40 */
    id[2] = w25x_spi_txrx(0xFF);  /* 容量 0x17（64 Mbit = 8 MB） */
    CS_HIGH;
}
```

**2) 写使能 + 轮询 BUSY（擦写前必做）**

```c
static uint8_t w25x_read_status(void) {
    CS_LOW; w25x_spi_txrx(0x05); uint8_t sr = w25x_spi_txrx(0xFF); CS_HIGH;
    return sr;
}
static uint8_t w25x_wait_busy(void) {
    uint32_t start = HAL_GetTick();
    while (w25x_read_status() & 0x01) {                 /* bit0 = BUSY */
        if (HAL_GetTick() - start > 5000) return HAL_TIMEOUT;
    }
    return HAL_OK;
}
```

**3) 跨页写入（NOR Flash 一页只能写 256B）**

```c
static void w25x_write(uint32_t addr, const uint8_t *buf, uint32_t len) {
    while (len) {
        uint32_t page_remain = 256 - (addr % 256);       /* 到页边界 */
        uint16_t chunk = (len < page_remain) ? len : page_remain;
        w25x_page_program(addr, buf, chunk);             /* 内部含写使能+等待 */
        addr += chunk; buf += chunk; len -= chunk;
    }
}
```

**4) 扇区擦除（4KB，擦后为 0xFF）**

```c
w25x_write_enable();
CS_LOW;
w25x_spi_txrx(0x20);                       /* 扇区擦除命令 */
w25x_spi_txrx(addr >> 16); w25x_spi_txrx(addr >> 8); w25x_spi_txrx(addr);
CS_HIGH;
w25x_wait_busy();                          /* 典型 ~45ms */
```

> **NOR Flash 特性**：只能把 1 写成 0，要把 0 变回 1 必须**先擦除**。所以「写之前先擦」。

## 五、编译烧录步骤

1. CubeMX 生成 F103C8 工程，配 SPI1（模式 0，软件 NSS），覆盖 `Core/Src/main.c`。
2. 编译下载；若已有 `MX_SPI1_Init`，删除本文件的 `spi_init()` 以免重复。
3. 上电观察板载 LED：常亮=校验通过，闪烁=数据不一致。

## 六、预期现象

- 读到的 JEDEC ID 为 `EF 40 17`（可在调试器观察 `id[]`）；
- 擦除→写入 300 字节→读回，`memcmp` 一致，板载 LED **常亮**；
- 若接线错误或芯片不在位，程序停在 `error_handler()`。

## 七、常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 读 ID 全 0xFF | MISO 没接 / 芯片没供电 | 检查 DO/DI 与 3.3V |
| 读 ID 全 0x00 | CS 没拉低 / SPI 模式错 | 检查 CS，确认 CPOL/CPHA |
| 写入读回不一致 | 写前没擦除 / 没写使能 | 先 `sector_erase`，每页前 `write_enable` |
| 只写了前 256 字节 | 页编程未跨页拆分 | 用 `w25x_write()` 自动拆页 |
| 偶尔校验失败 | 没等 BUSY 清零 | 每次擦/写后 `w25x_wait_busy()` |
| 通信不稳定 | 杜邦线太长/时钟太快 | 降 SPI 时钟（加大分频） |
| 数据错位 | MSB/LSB 顺序或模式错 | `SPI_FIRSTBIT_MSB` + 模式 0 |

## 八、相关资源

- 参考手册 **RM0008** 第 25 章（SPI，含 CR1/CR2/SR/DR）
- W25Q64 数据手册（Winbond，指令集与状态寄存器）
- 相关图：[`assets/animations/spi-transfer.svg`](../../assets/animations/spi-transfer.svg)
- 免责声明：本示例配图为作者自绘矢量图/程序生成动画，非厂商实拍照片。
