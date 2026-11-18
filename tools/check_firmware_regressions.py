#!/usr/bin/env python3
"""Execute current production C functions with explicit MMIO/HAL test doubles.

No firmware headers are fabricated: only selected function bodies and their real
preamble/globals are compiled. This is NOT a full target build or hardware test.
Generated translation units, executables and per-case logs require --out.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CASES = ['mco', 'clock-order', 'clock-readback', 'clock-hse', 'clock-pll-stop',
         'clock-pll-lock', 'clock-switch', 'clock-hse-readback', 'clock-flash', 'f407-toggle', 'f103-key',
         'uart-ht', 'uart-rearm', 'uart-error']


def function(text, name):
    pattern = rf'^(?:static\s+)?(?:void|int|uint32_t)\s+{re.escape(name)}\s*\([^;]*?\)\s*\{{'
    match = re.search(pattern, text, re.M)
    if not match:
        raise ValueError(f'Production function definition missing: {name}')
    start = match.end() - 1
    # Ignore braces inside comments and strings when locating the real body.
    token = re.compile(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|[{}]', re.S)
    depth = 0
    for item in token.finditer(text, start):
        if item.group() == '{':
            depth += 1
        elif item.group() == '}':
            depth -= 1
            if depth == 0:
                return text[match.start():item.end()]
    raise ValueError(f'Unbalanced production function: {name}')


HEADER = r'''
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x, message) do { if (!(x)) { fprintf(stderr,"FAIL: %s (line %d)\n",message,__LINE__); exit(1); } } while (0)
'''
MMIO = r'''
struct slot { uintptr_t address; uint32_t value; };
static struct slot slots[80]; static unsigned nslots, accesses;
static int auto_clock, enforce_safe, fault;
static volatile uint32_t *raw(uintptr_t address) {
    for(unsigned i=0;i<nslots;i++) if(slots[i].address==address) return &slots[i].value;
    CHECK(nslots<80,"MMIO fixture capacity"); slots[nslots].address=address;
    return &slots[nslots++].value;
}
static void step(void) {
    CHECK(++accesses<6000000,"register polling exceeded bounded wait budget");
    uint32_t bs=*raw(0x40021418); if(bs) {
        uint32_t odr=*raw(0x40021414);
        *raw(0x40021414)=(odr|(bs&0xffffU))&~(bs>>16);
        *raw(0x40021418)=0; /* BSRR reads never provide the ODR state. */
    }
    if(!auto_clock) return;
    uint32_t cr=*raw(0x40023800), cf=*raw(0x40023808);
    if(fault==5) *raw(0x40023c00)&=~7U; /* Flash latency write rejected. */
    if((cr&(1U<<16)) && fault!=1) cr|=1U<<17; else cr&=~(1U<<17);
    if(fault==2) cr|=1U<<25;
    else if((cr&(1U<<24)) && fault!=3) cr|=1U<<25;
    else cr&=~(1U<<25);
    *raw(0x40023800)=cr;
    if((cf&3U)==2U) {
        if(enforce_safe) {
            CHECK(((cf>>10)&7U)==5 && ((cf>>13)&7U)==4,"APB divisors must be safe BEFORE requesting PLL SYSCLK");
            CHECK((*raw(0x40023840)&(1U<<28))!=0,"PWR clock must be enabled before PLL switch");
            CHECK((*raw(0x40007000)&(1U<<14))!=0,"Scale1 required before PLL switch");
            CHECK((*raw(0x40023c00)&7U)>=5,"Flash latency must be prepared before PLL switch");
        }
        if(fault!=4) *raw(0x40023808)=(cf&~12U)|8U;
    }
}
static volatile uint32_t *reg(uintptr_t address) { step(); return raw(address); }
static void reset_model(void) {
    memset(slots,0,sizeof slots);nslots=accesses=0;auto_clock=enforce_safe=fault=0;
    *raw(0x40023800)=3; *raw(0x40021414)=1U<<6;
}
'''
CLOCK_MAIN = r'''
int main(int argc,char **argv) {
    CHECK(argc==2,"one case required"); reset_model();const char *c=argv[1];
    if(strcmp(c,"mco")==0) {
        *raw(0x40020000)=0xa5a5a5a5U;*raw(0x40020024)=0xffffffffU;
        *raw(0x40020004)=0xffffffffU;*raw(0x4002000c)=0xffffffffU;
        mco1_init(16000000U);step();
        CHECK(((*raw(0x40020000)>>16)&3U)==2,"MCO PA8 must use alternate-function MODER=10");
        CHECK((*raw(0x40020024)&15U)==0,"MCO PA8 AF0 required");
        CHECK((*raw(0x40020004)&(1U<<8))==0,"MCO requires push-pull");
        CHECK(((*raw(0x4002000c)>>16)&3U)==0,"MCO requires no pull");
        CHECK(((*raw(0x40020008)>>16)&3U)==3,"MCO uses official very-high speed setting");
        CHECK(((*raw(0x40023808)>>21)&3U)==0,"HSI MCO source required");
        CHECK(((*raw(0x40023808)>>24)&7U)==0,"HSI16 uses /1, not /4");
        CHECK((*raw(0x40020000)&~(3U<<16))==(0xa5a5a5a5U&~(3U<<16)),"other pins preserved");
        *raw(0x40023808)=8U|2U|(5U<<10)|(4U<<13);
        mco1_init(168000000U);step();
        CHECK(((*raw(0x40023808)>>21)&3U)==3,"PLL MCO source must be explicitly selected");
        CHECK(((*raw(0x40023808)>>24)&7U)==6,"PLL168 must use /4 encoding 110");
        CHECK((*raw(0x40023808)&0x0000fc0fU)==(8U|2U|(5U<<10)|(4U<<13)),"MCO preserves clock source/divisors");
    } else if(strcmp(c,"clock-hse-readback")==0) {
        *raw(0x40023808)=4U; clock_tree_readback(16000000U);
        CHECK(g_clock_tree[0]==HSE_VALUE_HZ,"SWS=HSE must not be reported as HSI");
    } else if(strcmp(c,"clock-readback")==0) {
        for(unsigned p=0;p<4;p++) for(unsigned apb=0;apb<8;apb++) {
            const uint32_t d[]={1,1,1,1,2,4,8,16};
            *raw(0x40023808)=8U|2U|(apb<<10);*raw(0x40023804)=8U|(336U<<6)|(p<<16)|(1U<<22)|(7U<<24);
            clock_tree_readback(16000000U);uint32_t sys=336000000U/((p+1U)*2U);
            CHECK(g_clock_tree[0]==sys,"all four PLLP field encodings must decode correctly");
            CHECK(g_clock_tree[4]==sys/d[apb]*(d[apb]==1?1U:2U),"PPRE 0xx means /1, not timer x2");
        }
    } else {
        auto_clock=1;enforce_safe=1;
        if(strcmp(c,"clock-hse")==0) fault=1;
        if(strcmp(c,"clock-pll-stop")==0) fault=2;
        if(strcmp(c,"clock-pll-lock")==0) fault=3;
        if(strcmp(c,"clock-switch")==0) fault=4;
        if(strcmp(c,"clock-flash")==0) fault=5;
        int result=clock_init();step();
        if(fault) { CHECK(result!=0 && g_clock_status!=0,"injected failure must not report success"); }
        else { CHECK(result==0,"PLL initialization succeeds in ready fixture"); CHECK(g_clock_tree[1]==168000000U && g_clock_tree[2]==42000000U && g_clock_tree[3]==84000000U,"final clock readback"); }
    }
    printf("PASS %s: actual production C with MMIO fixture; not hardware\n",c);return 0;
}
'''
F407_MAIN = r'''
int main(void) { reset_model();for(unsigned start=0;start<2;start++) {
 *raw(0x40021414)=0xa500U|(start?64U:0U);
 for(unsigned i=0;i<4;i++) {uint32_t before=*raw(0x40021414);EXTI0_IRQHandler();step();CHECK(*raw(0x40021414)==(before^64U),"each ISR must toggle ODR using one BSRR write, even when BSRR reads zero");}
}puts("PASS f407-toggle: actual ISR, no hardware");return 0; }
'''
HAL = r'''
#define GPIOA ((void*)1)
#define GPIOC ((void*)3)
#define USART1 ((void*)5)
#define GPIO_PIN_0 1U
#define GPIO_PIN_9 (1U<<9)
#define GPIO_PIN_10 (1U<<10)
#define GPIO_PIN_13 (1U<<13)
#define GPIO_PIN_RESET 0
#define GPIO_PIN_SET 1
#define HAL_OK 0
#define HAL_ERROR 1
#define HAL_BUSY 2
#define HAL_UART_RXEVENT_TC 0
#define HAL_UART_RXEVENT_HT 1
#define HAL_UART_RXEVENT_IDLE 2
#define HAL_UART_ERROR_ORE 8U
#define HAL_UART_ERROR_FE 4U
#define __HAL_UART_CLEAR_OREFLAG(x) ((void)(x))
#define __HAL_UART_CLEAR_FEFLAG(x) ((void)(x))
typedef struct {void *Instance;uint32_t ErrorCode;} UART_HandleTypeDef;
typedef struct {int unused;} DMA_HandleTypeDef;
static unsigned led,forced_writes,toggles,starts,stops,event_type;
static int restart_result;
static void __disable_irq(void) {} static void __enable_irq(void) {}
static void HAL_Delay(unsigned ms) {(void)ms;}
static int HAL_GPIO_ReadPin(void *port,unsigned pin) {(void)port;(void)pin;return GPIO_PIN_RESET;}
static void HAL_GPIO_TogglePin(void *port,unsigned pin) {(void)port;(void)pin;led^=1U;toggles++;}
static void HAL_GPIO_WritePin(void *port,unsigned pin,int state) {(void)port;(void)pin;led=(unsigned)state;forced_writes++;}
static unsigned HAL_UARTEx_GetRxEventType(UART_HandleTypeDef *h) {(void)h;return event_type;}
static int HAL_UARTEx_ReceiveToIdle_DMA(UART_HandleTypeDef *h,uint8_t *b,uint16_t len) {(void)h;(void)b;(void)len;starts++;return restart_result;}
static void error_handler(void) {stops++;} /* terminal stop made observable, not silently ignored */
'''
KEY_MAIN = r'''
int main(void) {led=1;for(unsigned i=1;i<=4;i++) {HAL_GPIO_EXTI_Callback(KEY_PIN);key_process();CHECK(led==(1U^(i&1U)),"even raw IRQ count must not override valid-event toggle");}CHECK(toggles==4 && forced_writes==0,"one toggle and no debug forced write per accepted event");puts("PASS f103-key: actual callbacks with HAL boundary doubles; not full firmware");return 0;}
'''
UART_MAIN = r'''
int main(int argc,char **argv) {
 CHECK(argc==2,"one case required");huart1.Instance=USART1;for(unsigned i=0;i<DMA_RX_BUF_SIZE;i++)g_dma_rx_buf[i]=(uint8_t)i;
 if(strcmp(argv[1],"uart-ht")==0) {
  event_type=HAL_UART_RXEVENT_HT;restart_result=HAL_BUSY;HAL_UARTEx_RxEventCallback(&huart1,32);
  CHECK(g_rb.head==0 && starts==0,"NORMAL HT must neither copy prefix nor restart active DMA");
  event_type=HAL_UART_RXEVENT_IDLE;restart_result=HAL_OK;HAL_UARTEx_RxEventCallback(&huart1,40);
  CHECK(g_rb.head==40 && starts==1,"HT32 then IDLE40 must enqueue 40, not 72");
  for(unsigned i=0;i<40;i++)CHECK(g_rb.buf[i]==i,"received bytes exactly once");
  event_type=HAL_UART_RXEVENT_TC;HAL_UARTEx_RxEventCallback(&huart1,64);
  CHECK(g_rb.head==104 && starts==2,"next completed transfer copied exactly once");
 } else if(strcmp(argv[1],"uart-rearm")==0) {
  event_type=HAL_UART_RXEVENT_IDLE;restart_result=HAL_ERROR;HAL_UARTEx_RxEventCallback(&huart1,4);
  CHECK(starts==1 && stops==1,"terminal receive rearm failure must enter existing error handler");
 } else {
  restart_result=HAL_BUSY;huart1.ErrorCode=HAL_UART_ERROR_ORE;HAL_UART_ErrorCallback(&huart1);
  CHECK(starts==1 && stops==1,"error callback must not ignore failed rearm");
 }
 printf("PASS %s: actual production callbacks with HAL boundary doubles; not full firmware\n",argv[1]);return 0;
}
'''


def source_group(group):
    if group == 'clock':
        path = ROOT/'mcu/code/stm32/01-rcc-clock/main.c'
        names = ['mco1_pre_for','mco1_init','flash_latency_ws_3v3','flash_config',
                 'pll_params_from_hse','clock_tree_readback','clock_init']
        text = path.read_text(encoding='utf-8')
        preamble = text[:text.index('static void systick_init')]
        code = preamble+'\n'+'\n'.join(function(text,n) for n in names)
        code = re.sub(r'\*\(volatile uint32_t \*\)\(([^()]*)\)',r'*reg(\1)',code)
        return HEADER+MMIO+code+CLOCK_MAIN,path,names
    if group == 'f407':
        path=ROOT/'mcu/code/stm32/04-nvic-exti-board/main.c';text=path.read_text(encoding='utf-8');names=['EXTI0_IRQHandler']
        code=text[:text.index('/* 粗略延时')]+function(text,names[0])
        code=re.sub(r'\*\(volatile uint32_t \*\)\(([^()]*)\)',r'*reg(\1)',code)
        return HEADER+MMIO+code+F407_MAIN,path,names
    path=ROOT/('examples/exti-key/main.c' if group=='key' else 'examples/uart-dma-idle/main.c')
    text=path.read_text(encoding='utf-8');names=['HAL_GPIO_EXTI_Callback','key_process'] if group=='key' else ['rb_push','HAL_UARTEx_RxEventCallback','HAL_UART_ErrorCallback']
    prefix=text[:text.index('/* ----------------------------------------------------------------- 私有函数')] if group=='uart' else text[:text.index('/* ----------------------------------------------------------------- 私有函数')]
    prefix=prefix.replace('#include "stm32f1xx_hal.h"','/* HAL boundary supplied by explicit test doubles above. */')
    return HEADER+HAL+prefix+'\n'+'\n'.join(function(text,n) for n in names)+(KEY_MAIN if group=='key' else UART_MAIN),path,names


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cc',default='gcc');parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--case',choices=['all']+CASES,default='all');args=parser.parse_args()
    out=args.out.resolve()
    if out==ROOT or ROOT in out.parents:parser.error('--out must be outside the repository')
    out.mkdir(parents=True,exist_ok=True);selected=CASES if args.case=='all' else [args.case];results=[];built={}
    for case in selected:
        group='clock' if case=='mco' or case.startswith('clock-') else 'f407' if case=='f407-toggle' else 'key' if case=='f103-key' else 'uart'
        if group not in built:
            code,path,names=source_group(group);c=out/(group+'.c');exe=out/(group+'.exe');c.write_text(code,encoding='utf-8')
            cmd=[args.cc,'-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-variable','-O0','-DUSE_HSE_PLL=1',str(c),'-o',str(exe)]
            build=subprocess.run(cmd,capture_output=True,text=True);(out/(group+'-build.log')).write_text(build.stdout+build.stderr,encoding='utf-8')
            if build.returncode:print(build.stdout+build.stderr);return build.returncode
            built[group]=exe
        run=subprocess.run([str(built[group]),case],capture_output=True,text=True,timeout=15)
        output=run.stdout+run.stderr;(out/(case+'.log')).write_text(output,encoding='utf-8');print(output,end='')
        _,path,names=source_group(group)
        results.append({'case':case,'exit':run.returncode,'output':output,'source':str(path.relative_to(ROOT)),'source_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'functions':names})
    (out/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    return int(any(x['exit'] for x in results))


if __name__=='__main__':sys.exit(main())
