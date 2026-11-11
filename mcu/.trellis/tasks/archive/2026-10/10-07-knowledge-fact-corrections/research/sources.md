# 事实依据

- ST 官方 STM32_open_pin_data 的 mcu/STM32F407Z(E-G)Tx.xml 确认 PA0/TIM2_CH1、PA6/TIM3_CH1；AF 编号由官方 TIM/GPIO 定义核对。缓存 .trellis/ref/f407-pins.xml。此次 datasheet PDF 下载只返回无效内容，没有用该下载件作为证据。
- ST CMSIS stm32f407xx.h 的 IS_TIM_32B_COUNTER_INSTANCE 指定 TIM2/TIM5 为 32 位计数器。
- ST CMSIS stm32f407xx.h：TIM2/TIM3 基址、IRQ 28、APB1 enable bit0/1；USART1 DMA2 Stream5 Channel4 映射。
- FreeRTOS V11.1.0 task.h vTaskSuspendAll 说明：不禁用中断。
- IDF 5.5.2 intr_alloc.rst：普通中断与 IRAM-safe 中断；ota.rst：回滚开关默认关闭与确认 API。

旧 TIM 模型 ARR=999 / last=990 / now=10 得 4294966316，而该次实际间隔为20；同相位跨整周期得0。旧 DMA 首次一个字节写索引1却从索引1读取，实际有效字节在索引0。生产共享函数的宿主断言覆盖修复后的行为。
