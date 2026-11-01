# 12 Flash 与 IAP 升级

> English: [Flash and IAP](en/12-flash-iap.md)

> 内部 Flash 存放并可在线擦写程序，IAP（在应用编程）让设备通过串口/CAN 自我升级固件，无需拆机接下载器。

<p align="center">
  <img src="../assets/animations/flash-iap.svg" width="760" alt="IAP 在线升级：Bootloader + APP 双区跳转">
  <br><sub>▲ 动画：IAP 在线升级 Bootloader + APP 双区跳转（作者自绘矢量动画，非实拍）</sub>
</p>

<!-- video:ch12 -->
<p align="center">
  <video width="640" controls poster="../assets/video/ch12-iap.png">
    <source src="../assets/video/ch12-iap.mp4" type="video/mp4">
  </video>
  <br><sub>▲ 本章讲解视频（2.6 分钟）。<a href="../assets/video/ch12-iap.mp4">MP4</a> · <a href="../assets/video/ch12-iap.srt">字幕</a></sub>
</p>

<details>
<summary>旁白文字稿</summary>

1. 闪存不能当内存随便改一个字节。通常要先擦，再写。擦写之前必须解锁。写到一半掉电，这一页可能是半新半旧，启动时要能认出来。
2. F103 的读保护里，选项字节 0xA5 表示不保护。改成别的值之前，先想清楚你还能不能再读出来。改保护之前，先把现有程序备份下来。
3. 到了 F4，0xCC 这一档是不可逆的读保护。手滑写进去，这颗芯片的调试口就回不来了。实验这种操作，不要放在你唯一的那块板子上。
4. 这一帧是仓库画的升级路径。正在执行的程序不要擦掉自己的脚下。新固件写到另一块区域，校验通过，再跳过去。校验失败就留在旧程序里，设备还活着。
5. 程序如果不是从默认的闪存起始跑，中断向量表的偏移也要改。只改链接脚本、不改向量表偏移，平时能跑，一进中断就飞到旧地址。
6. 跳转之前至少核对长度和校验。有条件再看版本号。没有校验就跳，等于允许任意一包噪声变成你的新程序。失败了要留在还能通信的旧程序里。
7. 擦除不是调用一下就结束。要等忙标志落下，再去读。写保护如果开着，解锁只解了闪存控制器还不够。手册里的顺序不要跳步。
8. 口诀：0xA5 是 F1 的开门钥匙，0xCC 是 F4 的单程票；改保护先备份。擦之前为什么必须解锁？因为锁着的闪存会拒绝你，或者你以为写进去了其实没有。
9. 实验选一页确定不会踩到当前程序的闪存，擦掉、写几个字、再读回来。和程序区叠在一起的实验，做完这章你就没有调试器可以后悔了。
10. 合上书，三问。擦除之前为什么必须解锁？F103 的 0xA5 表示保护还是不保护？F4 写进 0xCC 之后还能不能恢复调试？

</details>
<!-- /video:ch12 -->

## 学习目标

读这一章之前：会用第 01 章的方法烧录程序，会用第 06 章的串口收发字节，知道第 04 章讲的中断是怎么回事；还要认得十六进制、指针和 `volatile`（不熟的话先读第 00 章的「零基础预备」）。

- [ ] 说清 Flash 为什么要先擦后写，擦过的半字为什么读出 `0xFFFF`
- [ ] 用一个式子算出 STM32F103C8T6 任意一页的起始地址，例如第 16 页是 `0x08004000`
- [ ] 按手册顺序走完一次「解锁 → 擦页 → 写半字 → 读回 → 上锁」，说出钥匙写反的后果
- [ ] 画出本书的 IAP 地图（Bootloader 16 KB、参数区 2 KB、APP 46 KB），改好 APP 的链接脚本和 `VTOR`
- [ ] 写出一个不会跳飞的跳转函数：先查栈顶，再关中断、复位外设、停 SysTick、换向量表和 MSP
- [ ] 说出 F1 和 F4 的读保护差在哪，哪一步会整片擦除，哪一步回不了头

## 核心原理

**一句话结论：片内 Flash 是断电不丢的程序存储器，只能整页擦掉、再按 16 位一格写回；IAP（In-Application Programming，在应用中编程）就是让一段常驻的引导程序（Bootloader）用这套擦写流程，把新固件写进另一块区域，校验通过以后再跳过去运行。**

### 先打个比方

把 Flash 想成一本用铅笔写的笔记本，只是橡皮只能整页擦。

- 一页擦干净以后，每一格都是空白。空白在 Flash 里是 1，所以擦过的地方读出来全是 `0xFF`。
- 写字只能把空白涂黑，也就是把 1 改成 0。涂黑的格子不能单独擦回空白；想改一个字，就得把整页擦掉重抄。
- 本子平时锁在抽屉里，要用两把钥匙、按固定的顺序才能打开，写完再锁上。
- IAP 就像本子最前面几页抄着一份「怎么换正文」的说明，也就是 Bootloader。翻开本子先读说明，说明再决定是直接读后面的正文，还是先把正文擦掉、抄进新的。

比方到这里为止。真实的 Flash 一次写 16 位，不是一个字；擦一页要 20–40 ms，这段时间里 CPU 想从 Flash 取指令也得等着；每一页能擦写的次数也有限。具体数字在第 3 节。

### 1. Flash 组织结构：先擦后写，一次 16 位

STM32F103C8T6 的程序放在片内 64 KB 的 Flash（闪存）里，从地址 `0x08000000` 开始。读它和读内存一样，拿指针直接读；写它不行，`*(uint16_t *)addr = x;` 这样直接赋值，数不会写进去。

手册把「写入 Flash」叫做编程（program）。F1 的编程有三条规矩，出自 ST 的 Flash 编程手册 PM0075 Rev 2 第 2.3.3 节和 RM0008 Rev 21 第 3.3.3 节：

- **按页擦除。** 擦除把一整页变成全 1，每个半字都读出 `0xFFFF`。F103C8 属于中容量（medium-density）器件，一页 1 KB，共 64 页。
- **按半字编程。** 半字是 16 位、2 个字节，地址必须是偶数，一个 32 位的数要分两次写。写入的宽度不是半字，FPEC（Flash Program and Erase Controller，Flash 擦写控制器）会返回总线错误。
- **只能写到擦过的地方。** 目标半字不是 `0xFFFF`，硬件会跳过这次编程，并在状态寄存器里置 PGERR（编程错误）标志；唯一的例外是写 `0x0000`。所以在 F1 上，就算只想把几个 1 改成 0，也得先擦整页。

页的起始地址用一个式子就能算：

```text
第 n 页的起始地址 = 0x08000000 + n × 0x400        （0x400 = 1024 字节 = 1 KB）
```

| 页号 | 起始地址 | 怎么算 |
| --- | --- | --- |
| 0 | `0x08000000` | 0 × 0x400 = 0 |
| 16 | `0x08004000` | 16 × 0x400 = 0x4000 |
| 18 | `0x08004800` | 18 × 0x400 = 0x4800 |
| 63 | `0x0800FC00` | 63 × 0x400 = 0xFC00，这是最后一页 |

表里每一行都能用上面的式子算回去。一个地址落在两行之间，就属于上一行开头的那一页，比如 `0x08004321` 在第 16 页里。

### 2. 解锁与编程：擦写一页要走的步骤

**结论：解锁 → 等不忙 → 擦页 → 写半字 → 读回核对 → 上锁。HAL 库把它包成四个函数，寄存器写法放在「代码实现」的最后。**

这几步要用到 Flash 接口的四个寄存器：`FLASH_KEYR`（钥匙寄存器）、`FLASH_CR`（控制寄存器，里面有 LOCK、PER、PG、STRT 几个位）、`FLASH_AR`（地址寄存器）和 `FLASH_SR`（状态寄存器）。状态寄存器里的 BSY 位为 1 表示「正在擦或正在写」，PGERR 和 WRPRTERR（写保护错误）是两个出错标志，EOP 表示一次操作结束。下表的顺序出自 PM0075 Rev 2 第 2.3.2 到 2.3.4 节：

| 步骤 | 寄存器上做什么 | HAL 函数 |
| --- | --- | --- |
| 1 解锁 | 向 `FLASH_KEYR` 先写 `0x45670123`，再写 `0xCDEF89AB`，`FLASH_CR` 的 LOCK 位清零 | `HAL_FLASH_Unlock()` |
| 2 擦一页 | 等 BSY 为 0；置 PER；把页内任意一个地址写进 `FLASH_AR`；置 STRT；再等 BSY 为 0 | `HAL_FLASHEx_Erase()` |
| 3 写半字 | 置 PG；向目标地址写一个 16 位的数；等 BSY 为 0 | `HAL_FLASH_Program(FLASH_TYPEPROGRAM_HALFWORD, …)` |
| 4 核对 | 查 PGERR、WRPRTERR；把刚写的地址读回来比较 | HAL 只查标志，读回要自己写 |
| 5 上锁 | 置 LOCK | `HAL_FLASH_Lock()` |

从上往下照做即可，HAL 那一列是同一步的现成函数。三个细节最容易出事：

- **钥匙写错没有第二次机会。** 顺序反了或写错一个数，FPEC 会返回总线错误，并且把 FPEC 和 `FLASH_CR` 一直锁到下一次复位（PM0075 Rev 2 第 2.3.2 节）。
- **擦写期间 CPU 会被卡住。** BSY 为 1 时，CPU 只要去读 Flash（包括取指令）就会停下来等（PM0075 第 2.3.3 节）。程序和中断函数都放在 Flash 里，所以擦一页的 20–40 ms 里，串口中断也进不来。第 7 节会用到这一点。
- **HSI 要开着。** 擦和写的时候，片内 8 MHz 的 RC 振荡器 HSI 必须处于开启状态（RM0008 Rev 21 第 3.3.3 节）。复位后 HSI 默认是开的，为了省电把它关掉的程序要留意。

用 HAL 写，四行就是一次完整的擦写：

```c
HAL_FLASH_Unlock();                                          /* 解锁 */
HAL_FLASHEx_Erase(&erase, &page_err);                        /* 擦除（F1 按页，F4 按扇区） */
HAL_FLASH_Program(FLASH_TYPEPROGRAM_HALFWORD, addr, data);   /* F1 一次写半字 */
HAL_FLASH_Lock();                                            /* 上锁 */
```

F4 的流程大体相同，只有两处不一样：擦除用 `FLASH_CR` 的 SER 位加 SNB 字段选扇区号；写入宽度由 PSIZE 字段决定，HAL 里对应 `FLASH_TYPEPROGRAM_BYTE`、`FLASH_TYPEPROGRAM_WORD`、`FLASH_TYPEPROGRAM_DOUBLEWORD` 等选项。

### 3. F1 和 F4 的 Flash 差在哪

**结论：F1 按 1 KB 的页擦、只能按半字写；F4 按 16–128 KB 的扇区擦，写多宽要看供电电压。下表左右两列不能混用。**

| 项目 | STM32F103C8T6（F1） | STM32F407VG（F4） |
| --- | --- | --- |
| 擦除单位 | 页，1 KB，共 64 页（中容量）。大容量的 F1 是 2 KB 一页 | 扇区：S0–S3 各 16 KB，S4 为 64 KB，S5–S11 各 128 KB，共 1 MB |
| 一次写多宽 | 只有半字（16 位） | 8、16、32、64 位，由 PSIZE 选 |
| 擦写电压 | 用芯片自己的 VDD，2–3.6 V 都能擦写 | 按 32 位写要 2.7–3.6 V；按 64 位写要在 VPP 脚外加 8–9 V |
| 擦一个单位 | 页擦除 20–40 ms | 按 32 位擦：16 KB 扇区典型 250 ms、最长 500 ms；128 KB 扇区典型 1 s、最长 2 s |
| 写一次 | 半字 40–70 µs，典型 52.5 µs | 典型 16 µs，最长 100 µs |
| 擦写寿命 | 每页最少 1 万次 | 同左 |
| 数据保持 | 擦写 1 千次后，85 °C 下 30 年；擦写 1 万次后，55 °C 下 20 年 | 同左 |

F1 一列出自 RM0008 Rev 21 表 5、PM0075 Rev 2 第 2.3.3 节和 DS5319 Rev 20 表 28、表 29；F4 一列出自 RM0090 Rev 22 表 5、第 3.6.2 节表 13，以及 DS8626 Rev 12 表 40、表 42。读这张表注意两件事。第一，「按字节写」「扇区」「PSIZE」都是 F4 的说法，搬到 F103 上不成立。第二，时间一栏要按最长值留余量；寿命和保持时间是厂家评估出来的数字，DS5319 表 29 的脚注写的是「特性评估，未经量产测试」，不是每颗芯片出厂都测过。

> [!WARNING]
> Flash 只能整页（整扇区）擦。改一个字节，也要先把整页读出来、擦掉、再整页写回。1 万次听起来很多，可一个每秒整页存一次数据的程序，不到 3 个小时就把同一页写满了 1 万次。经常要存的数据，要么攒够了再写，要么轮流写到不同的页上，这叫磨损均衡。

### 4. IAP 原理与内存划分：Bootloader、参数区、APP

**结论：IAP 把 Flash 切成三块。上电先跑最前面的 Bootloader，由它决定是收新固件，还是直接跳到后面的 APP。三块的边界都要落在页边界上。**

本书和 `examples/iap-bootloader` 用的是下面这张地图。它是例程设定，不是手册规定：

| 区域 | 起始地址 | 大小 | 页号 | 放什么 |
| --- | --- | --- | --- | --- |
| Bootloader | `0x0800 0000` | 16 KB | 0–15 | 引导、串口升级、跳转 |
| 参数区 | `0x0800 4000` | 2 KB | 16–17 | 「APP 有效」标志、长度、校验和 |
| APP | `0x0800 4800` | 46 KB（`0xB800`） | 18–63 | 用户程序，链接脚本的起点改成 `0x08004800` |

三块加起来正好 64 KB。按行读：起始地址加上大小，就是下一行的起始地址。边界必须对齐到页，因为擦除以页为单位；参数区要是和 Bootloader 挤在同一页里，擦参数时就把 Bootloader 的代码一起擦掉了。给 Bootloader 留 16 KB 也是例程设定，你的 Bootloader 更大或更小，整张地图跟着挪，只要边界还在页上。

F4 也要按扇区划分。按 RM0090 Rev 22 表 5，1 MB 的 STM32F407VG 可以这样分：

| 区域 | 起始地址 | 大小 | 扇区 |
| --- | --- | --- | --- |
| Bootloader | `0x0800 0000` | 32 KB | S0–S1 |
| 参数区 | `0x0800 8000` | 16 KB | S2，独占一个扇区 |
| 备用 | `0x0800 C000` | 16 KB | S3，可以放第二份参数 |
| APP | `0x0801 0000` | 960 KB | S4–S11 |

在 F4 上，2 KB 的参数也得独占一个 16 KB 的扇区，否则擦参数会把同一扇区里的 Bootloader 一起擦掉。参数区放在 16 KB 的 S2，而不放在 64 KB 的 S4，还因为小扇区擦得快：按 32 位擦，16 KB 扇区最长 500 ms，64 KB 扇区最长 1.1 s（DS8626 Rev 12 表 40）。

芯片里其实还有一个 ST 出厂固化的 Bootloader，放在系统存储器里：BOOT0 接高电平、BOOT1 接低电平再复位，就能经 USART1（PA9/PA10）下载程序（AN2606 Rev 70 第 21 章）。IAP 和它的区别是：不用动 BOOT0 跳线，协议和校验由你自己定，还可以走 CAN、USB 等任何接口。

### 5. 跳转到 APP：两个字和一个寄存器

**结论：APP 区开头是它自己的向量表，第 0 个字是栈顶地址，第 1 个字是复位入口。跳转就是读出这两个字，把 CPU 收拾干净，告诉它新的向量表在哪，再从复位入口开始执行。**

先解释三个名词：

- **向量表**：程序开头的一张地址表。第 0 项是主栈指针 MSP 的初值，第 1 项是复位后要执行的 `Reset_Handler` 的地址，后面每一项是一个中断函数的地址（PM0056 Rev 7 第 2.3.4 节）。
- **MSP**（Main Stack Pointer，主栈指针）：CPU 存放局部变量和返回地址的栈从哪里开始。F103C8 的 SRAM 是 20 KB（DS5319 Rev 20 表 2），从 `0x20000000` 到 `0x20005000` 之前。栈从高地址往低地址长，所以 MSP 初值通常正好是 `0x20005000`；合法的初值大于 `0x20000000`，不超过 `0x20005000`。
- **VTOR**（Vector Table Offset Register，向量表偏移寄存器）：告诉 CPU 向量表在哪。它复位后是 0；从 Flash 启动时地址 0 映射到 `0x08000000`，所以默认用的是 Bootloader 的向量表。

跳转按下面的顺序做，每一步都有原因：

1. **先查 APP 在不在。** 读第 0 个字，看它是否落在 `0x20000000`–`0x20005000` 之间。APP 区是空的，读出来是 `0xFFFFFFFF`，这时不能跳。
2. **关中断，复位时钟和外设。** 先 `__disable_irq()`，再调 `HAL_RCC_DeInit()` 和 `HAL_DeInit()`，把 Bootloader 用过的东西恢复成复位状态。
3. **停 SysTick，清掉它的挂起位。** 这一步必须放在第 2 步之后：HAL 的 `HAL_RCC_DeInit()` 最后会调用 `HAL_InitTick()`，把 SysTick 和它的中断重新打开（见 STM32CubeF1 的 `stm32f1xx_hal_rcc.c`）。
4. **关掉并清掉所有外设中断。** 写 NVIC 的 ICER 和 ICPR 寄存器，免得 APP 还没初始化，Bootloader 留下的串口中断就先进来。
5. **把 APP 的起点写进 `SCB->VTOR`。** VTOR 的低 9 位必须是 0，也就是起点要按 `0x200` 对齐（PM0056 Rev 7 第 4.4.4 节）。`0x4800 ÷ 0x200 = 36`，能整除。
6. **装入 MSP，开中断，跳到复位入口。**

APP 那边要改两处，缺一处都会出问题：

- **链接脚本**：Flash 的起点改成 `0x08004800`，长度改成 46 KB（`0xB800`）。不改，APP 里所有函数的地址都按 `0x08000000` 算，跳过去就是乱跑。
- **向量表**：在 APP 的 `main()` 第一行写 `SCB->VTOR = 0x08004800UL;`。这样不论 APP 是从 Bootloader 跳来的，还是被调试器直接从 APP 起点启动的，向量表都是对的。

### 6. 选项字节：读保护、写保护和硬件看门狗

**结论：选项字节（option bytes）是 Flash 里单独的一小块，F103 的在 `0x1FFF F800`（RM0008 Rev 21 表 5）。它管读保护、写保护和几项上电配置，改它要开另一把锁（`FLASH_OPTKEYR`，钥匙值和 `FLASH_KEYR` 相同）。改之前先把程序备份出来。**

| 项目 | F103（PM0075 Rev 2） | F407（RM0090 Rev 22 第 3.7 节） |
| --- | --- | --- |
| RDP 读保护字节 | `0xA5` 不保护；其他任何值都是读保护，包括擦掉以后的 `0xFF`；只有这一级 | `0xAA` 是 Level 0，不保护；`0xCC` 是 Level 2；其他值是 Level 1 |
| 打开读保护时 | 程序不擦；调试器读不到 Flash；第 0–3 页自动写保护；系统复位后生效，连着调试器时要上电复位 | 提高保护等级时不擦 |
| 解除读保护时 | 写回 `0xA5` 会先整片擦除主 Flash，上电复位后生效 | Level 1 改回 Level 0 会整片擦除；Level 2 是永久的，调试口关闭，不能再降级 |
| USER 字节 | `WDG_SW` 为 0 是硬件看门狗，上电就开、软件停不掉；另有 `nRST_STOP`、`nRST_STDBY` | 同样有这三位 |
| WRP 写保护 | 中容量每 1 位管 4 页，位为 0 表示保护 | 每 1 位管一个扇区 |

一行一行横着读：同一个功能，两个系列的取值和后果都不一样。F103 的无保护值只有 `0xA5` 一个，F4 的 `0xAA`、`0xCC` 在 STM32F103C8T6 上没有意义。最危险的是两件事：F103 写回 `0xA5` 会丢掉整片程序；F4 写进 `0xCC` 就再也连不上调试器。

只读当前配置是安全的，也不需要解锁：

```c
FLASH_OBProgramInitTypeDef ob = {0};
HAL_FLASHEx_OBGetConfig(&ob);   /* 只读 */
/* ob.RDPLevel == OB_RDP_LEVEL_0 表示没有读保护（0xA5）；
   ob.WRPPage 是 FLASH_WRPR 的原值，某一位为 0 表示对应的 4 页被写保护 */
```

写 RDP 的代码这里不贴：复制进实验工程，很容易把唯一的一块板子锁住。

口诀：**0xA5 是 F1 的开门钥匙，0xCC 是 F4 的单程票；改保护先备份。**

### 7. 升级协议：为什么要逐块应答

**结论：串口只能暂存 1 个字节，而擦一页要 20–40 ms、写一个半字要 40–70 µs，这期间程序腾不出手去读串口。所以升级协议必须做到「设备说好了，上位机再发下一块」。**

按 115200 波特、8 个数据位、1 个停止位算，一个字节在线上占 10 位：

| 事件 | 时间 | 依据 |
| --- | --- | --- |
| 收一个字节 | 10 ÷ 115200 ≈ 86.8 µs | 第 06 章 |
| 擦 46 页（整个 APP 区） | 46 × (20–40 ms) = 0.92–1.84 s | DS5319 Rev 20 表 28 |
| 写 512 字节 = 256 个半字 | 256 × (40–70 µs) ≈ 10.2–17.9 ms | DS5319 Rev 20 表 28 |
| 写 512 字节期间线上到来的字节 | 10.2 ms ÷ 86.8 µs ≈ 118 个，到 17.9 ms ÷ 86.8 µs ≈ 206 个 | 上两行相除 |

看最后一行：上位机要是不停地发，写一块的工夫就有一两百个字节进来。USART 的接收数据寄存器只有一个，上一个字节还没被读走，下一个又收完了，硬件就置 ORE（Overrun Error，溢出错误），新来的字节丢掉（RM0008 Rev 21 第 27.6.1 节）。

本章的协议在 `examples/iap-bootloader` 的帧格式上加了应答。ACK（acknowledge，应答）是一个字节 `0x06`，NAK 是 `0x15`；「小端」指 4 个字节里低字节在前：

```text
上位机                                    Bootloader
'U' 'U' 'U' …（每 50 ms 一个）   ──▶  上电 500 ms 内收到 'U'
                                ◀──  0x06（ACK）
0x5A + 长度（4 字节，小端）      ──▶  擦参数页、擦 APP 区（最长约 1.88 s）
                                ◀──  0x06
第 1 块（512 字节）              ──▶  写 256 个半字，逐个读回核对
                                ◀──  0x06
…… 最后一块（可以不满 512 字节）……
累加和（4 字节，小端）           ──▶  按 Flash 里的内容重算一遍，比较
                                ◀──  0x06：写上「APP 有效」标志 / 0x15：失败
```

「APP 有效」标志是参数区的第一个半字，例程设定为 `0x5AA5`。升级一开始最先擦掉它，校验通过以后最后才写上。升级中途掉电，标志还是 `0xFFFF`，Bootloader 下次上电不会跳进半截 APP，而是留下来等下一次升级。

还要说清楚一点：这种单区方案里，旧 APP 在擦除那一刻就没了。升级失败后设备还活着，是因为 Bootloader 还在、还能再收一次，不是因为旧程序还在。想要「失败就回到旧版本」，得用实验三的 A/B 双区。

成熟的做法是 YMODEM 协议：每包 128 或 1024 字节，带 CRC16 校验和逐包应答，SecureCRT、Tera Term 这类终端软件就能发送。本章的帧格式更简单，配一个 20 来行的 Python 脚本，放在「代码实现」里。

## 硬件与接线

| 开发板 | 外设 | 引脚 | 备注 |
| --- | --- | --- | --- |
| BluePill（STM32F103C8T6） | USART1 | PA9 = TX（第 30 脚），PA10 = RX（第 31 脚） | 接 USB-TTL 模块收升级包，115200-8-N-1（例程设定） |
| BluePill | SWD | PA13 = SWDIO，PA14 = SWCLK | 用 ST-Link 烧 Bootloader、读 Flash 内容 |
| BluePill | 板载 LED | PC13 | 低电平亮，实验二的 APP 用它闪烁，表示自己在跑 |
| USB-TTL 模块 | 串口 | TXD、RXD、GND | 选 3.3 V 电平的模块 |

```text
电脑 ── USB ── USB-TTL 模块                    BluePill（STM32F103C8T6）
                  TXD ────────────────────▶ PA10  USART1_RX（第 31 脚）
                  RXD ◀──────────────────── PA9   USART1_TX（第 30 脚）
                  GND ───────────────────── GND
电脑 ── USB ── ST-Link
                  SWDIO ─────────────────── PA13
                  SWCLK ─────────────────── PA14
                  GND ───────────────────── GND
```

接线注意两件事：串口要交叉接，模块的 TXD 接 PA10、RXD 接 PA9；模块和板子一定要共地，否则收到的全是乱码。IAP 本身不需要别的硬件。

## 代码实现

下面三段放进同一个 `main.c`，就是一个能编译的最小 Bootloader：① 宏定义和 Flash 擦写，② 按第 7 节的协议收固件，③ 跳到 APP，再加 `main()`。CubeMX 里只配时钟（HSE，72 MHz，见第 02 章）和 SWD，不要勾 USART1，串口由下面的 `uart1_init()` 自己配；用这三段替换 CubeMX 生成的 `main()`，保留它生成的 `SystemClock_Config()`。和 [`examples/iap-bootloader/`](../examples/iap-bootloader/) 相比，地图和帧头一样，这一版多了逐块应答、「APP 有效」标志和跳转前的 SysTick 处理。

**① 宏定义和 Flash 擦写**

```c
/* main.c —— 最小串口 Bootloader（STM32F103C8T6，HAL） */
#include "stm32f1xx_hal.h"

#define FLASH_PAGE   1024U          /* F103C8 中容量 1KB/页 */
#define PARAM_ADDR   0x08004000UL   /* 参数区第一页（例程设定） */
#define APP_ADDR     0x08004800UL   /* APP 起点（例程设定） */
#define APP_MAX      0xB800UL       /* APP 区 46 KB */
#define APP_VALID    0x5AA5U        /* 「APP 有效」标志（例程设定） */
#define SRAM_START   0x20000000UL
#define SRAM_END     0x20005000UL   /* 20 KB SRAM 到这里为止 */
#define FRAME_HEAD   0x5AU
#define ACK          0x06U
#define NAK          0x15U
#define CHUNK        512U           /* 每块字节数，必须是偶数 */
#define WAIT_U_MS    500U

typedef void (*pFunction)(void);

UART_HandleTypeDef huart1;
void SystemClock_Config(void);      /* CubeMX 生成，72 MHz */

static uint16_t rx_buf[CHUNK / 2];  /* 按半字声明，保证 2 字节对齐 */

/* 擦除覆盖 [addr, addr+len) 的页 */
int Flash_EraseRange(uint32_t addr, uint32_t len)
{
    FLASH_EraseInitTypeDef er = {0};
    uint32_t page_err = 0;

    HAL_FLASH_Unlock();
    er.TypeErase   = FLASH_TYPEERASE_PAGES;
    er.PageAddress = addr;
    er.NbPages     = (len + FLASH_PAGE - 1) / FLASH_PAGE;
    if (HAL_FLASHEx_Erase(&er, &page_err) != HAL_OK) {
        HAL_FLASH_Lock();
        return -1;
    }
    HAL_FLASH_Lock();
    return 0;
}

/* 按半字写入缓冲区，每写一个就读回核对 */
int Flash_WriteBuf(uint32_t addr, const uint16_t *data, uint32_t halfwords)
{
    HAL_FLASH_Unlock();
    for (uint32_t i = 0; i < halfwords; i++) {
        uint32_t a = addr + i * 2;
        if (HAL_FLASH_Program(FLASH_TYPEPROGRAM_HALFWORD, a, data[i]) != HAL_OK ||
            *(volatile uint16_t *)a != data[i]) {
            HAL_FLASH_Lock();
            return -1;
        }
    }
    HAL_FLASH_Lock();
    return 0;
}
```

**② 收固件**

```c
static void send_byte(uint8_t b)
{
    HAL_UART_Transmit(&huart1, &b, 1, 100);
}

static uint32_t le32(const uint8_t *p)            /* 4 个字节按小端拼成 32 位 */
{
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) |
           ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

/* 上电后等 WAIT_U_MS，收到 'U' 就回 ACK 并返回 1 */
static int Boot_WaitForU(void)
{
    uint8_t ch;
    uint32_t t0 = HAL_GetTick();

    while (HAL_GetTick() - t0 < WAIT_U_MS) {
        if (HAL_UART_Receive(&huart1, &ch, 1, 10) == HAL_OK && ch == 'U') {
            send_byte(ACK);
            return 1;
        }
    }
    return 0;
}

/* 收一帧：0x5A | 长度 | 数据（每块等一次 ACK）| 累加和。成功返回 0 */
static int Boot_Receive(void)
{
    uint8_t  ch = 0, len_le[4], sum_le[4];
    uint8_t *bytes = (uint8_t *)rx_buf;
    uint32_t len, done = 0, sum = 0, t0 = HAL_GetTick();
    uint16_t flag = APP_VALID;

    while (ch != FRAME_HEAD) {                          /* 跳过多发的 'U'，等帧头 */
        if (HAL_GetTick() - t0 > 5000U) return -1;
        if (HAL_UART_Receive(&huart1, &ch, 1, 10) != HAL_OK) ch = 0;
    }
    if (HAL_UART_Receive(&huart1, len_le, 4, 100) != HAL_OK) return -1;
    len = le32(len_le);
    if (len == 0U || len > APP_MAX) return -1;

    if (Flash_EraseRange(PARAM_ADDR, FLASH_PAGE) != 0) return -1;   /* 先作废标志 */
    if (Flash_EraseRange(APP_ADDR, len) != 0) return -1;
    send_byte(ACK);                                     /* 擦完了，请发第一块 */

    while (done < len) {
        uint32_t n = (len - done > CHUNK) ? CHUNK : (len - done);
        if (HAL_UART_Receive(&huart1, bytes, (uint16_t)n, 2000) != HAL_OK) return -1;
        if (n & 1U) bytes[n] = 0xFF;                    /* 奇数长度：补一个 0xFF */
        if (Flash_WriteBuf(APP_ADDR + done, rx_buf, (n + 1U) / 2U) != 0) return -1;
        done += n;
        send_byte(ACK);                                 /* 这一块写好了，请发下一块 */
    }

    if (HAL_UART_Receive(&huart1, sum_le, 4, 1000) != HAL_OK) return -1;
    for (uint32_t i = 0; i < len; i++) {
        sum += *(volatile uint8_t *)(APP_ADDR + i);     /* 按 Flash 里的内容算 */
    }
    if (sum != le32(sum_le)) return -1;
    return Flash_WriteBuf(PARAM_ADDR, &flag, 1);        /* 最后才写「APP 有效」 */
}
```

**③ 跳转和 main()**

```c
static void JumpToApp(uint32_t app_addr)
{
    static pFunction s_entry;                           /* 放静态区，换了 MSP 也读得到 */
    uint32_t sp = *(volatile uint32_t *)app_addr;       /* 第 0 字：栈顶 */

    if (sp <= SRAM_START || sp > SRAM_END) return;      /* 空 Flash 读出 0xFFFFFFFF */
    s_entry = (pFunction)(*(volatile uint32_t *)(app_addr + 4U));   /* 第 1 字：复位入口 */

    __disable_irq();
    HAL_RCC_DeInit();                                   /* 时钟回到 HSI，会重新打开 SysTick */
    HAL_DeInit();                                       /* 复位所有外设 */
    SysTick->CTRL = 0;                                  /* 所以 SysTick 在这之后再停 */
    SysTick->LOAD = 0;
    SysTick->VAL  = 0;
    SCB->ICSR = SCB_ICSR_PENDSTCLR_Msk;                 /* 清掉已经挂起的 SysTick */
    for (uint32_t i = 0; i < 8U; i++) {                 /* 关掉、清掉所有外设中断 */
        NVIC->ICER[i] = 0xFFFFFFFFUL;
        NVIC->ICPR[i] = 0xFFFFFFFFUL;
    }
    SCB->VTOR = app_addr;                               /* 以后的中断查 APP 的向量表 */
    __DSB();
    __ISB();
    __set_MSP(sp);
    __enable_irq();
    s_entry();
}

static void uart1_init(void)
{
    GPIO_InitTypeDef io = {0};

    __HAL_RCC_GPIOA_CLK_ENABLE();
    __HAL_RCC_USART1_CLK_ENABLE();
    io.Pin   = GPIO_PIN_9;                              /* PA9 = USART1_TX */
    io.Mode  = GPIO_MODE_AF_PP;
    io.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &io);
    io.Pin  = GPIO_PIN_10;                              /* PA10 = USART1_RX */
    io.Mode = GPIO_MODE_INPUT;
    io.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &io);

    huart1.Instance          = USART1;
    huart1.Init.BaudRate     = 115200;
    huart1.Init.WordLength   = UART_WORDLENGTH_8B;
    huart1.Init.StopBits     = UART_STOPBITS_1;
    huart1.Init.Parity       = UART_PARITY_NONE;
    huart1.Init.Mode         = UART_MODE_TX_RX;
    huart1.Init.HwFlowCtl    = UART_HWCONTROL_NONE;
    huart1.Init.OverSampling = UART_OVERSAMPLING_16;
    HAL_UART_Init(&huart1);
}

int main(void)
{
    HAL_Init();
    SystemClock_Config();
    uart1_init();

    for (;;) {
        if (Boot_WaitForU()) {
            send_byte(Boot_Receive() == 0 ? ACK : NAK);
        }
        if (*(volatile uint16_t *)PARAM_ADDR == APP_VALID) {
            JumpToApp(APP_ADDR);                        /* 跳成功就不会回来 */
        }
        /* 没有有效的 APP：回到循环开头，继续等 'U' */
    }
}
```

逐段看：

- `FLASH_PAGE` 是 1024：F103C8 是中容量，1 KB 一页。`NbPages` 向上取整，所以只写 100 字节也会擦掉整整一页。
- `HAL_FLASHEx_Erase()` 里面就是第 2 节表格的第 2 步。`PageAddress` 填页内任何地址都行，PM0075 只要求「页内的一个地址」。
- `Flash_WriteBuf()` 每写一个半字就读回比较。`HAL_FLASH_Program()` 只查 PGERR、WRPRTERR 这些错误标志，不读回；读回核对是手册流程的最后一步。
- 参数页最先擦，APP 区随后擦，「APP 有效」最后写。任何一步掉电，标志都还是 `0xFFFF`，`main()` 不会跳进半截 APP。握手阶段（擦除之前）就失败的话，标志没动，`main()` 照旧跳回原来的 APP。
- 每块写完才回 ACK，上位机收到才发下一块。擦写的时候线上没有字节，第 7 节说的溢出就不会发生。
- 校验和按 Flash 里读出来的内容算，不按缓冲区算，写坏的半字也能查出来。累加和只防传输出错，防不了有人故意改固件；正式产品用 CRC32 再加签名校验。
- `JumpToApp()` 先查第 0 个字是否落在 SRAM 里，挡住「APP 区是空的」这种情况：空 Flash 读出 `0xFFFFFFFF`。
- SysTick 放在 `HAL_RCC_DeInit()` 之后停，并清掉 PENDST 挂起位。`examples/iap-bootloader` 是先停 SysTick、后调 `HAL_RCC_DeInit()`，SysTick 又被打开了；例程跳转前还开了中断，于是 APP 的启动代码还没跑完，SysTick 中断就进来了。只用 HAL 的 APP 多半没事，用 RTOS 的 APP 可能因此出错。
- `__DSB(); __ISB();` 保证 VTOR 真正写进去以后，后面的指令才执行。
- `s_entry` 用 `static`：`__set_MSP()` 换了栈，编译器要是按 SP 去找局部变量，就会读到 APP 的栈上去。
- 跳之前 `__enable_irq()`：CubeMX 生成的 APP 不会再去开总中断，PRIMASK 留着 1，APP 里的 `HAL_Delay()` 会一直等下去。
- 用 ST-Link 直接把 APP 烧到 `0x08004800`，参数区没有标志，这个 Bootloader 不会跳过去。实验二要走一次串口升级。

上位机脚本。它用 pyserial 库按第 7 节的帧格式发送，每一块都等 ACK：

```python
# send_fw.py —— 按本章的帧格式把 app.bin 发给 Bootloader
# 用法：python send_fw.py COM5 app.bin        需要先 pip install pyserial
import struct
import sys
import time

import serial

ACK = b"\x06"
port, path = sys.argv[1], sys.argv[2]
data = open(path, "rb").read()
link = serial.Serial(port, 115200, timeout=0.05)

print("请按一下板子上的复位键")
while link.read(1) != ACK:          # 每 50 ms 发一个 'U'，直到 Bootloader 应答
    link.write(b"U")
time.sleep(0.05)
link.reset_input_buffer()

link.timeout = 3                    # 擦 47 页最长约 1.88 s
link.write(b"\x5a" + struct.pack("<I", len(data)))
if link.read(1) != ACK:
    sys.exit("擦除没有应答：bin 超过 0xB800 字节，或者没有进入升级")
for i in range(0, len(data), 512):
    link.write(data[i:i + 512])
    if link.read(1) != ACK:
        sys.exit(f"第 {i // 512} 块没有应答")
link.write(struct.pack("<I", sum(data) & 0xFFFFFFFF))
print("成功" if link.read(1) == ACK else "校验失败，Bootloader 会继续等下一次升级")
```

APP 工程要改两处。GCC 工程改链接脚本（如 `STM32F103C8Tx_FLASH.ld`）的 FLASH 一行；Keil 在 Options for Target → Target 里把 IROM1 设成起点 `0x08004800`、大小 `0xB800`：

```text
MEMORY
{
  RAM   (xrw) : ORIGIN = 0x20000000, LENGTH = 20K
  FLASH (rx)  : ORIGIN = 0x08004800, LENGTH = 46K
}
```

实验二用的 APP，只闪 PC13：

```c
/* app/main.c —— 实验二的 APP：PC13 以 1 Hz 闪烁 */
#include "stm32f1xx_hal.h"

void SystemClock_Config(void);          /* CubeMX 生成 */

int main(void)
{
    GPIO_InitTypeDef io = {0};

    SCB->VTOR = 0x08004800UL;           /* 和 Bootloader 的 APP_ADDR 一致 */
    HAL_Init();
    SystemClock_Config();

    __HAL_RCC_GPIOC_CLK_ENABLE();
    io.Pin   = GPIO_PIN_13;
    io.Mode  = GPIO_MODE_OUTPUT_PP;
    io.Speed = GPIO_SPEED_FREQ_LOW;
    HAL_GPIO_Init(GPIOC, &io);

    for (;;) {
        HAL_GPIO_TogglePin(GPIOC, GPIO_PIN_13);
        HAL_Delay(500);                 /* 靠 SysTick 中断计时 */
    }
}
```

`HAL_Delay()` 靠 SysTick 中断计数。VTOR 没改对，SysTick 中断进的是 Bootloader 的处理函数，APP 自己的计数不涨，程序通常就停在这一行，灯不闪。

同样的擦页和写半字，用寄存器写是下面这样，每一行对应第 2 节表格里的一步：

```c
/* 寄存器写法：擦一页，再写一个半字（PM0075 Rev 2 第 2.3.2–2.3.4 节） */
#include "stm32f1xx_hal.h"

#define FPEC_KEY1  0x45670123UL
#define FPEC_KEY2  0xCDEF89ABUL

static void flash_wait(void)
{
    while (FLASH->SR & FLASH_SR_BSY) { }            /* 等忙标志落下 */
}

int Flash_PageWrite16_Reg(uint32_t addr, uint16_t value)
{
    int ret = 0;

    if (FLASH->CR & FLASH_CR_LOCK) {                /* 解锁：先 KEY1，再 KEY2 */
        FLASH->KEYR = FPEC_KEY1;
        FLASH->KEYR = FPEC_KEY2;
    }
    flash_wait();
    FLASH->SR = FLASH_SR_EOP | FLASH_SR_PGERR | FLASH_SR_WRPRTERR;   /* 写 1 清除旧标志 */

    FLASH->CR |= FLASH_CR_PER;                      /* 擦页 */
    FLASH->AR  = addr;                              /* 页内任何地址都可以 */
    FLASH->CR |= FLASH_CR_STRT;
    flash_wait();
    FLASH->CR &= ~FLASH_CR_PER;

    FLASH->CR |= FLASH_CR_PG;                       /* 写半字 */
    *(volatile uint16_t *)addr = value;             /* addr 必须是偶数 */
    flash_wait();
    FLASH->CR &= ~FLASH_CR_PG;

    if ((FLASH->SR & (FLASH_SR_PGERR | FLASH_SR_WRPRTERR)) != 0U ||
        *(volatile uint16_t *)addr != value) {
        ret = -1;
    }
    FLASH->CR |= FLASH_CR_LOCK;                     /* 上锁 */
    return ret;
}
```

## 动手实验

1. **实验一：在参数页存一个数，断电后读回来。** 在一个单独的测试程序里，擦第 16 页（`0x08004000`），写入 32 位的 `0x12345678`，分两次半字：先在 `0x08004000` 写 `0x5678`，再在 `0x08004002` 写 `0x1234`。断电再上电，读回来从串口打印。
   - 预期现象：每次上电都打印 `0x12345678`；只擦不写，打印 `0xFFFFFFFF`。
   - 怎么确认：用 STM32CubeProgrammer 经 SWD 连上，读 `0x08004000` 起的 8 个字节，应是 `78 56 34 12 FF FF FF FF`（低字节在前）。
   - 没成功先查：测试程序是否小于 16 KB（看编译输出的 text 加 data），否则第 16 页压在自己的代码上；钥匙顺序对不对，写反了要复位才能再试；是不是没擦就写。
2. **实验二：最小 IAP，用串口换一次 APP。** 用 ST-Link 烧入「代码实现」里的 Bootloader；APP 工程按上面改好链接脚本和 VTOR，编译后用 `arm-none-eabi-objcopy -O binary app.elf app.bin` 生成 bin 文件；运行 `python send_fw.py COM5 app.bin`，再按一下复位键。
   - 预期现象：脚本打印「成功」，PC13 的灯以 1 Hz 闪烁；之后每次复位，灯要等大约 0.5 s 才开始闪，那是 Bootloader 在等 'U'。
   - 怎么确认：用 CubeProgrammer 读 `0x08004000`，前两个字节是 `A5 5A`；读 `0x08004800` 的头 8 个字节，第 0 个字落在 `0x20000000`–`0x20005000` 之间，第 1 个字是奇数。向量的最低位必须是 1，表示 Thumb 代码（PM0056 Rev 7 第 2.3.4 节）。
   - 没成功先查：脚本一直停在「请按复位键」，多半是 TX、RX 接反或没共地；「擦除没有应答」，看 bin 是否超过 46 KB；灯不闪或常亮，看 APP 的链接脚本起点和 VTOR 是否都改成了 `0x08004800`。
3. **实验三（进阶）：A/B 双区，升级失败也能回到旧版本。** 把 APP 区对半分：A 区从 `0x08004800` 起 23 KB，B 区从 `0x0800A400` 起 23 KB。APP 始终在 A 区运行；新固件先收进 B 区，校验通过后在参数区记下「B 有效、长度、校验和」，复位后由 Bootloader 把 B 拷到 A，拷完、核对过 A 再清掉这条记录。
   - 预期现象：传到一半拔掉 USB-TTL，板子复位后照样运行旧版本；拷贝途中断电，下次上电从头再拷一遍。
   - 怎么确认：让 APP 用不同的闪烁节奏代表版本（例如 v1 闪 1 Hz，v2 闪 2 Hz），对比中断升级前后的节奏。
   - 没成功先查：APP 不能超过 23 KB（`0x5C00` 字节）；拷贝前要先擦 A 区；参数区的记录要等 A 区核对通过才能清。

## 自测

1. STM32F103C8T6 的第 40 页从哪个地址开始？地址 `0x08009F00` 落在第几页？
2. 某个半字已经写成 `0x1234`，现在想改成 `0x1230`。只是把两个 1 变成 0，能不能不擦页、直接再写一次？
3. 一个 46 KB 的 APP，用本章的协议从 115200 波特的串口传进来，最快和最慢大约各要多久？（不算 USB 转串口的往返延迟）
4. 为什么在 F103C8 上，只要 APP 从页边界开始，`VTOR` 的对齐要求就自动满足？
5. F103 的 RDP 从 `0xA5` 改成 `0x00` 以后，Flash 里的程序还在吗？想解除保护会发生什么？

参考答案：

1. `0x08000000 + 40 × 0x400 = 0x08000000 + 0xA000 = 0x0800A000`。`0x9F00 ÷ 0x400 = 39.75`，取整数部分，落在第 39 页。
2. 不能。PM0075 规定目标半字不是 `0xFFFF` 时，这次编程会被跳过并置 PGERR，只有写 `0x0000` 例外。要先把整页读出来、擦掉，再整页写回。
3. 传输：46 × 1024 = 47104 字节，× 10 位 ÷ 115200 ≈ 4.09 s。擦除：46 × (20–40 ms) = 0.92–1.84 s。编程：23552 个半字 × (40–70 µs) ≈ 0.94–1.65 s。三段不重叠，相加：最快约 4.09 + 0.92 + 0.94 ≈ 5.95 s，最慢约 4.09 + 1.84 + 1.65 ≈ 7.58 s。
4. VTOR 要求起点按 `0x200` 对齐，即低 9 位为 0。页的大小是 `0x400`，是 `0x200` 的 2 倍，所以任何页边界都是 `0x200` 的整数倍。
5. 程序还在，从 Flash 启动照常运行；但调试器读不到 Flash，第 0–3 页自动写保护。要解除，把 RDP 写回 `0xA5`，硬件会先整片擦除主 Flash，上电复位后保护才解除（PM0075 Rev 2 第 2.4.1 节）。

## 原理与适用范围

> [!NOTE]
> 从这一节到「常见坑与出处」是深入部分，把前面的结论落到具体订货号、手册章节和能复算的数字上。第一次读可以先跳过，做完动手实验再回来对照。

**订货号与页。** 这一章的页、半字和跳转只钉在订货号 STM32F103C8T6 上。它是中容量，闪存 64 KB，从 `0x08000000` 到 `0x08010000` 之前，1 KB 一页，共 64 页，页号 0 到 63，第 63 页从 `0x0800FC00` 起。[RM0008 Rev 21 第 3.3.3 节表 5](#source-rm0008-flash) 的同一张表里，第 127 页从 `0x0801FC00` 起，那是 128 KB 料的末页，越出 C8 的 64 KB；[DS5319](#source-ds5319-swd) 写明 STM32F103x8 的闪存是 64 KB。大容量的 2 KB/页在这颗料上作废。

**半字与擦除态。** 编程地址按 2 字节对齐，一次写 16 位，擦掉以后读回 `0xFFFF`。已经写成 0 的位，不擦整页变不回 1。按字节编程是 F4 的写法，在 C8 上作废，一个 32 位值要分两次半字写，见 [RM0008](#source-rm0008-flash)。PM0075 Rev 2 第 2.3.3 节再加两条：目标不是 `0xFFFF` 时这次写被跳过并置 PGERR（写 `0x0000` 例外）；写入宽度不是半字时返回总线错误。

**两把钥匙。** 先把 `0x45670123`、再把 `0xCDEF89AB` 写进 `FLASH_KEYR`，`FLASH_CR` 的 LOCK 才清零，写完再上锁，见 [RM0008](#source-rm0008-flash)。顺序错了，后果比「返回错误」重：PM0075 Rev 2 第 2.3.2 节规定会返回总线错误，并把 FPEC 和 `FLASH_CR` 锁到下一次复位。

**地图。** 这张地图是本书和 `examples/iap-bootloader` 在用的那一版，不是手册规定的唯一划分，见 [本仓库例程](#source-project-examples)。Bootloader 从 `0x08000000` 起，16 KB，16 页，到 `0x08004000` 之前；参数区从 `0x08004000` 起，2 KB，2 页，到 `0x08004800` 之前；APP 从 `0x08004800` 起，46 KB，46 页，长度 `0xB800`，到 `0x08010000` 之前。三块相加是 64 KB。例程用了这张地图和帧头 `0x5A`，没有用参数区，也没有逐块应答。

**跳转的两个字。** APP 区第 0 个字是 MSP 初值，第 1 个字在 `0x08004804`，是 `Reset_Handler` 的地址，见 [PM0056](#source-pm0056-vector)。链接脚本的起点和 `SCB->VTOR` 都要是 `0x08004800`；只改一个，或者 `VTOR` 留在 0，中断仍然进 Bootloader 的向量表。`VTOR` 的低 9 位恒为 0，见 [PM0056 Rev 7 第 4.4.4 节](#source-pm0056)；`0x4800` 正好是 `0x200` 的 36 倍。

**读保护。** 这颗料的无保护值是 `0xA5`，写回它会先整片擦除主闪存；擦掉选项字节得到的 `0xFF` 也算保护，见 [PM0075](#source-pm0075-rdp)。打开保护后第 0–3 页自动写保护、调试器读不到 Flash，这两句出自 PM0075 Rev 2 第 2.4.1 节，超出这张卡的范围。

**数字的性质。** 页擦除 20–40 ms、半字 40–70 µs、2–3.6 V 的擦写电压出自 [DS5319 Rev 20 表 28](#source-ds5319)，脚注写的是「设计保证，未经量产测试」；1 万次寿命和 30 年保持出自同一份数据手册的表 29，是特性评估值。

**换系列时。** F4 按扇区擦，写多宽由 PSIZE 和供电电压决定，读保护还多一个不可逆的 Level 2，见 [RM0090](#source-rm0090)。这一章的页号、地址和半字规则，到 F4 上要全部按 RM0090 重查。串口仍是第 06 章的第 30 脚 PA9、第 31 脚 PA10，这里只旁注。

## 关键插图

<p align="center">
  <img src="../assets/diagrams/sample-12-iap-map.svg" width="760" alt="中容量是 1 KB 页；APP 从 0x08004800 起，长度 0xB800；跳转要装入第 0 字和第 1 字">
  <br><sub>▲ 自绘。STM32F103C8T6，中容量，64 KB，1 KB 一页。正常路径先写 0x45670123，再写 0xCDEF89AB，半字写入 APP，再从 0x08004800 装入 MSP，从 0x08004804 装入复位入口，VTOR 写成 0x08004800。失败路径是钥匙反序、末页写成 0x0801FC00，或 VTOR 仍为 0。出处是 [RM0008 Rev 21 第 3 章](#source-rm0008-flash) 和 [PM0056](#source-pm0056-vector)。</sub>
</p>

<p align="center">
  <img src="../assets/gif/iap-jump.gif" width="640" alt="两把钥匙按顺序写完，CPU 读出 MSP 和复位入口">
  <br><sub>▲ 网页和公众号辅图。只播放正常路径：先 0x45670123，后 0xCDEF89AB，一个半字落进 APP，然后读出 MSP 和复位入口。印刷以静态主图为准。反序钥匙和 0x0801FC00 不在这条 GIF 上。</sub>
</p>

图里有三组内容：正常路径是两把钥匙、一个半字、跳转用的两个字和 VTOR；失败路径是反序的钥匙、越界的末页和留在 0 的 VTOR；旁注说明按字节编程在这颗料上作废。图上写「反序钥匙让 LOCK 保持置位、擦除报错」，只说了一半：按 PM0075 Rev 2 第 2.3.2 节，写错钥匙还会返回总线错误，并锁到下一次复位，所以出错以后要先复位再重试。

`flash-iap.svg` 留作辅图，不播放它。页边界、两把钥匙和跳转用的两个字都在静态主图上。

## 时序与状态

下表把地图、钥匙、半字和跳转放在一起，每一行都能用第 1 节的式子算回去：

| 项目 | 起始 | 长度 | 页 | 结束于或结果 |
| --- | --- | --- | --- | --- |
| Bootloader | `0x08000000` | 16 KB | 0–15 | `0x08004000` 之前 |
| 参数区 | `0x08004000` | 2 KB | 16–17 | `0x08004800` 之前 |
| APP | `0x08004800` | 46 KB，`0xB800` | 18–63 | `0x08010000` 之前 |
| 末页 | `0x0800FC00` | 1 KB | 63 | 落在 APP 里 |
| 失败地址 | `0x0801FC00` | — | — | 不在这 64 KB 里 |
| 钥匙 | 先 `0x45670123` | 后 `0xCDEF89AB` | — | 反序：总线错误，锁到下一次复位 |
| 半字 | 偶地址 | 16 位 | — | 擦除态 `0xFFFF`；按字节编程在 C8 上作废 |
| 跳转 | `0x08004800` 的字是 MSP | `0x08004804` 的字是复位入口 | — | `VTOR = 0x08004800`；留在 0 仍进 Bootloader |

本章 Bootloader 的状态迁移如下。时间按 [DS5319 Rev 20 表 28](#source-ds5319) 的最长值和 115200 波特算，等待时长是例程设定：

| 状态 | 做什么 | 最长耗时 | 成功去哪 | 失败去哪 |
| --- | --- | --- | --- | --- |
| 等 'U' | 每 10 ms 查一次串口 | 500 ms | 回 ACK，进「等帧头」 | 查标志 |
| 等帧头 | 跳过多余的 'U'，收 `0x5A` 和长度 | 5 s | 擦除 | 回 NAK，查标志 |
| 擦除 | 擦参数页，再擦 APP 区 | 47 页 × 40 ms = 1.88 s | 回 ACK，收块 | 回 NAK，查标志 |
| 收块、写块 | 收 512 字节，写 256 个半字并读回 | 512 × 86.8 µs ≈ 44.4 ms，加 256 × 70 µs ≈ 17.9 ms | 回 ACK，收下一块或校验和 | 回 NAK，查标志 |
| 校验 | 按 Flash 的内容算累加和并比较 | — | 写标志，回 ACK | 回 NAK，查标志 |
| 查标志 | 读 `0x08004000` 的半字 | — | 是 `0x5AA5` 就跳转 | 回到「等 'U'」 |

## 常见坑与出处

| 现象 | 原因 | 处理 | 出处 | 出处能证明的部分 |
| --- | --- | --- | --- | --- |
| 注释写成小容量，页大小却对 | 密度名用错了 | 改成中容量；页仍是 1 KB，共 64 页 | [RM0008](#source-rm0008-flash) | 中容量按 1 KB 擦除；大容量的 2 KB/页在 C8 上作废 |
| 解锁那一步出总线错误，之后擦写全部失败 | 两把钥匙顺序反了或写错 | 先写 `0x45670123`，再写 `0xCDEF89AB`；写错以后先复位 | [RM0008](#source-rm0008-flash) | 顺序是 `0x45670123` 然后 `0xCDEF89AB`。总线错误和锁到复位出自 PM0075 Rev 2 第 2.3.2 节，不在这张卡里 |
| 写半字报错，读回的不是写进去的值 | 目标没擦，不是 `0xFFFF`；或地址不是偶数 | 先擦整页，再按偶地址写半字 | [RM0008](#source-rm0008-flash) | 编程粒度是 16 位，擦除态是 `0xFFFF`，按字节编程在这颗料上作废。没擦就写会被跳过并置 PGERR，出自 PM0075 Rev 2 第 2.3.3 节 |
| 跳转后死机，或中断跑回 Bootloader | 没装入两个字，或 VTOR 仍为 0 | 从 `0x08004800` 装入 MSP 和复位入口，并写 `VTOR` | [PM0056](#source-pm0056-vector) | 第 0 字是栈初值，第 1 字是复位。对齐要求不在这张卡里 |
| APP 的启动代码还没跑完，就先进了 SysTick 中断 | 先停 SysTick、后调 `HAL_RCC_DeInit()`，后者经 `HAL_InitTick()` 又把 SysTick 打开 | 停 SysTick 放到 `HAL_RCC_DeInit()`、`HAL_DeInit()` 之后，并清 PENDST | [本仓库例程](#source-project-examples) | 只证明 `examples/iap-bootloader` 是先停后复位的顺序；`HAL_RCC_DeInit()` 调用 `HAL_InitTick()` 出自 STM32CubeF1 的源码 |
| 升级传到一半就失败，校验对不上 | 擦写期间腾不出手读串口，串口只能暂存 1 个字节，上位机却一直在发 | 每块写完回 ACK，上位机等到再发下一块 | [本仓库例程](#source-project-examples) | 只证明例程的帧格式是 `0x5A`、4 字节长度、数据、4 字节累加和，而且没有逐块应答 |
| APP 长度和链接脚本对不上 | 长度没按 46 KB 写 | 起点 `0x08004800`，长度 `0xB800` | [本仓库例程](#source-project-examples) | `examples/iap-bootloader` 的 APP 区是 46 KB，即 `0xB800` |
| 实验写到 `0x0801FC00` | 把 128 KB 料的末页套到了 C8 上 | C8 的最后一页是 `0x0800FC00` | [DS5319](#source-ds5319-swd) | STM32F103x8 的闪存是 64 KB；128 KB 的末页在这颗料上作废 |
| 按别的系列的无保护值解除读保护 | 这颗料只认一个无保护值 | 无保护是 `0xA5`，写回它会整片擦除 | [PM0075](#source-pm0075-rdp) | RDP 为 `0xA5` 才允许读出；编程回 `0xA5` 会先整片擦除主闪存 |

F4 的扇区擦除时间、VPP 和 Level 2 没有放进这张表：它们出自 RM0090 和 DS8626，不是这颗 C8 的数字。

## 相关资源

- RM0008《STM32F10xxx 参考手册》第 3 章 Embedded Flash memory（页结构、KEY、编程流程）。
- RM0090《STM32F4 参考手册》第 3 章 FLASH（扇区结构、SER/SNB、编程位宽）。
- 数据手册 DS：擦写寿命、数据保持时间、编程/擦除时间。
- 应用笔记 AN2557《STM32F10xxx in-application programming using the USART》。
- Cortex-M3/M4 权威指南：向量表、`SCB->VTOR`、异常模型。
- 配图：`../assets/animations/flash-iap.svg`（作者自绘矢量图）。

- 手机阅读版：[第 12 章 · Flash与IAP升级（公众号图文）](https://mp.weixin.qq.com/s/_pvTj84j-zOem8Iawpqiyw)
