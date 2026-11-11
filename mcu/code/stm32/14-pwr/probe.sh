#!/bin/sh
# probe.sh —— S14《低功耗：三档睡眠》全部取证，一条命令跑完（不需要开发板）
#
#   sh probe.sh   1) 宿主 gcc 真跑 probe.c：probe.c 把 PWR_CR/PWR_CSR/RCC_*/
#                    SCB_SCR/DBGMCU_CR/SysTick_LOAD/BKPSRAM 全改指一对假寄存器再
#                    #include "main.c"，所以下面断言跑的是固件本体
#                    （pwr_mode_words / enter_sleep / enter_stop / enter_standby /
#                      backup_domain_unlock / bkp_store / iwdg_timeout_ms /
#                      usart_baud_from_brr / reset_cause_decode / firmware_main），
#                    不是另抄一遍算术；
#                 2) 把第 2 节打印的全部位号与 CMSIS 官方头文件的 _Pos 逐位 diff
#                    （必须为空），再把第 9 节打印的 10 个寄存器地址用「头文件里挖出来
#                    的 base + 结构体成员 Address offset」独立算一遍 diff；
#                 3) PATH 里有 arm-none-eabi-gcc 时，把 main.c 编成 Cortex-M4 的
#                    -O2 目标文件并反汇编：三档睡眠各自那两位的 orr/bic、dsb sy + wfi
#                    相邻、wfi 之后还剩几条指令、备份域五个立即数、醒来查标志的符号位技巧。
#   sh probe.sh clean   删 build/
#
# 产物一律落在 build/（code/**/build/ 已 gitignore）。
#
# 想让第 3 步跑起来：把交叉工具链的 bin 目录加进 PATH，例如
#   PATH="/d/zhugu-home/tools/armgcc/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:$PATH"

set -e
cd "$(dirname "$0")"

if [ "${1:-}" = "clean" ]; then
    rm -rf build
    exit 0
fi

mkdir -p build

HOSTCC=${CC:-gcc}
MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
ARMPREFIX=arm-none-eabi-
CMSIS=../../../.trellis/ref/cmsis
HDR=$CMSIS/stm32f407xx.h
CORE=$CMSIS/core_cm4.h

echo "############ 1. 宿主：三档定档位 + 醒来那笔时钟账（断言取证） ############"
echo "宿主工具链：$HOSTCC $("$HOSTCC" -dumpfullversion 2>/dev/null || "$HOSTCC" -dumpversion)"
"$HOSTCC" -std=c11 -Wall -Wextra -Werror -O1 probe.c -o build/probe.exe
./build/probe.exe > build/probe.txt
tr -d '\r' < build/probe.txt > build/probe.lf
cat build/probe.lf
grep -q '断言全绿' build/probe.lf || { echo "第 1 步断言未过——下面两步不可信" >&2; exit 1; }

echo
echo "############ 2. 与 CMSIS 官方头文件对账：每一条位号 + 10 个寄存器地址 ############"
if [ -f "$HDR" ] && [ -f "$CORE" ]; then
    echo "头文件：$(basename "$HDR") / $(basename "$CORE")"

    # ---- 2a. 位号：probe 第 2 节的那一块，逐位和 *_Pos 对 ----
    sed -n '/^=== 2\./,/^$/p' build/probe.lf | grep -E '^[A-Z][A-Z0-9_]* [0-9]+$' \
        | sort > build/pos-probe.txt
    awk '/^#define [A-Z][A-Z0-9_]*_Pos/ {
           name = $2; sub(/_Pos$/, "", name);
           v = $3; gsub(/[^0-9]/, "", v);
           printf "%s %s\n", name, v
         }' "$HDR" "$CORE" | sort > build/pos-header-all.txt
    # 只留本章真正用到的那 30 个，多留的位号不算失败
    awk 'NR==FNR{k[$1]=$2;next} ($1 in k){printf "%s %s\n",$1,k[$1]}' \
        build/pos-header-all.txt build/pos-probe.txt | sort > build/pos-header.txt
    if diff -u build/pos-header.txt build/pos-probe.txt > build/pos.diff; then
        echo "  位号对账：$(wc -l < build/pos-probe.txt) 条逐位一致（diff 为空）"
    else
        echo "  位号对账：不一致！第 2 节那张位表不可信" >&2
        cat build/pos.diff >&2; exit 1
    fi

    # ---- 2b. 地址：base 与成员偏移全部从 CMSIS 现挖，独立算一遍 ----
    # fact 的两种形状：纯字面量（PERIPH_BASE 0x40000000UL）与「基址 + 偏移」
    # （RCC_BASE (AHB1PERIPH_BASE + 0x3800UL)）。偏移一律现挖，脚本里不写死任何一个地址。
    lit() { # $1=文件 $2=宏名 → 十进制值，并打出引证
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
    off_in() { # $1=CMSIS 文件 $2=typedef 名 $3=成员名 → 结构体里那条 Offset: 0x.. 注释
        _b=$(awk -v name="} $2;" '
            /^typedef struct$/ { inb=1; buf="" }
            inb { buf = buf $0 "\n" }
            inb && $0 == name { printf "%s", buf; inb=0 }
        ' "$1")
        _o=$(printf '%s\n' "$_b" | grep -E "^  __I[OM]M? uint32_t $3;" \
                | sed -n 's/.*t\?ffset: \(0x[0-9A-Fa-f]*\).*/\1/p' | head -1)
        [ -n "$_o" ] || { echo "提取失败：$2 的成员 $3 没有 Offset 注释（$1）" >&2; exit 1; }
        printf '%s' "$(( _o ))"
    }
    # APB1PERIPH_BASE 是「= PERIPH_BASE」，一个加号都不能有，否则下面算错还看不出来
    grep -q '^#define APB1PERIPH_BASE[[:space:]]*PERIPH_BASE$' "$HDR" \
        || { echo "CMSIS 里 APB1PERIPH_BASE 不再是 PERIPH_BASE 的原样别名——这一遍对账的口径要重看" >&2; exit 1; }
    echo "  APB1PERIPH_BASE = PERIPH_BASE（挖到的是原样别名，无偏移）  <- $(basename "$HDR"):$(grep -n -m1 '^#define APB1PERIPH_BASE' "$HDR" | cut -d: -f1)" >&2

    PERIPH=$(lit "$HDR" PERIPH_BASE)
    BKPSRAM=$(lit "$HDR" BKPSRAM_BASE)
    DBGMCU=$(lit "$HDR" DBGMCU_BASE)
    SCS=$(lit "$CORE" SCS_BASE)
    AHB1=$((PERIPH + $(plus "$HDR" AHB1PERIPH_BASE)))
    RCC=$((AHB1 + $(plus "$HDR" RCC_BASE)))
    PWR=$((PERIPH + $(plus "$HDR" PWR_BASE)))
    SYSTICK=$((SCS + $(plus "$CORE" SysTick_BASE)))
    SCB=$((SCS + $(plus "$CORE" SCB_BASE)))

    {
        printf 'PWR_CR 0x%08X\n'      $((PWR + $(off_in "$HDR" PWR_TypeDef CR)))
        printf 'PWR_CSR 0x%08X\n'     $((PWR + $(off_in "$HDR" PWR_TypeDef CSR)))
        printf 'RCC_APB1ENR 0x%08X\n' $((RCC + $(off_in "$HDR" RCC_TypeDef APB1ENR)))
        printf 'RCC_AHB1ENR 0x%08X\n' $((RCC + $(off_in "$HDR" RCC_TypeDef AHB1ENR)))
        printf 'RCC_BDCR 0x%08X\n'    $((RCC + $(off_in "$HDR" RCC_TypeDef BDCR)))
        printf 'RCC_CSR 0x%08X\n'     $((RCC + $(off_in "$HDR" RCC_TypeDef CSR)))
        printf 'SCB_SCR 0x%08X\n'     $((SCB + $(off_in "$CORE" SCB_Type SCR)))
        printf 'SysTick_LOAD 0x%08X\n' $((SYSTICK + $(off_in "$CORE" SysTick_Type LOAD)))
        printf 'DBGMCU_CR 0x%08X\n'   $((DBGMCU + $(off_in "$HDR" DBGMCU_TypeDef CR)))
        printf 'BKPSRAM 0x%08X\n'     $BKPSRAM
    } > build/addr-header.txt
    sed -n '/^=== 9\./,/^$/p' build/probe.lf | grep -E '^[A-Z][A-Za-z0-9_]* 0x' \
        > build/addr-probe.txt

    echo "  ----- 地址对账（左=CMSIS base+成员偏移算的，右=固件那一遍打印的） -----"
    paste -d' | ' build/addr-header.txt build/addr-probe.txt | sed 's/^/    /'
    if diff -u build/addr-header.txt build/addr-probe.txt > build/addr.diff; then
        echo "  地址对账：$(wc -l < build/addr-probe.txt) 个全中（diff 为空）"
    else
        echo "  地址对账：不一致！第 9 节那张地址表不可信" >&2
        cat build/addr.diff >&2; exit 1
    fi
else
    echo "未 provision .trellis/ref/cmsis（$HDR / $CORE 不存在）：跳过第 2 步对账" >&2
fi

echo
echo "############ 3. 交叉编译 -O2：三档睡眠在指令流里长什么样 ############"
if command -v "${ARMPREFIX}gcc" >/dev/null 2>&1; then
    echo "交叉工具链：$("${ARMPREFIX}gcc" -dumpfullversion)"
    "${ARMPREFIX}gcc" $MCU -std=c11 -Wall -Wextra -Werror -O2 -c main.c -o build/main_o2.o
    "${ARMPREFIX}objdump" -d build/main_o2.o > build/main_o2.dis

    echo "----- 代码/数据段大小（-c 只编不链，故没有链接地址） -----"
    "${ARMPREFIX}size" build/main_o2.o

    FN() { sed -n "/<$1>:/,/^\$/p" build/main_o2.dis; }
    FAIL3=0
    need() { # need 函数 正则 说明
        if FN "$1" | grep -qE "$2"; then
            echo "  [中] $1：$3"
        else
            echo "  [失] $1：$3（机身里没有 $2）" >&2; FAIL3=1
        fi
    }
    deny() { # deny 函数 正则 说明
        if FN "$1" | grep -qE "$2"; then
            echo "  [失] $1：$3（机身里居然有 $2）" >&2; FAIL3=1
        else
            echo "  [中] $1：$3"
        fi
    }
    adjacent() { # adjacent 函数 上一条正则 下一条正则 说明 —— 证明两条指令之间没插东西
        _ok=$(FN "$1" | awk -v a="$2" -v b="$3" '
            $0 ~ a { p=1; next }
            p { if ($0 ~ b) print "yes"; p=0 }' | head -1)
        if [ "$_ok" = yes ]; then
            echo "  [中] $1：$4"
        else
            echo "  [失] $1：$4（机身里 $2 后面接不上 $3）" >&2; FAIL3=1
        fi
    }

    echo "----- 三档全文：注意每档都恰好是「改 CR + 改 SCR + dsb sy + wfi」 -----"
    for F in enter_sleep enter_stop enter_standby; do FN "$F"; done

    echo "----- 每一档的两位组合（bic/orr 的立即数就是那两个位） -----"
    need enter_sleep      'bic\.w[[:space:]]+r3, r3, #4$'        'Sleep：把 SCR 的 SLEEPDEEP(bit2) 清成 0'
    deny enter_sleep      'orr\.w[[:space:]]+r0, r0,|bic\.w[[:space:]]+r0' 'Sleep：PWR_CR 读出来原样写回，中间一条修改都没有'
    need enter_stop       'bic\.w[[:space:]]+r3, r3, #2$'        'Stop：PWR_CR 清 PDDS(bit1)'
    need enter_stop       'orr\.w[[:space:]]+r3, r3, #1$'        'Stop：PWR_CR 置 LPDS(bit0)'
    need enter_stop       'orr\.w[[:space:]]+r1, r1, #4$'        'Stop：SCR 置 SLEEPDEEP(bit2)'
    need enter_standby    'bic\.w[[:space:]]+r3, r3, #1$'        'Standby：PWR_CR 清 LPDS'
    need enter_standby    'orr\.w[[:space:]]+r3, r3, #2$'        'Standby：PWR_CR 置 PDDS'
    need enter_standby    'orr\.w[[:space:]]+r1, r1, #4$'        'Standby：SCR 置 SLEEPDEEP'
    for F in enter_sleep enter_stop enter_standby; do
        adjacent $F 'dsb[[:space:]]+sy' 'wfi' "$F：dsb sy 之后紧跟 wfi，中间一条指令都没插"
        need $F 'bf30[[:space:]]+wfi'   "$F：wfi（编码 bf30，两位定档就在它前面）"
    done

    echo "----- wfi 之后还剩多少指令：Sleep 1 条、Stop 会执行、Standby 永不执行 -----"
    after_wfi() { # $1=函数名 → wfi 之后（到返回指令为止）的指令条数与字节数
        FN "$1" | awk '
            /[[:space:]]wfi[[:space:]]*$/ { seen=1; next }
            seen {
                n=0
                for (i=2; i<=NF; i++) { if ($i ~ /^[0-9a-f]{4}$/) n++; else break }
                if (n == 0) next                       # 字面量池，不是指令
                c++; b += n*2
                if ($i ~ /^(bx|pop)/) exit
            }
            END { printf "%d %d\n", c+0, b+0 }'
    }
    for F in enter_sleep enter_stop enter_standby; do
        set -- $(after_wfi "$F")
        printf '  %-14s wfi 之后 = %s 条指令 / %s 字节\n' "$F:" "$1" "$2"
    done
    need enter_stop     'movw[[:space:]]+r3, #15999'   'Stop：醒来第一件事就是重配 SysTick（HSI 16MHz 的装载值 15999）'
    need enter_stop     'str[[:space:]]+r3, \[r2, #20\]' 'Stop：那个装载值写的是 SysTick_BASE+0x14 = LOAD'
    need enter_standby  '[[:space:]]bl[[:space:]]+[0-9a-f]+[[:space:]]+<reset_cause_decode>' 'Standby：wfi 后面还有一次调用——它永远不会执行，醒来是复位'

    echo "----- 内核外设不是 STM32 地址空间：SCR/SysTick 都是 SCS_BASE 的偏移 -----"
    need enter_stop '22e0[[:space:]]+mov\.w[[:space:]]+r2, #3758153728' 'SCS_BASE = 0xE000E000 在机身里是一个立即数'
    need enter_stop '#3344\]' 'SCB->SCR 编成 [r2, #3344] = SCS+0xD10'
    # 注释符认两个：binutils 2.45 打 "; 0xd10"，2.42（CI 的 apt 工具链）打 "@ 0xd10"，
    # 要断的是「objdump 把十进制偏移还原成了可读的十六进制」这件事，不是某个版本的标点。
    need enter_stop '[@;][[:space:]]*0xd10' 'objdump 自己把这个十进制偏移还原成 0xd10'
    need enter_standby '#2164\]' 'Standby：读复位标志编成 [r3, #2164]，r3=0x40023000 → 0x40023874 = RCC_CSR（编译器把 base+0x74 合成一个偏移）'

    echo "----- 备份域解锁那五笔写，和那一个回执位 -----"
    need backup_domain_unlock '#268435456' 'RCC_APB1ENR |= PWREN（bit28）'
    need backup_domain_unlock '#256\b'      'PWR_CR |= DBP（bit8）'
    need backup_domain_unlock '#512\b'      'PWR_CSR |= BRE（bit9，备份调压器使能）'
    need backup_domain_unlock '#262144'     'RCC_AHB1ENR |= BKPSRAMEN（bit18）'
    need backup_domain_unlock '#32768'      'RCC_BDCR |= RTCEN（bit15）'
    need backup_domain_unlock 'ubfx[[:space:]]+r0, r0, #3, #1' '回执读的是 CSR bit3 = BRR（一条 ubfx 取一位）'

    echo "----- 固件本体：抠调试接口、清复位标志、醒来查的是哪两个标志 -----"
    need firmware_main 'e0042000'  'DBGMCU_BASE 0xE0042000 出现在字面量池'
    need firmware_main 'bic\.w[[:space:]]+r3, r3, #7$' 'DBGMCU_CR |= ~(DBG_SLEEP|DBG_STOP|DBG_STANDBY) 三个位一次清掉'
    need firmware_main 'orr\.w[[:space:]]+r3, r3, #16777216' 'RCC_CSR |= RMVF（bit24）清复位标志'
    need firmware_main 'lsls[[:space:]]+r1, r3, #31' '查 WUF：bit0 左移 31 位搬到符号位（和 S2 等 HSERDY 同一招）'
    need firmware_main 'lsls[[:space:]]+r2, r2, #30' '查 SBF：bit1 左移 30 位搬到符号位'
    need firmware_main 'orr\.w[[:space:]]+r3, r3, #4$' 'WUF 在 → 发 CWUF（bit2）清除动作'
    need firmware_main 'orr\.w[[:space:]]+r2, r2, #8$' 'SBF 在 → 发 CSBF（bit3）清除动作'

    [ "$FAIL3" = 0 ] || { echo "第 3 步机身断言未过——正文引用的那些反汇编结论不可信" >&2; exit 1; }

    echo "----- 两条指令的字节：dsb sy 与 wfi -----"
    grep -m1 -E 'f3bf 8f4f' build/main_o2.dis | sed 's/^/  /'
    grep -m1 -E 'bf30[[:space:]]+wfi' build/main_o2.dis | sed 's/^/  /'
    echo "  （wfi 是 32 位编码里最省的一条：bf30 两字节，纯事件类指令 T3；dsb sy 占两字 4 字节）"
else
    echo "（跳过：PATH 里没有 ${ARMPREFIX}gcc）"
fi

echo
echo "== probe.sh 全部步骤完成 =="
