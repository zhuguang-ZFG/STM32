# 抖音投稿清单 · 18 条

合集名（16 条共用，抖音里叫"合集"，第一条发布时建）：**通往单片机之路 · 屏上每个数都是本机跑的**

投稿顺序 = `video/series.json` 的 `no`，和 B站 那条序列一致——同一集在两个平台是同一个编号，
评论区对得上，不用维护第二套映射。

每条三步：① 传 `douyin.mp4` → ② 粘下面的**作品描述** → ③ 发完立刻在评论区贴**置顶评论**并长按置顶。

| # | 集 | 时长 | 体积 | 视频 | 封面 |
|---|---|---|---|---|---|
| 1 | C3 c3-volatile | 62.3s | 5.9 MB | `video/out/c3-volatile/douyin.mp4` | `video/out/c3-volatile/douyin-cover.png` |
| 1 | C3 c3b-volatile | 27.9s | 2.5 MB | `video/out/c3b-volatile/douyin.mp4` | `video/out/c3b-volatile/douyin-cover.png` |
| 2 | C4 c4-struct-abi | 68.6s | 6.1 MB | `video/out/c4-struct-abi/douyin.mp4` | `video/out/c4-struct-abi/douyin-cover.png` |
| 3 | C5 c5-func-pointer | 67.9s | 6.2 MB | `video/out/c5-func-pointer/douyin.mp4` | `video/out/c5-func-pointer/douyin-cover.png` |
| 4 | C6 c6-abi-stack | 62.7s | 5.4 MB | `video/out/c6-abi-stack/douyin.mp4` | `video/out/c6-abi-stack/douyin-cover.png` |
| 5 | C7 c7-ub | 62.8s | 5.5 MB | `video/out/c7-ub/douyin.mp4` | `video/out/c7-ub/douyin-cover.png` |
| 6 | F2 f2-context-switch | 61.0s | 6.2 MB | `video/out/f2-context-switch/douyin.mp4` | `video/out/f2-context-switch/douyin-cover.png` |
| 7 | F0 f0-why-rtos | 25.9s | 2.0 MB | `video/out/f0-why-rtos/douyin.mp4` | `video/out/f0-why-rtos/douyin-cover.png` |
| 8 | S16 s16-hardfault | 73.8s | 7.1 MB | `video/out/s16-hardfault/douyin.mp4` | `video/out/s16-hardfault/douyin-cover.png` |
| 9 | S2 s2-rcc | 65.6s | 6.3 MB | `video/out/s2-rcc/douyin.mp4` | `video/out/s2-rcc/douyin-cover.png` |
| 10 | S14 s14-pwr | 56.9s | 5.5 MB | `video/out/s14-pwr/douyin.mp4` | `video/out/s14-pwr/douyin-cover.png` |
| 11 | P4 p4-iram | 69.0s | 6.2 MB | `video/out/p4-iram/douyin.mp4` | `video/out/p4-iram/douyin-cover.png` |
| 12 | S4 s4-nvic | 66.7s | 5.8 MB | `video/out/s4-nvic/douyin.mp4` | `video/out/s4-nvic/douyin-cover.png` |
| 13 | C2 c2-pointer | 70.0s | 5.5 MB | `video/out/c2-pointer/douyin.mp4` | `video/out/c2-pointer/douyin-cover.png` |
| 14 | F3 f3-scheduler | 68.3s | 5.8 MB | `video/out/f3-scheduler/douyin.mp4` | `video/out/f3-scheduler/douyin-cover.png` |
| 15 | S7 s7-usart-baud | 69.7s | 5.5 MB | `video/out/s7-usart-baud/douyin.mp4` | `video/out/s7-usart-baud/douyin-cover.png` |
| 16 | F6 f6-timers | 66.7s | 6.3 MB | `video/out/f6-timers/douyin.mp4` | `video/out/f6-timers/douyin-cover.png` |
| 17 | F5 f5-sem-mutex | 67.0s | 6.2 MB | `video/out/f5-sem-mutex/douyin.mp4` | `video/out/f5-sem-mutex/douyin-cover.png` |

## 逐条文案（可直接粘贴）

### 1. C3 · 你的 volatile 白加了

- 视频：`D:\Users\mcu\video\out\c3-volatile\douyin.mp4`（62.3s / 5.9 MB）
- 封面：`D:\Users\mcu\video\out\c3-volatile\douyin-cover.png`

作品描述：

```text
-O0 灯在闪，-O2 灯灭了
源码一个字没改，编译器也没坏
#C语言 #嵌入式 #GPIO
```

置顶评论：

```text
完整图文在「通往单片机之路」C3《volatile：跟编译器约法三章》。六个变体、两份 -O2 反汇编，一条命令全跑出来，不需要开发板：sh code/c/03-volatile/blink-variants.sh
```

### 1. C3 · 三十七条塌成两条

- 视频：`D:\Users\mcu\video\out\c3b-volatile\douyin.mp4`（27.9s / 2.5 MB）
- 封面：`D:\Users\mcu\video\out\c3b-volatile\douyin-cover.png`

作品描述：

```text
-O2 前后：37 条 → 2 条
删掉的是三个 volatile，不是那行自增
#C语言 #编译优化 #volatile #单片机
```

置顶评论：

```text
完整图文在「通往单片机之路」C3《volatile：跟编译器约法三章》。六个变体、一份 -O2 反汇编，一条命令全跑出来，不需要开发板：sh code/c/03-volatile/blink-variants.sh
```

### 2. C4 · GPIOF->BSRR 凭什么罩住 0x40021418

- 视频：`D:\Users\mcu\video\out\c4-struct-abi\douyin.mp4`（68.6s / 6.1 MB）
- 封面：`D:\Users\mcu\video\out\c4-struct-abi\douyin-cover.png`

作品描述：

```text
结构体那根箭头，凭什么罩住寄存器
偏移不是背的：第七个成员 4×6=0x18
#C语言 #结构体 #寄存器 #STM32
```

置顶评论：

```text
完整图文在「通往单片机之路」C4《结构体与 ABI》。每一个 offsetof 都能自己重跑，条数是数出来的不是抄的，一条命令复现：sh code/c/04-struct-abi/probe.sh
```

### 3. C5 · 中断只负责跳一次：函数指针、状态机、环形缓冲

- 视频：`D:\Users\mcu\video\out\c5-func-pointer\douyin.mp4`（67.9s / 6.2 MB）
- 封面：`D:\Users\mcu\video\out\c5-func-pointer\douyin-cover.png`

作品描述：

```text
中断里只做快递分拣，不下厨房
你写的回调，-O2 之后只剩一条 blx
#C语言 #函数指针 #中断
```

置顶评论：

```text
完整图文在「通往单片机之路」C5《函数指针与状态机》。环形缓冲 A 派 7 格 B 派 8 格那笔账也在里面，560 条断言本机全绿：sh code/c/05-func-pointer/probe.sh
```

### 4. C6 · 一次函数调用的全程直播：参数、回家路、栈帧的生灭

- 视频：`D:\Users\mcu\video\out\c6-abi-stack\douyin.mp4`（62.7s / 5.4 MB）
- 封面：`D:\Users\mcu\video\out\c6-abi-stack\douyin-cover.png`

作品描述：

```text
一次函数调用，机器层只有四件事
宿主开 64 字节栈帧，M4 只花 24
#汇编 #调用约定 #栈帧
```

置顶评论：

```text
完整图文在「通往单片机之路」C6《调用约定与栈帧》。参数进 r0-r3、回家路记在 lr、多余的走栈、结果从 r0 带出去——9 条断言一条命令：sh code/c/06-abi-stack/probe.sh
```

### 5. C7 · 未定义行为：编译器不欠你一个答案

- 视频：`D:\Users\mcu\video\out\c7-ub\douyin.mp4`（62.8s / 5.5 MB）
- 封面：`D:\Users\mcu\video\out\c7-ub\douyin-cover.png`

作品描述：

```text
同一行代码，-O0 给你 2，-O2 给你 0
UB 的题目没有标准答案，这才要避开
#C语言 #未定义行为 #MISRA
```

置顶评论：

```text
完整图文在「通往单片机之路」C7《未定义行为》。三档读数 1/1/0、移位两档变脸、别名违规的报错原文，全部本机实跑：sh code/c/07-ub-misra/probe.sh
```

### 6. F2 · 上下文切换：PendSV 换魂术

- 视频：`D:\Users\mcu\video\out\f2-context-switch\douyin.mp4`（61.0s / 6.2 MB）
- 封面：`D:\Users\mcu\video\out\f2-context-switch\douyin-cover.png`

作品描述：

```text
两个任务同时在跑？每毫秒换一次魂
PendSV 必须最低，它要最后上场
#FreeRTOS #上下文切换 #STM32 #RTOS
```

置顶评论：

```text
完整图文在「通往单片机之路」F2《上下文切换：PendSV 逐指令》。软件帧 9 个字、正文 27 条指令、新任务第一帧 18 个字，三个数一条命令复现：sh code/rtos/01-freertos-lab/probe.sh
```

### 7. F0 · 先失败一次：状态机救不了你的实时性

- 视频：`D:\Users\mcu\video\out\f0-why-rtos\douyin.mp4`（25.9s / 2.0 MB）
- 封面：`D:\Users\mcu\video\out\f0-why-rtos\douyin-cover.png`

作品描述：

```text
串口没收到数据，为什么灯也不闪了？
只有一条执行路线，等就全停
#RTOS #裸机 #FreeRTOS
```

置顶评论：

```text
机制示意，非实拍。完整图文与实跑数据在「通往单片机之路」F0《为什么需要 RTOS：先失败一次》：这段循环六秒只转 55 圈，该翻 12 次的灯只翻了 5 次。不需要开发板，一条命令自己复现：sh code/rtos/00-why-rtos/probe.sh
```

### 8. S16 · HardFault 法医：崩溃现场读三条寄存器就够

- 视频：`D:\Users\mcu\video\out\s16-hardfault\douyin.mp4`（73.8s / 7.1 MB）
- 封面：`D:\Users\mcu\video\out\s16-hardfault\douyin-cover.png`

作品描述：

```text
有些崩溃，光把代码放那儿死不了
未对齐和除零被硬件兜住，开 trap 才报案
#HardFault #STM32 #调试 #嵌入式开发
```

置顶评论：

```text
完整图文在「通往单片机之路」S16《HardFault：崩溃现场的法医技术》。CFSR=0x00008200 只命中两位、BFAR 直接写出现场、EXC_RETURN 第三位决定挖哪个栈。四段一条命令跑完：sh code/stm32/16-debug-hardfault/probe.sh
```

### 9. S2 · 168MHz 是怎么算出来的：先 LATENCY 再切 SYSCLK

- 视频：`D:\Users\mcu\video\out\s2-rcc\douyin.mp4`（65.6s / 6.3 MB）
- 封面：`D:\Users\mcu\video\out\s2-rcc\douyin-cover.png`

作品描述：

```text
程序以为 168MHz，引脚只有 53.76
而算 PLL 那个函数返回值是 0：它认为正常
#STM32 #时钟树 #PLL
```

置顶评论：

```text
完整图文在「通往单片机之路」S2《RCC 时钟树》。五个闸门顺序错了不是跑慢是跑飞；0x07405408 这个字，源码算一遍、-O2 反汇编的字面量池里逐字节挖一遍，当场对上。一条命令：sh code/stm32/01-rcc-clock/probe.sh
```

### 10. S14 · 三种睡眠，三种醒法：Stop 记得，Standby 只留遗言

- 视频：`D:\Users\mcu\video\out\s14-pwr\douyin.mp4`（56.9s / 5.5 MB）
- 封面：`D:\Users\mcu\video\out\s14-pwr\douyin-cover.png`

作品描述：

```text
睡一觉醒来，1ms 量出了 10.5ms
Standby 之后那 18 字节，一句都不会跑
#STM32 #低功耗 #待机
```

置顶评论：

```text
完整图文在「通往单片机之路」S14《低功耗：三种睡眠的唤醒与代价》。三档在 wfi 之后各剩 1 / 6 / 7 条指令，装载值不改 1ms 变 10500µs，唤醒源漏配一格就是睡死。一条命令，不需要开发板：sh code/stm32/14-pwr/probe.sh
```

### 11. P4 · Cache 一关，你的中断服务函数就不存在了：IRAM 纪律

- 视频：`D:\Users\mcu\video\out\p4-iram\douyin.mp4`（69.0s / 6.2 MB）
- 封面：`D:\Users\mcu\video\out\p4-iram\douyin-cover.png`

作品描述：

```text
Cache 一关，你的 ISR 就不存在了
每条指令都在 IRAM，跳过去的地址在 Flash
#ESP32 #Cache #中断
```

置顶评论：

```text
完整图文在「通往单片机之路」P4《中断与双核》。isr_tight 在 0x403766ac、isr_plain 在 0x42008f08、isr_leaky 本体对但 callx8 目标是 42008f1c——断链不写在段名里，只能反汇编查。一条命令：sh code/esp32/09-iram-discipline/probe.sh
```

### 12. S4 · 谁能打断谁：中断这五幕戏，硬件早排好了

- 视频：`D:\Users\mcu\video\out\s4-nvic\douyin.mp4`（66.7s / 5.8 MB）
- 封面：`D:\Users\mcu\video\out\s4-nvic\douyin-cover.png`

作品描述：

```text
写 16，读回来是 0
priority 左移 4 位再截 8 位，16 正好切没
#STM32 #中断优先级 #嵌入式 #单片机
```

置顶评论：

```text
完整图文在「通往单片机之路」S4《NVIC 与 EXTI》。core_cm4.h:1818 那句 (priority << 4) & 0xFF，16→0x00、17→0x10、255→0xF0，一条错误返回都没有；52 条断言一条命令：sh code/stm32/04-nvic-exti/probe.sh
```

### 13. C2 · 指针不是玄学：地址、宽度、纪律

- 视频：`D:\Users\mcu\video\out\c2-pointer\douyin.mp4`（70.0s / 5.5 MB）
- 封面：`D:\Users\mcu\video\out\c2-pointer\douyin-cover.png`

作品描述：

```text
你抄的那行点灯，地址是算出来的
基址加偏移，编译器拆成两段塞进机身
#STM32 #GPIO #C语言 #寄存器
```

置顶评论：

```text
完整图文在「通往单片机之路」C2《指针：点灯公式的全部秘密》。屏上每一条汇编、每一个字节数都是本机实跑反汇编出来的，一条命令复现，不需要开发板：sh code/c/02-pointer/probe.sh
```

### 14. F3 · 调度器：一条 CLZ 选出下一个任务

- 视频：`D:\Users\mcu\video\out\f3-scheduler\douyin.mp4`（68.3s / 5.8 MB）
- 封面：`D:\Users\mcu\video\out\f3-scheduler\douyin-cover.png`

作品描述：

```text
32 个优先级挑最高，源码给两个答案
通用路最坏摸 31 下，位图路永远 1 下
#FreeRTOS #调度器 #位图
```

置顶评论：

```text
完整图文在「通往单片机之路」F3《调度器：位图、tick 与阻塞延时》。位图只有 32 位，把 configMAX_PRIORITIES 掰成 33 会被 #error 当场拦下——本机实测，一条命令：sh code/rtos/03-scheduler/probe.sh
```

### 15. S7 · 115200 你写不出来：波特率是算出来的

- 视频：`D:\Users\mcu\video\out\s7-usart-baud\douyin.mp4`（69.7s / 5.5 MB）
- 封面：`D:\Users\mcu\video\out\s7-usart-baud\douyin-cover.png`

作品描述：

```text
你写的不是 115200，是 139
它跑出来 115107.9，误差 -0.080%
#STM32 #USART #波特率 #串口
```

置顶评论：

```text
完整图文在「通往单片机之路」S7《USART》。一格就是 822.2 波特，想更准硬件没给你这一格；8N1 的总预算 0.5/8.5=5.882% 还要收发对半分。误差表还与 CI 逐行 diff，一条命令：sh code/stm32/03-uart-dma/probe.sh
```

### 16. F6 · 软件定时器的 RAM 账：一个都没建，已经付了 1312 字节

- 视频：`D:\Users\mcu\video\out\f6-timers\douyin.mp4`（66.7s / 6.3 MB）
- 封面：`D:\Users\mcu\video\out\f6-timers\douyin-cover.png`

作品描述：

```text
选型表写：软件定时器 RAM 开销零
一开就付 1312 字节，一个都没建
#FreeRTOS #软件定时器 #RAM
```

置顶评论：

```text
完整图文在「通往单片机之路」F6《任务通知、事件组与软件定时器》。守护任务 1128 + 命令队列 184，另有 60 字节在 .bss 里堆管不到；一个任务的名额够放 11 个定时器。七步一条命令，不需要开发板：sh code/rtos/06-timers/probe.sh
```

### 17. F5 · 信号量和互斥量是两样东西？xSemaphore 一个函数都没有

- 视频：`D:\Users\mcu\video\out\f5-sem-mutex\douyin.mp4`（67.0s / 6.2 MB）
- 封面：`D:\Users\mcu\video\out\f5-sem-mutex\douyin-cover.png`

作品描述：

```text
选型表列三行，其实是一个结构体
xSemaphore 展开后剩 0 个
#FreeRTOS #互斥锁 #优先级反转
```

置顶评论：

```text
完整图文在「通往单片机之路」F5《信号量与互斥量》。五个 xSemaphore* 全是宏、展开后剩 0 个；一把锁 sizeof(Queue_t)=80、载荷 0；互斥量的身份 = queue.c:65 `#define uxQueueType pcHead` 那一格是不是 NULL。八步一条命令，不需要开发板：sh code/rtos/05-sem-mutex/probe.sh
```

## 发布节奏与红线

- 时长全部落在 45–75s：‼️ 越界 c3b-volatile, f0-why-rtos
- 描述里没有任何站外字样，导流只在置顶评论（口径由用户 2026-10-14 定：描述不提，全进置顶评论）。
- 置顶评论要等片子发出去之后、在自己的作品下评论再置顶；发完就置顶，别拖到第二天补。
- 抖音一账号一天连发多条容易进低质池，建议 1 天 1 条、最多 2 条，先发前 3 号看数据再定后面的节奏。

## 已知的一条红线：片子里的导流句没有改（需要你决定）

描述改干净了，但**竖版成片本身**还在说"站内 X 全文免费"。这句既有口播也有画面，
下面的数是从 `episode.json` 的 douyin 可见字段里现扫的，不是估的：

  - 收尾那句明说"站内 X 有全篇/全文免费"的：**14 集、18 个字段**（C4、C5、C6、C7、F2、S16、S2、S14、P4、S4、C2、F3、S7、F6）
  - 说"仓库里跑一遍 / 克隆仓库进那个目录"的：**1 集、1 个字段**（C3）
  - 只是交代出处、不算导流的（如 F6"站内那张选型表原本这么写"）：**3 个字段**（S16、F6）
  - 合计 22 个字段，分布在 15 / 18 集

要么改这些 `cta` 场（旁白 + 屏上 sub/bullets）重渲受影响的那几条竖版，要么先发 3 条看是否被限流再决定。
这一轮没有替你改：改旁白 = 重合成 + 重渲，是要点头的动作。
