---
title: C1 内存模型：一个全局变量的三段旅程
status: done
difficulty: 2
minutes: 65
---

# C1 内存模型：一个全局变量的三段旅程

> 🎯 `int led = 5;` 在你的固件里其实**没有**这个 5。RAM 里那位 `led` 上电瞬间还是一堆随机值，5 住在别处，靠人搬过来。谁搬的、从哪搬、搬几个字节？本章把这三问一次答完。

## 本章精髓

1. **为什么段要分裂**：Flash 掉电不丢但写不了，RAM 能写但断电即失。"有初值的全局变量"必须同时住两边：RAM 里住本体、Flash 里住初值，这份"双重户籍"就叫 `.data`；没有有意义初值的只登记不给货，就叫 `.bss`。段不是语法分类，是两种介质的分工。
2. **为什么 C 的承诺需要别人兑现**：语言保证 `int g_init = 5;` 一执行就能读到 5，硬件可不保证。兑现承诺的是启动文件里那个不到 40 字节的拷贝循环，一出链接器与启动代码合演的戏：链接脚本把"行李"和"人"分成两个地址（VMA/LMA），`Reset_Handler` 照着这两个地址把行李搬进来。
3. **为什么 `const` 在嵌入式里值钱**：PC 上 `const` 是写给同事看的，MCU 上是写给链接脚本看的，它决定一块表是占 Flash 还是占 Flash **又**占 RAM。本章用 256 字节的表实测这个词的价钱。

- **能记住**：五个住处（`.text`/`.rodata`/`.data`/`.bss`/栈堆）各自放什么；`_sidata/_sdata/_edata/_sbss/_ebss` 五个符号各是什么
- **能理解**：为什么 ELF 里 `.data` 的运行地址是 RAM、文件偏移却在 Flash；`nm` 的字母为什么会"骗人"（`T` 也可以是数据）
- **能用**：`size`/`nm`/`readelf`/`objdump` 四条命令查自己工程里任何变量的住址与花费；改一行 `const` 前后能算出差额

## 先修

- [C0 嵌入式 C 是另一种 C](00-c-in-mcu.md)；[B1 四步构建](../build/01-four-steps.md) 可并行读。段是编译与链接两步的产物，链接脚本逐行讲解在 [B3](../build/03-linker-script.md)。

## 先跑起来（10 分钟 quick win，**不用开发板**）

```bash
cd code/c/01-memory-model
sh probe.sh mem          # 只跑段归属这一组
```

看到 `----- readelf -l -----` 那一行了吗？

```
LOAD  0x002000  0x20000000  0x080002a0  0x0000c  0x0002c RW
      ↑文件偏移  ↑运行地址     ↑存储地址     ↑文件里   ↑RAM 里
```

同一份东西，**运行地址在 RAM、存储地址在 Flash**，且文件里只有 12 字节、RAM 里要 44 字节。那 12 与 44 的差、以及"0x20000000 怎么会有个 Flash 的孪生地址"，就是本章要讲完的全部内容。跑不出来也别慌，下面每一步都带命令，照着敲即可。

跑之前先押两问：一个带初值的全局变量，此刻躺在固件的哪个介质里？上电之后它又住在哪？两问若答成同一个地方，第一段输出会当场纠偏。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、五段论 | `.text`/`.rodata`/`.data`/`.bss`/栈堆逐段讲解 + F407 地址实拍 | 配置 |
| 二、三段旅程 | 以 `int g_init = 5` 追踪：源码 → ELF 的 `.data`+LMA → 启动拷贝 → RAM（含两地生活全景动画） | 代码分析 |
| 三、const 经济学 | `const uint8_t lut[]` 为什么该留 Flash；256 字节对照实验 | 代码分析 |
| 四、nm/map 实操 | 亲手查符号地址；与链接脚本对照；字母与地址谁可信 | 代码分析 |

> 本章不涉及引脚设置，"库解析"在第四节以链接脚本为对象：**内存布局不是编译器单独决定的，链接脚本有一半话语权。**

## 一、五段论：先看地图，再认门牌

一张地图先收下：Flash 存粮，SRAM 住人，搬运工是 Reset_Handler。

![F407 内存地图：Flash 段落与 SRAM 段落各住着谁，Reset_Handler 负责搬运与归零](/arch/memory-map.png)

`code/stm32/00-blink` 那份链接脚本把 F407 的地址空间切成三块（`stm32f407xx.ld:24,28` 与文件头注释，数值以本工程脚本为准，芯片侧口径见 ST datasheet）：

| 区域 | 起始 | 本工程给的容量 | 谁能直接访问 |
|---|---|---|---|
| FLASH | `0x08000000` | 1024K | CPU；掉电不丢 |
| RAM | `0x20000000` | 128K | CPU + DMA |
| CCM | `0x10000000` | 64K（**本脚本未使用**） | 只有 CPU——DMA 够不着（见 [S8 DMA](../stm32/08-dma.md)） |

再看编译产物里真实的段表（`sh probe.sh mem`，`readelf -S` 摘五行）：

```
  [ 1] .isr_vector       PROGBITS   08000000 001000 000188 00   A
  [ 2] .text             PROGBITS   08000188 001188 000118 00  AX
  [ 3] .data             PROGBITS   20000000 002000 00000c 00  WA
  [ 4] .bss              NOBITS     2000000c 00200c 000020 00  WA
  [ 5] ._user_heap_stack NOBITS     2000002c 00202c 000604 00  WA
```

每一行都值得停一下：

- **`.isr_vector` 在 `0x08000000`，392 字节**：向量表。Cortex-M 复位后**先**从这里第 0 个字取栈顶、第 1 个字取复位入口。这时候 C 运行时还不存在，`.data` 里一个变量都没就位。
- **`.data` 的地址是 `0x20000000`（RAM），类型却是 `PROGBITS`（文件里有货）**：一个住在 RAM 的段，凭什么在二进制文件里占 12 个字节？因为那 12 字节是它的**初值备份**。第二节的三段旅程就从这条看起来矛盾的行列开始。
- **`.bss` 是 `NOBITS`**：文件里一个字节都不给。它只是链接器给启动代码留的一张便条："这段 RAM 请你清零"。`.bss` 的大小（32 字节）**不占 Flash，只占 RAM**。
- **`._user_heap_stack` 也是 `NOBITS`，0x604 字节**：链接脚本按 `_Min_Heap_Size = 0x200` + `_Min_Stack_Size = 0x400` 预留的下限（`stm32f407xx.ld:19-20,117-125`），末尾那个 `+4` 是 8 字节对齐的填充（`0x2000002c` 起、`ALIGN(8)` → `0x20000030`）。栈从 `_estack = 0x20020000`（RAM 顶，`ld:16`）向下长，堆从 `0x20000030` 向上长，中间这一百多 KB 是它们还没碰面的空地。
- **`.text` 里混着 `.rodata`**：上面五行里**没有 `.rodata`**。因为本工程链接脚本把 `*(.rodata)`、`*(.rodata*)` 收进了 `.text` 输出段（`stm32f407xx.ld:48-49`）。这是本站要提醒的一处工程取舍：只读数据放在可执行段里，功能完全正常，但"代码段只读、数据段另立"的这条边界就没了。**想验证代价很小**：`sh probe.sh rodata` 会从原脚本现场生成一份把 `.rodata` 单列的变体（原件不动），同一批符号的地址一格没动、字母却变了：

  ```
  原脚本（并进 .text）：  08000298 T g_ro      0800029c T k_tab
  变体脚本（单列）：      08000298 R g_ro      0800029c R k_tab
                          [ 2] .text    PROGBITS 08000188 001188 000108 00 AX
                          [ 3] .rodata  PROGBITS 08000290 001290 000010 00  A
  ```

  这就是"字母会骗人"的实锤：**T 与 R 说的是"在哪个输出段、什么属性"，不是"是函数还是数据"。**

把五段钉牢：**能执行的进 `.text`，只读数据进 `.rodata`（本工程并进 `.text`），有初值的活数据进 `.data`（双户籍），零初值的进 `.bss`（单户籍），函数里的自动变量既不在 ELF 也不在段表，它在栈上。**

![五段内存地图：代码与只读数据住 Flash，已初始化数据、零初始化数据、堆与栈住 RAM，堆向上长、栈向下长；.data 的初值另存一份在 Flash](/figures/c-01-memory-model.svg)

## 全景动画：一个变量的两地生活

下面这张图把本章要讲的五个瞬间压进一轮循环：上电时 RAM 一个字节都不可信 → `Reset_Handler` 从 `0x080002a0` 逐字搬 12 字节进 `0x20000000` → 顺手把 `0x2000000c..0x2c` 这 32 字节扫成 0 → 立起栈顶 `_estack` 让堆与栈相向生长 → 进 `main` 后所有写只落 RAM、永不回写 Flash。**图里每个数字都是 `mem_probe.elf` 的实测值**，`sh probe.sh mem` 一条命令复现。

![全局变量的两地生活动画](/anim/memory-two-homes.svg)

## 二、三段旅程：`int g_init = 5;` 的一生

取证工程 `mem_probe.c` 里一次摆了 11 个对象。本节只跟 `g_init` 走完全程，末尾回头清点其余的。

### 第一程：源码里，它只是一行声明

```c
int g_init = 5;               /* 文件作用域，有初值 */
```

此刻它有三个信息：类型（`int`，4 字节）、初值（5）、**存储期**（全程序）。第三个信息决定了它后面所有的遭遇：存储期是"全局"的变量，编译器必须为它**预先定址**，不能像自动变量那样运行时算。

### 第二程：ELF 里，它有了"户口"和"仓库"两个地址

编译链接后先查门牌：

```console
$ arm-none-eabi-nm -n --print-size build/mem_probe.elf | grep g_init
20000000 00000004 D g_init
```

地址 `0x20000000`，RAM 开头第一个字节。字母 `D`：住在数据段、全局可见。**这是它出生后的住址，不是它出生前的所在地。**

出生前它在哪？看程序头：

```console
$ arm-none-eabi-readelf -W -l build/mem_probe.elf | sed -n '/Program Header/,/Section to Segment/p'
  Type           Offset   VirtAddr   PhysAddr   FileSiz MemSiz  Flg Align
  LOAD           0x001000 0x08000000 0x08000000 0x002a0 0x002a0 R E 0x1000
  LOAD           0x002000 0x20000000 0x080002a0 0x0000c 0x0002c RW  0x1000
  LOAD           0x00002c 0x2000002c 0x080002ac 0x00000 0x00604 RW  0x1000
```

第二行是本章的心脏：

| 字段 | 值 | 含义 |
|---|---|---|
| VirtAddr | `0x20000000` | **VMA**：运行时这段要在哪（RAM） |
| PhysAddr | `0x080002a0` | **LMA**：烧录时这段实际压在哪（Flash 尾部） |
| FileSiz | `0x0000c` | 文件里真有 12 字节 |
| MemSiz | `0x0002c` | RAM 里要 44 字节（`.data` 12 + `.bss` 32） |

烧进 Flash 的固件里，`0x080002a0` 处躺着 12 个字节，它们是 `.data` 段的"初值备份"。把这份备份单独抠出来看（`objcopy -j .data -O binary`，或直接 `objdump -s -j .data`）：

```console
Contents of section .data:
 20000000 05000000 01000000 68690000           ........hi..
```

四个字节四个字节地读：`0500 0000` = `g_init` 的 5；`0100 0000` = `g_flag` 的 1；`6869 0000` = `g_msg` 的 `"hi"`（`68 69 00`）加一个对齐填充字节。正好 12 字节。**`.bss` 的对象一个都不在这里**：它们的初值全是 0，存进 Flash 是纯浪费空间，所以只在符号表里留个名字。

为什么 `VirtAddr` 和 `PhysAddr` 能不一样？链接脚本里两个词（`stm32f407xx.ld:91-100`）：

```ld
  _sidata = LOADADDR(.data);
  .data : {
    . = ALIGN(4);  _sdata = .;  *(.data)  *(.data*)  . = ALIGN(4);  _edata = .;
  } >RAM AT> FLASH
```

`>RAM` 说"运行时在 RAM"（定 VMA），`AT> FLASH` 说"存储时在 Flash"（定 LMA），`_sidata = LOADADDR(.data)` 把这个 LMA 变成一个符号交给启动代码。三个符号对上实测：`_sidata = 0x080002a0`（Flash）、`_sdata = 0x20000000`、`_edata = 0x2000000c`。

### 第三程：上电瞬间，搬运工逐字拷进 RAM

`Reset_Handler` 的反汇编里，那几个 `.word` 就是链接脚本发下来的地址条（`startup_stm32f407xx.s:35-80`，逐行走读在 [B4 启动过程](../build/04-startup.md) 第三节）：

```asm
 8000270:  20020000        @ _estack  → 装栈顶
 8000274:  e000ed88        @ SCB->CPACR → 使能 FPU
 8000278:  20000000        @ _sdata   → 拷贝目标起点
 800027c:  2000000c        @ _edata   → 拷贝目标终点
 8000280:  080002a0        @ _sidata  → 拷贝源起点（Flash！）
 8000284:  2000000c        @ _sbss    → 清零起点
 8000288:  2000002c        @ _ebss    → 清零终点
```

于是循环本体 `ldr r4, [r2, r3] / str r4, [r0, r3] / adds r3, #4` 从 `0x080002a0` 读、往 `0x20000000` 写，跑 `(0x2000000c - 0x20000000) / 4 = 3` 圈，正好 12 字节。接着 `str.w r3, [r2], #4` 把 `0x2000000c..0x2000002c` 这 32 字节扫成 0。然后 `bl main`。

**`main` 里第一次读 `g_init` 拿到 5，靠的全是这 3 圈 + 8 圈。** 这就是"三段旅程"：源码声明 → 链接器分两个地址 → 启动代码搬运。

::: tip 顺带看懂 Flash 里的字节
`0500 0000` 而不是 `0000 0005`——Cortex-M 是小端：低位字节放低地址。`objdump -s` 的右边 ASCII 栏里那个 `hi` 是 `"hi"` 的两个字符，剩下的点表示不可打印。**看二进制文件不神秘，只是没人告诉你列宽。**
:::

### 回头清点：另外八个对象的归宿

`nm -n --print-size` 的实测输出（另有 91 行同名 IRQ 别名指向 `0800028c`，此处省略）：

```
08000298 00000004 T g_ro          # const int      → Flash
0800029c 00000004 T k_tab         # const uint8_t[4] → Flash
080002a0 A _sidata
20000000 00000004 D g_init        # int =5         → .data
20000004 00000004 D g_flag        # volatile int =1 → .data
20000008 00000003 D g_msg         # char[] = "hi"  → .data（3 字节 + 对齐）
2000000c 00000004 B g_zero        # int =0         → .bss  ★
20000010 00000004 B g_uninit      # int            → .bss
20000014 00000010 b s_buf         # static uint8_t[16] → .bss
20000024 00000008 b s_local.0     # 函数内 static[8] → .bss
20020000 R _estack
```

三个反直觉的答案都在这张表里：

1. **`int g_zero = 0;` 竟在 `.bss`**。它明明写了初值。但 GCC 一看初值是 0，"清零"这件事 `.bss` 顺便就办了，何必占 Flash 四个字节再拷一遍？于是**"写没写 `=`"不重要，"初值是不是全零"才重要**。后果：`g_zero` 的值由启动代码现场清零产生，`g_init` 的值由 Flash 里的备份搬运产生，两条路来源不同，`main` 里看起来一样自然。
2. **`volatile int g_flag = 1;` 照样在 `.data`**。`volatile` 不改住址，只改访问方式：它管的是"每次都要真访存"（[C3](03-volatile.md)），跟"住在哪"是两个正交的问题。**volatile 是访问权限，段是存储地点。**
3. **函数里的 `static uint8_t s_local[8]` 在 `.bss`，而同一个函数里的 `int auto_var = 3;` 连符号都没有**。`nm build/mem_probe.elf | grep auto_var` 查无此人：自动存储期的变量活在栈上，链接期根本不存在。你只能从 `probe` 的反汇编里看到它（`-O0` 实测）：

   ```asm
     80001a2:  movs r3, #3
     80001a4:  str  r3, [r7, #0]      @ 栈帧里的一个槽，函数返回即蒸发
   ```

   写在函数里的 `static` 是"寿命全程序、可见性本文件"，所以它有固定地址（`b` = 局部符号）；`auto_var` 只有"这次调用的栈帧"这个临时地址。**`static` 与 `auto` 的差别是住址的差别，不是位置的差别。**

还有第四点最容易看错：`g_ro` 的地址是 `0x08000298`（Flash 里！），`nm` 的字母却是 `T`（"代码段符号"）。**因为本工程的链接脚本把 `.rodata` 并进了 `.text` 输出段**（`ld:48-49`），链接器眼里它就在代码段里。紧跟着的一行反证（`sh probe.sh mem` 的"字面量住哪"那一节）：

```
 8000288 2c000020 fee70000 666c6173 68000000   ,.. ....flash...
```

`0x08000290` 起是那串 `"flash"` 字面量（源码里 `const char *lit = "flash";`），**没有符号名，但确实在 Flash**。而 `lit` 这个指针本身是自动变量，活在栈上。**同一行代码里，字符串和指针分住两种介质**，这是本章最省话的一张图。

## 三、const 经济学：一个词值 256 字节 RAM

一张 256 字节的查找表，两种写法，各编译一次（`sh probe.sh lut`，实测值）：

| 写法 | `.text` | `.data` | `lut` 的 `nm` 行 | 第二个 LOAD 段 |
|---|---|---|---|---|
| `uint8_t lut[256] = {1,2,3};` | 148 | **256** | `20000000 00000100 D lut` | `VirtAddr 0x20000000 PhysAddr 0x0800021c FileSiz 0x100 MemSiz 0x700` |
| `const uint8_t lut[256] = {1,2,3};` | **404** | **0** | `0800021c 00000100 T lut` | `VirtAddr 0x20000000 PhysAddr 0x0800031c FileSiz 0x00000 MemSiz 0x600` |

三个数对着读：

- **RAM 从 256 字节变成 0 字节**：`.data` 那一列从 256 塌到 0，第二个 LOAD 段的 `FileSiz` 从 `0x100` 变成 `0x00000`，Flash 里不再需要为它存备份，启动代码也少拷 64 个字。**一个 `const` 换 256 字节 RAM**，在 128K 的 F407 上不算什么，在 RAM 只有几十 KB 的小型号上就是两位数的家底。同一笔交易的金额由你手上的 RAM 总量决定，不由 `const` 决定。
- **Flash 从 148 涨到 404**：`.text` 多出 256 字节（404 − 148 = 256），表还在，只是**只住 Flash 了**。所以"加 const 省一半"的说法要看口径：省的是 RAM 那一半，Flash 那一半本来就要花（初值也得存）。
- **`MemSiz 0x700 → 0x600`**：可写版的 `MemSiz` = 256(`.data`) + 0x600(堆栈预留) = 0x700；只读版只剩堆栈预留。链接器的 RAM 记账直接少了一笔。

为什么 const 数组**该**留 Flash：查表是只读行为，从 Flash 读和从 RAM 读，Cortex-M 都支持直接寻址（XIP），结果一模一样；差别只在访问速度（Flash 有等待周期，RAM 没有；量化数字要按你的 `FLASH_ACR` 配置与主频实测，这里不给结论）。**用一点访问延迟，换整块 RAM 归还**，这是嵌入式里最划算的一笔常规交易。

反过来，什么时候 `const` 不该乱加？表要被运行时改写（比如自动校准出来的补偿表）就不能 `const`，只能 `__attribute__((section(".data")))` 或者干脆普通全局；`const` 数组想"存初值 + 运行时改"就得自己写"从 Flash 模板拷一份到 RAM 工作区"的两段式，这正是 [P10 Flash/NVS/OTA](../esp32/10-flash-nvs-ota.md) 里出厂参数的标准做法。

## 四、nm/map 实操：把符号表变成审计工具

前面三节的所有结论都来自四条命令。本节把它们排成一张可背的检查单（`sh probe.sh` 会连着跑完）：

| 想知道 | 命令 | 实测里看哪一行 |
|---|---|---|
| 每段多大、住在哪 | `size -A build/mem_probe.elf` | `.data 12 / .bss 32 / ._user_heap_stack 1540` |
| 某个变量住哪个段、几个字节 | `nm -n --print-size build/mem_probe.elf` | `20000008 00000003 D g_msg`（3 字节，不是 4） |
| 文件里到底有几字节货 | `readelf -W -l build/mem_probe.elf` | 第二 LOAD 行 `FileSiz 0x0000c / MemSiz 0x0002c` |
| 初值备份长什么样 | `objdump -s -j .data build/mem_probe.elf` | `05000000 01000000 68690000` |
| 谁在拷它 | `objdump -d build/mem_probe.elf \| sed -n '/<Reset_Handler>:/,/^$/p'` | 字面量池里 `080002a0` |
| 全工程最大对象是谁 | `less build/mem_probe.map`（`-Wl,-Map=...` 产出） | `mem_probe.map` 里 `.bss` 段最大项是 `s_buf` 16 字节 |

字母表背这张（大写=全局可见，小写=局部/`static`）：

| 字母 | 含义 | 本章实例 |
|---|---|---|
| `T`/`t` | 代码段（含本工程并入的 `.rodata`） | `T probe`、**`T g_ro`（数据！）** |
| `D`/`d` | `.data`（有非零初值） | `D g_init`（大写=全局可见；同一声明加 `static` 就变小写 `d`，与下面的 `b`/`t` 同一套规则） |
| `B`/`b` | `.bss`（零初值） | `B g_zero`、`b s_buf` |
| `R`/`r` | 只读段 | `R _estack`、`r g_pfnVectors` |
| `A` | 绝对值符号（不是地址，是常量） | `A _sidata`、`A _Min_Heap_Size` |
| `W`/`w` | 弱符号 | `W Reset_Handler`、`W GPIOE_IRQHandler` |

两条读表纪律：

1. **字母会骗人，地址不会。** 判断"占 Flash 还是占 RAM"唯一可靠的依据是地址前缀：`0x0800xxxx` 是 Flash，`0x2000xxxx` 是 RAM。`g_ro` 顶着 `T` 却住在 Flash，就是 `ld:48-49` 那两行的直接后果；`sh probe.sh rodata` 生成的变体脚本（把 `.rodata` 单列）里，同一个符号字母变成 `R`、地址一格不动。另一个方向的验证也很快：把 `g_init` 加上 `static` 重新链接，同一地址 `0x20000000`，字母从 `D` 变 `d`，**变的只是可见性，住址没变**。**先查脚本，再下结论。**
2. **`nm` 的总和不等于固件大小。** `readelf -S` 里那些 `.debug_*`（本工程 `size -A` 的 Total 是 26775，而真正进 Flash+RAM 的只有 `392+280+12+32+1540 = 2256`）是调试信息，`objcopy -O binary` 之后全部蒸发。想知道烧进去多少字节，用 `size -A` 挑那五行加总，或者看 `.bin` 的文件大小。别拿 Total 吓人（也**别拿它做站内统计**，站内数字一律走 `npm run docs:gen`）。

`_Min_Stack_Size` 那 0x400（1KB）是**下限检查**，不是上限：链接期只要 RAM 剩余装得下 `._user_heap_stack` 就放行，运行期栈真溢出它不管。本工程实测高水位：`_ebss` 之后预留段跑到 `0x20000630`，离 `_estack = 0x20020000` 还有很大空地——空地多大？`(0x20020000 - 0x20000630) / 1024 ≈ 126.5 KB`。想把这个数变成硬约束，得自己在链接脚本加 `. = ASSERT(...)`，见 [B5 map 与体积](../build/05-map-size.md)。

## 附录：工程完整源码

十一个对象的段归属现场（正文所有地址、大小、字母都出自它）：

<<< ../../code/c/01-memory-model/mem_probe.c

const 对照实验：

<<< ../../code/c/01-memory-model/lut_probe.c

一条命令跑完全部取证（正文每条命令的包装在这里）：

<<< ../../code/c/01-memory-model/probe.sh

## 记忆锚点

::: tip 一句话记住
**有初值住 `.data`（Flash 存粮票，RAM 住人），没初值住 `.bss`（只分房不带行李），const 留 Flash（不动产的忠实租客）。**
粮票由 `_sidata` 发、`_sdata.._edata` 收货，搬运工是 `Reset_Handler` 那三圈循环。
**判断占哪种介质，看地址前缀，不看 `nm` 字母。**
:::

**延伸**：内存模型与链接脚本（[B3](../build/03-linker-script.md)）直接对应；`.data` 搬运由启动代码（[B4](../build/04-startup.md)）完成；指针操作这些地址（[C2](02-pointer.md)）是寄存器访问的基础。

## 实物实验

- **本机已全部实测（不需要板子）**：`cd code/c/01-memory-model && sh probe.sh`，把 `nm` 里 `g_zero` 那行、`readelf -l` 第二行的 `FileSiz/MemSiz`、`.data` 那 12 个字节抄进实测笔记，注明工具链版本（本机 xPack `arm-none-eabi-gcc 15.2.1`，2026-10-06）。
- **板上（三步，编译期已核实、肉眼现象待回填）**：
  1. GDB 里 `p &g_init` 与 `p _sidata`，一个 `0x2000xxxx`、一个 `0x0800xxxx`，"人在 RAM、粮票在 Flash"落在两条命令上；
  2. `set g_init = 99`、`p g_init` 确认改了，`monitor reset` + `load` 之后再 `p g_init`，**又变回 5**，因为 Flash 里的备份没动；
  3. 把 `Reset_Handler` 的拷贝循环上下断点（`b *0x0800024c` 那种形式，地址按你的构建查 `nm`），单步看 `p g_init` 从垃圾值变成 5 的那一刻。
- 观测点：GDB/`p`，不需要示波器。
- 预期现象：第 2 步复位后回到 5，这一条把"段"从抽象名词变成能按出来的事实。

::: warning 本轮取证状态
上述第 1–3 步需要接 F407 与 ST-Link，本轮写这一版时手边未接入，**板上现象待回填**；正文里所有地址、字节数、段大小均已在 `xPack arm-none-eabi-gcc 15.2.1`（`-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard -O0 -g3`，链接 `code/stm32/00-blink/stm32f407xx.ld`）下实测，命令与输出记录在 `code/c/01-memory-model/README.md`。
:::

## 常见坑

1. **`int x = 0;` 你以为在 `.data`，其实在 `.bss`**：后果不是 bug，而是你对 RAM 的账算错：加 `= 0` 不会让它在 Flash 里多占四字节，改初值也不会改变镜像大小。要看真相，`nm` 一个字母就够了（出现频率第一，因为几乎人人踩过）。
2. **以为 `.bss` 不占空间**：它不占 Flash 但**照占 RAM**。`uint8_t buf[100*1024];` 一句就爆 128K 的 RAM，而且链接脚本没写 ASSERT 时它可能真的链接通过，上电踩内存。自查：`size -A` 里 `.bss` 那一行。
3. **大初始化数组放错地方**：`uint8_t lut[1024] = {...}` 既吃 Flash（备份）又吃 RAM（本体）；加 `const` 立省 1024 字节 RAM。第三节实测：256 字节的表，`.data` 从 256 变 0。
4. **中断开启太早，`.data` 还没搬完**：如果你在 `Reset_Handler` 的拷贝循环之前就让能了某个中断（或把初始化搬进了启动文件的早期），中断里读全局变量读到的是 Flash 备份还没到位的垃圾值。现象是"偶发、换个编译器版本就变"。纪律：**外设初始化必须在 `main` 之后，别塞进启动文件的搬运前面**（见 [B4](../build/04-startup.md)）。
5. **把 `nm` 的字母当段名读**：`T g_ro` 不是"函数"，是"在 `.text` 输出段里"，本工程 `.rodata` 并进了 `.text`（`ld:48-49`）。看到字母与直觉不符，先去读链接脚本，别先改代码。
6. **拿 `volatile` 当段归属开关**：`volatile int x = 1;` 照样在 `.data`。想强制某个对象去特定区域用的是 `__attribute__((section(".xxx")))` / `__attribute__((aligned(n)))`，跟 `volatile` 没关系。
7. **忘了 `--gc-sections` 会删掉"没人用的变量"**：`-fdata-sections` + `-Wl,--gc-sections` 下，没有引用者的全局变量直接不进固件，你会以为"我明明定义了，`nm` 里怎么找不到"。本工程的对策是写一个真的引用者 `sink()`（`mem_probe.c:15`，每个变量取一次地址），需要保留但不想引用时用 `__attribute__((used))`。
8. **拿调试信息当固件体积**：`size` 的 Total 26775 里绝大部分是 `.debug_*`。汇报体积要么报 `.bin` 大小，要么报 `size -A` 里那五行加总，**并且别让这些数字进站内正文**，站点统计一律由 `npm run docs:gen` 生成。

## 短自测

**1. `static int counter;` 和 `static int counter = 0;` 有区别吗？`nm` 里分别是什么字母？**

<details><summary>答案</summary>

在这份 GCC 下**没有区别**：两者都进 `.bss`，字母都是 `b`（`static` → 局部符号）。`int counter = 5;` 才进 `.data`（字母 `d`）。判据是"初值是否全零"，不是"有没有写等号"。实测对照就在本章第二节：`B g_zero` 与 `D g_init`。

</details>

**2. 把 `stm32f407xx.ld` 里 `.data` 的 `AT> FLASH` 删掉（只留 `>RAM`），程序还能跑吗？**

<details><summary>答案</summary>

跑不了（或者说：初值全错）。删掉 `AT>` 后 LMA 与 VMA 相同，链接器认为这段"本来就住在 RAM"，于是 `.data` 的初值备份不再被安排进 Flash 镜像；`Reset_Handler` 仍然去 `0x2000xxxx` 拷 `0x2000xxxx`（甚至 `_sidata` 会变成 RAM 地址），搬回来的全是没定义的内容。现象是"全局变量的初值全都是随机值"。**`.data` 的双重户籍靠 `AT>` 建立**，逐行推导见 [B3](../build/03-linker-script.md)。

</details>

**3. `size -A` 显示 `.data 12 / .bss 32`，为什么 `.data` 里 `g_msg` 只有 3 字节却写成 4 的对齐？**

<details><summary>答案</summary>

`ld:94,98` 两个 `. = ALIGN(4);` 把段的头尾对齐到 4 字节；实测 `objdump -s -j .data` 的 `68690000` 里最后那个 `00` 是填充。收益：`.data` 里的每个 4 字节对象都落在 4 的边界上，启动拷贝循环才敢固定 `adds r3, r3, #4` 一个字一个字搬：**搬运循环的简单，是链接脚本的对齐换来的**。

</details>

**4. 你想让一张 4KB 的波形表既不占 RAM、又要能被 DMA 读走。放到 CCM（`0x10000000`）行不行？**

<details><summary>答案</summary>

不行。CCM 只有 CPU 直连，DMA 够不着，硬塞进去的后果是"CPU 看着数据对，DMA 搬出来全是 0/垃圾"（[S8](../stm32/08-dma.md) 有专门一小节讲这个坑）。正确做法：留在 Flash（`const`）+ DMA 从 Flash 读，或放主 SRAM `0x20000000`。只有"纯 CPU 访问、追求零等待"的大缓冲才值得搬去 CCM。

</details>

## 对照表：本章概念 → 仓库落点

| 概念 | 仓库落点 |
|---|---|
| 11 个对象的段归属现场 | `code/c/01-memory-model/mem_probe.c`（附录全文内嵌） |
| const 对照实验 | `code/c/01-memory-model/lut_probe.c`（用 `-DLUT_CONST` 切） |
| 全部取证命令 | `code/c/01-memory-model/probe.sh`（`sh probe.sh [mem\|lut\|boot]`） |
| 本机实测数值与记录 | `code/c/01-memory-model/README.md` |
| `>RAM AT> FLASH` / `_sidata` | `code/stm32/00-blink/stm32f407xx.ld:91-100`，逐行讲解 [B3](../build/03-linker-script.md) |
| `.rodata` 并进 `.text`（`T g_ro` 的成因） | 同上 `:48-49` |
| `_Min_Heap_Size/_Min_Stack_Size/_estack` | 同上 `:16,19-20,117-125` |
| 拷贝与清零循环 | `code/stm32/00-blink/startup_stm32f407xx.s:48-72`，走读 [B4 第三节](../build/04-startup.md) |
| `volatile` 与段归属正交 | [C3 volatile](03-volatile.md) |
| DMA 够不着 CCM | [S8 DMA](../stm32/08-dma.md) |
| map 文件与体积审计 | [B5 map 与体积](../build/05-map-size.md) |

## 你做到了

- 任何一条变量声明，能当场说出"住哪个段、占哪种介质、几个字节"，并且**能用 `nm`/`readelf` 自证**；
- 能解释 `_sidata`/`_sdata`/`_edata`/`_sbss`/`_ebss` 五个符号：谁发的（链接脚本）、谁消费的（`Reset_Handler`）、怎么对上实测地址；
- 会用 `const` 做预算：一个词省 256 字节 RAM，也能说清这笔交易在什么时候不划算。

回到开场那个「其实没有的 5」：它出厂就躺在 Flash 里，上电后由启动文件里的拷贝循环搬进 RAM。谁搬的、从哪搬、搬几个字节，这三问你现在都有凭证可查，工具就是本章第四节教你的那几件。

<div class="achievement">
✅ 下一站：<a href="02-pointer.html">C2 指针</a>：<code>*(volatile uint32_t *)0x40021418</code> 凭什么能点灯？地址、类型、解引用各管一件事。
</div>
