# s14-pwr 事实底稿（v2）

本集是「通往单片机之路 S14 · 低功耗三档」。屏幕上出现的每个测量值只来自 `code/stm32/14-pwr/probe.sh` 的本机实跑输出；模式能力/电流量级一类文字若上屏，须标注为数据手册口径，不写成实测。

## 取证环境与复现

- 复现：`cd code/stm32/14-pwr && sh probe.sh`
- 宿主：gcc 16.1.0（`probe.c` 把 PWR/CSR、RCC、SCB、SysTick、DBGMCU、BKPSRAM 全改指假寄存器后 `#include "main.c"`，断言跑固件本体）
- 交叉：xPack GNU Arm Embedded GCC 15.2.1（text 788 / data 4 / bss 4）
- 头文件对账：`stm32f407xx.h` / `core_cm4.h`，29 条位号 diff 为空；10 个寄存器地址 base+offset 全部对上
- 本集事实日志：`.temp/v2-facts/s14-probe.log`

## 一、三档定档：只有两个位在动（`mode-words`）

```
Sleep    CR=0x00004200 SCR=0x00000010   SLEEPDEEP=0 PDDS=0
Stop     CR=0x00004201 SCR=0x00000014   SLEEPDEEP=1 PDDS=0 LPDS=1
Standby  CR=0x00004202 SCR=0x00000014   SLEEPDEEP=1 PDDS=1 LPDS=0
```

- `SCB_SCR.SLEEPDEEP` bit2：Sleep 清 0，Stop/Standby 置 1。
- `PWR_CR.PDDS` bit1：Stop 清 0，Standby 置 1。
- `PWR_CR.LPDS` bit0：Stop 置 1；Standby 清 0（主调压器都要关了，LPDS 无意义）。
- `0x4200` 那个底子（VOS=1、FPDS=1、SEVONPEND=0x10）跟睡多深无关，三档都保留。

## 二、醒来那笔时钟账（`stop-bill`）

- 运行 HCLK 168000000 Hz，醒来 HSI 16000000 Hz，比例 **10.5**（不是"十倍左右"）。
- SysTick 1ms 装载值：运行档 `167999`；醒来档 `15999`。
- 不改装载值 → 真实周期 `105000`（µs×10）= **10500 µs**；改对 → `10000`（µs×10）= 1000 µs。
- USART：`BRR=729`（0x2D9）按 PCLK2=84000000 配 → 115226.0 baud，误差 +0.023%；醒来 PCLK2=8000000，BRR 仍旧 → 实际 **10973 baud**；重算应得 **BRR=69**（0x45）。
- 结论口径：Stop 醒来不是崩溃，是"数全错"；凡是 `数 = 时钟 / 目标` 的寄存器都要重算。

## 三、看门狗在 Stop 里还在数（`iwdg`）

LSI 不归 Stop 管，IWDG 继续计数。`PR` 3 位 = 8 个码，只有 7 档分频（`RLR=4095`，LSI≈32kHz）：

| PR | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| 分频 | /4 | /8 | /16 | /32 | /64 | /128 | /256 | /256 |
| 超时 ms | 511 | 1023 | 2047 | 4095 | 8190 | 16380 | 32760 | 32760 |
| LSI ±5% | 485~536 | 971~1074 | 1944~2149 | 3890~4299 | 7780~8599 | 15561~17199 | 31122~34398 | 同左 |

- `PR=6` 与 `PR=7` 实测同一个分频（断言 0x100）。
- 按"8 个码 = /512"想 → 65520 ms（0xFFF0），正好两倍；LSI ±5% 盖不住。
- 本工程查表，不写 `4 << pr`。

## 四、备份域：解锁之前写进去的是空气（`bkp`）

- BKPSRAM 容量 1024 个 32 位字（0x400）。
- 返回码：`DBP=0` 就写 → **−1**；`DBP` 有、备份调压器没开 → **−2**；`n > 1024` → **−3**；三关全过 → **0**。
- 前两关失败时备份 SRAM 仍为 0：断言证明"写进去的确实是空气"。
- 四笔解锁：`RCC_APB1ENR.PWREN`(bit28)、`PWR_CR.DBP`(bit8)、`PWR_CSR.BRE`(bit9)、`RCC_AHB1ENR.BKPSRAMEN`(bit18)、`RCC_BDCR.RTCEN`(bit15)。
- 就绪回执是 `PWR_CSR.BRR`(bit3)，不是 `BRE`：第一遍读回执=1（没就绪），置上 BRR 后第二遍=0。
- 遗言实测：第一个字 `0xA5A5A5A5`、第三个字 `0xDEADBEEF`。
- 取舍：越界整笔拒掉，不写一半——半份状态看起来是完整的。

## 五、唤醒源：睡前不配，WFI 就是睡死（`wake`）

- 没使能 EWUP 时 PA0/WKUP 叫不醒；RTC 闹钟走 EXTI17；PVD 走 EXTI16；RTC 唤醒走 EXTI18。
- `EXTI` 屏蔽寄存器写 `1<<17` = `0x00020000`（RTC 闹钟在硬件上就是这一根线）。
- `EWUP` 管不到 `EXTI17`；配了闹钟不等于配了唤醒定时器。

## 六、醒来是哪一种醒（`rstcause`）

| 现场 | RCC_CSR | PWR_CSR | 解码 |
|---|---|---|---|
| 刚上电 | 0x0C000000 | 0x00000000 | 0x0C（POR+PIN） |
| Standby 醒来 | 0x08000000 | 0x00000002 | 0x09（SBF+PORRSTF） |
| 看门狗 | 0x20000000 | 0x00000000 | 0x20（IWDGRSTF） |
| 软复位 | 0x10000000 | 0x00000000 | 0x10（SFTRSTF） |
| 欠压+BOR | 0x82000000 | 0x00000000 | 0x82（BORRSTF+LPWRRSTF） |

- 读完必须写 `RCC_CSR.RMVF`(bit24)；不清标志，下次开机照抄上次结论。
- 全零 = 分不清（标志已被清过）。

## 七、固件本体跑一遍（`firmware_main` 段）

- 跑完：`CR=0x00004205 SCR=0x00000004 DBGMCU=0x00000030 LOAD=0x00003E7F CSR=0x00000001`。
- 调试三位被清、其余保留（`0x30`）；醒来 `SLEEPDEEP=1`、`PDDS=0`、`LPDS=1`。
- 有 WUF → 发 `CWUF`(bit2)；有 SBF → 发 `CSBF`(bit3)；上一轮没有 SBF 就不该发 CSBF。
- SysTick 装载值按 16MHz 改成 `0x3E7F`（15999）。
- Standby 不碰 SysTick 装载值（醒来是复位，改了也白改）。

## 八、-O2 指令流（`disasm-*`）

- `enter_sleep` @1d0：SCR 清 bit2、CR 原样写回、`dsb sy` @1e6、`wfi` @1ea；wfi 之后 1 条/2 字节。
- `enter_stop` @1f4：CR 清 PDDS、置 LPDS；SCR 置 SLEEPDEEP；`dsb sy` @212、`wfi` @216；wfi 之后 6 条/14 字节（醒来重配 SysTick，LOAD 写 `15999`）。
- `enter_standby` @234：CR 清 LPDS、置 PDDS；SCR 置 SLEEPDEEP；`dsb sy` @254、`wfi` @258；wfi 之后 7 条/18 字节，含一次 `reset_cause_decode` 调用——永不执行。
- 编码：`dsb sy` = `f3bf 8f4f`（4 字节），`wfi` = `bf30`（2 字节）。
- `SCB->SCR` 编成 `[r2,#3344]`=SCS_BASE(0xE000E000)+0xD10；`RCC_CSR` 读编成 `[r3,#2164]`，r3=0x40023000 → 0x40023874（编译器把 base+0x74 合成一个偏移）。
- 字面量池：0x40007000（PWR）、0xE000E000（SCS）、0x40023000（RCC）、0x00F42400（16000000）。

## 九、v2 改写口径

- 叙事主线：睡前一切正常 → 醒来 1ms 变 10.5ms → 三档停什么/留什么 → Stop 的账（SysTick/USART）→ 备份域遗言 → 唤醒源 → 复位原因 → 看门狗/漏电清单 → 一句话记住。
- 生动化比喻（不得替代数字）：Stop = 睡着但记得一切，醒来要重新对表；Standby = 断电重生，只留备份域一张字条；备份域 = 带锁的抽屉，DBP 是钥匙、BRE 是供电、BRR 是"电稳了"的回执。
- 上屏数字必须来自本底稿；电流量级（mA/µA/nA）若出现，注明"数据手册量级，本集不实测"。
- douyin 竖版复用 `hook-01 / mode-words / tree-stop / stop-bill / disasm-standby / wake / iwdg / punch / cta`，逐场重写短旁白。
