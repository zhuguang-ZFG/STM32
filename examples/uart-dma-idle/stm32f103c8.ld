ENTRY(Reset_Handler)

MEMORY
{
    FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 64K
    RAM (rwx) : ORIGIN = 0x20000000, LENGTH = 20K
}

_estack = ORIGIN(RAM) + LENGTH(RAM);
_Min_Stack_Size = 2K;

SECTIONS
{
    .isr_vector : { KEEP(*(.isr_vector)) } > FLASH
    .text : {
        *(.text*)
        *(.rodata*)
        KEEP(*(.init))
        KEEP(*(.fini))
        . = ALIGN(4);
    } > FLASH
    .ARM.extab : { *(.ARM.extab*) } > FLASH
    .ARM.exidx : {
        __exidx_start = .;
        *(.ARM.exidx*)
        __exidx_end = .;
    } > FLASH
    .preinit_array : {
        PROVIDE_HIDDEN(__preinit_array_start = .);
        KEEP(*(.preinit_array))
        PROVIDE_HIDDEN(__preinit_array_end = .);
    } > FLASH
    .init_array : {
        PROVIDE_HIDDEN(__init_array_start = .);
        KEEP(*(SORT(.init_array.*)))
        KEEP(*(.init_array))
        PROVIDE_HIDDEN(__init_array_end = .);
    } > FLASH
    .fini_array : {
        PROVIDE_HIDDEN(__fini_array_start = .);
        KEEP(*(SORT(.fini_array.*)))
        KEEP(*(.fini_array))
        PROVIDE_HIDDEN(__fini_array_end = .);
    } > FLASH
    _sidata = LOADADDR(.data);
    .data : {
        . = ALIGN(4);
        _sdata = .;
        *(.data*)
        . = ALIGN(4);
        _edata = .;
    } > RAM AT> FLASH
    .bss (NOLOAD) : {
        . = ALIGN(4);
        _sbss = .;
        *(.bss*)
        *(COMMON)
        . = ALIGN(4);
        _ebss = .;
    } > RAM
    .stack_reservation (NOLOAD) : {
        . = ALIGN(8);
        PROVIDE(end = .);
        PROVIDE(_end = .);
        . = . + _Min_Stack_Size;
        . = ALIGN(8);
    } > RAM
}
