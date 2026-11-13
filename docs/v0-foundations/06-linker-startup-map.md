---
title: "链接脚本、启动与 map 体积审计"
platforms: [f407]
---

# 链接脚本、启动与 map 体积审计

> 第 5 章把一行 C 送到 `.elf`。这一章翻到链接器的工作台：一张 136 行的图纸决定每个段住哪，一段启动代码把图纸上的门牌读成动作，一份 map 文件记录谁占了哪块地。三件事连起来，固件才从“链接成功”走到“上电能跑、体积有账”。

## 本章罗盘

- **问题**：136 行链接脚本的契约头、MEMORY、SECTIONS 三段各管什么？向量表为什么必须住 Flash 头排，删掉 `KEEP` 后哪三层证据会同时报警？`.data` 的 VMA 与 LMA 分别给谁看，少写 `AT> FLASH` 为什么能让 660 字节的 bin 涨到 128MB？复位后到 `main` 之间硬件和软件各做什么？`size` 三列、map 三板斧、`nm --size-sort` 怎样把体积账对到具体符号？
- **交付**：能逐段读 136 行图纸，指出三段边界；能用 `nm`、`readelf`、map 三条证据判断向量表是否被回收、`.data` 是否搬得动、自定义段是否成了 orphan；能按五站复述启动流程并说出每站失败的样子；能用 size、map、nm 完成一次“先审账再优化”的体积审计。
- **边界**：单平台 F407（F407ZGT6：1MB Flash、128KB SRAM、64KB CCM）。数字来自 xPack GNU Arm Embedded GCC 15.2.1、binutils 2.45.1 的 `00-blink` 与 `link_probe` 标本；来源没有记录板上复跑，烧录后的现象在本章标为未跑。构建系统与链接旗标留给[第 7 章](./07-build-systems-legacy.md)，SWD 与 GDB 留给[第 20 章](../v2-reliability/20-debug-performance.md)，中断号与外设向量留给[第 10 章][ch10]，Flash 分区与 IAP 留给[第 17 章][ch17]。
- **依据锚点**：B3《链接脚本：固件的建筑图纸》（`mcu/docs/build/03-linker-script.md`）、B4《启动过程：上电到 main 的每一条指令》（`mcu/docs/build/04-startup.md`）、B5《map 与体积：谁吃了我的 Flash》（`mcu/docs/build/05-map-size.md`）；[第 5 章](./05-toolchain-four-steps.md)的四步构建与 ELF 节表。工具链版本、字节数、地址与 `nm` 输出转引自上述来源。

## 先做出来

不用开发板，只要工具链在 `PATH` 里。进入 `mcu/code/toolchain/03-linker`，先押两个判断：把链接脚本里的 `KEEP(*(.isr_vector))` 删成 `*(.isr_vector)`，链接器会不会报错？固件会变大还是变小？

```bash
cd mcu/code/toolchain/03-linker
sh probe.sh keep
```

来源记录的关键三行：

```text
blink.bin  = 660 字节
nokeep.bin = 268 字节
差 = 392 字节 = 0x188
```

链接器一声不吭，bin 却少了 392 字节，正好是向量表的 `0x188`。再把三个证据排在一起看：

- `readelf -S` 里 `.isr_vector` 还在，段号、段名都在，尺寸从 `000188` 变成 `000000`。
- `nm` 里 `g_pfnVectors` 消失，说明符号没有随段留下。
- bin 头两个字从 `20020000 08000189` 变成 `d040f8df 68014810`：上电硬件读到的“栈顶”成了两条指令的机器码，第一次压栈就死。

这就是本章的主线：**链接器只按图纸办事；图纸少一句话，它不报错，只是安静地给你一个错固件。** 下面把图纸、启动代码和体积账依次翻开。

## 机制

### 136 行图纸：契约头、MEMORY、SECTIONS

`mcu/code/stm32/00-blink/stm32f407xx.ld` 共 136 行，按行号切成三段：

```text
stm32f407xx.ld
├── 契约头      :13-20   ENTRY / _estack / 两份最小预算
├── MEMORY 圈地 :22-29   FLASH 1MB @0x0800_0000、RAM 128KB @0x2000_0000
└── SECTIONS 分房 :31-136  .isr_vector → .text → .data → .bss → ._user_heap_stack → 收尾
```

![链接脚本三契约：FLASH 与 RAM 两块圈地，.data 的双住址连线](/arch/linker-map.png)

契约头只有四行有效声明：

```ld
ENTRY(Reset_Handler)                        /* :13 */
_estack = ORIGIN(RAM) + LENGTH(RAM);        /* :16 */
_Min_Heap_Size  = 0x200;                    /* :19 */
_Min_Stack_Size = 0x400;                    /* :20 */
```

- `ENTRY(Reset_Handler)` 只对链接器说话：它写进 ELF 头，也参与 `--gc-sections` 的根集合。芯片不看这一行，芯片看向量表第 2 项；`readelf -h` 的入口与向量表第 2 项是两套口径，第 5 章已经拆过。
- `_estack` 算出 `0x20000000 + 0x20000 = 0x20020000`。`nm` 给 `20020000 R _estack`，bin 的第一个字也是它。栈向下生长，所以这是 RAM 最后一字节的上一格。
- `_Min_Heap_Size` 与 `_Min_Stack_Size` 是额度，不是空间。真正的占位在 `._user_heap_stack`：`. = . + _Min_Heap_Size;` 与 `. = . + _Min_Stack_Size;` 把两笔预算记在 RAM 账上（`:122-123`）。

MEMORY 圈两块地：

```ld
MEMORY
{
  FLASH (rxa)  : ORIGIN = 0x08000000, LENGTH = 1024K   /* :24 */
  RAM   (xrw)  : ORIGIN = 0x20000000, LENGTH = 128K    /* :28 */
}
```

F407ZGT6 的事实：Flash 1MB 从 `0x0800_0000` 起，SRAM 128KB 从 `0x2000_0000` 起；另有 64KB CCM 在 `0x1000_0000`，讲自定义段时再开。区域属性的合法字母只有 `r w x a i l` 六个。老教程常见的 `(xrwah)` 多一个 `h`，新版 ld 会拒绝：

```text
invalid character %c (104) in flags
error: ld returned 1 exit status
```

`104` 是 `h` 的 ASCII 码；`%c` 没被替换，是 binutils 自己的格式串少带了参数。看到这句，删 `h` 即可，不必去查“字符 104 是什么”。

图纸写对之后，map 文件的 `Memory Configuration` 会回显它理解的地块：

```text
Name             Origin             Length             Attributes
FLASH            0x08000000         0x00100000         axr
RAM              0x20000000         0x00020000         xrw
*default*        0x00000000         0xffffffff
```

属性从你写的 `rxa` 被重排成 `axr`，顺序由 ld 固定；`*default*` 是没进任何地块的东西的收容所，orphan 段会在这里露馅。SECTIONS 从 `:31` 到 `:136`，顺序就是 Flash 与 RAM 的住址顺序。下面只挑三个关键房间：向量表、`.data` 和自定义段。

### 向量表住头排：KEEP 管生死

```ld
  .isr_vector :
  {
    . = ALIGN(4);
    KEEP(*(.isr_vector))     /* :38 */
    . = ALIGN(4);
  } >FLASH
```

三个细节：

- `.` 是当前地址，不是文件偏移。没有 `AT>` 的输出段里，`.` 就是 VMA。`. = ALIGN(4)` 把向量表抬到 4 字节边界：Cortex-M 的每个向量项是一个 32 位地址。
- `*(.isr_vector)` 读作“所有输入文件里名叫 `.isr_vector` 的段”。名字来自启动文件 `startup_stm32f407xx.s` 的 `.section .isr_vector,"a",%progbits`；图纸声明房间，启动文件认领名字，两边是一套榫卯。向量表本质上是一个函数指针数组，[第 4 章](./04-function-pointer-state-machine.md)讲的函数指针在这里有了硬件读者。
- `KEEP()` 管生死。工程链接带 `--gc-sections`，GC 只看“有没有人引用”；向量表没有被任何指令引用，读它的是硅片里的硬件，而硬件不出现在符号表里。`KEEP` 就是给链接器的小抄：这一段不许回收。

第 1 刀已经演示了后果，把几条证据按排查顺序排：

| 层 | 命令 | 正常 | 删掉 KEEP 后 |
| --- | --- | --- | --- |
| 固件大小 | `wc -c` | `blink.bin` 660 字节 | 268 字节，少 392 = 0x188 |
| 段表 | `readelf -S` | `.isr_vector` 尺寸 `000188`，标志 `A` | 段名还在，尺寸 `000000`，标志 `W` |
| 头两个字 | `od -t x4 -N 8` | `20020000 08000189` | `d040f8df 68014810` |
| 符号 | `nm` 查 `g_pfnVectors` | `08000000 r g_pfnVectors` | 符号消失 |

第三层最要命。正常版本第一个字是 `_estack`，第二个是 `Reset_Handler` 加 Thumb 位（最低位为 1）；向量表被回收后，`.text` 顶到 `0x08000000`，芯片把两条指令的机器码当成 SP 和 PC 用：`SP = 0xd040f8df`，第一条压栈指令就打死机。`readelf -S` 里那具尺寸 0 的空壳不会提醒你，`nm` 里消失的 `g_pfnVectors` 才是“板子毫无反应”时最该先看的一行。

### `.data` 的双地址：VMA 与 LMA

```ld
  _sidata = LOADADDR(.data);                 /* :91 */
  .data :
  {
    . = ALIGN(4);
    _sdata = .;                              /* :95 */
    *(.data)
    *(.data*)
    . = ALIGN(4);
    _edata = .;                              /* :99 */
  } >RAM AT> FLASH                           /* :100 */
```

![.data 的 VMA 与 LMA 双地址动画](/anim/data-vma-lma.svg)

读法：`>RAM` 说运行时住 RAM，这是 VMA；`AT> FLASH` 说初值行李寄存在 Flash，这是 LMA。`LOADADDR(.data)` 取 LMA，所以 `_sidata` 是“去 Flash 哪里取货”的门牌；`_sdata` 与 `_edata` 则是 RAM 里的头尾。

链接结果在程序头里变成第二条 `LOAD`。来源基线三条：

```text
  LOAD  0x001000  0x08000000  0x08000000  0x00218  0x00218 R E
  LOAD  0x002000  0x20000000  0x08000218  0x00004  0x01008 RW
  LOAD  0x000008  0x20001008  0x0800021c  0x00000  0x00600 RW
```

第二行 `VirtAddr=0x20000000`、`PhysAddr=0x08000218`、`FileSiz=0x4`、`MemSiz=0x1008`：文件里只带 4 字节初值（标本 `g_live` 一个 int），运行时却占 4104 字节；`4104 − 4 = 4100`，正是启动代码要清零的 `.bss`。`nm` 给 `08000218 A _sidata`，map 里那一行更直白：

```text
.data   0x20000000   0x4  load address 0x08000218
```

第 2 刀删掉 `AT> FLASH`，只留 `>RAM`：

```text
  LOAD  0x001000  0x08000000  0x08000000  0x00218  0x00218 R E
  LOAD  0x002000  0x20000000  0x20000000  0x00004  0x01608 RW
```

三条 `LOAD` 塌成两条，`.data` 的 `PhysAddr` 与 `VirtAddr` 都变成 `0x20000000`。符号表跟着变：

```text
20000000 D _sdata
20000004 D _edata
20000000 A _sidata        ← 本来是 0x08000218
```

启动文件的搬运循环于是把 `_sdata` 拷到 `_sdata`，一个字节也没搬；Flash 里的初值还在，只是没人来取。上电后 RAM 是随机值，`g_live` 读到多少看运气。这个错误不报链接错、不报烧录错，`readelf -h` 也漂漂亮亮，判据只有一条：**`nm` 里 `_sidata` 必须不等于 `_sdata`，且它应落在 `0x0800xxxx`。**

### 启动五站：硬件两读到最后一声 `bl main`

`.data` 的门牌由启动文件兑现。复位松手后，CPU 没有操作系统、没有 C 世界，连栈都没有；硬件只做两件事：

1. 从 0 号地址读 4 字节，装进 MSP；
2. 从 4 号地址读 4 字节，装进 PC，开始取指。

“0 号地址”由 BOOT 引脚决定：BOOT0=0 时映射到用户 Flash `0x08000000`；BOOT0=1、BOOT1=0 时映射到系统存储器 `0x1FFF0000` 的出厂 ISP；BOOT0=1、BOOT1=1 时映射到 SRAM `0x20000000`。日常从用户 Flash 启动，所以 Flash 最前面必须躺一张向量表。F407 的向量表有 98 项：16 项内核异常加 82 项外设中断（RM0090 §12.2，IRQn 0..81），头两项是 `_estack` 与 `Reset_Handler`。

![启动五站：硬件两读、开 FPU、搬 .data、清 .bss、bl main](/arch/boot-sequence.png)

五站流水线：

| 站 | 谁做 | 关键动作 | 失败的样子 |
| --- | --- | --- | --- |
| 1 硬件两读 | 硅片硬逻辑 | `0x08000000` → MSP，`0x08000004` → PC | 向量表被 gc：SP 变成机器码，第一次压栈即 HardFault |
| 2 开 FPU | `Reset_Handler` 第 0 步 | `SCB->CPACR` 的 CP10/CP11 置全权限，`dsb` 与 `isb` | 第一条 FPU 指令触发 UsageFault(NOCP)，灯不闪、串口无声 |
| 3 搬 `.data` | `Reset_Handler` | `_sidata` → `_sdata`..`_edata` 的 4 字节循环 | 初值没搬，全局变量是上电垃圾 |
| 4 清 `.bss` | `Reset_Handler` | `_sbss`..`_ebss` 写 0 | 未初始化全局变量不是 0，行为随温度与板子变 |
| 5 `bl main` | `Reset_Handler` | 跳进 C 世界；返回则原地转圈 | 裸机 `main` return 等于停机，等看门狗收尸 |

FPU 那一步容易被漏：Makefile 写着 `-mfloat-abi=hard -mfpu=fpv4-sp-d16`，编译器相信“FPU 随时可用”；复位后 CP10/CP11 默认关闭，中间差一道开门手续（PM0214 §4.6.6）：

```asm
  ldr   r0, =0xE000ED88        /* SCB->CPACR */
  ldr   r1, [r0]
  orr   r1, r1, #(0xF << 20)   /* CP10/CP11 全权限（bit20~23） */
  str   r1, [r0]
  dsb                          /* 数据同步屏障 */
  isb                          /* 指令同步屏障 */
```

搬运循环在启动文件里是下面这组指令；清零循环更瘦，`ldr r2, =_sbss`、`ldr r4, =_ebss` 与 `movs r3, #0` 之后，一路 `str r3, [r2], #4` 扫到终点，连源操作数都不需要：

```asm
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
```

这些符号在 `Reset_Handler` 的字面量池里被物化。来源对 `link_probe` 标本的 `objdump -d` 给了七个字面量，和 `nm` 逐项对得上：

```text
 80001cc:  .word 0x20020000    ← _estack
 80001d0:  .word 0xe000ed88    ← SCB->CPACR
 80001d4:  .word 0x20000000    ← _sdata
 80001d8:  .word 0x20000004    ← _edata
 80001dc:  .word 0x08000218    ← _sidata
 80001e0:  .word 0x20000004    ← _sbss
 80001e4:  .word 0x20001008    ← _ebss
```

`_sbss == _edata == 0x20000004` 不是巧合：`.bss` 紧贴 `.data`，清零循环从搬运循环的终点开始。`_ebss = _sbss + 0x1004`，`0x1004 = 4100`，正是标本里 `g_dark` 加 `g_big[4096]` 的大小。这些是链接期常量，不是运行期查询；改图纸、加数组，池子里的数会跟着变，启动文件不用知道你有几个全局变量。

最后 `bl main`，裸机没有命令行可以退回。`main` 真敢 return，就掉进 `.L_hang` 原地转圈，等看门狗或调试器收尸。中断服务函数则由 weak 默认出口 `Default_Handler: b .` 兜底，你在 C 里写同名函数就自动覆盖，这条机制在[第 10 章][ch10]展开。

### 自定义段与 CCM：图纸和启动文件是一套榫卯

`.data` 这套契约在自定义段上会放大。C 里给变量加 `__attribute__((section(".ccmram"), used)) int g_ccm[4] = { 1, 2, 3, 4 };` 之后，F407 的 CCM（64KB @ `0x1000_0000`，CPU 直连、DMA 够不着；总线和 DMA 的边界见[第 8 章][ch08]与[第 14 章][ch14]）有四种结局：

| 图纸状态 | 链接结果 | 判据 |
| --- | --- | --- |
| 完全没登记 `.ccmram` | orphan 段被静默安置到普通 SRAM 的 `0x20000004` | `objdump -h` 看 `.ccmram` 的 VMA |
| 加了 `CCM` 地块与 `>CCM`，漏 `AT> FLASH` | LMA 跟 VMA 走，`objcopy` 把 `0x0800_0000` 到 `0x1000_0000` 的空洞填零 | bin 尺寸 134,217,744 字节 |
| 补上 `>CCM AT> FLASH` | LMA 回到 Flash，`0x0800022c` 紧贴 `.text` | bin 收回 576 字节 |
| 三行都写对，启动文件不搬 | `_siccm` 在启动文件里出现 0 次，CCM 里的初值仍是随机值 | `grep -c _siccm startup_stm32f407xx.s` |

第一态的杀伤力在于测不出来：变量明明能用，只是不在你以为的 CCM，DMA 能不能访问、速度多少全与预期不符。第二态的算术是 `0x10000000 − 0x08000000 = 134,217,728`，再加 16 字节初值，等于 134,217,744；660 字节的固件被一个词放大到 128MB。第三态收回 576 字节：`(0x0800023c + 4) − 0x08000000 = 0x240 = 576`。第四态最容易被忽略：图纸单方面开了房间，施工队不知道；`Reset_Handler` 里只有一个 `.data` 搬运循环，`_siccm/_sccm/_eccm` 三块门牌立着，没有一条指令走过去。要让带初值的变量真住进 CCM，得自己在启动文件补第二段拷贝，照抄 `.data` 那几条指令，把符号换成 `_siccm/_sccm/_eccm`。

### size 三列：Flash 与 RAM 各吃哪份

`size` 把固件的体积压成一行。来源 B5 记录的一份 `blink.elf`：

```text
   text    data     bss     dec     hex   filename
    280      12      32     324     144   blink.elf
```

第 5 章另一份 `blink.elf` 记录是 660/0/1536；两组数出自来源里的不同记录，数字会变，下面两条公式不变。三列对应三种资源：

| 列 | 装的是什么 | 住哪 | 算进谁的占用 |
| --- | --- | --- | --- |
| **text** | 代码（`.text`）、只读数据（`.rodata`）、向量表 | Flash | Flash |
| **data** | 有初值的全局变量（`.data`） | 运行在 RAM，初值存 Flash | **Flash + RAM 各一份** |
| **bss** | 零初始化的全局变量（`.bss`） | 纯 RAM，启动时清零 | RAM |

两条公式立刻出来：`Flash 占用 = text + data`，`RAM 占用 = data + bss`。

为什么 data 算两份？因为 `.data` 有初值，初值必须存在断电不丢的 Flash（`AT> FLASH`），运行时启动代码把它搬到 RAM；所以 Flash 存初值一份、RAM 住运行值一份。`bss` 没有初值，启动时清零即可，只吃 RAM。`._user_heap_stack` 是一段不存真实字节的检查段，但它的预算会进 bss 列、也进 RAM 占用；这就是第 5 章 660/0/1536 里那 1536 的来历。

`--print-memory-usage` 给的是同一笔账按地块汇总。`link_probe` 标本在原图纸上的读数：

```text
Memory region         Used Size  Region Size  %age Used
           FLASH:         540 B         1 MB      0.05%
             RAM:        5640 B       128 KB      4.30%
```

5640 能手算：`.data` 4 + `.bss`（4 + 4096）+ `._user_heap_stack`（`0x200 + 0x400 = 1536`）= 5640。把 RAM 改小到 2K，ld 报 `region 'RAM' overflowed by 3592 bytes`，`5640 − 2048 = 3592`。只把栈预算从 `0x400` 撑到 `0x20000`，代码一个没多，ld 点名 `._user_heap_stack` 报 `overflowed by 4616 bytes`，RAM 到 `135688 B = 103.52%`，`135688 − 131072 = 4616`。**栈不够用这件事，在构建窗口里以百分比失败，好过在客户手上以踩内存的形式失败。**

### map 三板斧：户口本怎么翻

map 文件由 `ld` 的 `-Map=build/blink.map` 生成（Makefile 里的旗标，[第 7 章](./07-build-systems-legacy.md)接线）。三块内容各查一件事：

1. **Archive member 表**：列出从哪些 `.a` 静态库里捞了哪些 `.o`。链接了 `libc.a` 时，这里能看到“为了 `printf` 捞了 `vfprintf.o`、`__assert.o`”，库被引用的粒度一目了然，也是 `gc-sections` 是否生效的证据。
2. **Memory Map**：每个 `.o` 的每个段落进哪个地址、每个符号多大住哪。找 `main.o` 的记录就能看到 `main` 多大、它引用了谁；按段汇总的数字告诉你 `.text` 里哪块最大。
3. **Discarded input**：被 `--gc-sections` 辞退的段。链接器发现某段没被任何入口（entry 与中断向量）引用，就把它丢弃，不进最终 `.elf`。本该保留的段出现在这里，说明链接脚本没把它标 `KEEP()`。

除了 map，链接器还有三条自述开关，出问题的第一步都该按它们来：

- `-Wl,--print-memory-usage`：每块地的账，上面 540 B / 5640 B 那两个数就是它打的。RAM 从 4.30% 跳到 103.52%，一眼能看出是栈预算还是大数组。
- `-Wl,--trace`：谁被链进来了。来源记录的前几行是 `build/startup.o`、`build/main.o`，随后是 `…thumb/v7e-m+fp/hard\libgcc.a`、`libc.a`、`libm.a`。`thumb/v7e-m+fp/hard` 是多架构目录，由 `-mcpu=cortex-m4 -mfpu=fpv4-sp-d16 -mfloat-abi=hard` 三个开关共同决定；换成 soft-float 会去另一个目录找库，找不到就报 `cannot find -lgcc`。`libc.a` 出现两次不是重复链接，archive 会被反复扫描，直到不再有新的目标文件被拉出来。
- `ld --verbose`：不打 `-T` 时它默认用哪张图纸。内置图纸的入口是 `_start`，而且完全没有 `MEMORY` 块，所以裸用 `ld` 不写 `-T`，程序会被塞进默认的 `TEXT`/`DATA` 布局，跟 `0x08000000` 没有半点关系。**`-T` 不是可选的美化，是芯片能启动的前提。**

### nm 按大小审计：先审账，再优化

`arm-none-eabi-nm -S --size-sort build/blink.elf | tail -10` 把所有符号按体积从小到大排，`tail` 看队尾，就是固件里最占地方的那几个；`-S` 让每行带上符号大小，`--size-sort` 按大小排序。典型大户与瘦身手段：

| 大户类型 | 典型来源 | 瘦身手段 |
| --- | --- | --- |
| `vfprintf` 一族 | `printf` 带浮点 | 不用 `%f` 就能关浮点版（`-u _printf_float` 的反向） |
| 大 `const` 表 | 正弦表、字库、查找表 | 必要的 Flash 开销，挪不走的 |
| 大缓冲区 | `uint8_t buf[4096]` | 搬进 CCM（CPU 专用）或改环形 |
| 启动代码 | `crt0.o`、`startup_*.s` | 固定开销，几十百来字节 |

审计纪律：**先看大项，再谈优化级别。** 一个 4KB 的未用数组，比 `-O2` 到 `-Os` 省的那几百字节大一个数量级；方向错了 `-O2` 也救不了。瘦身工具箱按顺序用：

1. `-ffunction-sections -fdata-sections` 加 `--gc-sections`：把每个函数、每份数据各放一个段，链接时丢弃没引用的。不加 `-ffunction-sections`，整个 `.o` 要么全进要么全不进，`gc-sections` 无从下手；00-blink 的 Makefile 已默认开这套旗。
2. `-Os`：优化体积，比 `-O2` 省 Flash，代价是速度略慢；速度敏感的热路径单独标 `-O2`/`-O3`。
3. 去未用库：链接了 `libc` 但没用 `malloc`，`gc-sections` 会把 `malloc.o` 辞退（前提仍是 `-ffunction-sections`）。
4. `const` 归位：把有初值的只读数组标 `const`，从 `.data`（Flash + RAM 双吃）挪进 `.rodata`（只吃 Flash）。加一个 `const`，data 降、text 涨、RAM 净省。
5. CCM 腾挪：128KB 主 SRAM 留给 DMA 缓冲、栈与堆，64KB CCM 专门放 CPU 专用的大缓冲；CCM 的数据 DMA 搬不动，配错了静默失败。

## 测量与证据

本章数字来自 B3、B4、B5 与第 5 章的取证记录，工具链是 xPack GNU Arm Embedded GCC 15.2.1、binutils 2.45.1。换版本、换优化档或换板子，具体数字会变，判读方法不变。

| 取证项 | 来源命令 | 来源记录里的读数 |
| --- | --- | --- |
| 图纸行数 | `wc -l stm32f407xx.ld` | 136 行；契约头 :13-20、MEMORY :22-29、SECTIONS :31-136 |
| 第 1 刀 | `sh probe.sh keep` | 660 → 268 字节，差 392 = 0x188；`.isr_vector` 尺寸 000188 → 000000；头两个字 `20020000 08000189` → `d040f8df 68014810` |
| 第 2 刀 | `sh probe.sh at` | `LOAD` 三条 → 两条；`_sidata` 从 `0x08000218` 变成 `0x20000000`；判据 `_sidata != _sdata` |
| 内存账 | `-Wl,--print-memory-usage` | FLASH 540 B / 0.05%；RAM 5640 B / 4.30%；5640 可手算 |
| 溢出两例 | `LENGTH = 2K`、`_Min_Stack_Size = 0x20000` | `overflowed by 3592 bytes`；`overflowed by 4616 bytes`，RAM 103.52% |
| 非法属性 | `(xrwah)` | `invalid character %c (104) in flags` |
| CCM 四态 | `sh probe.sh ccm` | orphan VMA `0x20000004`；bin 134,217,744 字节；补 `AT> FLASH` 后 576 字节；`_siccm` 引用 0 次 |
| 启动五站 | `objdump -d`、`nm` | 七个字面量；`_sbss == _edata == 0x20000004`；`_ebss = 0x20001008` |
| size 三列 | `arm-none-eabi-size blink.elf` | 280/12/32（B5）；660/0/1536（第 5 章）；公式 Flash=text+data、RAM=data+bss |
| map 三板斧 | `-Map=build/blink.map` | Archive member、Memory Map、Discarded input 三块 |
| nm 审计 | `nm -S --size-sort` | 来源给命令与大户类型表，未记录具体符号列表 |
| 链接器自述 | `--trace`、`ld --verbose` | `thumb/v7e-m+fp/hard` 多架构目录；内置图纸 `ENTRY(_start)` 且无 `MEMORY` |
| 板上实验 | 烧录、GDB 单步 | 来源未记录本机复跑，待上板 |

判断“真的会了”：给你一份 `.elf`，能用五条命令说出入口、Flash 占用、RAM 占用、`_sidata` 与 `_sdata` 是否相等、向量表是否还在；给你一次 `region overflowed`，能先看点名的段，再用手算核对总量；给你一个体积暴涨的工程，能按 map → `nm --size-sort` → `size` 的顺序找出大户，而不是先改 `-O` 级别。

## 失败分支

| 现象 | 原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| 板子上电毫无反应，第一次压栈就 HardFault | 向量表被 `--gc-sections` 回收 | `readelf -S` 里 `.isr_vector` 尺寸 0；`nm` 找不到 `g_pfnVectors`；bin 比正常小 392 字节 | 恢复 `KEEP(*(.isr_vector))` |
| 全局变量初值随机，换块板子结果又不同 | 漏写 `AT> FLASH`，`.data` 的 LMA 塌进 RAM | `nm` 里 `_sidata == _sdata`，且不是 `0x0800xxxx` | 给 `.data` 补 `AT> FLASH` |
| `.ccmram` 变量能读写，但不在 CCM | 自定义段没在图纸登记，成了 orphan | `objdump -h` 看 `.ccmram` 的 VMA 是 `0x20000004` 而不是 `0x1000xxxx` | 在 MEMORY 加 `CCM` 地块，在 SECTIONS 加房间 |
| 链接成功，bin 却有 128MB | 自定义段只写 `>CCM`，LMA 跟着 VMA 走 | `readelf -l` 里该段 `PhysAddr=0x10000000`；`objcopy` 补零 | 改成 `>CCM AT> FLASH` |
| CCM 变量地址对了，初值仍是随机值 | 启动文件没有第二段拷贝循环 | `grep -c _siccm startup_stm32f407xx.s` 为 0；`Reset_Handler` 只有一对 `ldr/str` | 照抄 `.data` 循环，补 `_siccm/_sccm/_eccm` 的搬运 |
| 链接报 `region 'RAM' overflowed by N bytes`，点名的却是 `._user_heap_stack` | `_Min_Stack_Size` 或 `_Min_Heap_Size` 太大，或某个 `.bss` 大数组 | `--print-memory-usage` 看 RAM 占比；map 的 Memory Map 找大段 | 先调预算或搬大缓冲，不要先删代码 |
| `invalid character %c (104) in flags` | MEMORY 属性多写了 `h` | 报错里的 104 是 `h` 的 ASCII 码 | 删掉 `h`，合法字母只有 `r w x a i l` |
| 装了库却报 `cannot find -lgcc` | 浮点 ABI 与 multilib 目录不匹配 | `--trace` 里找 `thumb/v7e-m+fp/hard` 还是 soft-float 目录 | 统一 `-mfpu` 与 `-mfloat-abi`，清掉旧构建 |
| `.elf` 几十 KB，以为 Flash 装不下 | 把调试信息算进了固件 | `size` 的 text + data 才是 Flash 占用 | 看 `size`，不要看 `.elf` 文件大小 |
| bin 比 text + data 大 | 段间空隙按地址铺开也占字节 | `readelf -l` 的 `LOAD` 地址与 `FileSiz` | 烧录大小以 `size` 与 map 为准；需要按需记录时用 hex |
| `.bss` 突然变大，代码没改几行 | 新加了大数组或栈预算被撑大 | `nm -S --size-sort` 的队尾；map 的 Memory Map | 搬 CCM、改环形缓冲或缩预算 |
| 烧录成功但固件“没被运行” | BOOT0 接错，芯片从系统存储器或 SRAM 启动 | BOOT0/BOOT1 电平；SWD 能否连上 | 把 BOOT0 拉回 GND，从用户 Flash 启动 |

## 离开检查

1. 136 行图纸的三段各管什么？`ENTRY(Reset_Handler)` 谁看，芯片复位后看哪里？
2. 向量表为什么必须住 Flash 头排？删掉 `KEEP` 后，`readelf -S`、`nm`、bin 头两个字各给什么证据？
3. `.data` 的 VMA 与 LMA 分别是什么？谁读 VMA、谁读 LMA？删掉 `AT> FLASH` 后，`nm` 的判据是什么？
4. 启动五站各做什么？CPACR 漏开会怎样？`main` 真的 return 会去哪？
5. `size` 三列公式是什么？为什么 data 算两份、bss 只算一份？`._user_heap_stack` 落在哪一列？
6. map 三板斧各查什么？`nm -S --size-sort` 怎样找大户？为什么优化要先看大项、再谈 `-O` 级别？
7. 自定义段 `.ccmram` 的四种结局各是什么？为什么补了 `AT> FLASH`，初值还可能到不了 CCM？

<details>
<summary>对照答案</summary>

1. 契约头管入口、栈顶与最小堆栈预算；MEMORY 圈定 Flash 与 RAM 的起止地址；SECTIONS 决定每个段住哪个地块、谁在头排。`ENTRY(Reset_Handler)` 只写进 ELF 头给链接器与调试器看；芯片复位后从 0 号地址读 MSP、从 4 号地址读 PC，向量表第 2 项才是它跳去的地方。
2. 因为硬件从 `0x08000000` 读栈顶、从 `0x08000004` 读复位入口，向量表必须在 Flash 最前面。删掉 `KEEP` 后，`readelf -S` 里 `.isr_vector` 尺寸变 0 但段名还在；`nm` 里 `g_pfnVectors` 消失；bin 头两个字变成 `d040f8df 68014810`，第一次压栈就死。
3. VMA 是运行时地址（`.data` 在 `0x20000000`），LMA 是初值在 Flash 的寄存地址（`0x08000218`）。CPU 的 `ldr` 读 VMA，装载器与 `objcopy -O binary` 读 LMA；`_sidata = LOADADDR(.data)` 取的是 LMA。删掉 `AT> FLASH` 后 `_sidata == _sdata`，启动循环把 `_sdata` 拷到 `_sdata`，初值永远搬不到位。
4. 五站：硬件两读（MSP 与 PC）、开 FPU（CPACR 的 CP10/CP11）、搬 `.data`（`_sidata` → `_sdata.._edata`）、清 `.bss`（`_sbss.._ebss` 写 0）、`bl main`。CPACR 漏开时第一条 FPU 指令触发 UsageFault(NOCP)，程序静默卡死。`main` return 后掉进 `.L_hang` 原地转圈，等看门狗或调试器。
5. `Flash = text + data`，`RAM = data + bss`。data 有初值，初值存 Flash、运行值在 RAM，两份都吃；bss 零初始化，启动时清零，只吃 RAM。`._user_heap_stack` 是检查段，预算进 bss 列，也进 RAM 占用。
6. Archive member 表查静态库捞了哪些 `.o`；Memory Map 查每个段、符号的地址与大小；Discarded input 查谁被 `gc-sections` 辞退。`nm -S --size-sort` 按符号大小排队，`tail` 看队尾的大户。一个 4KB 未用数组比 `-O2` 到 `-Os` 省的几百字节大一个数量级，所以先砍大项，再谈优化级别。
7. 四种结局：orphan 段被安置到普通 SRAM 的 `0x20000004`；只写 `>CCM` 时 bin 被空洞撑到 134,217,744 字节；补 `AT> FLASH` 后收回 576 字节；图纸全对但启动文件不搬，初值仍是随机值。因为 `Reset_Handler` 里只有一个 `.data` 搬运循环，`_siccm` 在启动文件里出现 0 次，得自己补第二段拷贝。

</details>

动作验收：在本机跑 `sh probe.sh keep` 与 `sh probe.sh at`，把三组输出留在 `build/`；再对一个本地 `.elf` 跑 `size`、`nm -S --size-sort | tail`、`grep -A3 "Discarded input" build/blink.map`，写下 Flash 与 RAM 占用、队尾三个符号与被 gc 的段名。

[ch08]: ../v1-drivers/08-architecture-memory-clock.md
[ch10]: ../v1-drivers/10-interrupts-nvic-exti.md
[ch14]: ../v1-drivers/14-dma.md
[ch17]: ../v1-drivers/17-flash-iap-ota.md
