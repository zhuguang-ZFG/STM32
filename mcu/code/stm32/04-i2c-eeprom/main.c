/*
 * STM32F407 / I2C1：AT24C02 单字节写入、ACK polling、重复 START 读回。
 * 地址/位：ST CMSIS stm32f407xx.h；流程：RM0090 I2C master receiver，
 * ST stm32f4xx_hal_i2c.c HAL_I2C_Mem_Read 的 XferSize==1 分支。
 * PB6/PB7 AF4 来自 DS8626 引脚复用表；这是外接模块接线，不假设板载 EEPROM。
 * 固定复位 HSI=16MHz、APB1=16MHz。写 0x10=0x5a（每次复位仅一次）。
 * USB-TTL RX 接 PA9，115200 8N1；待上板实测。
 */
#include <stdint.h>
#include <stdbool.h>

#define REG(base, off) (*(volatile uint32_t *)((base) + (off)))
#define RCC 0x40023800UL
#define GPIOA 0x40020000UL
#define GPIOB 0x40020400UL
#define I2C1 0x40005400UL
#define USART1 0x40011000UL
#define CR1 REG(I2C1, 0x00UL)
#define SR1 REG(I2C1, 0x14UL)
#define SR2 REG(I2C1, 0x18UL)
#define DR REG(I2C1, 0x10UL)
#define START (1UL << 8)
#define STOP (1UL << 9)
#define ACK (1UL << 10)
#define AF (1UL << 10)
#define ERRORS ((1UL << 8) | (1UL << 9) | AF | (1UL << 11))
#define ADDRESS 0x50U
static volatile uint32_t ms;
static const char *failure;

void SysTick_Handler(void) { ++ms; }
static void delay_ms(uint32_t duration)
{
    const uint32_t begin = ms;
    while ((uint32_t)(ms - begin) < duration) { __asm__ volatile ("nop"); }
}
static void log_text(const char *s)
{
    while (*s) {
        const uint32_t begin = ms;
        while (!(REG(USART1, 0x00UL) & (1UL << 7))) {
            if ((uint32_t)(ms - begin) > 20U) return;
        }
        REG(USART1, 0x04UL) = (uint8_t)*s++;
    }
}
static void log_hex(uint8_t value)
{
    const char digits[] = "0123456789ABCDEF";
    char s[] = {digits[value >> 4], digits[value & 15U], '\0'};
    log_text(s);
}
static bool wait_sr1(uint32_t flag, const char *stage)
{
    const uint32_t begin = ms;
    for (;;) {
        uint32_t status = SR1;
        if (status & ERRORS) { failure = stage; return false; }
        if (status & flag) return true;
        if ((uint32_t)(ms - begin) > 20U) { failure = stage; return false; }
    }
}
static bool bus_idle(void)
{
    const uint32_t begin = ms;
    while (SR2 & (1UL << 1)) {
        if ((uint32_t)(ms - begin) > 20U) { failure = "BUSY (check pullups/wiring)"; return false; }
    }
    return true;
}
static void clear_addr(void) { (void)SR1; (void)SR2; }
static bool address(bool read)
{
    CR1 |= START;
    if (!wait_sr1(1UL, "START/SB")) return false;
    DR = (ADDRESS << 1) | (read ? 1U : 0U);
    return wait_sr1(1UL << 1, "address/ACK"); /* ADDR 留给调用者清除。 */
}
static bool send(uint8_t value)
{
    if (!wait_sr1(1UL << 7, "TXE")) return false;
    DR = value;
    return wait_sr1(1UL << 2, "BTF"); /* 包含从机 ACK，不能只等 TXE。 */
}
static void abort_transfer(void)
{
    /* 单主机实验。ARLO 时已失去主机身份，不生成 STOP 干扰其它主机。 */
    if (!(SR1 & (1UL << 9))) CR1 |= STOP;
    SR1 &= ~ERRORS;
    CR1 |= ACK;
}
static bool write_byte(uint8_t offset, uint8_t value)
{
    if (!bus_idle() || !address(false)) return false;
    clear_addr();
    if (!send(offset) || !send(value)) return false;
    CR1 |= STOP;
    return true;
}
static bool ready(void)
{
    /* AT24C02 写周期内地址 NACK 是预期状态；最多尝试 20 次。 */
    for (unsigned i = 0; i < 20U; ++i) {
        if (!bus_idle()) return false;
        if (address(false)) { clear_addr(); CR1 |= STOP; return true; }
        bool nack = (SR1 & AF) && !(SR1 & (ERRORS & ~AF));
        abort_transfer();
        if (!nack) return false;
        delay_ms(1);
    }
    failure = "EEPROM write cycle ACK polling timeout";
    return false;
}
static bool read_byte(uint8_t offset, uint8_t *value)
{
    if (!bus_idle() || !address(false)) return false;
    clear_addr();
    if (!send(offset) || !address(true)) return false; /* 中间没有 STOP。 */
    /* 单字节读：先关闭 ACK，再读 SR1/SR2 清 ADDR，立即 STOP，最后读 DR。
     * 短临界区防止 SysTick 将清 ADDR 与 STOP 拉开；不在关中断状态轮询。 */
    uint32_t primask;
    __asm__ volatile ("mrs %0, primask\ncpsid i" : "=r"(primask) :: "memory");
    CR1 &= ~(ACK | (1UL << 11)); /* POS=0 */
    clear_addr();
    CR1 |= STOP;
    __asm__ volatile ("msr primask, %0" :: "r"(primask) : "memory");
    if (!wait_sr1(1UL << 6, "RXNE")) return false;
    *value = (uint8_t)DR;
    CR1 |= ACK;
    return bus_idle();
}
int main(void)
{
    /* SysTick 1ms，复位后 HSI16；无外部晶振依赖。 */
    REG(0xe000e010UL, 0x04UL) = 16000U - 1U;
    REG(0xe000e010UL, 0x08UL) = 0;
    REG(0xe000e010UL, 0x00UL) = 7U;
    REG(RCC, 0x30UL) |= (1UL << 0) | (1UL << 1);
    REG(RCC, 0x40UL) |= 1UL << 21; /* I2C1 */
    REG(RCC, 0x44UL) |= 1UL << 4;  /* USART1 */
    (void)REG(RCC, 0x44UL);        /* 外设时钟同步 */
    REG(GPIOA, 0x00UL) = (REG(GPIOA, 0x00UL) & ~(3UL << 18)) | (2UL << 18);
    REG(GPIOA, 0x24UL) = (REG(GPIOA, 0x24UL) & ~(15UL << 4)) | (7UL << 4);
    REG(USART1, 0x08UL) = 139U;    /* 16MHz/115200，四舍五入 */
    REG(USART1, 0x0cUL) = (1UL << 13) | (1UL << 3);
    REG(GPIOB, 0x00UL) = (REG(GPIOB, 0x00UL) & ~((3UL << 12) | (3UL << 14))) | (2UL << 12) | (2UL << 14);
    REG(GPIOB, 0x04UL) |= (1UL << 6) | (1UL << 7); /* 开漏；外接 4.7k 上拉至 3.3V */
    REG(GPIOB, 0x08UL) |= (3UL << 12) | (3UL << 14);
    REG(GPIOB, 0x20UL) = (REG(GPIOB, 0x20UL) & ~((15UL << 24) | (15UL << 28))) | (4UL << 24) | (4UL << 28);
    CR1 = 1UL << 15; CR1 = 0;     /* SWRST */
    REG(I2C1, 0x04UL) = 16U;      /* CR2 FREQ=APB1 MHz */
    REG(I2C1, 0x1cUL) = 80U;      /* 标准模式：16MHz/(2*100kHz) */
    REG(I2C1, 0x20UL) = 17U;      /* TRISE=16+1 */
    CR1 = ACK | 1U;
    delay_ms(20);
    log_text("E05: write EEPROM[0x10]=0x5A\r\n");
    uint8_t value = 0;
    bool ok = write_byte(0x10, 0x5a) && ready() && read_byte(0x10, &value);
    if (ok) { log_text("read=0x"); log_hex(value); log_text(value == 0x5a ? " PASS\r\n" : " MISMATCH\r\n"); }
    else { abort_transfer(); log_text("FAIL at "); log_text(failure ? failure : "unknown"); log_text("\r\n"); }
    for (;;) { __asm__ volatile ("wfi"); } /* 不反复擦写 EEPROM。 */
}
