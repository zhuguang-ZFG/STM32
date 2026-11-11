# 01-memory-model：不需要开发板的内存取证工程

C1 章的配套工程。别人讲"段"给你背名词，这里给你**地址**：同一份源码里的 11 个对象，
谁住 Flash、谁住 RAM、谁压根没有符号，全部由 `size` / `nm` / `readelf` / `objdump` 从 ELF 里读出来。

| 文件 | 角色 | 详解章节 |
|---|---|---|
| `mem_probe.c` | 11 个对象的段归属现场（含三个反直觉答案） | [C1 内存模型](../../../docs/c/01-memory-model.md) |
| `lut_probe.c` | 256 字节的表，加不加 `const` 的对照实验 | 同上第三节 |
| `probe.sh` | 一条命令跑完全部取证（`sh probe.sh`） | [B1 四步构建](../../../docs/build/01-four-steps.md) |

链接复用 [`code/stm32/00-blink`](../../stm32/00-blink/) 的 `startup_stm32f407xx.s` 与 `stm32f407xx.ld`，
所以本工程的地址布局与点灯工程完全同构——搬 .data 的那个循环，就是你在 [B4](../../../docs/build/04-startup.md) 逐行读过的那段。

## 构建与取证

```bash
sh probe.sh          # 全部：段归属 + const 对照 + 启动代码 + 字母骗局
sh probe.sh mem      # size -A / nm -n / readelf -S / readelf -l / "查无此人"
sh probe.sh lut      # uint8_t lut[256] vs const uint8_t lut[256]
sh probe.sh boot     # Reset_Handler 反汇编 + 链接脚本关键行 + .data 镜像字节
sh probe.sh rodata   # 把 .rodata 单列重链：同一地址，字母 T → R
sh probe.sh clean
```

没装 make 也能跑（本目录刻意用 shell 脚本）。工具链不在 PATH 时先设：

```bash
export PATH="/d/zhugu-home/tools/armgcc/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:$PATH"
# 或者：export ARM_PREFIX=/path/to/arm-none-eabi-   （脚本按前缀拼 gcc/nm/size/…）
```

产物一律落在 `build/`（已在 `.gitignore` 里）。

## 本机实测记录

环境：**xPack GNU Arm Embedded GCC 15.2.1 20251203**（`arm-none-eabi-gcc`，含同版本 binutils）。
编译参数：`-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard -O0 -g3 -Wall -Wextra -ffunction-sections -fdata-sections`，
链接：`-T stm32f407xx.ld -Wl,--gc-sections -nostartfiles -Wl,-Map=...`。Windows 10.0.26200，2026-10-06。

::: warning 取证边界
上面全部是**编译期/链接期事实**（ELF 里读出来的，随时可复现）。
"改 `g_flag=2` 后复位又变回 1"这类**板上肉眼现象本轮未跑**——写这一版时手边没接 F407 与 ST-Link。
:::

### 1. 段归属（`sh probe.sh mem`）

```console
$ arm-none-eabi-size -A build/mem_probe.elf
section              size        addr
.isr_vector           392   134217728      # 0x08000000  向量表，Flash
.text                 280   134218120      # 0x08000188  代码 + .rodata（合并进同一输出段）
.data                  12   536870912      # 0x20000000  有初值全局，RAM
.bss                   32   536870924      # 0x2000000c  零初始化全局，RAM
._user_heap_stack    1540   536870956      # 0x2000002c  链接脚本预留的堆+栈
Total               26775                  # 其余为 .debug_*，不进固件
```

```console
$ arm-none-eabi-nm -n --print-size build/mem_probe.elf
08000188 00000012 t sink          # static 函数：小写 t
0800019c 00000084 T probe
08000220 0000000c T main
0800022c 00000042 W Reset_Handler # .weak：大写 W
0800028c 00000002 t Default_Handler   # （此处省略 91 行同名 IRQ 别名——它们全指向 0800028c）
08000298 00000004 T g_ro          # const → 地址在 Flash，nm 字母却是 T
0800029c 00000004 T k_tab
080002a0 A _sidata                 # .data 初值在 Flash 的仓库地址（同址还有 _etext、__exidx_*）
20000000 00000004 D g_init          # 有初值 → .data
20000004 00000004 D g_flag          # volatile 不改段归属
20000008 00000003 D g_msg           # "hi"+NUL，3 字节
2000000c D _edata                  # ┐ .data 的尽头
2000000c B _sbss                   # ┘ 正好是 .bss 的起点
2000000c 00000004 B g_zero          # ★ 显式写 0，却在 .bss
20000010 00000004 B g_uninit
20000014 00000010 b s_buf           # 小写 b = 局部符号（static）
20000024 00000008 b s_local.0       # 函数里的 static；.0 是多次实例化的后缀
2000002c B _ebss
20020000 R _estack                 # 栈顶 = RAM 末尾
```

`auto_var` 在符号表里**查无此人**（脚本会明确打印这一条）——它是栈上的自动对象，链接期不存在。

```console
$ arm-none-eabi-readelf -W -l build/mem_probe.elf
  Type   Offset   VirtAddr   PhysAddr   FileSiz MemSiz  Flg Align
  LOAD   0x001000 0x08000000 0x08000000 0x002a0 0x002a0 R E 0x1000   # Flash 里的一切
  LOAD   0x002000 0x20000000 0x080002a0 0x0000c 0x0002c RW           # ★ VMA≠LMA：人在 RAM，行李在 Flash
  LOAD   0x00002c 0x2000002c 0x080002ac 0x00000 0x00604 RW           # FileSiz=0：.bss + 堆栈预留
```

```console
$ arm-none-eabi-objdump -s -j .data build/mem_probe.elf
Contents of section .data:
 20000000 05000000 01000000 68690000       ........hi..
   #        g_init=5   g_flag=1   "hi\0"+对齐
```

### 2. const 经济学（`sh probe.sh lut`）

| 源码 | `.text` | `.data` | `nm` 里的 `lut` | 第二个 LOAD 行 |
|---|---|---|---|---|
| `uint8_t lut[256] = {1,2,3};` | 148 | **256** | `20000000 00000100 D lut` | `VirtAddr 0x20000000 PhysAddr 0x0800021c FileSiz 0x100 MemSiz 0x700` |
| `const uint8_t lut[256] = {1,2,3};` | **404** | **0** | `0800021c 00000100 T lut` | `FileSiz 0x00000`（RAM 里不再有这样一段东西） |

一个 `const` 换来 256 字节 RAM；`.text` 从 148 涨到 404 正是那 256 字节换了住址（404 − 148 = 256）。

### 3. 搬运工（`sh probe.sh boot`）

`Reset_Handler` 反汇编里的字面量池（函数尾部那几个 `.word`）就是链接脚本发出的地址条，
逐个对上 `nm` 的符号：

```asm
 8000270:  20020000   @ _estack      → ldr sp, [pc, #64]
 8000274:  e000ed88   @ SCB->CPACR   → 使能 FPU（orr #0xf00000 = 0xF<<20）
 8000278:  20000000   @ _sdata       → 拷贝目标起点
 800027c:  2000000c   @ _edata       → 拷贝目标终点
 8000280:  080002a0   @ _sidata      → 拷贝源起点（Flash！）
 8000284:  2000000c   @ _sbss        → 清零起点
 8000288:  2000002c   @ _ebss        → 清零终点
```

拷贝循环 `ldr r4,[r2,r3] / str r4,[r0,r3] / adds r3,#4` 跑 `(0x2000000c-0x20000000)/4 = 3` 圈，
清零循环 `str.w r3,[r2],#4` 跑 `(0x2000002c-0x2000000c)/4 = 8` 圈——与上面 `.data 12 / .bss 32` 严丝合缝。
源码逐行走读见 [B4 启动过程](../../../docs/build/04-startup.md) 第三节。

## 三个反直觉答案（本工程存在的全部理由）

1. `int g_zero = 0;` —— 写了初值，却住在 `.bss`：初值是 0 就不必占 Flash 仓库，编译器替你做了这个决定。
2. `int auto_var = 3;` —— 源码里有，符号表里没有：自动存储期的东西归栈管，链接器不认识它。
3. `const int g_ro = 7;` —— 地址在 Flash（`0x08000298`），`nm` 字母却是 `T`（"在代码段"）：
   本工程的链接脚本把 `*(.rodata)` 并进了 `.text` 输出段（`stm32f407xx.ld:48-49`），
   所以 T 不代表它是函数。**看字母不如看地址。**

### 附：字母骗局的两条实测（`sh probe.sh rodata`）

变体脚本由 awk 从 `00-blink/stm32f407xx.ld` **现场生成**（只把 `*(.rodata)`、`*(.rodata*)` 从 `.text` 里摘走、在 `.text` 之后单开一个 `.rodata` 输出段），原件不动，产物在 `build/`：

```console
原脚本（并进 .text）：  08000298 T g_ro     0800029c T k_tab
变体脚本（单列 .rodata）：08000298 R g_ro   0800029c R k_tab
                         [ 2] .text   PROGBITS 08000188 001188 000108 00  AX
                         [ 3] .rodata PROGBITS 08000290 001290 000010 00   A
```

地址一格没动，字母变了。反向验证可见性也一样：把 `mem_probe.c` 的 `int g_init = 5;` 改成 `static int g_init = 5;` 重新链接，同一地址 `0x20000000`，字母从 `D` 变 `d`。

**结论：`T`/`R`/`D`/`d` 记的是"哪个输出段 + 全局还是局部"，与"Flash 还是 RAM"无关。介质只看地址前缀。**

### 4. 字母骗局的两条实测（`sh probe.sh rodata`）

脚本从 `00-blink` 的链接脚本**现场生成**一份变体（只删 `*(.rodata)`/`*(.rodata*)` 两行、在 `.text` 之后单开一个 `.rodata` 输出段），原件不动，产物在 `build/`：

```console
原脚本（并进 .text）：  08000298 T g_ro     0800029c T k_tab
变体脚本（单列）：      08000298 R g_ro     0800029c R k_tab
                        [ 2] .text    PROGBITS 08000188 001188 000108 00 AX
                        [ 3] .rodata  PROGBITS 08000290 001290 000010 00  A
```

地址一格没动，字母变了 —— `T`/`R` 说的是"哪个输出段 + 什么属性"，不是"函数还是数据"。

可见性同理（把 `mem_probe.c` 的 `int g_init = 5;` 改成 `static int g_init = 5;` 重新链接）：

```console
20000000 00000004 D g_init      →      20000000 00000004 d g_init
```
