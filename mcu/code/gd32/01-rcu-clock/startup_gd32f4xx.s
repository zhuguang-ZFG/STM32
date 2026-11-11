/**
 * startup_gd32f4xx.s —— GD32F4xx 最小启动文件（G1 工程）
 *
 * 向量表布局：16 个内核槽 + 82 个外设槽（IRQn 0..81，FPU_IRQn=81，
 * gd32f4xx.h IRQn_Type @10d02f4）。全部弱符号，应用可同名覆盖。
 * 复位流程：取 SP → 拷贝 .data → 清零 .bss → main。
 */
    .syntax unified
    .cpu cortex-m4
    .thumb

    .global __StackTop
    .global Reset_Handler

    .section .isr_vector,"a",%progbits
    .word __StackTop
    .word Reset_Handler
    .word NMI_Handler
    .word HardFault_Handler
    .word MemManage_Handler
    .word BusFault_Handler
    .word UsageFault_Handler
    .word 0, 0, 0, 0
    .word SVC_Handler
    .word DebugMon_Handler
    .word 0
    .word PendSV_Handler
    .word SysTick_Handler

    /* 外设向量 82 个：统一弱符号，名字对调试友好即可（G1 不挂中断） */
    .rept 82
    .word Default_IRQHandler
    .endr

    .section .text.Reset_Handler,"ax",%progbits
    .type Reset_Handler, %function
    .thumb_func
Reset_Handler:
    /* Cortex-M4 hard-float ABI：先开放 CP10/CP11，避免首条浮点指令 NOCP。 */
    ldr r0, =0xE000ED88
    ldr r1, [r0]
    orr r1, r1, #(0xf << 20)
    str r1, [r0]
    dsb
    isb
    ldr r0, =__data_load__
    ldr r1, =__data_start__
    ldr r2, =__data_end__
copy_data:
    cmp r1, r2
    bcc copy_data_word
    b zero_bss_start
copy_data_word:
    ldr r3, [r0], #4
    str r3, [r1], #4
    b copy_data
zero_bss_start:
    ldr r1, =__bss_start__
    ldr r2, =__bss_end__
    movs r3, #0
zero_bss:
    cmp r1, r2
    bcc zero_bss_word
    b enter_main
zero_bss_word:
    str r3, [r1], #4
    b zero_bss
enter_main:
    bl main
    b .

    .section .text.Default_Handler,"ax",%progbits
    .weak Default_IRQHandler, NMI_Handler, HardFault_Handler, MemManage_Handler
    .weak BusFault_Handler, UsageFault_Handler, SVC_Handler, DebugMon_Handler
    .weak PendSV_Handler, SysTick_Handler
    .thumb_func
Default_IRQHandler:
    b .
    .thumb_func
NMI_Handler:
    b .
    .thumb_func
HardFault_Handler:
    b .
    .thumb_func
MemManage_Handler:
    b .
    .thumb_func
BusFault_Handler:
    b .
    .thumb_func
UsageFault_Handler:
    b .
    .thumb_func
SVC_Handler:
    b .
    .thumb_func
DebugMon_Handler:
    b .
    .thumb_func
PendSV_Handler:
    b .
    .thumb_func
SysTick_Handler:
    b .

    .section .note.GNU-stack,"",%progbits
