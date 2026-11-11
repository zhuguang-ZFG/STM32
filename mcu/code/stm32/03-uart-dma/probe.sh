#!/bin/sh
# probe.sh —— S7《波特率是算出来的》全部取证，一条命令跑完（不需要开发板）
#
#   sh probe.sh    1) 宿主 gcc 真跑 probe.c：probe.c 把 USART1/DMA2/RCC/GPIO/SysTick/NVIC
#                     二十多个寄存器全改指一对假寄存器、再 #define MCU_PROBE_NO_MAIN 把
#                     main() 关掉，然后 #include "main.c"——所以下面断言跑的是固件本体
#                     （clocks_read / usart1_init / dma2_stream5_rx_init / led_set /
#                      uart_write_blocking / consume_rx / 三个 ISR），不是另抄一遍算术；
#                  2) 三方对账：第 2 节打印的 33 条位号与 CMSIS 官方头文件的 _Pos 逐位 diff
#                     （必须为空）；第 11 节打印的 25 个寄存器地址用「头文件里现挖的 base
#                     + 结构体成员偏移」独立算一遍 diff；第 6 节打印的那张误差表与
#                     docs/stm32/07-usart.md 里那张 markdown 表逐行 diff——正文数字一改，
#                     这一关立刻红。这一步只吃第 1 步的输出和站内正文，头文件不在也只跳
#                     位号/地址两小步，误差表那一小步永远跑；
#                  3) PATH 里有 arm-none-eabi-gcc 时，把 main.c 编成 Cortex-M4 的 -O2 与 -O0
#                     两份目标文件并反汇编：除以 115200 在机身里根本没有除法、BRR/CR1 的偏移
#                     以立即数出现、TXE/TC 是「左移进符号位」的自旋、DMA 字面量池把基址锚到
#                     DMA1 上、-O0 那个函数在 -O2 里整个消失。
#   sh probe.sh clean   删 build/
#
# 第 3 步只在 PINNED_CC 那一版交叉链上判定：那些结论逐条写着"哪条指令、哪个寄存器、字面量
# 池锚到哪"，那是那一版编译器的选择，不是硬件规定。CI 的 apt 交叉链版本不同，没有本机实跑
# 证据就不硬套——所以第 3 步在 CI 上会打印跳过。哪天有人在 CI 那版上把逐条断言验过，
# 再把这个门放开。第 1、2 步（也就是正文那张表的对账）不分版本，CI 每次都真判。
#
# 产物一律落在 build/probe/（code/**/build/ 已 gitignore）。本工程是 arm-make 项目，
# Makefile 自己会用 build/，所以这里刻意只写 build/probe/，两边不打架。
#
# CI 侧：code/projects.json 里本工程登记了 "probe": "probe.sh"，firmware:check 建完 ELF
# 就会跑这一遍；.trellis/ref/cmsis 那两个头文件由 .github/workflows/quality.yml 固定到
# cmsis-device-f4 v2.6.11 与 CMSIS_5 5.9.0 并校验 sha256（与本地这两份逐字节相同）。
#
# 想让第 3 步跑起来：把交叉工具链的 bin 目录加进 PATH，例如
#   PATH="/d/zhugu-home/tools/armgcc/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:$PATH"

set -e
cd "$(dirname "$0")"

if [ "${1:-}" = "clean" ]; then
    rm -rf build
    exit 0
fi

mkdir -p build/probe

HOSTCC=${CC:-gcc}
MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
ARMPREFIX=arm-none-eabi-
PINNED_CC=15.2.1   # 第 3 步的指令形状断言只在这一版交叉链上判定，理由见文件头
CMSIS=../../../.trellis/ref/cmsis
HDR=$CMSIS/stm32f407xx.h
CORE=$CMSIS/core_cm4.h
DOC=../../../docs/stm32/07-usart.md

echo "############ 1. 宿主：BRR 那张表 + 收发两级缓冲（断言取证） ############"
echo "宿主工具链：$HOSTCC $("$HOSTCC" -dumpfullversion 2>/dev/null || "$HOSTCC" -dumpversion)"
"$HOSTCC" -std=c11 -Wall -Wextra -Werror -O1 probe.c -o build/probe/probe.exe
./build/probe/probe.exe > build/probe/probe.txt
tr -d '\r' < build/probe/probe.txt > build/probe/probe.lf
cat build/probe/probe.lf
grep -q '断言全绿' build/probe/probe.lf || { echo "第 1 步断言未过——下面两步不可信" >&2; exit 1; }

echo
echo "############ 2. 与 CMSIS 官方头文件 + 站内正文对账 ############"
if [ -f "$HDR" ] && [ -f "$CORE" ]; then
    echo "头文件：$(basename "$HDR") / $(basename "$CORE")"

    # ---- 2a. 位号：probe 第 2 节那一块，逐位和 *_Pos 对 ----
    sed -n '/^=== 2\./,/^$/p' build/probe/probe.lf | grep -E '^[A-Z][A-Z0-9_]* [0-9]+$' \
        | sort > build/probe/pos-probe.txt
    awk '/^#define [A-Z][A-Z0-9_]*_Pos/ {
           name = $2; sub(/_Pos$/, "", name);
           v = $3; gsub(/[^0-9]/, "", v);
           printf "%s %s\n", name, v
         }' "$HDR" "$CORE" | sort > build/probe/pos-header-all.txt
    # 只留本章真正用到的那些，头文件里多出来的位号不算失败
    awk 'NR==FNR{k[$1]=$2;next} ($1 in k){printf "%s %s\n",$1,k[$1]}' \
        build/probe/pos-header-all.txt build/probe/pos-probe.txt | sort > build/probe/pos-header.txt
    if diff -u build/probe/pos-header.txt build/probe/pos-probe.txt > build/probe/pos.diff; then
        echo "  位号对账：$(wc -l < build/probe/pos-probe.txt) 条逐位一致（diff 为空）"
    else
        echo "  位号对账：不一致！第 2 节那张位表不可信" >&2
        cat build/probe/pos.diff >&2; exit 1
    fi

    # ---- 2b. 地址：base 与成员偏移全部从 CMSIS 现挖，独立算一遍 ----
    # 宏的两种形状：纯字面量（PERIPH_BASE 0x40000000UL）与「基址 + 偏移」
    # （USART1_BASE (APB2PERIPH_BASE + 0x1000UL)）。脚本里不写死任何一个地址。
    lit() { # $1=文件 $2=宏名 → 十进制值，并把引证打到 stderr
        _l=$(grep -n -m1 "^#define $2[[:space:]]" "$1")
        [ -n "$_l" ] || { echo "提取失败：$2（$1 里没有）" >&2; exit 1; }
        _v=$(printf '%s' "${_l#*:}" | sed -n 's/^#define '$2'[[:space:]]*(\{0,1\}\(0x[0-9A-Fa-f]*\)UL.*/\1/p')
        [ -n "$_v" ] || { echo "解析失败：$2 不是纯字面量（$1:${_l%%:*}）" >&2; exit 1; }
        echo "  $2 = $_v   <- $(basename "$1"):${_l%%:*}" >&2
        printf '%s' "$(( _v ))"
    }
    plus() { # $1=文件 $2=宏名 → 该宏里「+ 0x...UL」那个偏移的十进制
        _l=$(grep -n -m1 "^#define $2[[:space:]]" "$1")
        [ -n "$_l" ] || { echo "提取失败：$2（$1 里没有）" >&2; exit 1; }
        _v=$(printf '%s' "${_l#*:}" | sed -n 's/.*+[[:space:]]*\(0x[0-9A-Fa-f]*\)UL.*/\1/p')
        [ -n "$_v" ] || { echo "解析失败：$2 里没找到 + 0x...UL（$1:${_l%%:*}）" >&2; exit 1; }
        echo "  $2 偏移 = $_v   <- $(basename "$1"):${_l%%:*}" >&2
        printf '%s' "$(( _v ))"
    }
    struct_body() { # $1=文件 $2=typedef 名 → 那个 struct 的完整原文
        # 收尾那行不保证是一个空格：core_cm4.h 里 NVIC_Type 写的是「}  NVIC_Type;」两格
        awk -v name="$2" '
            /^typedef struct/ { inb=1; buf="" }
            inb { buf = buf $0 "\n" }
            inb && $0 ~ ("^}[[:space:]]*" name ";$") { printf "%s", buf; inb=0 }
        ' "$1"
    }
    # 成员偏移优先读头文件自己的「Address offset: 0x..」注释；DMA_Stream_TypeDef 这一类
    # 没写注释的，退到「按声明顺序数，全 uint32_t 无 reserved ⇒ 步长 4」，并且先验这个前提。
    off_in() { # $1=文件 $2=typedef 名 $3=成员名 → 十进制偏移
        _b=$(struct_body "$1" "$2")
        [ -n "$_b" ] || { echo "提取失败：$1 里找不到 } $2;" >&2; exit 1; }
        _o=$(printf '%s\n' "$_b" | grep -E "^  __I[OM]M? uint32_t $3;" \
                | sed -n 's/.*t\?ffset: \(0x[0-9A-Fa-f]*\).*/\1/p' | head -1)
        if [ -n "$_o" ]; then printf '%s' "$(( _o ))"; return; fi
        if printf '%s\n' "$_b" | grep -qE 'RESERVED|uint(8|16)_t|uint64_t'; then
            echo "拒绝推断：$2 里有 reserved/非 uint32_t 成员，数顺序不成立（$1）" >&2; exit 1
        fi
        _n=$(printf '%s\n' "$_b" | awk -v m="$3" '
            /^  __I[OM]M? uint32_t [A-Za-z0-9_]+;/ {
                k++
                if ($0 ~ ("uint32_t " m ";")) { print k-1; found=1; exit }
            }
            END { if (!found) exit 1 }') || true
        [ -n "$_n" ] || { echo "提取失败：$2 的成员 $3 既没有 Offset 注释也不在声明序列里（$1）" >&2; exit 1; }
        printf '%s' "$(( _n * 4 ))"
    }
    arr_in() { # $1=文件 $2=typedef 名 $3=数组成员 $4=下标 → 数组首偏移 + 下标×4
        _b=$(struct_body "$1" "$2")
        _o=$(printf '%s\n' "$_b" | grep -E "^  __I[OM]M? uint32_t $3\[" \
                | sed -n 's/.*t\?ffset: \(0x[0-9A-Fa-f]*\).*/\1/p' | head -1)
        [ -n "$_o" ] || { echo "提取失败：$2 的数组成员 $3 没有 Offset 注释（$1）" >&2; exit 1; }
        printf '%s' "$(( $(( _o )) + $4 * 4 ))"
    }
    # RCC 的 AHB1 段基址是本章所有 GPIO/DMA 地址的根，这一条不成立下面全错
    grep -q '^#define AHB1PERIPH_BASE[[:space:]]*(PERIPH_BASE + 0x00020000UL)$' "$HDR" \
        || { echo "CMSIS 里 AHB1PERIPH_BASE 不再是 PERIPH_BASE+0x20000——这一遍对账的口径要重看" >&2; exit 1; }
    echo "  AHB1PERIPH_BASE = PERIPH_BASE + 0x20000（现挖，无偏移假设）  <- $(basename "$HDR"):$(grep -n -m1 '^#define AHB1PERIPH_BASE' "$HDR" | cut -d: -f1)" >&2

    PERIPH=$(lit "$HDR" PERIPH_BASE)
    AHB1=$((PERIPH + $(plus "$HDR" AHB1PERIPH_BASE)))
    APB2=$((PERIPH + $(plus "$HDR" APB2PERIPH_BASE)))
    USART1=$((APB2 + $(plus "$HDR" USART1_BASE)))
    GPIOA=$((AHB1 + $(plus "$HDR" GPIOA_BASE)))
    GPIOF=$((AHB1 + $(plus "$HDR" GPIOF_BASE)))
    RCC=$((AHB1 + $(plus "$HDR" RCC_BASE)))
    DMA2=$((AHB1 + $(plus "$HDR" DMA2_BASE)))
    S5=$((DMA2 + $(plus "$HDR" DMA2_Stream5_BASE)))
    SCS=$(lit "$CORE" SCS_BASE)
    SYSTICK=$((SCS + $(plus "$CORE" SysTick_BASE)))
    NVIC=$((SCS + $(plus "$CORE" NVIC_BASE)))

    {
        for m in SR DR BRR CR1 CR2 CR3; do
            printf 'USART1_%s 0x%08X\n' "$m" $((USART1 + $(off_in "$HDR" USART_TypeDef "$m")))
        done
        printf 'GPIOA_MODER 0x%08X\n' $((GPIOA + $(off_in "$HDR" GPIO_TypeDef MODER)))
        # CMSIS 里 AFRH 不是独立成员，它是 AFR[2] 的第二格（注释写的是 0x20-0x24）
        printf 'GPIOA_AFRH 0x%08X\n' $((GPIOA + $(arr_in "$HDR" GPIO_TypeDef AFR 1)))
        for m in MODER BSRR; do
            printf 'GPIOF_%s 0x%08X\n' "$m" $((GPIOF + $(off_in "$HDR" GPIO_TypeDef "$m")))
        done
        for m in PLLCFGR CFGR AHB1ENR APB2ENR; do
            printf 'RCC_%s 0x%08X\n' "$m" $((RCC + $(off_in "$HDR" RCC_TypeDef "$m")))
        done
        for m in LISR HISR HIFCR; do
            printf 'DMA2_%s 0x%08X\n' "$m" $((DMA2 + $(off_in "$HDR" DMA_TypeDef "$m")))
        done
        for m in CR NDTR PAR M0AR FCR; do
            printf 'DMA2_S5_%s 0x%08X\n' "$m" $((S5 + $(off_in "$HDR" DMA_Stream_TypeDef "$m")))
        done
        for m in CTRL LOAD; do
            printf 'SysTick_%s 0x%08X\n' "$m" $((SYSTICK + $(off_in "$CORE" SysTick_Type "$m")))
        done
        printf 'NVIC_ISER1 0x%08X\n' $((NVIC + $(arr_in "$CORE" NVIC_Type ISER 1)))
    } > build/probe/addr-header.txt
    # 头文件那一遍按 CMSIS 的声明顺序排，probe 那一遍按本章正文的叙述顺序排——
    # 对账比的是「同一个名字同一个地址」，不是比谁先写，所以两边都排序再 diff。
    sort build/probe/addr-header.txt > build/probe/addr-header-sorted.txt
    sed -n '/^=== 11\./,/^$/p' build/probe/probe.lf | grep -E '^[A-Z][A-Za-z0-9_]* 0x' \
        | sort > build/probe/addr-probe.txt
    if diff -u build/probe/addr-header-sorted.txt build/probe/addr-probe.txt > build/probe/addr.diff; then
        echo "  地址对账：$(wc -l < build/probe/addr-probe.txt) 个全中（diff 为空）"
        paste -d' | ' build/probe/addr-header-sorted.txt build/probe/addr-probe.txt | sed 's/^/    /'
    else
        echo "  地址对账：不一致！第 11 节那张地址表不可信" >&2
        cat build/probe/addr.diff >&2; exit 1
    fi
else
    echo "未 provision .trellis/ref/cmsis（$HDR / $CORE 不存在）：跳过 2a/2b 的位号与地址对账" >&2
fi

# ---- 2c. 正文那张误差表：这一步只吃 probe 的输出和站内正文，不依赖 CMSIS，永远跑 ----
if [ -f "$DOC" ]; then
    echo "  ----- 正文误差表对账（左=本机固件宏算出来的，右=$DOC 里写的） -----"
    sed -n '/^=== 6\./,/^$/p' build/probe/probe.lf | grep -E '^\| ' \
        > build/probe/table-probe.txt
    grep -E '^\| [0-9]+ MHz \|' "$DOC" | tr -d '\r' > build/probe/table-doc.txt
    if diff -u build/probe/table-probe.txt build/probe/table-doc.txt > build/probe/table.diff; then
        echo "  误差表对账：$(wc -l < build/probe/table-probe.txt) 行逐格一致（diff 为空）"
    else
        echo "  误差表对账：不一致！正文那几个数不是本机算出来的" >&2
        cat build/probe/table.diff >&2; exit 1
    fi
else
    echo "找不到 $DOC：正文误差表无从对账" >&2; exit 1
fi

echo
echo "############ 3. 交叉编译：波特率与两级缓冲在指令流里长什么样 ############"
# Windows 的工具链把版本号打成 CRLF：dash 不剥 \r、bash 剥，所以必须 tr 一遍，
# 否则本机 15.2.1 会因为尾巴上那个 \r 判成「版本不对」，第 3 步静默跳过——证据没了却不红。
ARMCC=$("${ARMPREFIX}gcc" -dumpfullversion 2>/dev/null | tr -d '\r')
if [ "$ARMCC" = "$PINNED_CC" ]; then
    echo "交叉工具链：$ARMCC"
    "${ARMPREFIX}gcc" $MCU -std=c11 -Wall -Wextra -Werror -O2 -c main.c -o build/probe/main_o2.o
    "${ARMPREFIX}gcc" $MCU -std=c11 -Wall -Wextra -Werror -O0 -c main.c -o build/probe/main_o0.o
    "${ARMPREFIX}objdump" -d build/probe/main_o2.o > build/probe/main_o2.dis
    "${ARMPREFIX}objdump" -d build/probe/main_o0.o > build/probe/main_o0.dis

    echo "----- 同一份源码，两个优化档的段大小 -----"
    "${ARMPREFIX}size" build/probe/main_o0.o build/probe/main_o2.o

    FN() { sed -n "/<$1>:/,/^\$/p" "$2"; }
    FAIL3=0
    need() { # need 函数 正则 说明 —— 在 -O2 的 main 里必须出现
        if FN "$1" build/probe/main_o2.dis | grep -qE "$2"; then
            echo "  [中] $1：$3"
        else
            echo "  [失] $1：$3（机身里没有 $2）" >&2; FAIL3=1
        fi
    }
    deny() { # deny 函数 正则 说明 —— 在 -O2 的 main 里必须不出现
        if FN "$1" build/probe/main_o2.dis | grep -qE "$2"; then
            echo "  [失] $1：$3（机身里居然有 $2）" >&2; FAIL3=1
        else
            echo "  [中] $1：$3"
        fi
    }

    echo "----- 现场1：/115200 在机身里根本不是除法 -----"
    need main 'add\.w[[:space:]]+r3, r3, #57600' '四舍五入那一次加法 = 115200/2 的立即数 0xe100'
    need main '91a2b3c5'                        '除以 115200 变成乘这个 magic 常数（字面量池）'
    need main 'umull'                           'magic multiply：umull 取高位'
    need main 'lsrs[[:space:]]+r3, r3, #16'     '再右移 16 位就商——一条 udiv 都没花'
    need main 'str[[:space:]]+r3, \[r5, #8\]'   '商写进 USART1_BASE+0x08 = BRR'
    need main '10624dd3'                        '/1000（SysTick 装载值）同样走 magic，另一个常数'
    echo "  （对照：同一段代码里 HPRE/PPRE2 那两个除法编成了真 udiv——除数是运行时查表来的，编译器折不动）"
    need main 'udiv'                            'HPRE/PPRE2 的分频系数是运行时查出来的，只能真除'

    echo "----- 现场2：回读时钟树 = 读字段 + 查两张半字表 -----"
    need main 'ldr\.w[[:space:]]+r5, \[r1, #2056\]'  'RCC_CFGR 编成 [r1,#2056]：r1=0x40023000 → 0x40023808'
    need main 'and\.w[[:space:]]+r3, r5, #12'        'SWS 取 [3:2]，先 and 再 cmp #8 / #4'
    need main 'ubfx[[:space:]]+r0, r5, #4, #4'       'HPRE 字段 [7:4]'
    need main 'ubfx[[:space:]]+r3, r5, #13, #3'      'PPRE2 字段 [15:13]'
    need main 'ldrh\.w[[:space:]]+r1, \[r1, r0, lsl #1\]' '分频系数不是算的是查的：半字表按字段值索引'

    echo "----- 现场3：CR1 那一个 0x201C，与点灯那两位 -----"
    need main 'movw[[:space:]]+r2, #8220'   'CR1 = UE|TE|RE|IDLEIE = 0x201C，一条 movw'
    need main 'str[[:space:]]+r2, \[r5, #12\]' '写进 USART1_BASE+0x0C = CR1'
    need main 'strb\.w[[:space:]]+r2, \[r3, #37\]' 'IP[37]：USART1 的优先级是一个字节（接 S4）'
    need main 'strb\.w[[:space:]]+r2, \[r3, #68\]' 'IP[68]：DMA2_Stream5 同理'
    need main 'orr\.w[[:space:]]+r3, r3, #32'      'ISER1 |= 1<<(37-32) = bit5'
    need main 'orr\.w[[:space:]]+r3, r3, #16'      'ISER2 |= 1<<(68-64) = bit4'

    echo "----- 现场4：TXE 与 TC 的自旋，都是「搬进符号位再判」 -----"
    need main 'ldr[[:space:]]+r3, \[r5, #0\]'  '先读 USART1_SR（+0x00）'
    need main 'lsls[[:space:]]+r6, r3, #24'    'TXE=bit7 左移 24 位搬到符号位'
    need main 'lsls[[:space:]]+r1, r3, #25'    'TC=bit6 左移 25 位搬到符号位'
    need main 'bpl\.n'                         'bpl 自旋：符号位为 0（标志没起来）就再读一遍'
    need main 'str[[:space:]]+r1, \[r5, #4\]'  '每个字节一次 str 进 USART1_DR（+0x04）'

    echo "----- 现场5：DMA 那六个字，和字面量池把基址锚到 DMA1 上 -----"
    need dma2_stream5_rx_init '0800051c'                  'CR 的初值（CHSEL=4|PSIZE=WORD|MSIZE=WORD|CIRC|MINC|三个中断使能）在池里'
    need dma2_stream5_rx_init 'orr\.w[[:space:]]+r3, r3, #1' 'EN=bit0 是最后一步读-改-写上去的'
    need dma2_stream5_rx_init 'str\.w[[:space:]]+ip, \[r2, #1168\]' 'PAR 编成 [r2,#1168]=0x490'
    need dma2_stream5_rx_init '40011004'                  'PAR 的值 = USART1_DR 的地址，不是 USART1_SR'
    need dma2_stream5_rx_init 'mov\.w[[:space:]]+ip, #64' 'NDTR = 环形缓冲一半（64 字节）'
    need dma2_stream5_rx_init '40026000'                  '池里躺的是 0x40026000——那是 DMA1 的基址'
    echo "     （编译器把 DMA2_BASE(0x40026400)+0x88 折成了 0x40026000 + #1160：跨外设重新锚基址，靠立即数补回来）"

    echo "----- 现场6：中断里一次清掉三个标志 -----"
    need consume_rx 'and\.w[[:space:]]+ip, r0, #3584' 'TEIF5|HTIF5|TCIF5 = bit9..11 → 0xe00'
    need consume_rx 'str\.w[[:space:]]+ip, \[r1, #1036\]' '写的是 HIFCR（0x40026000+0x40c），不是只读的 HISR'

    echo "----- 现场7：-O0 与 -O2 的形状差 -----"
    if grep -qE '^0*[0-9a-f]* <usart1_init>:' build/probe/main_o0.dis; then
        echo "  [中] -O0：usart1_init 是一个真函数（有独立标签）"
    else
        echo "  [失] -O0：没找到 usart1_init 的函数标签" >&2; FAIL3=1
    fi
    if grep -qE '^0*[0-9a-f]* <usart1_init>:' build/probe/main_o2.dis; then
        echo "  [失] -O2：usart1_init 还在——它应该已经被折进 main 了" >&2; FAIL3=1
    else
        echo "  [中] -O2：usart1_init 整个消失（没有标签），调用点被搬进 main 里"
    fi
    if FN usart1_init build/probe/main_o0.dis | grep -qE 'str[[:space:]]+r3, \[r7, #12\]'; then
        echo "  [中] -O0：BRR 先存到栈上临时变量 [r7,#12]，下一步再读回来——源码里一行，机身里三步"
    else
        echo "  [失] -O0：没看到 [r7,#12] 那个栈槽往返" >&2; FAIL3=1
    fi
    deny main 'str[[:space:]]+r3, \[r7, #12\]' 'main：-O2 里 BRR 从算出到写寄存器全程待在寄存器，那个栈槽没了'

    [ "$FAIL3" = 0 ] || { echo "第 3 步机身断言未过——正文引用的那些反汇编结论不可信" >&2; exit 1; }

    echo "----- 那一条 magic 乘法的原码 -----"
    grep -m1 -E '91a2b3c5' build/probe/main_o2.dis | sed 's/^/  /'
    grep -m1 -E 'umull' build/probe/main_o2.dis | sed 's/^/  /'
    echo "  （除数 115200 是编译期常数 → 编译器换成乘倒数；1000 同理，两个常数两枚 magic）"
else
    echo "（跳过第 3 步：指令形状断言只认 $PINNED_CC 这一版口径，当前交叉链是「${ARMCC:-PATH 里没有}」——没有本机证据就不套到别的版本上，理由见文件头）"
fi

echo
echo "== probe.sh 全部步骤完成 =="
