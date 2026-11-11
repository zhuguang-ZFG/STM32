/*
 * stm32f407xx.ld —— STM32F407ZGT6 链接脚本
 *
 * 回答一个问题：编译出来的一堆 .o，凭什么拼成一颗芯片能跑的固件？
 *   - FLASH：1MB @ 0x08000000，断电不丢，程序住这（.text/.rodata/.data 的初值）
 *   - RAM ：128KB @ 0x20000000，掉电即失，运行期数据住这（.data/.bss/栈/堆）
 *   （F407 另有 64KB CCM 内存 @ 0x10000000，CPU 直连、DMA 够不着，本章先不用）
 *
 * 启动时 Reset_Handler 按这里的符号把 .data 从 Flash 搬进 RAM、清零 .bss，
 * 所以 C 里的全局变量"天生就有初值"。
 */

ENTRY(Reset_Handler)

/* 栈顶 = RAM 末尾（栈向下生长）；向量表第 0 项就是它的值 */
_estack = ORIGIN(RAM) + LENGTH(RAM);

/* 最小栈/堆预算：链接时不够就报错，别等运行时踩内存 */
_Min_Heap_Size  = 0x200;
_Min_Stack_Size = 0x400;

MEMORY
{
  FLASH (rxa)  : ORIGIN = 0x08000000, LENGTH = 1024K
  /* 区域属性合法字母只有 r/w/x/a/i/l：早年的教程常写 (xrwah)，含非法的 h，
     旧 binutils 容忍，新版 ld 直接报 "invalid character (104) in flags"。
     本工程只需要 可执行/可写/可读 三个属性。 */
  RAM   (xrw)  : ORIGIN = 0x20000000, LENGTH = 128K
}

SECTIONS
{
  /* 向量表必须躺在 Flash 最前面：上电后硬件从 0x08000000 读栈顶、
     从 0x08000004 读复位入口 */
  .isr_vector :
  {
    . = ALIGN(4);
    KEEP(*(.isr_vector))
    . = ALIGN(4);
  } >FLASH

  /* 代码 + 只读数据 */
  .text :
  {
    . = ALIGN(4);
    *(.text)
    *(.text*)
    *(.rodata)
    *(.rodata*)
    *(.glue_7)
    *(.glue_7t)
    KEEP(*(.init))
    KEEP(*(.fini))
    . = ALIGN(4);
    _etext = .;
  } >FLASH

  /* ARM 异常展开表（C 也用不到，但链接器可能生成；放 Flash） */
  .ARM.extab : { *(.ARM.extab* .gnu.linkonce.armextab.*) } >FLASH
  .ARM :
  {
    __exidx_start = .;
    *(.ARM.exidx*)
    __exidx_end = .;
  } >FLASH

  /* C 库初始化/析构函数表（newlib 用，空着也无妨） */
  .preinit_array :
  {
    PROVIDE_HIDDEN(__preinit_array_start = .);
    KEEP(*(.preinit_array*))
    PROVIDE_HIDDEN(__preinit_array_end = .);
  } >FLASH
  .init_array :
  {
    PROVIDE_HIDDEN(__init_array_start = .);
    KEEP(*(SORT(.init_array.*)))
    KEEP(*(.init_array*))
    PROVIDE_HIDDEN(__init_array_end = .);
  } >FLASH
  .fini_array :
  {
    PROVIDE_HIDDEN(__fini_array_start = .);
    KEEP(*(SORT(.fini_array.*)))
    KEEP(*(.fini_array*))
    PROVIDE_HIDDEN(__fini_array_end = .);
  } >FLASH

  /* .data：有初值的全局变量。运行在 RAM，初值存 Flash(_sidata)，
     启动时 Reset_Handler 负责搬运。AT> FLASH 就是"初值仓库地址" */
  _sidata = LOADADDR(.data);
  .data :
  {
    . = ALIGN(4);
    _sdata = .;
    *(.data)
    *(.data*)
    . = ALIGN(4);
    _edata = .;
  } >RAM AT> FLASH

  /* .bss：没初值的全局变量，不占 Flash，启动时清零 */
  .noinit (NOLOAD) : { . = ALIGN(4); *(.noinit*) . = ALIGN(4); } >RAM

  .bss :
  {
    . = ALIGN(4);
    _sbss = .;
    __bss_start__ = _sbss;
    *(.bss)
    *(.bss*)
    *(COMMON)
    . = ALIGN(4);
    _ebss = .;
    __bss_end__ = _ebss;
  } >RAM

  /* 堆 + 栈的最小空间检查：RAM 剩不下这么多就链接失败 */
  ._user_heap_stack :
  {
    . = ALIGN(8);
    PROVIDE(end = .);
    PROVIDE(_end = .);
    . = . + _Min_Heap_Size;
    . = . + _Min_Stack_Size;
    . = ALIGN(8);
  } >RAM

  /* 裸机工程会整块丢弃 libc.a/libm.a/libgcc.a；本工程用 snprintf（vTaskList 内部），
     需要 libc 的格式化代码真正落进固件，所以不丢。
     newlib 的系统调用桩见 syscalls.c。 */

  .ARM.attributes 0 : { *(.ARM.attributes) }
}
