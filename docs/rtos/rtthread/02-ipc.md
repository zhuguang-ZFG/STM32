---
title: R2 IPC 全家桶：一套范式五种武器
status: done
difficulty: 2
minutes: 35
---

# R2 IPC：对象容器 + 挂起列表的统一范式

> 🎯 信号量、互斥量、事件集、邮箱、消息队列：RT-Thread 的 IPC 看起来像五件武器，拆开全是同一副骨架：**一个对象头 + 一个资源计数/存储区 + 一条按优先级排队的挂起列表**。学会一副骨架，五种武器全会。

## 本章精髓

1. 挂起列表（suspend list）是灵魂：`rt_ipc_list_suspend/resume` 统一处理"排队等号"：FIFO 或按优先级（PRIO）两种秩序，创建时一个标志位决定。
2. 五种 IPC 的分工：信号量=计数令牌、互斥量=带持有者与继承的令牌、事件集=32 位旗语、邮箱=定长消息（4 字节）池、消息队列=变长消息环形队。选型按"同步还是传信、消息多大"。
3. 互斥量的继承与 FreeRTOS 同构：`rt_mutex` 记录 owner 与 original priority，同样是火星 bug 的解法，读 `rt_ipc.c` 对照 [F5](../freertos/05-sem-mutex.md) 最有味道。

- **能理解**：为什么五种 IPC 共用一套 `rt_ipc_list_suspend/resume`；为什么互斥量的继承和 F5 同构（owner + original priority）；为什么邮箱固定 4 字节而不是变长。
- **能用**：用信号量+邮箱打通中断→线程、线程→线程双通信；E04 双 OS 双跑对比继承行为，两组日志并排核对。

## 先修

- [R1](01-thread-sched.md)、[F4](../freertos/04-queue.md)~[F5](../freertos/05-sem-mutex.md)。

## 先跑起来（10 分钟 quick win）

finsh 一把梭：`list_sem`、`list_mutex`、`list_msgqueue`，刚创建的 IPC 对象全部在册，对象模型（R0）的可观测性再次立功。

先押个骨架数：信号量、互斥量、事件集、邮箱、消息队列五件兵器，拆开到底是几副骨架？押完翻 rt_ipc.c，答案会逼你把五件当一个背。

## 动画：五种武器一副骨架

信号量、互斥量、事件集、邮箱、消息队列轮番上阵，但每一次阻塞与唤醒都落到同一条挂起列表上。五张皮共享一副骨架，排队秩序创建时一锤定音。

![R2 IPC 五种武器一副骨架](/anim/rtt-ipc-skeleton.svg)

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 通用骨架 | rt_ipc_object 与挂起列表；FIFO/PRIO 两秩序 | 库解析 |
| 信号量/互斥量 | take/release 源码路径；继承发生点对照 F5 | 库解析 |
| 事件集 | AND/OR 等待与清零语义；与 FreeRTOS 事件组对表 | 配置 |
| 邮箱 vs 消息队列 | 定长池 vs 变长队；内存来源与拷贝成本 | 代码分析 |
| 反转复现 RTT 版 | E04 双跑：两 OS 继承行为实测对比 | 代码分析 |
| finsh 观测 | list_* 系列命令的对象模型原理 | 库解析 |

## 一、通用骨架：rt_ipc_object 与那条挂起列表

RT-Thread 5.x 把所有 IPC 的公共部分抽到 `struct rt_ipc_object`（位于 `include/rtdef.h`，**以 RT-Thread 官方源码为准**）。它有两个灵魂字段：

- `suspend_list`：一条 `rt_list_t` 双向链表，挂着所有"在等这个 IPC"的线程。`rt_ipc_list_suspend` 把申请失败要阻塞的线程按秩序塞进这条链表；`rt_ipc_resume` 在资源到位时把"该醒的第一个"摘下来唤醒。
- `suspend_list` 的秩序二选一：`RT_IPC_FLAG_FIFO`（先到先得）或 `RT_IPC_FLAG_PRIO`（按线程优先级排序），**创建时一个标志位决定，之后不再改**。

为什么这副骨架能统一五种 IPC：信号量、互斥量、事件集、邮箱、消息队列的"等"都落到这条链表上，差别只在"等的是什么、醒了之后怎么判断能不能拿走"。读源码盯住 `rt_ipc_list_suspend`/`rt_ipc_resume` 这一对函数，五种 IPC 的阻塞/唤醒路径一通百通。

> **【对照】** FreeRTOS 的"等"挂在 `xTasksWaitingToReceive`/`xTasksWaitingToSend` 两条名单上（[F4](../freertos/04-queue.md)），且**默认按优先级排序**。RT-Thread 给你两种秩序的选择：PRIO 是实时系统标配，FIFO 用在"不希望高优先级任务总抢头"的场景。

## 二、信号量与互斥量：take/release 与继承发生点

### 信号量 = 计数令牌

`rt_sem` 的核心字段是 `value`（当前可用令牌数）和 `max_value`（上限）。`rt_sem_take`：`value` 大于 0 减一返回；为 0 就把自己挂进 `suspend_list` 等到点。`rt_sem_release`：`value` 加一，若有人在等就 `rt_ipc_resume` 一个。ISR 纪律同 FreeRTOS：`rt_sem_release` 可在中断里调，`rt_sem_take` 不可，ISR 没有"等"的资格。

### 互斥量 = 带持有者与继承的令牌

`rt_mutex` 比信号量多两个灵魂字段：`owner`（当前持有线程）和 `original_priority`（继承前的原优先级）。`rt_mutex_take` 失败时走继承路径：若 owner 的优先级比当前线程低，把 owner 临时抬到当前优先级，原值存 `original_priority`；`rt_mutex_release` 走镜像路径回落。

> **【对照 F5】** RT-Thread 的继承源码与 FreeRTOS 的 `xTaskPriorityInherit`（[F5](../freertos/05-sem-mutex.md) 第三节）是同一个解法的两种语言：判（持锁者更低）→ 改（升优先级）→ 唤醒路径调整。火星 bug 的解法在两个内核里长得几乎一样。读 `ipc.c`（以 RT-Thread 官方源码为准）对照 `tasks.c` 的 `xTaskPriorityInherit`/`xTaskPriorityDisinherit`，最有味道的对照学习。

## 三、事件集：32 位旗语 + AND/OR + CLEAR

`rt_event` 的核心是一段 32 位 `set` 字段，每位代表一个事件。`rt_event_recv` 等一组事件，支持两种模式：

- **RT_EVENT_FLAG_AND**：32 位里**所有指定的位**都置位才醒（"全部条件满足"）；
- **RT_EVENT_FLAG_OR**：**任意一位**置位即醒（"任一事件发生"）；
- **RT_EVENT_FLAG_CLEAR**：醒时顺便把命中的位清零（"消费式"）；不带 CLEAR 则位保持（"广播式"）。

> **【对照】** 这套语义与 FreeRTOS 事件组（`xEventGroupWaitBits`）几乎一致：`pdTRUE` 对应 CLEAR，`pdFALSE` 对应不清零；`xAnd` 对应 AND，`xOr` 对应 OR。**API 名不同，语义同**：迁移时逐参数对照，别凭名字猜。

## 四、邮箱 vs 消息队列：定长池 vs 变长队

| 维度 | 邮箱 `rt_mailbox` | 消息队列 `rt_messagequeue` |
|---|---|---|
| 单条大小 | **固定 4 字节** | 调用方指定（变长） |
| 拷贝成本 | 一次 4 字节拷贝 | 整条按 size 拷贝 |
| 典型用途 | 传指针/句柄/小型枚举值 | 传结构体/帧/字符串 |
| 内存来源 | 创建时申请 `size * 4` 字节环形池 | 创建时申请 `size * msg_size` 字节环形池 |

**邮箱固定 4 字节**是设计取舍，不是缺陷：它专门服务"传一个指针或一个句柄"的场景，32 位平台上指针正好 4 字节，写邮件就是把指针塞进去，对方拿到的就是指针本身（指向的对象不拷贝）。要传结构体请用消息队列（队列会按你给的 `msg_size` 整条拷贝）。

两者背后都是**环形缓冲**：send 写头、recv 读尾，满了发送方挂起、空了接收方挂起，挂起同样走 `rt_ipc_list_suspend`，再次印证"一副骨架"。

> **【对照 F4】** FreeRTOS 的 `xQueue`（[F4](../freertos/04-queue.md)）只有"变长队列"一种形态。RT-Thread 把"定长 4 字节"单独拎出来叫邮箱，背后是更明确的"传指针/句柄"语义。FreeRTOS 想做同样的事得自己约定 item size=4。

## 五、反转复现 RTT 版：E04 双跑

把 [E04](../../lab/e04-priority-inversion.md) 的三任务剧本在 RT-Thread 工程上跑两遍：`rt_sem`（当"锁"用）版 vs `rt_mutex` 版。

预期：信号量版同样上演死亡螺旋：H 等锁、L 持锁、M 狂跑把 L 挤下台；互斥量版继承一启动，L 被抬到 H 的优先级，M 立刻让路。**两份日志并排贴**，与 FreeRTOS 版逐行对比：

- 等待时间是否一致？继承点是否在同一个相对位置？
- 不同的是 RT-Thread 的 `list_thread` 能直接打印优先级变化的现场：继承瞬间 L 的 priority 列从 1 变 3，还锁后回落 1，**优先级继承在终端上看得见**，这是 RT-Thread 可观测性的额外加分。

## 六、finsh 观测：list_* 系列为什么万能

`list_sem`、`list_mutex`、`list_event`、`list_mailbox`、`list_msgqueue`，一共五条 finsh 命令，一行命令列出全系统该类型的所有 IPC 对象，含名称/计数/持有者/挂起线程数。

为什么这么爽：所有 IPC 都继承自 `rt_object`（[R0](00-arch.md)），对象容器按类型统一登记：`list_*` 命令就是遍历对应类型的容器链表逐条打印。这是"万物皆对象"在 IPC 篇的直接兑现：FreeRTOS 要你自己维护一份句柄表，RT-Thread 内核替你管。

> **quick win 落地**：刚 create 完一个邮箱，立刻 `list_mailbox` 看到它在册、挂起线程数=0；再 `list_thread` 看主线程阻塞在 `rt_mb_recv` 上，两屏对照，IPC 的工作状态一目了然。

## 记忆锚点

::: tip 一句话记住
**一副骨架五张皮：令牌、带主令牌、旗语、定长池、变长队；排队要么 FIFO 要么 PRIO，创建时一锤定音。**
:::

**延伸**：RTT IPC 五种武器动画见 [R2 动画](/anim/rtt-ipc-skeleton.svg)；FreeRTOS 队列/信号量对照见 [F4](../freertos/04-queue.md) 和 [F5](../freertos/05-sem-mutex.md)；双 OS IPC 对比见 [X0](../compare/00-side-by-side.md)。

## 实物实验

- E04 RT-Thread 版：与 FreeRTOS 版同剧本，两组日志并排贴，继承机制的行为一致性/差异亲眼核对。

## 常见坑

- **事件集 flag 混用接收选项**：RT_EVENT_FLAG_AND/OR + CLEAR 组合语义，与 FreeRTOS 事件组几乎一致但 API 名不同，迁移时逐参数对照。
- **邮箱当消息队列用**：邮箱固定 4 字节（指针/句柄专用），塞结构体请用消息队列。
- **IPC 对象在中断里的权限**：ISR 只能 send/release，不能 take（同 FreeRTOS 纪律）。
- **delete 时还有线程挂着**：删除前确保无人等待，否则唤醒路径指向已释放内存（RT-Thread 会报警告/断言，别忽略）。
- **互斥量 release 也别在 ISR 调**：信号量 release 可在 ISR，但互斥量 release 涉及继承回落，ISR 里没有"持有者"概念，整条互斥量路径都是禁区，别和信号量的纪律混。

## 短自测

1. 五种 IPC 共用哪条数据结构？为什么这套设计能让 `rt_ipc_list_suspend/resume` 通吃？
<details><summary>参考答案</summary>共用 struct rt_ipc_object 的 suspend_list（一条 rt_list_t 双向链表）。五种 IPC 的"等"都是"把自己挂进这条链表等到点被唤醒"，差别只在"等什么、醒了怎么判断"，所以挂起/唤醒这对操作可以通用。</details>

2. `RT_IPC_FLAG_FIFO` 与 `RT_IPC_FLAG_PRIO` 的区别是什么？什么时候选 FIFO？
<details><summary>参考答案</summary>PRIO 按等待线程的优先级排序唤醒（高优先级先拿），FIFO 按进入顺序先到先得。实时系统默认 PRIO；FIFO 用在"不希望高优先级任务总抢头"或"想保证低优先级任务也公平拿到资源"的场景。一旦创建不再改。</details>

3. 互斥量的继承与 FreeRTOS 的 `xTaskPriorityInherit` 同构，请说出对应字段与三步动作。
<details><summary>参考答案</summary>RT-Thread 的 owner 对应 FreeRTOS 的 xMutexHolder；original_priority 存继承前的原优先级；继承动作都是"持锁者优先级低于等待者就升到等待者级别"，还锁时走镜像路径回落原值。落点对照：ipc.c（以 RT-Thread 官方源码为准）vs tasks.c 的 xTaskPriorityInherit/xTaskPriorityDisinherit。</details>

4. 邮箱为什么固定 4 字节？什么场景下用它？
<details><summary>参考答案</summary>32 位平台指针正好 4 字节，邮箱专门服务"传指针/句柄/小型枚举值"，把指针塞进去，对方拿到的就是指针本身（指向对象不拷贝）。要传结构体/帧/字符串请用消息队列（按指定 msg_size 整条拷贝）。</details>

5. RT-Thread 的事件集与 FreeRTOS 事件组语义几乎一致，迁移时容易踩什么坑？
<details><summary>参考答案</summary>API 名不同：RT-Thread 用 rt_event_recv/send，FreeRTOS 用 xEventGroupWaitBits/SetBits，但参数语义对应：RT-Thread 的 RT_EVENT_FLAG_AND/OR 对应 xAnd/xOr，RT_EVENT_FLAG_CLEAR 对应 pdTRUE（消费式清零）。逐参数对照，别凭名字猜语义。</details>

## 对照表：本章概念 → 源码落点

| 概念 | 落点（以 RT-Thread 5.x 官方源码为准） |
|---|---|
| rt_ipc_object 通用骨架 | `include/rtdef.h`（rt_ipc_object）+ `src/ipc.c`（rt_ipc_list_suspend/resume） |
| FIFO/PRIO 秩序 | 各 IPC 创建函数的 flag 参数（rt_sem_create 等） |
| 互斥量继承 | `src/ipc.c` rt_mutex_take/release vs [F5](../freertos/05-sem-mutex.md) tasks.c xTaskPriorityInherit |
| 事件集 AND/OR+CLEAR | `src/ipc.c` rt_event_recv/send（与 FreeRTOS 事件组对表） |
| 邮箱 4 字节定长 | `src/ipc.c` rt_mb_send/recv（环形 4 字节池） |
| 消息队列变长 | `src/ipc.c` rt_mq_send/recv（按 msg_size 环形拷贝） |
| finsh list_* 万能 | [R0](00-arch.md) 对象容器遍历；list_sem/mutex/event/mailbox/msgqueue |
| 反转实验 | [E04](../../lab/e04-priority-inversion.md) 双 OS 双跑 |

## 延伸阅读

`rt_mutex` 优先级继承的理论出处：

- **[\[D2\]](../../reference/bibliography.md#papers)** Sha, Rajkumar, Lehoczky 1990 — 继承协议的原始论文；记住它不防死锁，天花板协议才防。

## 你做到了

- IPC 从"五个 API 要背"变成"一副骨架推演"；
- 双 OS 反转实验双跑——你的证据链比教科书还硬。

骨架只有一副：一个对象头、一份资源或存储、一条挂起列表，五件兵器是同一副骨头换皮。往后选型先问场景要什么，再问这件兵器披的是哪层皮。

<div class="achievement">
✅ 下一站：<a href="03-mem.html">R3 内存管理</a>：memheap/slab/TLSF 三选与内存池的确定性之美。
</div>
