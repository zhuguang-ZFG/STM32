---
title: R5 finsh 控制台：板子上的 shell
status: done
difficulty: 1
minutes: 25
---

# R5 finsh：在单片机上跑 shell 的原理

> 🎯 插根串口线，板子上敲 `list_thread` 回车，线程表跃然屏上。这不是 IDE 的专利，是 finsh：RT-Thread 自带的微型 shell。它的原理就一条：**把函数名和地址编进一张符号表，运行时按名调用**。

## 本章精髓

1. MSH_CMD_EXPORT 的魔法：宏展开=把一个 `{名字, 描述, 函数指针}` 结构体放进专用链接段（FsymTab），链接器收齐，运行时 finsh 按名字段内查找并调用（链接段的又一神用，回 [B3](../../build/03-linker-script.md)/R0 自动初始化）。
2. 解析器极简：按空格切词→首词查符号表→参数逐个转换（支持整型/字符串）→按原型调用，所以命令的形参列表是受约束的。
3. list 系列的实现套路：`list_thread` 就是遍历对象容器（R0）+ 格式化打印，你会写 list，就会给自己的子系统加自检命令。

- **能理解**：为什么用链接段而不是运行时注册表；为什么命令签名必须是 `int func(int argc, char **argv)`；finsh 线程为什么需要单独预算栈而不是用主线程或空闲线程。
- **能用**：给工程加一个 `led` 命令实测；在 map 文件里定位 FSymTab 段；给自己的子系统写一个 `list_xxx` 自检命令。

## 先修

- [R0 对象模型](00-arch.md)、[S7 USART](../../stm32/07-usart.md)、[C5 函数指针](../../c/05-func-pointer.md)。

## 先跑起来（10 分钟 quick win）

串口终端连上 R7 移植工程：回车出 `msh />`，敲 `help`，全部命令清单立刻到手（自助文档系统）。

敲 help 之前先押个名册：那张命令清单存在哪、运行时又是谁按名翻它？押完去 map 文件里找 FSymTab 段，答案在链接期就排好了。

## 动画：finsh 命令分发四步

编译期宏钉进 FSymTab 段、链接期界桩圈地、运行期切词/查表/转换/调用：三个命令词从输入行飞向各自的步骤框，光标闪烁的终端就是板上的最小人机界面。

![R5 finsh 命令分发：宏钉进段，shell 按名翻牌](/anim/rtt-finsh-dispatch.svg)

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 符号表机制 | MSH_CMD_EXPORT 宏展开与 FsymTab 段 | 库解析 |
| 解析与调用 | 切词/查表/类型转换/调用四步 | 库解析 |
| list 系列 | 对象容器遍历；给自己的子系统写 list 命令 | 代码分析 |
| 自定义命令 | `led` 命令完整实战（参数解析+错误提示） | 代码分析 |
| 裁剪与资源 | finsh 的 RAM/Flash 账；生产固件关不关 | 配置 |

## 一、符号表机制：MSH_CMD_EXPORT 的魔法

```c
/* 代表性展开（字段名随版本微调，三字段稳定） */
#define MSH_CMD_EXPORT(name, desc)                              \
    USED_CMD const struct msh_cmd_entry _cmd_##name             \
    SECTION("FSymTab") = { #name, desc, (int (*)(int, char**))name };

struct msh_cmd_entry
{
    const char *name;                       /* 名字：find 时的 key */
    const char *desc;                       /* 描述：help 时显示 */
    int (*func)(int argc, char **argv);     /* 函数指针：调用入口 */
};
```

宏做三件事：

1. 定义一个 `msh_cmd_entry` 结构体，三字段 `{名字, 描述, 函数指针}`；
2. 用 `SECTION("FSymTab")` 把它放进专用链接段；
3. `used` 防止编译器因为"没人引用"而删掉它，引用由链接段在运行时建立。

链接脚本（回 [B3](../../build/03-linker-script.md)）划出 FSymTab 段并打起止界桩：

```
. = ALIGN(4);
__fsymtab_start__ = .;
KEEP(*(FSymTab))
__fsymtab_end__ = .;
```

`KEEP` 是关键：没有它，gc-sections 会把"没人引用"的命令全清掉（常见坑第 2 条）。运行时 finsh 在 `[__fsymtab_start__, __fsymtab_end__)` 区间遍历，按名字二分/线性查找，命中就调用 `entry->func`。**这就是 [R0](00-arch.md) 自动初始化段的同一招：把"编译期已知、运行期要遍历"的东西钉进段里，链接器替你收齐。** 第三次见这个手法了（R0 INIT 段、B3 链接脚本、这里 FSymTab），你应该已经炉火纯青。

## 二、解析与调用：切词/查表/类型转换/调用

用户敲 `led 1 on` 回车，解析器走四步：

1. **切词**：按空格切成 `led 1 on` 三段，首词是命令名，其余是参数。
2. **查表**：拿 `"led"` 在 FSymTab 区间里按名查找（命令少时线性，多时排序后二分），命中拿到 `entry`。
3. **类型转换**：参数逐个转：字符串原样传（`"on"`），数字用 `atoi`/`strtol`（`"1"` → `1`）。所以命令形参类型受约束：finsh 只认整型和字符串，不支持浮点、结构体直接传。
4. **调用**：`entry->func(argc, argv)`：`argc=3, argv` 三段，与 C main 同型。

签名约束由此而来：**命令函数必须是 `int func(int argc, char **argv)`**（常见坑第 1 条）。原型不符（写成 `void func(void)` 或多了个参数）→ 解析器按 argc/argv 调用，栈布局对不上，一调就崩。

## 三、list 系列：遍历对象容器

`list_thread` 不是魔法，就是"遍历线程对象容器 + 格式化打印"。框架（[R0](00-arch.md)）把所有线程挂在 `rt_object_container[RT_Object_Class_Thread]` 链表上，`list_thread` 走这张链表逐个打印：

```c
int list_thread(int argc, char **argv)
{
    rt_kprintf("thread    pri  status    sp     ...\n");
    for (each tcb in thread container)
        rt_kprintf("%-8s %3d  %-8s 0x%08x ...\n",
                   tcb->name, tcb->current_priority, status_str, tcb->sp);
    return 0;
}
MSH_CMD_EXPORT(list_thread, list all threads);
```

`list_device`/`list_timer`/`list_sem`/`list_mutex` 同构，只是遍历的对象容器不同。**会写一个 list，就会给自己的子系统加自检命令**：你的驱动/中间件维护一个链表（任务、连接、缓存块），照葫芦画瓢写一个 `list_xxx`，`MSH_CMD_EXPORT` 一挂，`help` 里就有、运行时就能查，板子上的自检面板到手。

## 四、自定义命令：led 命令实战

把 [E01](../../lab/e01-blink.md) 的点灯包装成 shell 命令，串口敲 `led 1 on` 就亮灯：

```c
#include <rtthread.h>
#include <rtdevice.h>

static rt_base_t leds[] = { GET_PIN('B', 0), GET_PIN('B', 1), GET_PIN('B', 5) };

int led(int argc, char **argv)
{
    if (argc < 3) {
        rt_kprintf("usage: led <index 0..2> <on|off>\n");
        return -1;
    }
    int idx = atoi(argv[1]);
    if (idx < 0 || idx > 2) { rt_kprintf("index out of range\n"); return -2; }
    rt_base_t val = (strcmp(argv[2], "on") == 0) ? PIN_HIGH : PIN_LOW;
    rt_pin_write(leds[idx], val);
    return 0;
}
MSH_CMD_EXPORT(led, "led <index> <on|off> - control onboard RGB");
```

串口实测：

```
msh /> help              ← 全部命令清单
msh /> led 1 on          ← LED1 亮
msh /> led 1 off         ← LED1 灭
msh /> led 9 on          ← "index out of range"
```

注意三件事：**argc 含命令名本身**（`led` 是 argv[0]，所以 `led 1 on` 的 argc=3）；**错误路径要有提示和返回码**（用户敲错能看清）；**命令名别撞内核自带**（`help`/`list`/`ps` 等已占）。

## 五、裁剪与资源：RAM/Flash 账 + 生产开关

finsh 不是免费的，上板前要算账：

- **RAM**：finsh 线程（tshell）单独预算栈，`FINSH_THREAD_STACK_SIZE` 默认 2~4KB，`list` 类命令带格式化打印，栈深由 `rt_kprintf` 的格式化嵌套决定，开小了爆栈（常见坑第 3 条）。再加 RX 环形缓冲、history 缓冲。
- **Flash**：每条命令在 FSymTab 占一个 entry（名字串 + 描述串 + 函数指针 ≈ 16~24 字节），再加解析器 + list 系列代码，一整套 msh 约 10~20KB Flash（视裁剪）。

生产固件的取舍：

- **保留 msh，关 C 表达式**：`FINSH_USING_MSH_ONLY`，砍掉 VSymTab 和 C 表达式解析器，省一块 Flash，留下 `led`/`list` 这类工程命令。
- **整包关掉**：量产固件若串口对外暴露，finsh 就是攻击面，任何人接根线就能 `rt_thread_control` 改优先级、`list` 翻内存。配置 `RT_DEBUG` 或直接关 `FINSH_USING_MSH`，仅在工程版保留。

两种模式速记：

- **msh（命令行，默认）**：`MSH_CMD_EXPORT` 注册，argc/argv 调用，像 bash：轻、安全面窄。
- **finsh C 表达式（老式）**：能在 shell 里直接写 C 表达式、调任意函数（`rt_kprintf("%d", 3+4)`），靠 VSymTab 把全局变量/函数地址也编进段，重、调试强但攻击面大，量产基本不用。

## 记忆锚点

::: tip 一句话记住
**宏把函数钉进段里，shell 按名翻牌；help 即是文档，list 即是自检：finsh 是板子上的最小人机界面。**
:::

**延伸**：RTT finsh 命令分发动画见 [R5 动画](/anim/rtt-finsh-dispatch.svg)；链接脚本段属性在 [B3](../../build/03-linker-script.md) 详解；GDB 调试对照见 [B6](../../build/06-flash-debug.md)。

## 实物实验

- 自定义 `led` 命令 + 在 [E04](../../lab/e04-priority-inversion.md) 实验里用 finsh 动态改任务优先级（`rt_thread_control` 包一个命令），现场调参不重烧。

## 常见坑

- **命令函数原型不符**：finsh 参数约定（int argc, char**argv）写错，调用即崩。
- **段被 gc-sections 回收**：FsymTab 段必须 KEEP，链接脚本少了它，命令"编译通过但 help 里没有"。
- **finsh 线程栈太小**：命令里调用深（如 list 带格式化打印）爆栈，finsh 栈单独预算（F7 方法）。
- **生产固件忘裁剪**：finsh 是调试利器也是攻击面，量产版 RT_DEBUG/FINSH 配置过一遍。
- **finsh 线程优先级设得比业务任务还高**：tshell 默认优先级较低是有意为之：敲命令时若它抢占业务任务，整板都在等 finsh 让出。别为了"命令响应快"把 finsh 拉到最高优先级，否则业务实时性被你亲手破坏。

## 短自测

1. MSH_CMD_EXPORT 的宏展开做了什么？为什么用链接段而不是运行时注册表？
<details><summary>参考答案</summary>宏定义一个 {名字， 描述， 函数指针} 结构体，用 SECTION 把它放进 FSymTab 段、用 used 防止编译器删除。用链接段而不是运行时注册表的好处：编译期就把所有命令收齐，启动即可用、无需额外 init 代码；省掉运行时注册的 RAM 开销和时序问题；与 R0 自动初始化段是同一手法。</details>

2. 命令函数为什么必须是 int func(int argc, char **argv) 签名？签名不符会怎样？
<details><summary>参考答案</summary>解析器四步最后一步按 (int argc, char** argv) 这个原型把切好的参数压栈调用，签名是解析器和命令之间的 ABI。写成 void func(void) 或多带参数，栈布局对不上：argv 指针被当成你的"参数"、argc 落到野地址，一调就 HardFault。这是 finsh 崩溃的头号原因。</details>

3. 链接脚本里 FSymTab 段少了 KEEP，会发生什么？
<details><summary>参考答案</summary>gc-sections 优化会以"没人引用"为由把整个 FSymTab 段删掉，因为命令函数只在段里被"按名引用"、没有直接调用点。结果：编译完全通过、烧进去 help 里一条命令都没有、敲啥都 command not found。必须 KEEP(*(FSymTab)) 把段钉死。</details>

4. finsh 的两种模式有什么区别？为什么 msh 成为默认？
<details><summary>参考答案</summary>msh 是命令行风格（命令+参数，argc/argv 调用），轻、安全面窄；finsh C 表达式风格能在 shell 里直接写 C 表达式、调任意函数（要 VSymTab 把变量和函数都编进段），调试强但重、攻击面大。msh 成为默认是因为量产需要安全面窄和体积小，调试用得着的 C 表达式在工程版单独开。</details>

5. finsh 线程栈为什么需要单独预算？默认大小不够时会怎样？
<details><summary>参考答案</summary>finsh 命令（尤其 list 系列）带 rt_kprintf 格式化打印，嵌套深、局部变量多，栈消耗波动大；和业务任务共用栈会互相挤爆。单独预算 FINSH_THREAD_STACK_SIZE（默认 2~4KB）才安全。不够时表现为：敲 list_thread 这种深打印就 HardFault 或栈溢出告警，且只在特定命令才暴露，调试时要把栈开大一点先验证。</details>

## 对照表：本章概念 → 源码落点

| 概念 | 落点（RT-Thread 5.x） |
|---|---|
| MSH_CMD_EXPORT 宏 + msh_cmd_entry 结构 | `components/finsh/msh.h` |
| FSymTab 段 + KEEP 界桩 | 链接脚本（回 [B3](../../build/03-linker-script.md)） |
| 切词/查表/调用解析器 | `components/finsh/msh.c`（msh_exec） |
| list_thread / list_device | `components/finsh/msh_cmd.c` |
| finsh 线程 + 栈预算 | `components/finsh/shell.c` + `rtconfig.h` FINSH_THREAD_STACK_SIZE |

## 你做到了

- 板子有了"键盘鼠标"；
- 链接段技术第三次立功，你对它的运用已炉火纯青。

名册叫 FSymTab：编译期就把命令名和函数指针排进链接段，运行时按名翻页。以后想给自己的子系统加 list 命令，走的还是这条老路。

<div class="achievement">
✅ 下一站：<a href="06-env-menuconfig.html">R6 Env 与 menuconfig</a>，RT-Thread 的"点单系统"：scons 与 Kconfig。
</div>
