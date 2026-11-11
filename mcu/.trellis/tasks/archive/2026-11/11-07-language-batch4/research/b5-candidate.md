---
title: B5 map 与体积：谁吃了我的 Flash
status: done
difficulty: 2
minutes: 25
---

# B5 map 文件与体积审计：谁吃了我的 Flash/RAM

> 🎯 加了一个库，固件从 20KB 涨到 200KB——谁干的？map 文件就是"固件户口本"：每个符号多大、住哪、谁引进的，一查便知。嵌入式工程师的基本功：**先审账，再优化**。

## 本章精髓

1. `size` 的三列是三种资源：text（Flash：代码+只读）、data（Flash 存初值+RAM 住人）、bss（纯 RAM）：Flash 占用=text+data，RAM 占用=data+bss。
2. map 文件的三板斧各查一件事：Archive member 表查谁被从库里捞出来，Memory Map 查每个符号的落位， discarded 段查谁被 gc-sections 辞退。
3. 优化的顺序：先看大项（库/表/缓冲区），再谈 -O 级别；方向错了 -O2 也救不了你。

- **能理解**：解释为什么带初值的数组让 Flash 和 RAM 双涨，加 const 后 data 回落、text 涨；再解释为什么 bin 比 text+data 大。
- **能用**：`size`/`nm --size-sort`/`map` 三把刀完成一次"揪出大尾巴"审计。

## 先修

- [B2 ELF](02-elf.md)、[B3 链接脚本](03-linker-script.md)。

## 先跑起来（10 分钟 quick win）

跑之前先押：这个只点灯的小固件，Flash 里体积最大的单个符号会是谁？主函数、启动代码、还是库里的东西？押一个名字，再看按大小排队的队尾。

```bash
arm-none-eabi-size build/blink.elf
arm-none-eabi-nm -S --size-sort build/blink.elf    # 符号按大小排，倒数五个就是大户
grep -A3 "Discarded input" build/blink.map | more  # 谁被辞退了
```

`size` 的三列用来算 Flash/RAM 占用；要找体积最大的几个符号，就看 `nm --size-sort`；要查 gc-sections 辞退了谁，就看 `map` 的 Discarded 段。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| size 三列 | Flash=text+data、RAM=data+bss 的推导与验证 | 配置 |
| map 三板斧 | Archive 表/Memory Map/Discarded 逐段实读 | 库解析 |
| nm 审计 | --size-sort 找大户；A/B/C 实验各一次 | 代码分析 |
| 瘦身工具箱 | -ffunction-sections+--gc-sections、-Os、去未用库、const 归位 | 配置 |
| CCM 腾挪 | 大缓冲搬进 CCM 的链接脚本配合（B3 联动） | 配置 |

**map 分析的下游应用**：审计完体积，遇到"Flash 不够装"或"要做 IAP 双区"，就回看 [S13 Flash 与 IAP](../stm32/13-flash-iap.md) 的分区布局，以及 [B3 链接脚本](03-linker-script.md) 的段排布。这里分清两件事：map 文件告诉你"现在住哪"，链接脚本决定"将来搬哪"。

## 动画：size → map → nm 三板斧

size 三列算总账，map 文件查明细，nm --size-sort 找大户。盯住"先审账再优化"五个字，这是体积审计的核心纪律。

![Map 文件与体积审计](/anim/map-size-audit.svg)

## 一、size 三列：Flash 与 RAM 各吃哪几份

账目公式先看图：三列输入两条公式，Flash 与 RAM 各吃哪几份一目了然。

![size 三列的账：text/data/bss 汇入 Flash=text+data 与 RAM=data+bss](/arch/map-audit.png)

`arm-none-eabi-size blink.elf` 输出三列（本站 00-blink 实测，具体数以你本地 build 为准）：

```text
   text	   data	    bss	    dec	    hex	filename
   280	     12	     32	    324	    144	blink.elf
```

三列对应三种资源，推导靠 [B3 链接脚本](03-linker-script.md) 的段属性：

| 列 | 装的是什么 | 住哪 | 算进谁的占用 |
|---|---|---|---|
| **text** | 代码（.text）+ 只读数据（.rodata）+ 向量表 | Flash | Flash |
| **data** | 有初值的全局变量（.data） | 运行在 RAM，**初值存 Flash** | **Flash + RAM 各一份** |
| **bss** | 零初始化的全局变量（.bss） | 纯 RAM（启动时清零，不占 Flash） | RAM |

两条占用公式立刻出来：

$$\text{Flash 占用} = \text{text} + \text{data}$$
$$\text{RAM 占用} = \text{data} + \text{bss}$$

为什么 data 算两份？因为 .data 有初值，初值必须存在断电不丢的 Flash 里（[B3](03-linker-script.md) 的 `AT> FLASH`），运行时启动代码把它搬到 RAM（[B4 启动](04-startup.md) 的 Reset_Handler 搬运循环）。所以 data 在 Flash 里存初值、在 RAM 里住运行值，两份都吃。bss 没初值，启动时清零即可，只吃 RAM。

> **【注】** 这是 [C1 内存模型](../c/01-memory-model.md) "const 经济学"的账本版：const 数组进 .rodata（算 text，只吃 Flash），可写数组进 .data（算 data，Flash+RAM 双吃），未初始化数组进 .bss（只吃 RAM）。B5 审计就是把 C1 的段归属用 size 数字验证一遍。

## 二、map 三板斧：Archive 表、Memory Map、Discarded

map 文件是链接器 `ld` 加 `-Map=` 旗生成的"链接户口本"（00-blink 的 Makefile 里 `... -Map=build/blink.map`）。三块内容各有用途：

**第一板斧：Archive member 表**：列出从哪些 `.a` 静态库里捞了哪些 `.o`。如果链接了 `libc.a`，这里能看到"为了 printf 捞了 `vfprintf.o`、`__assert.o`..."，库被引用的粒度一目了然，是 gc-sections 是否生效的证据。

**第二板斧：Memory Map**：每个 `.o` 的每个段落进哪个地址、每个符号多大住哪。找 `main.o` 的记录就能看到 main 函数多大、它引用了谁。这是"揪大户"的主要战场：按段汇总的数字告诉你 `.text` 里哪块最大。

**第三板斧：Discarded input**：被 `--gc-sections` 辞退的段。链接器发现某段没被任何入口（entry/中断向量）引用，就把它丢弃，不进最终 `.elf`。这里列出"谁被辞了"。如果某本该保留的段出现在这里，说明链接脚本没把它标 `KEEP()`（[B3](03-linker-script.md) 的 KEEP 用法）。

## 三、nm 审计：按大小排队找大户

`nm -S --size-sort` 把所有符号按体积从大到小排，倒数五个就是固件里最占地方的：

```bash
arm-none-eabi-nm -S --size-sort build/blink.elf | tail -10
```

典型大户（00-blink 量级很小，加库后才看得出）：

| 大户类型 | 典型来源 | 瘦身手段 |
|---|---|---|
| `vfprintf` 一族 | printf 带浮点 | 不用 `%f` 就能关浮点版（`-u _printf_float` 反向） |
| 大 `const` 表 | 正弦表/字库/查找表 | 必要的 Flash 开销，挪不走的 |
| 大缓冲区 | `uint8_t buf[4096]` | 搬进 CCM（第五节）或改环形 |
| 启动代码 | `crt0.o`/`startup_*.s` | 固定开销，几十百来字节 |

审计纪律：**先看大项再谈优化级别**。一个 4KB 的未用数组比 `-O2` 到 `-Os` 省的那几百字节大一个数量级。方向错了 -O2 也救不了你。

## 四、瘦身工具箱：四把刀按顺序用

1. **`-ffunction-sections -fdata-sections` + `--gc-sections`**：把每个函数/数据各放一个段，链接时丢弃没引用的。这是"没用到的库函数不进固件"的前提：不加 `-ffunction-sections`，整个 `.o` 要么全进要么全不进，gc-sections 无从下手。00-blink 的 Makefile 已默认开这套旗。
2. **`-Os`**：优化体积（比 -O2 更省 Flash，代价是速度略慢）。Flash 敏感场景首选；速度敏感的热路径单独标 `-O2`/`-O3`。
3. **去未用库**：链接了 `libc` 但没用 `malloc`，gc-sections 会把 `malloc.o` 辞退（前提是 `-ffunction-sections`）。整库链接不可怕，gc-sections 救场。
4. **const 归位**：把有初值的"只读"数组标 `const`，从 .data（Flash+RAM 双吃）挪进 .rodata（只吃 Flash）。C1 的"const 经济学"在 B5 的账本上直接体现：加一个 `const`，data 降、text 涨、RAM 净省。

## 五、CCM 腾挪：大缓冲搬进核心耦合内存

F407 除了 128KB SRAM，还有 **64KB CCM RAM**（Core Coupled Memory，0x10000000）——CPU 直连、零等待、但 **DMA 访问不到**。适合放 CPU 专用的大缓冲（DMA 缓冲不能放这，[S8](../stm32/08-dma.md) 的坑）。

链接脚本加一段（[B3](03-linker-script.md) 的 MEMORY 范式）：

```ld
MEMORY { RAM (xrw) : ORIGIN=0x20000000, LENGTH=128K
         CCM (xrw) : ORIGIN=0x10000000, LENGTH=64K }
/* 大缓冲指定进 CCM */
.bss.dma_buf (NOLOAD) : { *(.dma_buf) } > RAM      /* DMA 缓冲留 RAM */
.bss.cpu_buf  (NOLOAD) : { *(.cpu_buf)  } > CCM    /* CPU 专用缓冲进 CCM */
```

代码侧给缓冲加 section 属性：`__attribute__((section(".cpu_buf")))`。CCM 腾挪的收益：128KB 主 SRAM 留给 DMA/栈/堆，64KB CCM 专门放大缓冲，两个内存域分工，不互相挤。代价：CCM 的数据 DMA 搬不动，配错了 DMA 静默失败（[S8](../stm32/08-dma.md)）。

## 记忆锚点

::: tip 一句话记住
**Flash=text+data，RAM=data+bss；优化先审账，nm 按大小排队，map 查户口本。**
:::

**延伸**：size 审计的 .data/.bss 来源在 [B3 链接脚本](03-linker-script.md) 讲透；CCM 腾挪与 DMA 的冲突在 [S8 DMA](../stm32/08-dma.md) 展开；构建系统自动生成 map 的机制见 [B7](07-build-system.md)。

## 实物实验

- 实验三连：① 加一个 4KB 未初始化数组→看 bss 涨、Flash 不涨；② 改成带 `={...}` 初始化→data 涨、Flash/RAM 双涨；③ 加 `const`→data 回落、text 涨。三次 `size` 截图对比，规律亲手验证。

## 常见坑

- **bin 比 text+data 大**：bin 里段间空隙也占字节（按地址铺开）；hex 才是真"按需记录"。
- **Debug 信息背锅**：-g3 让 elf 巨大，但调试信息不进 Flash，烧录大小以 map/size 为准。
- **栈堆不算进 bss**：它们靠 `_Min_*` 预算段占位+运行时生长（B3）；爆 RAM 的另一种死法。
- **优化级别迷信**：-Os 通常赢 -O2（Flash 敏感场景）；但先砍大项再谈级别。

## 短自测

1. 为什么 .data 同时算进 Flash 和 RAM 占用，.bss 只算 RAM？
<details><summary>参考答案</summary>.data 有初值，初值必须存在断电不丢的 Flash（链接脚本 AT> FLASH），运行时启动代码搬到 RAM，所以 Flash 存初值一份、RAM 住运行值一份，两份都吃。.bss 零初始化，启动时清零即可，初值不需要存 Flash，只占 RAM。</details>

2. `nm --size-sort` 倒数五个符号里，最大的一般是哪类？瘦身优先级怎么排？
<details><summary>参考答案</summary>典型大户：vfprintf 一族（printf 带浮点）、大 const 表、大缓冲区、启动代码。瘦身优先级：先砍大项（未用数组、未用库函数靠 gc-sections）→ 再调优化级别（-Os）→ 最后抠 const 归位。一个 4KB 未用数组比 -O2 到 -Os 省的几百字节大一个数量级，方向错了 -O2 救不了。</details>

3. gc-sections 为什么必须配 `-ffunction-sections` 才有效？
<details><summary>参考答案</summary>不加 `-ffunction-sections`，一个 .o 里的所有函数被打包进同一个 .text 段，链接器只能整段进或整段丢：只要有一个函数被引用，整段都保留，没引用的函数也跟着进固件。加了 `-ffunction-sections`，每个函数各占一个 .text.funcname 段，链接器能精确丢弃没被引用的单个函数。gc-sections 的"按段丢弃"粒度依赖 -ffunction-sections 把段切细。</details>

4. CCM RAM 适合放什么、不适合放什么？为什么？
<details><summary>参考答案</summary>适合放 CPU 专用的大缓冲（零等待、不与主 SRAM 抢空间）；不适合放 DMA 缓冲：CCM 直连 CPU 不挂总线矩阵，DMA 访问不到，配错了 DMA 静默失败。判断标准：这块数据 DMA 要不要碰？要碰就留主 SRAM，不碰就腾进 CCM。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| size 三列公式 | 本节第一节；[C1 内存模型](../c/01-memory-model.md) 段归属 |
| map 三板斧 | 00-blink 的 `build/blink.map`（`make` 生成） |
| nm --size-sort 审计 | `arm-none-eabi-nm`；[C6 栈帧](../c/06-abi-stack.md) 也用 nm |
| gc-sections + -ffunction-sections | 00-blink Makefile 默认旗 |
| CCM 链接脚本 | [B3 链接脚本](03-linker-script.md) MEMORY 范式 + 本节第五节 |
| const 经济学验证 | [C1](../c/01-memory-model.md) 第二节 + 本节实验三连 |

## 你做到了

- 固件体积在你眼里是一笔能逐条对账的账；
- 手握 size/nm/map 三把审计刀，优化不再靠猜。

开场那本「固件户口本」你已经会翻了：每个符号多大、住在哪个段、由谁引进，三把刀各查一类。下次体积暴涨，第一反应不再是删代码，而是先审账，找出真正的大户再动手。

<div class="achievement">
✅ 下一站：<a href="06-flash-debug.html">B6 烧录与调试</a>：SWD 两根线，怎么把固件送进 Flash，又凭什么让 CPU 说停就停。
</div>
