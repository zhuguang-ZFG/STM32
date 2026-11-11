# B3 链接脚本 · 资料与取证清单（2026-10-06 建档）

写作前的一手材料盘点：**已在手**、**已实测**、**待实测**、**缺口**。
本章拆的是 `code/stm32/00-blink/stm32f407xx.ld`（136 行，3,512 B，md5 前缀 `663daa4b`）。

## 1. 已在手，可直接引用

| 材料 | 位置 | 用途 |
|---|---|---|
| 本工程手写图纸（主拆对象） | `code/stm32/00-blink/stm32f407xx.ld`；01/02/03 三工程副本**逐字节相同** | 逐行讲解 |
| 唯一的工程间差异 | `code/rtos/01-freertos-lab/stm32f407xx.ld`：只把 `/DISCARD/ { libc.a(*) libm.a(*) libgcc.a(*) }` 换成三行注释（要用 `snprintf`，libc 不能丢） | "同一张图纸为什么会分叉"的现成例子 |
| 官方 GCC 图纸（本轮取到） | **本机** `.trellis/ref/st-linker/STM32F407VGTX_FLASH.ld`，5,827 B，STM32CubeF4 @`60c8abe0ae88a23bbd1c925358330031e36dd20f`（同目录 PROVENANCE.txt）。⚠️ `.trellis/ref/` 与 `code/**/build/` 都在 `.gitignore` 里，**不进仓库**：正文只能引用文件名+commit+路径，不能给站内链接 | 四件套的"库源码对照"；`CCMRAM` 地块与 `.ccmram` 段的官方写法 |
| CMSIS 设备头（已在库） | `.trellis/ref/cmsis/stm32f407xx.h:906-907`：`FLASH_BASE 0x08000000`、`CCMDATARAM_BASE 0x10000000`（注释 "64 KB"），@`9192c7b9` | F407 地址与容量（第二来源） |
| RM0090 **Rev 22** 全文 | 本机 `D:\Temp`/`/tmp/rm0090.pdf`，21,385,881 B，sha256 `f3ff2322eec21f4e49081f68481b764506eee81dba6031bc767e2f8955b27cca`；**PDF 不入库**，正文引原文+页码 | MEMORY 地块与 CCM 结论的裁决来源 |
| GNU ld 手册节号 | 目录已核对：3.4.1 ENTRY、3.5.3/3.5.4 PROVIDE(_HIDDEN)、3.6 SECTIONS、3.6.3 Output Section Address、3.6.4.4 Input Section and Garbage Collection（KEEP）、3.6.7 Output Section Discarding（`/DISCARD/`）、3.6.8.2 Output Section LMA（`AT>`）、3.6.8.3/3.6.8.6 对齐与区域、3.7 MEMORY、3.10.5 The Location Counter、3.10.9 Builtin Functions（`LOADADDR`） | 语法条款出处 |
| 别人家的自动生成图纸 | **本机**（`code/esp32/*/build/` 不入库）：`esp-idf/esp_system/ld/memory.ld`（5,870 B）、`sections.ld`（**97,538 B**） | "手写 136 行 vs 生成 9.7 万字节"的对照；REGION/PROVIDE 的真实工程用法。正文要说明这是 ESP-IDF 构建时生成的，读者自己 `idf.py build` 就有 |
| 本站已有变体 | `code/c/01-memory-model/build/stm32f407xx-rodata-sep.ld` 由 `probe.sh rodata` **按需生成**（把 `.rodata` 从 `.text` 单列） | 已在 C1/B2 出现，B3 承接"那个把 .rodata 并进 .text 的决定" |

### RM0090 原文（照抄，勿改写）

- §2.1 System architecture，印刷页 **59**：
  > "The 64-Kbyte CCM (core coupled memory) data RAM is **not part of the bus matrix and can be accessed only through the CPU**."
  同页还列出 8 个 master（Cortex-M4 I/D/S-bus、DMA1/DMA2…）与 7 个 slave，其中 SRAM 是 "Main internal SRAM1 (**112 KB**) + Auxiliary internal SRAM2 (**16 KB**)"。
- §2.3.1 Embedded SRAM，印刷页 **68**：
  > "SRAM1 and SRAM2 mapped at address 0x2000 0000 and accessible by all AHB masters" / "CCM (core coupled memory) mapped at address **0x1000 0000** and accessible only by [the CPU]" / F405/407 为 "plus **192 Kbytes** of system SRAM"（= 112 + 16 + 64，**含 CCM**）。

⚠️ 站内既有引用是 **Rev 18**（Table 10 p.80、§7.2.3 等，见 `10-06-stm32-depth-animations/research/baseline-and-sources.md:103,117`），本轮下到的是 **Rev 22**。页码不同，B3 引用必须逐处标 Rev，不能沿用 Rev 18 的页码。

## 2. 已实测（今天复跑，命令与输出对应）

工具链：xPack `arm-none-eabi-gcc` 15.2.1；`cd code/stm32/00-blink && mingw32-make`（`-O0 -g3`，链接本工程 `.ld`）。

- `size`：**text 660 / data 0 / bss 1536**；`build/blink.bin` **660 B**。
- map：`.isr_vector 0x08000000 0x188`、`.text 0x08000188 0x10c`（0x188+0x10c=0x294=660，**代码终点即数据镜像起点**）、`.data 0x20000000 0x0 load address 0x08000294`、`.bss 0x20000000 0x0`。
- `nm` 界碑：`_estack=0x20020000`、`_etext=_sidata=0x08000294`、`_sdata=_edata=_sbss=_ebss=0x20000000`。
- `bin` 头 8 字节：`00 00 02 20 | 89 01 00 08` → 小端读作 **0x20020000**（= `_estack`，图纸第 16 行）与 **0x08000189**（复位入口，最低位是 Thumb 态）。**图纸 → 二进制第 0 项**这条链在这里闭合，是本章开头的钩子。
- `readelf -SW`：`._user_heap_stack NOBITS 0x20000000 size 0x600`——**blink 那 1536 字节 RAM 全部来自堆栈检查段**（`_Min_Heap_Size 0x200` + `_Min_Stack_Size 0x400`），`.bss` 本身是 0。B2 现有写法"RAM 0+1536"没错但把来源记在 bss 名下，B3 里要讲清这 1536 是谁。
- B2/C1 的三个 `_sidata` **不是矛盾**，是三具标本：`blink.elf` = `0x08000294`（今日复现）；`elf_probe.elf` = `0x08000244`（B2 第三刀）；C1 的 `g_init/g_flag/g_msg` 标本 = `0x080002a0`。B2 精髓#2 原先不指名，已补"0x244 属于 elf_probe"。

## 3. 待实测（都**不需要开发板**，写正文前必须跑出来）

1. **KEEP 与 `--gc-sections`**：临时删掉 `KEEP(*(.isr_vector))` 里的 `KEEP` 重建，`readelf -S`/`objdump -s -j .isr_vector` 看向量表是否被回收、0x08000000 变成什么。产出：真实 map 差异，不是"听说会没"。
2. **去掉 `AT> FLASH`**：`readelf -l` 的 `PhysAddr` 会从 `0x0800xxxx` 变成 `0x2000xxxx`，`nm _sidata` 同步变 RAM 地址。C1 现在这段是思想实验（`docs/c/01-memory-model.md:337`），B3 给实测输出并回指 C1。
3. **RAM LENGTH 改小 + 大数组**：抄 `ld` 报错原文（预期形如 `region 'RAM' overflowed by <N> bytes`，并确认报的是哪个段触发）；骨架页承诺了这个"实物实验"，无板可做，改标"链接期实验"。
4. **非法区域属性复现**：`RAM (xrw)` 改回 `(xrwah)`，取 `invalid character (104) in flags` 原文（104 = `h`）——本工程 `.ld:25-27` 注释已记，需真跑一遍取证。
5. **CCM 实战（本章最值钱的一段）**：按官方模板加 `CCMRAM (xrw) : ORIGIN = 0x10000000, LENGTH = 64K` + `.ccmram : { _sccmram=. ... } >CCMRAM AT> ROM`，把一个大数组 `__attribute__((section(".ccmram")))` 放进去，然后量：
   - map 里是否真落在 `0x10000000`；
   - **`objcopy -O binary` 的下场**：0x08000000 与 0x10000000 之间不连续，bin 会被填充成天文数字（实测字节数！）或报警——由此引出"烧 CCM 要用 `.hex`/分段 objcopy"的正解。这是网上教程极少讲、又一定会踩的坑；
   - `.ccmram AT> ROM` 有初值而**本工程启动文件不搬 `.ccmram`**（官方模板同理，靠 `_siccmram` 由代码搬）→ 实测"放了初值却读到 0"，与 B4 的搬运循环对照；
   - CCM 只能被 CPU 访问的依据：RM0090 Rev 22 p.59 原文 + 官方 `.ld` 把 CCMRAM 单独列块，两处互为佐证。
6. **`-Wl,--trace` / `ld --verbose`**：看链接器实际吃了哪张图纸、内置默认脚本长什么样（"没有 -T 时谁在分配房间"，回答新手"为什么我的 .rodata 不见了"）。

## 4. 缺口与顺带要修的账

- **`docs/stm32/08-dma.md:122/154/163` 的"DMA 够不着 CCM"目前是**无出处断言**（依据表里没有 RM0090 行）。B3 成稿时顺手补：RM0090 Rev 22 §2.1 p.59。
- RM0090 只在下机本机，仓库里不入库（21 MB）；若要求"读者也能复现引用"，`docs/guide/manuals.md` 已有下载指引，可补一行"Rev 22，正文引用一律标版本"。
- B3 骨架里的"MEMORY 地块"节需改成 **Flash / SRAM1+SRAM2 / CCM** 三块口径，并说明 128K 是 112+16 两块（RM0090 p.59）——现在手写 `.ld` 只有一个 `RAM (xrw) : 0x20000000, 128K`，正好讲"图纸可以把连续地址合并成一块，芯片里仍是两块"。
- 四份逐字节相同的 `.ld` 副本是否收敛成一份共享：留待 B7 构建系统讲，B3 只在"为什么副本会分叉"处点一句。
