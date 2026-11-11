# F6《软件定时器的 RAM 账：一个都没建，已经付了 1312 字节》事实底稿

本文件是 `video/episodes/f6-timers/episode.json` 的上屏/口播数字对账底稿。所有“实测”都来自**本次**运行
`.temp/v2-facts/06-timers-probe.log`（295 行，EXIT 0）；旧稿与
`docs/rtos/freertos/06-notify-event-timer.md` 只在「叙述前提」与「例外」两处出现，并逐条标明，
不冒充本次读数。宿主模拟器的五幕是**模型值**，不是板级测量。

## 1. 取证信息

| 项 | 值 |
|---|---|
| 源文档 | `docs/rtos/freertos/06-notify-event-timer.md` §五 / §八 |
| 取证脚本 | `code/rtos/06-timers/probe.sh`（七步；宿主探针 + 交叉 `nm` / `objdump` + `sim_daemon.c`） |
| 本次日志 | `.temp/v2-facts/06-timers-probe.log`（295 行，EXIT 0） |
| 内核 | FreeRTOS `V11.1.0`（日志 L3，`tskKERNEL_VERSION_NUMBER`） |
| 交叉工具链 | `15.2.1`（日志 L2） |
| 宿主工具链 | `gcc 16.1.0`（日志 L2） |
| 目标 | Cortex-M4F（日志 L192 的回归护栏写明 `lab 配置 + CM4F + V11.1.0`；L172 指针宽度 4 字节） |
| 板级输出 | 无。本集不需要开发板，日志没有灯态、串口或示波器读数 |
| 模拟器 | `code/rtos/06-timers/sim_daemon.c`，宿主编译，事件表写死，同一二进制连跑两次逐字节相同（L243–L245） |
| 数字审计 | `npm run video:numbers -- f6-timers` → `86 个数字都有依据`（§7） |

本次日志的“实测”只有四类：编译器报出的配置与 `sizeof`（L10–L13、L77–L85）、交叉反汇编里的立即数
（L88、L129–L133、L161）、`.bss` 的段大小（L99、L202–L204）、以及宿主模拟器的五幕输出
（L248–L292）。配置宏的取值、内核源码的行为，是编译前提或源码事实，在 §5 单列，不冒充探针读数。

## 2. 本集必须回答的 6 个问题

1. 为什么“软件定时器 RAM 开销：零”在两个方向都不成立？——`card-01`、`code-12`、`punch`。
2. 精确的账本是什么：1312 固定 + 每个 56，以及与一个任务的比价？——`code-04`、`code-05`、
   `card-03`、`code-09`、`code-10`、`card-05`、`punch`。
3. 为什么所有回调必然串行？——`hook-02`、`cb-01`、`code-13`、`code-14`。
4. 回调什么时候开始落后？Σ(耗时 ÷ 周期) 的两侧各是什么形态？拍到底丢没丢？——
   `sim-A`、`sim-B`、`sim-E`、`sim-C`、`sim-D`、`punch-01`、`punch-02`。
5. 同一刻到期的回调，谁先跑？——`code-15`。
6. 哪些配置开关会改这笔账，哪两个开关不能随便组合？——`card-02`、`code-06`、`code-07`、
   `code-08`、`code-11`。

五个内容小节都以结论收尾：`code-01`（三条独立路子互证）、`code-08`（`#error` 是编译期强制）、
`code-12`（零成本在两个方向破产）、`code-14`（串行之后平局也要有秩序）、`cta`（先算账再决定用不用）。
`片头` 小节负责立题，不冒充结论。

## 3. 上屏数字逐项对账

> 场景写法：`B:` = bilibili，`D:` = douyin，`封面` = 主封面，`发行` = publish 文案。
> 同一行日志里的多个 token 共用一个证据行；每个 token 都列出它实际出现的场景。

### 3.1 工具链、版本、默认值与配置

| 上屏 token | 日志证据 | 场景 |
|---|---|---|
| `15.2.1` | L2 `交叉工具链：15.2.1` | B: cta；D: cta |
| `16.1.0` | L2 `宿主机 gcc：16.1.0` | B: cta；D: cta |
| `1.0` | L3 `V11.1.0` 被 `numbers.mjs` 拆出的 `1.0`；不是另一次测量 | B: code-01 |
| `284` | L110 `FreeRTOS.h:284: #define INCLUDE_xTimerPendFunctionCall 0` | B: code-06 |
| `2824` | L164 `FreeRTOS.h:2824:` 的 `#error` 原文 | B: code-08 |
| `10012` / `10616` | L114 `不写 10012 B，-DPEND=0 10012 B，-DPEND=1 10616 B` | B: code-06 |
| `2` | L117 开 PEND 多出的符号个数（= 2）；L202 `20×2` 里的乘数 2 | B: code-06、code-12；D: code-12 |
| `1` | L113 `-DPEND=1` 与不写不同；L128 全文只有 1 处 `xQueueGenericCreate`；L166 只报 1 条 `#error`；源码 `configUSE_TIMERS=1` | B: hook-01、code-02、card-02、code-03、code-06、code-07、code-08、code-11、code-12、punch-01、punch；D: hook-01、punch-01、punch |
| `0` | L110 `INCLUDE_xTimerPendFunctionCall` 默认 0；L112 不写与 `-DPEND=0` 逐字节相同；L249/L259–L261、L276–L277 幕 A 的 0；其余为源码字面量或模型零值 | B: card-01、card-02、code-06、code-08、code-09、code-11、sim-A、sim-B、sim-E、sim-C、sim-D、punch-01、punch-02；D: card-01、code-09、sim-B；发行：bilibili |
| `8` | L10 `configTIMER_QUEUE_LENGTH（= 8）`；L105 `sizeof(BlockLink_t)=8`；L129–L130 队列长度 8 | B: hook-01、code-03、code-07、code-05、code-11；D: hook-01；封面；发行：bilibili |
| `256` | L11 `configTIMER_TASK_STACK_DEPTH（单位是字）（= 256）`；L173 `256 字 = 1024 B` | B: hook-01、code-04；D: hook-01、code-04；封面；发行：bilibili |
| `128` | L12 `configMINIMAL_STACK_SIZE（单位是字）（= 128）`；L189 每最小任务 616 B | B: code-07、code-10 |

注：`configMAX_TASK_NAME_LEN + 1 = 13`（L13）没有上屏，不进 token 表。`configUSE_TIMERS = 1` 是
编译 `timers.c` 的前提，不是探针量出的尺寸；屏幕上是配置片段，旁白只说“屏上的尺寸由编译器报数”，
不把每个宏都称作实测。

### 3.2 对象尺寸与 TRACE 那一档（日志 L77–L90、L144–L162）

| 上屏 token | 日志证据 | 场景 |
|---|---|---|
| `44` | L77 `sizeof(Timer_t) 44 B`；L88 `xTimerCreate` 里 `pvPortMalloc` 的立即数 44；L179–L180 成员和 41 + 尾对齐 3 | B: code-01、code-02、card-02、code-09；D: code-09 |
| `40` | L149/L154 `TRACE=1 44 / TRACE=0 40`；L157 `StaticTimer_t` 同为 40；L161 反汇编立即数 40 | B: card-02、code-09；D: code-09、code-12 |
| `20` | L80–L81 `sizeof(List_t)=20`、`sizeof(ListItem_t)=20`；L159 TRACE=0 不影响链表 | B: code-02、card-02、code-12；D: code-12 |
| `12` | L79 `sizeof(DaemonTaskMessage_t)=12`；L124–L126 不写/PEND=0 同为 12；L158 TRACE=0 不影响消息体；L187 `80+8×12=176` | B: card-02、code-07、code-05、sim-A；封面 |
| `80` | L82 `sizeof(Queue_t)=80`；L151 `Queue_t TRACE=1 80`；L187 队列头 80 | B: card-02、code-05、card-03；封面 |
| `72` | L151/L156 `Queue_t` 在 TRACE=0 时为 72 | B: card-02 |
| `88` | L84 `sizeof(TCB_t)=88`；L185 守护任务 TCB `pvPortMalloc(88)` | B: card-02、code-04、code-10；D: code-04；封面 |
| `41` | L179 成员逐个量之和 = 41 B；L180 `sizeof(Timer_t)=44`，尾部补 3 | B: code-02 |
| `4` | L172 指针宽度 4 字节；L173 `sizeof(StackType_t)=4`；L30 建任务调用点 4 处；L41 回调调用点总数 4；L283 幕 D slow 补拍 4 次 | B: code-02、code-04、code-10、code-12、hook-02、cb-01、sim-D；D: code-04、code-12；封面 |
| `104` | L104 `heap_4.c:104 } BlockLink_t;` 的源码行号 | B: code-03 |
| `187` / `198` | L102/L103 `heap_4.c:187` / `:198` 的抽头加法与取整行号 | B: code-03 |
| `349` | L89 `timers.c:349` 的 `pvPortMalloc( sizeof( Timer_t ) )` 行号 | B: code-01 |

注：`104`、`187`、`198`、`349` 是源码行号，不是字节数。`StaticTimer_t = 44 / 40` 与
`StaticQueue_t = 80 / 72`（L78、L150、L152）没有单独上屏，但支撑“静态版与动态版同尺寸”的旁白。

### 3.3 heap_4 抽头、固定总账与比价（日志 L175–L223）

| 上屏 token | 日志证据 | 场景 |
|---|---|---|
| `56` | L189 `每建一个定时器：56 B`；L193 回归护栏；L211 lab 档每定时器 56 B | B: card-01、card-03、code-09、card-05、code-11、punch；D: card-01、code-09、card-05、punch；发行：四平台 |
| `48` | L212 `t0 档每定时器 48 B`；L216 TRACE=0 每定时器省 8（56−8） | B: code-09、code-11；D: code-09 |
| `96` | L185 `pvPortMalloc(88) → 实付 96 B`；L139 队列 8→16 固定涨 96；L218 涨幅 = 长度增量 × 消息大小 | B: code-07、code-04、code-10；D: code-04；封面；发行：bilibili |
| `1024` | L173 `256 字 = 1024 B`；L186 `pvPortMallocStack(256×4=1024)` | B: code-04；D: code-04 |
| `1032` | L186 守护任务栈实付 1032 B | B: code-04；D: code-04；封面；发行：bilibili |
| `1128` | L185 的 96 + L186 的 1032 = 1128；L188 固定 1312 = 1128 + 184 | B: code-04、card-03；D: code-04；发行：四平台 |
| `176` | L187 `pvPortMalloc(80+8×12=176)` | B: code-05；封面 |
| `184` | L187 命令队列实付 184 B | B: code-05、card-03；D: card-03；封面；发行：四平台 |
| `1312` | L188 固定那笔合计 1312 B；L192 回归护栏 | B: card-01、card-03、card-05、code-11、punch；D: card-01、card-03、card-05、punch；封面；发行：四平台 |
| `60` | L99 `timers.o 的 .bss：60 字节`；L202–L204 `20×2 + 4×4 + 4×1 = 60` | B: card-01、code-12、punch；D: card-01、code-12、punch；封面；发行：四平台 |
| `16384` | L174 `configTOTAL_HEAP_SIZE = 16384 B`；L196 `1312 ≤ 16384` | B: hook-01、card-03；D: hook-01 |
| `8.0%` | L190 `千分比 80‰，也就是 8.0%`；L195 回归护栏 | B: card-03；D: card-03；发行：bilibili、zhihu、xiaohongshu |
| `8%` | 同一行 `80‰ = 8.0%` 的简写；D 旁白取一位小数以下的写法 | D: card-03 |
| `16 KiB`（token 规范化为 `16kib`） | L174 `16384 B`，即 16 KiB；L190 占它的 8.0% | D: card-03；发行：bilibili、zhihu、xiaohongshu |
| `616` | L189 `每开一个最小任务：616 B（栈 128 字）`；L206 `616 ÷ 56` | B: card-03、code-10、card-05、card-08；D: card-05；发行：四平台 |
| `512` | L12 的 128 字 × L173 的 4 B/字 = 512；代入 L175 公式得 520 | B: code-10 |
| `520` | 两个来源：L189 的 `tap(512) = 520`（code-10）；L251/L268/L280 幕 C fast 最大迟到 520（sim-C、punch-01） | B: code-10、sim-C、punch-01 |
| `2.12` | L208 `1312 ÷ 616 = 2.12 个最小任务` | B: card-03、card-05；D: card-03、card-05 |
| `11` | L206 `616 ÷ 56 = 11`（一个任务的名额） | B: card-05；D: card-05；发行：bilibili、zhihu、xiaohongshu |
| `269` | L223 `(16384 − 1312) ÷ 56 = 269`，明确是上界不是预算 | B: card-03；D: card-03 |
| `1296` | L212 `t0 档固定 1296 B`；L215 相对 lab −16 | B: code-11；发行：bilibili |
| `1344` | L213 `p1 档固定 1344 B`；L217 相对 lab +32 | B: code-11；发行：bilibili |
| `1408` | L214 `q16 档固定 1408 B`；L218 相对 lab +96 | B: code-11；发行：bilibili |
| `+0` | L211 `sizes 档相对 lab +0 B` | B: code-11 |
| `-16` | L212/L215 `t0 档相对 lab −16 B` | B: code-11 |
| `+32` | L213/L217 `p1 档相对 lab +32 B = 8 × 4` | B: code-07、code-11 |
| `+96` | L214/L218 `q16 档相对 lab +96 B = 8 × 12` | B: code-07、code-11 |
| `16` | L126 PEND 消息体 16；L136–L137 `-DQLEN=16`；L202 四个指针 `4×4=16` | B: code-07、code-11；D: code-12；发行：bilibili |

注：`+0`、`-16`、`+32`、`+96` 是相对 lab 档的差值，不是四次独立测量；它们都能由
`长度 × 消息宽` 或 `56−48` 复现。`8.0%` 与 `8%` 是同一个比例的不同写法，不构成两次测量；
`16 KiB` 是 `16384 B` 的单位换算，token 规范化为 `16kib`。

### 3.4 守护任务、串行与同刻平局（日志 L24–L73、L226–L242）

| 上屏 token | 日志证据 | 场景 |
|---|---|---|
| `4` | L29–L31 建任务调用点 4 处，全在 `xTimerCreateTimerTask`；L41 回调调用点 4 处 | B: hook-02、cb-01 等（另见 §3.2） |
| `3` | L43–L48 四个回调调用点分属 `prvReloadTimer` / `prvProcessExpiredTimer` / `prvProcessReceivedCommands` 三个 `static` 函数；L281 幕 C slow 补拍 3 次 | B: code-02、cb-01、sim-C；D: cb-01 |
| `260` / `276` / `295` / `310` | L25–L28 四个 `xTaskCreate*` 调用点行号，第一实参均为 `prvTimerTask` | B: hook-02 |
| `65` | L33 `timers.c:65` 的守护任务名 `"Tmr Svc"` | B: hook-02 |
| `713` / `744` / `960` / `1021` | L37–L40 四个 `pxCallbackFunction` 调用点行号 | B: cb-01；D: cb-01 |
| `724` | L67 `listGET_OWNER_OF_HEAD_ENTRY( pxCurrentTimerList )`：一轮只取表头一个 | B: code-13 |
| `820` | L65 `vQueueWaitForMessageRestricted( ..., xNextExpireTime - xTimeNow, ... )` | B: code-13 |
| `795` | L237 `xTimeNow = prvSampleTimeNow( ... )`：一轮只采样一次 | B: code-14 |
| `192` | L238 `list.c:192` 的 `pxIterator->pxNext->xItemValue <= xValueOfInsertion` | B: code-07、code-15；发行：zhihu |
| `600` | L287 `t=600` 的动手顺序 `slow fast`；L288 slow 在 480 那一拍被插进 600 | B: code-15 |
| `1200` | L289 `t=1200` 再撞一次，顺序一样；sim_daemon.c 五幕观测窗口 1200 拍 | B: sim-D、code-15 |

注：`260/276/295/310`、`713/744/960/1021`、`724/795/820` 是源码行号；`600/1200` 是模型 tick，
不是耗时毫秒。`xNextExpireTime - xTimeNow` 在表空时按无符号回绕，等价于睡到滴答溢出：这是
源码语义（`prvGetNextExpireTime` 空表返回 0，L864）加无符号减法的推导，日志只直接打印了 L820 的
等待调用，factsheet 在此标明推导来源。

### 3.5 五幕模型（日志 L248–L292）

| 上屏 token | 日志证据 | 场景 |
|---|---|---|
| `100` | L230/L276–L285 fast 周期 100；L265 欠的不足一整拍（100） | B: sim-A、sim-B、sim-E、sim-C、sim-D；D: sim-B |
| `120` | L230–L236 slow 周期 120；L267 幕 C `200 > 120` | B: sim-A、sim-B、sim-C、sim-D；D: sim-B |
| `50` | L250 幕 B 占空比 416‰、最大迟到 50；L264 欠 50；L278 欠 50 / 补拍 0 | B: sim-B、punch-01；D: sim-B；发行：bilibili、douyin、zhihu |
| `416` | L250 幕 B 占空比 416‰（不满） | B: sim-B；D: sim-B |
| `200` | L251/L268 幕 C 最大迟到 520 > 耗时 200；L271 幕 E 最大迟到恰好 200；L284 幕 E 欠 200 | B: sim-E、sim-C、punch-01 |
| `666` | L252 幕 E 占空比 666‰（不满）；L272 `666 < 1000` | B: sim-E |
| `1666` | L251 幕 C 占空比 1666‰（满了） | B: sim-C |
| `520` | L251/L268/L280 幕 C fast 最大迟到 520、欠 520；另见 §3.3 的 `tap(512)` | B: sim-C、punch-01、code-10 |
| `560` | L281 幕 C slow 欠 560（周期 120，补拍 3） | B: sim-C |
| `970` | L270/L282 幕 D fast 收工欠 970（周期 100，补拍 5） | B: sim-D、punch-01；D: punch-01 |
| `910` | L283 幕 D slow 欠 910（周期 120，补拍 4） | B: sim-D |
| `250` | sim_daemon.c:236 D 幕输入 `slow 120 250`（日志 L270 只打印欠账 970，不打印 250） | B: sim-D |
| `300` | L271/L272 幕 E slow 周期 300；sim_daemon.c:238 的 E 幕输入 | B: sim-E |
| `1200` | sim_daemon.c 五幕观测窗口 1200 拍；L289 `t=1200` | B: sim-D、code-15 |
| `600` | L287–L289 同刻撞车 tick 600 / 1200 | B: code-15 |
| `5` | L262 幕 B fast 迟到 5 次；L282 幕 D fast 补拍 5 次 | B: sim-B、sim-D、punch-01 |
| `6` | L267 幕 C 同一时刻最多连开 6 次；L274/L280/L284 幕 C/E fast 补拍 6 次；L170 第 6 步 | B: code-02、code-04、code-05、sim-E、sim-C；D: code-04 |
| `3` | L281 幕 C slow 补拍 3 次；L43–L48 三个 static 函数 | B: sim-C、cb-01；D: cb-01 |
| `10` | L260 幕 A slow 应拍 = 实拍（10） | B: sim-A |
| `0` | L249/L258/L261/L263/L266/L273 幕 A/B/E 的零迟到、零补拍、零欠账；L276–L278 两对欠 0 | B: sim-A、sim-B、sim-E、sim-C、sim-D、punch-01、punch-02；D: sim-B |

注：五幕的 `实际拍数` 只有幕 A 的 12/10 被日志打印（L259–L260）；幕 B/C/D/E 的“实拍”没有逐条
打印，所以 v2 不写 v1 的 9/7/8 之类的实际计数。幕 C slow 的“最大迟到”也没有打印，代码里用
`—` 而不是 `720`；只写日志给出的欠 560、补拍 3。幕 D 的“最大迟到”同样没有打印，v2 只写
欠 970、补拍 5。`520` 在 `code-10` 是 `tap(512)` 的实付，在 `sim-C` 是最大迟到，两个含义在
numbers JSON 的同一个证据串里分别注明。

### 3.6 路径与例外

| 上屏 token | 证据 | 场景 |
|---|---|---|
| `06` | 复现路径 `code/rtos/06-timers` 的章节号；不是 probe 读数 | B: cta；D: cta；发行：四平台；`exceptions` |

## 4. 不能删的技术断言（删了会让章节断链）

1. **“零”有两个方向的反例**：一个定时器都没建，固定 1312 B 已经付出（守护任务 + 命令队列）；另有
   60 B 落在 `.bss`，堆参数调多大都碰不到（L188、L199–L204）。删掉任一条，“零”只被推翻一半。
2. **对象是 44 B，建一个实付 56 B**：`Timer_t` 自身 44 B（L77、L88），成员和 41 + 尾对齐 3（L179–L180），
   自带 `ListItem_t` 20 B，所以每建一个只走一笔 malloc，`tap(44) = 56`（L189）。删掉这条，后面
   所有“每个 56”的账都失去起点。
3. **heap_4 的抽头是 8 B**：`align_up(n + 8, 8)`，`BlockLink_t = 8`、`portBYTE_ALIGNMENT = 8`
   （L102–L105、L175）。88→96、1024→1032、176→184 都是同一条公式的三个实例。删掉这条，
   三个“实付”会像三个魔法数。
4. **固定账本是 1128 + 184 = 1312**：TCB 96 + 栈 1032 = 1128，队列 184；占 16384 B 的 8.0%
   （L185–L190）。删掉这条，封面和总账小节没有落点。
5. **比价基准是 616 B 的最小任务**：`tap(88)=96`、`tap(512)=520`，合计 616；`616 ÷ 56 = 11`，
   `1312 ÷ 616 = 2.12`；269 是整池上限，不是预算（L189、L206–L208、L223）。删掉这条，
   “共用守护任务所以便宜”没有刻度。
6. **配置开关各有一笔价**：PEND 默认 0（不写与 `-DPEND=0` 逐字节相同），开 PEND 多 2 个符号、
   消息 12→16、固定 +32；QLEN 8→16 固定 +96 而消息宽不变；TRACE=0 让 Timer_t 44→40、
   TCB 88→80、Queue 80→72，固定 1296、每定时器 48；`TRACE=0 + STATS=1` 被 `FreeRTOS.h:2824`
   的 `#error` 拦下（L110–L168、L211–L218）。删掉这条，价目表只剩四个数。
7. **回调只有一个执行线程**：建任务调用点 4 处全在 `xTimerCreateTimerTask`，第一实参只有
   `prvTimerTask`（L25–L31）；回调调用点 4 处，分属 3 个 `static` 函数，且都只在守护任务的调用树里
   （L37–L48）。删掉这条，“串行”只是形容词。
8. **一轮只取表头一个、只采样一次时钟、然后睡到下一个到期**：L67、L237、L65。删掉这条，
   “一个回调磨蹭，后面全排队”没有机制。
9. **占空比判据**：A/B/E 三幕占空比不满，零耗时者的最大迟到等于最大回调耗时（0/50/200）；
   C/D 越线，C 最大迟到 520 > 200 且同一时刻连开 6 次，D 收工欠 970、补拍 5 次。
   拍没有丢：欠 < 周期或补拍 > 0（L249–L285）。删掉这条，五幕只是五个故事。
10. **同刻平局按插入顺序**：`list.c:192` 用 `<=`，相等时继续向后走；模型 `t=600` 与 `t=1200`
    都是 `slow fast`，因为 slow 在 480 就被插进 600 这个位置（L238–L240、L287–L290）。删掉这条，
    “先创建先跑”会被误当成规则。

## 5. 已知未取证项（明确“不上屏”或只作叙述前提）

| 项 | 状态 | 处理 |
|---|---|---|
| 板级 RAM / 运行时占用 | 日志没有开发板输出，也没有运行时 heap 统计 | 不上屏任何板级读数；1312 与 60 都是编译期与静态账 |
| 真实 TTS 时长、节拍审计 | 尚未构建；本次只做文稿与 `video:lint` / `video:numbers` | 节拍由 `deriveBeats` 自动生成，构建时 `validateBeats` 才是终审；报告里只给估算 |
| 守护任务栈的高水位 | 日志没有运行时栈水印 | 只说配置的 256 字与实付 1032 B，不说“够用/不够用” |
| `configTIMER_TASK_PRIORITY` 的具体值 | 日志只打印使用点，不打印优先级数字 | 不上屏；`hook-02` 只说“优先级来自配置” |
| `configMAX_TASK_NAME_LEN` 的原始值 | 日志只打印 `+1 = 13`，且本集未上屏 | 不写“12 或 13”；不在 numbers 里 |
| `configUSE_TIMERS = 1` | 编译 `timers.c` 的前提，不是探针量出的尺寸 | 只作为屏幕配置片段出现；旁白说“尺寸由编译器报数” |
| C 幕 slow 的最大迟到 | 日志只打印欠 560、补拍 3，没有最大迟到 | 代码用 `—`；不写 v1 的 720 |
| D 幕 fast/slow 的最大迟到 | 日志只打印欠 970/910、补拍 5/4，没有最大迟到 | 不写 v1 的 470/1140；只写欠账与补拍 |
| B/C/D/E 的实际拍数 | 日志只打印幕 A 的 12/10；其余没有逐条实拍 | 不写 v1 的 9/7/8；只写日志给出的迟到、补拍、欠账 |
| D 幕占空比 2.083 | 日志没有打印 D 的占空比；只打印欠账与补拍 | 不上屏 2.083；只写“越线”与欠账 |
| 空表睡到溢出的直接读数 | L820 打印等待调用；空表返回 0 与无符号回绕是源码推导 | 旁白保留机制，factsheet 标明推导来源 |
| 模拟器之外的调度器行为 | 宿主模拟器只抄分派规则，不含真实中断、tick 抖动 | 五幕统一标“模型值”，不说“板上实测” |

## 6. 与旧稿的关系

v1 的 34 场 id 全部保留，但正文、代码块、标题、封面和发行文案都按本次取证重写。场序也做了
调整：把 `code-06/07/08` 放到 `code-04/05/card-03` 之前，让“结构与配置税”先立住，再进总账；
id 不变。v1 的 `hook-02` 原本也是 `kind: "hook"`；v2 把它改成 `kind: "code"`，保证“只有开头
连续 hook 计入 15 s”的规则下只剩 `hook-01` 一个 hook。v1 的五幕顺序已经是 A/B/E/C/D（E 在
第三），v2 保留这个顺序，只把每一幕的标题、代码块和“模型值”标注补齐；id 不变。

v1 中以下说法没有本次日志依据，已删除或改写：

- **幕 C slow 最大迟到 720**：日志只给欠 560、补拍 3（L281），没有 720 的最大迟到；v2 用 `—`。
- **幕 D fast 最大迟到 470、slow 最大迟到 1140、占空比 2.083**：日志只给欠 970/910、补拍 5/4
  （L282–L283）；v2 不写 470、1140、2.083。
- **幕 B/C/D/E 的实际拍数 9/7/8 等**：日志只打印幕 A 的 12/10（L259–L260）；v2 不写这些计数。
- **“实物实验让人去数丢了几拍”**：本集是宿主模拟器，不是板级实物实验；日志明确“同一二进制连跑
  两次逐字节相同”（L245）。v2 改成“模型值”，并保留“拍没丢，是欠着”的结论。
- **“下一站看优先级反转……下期见”**：与本章无关的站外/下一集导流，v2 删除；结尾只留复现命令。
- **“每一句都复现 / 没有一个数是拟合出来的”**：v2 不把模型值说成实测，统一标“模型值/模拟器”；
  发行文案也不超额承诺。
- **v1 的 hook-02 作为第二个 hook**：v2 改成 code，避免两个 hook 相加超过 15 s。
- **v1 code-13 的“CPU 占用按到期事件算”**：日志没有 CPU 占用率；v2 只说“按到期事件醒”，
  不说占用率。
- **v1 的 `configTOTAL_HEAP_SIZE 调大调小` 叙述**：v2 保留“堆调多大都碰不到 60 B”的结论，
  但不再暗示做过“调大十倍”的实验；日志只给 `.bss` 段大小与堆分母。

逐句比对结果：v1 句子原样复用 **0 条**；按原始旁白重算，最长公共片段 13 字（含标点）：
`建，一千三百一十二字节已经`，位于 `card-01`，是“一个定时器都没建，一千三百一十二字节已经……”
这一句里的技术短语，不是整句。v2 没有“最快/最简单/零成本”这类绝对化说法；封面左侧的
“选型表：零开销”是待反驳的表格原话，右侧“实测：先付 1312 B”才是本集读数。

## 7. 审计回填

### 7.1 两条必跑命令

```text
> mcu-road@0.1.0 video:lint
> node video/src/cli.mjs lint f6-timers


▶ f6-timers  软件定时器的 RAM 账：一个都没建，已经付了 1312 字节  [bilibili, douyin]
  ✅ 通过：bilibili 34 场，douyin 12 场

✅ 全部通过
```

```text
> mcu-road@0.1.0 video:numbers
> node video/src/cli.mjs numbers f6-timers

✅ f6-timers: 86 个数字都有依据
```

`86` = `f6-timers-numbers.json` 的 85 个 `evidence` 键 + 1 个 `exceptions` 键（`06`）。每个键按
`numbers.mjs` 的 `extractTokens` 取 token；`16 KiB` 因此以 `16kib` 计，`V11.1.0` 里的 `1.0`
单独成键。

### 7.2 预算与结构

| 项 | 实测 | 要求 | 结论 |
|---|---|---|---|
| bilibili 场数 | 34 | 34 | 通过 |
| bilibili 旁白字数（JS `.length`） | 3150 | 3000–3400 | 通过 |
| bilibili 小节 | 5 | 3–6 | 通过 |
| douyin 场数 | 12 | 12 | 通过 |
| douyin 旁白字数 | 257 | 240–280（硬 305） | 通过 |
| douyin 小节 | 4 | 3–5 | 通过 |
| `hook-01` 旁白 | 65 字 | hook 合计 ≤15.0 s | 估算约 12.7 s（0.1955 s/字），构建时以 TTS 实测为准 |
| 唯一 hook | `hook-01` | 开头连续 hook 才计入 | `hook-02` 已改为 code，不计入 |

场景表（B = bilibili，D = douyin 选场；字数为旁白 `.length`）：

| B 场 | kind | 字 | 小节 | D 选 |
|---|---|---:|---|---|
| hook-01 | hook | 65 | 片头 | ✓ |
| card-01 | card | 78 | 片头 | ✓ |
| anim-01 | anim | 92 | 片头 |  |
| code-01 | code | 102 | 片头 |  |
| code-02 | code | 92 | 结构与配置税 |  |
| card-02 | card | 108 | 结构与配置税 |  |
| code-03 | code | 96 | 结构与配置税 |  |
| code-06 | code | 88 | 结构与配置税 |  |
| code-07 | code | 94 | 结构与配置税 |  |
| code-08 | code | 95 | 结构与配置税 |  |
| code-04 | code | 78 | 总账 | ✓ |
| code-05 | code | 94 | 总账 |  |
| card-03 | card | 95 | 总账 | ✓ |
| code-09 | code | 97 | 总账 | ✓ |
| code-10 | code | 85 | 总账 |  |
| card-05 | card | 106 | 总账 | ✓ |
| code-11 | code | 88 | 总账 |  |
| code-12 | code | 87 | 总账 | ✓ |
| hook-02 | code | 106 | 串行 |  |
| cb-01 | code | 92 | 串行 | ✓ |
| code-13 | code | 86 | 串行 |  |
| code-14 | code | 92 | 串行 |  |
| card-06 | card | 95 | 模型与判决 |  |
| sim-A | code | 101 | 模型与判决 |  |
| sim-B | code | 89 | 模型与判决 | ✓ |
| sim-E | code | 103 | 模型与判决 |  |
| sim-C | code | 98 | 模型与判决 |  |
| sim-D | code | 82 | 模型与判决 |  |
| punch-01 | card | 99 | 模型与判决 | ✓ |
| punch-02 | card | 88 | 模型与判决 |  |
| code-15 | code | 81 | 模型与判决 |  |
| card-08 | card | 101 | 模型与判决 |  |
| punch | card | 93 | 模型与判决 | ✓ |
| cta | outro | 104 | 模型与判决 | ✓ |

合计 3150 字。D 选场 12 个：`hook-01, card-01, code-04, card-03, code-09, card-05, code-12,
cb-01, sim-B, punch-01, punch, cta`，共 257 字；`set` 对 12 场全部覆写标题，另覆写
`card-01/code-04/card-03/code-09/card-05/code-12/cb-01/sim-B/punch-01/punch` 的代码或要点。

### 7.3 合同项逐条核对

- `formatVersion: 2`；`voice: "zh-CN-YunyangNeural"`；`rate: "+2%"`。
- 封面 `variant: "vs"`；四尺寸 `bilibili [1920,1200]`、`douyin [1080,1440]`、
  `zhihu [1920,1080]`、`xiaohongshu [1440,1080]`；`num` 为 `1312 B`，有 L188 证据。
- 封面**没有** `vs.labels`：左侧是“选型表：零开销”的表格原话，不是本机测量；右侧才是实测
  1312 B。只有两侧都实测时才该写 `["MEASURED","MEASURED"]`，本集不满足，所以留空。
- 全 34 + 12 场没有 `codeB`，因此不存在 `codeBLabel` 采用布局默认值的问题。
- 全稿没有显式 `beatMap`；`deriveBeats` 对每场用 `max(2, caption 数)` 生成节拍，且每 6 s 插入
  pulse，静态空档按构造不超过 6.05 s。构建时 `validateBeats` 是最终闸门；本报告只给估算。
- 所有 `emphasis` 都是对应场上屏文本的字面子串（lint 的 `validateEmphasis` 已逐场检查）；
  没有把旁白句子当 emphasis。
- 模型标注：`sim-A`–`sim-D` 标题均带“（模型）”，`codeLabel` 均为
  “模拟器输出 · 模型值，不是板级实测”，旁白均以“以上是/为模型值”收尾；`card-06` 明说
  “下面五幕全是模型值”；D 的 `sim-B` 标题为“模型 B 幕”，代码写“（模型值）”，note 写
  “模拟器输出，不是板级实测”。全稿没有把模拟器输出称作板级实测。
- 发行：四个平台均有 `publish`；抖音 caption 三行非空白字数 13 / 14 / 19，合计 46 ≤ 62；
  抖音标题 19 / 16 / 19 ≤ 30；小红书标题 18 ≤ 20、正文 273 ≤ 1000、合集非空、pinned 含
  `sh code/rtos/06-timers/probe.sh`；知乎字段与 c5 同口径。
- 复现命令：`sh code/rtos/06-timers/probe.sh`；没有站外地址、GitHub 字样或“下期见”式导流。

### 7.4 额外校验

- **v1 复用检查**：`git show HEAD:video/episodes/f6-timers/episode.json` 取 v1，与 v2 的 34 条
  旁白逐条做 `difflib.SequenceMatcher`；精确整句复用 0 条，最长公共片段 13 字（见 §6）。
- **陈旧数字 grep**：`470`、`720`、`1140`、`2.083`、`9/7/8` 实际计数均未出现在 v2 正文/代码/
  封面/发行中（`720` 只作为 `bilibili.targetSec` 的上限出现，不是内容数字）。
- **离站措辞 grep**：`公众号|关注|点赞|投币|收藏|转发|评论区|下期|加群|私信|三连|B站|b站|up主`
  在 episode 中 0 命中。
- **未跑项**：按任务要求没有运行 `npm run video:check`（它会读构建前的陈旧时间轴），也没有构建。
  真实 TTS 时长、`validateBeats`、排版渲染与音频响度都要等控制器构建后回填。
