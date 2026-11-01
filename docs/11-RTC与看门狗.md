# 11 RTC 与看门狗

> English: [RTC and the watchdog](en/11-rtc-watchdog.md)

> RTC 提供掉电仍走时的日历时钟，独立/窗口看门狗保证程序跑飞后能自动复位，是产品可靠性的两大基石。

<p align="center">
  <img src="../assets/animations/iwdg-window.svg" width="760" alt="独立看门狗计数与喂狗窗口动画">
  <br><sub>▲ 辅图。独立看门狗只惩罚喂晚。喂早也复位的是窗口看门狗。不播放这张图时，1 秒和减到 0 才复位都在静态主图上。（作者自绘矢量动画，非实拍）</sub>
</p>

<!-- video:ch11 -->
<p align="center">
  <video width="640" controls poster="../assets/video/ch11-rtc.png">
    <source src="../assets/video/ch11-rtc.mp4" type="video/mp4">
  </video>
  <br><sub>▲ 本章讲解视频（2.6 分钟）。<a href="../assets/video/ch11-rtc.mp4">MP4</a> · <a href="../assets/video/ch11-rtc.srt">字幕</a></sub>
</p>

<details>
<summary>旁白文字稿</summary>

1. RTC 住在备份域。主电源掉了，只要备用电池和低速晶振还在，日历就能继续走。时钟源优先选外部 32.768 千赫，它比内部低速时钟准。
2. 备份域默认不让你随便写。要先允许访问，再选时钟、设分频。写不进去的时候，多半不是晶振坏了，而是域还锁着，或者写保护没解。
3. 独立看门狗的时钟独立，喂晚了就复位，用来兜底。窗口看门狗喂早喂晚都会复位，用来发现程序走得太快或太慢。两只可以同时在岗。
4. 这一帧是仓库画的看门狗窗口。太早喂，说明程序没有走到该到的地方；太晚喂，说明它卡住了。窗口看门狗把这两种都当成故障。独立看门狗只惩罚迟到。
5. 32.768 千赫晶振起振慢，初始化超时给得太短，会误判失败。真的不起振，再查负载电容和焊接。调试阶段可以暂时改用内部低速时钟，先把日历逻辑跑通。
6. 把喂狗放在一个和业务无关的定时中断里，主循环死锁时狗仍然吃得饱，等于没养。喂狗要放在你确认「这一圈真的走完了」的地方，并且落在窗口里面。
7. 芯片为什么重启，复位标志里有记录。独立看门狗、窗口看门狗、上电，是不同的旗。读完记得清掉，不然下一次你分不清是新的复位还是旧旗。
8. 口诀：独立看门狗只怕喂晚；窗口看门狗喂早喂晚都会复位。RTC 走在备份域，主电掉了还靠备用电池和低速钟。
9. 实验先故意不喂狗，确认它真的会复位，并且复位旗对得上。然后再把喂狗放到主循环里正确的位置。从没被咬过的狗，你不知道它在不在岗。
10. 合上书，三问。主电源掉了，RTC 还靠什么继续走？哪只看门狗喂早了也会复位？为什么不要把喂狗只放在一个无关的定时中断里？

</details>
<!-- /video:ch11 -->

## 学习目标

读这一章之前：知道二进制、十六进制和 `volatile` 是什么意思（不熟的话先读第 00 章的「零基础预备」），会用第 03 章的方法点亮 PC13 的灯，知道第 02 章里 LSI、LSE、HSE 和 PCLK1 是哪几路时钟，知道第 04 章讲的中断服务函数是什么。

- [ ] 说出 RTC 的三种时钟源，并说明为什么只有 LSE 能在主电源掉电以后靠 VBAT 接着走时
- [ ] 算出 32.768 kHz 下 PRL 要写 32767 才是 1 Hz，以及停在复位值 0x8000 时每天慢约 2.64 s
- [ ] 用备份寄存器存「已经设过时间」的记号和当天日期，按复位键以后日期不回到 2000-01-01
- [ ] 设一个每天 08:30 的闹钟，每次响过以后重新设到明天
- [ ] 用 T = 预分频 ÷ f_LSI × (Reload + 1) 算独立看门狗的超时，并按 LSI 30–60 kHz 的范围留余量
- [ ] 在 PCLK1 = 36 MHz、预分频 8、初值 0x7F、窗口 0x50 下，算出窗口看门狗允许喂狗的时间段
- [ ] 读 RCC_CSR 的复位标志判断芯片为什么重启，调试时把两只看门狗冻住

## 核心原理

**一句话结论：STM32F103 的 RTC（Real-Time Clock，实时时钟）是一只由备用电池供电的秒计数器，32.768 kHz 的 LSE 配 PRL = 32767，正好每秒加 1；看门狗是一只要按时「喂」的倒数计数器，数到底就让芯片复位。独立看门狗（IWDG）只怕喂晚，窗口看门狗（WWDG）喂早喂晚都复位。**

### 先打个比方

RTC 像一只装了纽扣电池的挂钟。家里停电，挂钟照走，来电以后时间还是对的。前提是电池有电，机芯（晶振）还在摆。

看门狗像夜班保安的打卡钟。保安每隔一段时间要去打一次卡，超过时限没打，值班室就派人把他换掉。独立看门狗只管「别迟到」，早打卡不算错。窗口看门狗更严：两次打卡之间至少要隔一段时间，打早了也算错，因为认真巡逻的人不可能那么快走完一圈。

比方到这里为止。F1 的 RTC 硬件只数秒，年月日要软件换算，芯片里并没有一块「表盘」；看门狗的「换人」是整颗芯片复位，程序从头跑；「打卡」就是往一个寄存器里写一个约定好的值。

### 1. RTC 与备份域：主电掉了还在走的秒表

**结论：RTC 住在备份域里。主电源 VDD 掉了，第 1 脚 VBAT 上的电池接着给 RTC、LSE 振荡器和备份寄存器供电；只有选 LSE 做 RTC 的时钟，VDD 掉电以后才保证还在走时。**

几个词先说清：

- **备份域**（backup domain）：芯片里单独供电的一小块电路，装着 RTC、LSE 振荡器和备份寄存器。VDD 在的时候由 VDD 供电，VDD 掉了自动切到 VBAT（RM0008 Rev 21 第 5.1.2 节）。
- **VBAT**：LQFP48 的第 1 脚，接备用电池。DS5319 Rev 20 第 2.3.9 节给出的工作范围是 1.8–3.6 V，一颗 3 V 的 CR2032 纽扣电池在范围之内。
- **LSE**（Low-Speed External，外部低速振荡器）：接在第 3 脚 PC14-OSC32_IN 和第 4 脚 PC15-OSC32_OUT 上的 32.768 kHz 晶振。
- **LSI**（Low-Speed Internal，内部低速振荡器）：片内的 RC 振荡器，不用外接元件，但频率不准。

RTC 的时钟从下面三路里选一路：

| 时钟源 | 频率 | VDD 掉电以后 RTC 还走吗 | 代价 |
| --- | --- | --- | --- |
| LSE | 32.768 kHz，准不准看晶振 | 走。LSE 在备份域里，靠 VBAT 供电 | 占用第 3、4 脚；起振慢，DS5319 Rev 20 表 23 的典型值在 25 °C 是 2.5 s，越冷越慢 |
| LSI | 最小 30 kHz、典型 40 kHz、最大 60 kHz（DS5319 Rev 20 表 25） | 不保证。LSI 不在备份域里 | 不占引脚，频率随芯片、温度和电压变 |
| HSE/128 | 8 MHz 晶振时是 62.5 kHz | 不保证。HSE 不在备份域里 | 主晶振要一直开着 |

这张表的用法：要「掉电还走时」，只有第一行可选；LSI 和 HSE/128 只适合 VDD 一直在、只想要一个秒节拍的场合。依据是 RM0008 Rev 21 第 7.2.8 节：LSE 在备份域里，HSE 和 LSI 不在；用 HSE/128 时，VDD 掉电后 RTC 的状态不保证。

选哪一路由 RCC_BDCR 寄存器的 RTCSEL 两位决定：00 无时钟，01 LSE，10 LSI，11 HSE/128。这两位一旦写成非零就改不了，只有复位整个备份域才能重选（RM0008 Rev 21 第 7.3.9 节）。复位备份域会把备份寄存器一起清掉，所以时钟源最好一次选定。

> [!TIP]
> 备份域上电以后默认写保护。动它之前要做两步：打开 PWR 和 BKP 两个外设时钟，再把 PWR_CR 寄存器的 DBP 位置 1（RM0008 Rev 21 第 6.1 节）。写不进去的时候，多半不是晶振坏了，而是这一步漏了。

### 2. 1 Hz 从哪来：PRL 和 (PRL + 1)

**结论：RTC 先用一只 20 位的预分频器把 RTCCLK 分成秒节拍，分频比是 (PRL + 1)。32.768 kHz 的 LSE 要写 PRL = 32767，32768 ÷ (32767 + 1) = 1 Hz。**

RTC 里有两只计数器串在一起：

- **预分频器**：RTCCLK 每来一个脉冲减 1，减完一轮产生一个节拍，再从 PRL 重新装。PRL（prescaler reload value，预分频重载值）是 20 位。
- **秒计数器 CNT**：32 位，每个节拍加 1。

公式在 RM0008 Rev 21 第 18.4.3 节：

```text
f_TR_CLK = f_RTCCLK / (PRL + 1)
```

「+1」是因为预分频器从 PRL 数到 0，一共数了 PRL + 1 个脉冲。下表按时钟源列出 PRL 该写多少，第二行是最常见的错：

| 时钟源 | f_RTCCLK | PRL | 节拍 | 说明 |
| --- | --- | --- | --- | --- |
| LSE | 32768 Hz | 32767（0x7FFF） | 1 Hz | 正确写法 |
| LSE | 32768 Hz | 32768（0x8000，复位值） | 每 32769 ÷ 32768 s 一拍 | 每天慢 86400 ÷ 32769 ≈ 2.64 s |
| LSI | 按典型值 40000 Hz 算 | 39999 | 只在 LSI 正好 40 kHz 时是 1 Hz | 30 kHz 时一拍约 1.33 s，60 kHz 时约 0.67 s |
| HSE/128 | 8 MHz ÷ 128 = 62500 Hz | 62499 | 1 Hz | VDD 掉电后不保证 |

表的读法：PRL 永远是「频率减 1」。RTC_PRLL 寄存器的复位值是 0x8000（RM0008 Rev 21 第 490 页），同一页的注写明 32.768 kHz 时要写 7FFFh 才是 1 秒。开了 RTC 却忘了写 PRL，钟照样走，只是每天慢两秒多。

晶振本身也不是绝对准。晶振的误差用 ppm（parts per million，百万分之一）表示，1 ppm 相当于每天差 86400 × 10⁻⁶ = 0.0864 s；上表第二行的错折算下来约 30.5 ppm。一颗 32.768 kHz 晶振每天差多少，看它自己的规格书。F1 可以用 BKP_RTCCR 寄存器的 CAL[6:0] 把 RTC 调慢 0–121 ppm（RM0008 Rev 21 第 6.3.2 节，做法见 ST 应用笔记 AN2604），只能调慢，不能调快。

RTC 的 PRL、CNT 和闹钟寄存器 ALR 不能像普通寄存器那样直接写。RM0008 Rev 21 第 18.3.4 节规定了五步：等 RTOFF = 1，置 CNF 进入配置模式，写寄存器，清 CNF，再等 RTOFF = 1；一次写至少要 3 个 RTCCLK 周期。复位或从 Stop、Standby 醒来以后，读 RTC 寄存器之前还要先等 RSF 置位（第 18.3.3 节）。HAL 把这些步骤包在函数里，寄存器写法放在「代码实现」末尾。

### 3. 备份寄存器：20 字节的掉电记事本

**结论：STM32F103C8T6 有 10 个 16 位的备份数据寄存器 BKP_DR1–BKP_DR10，共 20 字节。它们和 RTC 一样由 VBAT 续电，系统复位、上电复位、从 Standby 醒来都不会清掉它们（RM0008 Rev 21 第 6.1 节）。**

| 器件 | 备份寄存器 | 容量 | 出处 |
| --- | --- | --- | --- |
| STM32F103C8T6（中密度） | BKP_DR1–BKP_DR10，16 位 | 20 字节 | DS5319 Rev 20 第 2.3.14 节；RM0008 Rev 21 第 6.2 节 |
| F1 大容量、XL 和互联型 | BKP_DR1–BKP_DR42，16 位 | 84 字节 | RM0008 Rev 21 第 6.2 节 |
| STM32F4 | RTC_BKP0R–RTC_BKP19R，32 位 | 80 字节 | RM0090 Rev 22 第 26 章 |

这张表说明两件事：20 字节很少，只够存几个标志和一个日期；换系列时寄存器的名字和宽度都变了，代码不能照搬。

典型用法是「魔法值」：上电先读 BKP_DR1，读到约定的值（本章例程用 0xA5A5），说明时间设过、备份域没掉过电，直接接着用；读到别的值，说明是第一次上电或者电池没电了，重新设时间，最后再写魔法值。魔法值放在最后写，设时间的中途掉电，下次上电读不到它，会整个重来一遍。

能清掉备份寄存器的事件只有几种：备份域复位，也就是软件置 RCC_BDCR 的 BDRST，或 VDD 和 VBAT 都掉过电以后重新上电（RM0008 Rev 21 第 7.1.3 节）；另外，开了入侵检测时，TAMPER 脚（PC13）上的入侵事件也会清掉全部备份数据寄存器（第 6.3.1 节）。

### 4. F1 的日历和闹钟：硬件只数秒

**结论：F1 的 RTC 没有年月日寄存器，只有一只 32 位秒计数器 CNT 和一只 32 位闹钟寄存器 ALR。CNT 走完等于 ALR 的那一秒时，闹钟标志 ALRF 置位，可以触发中断；年月日、星期、闰年全靠软件。**

| 功能 | STM32F103（RM0008 Rev 21 第 18 章） | STM32F4（RM0090 Rev 22 第 26 章） |
| --- | --- | --- |
| 日历 | 无。32 位秒计数器，日期由软件换算 | 硬件 BCD 日历（RTC_TR、RTC_DR），带星期和闰年 |
| 闹钟 | 1 个，和秒计数器比大小 | 2 个，可以按秒、分、时、日期或星期屏蔽 |
| 周期唤醒 | 没有专门的定时器，用秒中断或闹钟代替 | 有周期唤醒定时器 |
| 时间戳 | 无 | 有 |

这张表的用法：很多 RTC 教程是按 F4 写的，看到 `RTC_TR` 或 `AlarmMask` 这类名字，在 F1 上都对不上。

HAL 在 F1 上怎么做日历，下面几条是 STM32CubeF1 HAL 源码的行为，不是手册内容：

- 时分秒：`HAL_RTC_SetTime` 把时分秒换算成秒写进 CNT，`HAL_RTC_GetTime` 读 CNT 再换算回来。
- 年月日：放在句柄的 `hrtc.DateToUpdate` 里，在 RAM 里，不在 RTC 里。`HAL_RTC_GetTime` 发现 CNT 超过 24 小时，就把整天数加到日期上，再把 CNT 减回当天的秒数。
- 复位以后：`HAL_RTC_Init` 把日期重置成 2000-01-01。秒计数器在备份域里没丢，日期却丢了，所以日期要自己存进备份寄存器，复位后再填回去。
- 闹钟：`RTC_AlarmTypeDef` 只有 `AlarmTime` 和 `Alarm` 两个成员，`Alarm` 只能是 `RTC_ALARM_A`。闹钟按秒比大小，响一次就过去了；要每天响，就在每次响过以后重新设一次。设的时刻如果今天已经过了，`HAL_RTC_SetAlarm_IT` 会自动加 24 小时。

### 5. 看门狗是什么：一个要按时喂的倒数计数器

**结论：看门狗是一只自己往下数的计数器。程序隔一段时间往它的寄存器里写一个约定的值，俗称「喂狗」，计数就重新开始；程序跑飞或卡死，没人喂，计数到底，芯片复位。**

为什么要它：程序可能因为一个没想到的死循环、一个永远等不到的标志卡住。设备放在现场，没人去按复位键，看门狗保证卡住以后能自己重启。它只负责重启，不负责修好：重启以后同样的条件可能再出现，这一点放到第 8 节。

STM32F103 有两只看门狗：独立看门狗 IWDG（RM0008 Rev 21 第 19 章）和窗口看门狗 WWDG（第 20 章）。先看差别：

| 项目 | 独立看门狗 IWDG | 窗口看门狗 WWDG |
| --- | --- | --- |
| 时钟 | LSI（典型 40 kHz，范围 30–60 kHz） | PCLK1 ÷ 4096 ÷ 预分频（本书 PCLK1 = 36 MHz） |
| 计数器 | 12 位，往下减 | 7 位 T[6:0]，往下减 |
| 什么时候复位 | 减到 0 | 计数器从 0x40 减到 0x3F（T6 位变 0），或在计数器大于窗口值时喂狗 |
| 喂早了 | 不复位 | 复位 |
| 超时范围 | 40 kHz 下 0.1 ms 到 26214.4 ms（RM0008 Rev 21 表 96） | 36 MHz 下 113 µs 到 58.25 ms（表 98） |
| 主时钟出问题 | 照样计时（第 19.1 节） | 时钟从 APB1 分出来，跟着主时钟走 |
| 启动以后能关吗 | 不能，只有复位能停（第 5.3.4 节） | 不能，WDGA 置位后只有复位能清（第 20.6.1 节） |

表的读法：IWDG 的长处是时钟独立，主时钟出了问题也能把芯片拉回来；WWDG 的长处是有窗口，能抓到「跑得太快」的程序。两只可以同时用。

### 6. 独立看门狗（IWDG）：只怕喂晚

**结论：IWDG 用 LSI 计时。预分频 64、LSI 按典型 40 kHz 算，计数频率是 625 Hz；Reload 写 624，从 624 减到 0 正好 625 拍，就是 1 秒。减到 0 之前任何时候喂都行，喂早不复位。**

它的结构很简单（RM0008 Rev 21 第 19.3 节图 182）：LSI 进一只 8 位预分频器，再进一只 12 位往下减的计数器。程序和它打交道全靠往键寄存器 IWDG_KR 写三个值：

| 写进 IWDG_KR 的值 | 作用 |
| --- | --- |
| 0xCCCC | 启动。LSI 被强制打开（RM0008 Rev 21 第 7.2.9 节），计数器从 0xFFF 开始往下减 |
| 0x5555 | 解锁预分频寄存器 IWDG_PR 和重载寄存器 IWDG_RLR，之后才能改它们 |
| 0xAAAA | 喂狗：把 RLR 里的值重新装进计数器 |

这张表就是 IWDG 的全部操作。HAL 的 `HAL_IWDG_Init` 按「启动、解锁、写 PR 和 RLR、等写完、喂一次」的顺序做，`HAL_IWDG_Refresh` 就是写 0xAAAA。

超时这样算：

```text
T = 预分频 ÷ f_LSI × (Reload + 1)
  = 64 ÷ 40000 × (624 + 1) = 1 s          （LSI 按典型值 40 kHz）
```

为什么是 Reload + 1：计数器从 624 数到 0，一共 625 个状态。RM0008 Rev 21 表 96 可以对上这一点：64 分频那一行，Reload = 0 时最短 1.6 ms，正好一拍 64 ÷ 40000；Reload = 0xFFF 时最长 6553.6 ms，正好 4096 拍。

| 预分频 | PR 的值 | 最短超时（Reload = 0） | 最长超时（Reload = 0xFFF） |
| --- | --- | --- | --- |
| 4 | 0 | 0.1 ms | 409.6 ms |
| 8 | 1 | 0.2 ms | 819.2 ms |
| 16 | 2 | 0.4 ms | 1638.4 ms |
| 32 | 3 | 0.8 ms | 3276.8 ms |
| 64 | 4 | 1.6 ms | 6553.6 ms |
| 128 | 5 | 3.2 ms | 13107.2 ms |
| 256 | 6 或 7 | 6.4 ms | 26214.4 ms |

这张表是 RM0008 Rev 21 表 96 的数字，表注写明按 40 kHz 计算。用法：按需要的超时找一行，最长超时比需要的大就行，再用公式反算 Reload。

LSI 并不正好是 40 kHz，DS5319 Rev 20 表 25 给的是最小 30 kHz、最大 60 kHz。同一套 64 和 624：

- LSI = 60 kHz：64 ÷ 60000 × 625 ≈ 0.667 s，狗咬得最早。
- LSI = 30 kHz：64 ÷ 30000 × 625 ≈ 1.333 s，狗咬得最晚。

所以喂狗间隔要按最早的 0.667 s 来定，还要给程序的抖动留余量，本章例程每 200 ms 喂一次（例程设定）。反过来，程序卡死以后最晚要 1.333 s 才复位，系统要能接受这段延迟。

IWDG 还可以不靠软件启动：选项字节里的 WDG_SW 写成 0，上电就自动开始计时，叫「硬件看门狗」（RM0008 Rev 21 第 19.3.1 节）。它对启动代码的影响放在「原理与适用范围」里算。

### 7. 窗口看门狗（WWDG）：喂早喂晚都复位

**结论：WWDG 的 7 位计数器从写进去的值往下减，减到 0x3F（T6 位变 0）时复位；计数器还大于窗口值时喂狗，也复位。喂狗只能落在「低于窗口值、高于 0x3F」这一段里。**

先算一拍多长（RM0008 Rev 21 第 20.4 节）：

```text
一拍    = 4096 × 2^WDGTB ÷ f_PCLK1
        = 4096 × 8 ÷ 36 MHz ≈ 0.910 ms        （WDGTB = 3，即预分频 8）
t_WWDG  = 一拍 × (T[5:0] + 1)
        = 0.910 ms × 64 = 58.25 ms             （初值 0x7F，T[5:0] = 63）
```

本章的设定：PCLK1 = 36 MHz，预分频 8，每次喂狗写回 0x7F，窗口值 0x50。从上一次喂狗算起，时间线是这样的：

| 距上次喂狗 | 计数器 | 这时喂狗会怎样 |
| --- | --- | --- |
| 0 到约 43.7 ms | 0x7F 减到 0x50 | 太早，复位 |
| 约 43.7 ms 到约 57.3 ms | 0x4F 到 0x40 | 正好，计数器回到 0x7F |
| 约 57.3 ms | 到 0x40 | 开了 EWI 的话，进一次早期唤醒中断 |
| 约 58.25 ms | 0x40 减到 0x3F | 复位 |

表里的数这样算：0x7F 减到 0x4F 是 48 拍，48 × 0.910 ≈ 43.7 ms；减到 0x40 是 63 拍，约 57.3 ms；减到 0x3F 是 64 拍，58.25 ms。写 CR 的时候预分频器走到哪一拍不知道，所以每个时间点最多提早一拍，也就是 0.91 ms（RM0008 Rev 21 第 20.3 节）。表 98 给出 36 MHz、预分频 8 时的超时范围是 910 µs 到 58.25 ms，两头正好是 1 拍和 64 拍。

所以喂狗周期选 50 ms（例程设定）：那时计数器在 0x49 或 0x48，在窗口里面，离 EWI 还有 6 ms 以上。

EWI（Early Wakeup Interrupt，早期唤醒中断）在计数器到 0x40 时进一次，离复位只剩一拍。可以在这里把出错的现场写进备份寄存器，复位以后再看。

### 8. 两只狗怎么选、喂狗放在哪

**结论：只用一只就选 IWDG，它的时钟独立；要抓「程序跑太快」再加 WWDG。喂狗的位置比选哪只狗更要紧：只在确认「这一圈真的走完了」的地方喂。**

几种喂法的对比（经验做法，不是手册条文）：

- **主循环末尾喂**：最常见。主循环里任何一步卡住，狗都会咬。主循环里某一步本来就慢，就得把超时放宽。
- **只在定时器中断里喂**：不要这样做。主循环卡死时定时器中断照样进，狗一直吃得饱，等于没养。
- **主循环打卡，定时器中断里检查**：主循环每走完一圈置一个标志，定时器中断看到标志才喂并清掉它。效果等于主循环喂狗，但喂的时刻规整，适合 WWDG 的窗口。
- **RTOS 里每个任务打卡**：每个关键任务各自置一个标志，一个监视任务看到标志全齐了才喂。任何一个任务卡住，狗都会咬。

看门狗复位以后程序从头跑，引起卡死的条件要是还在，设备会反复重启。所以启动时先读复位原因（第 9 节），连续几次都是看门狗复位，就进一个功能最少的安全模式，不要照常再跑一遍。

### 9. 调试时冻住计数器，复位后查原因

**结论：单步调试时内核停了，看门狗还在数，一会儿就把芯片复位。调试前用 `__HAL_DBGMCU_FREEZE_IWDG()` 和 `__HAL_DBGMCU_FREEZE_WWDG()` 让它们跟着内核停。芯片为什么重启，看 RCC_CSR 里的复位标志，读完用 RMVF 清掉。**

冻结：RM0008 Rev 21 第 19.3.3 节和第 20.5 节说，内核停下时，两只看门狗是接着数还是停，由 DBG_IWDG_STOP 和 DBG_WWDG_STOP 两个配置位决定。它们在 DBGMCU_CR 寄存器里（第 31.16.3 节），不在选项字节里。

复位标志：RCC_CSR 寄存器（RM0008 Rev 21 第 7.3.10 节）用六个位记录上一次复位是谁引起的。

| 标志 | 位 | 谁引起的复位 |
| --- | --- | --- |
| LPWRRSTF | 31 | 低功耗管理复位：选项字节 nRST_STOP 或 nRST_STDBY 让「进 Stop / Standby」变成复位 |
| WWDGRSTF | 30 | 窗口看门狗 |
| IWDGRSTF | 29 | 独立看门狗 |
| SFTRSTF | 28 | 软件复位，例如调用 `NVIC_SystemReset()` |
| PORRSTF | 27 | 上电复位或掉电复位 |
| PINRSTF | 26 | NRST 脚（第 7 脚）被拉低 |

这张表的用法：启动时先读这几位，再写 RMVF（第 24 位）把它们一起清掉。这些标志只在上电复位时清零，别的复位都不清，不清的话下一次复位时旧标志还在，分不清新旧。RCC_CSR 的复位值是 0x0C00 0000，也就是上电复位时 PORRSTF 和 PINRSTF 同时为 1；第 7.1.2 节还说，每一种复位源都会让 NRST 脚输出至少 20 µs 的低电平。所以判断时把 PINRSTF 放到最后：先看看门狗、软件和上电，都不是，才算有人按了复位键。

口诀：**LSE 配 32767 才是一秒；独立看门狗只怕喂晚，窗口看门狗早晚都怕；喂狗放在一圈真的走完的地方。**

## 硬件与接线

| 开发板 | 外设 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill（STM32F103C8T6） | LSE 32.768 kHz 晶振 | 第 3 脚 PC14-OSC32_IN、第 4 脚 PC15-OSC32_OUT | 先看板上这两只脚旁边有没有 32.768 kHz 晶振，没有就焊一颗；用作 LSE 后这两只脚不再当 GPIO |
| BluePill | 备用电池 | 第 1 脚 VBAT | 接 CR2032（3 V，在 DS5319 Rev 20 第 2.3.9 节的 1.8–3.6 V 之内）。不接电池时，RM0008 Rev 21 第 5.1.2 节建议把 VBAT 接到 VDD，并加 100 nF 陶瓷电容 |
| BluePill | 心跳灯 | 第 2 脚 PC13 | 板载灯，写 0 亮（第 03 章）。PC13–PC15 当输出时速度不超过 2 MHz，不能向外输出电流（RM0008 Rev 21 第 5.1.2 节） |
| BluePill | 复位脚 | 第 7 脚 NRST | 实验三用逻辑分析仪看复位脉冲 |
| 任意 | IWDG、WWDG | 无 | 纯片内，不占引脚 |

```text
STM32F103C8T6（LQFP48）

第 1 脚 VBAT ──────────── CR2032 正极（负极接 GND）
第 2 脚 PC13 ── LED ── 电阻 ── 3.3 V        板载心跳灯，写 0 亮

第 3 脚 PC14-OSC32_IN ──┬──[ 32.768 kHz 晶振 ]──┬── 第 4 脚 PC15-OSC32_OUT
                        CL1                     CL2
                        │                        │
                       GND                      GND

第 7 脚 NRST ──────────── 逻辑分析仪（实验三）
IWDG、WWDG：不占引脚
```

> [!WARNING]
> 晶振选负载电容 CL ≤ 7 pF 的，不要用 12.5 pF 的：DS5319 Rev 20 第 5.3.6 节为了不让外接电容 CL1、CL2 超过最大 15 pF 给出这条建议，选大了 LSE 可能起不来。纽扣电池不能被充电，RM0008 Rev 21 第 5.1.2 节提醒：上电阶段 VDD 在 tRSTTEMPO（上电复位延时，数值见数据手册）之内就建立起来、又比 VBAT 高 0.6 V 以上时，电流可能经内部二极管灌进 VBAT，电池受不了就在电池和 VBAT 之间串一只低压降二极管。

## 代码实现

下面是一个完整的程序：LSE 走时，日期存进备份寄存器，每天 08:30 闹钟翻转一次 PC13 的灯，独立看门狗约 1 秒超时，主循环每 200 ms 喂一次。基于 STM32CubeF1 的 HAL。

```c
/* rtc_wdg.c —— LSE 日历 + 每天 08:30 闹钟 + 约 1 秒的独立看门狗（HAL，STM32F103C8T6） */
#include "stm32f1xx_hal.h"

#define LED_PORT        GPIOC
#define LED_PIN         GPIO_PIN_13        /* BluePill 板载灯，写 0 亮 */

#define LSE_TRIES       3U                 /* HAL 每次最多等 LSE_STARTUP_TIMEOUT，默认 5000 ms */

#define RTC_BKP_MAGIC   0xA5A5U            /* 「时间已经设过」的记号 */
#define BKP_REG_MAGIC   RTC_BKP_DR1
#define BKP_REG_YEAR    RTC_BKP_DR2
#define BKP_REG_MONTH   RTC_BKP_DR3
#define BKP_REG_DAY     RTC_BKP_DR4

#define START_YEAR      26U                /* 例程设定：2026-01-07 12:00:00 */
#define START_MONTH     RTC_MONTH_JANUARY
#define START_DAY       7U
#define START_HOURS     12U
#define START_MINUTES   0U
#define START_SECONDS   0U

#define ALARM_HOURS     8U                 /* 例程设定：每天 08:30:00 */
#define ALARM_MINUTES   30U
#define ALARM_SECONDS   0U

#define IWDG_RELOAD     624U               /* 64 / 40 kHz × (624 + 1) = 1 s，LSI 典型值 */
#define LOOP_PERIOD_MS  200U               /* 例程设定：小于 LSI 60 kHz 时的 0.667 s */

RTC_HandleTypeDef  hrtc;
IWDG_HandleTypeDef hiwdg;

typedef enum {
    RESET_OTHER = 0,
    RESET_POWER_ON,
    RESET_PIN,
    RESET_SOFTWARE,
    RESET_IWDG,
    RESET_WWDG,
    RESET_LOW_POWER
} reset_cause_t;

volatile reset_cause_t g_reset_cause;      /* 调试器里看：这次为什么复位 */
volatile uint32_t      g_alarm_count;      /* 闹钟响过几次 */
volatile uint8_t       g_alarm_pending;    /* 中断里置 1，主循环里处理 */
RTC_TimeTypeDef        g_time;             /* 调试器里看：时分秒 */
RTC_DateTypeDef        g_date;             /* 调试器里看：年月日 */

static void SystemClock_Config(void);
static reset_cause_t read_reset_cause(void);
static void led_init(void);
static void rtc_clock_init(void);
static void rtc_init(void);
static void clock_update(void);
static void save_date(const RTC_DateTypeDef *d);
static void alarm_arm_daily(void);
static void iwdg_init(void);
static void error_handler(void);

int main(void)
{
    HAL_Init();
    SystemClock_Config();

    g_reset_cause = read_reset_cause();    /* 先读复位原因，再清旗 */
    __HAL_DBGMCU_FREEZE_IWDG();            /* 内核停在断点时 IWDG 也停 */

    led_init();
    rtc_clock_init();
    rtc_init();
    clock_update();
    alarm_arm_daily();
    HAL_NVIC_SetPriority(RTC_Alarm_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(RTC_Alarm_IRQn);

    iwdg_init();                           /* 放在最后：等 LSE 可能要好几秒 */

    while (1) {
        clock_update();
        if (g_alarm_pending != 0U) {
            g_alarm_pending = 0U;
            g_alarm_count++;
            HAL_GPIO_TogglePin(LED_PORT, LED_PIN);
            alarm_arm_daily();             /* F1 的闹钟只响一次，重新设到明天 */
        }
        HAL_IWDG_Refresh(&hiwdg);          /* 这一圈真的走完了才喂 */
        HAL_Delay(LOOP_PERIOD_MS);
    }
}

static reset_cause_t read_reset_cause(void)
{
    reset_cause_t cause = RESET_OTHER;

    if (__HAL_RCC_GET_FLAG(RCC_FLAG_IWDGRST) != 0U) {
        cause = RESET_IWDG;
    } else if (__HAL_RCC_GET_FLAG(RCC_FLAG_WWDGRST) != 0U) {
        cause = RESET_WWDG;
    } else if (__HAL_RCC_GET_FLAG(RCC_FLAG_LPWRRST) != 0U) {
        cause = RESET_LOW_POWER;
    } else if (__HAL_RCC_GET_FLAG(RCC_FLAG_SFTRST) != 0U) {
        cause = RESET_SOFTWARE;
    } else if (__HAL_RCC_GET_FLAG(RCC_FLAG_PORRST) != 0U) {
        cause = RESET_POWER_ON;
    } else if (__HAL_RCC_GET_FLAG(RCC_FLAG_PINRST) != 0U) {
        cause = RESET_PIN;                 /* 别的旗都没有，才算按了复位键 */
    }
    __HAL_RCC_CLEAR_RESET_FLAGS();         /* 写 RMVF，六面旗一起清 */
    return cause;
}

static void led_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOC_CLK_ENABLE();
    HAL_GPIO_WritePin(LED_PORT, LED_PIN, GPIO_PIN_SET);   /* 先写 1：灯灭 */
    io.Pin   = LED_PIN;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Pull  = GPIO_NOPULL;
    io.Speed = GPIO_SPEED_FREQ_LOW;        /* PC13 不超过 2 MHz */
    HAL_GPIO_Init(LED_PORT, &io);
}

static void rtc_clock_init(void)
{
    RCC_OscInitTypeDef       osc  = {0};
    RCC_PeriphCLKInitTypeDef pclk = {0};
    HAL_StatusTypeDef        st   = HAL_ERROR;
    uint32_t                 tries;

    __HAL_RCC_PWR_CLK_ENABLE();
    __HAL_RCC_BKP_CLK_ENABLE();
    HAL_PWR_EnableBkUpAccess();            /* PWR_CR 的 DBP 置 1，备份域才能写 */

    osc.OscillatorType = RCC_OSCILLATORTYPE_LSE;
    osc.LSEState       = RCC_LSE_ON;
    osc.PLL.PLLState   = RCC_PLL_NONE;     /* 不碰已经配好的 PLL */
    for (tries = 0U; (tries < LSE_TRIES) && (st != HAL_OK); tries++) {
        st = HAL_RCC_OscConfig(&osc);      /* LSE 已经在走时立刻返回 */
    }
    if (st != HAL_OK) {
        error_handler();
    }

    pclk.PeriphClockSelection = RCC_PERIPHCLK_RTC;
    pclk.RTCClockSelection    = RCC_RTCCLKSOURCE_LSE;
    if (HAL_RCCEx_PeriphCLKConfig(&pclk) != HAL_OK) {
        error_handler();
    }
    __HAL_RCC_RTC_ENABLE();                /* RCC_BDCR 的 RTCEN */
}

static void rtc_init(void)
{
    RTC_TimeTypeDef t = {0};
    RTC_DateTypeDef d = {0};

    hrtc.Instance          = RTC;
    hrtc.Init.AsynchPrediv = RTC_AUTO_1_SECOND;    /* HAL 按 LSE 频率写 PRL = 32768 - 1 */
    hrtc.Init.OutPut       = RTC_OUTPUTSOURCE_NONE;
    if (HAL_RTC_Init(&hrtc) != HAL_OK) {
        error_handler();
    }

    if (HAL_RTCEx_BKUPRead(&hrtc, BKP_REG_MAGIC) != RTC_BKP_MAGIC) {
        /* 第一次上电，或备份域掉过电：设起始时间 */
        t.Hours   = START_HOURS;
        t.Minutes = START_MINUTES;
        t.Seconds = START_SECONDS;
        d.Year    = START_YEAR;
        d.Month   = START_MONTH;
        d.Date    = START_DAY;
        if ((HAL_RTC_SetTime(&hrtc, &t, RTC_FORMAT_BIN) != HAL_OK) ||
            (HAL_RTC_SetDate(&hrtc, &d, RTC_FORMAT_BIN) != HAL_OK)) {
            error_handler();
        }
        save_date(&d);
        HAL_RTCEx_BKUPWrite(&hrtc, BKP_REG_MAGIC, RTC_BKP_MAGIC);   /* 最后写记号 */
    } else {
        /* 复位以后：秒计数器还在走，日期从备份寄存器拿回来 */
        hrtc.DateToUpdate.Year  = (uint8_t)HAL_RTCEx_BKUPRead(&hrtc, BKP_REG_YEAR);
        hrtc.DateToUpdate.Month = (uint8_t)HAL_RTCEx_BKUPRead(&hrtc, BKP_REG_MONTH);
        hrtc.DateToUpdate.Date  = (uint8_t)HAL_RTCEx_BKUPRead(&hrtc, BKP_REG_DAY);
    }
}

static void clock_update(void)
{
    RTC_DateTypeDef d;

    if (HAL_RTC_GetTime(&hrtc, &g_time, RTC_FORMAT_BIN) != HAL_OK) {
        error_handler();
    }
    if (HAL_RTC_GetDate(&hrtc, &d, RTC_FORMAT_BIN) != HAL_OK) {
        error_handler();
    }
    if ((d.Year != g_date.Year) || (d.Month != g_date.Month) || (d.Date != g_date.Date)) {
        g_date = d;
        save_date(&d);                     /* 日期变了：写回备份寄存器 */
    }
}

static void save_date(const RTC_DateTypeDef *d)
{
    HAL_RTCEx_BKUPWrite(&hrtc, BKP_REG_YEAR,  d->Year);
    HAL_RTCEx_BKUPWrite(&hrtc, BKP_REG_MONTH, d->Month);
    HAL_RTCEx_BKUPWrite(&hrtc, BKP_REG_DAY,   d->Date);
}

static void alarm_arm_daily(void)
{
    RTC_AlarmTypeDef a = {0};

    a.Alarm             = RTC_ALARM_A;     /* F1 只有这一个闹钟 */
    a.AlarmTime.Hours   = ALARM_HOURS;
    a.AlarmTime.Minutes = ALARM_MINUTES;
    a.AlarmTime.Seconds = ALARM_SECONDS;
    if (HAL_RTC_SetAlarm_IT(&hrtc, &a, RTC_FORMAT_BIN) != HAL_OK) {   /* 今天已过就设到明天 */
        error_handler();
    }
}

void RTC_Alarm_IRQHandler(void)
{
    HAL_RTC_AlarmIRQHandler(&hrtc);
}

void HAL_RTC_AlarmAEventCallback(RTC_HandleTypeDef *h)
{
    (void)h;
    g_alarm_pending = 1U;                  /* 中断里只置旗 */
}

static void iwdg_init(void)
{
    hiwdg.Instance       = IWDG;
    hiwdg.Init.Prescaler = IWDG_PRESCALER_64;      /* 40 kHz / 64 = 625 Hz（典型） */
    hiwdg.Init.Reload    = IWDG_RELOAD;
    if (HAL_IWDG_Init(&hiwdg) != HAL_OK) {         /* 这一句就把狗放出去了，停不下来 */
        error_handler();
    }
}

static void SystemClock_Config(void)
{
    RCC_OscInitTypeDef osc = {0};
    RCC_ClkInitTypeDef clk = {0};

    osc.OscillatorType = RCC_OSCILLATORTYPE_HSE;
    osc.HSEState       = RCC_HSE_ON;
    osc.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
    osc.PLL.PLLState   = RCC_PLL_ON;
    osc.PLL.PLLSource  = RCC_PLLSOURCE_HSE;
    osc.PLL.PLLMUL     = RCC_PLL_MUL9;              /* 8 MHz × 9 = 72 MHz */
    if (HAL_RCC_OscConfig(&osc) != HAL_OK) {
        error_handler();
    }
    clk.ClockType      = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK |
                         RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
    clk.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK;
    clk.AHBCLKDivider  = RCC_SYSCLK_DIV1;
    clk.APB1CLKDivider = RCC_HCLK_DIV2;             /* PCLK1 = 36 MHz，WWDG 用它 */
    clk.APB2CLKDivider = RCC_HCLK_DIV1;
    if (HAL_RCC_ClockConfig(&clk, FLASH_LATENCY_2) != HAL_OK) {
        error_handler();
    }
}

static void error_handler(void)
{
    __disable_irq();
    while (1) { }          /* IWDG 已经启动时约 1 秒后复位；还没启动时停在这里 */
}
```

逐段看：

- `read_reset_cause()` 放在最前面：复位标志要在清掉之前读。PINRSTF 放在最后判断，理由见第 9 节。
- `__HAL_DBGMCU_FREEZE_IWDG()`：调试器停住内核时 IWDG 跟着停，单步不会被复位。不接调试器时它不起作用。
- `rtc_clock_init()`：先开 PWR、BKP 时钟并置 DBP，备份域才能写。`HAL_RCC_OscConfig` 只配 LSE，`PLL.PLLState = RCC_PLL_NONE` 表示不动 PLL。HAL 每次最多等 5000 ms，这里最多试三次，共 15 s（例程设定）。DS5319 Rev 20 表 23 的 LSE 起振时间典型值在 25 °C 是 2.5 s，−10 °C 是 10 s，冷天要等得更久。
- `HAL_RCCEx_PeriphCLKConfig` 写 RTCSEL；它不开 RTC，所以后面还要 `__HAL_RCC_RTC_ENABLE()`。RTCSEL 已经是别的非零值时，这个函数会先复位备份域才能改选，备份寄存器随之清空（HAL 源码行为，对应第 1 节的 RTCSEL 锁定）。
- `RTC_AUTO_1_SECOND`：HAL 读出 LSE 的频率 32768，减 1 写进 PRL，得到 32767。
- 魔法值的分支：第一次上电走上面一支，设时间、存日期，最后写记号；复位以后走下面一支，秒计数器没动，只把年月日填回 `hrtc.DateToUpdate`。这里不用 `HAL_RTC_SetDate`：它会把计数器里攒下的整天数扔掉，设备断电好几天再上电，日期就少了这几天。
- `clock_update()`：`HAL_RTC_GetTime` 遇到计数器超过 24 小时会把整天数折进日期，所以每次日期变了都写回备份寄存器。折算和写回之间掉电会丢掉这一天的进位，例程不处理这个窄窗口。
- `alarm_arm_daily()` 启动时调一次，每次闹钟响过再调一次。系统复位会清掉闹钟中断使能，因为 RM0008 Rev 21 第 18.3.2 节规定，RTC 只有 PRL、ALR、CNT、DIV 四个寄存器要备份域复位才清，其余的系统复位就清。
- 闹钟回调只置一个标志，翻灯和重设闹钟都放回主循环，中断里不调用会上锁的 HAL 函数。
- `iwdg_init()` 放在最后：第一次上电等 LSE 可能要好几秒，IWDG 先启动的话，1 秒就把芯片咬回去了。现行的 STM32CubeF1 HAL 里，`HAL_IWDG_Init` 本身就会启动 IWDG，没有单独的 Start 函数。
- `HAL_Delay` 和 HAL 里的各种超时都靠 SysTick 计时；`SysTick_Handler` 里调用 `HAL_IncTick()`，由 CubeMX 生成在 `stm32f1xx_it.c` 里。CubeMX 里如果也勾了 RTC 闹钟中断，`stm32f1xx_it.c` 里会再生成一个 `RTC_Alarm_IRQHandler`，两处只留一处。`stm32f1xx_hal_conf.h` 里要打开 `HAL_RTC_MODULE_ENABLED` 和 `HAL_IWDG_MODULE_ENABLED`，用窗口看门狗时再打开 `HAL_WWDG_MODULE_ENABLED`。

窗口看门狗不在上面的程序里。要加的话，把下面这段放进同一个文件、放在 `main()` 前面：`main()` 里在 `iwdg_init()` 后面调用 `wwdg_init()`，主循环的最后、`HAL_Delay` 之后调用 `task_50ms()`，再把 `LOOP_PERIOD_MS` 改成 50。

```c
/* 片段：窗口看门狗。PCLK1 = 36 MHz，一拍 = 4096 × 8 / 36 MHz ≈ 0.91 ms */
#define WWDG_WINDOW    0x50U               /* 计数器降到 0x50 以下才许喂 */
#define WWDG_COUNTER   0x7FU               /* 每次喂狗写回的值 */

WWDG_HandleTypeDef hwwdg;

static void wwdg_init(void)
{
    __HAL_DBGMCU_FREEZE_WWDG();                    /* 内核停在断点时 WWDG 也停 */
    hwwdg.Instance       = WWDG;
    hwwdg.Init.Prescaler = WWDG_PRESCALER_8;
    hwwdg.Init.Window    = WWDG_WINDOW;
    hwwdg.Init.Counter   = WWDG_COUNTER;
    hwwdg.Init.EWIMode   = WWDG_EWI_ENABLE;        /* 计数器到 0x40 时进一次中断 */
    if (HAL_WWDG_Init(&hwwdg) != HAL_OK) {         /* 置 WDGA，从此只有复位能关 */
        error_handler();
    }
}

void HAL_WWDG_MspInit(WWDG_HandleTypeDef *h)
{
    (void)h;
    __HAL_RCC_WWDG_CLK_ENABLE();
    HAL_NVIC_SetPriority(WWDG_IRQn, 0, 0);
    HAL_NVIC_EnableIRQ(WWDG_IRQn);
}

void WWDG_IRQHandler(void)
{
    HAL_WWDG_IRQHandler(&hwwdg);
}

void HAL_WWDG_EarlyWakeupCallback(WWDG_HandleTypeDef *h)
{
    (void)h;
    /* 离复位只剩一拍，约 0.91 ms：记下现场，不在这里喂狗 */
}

void task_50ms(void)                        /* 例程设定：大约每 50 ms 调一次 */
{
    /* ……这一轮的工作…… */
    HAL_WWDG_Refresh(&hwwdg);               /* 落在 43.7 ms 到 57.3 ms 之间 */
}
```

逐段看：

- `HAL_WWDG_Init` 先调 `HAL_WWDG_MspInit` 开时钟和中断，再写 CR 置 WDGA，狗从这一刻开始数。第一次喂狗也要落在初始化以后的 43.7–57.3 ms 里，所以 `task_50ms()` 放在 `HAL_Delay` 之后，不放在循环开头。
- `HAL_Delay(50)` 加上主循环其余几步，两次喂狗相隔 50 到 52 ms，仍在 43.7–57.3 ms 里。
- `HAL_WWDG_Refresh` 把 `Counter` 的值 0x7F 写回 CR。
- 早期唤醒回调里不喂狗，复位照常发生。RM0008 Rev 21 第 20.3 节也允许在这个中断里喂狗、做降级处理，那样就放弃了这一次复位，要自己保证还有别的兜底。

和 `iwdg_init()` 等价的寄存器写法，可以对照 RM0008 Rev 21 第 19.3 节看每一步：

```c
/* 寄存器写法：IWDG 预分频 64、Reload 624 */
IWDG->KR  = 0xCCCCU;                   /* 启动：LSI 被强制打开，计数器从 0xFFF 往下减 */
IWDG->KR  = 0x5555U;                   /* 解锁 PR 和 RLR */
IWDG->PR  = 4U;                        /* PR = 4：64 分频 */
IWDG->RLR = 624U;                      /* 重载值 */
while (IWDG->SR != 0U) { }             /* PVU、RVU 都清零，才算写进去了 */
IWDG->KR  = 0xAAAAU;                   /* 喂一次：把 624 装进计数器 */
```

RTC 写 PRL 的五步，对照 RM0008 Rev 21 第 18.3.3 节和第 18.3.4 节：

```c
/* 寄存器写法：把 PRL 写成 32767 */
RCC->APB1ENR |= RCC_APB1ENR_PWREN | RCC_APB1ENR_BKPEN;
PWR->CR      |= PWR_CR_DBP;                    /* 备份域解锁 */
RTC->CRL     &= ~RTC_CRL_RSF;
while ((RTC->CRL & RTC_CRL_RSF) == 0U) { }     /* 等 APB1 和 RTC 同步 */
while ((RTC->CRL & RTC_CRL_RTOFF) == 0U) { }   /* 上一次写操作完成 */
RTC->CRL     |= RTC_CRL_CNF;                   /* 进入配置模式 */
RTC->PRLH     = 0U;
RTC->PRLL     = 0x7FFFU;                       /* 32767：32768 Hz ÷ (32767 + 1) = 1 Hz */
RTC->CRL     &= ~RTC_CRL_CNF;                  /* 退出配置模式，这时才真正开始写 */
while ((RTC->CRL & RTC_CRL_RTOFF) == 0U) { }   /* 至少 3 个 RTCCLK 周期 */
```

完整工程见 [`examples/rtc-alarm/`](../examples/rtc-alarm/)。那份例程里的 `alarm.AlarmMask` 是 F4 HAL 的成员，STM32CubeF1 的 `RTC_AlarmTypeDef` 没有它；闹钟中断的名字也要按上面写成 `RTC_Alarm_IRQn` 和 `RTC_Alarm_IRQHandler`。

## 动手实验

1. **实验一：拔掉电源，时间接着走。** 装上 CR2032，运行程序，在调试器里看 `g_time` 和 `g_date`。然后断开所有供电（USB 和调试器的 3.3 V），等一分钟再接回去，用调试器以不复位的方式连上（Keil 和 STM32CubeIDE 都有这个选项）再看一次。
   - 预期现象：`g_time` 比断电前多了大约那一分钟，`g_date` 还是断电前的日期，不是 2000-01-01；`g_reset_cause` 是 `RESET_POWER_ON`。
   - 怎么确认：断电前后各记一次手机上的时间和 `g_time`，两边的差应该相同。再把电池取下来重复一次：备份域掉了电，魔法值丢了，时间回到起始的 12:00:00。
   - 没成功先查：VBAT 上有没有 3 V；`g_time` 的秒在不在走（不走多半是 LSE 没起振）；RTCSEL 是不是 LSE。
2. **实验二：每天 08:30 的闹钟。** 把 `START_HOURS`、`START_MINUTES`、`START_SECONDS` 改成 8、29、50，再临时把 `RTC_BKP_MAGIC` 换一个值，让程序重新设时间，编译下载。
   - 预期现象：大约 10 s 后 PC13 的灯翻转一次，`g_alarm_count` 变成 1。RM0008 Rev 21 第 18.3.5 节说，闹钟标志在计数器从 08:30:00 走到 08:30:01 的那一刻置位，所以灯是在 08:30:01 出现时翻的。之后灯不再动，第二天 08:30 再翻一次。
   - 怎么确认：在 `HAL_RTC_AlarmAEventCallback` 里打断点，停下后单步回到主循环，看 `g_time` 是 08:30:01。想验证「明天还响」，把起始时间设成 23:59:50、闹钟设成 00:00:05，看过零点以后 `g_date` 加了一天，闹钟照样响。
   - 没成功先查：`RTC_Alarm_IRQn` 有没有在 NVIC 里打开；中断函数名是不是 `RTC_Alarm_IRQHandler`，写成别的名字不会报错，只是永远进不去；每次响过有没有重新调用 `alarm_arm_daily()`。
3. **实验三：让两只看门狗各咬一次。** 先把主循环里的 `HAL_IWDG_Refresh(&hiwdg);` 注释掉。恢复以后，按上面的说明加入窗口看门狗片段，但先把 `LOOP_PERIOD_MS` 改成 30。
   - 预期现象：不喂 IWDG 时，芯片大约每 1 s 复位一次，按 LSI 的范围在 0.667–1.333 s 之间，`g_reset_cause` 是 `RESET_IWDG`。WWDG 每 30 ms 左右喂一次时，第一次喂狗就复位，`g_reset_cause` 是 `RESET_WWDG`；`LOOP_PERIOD_MS` 改回 50 以后不再复位。
   - 怎么确认：逻辑分析仪接第 7 脚 NRST，每次复位都有一个至少 20 µs 的低脉冲（RM0008 Rev 21 第 7.1.2 节）。量出两个脉冲的间隔 T，就能反推这颗芯片的 LSI：f_LSI ≈ 64 × 625 ÷ T，例如 T = 1.10 s 时约 36.4 kHz。WWDG 那一半，喂狗时计数器才减了三十几拍，还在 0x5C 以上，高于窗口值 0x50，这就是复位的原因。
   - 没成功先查：IWDG 不咬，看主循环别处是不是还在调用 `HAL_IWDG_Refresh`，以及调试器是不是正停在断点上（冻结时不数）；WWDG 不咬，看 PCLK1 是不是 36 MHz、`HAL_WWDG_MspInit` 有没有打开 WWDG 时钟。

## 自测

1. LSI 正好跑在 60 kHz，预分频 64、Reload 624 的独立看门狗多久复位？喂狗间隔该怎么定？
2. 忘了写 PRL，RTC 用复位值 0x8000 跑在 32.768 kHz 的 LSE 上，一天差多少？快还是慢？
3. 窗口看门狗按本章设定（36 MHz、预分频 8、初值 0x7F、窗口 0x50），一个任务每 30 ms 喂一次会怎样？每 50 ms 呢？
4. 用本章例程，按一下复位键以后日期变成了 2000-01-01，时间却是对的。少了哪一步？
5. 现场设备重启了，RCC_CSR 里 IWDGRSTF 和 PINRSTF 都是 1。是谁引起的复位？读完要做什么？

参考答案：

1. T = 64 ÷ 60000 × (624 + 1) ≈ 0.667 s。喂狗间隔要明显小于 0.667 s，还要留出程序的抖动，本章取 200 ms。
2. 分频比变成 32768 + 1 = 32769，每一拍是 32769 ÷ 32768 s，比 1 s 长，所以钟慢。一天 86400 s 只走 86400 × 32768 ÷ 32769 ≈ 86397.36 拍，慢约 2.64 s，约合 30.5 ppm。
3. 一拍 = 4096 × 8 ÷ 36 MHz ≈ 0.910 ms。30 ms 是 32 到 33 拍，计数器在 0x5F 或 0x5E，高于 0x50，一喂就复位。50 ms 是 54 到 55 拍，计数器在 0x49 或 0x48，落在 0x4F 到 0x40 之间，正常；离 0x40 的 EWI 还有 6 ms 以上。
4. F1 HAL 的日期在 RAM 里的 `hrtc.DateToUpdate`，`HAL_RTC_Init` 每次都把它重置成 2000-01-01；秒计数器在备份域里没丢，所以时间对。要在复位后从备份寄存器读回年月日，直接填进 `hrtc.DateToUpdate`，日期变了再写回备份寄存器。不能用 `HAL_RTC_SetDate` 填，它会扔掉计数器里攒下的整天数。
5. 独立看门狗。每一种复位都会让 NRST 脚输出低脉冲，PINRSTF 常常跟着置位，所以判断时把它放在最后。读完写 RMVF 把标志一起清掉，否则下一次复位时分不清新旧。

## 原理与适用范围

> [!NOTE]
> 从这一节到「常见坑与出处」是深入部分，把前面的结论落到具体订货号、手册章节和能复算的数字上。第一次读可以先跳过，做完动手实验再回来对照。

**订货号与时钟。**这一章的看门狗和 RTC 结论只钉在订货号 STM32F103C8T6 上，LQFP48，中密度。1 秒整格照抄附录 D：预分频 64，Reload = 624，LSI 按典型 40 kHz 得到 625 Hz。LSI 的范围用 [DS5319 Rev 20 表 25](#source-ds5319-rtc) 的 30 / 40 / 60 kHz，不把 40 kHz 写成保证值。窗口看门狗的 PCLK1 = 36 MHz 来自第 02 章的时钟树：72 MHz 的 HCLK 经 APB1 二分频。

**一秒怎么算。**`T = 64 / 40000 × (624 + 1) = 1` s。Reload 写成 625 时，`(625 + 1) / 625` 多一个计数。同一套预分频和重载：LSI = 30 kHz 时 `64 / 30000 × 625 = 4/3` s；LSI = 60 kHz 时 `64 / 60000 × 625 = 2/3` s，正是 30 kHz 那一档的一半。附录 D 写「大约一半」，因为 30 kHz 和 60 kHz 是手册范围的两端，不是每颗料的实测。最长一档大约 26 s 这句沿用附录 D，RM0008 Rev 21 表 96 印的是 40 kHz 下的 26214.4 ms；LSI 跑在 30 kHz 时同一档是 `256 × 4096 / 30000 ≈ 34.95` s，所以这也不是保证的最大值。独立看门狗只在减到 0 时复位。喂早不复位。见 [RM0008 Rev 21 第 19 章](#source-rm0008-wdg)。

**上电就跑的独立看门狗。**`WDG_SW = 0` 时上电就由硬件看门狗接管，软件关不掉；为 1 时是软件看门狗，写 0xCCCC 才启动。这一位见 [PM0075](#source-pm0075-rdp)。硬件看门狗启动时，IWDG_PR 和 IWDG_RLR 还是复位值 0 和 0xFFF，按表 96 第一行，40 kHz 下 409.6 ms 就复位，60 kHz 下约 273 ms。本章例程启动时要等 LSE，可能要好几秒；改用硬件看门狗以后，HAL 等 LSE 的那几秒会被它打断，要先把 PR、RLR 改成 4 和 624，再自己写等 LSERDY 的循环，循环里喂狗。

**窗口看门狗。**窗口看门狗喂早和喂晚都会复位。PCLK1 = 36 MHz，预分频 8，计数初值 `0x7F`：超时 `(1/36e6) × 4096 × 8 × 64 = 58.25` ms。窗口值 `0x50` 时，计数器还大于 `0x50` 就喂狗，会立刻复位；计数器从 0x40 减到 0x3F 时也复位（RM0008 Rev 21 第 20.3 节）。窗口在 48 拍后打开，约 43.7 ms；EWI 在第 63 拍，约 57.3 ms。每个时刻最多提早一拍 0.91 ms，因为写 CR 时预分频器的相位未知；表 98 在 36 MHz、预分频 8 时给出 910 µs 到 58.25 ms。见 [RM0008 Rev 21 第 20 章](#source-rm0008-wdg)。

**4095 那一行。**Reload 写成最大值 4095 时，超时是 `(4095 + 1) / 625 = 6.5536` s，正好是表 96 里 64 分频那一行的最大值 6553.6 ms。这一行只作对照，不取代 Reload 624；主图只画 624 这一秒。

**LSE 与 PRL。**LSE 是 32.768 kHz，从第 3 脚 PC14-OSC32_IN 和第 4 脚 PC15-OSC32_OUT 进来。PRL = 32767 时 `(32767 + 1)` 把 32768 Hz 分成 1 Hz。PRL = 32768 不是 1 Hz，这是 RTC 的失败路径。RTC_PRLL 的复位值是 0x8000，停在复位值上就是这一行，每天慢约 2.64 s。DS5319 Rev 20 第 2.3.14 节说预分频「默认」从 32.768 kHz 产生 1 秒时基，和 RM0008 Rev 21 第 490 页的复位值对不上，以寄存器复位值和那一页的注（写 7FFFh）为准。LSI 典型 40 kHz，用整数 PRL 得不到跨 30–60 kHz 仍成立的 1 Hz。备份域由第 1 脚 VBAT 在主电源消失后续电。写之前打开 PWR 与 BKP 时钟，并置 `PWR_CR` 的 DBP。见 [RM0008 Rev 21 第 18 章](#source-rm0008-rtc)。

**HAL 的日期。**STM32CubeF1 的 HAL 把日期放在 RAM 里的 `hrtc.DateToUpdate`，`HAL_RTC_GetTime` 遇到计数器超过 24 小时，会把整天数折进日期并改写 CNT。RM0008 Rev 21 第 18.4.4 节说，PRL 或 CNT 一改，预分频计数器 DIV 就重新装载，这一秒里已经走过的零头随之丢掉；所以每次折算、每次 `HAL_RTC_Init` 重写 PRL，都可能让钟慢下不到 1 s。要求一天误差小于 1 s 的产品，直接读写 32 位计数器，自己换算日期。

**备份寄存器。**这颗中密度是 10 个 16 位备份数据寄存器，共 20 字节。42 个是大容量的说法，在 C8 上作废。F4 的 20 个 32 位备份寄存器和 BCD 的 `TR`/`DR` 在这颗料上作废。日历由软件从 32 位秒计数换算，依据就是这颗料只有一只 32 位计数器和 10 个 16 位寄存器。

**调试与冻结。**IWDG 在 Stop 和 Standby 里继续计数：RM0008 Rev 21 图 182 的注说它所在的电压域在这两种模式下仍然工作，DS5319 Rev 20 第 2.3.15 节也这样写。调试时可以冻住计数器，用章内的 `__HAL_DBGMCU_FREEZE_IWDG()`。RM0008 §19.3.3 印出的配置位名是 `DBG_IWDG_STOP`，这一节没有给位号。这个位所在的 DBGMCU_CR 只在上电复位时清零（第 31.16.3 节），看门狗复位以后冻结设置还在。

**引脚复用。**LSE 用着第 3 脚和第 4 脚时，这两只脚不再当 GPIO。PC13 若还当心跳灯，沿用第 03 章：只能灌电流，写 0 才亮，不重画那张 LED 图。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-11-iwdg-1s.svg" width="760" alt="Reload 624 在 40 kHz 典型值下是 1 秒；减到 0 才复位；LSE 要 PRL = 32767 才是 1 Hz">
  <br><sub>▲ 自绘。STM32F103C8T6。LSI 典型 40 kHz，范围 30–60 kHz。预分频 64，计数频率 625 Hz，Reload = 624，在减到 0 之前喂狗是 1 秒的典型账，不是保证值。失败路径是减到 0，或把 Reload 写成 625。备份域是第 1 脚 VBAT、第 3 脚 PC14、第 4 脚 PC15，32.768 kHz，PRL = 32767，10 个 16 位寄存器。PRL = 32768 不是 1 Hz。窗口看门狗在计数器大于 0x50 时喂狗会复位，超时 58.25 ms。出处是 [DS5319 Rev 20 表 25、第 2.3.14 节和第 2.3.15 节](#source-ds5319-rtc) 以及 [RM0008 Rev 21 第 19 章](#source-rm0008-wdg)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/iwdg-1s.gif" width="640" alt="625 Hz 的计数在减到 0 之前被喂狗，Reload = 624">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：625 Hz 的计数在减到 0 之前被喂狗，标出 Reload = 624 和 40 kHz 典型值。印刷以静态主图为准。减到 0、Reload = 625 和窗口看门狗的早喂不在这条 GIF 上。</sub>
</p>

图从上往下读。上半张是独立看门狗的账：同一只 625 Hz 的计数器有两条路，减到 0 之前喂狗，计数器回到 624，什么都不发生；一直不喂，减到 0，芯片复位。中间一条是备份域：第 1 脚接电池，第 3、4 脚接 32.768 kHz 晶振，PRL 写 32767 才是 1 Hz。最下面一行单独写窗口看门狗：计数器大于 0x50 时喂狗也复位，时间尺度是 58.25 ms，和上面的 1 秒不是同一只狗。

章首的 `iwdg-window.svg` 画的是带窗口的喂狗时序，那是窗口看门狗的行为。独立看门狗喂早不复位，以这张静态主图为准。

## 时序与状态

下表把这一章能复算的数放在一起，每一行都能用前面的公式算回去。看门狗的行出自 [RM0008 Rev 21 第 19、20 章](#source-rm0008-wdg)，RTC 的行出自 [RM0008 Rev 21 第 18 章](#source-rm0008-rtc)，LSI 的范围和备份寄存器出自 [DS5319 Rev 20](#source-ds5319-rtc)。

| 预分频或对象 | 时钟 | 重载或设定 | 计数 | 时间 | 结果 |
| --- | --- | --- | --- | --- | --- |
| 64 | 40 kHz | 624 | 625 | 1 s | 减到 0 才复位。喂早不复位 |
| 64 | 40 kHz | 625 | 626 | 多一个计数 | 不是 1 秒整 |
| 64 | 30 kHz | 624 | 625 | 4/3 s | 不是保证值 |
| 64 | 60 kHz | 624 | 625 | 2/3 s | 大约是 30 kHz 那一档的一半 |
| 4（复位值） | 40 kHz | 0xFFF（复位值） | 4096 | 409.6 ms | 硬件看门狗上电后的超时 |
| RTC | 32768 Hz | PRL = 32767 | 32768 | 1 Hz | 分频比是 (PRL + 1) |
| RTC 失败 | 32768 Hz | PRL = 32768 | 32769 | 不是 1 Hz | 每天慢约 2.64 s，改成 32767 |
| 备份寄存器 | — | 10 个 16 位 | 20 字节 | 第 1 脚 VBAT 续电 | 42 个在 C8 上作废 |
| WWDG | PCLK1 = 36 MHz | 预分频 8，初值 `0x7F` | 64 拍 | 58.25 ms | 计数器大于 `0x50` 时喂狗复位 |
| WWDG 窗口 | PCLK1 = 36 MHz | 窗口 `0x50` | 48 拍 | 约 43.7 ms | 从这里到 0x40 之前喂狗才不复位 |
| 64（对照） | 40 kHz | 4095 | 4096 | 6.5536 s | 不取代 Reload 624 |

**IWDG 的状态。**未启动，写 0xCCCC（或 `WDG_SW = 0` 时上电）进入计数。计数中写 0xAAAA，计数器回到 Reload；减到 0，复位。没有「停止」这个状态，只有复位能让它回到未启动（RM0008 Rev 21 第 5.3.4 节）。

**WWDG 的状态。**未启动，置 WDGA 进入计数。计数器大于窗口值时喂狗，复位；低于窗口值、高于 0x3F 时喂狗，回到 0x7F；到 0x40，进 EWI（如果开了）；到 0x3F，复位。

**RTC 写寄存器。**等 RTOFF = 1，置 CNF 进入配置模式，写 PRL、CNT 或 ALR，清 CNF，再等 RTOFF = 1。最后一步至少 3 个 RTCCLK 周期，32.768 kHz 下约 92 µs（RM0008 Rev 21 第 18.3.4 节）。

## 常见坑与出处

| 现象 | 原因 | 处理 | 出处 | 出处能证明的部分 |
| --- | --- | --- | --- | --- |
| 按 40 kHz 算的 1 秒，板上偏短或偏长 | 40 kHz 只是典型值 | Reload 用 624，并按 30–60 kHz 留余量 | [DS5319](#source-ds5319-rtc) | 表 25 的 fLSI 是 30 / 40 / 60 kHz。40 kHz 是典型值。这一秒不是保证值 |
| Reload 写成 625，超时比 1 秒多一拍 | 忘了计数是 (Reload + 1) 个 | 改成 624 | [RM0008](#source-rm0008-wdg) | 预分频 64、40 kHz 时计数频率 625 Hz。时间用 `(Reload + 1)`。625 多一个计数 |
| 以为在喂独立看门狗，却一喂就复位 | 实际开的是窗口看门狗，喂得太早 | IWDG 喂早没事；用 WWDG 就把喂狗放进窗口，本章设定是 43.7–57.3 ms | [RM0008](#source-rm0008-wdg) | IWDG 减到 0 才复位。WWDG 在计数器大于窗口值时喂狗也会复位。36 MHz 下 `0x7F` 与预分频 8 的超时是 58.25 ms |
| 主电源掉了，日历归零 | 备份域没有续电 | 接上第 1 脚 VBAT，RTC 时钟用第 3 脚和第 4 脚上的 LSE | [DS5319](#source-ds5319-rtc) | 第 1 脚 VBAT，第 3 脚 PC14-OSC32_IN，第 4 脚 PC15-OSC32_OUT。10 个 16 位备份寄存器共 20 字节。42 个在这颗料上作废 |
| PRL 写成 32768，或忘了写、停在复位值，秒节拍偏慢 | 分频比是 (PRL + 1) | 改成 32767 | [RM0008](#source-rm0008-rtc) | 分频比是 `(PRL + 1)`。32768 Hz 要写成 32767 才是 1 Hz。写备份域之前置 DBP |
| 断点停住以后自己复位 | 调试时计数器还在减 | 调试时冻住 IWDG | [RM0008](#source-rm0008-wdg) | §19.3.3 印出配置位名 `DBG_IWDG_STOP`。调试时可以冻住独立看门狗。这一节没有给位号 |
| 选项字节把看门狗改成上电就跑，软件关不掉 | `WDG_SW` 为 0 | `WDG_SW` 为 0 是硬件看门狗，为 1 才是软件看门狗 | [PM0075](#source-pm0075-rdp) | USER 字节的这一位：0 表示硬件看门狗，1 表示软件看门狗 |
| 第一次上电卡在 RTC 初始化，冬天卡得更久 | LSE 起振慢 | 起振等待留足，看门狗放在最后启动 | [DS5319](#source-ds5319) | 表 23 的 LSE 起振时间典型值：25 °C 时 2.5 s，−10 °C 时 10 s |
| LSE 怎么都不起振 | 晶振的负载电容太大 | 换 CL ≤ 7 pF 的晶振，不用 12.5 pF 的 | [DS5319](#source-ds5319) | 第 5.3.6 节：外接电容最大 15 pF，强烈建议 CL ≤ 7 pF，不要用 12.5 pF |
| 复位原因读出来总是好几面旗 | 上一次的旗没清，或 NRST 的旗跟着置位 | 读完写 RMVF；PINRSTF 放到最后判断 | [RM0008](#source-rm0008) | 第 7.3.10 节：复位标志只在上电复位时清零，写 RMVF 清除；RCC_CSR 复位值 0x0C00 0000 |

下面三条来自 STM32CubeF1 的 HAL 源码，不是手册内容，manifest 里没有对应的出处卡，所以不进表格：F1 HAL 的日期在 RAM 里的 `hrtc.DateToUpdate`，`HAL_RTC_Init` 把它重置成 2000-01-01，复位后日期要从备份寄存器填回去；`RTC_AlarmTypeDef` 没有 `AlarmMask`，那是 F4 HAL 的成员；启动文件里闹钟中断的向量名是 `RTC_Alarm_IRQHandler`，NVIC 用 `RTC_Alarm_IRQn`。

## 相关资源

- RM0008《STM32F10xxx 参考手册》第 18 章 RTC、第 19 章 IWDG、第 20 章 WWDG、第 5 章 PWR、第 6 章 BKP、第 7 章 RCC（LSE/LSI 配置）。
- RM0090《STM32F4 参考手册》第 26 章 RTC、IWDG/WWDG 对应章节。
- 数据手册 DS：LSE 起振条件、LSI 频率范围、VBAT 工作电压。
- 应用笔记 AN4759《Using the hardware real-time clock (RTC) in STM32》。
- 配图：`../assets/animations/iwdg-window.svg`（作者自绘矢量图）。

- 手机阅读版：[第 11 章 · RTC与看门狗（公众号图文）](https://mp.weixin.qq.com/s/MSNJ-MdVM15opQi3W20V1g)
