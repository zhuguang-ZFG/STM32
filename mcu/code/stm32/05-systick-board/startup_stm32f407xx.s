/**
 * startup_stm32f407xx.s —— STM32F407ZGT6 启动文件（GNU as 语法）
 *
 * 干四件事：
 *   0. 使能 FPU：复位后 CP10/CP11 默认关闭，硬浮点编译的代码一旦碰到
 *      FPU 指令就是 UsageFault(NOCP) —— 必须最先做（对照 ST 官方
 *      SystemInit 的同款操作：SCB->CPACR |= 0xF<<20）。
 *   1. 提供向量表 g_pfnVectors：第 0 项是初始栈顶，第 1 项是复位入口，
 *      后面依次是 15 个内核异常 + 82 个外设中断（RM0090 §12.2 表 62）。
 *   2. Reset_Handler：使能 FPU，把 .data 初值从 Flash 拷到 RAM，
 *      把 .bss 清零，然后跳进 main —— C 语言的"起跑准备"。
 *   3. 所有中断默认指向 Default_Handler 死循环；谁要用谁在自己的 C
 *      文件里写同名函数，链接器自动覆盖（weak 机制）。
 */

  .syntax unified
  .cpu cortex-m4
  .fpu fpv4-sp-d16
  .thumb

/* 链接脚本提供的边界符号（见 stm32f407xx.ld） */
  .global _estack
  .global _sidata
  .global _sdata
  .global _edata
  .global _sbss
  .global _ebss

/* ------------------------------------------------------------------ */
/* Reset_Handler：上电/复位后执行的第一条代码                            */
/* ------------------------------------------------------------------ */
  .section .text.Reset_Handler
  .weak Reset_Handler
  .type Reset_Handler, %function
Reset_Handler:
  /* 栈顶硬件已按向量表第 0 项装好，这里再装一次无妨（单核裸机） */
  ldr   sp, =_estack

  /* ---- 第 0 步：使能 FPU（CPACR 的 CP10/CP11 全权限） ----
     复位后 FPU 默认关闭；硬浮点编译的代码碰到 FPU 指令即 UsageFault。
     SCB->CPACR 地址 0xE000ED88，bit20~23 置 1（与 ST SystemInit 同款）。 */
  ldr   r0, =0xE000ED88
  ldr   r1, [r0]
  orr   r1, r1, #(0xF << 20)
  str   r1, [r0]
  dsb
  isb
  /* ---- 拷贝 .data：已初始化全局变量，初值存在 Flash(_sidata) ---- */
  ldr   r0, =_sdata        /* RAM 目标起点 */
  ldr   r1, =_edata        /* RAM 目标终点 */
  ldr   r2, =_sidata       /* Flash 源起点 */
  movs  r3, #0
  b     .L_check_copy
.L_copy_loop:
  ldr   r4, [r2, r3]       /* 从 Flash 读一个字 */
  str   r4, [r0, r3]       /* 写到 RAM     */
  adds  r3, r3, #4
.L_check_copy:
  adds  r4, r0, r3
  cmp   r4, r1
  bcc   .L_copy_loop

  /* ---- 清零 .bss：未初始化全局变量 ---- */
  ldr   r2, =_sbss
  ldr   r4, =_ebss
  movs  r3, #0
  b     .L_check_zero
.L_zero_loop:
  str   r3, [r2], #4
.L_check_zero:
  cmp   r2, r4
  bcc   .L_zero_loop

  /* ---- 进 C 世界 ---- */
  bl    main

  /* main 返回（不该发生）：原地转圈等看门狗/调试器 */
.L_hang:
  b     .L_hang
  .size Reset_Handler, .-Reset_Handler

/* ------------------------------------------------------------------ */
/* Default_Handler：所有没实现的中断都掉进来（调试时一眼能抓到）           */
/* ------------------------------------------------------------------ */
  .section .text.Default_Handler,"ax",%progbits
  .type Default_Handler, %function
Default_Handler:
  b     .
  .size Default_Handler, .-Default_Handler

/* ------------------------------------------------------------------ */
/* 向量表：必须在 Flash 起始位置（链接脚本把 .isr_vector 放最前）          */
/* ------------------------------------------------------------------ */
  .section .isr_vector,"a",%progbits
  .type g_pfnVectors, %object
g_pfnVectors:
  .word _estack                    /* 0x00 初始栈顶 MSP            */
  .word Reset_Handler              /* 0x04 复位入口                */
  .word NMI_Handler
  .word HardFault_Handler
  .word MemManage_Handler
  .word BusFault_Handler
  .word UsageFault_Handler
  .word 0
  .word 0
  .word 0
  .word 0
  .word SVC_Handler
  .word DebugMon_Handler
  .word 0
  .word PendSV_Handler
  .word SysTick_Handler

  /* ---- 82 个外设中断（IRQn 0..81，顺序即向量表位置） ---- */
  .word WWDG_IRQHandler                 /*  0 窗口看门狗            */
  .word PVD_IRQHandler                  /*  1 可编程电压检测         */
  .word TAMP_STAMP_IRQHandler           /*  2 侵入/时间戳           */
  .word RTC_WKUP_IRQHandler             /*  3 RTC 唤醒             */
  .word FLASH_IRQHandler                /*  4 Flash 全局            */
  .word RCC_IRQHandler                  /*  5 RCC 全局              */
  .word EXTI0_IRQHandler                /*  6                       */
  .word EXTI1_IRQHandler                /*  7                       */
  .word EXTI2_IRQHandler                /*  8                       */
  .word EXTI3_IRQHandler                /*  9                       */
  .word EXTI4_IRQHandler                /* 10                       */
  .word DMA1_Stream0_IRQHandler         /* 11                       */
  .word DMA1_Stream1_IRQHandler         /* 12                       */
  .word DMA1_Stream2_IRQHandler         /* 13                       */
  .word DMA1_Stream3_IRQHandler         /* 14                       */
  .word DMA1_Stream4_IRQHandler         /* 15                       */
  .word DMA1_Stream5_IRQHandler         /* 16                       */
  .word DMA1_Stream6_IRQHandler         /* 17                       */
  .word ADC_IRQHandler                  /* 18 ADC1/2/3 全局         */
  .word CAN1_TX_IRQHandler              /* 19                       */
  .word CAN1_RX0_IRQHandler             /* 20                       */
  .word CAN1_RX1_IRQHandler             /* 21                       */
  .word CAN1_SCE_IRQHandler             /* 22                       */
  .word EXTI9_5_IRQHandler              /* 23 EXTI5..9              */
  .word TIM1_BRK_TIM9_IRQHandler        /* 24                       */
  .word TIM1_UP_TIM10_IRQHandler        /* 25                       */
  .word TIM1_TRG_COM_TIM11_IRQHandler   /* 26                       */
  .word TIM1_CC_IRQHandler              /* 27                       */
  .word TIM2_IRQHandler                 /* 28                       */
  .word TIM3_IRQHandler                 /* 29                       */
  .word TIM4_IRQHandler                 /* 30                       */
  .word I2C1_EV_IRQHandler              /* 31                       */
  .word I2C1_ER_IRQHandler              /* 32                       */
  .word I2C2_EV_IRQHandler              /* 33                       */
  .word I2C2_ER_IRQHandler              /* 34                       */
  .word SPI1_IRQHandler                 /* 35                       */
  .word SPI2_IRQHandler                 /* 36                       */
  .word USART1_IRQHandler               /* 37                       */
  .word USART2_IRQHandler               /* 38                       */
  .word USART3_IRQHandler               /* 39                       */
  .word EXTI15_10_IRQHandler            /* 40 EXTI10..15            */
  .word RTC_Alarm_IRQHandler            /* 41 闹钟 A/B              */
  .word OTG_FS_WKUP_IRQHandler          /* 42 USB OTG FS 唤醒       */
  .word TIM8_BRK_TIM12_IRQHandler       /* 43                       */
  .word TIM8_UP_TIM13_IRQHandler        /* 44                       */
  .word TIM8_TRG_COM_TIM14_IRQHandler   /* 45                       */
  .word TIM8_CC_IRQHandler              /* 46                       */
  .word DMA1_Stream7_IRQHandler         /* 47                       */
  .word FSMC_IRQHandler                 /* 48                       */
  .word SDIO_IRQHandler                 /* 49                       */
  .word TIM5_IRQHandler                 /* 50                       */
  .word SPI3_IRQHandler                 /* 51                       */
  .word UART4_IRQHandler                /* 52                       */
  .word UART5_IRQHandler                /* 53                       */
  .word TIM6_DAC_IRQHandler             /* 54 TIM6 + DAC 下溢       */
  .word TIM7_IRQHandler                 /* 55                       */
  .word DMA2_Stream0_IRQHandler         /* 56                       */
  .word DMA2_Stream1_IRQHandler         /* 57                       */
  .word DMA2_Stream2_IRQHandler         /* 58                       */
  .word DMA2_Stream3_IRQHandler         /* 59                       */
  .word ETH_IRQHandler                  /* 60 以太网                */
  .word ETH_WKUP_IRQHandler             /* 61                       */
  .word CAN2_TX_IRQHandler              /* 62                       */
  .word CAN2_RX0_IRQHandler             /* 63                       */
  .word CAN2_RX1_IRQHandler             /* 64                       */
  .word CAN2_SCE_IRQHandler             /* 65                       */
  .word OTG_FS_IRQHandler               /* 66 USB OTG FS 全局       */
  .word DMA2_Stream4_IRQHandler         /* 67                       */
  .word DMA2_Stream5_IRQHandler         /* 68                       */
  .word DMA2_Stream6_IRQHandler         /* 69                       */
  .word DMA2_Stream7_IRQHandler         /* 70                       */
  .word USART6_IRQHandler               /* 71                       */
  .word I2C3_EV_IRQHandler              /* 72                       */
  .word I2C3_ER_IRQHandler              /* 73                       */
  .word OTG_HS_EP1_OUT_IRQHandler       /* 74                       */
  .word OTG_HS_EP1_IN_IRQHandler        /* 75                       */
  .word OTG_HS_WKUP_IRQHandler          /* 76                       */
  .word OTG_HS_IRQHandler               /* 77 USB OTG HS 全局       */
  .word DCMI_IRQHandler                 /* 78 摄像头接口            */
  .word CRYP_IRQHandler                 /* 79 加密                  */
  .word HASH_RNG_IRQHandler             /* 80 哈希 + 随机数         */
  .word FPU_IRQHandler                  /* 81 FPU 全局              */
  .size g_pfnVectors, .-g_pfnVectors

/* ------------------------------------------------------------------ */
/* weak 默认别名：C 里写了同名函数就自动顶替 Default_Handler              */
/* ------------------------------------------------------------------ */
  .macro IRQ_DEFAULT name
  .weak \name
  .thumb_set \name, Default_Handler
  .endm

  IRQ_DEFAULT NMI_Handler
  IRQ_DEFAULT HardFault_Handler
  IRQ_DEFAULT MemManage_Handler
  IRQ_DEFAULT BusFault_Handler
  IRQ_DEFAULT UsageFault_Handler
  IRQ_DEFAULT SVC_Handler
  IRQ_DEFAULT DebugMon_Handler
  IRQ_DEFAULT PendSV_Handler
  IRQ_DEFAULT SysTick_Handler
  IRQ_DEFAULT WWDG_IRQHandler
  IRQ_DEFAULT PVD_IRQHandler
  IRQ_DEFAULT TAMP_STAMP_IRQHandler
  IRQ_DEFAULT RTC_WKUP_IRQHandler
  IRQ_DEFAULT FLASH_IRQHandler
  IRQ_DEFAULT RCC_IRQHandler
  IRQ_DEFAULT EXTI0_IRQHandler
  IRQ_DEFAULT EXTI1_IRQHandler
  IRQ_DEFAULT EXTI2_IRQHandler
  IRQ_DEFAULT EXTI3_IRQHandler
  IRQ_DEFAULT EXTI4_IRQHandler
  IRQ_DEFAULT DMA1_Stream0_IRQHandler
  IRQ_DEFAULT DMA1_Stream1_IRQHandler
  IRQ_DEFAULT DMA1_Stream2_IRQHandler
  IRQ_DEFAULT DMA1_Stream3_IRQHandler
  IRQ_DEFAULT DMA1_Stream4_IRQHandler
  IRQ_DEFAULT DMA1_Stream5_IRQHandler
  IRQ_DEFAULT DMA1_Stream6_IRQHandler
  IRQ_DEFAULT ADC_IRQHandler
  IRQ_DEFAULT CAN1_TX_IRQHandler
  IRQ_DEFAULT CAN1_RX0_IRQHandler
  IRQ_DEFAULT CAN1_RX1_IRQHandler
  IRQ_DEFAULT CAN1_SCE_IRQHandler
  IRQ_DEFAULT EXTI9_5_IRQHandler
  IRQ_DEFAULT TIM1_BRK_TIM9_IRQHandler
  IRQ_DEFAULT TIM1_UP_TIM10_IRQHandler
  IRQ_DEFAULT TIM1_TRG_COM_TIM11_IRQHandler
  IRQ_DEFAULT TIM1_CC_IRQHandler
  IRQ_DEFAULT TIM2_IRQHandler
  IRQ_DEFAULT TIM3_IRQHandler
  IRQ_DEFAULT TIM4_IRQHandler
  IRQ_DEFAULT I2C1_EV_IRQHandler
  IRQ_DEFAULT I2C1_ER_IRQHandler
  IRQ_DEFAULT I2C2_EV_IRQHandler
  IRQ_DEFAULT I2C2_ER_IRQHandler
  IRQ_DEFAULT SPI1_IRQHandler
  IRQ_DEFAULT SPI2_IRQHandler
  IRQ_DEFAULT USART1_IRQHandler
  IRQ_DEFAULT USART2_IRQHandler
  IRQ_DEFAULT USART3_IRQHandler
  IRQ_DEFAULT EXTI15_10_IRQHandler
  IRQ_DEFAULT RTC_Alarm_IRQHandler
  IRQ_DEFAULT OTG_FS_WKUP_IRQHandler
  IRQ_DEFAULT TIM8_BRK_TIM12_IRQHandler
  IRQ_DEFAULT TIM8_UP_TIM13_IRQHandler
  IRQ_DEFAULT TIM8_TRG_COM_TIM14_IRQHandler
  IRQ_DEFAULT TIM8_CC_IRQHandler
  IRQ_DEFAULT DMA1_Stream7_IRQHandler
  IRQ_DEFAULT FSMC_IRQHandler
  IRQ_DEFAULT SDIO_IRQHandler
  IRQ_DEFAULT TIM5_IRQHandler
  IRQ_DEFAULT SPI3_IRQHandler
  IRQ_DEFAULT UART4_IRQHandler
  IRQ_DEFAULT UART5_IRQHandler
  IRQ_DEFAULT TIM6_DAC_IRQHandler
  IRQ_DEFAULT TIM7_IRQHandler
  IRQ_DEFAULT DMA2_Stream0_IRQHandler
  IRQ_DEFAULT DMA2_Stream1_IRQHandler
  IRQ_DEFAULT DMA2_Stream2_IRQHandler
  IRQ_DEFAULT DMA2_Stream3_IRQHandler
  IRQ_DEFAULT ETH_IRQHandler
  IRQ_DEFAULT ETH_WKUP_IRQHandler
  IRQ_DEFAULT CAN2_TX_IRQHandler
  IRQ_DEFAULT CAN2_RX0_IRQHandler
  IRQ_DEFAULT CAN2_RX1_IRQHandler
  IRQ_DEFAULT CAN2_SCE_IRQHandler
  IRQ_DEFAULT OTG_FS_IRQHandler
  IRQ_DEFAULT DMA2_Stream4_IRQHandler
  IRQ_DEFAULT DMA2_Stream5_IRQHandler
  IRQ_DEFAULT DMA2_Stream6_IRQHandler
  IRQ_DEFAULT DMA2_Stream7_IRQHandler
  IRQ_DEFAULT USART6_IRQHandler
  IRQ_DEFAULT I2C3_EV_IRQHandler
  IRQ_DEFAULT I2C3_ER_IRQHandler
  IRQ_DEFAULT OTG_HS_EP1_OUT_IRQHandler
  IRQ_DEFAULT OTG_HS_EP1_IN_IRQHandler
  IRQ_DEFAULT OTG_HS_WKUP_IRQHandler
  IRQ_DEFAULT OTG_HS_IRQHandler
  IRQ_DEFAULT DCMI_IRQHandler
  IRQ_DEFAULT CRYP_IRQHandler
  IRQ_DEFAULT HASH_RNG_IRQHandler
  IRQ_DEFAULT FPU_IRQHandler
