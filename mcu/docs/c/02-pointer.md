---
title: C2 指针：点灯公式的全部秘密
status: done
difficulty: 3
minutes: 40
---

# C2 指针：点灯公式的全部秘密

> 🎯 先破一桩点灯怪案：地址没写错，数值也没写错，只把指针类型换窄，灯就可能“亮得下不来”。编译器没有报错，芯片也没有闹脾气，真正变掉的是哪一条机器指令？沿着 `*(volatile uint32_t *)0x40021418 = 1UL << 22;` 往下查，你会发现指针从来不是玄学，它只管三件事：**地址 + 宽度 + 纪律**。

## 本章精髓

1. 指针的值是地址，指针的类型决定**每次读写的字节宽度**（uint8/16/32 对应 LDRB/LDRH/LDR）：寄存器必须 32 位访问，类型错了硬件不理你。
2. 指针运算的步长由类型定：`p+1` 对 uint32_t* 是 +4 字节，这正是"寄存器数组"能用结构体/数组索引访问的原因（C4 展开）。
3. 数组名与指针的"纠缠"在嵌入式里有一个实用出口：`((uint32_t*)0x40021400)[6]` 就是 BSRR。
4. `const` 在 `*` 左边锁目标、右边锁指针，全部在**编译期**拦截，不要一分钱运行时开销，驱动里满街都是 `volatile uint32_t * const`。

<details>
<summary>🌐 English Abstract</summary>

**Pointer = address + width + discipline**. The pointer value is the address; the pointer type determines **bytes per access** (uint8/16/32 → LDRB/LDRH/LDR). Hardware registers require 32-bit access—wrong type, hardware ignores you. **Pointer arithmetic**: `p+1` steps by the pointed-to type's size (uint32_t* → +4 bytes). **Array-pointer equivalence**: `((uint32_t*)0x40021400)[6]` is BSRR. **const placement**: left of `*` locks the target, right locks the pointer—all compile-time checks, zero runtime cost.

</details>

- **能记住**：地址定位置、类型定宽度、volatile 定纪律（三板斧）

## 先修

- [C1 内存模型](01-memory-model.md)。

## 先跑起来（10 分钟 quick win）

本章全部事实由一个取证工程跑出（宿主 gcc 16.1.0 + xPack arm-none-eabi-gcc 15.2.1，均本机实测）：

先别执行。拿张纸押三个答案：三种读取会不会生成同一条指令？三种指针的 `p+1` 会不会都只加一个字节？索引写法和偏移写法会不会编成不同机器码？押完再开庭，避免看过答案后误以为自己早就知道。

```bash
cd code/c/02-pointer
sh probe.sh        # 交叉汇编 + 宿主真跑 + const 反例，一次跑完
```

你将看到：`ldrb/ldrh/ldr` 三条指令并排、`p+1` 的 +1/+2/+4 字节增量、`[6]` 与 `+0x18` 编出**逐字节相同**的机器码、三条 const 越界"如期报错"。`probe.sh` 不在 PATH 的 xPack 会自动垫上，ARM 工具链位置不同就用 `ARM_PREFIX=... sh probe.sh`。

现在给刚才的下注判分：读取指令不同，步长不同，最后两种写法的机器码反而相同。三个结果看似互相打架，其实都由同一条规则解释：类型决定一次访问多宽，也决定一次“前进一步”跨多远；只要最终地址与访问宽度相同，写法的外形就不重要。

有板子的再加一道：对 `code/stm32/00-blink` 构建产物跑 `arm-none-eabi-objdump -d`，找到 main 里写 BSRR 的那条 `str`，对照 `code/stm32/00-blink/main.c:60`，亲眼看 C 咒语变成机器指令。

## 动画：指针三件事

取地址是抄门牌、指针是存门牌的格子、解引用是顺箭头登门。`p+1` 为什么跳 4 格、野指针登门为什么有三种下场，动画逐阶段演一遍。

![指针三件事：取地址 · 存门牌 · 解引用登门](/anim/pointer-arrows.svg)

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、咒语逐词翻译 | 地址字面量→指针类型→解引用；LDR/STR 宽度对照 | 代码分析 |
| 二、步长的真相 | `p+1` 的字节数实验；寄存器块的"索引访问"写法 | 代码分析 |
| 三、野指针三宗罪 | HardFault 定位（联动 [S16](../stm32/16-debug-hardfault.md)）；静默改写案例 | 代码分析 |
| 四、const 与指针三组合 | `const int*`/`int* const`/`const int* const` 在驱动里的真实用途 | 配置 |

## 一、咒语逐词翻译

把 `*(volatile uint32_t *)0x40021418 = 1UL << 22;` 从右往左拆：

| token | 人话 |
|---|---|
| `0x40021418` | 门牌号：GPIOF 基址 `0x40021400` + BSRR 偏移 `0x18`（出处 `code/stm32/00-blink/main.c:29,34`，STM32F407） |
| `(volatile uint32_t *)` | 给裸地址装上类型：**32 位宽**的钥匙 + volatile 的叮嘱（[C3](03-volatile.md) 展开） |
| `*` | 解引用：这一次真的要登门访存 |
| `= 1UL << 22` | 一次 32 位写：BSRR 高 16 位的 BR6，PF6 拉低，红灯亮（共阳，见 00-blink 头注释） |

"类型定宽度"不是修辞，是指令层面的分叉。取证（`probe.c` 的 read/write 六函数，`arm-none-eabi-gcc -std=c11 -Wall -Wextra -O2 -mcpu=cortex-m4 -mthumb -S`，版本 15.2.1）：

```asm
read8:                          read16:                         read32:
        ldrb    r0, [r0]                ldrh    r0, [r0]                ldr     r0, [r0]
        bx      lr                      bx      lr                      bx      lr
write8:                         write16:                        write32:
        strb    r1, [r0]                strh    r1, [r0]                str     r1, [r0]
        bx      lr                      bx      lr                      bx      lr
```

后缀即宽度：`B`=8 位字节、`H`=16 位半字、无后缀=32 位字。**同一个 `*p`，类型换了，生成的指令就换。** F407 的 GPIO 寄存器全是 32 位，所以 00-blink 的宏一律 `uint32_t`；你若用 `uint16_t*` 去写 BSRR，编出来是 `strh`：只写低 16 位，高 16 位（复位区）根本够不着（指令宽度编译期已核实，板上现象待回填，见实物实验）。

![指针步长：int *p 加一前进 4 字节，char *q 加一前进 1 字节](/figures/c-02-pointer.svg)

## 二、步长的真相

C 标准把 `p+1` 定义为"前进一个**指向对象**"，不是前进一个字节。编译器干脆把步长折进寻址偏移，一条指令都不多花（同一取证汇编）：

```asm
next8:                          next16:                         next32:
        ldrb    r0, [r0, #1]            ldrh    r0, [r0, #2]            ldr     r0, [r0, #4]
        bx      lr                      bx      lr                      bx      lr
```

`p[1]` 的地址增量是 `#1/#2/#4`，就是 `sizeof` 三兄弟。宿主侧真跑（`gcc -std=c11 -Wall -Wextra -O2`，MinGW gcc 16.1.0，断言全过）：

```text
sizeof: uint8_t=1 uint16_t=2 uint32_t=4  指针自身=8 字节
p+1 字节增量: uint8_t* +1  uint16_t* +2  uint32_t* +4
```

（指针自身 8 字节是 x86-64 宿主的口径，与"指向宽度"无关，别把这两件事搅在一起。）

**这一步直接通往寄存器块的索引写法。** 既然 `p[i]` 恒等于 `*(p+i)`，而 `i` 的单位是类型宽度，那么：

```c
((volatile uint32_t *)0x40021400)[6]   /* 地址 = 0x40021400 + 6×4 = 0x40021418 = BSRR */
```

`6 × sizeof(uint32_t) == 0x18` 这条等式用 `_Static_assert` 锁死在 `probe.c` 里（随每次编译校验，编过即证）。宿主真跑同样确认（只取地址、不解引用）：

```text
寄存器索引: &((uint32_t*)0x40021400)[6] = 0x40021418 (= 基址 + 6*4 = +0x18)
```

更狠的证据在汇编：索引写法 `led_on_indexed` 与 00-blink 宏写法 `led_on_macro` 编出**逐字节相同**的机器码：

```asm
led_on_indexed:                 @ led_on_macro 与此完全相同
        ldr     r3, .L12
        mov     r2, #4194304            @ 1<<22 = BR6
        str     r2, [r3, #1048]
        bx      lr
.L12:
        .word   1073876992              @ 0x40021000；+1048(0x418) = 0x40021418
```

编译器把最终地址 `0x40021418` 拆成"字面值 `0x40021000` + 12 位偏移 `1048`"，殊途同归。**两种 C 写法，零差别**：选哪个是风格问题，不是正确性问题。这也是 C4 用结构体罩住整组寄存器的地基：结构体字段偏移与数组下标，走的是同一套"下标 × 宽度"算术。

## 三、野指针三宗罪

裸机没有 MMU 页保护，指错了没人立刻拦你。宿主上野指针通常吃到 segfault，那是操作系统的馈赠；板子上只有三种下场：

1. **HardFault**：访问了不存在的地址（未使能时钟的外设区、保留区、越出存储映射），总线错误升级成 HardFault。这是最好的一种：当场死给你看，定位方法见 [S16](../stm32/16-debug-hardfault.md)。
2. **静默改写**：地址合法但指错了对象，写穿到隔壁变量、别的外设寄存器。没有任何异常，系统在几天后、另一个看似无关的功能里爆雷。排查成本以天计。
3. **碰巧能用**：最可怕的一种。野到的内存当前恰好无害，功能"正常"，换优化档、换芯片、加一行代码才复发，与 [C3](03-volatile.md) 里"`-O0` 一切正常"同源：**运气不是设计**。

注意 `probe.c` 的一个细节：宿主运行只敢对 `0x40021400` **取地址**做算术，从不敢解引用：在 Windows 宿主上那个地址摸不得。这本身就是活教材："合法的 C 指针值"与"可访问的地址"是两回事，指针合法性的最终裁判是**存储映射**，不是编译器。

防御纪律就三条：指针必先初始化再使用；地址常量集中在一处定义（像 00-blink 那样 `GPIOF_BASE + 偏移`，别满篇魔法数）；需要按地址打印/存储时用 `uintptr_t`，需要表偏移差用 `size_t`/`ptrdiff_t`。

## 四、const 与指针三组合

`const` 的位置决定锁谁，口诀"从右往左念，const 锁左边最近的那个"：

| 写法 | 锁住的 | 放行的 |
|---|---|---|
| `const int *p`（同 `int const *p`） | `*p = x` 透过指针改目标 | `p = &b` 换指向 |
| `int * const p` | `p = &b` 换指向 | `*p = x` 改目标 |
| `const int * const p` | 全锁 | 只能读 |

三条越界全部**编译期**拦截（`probe.sh const` 段，宿主 gcc 16.1.0 实测，如期报错）：

```text
probe.c:50:52: error: assignment of read-only location '*p'        @ const int *p：*p = 1
probe.c:52:58: error: assignment of read-only variable 'p'         @ int * const p：p = &b
probe.c:54:59: error: assignment of read-only location '*(const int *)p'  @ 全锁
```

合法半边真跑通过：`*pc=2 *cp=42 *cpc=2`，断言全过。const 不要钱——跑都不用跑，错在编译期就死了。

**为什么驱动里满街是 `volatile uint32_t * const`**：指针本身锁死（这个句柄永远指向 GPIOF，不许被改去指别人），目标保持 volatile（硬件会绕过 CPU 改它，[C3](03-volatile.md) 的合同照旧）。两个限定词各管一件事，叠在一起恰好是"寄存器句柄"的完整语义。CMSIS 的 `GPIO_TypeDef` 结构体指针用法（C4 展开）就是这一组合的批量化。

## 附录：工程完整源码

取证工程（宿主 gcc 与 Cortex-M4 交叉各一套，一分钟可复现）：

<<< ../../code/c/02-pointer/probe.c

构建与取证命令（`sh probe.sh` 从工程目录直接跑）：

<<< ../../code/c/02-pointer/probe.sh

板级对照工程（点灯咒语的出处）：

<<< ../../code/stm32/00-blink/main.c

## 记忆锚点

::: tip 一句话记住
**地址定位置，类型定宽度，volatile 定纪律**（width/where/don't-optimize）。指针三板斧，念念有回响。
:::

**延伸**：指针与内存布局的关系在 [C1](01-memory-model.md) 铺垫；volatile 防止编译器优化指针读取在 [C3](03-volatile.md) 展开；指针访问外设寄存器是 [S3 GPIO](../stm32/03-gpio.md) 的核心操作。

## 实物实验

- **无板上（本机已全部实测通过）**：`cd code/c/02-pointer && sh probe.sh`，把 `read8/16/32` 三条指令、`p+1` 的 +1/+2/+4 输出、两条 `led_on_*` 的相同汇编抄进实测记录，注明工具链版本与完整命令行（本机：arm-none-eabi-gcc 15.2.1 `-mcpu=cortex-m4 -mthumb -O2 -S`；宿主 gcc 16.1.0 `-O2`）。
- **板上（编译期结论已核实，肉眼现象待回填）**：在 `code/stm32/00-blink/main.c:34` 把 `GPIOF_BSRR` 的类型从 `uint32_t*` 改成 `uint16_t*`，构建烧录：`str` 变 `strh`，只写低 16 位：置位（BSx 低 16 位）仍有效，复位（BRx 高 16 位）够不着，灯将"亮得下不来"（预期现象，待回填）。亲手证明"类型=访存宽度"。

::: warning 本轮取证状态
本章汇编与宿主运行输出均为本机实测（版本与命令行如上）；**板上肉眼现象本轮未跑**。谁先烧录验证，欢迎把现象回填到这一节。
:::

## 常见坑

- **用 int* 访问寄存器**：多数平台 int=32 位碰巧对，但风格即隐患；寄存器访问一律定宽类型 `uint32_t`。
- **忘记括号**：`*GPIOF_BSRR = x` 与宏定义展开优先级。所以我们的宏写成 `(*(volatile uint32_t *)(...))`，括号一个不能少。
- **把指针当整数打印**：嵌入式 printf 打印指针用 `%p` 且强转 `(void*)`，否则行为未定义。
- **以为 `const` 有运行时开销**：三组合全部编译期拦截，生成的机器码与不加 const 逐字节相同——不加白不加。
- **`p+1` 当字节加**：`uint32_t *p = (uint32_t *)0x40021400; p + 6` 是 `0x40021418`，`(char *)p + 6` 才是 `0x40021406`，单位是指向对象，不是字节（第二节汇编里 `#1/#2/#4` 的铁证）。

## 短自测

**1. 把 00-blink 的 BSRR 宏改成 `*(volatile uint16_t *)0x40021418 = 1U << 22;`，会发生什么？为什么？**

<details><summary>答案</summary>

编译产出 `strh`（16 位写），且 `1U << 22` 截成 16 位后是 0，这行实际往 BSRR 低 16 位写 0，"写 0 无影响"，什么都不发生。就算改成 `uint16_t*` 写 `1U << 6`，也只能碰置位区，复位区（高 16 位）永远够不着：灯"亮得下不来"。指令宽度由指针类型决定（第一节 `strb/strh/str` 对照），寄存器必须按手册宽度 32 位访问。（指令侧已核实，板上现象待回填。）

</details>

**2. `uint32_t *p = (uint32_t *)0x40021400;` 时，`p + 6` 与 `(char *)p + 6` 各等于多少？**

<details><summary>答案</summary>

`p + 6` = `0x40021400 + 6×4` = `0x40021418`（正是 BSRR）；`(char *)p + 6` = `0x40021406`。指针加减的单位是**指向对象的大小**，不是字节，`probe.sh run` 的实测输出 +1/+2/+4 即证据。

</details>

**3. `const int *p` 与 `int * const p` 各拦什么？驱动句柄为什么常写成 `volatile uint32_t * const`？**

<details><summary>答案</summary>

`const int *p` 拦"透过 p 改目标"（`error: assignment of read-only location`），放行换指向；`int * const p` 拦"换指向"（`error: assignment of read-only variable`），放行改目标。`volatile uint32_t * const` 是两者合体的驱动语义：指针锁死在这个外设地址上不许改指（const 在 `*` 右），目标可被硬件异步修改、每次访问都必须真访存（volatile 管目标）。全在编译期生效，零运行时开销。

</details>

**4. 凭什么说 `((uint32_t *)0x40021400)[6]` 与 `*(uint32_t *)(0x40021400 + 0x18)` 等价？证据链有几环？**

<details><summary>答案</summary>

三环，全部可复现：① 语义环：`p[i]` 恒等于 `*(p+i)`，`i` 以 `sizeof(*p)` 为单位，`6×4=24=0x18`；② 编译期环：`_Static_assert(6U*sizeof(uint32_t)==0x18)` 随每次编译校验；③ 指令环：`-O2` 下 `led_on_indexed` 与 `led_on_macro` 编出逐字节相同的汇编（`str r2, [r3, #1048]`，字面池 `0x40021000`，落点 `0x40021418`）。

</details>

## 对照表：本章概念 → 仓库落点

| 概念 | 仓库落点 |
|---|---|
| 类型定访存宽度（ldrb/ldrh/ldr、strb/strh/str） | `code/c/02-pointer/probe.c` read/write 六函数，正文第一节汇编引证 |
| `p+1` 步长 = 类型宽度 | 同上 next8/16/32 汇编（`#1/#2/#4`）+ `sh probe.sh run` 输出 |
| BSRR = 基址 `[6]`（索引=偏移） | 同上 `_Static_assert` + `led_on_indexed`/`led_on_macro` 同码对照 |
| 点灯咒语 `0x40021418`/`0x40021400`/`0x18` | `code/stm32/00-blink/main.c:29,34,60,62`（全部地址的唯一出处） |
| const 三组合编译期拦截 | `sh probe.sh const` 三条如期报错 |
| `volatile uint32_t * const` 驱动惯用法 | `probe.c` main() 运行输出；volatile 合同见 [C3](03-volatile.md) |
| 野指针 HardFault 定位 | [S16](../stm32/16-debug-hardfault.md) |
| 取证脚本入口（host-probe） | `code/c/02-pointer/probe.sh` |

## 你做到了

- 点灯咒语再无秘密，还能随手写出同类；
- 会按"地址+宽度+纪律"三问审查任何寄存器访问代码；
- 会用 `_Static_assert` + 同码对照证明"两种写法等价"，而不是靠嘴。

回到开场那盏“亮得下不来”的灯：地址与数值都可以正确，类型仍能让访问宽度悄悄换掉。以后再遇到寄存器写入怪案，先查生成的是哪种 load/store，再查门牌号。

<div class="achievement">
✅ 下一站：<a href="03-volatile.html">C3 volatile</a>：编译器会把你的寄存器读写"优化"成什么样，volatile 又能管到哪一截。
</div>
