# rtc-alarm —— RTC 闹钟 + 唤醒中断 + 时间戳记录

> 难度：★★★☆　｜　涉及外设：RTC + PWR（STOP）+ 备份域　｜　对应章节：[11 RTC 与看门狗](../../docs/11-RTC与看门狗.md)

<p align="center">
  <img src="../../assets/animations/lowpower-wakeup.svg" width="760" alt="低功耗模式与唤醒源">
  <br><sub>▲ 动画：睡眠/停止/待机三种低功耗模式与唤醒源（作者自绘矢量图）</sub>
</p>

## 一、功能说明

配置 LSE 作为 RTC 时钟源，用 **RTC 闹钟中断**作为 **STOP 模式的唤醒源**：

- 解锁备份域，用 **BKP_DR1 存魔法值**判断是否首次上电，避免每次复位重设时间；
- 主循环设置「10 秒后」的闹钟，然后进入 **STOP 低功耗模式**，靠闹钟中断唤醒；
- 每次唤醒**记录一条时间戳**到环形日志，并翻转板载 LED；
- 唤醒后重新把系统时钟从 HSI 恢复到 72MHz。

## 二、硬件接线表

| 开发板 | 外设 | 引脚 | 接法 | 备注 |
| --- | --- | --- | --- | --- |
| BluePill | LSE 晶振 | PC14 (OSC32_IN)、PC15 (OSC32_OUT) | 焊 32.768kHz 晶振 + 2×负载电容 | 常用 6pF |
| BluePill | VBAT | VBAT 脚 | 接 3V 纽扣电池(CR2032) | 掉电继续走时 |
| BluePill | LED | PC13 | 板上已接 | 唤醒指示 |

> **LSE 不起振是「RTC 不走时」的头号原因**：负载电容按晶振手册选（常见 6pF / 12.5pF），
> 电容过大或走线过长都会导致不起振。

## 三、CubeMX 关键配置

| 配置项 | 取值 | 说明 |
| --- | --- | --- |
| RCC → LSE | Crystal/Ceramic Resonator | 32.768kHz |
| RCC → RTC Clock Source | LSE | 高精度走时 |
| RTC → Activate Clock Source | ✔ | 使能 RTC |
| RTC → Alarm A | Enabled，NVIC 使能 | 闹钟中断 |
| PWR | 使能（代码里 `__HAL_RCC_PWR_CLK_ENABLE`） | STOP 模式需要 |

## 四、关键代码解读

**1) 解锁备份域 + 配置 LSE**

```c
__HAL_RCC_PWR_CLK_ENABLE();
__HAL_RCC_BKP_CLK_ENABLE();
HAL_PWR_EnableBkUpAccess();               /* 写 RTC/BKP 前必须解锁备份域 */

RCC_OscInitTypeDef osc = {0};
osc.OscillatorType = RCC_OSCILLATORTYPE_LSE;
osc.LSEState       = RCC_LSE_ON;
HAL_RCC_OscConfig(&osc);                   /* LSE 不起振会返回错误 */
```

**2) 用备份寄存器判断首次上电**

```c
if (HAL_RTCEx_BKUPRead(&hrtc, RTC_BKP_DR1) != 0xA5A5) {
    HAL_RTC_SetTime(&hrtc, &t, RTC_FORMAT_BIN);   /* 首次才设时间 */
    HAL_RTC_SetDate(&hrtc, &d, RTC_FORMAT_BIN);
    HAL_RTCEx_BKUPWrite(&hrtc, RTC_BKP_DR1, 0xA5A5);
}
```

`BKP_DRx` 由 VBAT 供电，主电源掉电也不丢，是「是否初始化过」的可靠标志。

**3) 设置闹钟（当前时间 + N 秒）**

```c
uint32_t secs = t.Hours*3600 + t.Minutes*60 + t.Seconds;
secs = (secs + 10) % 86400;               /* 当天内取模 */
alarm.AlarmTime.Hours   = secs/3600;
alarm.AlarmTime.Minutes = (secs%3600)/60;
alarm.AlarmTime.Seconds = secs%60;
alarm.AlarmMask         = RTC_ALARMMASK_DATEWEEKDAY;   /* 忽略日期 */
HAL_RTC_SetAlarm_IT(&hrtc, &alarm, RTC_FORMAT_BIN);
```

**4) STOP 模式 + 闹钟唤醒**

```c
HAL_SuspendTick();                         /* 挂起 SysTick，否则它会唤醒 */
HAL_PWR_EnterSTOPMode(PWR_LOWPOWERREGULATOR_ON, PWR_STOPENTRY_WFI);
/* —— 闹钟中断把 MCU 唤醒，继续执行 —— */
HAL_ResumeTick();
SystemClock_Config();                      /* STOP 后时钟回 HSI，需恢复 72MHz */
```

> 进入 STOP 后 CPU 停摆、SRAM 保持，功耗降到 µA 级；**任意 EXTI 中断**都能唤醒，
> RTC 闹钟正是通过 EXTI17 接入的。

## 五、编译烧录步骤

1. CubeMX 生成 F103C8 工程，使能 LSE 与 RTC Alarm，覆盖 `Core/Src/main.c`
   （若生成代码已有 `RTCAlarm_IRQHandler`，删除以免重复）。
2. 编译下载；用调试器观察 `g_log[]` 里的时间戳，或接串口打印。

## 六、预期现象

- 上电后板载 LED 每约 10 秒翻转一次（每次闹钟唤醒）；
- `g_log[]` 中按顺序记录唤醒时刻的时/分/秒，间隔 10 秒；
- 接上 VBAT 电池后断电再上电，时间连续不归零。

## 七、常见问题

| 现象 | 原因 | 解决 |
| --- | --- | --- |
| RTC 不走/上电归零 | LSE 未起振、VBAT 未接 | 换 6pF 电容，接电池 |
| LSE 起振失败 | 负载电容过大/走线长 | 减小电容，缩短走线 |
| 闹钟不触发 | 没使能 NVIC/EXTI17 | `HAL_NVIC_EnableIRQ(RTCAlarm_IRQn)` |
| 时间被反复重置 | 没写魔法值/备份域没解锁 | `HAL_PWR_EnableBkUpAccess` + BKP 魔法值 |
| 唤醒后串口乱码 | STOP 后时钟回 HSI | 唤醒后 `SystemClock_Config()` |
| 进不了 STOP | SysTick 一直中断 | `HAL_SuspendTick()` 后再进 STOP |
| 年份/月份错乱 | F1 日历需软件换算 | 用标准秒↔日历换算，核对基准 |

## 八、相关资源

- 参考手册 **RM0008** 第 16 章（RTC）、第 5 章（PWR）、第 6 章（BKP）、第 7 章（RCC LSE/LSI）
- 应用笔记 AN4759《Using the hardware real-time clock (RTC) in STM32》
- 相关图：[`assets/animations/iwdg-window.svg`](../../assets/animations/iwdg-window.svg)、[`assets/animations/lowpower-wakeup.svg`](../../assets/animations/lowpower-wakeup.svg)
- 免责声明：本示例配图为作者自绘矢量图/程序生成动画，非厂商实拍照片。
