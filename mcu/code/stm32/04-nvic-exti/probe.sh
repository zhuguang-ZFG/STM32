#!/bin/sh
# probe.sh —— S4 NVIC/EXTI 章全部取证，一条命令跑完（不需要开发板）
#
#   sh probe.sh         三步取证：
#                       0. 用 grep/sed 从 .trellis/ref/cmsis 头文件"现挖"常数（输出自带行号）
#                       1. 宿主 gcc 编译运行 probe.c（_Static_assert 对撞 + 运行期断言）
#                       2. 启动文件向量表槽位核对（shell 直接数 .word 行）
#                       3. PATH 里有 arm-none-eabi-gcc 时：真链接一次，
#                          验证"强符号 ISR 顶替 weak 别名"且槽 22 装的是它的地址|1
#   sh probe.sh clean
#
# 产物一律落在 build/（code/**/build/ 已 gitignore）。

set -e
cd "$(dirname "$0")"

if [ "${1:-}" = "clean" ]; then rm -rf build; echo "已清理 build/"; exit 0; fi
mkdir -p build

CMSIS=../../../.trellis/ref/cmsis
HDR=$CMSIS/stm32f407xx.h
CORE=$CMSIS/core_cm4.h
STARTUP=../00-blink/startup_stm32f407xx.s
LDSCRIPT=../00-blink/stm32f407xx.ld

# .trellis/ref/ 被 gitignore（.gitignore:8），CI 上不存在；第 0 段挖出的常数
# 喂给宿主编译宏与向量槽核对（§0–§2）。缺头文件时仅跳过 §0–§2；
# §3 交叉链接只依赖 code/stm32/00-blink（入库文件）与 arm-none-eabi-gcc，
# 照常运行——CI 上保住"强符号顶替 weak、槽 22 = handler|1"主线取证。
if [ -f "$HDR" ] && [ -f "$CORE" ]; then

echo "############ 0. 从 CMSIS 头文件现挖常数（每行自带 文件:行号 引证） ############"

# fact <文件> <grep锚> <sed提取式> <名字>
# 值从 stdout 返回（调用方命令替换接走），引证行打到 stderr 直接显示
fact() {
    _l=$(grep -n "$2" "$1" | head -1)
    [ -n "$_l" ] || { echo "提取失败：$4（$1 里没有锚 $2）" >&2; exit 1; }
    _n=${_l%%:*}
    _v=$(printf '%s' "${_l#*:}" | sed -n "$3")
    [ -n "$_v" ] || { echo "解析失败：$4（$1:$_n）" >&2; exit 1; }
    echo "  $4 = $_v    <- $(basename "$1"):$_n" >&2
    printf '%s' "$_v"
}

PERIPH_BASE=$(fact  $HDR '^#define PERIPH_BASE'      's/^#define PERIPH_BASE[[:space:]]*\(0x[0-9A-Fa-f]*\)UL.*/\1/p'        PERIPH_BASE)
APB2_OFF=$(fact     $HDR '^#define APB2PERIPH_BASE'   's/.*+[[:space:]]*\(0x[0-9A-Fa-f]*\)UL).*/\1/p'                        APB2_OFFSET)
SYSCFG_OFF=$(fact   $HDR '^#define SYSCFG_BASE'       's/.*+[[:space:]]*\(0x[0-9A-Fa-f]*\)UL).*/\1/p'                        SYSCFG_OFFSET)
EXTI_OFF=$(fact     $HDR '^#define EXTI_BASE'         's/.*+[[:space:]]*\(0x[0-9A-Fa-f]*\)UL).*/\1/p'                        EXTI_OFFSET)
SCS_BASE=$(fact     $CORE '^#define SCS_BASE'         's/^#define SCS_BASE[[:space:]]*(\(0x[0-9A-Fa-f]*\)UL).*/\1/p'         SCS_BASE)
SYSTICK_OFF=$(fact  $CORE '^#define SysTick_BASE'     's/.*+[[:space:]]*\(0x[0-9A-Fa-f]*\)UL).*/\1/p'                        SYSTICK_OFFSET)
NVIC_OFF=$(fact     $CORE '^#define NVIC_BASE'        's/.*+[[:space:]]*\(0x[0-9A-Fa-f]*\)UL).*/\1/p'                        NVIC_OFFSET)
SCB_OFF=$(fact      $CORE '^#define SCB_BASE'         's/.*+[[:space:]]*\(0x[0-9A-Fa-f]*\)UL).*/\1/p'                        SCB_OFFSET)
PRIO_BITS=$(fact    $HDR '^#define __NVIC_PRIO_BITS'  's/^#define __NVIC_PRIO_BITS[[:space:]]*\([0-9]\{1,\}\)U.*/\1/p'       NVIC_PRIO_BITS)
PRIGROUP_POS=$(fact $CORE '^#define SCB_AIRCR_PRIGROUP_Pos' 's/^#define SCB_AIRCR_PRIGROUP_Pos[[:space:]]*\([0-9]\{1,\}\)U.*/\1/p' PRIGROUP_Pos)
VECTKEY=$(fact      $CORE '0x5FAUL << SCB_AIRCR_VECTKEY_Pos' 's/.*)0x\([0-9A-Fa-f]*\)UL << SCB_AIRCR_VECTKEY_Pos.*/\1/p'         AIRCR_VECTKEY)
SYSCFGEN_POS=$(fact $HDR '^#define RCC_APB2ENR_SYSCFGEN_Pos' 's/.*(\([0-9]\{1,\}\)U).*/\1/p'                                 RCC_SYSCFGEN_Pos)
EXTI0_PF=$(fact     $HDR '^#define SYSCFG_EXTICR1_EXTI0_PF[[:space:]]' 's/^#define SYSCFG_EXTICR1_EXTI0_PF[[:space:]]*\(0x[0-9A-Fa-f]*\)U.*/\1/p' EXTICR_EXTI0_PF)

irqn() { # $1=枚举名
    fact $HDR "^[[:space:]]*$1_IRQn[[:space:]]*=" \
         "s/^[[:space:]]*[A-Za-z0-9_]*IRQn[[:space:]]*=[[:space:]]*\(-\{0,1\}[0-9]\{1,\}\),.*/\1/p" "$1_IRQn"
}
SYSTICK_IRQN=$(irqn SysTick)
EXTI0_IRQN=$(irqn EXTI0)
EXTI1_IRQN=$(irqn EXTI1)
EXTI9_5_IRQN=$(irqn EXTI9_5)
TIM2_IRQN=$(irqn TIM2)
USART1_IRQN=$(irqn USART1)
EXTI15_10_IRQN=$(irqn EXTI15_10)

exti_off() { # $1=寄存器名 $2=结构体行锚
    fact $HDR "^  __IO uint32_t $1;" 's/.*Address offset: \(0x[0-9A-Fa-f]*\).*/\1/p' "EXTI_$1偏移"
}
EXTI_IMR_OFF=$(exti_off   IMR)
EXTI_EMR_OFF=$(exti_off   EMR)
EXTI_RTSR_OFF=$(exti_off  RTSR)
EXTI_FTSR_OFF=$(exti_off  FTSR)
EXTI_SWIER_OFF=$(exti_off SWIER)
EXTI_PR_OFF=$(exti_off    PR)
EXTICR_OFF=$(fact $HDR '^  __IO uint32_t EXTICR\[4\];' 's/.*Address offset: \(0x[0-9A-Fa-f]*\).*/\1/p' SYSCFG_EXTICR偏移)

echo
echo "############ 1. 宿主编译并运行（_Static_assert 对撞 + 运行期断言） ############"
HOSTCC=${CC:-gcc}
echo "宿主工具链：$HOSTCC $("$HOSTCC" -dumpfullversion 2>/dev/null || "$HOSTCC" -dumpversion)"
"$HOSTCC" -std=c11 -Wall -Wextra -Werror -O2 \
    -DHDR_PERIPH_BASE=${PERIPH_BASE}UL \
    -DHDR_APB2_OFF=${APB2_OFF}UL \
    -DHDR_SYSCFG_OFF=${SYSCFG_OFF}UL \
    -DHDR_EXTI_OFF=${EXTI_OFF}UL \
    -DHDR_SCS_BASE=${SCS_BASE}UL \
    -DHDR_SYSTICK_OFF=${SYSTICK_OFF}UL \
    -DHDR_NVIC_OFF=${NVIC_OFF}UL \
    -DHDR_SCB_OFF=${SCB_OFF}UL \
    -DHDR_PRIO_BITS=${PRIO_BITS}U \
    -DHDR_PRIGROUP_POS=${PRIGROUP_POS}U \
    -DHDR_VECTKEY=0x${VECTKEY}UL \
    -DHDR_SYSCFGEN_POS=${SYSCFGEN_POS}U \
    -DHDR_EXTI0_PF=${EXTI0_PF}U \
    -DHDR_SYSTICK_IRQN=${SYSTICK_IRQN} \
    -DHDR_EXTI0_IRQN=${EXTI0_IRQN} \
    -DHDR_EXTI1_IRQN=${EXTI1_IRQN} \
    -DHDR_EXTI9_5_IRQN=${EXTI9_5_IRQN} \
    -DHDR_TIM2_IRQN=${TIM2_IRQN} \
    -DHDR_USART1_IRQN=${USART1_IRQN} \
    -DHDR_EXTI15_10_IRQN=${EXTI15_10_IRQN} \
    -DHDR_EXTI_IMR_OFF=${EXTI_IMR_OFF}UL \
    -DHDR_EXTI_EMR_OFF=${EXTI_EMR_OFF}UL \
    -DHDR_EXTI_RTSR_OFF=${EXTI_RTSR_OFF}UL \
    -DHDR_EXTI_FTSR_OFF=${EXTI_FTSR_OFF}UL \
    -DHDR_EXTI_SWIER_OFF=${EXTI_SWIER_OFF}UL \
    -DHDR_EXTI_PR_OFF=${EXTI_PR_OFF}UL \
    -DHDR_SYSCFG_EXTICR_OFF=${EXTICR_OFF}UL \
    probe.c -o build/probe.exe
./build/probe.exe

echo
echo "############ 2. 向量表槽位核对（直接数 startup_stm32f407xx.s 的 .word 行） ############"
slots=$(sed -n '/^g_pfnVectors:/,/^  \.size g_pfnVectors/p' "$STARTUP" \
        | sed -n 's/^  \.word[[:space:]]*\([A-Za-z_0-9]*\).*/\1/p')
n_slots=$(printf '%s\n' "$slots" | wc -l)
echo "  向量表总项数 = $n_slots（16 内核 + 82 外设，应为 98）"
[ "$n_slots" -eq 98 ] || { echo "  ✗ 项数不符" >&2; exit 1; }

check_slot() { # $1=IRQn $2=期望符号 —— 槽号 = IRQn+16，sed 行号从 1 起故再 +1
    _s=$(printf '%s\n' "$slots" | sed -n "$(($1 + 17))p")
    if [ "$_s" = "$2" ]; then
        echo "  IRQn $1 -> 向量槽 $(($1 + 16)) = $_s  ✓"
    else
        echo "  IRQn $1 -> 向量槽 $(($1 + 16)) 取出「$_s」，期望 $2  ✗" >&2; exit 1
    fi
}
check_slot "$SYSTICK_IRQN"   SysTick_Handler
check_slot "$EXTI0_IRQN"     EXTI0_IRQHandler
check_slot "$EXTI1_IRQN"     EXTI1_IRQHandler
check_slot "$EXTI9_5_IRQN"   EXTI9_5_IRQHandler
check_slot "$TIM2_IRQN"      TIM2_IRQHandler
check_slot "$USART1_IRQN"    USART1_IRQHandler
check_slot "$EXTI15_10_IRQN" EXTI15_10_IRQHandler
else
    echo "未 provision .trellis/ref/cmsis（$HDR / $CORE 不存在）：跳过 §0–§2（常数对账/宿主编译/向量槽核对）；§3 交叉链接继续" >&2
fi

ARMPREFIX=arm-none-eabi-
if command -v "${ARMPREFIX}gcc" >/dev/null 2>&1; then
    echo
    echo "############ 3. 交叉链接：weak 默认被强符号顶替，槽 22 装的是 ISR 地址|1 ############"
    MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
    echo "交叉工具链：$("${ARMPREFIX}gcc" -dumpfullversion)"

    cat > build/isr_demo.c <<'EOF'
#include <stdint.h>

volatile uint32_t g_exti0_count;

/* 强符号：顶替启动文件里的 weak 别名（startup_stm32f407xx.s:222）。
 * ISR 进门第一件事：EXTI->PR（0x40013C14）写 1 清挂起，否则无限重进。 */
void EXTI0_IRQHandler(void)
{
    *(volatile uint32_t *)0x40013C14UL = 1UL << 0;
    g_exti0_count++;
}

int main(void)
{
    for (;;) { }
}
EOF

    "${ARMPREFIX}gcc" $MCU -std=c11 -Wall -Wextra -Werror -O2 -c build/isr_demo.c -o build/isr_demo.o
    "${ARMPREFIX}gcc" $MCU -c "$STARTUP" -o build/startup.o
    "${ARMPREFIX}gcc" $MCU -nostdlib -T "$LDSCRIPT" build/startup.o build/isr_demo.o -o build/irq_demo.elf

    echo "----- .isr_vector 落在 Flash 起始（objdump -h） -----"
    "${ARMPREFIX}objdump" -h build/irq_demo.elf | grep -E 'Idx|isr_vector|\.text' || true
    echo "----- 符号表：EXTI0_IRQHandler 是强定义，不再是 weak（objdump -t） -----"
    "${ARMPREFIX}objdump" -t build/irq_demo.elf | grep -E 'EXTI0_IRQHandler|Default_Handler$|g_pfnVectors' || true

    "${ARMPREFIX}objcopy" -O binary --only-section=.isr_vector build/irq_demo.elf build/vec.bin
    word22=$(dd if=build/vec.bin bs=4 skip=22 count=1 2>/dev/null | od -A n -t x4 | tr -d ' \n')
    handler=$("${ARMPREFIX}nm" build/irq_demo.elf | grep ' T EXTI0_IRQHandler$' | cut -d' ' -f1) \
        || { echo "nm 未找到强符号 EXTI0_IRQHandler——取证段失效" >&2; exit 1; }
    [ -n "$handler" ] || { echo "nm 取到的 EXTI0_IRQHandler 地址为空——取证段失效" >&2; exit 1; }
    defaddr=$("${ARMPREFIX}nm" build/irq_demo.elf | grep ' T Default_Handler$' | cut -d' ' -f1) || true
    want=$(printf '%08x' $((0x$handler | 1)))
    echo "  槽22（EXTI0）内容 = $word22"
    echo "  nm: EXTI0_IRQHandler = 0x$handler（|Thumb 位 = $want），Default_Handler = 0x$defaddr"
    if [ "$word22" = "$want" ]; then
        echo "  ✓ 向量槽装的是强符号地址（最低位 1 = Thumb），weak 别名被顶替"
    else
        echo "  ✗ 槽位内容与强符号地址不符" >&2; exit 1
    fi

    echo "----- EXTI0_IRQHandler 反汇编（可见清挂起的绝对地址 0x40013C14） -----"
    "${ARMPREFIX}objdump" -d build/irq_demo.elf > build/irq_demo.s
    sed -n '/<EXTI0_IRQHandler>:/,/^$/p' build/irq_demo.s
    grep -i '40013c14' build/irq_demo.s | head -3
else
    echo
    echo "（跳过交叉链接：PATH 里没有 arm-none-eabi-gcc；宿主断言不受影响）"
fi

echo
echo "== probe.sh 全部步骤完成 =="
