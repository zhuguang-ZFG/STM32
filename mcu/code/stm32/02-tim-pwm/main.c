/*
 * S6: TIM3_CH1 PA6/AF2 outputs PWM; independent TIM2_CH1 PA0/AF1 captures.
 * Connect PA6 -> PA0 (old PA7 wiring no longer applies).
 * Sources: DS8626 alternate function table, RM0090 TIM2..5 chapters,
 * ST CMSIS stm32f407xx.h (TIM2_IRQn=28, APB1 enable bits TIM2=0 TIM3=1).
 * Hardware measurements pending; host tests verify the shared counter logic.
 */
#include <stdint.h>
#include "../../common/behavior/capture.h"
#define R(b,o) (*(volatile uint32_t *)((b)+(o)))
#define RCC 0x40023800UL
#define GPIOA 0x40020000UL
#define GPIOF 0x40021400UL
#define TIM2 0x40000000UL
#define TIM3 0x40000400UL
#ifndef HSE_VALUE_HZ
#define HSE_VALUE_HZ 8000000UL
#endif
#define PWM_PERIOD_TICKS 999U
#define COUNT_HZ 1000000UL
volatile uint32_t g_hclk, g_pclk1_before, g_pclk1_after;
volatile uint32_t g_tim_clk_before, g_tim_clk_after, g_pwm_hz;
volatile uint32_t g_measured_hz, g_capture_edges, g_overcapture;
static capture_t capture;
static volatile uint32_t g_ms;
void SysTick_Handler(void) { ++g_ms; }
static void delay_ms(uint32_t delay) { uint32_t start=g_ms; while(g_ms-start<delay){} }
static uint32_t lock(void) {
    uint32_t mask; __asm__ volatile("mrs %0, primask\ncpsid i":"=r"(mask)::"memory"); return mask;
}
static void unlock(uint32_t mask) { __asm__ volatile("msr primask, %0"::"r"(mask):"memory"); }
static uint32_t system_clock(void) {
    static const uint16_t ahb[16]={1,1,1,1,1,1,1,1,2,4,8,16,64,128,256,512};
    uint32_t cfgr=R(RCC,8UL), source=16000000UL, sws=(cfgr>>2)&3U;
    if(sws==1) source=HSE_VALUE_HZ;
    if(sws==2) {
        uint32_t pll=R(RCC,4UL), m=pll&63U, n=(pll>>6)&511U, p=2U*(((pll>>16)&3U)+1U);
        if(!m) return 0;
        source=(uint32_t)(((uint64_t)((pll&(1UL<<22))?HSE_VALUE_HZ:16000000UL)*n)/(m*p));
    }
    return source/ahb[(cfgr>>4)&15U];
}
static uint32_t timer_clock(void) {
    uint32_t div=apb_div((R(RCC,8UL)>>10)&7U);
    return g_hclk/div*(div==1?1U:2U);
}
static void pin_af(unsigned pin,unsigned af) {
    R(GPIOA,0UL)=(R(GPIOA,0UL)&~(3UL<<(2*pin)))|(2UL<<(2*pin));
    R(GPIOA,0x20UL)=(R(GPIOA,0x20UL)&~(15UL<<(4*pin)))|((uint32_t)af<<(4*pin));
}
void TIM2_IRQHandler(void) {
    uint32_t sr=R(TIM2,0x10UL);
    if(sr&(1UL<<1)) {
        uint32_t stamp=R(TIM2,0x34UL); /* SR then CCR1 clears CC1IF. */
        bool lost=((sr|R(TIM2,0x10UL))&(1UL<<9))!=0;
        if(lost) R(TIM2,0x10UL)=~(1UL<<9); /* rc_w0: only clear overcapture. */
        capture_edge(&capture,stamp,lost);
        ++g_capture_edges;
    }
}
int main(void) {
    R(RCC,0x30UL)|=(1UL<<0)|(1UL<<5);
    R(RCC,0x40UL)|=3UL; (void)R(RCC,0x40UL);
    pin_af(6,2); pin_af(0,1);
    R(GPIOF,0UL)=(R(GPIOF,0UL)&~((3UL<<12)|(3UL<<16)))|(1UL<<12)|(1UL<<16);
    g_hclk=system_clock();
    g_pclk1_before=g_hclk/apb_div((R(RCC,8UL)>>10)&7U);
    g_tim_clk_before=timer_clock();
    uint32_t cfgr=R(RCC,8UL);
    R(RCC,8UL)=(cfgr&~(7UL<<10))|(4UL<<10);
    g_pclk1_after=g_hclk/2U; g_tim_clk_after=timer_clock();
    R(RCC,8UL)=cfgr;
    uint32_t clock=timer_clock();
    if(!g_hclk || clock%COUNT_HZ) for(;;){}
    R(0xe000e010UL,4UL)=g_hclk/1000U-1U;
    R(0xe000e010UL,8UL)=0; R(0xe000e010UL,0UL)=7;
    R(TIM3,0x28UL)=clock/COUNT_HZ-1U; R(TIM3,0x2cUL)=PWM_PERIOD_TICKS;
    R(TIM3,0x18UL)=(6UL<<4)|(1UL<<3); R(TIM3,0x34UL)=500;
    R(TIM3,0x20UL)=1; R(TIM3,0x14UL)=1; R(TIM3,0x10UL)=0; R(TIM3,0UL)=0x81;
    R(TIM2,0x28UL)=clock/COUNT_HZ-1U; R(TIM2,0x2cUL)=UINT32_MAX;
    R(TIM2,0x18UL)=1UL|(2UL<<4); R(TIM2,0x20UL)=1;
    R(TIM2,0x14UL)=1; R(TIM2,0x10UL)=0; R(TIM2,0x0cUL)=2;
    R(0xe000e100UL,0UL)=1UL<<28; R(TIM2,0UL)=1;
    g_pwm_hz=COUNT_HZ/(PWM_PERIOD_TICKS+1U);
    unsigned phase=0;
    for(;;) {
        phase=(phase+1U)%200U;
        uint32_t ccr=(phase<100U?phase+1U:200U-phase)*(PWM_PERIOD_TICKS+1U)/100U;
        R(TIM3,0x34UL)=ccr;
        uint32_t mask=lock();
        capture_expire(&capture,R(TIM2,0x24UL));
        g_measured_hz=capture.frequency; g_overcapture=capture.lost;
        unlock(mask);
        R(GPIOF,0x18UL)=(g_measured_hz>900&&g_measured_hz<1100)?1UL<<24:1UL<<8;
        R(GPIOF,0x18UL)=((g_ms/500U)&1U)?1UL<<22:1UL<<6;
        delay_ms(20);
    }
}
