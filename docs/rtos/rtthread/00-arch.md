---
title: R0 RT-Thread 架构：万物皆对象
status: done
difficulty: 2
minutes: 30
---

# R0 RT-Thread 架构：分层与对象模型

> 🎯 如果说 FreeRTOS 是"瑞士军刀"（内核极致精简），RT-Thread 就是"工具箱"：内核之外自带设备框架、控制台、软件包生态。而理解这一切的钥匙只有一把——**万物皆对象**。

## 本章精髓

1. 三层架构：**内核层**（调度/IPC/内存，libcpu+BSP 之下）、**组件层**（finsh/设备框架/文件系统/网络）、**软件包**（社区三方，menuconfig 即点即用），生态是它的护城河。
2. 对象模型是统一世界观：线程/信号量/互斥量/定时器/设备全部继承自 `rt_object`（名字+类型+标志），`rt_object` 就是"基类"，容器（object container）统一管理，所以 finsh 能 `list_thread`/`list_sem` 一把梭。
3. 自动初始化有"段位"：`rt_components_board_init` → `rt_components_init` → 应用。INIT_BOARD_EXPORT/INIT_COMPONENT_EXPORT 等宏把各层初始化函数按段排好，启动时依次执行（链接脚本段机制的教科书级应用，回 [B3](../../build/03-linker-script.md)）。

- **能理解**：为什么 finsh 能 `list_thread`/`list_sem`/`list_device` 一把梭；为什么 `INIT_*_EXPORT` 不用调用链就能按顺序跑；Nano 和标准版到底差在哪。
- **能用**：对照源码指认 `rt_object`→`rt_thread` 的继承（第一个成员就是对象头）；按移植目标选 Nano 还是标准版；看懂对象容器与 INIT 段位的配合。

## 先修

- [F1~F3](../freertos/01-task-tcb.md)（内核概念对照锚点）；[C4](../../c/04-struct-abi.md)、[B3](../../build/03-linker-script.md)。

## 先跑起来（10 分钟 quick win）

打开 RT-Thread 源码 `include/rtdef.h` 找到 `struct rt_object` 与 `struct rt_thread`，亲眼看到"线程结构的第一个成员就是对象"，继承一目了然。

翻 rtdef.h 之前先押个辈分：rt_thread 的第一个成员是谁，凭什么排在栈顶指针前面？押完往下翻两屏就见分晓。

## 动画：对象模型与容器

rt_object 基类、rt_thread 的首成员继承、对象容器按类型分链，橙色遍历珠沿 thread 链移动，list_thread 的"一把梭"就是它在逐节点走。

![R0 对象模型：万物继承 rt_object](/anim/rtt-object-model.svg)

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 三层架构 | 内核/组件/软件包目录巡礼（src/components/packages） | 库解析 |
| 对象模型 | rt_object 基类与容器；list API 为什么万能 | 库解析 |
| 自动初始化 | INIT_*_EXPORT 段位表；与链接脚本的配合 | 库解析 |
| Nano vs 标准版 | 裁剪版与完整版的定位差；R7 移植选哪条路 | 配置 |
| 版本与许可 | 5.x 主线与 Apache-2.0；商业使用无负担 | 配置 |

## 一、三层架构：内核/组件/软件包目录巡礼

RT-Thread 把整个系统分成三层，每层职责分明、目录也分得开：

- **内核层**（`src/` + `include/` + `libcpu/`）：调度器、线程、IPC（信号量/互斥量/事件/邮箱/消息队列）、定时器、内存管理、对象容器。这一层只关心"怎么把 CPU 公平地分给一堆线程"，和 FreeRTOS 的内核职责一一对应。`libcpu/` 放的是与具体 CPU 架构相关的上下文切换、中断接管（对应 [F2](../freertos/02-context-switch.md) 的 PendSV 那一层）。
- **组件层**（`components/`）：finsh 控制台、设备框架（`rt_device`）、文件系统（dfs）、网络（lwip）、shell、msh，内核之外的"水电"都住这儿。组件通过 `INIT_*_EXPORT` 自动登记自己，应用代码用统一 API 调它们，不用关心谁先初始化。
- **软件包**（`packages/`）：社区三方包，`menuconfig` 里勾选、`pkgs --update` 拉源码，编译时一并进工程。从传感器驱动到 MQTT 客户端到 JSON 解析，生态是 RT-Thread 的护城河。

对照 FreeRTOS：它的内核对应 RTT 的内核层，但 FreeRTOS 没有"组件层"这一档：设备框架/文件系统/控制台都得自己接或用第三方（ESP-IDF 那一套就相当于给 FreeRTOS 配了个"组件层"）。RTT 把这一层做进了主线。

> 口诀版区分：内核打地基（调度/IPC/内存）、组件当水电（控制台/设备/文件系统）、软件包是家具（按需拎包入住）。

## 二、对象模型：rt_object 基类与容器

RT-Thread 的"万物皆对象"不是说用 C++ 写了个抽象基类。它是纯 C，用**结构体嵌套**模拟继承（回 [C4](../../c/04-struct-abi.md)）。`rt_object` 是"基类"，每个具体类型（线程/信号量/定时器/设备/内存池）的结构体第一个成员都是 `rt_object`：

```c
struct rt_object
{
    char       name[RT_NAME_MAX];   /* 名字 */
    rt_uint8_t type;                 /* 类型（线程/信号量/…） */
    rt_uint8_t flag;                  /* 标志（静态/动态） */
    rt_list_t  list;                  /* 挂在对象容器里 */
};

struct rt_thread
{
    struct rt_object parent;   /* 第一个成员 = 对象头，继承 */
    volatile rt_uint32_t sp;    /* 栈顶 */
    rt_uint8_t  current_priority;
    rt_uint8_t  stat;
    ...
};
```

因为 `rt_object` 排在最前，任何具体对象的指针都能"安全地"当成 `rt_object*` 用，这是 C 语言里"继承"的标准玩法。对象容器（`rt_object_container`）按类型维护链表（`rt_object_container[type]`），每创建一个对象就挂进对应链表。finsh 的 `list_thread`/`list_sem`/`list_timer`/`list_device` 能一把梭打印，本质就是遍历对应类型的容器链表，把每个对象当 `rt_object` 读名字、当具体类型读字段。这就是"万能"的来源。

> 钥匙：`rt_object` 排第一 → 任何对象都是 `rt_object` → 容器统一登记 → list API 统一遍历。

## 三、自动初始化：INIT_*_EXPORT 段位表

RT-Thread 不让你在 main 里一条条调初始化函数，而是用链接段（回 [B3](../../build/03-linker-script.md)）把所有初始化函数按"段位"排好：

| 段位宏 | 触发时机 | 典型用途 |
|---|---|---|
| `INIT_BOARD_EXPORT` | `rt_components_board_init()`，最早 | 板级 GPIO/时钟 |
| `INIT_DEVICE_EXPORT` | `rt_components_init()`，设备段 | 设备驱动注册 |
| `INIT_COMPONENT_EXPORT` | `rt_components_init()`，组件段 | finsh/dfs 框架 |
| `INIT_ENV_EXPORT` | `rt_components_init()`，环境段 | 环境变量/挂载 |
| `INIT_APP_EXPORT` | `rt_components_init()`，应用段 | 应用入口 |

机制（以 RT-Thread 官方源码 `rt-thread/src/components.c` 为准，不引行号）：每个宏把函数指针放进一个特殊的链接段（如 `.rti_fn.*`），启动时 `rt_components_board_init` / `rt_components_init` 各自遍历自己负责的那一段、挨个调用。所以你只写 `INIT_DEVICE_EXPORT(my_driver_init)`，从不在 main 调它，它也会在合适时机自动跑，这就是"免调用链"。

段内顺序由链接顺序定（看链接脚本里段的排布），所以**板级依赖关系**要靠段位选择对，而不是靠"我写在前面它就先跑"。这也是常见坑的来源：设备注册依赖了某组件，但你把驱动放进了更早的段，结果"设备没注册上"。

## 四、Nano vs 标准版

RT-Thread 有两个裁剪档：

- **Nano**：内核 + 精简 finsh，**没有**设备框架、文件系统、网络、组件层那一套。体积极小，适合资源紧张（Flash 小于 64KB）或只需要"调度 + IPC"的场景。上手快、移植简单（R7 走 Nano 路最省事）。
- **标准版**：三层齐全，组件/软件包生态全开。要 finsh msh、要 `list_device`、要 dfs 文件系统、要 lwip 上网，就只能上标准版。

选择规则：只跑几个线程做控制，Nano 够用；要用设备框架挂传感器、要文件系统存数据、要网络通信，直接标准版。R7 移植章节会分两条路走。

> 划重点：Nano 没有设备框架/finsh 全功能，想要生态就上标准版（R6/R7）。

## 五、版本与许可

- **主线版本**：RT-Thread 5.x，长期演进。本书所有结论以 5.x 为准。
- **许可**：Apache-2.0，商业使用无负担，可以闭源衍生，只需保留许可声明。与 FreeRTOS 的 MIT 同属宽松档，做产品不用担心许可问题。

RT-Thread 的生态更偏国内（中文文档、国产 MCU 适配多），FreeRTOS 更国际化。两者都是"商业可用"，选哪个看生态与团队熟悉度。

## 记忆锚点

::: tip 一句话记住
**RTT 三层楼：内核打地基、组件当水电、软件包是家具；万物继承 rt_object，初始化按段自动排队。**
:::

**延伸**：RTT 对象模型动画见 [R0 动画](/anim/rtt-object-model.svg)；FreeRTOS 对象管理对照见 [F1](../freertos/01-task-tcb.md)；双 OS 架构对比见 [X0](../compare/00-side-by-side.md)。

## 实物实验

- 在 R7 移植工程上执行 finsh 命令 `list_thread`、`list_device`（对象模型的"户口本"直接打印在终端上）。

## 常见坑

- **Nano 当标准版用**：Nano 没有设备框架/finsh，想要生态就上标准版（R6/R7）。
- **对象当线程用**：`rt_object` 是"概念基类"，直接操作它是糊涂账，走具体类型的 API。
- **自动初始化顺序误解**：段内顺序由链接顺序定，板级依赖关系错时表现为"设备没注册上"。
- **标准版工程漏了 `rt_components_init`**：段里的初始化函数不会自己跑，要在 main 流程里触发 `rt_components_init()`，漏掉就是 `list_device` 一片空、文件系统/网络没动静。
- **menuconfig 后忘了 `pkgs --update`**：Kconfig 只动了配置，软件包源码没拉下来，编译直接报找不到头文件。配置完务必同步拉包。

## 短自测

1. RT-Thread 的三层架构是哪三层？各自对应哪些目录？
<details><summary>看答案</summary>内核层（src/ + include/ + libcpu/）、组件层（components/）、软件包（packages/）。内核打地基、组件当水电、软件包是家具。</details>

2. 为什么 finsh 能用 `list_thread`/`list_sem`/`list_device` 一把梭打印所有对象？
<details><summary>看答案</summary>所有对象都继承自 rt_object（结构体第一个成员就是 rt_object），对象容器按类型维护链表。list API 遍历对应类型的容器链表，把每个对象当 rt_object 读名字、当具体类型读字段，"万物皆对象"让统一遍历成为可能。</details>

3. `INIT_*_EXPORT` 是怎么做到"免调用链"自动初始化的？
<details><summary>看答案</summary>每个宏把函数指针放进一个特殊链接段（如 .rti_fn.*），启动时 rt_components_board_init / rt_components_init 各自遍历自己负责的段、挨个调用。链接脚本（回 B3）的段机制是它的物理基础。所以你只写 INIT_DEVICE_EXPORT(my_init)，从不在 main 调它，它也会自动跑。</details>

4. Nano 和标准版的主要差异是什么？什么场景选哪个？
<details><summary>看答案</summary>Nano 只有内核 + 精简 finsh，没有设备框架/文件系统/网络/组件层；标准版三层齐全。只跑几个线程做控制选 Nano，要用设备框架/文件系统/网络选标准版。R7 移植分两条路走。</details>

5. RT-Thread 用什么开源许可？商业使用有什么影响？
<details><summary>看答案</summary>Apache-2.0。商业可用、可闭源衍生，只需保留许可声明，做产品无负担，与 FreeRTOS 的 MIT 同属宽松档。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| 三层架构目录 | RT-Thread 源码 `src/` + `include/` + `libcpu/`、`components/`、`packages/` |
| `rt_object` 基类 | 以 RT-Thread 官方源码（`rt-thread/include/rtdef.h`）为准（`struct rt_object`） |
| `rt_thread` 继承 `rt_object` | 以 RT-Thread 官方源码（`rt-thread/include/rtthread.h`）为准（`struct rt_thread`，首成员 `parent`） |
| 对象容器 | 以 RT-Thread 官方源码（`rt-thread/src/object.c`）为准（`rt_object_container`） |
| `INIT_*_EXPORT` 段位宏 | 以 RT-Thread 官方源码（`rt-thread/include/rtdef.h`）为准 |
| 段位执行 | 以 RT-Thread 官方源码（`rt-thread/src/components.c`）为准（`rt_components_board_init`/`rt_components_init`） |
| 版本与许可 | RT-Thread 5.x 主线，Apache-2.0 |
| 对照锚点 | [F1](../freertos/01-task-tcb.md) tskTCB 继承对照 |

## 你做到了

- RT-Thread 的"世界观"成型：一张架构图 + 一个对象模型；
- 拿到对照学习的第二锚点：与 F 篇逐章对表开始。

辈分第一：rt_object 领衔，万物皆对象不是口号，是结构体第一排的座位；对象挂进容器统一登记，finsh 那些一把梭的 list 命令才有根。

<div class="achievement">
✅ 下一站：<a href="01-thread-sched.html">R1 线程与调度</a>：rt_thread 解剖与 256 级位图，和 FreeRTOS 逐项对照。
</div>
