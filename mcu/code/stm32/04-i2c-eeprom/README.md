# E05：I2C EEPROM 写入与读回

基准 STM32F407ZGT6，复位 HSI 16MHz、APB1 16MHz；GNU Arm Embedded 编译器，GNU make。不要在未复位、时钟树已被其它程序改动的条件下直接跳入 main。

## 接线

外接 AT24C02 模块：PB6→SCL、PB7→SDA、3.3V、GND 共地；SCL/SDA 外部 4.7kΩ 上拉；A0/A1/A2 与 WP 接地。地址 0x50 为 7 位地址。USB-TTL RX→PA9（115200 8N1），GND 共地。先确认板上这些引脚没有其它负载占用。

PB6/PB7 AF4、PA9 AF7 依据 [ST STM32F407 数据手册](https://www.st.com/resource/en/datasheet/stm32f407vg.pdf)；寄存器/单字节读取时序依据 [RM0090](https://www.st.com/resource/en/reference_manual/dm00031020-stm32f405415-stm32f407417-stm32f427437-and-stm32f429439-advanced-armbased-32bit-mcus-stmicroelectronics.pdf) 与 [ST HAL I2C 源码](https://github.com/STMicroelectronics/stm32f4xx-hal-driver/blob/master/Src/stm32f4xx_hal_i2c.c) HAL_I2C_Mem_Read 单字节分支。

## 构建与运行

~~~sh
cd code/stm32/04-i2c-eeprom
make
make flash
~~~

Windows 可用 mingw32-make，并将 GNU Arm 工具链与 Git usr/bin 放入 PATH；flash 使用 OpenOCD + ST-Link。

每次复位只向地址 0x10 写入 0x5A 一次，再 ACK polling 等待 EEPROM 完成写周期，重复 START 读回。该地址旧值会被覆盖，使用实验专用模块。预期串口输出 read=0x5A PASS，不会无限擦写。

## 排查与观测

- FAIL at BUSY：检查上拉、SDA/SCL、模块供电，排除总线被拉死。
- address/ACK：查 7 位地址 0x50、A0–A2 接地；写周期内 NACK 被轮询处理，超时则退出。
- MISMATCH：查 WP 接地、模块型号与接线。
- 单字节接收顺序：关 ACK → 清 ADDR（读 SR1/SR2）→ STOP → 等 RXNE → 读 DR。
- 分析仪抓取需至少 1MHz；地址显示可能是 7 位 0x50 或含 R/W 的 0xA0/0xA1。

## 验证状态

已用 GNU Arm 15.2.1 编译链接，-Wall -Wextra -Werror 零警告。固件编译不等于硬件验证；EEPROM 读数与波形 **待上板实测**。
