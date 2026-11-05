---
title: B7 构建系统：从手写 Makefile 到 CMake 与 scons
status: done
difficulty: 2
minutes: 30
---

# B7 构建系统：Makefile→CMake/Ninja→IDF/scons

> 🎯 一张最气人的构建工单：你明明改了头文件，编译器却说没有东西需要重建；固件顺利烧进去，行为还是旧的。谁在撒谎？编译器没撒谎，Make 也没撒谎，是依赖图根本不知道那次修改。沿着这张工单追下去，Makefile、CMake、IDF 与 scons 都会显出同一副骨架：**依赖图 + 配置层**。

## 本章精髓

1. Make 的本质是一张依赖图：目标←依赖←规则，mtime 比新旧决定要不要重来；`make -n` 干跑一遍，图就摆在眼前。
2. CMake 不构建，它**生成**构建文件（Ninja/Makefile）：多一层抽象换来跨平台+组件化；ESP-IDF 的 `idf_component_register` 就是在这层抽象上圈地。
3. 配置是独立一维：Kconfig 把"编不编这个组件/开不开这个功能"变成菜单（IDF 的 sdkconfig、RT-Thread 的 menuconfig 同源）：**构建系统管怎么编，Kconfig 管编什么**。

- **能理解**：为什么头文件改了 Makefile 不重建是"没写依赖"；为什么 CMake 工具链文件必须在 `project()` 之前设。
- **能用**：`make -n` 干跑看依赖图；读懂 00-blink Makefile 的每一行在画什么图。

## 先修

- [B1 四步构建](01-four-steps.md)；用过 [P0](../esp32/00-env.md) 的 idf.py 更佳。

## 先跑起来（10 分钟 quick win）

先预测再执行：第一次干跑会列出哪些命令？只碰一下源文件后，是全部重建，还是只有一条路径变脏？如果你的预测是“构建系统会自己理解文件内容”，这十分钟会把这个直觉推翻。

```bash
make clean && make -n        # 干跑：把将执行的命令全列出，不真做
touch main.c && make -n      # 只动了 main.c，看依赖图如何"局部重建"
```

`make -n` 是构建系统的"X 光"：它把将执行的命令全列出来但不真做，依赖图的形状一目了然。`touch` 改一个文件的 mtime，再 `make -n` 看只有哪些目标会被重建，这就是依赖图"局部重建"的实证。

立即核对：Make 没读懂你的源代码，它只比较图上的节点和时间。图上没有的关系，在它眼里就不存在。开场工单里“头文件改了，目标没动”的怪现象，到这里已经抓到第一名嫌疑人：缺失的依赖边。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| Make 依赖图 | 目标/依赖/规则三要素；模式规则 %.o:%.c；自动变量 $@$< | 库解析 |
| Makefile 解剖 | 00-blink 的 Makefile 逐行回看：我们其实写了张什么图 | 代码分析 |
| CMake 一层抽象 | add_executable/target_compile_options；工具链文件 toolchain.cmake | 库解析 |
| IDF 组件机制 | idf_component_register 做了什么；REQUIRES/PRIV_REQUIRES 依赖声明 | 库解析 |
| Kconfig 一维 | menuconfig→sdkconfig→宏：配置如何流进代码（联动 [P3](../esp32/03-idf-anatomy.md)） | 配置 |
| scons 对照 | RT-Thread 的 SConscript 思路（联动 [R6](../rtos/rtthread/06-env-menuconfig.md)） | 库解析 |

## 动画：依赖图与局部重建

依赖图画出"谁影响谁"，mtime 比对决定"要不要重建"，touch 改一个文件看只有哪些路径被重建。盯住"局部重建"三个字，这是构建系统的核心价值。

![构建系统依赖图与局部重建](/anim/build-dep-graph.svg)

## 一、Make 依赖图：目标/依赖/规则三要素

Make 的世界只有三样东西：**目标**（要产出的文件，如 `blink.elf`）、**依赖**（产出它需要的文件，如 `main.o startup.o`）、**规则**（怎么从依赖造目标，如 `$(CC) ... -o $@ $^`）。三者用 `:` 连起来就是一条 Make 规则：

```makefile
blink.elf: main.o startup.o           # 目标: 依赖
	$(CC) $(LDFLAGS) -o $@ $^          # 规则（Tab 缩进！）
```

Make 的核心算法只有一条：**比 mtime**。目标的 mtime 比所有依赖都新 → 不重建；有依赖比目标新 → 重建。`make -n` 干跑就是把这套比对跑一遍，列出将执行的命令但不真做，依赖图的"形状"（谁依赖谁、谁该先建）一览无余。

两个自动变量背下来：`$@`=目标名、`$<`=第一个依赖、`$^`=所有依赖。模式规则 `%.o: %.c` 让 Make 自动把每个 `.c` 编成 `.o`，不用为每个文件写一条规则，00-blink 的 Makefile 就靠这条管所有源文件。

## 二、Makefile 解剖：00-blink 写了张什么图

回看 00-blink 的 Makefile（`code/stm32/00-blink/Makefile`），它画的依赖图：

```text
blink.elf ──┬── main.o ──── main.c + stm32f407.h
            ├── startup_stm32f407xx.o ──── startup_stm32f407xx.s
            └── linker.ld（链接脚本，不编译，直接喂 ld）
blink.bin ──── blink.elf（objcopy 转格式）
flash ──── blink.bin（调 OpenOCD 烧录，伪目标）
debug ──── 无依赖（常驻 OpenOCD，伪目标）
gdb ──── 无依赖（连 OpenOCD，伪目标）
```

每个 Makefile target 对应图上一个节点。**伪目标**（`.PHONY` 声明的，如 `flash`/`debug`/`gdb`）不产出文件，只是"命令别名"：`make flash` 就是跑那行 OpenOCD 烧录命令，不比对 mtime。

骨架页坑列表第一名的"头文件改了不重建"：图里 `main.o` 的依赖只写了 `main.c`，没写 `stm32f407.h`。改了头文件，main.o 的 mtime 仍比 main.c 新（main.c 没动），Make 不重建 main.o，固件用的是旧编译的 main.o。解法：`-MMD -MP` 让 gcc 编译时自动生成 `.d` 依赖文件（把头文件依赖也写进去），Makefile `include` 这些 `.d`，头文件依赖自动维护，是进阶 Makefile 的标配。

工单到这里可以结案：不是“Make 偶尔抽风”，而是图画漏了一条边。这个结论比背一条修复命令更重要，因为以后遇到链接顺序、组件循环依赖或配置没生效，你都可以问同一句：真实关系有没有进入构建系统看得见的图？

## 三、CMake 一层抽象：生成构建文件

CMake 不直接构建，它**生成** Makefile 或 Ninja 构建文件，多一层抽象，换来跨平台+组件化。最小裸机工程骨架：

```cmake
# 顶层 CMakeLists.txt
cmake_minimum_required(VERSION 3.13)
set(CMAKE_TOOLCHAIN_FILE arm-none-eabi.cmake)   # 工具链文件，必须在 project() 之前
project(blink C)
add_executable(blink main.c startup.s)
target_compile_options(blink PRIVATE -mcpu=cortex-m4 -mthumb -Os)
target_link_options(blink PRIVATE -Tlinker.ld)
add_custom_command(TARGET blink POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE:blink> blink.bin)
```

```cmake
# arm-none-eabi.cmake（工具链文件）
set(CMAKE_SYSTEM_NAME Generic)
set(CMAKE_SYSTEM_PROCESSOR cortex-m4)
set(CMAKE_C_COMPILER arm-none-eabi-gcc)
set(CMAKE_ASM_COMPILER arm-none-eabi-gcc)
set(CMAKE_OBJCOPY arm-none-eabi-objcopy)
set(CMAKE_TRY_COMPILE_TARGET_TYPE STATIC_LIBRARY)   # 不试链接（交叉链没有运行环境）
```

两条铁律（骨架坑列表）：① 工具链文件必须在 `project()` 之前 `set(CMAKE_TOOLCHAIN_FILE ...)`，否则 CMake 用主机 gcc 探测环境、编出 x86 的东西；② `CMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY` 让 CMake 不试运行编译产物（交叉编译的产物在 PC 上跑不了）。

CMake 的价值在"规模"：两百个文件分二十个目录，`add_subdirectory` 递归管理，每个目录一个 `CMakeLists.txt`，比手写一个大 Makefile 好维护。代价是多一层"生成"步骤（`cmake -B build` 生成，`make -C build` 构建）。

## 四、IDF 组件机制：idf_component_register 圈地

ESP-IDF 在 CMake 之上加了"组件"抽象（[P3 IDF 工程解剖](../esp32/03-idf-anatomy.md) 全章展开）。每个组件（component）是一个目录，含 `CMakeLists.txt` + 源码 + `Kconfig`，顶层 `idf_component_register` 声明组件名、源文件、依赖：

```cmake
# 组件的 CMakeLists.txt
idf_component_register(
    SRCS "my_driver.c"
    INCLUDE_DIRS "include"
    REQUIRES driver          # 依赖其他组件
    PRIV_REQUIRES freertos   # 仅实现层依赖，不暴露给依赖我的组件
)
```

`REQUIRES` vs `PRIV_REQUIRES`：前者把依赖组件的头文件也暴露给"依赖我的组件"（传递），后者只给本组件实现用（不传递），这是 C/C++ 接口与实现分离在构建层的体现。骨架坑列表的"循环依赖"（A REQUIRES B、B REQUIRES A）解法：抽出公共部分进 C，A/B 都 REQUIRES C，不再互引。

IDF 用 CMake 圈组件、Kconfig 管配置、idf.py 调度，三层叠在一起，底层还是 B1 那四步（预处理→编译→汇编→链接）。

## 五、Kconfig 一维：配置如何流进代码

Kconfig 把"编不编这个组件/开不开这个功能"变成菜单（`menuconfig` 命令打开），选择结果存进 `sdkconfig`（键值对），构建时生成 `sdkconfig.h`（宏定义）供 C 代码 `#include`：

```text
Kconfig（菜单定义）─menuconfig─> sdkconfig（选择结果）─生成─> sdkconfig.h（宏）
                                                                     ↓
                                                          C 代码 #include，#ifdef 走分支
```

同一个机制，IDF 叫 sdkconfig、RT-Thread 叫 .config（[R6 Env 与 menuconfig](../rtos/rtthread/06-env-menuconfig.md) 全章展开）。**Kconfig 是独立一维**，与构建系统（CMake/scons）正交。构建系统管"怎么编"（依赖图+命令），Kconfig 管"编什么"（哪些组件进、哪些宏开）。两维独立配置，不互相绑死。

骨架坑列表的"把 sdkconfig 提交进仓库"：sdkconfig 是构建产物（每个人配不同），该提交的是 `sdkconfig.defaults`（默认值的种子），新人 `idf.py build` 时由 defaults 重新生成本地 sdkconfig。

## 六、scons 对照：RT-Thread 的另一套衣服

RT-Thread 用 scons（Python 写的构建系统）+ Kconfig，与 IDF 的 CMake+Kconfig 对照：

| 维度 | ESP-IDF | RT-Thread |
|---|---|---|
| 构建系统 | CMake（生成 Ninja/Makefile） | scons（Python 脚本） |
| 配置系统 | Kconfig → sdkconfig | Kconfig → .config（同源） |
| 组件声明 | `idf_component_register` | `SConscript`（Python 函数） |
| 调度入口 | `idf.py build/flash` | `scons` / `scons -j4` |

两者都把 B1 的四步包成"组件化+配置化"，差别只在构建脚本语言（CMake 的 DSL vs Python）。**底层都是依赖图+配置层两件事**，会一种就能读另一种；[R6](../rtos/rtthread/06-env-menuconfig.md) 会展开 RT-Thread 的 env/menuconfig 全流程。

## 记忆锚点

::: tip 一句话记住
**Make 画图（依赖），CMake 生图（跨平台），Kconfig 管编什么，构建系统管怎么编**——IDF 用 CMake 圈组件，RTT 用 scons 走江湖，底层还是 B1 那四步。
:::

**延伸**：IDF 的 CMake 组件化在 [P3 IDF 解剖](../esp32/03-idf-anatomy.md) 展开；RT-Thread 的 scons+menuconfig 在 [R6](../rtos/rtthread/06-env-menuconfig.md) 完整走一遍；依赖图与局部重建的动画见 [B1 四步构建](01-four-steps.md)。

## 实物实验

- 在 00-blink 的 Makefile 里故意删掉 `startup_stm32f407xx.o` 的依赖，touch 启动文件后 make，观察到"没重建"，亲手证明依赖图的价值，然后改回来。

## 常见坑

- **头文件改了不重建**：Makefile 没写头文件依赖。用 `-MMD -MP` 让 gcc 自动生成 .d 依赖文件（进阶 Makefile 标配）。
- **CMake 工具链文件顺序错**：必须在 `project()` 之前 `set(CMAKE_TOOLCHAIN_FILE ...)`，否则用的是主机 gcc。
- **IDF 组件循环依赖**：A REQUIRES B、B REQUIRES A，抽出公共组件 C 是标准解法。
- **把 sdkconfig 提交进仓库**：它是构建产物；该提交的是 `sdkconfig.defaults`。

## 短自测

1. Make 怎么决定一个目标要不要重建？`make -n` 干跑看的是什么？
<details><summary>参考答案</summary>比 mtime：目标比所有依赖都新就不重建，有依赖比目标新就重建。`make -n` 干跑把这套比对跑一遍，列出将执行的命令但不真做，依赖图的形状（谁依赖谁、谁该先建、谁会被重建）一目了然，是构建系统的"X 光"。</details>

2. 改了头文件 Makefile 不重建，根因和解法各是什么？
<details><summary>参考答案</summary>根因：Makefile 里 main.o 的依赖只写了 main.c，没写 stm32f407.h。改了头文件，main.o 的 mtime 还比 main.c 新（main.c 没动），Make 不重建 main.o。解法：加 `-MMD -MP` 编译旗，gcc 编译时自动生成 .d 依赖文件（把头文件依赖也写进去），Makefile `include` 这些 .d，头文件依赖自动维护，不用手写。</details>

3. CMake 工具链文件为什么必须在 `project()` 之前设？设晚了会怎样？
<details><summary>参考答案</summary>CMake 在 `project()` 时探测编译器、试编译、设置系统名。如果工具链文件在 project() 之后才设，CMake 已用主机 gcc 探测完环境、编出 x86 的东西，交叉工具链设了也来不及。必须在 project() 之前 set(CMAKE_TOOLCHAIN_FILE)，让 CMake 一开始就用交叉 gcc 探测。</details>

4. Kconfig 与构建系统（CMake/scons）是什么关系？为什么说 Kconfig 是"独立一维"？
<details><summary>参考答案</summary>Kconfig 管编什么（哪些组件进、哪些宏开），构建系统管怎么编（依赖图+命令）。两者正交：同一份 Kconfig 配置可以喂给 CMake 也可以喂给 scons；同一套构建系统可以编不同 Kconfig 配置。Kconfig 的输出（sdkconfig/.config → 宏头）是构建系统的一个输入，但两者各自独立演化，不互相绑死。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| 00-blink Makefile 依赖图 | `code/stm32/00-blink/Makefile` |
| 模式规则 %.o:%.c + 自动变量 | 同上 Makefile |
| CMake 裸机骨架 | 本节第三节；对比 [P3](../esp32/03-idf-anatomy.md) IDF 组件 |
| idf_component_register | [P3 IDF 工程解剖](../esp32/03-idf-anatomy.md) 全章 |
| Kconfig → sdkconfig | [P3](../esp32/03-idf-anatomy.md)；[R6](../rtos/rtthread/06-env-menuconfig.md) RT-Thread 同源 |
| scons + SConscript | [R6](../rtos/rtthread/06-env-menuconfig.md) 全章 |

## 你做到了

- 构建系统从"玄学配置"还原成"依赖图 + 配置层"两件事；
- Makefile/CMake/IDF/scons 四种形态在你眼里是同一件衣服的四个剪裁。

回看开场那张工单：命令成功不等于产物包含了你的修改。只要依赖图漏边，构建系统就会非常诚实地生成一个过期固件。你现在不仅知道怎么补边，也知道下一次该从哪里开始审讯。

<div class="achievement">
✅ B 篇收官。下一站：<a href="../stm32/index.html">S 篇 STM32 裸机</a>：地基已经打完，去寄存器的世界里大干一场。
</div>
