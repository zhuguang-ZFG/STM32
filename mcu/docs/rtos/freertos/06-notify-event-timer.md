---
title: F6 任务通知、事件组与软件定时器
status: done
difficulty: 2
minutes: 50
---

# F6 任务通知、事件组与软件定时器

> 🎯 队列通用但有"运费"：建队列要 RAM、发送要拷贝。任务通知直接写进对方 TCB——零队列、零拷贝、一次写操作。一对一的通信场景，通知几乎总是更优解；但"更快"快多少取决于配置与场景，别背固定百分比。

## 本章精髓

1. **任务通知 = TCB 里的 32 位邮箱**：每个任务在 TCB 里有 `ulNotifiedValue[]`（值）+ `ucNotifyState[]`（状态）两个字段，槽位数由 `configTASK_NOTIFICATION_ARRAY_ENTRIES` 决定（本工程=1，所以"通知容量一"）。`xTaskNotifyGive` 走 eIncrement 累加，`xTaskNotify` 可覆盖/置位，**计数语义和覆盖语义是两条不同的路**。
2. **事件组 = 24 个标志位的"公告栏"**（TickType_t 32 位，扣掉 8 个控制位）：多任务按"任意/全部"条件等待一组位。**清位不是先唤醒者独占**：`xEventGroupSetBits` 把整个等待列表走一遍、满足条件的全部唤醒，最后按 `uxBitsToClear` **汇总一次清掉**（V11.1.0 `event_groups.c:547` 起）。
3. **软件定时器跑在"守护任务"里，但不是零成本**：`configUSE_TIMERS=1` 一开就固定付掉 **1312 B**（守护任务 1128 + 命令队列 184，此时一个定时器都还没建），每建一个定时器再收 **56 B**，另有 **60 B** 落在 `.bss`、`configTOTAL_HEAP_SIZE` 调多大都管不到它（本机 `timers.o` 实测，见 §八）。回调在守护任务上下文**串行**执行，代价也不是一句"晚一拍"：Σ(回调耗时 ÷ 周期) **小于一**时，零耗时定时器的最大迟到恰好等于最大的那次回调耗时；**不小于一**时迟到跳出耗时之外发散，并连环补拍（§五 的模拟器实测）。所以回调里**禁止阻塞**，周期性小任务用它代替创建真任务，省的是那 616 B 的栈与 TCB，不是 1312 B。

- **能理解**：为什么通知比队列快（无队列对象、无拷贝）；为什么"快 45%"不能当无条件结论；为什么事件组清位是汇总清而不是独占清。
- **能用**：用通知做一对一同步；用事件组做多条件汇合；用软件定时器做周期杂务。

## 先修

- [F1 任务与 TCB](01-task-tcb.md)、[F4 队列](04-queue.md)、[F5 信号量](05-sem-mutex.md)。

## 先跑起来（10 分钟 quick win）

**不要板子的那条先跑**：本章每个字节数都来自 `code/rtos/06-timers/probe.sh`，七步一条命令跑完（只要交叉编译器和上游内核）：

```bash
cd code/rtos/06-timers && sh probe.sh   # 结构体尺寸、机身立即数、.bss、五幕分派模拟
```

`code/rtos/01-freertos-lab` 场景 2/3/4（要板子）：

```bash
make DEMO_SCENE=2 flash    # 通知：took 的值就是"欠账总数"
make DEMO_SCENE=3 flash    # 事件组：ANY 先醒，ALL 等齐
make DEMO_SCENE=4 flash    # 定时器：slow cb 耗时 50ms → fast cb 最大迟到恰好 50ms
```

先押个首付：configUSE_TIMERS 这一行敲下去，一个定时器都还没建，RAM 先被划走多少？押完跑 probe.sh，尺寸表当账本。

## 动画：三条路各一张

通知的两种语义（计数 vs 覆盖）、事件组的 ANY/ALL 与汇总清位、软件定时器的命令队列→守护任务→回调，各自一张图：

![任务通知动画](/anim/task-notification.svg)

![事件组等待动画](/anim/event-group-wait.svg)

![软件定时器动画](/anim/software-timer-service.svg)

## 版本与配置前提

- 内核：上游 **FreeRTOS-Kernel V11.1.0**。通知/事件组/定时器的 API 名与语义以 `include/task.h`、`event_groups.c`、`timers.c` 为准。
- 本工程 `FreeRTOSConfig.h`：`configTASK_NOTIFICATION_ARRAY_ENTRIES=1`、`configUSE_TIMERS=1`、`configTIMER_TASK_PRIORITY=4`（守护任务跑最高）、`configUSE_16_BIT_TICKS=0`（事件组 24 个可用位）。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、通知原理 | TCB 两字段；give/take/notify 三组 API 的语义差 | 库解析 |
| 二、通知 vs 队列/信号量 | 快在哪里、为什么；选型表（一对一/多对一/多对多） | 配置 |
| 三、事件组 | 位语义/ANY/ALL/汇总清位 | 代码分析 |
| 四、软件定时器 | 守护任务模型；one-shot vs auto-reload | 配置 |
| 五、回调纪律 | 不能阻塞的原因推导；回调里该干什么 | 代码分析 |
| 六、代码分析 | 场景 2/3/4 的日志对照 | 代码分析 |

## 一、通知原理：TCB 里的 32 位邮箱

每个任务的 TCB 里有两组字段（数组长度 = `configTASK_NOTIFICATION_ARRAY_ENTRIES`）：

- `ulNotifiedValue[]`：32 位值；
- `ucNotifyState[]`：状态（未通知/已通知待取）。

三组 API（V11.1.0 `task.h` 宏 → `tasks.c` 实现）：

| API | 语义 | 落点 |
|---|---|---|
| `xTaskNotifyGive(x)` | 通知值 +1（eIncrement），**计数语义** | `task.h:2984` → `xTaskGenericNotify`（`tasks.c:7832`） |
| `xTaskNotify(x, v, eSetValueWithOverwrite)` | 直接覆盖，**覆盖语义** | `task.h:2611` |
| `ulTaskNotifyTake(pdTRUE, timeout)` | 阻塞到计数非零，取走时清零 | `task.h:3177` → `xTaskGenericNotifyWait`（`tasks.c:7717`） |

注意函数名：是 **`ulTaskNotifyTake`**（返回计数值），不是 `xTaskNotifyTake`，后者不存在。

## 二、通知 vs 队列/信号量：快在哪里

通知比队列快的原因很具体：**没有队列对象、没有拷贝、没有额外的链表项**：写一次 TCB 就完事。但"快多少"取决于你的配置（队列深度、是否从中断上下文、调度器当时的状态），官方文档里出现过"约 45%"的实测数字，那是**某个版本某个配置下**的结果，不是无条件结论。

选型表：

| 场景 | 选型 |
|---|---|
| 一对一、容量一、只要信号 | 通知（give/take） |
| 一对一、要带 32 位数据 | 通知（notify 覆盖语义） |
| 多对一 / 一对多 | 队列 |
| 多对多、要带任意长数据 | 队列 |
| 要等"几个条件都齐" | 事件组 |

## 三、事件组：ANY/ALL 与汇总清位

`xEventGroupWaitBits(组, 位掩码, xClearOnExit, xWaitForAllBits, timeout)`：

- `xWaitForAllBits=pdFALSE` → **ANY**：任一位满足就醒；
- `xWaitForAllBits=pdTRUE` → **ALL**：所有位都满足才醒。

**清位的真相**（V11.1.0 `event_groups.c` `xEventGroupSetBits`）：`SetBits` 会把整个等待列表**完整走一遍**，每个满足条件的任务都被唤醒；每个带 `xClearOnExit` 的等待者把它等的位并进 `uxBitsToClear`，**列表走完后统一清一次**（`pxEventBits->uxEventBits &= ~uxBitsToClear`）。

所以"第一个等到的人把位清掉、后来者永远等不到"是错的：**同一次 SetBits 里所有满足条件的等待者都能醒**，清位发生在所有人都看完之后。真正的坑在另一边：如果你想让"下一批人"也看到这些位，就别开 `xClearOnExit`。

## 四、软件定时器：守护任务模型

`xTimerCreate(名字, 周期, autoReload, id, 回调)` 创建的定时器**不是**一个独立的执行上下文。所有定时器的回调都跑在同一个**守护任务**里（`timers.c` 的 `prvTimerTask`）：

```
你的代码 xTimerStart() → 命令进 xTimerQueue → 守护任务取出执行回调
```

守护任务的优先级由 `configTIMER_TASK_PRIORITY` 决定（本工程=4，最高）。"只有一个守护任务"不是修辞，是数出来的：`timers.c` 全文创建任务的调用点 4 处（V11.1.0 的 `:260`、`:276`、`:295`、`:310`，覆盖静态/亲和性/动态几种组合），四处都在 `xTimerCreateTimerTask` 的函数体内、第一个实参全都写作 `prvTimerTask`，定时器系统不会为你多建任务。能调到用户回调的地方也只有 4 处（`:713`、`:744`、`:960`、`:1021`），分属三个 `static` 函数，而这三个函数只出现在 `prvTimerTask` 的调用树里。**所以回调串行是结构决定的，不是配置出来的。**

守护任务也不是"每拍醒一次"：它按 `xNextExpireTime - xTimeNow` 阻塞在命令队列上（`:820`），表空时下一个到期时刻是 0，于是睡到 tick 溢出；一轮处理里时钟只采样一次（`:795`），整轮判定共用同一个 `xTimeNow`。

串行磨蹭到底贵多少，§五 用模拟器把它算成了数，不是"晚一拍"这么轻。

one-shot vs auto-reload：`autoReload=pdTRUE` 周期触发，`pdFALSE` 触发一次就停。

## 五、回调纪律：为什么禁止阻塞

回调跑在守护任务里，守护任务是"所有定时器共用的执行线程"。你在回调里 `vTaskDelay`，守护任务阻塞，**所有**定时器停摆。所以回调里：

- **可以**：置标志、发通知、写队列（不带阻塞的版本）、改 GPIO；
- **不可以**：`vTaskDelay`、等队列满/空（带 timeout）、等信号量。

想让定时器"每 100ms 闪一下灯"：回调里只翻 GPIO，别在回调里睡。

### 磨蹭的代价能算：五幕实测

把守护任务的分派规则原样抄成宿主机模拟器（`code/rtos/06-timers/sim_daemon.c`，事件表写死，所以每次跑出的数一样），两个定时器 fast/slow，观测窗口 1200 拍。规则逐条钉在上游源码行号上：`probe.sh` 第 7 步用 `at_line` 校验这十一行，行号一漂这一步就失败，宁可红也不给错的数：R1 只看表头 `timers.c:859`、R2 到期比较 `:800`/`:803`、R3 睡到下一个到期 `:820`、R4 重装调用 `:735`、R5 补拍循环 `:706`/`:709` 与判据 `:904`/`:908`、R6 插入条件 `list.c:192`、R7 一轮一次采样 `:795`。

| 幕 | fast 周期/耗时 | slow 周期/耗时 | Σ(耗时÷周期) | fast 最大迟到 | fast 补拍 | fast 连发 | fast 欠账 |
|---|---|---|---|---|---|---|---|
| A | 100/0 | 120/0 | 0.000 | 0 | 0 | 1 | 0 |
| B | 100/0 | 120/50 | 0.416 | **50** | 0 | 1 | 50 |
| E | 100/0 | 300/200 | 0.666 | **200** | 6 | 3 | 200 |
| C | 100/0 | 120/200 | 1.666 | **520** | 6 | 6 | 520 |
| D | 100/0 | 120/250 | 2.083 | 470 | 5 | 5 | **970** |

一条律：**Σ(回调耗时 ÷ 周期) 小于一时，零耗时定时器的最大迟到恰好等于最大的那次回调耗时**：A 的 0、B 的 50、E 的 200 三幕全是这个形状；**一旦不小于一，迟到就跳出所有耗时之外发散**，C 幕的 520 早就盖过了那个 200，而 D 幕收工时 fast 还欠着 970 拍（观测窗口总共才 1200 拍）。注意 E 幕那个反直觉的组合：耗时 200 大于 fast 的周期 100，却小于 slow 自己的周期 300，占空比仍不满 → 迟到有界。所以关键从来不是"谁的回调长"，而是总占空比。

**拍没有丢。** 上面每一对（幕 × 定时器）都满足"欠账 < 周期 **或** 补拍数 > 0"：欠下的要么只是还没到，要么已经当场补开了。原因是自动重装的锚点写的是 `xExpiredTime += pxTimer->xTimerPeriodInTicks`（`:709`），不是"现在 + 周期"，周期不漂，欠的一定要还。所以正文原来那句"数 fast cb 丢了几拍"问错了问题：该数的是欠账和连发。

**同一刻到期谁先跑？** 由 `list.c:192` 那个插入条件决定：`pxIterator->pxNext->xItemValue <= xValueOfInsertion`，是 `<=` 不是 `<`，等于时继续往后走，于是**先入表者先服务**。模拟里 t=600 那一拍 fast 与 slow 撞车，先动的是 slow（它在 480 那一拍就被插到 600 这个位置，比 fast 早），t=1200 再撞一次顺序一样。⚠️ 这里的"入表"是**被插进链表的那一刻**，不是 `xTimerCreate` 的先后：自动重装一跑，两者的插入时刻就交错分了，创建顺序只在第一轮管用。

## 六、代码分析：场景 2/3/4 日志对照

- **场景 2（通知）**：生产端每 50ms give 一次，消费端 `ulTaskNotifyTake` 取走。把生产 delay 改小，`took` 的值就会变成 >1，计数语义把"欠的账"攒着；如果改成覆盖语义，多出来的就丢了。
- **场景 3（事件组）**：只发 bit0 时只有 `ANY woke`；bit0+bit1 都置上后 `ALL woke` 才出现，而且**两个等待者同时醒**：汇总清位的直接证据。
- **场景 4（定时器）**：`slow cb` 每次磨蹭 ~50ms，你会看到紧跟其后的 `fast cb` 迟到恰好 50ms，守护任务串行执行回调的直接证据。这一条正是上面 B 幕那档（Σ=0.416，占空比不满），所以迟到有界、等于耗时本身；把 `slow cb` 的耗时改到 200ms 就等于跨进 C 幕，`fast cb` 的迟到会超过 200ms 并开始连环补拍。

## 七、选型决策树：通知 / 队列 / 事件组

拿到一个"任务间通信"需求，按这个顺序问：

```
1. 是"一对一"还是"多对多"？
   ├─ 一对一 → 继续问 2
   └─ 多对多 → 队列（带数据）/ 事件组（只带信号）

2. 需要传数据还是只传信号？
   ├─ 只传信号 → 继续问 3
   └─ 要传数据 → 队列（数据 > 32 位）/ 通知（数据 ≤ 32 位，覆盖语义）

3. 需要攒"欠账"还是只关心最新值？
   ├─ 攒欠账 → xTaskNotifyGive（计数语义）
   └─ 只关心最新 → xTaskNotify（覆盖语义）

4. 需要等"几个条件都齐"？
   └─ 是 → 事件组（ANY/ALL）
```

**经验法则**：中断 → 单任务同步，默认用通知；任务 → 任务传数据，默认用队列；多条件汇合（如"初始化完成 + 传感器就绪 + 网络连上"），用事件组。

## 八、软件定时器 vs 任务内 vTaskDelay

两者都能做周期任务，选型看三点：

| 维度 | 软件定时器 | 任务 + vTaskDelay |
|---|---|---|
| RAM 开销 | **固定 1312 B**（一个定时器都没建就要付）+ 每个定时器 56 B | 每个任务 616 B（栈 128 字 + TCB） |
| 回调里能阻塞吗 | **不能**（堵守护任务） | 能（只堵自己） |
| 时间精度 | 受守护任务队列负载影响 | 只受调度器影响 |
| 适合 | 周期杂务（LED 闪、看门狗喂） | 需要独立逻辑、可能阻塞的任务 |

**反模式**：在软件定时器回调里做 I2C 读取，I2C 超时阻塞会拖垮所有定时器。正确做法是回调里发通知，由专门的任务做 I2C。

### 那句"RAM 开销：零"，两个方向都不成立

网上讲软定时器几乎都有一行"RAM 开销：零（共用守护任务）"。这台机器上量的结果（`sh probe.sh` 第 6 步，heap_4 + CM4F + V11.1.0，配置就是本工程的 `code/rtos/01-freertos-lab`）：

```
守护任务 TCB   ：pvPortMalloc(88)              → 实付 96 B
守护任务栈     ：pvPortMallocStack(256×4=1024) → 实付 1032 B
命令队列       ：pvPortMalloc(80+8×12=176) → 实付 184 B
── 固定那笔合计：1312 B（一个定时器都没建就要付）
── 每建一个定时器：56 B ｜ 每开一个最小任务：616 B（栈 128 字）
── 固定那笔占 configTOTAL_HEAP_SIZE 的千分比：80‰，也就是 8.0%
```

三个数都是量出来的，不是抄的：`sizeof(Timer_t)=44`、`sizeof(Queue_t)=80`、`sizeof(TCB_t)=88`、`sizeof(DaemonTaskMessage_t)=12` 由 `nm --print-size` 从目标文件里读，队列那笔的长度 8、消息 12、栈深 256 字由编译器报出来；`实付` 那一步是 heap_4 每笔 malloc 收的抽头，`heap_4.c:187` 加 `xHeapStructSize`、`:198` 补对齐，`(8 + 8 - 1) & ~(8 - 1) = 8 B`。

方向一：`configUSE_TIMERS=1` 一开，1312 B 就没了，跟定时器个数无关。

方向二：还有 **60 B 落在 `.bss`**，`configTOTAL_HEAP_SIZE` 调多大都管不到它，因为它根本不在这笔账的池子里。这 60 B 是从源码数出项数再乘实测宽度预测的（两条到期表 `List_t×2` + 4 个指针 + `xLastTime`），`= 20×2 + 4×4 + 4×1 = 60 B`，跟 `nm` 打出的实际值对上了才对上。

那"共用守护任务所以便宜"这句到底对多少？拿比价基准看：**一个最小任务 616 B，等于 11 个定时器的名额**；反过来，**固定那笔 = 2.12 个最小任务的名额**（`1312 ÷ 616` 向下取整，精确值 2.129），为了能用定时器，你先付了两个任务的价钱。所以省的是每个定时器自己那 616 B 的栈与 TCB，1312 B 那笔一分不省，只用一两个定时器时最不划算。

换档配置账怎么动（同一个公式换实测输入）：

| 档位 | 固定那笔 | 每定时器 | 相对 lab |
|---|---|---|---|
| lab 默认 | 1312 B | 56 B | +0 |
| `configUSE_TRACE_FACILITY=0` | 1296 B | 48 B | −16 |
| `INCLUDE_xTimerPendFunctionCall=1` | 1344 B | 56 B | +32 |
| `configTIMER_QUEUE_LENGTH` 8→16 | 1408 B | 56 B | +96 |

`+32` 恰好是"队列长度 × 消息增重"（8 × 4），`+96` 恰好是"长度增量 × 消息大小"（8 × 12），涨幅能被公式复现，说明这笔账里没有魔法数。整池 16 KiB 若只塞定时器，`(16384 − 1312) ÷ 56 = 269` 个：那是上界，不是预算，真实工程里这笔钱还要给任务和栈。

## 九、GDB 调试通知与事件组

通知和事件组的状态都在 TCB 里，GDB 可以直接看：

```bash
# 查看任务的通知值（计数语义）
(gdb) p pxCurrentTCB->ulNotifiedValue[0]
$1 = 3    # 欠了 3 次没取

# 查看通知状态
(gdb) p pxCurrentTCB->ucNotifyState[0]
$2 = 1 '\001'    # 1 = 已通知待取

# 查看事件组位
(gdb) p xEventGroup->uxEventBits
$3 = 5    # bit0 + bit2 置位

# 在通知到达时打断点
(gdb) break xTaskNotifyGive
(gdb) commands 1
> p xTaskToNotify->pcTaskName
> continue
> end
```

**调试纪律**：通知是"瞬时状态"，GDB 暂停时看到的值可能已经被消费。用 `watch` 命令抓变化比 `break` 更精准：

```bash
# 通知值变化时自动暂停
(gdb) watch pxCurrentTCB->ulNotifiedValue[0]
```

## 附录：工程完整源码

<<< ../../../code/rtos/01-freertos-lab/main.c

## 记忆锚点

::: tip 一句话记住
**通知写 TCB 一步到位，事件组是位公告栏，软定时器住守护任务——回调里只办事，不等待；清位是汇总清，不是先醒者独占。**
:::

**延伸**：硬件 TIM（[S6](../../stm32/06-tim.md)）管外设时基，软件定时器管周期任务，分工不同；任务通知可替代队列用于 1:1 数据传递（[F4](04-queue.md)），更轻量。

## 实物实验

- **不用板子也能把本章每一个数字打出来**：`cd code/rtos/06-timers && sh probe.sh`。七步一条命令跑完，用 `nm --print-size` 量出 `Timer_t 44 / ListItem_t 20 / DaemonTaskMessage_t 12 / Queue_t 80 / TCB_t 88`，再拿机身里那句 `movs r0, #44` 和静态版 `StaticTimer_t` 作为第二、三条独立路子对上同一个 44；从 `xQueueGenericCreate` 调用点读队列的 `(8, 12)`（不写进脚本，写了就不叫实测）；把 heap_4 的抽头算进去，逐笔打出 96 / 1032 / 184 → 固定 **1312 B**、每定时器 **56 B**、每最小任务 **616 B**；按源码数出的项数预测 `.bss` 那 **60 B** 再跟 nm 对上；最后跑一遍把七条分派规则抄成的宿主机模拟器，打出五幕的迟到/补拍/连发/欠账（§五）。每条规则都由 `at_line` 钉住上游行号，内核一升级行号漂了这一步直接变红，而不是悄悄给一个错的数。需要交叉工具链与 V11.1.0 内核（CI 的 arm-host 作业两样都装）。
- 场景 2：把生产端 delay 从 50ms 改到 10ms，看 `took` 的值涨上去；
- 场景 3：给 ANY 等待者加 `xClearOnExit=pdFALSE`，再发一次 bit0，这次 ALL 也能等到；
- 场景 4：把 `slow cb` 的磨蹭时间从 50ms 改到 200ms，这一步正好跨过 Σ(耗时 ÷ 周期) = 1 那条线（50ms 时 0.416，200ms 时 1.666）。**别数"丢了几拍"**：模拟实测拍没丢，`owed` 那栏欠着、`catchup` 连环补拍，`fast cb` 的最大迟到从恰好 50 涨到 520。无板复现同一张表：`cd code/rtos/06-timers && sh probe.sh` 第 7 步。

## 常见坑

- **通知当通用队列用**：槽位数 = `configTASK_NOTIFICATION_ARRAY_ENTRIES`（本工程=1），多对多还是队列；
- **记错函数名**：是 `ulTaskNotifyTake`，不是 `xTaskNotifyTake`；
- **覆盖丢事件**：高频通知未消费就被覆盖，要攒"欠账"用 `xTaskNotifyGive`（eIncrement）；
- **事件组 xClearOnExit 误用**：想让"下一批"也看到这些位就别开自动清；
- **软定时器回调里 vTaskDelay**：守护任务一堵，所有定时器集体迟到。
- **把"晚一拍"当成结论**：它是现象，不是判据。判据是 Σ(回调耗时 ÷ 周期) 有没有过 1：没过，零耗时定时器的最大迟到恰好等于最大那次耗时（有界）；过了，迟到超出耗时本身并连环补拍（发散）。看日志数"晚了几拍"永远看不出这条线，模拟器一次就量到。
- **把定时器当零成本**：`configUSE_TIMERS=1` 一开就固定付 1312 B，另有 60 B 在 `.bss` 里不受 `configTOTAL_HEAP_SIZE` 管（§八）。只用一两个定时器时，这笔钱比开任务还贵：固定那笔 = 2.12 个最小任务。
- **"入表顺序"当成 `xTimerCreate` 的先后**：同一刻到期谁先跑，由链表插入时 `list.c:192` 那个 `<=` 决定，是"插入那一刻的先后"，不是创建顺序，也不是 ID 大小。

## 短自测

1. 任务通知的"计数语义"和"覆盖语义"分别对应哪个 API？
<details><summary>参考答案</summary>计数语义是 xTaskNotifyGive（eIncrement，通知值 +1）；覆盖语义是 xTaskNotify 的 eSetValueWithOverwrite（直接盖掉旧值）。欠账要攒就用前者，只关心最新值就用后者。</details>

2. 事件组里两个任务都在等同一组位，一个等 ANY、一个等 ALL，发 SetBits 把位全置上后，谁会醒？位什么时候清？
<details><summary>参考答案</summary>两个都醒。SetBits 把整个等待列表走完、所有满足条件的都唤醒，然后按 uxBitsToClear 汇总清一次（event_groups.c:547 起）。不存在"先醒者独占"。</details>

3. 软件定时器的回调里为什么不能 vTaskDelay？
<details><summary>参考答案</summary>回调跑在守护任务里，守护任务是所有定时器共用的执行线程。回调阻塞 = 守护任务阻塞 = 所有定时器集体停摆。回调必须快进快出。</details>

4. 为什么"通知比队列快 45%"不能当无条件结论引用？
<details><summary>参考答案</summary>那是官方文档在某个版本、某个配置下的实测数字。通知快的根源是无队列对象、无拷贝、无额外链表项；具体快多少取决于你的队列深度、是否从中断上下文、调度器当时的状态。引用时必须带版本与配置条件。</details>

5. `configUSE_TIMERS=1`、一个定时器都没建，堆已经被吃掉多少？另有几字节不在堆里？
<details><summary>参考答案</summary>固定 1312 B：守护任务 TCB 实付 96 + 守护任务栈（256 字 × 4）实付 1032 = 1128，命令队列 pvPortMalloc(80 + 8×12 = 176) 实付 184。另有 60 B 落在 .bss（两条到期表 List_t×2 + 4 个指针 + xLastTime），configTOTAL_HEAP_SIZE 调多大都管不到它。每建一个定时器再收 56 B，一个最小任务是 616 B。</details>

6. 一个 100ms 的零耗时定时器，被一个耗时 200ms 的 120ms 定时器压着，它的最大迟到是 200ms 吗？
<details><summary>参考答案</summary>不是，实测 520 拍（毫秒）。Σ(耗时÷周期) = 200/120 = 1.666 ≥ 1，迟到跳出耗时本身并发散，且出现连环补拍（catchup 6 次、连发 6）。把耗时降到 50ms（Σ=0.416 < 1），最大迟到才恰好等于那次耗时 50；耗时 200ms 但周期 300ms（Σ=0.666 < 1），最大迟到又回到恰好 200，有界条件是那个和小于 1，不是单次耗时小于某个数。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| give/take/notify API | 上游 V11.1.0 `task.h:2984/3177/2611` → `tasks.c:7832/7717` |
| 事件组汇总清位 | 上游 V11.1.0 `event_groups.c:547`（xEventGroupSetBits） |
| 守护任务 | 上游 V11.1.0 `timers.c`（prvTimerTask） |
| 定时器 RAM 账 + 分派规则实测 | [code/rtos/06-timers](https://github.com/zhuguang-ZFG/STM32/tree/main/mcu/code/rtos/06-timers) `sh probe.sh`（第 6 步总账、第 7 步五幕模拟，无需开发板） |
| 场景实验 | [code/rtos/01-freertos-lab](https://github.com/zhuguang-ZFG/STM32/tree/main/mcu/code/rtos/01-freertos-lab) 场景 2/3/4 |
| 动画 | [task-notification.svg](/anim/task-notification.svg)、[event-group-wait.svg](/anim/event-group-wait.svg)、[software-timer-service.svg](/anim/software-timer-service.svg) |

## 你做到了

- 通信工具箱从"队列打天下"升级为按场景选型；
- 事件组的"汇总清位"不再是玄学；
- 软定时器接管周期性杂务，任务数开始下降。

首付交了 1312 B，每建一个定时器再收 56 B：守护任务串行跑所有回调，回调小而快、禁止阻塞，是这条通道的纪律。

<div class="achievement">
✅ 下一站：<a href="07-heap.html">F7 内存管理</a>：heap_1~heap_5 五种人生，栈水位与堆碎片实测。
</div>