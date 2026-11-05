---
title: S17 看门狗：任务失去进展之后
status: done
difficulty: 3
minutes: 45
---

# S17 看门狗：任务失去进展之后

> 🎯 定时器中断里每 10ms 喂一次狗，采集任务卡死了，狗会叫吗？不会。它只证明中断还活着。

## 本章精髓

1. **喂狗要证明关键工作在按期完成**：每个必需任务完成一轮有界工作后上报进展，监督任务确认全部按期才喂。任何一个迟到，就锁存"该重启"，之后来的心跳也撤销不了。
2. **两只狗量两种健康**：IWDG 用独立的 LSI 时钟，只管"别太晚"；WWDG 用 PCLK1，窗口两头都是死路，喂早了也复位。超时值要按时钟的最坏情况算，不能按名义值算。
3. **复位之后要留证据**：RCC_CSR 的复位标志先读出来再清；`.noinit` 里放一条带 magic/version/CRC 的记录，只在看门狗暖复位后才解读。断电后 RAM 内容不可信，CRC 对不上就报"没有有效记录"。

- **能理解**：为什么任务期限（500ms）和硬件超时（2s）是两个参数；为什么 MODE=2 要连写两次 WWDG_CR；为什么调试器断开后还要重新上电。
- **能用**：四种 MODE 各自构建；用 `fault` 命令停掉 worker，按时间预算预测复位时刻，再用 STATUS 和复位原因核对。

## 先修

- 必需：[S5 SysTick](05-systick.md)、[F8 FreeRTOS F407 移植](../rtos/freertos/08-port-f407.md)、[C8 串口协议](../c/08-framed-protocol.md)（数据口和 STATUS 都用它）。

## 先跑起来（10 分钟 quick win）

```sh
cd code/stm32/06-watchdog-health
make MODE=0 FAULTS=0      # IWDG，普通固件
```

用 ST-Link 烧录 `build/mode-0-faults-0` 下的产物。**烧完断开调试器，再给板子重新上电**（原因见第七节）。然后在仓库根执行：

```sh
python3 scripts/device-console.py status --port COMx
```

隔几秒再执行一次。运行毫秒在涨、复位原因没变、过期任务 mask 为 0，说明监督在正常喂狗，系统没有反复重启。数据口是 PA9/PA10，115200，协议和 C8 相同。

上电之前先押个喂养：喂狗是不是喂得越频繁越稳？逮着空就喂一口，行不行？押完往下看：有一种看门狗，喂得太早，下场和从来不喂一样。

## 动画：看门狗双雄

IWDG 倒数到 0 复位、喂狗等于重装；WWDG 只许在窗口内刷新——喂早了同样复位。两把尺子量两种健康："活着"与"节奏对"，动画把窗口的两头死路演出来。

![看门狗双雄：IWDG 只管活着，WWDG 还管节奏](/anim/watchdog-window.svg)

## 板卡事实

- 复位后系统时钟是 HSI16，本工程不改时钟树，所以 PCLK1 = 16MHz。WWDG 的窗口跟着 PCLK1 走，改了时钟树就得重算。
- LSI 名义 32kHz。DS8626 Rev 12 第 105 页表 35 给出的范围是 **17 / 32 / 47 kHz**（最小/典型/最大），注明是特性测试结果。手里这块板的 LSI 精确值待实测。
- IWDG 在 VDD 域，Stop 和 Standby 模式下照样计数（RM0090 Rev 22 §21.3）。用了 IWDG 再进低功耗，得把唤醒周期算进超时。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、喂狗证明什么 | 无条件喂狗的反例；三任务分工 | 代码分析 |
| 二、health 模块 | required/seen/deadline 三个 mask，宽限期与锁存 | 库解析 |
| 三、IWDG | 四步配置、表 107 实算、LSI 三档超时 | 配置 |
| 四、WWDG | 窗口公式实算，为什么 5ms 轮询正好 | 配置 |
| 五、故障注入与时间预算 | 四种 MODE；从命令到复位的时间线 | 代码分析 |
| 六、复位证据 | RCC_CSR 读后清；`.noinit` 记录的写入顺序 | 代码分析 |
| 七、调试器与看门狗 | DBGMCU 冻结位只在上电复位时清零 | 引脚 |

## 一、喂狗到底证明了什么

最常见的写法是在定时器中断或主循环里无条件喂狗：

```c
void TIM6_DAC_IRQHandler(void) { IWDG->KR = 0xAAAA; ... }   /* 反例 */
```

这只能证明"这个中断还在进"。采集任务死等一个永远不来的信号量、通信任务卡在一个没有超时的 while 里，中断照样准时到，狗永远不叫。看门狗该监督的是**工作有没有按期完成**，而不是**有没有代码在跑**。

本工程把职责拆成三个 FreeRTOS 任务：

| 任务 | 优先级 | 周期 | 职责 |
|---|---|---|---|
| worker | 2 | 10ms | 模拟一轮采集，完成后上报进展 id=0 |
| communication | 3 | 1ms | 最多读 128 字节喂给 C8 解析器，推进 TX，然后上报进展 id=1 |
| supervisor | 4 | 5ms | 评估健康；**唯一**允许喂狗的地方 |

通信任务没有收到串口数据也会上报进展。它证明的是"这一轮有界的服务检查做完了"，不要求主机一直发数据。监督任务优先级最高，低优先级任务忙死了也挡不住它判断超时。

## 二、health 模块：把"进展"变成可检查的 mask

`code/common/reliability/health.c` 是平台无关的纯 C，F407 和 S3 共用，主机上就能测。它不拿锁，也不碰看门狗寄存器，调用方负责串行化（F407 用 `taskENTER_CRITICAL`）。

```c
typedef struct {
    uint32_t required_mask, seen_mask, deadline_ms[8], last_ms[8], start_ms, grace_ms;
    bool valid, grace_active;
} health_t;
```

- **`health_init`** 校验配置：required 不能为 0，只能用低 8 位；每个必需 id 的期限不能为 0，期限和宽限期都必须小于 0x80000000（保证无符号减法比较不会出错）。任何一项不合法就返回 false，`valid` 保持 false，之后 `health_evaluate` 永远返回 `may_feed=false`。
- **`health_progress`** 只接受 required 里的 id，记下时间并置 `seen_mask` 对应位。
- **`health_evaluate`** 先处理宽限期：上电后 1000ms 内，或者所有必需任务都至少报到一次之前，允许喂狗。宽限期一结束，任何必需 id 满足"从没报到过"或"距上次报到 ≥ 期限"，就进 `overdue_mask`：

```c
if ((h->required_mask&bit) && (!(h->seen_mask&bit) ||
    (uint32_t)(now-h->last_ms[i])>=h->deadline_ms[i])) out.overdue_mask|=bit;
```

- **`health_supervise`** 第一次看到 `may_feed=false` 就锁存 `restart_latched`，并记下当时的 `first_overdue`。锁存之后永远返回 false：

```c
if (!result.may_feed && !s->restart_latched) {
    s->restart_latched=true; s->first_overdue=result.overdue_mask;
}
return !s->restart_latched && result.may_feed;
```

为什么要锁存？worker 卡了 600ms 又自己恢复，偶尔来一次心跳，系统看起来"又好了"。但它已经错过了一次期限，说明有个没被理解的故障。复位决定一旦做出就不撤回，留给复位后的记录去解释。

## 三、IWDG：四步配置，两个时间尺度

`code/stm32/platform/watchdog.h` 的启动顺序和 HAL v1.8.5 的 `HAL_IWDG_Init` 一致：

```c
REG32(IWDG,KR)=0xcccc;          /* 1. 启动；LSI 自动打开 */
REG32(IWDG,KR)=0x5555;          /* 2. 解锁 PR/RLR 写权限 */
REG32(IWDG,PR)=4;               /* 3. /64 */
REG32(IWDG,RLR)=999;
unsigned limit=1000000;while(REG32(IWDG,SR)&&--limit){}   /*    等 PVU/RVU 清零，有界 */
REG32(IWDG,KR)=0xaaaa;          /* 4. 用新值刷新 */
return limit!=0;
```

（代码里写的是基址加偏移：IWDG=0x40003000，KR/PR/RLR/SR 偏移 0/4/8/0xC。）

几个要点：

- **先启动再配置**。0xCCCC 写下去，计数器就从复位值 0xFFF、按复位分频 /4 开始倒数，约 512ms。万一后面的配置失败，狗也已经在跑，最终一定会复位，不会出现"配置失败所以没狗"的状态。
- **等 SR 必须有界**。PVU/RVU 清零要等 LSI 域同步完成。死等写成 `while(SR){}`，LSI 坏了就永远卡在这里。超时返回 false，supervisor 进 `for(;;){}`，让已经启动的狗去复位。
- **启动后不可停止**，只有复位能关掉它。

**表 107 实算。** RM0090 Rev 22 第 705 页表 107 给出 32kHz 下 /64 档每个计数 2ms（RL=0 时 2ms，RL=0xFFF 时 8192ms）。RLR=999 即 1000 个计数：

| LSI | 一个计数 | 超时 = 1000 × 64 / f_LSI |
|---|---|---|
| 47kHz（最快） | 1.36ms | **约 1.36 秒** |
| 32kHz（名义） | 2.00ms | **2.00 秒** |
| 17kHz（最慢） | 3.76ms | **约 3.76 秒** |

"2 秒"只是名义值。设计时要保证**最快的 LSI** 下（1.36 秒）正常喂狗也来得及，**最慢的 LSI** 下（3.76 秒）的故障检测延迟也能接受。

**两个时间尺度别混。** 任务期限 500ms 决定"什么时候停止喂狗"，IWDG 超时决定"停止喂狗之后多久复位"。故障到复位的延迟是两者相加，第五节会算一遍。

## 四、WWDG：窗口两头都是死路

`MODE=1` 换成 WWDG。它的计数器 T 是 7 位，每 `4096 × 2^WDGTB` 个 PCLK1 周期减一，从 0x40 减到 0x3F（T6 位清零）的那一刻复位。RM0090 Rev 22 第 711 页给出的公式：

t_WWDG = t_PCLK1 × 4096 × 2^WDGTB × (T[5:0] + 1)

本工程的配置（`f407_wwdg_start`）：先开 RCC_APB1ENR 的 WWDGEN（bit11）；CFR 写 `(3<<7)|0x5F`，即 WDGTB=3（/8）、窗口 W=0x5F；CR 写 0xFF，即 WDGA=1 启动、T=0x7F。

| 量 | 计算 | 结果 |
|---|---|---|
| 一个计数 | 4096 × 8 / 16MHz | **2.048ms** |
| 刷新后到复位 | (0x3F + 1) × 2.048ms | **约 131ms** |
| 窗口何时打开 | T 从 0x7F 减到 0x5E：(0x7F − 0x5E) × 2.048ms | **约 67.6ms** |

刷新只能在 0x3F < T < W 时进行。早于窗口刷新（T ≥ 0x5F）会立刻复位，晚了（T 降到 0x3F）也复位。RM0090 第 710 页原话：计数器必须在"小于窗口寄存器值且大于 0x3F"时重载。

`f407_wwdg_feed` 的判断和手册条件逐字对应，`0x3F < T < 0x5F` 才写；不在窗口内就返回 false，不为了"保命"硬喂：

```c
uint32_t count=REG32(WWDG,CR)&0x7f;
if(count>0x3f && count<0x5f){REG32(WWDG,CR)=0xff;return true;}
return false; /* Do not refresh early just to keep the MCU alive. */
```

supervisor 每 5ms 看一次。刷新后约 67.6ms 窗口打开，下一次轮询最多再晚 5ms，所以实际刷新间隔约 68~73ms，离 131ms 的复位还有将近 60ms 的余量。期限也得跟着收紧：WWDG 模式下两个任务的期限是 30ms，不能套用 IWDG 的 500ms，否则还没判定超时，WWDG 就已经复位了。

## 五、故障注入与时间预算

| 构建 | 看门狗 | 故障命令 | 预期 |
|---|---|---|---|
| `MODE=0 FAULTS=0` | IWDG | 拒绝（UNSUPPORTED） | 正常运行 |
| `MODE=1 FAULTS=0` | WWDG | 拒绝 | 正常运行 |
| `MODE=2 FAULTS=1` | WWDG | `fault --fault 2 --port COMx` | 停止正常监督，连写两次 CR，**过早刷新复位** |
| `MODE=3 FAULTS=1` | WWDG | `fault --fault 2 --port COMx` | 停止喂狗，**过晚复位** |

任何 FAULTS=1 的构建都可以用 `fault --fault 1 --task 0 --port COMx` 暂停 worker 的进展上报。

MODE=2 为什么要连写两次？第一次写可能恰好落在窗口里，算一次合法刷新，T 被重置为 0x7F；紧接着的第二次一定在窗口之外，必然触发过早复位。只写一次的话，结果取决于那一刻 T 是多少，实验不可复现。

故障命令都**先回确认，200ms 之后才生效**。这和 C8 的规则一样：确认帧入队成功才安排执行，延迟 200ms 让确认帧来得及发出去。

**时间预算**（MODE=0，`fault 1` 暂停 worker；t0 为设备收到命令的时刻）：

| 时刻 | 事件 |
|---|---|
| t0 | 确认帧入队，安排 200ms 后生效 |
| t0 + 200ms | worker 停止上报，它最后一次进展大约就在这时 |
| t0 + 700ms | supervisor 发现 worker 超过 500ms 期限：锁存重启、保存记录、停止喂狗 |
| t0 + 2.7s | IWDG 名义超时，复位（按 LSI 范围约 2.06~4.46s） |

MODE=1 下同样的故障：t0 + 230ms 判定过期，之后再过 58~131ms（取决于上次刷新在多久之前），约 t0 + 0.29~0.36s 复位。量出来的时刻落在预算区间外，就要怀疑时钟配置或调试器冻结（第七节）。

## 六、复位证据：先读后清，记录只信校验过的

**RCC_CSR 读后清。** `f407_reset_reason` 取 RCC+0x74 的高 7 位，然后写 RMVF（bit24）清除：

| 位 | 31 | 30 | 29 | 28 | 27 | 26 | 25 |
|---|---|---|---|---|---|---|---|
| 标志 | LPWRRSTF | WWDGRSTF | IWDGRSTF | SFTRSTF | PORRSTF | PINRSTF | BORRSTF |

标志不清除会一直累积，下一次复位时就分不清这次是哪个来源。也别把 RCC+0x74 写成别的偏移（比如把 AHB2ENR 当成复位原因读）。读出来的原值通过 STATUS 的"复位原因"字段原样交给主机。

注意：看门狗复位时 **PINRSTF 通常也会置位**。内部复位源会通过 NRST 引脚输出至少 20µs 的复位脉冲（RM0090 Rev 22 §7.1，第 215 页）。所以判断"是不是看门狗复位"要看 bit29/30，不能因为看到 PINRSTF 就认定是有人按了复位键。这块板上两个标志的实际组合待上板记录。

**`.noinit` 记录。** 链接脚本里有一个 `.noinit (NOLOAD)` 段，启动代码不清零它。supervisor 停止喂狗前写一条 12 字节记录：

| 偏移 | 内容 |
|---|---|
| 0..3 | magic `0x57444731`（小端，ASCII "1GDW"） |
| 4 | version = 1 |
| 5 | 保留，必须为 0 |
| 6..9 | mask：哪几个任务过期；0x80 表示监督被停止 |
| 10..11 | 对前 10 字节的 CRC-16（与 C8 同一个函数） |

写入顺序是"先作废、再写内容、最后写 magic"：

```c
for (unsigned i=0;i<4;i++) dst->bytes[i]=0;     /* 先清 magic：写到一半复位 = 无效记录 */
for (unsigned i=4;i<12;i++) dst->bytes[i]=b[i];
for (unsigned i=0;i<4;i++) dst->bytes[i]=b[i];  /* 最后发布 */
```

启动时 `fault_record_take` 只在 IWDGRSTF 或 WWDGRSTF 置位时才解读记录，读完立刻清掉 magic，防止以后某次无关的暖复位又把旧记录读出来。上电复位后 SRAM 是随机值，magic、version、CRC 三关都过不了，就报"没有有效记录"。这条记录只用于辅助诊断暖复位，不保证掉电保存。

HardFault 里同样不能"打印一下、喂一下狗"。栈可能已经坏了，这时候该做的是停住，让狗复位（[S16](16-debug-hardfault.md)）。工程里的栈溢出钩子就是关中断后死循环。

## 七、调试器与看门狗

内核被调试器停住时，IWDG/WWDG 是继续计数还是暂停，由 DBGMCU_APB1_FZ（0xE004 2008）的 DBG_IWDG_STOP（bit12）、DBG_WWDG_STOP（bit11）决定（RM0090 Rev 22 §38.16.4）。很多 IDE 和 OpenOCD 配置会在连接时把这两位置 1，断点停住时狗不会叫，方便调试。

麻烦在于：这个寄存器**只被上电复位清零**，普通的系统复位清不掉。调试会话结束后，冻结位可能还留着。这时测"卡死后会不会复位"，得到的"没复位"不代表代码对了。

所以复位实验的固定流程是：烧录 → 断开 ST-Link → 板子断电再上电 → 再发故障命令。

## 附录：工程完整源码

<<< ../../code/stm32/06-watchdog-health/main.c

## 记忆锚点

::: tip 一句话记住
**进展才喂狗，迟到就锁存；IWDG 管太晚，WWDG 还管太早；超时按最慢的 LSI 算，复位原因先读后清，冻结位只有断电才清。**
:::

## 实物实验

- **装备**：F407 板、ST-Link、3.3V USB-TTL；有示波器的话加一路接 NRST。
- **实验 1（IWDG 时间预算）**：`make MODE=0 FAULTS=1`，按第七节流程上电，执行 `fault --fault 1 --task 0`。记录主机发出命令到 NRST 出现低脉冲的时间，和第五节的 2.06~4.46s 对照。复位后 `status` 的复位原因应含 bit29。
- **实验 2（WWDG 两头）**：分别用 MODE=2 和 MODE=3 执行 `fault --fault 2`。两者复位原因都应含 bit30，区别在复位时刻：MODE=2 在生效（t0+200ms）后的下一轮监督里立刻复位，MODE=3 要等到上次刷新后约 131ms。
- **实验 3（冻结位）**：不断电，直接在调试会话结束后做实验 1，看是否能复位；再断电重做一遍对比。

## 实验记录

模型/编译验证不等于上板实测。当前待上板；请记录日期、板版本、固件版本、接线、输入、原始输出与结论。

| 日期 | 板卡/版本 | 故障输入 | 原始结果 | 结论 |
|---|---|---|---|---|
| 待实测 | | | | |

## 常见坑

- **定时中断里无条件喂狗**：只证明中断活着（第一节）。
- **调试器连着测复位**：冻结位让狗不叫，以为代码没问题。必须断电重来（第七节）。
- **按名义 LSI 算超时**：最快的 LSI 下 2 秒会变成 1.36 秒，正常喂狗的周期抖一下就误复位（第三节）。
- **IWDG 和 WWDG 用同一套期限**：WWDG 131ms 就复位，500ms 的任务期限永远来不及判定（第四节）。
- **复位标志不清**：标志累积，下一次复位分不清来源（第六节）。
- **故障处理里喂狗**：HardFault 或栈溢出钩子里"顺手喂一下"，等于把唯一能救场的复位关掉了。

## 短自测

1. 通信口一直没有数据，会触发看门狗吗？
<details><summary>参考答案</summary>不会。通信任务每轮做完一次有界的读取和发送推进就上报进展，"这一轮服务检查完成了"就是它的进展，不要求主机持续发数据。</details>

2. 传感器读数报错、或者收到 STOP 命令，要不要停止喂狗？
<details><summary>参考答案</summary>不要。只要任务还能处理这个错误并按期完成下一轮，系统就是健康的，重启解决不了传感器的问题。看门狗只处理"失去进展"，不处理"业务结果不好"。</details>

3. 用 RLR=999、/64，LSI 实际是 40kHz 时 IWDG 超时多少？
<details><summary>参考答案</summary>1000 × 64 / 40000 = 1.6 秒。所以说"2 秒"只是 32kHz 下的名义值。</details>

4. WWDG 模式下，如果 supervisor 每 1ms 轮询一次而不是 5ms，会出什么问题吗？
<details><summary>参考答案</summary>不会更早复位，因为 f407_wwdg_feed 只在 0x3F &lt; T &lt; 0x5F 时才写，窗口外的轮询直接返回 false。只是 CPU 开销变大，刷新时刻更靠近窗口打开的那一刻。</details>

## 对照表：本章概念 → 仓库与手册落点

| 概念 | 落点 |
|---|---|
| 进展、期限、锁存 | `code/common/reliability/health.c` |
| IWDG 四步与有界等待 | `code/stm32/platform/watchdog.h` `f407_iwdg_start()`；HAL v1.8.5 `HAL_IWDG_Init` |
| IWDG 超时表 | RM0090 Rev 22 第 705 页表 107；LSI 范围见 DS8626 Rev 12 第 105 页表 35 |
| WWDG 公式与窗口条件 | RM0090 Rev 22 第 710–711 页；`f407_wwdg_feed()` |
| 复位标志位 | CMSIS `stm32f407xx.h` `RCC_CSR_*RSTF`；`f407_reset_reason()` |
| 暖复位记录 | `code/common/reliability/record.c`；链接脚本 `.noinit (NOLOAD)` |
| 调试冻结 | RM0090 Rev 22 §38.16.4 DBGMCU_APB1_FZ |

## 延伸阅读

喂狗的方法论：

- **[\[D12\]](../reference/bibliography.md#papers)** Ganssle《Great Watchdog Timers for Embedded Systems》：为什么"主循环里定时喂狗"几乎等于没装狗，以及窗口看门狗（WWDG）的设计动机。

## 你做到了

- 喂狗从"定时做的一件事"变成"健康检查通过后的结论"；
- IWDG 超时能按 LSI 三档算出区间，WWDG 窗口能算到毫秒；
- 复位后能说清"是谁、因为哪个任务、在什么时候"让它复位的。

<div class="achievement">
✅ 下一站：<a href="../esp32/13-watchdog-health.html">P13 健康监督</a>：同一份 health 模块搬到 S3，看 TWDT 怎么替你管"谁该喂"。
</div>
