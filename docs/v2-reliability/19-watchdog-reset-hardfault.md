---
title: "看门狗、复位与 HardFault"
platforms: [f407, f103, esp32]
---

# 看门狗、复位与 HardFault

看门狗防的是"程序不再前进"，复位标志回答"这一次是谁让它重来"，HardFault 取证回答"它死在哪一行"。三件事都容易停在表面：灯又闪了、板子重启了、调试器里断下来了，都不等于你拿到了证据。

两个来源的实验记录仍是"待实测"，第三个来源的 274/274 是宿主 probe。本章把手册规则、公式推导、宿主断言与尚未上板的实验分开写；凡是没有读数的结论，都在原处标出来。

## 本章罗盘

- **问题**：IWDG 与 WWDG 的时间基准差在哪，为什么一只只罚"太晚"、另一只连"太早"也罚？超时公式里的 `(RLR+1)` 少写会差多少，LSI 的 30/60 kHz 与 17/47 kHz 又让同一个 RLR 差出几倍？WWDG 的 58.25 ms 与 131 ms 各自绑定了哪些条件？`RCC_CSR` 为什么必须一次读全再写 `RMVF`，POR 为什么会把 `PINRSTF` 一起置起来？复位记录怎样写到一半被打断也不误导下一次启动？HardFault 的 19 位 CFSR、`FORCED`、两个 VALID 位、32 字节栈帧与 `EXC_RETURN` 怎样串成一条到源码行的链？调试器为什么会把狗关掉、把现场改掉？ESP32 的四类狗里，哪一类能平移到 Cortex-M，哪一类不能？
- **交付**：能按 `t = (4·2^PR)·(RLR+1)/f_LSI` 给 F103 与 F407 各算一张"设计值/最坏值"表；能写出 IWDG 的 `0xCCCC → 0x5555 → PR/RLR → 0xAAAA` 序列并说清"启动后关不掉"；能按 `0x3F < T < W` 判断 WWDG 何时可以喂；能一次读全 `RCC_CSR` 的 bit31..25、写 `RMVF` 清标志，并按位图解释 POR 与 PINRSTF 的伴随关系；能用 `.noinit`、BKP 或 `RTC_NOINIT_ATTR` 写一条带 magic、版本、掩码与 CRC-16 的复位记录；能写 naked `HardFault_Handler`，从栈帧取 PC，交给 `addr2line`；能说出 F1 与 F4 的调试冻结位和 OpenOCD 的副作用；能解释 ESP32 的 TWDT 为什么是任务级契约。
- **边界**：三平台章。F103 的 LSI、IWDG 与复位位号来自 DS5319、RM0008 与根书第 11 章（来源转引）；F407 的 IWDG/WWDG 公式、`RCC_CSR` 与冻结位来自 DS8626、RM0090 与 S17；HardFault 的寄存器地图、CFSR 分区、栈帧与汇编来自 S16 与 ARMv7-M/CMSIS；ESP32 的四类狗、TWDT 与 `esp_reset_reason()` 来自 P13 与 IDF 5.5.2 文档。三个来源都没有留下上板读数：S17 与 P13 的实验表体是"待实测"，S16 的 274/274 是宿主 probe，没有板级故障现场；本工作树缺 `mcu/.trellis/ref/cmsis`，S16 的 CMSIS 逐位对账未复核。RTC 与备份域回链第 11 章，异常进入与优先级回链第 10 章，Flash 参数区回链第 17 章，调试工具与测量方法留给第 20 章。
- **依据锚点**：根书第 11 章《RTC 与看门狗》（`docs/11-RTC与看门狗.md`，只取看门狗段）、S16《HardFault 与排错》（`mcu/docs/stm32/16-debug-hardfault.md`）、S17《看门狗：任务失去进展之后》（`mcu/docs/stm32/17-watchdog-reset.md`）、P13《看门狗与健康监督》（`mcu/docs/esp32/13-watchdog-health.md`）；[第 11 章](../v1-drivers/11-systick-timebase-rtc.md)、[第 10 章](../v1-drivers/10-interrupts-nvic-exti.md)、[第 17 章](../v1-drivers/17-flash-iap-ota.md)、[第 18 章](./18-low-power.md)是本章的回链。RM0008、RM0090、DS5319、DS8626、ARM PM0214/PM0056 与 ESP-IDF 文档均转引自上述来源，本章没有取到原件逐页核对。

## 先做出来

先不接调试器，把三笔账算在纸上，再去板上读一次复位原因。

1. **超时账**：F407 取 /64、RLR=999，按 32 kHz 算 2.00 s；按 47 kHz 算 1.36 s，按 17 kHz 算 3.76 s。F103 取 /64、RLR=624，按 40 kHz 算 1.00 s；按 60 kHz 算 0.67 s，按 30 kHz 算 1.33 s。两个平台的"1 秒"不是同一个 RLR。
2. **窗口账**：F103 在 PCLK1=36 MHz、/8、T=0x7F 时，一拍 910.2 µs，64 拍 58.25 ms；W=0x50 时，从 0x7F 数到 0x50 要 47 拍（约 42.8 ms），按 `0x3F < T < W`，合法刷新区间是 `0x40 ≤ T < 0x50`。
3. **复位账**：读一次 `RCC->CSR`，把 bit31..25 原样记下来，再写 `RMVF`（bit24）清掉。POR 会同时置 `PORRSTF` 与 `PINRSTF`；看到 `PINRSTF` 就说"有人按了复位键"，会把电源上电认错。

三笔账都能用纸笔复算，不需要示波器。它们对上了，才轮到上板看真实复位时刻。

S16 的 `probe.sh` 可以在没有板子的机器上跑：第 1 段用宿主 gcc 与假寄存器执行断言，第 3、4 段用 `arm-none-eabi-` 工具链做反汇编、`addr2line` 与字节学。本章把该目录复制到临时目录重跑，得到 274/274；第 2 段的 CMSIS 逐位对账因本工作树缺 `mcu/.trellis/ref/cmsis` 而跳过，39 条位号"逐位一致"未复核。这是实测记录，但测的是宿主模型与机器码，不是板上的 HardFault 现场。

## 机制

### 一、两只狗：一只只罚太晚，一只早晚都罚

IWDG 的时钟是片内 LSI，和主时钟无关。主时钟跑飞、PLL 失锁、代码把系统时钟改坏，LSI 仍在数。代价是频率不准：F103 典型 40 kHz，数据手册给 30/60 kHz 两端；F407 典型 32 kHz，给 17/47 kHz 两端。同一个 RLR，在两颗芯片上的超时差 25%，在同一颗芯片的两端能差一倍以上。

WWDG 的时钟是 PCLK1，跟着 APB1 走。它准，但主时钟坏了它也会坏；它管的是"节奏"：喂得太晚复位，喂得太早也复位。两只狗可以同时开：IWDG 兜底"还活着"，WWDG 检查"这一圈是不是按顺序走完"。

| 项 | IWDG | WWDG |
| --- | --- | --- |
| 时钟 | LSI（独立） | PCLK1（APB1） |
| 计数 | 12 位递减 + 8 位预分频 | 7 位递减（`T[6:0]`） |
| 复位条件 | 减到 0 前没喂 | 喂早（`T > W`）或喂晚（`T < 0x40`） |
| 精度 | 差（LSI 容差大） | 好（跟随 PCLK1） |
| 低功耗 | Stop/Standby 下继续数 | 时钟停了就不数 |
| 调试冻结 | `DBG_IWDG_STOP` | `DBG_WWDG_STOP` |

IWDG 没有窗口，喂早不会复位；"喂狗有窗口"只属于 WWDG。把这条记反，排障时会往错误方向查。

![看门狗双雄：IWDG 只管活着，WWDG 还管节奏](/anim/watchdog-window.svg)

图中两条时间轴：IWDG 减到 0 才复位；WWDG 在窗口外刷新，无论早于 W 还是低于 0x40 都复位。

### 二、IWDG：0xCCCC → 0x5555 → 0xAAAA

IWDG 的启动顺序是固定的，少一步就写不进配置：

```c
IWDG->KR  = 0xCCCC;   /* 启动；LSI 自动打开，计数器按默认 /4 起跑 */
IWDG->KR  = 0x5555;   /* 解锁 PR/RLR */
IWDG->PR  = 4;        /* /64 */
IWDG->RLR = 999;      /* 1000 个计数 */
while (IWDG->SR & (IWDG_SR_PVU | IWDG_SR_RVU)) { }  /* 等 LSI 域同步；生产代码要加超时 */
IWDG->KR  = 0xAAAA;   /* 用新值重装，之后每次喂狗都写它 */
```

`0xCCCC` 一写下去，计数器就从复位值 `0xFFF`、按复位分频 /4 开始倒数，F407 约 512 ms（32 kHz），F103 约 410 ms（40 kHz）。后面的配置即使失败，狗也已经在跑，最终一定会复位。这是"先启动再配置"的理由。

PR 有 8 个编码，只有 7 档：0–6 是 /4、/8、/16、/32、/64、/128、/256，7 也是 /256。公式里的 `2^PR` 对 PR=7 不成立，写表时要么只列 0–6，要么单独注明 7 与 6 同档。

超时公式必须带 `(RLR+1)`：

```text
t = (4 × 2^PR) × (RLR + 1) / f_LSI
```

RLR 是重装值，计数器从 RLR 减到 0 一共 RLR+1 个计数。`14-pwr` 的超时表把 512 ms 写成 511 ms、把 32768 ms 写成 32760 ms，漏的就是这个 +1；同一份资料的另一处又写了 `(RLR+1)`，两种口径不能并存。本章一律按 +1 算。

| 平台 | PR | RLR | 设计值（典型 LSI） | 最坏值（LSI 区间） |
| --- | --- | --- | --- | --- |
| F103 | /4（默认） | 4095 | 0.410 s @40 kHz | 0.273–0.546 s（60/30 kHz） |
| F103 | /64 | 624 | 1.000 s @40 kHz | 0.667–1.333 s |
| F103 | /64 | 999 | 1.600 s @40 kHz | 1.067–2.133 s |
| F103 | /256 | 4095 | 26.214 s @40 kHz | 17.476–34.952 s |
| F407 | /4（默认） | 4095 | 0.512 s @32 kHz | 0.349–0.964 s（47/17 kHz） |
| F407 | /64 | 624 | 1.250 s @32 kHz | 0.851–2.353 s |
| F407 | /64 | 999 | 2.000 s @32 kHz | 1.362–3.765 s |
| F407 | /256 | 4095 | 32.768 s @32 kHz | 22.310–61.681 s |

设计时按最快 LSI 检查"正常喂狗来不来得及"，按最慢 LSI 检查"故障后多久才复位"。只按典型值算，47 kHz 的板子会把 2.00 s 变成 1.36 s；只留最慢值，又会把故障检测拖到 3.76 s。

IWDG 一旦启动，软件关不掉，只有复位能停。它在 Stop 和 Standby 下照样计数：用了 IWDG 再进低功耗，要把唤醒周期算进超时，否则睡过头就是一次看门狗复位。低功耗与唤醒源见[第 18 章](./18-low-power.md)。选项字节把 `WDG_SW` 写成 0 时，上电就由硬件启动看门狗，软件连"什么时候启动"都决定不了。

### 三、WWDG：窗口是 `0x3F < T < W`

WWDG 的计数器是 7 位，每个 `4096 × 2^WDGTB` 个 PCLK1 周期减一。刷新只能在 `0x3F < T < W` 时进行：`T > W` 刷新立刻复位，`T` 减到 `0x3F` 也复位。

```text
t_WWDG = t_PCLK1 × 4096 × 2^WDGTB × (T[5:0] + 1)
```

F103 的例子：PCLK1=36 MHz、WDGTB=3（/8）、T=0x7F。一拍 `4096×8/36 MHz = 910.2 µs`，`(0x7F & 0x3F) + 1 = 64` 拍，超时 58.25 ms。W=0x50 时，从 0x7F 数到 0x50 要 47 拍；第一个合法刷新点是 0x4F，约 43.7 ms 后。58.25 ms 离开"36 MHz、/8、T=0x7F"这三个条件就不成立。

F407 的例子：复位后不改时钟树，PCLK1=16 MHz、/8、T=0x7F。一拍 2.048 ms，64 拍 131 ms；W=0x5F 时，从 0x7F 数到 0x5E 要 33 拍（约 67.6 ms），之后才进窗口。131 ms 同样绑着"16 MHz、/8"；把 F103 的 36 MHz 数字搬到 F407，或者反过来，都是错数。

```c
RCC->APB1ENR |= RCC_APB1ENR_WWDGEN;
WWDG->CFR = (3U << 7) | 0x5FU;        /* WDGTB=3 → /8；W=0x5F */
WWDG->CR  = 0x7FU | WWDG_CR_WDGA;     /* T=0x7F，启动 */

uint32_t t = WWDG->CR & 0x7FU;
if (t > 0x3FU && t < 0x5FU) {
    WWDG->CR = 0x7FU | WWDG_CR_WDGA;  /* 只在窗口内重装 */
}
```

窗口外的轮询直接返回，不"为了保命"硬喂。喂早了会立刻复位，这一口不是保命，是催命。

![WWDG 的窗口与 IWDG 的底线](/figures/stm32-17-watchdog-reset.svg)

图中把 IWDG 的"减到 0"与 WWDG 的"两头死路"放在同一条时间轴上；窗口宽度由 W 决定，超时由 PCLK1、WDGTB 与 T 共同决定。

### 四、复位源是位图，不是枚举

`RCC_CSR` 的高 7 位是复位标志，bit24 是 `RMVF`。它们不是"最后一次复位原因"的枚举，而是一张可以多位同置的位图。

| 位 | 31 | 30 | 29 | 28 | 27 | 26 | 25 | 24 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 标志 | `LPWRRSTF` | `WWDGRSTF` | `IWDGRSTF` | `SFTRSTF` | `PORRSTF` | `PINRSTF` | `BORRSTF` | `RMVF` |

上电时 `PORRSTF` 置位，`PINRSTF` 也会一起置位：内部复位源会通过 NRST 引脚输出至少 20 µs 的复位脉冲，上电复位同样会把 NRST 拉低。所以"看到 `PINRSTF` 就是有人按了复位键"不成立；判断看门狗复位要看 bit29/30。

读的顺序是"一次读全，再清"：

```c
uint32_t csr = RCC->CSR;             /* 一次读全：多位可能同置 */
uint32_t flags = csr & 0xFE000000U;  /* bit31..25 */
RCC->CSR = RCC_CSR_RMVF;             /* 写 1 清全部标志 */
```

标志会累积，读完不写 `RMVF` 就一直留着，下一次复位分不清新旧；先读全再清，才能把同一次复位里同时置起的多位一起记下来。F407 的 `RCC_CSR` 在 `0x40023874`，F103 在 `0x40021024`；用 `RCC->CSR` 就不必记地址。

`LPWRRSTF` 与 `BORRSTF` 是电源侧的证据，`SFTRSTF` 是软件复位，`IWDGRSTF`/`WWDGRSTF` 才是两只狗。复位原因只说明哪一类源触发了复位，不告诉你"为什么"；后者要靠复位记录。

### 五、复位记录：magic、版本、掩码与 CRC-16

复位标志只保留"哪一类复位"，保留不了"哪个任务过期、第几次"。要跨复位留下一条可解释的记录，最省事的是 `.noinit`：链接脚本里给它一个 `NOLOAD` 段，启动代码不清零，暖复位后内容还在。

记录布局是 12 字节：

| 偏移 | 内容 |
| --- | --- |
| 0..3 | magic `0x57444731`（小端 ASCII "1GDW"），同时充当有效位 |
| 4 | version = 1 |
| 5 | 保留，必须为 0 |
| 6..9 | 有效掩码：哪几个任务过期；0x80 表示监督被停 |
| 10..11 | 前 10 字节的 CRC-16 |

写入顺序是"先清有效位、再写体、最后置有效位"：

```c
for (unsigned i = 0; i < 4; i++) dst->bytes[i] = 0;     /* 先清 magic：写到一半复位 = 无效记录 */
for (unsigned i = 4; i < 12; i++) dst->bytes[i] = body[i];
for (unsigned i = 0; i < 4; i++) dst->bytes[i] = body[i];  /* 最后发布 magic */
```

写到一半被复位，magic 不完整，记录就当不存在；体和 CRC 已经写完但 magic 还没发布，同样当不存在。启动时只在 `IWDGRSTF` 或 `WWDGRSTF` 置位时解读记录，读完立刻清掉 magic，防止下一次无关的暖复位把旧记录再报一遍。冷上电后 SRAM 内容不确定，magic、version、CRC 三关都过不了，报"没有有效记录"。

| 载体 | 扛得住 | 扛不住 | 容量与代价 |
| --- | --- | --- | --- |
| `.noinit`（SRAM） | 暖复位、看门狗复位 | 掉电、Standby 若 SRAM 失电 | 12 字节；要改链接脚本与启动代码 |
| BKP（备份寄存器） | 复位、Standby，VBAT 有电时掉主电也能留 | VBAT 也掉电 | F103 10×16 bit；F407 20×32 bit；12 字节在 F103 上要占 6 个寄存器 |
| `RTC_NOINIT_ATTR`（ESP32） | 软件复位、看门狗复位、Deep sleep | 冷上电（内容不确定） | RTC 内存；同样要 magic/版本/CRC 三关 |

F103 与 F407 的备份域写法、VBAT 与 BKP 容量见[第 11 章](../v1-drivers/11-systick-timebase-rtc.md)。如果记录要落 Flash 参数区，擦写寿命与掉电保护是另一套规则，见[第 17 章](../v1-drivers/17-flash-iap-ota.md)；本章不重讲 Flash 编程时序。

![复位闭环：故障、超时、复位原因与重启记录必须对得上](/figures/watchdog-reset-evidence.svg)

灯重新闪只证明"重启了"；要证明"是 IWDG 让它重启"，得让 `IWDGRSTF`、复位记录与故障注入的时间线互相对上。

### 六、HardFault：从 CFSR 到源码行

HardFault 是异常升级的终点。MemManage、BusFault、UsageFault 没使能或处理不当时，会升级成 HardFault；`HFSR.FORCED`（bit30）置位说明"这是升级案，真凶在 CFSR 里"。三个可配置故障的使能位在 `SHCSR`：`MEMFAULTENA`(16)、`BUSFAULTENA`(17)、`USGFAULTENA`(18)。异常进入、优先级与向量表的机制见[第 10 章](../v1-drivers/10-interrupts-nvic-exti.md)；本节只讲取证。

故障寄存器都挂在 `SCB`（基址 `0xE000ED00`）下：

| 寄存器 | 地址 | 用途 |
| --- | --- | --- |
| `SHCSR` | `0xE000ED24` | 三个故障使能位 |
| `CFSR` | `0xE000ED28` | 19 位，逐位点名死因 |
| `HFSR` | `0xE000ED2C` | 3 位，定性 |
| `MMFAR` | `0xE000ED34` | 存储管理故障地址 |
| `BFAR` | `0xE000ED38` | 总线故障地址 |

CFSR 是三个子寄存器拼成的：低 8 位 MMFSR、次 8 位 BFSR、高 16 位 UFSR。19 个位里，两个是"地址有效性位"：

| 子寄存器 | 位 | 名字 | 含义 |
| --- | --- | --- | --- |
| MMFSR | 0 | `IACCVIOL` | 取指越权 |
| MMFSR | 1 | `DACCVIOL` | 访存越权 |
| MMFSR | 3 | `MUNSTKERR` | 出栈时存储管理错 |
| MMFSR | 4 | `MSTKERR` | 入栈时存储管理错 |
| MMFSR | 5 | `MLSPERR` | 懒浮点保存时出错 |
| MMFSR | 7 | `MMARVALID` | MMFAR 可信 |
| BFSR | 8 | `IBUSERR` | 取指总线错 |
| BFSR | 9 | `PRECISERR` | 精确总线错，地址就是 BFAR |
| BFSR | 10 | `IMPRECISERR` | 不精确总线错，PC 与地址都不可靠 |
| BFSR | 11 | `UNSTKERR` | 出栈时总线错 |
| BFSR | 12 | `STKERR` | 入栈时总线错 |
| BFSR | 13 | `LSPERR` | 懒浮点保存时总线错 |
| BFSR | 15 | `BFARVALID` | BFAR 可信 |
| UFSR | 16 | `UNDEFINSTR` | 未定义指令 |
| UFSR | 17 | `INVSTATE` | 非法状态（Thumb 位丢了） |
| UFSR | 18 | `INVPC` | 非法 PC |
| UFSR | 19 | `NOCP` | 用了没开的协处理器 |
| UFSR | 24 | `UNALIGNED` | 未对齐访问 |
| UFSR | 25 | `DIVBYZERO` | 除以零 |

`MMFAR`/`BFAR` 里的地址不是永远可信：只有 `MMARVALID`/`BFARVALID` 为 1 时才对得上。`IMPRECISERR` 下总线写是缓冲的，出错时 PC 可能已经跑远；`STKERR`/`MSTKERR` 表示入栈本身就错了，`UNSTKERR`/`MUNSTKERR` 表示出栈错了，这两种情况下硬件压的那 8 个字可能不完整，不能直接解引用。

![CFSR 的 19 个位：三个子寄存器、两个 VALID 位，真凶在 HFSR.FORCED 后面](/figures/stm32-16-cfsr-bits.svg)

异常进入时，硬件把 8 个寄存器压进当前栈，共 32 字节：

```text
偏移  0 / 4 / 8 / 12 = r0–r3
偏移 16 = r12
偏移 20 = lr
偏移 24 = pc      ← 案发时正在执行的指令
偏移 28 = xpsr
```

PC 在 `sp[6]`，也就是 `((uint32_t *)sp)[6]`。案发时用的是 MSP 还是 PSP，藏在 `EXC_RETURN` 的 bit2 里：bit2=0 用 MSP，bit2=1 用 PSP。0xFFFFFFF1/0xFFFFFFF9 是 MSP，0xFFFFFFFD 是 PSP；带 FPU 上下文的 0xFFFFFFE1/E9/ED 只在 M4F/M7F 出现，M3 没有。拿错栈指针，读出来的 8 个字全是垃圾，后面所有推断都是假的。

Handler 用 `naked` 属性自己选栈，别让编译器插桩：

```c
__attribute__((naked)) void HardFault_Handler(void)
{
    __asm volatile(
        "tst   lr, #4              \n"  /* bit2 决定 MSP/PSP */
        "ite   eq                  \n"
        "mrseq r0, msp             \n"
        "mrsne r0, psp             \n"
        "b     hardfault_report    \n"  /* r0 就是栈帧指针 */
    );
}
```

交叉编译后的机器码是 `f01e 0f04`（`tst.w lr,#4`）、`bf0c`（`ite eq`）、`f3ef 8008`（`mrseq r0,msp`）、`f3ef 8009`（`mrsne r0,psp`）。`mrs` 的条件不在自己身上，而在 `ite` 那个词里：同样取 MSP，`mrseq r0,msp` 与 `mrsne r0,msp` 的机器码完全相同（都是 `f3ef 8008`），条件只由 `ite` 决定；把源寄存器换成 PSP 只改 imm5 的 bit0（MSP=0x08、PSP=0x09）。把 ne 槽写成 `msp`，整段只改一个字节，工具链照收，语义整个反了。

C 侧只搬现场，不打印、不喂狗：

```c
void hardfault_report(uint32_t *sp)
{
    g_cfsr  = SCB->CFSR;
    g_hfsr  = SCB->HFSR;
    g_mmfar = SCB->MMFAR;
    g_bfar  = SCB->BFAR;
    g_lr    = sp[5];
    g_pc    = sp[6];
    g_xpsr  = sp[7];
    for (;;) { }   /* 等调试器来读；printf 可能二次故障，把现场也毁掉 */
}
```

拿到 PC 之后用 `addr2line` 对源码行：

```bash
arm-none-eabi-addr2line -e build/firmware.elf 0x0800008E
```

`nm` 给的函数入口不是案发 PC。S16 的宿主 probe 里：`crash_null` 入口 `0x08000084` 对到 `fault_ctx.c:69`（函数体的 `{`），反汇编找出的出错指令 `0x0800008e` 对到 `fault_ctx.c:70` 的空指针写。差 10 个字节，差一行；拿入口地址去凑，会把"真凶"指到函数开头。`addr2line` 能查到行的前提是编译带 `-g3`，优化版本优先 `-O0`/`-Og`；`-O2` 会重排指令，行号可能对不上。

除零与未对齐不会默认崩：`CCR.DIV_0_TRP`（bit4）与 `CCR.UNALIGN_TRP`（bit3）不开时，`SDIV` 返回 0、普通单字 LDR/STR 的未对齐访问由硬件兜住，程序继续跑，只是结果悄悄错了。`SCB->CCR` 在 `0xE000ED14`。

![HardFault 取证全流程：CFSR 定性、VALID 取址、栈帧取 PC、addr2line 对行](/anim/hardfault-forensics.svg)

流水线的每一步都有失效条件：CFSR 可能只说明"升级了"，VALID 位为 0 时地址不可信，栈帧可能不完整，`-O2` 下行号可能漂移。

### 七、调试器会把故障现场改掉

调试器连着时，内核被停住，看门狗是否继续数由 `DBGMCU` 的冻结位决定。F1 的惯用位号是 `DBGMCU_CR` 的 bit8（IWDG）与 bit9（WWDG）；F4 是 `DBGMCU_APB1_FZ`（`0xE0042008`）的 bit11（WWDG）与 bit12（IWDG）。调试器的启动脚本常把这两位置 1，断点停住时狗不叫。

```c
/* F1 */
DBGMCU->CR |= (1U << 8) | (1U << 9);
/* F4 */
DBGMCU->APB1FZ |= (1U << 11) | (1U << 12);
```

HAL 的 `__HAL_DBGMCU_FREEZE_IWDG()` 与 `__HAL_DBGMCU_FREEZE_WWDG()` 会按系列选寄存器。麻烦在于冻结位属于调试域，普通系统复位不保证清掉：F4 的 `DBGMCU_APB1_FZ` 明确只被上电复位清零。调试会话结束后直接测"卡死后会不会复位"，得到的"没复位"不代表代码对了。

ESP32 侧的副作用更直接：OpenOCD 在断点处会关掉 IWDT 与 TWDT 的硬件定时器，离开断点后也不会再打开。只要通过 JTAG 连过 OpenOCD，这两只狗就等于没装。

复位实验的固定流程是：烧录、断开调试器、板子断电再上电、再发故障命令。"调试下从不复位"是假阴性，不是证据。调试链路与工具侧细节留给第 20 章。

### 八、ESP32：四类狗与任务级契约

ESP32 没有 STM32 的 IWDG/WWDG 这对组合，它把监督拆成四类：

| 看门狗 | 监督什么 | 谁喂 |
| --- | --- | --- |
| RTC_WDT | 上电到 `app_main` 之前的启动过程 | 引导代码；默认在进入用户主函数前关闭 |
| IWDT（中断看门狗） | 中断是否被长时间屏蔽、ISR 是否跑太久 | 每个核的 FreeRTOS tick 中断 |
| TWDT（任务看门狗） | 订阅的任务/用户是否在期限内报到 | 被订阅者自己调 `reset`/`reset_user` |
| XTWDT | 外部 32 kHz 晶振是否停振 | 硬件 |

TWDT 不是"往一个键值寄存器写 0xAAAA"。它是任务级契约：被订阅者必须在期限内报到，超时后按配置打印回溯或进入 panic。默认的 TWDT 只订阅每个核的空闲任务，能发现"有人霸占 CPU 不让出"，发现不了"任务按时让出 CPU、却一直没完成工作"。

```c
esp_task_wdt_config_t cfg = {
    .timeout_ms = 2000,
    .idle_core_mask = 0x3,      /* S3 双核：两个空闲任务都订阅 */
    .trigger_panic = true,      /* 默认 false 只打印警告，程序继续跑 */
};
esp_err_t err = esp_task_wdt_init(&cfg);
if (err == ESP_ERR_INVALID_STATE) {
    err = esp_task_wdt_reconfigure(&cfg);   /* IDF 启动时已初始化过 */
}
ESP_ERROR_CHECK(err);
ESP_ERROR_CHECK(esp_task_wdt_add_user("health", &health_user));
```

监督任务判定通过才 `esp_task_wdt_reset_user(health_user)`；判定失败就停止喂，但不要把 user 删掉。删掉 user，TWDT 就不再等它，超时来源没了，系统反而不复位。监督任务自己卡死时也要有一个没人刷新的超时来源，所以 health user 由监督任务单独注册。

三个任务可能落在两个核上，共享状态要用 `portMUX` 自旋锁保护。时间戳必须在锁内读：先读时间再拿锁，另一个核可能在这中间写入更晚的 `last`，无符号减法回绕成一个大数，误判过期。`esp_task_wdt_reset_user` 有自己的锁，放在临界区外调用。

复位后先读 `esp_reset_reason()`，只在 `ESP_RST_TASK_WDT`、`ESP_RST_INT_WDT`、`ESP_RST_PANIC` 这几类暖复位时才去信 `RTC_NOINIT_ATTR` 里的记录。`RTC_NOINIT_ATTR` 不初始化，冷上电后内容不确定，magic、版本、CRC 三关都要过；读完同样把 magic 清掉。TWDT 触发 panic 后到底报 `ESP_RST_TASK_WDT` 还是 `ESP_RST_PANIC`，日志里的原始值待上板记录；代码对两种都接受。

HardFault 是 Cortex-M 的概念。ESP32 没有 CFSR、HFSR、MMFAR/BFAR，也没有 `EXC_RETURN` 和 32 字节栈帧；它只有 panic 与 backtrace。"把 IWDG 的键值序列搬到 ESP32"或"在 ESP32 上读 CFSR"都是把两套模型硬拼在一起，不能这么写。

![ESP32 TWDT：订阅、进展上报、监督判定与 reset_user 的链条](/anim/esp32-twdt-chain.svg)

图中链条断在哪一环，超时就从哪里开始倒数；TWDT 只认"有没有人 reset"，不认"任务是不是忙"。

## 测量与证据

本章的读数按来路分四类：实测记录、来源说法(未复核)、文档推导、未实测。下表逐项标出来路；没有一条是本章的上板读数。

### 读数来路表

| 取证项 | 来路 | 读数或结论 | 性质 |
| --- | --- | --- | --- |
| IWDG 超时账 | 本章按 `(4·2^PR)·(RLR+1)/f_LSI` 复算；LSI 取 DS5319 与 DS8626 的范围 | RLR=999、/64：F407 2.000 s（32 kHz）、1.362–3.765 s（47/17 kHz）；F103 1.600 s（40 kHz）、1.067–2.133 s | 文档推导 |
| LSI 频率范围 | DS5319 表 25（F103 30/40/60 kHz）、DS8626 表 35（F407 17/32/47 kHz），经根书第 11 章与 S17 转引，未核原件 | 两颗芯片的典型值与两端 | 来源说法(未复核) |
| WWDG 58.25 ms | 本章按 4096×8/36 MHz×64 复算；条件 PCLK1=36 MHz、/8、T=0x7F | 910.2 µs/拍；58.25 ms | 文档推导 |
| WWDG 131 ms | 本章按 4096×8/16 MHz×64 复算；条件 PCLK1=16 MHz、/8、T=0x7F | 2.048 ms/拍；131 ms | 文档推导 |
| RCC_CSR 位图 | RM0008/RM0090 的 RCC 章，经根书第 11 章与 S17 转引，未核原件 | bit31..25 七类标志 + RMVF bit24；POR 伴随 PINRSTF；内部复位拉 NRST ≥20 µs | 文档推导 |
| 复位记录格式 | S17 `record.c` 与 `.noinit (NOLOAD)` 链接脚本（设计常量） | magic 0x57444731、版本 1、掩码、CRC-16；写序三句 | 文档推导 |
| HardFault 寄存器与栈帧 | S16 `probe.c`/`fault_ctx.c` 与 ARMv7-M/CMSIS 规则 | CFSR 19 位、PC@24、EXC_RETURN bit2、栈帧 32 字节 | 文档推导 |
| S16 宿主 probe | `sh probe.sh` 第 1/3/4 段；本工作树复制到临时目录重跑，gcc 16.1.0 + arm-none-eabi 10.3 | 274/274（宿主断言）；第 3/4 段附反汇编与 addr2line | 实测记录 |
| S16 CMSIS 逐位对账 | `probe.sh` 第 2 段；本工作树缺 `mcu/.trellis/ref/cmsis` | 39 条位号逐位一致未复核 | 来源说法(未复核) |
| S16 板级故障现场 | S16 实物实验（空指针、未对齐、除零） | 未记录 `CFSR` 与 `addr2line` 原始输出 | 未实测 |
| S17 实验记录 | `17-watchdog` 实验记录表，表体「待实测」 | 无读数 | 未实测 |
| P13 实验记录 | `13-watchdog` 实验记录表，表体「待实测」 | 无读数 | 未实测 |
| ESP32 TWDT 时间线 | P13 按 2000 ms 超时、500 ms 期限、1000 ms 宽限期推的模型 | worker 过期约 t0+2.6–2.8 s；监督自停约 t0+2.15–2.25 s | 文档推导 |
| 调试冻结位 | S17 第七节、根书第 11 章；F4 的 bit11/12 来自 RM0090 §38.16.4 转引；F1 的 bit8/9 未核 RM0008 原件 | IWDG/WWDG 各一位；F4 只被上电复位清零 | 来源说法(未复核) |
| 本章台架 | 实验设计尚未执行 | 待实测 | 未实测 |

能互相对上的只有手册位、算术与机器码：2.000 s 是 1000×64/32000 算出来的，58.25 ms 是 4096×8×64/36e6 算出来的，`f3ef 8009` 是从交叉编译输出里读出来的。它们都不能证明某块板上的 LSI 真是 32 kHz，也不能证明某次 HardFault 真的抓到了 PC。要补上后者，得按下面的台架留下复位时刻、`RCC_CSR` 原值与故障现场。

### 待做台架

1. **IWDG 时间预算**：F407 用 `fault` 停掉 worker，记录命令到 NRST 低脉冲的时间，与 2.06–4.46 s 的预算对照；F103 用 RLR=624 做同样的实验，记录 0.67–1.33 s。两种板子都要记 LSI 实测值。
2. **WWDG 两头**：分别制造喂早与喂晚，确认两次都复位、复位原因都含 bit30，并记录复位时刻的差别。
3. **复位原因与记录**：故意上电、按复位键、看门狗复位、软件复位各一次，记录 `RCC_CSR` 原值与复位记录的回放；确认 POR 时 `PINRSTF` 的伴随关系。
4. **HardFault 现场**：在 F407 上触发空指针写与栈溢出，记录 `CFSR`、`HFSR`、`BFAR`、栈帧 PC 与 `addr2line` 行号；在 RTOS 任务里再触发一次，确认 `EXC_RETURN` 的 bit2。
5. **ESP32 TWDT**：故障固件下分别停 worker 与停监督，记录 panic 时刻、`esp_reset_reason()` 原始值与 `RTC_NOINIT_ATTR` 记录。

这些台架都还没做。没有读数之前，本章只给判据与记录方法。

| 日期 | 平台/板卡 | 故障输入 | 原始结果 | 结论 |
| --- | --- | --- | --- | --- |
| 待实测 | F407 | 停 worker | | |
| 待实测 | F103 | 停喂 IWDG | | |
| 待实测 | ESP32-S3 | 停 worker / 停监督 | | |

## 失败分支

| 现象 | 原因 | 区分证据 | 下一动作 |
| --- | --- | --- | --- |
| 超时比算的短 | LSI 跑在 47 kHz（或 60 kHz）而不是典型值 | 按最坏值重算；读回 PR/RLR | 按最快 LSI 留喂狗余量 |
| F103 的 1 秒配方搬到 F407 变成 1.25 s | LSI 40 kHz 与 32 kHz 不同 | 同一 RLR 在两颗芯片上的账 | 按目标芯片重算 RLR |
| 超时表比实测少 1 ms/8 ms | 漏了 `(RLR+1)` | 512 ms 写成 511 ms、32768 ms 写成 32760 ms | 公式补 +1 |
| IWDG 一上电就复位 | `WDG_SW=0` 的硬件狗先跑，软件还没配置 | 读选项字节；复位发生在初始化之前 | 上电后尽早解锁配置并喂狗，或把 `WDG_SW` 改回 1 |
| 写完 PR/RLR 不生效 | 没先写 `0x5555` 解锁，或没等 PVU/RVU | 读回 PR/RLR 与写入不符；SR 的 PVU/RVU 仍为 1 | 按 `0xCCCC→0x5555→写→0xAAAA` 重来 |
| WWDG 一喂就复位 | `T > W`，喂早了 | 读 `WWDG->CR` 的 T 与 CFR 的 W | 等 `T < W` 再喂 |
| WWDG 永远不复位 | 没开 WWDGEN 或没置 WDGA | 读回 CR/CFR；看 APB1ENR | 开时钟、置 WDGA、在窗口内重装 |
| 看到 `PINRSTF` 就以为按了复位键 | POR 与内部复位都会拉 NRST | 同一次读到的 `PORRSTF`/`IWDGRSTF` | 一次读全，按位图判断 |
| 复位原因越积越多 | 没写 `RMVF` | 读到的标志多于本次复位 | 读全后写 `RCC_CSR_RMVF` |
| 复位记录的 CRC 总不对 | 先写 magic 后写体，或写到一半复位 | magic 对但 CRC 错；或 magic 本身不完整 | 先清 magic，最后发布 |
| 复位记录读到上一次的旧内容 | 读完没清 magic | magic 一直是 `0x57444731` | 读完立刻清 magic |
| HardFault 读出的 PC 是垃圾 | 拿错 MSP/PSP，或 `STKERR`/`MSTKERR` 压栈不完整 | `EXC_RETURN` bit2 与 CFSR 的 STKERR 位 | 按 bit2 选栈；栈错时不硬解帧 |
| `addr2line` 报 `??:0` | 没带 `-g3`，或用了 `-O2` 后行号漂移 | ELF 里没有调试段；反汇编与源码对不上 | 调试版本用 `-O0 -g3` |
| 把函数入口当案发 PC | `nm` 给的是入口，栈里是出错指令 | 两个地址差几个字节、行号差一行 | 从反汇编找出错指令地址 |
| 除零/未对齐不崩 | `CCR` 的两个 trap 位没开 | `SDIV` 返回 0；普通单字未对齐访问被硬件兜住 | 需要复现时开 `DIV_0_TRP`/`UNALIGN_TRP` |
| 调试时从不复位 | 冻结位或 OpenOCD 把狗关了 | 断电重上电后同样的实验会复位 | 烧录→断开→断电重上电 |
| ESP32 TWDT 超时只打印不复位 | `trigger_panic=false` | 日志有警告，程序继续跑 | 置 `trigger_panic=true` |
| ESP32 停监督后反而永不复位 | 把 user `delete` 了 | TWDT 不再等这个 user | 保留 user，只是不再 reset |
| ESP32 冷上电读到脏记录 | 只查了 magic，没查复位原因 | `esp_reset_reason()` 是 `ESP_RST_POWERON` | 先按复位原因过滤，再验 CRC |

## 跨平台边界

同一个"看门狗 + 复位 + 故障"在三颗芯片上的落点不同，代码与数字都不能平移。

| 维度 | F103 | F407 | ESP32 |
| --- | --- | --- | --- |
| 低速时钟 | LSI 40 kHz（30/60） | LSI 32 kHz（17/47） | RTC 慢时钟（RC 或晶振，按型号） |
| IWDG | 12 位 + 8 位预分频，键值序列相同 | 同左 | IWDT 由 IDF 封装，语义不同 |
| 第二只狗 | WWDG（PCLK1） | WWDG（PCLK1，例中 16 MHz） | TWDT + RTC_WDT + XTWDT |
| 复位标志 | `RCC_CSR` bit31..25 | 同左 | `esp_reset_reason()` 枚举 |
| 现场保存 | BKP 10×16 bit + `.noinit` | BKP 20×32 bit + 4 KB BKPSRAM + `.noinit` | `RTC_NOINIT_ATTR` |
| 调试冻结 | `DBGMCU_CR` bit8/9 | `DBGMCU_APB1_FZ` bit11/12 | OpenOCD 关 IWDT/TWDT |
| 故障取证 | CFSR/HFSR/MMFAR/BFAR（M3） | 同左 + FPU 扩展栈帧 | panic + backtrace，无 CFSR |
| 超时基准 | `t=(4·2^PR)·(RLR+1)/f_LSI` | 同左，f_LSI 不同 | TWDT 一个全局 `timeout_ms` |

F103 没有 FPU 扩展栈帧，`EXC_RETURN` 只有 F1/F9/FD 三个值；F407 的 M4F 多出 E1/E9/ED，栈帧可能更长。F103 的 LSI 是 40 kHz、F407 是 32 kHz，同一个 RLR 的超时差 25%；WWDG 的 58.25 ms 与 131 ms 也各自绑着不同的 PCLK1。ESP32 的 TWDT 是任务级契约，不是"写 0xAAAA"；它的 IWDT 管中断，不负责"任务有没有交结果"。

换芯片先查对应 RM/DS 的 IWDG/WWDG、RCC 与 DBGMCU 章，再看备份域容量与调试冻结位。RTC 与备份域的写法见[第 11 章](../v1-drivers/11-systick-timebase-rtc.md)，异常进入与优先级见[第 10 章](../v1-drivers/10-interrupts-nvic-exti.md)，Flash 参数区见[第 17 章](../v1-drivers/17-flash-iap-ota.md)，低功耗下的 IWDG 计数见[第 18 章](./18-low-power.md)。

## 离开检查

1. IWDG 的超时公式是什么？RLR=999、/64、LSI=32 kHz 时是多少？LSI 换成 17/47 kHz 后区间是多少？
2. 为什么 `14-pwr` 的 511…32760 ms 表是错的？正确的两端是多少？
3. F103 与 F407 的 LSI 典型值各是多少？同一个 RLR=624、/64 在两颗芯片上的设计值各是多少？
4. WWDG 的 58.25 ms 绑定了哪三个条件？F407 的 131 ms 又绑定了什么？
5. IWDG 有喂狗窗口吗？WWDG 的合法刷新区间怎么写？
6. 为什么 `RCC_CSR` 要先一次读全再清？POR 与 `PINRSTF` 是什么关系？
7. 复位记录的 12 个字节怎么排？写序为什么是"先清有效位、最后置有效位"？
8. HardFault 的栈帧有多大？PC 在哪个偏移？`EXC_RETURN` 的 bit2 怎么选 MSP/PSP？
9. `IMPRECISERR` 与 `STKERR` 各会让哪一步取证失效？
10. 调试器怎样制造"从不复位"的假阴性？F1 与 F4 的冻结位分别在哪？
11. ESP32 的四类狗各管什么？TWDT 为什么不是"写键值寄存器"？

<details>
<summary>对照答案</summary>

1. `t=(4·2^PR)·(RLR+1)/f_LSI`。RLR=999、/64、32 kHz：1000×64/32000=2.000 s；47 kHz 为 1.362 s，17 kHz 为 3.765 s。
2. 漏了 `(RLR+1)`：512 ms 被写成 511 ms，32768 ms 被写成 32760 ms。正确两端是 512 ms 与 32768 ms（32 kHz、RLR=4095）。
3. F103 典型 40 kHz（30/60），F407 典型 32 kHz（17/47）。RLR=624、/64：F103 是 625×64/40000=1.000 s；F407 是 625×64/32000=1.250 s。
4. 58.25 ms 绑定 PCLK1=36 MHz、WDGTB=3（/8）、T=0x7F；131 ms 绑定 PCLK1=16 MHz、/8、T=0x7F。
5. IWDG 没有窗口，喂早不复位；WWDG 只在 `0x3F < T < W` 时允许刷新，T 减到 0x3F 也复位。
6. 标志可以多位同置，也会跨复位累积；先读全再清，才能把同一次复位的多位一起记下来，也不会把没读到的位清掉。POR 会同时置 `PORRSTF` 与 `PINRSTF`，所以看到 `PINRSTF` 不能断定有人按了复位键。
7. 0..3 magic（`0x57444731`，兼作有效位）、4 版本、5 保留、6..9 掩码、10..11 CRC-16。先清 magic，写到一半复位就是无效记录；体和 CRC 写完后再发布 magic，读方一次就能判断记录是否完整。
8. 32 字节；PC 在偏移 24（`sp[6]`）。`EXC_RETURN` bit2=0 用 MSP，bit2=1 用 PSP。
9. `IMPRECISERR` 下总线写是缓冲的，PC 可能已经跑远，栈帧里的 PC 不可靠；`STKERR`/`MSTKERR` 表示入栈出错，`UNSTKERR`/`MUNSTKERR` 表示出栈出错，硬件压的 8 个字可能不完整，不能直接解引用。
10. 冻结位让狗在断点停住时不数，OpenOCD 还会直接关掉 IWDT/TWDT；F1 在 `DBGMCU_CR` bit8/9，F4 在 `DBGMCU_APB1_FZ` bit11/12。复位实验要烧录、断开调试器、断电重上电。
11. RTC_WDT 管启动，IWDT 管中断，TWDT 管任务/用户是否在期限内报到，XTWDT 管外部 32 kHz 晶振。TWDT 是任务级契约：订阅者要主动 `reset`/`reset_user`，超时后打印回溯或 panic，没有"写 0xAAAA"这种键值序列。

</details>
