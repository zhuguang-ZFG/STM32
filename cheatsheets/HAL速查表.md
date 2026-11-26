# HAL 速查表

> 常用 HAL 库函数按模块分类。列含义：**函数原型 / 作用 / 常用参数 / 返回值与错误码**。
> 返回值统一为 `HAL_StatusTypeDef`：`HAL_OK` / `HAL_ERROR` / `HAL_BUSY` / `HAL_TIMEOUT`（详见[错误码与排查速查表](错误码与排查速查表.md)）。
> 以 STM32F1 HAL 为准；F4 差异在备注中标注。

## 目录

| 模块 | 跳转 |
| --- | --- |
| 系统与时钟 | [§1](#1-系统与时钟hal--rcc) |
| GPIO | [§2](#2-gpiogpio) |
| EXTI / NVIC | [§3](#3-中断extinvicsystick) |
| 定时器 TIM | [§4](#4-定时器tim) |
| 串口 UART | [§5](#5-串口usartuart) |
| SPI | [§6](#6-spispi) |
| I2C | [§7](#7-i2ci2c) |
| ADC / DAC | [§8](#8-adcdacadcdac) |
| DMA | [§9](#9-dmadma) |
| RTC / 备份域 | [§10](#10-rtc与备份域rtcrtc_expwr) |
| Flash / IAP | [§11](#11-flashflashflash_ex) |
| 看门狗 | [§12](#12-看门狗iwdgwwdg) |
| FreeRTOS 常用宏 | [§13](#13-freertos-常用宏) |

## 1. 系统与时钟（HAL / RCC）

| 函数原型 | 作用 | 常用参数 | 返回值/错误码 |
| --- | --- | --- | --- |
| `HAL_Init(void)` | 初始化 HAL、Flash 接口、SysTick(1ms) | 无 | `HAL_OK` |
| `HAL_DeInit(void)` | 复位所有外设到默认状态 | 无 | `HAL_OK` |
| `HAL_Delay(uint32_t ms)` | 阻塞延时（基于 SysTick 中断） | 毫秒数 | 无（void） |
| `HAL_GetTick(void)` | 获取自启动以来的毫秒数 | 无 | 当前 tick 值 |
| `HAL_IncTick(void)` | 由 SysTick_Handler 调用，累加 tick | 无 | 无（勿手动调） |
| `HAL_RCC_OscConfig(RCC_OscInitTypeDef*)` | 配置 HSE/HSI/LSE/LSI/PLL | `OscillatorType`,`HSEState`,`PLL.PLLMUL` | `HAL_OK/ERROR/TIMEOUT`（HSE 不起振返回 ERROR） |
| `HAL_RCC_ClockConfig(RCC_ClkInitTypeDef*, uint32_t lat)` | 配置 SYSCLK/AHB/APB 分频 | `SYSCLKSource`,`AHBCLKDivider`,`APB1CLKDivider` | `HAL_OK/ERROR`（超频会 ERROR） |
| `HAL_RCCEx_PeriphCLKConfig(RCC_PeriphCLKInitTypeDef*)` | 配置 ADC/RTC/USB 等外设时钟 | `PeriphClockSelection`,`AdcClockSelection` | `HAL_OK/ERROR` |
| `HAL_RCC_GetHCLKFreq(void)` | 读当前 AHB 频率 | 无 | Hz |
| `HAL_RCC_GetPCLK1Freq(void)` | 读当前 APB1 频率 | 无 | Hz |

## 2. GPIO（GPIO）

| 函数原型 | 作用 | 常用参数 | 返回值/错误码 |
| --- | --- | --- | --- |
| `HAL_GPIO_Init(GPIO_TypeDef*, GPIO_InitTypeDef*)` | 初始化引脚（模式/上下拉/速度） | `Pin`,`Mode`,`Pull`,`Speed`,`Alternate`(F4) | 无（void） |
| `HAL_GPIO_DeInit(GPIO_TypeDef*, uint32_t Pin)` | 复位引脚到默认 | `Pin` | 无 |
| `HAL_GPIO_WritePin(GPIOx, uint16_t Pin, GPIO_PinState st)` | 写引脚电平 | `GPIO_PIN_SET/RESET` | 无 |
| `HAL_GPIO_ReadPin(GPIOx, uint16_t Pin)` | 读引脚电平 | `Pin` | `GPIO_PIN_SET/RESET` |
| `HAL_GPIO_TogglePin(GPIOx, uint16_t Pin)` | 翻转引脚 | `Pin` | 无 |
| `HAL_GPIO_LockPin(GPIOx, uint16_t Pin)` | 锁定引脚配置 | `Pin` | `HAL_OK` |
| `HAL_GPIO_EXTI_IRQHandler(uint16_t Pin)` | EXTI 中断处理（清标志+回调） | `Pin` | 无 |

**常用宏**：`GPIO_MODE_INPUT/OUTPUT_PP/OUTPUT_OD/ANALOG/AF_PP/AF_OD/IT_RISING/IT_FALLING/IT_RISING_FALLING`、
`GPIO_PULLUP/PULLDOWN/NOPULL`、`GPIO_SPEED_FREQ_LOW/MEDIUM/HIGH/VERY_HIGH`。

## 3. 中断（EXTI / NVIC / SysTick）

| 函数原型 | 作用 | 常用参数 | 返回值/错误码 |
| --- | --- | --- | --- |
| `HAL_NVIC_SetPriority(IRQn_Type, uint32_t pre, uint32_t sub)` | 设抢占/子优先级 | `IRQn`,`pre`,`sub`（数值越小越优先） | 无 |
| `HAL_NVIC_EnableIRQ(IRQn_Type)` | 使能某中断线 | `IRQn` | 无 |
| `HAL_NVIC_DisableIRQ(IRQn_Type)` | 关闭某中断线 | `IRQn` | 无 |
| `HAL_NVIC_SetPriorityGrouping(uint32_t g)` | 设置优先级分组 | `NVIC_PRIORITYGROUP_0..4` | 无 |
| `HAL_NVIC_SystemReset(void)` | 系统复位 | 无 | 不返回 |
| `__disable_irq()/__enable_irq()` | 关/开全局中断（临界区） | 无 | 无 |
| `__HAL_GPIO_EXTI_GET_IT(Pin)` | 读 EXTI 挂起标志 | `Pin` | 非 0=有事件 |
| `__HAL_GPIO_EXTI_CLEAR_IT(Pin)` | 清 EXTI 挂起标志 | `Pin` | 无 |
| `HAL_SuspendTick()/HAL_ResumeTick()` | 挂起/恢复 SysTick | 无 | 无 |

## 4. 定时器（TIM）

| 函数原型 | 作用 | 常用参数 | 返回值/错误码 |
| --- | --- | --- | --- |
| `HAL_TIM_Base_Init(TIM_HandleTypeDef*)` | 初始化时基（PSC/ARR） | `Init.Prescaler`,`Init.Period` | `HAL_OK/ERROR` |
| `HAL_TIM_Base_Start(TIM_HandleTypeDef*)` | 启动计数（查询） | — | `HAL_OK/BUSY` |
| `HAL_TIM_Base_Start_IT(TIM_HandleTypeDef*)` | 启动计数 + 更新中断 | — | `HAL_OK/BUSY` |
| `HAL_TIM_PWM_Init(TIM_HandleTypeDef*)` | 初始化 PWM 时基 | 同 Base | `HAL_OK/ERROR` |
| `HAL_TIM_PWM_ConfigChannel(TIM*, TIM_OC_InitTypeDef*, uint32_t ch)` | 配置 PWM 通道 | `OCMode`,`Pulse`,`OCPolarity` | `HAL_OK/ERROR` |
| `HAL_TIM_PWM_Start(TIM*, uint32_t ch)` | 启动 PWM 输出（含 MOE） | `TIM_CHANNEL_x` | `HAL_OK/BUSY/ERROR` |
| `HAL_TIM_PWM_Stop(TIM*, uint32_t ch)` | 停止 PWM | `ch` | `HAL_OK/ERROR` |
| `HAL_TIM_IC_Start_IT(TIM*, uint32_t ch)` | 启动输入捕获 + 中断 | `ch` | `HAL_OK/BUSY` |
| `HAL_TIM_OC_Start(TIM*, uint32_t ch)` | 启动输出比较 | `ch` | `HAL_OK/BUSY` |

**常用宏**：`__HAL_TIM_SET_COMPARE(&h,ch,ccr)`、`__HAL_TIM_GET_COMPARE(&h,ch)`、
`__HAL_TIM_SET_COUNTER`、`__HAL_TIM_GET_COUNTER`、`__HAL_TIM_MOE_ENABLE(&h)`（高级定时器）、
`__HAL_TIM_SET_AUTORELOAD`、`TIM_OCMODE_PWM1/PWM2`、`TIM_OCPOLARITY_HIGH/LOW`。

## 5. 串口 USART（UART）

| 函数原型 | 作用 | 常用参数 | 返回值/错误码 |
| --- | --- | --- | --- |
| `HAL_UART_Init(UART_HandleTypeDef*)` | 初始化 UART | `BaudRate`,`WordLength`,`StopBits`,`Parity` | `HAL_OK/ERROR` |
| `HAL_UART_Transmit(UART*, uint8_t*, uint16_t, uint32_t to)` | 阻塞发送 | `buf`,`len`,`timeout` | `HAL_OK/BUSY/TIMEOUT/ERROR` |
| `HAL_UART_Receive(UART*, uint8_t*, uint16_t, uint32_t to)` | 阻塞接收 | `buf`,`len`,`timeout` | `HAL_OK/BUSY/TIMEOUT/ERROR` |
| `HAL_UART_Transmit_IT / Receive_IT` | 中断方式收发 | 同上（无 timeout） | `HAL_OK/BUSY/ERROR` |
| `HAL_UART_Transmit_DMA / Receive_DMA` | DMA 方式收发 | 同上（无 timeout） | `HAL_OK/BUSY/ERROR` |
| `HAL_UARTEx_ReceiveToIdle_DMA(UART*, uint8_t*, uint16_t)` | DMA+空闲中断不定长接收 | `buf`,`len` | `HAL_OK/BUSY/ERROR` |
| `HAL_UART_IRQHandler(UART*)` | 中断统一入口（放 `USARTx_IRQHandler`） | — | 无 |
| `HAL_UART_Abort(UART*)` | 中止收发并复位状态 | — | `HAL_OK/ERROR` |
| `__HAL_UART_CLEAR_OREFLAG(UART*)` | 清溢出标志 | — | 无 |
| `__HAL_UART_CLEAR_FEFLAG(UART*)` | 清帧错误标志 | — | 无 |

**回调**：`HAL_UART_RxCpltCallback`、`HAL_UART_TxCpltCallback`、`HAL_UARTEx_RxEventCallback`、`HAL_UART_ErrorCallback`。

## 6. SPI（SPI）

| 函数原型 | 作用 | 常用参数 | 返回值/错误码 |
| --- | --- | --- | --- |
| `HAL_SPI_Init(SPI_HandleTypeDef*)` | 初始化 SPI | `Mode`,`CLKPolarity`,`CLKPhase`,`NSS`,`BaudRatePrescaler` | `HAL_OK/ERROR` |
| `HAL_SPI_Transmit(SPI*, uint8_t*, uint16_t, uint32_t)` | 阻塞发送 | `buf`,`len`,`timeout` | `HAL_OK/BUSY/TIMEOUT/ERROR` |
| `HAL_SPI_Receive(SPI*, uint8_t*, uint16_t, uint32_t)` | 阻塞接收 | 同上 | 同上 |
| `HAL_SPI_TransmitReceive(SPI*, uint8_t*, uint8_t*, uint16_t, uint32_t)` | 全双工收发 | `tx`,`rx`,`len`,`timeout` | 同上 |
| `HAL_SPI_Transmit_IT / TransmitReceive_IT` | 中断方式 | 同阻塞（无 timeout） | `HAL_OK/BUSY/ERROR` |
| `HAL_SPI_TransmitReceive_DMA(SPI*, uint8_t*, uint8_t*, uint16_t)` | DMA 全双工 | `tx`,`rx`,`len` | `HAL_OK/BUSY/ERROR` |

**常用宏**：`SPI_MODE_MASTER/SLAVE`、`SPI_POLARITY_LOW/HIGH`、`SPI_PHASE_1EDGE/2EDGE`、
`SPI_NSS_SOFT/HARD`、`SPI_BAUDRATEPRESCALER_2..256`、`SPI_FIRSTBIT_MSB/LSB`、`SPI_DATASIZE_8BIT/16BIT`。
**模式对应**：模式0=CPOL0+CPHA0；模式1=CPOL0+CPHA1；模式2=CPOL1+CPHA0；模式3=CPOL1+CPHA1。

## 7. I2C（I2C）

| 函数原型 | 作用 | 常用参数 | 返回值/错误码 |
| --- | --- | --- | --- |
| `HAL_I2C_Init(I2C_HandleTypeDef*)` | 初始化 I2C | `ClockSpeed`,`DutyCycle`,`AddressingMode` | `HAL_OK/ERROR` |
| `HAL_I2C_Master_Transmit(I2C*, uint16_t addr, uint8_t*, uint16_t, uint32_t)` | 主机发送 | `addr`(8位,已左移),`buf`,`len`,`timeout` | `HAL_OK/BUSY/TIMEOUT/ERROR` |
| `HAL_I2C_Master_Receive(I2C*, uint16_t, uint8_t*, uint16_t, uint32_t)` | 主机接收 | 同上 | 同上 |
| `HAL_I2C_Mem_Write(I2C*, addr, memaddr, memsize, buf, len, to)` | 写寄存器 | `MemAddress`,`MemAddSize` | 同上 |
| `HAL_I2C_Mem_Read(I2C*, addr, memaddr, memsize, buf, len, to)` | 读寄存器 | 同上 | 同上 |
| `HAL_I2C_IsDeviceReady(I2C*, addr, trials, to)` | 探测从机是否应答 | `Trials`,`Timeout` | `HAL_OK/BUSY/TIMEOUT/ERROR` |
| `HAL_I2C_Master_Transmit_DMA(...)` | DMA 方式发送 | 同阻塞（无 timeout） | `HAL_OK/BUSY/ERROR` |
| `HAL_I2C_DeInit(I2C*)` | 复位 I2C（总线恢复时用） | — | `HAL_OK` |

**常用宏**：`I2C_ADDRESSINGMODE_7BIT/10BIT`、`I2C_DUTYCYCLE_2/16_9`、`I2C_DUALADDRESS_DISABLE/ENABLE`、`I2C_NOSTRETCH_DISABLE/ENABLE`。

## 8. ADC/DAC（ADC/DAC）

| 函数原型 | 作用 | 常用参数 | 返回值/错误码 |
| --- | --- | --- | --- |
| `HAL_ADC_Init(ADC_HandleTypeDef*)` | 初始化 ADC | `ScanConvMode`,`ContinuousConvMode`,`DataAlign`,`NbrOfConversion` | `HAL_OK/ERROR` |
| `HAL_ADC_ConfigChannel(ADC*, ADC_ChannelConfTypeDef*)` | 配置规则组通道 | `Channel`,`Rank`,`SamplingTime` | `HAL_OK/ERROR` |
| `HAL_ADCEx_Calibration_Start(ADC*)` | ADC 校准（上电必做） | — | `HAL_OK/ERROR` |
| `HAL_ADC_Start(ADC*)` | 启动转换（查询） | — | `HAL_OK/BUSY` |
| `HAL_ADC_Start_DMA(ADC*, uint32_t*, uint32_t)` | 启动 + DMA | `buf`,`len` | `HAL_OK/BUSY/ERROR` |
| `HAL_ADC_PollForConversion(ADC*, uint32_t to)` | 轮询等待转换完成 | `timeout` | `HAL_OK/TIMEOUT/ERROR` |
| `HAL_ADC_GetValue(ADC*)` | 读转换结果 | — | 12 位码值 |
| `HAL_ADC_Stop_DMA(ADC*)` | 停止 DMA 采集 | — | `HAL_OK/ERROR` |
| `HAL_DAC_Start(DAC_HandleTypeDef*, uint32_t ch)` | 启动 DAC 输出 | `DAC_CHANNEL_1/2` | `HAL_OK/ERROR` |
| `HAL_DAC_SetValue(DAC*, ch, align, value)` | 设置输出值 | `DAC_ALIGN_12B_R`,`0..4095` | `HAL_OK/ERROR` |
| `HAL_DAC_Start_DMA(DAC*, ch, buf, len, align)` | DMA 更新（任意波形） | `buf`,`len` | `HAL_OK/ERROR` |

**常用宏**：`ADC_SAMPLETIME_1CYCLE_5 ... _239CYCLES_5`、`ADC_CHANNEL_0..17`、
`ADC_DATAALIGN_RIGHT/LEFT`、`ADC_EXTERNALTRIGCONV_Tx_TRGO`、`ADC_SOFTWARE_START`。

## 9. DMA（DMA）

| 函数原型 | 作用 | 常用参数 | 返回值/错误码 |
| --- | --- | --- | --- |
| `HAL_DMA_Init(DMA_HandleTypeDef*)` | 初始化 DMA 通道/流 | `Direction`,`PeriphInc`,`MemInc`,`Mode`,`Priority` | `HAL_OK/ERROR` |
| `HAL_DMA_Start(DMA*, uint32_t src, uint32_t dst, uint32_t len)` | 启动一次传输 | `src`,`dst`,`len` | `HAL_OK/ERROR` |
| `HAL_DMA_Start_IT(DMA*, src, dst, len)` | 启动 + 中断 | 同上 | `HAL_OK/ERROR` |
| `HAL_DMA_PollForTransfer(DMA*, level, uint32_t to)` | 轮询等待完成 | `HAL_DMA_FULL_TRANSFER`,`timeout` | `HAL_OK/TIMEOUT/ERROR` |
| `HAL_DMA_Abort(DMA*)` | 中止传输 | — | `HAL_OK/ERROR` |
| `__HAL_LINKDMA(handle, field, dma_handle)` | 把 DMA 关联到外设句柄 | `field`=`hdmatx/hdmarx` | 无 |

**常用宏**：`DMA_MEMORY_TO_PERIPH/PERIPH_TO_MEMORY/MEMORY_TO_MEMORY`、`DMA_PINC_ENABLE/DISABLE`、
`DMA_MINC_ENABLE/DISABLE`、`DMA_NORMAL/CIRCULAR`、`DMA_PRIORITY_LOW..VERY_HIGH`、
`DMA_PDATAALIGN_BYTE/HALFWORD/WORD`、`DMA_MDATAALIGN_*`。


## 10. RTC 与备份域（RTC / RTC_EX / PWR）

| 函数原型 | 作用 | 常用参数 | 返回值/错误码 |
| --- | --- | --- | --- |
| `HAL_RTC_Init(RTC_HandleTypeDef*)` | 初始化 RTC | `AsynchPrediv`,`OutPut` | `HAL_OK/ERROR` |
| `HAL_RTC_SetTime/GetTime(RTC*, RTC_TimeTypeDef*, fmt)` | 设置/读取时间 | `RTC_FORMAT_BIN/BCD` | `HAL_OK/ERROR` |
| `HAL_RTC_SetDate/GetDate(RTC*, RTC_DateTypeDef*, fmt)` | 设置/读取日期 | 同上 | `HAL_OK/ERROR` |
| `HAL_RTC_SetAlarm_IT(RTC*, RTC_AlarmTypeDef*, fmt)` | 设置闹钟（中断） | `AlarmTime`,`AlarmMask` | `HAL_OK/ERROR` |
| `HAL_RTC_DeactivateAlarm(RTC*, uint32_t)` | 关闭闹钟 | `RTC_ALARM_A/B` | `HAL_OK/ERROR` |
| `HAL_RTCEx_BKUPWrite(RTC*, uint32_t reg, uint32_t val)` | 写备份寄存器 | `RTC_BKP_DRx` | 无 |
| `HAL_RTCEx_BKUPRead(RTC*, uint32_t reg)` | 读备份寄存器 | `RTC_BKP_DRx` | 寄存器值 |
| `HAL_PWR_EnableBkUpAccess(void)` | 解锁备份域（写 RTC/BKP 前） | 无 | 无 |
| `HAL_PWR_EnterSTOPMode(uint32_t reg, uint32_t entry)` | 进入 STOP 模式 | `PWR_LOWPOWERREGULATOR_ON`,`PWR_STOPENTRY_WFI` | 无 |

**回调**：`HAL_RTC_AlarmAEventCallback`、`HAL_RTC_AlarmBEventCallback`、`HAL_RTCEx_WakeUpTimerEventCallback`（F4）。

## 11. Flash（FLASH / FLASH_EX）

| 函数原型 | 作用 | 常用参数 | 返回值/错误码 |
| --- | --- | --- | --- |
| `HAL_FLASH_Unlock(void)` | 解锁 Flash（KEY1/KEY2） | 无 | `HAL_OK/ERROR` |
| `HAL_FLASH_Lock(void)` | 上锁 Flash | 无 | `HAL_OK/ERROR` |
| `HAL_FLASHEx_Erase(FLASH_EraseInitTypeDef*, uint32_t* err)` | 擦除页/扇区 | `TypeErase`,`PageAddress`,`NbPages` | `HAL_OK/ERROR/TIMEOUT` |
| `HAL_FLASH_Program(uint32_t type, uint32_t addr, uint64_t data)` | 编程 | `FLASH_TYPEPROGRAM_HALFWORD/WORD/DOUBLEWORD` | `HAL_OK/ERROR/BUSY` |
| `HAL_FLASHEx_OBProgram(FLASH_OBProgramInitTypeDef*)` | 编程选项字节 | — | `HAL_OK/ERROR` |
| `HAL_FLASH_GetError(void)` | 读错误标志 | — | 位掩码 |

**F1**：擦除以「页」为单位（小容量 1KB、大容量 2KB），编程以「半字」为单位；
**F4**：擦除以「扇区」为单位（16/64/128KB），编程支持字节/半字/字/双字。

## 12. 看门狗（IWDG / WWDG）

| 函数原型 | 作用 | 常用参数 | 返回值/错误码 |
| --- | --- | --- | --- |
| `HAL_IWDG_Init(IWDG_HandleTypeDef*)` | 初始化独立看门狗 | `Prescaler`,`Reload` | `HAL_OK/ERROR` |
| `HAL_IWDG_Refresh(IWDG*)` | 喂狗 | — | `HAL_OK/ERROR` |
| `HAL_WWDG_Init(WWDG_HandleTypeDef*)` | 初始化窗口看门狗 | `Prescaler`,`Window`,`Counter` | `HAL_OK/ERROR` |
| `HAL_WWDG_Refresh(WWDG*)` | 喂狗（须在窗口内） | — | `HAL_OK/ERROR` |

**常用宏**：`IWDG_PRESCALER_4..256`、`WWDG_PRESCALER_1..8`、`WWDG_EWI_ENABLE/DISABLE`。

## 13. FreeRTOS 常用宏

| 宏/函数 | 作用 | 常用参数 | 说明 |
| --- | --- | --- | --- |
| `xTaskCreate(fn, name, stack, arg, prio, handle)` | 创建任务 | `stack`单位为字(4B) | 返回 `pdPASS/pdFAIL` |
| `vTaskDelete(handle)` | 删除任务 | `NULL`=删自己 | 无返回 |
| `vTaskDelay(ticks)` | 阻塞延时 | `pdMS_TO_TICKS(ms)` | 让出 CPU |
| `xTaskGetTickCount()` | 获取节拍数 | 无 | 返回 TickType_t |
| `xQueueCreate(len, item_size)` | 创建队列 | `len`,`item_size` | 返回句柄或 NULL |
| `xQueueSend/Receive(q, &item, ticks)` | 队列收发 | `portMAX_DELAY`=永久等待 | `pdTRUE/pdFALSE` |
| `xQueueSendFromISR(q, &item, &woken)` | 中断中发送 | `woken`=是否唤醒任务 | `pdTRUE/pdFALSE` |
| `xSemaphoreCreateMutex/Binary()` | 创建互斥/二值信号量 | — | 返回句柄 |
| `xSemaphoreTake/Give(sem, ticks)` | 获取/释放信号量 | `ticks` | `pdTRUE/pdFALSE` |
| `xSemaphoreGiveFromISR(sem, &woken)` | 中断中释放 | `woken` | `pdTRUE/pdFALSE` |
| `portYIELD_FROM_ISR(woken)` | 中断末尾触发切换 | `woken` | 无 |
| `pdMS_TO_TICKS(ms)` | 毫秒→tick 换算 | `ms` | 依 `configTICK_RATE_HZ` |
| `configASSERT(x)` | 断言（优先级/参数检查） | 条件 | 失败进死循环 |
| `taskENTER_CRITICAL()/EXIT()` | 任务级临界区 | 无 | 关中断保护 |

> 相关：[寄存器速查表](寄存器速查表.md) · [外设总线与引脚速查表](外设总线与引脚速查表.md) · [错误码与排查速查表](错误码与排查速查表.md)

