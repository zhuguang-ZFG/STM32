/**
 * gd32f4xx.ld —— GD32F450 最小链接脚本（G1 工程）
 *
 * 容量依据：GD32F450ZG = 1MB Flash + 256KB SRAM（产品选型表口径，
 * **待 UM 核验**；上板前请与所用料号核对，溢出不会编译报错只会运行踩雷）。
 * 内存映射与 STM32F4 一致：Flash 0x08000000，SRAM 0x20000000。
 */
MEMORY
{
    FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 1024K
    RAM (rwx)   : ORIGIN = 0x20000000, LENGTH = 256K
}

ENTRY(Reset_Handler)

__StackTop = ORIGIN(RAM) + LENGTH(RAM);

SECTIONS
{
    .text :
    {
        KEEP(*(.isr_vector))
        *(.text*)
        *(.rodata*)
        KEEP(*(.init))
        KEEP(*(.fini))
        . = ALIGN(4);
        __text_end__ = .;
    } > FLASH

    .data : AT(__text_end__)
    {
        . = ALIGN(4);
        __data_start__ = .;
        *(.data*)
        . = ALIGN(4);
        __data_end__ = .;
    } > RAM
    __data_load__ = LOADADDR(.data);

    .bss :
    {
        . = ALIGN(4);
        __bss_start__ = .;
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        __bss_end__ = .;
    } > RAM

    /DISCARD/ :
    {
        *(.ARM.exidx*)
        *(.ARM.extab*)
        *(.comment)
        *(.note*)
    }
}
