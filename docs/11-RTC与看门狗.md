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
  <br><sub>▲ 本章讲解 2.6 分钟。配音是微软 Edge 在线神经语音「晓晓」（zh-CN-XiaoxiaoNeural），经 edge-tts 调用。edge-tts 大部分源码为 LGPLv3，srt_composer.py 为 MIT；声线模型是微软在线服务，不是开放模型。这里提交的是合成后的 MP4，离线可看。重新生成需要联网。画面由脚本和本仓库 SVG 生成，不是实拍。 视频：<a href="../assets/video/ch11-rtc.mp4">MP4</a> · 字幕：<a href="../assets/video/ch11-rtc.srt">SRT</a>。由 <code>python3 tools/gen_narrated.py --speak</code> 用 ffmpeg 合成。</sub>
</p>

**旁白（与字幕、配音同一份稿）**

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
<!-- /video:ch11 -->

## 原理与边界

这一章的看门狗和 RTC 结论只钉在订货号 STM32F103C8T6 上。1 秒整格照抄附录 D：预分频 64，Reload = 624，LSI 按典型 40 kHz 得到 625 Hz。LSI 的范围用表 25 的 30 / 40 / 60 kHz，不把 40 kHz 写成保证值。

`T = 64 / 40000 × (624 + 1) = 1` s。Reload 写成 625 时，`(625 + 1) / 625` 多一个计数。同一套预分频和重载：LSI = 30 kHz 时 `64 / 30000 × 625 = 4/3` s；LSI = 60 kHz 时 `64 / 60000 × 625 = 2/3` s，正是 30 kHz 那一档的一半。附录 D 写「大约一半」，因为 30 kHz 和 60 kHz 是手册范围的两端，不是每颗料的实测。最长一档大约 26 s 这句沿用附录 D，不另编一个保证的最大值。独立看门狗只在减到 0 时复位。喂早不复位。见 [RM0008 Rev 21 第 19 章](#source-rm0008-wdg) 和 [DS5319 Rev 20 表 25](#source-ds5319-rtc)。

窗口看门狗喂早和喂晚都会复位。PCLK1 = 36 MHz，预分频 8，计数初值 `0x7F`：超时 `(1/36e6) × 4096 × 8 × 64 = 58.25` ms。窗口值 `0x50` 时，计数器还大于 `0x50` 就喂狗，会立刻复位。这是旁注，不是 IWDG 的主波形。

若片段留下 Reload = 4095，超时写成 `(4095 + 1) / 625 = 6.5536` s。动手实验里的「约 6.5 s」可以留下，不进四块的主账。主图只画 624 这一秒。

LSE 是 32.768 kHz，从第 3 脚 PC14-OSC32_IN 和第 4 脚 PC15-OSC32_OUT 进来。PRL = 32767 时 `(32767 + 1)` 把 32768 Hz 分成 1 Hz。PRL = 32768 不是 1 Hz。这是 RTC 的失败路径。LSI 典型 40 kHz，用整数 PRL 得不到跨 30–60 kHz 仍成立的 1 Hz。备份域由第 1 脚 VBAT 在主电源消失后续电。写之前打开 PWR 与 BKP 时钟，并置 `PWR_CR` 的 DBP。见 [RM0008 Rev 21 第 18 章](#source-rm0008-rtc)。

这颗中密度是 10 个 16 位备份数据寄存器，共 20 字节。42 个是大容量的句子，在 C8 上作废。F4 的 20 个 32 位备份寄存器和 BCD 的 `TR`/`DR` 在这颗料上作废。日历由软件从 32 位秒计数换算。这句由「这颗料是 32 位计数器、10 个 16 位寄存器」支持，不新开 F4 RTC 的 id。

IWDG 在 Stop 和 Standby 里继续计数。调试时可以冻住计数器，沿用章内的 `__HAL_DBGMCU_FREEZE_IWDG()`。RM0008 §19.3.3 印出的配置位名是 `DBG_IWDG_STOP`。不编位号。`WDG_SW = 0` 时上电就由硬件看门狗接管，软件关不掉；为 1 时是软件看门狗。这句链接 [PM0075](#source-pm0075-rdp)，不在第 01 章展开。

LSE 用着第 3 脚和第 4 脚时，这两只脚不再当 GPIO。PC13 若还当心跳灯，沿用第 03 章：只能灌电流，写 0 才亮，不重画那张 LED 图。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-11-iwdg-1s.svg" width="760" alt="Reload 624 在 40 kHz 典型值下是 1 秒；减到 0 才复位；LSE 要 PRL = 32767 才是 1 Hz">
  <br><sub>▲ 自绘。STM32F103C8T6。LSI 典型 40 kHz，范围 30–60 kHz。预分频 64，计数频率 625 Hz，Reload = 624，在减到 0 之前喂狗是 1 秒的典型账，不是保证值。失败路径是减到 0，或把 Reload 写成 625。备份域是第 1 脚 VBAT、第 3 脚 PC14、第 4 脚 PC15，32.768 kHz，PRL = 32767，10 个 16 位寄存器。PRL = 32768 不是 1 Hz。窗口看门狗在计数器大于 0x50 时喂狗会复位，超时 58.25 ms。出处是 [DS5319 Rev 20 表 25、第 2.3.14 节和第 2.3.15 节](#source-ds5319-rtc) 以及 [RM0008 Rev 21 第 19 章](#source-rm0008-wdg)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/iwdg-1s.gif" width="640" alt="625 Hz 的计数在减到 0 之前被喂狗，Reload = 624">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：625 Hz 的计数在减到 0 之前被喂狗，标出 Reload = 624 和 40 kHz 典型值。印刷以静态主图为准。减到 0、Reload = 625 和窗口看门狗的早喂不在这条 GIF 上。</sub>
</p>

`iwdg-window.svg` 留作辅图。不播放它。喂早也复位的那一条属于窗口看门狗，已经改在章首图注里，不在这张静态主图上冒充 IWDG。

## 时序或状态

| 预分频 | f_LSI | Reload | (Reload + 1) | 时间 | 复位与否 |
| --- | --- | --- | --- | --- | --- |
| 64 | 40 kHz | 624 | 625 | 1 s | 减到 0 才复位。喂早不复位 |
| 64 | 40 kHz | 625 | 626 | 多一个计数 | 不是 1 秒整 |
| 64 | 30 kHz | 624 | 625 | 4/3 s | 不是保证值 |
| 64 | 60 kHz | 624 | 625 | 2/3 s | 大约是 30 kHz 那一档的一半 |
| RTC | 32768 Hz | PRL = 32767 | 32768 | 1 Hz | 分频比是 (PRL + 1) |
| RTC 失败 | 32768 Hz | PRL = 32768 | 32769 | 不是 1 Hz | 改成 32767 |
| 备份寄存器 | — | 10 个 16 位 | 20 字节 | 第 1 脚 VBAT 续电 | 42 个在 C8 上作废 |
| WWDG | PCLK1 = 36 MHz | 预分频 8，初值 `0x7F` | — | 58.25 ms | 计数器大于 `0x50` 时喂狗复位 |
| 对照 | 64 | 4095 | 4096 | 6.5536 s | 不取代 Reload 624 |

## 坑与出处卡

| 现象 | 原因 | 处理 | 出处 | 该来源允许支持的主张 |
| --- | --- | --- | --- | --- |
| 按 40 kHz 算的 1 秒，板上偏短或偏长 | 40 kHz 只是典型值 | Reload 用 624，并按 30–60 kHz 留余量 | [DS5319](#source-ds5319-rtc) | 表 25 的 fLSI 是 30 / 40 / 60 kHz。40 kHz 是典型值。这一秒不是保证值 |
| Reload 写成 625，超时比 1 秒多一拍 | 少算了一次 +1 的位置 | 改成 624 | [RM0008](#source-rm0008-wdg) | 预分频 64、40 kHz 时计数频率 625 Hz。时间用 `(Reload + 1)`。625 多一个计数 |
| 独立看门狗一喂就复位，像有窗口 | 把它当成了窗口看门狗 | 喂早对 IWDG 是允许的。要窗口用 WWDG | [RM0008](#source-rm0008-wdg) | IWDG 减到 0 才复位。WWDG 在计数器大于窗口值时喂狗也会复位。36 MHz 下 `0x7F` 与预分频 8 的超时是 58.25 ms |
| 主电源掉了日历归零 | 备份域没有续电，或 PRL 不对 | 接上第 1 脚 VBAT，LSE 用第 3 脚和第 4 脚，PRL 写 32767 | [DS5319](#source-ds5319-rtc) | 10 个 16 位备份寄存器由 VBAT 续电。默认 1 秒时基来自 32.768 kHz。42 个在这颗料上作废 |
| 预分频写成 32768，秒脉冲偏慢 | 分频比是 (PRL + 1) | 改成 32767 | [RM0008](#source-rm0008-rtc) | 分频比是 `(PRL + 1)`。32768 Hz 要写成 32767 才是 1 Hz |
| 断点停住以后自己复位 | 调试时计数器还在减 | 调试时冻住 IWDG | [RM0008](#source-rm0008-wdg) | §19.3.3 印出配置位名 `DBG_IWDG_STOP`。调试时可以冻住独立看门狗。不编位号 |
| 选项字节把看门狗改成上电就跑，软件关不掉 | `WDG_SW` 为 0 | `WDG_SW` 为 0 是硬件看门狗，为 1 才是软件看门狗 | [PM0075](#source-pm0075-rdp) | USER 字节的这一位：0 表示硬件看门狗，1 表示软件看门狗 |

## 📌 学习目标

- [ ] 掌握 RTC 的四种时钟源（LSE/LSI/HSE/128）取舍，理解备份域与 VBAT。
- [ ] 会用 BKP 备份寄存器保存标志，判断是否首次上电。
- [ ] 会配置日历、闹钟、周期唤醒、时间戳。
- [ ] 说清 IWDG 与 WWDG 的区别，并给出正确的喂狗策略。
- [ ] 会排查「RTC 不走时」「LSE 不起振」「看门狗误复位」等问题。

## 🧠 核心原理

### 1. RTC 与备份域

**结论**：RTC 位于**备份域**，由 `VBAT` 供电，主电源掉电后仍能走时；时钟源优先选 **LSE 32.768 kHz**（精度最高）。

| 时钟源 | 频率 | 精度 | 引脚占用 | 适用 |
| --- | --- | --- | --- | --- |
| LSE（外部 32.768 kHz 晶振） | 32.768 kHz | 由晶振决定。±20 ppm 不进四块 | PC14/PC15 | 需要准确走时 |
| LSI（内部 RC） | 最小 30 kHz，典型 40 kHz，最大 60 kHz | 表 25 的范围，不是 ±50% | 无 | 省引脚/仅做唤醒 |
| HSE/128（主晶振分频） | 8 MHz/128 | 取决于 HSE | 占用 HSE | 已有高精度主晶振 |
| RTC 预分频 | — | 由 `PRL` 设定 | — | 把源频率分到 1 Hz |

- F1 的 RTC 是一个 **32 位秒计数器**，日历（年月日时分秒）需软件把秒数换算；F4 及以上内置 **BCD 硬件日历**（`TR`/`DR` 寄存器），带星期与闰年自动处理。
- 备份域访问要先使能 `PWR` 与 `BKP` 时钟，并解锁备份域（`PWR_CR.DBP`，见 RM0008 第 5 章 PWR / 第 6 章 BKP）。

### 2. BKP 备份寄存器

**结论**：`BKP_DRx` 由 `VBAT` 供电，主电源掉电也不丢，常用来保存「是否首次上电」「校准参数」等标志。

| 系列 | 备份寄存器 | 位数 |
| --- | --- | --- |
| STM32F103C8T6 | `BKP_DR1`~`BKP_DR10`，10 个 16 位，共 20 字节。42 个是大容量，在这颗料上作废 | 16 位 |
| STM32F4 | `RTC_BKP_DR0`~`DR19` | 32 位 |

典型用法：上电先读一个「魔法值」（如 `0xA5A5`），若匹配说明之前初始化过，直接读时间；否则写入魔法值并初始化日历。

### 3. 日历、闹钟、唤醒与时间戳

| 功能 | 说明 | 关键寄存器 |
| --- | --- | --- |
| 日历 | 秒/分/时/日/月/年（F1 需软件换算，F4 硬件 BCD） | `RTC_TR`/`RTC_DR`（F4） |
| 闹钟 Alarm | 与计数器比较，到点产生中断/事件 | `RTC_ALR`（F1）/`RTC_ALRMxR`（F4） |
| 周期唤醒 Wakeup | 按固定周期自动唤醒，配合 STOP 省电 | `RTC_WUTR`（F4） |
| 时间戳 Timestamp | 引脚上升沿记录当前时间 | `RTC_TSTR`/`RTC_TSDR`（F4） |

> F1 的闹钟是比较**秒计数器**；F4 可按「秒/分/时/日/月/星期」掩码匹配，更灵活。

### 4. IWDG 与 WWDG 对比

**结论**：IWDG 时钟独立、能兜底，是**安全底线**；WWDG 精度高、有喂狗窗口，能**检测程序时序异常**。二者可同时使用。

| 项 | IWDG（独立看门狗） | WWDG（窗口看门狗） |
| --- | --- | --- |
| 时钟源 | LSI（独立，与主时钟无关） | PCLK1（APB1） |
| 计数器 | 12 位递减 + 8 位预分频 | 7 位递减（`T[6:0]`） |
| 复位条件 | 计数到 0 前未喂狗 | **喂太早（>W[6:0]）或太晚（<0x40）都复位** |
| 窗口 | 无（随时可喂） | 有（`WWDG_CFR.W[6:0]` 设定） |
| 精度 | 差（LSI 温漂大） | 好（跟随 PCLK1） |
| 超时范围 | 约 0.1 ms ~ 26 s | 约 0.1 ms ~ 60 ms |
| 典型场景 | 死机兜底、低功耗 | 检测周期性任务是否按时执行 |
| F1 章节 | RM0008 第 19 章 | RM0008 第 20 章 |

独立看门狗喂早不复位。喂早也复位的是窗口看门狗。

**喂狗策略**：

- **主循环喂狗**：最简单，但若某个子函数死循环就失效。
- **定时器/中断喂狗**：适合 IWDG，但中断卡死也会误复位。
- **多任务各喂一次**：RTOS 中让每个关键任务都喂，任一任务卡死即复位。
- **WWDG 窗口**：强制在「不太早、不太晚」的窗口内喂，能发现「跑太快」（如时钟异常）和「跑太慢」。

## 🛠️ 硬件与接线

| 开发板 | 外设 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill (F103) | LSE 晶振 | PC14=OSC32_IN、PC15=OSC32_OUT | 焊 32.768 kHz 晶振，负载电容按晶振手册选择 |
| BluePill | VBAT | VBAT 脚 | 接 3 V 纽扣电池（CR2032）维持走时 |
| BluePill | 备用 LED | PC13 | 常用于心跳指示 |
| Nucleo-F411RE | LSE | PC14/PC15 | 板上已焊 32.768 kHz |
| 任意 | 看门狗 | 无需引脚 | 纯片内 |

> ⚠️ 负载电容按晶振手册选择。四块不写皮法。电容过大时 LSE 可以不起振。

## 💻 代码实现

**① RTC 初始化 + 读时间（F1，LSE 源）**

```c
#include "stm32f1xx_hal.h"

RTC_HandleTypeDef hrtc;

static void MX_RTC_Init(void)
{
    __HAL_RCC_PWR_CLK_ENABLE();
    __HAL_RCC_BKP_CLK_ENABLE();

    hrtc.Instance          = RTC;
    hrtc.Init.AsynchPrediv = RTC_AUTO_1_SECOND;   /* F1 预分频到 1Hz */
    hrtc.Init.OutPut       = RTC_OUTPUTSOURCE_NONE;
    HAL_RTC_Init(&hrtc);

    /* 首次上电（BKP 无魔法值）才设置时间 */
    if (HAL_RTCEx_BKUPRead(&hrtc, RTC_BKP_DR1) != 0xA5A5) {
        RTC_TimeTypeDef t = { .Hours = 12, .Minutes = 0, .Seconds = 0 };
        RTC_DateTypeDef d = { .Year = 26, .Month = RTC_MONTH_JANUARY,
                              .Date = 7, .WeekDay = RTC_WEEKDAY_WEDNESDAY };
        HAL_RTC_SetTime(&hrtc, &t, RTC_FORMAT_BIN);
        HAL_RTC_SetDate(&hrtc, &d, RTC_FORMAT_BIN);
        HAL_RTCEx_BKUPWrite(&hrtc, RTC_BKP_DR1, 0xA5A5);   /* 存魔法值 */
    }
}

void RTC_PrintTime(void)
{
    RTC_TimeTypeDef t; RTC_DateTypeDef d;
    HAL_RTC_GetTime(&hrtc, &t, RTC_FORMAT_BIN);
    HAL_RTC_GetDate(&hrtc, &d, RTC_FORMAT_BIN);   /* 读日期会锁存时间寄存器 */
    printf("20%02d-%02d-%02d %02d:%02d:%02d\r\n",
           d.Year, d.Month, d.Date, t.Hours, t.Minutes, t.Seconds);
}
```

**② 闹钟中断**

```c
void MX_RTC_Alarm_Init(void)
{
    RTC_AlarmTypeDef alarm = {0};
    alarm.AlarmTime.Hours   = 8;
    alarm.AlarmTime.Minutes = 30;
    alarm.AlarmTime.Seconds = 0;
    alarm.AlarmMask         = RTC_ALARMMASK_DATEWEEKDAY;  /* 每天触发 */
    HAL_RTC_SetAlarm_IT(&hrtc, &alarm, RTC_FORMAT_BIN);
}

void HAL_RTC_AlarmAEventCallback(RTC_HandleTypeDef *hrtc)
{
    /* 到点回调，可置标志唤醒主循环 */
}
```

**③ 独立看门狗 IWDG**

```c
IWDG_HandleTypeDef hiwdg;

static void MX_IWDG_Init(void)
{
    hiwdg.Instance       = IWDG;
    hiwdg.Init.Prescaler = IWDG_PRESCALER_64;   /* LSI≈40kHz /64 = 625Hz */
    hiwdg.Init.Reload    = 4095;                /* 超时 (4095 + 1) / 625 = 6.5536 s。四块的主账仍是 Reload 624 的 1 秒 */
    HAL_IWDG_Init(&hiwdg);
}

/* 主循环里定期喂狗（不要放在中断里，否则中断卡死也救不了） */
HAL_IWDG_Refresh(&hiwdg);
```

**④ 窗口看门狗 WWDG**

```c
WWDG_HandleTypeDef hwwdg;

static void MX_WWDG_Init(void)
{
    hwwdg.Instance       = WWDG;
    hwwdg.Init.Prescaler = WWDG_PRESCALER_8;    /* PCLK1/4096/8 */
    hwwdg.Init.Window    = 0x50;                /* 窗口上界 */
    hwwdg.Init.Counter   = 0x7F;                /* 初值，超时 ≈ 58.25ms @36MHz */
    hwwdg.Init.EWIMode   = WWDG_EWI_ENABLE;     /* 使能早唤醒中断 */
    HAL_WWDG_Init(&hwwdg);
}

/* 必须落在 [0x40, 0x50] 窗口内喂狗 */
HAL_WWDG_Refresh(&hwwdg);
```

## 🧪 动手实验

1. **掉电走时**：焊上 LSE 晶振与 VBAT 纽扣电池，串口每秒打印时间；断电再上电。预期：时间连续，不会归零。
2. **每天定时闹钟**：设置每天 08:30 闹钟，到点在回调里点亮 LED。预期：到点触发一次，其余时间不动作。
3. **看门狗压力测试**：IWDG 超时设为 6.5 s；在代码里故意 `while(1)` 死循环不喂狗。预期：约 6.5 s 后芯片自动复位。
4. **（进阶）窗口看门狗检测时序**：用 WWDG 窗口检测一个周期性任务；把任务延迟调大到超时，观察复位；把任务改得过快（喂太早），同样复位。

### 超时怎么算，调试时怎么冻住

**结论**：`T = 预分频 ÷ f_LSI × (Reload + 1)`。`IWDG_PRESCALER_64` 在 LSI 典型 40 kHz 下是 625 Hz，想要 1 秒要把 Reload 写成 **624**，写成 625 会多一个计数。

LSI 的数据手册范围大约 30~60 kHz，40 kHz 只是典型值。超时要留余量，不要卡在标称值上。

| 看门狗 | 什么时候复位 | 时间尺度 |
| --- | --- | --- |
| IWDG | 只在喂晚了（减到 0） | 约 0.1 ms ~ 26 s |
| WWDG | 喂早了或喂晚了都复位 | F103 @ 36 MHz 大约 0.1~58 ms |

单步调试会被 IWDG 复位。在选项或调试寄存器里冻住它：

```c
__HAL_DBGMCU_FREEZE_IWDG();   /* F1 在 DBGMCU->CR，F4 在 APB1FZ，宏会选对寄存器 */
__HAL_DBGMCU_FREEZE_WWDG();
```

IWDG 一旦 `HAL_IWDG_Init` 成功就停不下来，只有复位能关。选项字节里把 `WDG_SW` 写成 0，上电就由硬件看门狗接管，软件想关也关不掉。

口诀：**1 秒是 624 不是 625；IWDG 怕喂晚，WWDG 早晚都怕；调试先冻计数器。**

自测：

1. 预分频 64、Reload 624、LSI 按 40 kHz，超时是不是刚好 1 秒？差在哪一个“+1”？
2. 窗口看门狗在计数器还大于窗口值时喂狗，会发生什么？
3. 为什么断点停在 `HAL_Delay` 里，板子会自己复位？

## 🔗 相关资源

- RM0008《STM32F10xxx 参考手册》第 18 章 RTC、第 19 章 IWDG、第 20 章 WWDG、第 5 章 PWR、第 6 章 BKP、第 7 章 RCC（LSE/LSI 配置）。
- RM0090《STM32F4 参考手册》第 26 章 RTC、IWDG/WWDG 对应章节。
- 数据手册 DS：LSE 起振条件、LSI 频率范围、VBAT 工作电压。
- 应用笔记 AN4759《Using the hardware real-time clock (RTC) in STM32》。
- 配图：`../assets/animations/iwdg-window.svg`（作者自绘矢量图）。

- 📱 手机阅读版：[第 11 章 · RTC与看门狗（公众号图文）](https://mp.weixin.qq.com/s/MSNJ-MdVM15opQi3W20V1g)