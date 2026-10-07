# iap-bootloader —— IAP 串口升级 Bootloader

> 难度：★★★★　｜　涉及外设：USART + Flash　｜　对应章节：[12 Flash 与 IAP 升级](../../docs/12-Flash与IAP升级.md)

<p align="center">
  <img src="../../assets/animations/flash-iap.svg" width="760" alt="IAP 在线升级 Bootloader + APP 双区跳转">
  <br><sub>▲ 动画：IAP 在线升级 Bootloader + APP 双区跳转（作者自绘矢量图）</sub>
</p>

## 一、功能说明

一个最小的 **IAP Bootloader**：上电等待约 500ms，收到 `'U'` 就通过 USART1 接收固件、
写入 Flash 并校验，然后跳转到 APP；否则直接跳 APP。

**帧协议**：`0x5A | len(4B, 小端) | data | checksum(4B, 小端)`。

**Flash 划分**（F103C8T6，64KB）：

| 区域 | 起始地址 | 大小 | 内容 |
| --- | --- | --- | --- |
| Bootloader | `0x0800 0000` | 16KB | 本工程 |
| 参数区 | `0x0800 4000` | 2KB | 升级标志/CRC（本示例未用） |
| APP | `0x0800 4800` | 46KB | 用户应用 |

## 二、硬件接线表

| 开发板 | 外设 | 引脚 | 接法 | 备注 |
| --- | --- | --- | --- | --- |
| BluePill | USB-TTL | PA9 (TX) → 模块 RX | 交叉 | 收固件/打印 |
| BluePill | USB-TTL | PA10 (RX) ← 模块 TX | 交叉 | — |
| BluePill | 共地 | GND ↔ GND | 必须 | — |
| BluePill | LED | PC13 | 板上已接 | 状态指示 |
| BluePill | 调试 | SWDIO/SWCLK | ST-Link | 掉进 Bootloader 也能连 |

## 三、CubeMX 关键配置

| 配置项 | 取值 | 说明 |
| --- | --- | --- |
| USART1 | 115200-8-N-1 | 收固件 |
| RCC → HSE | Crystal | 8MHz |
| SYS → Debug | Serial Wire | 保留 SWD |

> **APP 工程**（不是本工程）需要额外配置：
> - Keil：`Options → Target → IROM1` 起始 `0x08004800`、大小 `0xB800`（46KB）；
> - CubeIDE/GCC：改 `STM32F103C8Tx_FLASH.ld` 里 `FLASH ORIGIN = 0x08004800, LENGTH = 46K`；
> - 并在 `main()` 开头加 `SCB->VTOR = 0x08004800UL;`。

## 四、关键代码解读

**1) 上电选择：升级 or 跳转**

```c
if (uart_wait_for_upgrade(500)) {          /* 500ms 内收到 'U' */
    uart_receive_firmware(APP_ADDR, &size); /* 收包→擦→写→校验 */
}
jump_to_app(APP_ADDR);                       /* 无论成功与否都跳 APP */
```

**2) 按页擦除 + 按半字写入（F1 特性）**

```c
er.TypeErase   = FLASH_TYPEERASE_PAGES;
er.PageAddress = addr;
er.NbPages     = (len + 1024 - 1) / 1024;
HAL_FLASHEx_Erase(&er, &page_err);

/* F1 只支持半字编程，一次写 16 位 */
HAL_FLASH_Program(FLASH_TYPEPROGRAM_HALFWORD, addr + i, half);
```

**3) 跳转前四步（最关键）**

```c
__disable_irq();                 /* ① 关中断 */
SysTick->CTRL = 0;               /*    关 SysTick，避免跳转时被打断 */
HAL_RCC_DeInit(); HAL_DeInit();  /* ② 复位外设 */
__set_MSP(app_stack);            /* ③ 设主栈指针 = 向量表[0] */
SCB->VTOR = app_addr;            /*    设向量表偏移 = APP 基址 */
__enable_irq();                  /* ④ 开中断并跳转 */
((pFunction)app_entry)();        /*    app_entry = 向量表[1] */
```

少了 `SCB->VTOR` 或没设 MSP，APP 里的中断会跳到 Bootloader 的向量表 → 死机。

**4) 校验（累加和，量产建议 CRC32）**

```c
if (checksum32((const uint8_t *)app_addr, fw_len) != csum) return -1;
/* 校验失败保留旧 APP，避免变砖 */
```

## 五、编译烧录步骤

1. 本 Bootloader 工程：Flash 起始保持 `0x08000000`，编译烧录。
2. APP 工程：按上表改链接脚本起始地址，并在 `main()` 开头设 `SCB->VTOR`，编译得到 `.bin`。
3. 用串口工具连接 115200，复位后 500ms 内发送字符 `U`，再发送 `.bin` 文件
   （或自写上位机按帧协议打包：`0x5A + 长度 + 数据 + 校验`）。
4. 升级成功后设备自动跳转运行新 APP。

## 六、预期现象

- 上电后 LED 点亮（Bootloader 运行），500ms 内不操作则跳到 APP；
- 发送 `'U'` 后 LED 保持，接收固件期间可看到数据流；成功后 LED 快闪 3 次；
- 跳转 APP 后，APP 的心跳/串口输出正常。

## 七、常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| 跳转后死机 | 未设 MSP / 未设 VTOR | `__set_MSP` + `SCB->VTOR = APP_ADDR` |
| 中断跳回 Bootloader | 跳转时没关中断 | `__disable_irq()` 并关 SysTick |
| 擦除返回错误 | 地址非页边界 / 未解锁 | 页对齐；`HAL_FLASH_Unlock` |
| 编程后数据错 | 未按半字对齐写 | 地址 2 字节对齐，写 16 位 |
| APP 跑不起来 | 链接脚本起始地址没改 | 改 IROM1/ld 起始到 0x08004800 |
| 校验失败 | 传输丢字节/波特率不符 | 校验波特率与流控，重传 |
| 升级中断电变砖 | 单区无回退 | 用 A/B 双区 + 引导标志 |
| 连不上调试器 | APP 改了 SWD 引脚 | 用「连接下复位」或 BOOT0 拉高 |

## 八、相关资源

- 参考手册 **RM0008** 第 3 章（Embedded Flash，KEY/编程流程）
- 应用笔记 AN2557《STM32F10xxx in-application programming using the USART》
- 《Cortex-M3 权威指南》（向量表、`SCB->VTOR`）
- 相关图：[`assets/animations/flash-iap.svg`](../../assets/animations/flash-iap.svg)
- 免责声明：本示例配图为作者自绘矢量图/程序生成动画，非厂商实拍照片。
