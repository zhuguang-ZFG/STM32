---
title: "结构体、ABI 与寄存器映射"
platforms: [f407, f103]
---

# 结构体、ABI 与寄存器映射

> 同一块寄存器有两种写法：`GPIOF->BSRR = 1 << 6;` 和 `*(volatile uint32_t *)(0x40021418) = 1 << 6;`。前者凭什么等价于后者？答案不在语法里，在三条布局规则里。

## 本章罗盘

- **问题**：`GPIOF->BSRR` 展开后为什么正好落在 `0x40021418`？一个只有 `a`、`b`、`c` 三个成员、数据宽度合计 6 字节的结构体，为什么 `sizeof` 是 12？为什么硬件寄存器映射不能用位域，也不能随手加 `#pragma pack(1)`？三个问题分别指向成员顺序、对齐填充与编译器自由裁量的边界。
- **交付**：能拿到一张寄存器地图就写出对应的 `TypeDef`，用 `offsetof`、`sizeof`、`_Static_assert` 三件工具逐成员对账；能手算含填充结构体的每个偏移，并在内存画布上指出洞的位置；能说清结构体映射担保什么、不担保什么，以及为什么位域与 pack 不属于寄存器。
- **边界**：本章逐成员核对的是 F407 的 `stm32f407xx.h`；F103 的寄存器组不是同一张地图，来源 C4 没有给出它的成员表与偏移，本章不补，寄存器级差异指向卷 4 的[第 28 章][ch28]与[第 29 章][ch29]。结构体按值传参、返回时的寄存器与栈约定属于调用约定，留给[第 4 章][ch04]。来源记录里板上 GDB 对照仍标为待回填，本章不把它写成已完成。位域布局的可移植性只有编译器文档与来源结论，没有跨工具链对照实验。
- **依据锚点**：C4《结构体与 ABI：一个结构体罩住整组寄存器》（`mcu/docs/c/04-struct-abi.md`）及其取证工程 `mcu/code/c/04-struct-abi/probe.c`、`broken.c`；`stm32f407xx.h` 第 526–537 行的 `GPIO_TypeDef` 定义、RM0090 §8.4 的寄存器地图与 ARM AAPCS 的布局规则均转引自 C4；变量段归属与指针宽度在[第 1 章](./01-c-memory-model.md)，volatile 的访存合同在[第 2 章](./02-c-volatile-ub.md)。

## 先做出来

这一节不需要开发板，只需要一个宿主 `gcc`。目标只有一个：先押两个数字，再让编译器当场对账。

```bash
cd mcu/code/c/04-struct-abi
sh probe.sh
```

跑之前先回答：`GPIO_TypeDef` 里 `BSRR` 排第 7 个，前面 6 个成员都是 32 位，偏移该是多少？整个结构体有 9 个成员、10 个寄存器，大小又该是多少？把数字写在纸上，再在输出里找这两行：

```text
offsetof(BSRR)    = 0x18  <-- target: 0x18
sizeof(GPIO_TypeDef) = 0x28  <-- target: 0x28
```

对上了，说明你对“声明顺序 + 4 字节宽度”的直觉与编译器一致。再跑反面工程，看四种写错一位的布局：

```bash
sh broken.sh
```

最后一行会故意让编译失败，把 `_Static_assert` 的原话打出来。手上有 ARM 交叉编译器时，换一个 `CC` 再跑：

```bash
CC=arm-none-eabi-gcc sh probe.sh
```

交叉编译器链接不了带 `printf` 的宿主程序，脚本会自动退化为只编译，只验证编译期断言。布局事实在这一步就应该站得住，后面的板子只是复核。

## 机制

### GPIO_TypeDef：寄存器地图的 C 版翻译

CMSIS 头文件把“哪个偏移上住着哪个寄存器”翻译成一个结构体。下面是 `stm32f407xx.h` 第 526–537 行的定义，成员顺序与官方头文件一致：

```c
typedef struct
{
  __IO uint32_t MODER;    /*!< GPIO port mode register,               Address offset: 0x00 */
  __IO uint32_t OTYPER;   /*!< GPIO port output type register,        Address offset: 0x04 */
  __IO uint32_t OSPEEDR;  /*!< GPIO port output speed register,       Address offset: 0x08 */
  __IO uint32_t PUPDR;    /*!< GPIO port pull-up/pull-down register,  Address offset: 0x0C */
  __IO uint32_t IDR;      /*!< GPIO port input data register,         Address offset: 0x10 */
  __IO uint32_t ODR;      /*!< GPIO port output data register,        Address offset: 0x14 */
  __IO uint32_t BSRR;     /*!< GPIO port bit set/reset register,      Address offset: 0x18 */
  __IO uint32_t LCKR;     /*!< GPIO port configuration lock register, Address offset: 0x1C */
  __IO uint32_t AFR[2];   /*!< GPIO alternate function registers,     Address offset: 0x20-0x24 */
} GPIO_TypeDef;
```

九个成员、十个寄存器：`AFR[2]` 一个成员占两格。每个成员前面的 `__IO` 不是装饰，是 CMSIS 给类型限定符起的名字：

| 宏 | 展开为 | 含义 |
| --- | --- | --- |
| `__IO` | `volatile` | 读和写都可能被硬件改变 |
| `__I` | `volatile const` | 程序只读，硬件随时可能改 |
| `__O` | `volatile` | 只写，语义上强调写 |

`GPIOF` 在头文件另一处定义，基址是 `0x40021400`：

```c
#define GPIOF               ((GPIO_TypeDef *) GPIOF_BASE)   /* GPIOF_BASE = 0x40021400 */
```

于是那一行“好看一百倍”的访问，完整展开是：

```c
GPIOF->BSRR = 1 << 6;
/* ⇔ */ (*(volatile uint32_t *)(0x40021400 + 0x18)) = (1 << 6);
```

偏移 `0x18` 不是从手册抄来的魔法数字，是三个事实共同作用的结果：成员按声明顺序排、`uint32_t` 占 4 字节、地址按对齐规则递增。C4 把这三个事实写成两条编译期断言，顺序错、宽度错都在编译时报警：

```c
_Static_assert(offsetof(GPIO_TypeDef, BSRR) == 0x18,
               "BSRR offset must be 0x18");
_Static_assert(sizeof(GPIO_TypeDef) == 0x28,
               "GPIO_TypeDef size must be 0x28 (10 x uint32)");
```

![结构体对齐与填充动画：偏移沿 GPIO_TypeDef 条带逐格数出，Padded_t 重排为 Packed_t 后填充缩短](/anim/struct-alignment.svg)

### 对齐三规则：成员、结构体、数组

ARM AAPCS（ARM 架构过程调用标准）把结构体布局固定成三条规则，编译器没有重排成员的自由：

| 规则 | 内容 | 结果 |
| --- | --- | --- |
| 成员对齐 | 每个成员的起始偏移必须是其对齐值的倍数 | `uint32_t` 永远落在 4 的倍数上 |
| 结构体对齐 | 结构体总大小必须是其最大成员对齐值的倍数 | 尾部可能补填充 |
| 数组 stride | `sizeof(struct)` 已含尾部填充，数组元素连续 | `arr[i]` 的地址 = base + i × sizeof |

拿两个结构体手算一遍。第一个故意按窄、宽、窄排：

```c
typedef struct { uint8_t a; uint32_t b; uint8_t c; } Padded_t;
/* a@0，b 要求 4 的倍数 → a 后填 3 字节，b@4，c@8；
   总大小要是 4 的倍数 → 尾部再填 3 字节，sizeof=12 */

typedef struct { uint32_t b; uint8_t a; uint8_t c; } Packed_t;
/* b@0，a@4，c@5；尾部填 2 字节，sizeof=8 */
```

第二段里的 `Packed_t` 是来源给“重排后版本”起的名字，它没有使用 `#pragma pack`，省下的 4 字节全部来自成员顺序。宽成员先排、窄成员后排，洞自然变少，这就是“结构体成员从大到小排”省内存的力学原理。

### 填充可视化：洞在哪里

`probe.c` 在宿主上打印的真实布局：

```text
Padded_t: sizeof=12, offsets a=0 b=4 c=8
Packed_t: sizeof=8, offsets a=4 b=0 c=5
```

把 `Padded_t` 按字节摊开，`x` 是编译器插入的填充：

```text
偏移:  0    1 2 3    4 5 6 7    8    9 10 11
      [a] [x x x]  [b b b b]   [c]  [x x x]
```

洞有两处：`a` 后面的 3 字节是为了让 `b` 落回 4 的倍数；`c` 后面的 3 字节是为了让整个结构体的大小成为最大成员对齐值 4 的倍数。前者叫成员间填充，后者叫尾部填充。

![结构体对齐：char a、int b、char c 之间插入 3 字节与 3 字节填充，sizeof 从 6 变 12](/figures/c-04-struct-abi.svg)

尾部填充买的不是浪费，是数组 stride。`broken.c` 里把 `Padded_t arr[2]` 摆开实测：

```text
Padded_t: sizeof = 12  a=0 b=4 c=8
arr[1] - arr[0] = 12 字节
arr[0].b 距基址 4 字节，arr[1].b 距基址 16 字节
```

如果 `sizeof` 只算到 `c` 结束的 9，`arr[1].b` 会落在偏移 13，不再是 4 的倍数。下一次数组访问就变成非对齐访问，Cortex-M4 上可能触发 `UsageFault`。

### 位域：布局是实现定义的

位域看起来像为寄存器量身定做的：

```c
typedef struct {
    uint32_t a : 1;
    uint32_t b : 2;
    uint32_t c : 5;
    uint32_t d : 24;
} Bitfield_1_t;
```

C 标准把位域的分配方向（从高位到低位还是反过来）、是否跨存储单元、填充单元怎么处理，全部留给编译器实现定义。`probe.c` 里两种相反的声明顺序在同一个编译器上 `sizeof` 都是 4：

```text
bitfield_1 sizeof=4, bitfield_2 sizeof=4
bitfield layout is implementation-defined; use mask macros for hardware registers
```

大小相同不代表位序相同。同一份代码换到 GCC、Clang、IAR，位序可能完全相反；硬件寄存器要求跨工具链稳定，所以映射寄存器用掩码宏加移位，不用位域：

```c
#define REG_FIELD_A_MASK  (1UL << 0)
#define REG_FIELD_B_MASK  (3UL << 1)
#define REG_FIELD_C_MASK  (31UL << 3)
#define REG_FIELD_D_MASK  (0xFFFFFFUL << 8)

/* 读：(reg & REG_FIELD_B_MASK) >> 1 */
/* 写：reg = (reg & ~REG_FIELD_B_MASK) | ((val << 1) & REG_FIELD_B_MASK) */
```

掩码的移位计数怎么证明小于 32 位、`1UL` 与 `1` 差在哪，[第 2 章](./02-c-volatile-ub.md)已经逐条对过账；这里只记住结论：位域管软件内部打包，掩码管硬件寄存器。

### 端序与打包：小端确认与 pack 的用途

`probe.c` 的端序实验：

```text
endian: 0x12345678 stored as 78 56 34 12 -> little-endian
```

最低有效字节 `0x78` 住在最低地址，这是小端。来源记录写明 ARM Cortex-M4 默认小端；本章只在宿主上实测了这一读数，没有把它扩展成“所有 ARM 芯片都如此”的断言。

`#pragma pack(1)` 或 `__attribute__((packed))` 能把填充压掉，`broken.c` 里同一组成员在 pack(1) 下变成 6 字节：

```text
Packed1_t: sizeof = 6  a=0 b=1 c=5   (b 落在 1 = 非对齐访问)
```

`b` 从偏移 4 挪到偏移 1，结构体里出现了成员自身对齐要求不被满足的访问。Cortex-M4 上这类访问可能触发 `UsageFault`。pack 的正确用途是协议帧、文件头这类“字节位置由协议规定、与 CPU 对齐无关”的数据结构；寄存器结构体的对齐要求来自硬件总线，加 pack 是画蛇添足。

### 结构体映射的边界：能担保什么，不能担保什么

结构体映射不是“把寄存器名写进 struct 就完事”，它只在下面四条同时成立时可靠：

1. 成员顺序与手册寄存器地图逐个一致，包括地图里的空洞。空洞必须用 `RESERVED` 占位成员顶住，否则后面的偏移整体前移。`broken.c` 实测：缺一个保留字时 `DR` 从 `0x08` 前移到 `0x04`，补上占位成员才回到 `0x08`。
2. 成员宽度与寄存器宽度一致。`AFR[2]` 写成 `AFR` 后，`BSRR` 仍停在 `0x18`，但 `sizeof` 从 `0x28` 变成 `0x24`；地图里若还有排在 `AFR` 之后的寄存器，它们的偏移会整体前移。前面的偏移对、后面的错，这种半对半错最难查。
3. 每个寄存器成员都是 volatile（CMSIS 用 `__IO`）。漏掉一个词，优化器就可能缓存、删除或合并访存，[第 2 章](./02-c-volatile-ub.md)的四个现场就是证据。
4. 结构体与芯片头文件版本匹配。用错芯片系列的头文件，或者库版本与芯片型号不匹配，偏移全错，现象是“偶尔配不上、换颗芯片就不好使”。

反过来，结构体映射不担保这些事：

| 想做的事 | 结构体映射能不能担保 | 正确去处 |
| --- | --- | --- |
| 逐寄存器读写，偏移唯一 | 能，前提是上面四条 | `offsetof` + `sizeof` + `_Static_assert` |
| 用位域描述寄存器位 | 不能，布局实现定义 | 掩码宏 + 移位 |
| 同一份 TypeDef 跨芯片复用 | 不能，寄存器地图是芯片专属 | 每颗芯片各自对账 |
| 用 pack 压缩寄存器结构体 | 不能，破坏对齐访问 | pack 只用于协议帧 |
| 结构体按值传参、按值返回 | 不在本章范围 | [第 4 章][ch04]的调用约定 |

最后一行要说清楚：本章只讨论“结构体在内存里怎么排”，不讨论“结构体作为参数怎么进寄存器、怎么走栈、大结构体返回时谁负责拷贝”。那是 AAPCS 的调用约定部分，第 4 章展开。

## 测量与证据

本章所有布局读数来自 C4 的取证工程。来源记录与本次复跑一致，复跑环境：宿主 MinGW-Builds gcc 16.1.0（x86_64-posix-seh），交叉 GNU Arm Embedded Toolchain 10.3.1，编译旗 `-std=c11 -Wall -Wextra -O0`。布局由 ABI 决定，与优化档无关，`-O0` 只是让取证工程保持最直白的形式。

| 取证项 | 命令 | 读数 |
| --- | --- | --- |
| `BSRR` 偏移 | `sh probe.sh` | `0x18` |
| `GPIO_TypeDef` 大小 | `sh probe.sh` | `0x28` |
| 含洞结构体 | `sh probe.sh` | `Padded_t` 12 字节，`a@0 b@4 c@8` |
| 重排结构体 | `sh probe.sh` | `Packed_t` 8 字节，`b@0 a@4 c@5` |
| 端序 | `sh probe.sh` | `78 56 34 12`，小端 |
| 位域大小 | `sh probe.sh` | 两种顺序都是 4 |
| 数组 stride | `sh broken.sh` | `arr[1]-arr[0] = 12` |
| 漏一个保留字 | `sh broken.sh` | `DR` 偏移 `0x04`（应为 `0x08`） |
| 少写一个寄存器 | `sh broken.sh` | `BSRR` 仍 `0x18`，`sizeof = 0x24` |
| pack(1) | `sh broken.sh` | `Packed1_t` 6 字节，`b@1` |
| 交叉编译断言 | `CC=arm-none-eabi-gcc sh probe.sh` | `compile-time _Static_assert PASSED` |

`probe.sh` 的关键输出：

```text
offsetof(MODER)   = 0x00
offsetof(OTYPER)  = 0x04
offsetof(OSPEEDR) = 0x08
offsetof(PUPDR)   = 0x0C
offsetof(IDR)     = 0x10
offsetof(ODR)     = 0x14
offsetof(BSRR)    = 0x18  <-- target: 0x18
offsetof(LCKR)    = 0x1C
offsetof(AFR)     = 0x20
sizeof(GPIO_TypeDef) = 0x28  <-- target: 0x28
```

`broken.sh` 末尾故意制造的编译失败，是 `_Static_assert` 在工程里的日常样子：

```text
assert-fail.c:6:1: error: static assertion failed: "GPIO_TypeDef size must be 0x28 (10 x uint32)"
```

板上那一步要标清楚：来源记录里在 F407 工程用 GDB 执行 `print &((GPIO_TypeDef*)0)->BSRR`、再对照 `0x40021400 + 0x18` 的步骤，只做到编译期核实，读数待回填。本章能用编译期断言证明的内容不依赖这块板子；板上对照是复核，不是前提。

判断“真的会了”：给你一张没见过的寄存器地图，你能在十分钟内写出 `TypeDef`、为每个成员补 `_Static_assert`，并在不运行程序的情况下算出 `sizeof`；再给你一个含填充的结构体，你能在纸上画出每个洞的位置和数组 stride。

## 失败分支

| 现象 | 原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| 换颗芯片就偶尔配不上，同一份代码时好时坏 | 结构体成员顺序或保留字与手册不一致 | `broken.sh`：漏保留字时 `DR` 落在 `0x04` | 按手册逐成员重排，空洞补 `RESERVED` |
| `sizeof` 少了 4，前面的寄存器却都正常 | 漏写一个寄存器（如 `AFR[2]` 写成 `AFR`） | `Short_t`：`BSRR` 仍 `0x18`，`sizeof = 0x24` | 断言 `sizeof` 与每个关键偏移 |
| `sizeof` 对、偏移错 | 同宽度成员互换顺序，总大小不变 | `_Static_assert(sizeof)` 通过，`offsetof` 失败 | 每个寄存器各断言一条偏移，不只断言总大小 |
| 配置序列偶尔少一次写 | 寄存器成员漏了 volatile | 反汇编里多次读-改-写被合并 | 用 CMSIS `__IO`，或给成员补 `volatile` |
| 换编译器后寄存器位读写串位 | 用位域映射硬件寄存器 | 位域布局是实现定义，`sizeof` 相同也可能位序相反 | 改成掩码宏 + 移位 |
| 给寄存器结构体加了 pack(1)，现场可能触发 UsageFault | 成员被压到非对齐偏移 | `Packed1_t`：`b@1`，`sizeof=6` | 去掉 pack；协议帧另立结构体 |
| 结构体里数据都对，函数调用后值变了 | 把布局约定当成调用约定 | 第 4 章的传参/返回规则未核对 | 先读[第 4 章][ch04]，再查汇编 |
| 数组第二个元素字段错位 | 误以为 `sizeof` 不含尾部填充 | `arr[1]-arr[0]=12`，不是 9 | 用 `sizeof` 算 stride，不手算成员宽度 |
| 在宿主上量到小端，就在目标板上照抄字节序假设 | 端序是目标架构与工具链的事 | 来源只实测宿主小端、写明 M4 默认小端 | 在目标板上重测，别跨平台搬运结论 |

## 跨平台边界

本章的布局规则不是 F407 专属。声明顺序、成员对齐、结构体对齐与数组 stride 来自 ARM AAPCS，属于架构级约定；两平台的 C 编译器都受它约束，所以“成员按声明顺序排、地址按对齐递增、成员不许重排”这套算法可以带着走。`offsetof`、`sizeof`、`_Static_assert` 三件工具也是标准 C，不依赖某一颗芯片。

但寄存器块的具体形状是芯片专属。本章逐成员核对的是 F407 的 `stm32f407xx.h`，由此得到的 `BSRR = 0x18`、`sizeof(GPIO_TypeDef) = 0x28`、`GPIOF_BASE = 0x40021400` 都只属于这张地图。来源 C4 没有给出 F103 的 GPIO 成员表、偏移或基址，本章不替它补；把 F407 的寄存器名、偏移、时钟或引脚直接套到 F103 上，是本章明确划出的红线。两平台的寄存器级差异、移植检查表与型号对照，放在卷 4 的[第 28 章][ch28]与[第 29 章][ch29]。

其余几条边界同样按来源收口：

| 事项 | 本章的证据范围 | 跨平台时的处理 |
| --- | --- | --- |
| 布局规则 | AAPCS 三规则，来源 C4 | 规则可复用，具体偏移必须逐芯片对账 |
| GPIO 寄存器地图 | 仅 F407 头文件 | F103 不照搬，指向[第 28 章][ch28]、[第 29 章][ch29] |
| 端序 | 宿主实测小端；来源写明 M4 默认小端 | F103 未测，不在两平台间泛化 |
| pack 的对齐风险 | Cortex-M4 上可能触发 `UsageFault` | 具体异常行为按目标平台手册复核 |
| 结构体传参/返回 | 本章未展开 | 第 4 章的调用约定 |

## 离开检查

1. `GPIOF->BSRR = 1 << 6` 的完整展开是什么？`0x18` 由哪三件事共同决定？
2. `Padded_t { uint8_t a; uint32_t b; uint8_t c; }` 的 `sizeof` 为什么是 12 而不是 6？两个洞各自由哪条规则产生？
3. 尾部填充对数组访问意味着什么？如果 `sizeof` 只算到最后一个成员结束，`arr[1].b` 会落在哪，为什么危险？
4. 为什么位域不能用来映射硬件寄存器？掩码写法怎么读写同一个字段？
5. `#pragma pack(1)` 用在哪类结构体上是对的？为什么给寄存器结构体加 pack 会出问题？
6. 只断言 `sizeof`、不断言 `offsetof`，会漏掉哪类错误？各举一个能过、一个不能过的例子。

<details>
<summary>对照答案</summary>

1. `(*(volatile uint32_t *)(0x40021400 + 0x18)) = (1 << 6)`。`0x18` 由成员声明顺序、`uint32_t` 的 4 字节宽度与对齐规则共同决定；`__IO` 让每次访问都真访存。
2. `b` 要求起始偏移是 4 的倍数，`a` 后填 3 字节；`c` 之后总大小要是最大成员对齐值 4 的倍数，尾部再填 3 字节。`1 + 3 + 4 + 1 + 3 = 12`。
3. 尾部填充保证 `sizeof` 是 4 的倍数，数组元素按 stride 连续排。若只算到 9，`arr[1].b` 落在 13，偏离 4 的倍数，成为非对齐访问。
4. 位域的分配方向、跨单元策略与填充单元都是实现定义的，换编译器可能位序相反。掩码写法：读 `(reg & MASK) >> SHIFT`，写 `reg = (reg & ~MASK) | ((val << SHIFT) & MASK)`。
5. 协议帧、文件头这类字节位置由协议规定的数据。寄存器结构体的对齐要求来自硬件总线，pack 会把成员压到非对齐偏移，Cortex-M4 上可能触发 `UsageFault`。
6. 会漏掉“总大小不变但成员顺序错”的情况：两个同宽度成员互换，`sizeof` 仍是 `0x28`，`offsetof(BSRR)` 却会变；`AFR[2]` 写成 `AFR` 则相反，`BSRR` 偏移不变、`sizeof` 变成 `0x24`。所以每个关键成员都要断言偏移。

</details>

动作验收：找一张你手上芯片的 GPIO 寄存器地图，写出 `TypeDef`，为地图上的第一个、最后一个与任意一个中间寄存器各写一条偏移断言，再写一条总大小断言；编译通过后，故意把两个同宽成员对调，确认断言能抓住你。

[ch04]: ./04-function-pointer-state-machine.md
[ch28]: ../v4-platforms/28-chip-migration-differences.md
[ch29]: ../v4-platforms/29-gd32-arm-riscv.md
