/**
 * main.c —— 03-uart-dma：串口收发的两级缓冲，和"可写 ≠ 发完"
 *
 * 这个工程想讲清三件事：
 *
 * 1) 波特率是算出来的，不是填出来的。
 *    默认 16 倍过采样（OVER8=0）时  baud = f_PCLK / BRR。时钟一变，波特率就跟着变，
 *    所以 BRR 必须由"回读出来的 PCLK"算，而不是写死一个魔数。
 *    （1MHz 那种 PLL 参考时钟不能直接喂 USART：BRR=9 时实际 111111，误差 -3.549%，
 *      单这一项就吃掉 8N1 帧 5.882% 总预算的六成，收发已经不可靠了。见 S2/S7。）
 *
 * 2) 接收有两级缓冲：串口自己的移位寄存器/FIFO，DMA 搬进我们的环形数组。
 *    DMA 不理解"帧"，它只理解"搬够 N 个字节"。
 *    IDLE 只提示总线空闲；应用协议必须自行定义帧边界。
 *
 * 3) TXE 只说明"数据寄存器空出来了"，TC 才说明"停止位已经发出去"。
 *    在 RS-485 这种需要切方向的场合，漏掉 TC 就会把最后一位切掉。
 *
 * 引脚依据：DS8626 Table 9，PA9=USART1_TX(AF7)、PA10=USART1_RX(AF7)。
 *
 * ⚠ DMA stream/channel 的取值见下方宏区。权威来源是 RM0090 的
 *   "DMA2 request mapping" 表（Rev 18 Table 43）；本次实施未能取得该表正文（见任务研究记录），
 *   所以这里不把它当成"板上事实"，而是集中成两个宏：
 *   换板子/换 IDF 版本时只改这两行，改完跑一遍下面的自检步骤即可确认。
 *
 * 上板自检步骤（USB-TTL 接 PA9/PA10，115200 8N1）：
 *   a. 电脑上发任意字符串；
 *   b. g_rx_bytes 与 g_frames 应同时增长，g_frames 是 IDLE 通知次数，不是协议帧数；
 *   c. 蓝灯每收到一帧闪一次；
 *   d. 若 g_rx_bytes 始终为 0，说明 stream/channel 配错了——
 *      回查 RM0090 的 DMA2 request mapping 表，改上面两个宏重来。
 */

#include <stdint.h>
#include "../platform/uart.h"
#include "../../common/behavior/circular.h"

/* ============================ 板级/通道配置 ============================ */

#ifndef USART1_BASE
#define USART1_BASE   (0x40011000UL)   /* APB2PERIPH_BASE + 0x1000 */
#endif
#ifndef DMA2_BASE
#define DMA2_BASE     (0x40026400UL)   /* AHB1PERIPH_BASE + 0x6400 */
#endif
#ifndef DMA2_S5_BASE
#define DMA2_S5_BASE  (DMA2_BASE + 0x088UL)
#endif
#ifndef DMA2_LISR
#define DMA2_LISR     (*(volatile uint32_t *)(DMA2_BASE + 0x00UL))
#endif
#ifndef DMA2_HISR
#define DMA2_HISR     (*(volatile uint32_t *)(DMA2_BASE + 0x04UL))
#endif
#ifndef DMA2_HIFCR
#define DMA2_HIFCR    (*(volatile uint32_t *)(DMA2_BASE + 0x0CUL)) /* 标志清除只走这个寄存器 */
#endif

#define GPIOA_BASE    (0x40020000UL)
#ifndef GPIOA_MODER
#define GPIOA_MODER   (*(volatile uint32_t *)(GPIOA_BASE + 0x00UL))
#endif
#ifndef GPIOA_AFRH
#define GPIOA_AFRH    (*(volatile uint32_t *)(GPIOA_BASE + 0x24UL)) /* 引脚 8..15 */
#endif

#define GPIOF_BASE    (0x40021400UL)
#ifndef GPIOF_MODER
#define GPIOF_MODER   (*(volatile uint32_t *)(GPIOF_BASE + 0x00UL))
#endif
#ifndef GPIOF_BSRR
#define GPIOF_BSRR    (*(volatile uint32_t *)(GPIOF_BASE + 0x18UL))
#endif

#define RCC_BASE      (0x40023800UL)
#ifndef RCC_PLLCFGR
#define RCC_PLLCFGR   (*(volatile uint32_t *)(RCC_BASE + 0x04UL))
#endif
#ifndef RCC_CFGR
#define RCC_CFGR      (*(volatile uint32_t *)(RCC_BASE + 0x08UL))
#endif
#ifndef RCC_AHB1ENR
#define RCC_AHB1ENR   (*(volatile uint32_t *)(RCC_BASE + 0x30UL))
#endif
#ifndef RCC_APB2ENR
#define RCC_APB2ENR   (*(volatile uint32_t *)(RCC_BASE + 0x44UL))
#endif

/* ---- DMA 通道选择：权威表是 RM0090 Rev 18 Table 43（DMA2 request mapping） ----
 * USART1_RX → DMA2 Stream5 Channel4（也可走 Stream2 Channel4）。
 * 注意控制器是 DMA2 不是 DMA1：USART1 挂在 APB2 上，它的 DMA 请求归 DMA2 管——
 * 选错控制器，数据永远不会来。本次实施未能取得 Table 43 正文（见研究记录），
 * 取值按广泛使用的映射给出，上板自检步骤见工程 README。 */
#define USART1_RX_STREAM        5U
#define USART1_RX_CHANNEL       4U
#ifndef DMA_S5_CR
#define DMA_S5_CR   (*(volatile uint32_t *)(DMA2_S5_BASE + 0x00UL))
#endif
#ifndef DMA_S5_NDTR
#define DMA_S5_NDTR (*(volatile uint32_t *)(DMA2_S5_BASE + 0x04UL))
#endif
#ifndef DMA_S5_PAR
#define DMA_S5_PAR  (*(volatile uint32_t *)(DMA2_S5_BASE + 0x08UL))
#endif
#ifndef DMA_S5_M0AR
#define DMA_S5_M0AR (*(volatile uint32_t *)(DMA2_S5_BASE + 0x0CUL))
#endif
#ifndef DMA_S5_FCR
#define DMA_S5_FCR  (*(volatile uint32_t *)(DMA2_S5_BASE + 0x14UL))
#endif

/* ---- USART 寄存器（偏移对应该头文件 USART_TypeDef） ---- */
#ifndef USART1_SR
#define USART1_SR    (*(volatile uint32_t *)(USART1_BASE + 0x00UL))
#endif
#ifndef USART1_DR
#define USART1_DR    (*(volatile uint32_t *)(USART1_BASE + 0x04UL))
#endif
#ifndef USART1_BRR
#define USART1_BRR   (*(volatile uint32_t *)(USART1_BASE + 0x08UL))
#endif
#ifndef USART1_CR1
#define USART1_CR1   (*(volatile uint32_t *)(USART1_BASE + 0x0CUL))
#endif
#ifndef USART1_CR3
#define USART1_CR3   (*(volatile uint32_t *)(USART1_BASE + 0x14UL))
#endif
#ifndef USART1_CR2
#define USART1_CR2   (*(volatile uint32_t *)(USART1_BASE + 0x10UL))
#endif

#define USART_SR_RXNE (1UL << 5)
#define USART_SR_TC   (1UL << 6)
#define USART_SR_TXE  (1UL << 7)
#define USART_SR_IDLE (1UL << 4)
#define USART_SR_ORE  (1UL << 3)
#define USART_SR_FE   (1UL << 1)
#define USART_SR_NE   (1UL << 2)

#define USART_CR1_RE  (1UL << 2)
#define USART_CR1_TE  (1UL << 3)
#define USART_CR1_IDLEIE (1UL << 4)
#define USART_CR1_UE  (1UL << 13)
#define USART_CR3_DMAR (1UL << 6)

/* ---- DMA 流配置位（stm32f407xx.h） ---- */
#define DMA_SxCR_EN     (1UL << 0)
#define DMA_SxCR_DMEIE  (1UL << 1)
#define DMA_SxCR_TEIE   (1UL << 2)
#define DMA_SxCR_HTIE   (1UL << 3)
#define DMA_SxCR_TCIE   (1UL << 4)
#define DMA_SxCR_DIR    (0x3UL << 6)   /* 00=外设到内存，位宽 2、起始 bit6 */
#define DMA_SxCR_CIRC   (1UL << 8)
#define DMA_SxCR_MINC   (1UL << 10)
#define DMA_SxCR_PS     (0x7UL << 11)  /* 外设地址宽度 */
#define DMA_SxCR_MSIZE  (0x3UL << 13)
#define DMA_SxCR_DIR_PeripheralToMemory 0UL
#define DMA_SxCR_PS_Byte    (0UL << 11)
#define DMA_SxCR_MSIZE_Byte (0UL << 13)
#define DMA_SxCR_CHSEL  (0x7UL << 25)

/* DMA2_Stream5 的状态位在 HISR 里（stream4..7 走高位寄存器，位号不变）；
 * 清除要写 HIFCR——HISR 是只读状态寄存器，往它写 1 不会清任何标志。 */
#define DMA_HISR_TEIF5  DMA5_TE
#define DMA_HISR_HTIF5  DMA5_HT
#define DMA_HISR_TCIF5  DMA5_TC

#ifndef NVIC_ISER0
#define NVIC_ISER0 (*(volatile uint32_t *)(0xE000E100UL)) /* IRQ 0..31   */
#endif
#ifndef NVIC_ISER1
#define NVIC_ISER1 (*(volatile uint32_t *)(0xE000E104UL)) /* IRQ 32..63  */
#endif
#ifndef NVIC_ISER2
#define NVIC_ISER2 (*(volatile uint32_t *)(0xE000E108UL)) /* IRQ 64..95  */
#endif

#ifndef SysTick_CTRL
#define SysTick_CTRL (*(volatile uint32_t *)(0xE000E010UL))
#endif
#ifndef SysTick_LOAD
#define SysTick_LOAD (*(volatile uint32_t *)(0xE000E014UL))
#endif
#ifndef SysTick_VAL
#define SysTick_VAL  (*(volatile uint32_t *)(0xE000E018UL))
#endif

#define LED_R_PIN 6U
#define LED_B_PIN 8U
#define RX_BUF_LEN 64U
#define BAUD       115200UL

#ifndef HSE_VALUE_HZ
#define HSE_VALUE_HZ 8000000UL /* 本工程默认跑在 HSI；这个宏只在"已切到 PLL 且源是 HSE"时才会用到，
                                 数值错了只会让推导出的时钟偏掉，不会报错——按你板上的晶振填。 */
#endif

/* ============================ 观测量 ============================ */
volatile uint32_t g_rx_bytes;      /* DMA 搬进环形数组的字节总数 */
volatile uint32_t g_frames;        /* IDLE 判出的帧数 */
volatile uint32_t g_overruns;      /* ORE/FE/NE 计数 */
volatile uint32_t g_half_events;   /* 半缓冲中断次数 */
volatile uint32_t g_full_events;   /* 整缓冲中断次数 */
volatile uint32_t g_pclk2;         /* 实际生效的 APB2 时钟 */
volatile uint32_t g_hclk;          /* 实际生效的 HCLK：SysTick 与波特率都以它为准 */
volatile uint32_t g_brr;           /* 实际写进 BRR 的值 */
volatile uint8_t  g_rx_buf[RX_BUF_LEN];

static volatile uint32_t g_ms;
void SysTick_Handler(void) { g_ms++; }



/* ============================ GPIO / 时钟 ============================ */

static void led_init(void)
{
    RCC_AHB1ENR |= (1UL << 5);                       /* GPIOFEN */
    GPIOF_MODER &= ~(3UL << (LED_R_PIN * 2));
    GPIOF_MODER |=  (1UL << (LED_R_PIN * 2));
    GPIOF_MODER &= ~(3UL << (LED_B_PIN * 2));
    GPIOF_MODER |=  (1UL << (LED_B_PIN * 2));
}

static void led_set(uint32_t pin, uint32_t on)
{
    GPIOF_BSRR = on ? (1UL << (pin + 16)) : (1UL << pin);
}

static void usart1_pins(void)
{
    RCC_AHB1ENR |= (1UL << 0);                       /* GPIOAEN  */
    RCC_APB2ENR |= (1UL << 4);                       /* USART1EN */

    GPIOA_MODER &= ~(3UL << (9 * 2));
    GPIOA_MODER |=  (2UL << (9 * 2));                /* PA9  复用 */
    GPIOA_AFRH  &= ~(0xFUL << ((9 - 8) * 4));
    GPIOA_AFRH  |=  (7UL << ((9 - 8) * 4));          /* AF7 = USART1_TX */

    GPIOA_MODER &= ~(3UL << (10 * 2));
    GPIOA_MODER |=  (2UL << (10 * 2));               /* PA10 复用 */
    GPIOA_AFRH  &= ~(0xFUL << ((10 - 8) * 4));
    GPIOA_AFRH  |=  (7UL << ((10 - 8) * 4));         /* AF7 = USART1_RX */
}

/** 从 CFGR 回读 HCLK 与 PCLK2。波特率与毫秒基准都必须跟着真实时钟走。 */
static void clocks_read(uint32_t hsi_hz, volatile uint32_t *hclk, volatile uint32_t *pclk2)
{
    /* RM0090 Rev 18：HPRE 0xxx=/1、1000=/2、1001=/4、1010=/8、1011=/16、
     * 1100=/64、1101=/128、1110=/256、1111=/512（F4 没有 /32 这一档） */
    static const uint16_t hpre_div[]  = { 1,1,1,1,1,1,1,1,2,4,8,16,64,128,256,512 };
    /* PPRE2：0xx=/1、100=/2、101=/4、110=/8、111=/16 */
    static const uint16_t ppre_div[]  = { 1,1,1,1,2,4,8,16 };

    uint32_t cfgr = RCC_CFGR;
    uint32_t src  = hsi_hz;

    if (((cfgr >> 2) & 0x3UL) == 0x2UL) {
        uint32_t pll = RCC_PLLCFGR;
        uint32_t m =  pll & 0x3FUL;
        uint32_t n = (pll >> 6) & 0x1FFUL;
        uint32_t p = 2UL * (((pll >> 16) & 0x3UL) + 1UL);
        uint32_t hse = (pll & (1UL << 22)) ? HSE_VALUE_HZ : hsi_hz;
        src = m ? (uint32_t)(((uint64_t)hse * n) / (m * p)) : 0;
    }
    if (((cfgr >> 2) & 3U) == 1U) src = HSE_VALUE_HZ;
    *hclk  = src / hpre_div[(cfgr >> 4) & 0xFUL];
    *pclk2 = *hclk / ppre_div[(cfgr >> 13) & 0x7UL];
}

/* ============================ USART ============================ */

/** 阻塞发送。注意最后等的是 TC 不是 TXE：
 *  TXE = 数据寄存器空了，可以塞下一个字节；
 *  TC  = 移位寄存器里的停止位已经跑完，此时才敢切方向/断电。 */
static void uart_write_blocking(const char *s)
{
    for (; *s != '\0'; s++) {
        while ((USART1_SR & USART_SR_TXE) == 0UL) { }
        USART1_DR = (uint32_t)(uint8_t)*s;
    }
    while ((USART1_SR & USART_SR_TC) == 0UL) { }
}

/* 波特率与 BRR 的互算：OVER8=0（16 倍过采样）时 baud = PCLK / BRR，
 * 于是 BRR = round(PCLK/baud)——四舍五入靠 +baud/2 这一次加法，不是靠浮点。
 * 写成宏而不是函数，是为了让 -O0 与 -O2 下的机身形状由调用点决定；
 * probe.sh 打的那张误差表也走这两个宏，不与固件各算一套。 */
#ifndef BAUD_FROM_PCLK
#define BAUD_FROM_PCLK(pclk, baud) ((uint32_t)(((pclk) + ((baud) / 2U)) / (baud)))
#endif
#ifndef PCLK_OF_BRR
#define PCLK_OF_BRR(pclk, brr)     ((uint32_t)((pclk) / (brr)))
#endif

/* dmb 是 ARM 指令，宿主机（probe.c 那一遍）编不过：那边只留编译器栅栏，
 * 内存栅栏的真实形状由 probe.sh 第 3 步的交叉反汇编给出。 */
#if defined(__arm__)
#define MCU_DMB()         __asm__ volatile("dmb" ::: "memory")
#else
#define MCU_DMB()         __asm__ volatile("" ::: "memory")
#endif

static void usart1_init(uint32_t pclk2)
{
    USART1_CR1 = 0;
    USART1_CR2 = 0;
    USART1_CR3 = 0;

    /* OVER8 默认 0 = 16 倍过采样，于是 baud = PCLK2 / BRR */
    uint32_t brr = BAUD_FROM_PCLK(pclk2, BAUD);
    USART1_BRR = brr;
    g_brr = brr;

    USART1_CR1 = USART_CR1_UE | USART_CR1_TE | USART_CR1_RE | USART_CR1_IDLEIE;
}

static void dma2_stream5_rx_init(void)
{
    /* 先开 DMA2 时钟（RCC_AHB1ENR bit22）——不开时钟，流配置写了也白写 */
    RCC_AHB1ENR |= (1UL << 22);

    /* 配置前先关流：CHSEL/DIR/CIRC 这些位只有在 EN=0 时才能改 */
    DMA_S5_CR = 0;
    while (DMA_S5_CR & DMA_SxCR_EN) { }

    DMA_S5_PAR  = USART1_BASE + 0x04UL;     /* DR：串口数据寄存器 */
    DMA_S5_M0AR = (uint32_t)(uintptr_t)g_rx_buf;
    DMA_S5_NDTR = RX_BUF_LEN;               /* 环形模式跑到 0 会自动回装成原值 */
    DMA_S5_FCR  = 0;                        /* 直接模式，不走 FIFO */

    DMA_S5_CR = DMA_SxCR_DIR_PeripheralToMemory
              | DMA_SxCR_CIRC | DMA_SxCR_MINC
              | DMA_SxCR_HTIE | DMA_SxCR_TCIE | (1UL << 2)
              | DMA_SxCR_PS_Byte | DMA_SxCR_MSIZE_Byte
              | ((USART1_RX_CHANNEL & 0x7UL) << 25);

    USART1_CR3 |= USART_CR3_DMAR;           /* 告诉 USART：RXNE 由 DMA 来取 */
    DMA_S5_CR |= DMA_SxCR_EN;
}


/* ISR producer / main consumer. Both IRQs use the same preemption priority. */
static dma_cursor_t rx_cursor;
static volatile uint8_t tx_queue[1024];
static volatile uint32_t tx_head, tx_tail;
static void consume_rx(void)
{
    uint32_t flags=DMA2_HISR;
    uint32_t pos=(RX_BUF_LEN-DMA_S5_NDTR)%RX_BUF_LEN;
    flags |= DMA2_HISR; /* Include a boundary crossed while sampling NDTR. */
    unsigned events=((flags&DMA_HISR_HTIF5)?1U:0U)|((flags&DMA_HISR_TCIF5)?2U:0U)|((flags&DMA_HISR_TEIF5)?4U:0U);
    DMA2_HIFCR=flags&(DMA_HISR_HTIF5|DMA_HISR_TCIF5|DMA_HISR_TEIF5);
    dma_span_t span=dma_consume(&rx_cursor,pos,RX_BUF_LEN,events);
    if(flags&DMA_HISR_HTIF5) ++g_half_events;
    if(flags&DMA_HISR_TCIF5) ++g_full_events;
    if(span.dropped) { ++g_overruns; return; }
    for(uint32_t i=0;i<span.count;i++) {
        if(tx_head-tx_tail>=sizeof(tx_queue)) { ++g_overruns; break; }
        tx_queue[tx_head%sizeof(tx_queue)]=g_rx_buf[(span.start+i)%RX_BUF_LEN];
        MCU_DMB();
        ++tx_head; ++g_rx_bytes;
    }
}
void USART1_IRQHandler(void)
{
    uint32_t sr=USART1_SR;
    if(sr&(USART_SR_ORE|USART_SR_FE|USART_SR_NE|USART_SR_IDLE)) {
        (void)USART1_DR; /* SR then DR acknowledges flags; IDLE is not a protocol boundary. */
        if(sr&(USART_SR_ORE|USART_SR_FE|USART_SR_NE)) ++g_overruns;
        if(sr&USART_SR_IDLE) ++g_frames; /* historical name: counts IDLE notifications only */
        consume_rx();
    }
}
void DMA2_Stream5_IRQHandler(void) { consume_rx(); }

/* ============================ main ============================ */

#ifndef MCU_PROBE_NO_MAIN   /* 无板取证（probe.c）把 main.c 整个 #include 进去，
                               这一遍只要固件本体，不要那个 while(1)。 */
int main(void)
{
    led_init();
    usart1_pins();

    clocks_read(16000000UL, &g_hclk, &g_pclk2);

    SysTick_CTRL = 0;
    /* SysTick 挂在内核时钟上，是 HCLK 而不是 PCLK2：
     * 用 g_pclk2 在 HSI 下恰好同值，一旦切到 PLL（APB2=84MHz）就会让毫秒基准错 5.25 倍。 */
    SysTick_LOAD = g_hclk / 1000UL - 1UL;
    SysTick_VAL  = 0;
    SysTick_CTRL = 0x7UL;

    usart1_init(g_pclk2);
    dma2_stream5_rx_init();

    ((volatile uint8_t *)0xe000e400UL)[37]=0x60;
    ((volatile uint8_t *)0xe000e400UL)[68]=0x60;
    NVIC_ISER1 |= (1UL << (37 - 32));    /* USART1_IRQn       */
    NVIC_ISER2 |= (1UL << (68 - 64));    /* DMA2_Stream5_IRQn */

    uart_write_blocking("uart-dma ready\r\n");

    /* No sleeping while responsible for draining the transmit queue. */
    while (1) {
        if(!(DMA_S5_CR&DMA_SxCR_EN)) {
            uint32_t mask;
            __asm__ volatile("mrs %0, primask\ncpsid i":"=r"(mask)::"memory");
            ++g_overruns; rx_cursor.read=0;
            DMA2_HIFCR=DMA_HISR_HTIF5|DMA_HISR_TCIF5|DMA_HISR_TEIF5;
            dma2_stream5_rx_init();
            __asm__ volatile("msr primask, %0"::"r"(mask):"memory");
        }
        if(tx_tail!=tx_head && (USART1_SR&USART_SR_TXE)) {
            MCU_DMB();
            USART1_DR=tx_queue[tx_tail%sizeof(tx_queue)];
            MCU_DMB();
            ++tx_tail;
        }
        led_set(LED_R_PIN,(g_ms/500U)&1U);
        led_set(LED_B_PIN,g_overruns==0 && g_rx_bytes!=0);
    }
}
#endif
