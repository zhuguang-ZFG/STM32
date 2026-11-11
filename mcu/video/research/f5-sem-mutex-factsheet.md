# F5《信号量与互斥量：五个名字，零个函数》事实底稿

本文件是 `video/episodes/f5-sem-mutex/episode.json` 的上屏/口播数字对账底稿。所有“实测”行都从**本次**运行
`.temp/v2-facts/05-sem-mutex-probe.log`（388 行，EXIT 0）原样摘出；`docs/rtos/freertos/05-sem-mutex.md`
只用于叙述前提与 E04 的口径说明，逐条标明，不冒充本次读数。v1 的旧句已整体重写，见 §6。

## 1. 取证信息

| 项 | 值 |
|---|---|
| 源文档 | `docs/rtos/freertos/05-sem-mutex.md` |
| 取证脚本 | `code/rtos/05-sem-mutex/probe.sh`（八步：宏与符号 / 预处理 / 符号表 / 形状与账 / 出生 give / 身份 / 继承 / 模型） |
| 本次日志 | `.temp/v2-facts/05-sem-mutex-probe.log`（388 行，EXIT 0） |
| 内核与工具链 | 日志 L2–L4：交叉工具链 15.2.1、宿主 gcc 16.1.0、内核 `V11.1.0`；未上屏版本号 |
| 五个名字 | 日志 L8–L14：`semphr.h:167/735/1025/298/460/675` 六条宏；`SemaphoreHandle_t` 的 typedef 在 L89 |
| 预处理证明 | 日志 L36–L70：`gcc -E` 展开文本 `xSemaphore` 字样 0 个；五个队列入口分别出现 2/2/2/2/3 次 |
| 符号表证明 | 日志 L72–L92：`nm -u lin.o` 的 0 个 `xSemaphore*`、≥5 个 `xQueue*`，逐函数重定位配对；反向扫 queue.o+tasks.o 定义 0 个 |
| 形状与偏移 | 日志 L94–L146：`sizeof(Queue_t)=80`、`TCB_t=88`、偏移表、RAM 账、`adds r3,#80`、lab 配置 32 项逐项相同 |
| 出生 give | 日志 L148–L202：queue.c:647/651/652/631、机身顺序 16 < 20、实参 1/0、二值对照 main.c:352–353 |
| 身份 | 日志 L204–L256：queue.c:65/66、582、623；七处 `uxQueueType==queueQUEUE_IS_MUTEX`；TRACE 标签税 |
| 继承与回落 | 日志 L258–L310：判/改/搬、唯一调用 `uxListRemove`、机身顺序 45/64/110、`rsb #5`、回落 72→44、MUTEX=0 |
| 中断版 take | 日志 L15–L23：2035→2132 共 98 行，三样引用 0 处；任务路径 1652–1874 有 6 处 |
| 模型 | 日志 L312–L386：脚本参数、RES 两行、事件切片、E04 文档第 78 行“理论值”、实测表 0 个数字 |
| 板级输出 | **没有**。本集不烧板，不报串口毫秒、LED、示波器或运行时寄存器快照 |
| 数字审计 | `npm run video:numbers -- f5-sem-mutex` → `86 个数字都有依据`（§7） |

本次日志能兑现的“实测”只有：六条宏与一行 typedef 的源码行号（L8–L14、L89）、`-E` 的 0 与 2/2/2/2/3
（L40–L45）、`nm` 的 0 与 ≥5（L74–L80）、反向扫描的 0（L88）、尺寸与偏移（L96–L106）、两条独立的
80 字节路径（L108–L135）、lab 配置 32 项一致（L144–L146）、出生 give 的源码与机身顺序（L150–L196）、
身份宏与七处判断（L206–L256）、继承/回落的源码与机身顺序（L260–L310）、以及两档模型 RES 与 E04 的
口径（L338–L386）。其余机制若来自源码语义或文档，在 §5 单列。

## 2. 本集必须回答的 8 个问题

1. **为什么说 `xSemaphore` 不是类型、不是函数，而是五条宏？** `SemaphoreHandle_t` 是
   `QueueHandle_t` 的 typedef（L89）。创建二值/互斥/计数、take、give 五个名字分别展开到
   `xQueueGenericCreate`、`xQueueCreateMutex`、`xQueueCreateCountingSemaphore`、`xQueueSemaphoreTake`、
   `xQueueGenericSend`（L8–L13）。`gcc -E` 之后 `xSemaphore` 字样剩 0 个（L40）；`nm -u lin.o`
   的未定义引用是 0 个 `xSemaphore*`、5 个 `xQueue*`（L74–L80）；逐函数重定位配对证明每个 probe
   函数只调一个队列入口（L82–L86）；反过来扫 queue.o+tasks.o，内核也没有定义任何 `xSemaphore*`
   符号（L88）。
2. **预处理文本和符号表各证明了什么？** `-E` 证明“名字在进入编译器前就没了”，且五个入口分别出现
   2/2/2/2/3 次（L41–L45）；`nm -u` 证明“目标文件真正依赖的是队列函数”，0 对 ≥5（L79–L80）。
   前者证明落点，后者证明依赖；两者不是同一次测量，不能互相替代。
3. **一把锁到底占多少字节？** `sizeof(Queue_t)=80`，`sizeof(StaticQueue_t)=80`（L96–L99）；
   互斥量与二值信号量都是 `uxLength=1`、`uxItemSize=0`，载荷 `1×0=0`，所以一次分配只有结构体
   本身 80 字节（L108–L111）。独立的反汇编路子在同一段 `pvPortMalloc` 前读到 `adds r3,#80`
   （L113–L135）。TRACE=0 时 `ucQueueType` 标签连同成员消失，结构体从 80 掉到 72，标签税 8 字节
   （L240–L244）。
4. **互斥量的“身份”是什么，为什么没有“我是锁”的字段？** queue.c:65 把 `uxQueueType` 宏定义成
   `pcHead`，queue.c:66 把 `queueQUEUE_IS_MUTEX` 定义成 `NULL`（L206–L207）。项大小为 0 时，
   `prvInitialiseNewQueue` 把 `pcHead` 指向结构体自己（queue.c:582，L219）；`prvInitialiseMutex`
   再把同一个槽覆盖成 NULL（queue.c:623，L222）。机身对应偏移 0/8/12 三次写零（L224–L226）。
   全文七处判断读的都是这个槽：705、737、1353、1699、1784、1834、2405（L249–L255）。其中 1353 是
   `configASSERT`，1834 是注释里对同一判断的引用；七处都指向同一个 `pcHead` 比较。
5. **互斥量为什么“出生即满”？** `xQueueCreateMutex` 把长度写死为 1、每项写死为 0
   （queue.c:647，L150），先 `xQueueGenericCreate`（queue.c:651），再 `prvInitialiseMutex`
   （queue.c:652）；后者最后一句就是 `xQueueGenericSend(..., 0U, queueSEND_TO_BACK)`
   （queue.c:631，L156）。机身顺序是 `bl xQueueGenericCreate` 第 16 行、`bl prvInitialiseMutex`
   第 20 行（16 < 20，L185），实参是立即数 1 和 0（L187–L188），give 的 blockTime 是 0
   （L189–L196）。二值信号量没有这一发，main.c:352 建完、353 由剧本自己补 give（L197–L201）。
6. **继承的“判 → 改 → 搬”和回落镜像是什么？** 判：持有者非空（tasks.c:6589）且持锁者优先级更低
   （tasks.c:6594，L260–L263）。改：事件表值写成 `configMAX_PRIORITIES - 等待者优先级`
   （tasks.c:6601），当前优先级抄成等待者（tasks.c:6625，L265–L266）；`configMAX_PRIORITIES=5`
   是探针量出来的（L97），机身里是 `rsb r2, r3, #5`（L286）。搬：`uxListRemove` 摘旧表
   （tasks.c:6612）、位图复位（tasks.c:6617）、`prvAddTaskToReadyList` 挂新表（tasks.c:6626，
   L269–L271）。整个 `xTaskPriorityInherit` 只有一次函数调用，就是 `uxListRemove`；挂表是
   `listINSERT_END` 宏（list.h:362，L291）。机身顺序是摘 45 → 改 64 → 搬 110（L294–L295）。
   回落：`xTaskPriorityDisinherit`（queue.c:2408）在 `uxMutexesHeld==0` 时（tasks.c:6705）把
   `uxBasePriority` 写回 `uxPriority`（tasks.c:6724）；机身从偏移 72 读、往 44 写（L299–L301），
   并先摘表。基准值是任务创建时写的（tasks.c:1906，L279）。
7. **为什么中断版 take 没有互斥量机制？** `xSemaphoreTakeFromISR` 展开成 `xQueueReceiveFromISR`
   （semphr.h:675，L14）。整个函数体 2035→2132 共 98 行（L19），从未写 `xMutexHolder`、从未比较
   `uxQueueType`、从未调用 `xTaskPriorityInherit`，三样引用都是 0（L20）；同一把尺子量任务路径
   take（1652–1874），三样引用 6 次（L21）。所以“中断里不该拿互斥锁”的凭据是这条路径根本不登记
   持有者，不是 tasks.c:6589 那一问（L16–L17）。
8. **6000/2500/3500 是什么数？** 是 `sim_invert.c` 的模型值，不是板子毫秒：二值档
   `waited=6000`，互斥量档 `waited=2500`，两档之差 3500（L343–L347）。两档里 L 都跑到 3000 拍
   （L353–L355）；二值档 M 跑到 4000 拍（L356）。同一二进制连跑两次逐字节相同（L338），模型没有
   真时钟、没有随机数。E04 文档第 78 行称其为“理论值……不是实测数据”（L385），那张实测记录表里
   0 个数字（L386）。因此上屏只写“模型值”，绝不写成串口毫秒。

### 必须保留的断言（改写时不得丢失）

1. 五个 `xSemaphore` 名字是宏，落点是五个队列入口；`-E` 后 0 个 `xSemaphore` 字样，`nm` 是 0 对
   ≥5，反向扫描也是 0。
2. 一把锁 80 字节、载荷 0；TRACE=0 时 72 字节，标签税 8 字节。
3. 身份就是 `pcHead` 是否为 NULL；`pcHead` 是 `uxQueueType` 的别名；七处判断读同一格；结构体
   没有专用的“我是锁”字段。
4. 出生 give：长度 1、每项 0，`prvInitialiseMutex` 发送一次；二值信号量没有这一发，
   main.c:352/353 自己补 give。
5. 继承三步是判 → 改 → 搬；唯一函数调用是 `uxListRemove`；机身顺序 45 → 64 → 110；最大优先级
   5 是探针量出的；回落从 72 读、往 44 写。
6. 中断版 take 的函数体 98 行，三样引用 0 处；任务路径 take 有 6 处。
7. 6000/2500/3500 是模型值；两档 L 都跑 3000 拍，二值档 M 跑 4000 拍；E04 文档第 78 行称理论值，
   实测表 0 个数字。
8. 所有行号、偏移、尺寸都标明来源（probe 读数或源码行号），不把源码行号说成运行时测量。

## 3. 结构体、偏移与长度（日志 L94–L146）

| 项 | 读数 | 日志行 |
|---|---|---|
| `sizeof(Queue_t)` | 80 | L96 |
| `sizeof(StaticQueue_t)` | 80（queue.c:406 断言） | L98–L99 |
| `sizeof(TCB_t)` | 88 | L96 |
| 指针 / `UBaseType_t` | 4 / 4 | L96 |
| `List_t` / `ListItem_t` | 20 / 20 | L96 |
| `configMAX_PRIORITIES` | 5（探针量出，不抄配置） | L97 |
| `pcHead` / `pcWriteTo` / `u` | 0 / 4 / 8 | L101 |
| `pcTail` / `xMutexHolder` | 8 / 8（同一联合槽） | L101、L104 |
| `pcReadFrom` / `uxRecursiveCallCount` | 12 / 12（同一联合槽） | L101、L105 |
| 两个联合成员的大小 | 各 8 字节 | L106 |
| `uxMessagesWaiting` / `uxLength` / `uxItemSize` | 56 / 60 / 64 | L102 |
| `TCB.uxPriority` / `uxBasePriority` / `uxMutexesHeld` | 44 / 72 / 76 | L103 |
| `TCB.xStateListItem` / `xEventListItem` | 4 / 24 | L103 |
| `ucQueueType` | 76（仅 TRACE=1；TRACE=0 时消失） | L244–L246 |

RAM 账：`xQueueSizeInBytes = uxQueueLength × uxItemSize`（queue.c:521，L109），
`pvPortMalloc(sizeof(Queue_t) + xQueueSizeInBytes)`（queue.c:526，L108）。锁的输入是 1×0=0，
所以一次分配就是 80 字节；`adds r3,#80` 是第二条独立证据（L133）。lab 配置档重编后，上表
全部数字与默认档逐项相同（32 项全比，L144–L146）。

## 4. 上屏数字逐项对账（86 个 token）

> 场景写法：`B:` = bilibili，`D:` = douyin，`封面` = 主封面，`发行` = publish 文案。
> 每个 token 的完整证据字符串见 `f5-sem-mutex-numbers.json`；本表按语义分组，不重复抄整段。
> 审计同时覆盖场景字段、`bullets`、封面字段与四个平台的发布文案。

### 4.1 名字、宏与符号

| token | 证据 | 代表场景 |
|---|---|---|
| `167` / `735` / `1025` / `298` / `460` | L8–L13 五条 `semphr.h` 宏的行号与展开目标 | B: hook-01、code-01；D: hook-01；发行 |
| `675` | L14：`xSemaphoreTakeFromISR` → `xQueueReceiveFromISR` | B: code-20；发行 |
| `38` | L89：`semphr.h:38 typedef QueueHandle_t SemaphoreHandle_t;` | B: code-05 |
| `0` | L40：`-E` 后 `xSemaphore` 字样 0；L79/L88：两个方向的符号扫描都是 0；L49/L110：项长与载荷 0；L386：E04 实测表 0 个数字 | 多处 |
| `5` | L80：未定义 `xQueue*` ≥5；L41–L45：五个入口各 ≥1；L97：`configMAX_PRIORITIES=5` | B: code-04、code-16、cta；D: code-02；发行 |
| `2` / `3` | L41–L45：展开计数 2/2/2/2/3；L49：二值标签 3；L60：计数初值 2；L239：二值标签宏 = 3 | B: code-01、code-02、code-03 |
| `4` | L96：指针与 `UBaseType_t` 各 4；L60：计数信号量上限 4U | B: code-03、code-07 |
| `1` | L49：二值长度 1；L54：互斥标签 1；L150：`uxMutexLength=1`；L156：出生发送一次；L307：`xQueueSemaphoreTake` 定义数 1 | 多处 |

### 4.2 形状、长度与偏移

| token | 证据 | 代表场景 |
|---|---|---|
| `80` | L96：`Queue_t=80`；L98：`StaticQueue_t=80`；L111：一把锁 80 字节；L133：机身 `#80`；L144：lab 档仍 80 | B: card-02、code-06、code-07、code-08、punch、cta；D: card-01、punch；封面；发行 |
| `88` | L96/L144：`TCB_t=88` | B: code-07 |
| `521` / `526` | L109 / L108：`xQueueSizeInBytes` 乘法与 `pvPortMalloc` | B: code-06 |
| `406` | L99：`queue.c:406 configASSERT( xSize == sizeof( Queue_t ) )` | B: code-07 |
| `20` | L96：`List_t`/`ListItem_t` 各 20；日志 L176 所抄机身清单的第 20 行是 `bl prvInitialiseMutex` | B: code-07、code-09 |
| `8` | L101：`u` 偏移 8；L104：第一联合槽重叠 8；L106：联合成员各 8；L241：标签税 8 | B: code-08、card-03、card-04；D: code-13；发行 |
| `12` | L101/L105：第二联合槽偏移 12 | B: code-08、card-03；D: code-13；发行 |
| `56` / `60` / `64` | L102：`uxMessagesWaiting`/`uxLength`/`uxItemSize` 偏移；L294：继承机身‘改’在清单第 64 行 | B: code-08、code-17、cta；发行 |
| `44` / `72` / `76` / `24` | L103：TCB 的 `uxPriority`/`uxBasePriority`/`uxMutexesHeld`/`xEventListItem` 偏移；L244：`ucQueueType` 偏移 76 | B: code-08、code-15、code-16、code-18；发行 |
| `16` | L185：机身清单第 16 行 `bl xQueueGenericCreate`，早于第 20 行 | B: code-09；发行 |
| `72`（另一义） | L240–L241：TRACE=0 时 `Queue_t` 为 72 字节 | B: card-04；发行 |

### 4.3 出生 give

| token | 证据 | 代表场景 |
|---|---|---|
| `647` / `651` / `652` / `631` | L150–L156：长度 1、每项 0、建队列、初始化、创建时发送一次 | B: code-09；发行 |
| `1` / `0` | L150/L187–L188：长度与每项大小的立即数；L156：give blockTime 0 | B: code-09、code-10 |
| `352` / `353` | L201 / L200：二值信号量建完由剧本补 give | B: code-10；发行（二值对照） |

### 4.4 身份与 TRACE

| token | 证据 | 代表场景 |
|---|---|---|
| `65` / `66` | L206–L207：`uxQueueType` 是 `pcHead` 的别名，互斥量身份值是 NULL | B: code-11、code-12；D: code-11；发行 |
| `582` / `623` | L219 / L222：项大小 0 时自指；`prvInitialiseMutex` 覆盖成 NULL | B: code-13 |
| `705` / `737` / `1353` / `1699` / `1784` / `1834` / `2405` | L249–L255：七处 `uxQueueType == queueQUEUE_IS_MUTEX` 判断/引用 | B: code-14 |
| `0` / `8` / `12` | L224–L226：机身往偏移 0/8/12 三发写零 | B: code-13；D: code-13 |
| `76` / `80` / `72` / `8` | L244/L240–L241：标签偏移、TRACE=1 的 80、TRACE=0 的 72、标签税 8 | B: hook-02、card-04 |

### 4.5 继承与回落

| token | 证据 | 代表场景 |
|---|---|---|
| `6589` / `6594` / `6601` / `6625` | L260–L266：判空、比优先级、写事件表值、写当前优先级 | B: code-15、code-16；发行 |
| `6612` / `6617` / `6626` | L269–L271：摘表、复位位图、挂新表 | B: code-17；发行 |
| `362` | L291：`list.h:362` 的 `listINSERT_END` 是宏 | B: code-17 |
| `45` / `64` / `110` | L293–L295：机身顺序 摘 45 → 改 64 → 搬 110（清单行号） | B: code-17、cta；发行 |
| `2408` / `6705` / `6724` / `1906` | L318/L273/L274/L279：回落入口、`uxMutexesHeld==0`、写回基准、基准来源 | B: code-18；发行 |
| `44` / `72` | L299–L301：回落读 72、写 44；L281–L284：判读 44 | B: code-15、code-18 |
| `5` / `24` | L97：最大优先级 5；L286：`rsb #5`；L287：写 `xEventListItem` 偏移 24 | B: code-16 |
| `320` / `0` | L309–L310：MUTEX=0 时 `.text.xTaskPriorityInherit` 320→0；L305–L307：两个符号 0，`xQueueSemaphoreTake` 仍在 | B: card-05；D: card-05；发行 |

### 4.6 中断路径

| token | 证据 | 代表场景 |
|---|---|---|
| `675` / `2035` / `2132` / `98` | L14/L19：宏落点、函数体范围、98 行 | B: code-20；D: code-20；发行 |
| `1652` / `1874` / `6` | L21：任务路径 take 的范围与 6 次引用 | B: code-20；发行 |
| `0` | L20：三样引用各 0 | B: code-20；D: code-20 |

### 4.7 剧本参数与模型值

| token | 证据 | 代表场景 |
|---|---|---|
| `315` / `3000` | L329：`cpu_work_ms(3000)`；L353–L355：两档 L 都跑 3000 拍 | B: code-19、intro；D: 发行 |
| `324` / `500` | L330：M 从第 500 拍起跑 | B: code-19 |
| `326` / `4500` | L331：M 占 CPU 到 4500；L343–L344：两档 `m_end=4500` | B: code-19、sim-binary、sim-mutex；D: sim-binary、sim-mutex |
| `334` / `1000` | L332：H 第 1000 拍醒来；L343–L344：`h_want=1000` | B: code-19、sim-binary、sim-mutex |
| `356` / `358` | L333–L334：L 优先级 1、H 优先级 3（与 `prio_inherited=3` 对应） | B: code-19；D: sim-mutex |
| `6000` / `7000` / `4000` | L343：二值档 `waited=6000`、`h_got/l_give=7000`、`m_ran=4000`；L345–L347 标注模型值 | B: sim-binary、punch-01；D: sim-binary、card-06；发行 |
| `2500` / `3500` / `1500` | L344：互斥档 `waited=2500`、`h_got/l_give=3500`、`m_ran=1500`；L346–L347 标注模型值 | B: sim-mutex、punch-01；D: sim-mutex、card-06；发行 |
| `78` | L385：E04 文档第 78 行自称“理论值……不是实测数据”；L386：实测表 0 个数字 | B: card-06；发行 |

### 4.8 发布与路径例外

| token | 证据 | 代表场景 |
|---|---|---|
| `80` / `0` / `1` / `65` / `8` / `12` / `72` | 封面与发布文案只复述 §4.2–§4.4 的读数，不引入新测量 | 封面；B/D/Zhihu/XHS 文案 |
| `05` | 复现路径 `code/rtos/05-sem-mutex/probe.sh` 的章节号，不是 probe 读数 | 全部平台的 repro / cta |
| `17` | `video/series.json` 中 `f5-sem-mutex` 的 `no=17`，即“第 17 集”，不是 probe 读数 | 小红书正文末尾 |

## 5. 已知未取证项与口径边界

| 项 | 状态 | 处理 |
|---|---|---|
| 板级毫秒、串口日志、周期数 | 本次没有开发板，没有真时钟/示波器/DWT | v2 不报任何“实测毫秒”；6000/2500/3500 只叫拍/模型值 |
| 模型值的身份 | `sim_invert.c` 是宿主机模型，事件表写死，无真时钟、无随机数；同二进制两次逐字节相同（L338） | 上屏标注“模型值”；card-06 与 cta 反复声明不是板子毫秒 |
| E04 的“理论值” | L385 是文档自述，L386 说明实测记录表 0 个数字 | 只引用“第 78 行”和“0 个数字”，不把理论值升级为实测 |
| `ucQueueType` 的标签值 4 | L233 的分类标题提到 0/1/3/4，但 L237–L239 只定义 0/1/3；没有 4 的宏定义 | v2 只上屏 0/1/3，v1 的“四”已删除 |
| 七处判断的形态 | 705/737/1699/1784/2405 是运行时判断，1353 是 `configASSERT`，1834 是注释引用 | 统一说“七处判断/引用”，不夸成全在取锁热路径上执行 |
| 机身 16/20、45/64/110 | 是反汇编清单里的行序号，不是源码行号，也不是结构体偏移 | code-09/17 明说“第 16 行/第 20 行”“摘 45 → 改 64 → 搬 110” |
| 源码行号 406/521/526/647/… | 是本次 probe 读取并核对的源码行号，不是运行时测量 | 上屏写成 `queue.c:xxx`；数字 JSON 逐条给日志行 |
| 工具链版本 15.2.1 / gcc 16.1.0 / V11.1.0 | 日志 L2–L3 有，但本集不靠版本号立论 | 不占用屏面；正文只说“本机 probe” |
| 互斥量对象/堆地址 | 日志只有 `sizeof`、偏移与静态反汇编，没有运行时地址 | v2 不报地址、不报堆布局 |
| `xTaskPriorityInherit` 的 320 字节 | 是 `.text` 段大小（L309），不是执行时间或指令条数 | 只说“320 字节 → 0 字节” |
| “中断里不该拿互斥锁” | 依据是 98 行函数体三样引用全 0（L19–L21），不是 API 明文禁止，也不是 tasks.c:6589 | 只讲“这条路不登记持有者/没有互斥量机制”，并说明理由不在那两行判断 |
| `configMAX_PRIORITIES=5` | 探测数组量出（L97），不是从配置文件抄的 | 上屏写“探针量出”；机身 `rsb #5` 是第二证据（L286） |
| TRACE=0 的偏移 76 | TRACE=0 时标签成员不存在，偏移探针也不存在（L243） | card-04 只说“TRACE=1 时偏移 76；TRACE=0 时消失”，不把 76 当成 TRACE=0 的字段 |
| `05` / `17` | 路径编号与系列编号 | 放进 numbers JSON 的 `exceptions`，不算测量 |

## 6. 与 v1 的关系

v1 的 35 场已整体重写为 v2 的 35 场（6 节），场景 id 全部保留；抖音仍是 12 场，但换成
`reuseFrom: "bilibili"` + `pick` 的新短版（4 节）。结构变化：

- 口播从 **3597** 字降到 **3393** 字（目标 3000–3400），每场都重写；v1 的 `hook-01` + `hook-02`
  两个 hook 改为只有一个 `hook-01`（69 字，约 13.49 s），`hook-02` 保留 id 但改成 `card`。
- v1 没有 `formatVersion`、没有 sections、没有封面尺寸、voice 是 `zh-CN-YunxiNeural` / `+4%`；
  v2 是 `formatVersion: 2`、6 节、四平台尺寸、`zh-CN-YunyangNeural` / `+2%`。
- v1 没有任何 `codeB`；v2 的 code-11/13/16/17 有 `codeB`，全部显式写 `codeBLabel`，不用 layout
  默认的“-O2 编出来的汇编”。
- v1 的 code-20（中断）排在 code-19（剧本参数）之后；v2 把 code-20 提前到 card-05 之前，让
  “中断没有互斥量机制”先收口，再讲“MUTEX=0 整段消失”，id 不变。
- v1 的抖音 12 场是直接写 12 段；v2 用 `pick` 从 bilibili 选 12 场，再 `set` 标题/要点/`codeLine`
  与 `narration` 覆盖，抖音总口播 265 字（目标 240–280）。

v1 中以下说法**没有本次日志依据、或与日志口径冲突**，已删除或改写：

- **“零、一、三、四这种标签值”**：v1 把 4 也列进标签。本次日志只在 L233 的分类标题提到
  0/1/3/4，L237–L239 只定义 0/1/3，没有 4 的宏定义。v2 只写 0/1/3。
- **“两个毫秒数”“串口打出来是几毫秒”**：v1 把模型差说成毫秒。日志 L345–L346 明确写“模型值，
  不是板子毫秒”，模型是宿主机、无真时钟。v2 改说“拍/模型值”，card-06 反复声明不是板级毫秒。
- **“实验文档自己写着……脚本专门断言，只要有人往表里填数取证就报错”**：日志只证明 E04 第 78 行
  自称理论值、实测表 0 个数字（L385–L386），没有打印“填数就报错”的脚本断言。v2 删掉这层推断，
  只说文档自述与空表。
- **“我们板子上那出剧本”**：v1 的措辞容易被听成“已经在板子上跑过”。本次没有板级输出，v2 改成
  “板子源码/main.c 的剧本参数”，并明确模型在宿主机跑。
- **“三行不同的东西……并成一行”作为结论**：v2 保留“选型表三行”的开场，但不把三行当成三种
  数据结构；结论是“五个入口、一个结构体”。
- **“V11.1.0 头文件原文连行号一起 grep”**：日志确实有 V11.1.0（L3）与行号，但本集为控制屏面
  不再报版本号；v2 只报 `semphr.h` 的行号。
- **“那段机身三百二十字节变成零……你照样能拿一把完全没有继承的锁”**：v2 保留“320→0”与
  “取锁入口还在”（L305–L307），但把“完全没有继承的锁”改成“所有权只在任务之间成立”，避免把
  符号消失延伸成运行时语义的过度概括。

逐句比对：v1 与 v2 的 bilibili 旁白**没有整句复用**；最长公共片段 20 字，是技术文件名
`的 queue.o 和 tasks.o `，不是叙述句。抖音旁白与 v1 抖音的最长公共片段 10 字
（`H 只等 2500 拍。`），也是模型字段的读法，不是整句复用。v2 没有“最快/最简单/只要一个周期”
这类绝对化说法。

## 7. 审计回填

- `npm run video:lint -- f5-sem-mutex`：

  ```
  > mcu-road@0.1.0 video:lint
  > node video/src/cli.mjs lint f5-sem-mutex


  ▶ f5-sem-mutex  信号量与互斥量：五个名字，零个函数  [bilibili, douyin]
    ✅ 通过：bilibili 35 场，douyin 12 场

  ✅ 全部通过
  ```

- `npm run video:numbers -- f5-sem-mutex`：

  ```
  > mcu-road@0.1.0 video:numbers
  > node video/src/cli.mjs numbers f5-sem-mutex

  ✅ f5-sem-mutex: 86 个数字都有依据
  ```

- 旁白字数（实测，`resolveScenes` 后逐场相加）：bilibili **3393** 字（目标 3000–3400）；
  douyin **265** 字（目标 240–280，硬 305）。
- 片头：只有 `hook-01` 是 `kind: "hook"`，69 字 × 0.1955 s/字 ≈ **13.49 s**，≤15.0 s；
  `hook-02` 是 `card`，不并入钩子。
- 封面：`variant: "vs"`，四尺寸齐全；`vs.labels = ["CLAIM","MEASURED"]` 表示左边是选型表的
  主张、右边是本次展开的读数；`num = "80 B"` 来自 L96/L110。
- 抖音 caption 三行非空白字数 9 / 16 / 17，合计 42（上限 20 / 24 / 62）；pinned 含
  `sh code/rtos/05-sem-mutex/probe.sh`；repro 同命令。
- 小红书：标题 9 字（≤20）；正文 622 字（≤1000）；合集“通往单片机之路”非空；pinned 含复现命令；
  正文与标题没有 http/github/www 字样。
- 本稿未构建视频、未提交、未改本任务三份交付物之外的文件（报告另存于
  `.superpowers/sdd/implement/task-13-f5-authoring.md`）。
