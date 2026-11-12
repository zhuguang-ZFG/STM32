/* Linker script for STM32F103C8T6: 64 KiB Flash, 20 KiB RAM (DS5319 Rev 20).
 * Budget per plan design §3: Flash ≤56 KiB, static RAM ≤12 KiB, ≥2 KiB stack reserved.
 */
MEMORY
{
  FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 64K
  RAM   (rwx) : ORIGIN = 0x20000000, LENGTH = 20K
}

_estack = ORIGIN(RAM) + LENGTH(RAM);   /* 8-byte aligned by startup */
_Min_Heap_Size = 0;                    /* no dynamic allocation in firmware */
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
    _etext = .;
  } > FLASH
  .data : {
    _sdata = .;
    *(.data*)
    . = ALIGN(4);
    _edata = .;
  } > RAM AT> FLASH
  _sidata = LOADADDR(.data);
  .bss : {
    _sbss = .;
    *(.bss*)
    *(COMMON)
    . = ALIGN(4);
    _ebss = .;
  } > RAM
  PROVIDE(end = _ebss);
  PROVIDE(_end = _ebss);
  ._user_stack : {
    . = ALIGN(8);
    . = . + _Min_Stack_Size;
    . = ALIGN(8);
  } > RAM
  /DISCARD/ : { *(.ARM.attributes) }
}
