---
title: 实验 E05 I2C 抓包读 EEPROM
status: done
difficulty: 3
minutes: 60
code_status: ready
hardware_status: pending
code_note: 完整 I2C EEPROM 工程；外接 AT24C02，非假定板载接线。
projects: ["stm32-04-i2c-eeprom"]

---

# 实验 E05 I2C 抓包读 EEPROM：时序与手册逐拍对表

> 🎯 I2C 学得扎不扎实，一块 AT24C EEPROM + 一台逻辑分析仪就能验出来：把"写 0x5A 到地址 0x10 再读回"的完整事务抓下来，每一拍对应手册的哪个状态、驱动代码的哪一行。全对上了，I2C 才算毕业。

## 实验信息卡

<LabStatus />

| 项 | 内容 |
|---|---|
| 编号 | E05 |
| 对应章节 | [S11 I2C](../stm32/11-i2c.md) |
| 目标板 | 霸天虎 |

## 实验目标

- 现象：EEPROM 写入并读回 0x5A；分析仪解码出完整事务（START/地址/ACK/数据/重复 START/NACK/STOP）。
- 能力：I2C 波形解码、事件位与波形互查、上拉电阻对波形的影响评估。

## 装备

| 装备 | 数量 | 备注 |
|---|---|---|
| AT24C02 模块 | 1 | 地址 0x50（A0-A2 接地） |
| 逻辑分析仪 | 1 | 两通道：SDA/SCL |
| 上拉电阻 4.7kΩ ×2 | 2 | 模块自带则免 |
| 霸天虎（本页 EEPROM 工程） | 1 | I2C1 PB6/PB7，外接模块按下文接线 |

> 板卡外观与原理图见 [野火霸天虎官方资料页](https://doc.embedfire.com/products/link/zh/latest/mcu/stm32/stm32f407_batianhu.html)。

![24C02 EEPROM 芯片，SOIC-8 贴片封装，表面丝印 24C02](/images/tools/eeprom-24c02.jpg)

被测芯片形态参考（资料参考图，不是上板验证证据）：SOIC-8 封装，圆点为 1 脚（A0），逆时针编号，8 脚 VCC、4 脚 GND。来源：[Wikimedia Commons](https://commons.wikimedia.org/wiki/File:24C02_Package.jpg)（CC BY-SA 2.0，作者 cole8888）。

## 原理一句话

I2C 的每次交互都是"START + 地址帧 + ACK + 数据帧(+ACK) + STOP"的积木组合，寄存器级驱动就是按事件位依次搭建这些积木。

换挡前先猜：上拉从 10kΩ 换到 1kΩ，上升沿会陡一半，还是陡好几倍？押一个倍数，波形自己公布。

## 接线

- PB6→SCL、PB7→SDA、GND 共地、3.3V 供电；
- 分析仪 CH0→SDA、CH1→SCL；
- 若无上拉：SCL/SDA 各经 4.7kΩ 上拉到 3.3V。

![E05 接线与事务：PB6/PB7 接 AT24C02，SCL/SDA 上拉，分析仪 CH0 接 SDA、CH1 接 SCL；下方为写事务与随机读事务的字节条](/images/labs/e05-i2c-wiring.svg)

START/STOP/ACK 的逐拍电平变化见 [S11 I2C](../stm32/11-i2c.md) 的时序动画。

## 步骤

1. 在仓库根运行 `cd code/stm32/04-i2c-eeprom`，`make` 后 `make flash`（ST-Link）；USB-TTL RX 接 PA9、GND 共地，以 115200 8N1 观察 `read=0x5A PASS`。程序每次复位仅写一次 0x10，并用 ACK polling 等写周期完成。
2. 分析仪 1MHz 采样抓取完整事务；
3. 添加 I2C 解码器，核对：START→0xA0（写地址+W）→ACK→0x10（字地址）→ACK→0x5A→ACK→STOP；
4. 再核对读事务：START→0xA0→ACK→0x10→ACK→**重复 START**→0xA1（读地址+R）→ACK→0x5A→**NACK**→STOP；
5. 换上拉电阻 10kΩ vs 1kΩ 各抓一屏：对比上升沿斜率。

## 预期现象

- 读回值 0x5A；解码与手册时序逐拍吻合；
- 1kΩ 上拉上升沿明显更陡（功耗换速度）。

## 实测记录

| 日期 | 板子 | 观测手段 | 结果 | 备注 |
|---|---|---|---|---|
| | | | | |

## 故障排查

| 症状 | 最可能原因 | 处置 |
|---|---|---|
| 全 NACK | 地址错/没上拉 | 0x50 左移=0xA0；查上拉 |
| 波形全是低 | 总线被拉死 | 查 SDA/SCL 是否短路、器件损坏 |
| 读到 0xFF | 写周期没等够 | EEPROM 写周期 5ms，用 ACK polling |
| 解码错位 | 采样率不足 | ≥10 倍于 SCL（100k→1MHz） |

## 思考题

1. 为什么读事务要"重复 START"而不是 STOP 后再 START？（提示：多主竞争与原子性）
2. NACK 在"主机读最后一字节"时的作用是什么？

## 你做到了

- I2C 从波形到代码全链路打通；
- 抓包对表法毕业；以后遇到任何新协议（1-Wire/自定义），都用这把刀。

## 附录：工程完整源码

构建、接线与排查见[工程 README](https://github.com/zhuguang-ZFG/mcu/tree/main/code/stm32/04-i2c-eeprom)。

<<< ../../code/stm32/04-i2c-eeprom/main.c
