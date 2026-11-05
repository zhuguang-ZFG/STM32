# F3《调度器：一条 clz 选人，背后还有三笔账》事实底稿

本文件是 `video/episodes/f3-scheduler/episode.json` 的上屏/口播数字对账底稿。所有“实测”输出都从**本次**运行
`.temp/v2-facts/03-scheduler-probe.log`（373 行）原样摘出；旧稿与 `docs/rtos/freertos/03-scheduler.md`
只在「叙述前提」与「例外」两处出现，并逐条标明，不冒充本次读数。

## 1. 取证信息

| 项 | 值 |
|---|---|
| 源文档 | `docs/rtos/freertos/03-scheduler.md` |
| 取证脚本 | `code/rtos/03-scheduler/probe.sh`（交叉编译三份配置、`objdump -d` 截选优/插入/tick 机身、宿主程序跑两条规则的模拟器） |
| 本次日志 | `.temp/v2-facts/03-scheduler-probe.log`（`wc -l` = 373 行） |
| 内核 | FreeRTOS-Kernel `V11.1.0`（日志 L2，`tasks.c:56`） |
| 交叉工具链 | `15.2.1`（日志 L2） |
| 宿主工具链 | 日志**没有打印版本号**；只说“宿主编译器跑模拟器”，不写 `gcc x.y.z` |
| 配置实测 | 不写 / 写 1 / 写 0 三份 `tasks.o`；`opt=140 omit=140 gen=160`（L27–L29） |
| 反汇编 | 位图路 L32–L42、通用路 L43–L53；`uint8_t` 与 -O2 L65–L82；下标算术 L144–L186；tick L203–L258；链表 L260–L371 |
| 模拟器 | L84–L109：23 个事件、10 次选择，n=5 与 n=32 两轮 |
| 板级输出 | 本集不需要开发板；日志没有 LED、串口、示波器或周期计数 |
| 数字审计 | `npm run video:numbers -- f3-scheduler` → `62 个数字都有依据`（§7） |

本次日志的全部“实测”只有四件事：三次配置编译的字节对照（L27–L29）、两个优化档的机身大小（L82）、
23 个事件的模拟器计数（L84–L109）、以及链接符号表里的数组大小（L112–L114）。其余技术叙述若来自
源码阅读或指令语义，在 §5 单列，不冒充 probe 读数。

## 2. 本集必须回答的 6 个问题

1. **谁决定走位图路还是通用路？** 预处理，不是运行时。`tasks.c:159` 的
   `#if ( configUSE_PORT_OPTIMISED_TASK_SELECTION == 0 )` 把两份实现隔开（L7）；同一文件
   `3903`–`3924` 还有内层分岔（L8–L9）。端口层先给默认值 1（`portmacro.h:144–146`，L11–L13），
   通用层后给默认值 0（`FreeRTOS.h:2766–2768`，L16–L18）。`FreeRTOS.h:64` 先包含
   `FreeRTOSConfig.h`，`:107` 才包含 `portable.h`（L20–L21），所以 CM4F 端口上不写就是 1：
   不写与写 1 的 `tasks.o` 逐字节相同，选优函数都是 140 字节；写 0 是 160 字节（L27–L29）。
   “默认 0”是通用层的兜底，不是 CM4F 的实际结果。

2. **一条 `clz` 加一次 `rsb #31` 怎样选出最高优先级？`uxtb` 为什么在 -O2 还在？**
   `portGET_HIGHEST_PRIORITY` 先 `clz` 数出位图前导零，再用 `31 − clz` 得到最高置位的编号
   （L34–L38）。`ucPortCountLeadingZeros` 返回 `uint8_t`（L66），-O0 机身先 `strb` 再 `ldrb`
   （L36–L37）；-O2 把这对字节往返压成寄存器里的 `uxtb`，但 `clz`、`uxtb`、`rsb` 三件都在
   （L74–L77）。函数从 140 字节缩到 92 字节（L82），类型转换没有消失。

3. **通用路怎样扫，代价是多少？** 从 `uxTopReadyPriority` 这个缓存层号开始，链表空就减一，
   直到非空，再把层号存回（L43–L53）。同一张事件表、10 次选择：n=5 时累计判空 21 次、平均
   2.10、最坏 5 次（第 4 次选择，L85–L90）；n=32 时累计 51 次、平均 5.10、最坏 31 次
   （第 9 次选择，缓存停在 30，真实最高位 0，L92–L97）。位图路两轮都是 10 次 `clz`、平均 1.00
   （L88、L95），且两条路每次选出的优先级分歧为 0（L100–L102）。

4. **为什么 32 位是位图路的硬天花板？通用路为什么不撞墙？** 33 级时通用路照编，
   `pxReadyTasksLists` 涨到 660 字节（L113、L190）；位图路被 `portmacro.h:162:10` 的 `#error`
   当场拒绝（L196、L199），并**没有留下目标文件**（L197）。这条 `#error` 在端口头文件里，
   不在 `tasks.c` 里（L200）。通用路用空间换：每级一条 `List_t`，20 字节，5 级 100 字节、
   33 级 660 字节（L112–L114），所以它不为 32 位所困，但每加一级都要付 20 字节。

5. **tick 干哪三件事，源码顺序如何？调度器挂起时 `xPendedTicks` 怎样？**
   先拍号加一（`tasks.c:4699`，L205）；再比较 `xConstTickCount >= xNextTaskUnblockTime`
   （`tasks.c:4714`，L209），追上了才进醒人循环（`4737`），最后请求切换（`4789`，L216、L225；
   另两处在 `4816`、`4865`，L226–L227）。机身里那次比较是函数第 39 条指令，整个函数 237 条
   （L215）；剪枝现场是 `4e ldr / 50 cmp / 52 bcc.w 1a6`（L210–L212）。调度器挂起时，
   `xTaskIncrementTick` 走 else 分支，只执行 `xPendedTicks += 1U;`（内核 `tasks.c:4907`）并返回，
   拍号不前进、也不选人；恢复调度时 `xTaskResumeAll` 按 `xPendedTicks` 的次数补跑
   `xTaskIncrementTick`，欠下的拍一次补齐。**注意**：probe 日志 L242 抓到的
   `tasks.c:4527: xPendedTicks++;` 属于 `vTaskStepTick`，不是 `xTaskIncrementTick`；本集上屏改用
   4907，日志行只作为“同名 token 在 tasks.c 内存在”的旁证。

6. **延时链表为什么只查队首？** 插入按 `xItemValue` 升序（`list.c:192` 的循环，L365），队首就是
   最早该醒的节点；队首没到点，后面全没到点，tick 的比较可以一跳而过。代价付在插入：
   `vListInsertEnd` 35 条指令、0 条后向边（O(1)，L357）；`vListInsert` 55 条、1 条后向边
   （O(n)，L358、L361）。一个管轮转，一个管守时。

## 3. 上屏数字逐项对账

> 场景写法：`B:` = bilibili，`D:` = douyin，`封面` = 主封面，`发行` = publish 文案。
> 全量 token 见 `f3-scheduler-numbers.json`（62 个）；下面按证据段合并，同一行日志的多个 token
> 共用一个证据行。

### 3.1 选路、默认值与配置实测（L2、L7–L29）

```text
交叉工具链：15.2.1；内核：56:#define tskKERNEL_VERSION_NUMBER "V11.1.0"
159:#if ( configUSE_PORT_OPTIMISED_TASK_SELECTION == 0 )
144:#ifndef configUSE_PORT_OPTIMISED_TASK_SELECTION
145-    #define configUSE_PORT_OPTIMISED_TASK_SELECTION    1
2766:#ifndef configUSE_PORT_OPTIMISED_TASK_SELECTION
2767-    #define configUSE_PORT_OPTIMISED_TASK_SELECTION    0
64:#include "FreeRTOSConfig.h"
107:#include "portable.h"
[中] 不写 = 写 1：两份 tasks.o 逐字节相同
[中] 写 0 是另一份机身：opt 与 gen 不同
三者的 .text.vTaskSwitchContext 大小：opt=140 omit=140 gen=160 字节
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `15.2.1` | L2 `交叉工具链：15.2.1` | B: cta；D: cta；发行（B站/知乎） |
| `1.0` | L2 版本号 `V11.1.0` 经分词器取 `.1.0`；不是一个独立测量 | B: cta；D: cta；发行（B站/知乎） |
| `159` | L7 `159:#if ...` | B: fork-01 |
| `144` | L11 `144:#ifndef ...` | B: fork-02 |
| `2766` | L16 `2766:#ifndef ...` | B: fork-02 |
| `140` | L29 `opt=140 omit=140`；L82 `-O0 140 字节` | B/D: fork-03；发行（B站/知乎） |
| `160` | L29 `gen=160 字节` | B/D: fork-03；发行（B站/知乎） |
| `162` | L196 `portmacro.h:162:10: error: #error`；L199 同 | B: cap-01、cap-02；D: cap-01；发行（四平台） |

注：`FreeRTOS.h` 的 `64` 与 `107` 在旁白里读作“第六十四行”“第一百零七行”，不是数字 token；
日志 L20–L21 给出原文。`1`（写 1）同时出现在 L12、L29、L196，是同一个配置取值。

### 3.2 两副机身与 `uint8_t` 的疤（L32–L82）

```text
位图路：
  22: ldr r3, [r7, #4]
  24: clz r3, r3
  28: strb r3, [r7, #3]
  2a: ldrb r3, [r7, #3]
  2c: rsb r3, r3, #31
通用路：
  30: lsls r3, r3, #2
  32: add r3, r2
  34: lsls r3, r3, #2
  36: add r3, r1
  38: ldr r3, [r3, #0]
  3a: cmp r3, #0
  3c: beq.n 24 <vTaskSwitchContext+0x24>
位图路 vTaskSwitchContext：58 条指令，后向跳转 0 条
通用路 vTaskSwitchContext：70 条指令，后向跳转 1 条
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `22` / `24` / `2a` / `2c` | L34–L38 位图路机身地址与指令 | B: body-03 |
| `0x24` | L53 `3c: beq.n 24 <vTaskSwitchContext+0x24>`；L63 再列 | B: body-03 |
| `30` / `32` / `34` / `36` | L47–L50 通用路下标算术；也是 L145–L148 的同一形状 | B: body-03、ram-03 |
| `3a` | L52 `3a: cmp r3, #0` | B: body-03 |
| `58` / `70` / `0` / `1` | L55–L56 指令数与后向跳转数 | B/D: body-04 |
| `151` | L66 `151: ... uint8_t ucPortCountLeadingZeros ...` | B: body-05 |
| `16` / `1a` / `1e` | L74–L77 -O2 的 `clz`/`uxtb`/`rsb` 地址 | B: body-07 |

注：`58` 与 `70` 是**整个 `vTaskSwitchContext`** 的指令数，不是选优片段；`0` 与 `1` 是后向跳转
条数，不是优先级。`0x24` 是回边目标，`24` 也是 `clz` 所在地址，但两者语义不同，台词分别说
“往回跳的边”和“clz 那一条”。日志 L82 的 `-O2 92 字节` 在旁白里读作“九十二”，不是数字 token，
所以 numbers JSON 没有 `92` 这一项。

### 3.3 模拟器：23 个事件、10 次选择（L84–L109）

```text
### 场景二：同一张事件表跑完（configMAX_PRIORITIES = 5）
  事件 23 个，其中选择 10 次；两条路选出不同优先级的次数 = 0
  通用路累计判空 21 次，平均每次选择 2.10 次
  位图路累计 clz 10 次，平均 1.00 次
  通用路最坏那一次是第 4 次选择：缓存停在 4，真实最高位是 0，判空 5 次；

### 场景二：同一张事件表跑完（configMAX_PRIORITIES = 32）
  事件 23 个，其中选择 10 次；两条路选出不同优先级的次数 = 0
  通用路累计判空 51 次，平均每次选择 5.10 次
  位图路累计 clz 10 次，平均 1.00 次
  通用路最坏那一次是第 9 次选择：缓存停在 30，真实最高位是 0，判空 31 次；
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `23` / `10` / `0` | L86、L93：事件 23 个、选择 10 次、分歧 0 | B/D: scan-02、scan-03 |
| `21` / `2.10` / `5` / `4` | L87、L89：n=5 的累计、平均、最坏与选择序号 | B/D: scan-02；发行（四平台） |
| `51` / `5.10` / `30` / `9` | L94、L96：n=32 的累计、平均、缓存值与选择序号 | B/D: scan-03、scan-04；发行（B站/知乎） |
| `31` | L96 `判空 31 次` | B/D: scan-03、scan-04；封面；发行（四平台） |
| `1.00` | L88、L95、L105、L108：位图路平均 `10/10` | B/D: scan-02、scan-03；旁白读作“一点零零” |
| `32` | L92 `configMAX_PRIORITIES = 32` | B: hook-01、scan-03、scan-04、cap-01、cap-03、punch；D: hook-01、scan-03、scan-04、cap-01、punch；封面；发行（四平台） |

注：`2.10` 与 `5.10` 是同一张 23 事件表在 5 级/32 级下的**每次选择平均判空次数**，不是 CPU 周期，
也不是所有工作负载的期望值。`1.00` 是 10 次 `clz` 除以 10 次选择；不是因为“位图路每次一定只花
1 个周期”。`0` 分歧是模拟器一致性门禁，不是硬件实测。

### 3.4 RAM 账：每级 20 字节（L111–L143）

```text
configMAX_PRIORITIES=5  → .bss.pxReadyTasksLists = 100 字节；uxTopReadyPriority = 4 字节
configMAX_PRIORITIES=33 → .bss.pxReadyTasksLists = 660 字节；uxTopReadyPriority = 4 字节
sizeof(List_t) = (660 − 100) ÷ (33 − 5) = 20 字节
= uxNumberOfItems 4 + pxIndex 4 + xListEnd(MiniListItem_t) 12 = 20
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `100` / `660` | L112–L113 两次数组大小 | B/D: ram-01、cap-01；发行（B站/知乎） |
| `33` | L113 `configMAX_PRIORITIES=33`；L190 `gen33` | B/D: ram-01、cap-01、punch；发行（四平台） |
| `5` | L112 `configMAX_PRIORITIES=5`；L85 模拟器场景 | B/D: scan-02、scan-03、ram-01；发行（四平台） |
| `20` | L114 除法；L142 组成；L145 下标算术 | B: ram-01、ram-02、ram-03；D: ram-01；发行（B站/知乎/小红书） |
| `12` | L142 `xListEnd(MiniListItem_t) 12` | B: ram-02 |
| `4` | L112/L113 `uxTopReadyPriority = 4 字节`；L142 两个 4 字节成员 | B: ram-04；旁白读“四字节” |
| `256` / `8` | L201 `RT-Thread ...（32×8 = 256 级）` | B: cap-03 |

注：`20` 字节是 `List_t` 的完整宽度（含 12 字节哨兵），不是“每个任务节点 20 字节”；
`uxTopReadyPriority` 两边都只占 4 字节（L112–L113、L143）。`256 = 32×8` 是 RT-Thread 的两级位图
尺寸，日志只给这一行注释，没有 RT-Thread 的机器码或运行读数。

### 3.5 32 位天花板：33 级被谁拦下（L188–L201）

```text
gen33/tasks.o 编出来了，pxReadyTasksLists = 660 字节
portmacro.h:162:10: error: #error configUSE_PORT_OPTIMISED_TASK_SELECTION
can only be set to 1 when configMAX_PRIORITIES is less than or equal to 32.
[中] 被拒的那一次没有留下目标文件
注意这条 #error 在【端口头文件】里，不在 tasks.c 里；
同一条约束在 RT-Thread 那边是两套位图（32×8 = 256 级）
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `33` | L113 `configMAX_PRIORITIES=33`；L190 `gen33/tasks.o` | B/D: ram-01、cap-01、punch；发行（四平台） |
| `660` | L113、L190 | B: ram-01、cap-01；D: ram-01、cap-01；发行（B站/知乎） |
| `162` | L196、L199 | B: cap-01、cap-02；D: cap-01；发行（四平台） |
| `32` | L196 `less than or equal to 32`；L201 `32×8` | 见 §3.3；cap-01/cap-03 也用 |
| `256` / `8` | L201 | B: cap-03 |

注：`#error` 原文里的 `10 to 15 difference priorities` 是编译器作者的建议，不是本次测量；
旁白与画面都没有引用这组数。`被拒` 的直接证据是 L197 的断言“没有留下目标文件”和 L190 的
`gen33/tasks.o` 对照，不是靠报错文本推断。

### 3.6 tick 三件事与挂起记账（L203–L258）

```text
凭据(节拍++) tasks.c:4699:        xTickCount = xConstTickCount;
凭据(剪枝) tasks.c:4714:        if( xConstTickCount >= xNextTaskUnblockTime )
剪枝现场：  4e: ldr r2, [r7, #24]
剪枝现场：  50: cmp r2, r3
剪枝现场：  52: bcc.w 1a6 <xTaskIncrementTick+0x1a6>
那次寄存器间比较是函数第 39 条指令，整个 xTaskIncrementTick 在 -O0 机身上共 237 条。
源码顺序：剪枝 4714 行 → 醒人循环 4737 行 → 请求切换 4789 行。
凭据(请求切换) tasks.c:4789 / 4816 / 4865: xSwitchRequired = pdTRUE;
凭据(暂停期记账) tasks.c:4527: xPendedTicks++;
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `4699` | L205 | B: tick-02 |
| `4714` | L209、L216 | B: tick-02 |
| `4737` | L216 | B: tick-02 |
| `4789` / `4816` / `4865` | L225–L227 | B: tick-02 |
| `39` / `237` | L215 | B: tick-03 |
| `50` / `52` / `0x1a6` | L211–L212 | B: tick-03 |
| `24` | L210 `[r7, #24]` 的栈偏移 | B: tick-03 |
| `4907` | 内核 `tasks.c:4907`；日志 L242 的 4527 属 `vTaskStepTick`，只作旁证 | B: vdelay-03 |

注：L242 抓到的 `4527` 不是 `xTaskIncrementTick` 的挂起分支。v2 上屏写 4907，并在旁白里只说
“只把 xPendedTicks 加一返回”；`xTaskResumeAll` 的补跑循环来自内核源码阅读，不是本次日志逐行。
v1 说“拍号照加”是错的：挂起分支不推进 `xTickCount`，只累计 `xPendedTicks`。

### 3.7 链表两兄弟（L260–L371）

```text
vListInsertEnd：35 条指令，后向跳转 0 条
vListInsert   ：55 条指令，后向跳转 1 条
后向边：  38: bcs.n 28 <vListInsert+0x28>
192:        for( pxIterator = ...; pxIterator->pxNext->xItemValue <= xValueOfInsertion; ... )
```

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `35` / `0` | L357 | B: tick-06 |
| `55` / `1` | L358 | B: tick-06 |
| `0x28` / `28` / `38` | L361 | B: tick-06 |

注：`35` 与 `55` 是整个函数的指令数，不是“插一次要 35/55 个周期”。`O(1)` / `O(n)` 是复杂度
标签，不是本次计时；`0` 条 / `1` 条后向边是机身里数出来的控制流事实。

### 3.8 封面与发行文案

封面 `line2` / `vs.left` / `vs.right` / `num` / `numNote` / `proof` / `proofShort` 只用了 `31`、`10`、
`1`、`32`，均在 §3.3–§3.5 有日志行。两侧都是实测：通用路 n=32 最坏 31 次判空，位图路
10 次选择 10 次 `clz`，所以 `vs.labels` 写 `["MEASURED","MEASURED"]`，不把任何一侧标成 EXPECTED。
`num` 取 `31 次`，是“最坏一次选择的判空次数”，不是平均值。

发行文案（B站/抖音/知乎/小红书）里的 `140`、`160`、`21`、`2.10`、`51`、`5.10`、`31`、`100`、`660`、
`20`、`33`、`32`、`162`、`15.2.1`、`1.0` 同样落在上述证据行；`03` 是复现路径
`code/rtos/03-scheduler` 的章节号，进 `exceptions`。发行文案没有出现周期数、板级读数、
`10 to 15` 建议、RT-Thread 的两次 `clz` 实现细节。

## 4. 不能删的技术断言（删了会让章节断链）

1. **分岔是预处理，不是运行时判断**：`tasks.c:159` 的 `#if` 把两份实现隔开（L7）；同一文件
   3903–3924 还有内层分岔（L8–L9）。删掉这条，后面“两条机身”没有来源。
2. **端口默认 1 先落地，通用层默认 0 后到**：`portmacro.h:144–146`（L11–L13）先于
   `FreeRTOS.h:2766–2768`（L16–L18），因为 `FreeRTOS.h:107` 才包含 `portable.h`（L21）。
   删掉这条，“不写 = 1”会被误解成文档约定。
3. **不写与写 1 逐字节相同**：两份 `tasks.o` 相同、选优函数 140 对 140；写 0 是 160（L27–L29）。
   删掉这条，“默认值之争”只剩口头结论。
4. **位图一位一级，选优是 `31 − clz`**：`portGET_HIGHEST_PRIORITY` 的 `rsb #31`（L38、L58）；
   `clz` 是端口内联汇编（L66–L70）。删掉这条，封面上的“一条 clz”没有落点。
5. **`uint8_t` 的截断在 -O2 仍活着**：-O0 是 `strb`/`ldrb`（L36–L37），-O2 是 `uxtb`（L75），
   函数从 140 缩到 92 字节（L82）。删掉这条，“clz 一条指令”会变成“没有任何代价”。
6. **通用路有回边，位图路没有**：58 条 0 回边对 70 条 1 回边（L55–L56、L63）。删掉这条，
   “定长 vs 随层数变长”没有机身证据。
7. **32 位天花板画在端口头文件**：`portmacro.h:162:10` 的 `#error`（L196、L199），不在
   `tasks.c`（L200）；33 级位图路没有目标文件（L197），通用路 660 字节照编（L190）。删掉这条，
   观众会以为上限是内核或编译器给的。
8. **tick 三件事的顺序**：4699 → 4714/4737 → 4789（L205、L209、L216、L225）；剪枝比较是第 39 条，
   全函数 237 条（L215）。删掉这条，“tick 只做三件事”没有源码顺序。
9. **挂起时只记账，不推进拍号**：`xPendedTicks += 1U`（内核 4907），恢复时补跑。
   删掉这条，会把“挂起”误讲成“停表”或“照常加拍”。
10. **延时链表按值有序，所以只查队首**：`list.c:192` 的插入循环（L365）；`vListInsert` 55 条 1 回边，
    `vListInsertEnd` 35 条 0 回边（L357–L358）。删掉这条，“只查队首”变成无根据的优化。

## 5. 已知未取证项（明确“不上屏”或只作叙述前提）

| 项 | 状态 | 处理 |
|---|---|---|
| 宿主 `gcc` 版本 | 日志只写“宿主编译器跑模拟器”，没有版本号 | cta 不写版本号；只写交叉工具链 15.2.1 |
| CPU 周期 / 执行时间 | 日志没有周期计数、没有计时 | 只说指令条数与判空次数；不写“快多少纳秒/周期” |
| 板级现象 | 本集不需要开发板，日志无板级输出 | 不上屏灯态、串口波形、示波器读数 |
| 模拟器结论的普适性 | 只有一张 23 事件、10 次选择的表 | 明说“同一张事件表”；不把 2.10/5.10 说成所有负载的期望 |
| `xPendedTicks` 补跑 | 日志只给 4527（属 `vTaskStepTick`）与函数序言分支 | 上屏用内核 4907；补跑循环来自源码阅读，不冒充日志逐行 |
| `configUSE_TICK_HOOK` | 挂起分支在自增后还会按该宏调用钩子；本集不讨论钩子 | 旁白只说“拍号不前进、不选人”，不把“只做一件事”扩成“函数体只有一行” |
| RT-Thread 的“两次 clz” | 日志只给 `32×8 = 256` 一行注释 | 只说两级位图尺寸；不编 RT-Thread 的机器码或运行读数 |
| `#error` 里的 `10 to 15` | 编译器建议，不是本集测量 | 不上屏、不进 numbers 证据 |
| `List_t` 的完整性检查字段 | 日志 L117 注明 `configUSE_LIST_DATA_INTEGRITY_CHECK_BYTES=0` | 明说本工程为 0；不把 20 字节说成所有配置的固定值 |
| `vTaskDelay` 的运行时轨迹 | 日志只给 2435/2457 等源码行，没有运行 trace | 只讲源码动作与链表语义；不编“挂起多久”的实测 |
| 封面“同一张就绪表” | 比喻，不是日志原文 | 作为封面文案；数字仍受 §3.1–§3.5 约束 |

## 6. 与旧稿的关系

v1 的 34 场已整体重写为 v2 的 34 场（6 节）；竖版 12 场 pick 保持 v1 的选择。旧稿的以下说法
**没有本次日志依据或与源码不符**，已删除或改写：

- v1 说调度器挂起时“tick 照常进来，拍号照加，只是不选人”。内核 `xTaskIncrementTick` 的 else
  分支只执行 `xPendedTicks += 1U;`，`xTickCount` 不前进；恢复时才由 `xTaskResumeAll` 补跑。
  v2 改成“只记账、拍号不前进，恢复时补跑”。
- v1 把 4527 当作 `xTaskIncrementTick` 的记账行；实际 4527 是 `vTaskStepTick` 的自增。
  v2 上屏改用 4907，并在 §5 标明日志行的旁证身份。
- v1 的“位图只有 32 位，那开 32 级以上会怎样”是设问句；v2 改成先给 33 级的两个编译结果，
  再解释拦截位置。
- v1 的“二十字节拆开来”只列成员；v2 补了 `4 + 4 + 12` 的算术与完整性检查为 0 的前提。
- v1 的“通用路径并不傻……平均只摸两三层”是定性描述；v2 用 n=5/n=32 的 2.10/5.10 与 5/31
  重新落地，并明确“平均是账面，最坏才是底线”。
- v1 的“位图路那一栏永远是一点零零——因为累计、平均、最坏三个数必然相等”是推理；v2 只报
  日志里的 10 次 `clz` / 平均 1.00，不把“必然相等”当测量。

逐句比对：v1 句子原样复用 **0 条**；按原始旁白重算，最长公共片段 20 字，是标识符
`uxTopReadyPriority`（技术名词，无法改写），其余最长片段 13 字，均为“二十三个事件、十次选择”
这类技术短语，不是整句。v2 没有“最快/最简单/一定”这类绝对化说法。

## 7. 审计回填

- `npm run video:lint -- f3-scheduler`：✅ 通过：bilibili 34 场，douyin 12 场。
- `npm run video:numbers -- f3-scheduler`：✅ f3-scheduler: 62 个数字都有依据。
- 旁白字数（实测，`narration.length` 口径）：bilibili 3392 字；douyin 255 字。
  去空白口径：bilibili 3323 字；douyin 242 字。两者都在 3000–3400 / 240–280 目标内。
- 节数：bilibili 6 节（片头/谁选的路/两副机身/跑一遍账/租子与天花板/tick 与链表）；
  douyin 5 节（片头/选路/两副机身/账本/收束）。
- 钩子：开头连续 `kind: "hook"` 只有 `hook-01` 一场（60 字）；hook-02 已是 `card`。按
  `spec.mjs` 的 0.1955 s/字估算约 11.7 s，低于 15 s。**未建片，未量实测语音时长**；
  正式建片仍需节拍审计确认。
- 抖音字幕：三行非空白字数 14 / 13 / 16，合计 43；首行 ≤20、次行 ≤24、总计 ≤62。
- 小红书：标题 14 字（≤20），正文 214 字（≤1000），合集“通往单片机之路”非空，
  置顶含 `sh code/rtos/03-scheduler/probe.sh`。
- 按 brief 要求未构建视频、未提交、未改其他文件。
