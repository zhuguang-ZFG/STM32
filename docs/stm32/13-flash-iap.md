---
title: S13 内部 Flash 与 IAP：固件给自己动手术
status: done
difficulty: 3
minutes: 40
---

# S13 内部 Flash 与 IAP：擦写规则与选项字节

> 🎯 程序住在 Flash 里，能不能让程序**自己改写** Flash？能——存参数、做 IAP（应用内编程/远程升级）都靠它。但 Flash 是个怪房东：写只能 1→0，想 0→1 必须整页（扇区）推倒重建。

## 本章精髓

1. 擦写铁律：按"位"只能写 0，按"扇区"才能擦回全 1，所以存参数要先擦后写，且擦除单位是扇区（F407 扇区大小 16K~128K 不等，布局见 RM0090 §3）。
2. 擦写要"解锁+等空闲+设并行位数"：KEYR 序列解锁 → BSY 空闲 → PSIZE（按供电电压选 x8/x16/x32/x64）→ 擦/写 → 上锁，漏一步要么不动要么 HardFault。
3. IAP 的双固件结构：Bootloader 住扇区 0，App 住后面；跳转前三件事：关中断→设 MSP（App 栈顶）→跳 App 复位入口；向量表偏移（VTOR）别忘改。

- **能理解**：为什么"擦在运行的代码扇区"会让 PC 瞬间跑飞；为什么 VTOR 必须在跳转前改、不能让 App 的 reset handler 自己改。
- **能用**：写一个"参数不随断电丢失"的小框架；画出 IAP 双固件内存布局并实现跳转函数。

## 先修

- [B3 链接脚本](../build/03-linker-script.md)、[B4 启动](../build/04-startup.md)（向量表）、[S2 时钟](02-rcc-clock.md)。

## 先跑起来（10 分钟 quick win）

在最后一个扇区写入 `0xA5A5`，断电重启后读回，数据还在，你就拥有了"不丢的记忆"。

写入之前先押个顺序：Flash 这块地方，是想写就写，还是得先走完什么手续才轮得到你写？再顺手押一个：扇区里原有的旧数据，不做任何处理直接盖上去，行吗？押完往下读，两把钥匙和擦的规矩会轮流登场。

## 动画：IAP 跳转接力

四阶段循环：① 双固件布局（Bootloader 住扇区 0、App 住后面，一条蓝线连接两块）；② 关中断 + 复位 SysTick（PRIMASK 置 1、SysTick 的红框熄灭）；③ 设 VTOR + MSP（向量表指针从扇区 0 切到 App 起始、MSP 从 App 第一字载入）；④ 跳 App 复位入口（PC 接力棒从 Bootloader 末尾滑到 App 的 reset handler）。每一步的"此刻向量表指向谁、此刻栈顶是谁"在画面上随阶段切换：这是 IAP 区别于"普通函数调用"的全部秘密。

![IAP 跳转接力动画](/anim/iap-handoff.svg)

## 板卡事实

- Flash 控制器基址 `FLASH_R_BASE = AHB1 + 0x3C00 = 0x40023C00`（CMSIS 已核对）；寄存器序：ACR(0x00)、KEYR(0x04)、OPTKEYR(0x08)、SR(0x0C)、CR(0x10)、OPTCR(0x14)、OPTCR1(0x18)。
- 解锁键两把：`KEY1 = 0x45670123`、`KEY2 = 0xCDEF89AB`（RM0090 FLASH 解锁键，写 KEYR 序列即解锁；这两把不是 CMSIS 宏，是手册常数）。
- F407 擦除并行度 PSIZE：x8/x16/x32 三档（2.7–3.6V 选 **x32**）；F427/F439 才有 x64，**F407 不要碰 x64**，以 RM0090"电压-并行度"对照表为准。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 扇区地图 | F407 扇区布局与"参数区选哪扇"的考量 | 配置 |
| 解锁序列 | KEYR 两把钥匙；PSIZE 与电压的关系 | 配置 |
| 擦写例程 | 扇区擦除+字写入逐行；BSY 等待纪律 | 代码分析 |
| 参数框架 | 结构体+魔数+校验和的防呆设计 | 代码分析 |
| IAP 原理 | 双固件布局图；跳转函数逐行（MSP/VTOR/关中断） | 代码分析 |
| 选项字节 | 读保护 RDP 三级与"锁死救砖"常识 | 配置 |
| SPL 对照 | FLASH_Unlock/FLASH_EraseSector 落位 | 库解析 |

## 一、扇区地图：参数区选哪一扇

F407 是 1MB Flash，11 个扇区大小不等（RM0090 §3，CMSIS F4 头文件此芯片一档）：

| 扇区 | 起始地址 | 大小 | 用途建议 |
|---|---|---|---|
| 0 | `0x08000000` | 16 KB | Bootloader（IAP） |
| 1 | `0x08004000` | 16 KB | App 起点 / 或 Bootloader 续 |
| 2 | `0x08008000` | 16 KB | App |
| 3 | `0x0800C000` | 16 KB | App |
| 4 | `0x08010000` | 64 KB | App |
| 5 | `0x08020000` | 128 KB | App |
| 6 | `0x08040000` | 128 KB | App |
| 7 | `0x08060000` | 128 KB | App |
| 8 | `0x08080000` | 128 KB | App |
| 9 | `0x080A0000` | 128 KB | App |
| 10 | `0x080C0000` | 128 KB | App |
| 11 | `0x080E0000` | 128 KB | **参数区**（最后扇区，与代码隔离） |

两条选址铁律：

1. **参数区与代码区物理隔离**：别把参数塞进代码扇区的空隙，擦参数等于擦代码，PC 瞬间跑飞。F407 最后一个 128KB 扇区是首选（如果 App 用不满前面 10 个扇区）。
2. **IAP 双固件布局**：Bootloader 住扇区 0（16KB 足够放一个最小 bootloader），App 从扇区 1 起；App 的起始地址 = `0x08004000`，这正是第五节跳转函数的 `app_addr`。Bootloader 的链接脚本 `ORIGIN` 落 `0x08000000`、App 的 `ORIGIN` 落 `0x08004000`，这就是 [B3 链接脚本](../build/03-linker-script.md) 里那条 MEMORY 规则的实战场景。

## 二、解锁序列：两把钥匙与并行度

Flash 上锁后，CR 的 PG/SER/MER 全部被硬件忽略（防误写）。解锁是把 KEY1、KEY2 顺序写进 KEYR：

```c
#include "stm32f407.h"   /* CMSIS：FLASH_TypeDef + 各 _Msk */

static void flash_unlock(void)
{
    /* 已上锁才需要解（重复写 KEY1/KEY2 在已解锁态是错的，会触发误写保护） */
    if (FLASH->CR & FLASH_CR_LOCK_Msk) {     /* LOCK = CR bit31（CMSIS 已核对） */
        FLASH->KEYR = 0x45670123u;            /* KEY1 */
        FLASH->KEYR = 0xCDEF89ABu;            /* KEY2 */
    }
}

static void flash_lock(void)
{
    FLASH->CR |= FLASH_CR_LOCK_Msk;           /* 一位置 1 即重新上锁 */
}
```

擦/写前还有一步"设并行度"：CR 的 PSIZE（bits8-9，CMSIS：0x300）。F407 在 2.7–3.6V 供电下选 `0b10 = x32`（一次写 32 位）：

```c
#define FLASH_PSIZE_X32   (0x2u << FLASH_CR_PSIZE_Pos)   /* 0x200 */
```

PSIZE 必须在 STRT 之前设好，硬件按 PSIZE 决定每次 DRAM-flash 的字节数；选错档（低压跑 x32）会写坏数据不报错。

## 三、擦写例程：扇区擦除、字写入、BSY 等待

**扇区擦除**完整序列（以擦参数扇区 11 为例）：

```c
static void flash_erase_sector(uint8_t snb)
{
    flash_unlock();
    FLASH->CR &= ~FLASH_CR_PSIZE_Msk;
    FLASH->CR |= FLASH_PSIZE_X32;                  /* 设并行度 */
    FLASH->CR &= ~FLASH_CR_SNB_Msk;                 /* 清旧扇区号（SNB = CR bits3-6） */
    FLASH->CR |= (snb << FLASH_CR_SNB_Pos);         /* 写新扇区号 */
    FLASH->CR |= FLASH_CR_SER_Msk;                 /* 选扇区擦除（SER = bit1） */
    FLASH->CR |= FLASH_CR_STRT_Msk;                 /* 触发擦除（STRT = bit16）——硬件置后自清 */
    while (FLASH->SR & FLASH_SR_BSY_Msk) { }       /* BSY = SR bit16：擦完才清 */
    /* 收尾：清可能的 EOP、上锁 */
    if (FLASH->SR & FLASH_SR_EOP_Msk) { FLASH->SR = FLASH_SR_EOP_Msk; }  /* EOP = SR bit0，写 1 清 */
    FLASH->CR &= ~FLASH_CR_SER_Msk;
    flash_lock();
}
```

**字写入**（每次 32 位）：

```c
static void flash_write_word(uint32_t addr, uint32_t data)
{
    flash_unlock();
    FLASH->CR &= ~FLASH_CR_PSIZE_Msk;
    FLASH->CR |= FLASH_PSIZE_X32 | FLASH_CR_PG_Msk;  /* PG = CR bit0：编程使能 */
    *(volatile uint32_t *)addr = data;                 /* 直接写 Flash 地址——硬件自己编程 */
    while (FLASH->SR & FLASH_SR_BSY_Msk) { }
    if (FLASH->SR & FLASH_SR_EOP_Msk) { FLASH->SR = FLASH_SR_EOP_Msk; }
    FLASH->CR &= ~FLASH_CR_PG_Msk;
    flash_lock();
}
```

三条等待纪律，缺一就翻车：

1. **解锁与擦/写之间不能有别的 Flash 访问**（含向量取指之外的中断处理函数若在 Flash 里运行），把这段代码搬进 RAM 执行是严谨做法（见骨架坑列表）；
2. **BSY 必须等到底**（擦一个 128KB 扇区最坏几百毫秒，`while` 轮询要给 WDT 喂狗）；
3. **EOP 写 1 清零**：SR 大多标志是"写 1 清"，按 RM0090 §3 顺序处理。

> **【注】** 擦写期间任何中断如果处理函数也在 Flash 里运行，CPU 取指会和 Flash 编程抢总线，某些 F4 版本上会卡死。擦写关键路径放 SRAM 执行（`__attribute__((section(".ramfunc")))` + 链接脚本，见 [B3](../build/03-linker-script.md)）是工业代码的标准姿势。

## 四、参数框架：魔数 + 校验和的防呆设计

存进 Flash 的不是裸数据，是一份**自描述的快照**：

```c
#include <stdint.h>
#include <string.h>

#define PARAM_MAGIC   0x50415241u   /* 'PARA' */
#define PARAM_ADDR    0x080E0000u   /* 扇区 11 起始 */

typedef struct {
    uint32_t magic;
    uint32_t version;
    /* 业务字段 */
    uint32_t baud;
    uint32_t sample_rate;
    /* 校验 */
    uint32_t crc;
} params_t;

static uint32_t crc32_simple(const uint8_t *p, uint32_t n)   /* 简易 CRC32，足以防单字节错 */
{
    uint32_t c = 0xFFFFFFFFu;
    for (uint32_t i = 0; i < n; i++) { c ^= p[i]; for (int b = 0; b < 8; b++) c = (c >> 1) ^ (0xEDB88320u & -(c & 1u)); }
    return ~c;
}

/* 复位时调：找不到合法快照 → 用默认值回填 */
params_t params_load_or_default(const params_t *defaults)
{
    const params_t *stored = (const params_t *)PARAM_ADDR;   /* Flash 直接可读 */
    if (stored->magic == PARAM_MAGIC) {
        params_t probe;
        memcpy(&probe, stored, sizeof probe);
        if (crc32_simple((const uint8_t *)&probe, offsetof(params_t, crc)) == probe.crc) {
            return probe;      /* 校验通过：用快照 */
        }
    }
    return *defaults;          /* 魔数错或校验败：回退默认，防"半擦"数据被当合法 */
}
```

三道防呆：**魔数**（`'PARA'` 当签名，擦空时读到 0xFFFFFFFF 不等于合法）+ **校验和**（防单字节损坏）+ **默认回退**（校验败不报错，回退，这是"半擦"状态下的安全选择）。骨架坑列表里的"擦除中断电进入半擦状态"靠这个三层防御兜底：即便某次擦了一半断电，下次复位读到的是错魔数或坏 CRC，照样回退默认值。

> **【注】** 升级型产品用**双备份**：A/B 两个快照交替写、各自带版本号：写 A 成功才切到 A、失败停在 B。这样擦 A 中途断电，B 仍是上次有效值。本节框架是单备份基础版，双备份是把"半擦"风险降到零的工业级升级。

## 五、IAP 原理：双固件布局与跳转函数

Bootloader 与 App 各有独立的向量表与复位入口。Bootloader 跑完升级逻辑后，把控制权交给 App，这不是"函数调用"（App 有自己的栈、自己的中断表、自己的复位序列），是**硬件级接力**。跳转函数（CMSIS-Core 内建 intrinsic 全部就位）：

```c
#include "stm32f407.h"   /* SCB、SysTick、__set_MSP、__disable_irq */

typedef void (*reset_handler_t)(void);

#define APP_ADDR  0x08004000u   /* App 起始 = 扇区 1 */

static void jump_to_app(void)
{
    /* ① 关掉所有可屏蔽中断：PRIMASK 置 1，防 NVIC 里挂着的请求在 VTOR 切换瞬间触发 */
    __disable_irq();

    /* ② 复位内核 SysTick：清 CTRL、清挂起位——App 启动时它必须是干净的 */
    SysTick->CTRL = 0;
    SCB->ICSR = SCB_ICSR_PENDSTCLR_Msk;

    /* ③ 重设向量表偏移：VTOR 指向 App 起始处的向量表 */
    SCB->VTOR = APP_ADDR;

    /* ④ 设主栈指针：App 向量表第一字就是它的初始栈顶 */
    __set_MSP(*(uint32_t *)APP_ADDR);

    /* ⑤ 取 App 复位入口（向量表第二字）并跳——Thumb 地址位 0 已由链接器置好 */
    reset_handler_t handler = (reset_handler_t)(*(uint32_t *)(APP_ADDR + 4u));
    handler();

    /* 跳过去就回不来了；理论兜底死循环 */
    while (1) { }
}
```

五步为什么是这个顺序（每一步都能在动画里对上阶段）：

- **关中断优先**：VTOR 切换是个"窗口期"，期间任何中断都会按**旧向量表**取入口，而旧表马上要被覆盖，取到垃圾地址就 HardFault。关 PRIMASK 把窗口期焊死；
- **VTOR 在 MSP 之前**：先让向量表归位，再从新表读栈顶；顺序反了，MSP 是从旧表读的；
- **跳复位入口而非 `main`**：App 的复位入口才是 App 启动代码的真正起点（[B4 启动](../build/04-startup.md) 里 .data/.bss 初始化在那之前），直接跳 main 会跳过这些初始化；
- **不复位外设**：IAP 的 Bootloader 已经配好的外设（如 UART）由 App 接管决定复位与否，这是设计选择，不是 bug。需要干净环境时由 Bootloader 自己复位（RCC 一刀切）。

App 一侧记得两件事：链接脚本 `ORIGIN = 0x08004000`、`SCB->VTOR` 在 reset handler 早期就指向自己（或保留 Bootloader 设的 VTOR，因为已经指向 App）；通常 App 的 startup 代码自己再写一次 VTOR 兜底。

## 六、选项字节：读保护 RDP 与"锁死救砖"

Flash 顶上还有一层"选项字节"（OPTCR/OPTCR1，CMSIS 已核对偏移 0x14/0x18），存的是芯片级配置：读保护（RDP）、写保护（WRP）、看门狗硬件使能、复位阈值等。对开发者影响最大的是 **RDP 三级**：

- **Level 0（默认）**：OPTCR 的 RDP 字段写 `0xAA`，无读保护，调试器可读可擦；
- **Level 1**：RDP 写任意非 `0xAA`、非 `0xCC` 的值，读保护启用，调试器能擦但不能读 Flash 内容；从 RAM 启动也被禁；
- **Level 2**：RDP 写 `0xCC`：**永久**读保护，Flash 永远不能再被调试器访问，**也不能降回 Level 0/1**（这一档是单向门，写错了芯片基本作废，只能当 OTP 用）。

救砖常识：Level 2 是"锁死"，没有"解锁"，只能擦整片回 Level 0 但 Flash 内容全失（这已经是好消息）；写 Level 2 之前先用 `0xAA`/Level 1 跑产品验证。选项字节解锁有自己的两把钥匙（OPTKEYR，`0x08192A3B` / `0x4C4D4E4F`，与主 Flash 解锁键不同），写法和主解锁同构。**写 Level 2 是一行代码就毁片的操作，没有板子量产前别碰。**

## 七、SPL 对照：`FLASH_Unlock` / `FLASH_EraseSector` 落位

SPL 的 Flash 操作 API 几乎是寄存器序列的逐字直译（stm32f4xx_flash.c V1.8.0）：

| SPL API | 寄存器序列（对照本节实现） |
|---|---|
| `FLASH_Unlock()` | 写 KEYR = KEY1、KEY2（解锁；本节 `flash_unlock` 同） |
| `FLASH_Lock()` | CR `\|= LOCK`（本节 `flash_lock` 同） |
| `FLASH_EraseSector(sn)` | 设 PSIZE → 清/写 SNB → SER → STRT → 等 BSY → 清 SER |
| `FLASH_ProgramWord(addr, data)` | 设 PSIZE → PG → 写地址 → 等 BSY → 清 PG |
| `FLASH_GetStatus()` | 读 SR 的 BSY/PGSERR/WRPERR |
| `FLASH_WaitForLastOperation()` | `while (FLASH->SR & BSY)` + 清 EOP + 返回错误码 |

看一眼就明白：SPL 没有替你做任何"魔法判断"，它把"等 BSY、清 EOP、报 WRPERR"这些**纪律性步骤**包成函数。库的价值在此：寄存器序列太长，手写容易漏一步；SPL 把漏步做成"漏 API 调用"，编译期就看得见。**读库姿势**照旧：拿到 `FLASH_EraseSector` 先问"它动了 CR 的哪几位"，逐位与本节的 `flash_erase_sector` 对答案（[S15](15-spl-anatomy.md) 的方法论在 Flash 上特别好用，因为这里的"翻译"几乎是 1:1）。

## 附录：本章代码落点

本章擦写例程、参数框架、跳转函数全部以内联代码呈现（无独立工程），可直接进任何项目主组件。Flash 控制器基址与位定义对照见 `docs/.vitepress` 工具链对 CMSIS 头文件的核对记录（`.trellis/ref/cmsis/stm32f407xx.h`）；W25Q 外部 Flash 的 SPI 读写（参数备份到外部 Flash 时复用）见 [S12](12-spi.md)。

## 记忆锚点

::: tip 一句话记住
**写 1 变 0 随意，0 回 1 整扇区；解锁等空再动手，IAP 跳转三件宝：关断、换栈、改向量。**
:::

**延伸**：IAP 跳转与启动过程（[B4](../build/04-startup.md)）同构；Flash 擦写算法灌 RAM 的做法与 OpenOCD 烧录（[B6](../build/06-flash-debug.md)）原理一致。

## 实物实验

- 参数保存：改参数→断电→重上电，串口打印参数仍在；
- 故意写坏校验和，看固件回退默认值，防呆机制亲自验证。

## 常见坑

- **擦正在运行的扇区**：代码自己擦掉自己，瞬间跑飞，参数区别放代码扇区。
- **擦除中断电**：扇区进入"半擦"状态；参数框架必须有双备份或掉电检测。
- **PSIZE 与电压不配**：低压跑 x32 并行写，写坏数据不报错；F407 上别碰 x64。
- **IAP 跳完中断向量没偏移**：App 的中断全跳到 Bootloader 的表，VTOR 是 IAP 的第一大坑。
- **解锁重复写 KEY1/KEY2**：已解锁态再写钥匙触发误写保护；先查 LOCK 位。

## 短自测

1. 为什么存参数到 Flash 必须"先擦后写"？
<details><summary>参考答案</summary>Flash 按位只能 1→0 写，0→1 必须整扇区擦除。如果 Flash 上已有 0xA5A5、想改写成 0x3C3C（位级上需要把某些 0 翻回 1），不擦就只能 1→0，写不出目标位模式。先擦把整个扇区复位为全 1（全 0xFF），再写就只有 1→0 一种方向，目标位模式自然落成。</details>

2. IAP 跳转函数为什么先关中断、再设 VTOR，而不是反过来？
<details><summary>参考答案</summary>VTOR 切换是个"窗口期"：期间任何可屏蔽中断都会按 VTOR 当时指向的向量表取入口。若先改 VTOR 再关中断，窗口期内挂着的请求会按**新表**取入口，而新表（App 的）此刻 MSP 还是 Bootloader 的、栈布局未就绪，极易取到未对齐地址 HardFault。先关 PRIMASK 焊死窗口期，再改 VTOR，中断进不来，安全切换。</details>

3. 跳转函数为什么不跳 App 的 `main`，而跳它的"复位入口"（向量表第二字）？
<details><summary>参考答案</summary>App 的复位入口是它启动代码的真正起点：[B4 启动](../build/04-startup.md)里 .data 拷贝、.bss 清零、SystemClock 配置都在 main 之前发生。直接跳 main 会跳过这些初始化，App 运行在"半初始化"状态：全局变量全是 0 或未定义、系统时钟没配好。跳复位入口等于让 App 重新走一次完整的上电启动序列，正是 IAP 的本意。</details>

4. RDP 的三个级别里，哪一级是"单向门"？为什么量产前别用它做"防抄板调试"？
<details><summary>参考答案</summary>Level 2（写 0xCC）是单向门：一旦写入，Flash 永远不能再被调试器访问，也永远降不回 Level 0/1（只能整片擦除回 Level 0，但内容全失）。它适合真正量产定型后做终极防抄板，而不是开发期用来"挡调试"，开发期写错 Level 2 就意味着这块芯片基本作废，只能当 OTP 用。量产前用 Level 1（可降回 Level 0）就够防调试器读，且能擦回来。</details>

5. 给一段"擦写关键路径放 SRAM 执行"的最小做法（提示：链接脚本 + section 属性）。
<details><summary>参考答案</summary>链接脚本加一段 `.ramfunc : { *(.ramfunc) } >RAM AT>FLASH`（VMA 在 RAM、LMA 在 Flash，[B3 链接脚本](../build/03-linker-script.md)的 VMA/LMA 范式）；启动代码把这段从 Flash 拷到 RAM；擦写函数加 `__attribute__((section(".ramfunc")))`。这样擦写期间 CPU 从 RAM 取指，不与 Flash 编程抢总线，规避某些 F4 版本上的卡死风险。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| FLASH_TypeDef 偏移（KEYR/SR/CR/OPTCR） | CMSIS `stm32f407xx.h`（本站 `.trellis/ref/cmsis/`，逐位核对） |
| CR 位（PG/SER/MER/SNB/PSIZE/STRT/LOCK） | 同上，本节第二、三节 |
| SR 位（BSY/EOP/WRPERR） | 同上；WRPERR = bit4 |
| 解锁键 KEY1/KEY2 | RM0090 FLASH 解锁键（手册常数，非 CMSIS 宏） |
| 扇区布局表 | RM0090 §3（F407 1MB / 11 扇区） |
| 跳转用 CMSIS-Core 内建 | `__disable_irq`、`__set_MSP`、`SCB->VTOR`、`SysTick->CTRL` |
| IAP 跳转动画 | [iap-handoff.svg](/anim/iap-handoff.svg)（四阶段接力） |
| SPI 擦写外部 Flash | [S12 SPI](12-spi.md) W25Q 实战 |

## 你做到了

- 固件拥有了"长期记忆"；
- IAP 的原理图刻进脑子，OTA（P10）与 bootloader 设计不再神秘。

<div class="achievement">
✅ 下一站：<a href="14-pwr.html">S14 低功耗</a>：电池供电的产品想活过一年，先学会睡觉。
</div>
