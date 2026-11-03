---
title: R6 Env 与 menuconfig：RT-Thread 的点单系统
status: done
difficulty: 1
minutes: 25
---

# R6 Env、scons 与 menuconfig：配置即代码

> 🎯 RT-Thread 生态的恐怖之处：menuconfig 里勾一个"MQTT 客户端"，`pkgs --update` 一敲，源码自动下载、自动进构建——像点外卖。这背后是 Env（工具环境）+ scons（构建）+ Kconfig（配置）的三人转。

![R6 menuconfig 点单流水线：Kconfig → .config → rtconfig.h → 构建](/anim/menuconfig-flow.svg)

## 本章精髓

1. Kconfig 管"编什么"：每个组件/软件包自带 Kconfig 描述依赖与选项，`menuconfig` 生成 `.config`→`rtconfig.h`：**菜单项=宏**，代码里 `#ifdef` 应声而开（与 ESP-IDF 同源，对照 [P3](../../esp32/03-idf-anatomy.md)）。
2. scons 管"怎么编"：SConstruct/SConscript（Python）描述源码清单与依赖，`scons -j8` 出固件；`scons --target=mdk5/iar` 还能一键导出 IDE 工程：源码是单一事实源。
3. Env 是"开箱即用"的 Windows 环境：内置 Python/scons/gcc/menuconfig，装一个 Env，全站工具零配置（与 P0 的 IDF 安装器同思路）。

- **能理解**：为什么 `rtconfig.h` 是生成物不该手改；为什么 SConscript 用 Python 比纯 DSL 灵活；为什么"在 applications 里改驱动"换 BSP 会全丢。
- **能用**：menuconfig 勾选组件 → `pkgs --update` 拉源码 → `scons -j8` 出固件完整跑一遍；为一个自写组件加一条 Kconfig 选项并在菜单里出现。

## 先修

- [B7 构建系统](../../build/07-build-system.md)（CMake/scons/Kconfig 对照锚点）。

## 先跑起来（10 分钟 quick win）

```bash
cd bsp/stm32f407-zeo   # 进 BSP 目录
menuconfig             # 方向键翻菜单，空格勾选（如 cJSON），保存退出
pkgs --update          # 拉取选中软件包源码到 packages/
scons -j8              # 并行编译，出固件
```

四条命令走完：menuconfig 勾一个软件包（cJSON/MQTT/lwIP 任选），pkgs 把源码拉到 `packages/`，scons 编进固件，新组件已进镜像。配置驱动开发，第一次体感：**菜单项即宏，勾选即编译**。改了菜单一定 `scons` 重编，否则宏变了固件没变（这是后面常见坑第一条）。

打开菜单之前先押个落点：勾选那一下，最终变成哪个文件里的哪一行？编译时读的又是哪份？押完走完四条命令，打开 rtconfig.h 对答案。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| Env 安装与命令 | env 控制台；menuconfig/pkgs/scons 三板斧 | 配置 |
| Kconfig 机制 | config 项→.config→rtconfig.h 的宏链路 | 库解析 |
| scons 构建 | SConscript 逐行：源文件分组与依赖 | 库解析 |
| 软件包生态 | 在线包索引/版本选择/离线包处理 | 配置 |
| BSP 解剖 | board/libraries/applications 三区职责 | 库解析 |
| 对比 IDF | Kconfig 同源、构建异构（CMake vs scons）的取舍 | 库解析 |

## 一、Env 安装与命令：三板斧

Env 是 RT-Thread 官方提供的 Windows 开箱即用环境，内置 Python/scons/gcc/menuconfig，装一个 Env，全站工具零配置（与 ESP-IDF 的 IDF 安装器同思路，回 [B7](../../build/07-build-system.md)）。打开 env 控制台（双击 `env.exe` 或运行 `env.bat`），进 BSP 目录，三板斧：

```bash
menuconfig          # 打开菜单，勾选组件/软件包
pkgs --update       # 拉取/更新选中的软件包源码
scons -j8           # 并行编译，出固件 .bin/.elf
```

三板斧的分工：menuconfig 管"编什么"（写 `.config`），pkgs 管"取什么"（下载软件包源码），scons 管"怎么编"（执行构建）。还有一个常用招，一键导出 IDE 工程：

```bash
scons --target=mdk5   # 导出 Keil MDK5 工程
scons --target=iar    # 导出 IAR 工程
```

源码与 SConscript 是单一事实源，IDE 工程是衍生品：改了 SConscript 重新导出，不用在 IDE 里手动维护文件清单。这也是为什么团队协作时该提交 SConscript 而不是 IDE 工程文件（`.uvprojx`/`.eww`）：前者是源头，后者是人手一份的衍生品。

## 二、Kconfig 机制：菜单项 = 宏

每个组件/软件包自带一份 Kconfig 文件，描述它的依赖与选项。`menuconfig` 命令收集所有 Kconfig 拼成菜单树。链路：

```text
Kconfig（菜单定义）─menuconfig─> .config（选择结果）─scons 生成─> rtconfig.h（宏）
                                                                        ↓
                                                             C 代码 #include，#ifdef 走分支
```

一个 Kconfig 选项长这样：

```kconfig
config RT_USING_I2C
    bool "Enable I2C bus driver"
    select RT_USING_DEVICE
    default n
    help
      勾选后生成 #define RT_USING_I2C
```

- `bool` = 开关项（y/n）；`select` = 选中它时自动勾选依赖项（`RT_USING_DEVICE` 自动开）。
- 存盘后 `.config` 里多一行 `CONFIG_RT_USING_I2C=y`，scons 再生成 `rtconfig.h` 多一行 `#define RT_USING_I2C 1`。
- 代码里 `#ifdef RT_USING_I2C` 应声而开：**菜单项即宏，配置即代码**。

`select` 是"依赖自动满足"：勾 I2C 自动勾 DEVICE，省得忘开依赖；`depends on` 反过来，父依赖没开时子选项灰着选不上（按 `?` 看依赖表达式）。骨架坑列表第三条"Kconfig 依赖断链"就是这么来的：选项灰着选不上=父依赖没开。

与 ESP-IDF 的 sdkconfig 同源（回 [B7 第五节](../../build/07-build-system.md)）：同一套 Kconfig 语法，只是产物文件名不同，IDF 叫 `sdkconfig.h`，RT-Thread 叫 `rtconfig.h`。**rtconfig.h 是生成物，不该手改**，手改的下次 menuconfig 会被覆盖。要改默认值，去改 Kconfig 里的 `default`，或直接编辑 `.config`。

## 三、scons 构建：SConscript 逐行

scons 用 Python 写构建脚本：SConstruct 是顶层入口，SConscript 散落在各子目录描述"我这目录编什么"。一个典型 BSP 的 SConscript：

```python
# bsp/stm32f407/SConscript（节选）
import rtconfig
from building import *

cwd = GetCurrentDir()
src = Glob('*.c')                    # 收集本目录所有 .c
path = [cwd]                         # 头文件搜索路径
group = DefineGroup('Drivers', src, depend=['RT_USING_DEVICE'], CPPPATH=path)
```

逐行读：
- `Glob('*.c')`：把本目录所有 `.c` 收进源文件清单。
- `depend=['RT_USING_DEVICE']`：只有 rtconfig.h 里 `RT_USING_DEVICE` 开了，这组才进构建，**Kconfig 与 scons 的接合点就在 depend**。
- `DefineGroup`：把"组名+源文件+依赖+头文件路径"注册给构建系统，scons 收齐所有 group 后编。

SConstruct 顶层做三件事：设工具链、读 rtconfig.h、递归遍历所有 SConscript 收 group、链接出 `.elf`、objcopy 出 `.bin/.hex`。关键一句：

```python
# SConstruct（节选）
env = Environment(tools=['gccarm'], ARM_GCC_PATH=rtconfig.EXEC_PATH)
```

scons 与 CMake 的差别（回 [B7 第六节](../../build/07-build-system.md)）：CMake 是"生成器"（生成 Makefile/Ninja 再构建），scons 是"直接构建器"（Python 脚本直接驱动 gcc），少一层"生成"步骤，但依赖 Python 运行时。**SConscript 用 Python 比纯 DSL 灵活**：循环、条件、字符串拼接都是原生 Python，不用学专用语法。代价是构建速度依赖 scons 实现（`-j8` 并行比 Ninja 慢一档），但中小工程无感。

## 四、软件包生态：在线点单

`pkgs --update` 是 RT-Thread 生态的"外卖骑手"：menuconfig 里勾的软件包（cJSON/MQTT/AT/...）存在线包索引里，`pkgs --update` 按选择拉源码到 `packages/` 目录，下次 scons 就编进去。

```bash
pkgs --update          # 按 .config 拉选中包
pkgs --list            # 看本地已装包
pkgs --upgrade         # 升级有新版的包
```

版本选择在 menuconfig 里：每个包可选 latest/特定 tag/特定版本，生产固件建议钉版本（防上游更新引入不兼容）。离线场景：提前 `pkgs --update` 拉全，把 `packages/` 目录一起带，离线构建不依赖网络。

软件包生态是 RT-Thread 区别于 FreeRTOS 的最大护城河（回 [R0](00-arch.md)）：FreeRTOS 只给内核，外设驱动/网络栈/文件系统全靠自己拼；RT-Thread 一个 menuconfig 就能拉 MQTT 客户端、cJSON、lwIP，"点外卖式做固件"由此得名。R7 移植完标准版，回来勾一个软件包跑通，就能体感这条护城河。

## 五、BSP 解剖：三区职责

一个标准版 BSP 目录长这样：

```text
bsp/stm32f407-zeo/
├── board/            # 板级：时钟/堆/外设初始化、链接脚本
│   ├── board.c       # rt_hw_board_init 实现
│   ├── linker.ld     # FLASH/RAM 布局
│   └── CubeMX_Config/# 引脚配置（HAL 生成）
├── libraries/        # HAL 驱动层：STM32 HAL + rt-thread 设备驱动
│   ├── HAL_Drivers/  # rt_device 包装（uart/spi/i2c）
│   └── STM32F4xx_HAL/# ST 官方 HAL 库
├── applications/     # 应用：main.c、业务代码
├── Kconfig           # 本 BSP 的菜单项（板级选项）
├── SConscript        # 构建脚本
└── rtconfig.h        # 裁剪配置（生成物）
```

三区职责分明：
- **board/**：板级知识（时钟树、堆边界、引脚、链接脚本），换板改这里。
- **libraries/**：HAL 驱动，把 STM32 HAL 包装成 `rt_device`（回 [R4](04-device.md)）。
- **applications/**：业务代码，与板级解耦，换板不丢。

骨架坑列表第四条"在 applications 里改驱动"的根因：板级驱动该去 board/ 与 libraries/，applications 只放应用，否则换 BSP 全丢。这是 RT-Thread 工程化的核心纪律：**板级与应用解耦**，靠设备框架（R4）做接合层。R7 标准版移植的"改板三步"全在 board/ 里改，applications/ 一行不动，这就是解耦的红利。

## 六、对比 IDF：Kconfig 同源、构建异构

把 RT-Thread 与 ESP-IDF 的配置/构建体系摆一起（回 [B7 第六节](../../build/07-build-system.md)）：

| 维度 | ESP-IDF | RT-Thread |
|---|---|---|
| 配置系统 | Kconfig → sdkconfig → sdkconfig.h | Kconfig → .config → rtconfig.h（同源） |
| 构建系统 | CMake（生成 Ninja） | scons（Python 直接构建） |
| 组件声明 | idf_component_register（CMake DSL） | SConscript（Python 函数） |
| 包管理 | idf.py add-dependency | pkgs --update（在线包索引） |
| 调度入口 | idf.py build/flash | scons / scons --target=mdk5 |
| 工具环境 | IDF 安装器（自带 Python/cmake/ninja） | Env（自带 Python/scons/gcc/menuconfig） |

两者都把"组件化+配置化"叠在 B1 那四步之上。差别在构建脚本语言：CMake 是专用 DSL（跨平台好、但语法另学），scons 是 Python（灵活、但要装 Python）。**Kconfig 是共用层**——同一套语法，菜单项=宏的链路两边都成立。会一种就能读另一种，会两种就能看穿"配置与构建是正交两维"（B7 的结论）。

## 记忆锚点

::: tip 一句话记住
**menuconfig 点单，pkgs 取货，scons 下厨；Kconfig 管编什么，scons 管怎么编：点外卖式做固件。**
:::

**延伸**：menuconfig 点单流水线动画见 [R6 动画](/anim/menuconfig-flow.svg)；ESP-IDF Kconfig 对照见 [P3](../../esp32/03-idf-anatomy.md)；构建系统在 [B7](../../build/07-build-system.md) 详解。

## 实物实验

- 勾一个软件包（如 cJSON）→ 应用里 `#include "cJSON.h"` 解析一段 JSON 串口打印：从零到用上社区库，十分钟。

## 常见坑

- **menuconfig 保存后忘 scons 重编**：宏已变固件未新，"勾了没用"的第一原因。
- **pkgs --update 网络失败**：代理/镜像问题，pkgs 支持镜像源配置，公司网先配好。
- **Kconfig 依赖断链**：选项灰着选不上=父依赖没开，按 ? 看依赖表达式。
- **在 applications 里改驱动**：改板级驱动请去 board/ 与 libraries/，applications 只放应用，否则换 BSP 全丢。
- **rtconfig.h 手改后被覆盖**：rtconfig.h 是 menuconfig 生成物，手改的下次 menuconfig 全冲掉。要改默认值改 Kconfig 的 `default` 或直接编辑 `.config`，别直接改 rtconfig.h。

## 短自测

**1. menuconfig/pkgs/scons 三板斧各管什么？为什么说"配置与构建是正交两维"？**

<details><summary>看答案</summary>

menuconfig 管"编什么"（写 .config，决定哪些组件进、哪些宏开），pkgs 管"取什么"（按选择下载软件包源码），scons 管"怎么编"（按 SConscript 描述的依赖图驱动 gcc 出固件）。说它们正交是因为：同一份 Kconfig 配置可以喂给 scons 也可以喂给 CMake；同一套 scons 可以编不同 Kconfig 配置，两维各自独立演化，不互相绑死（这是 B7 的结论）。

</details>

**2. Kconfig 的 `select` 与 `depends on` 各是什么？灰着选不上的选项什么原因？**

<details><summary>看答案</summary>

`select` 是"选中我时自动勾选依赖项"，勾 I2C 自动开 DEVICE，省得忘开依赖。`depends on` 是"父依赖开了我才能选"，父依赖没开时子选项灰着选不上。灰选项的根因就是 `depends on` 表达式里的父依赖没满足，按问号键看依赖表达式，先开父依赖即可。

</details>

**3. rtconfig.h 为什么不该手改？要改默认值怎么办？**

<details><summary>看答案</summary>

rtconfig.h 是 menuconfig 按 .config 生成的产物，手改的下次 menuconfig 会按 .config 重新生成，全冲掉。要改默认值改 Kconfig 里的 `default`，或直接编辑 .config（下次 menuconfig 会读它）。rtconfig.h 该被 gitignore，该提交的是 Kconfig 与 .config（或 .config.defaults 种子文件）。

</details>

**4. SConscript 里 `DefineGroup` 的 `depend` 参数起什么作用？**

<details><summary>看答案</summary>

`depend` 指定这组源码进构建的前提：只有 rtconfig.h 里对应的宏开了，这组才编。比如 `depend=['RT_USING_DEVICE']` 表示设备框架开了才编这组驱动。这是 Kconfig 与 scons 的接合点：Kconfig 决定宏开不开，SConscript 的 depend 决定宏开了才进构建，两维在这里汇合。

</details>

**5. BSP 三区（board/libraries/applications）各放什么？为什么改驱动不能去 applications？**

<details><summary>看答案</summary>

board 放板级知识（时钟、堆、引脚、链接脚本），libraries 放 HAL 驱动（把 STM32 HAL 包装成 rt_device），applications 放业务代码。改驱动去 applications 会把板级耦合进应用，换 BSP 时 applications 全丢。正确做法是板级驱动放 board/libraries，靠设备框架（R4）做接合层，applications 只调 rt_device 接口，换板不动应用。

</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| Env 三板斧（menuconfig/pkgs/scons） | env 控制台；本章第一节 |
| Kconfig → .config → rtconfig.h 链路 | BSP 目录的 Kconfig + rtconfig.h |
| SConscript 的 DefineGroup/depend | bsp/*/SConscript |
| 软件包在线点单 | pkgs --update；packages/ 目录 |
| BSP 三区（board/libraries/applications） | bsp/stm32f407-*/ 目录结构 |
| scons --target=mdk5/iar 一键导出 | 本章第一节命令 |
| Kconfig 与 ESP-IDF 同源 | [B7 第五节](../../build/07-build-system.md)；[P3](../../esp32/03-idf-anatomy.md) |

## 你做到了

- RT-Thread 生态的"点单-取货-下厨"全流程跑通；
- 配置体系与构建体系的分工彻底清晰：B7 的理论在此落地。

落点在 rtconfig.h：菜单那一下勾选，最终变成这个生成文件里的一行宏，代码编译时读的也是它。手改它就像改收据，下次 menuconfig 一开，墨迹全无。

<div class="achievement">
✅ 下一站：<a href="07-port-f407.html">R7 移植到霸天虎</a>：Nano 手动移植到标准版，两步走全记录。
</div>
