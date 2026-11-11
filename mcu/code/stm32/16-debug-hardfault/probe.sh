#!/bin/sh
# probe.sh —— S16 章全部取证，一条命令跑完（不需要开发板）
#
#   sh probe.sh         1) 宿主 gcc 编译运行 probe.c（断言全绿退出 0）；
#                       2) 位号与 CMSIS 官方头文件逐位对账（diff 必须为空）；
#                       3) PATH 里有 arm-none-eabi-gcc 时，附送 naked
#                          HardFault_Handler 反汇编 + PC→addr2line→源码行全链路，
#                          外加三具"尸体"与 fault_demo_entry 的完整机身断言；
#                       4) 条件指令的字节学：ite/mrs 谁带条件、MSP↔PSP 差哪一位，
#                          以及两种写错的写法被 GAS 拒绝的原文。
#   sh probe.sh clean   删 build/
#
# 产物一律落在 build/（code/**/build/ 已 gitignore）。
#
# 想让第 3 步跑起来：把交叉工具链的 bin 目录加进 PATH，例如
#   PATH="/d/zhugu-home/tools/armgcc/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:$PATH"

set -e
cd "$(dirname "$0")"

if [ "$1" = "clean" ]; then
    rm -rf build
    exit 0
fi

mkdir -p build

HOSTCC=${CC:-gcc}
CMSIS=../../../.trellis/ref/cmsis/core_cm4.h

echo "############ 1. 宿主：故障寄存器解码 + 栈帧选择（断言取证） ############"
echo "宿主工具链：$HOSTCC $("$HOSTCC" -dumpfullversion 2>/dev/null || "$HOSTCC" -dumpversion)"
"$HOSTCC" -std=c11 -Wall -Wextra -Werror -O2 probe.c -o build/probe.exe
./build/probe.exe

echo
echo "############ 2. 位号逐位对账：本文件的表 vs CMSIS 官方头文件 ############"
if [ -f "$CMSIS" ]; then
    ./build/probe.exe --dump-positions | sort > build/pos-probe.txt
    awk '
      /^#define SCB_CFSR_MEMFAULTSR_Pos/ { m = $3 + 0 }
      /^#define SCB_CFSR_BUSFAULTSR_Pos/  { b = $3 + 0 }
      /^#define SCB_CFSR_USGFAULTSR_Pos/  { u = $3 + 0 }
      /^#define SCB_CFSR_[A-Z]+_Pos/ {
        name = $2; sub(/^SCB_CFSR_/, "", name); sub(/_Pos$/, "", name)
        rest = $0
        if      (name == "MEMFAULTSR") v = m
        else if (name == "BUSFAULTSR") v = b
        else if (name == "USGFAULTSR") v = u
        else if (rest ~ /MEMFAULTSR_Pos/) v = m
        else if (rest ~ /BUSFAULTSR_Pos/) v = b
        else if (rest ~ /USGFAULTSR_Pos/) v = u
        else v = 0
        if (match(rest, /\+ *[0-9]+U/)) {
          t = substr(rest, RSTART, RLENGTH); gsub(/[^0-9]/, "", t); v += t + 0
        }
        printf "CFSR:%s %d\n", name, v
      }
      /^#define SCB_SHCSR_[A-Z]+_Pos/ {
        name = $2; sub(/^SCB_SHCSR_/, "", name); sub(/_Pos$/, "", name)
        t = $3; gsub(/[^0-9]/, "", t)
        printf "SHCSR:%s %d\n", name, t + 0
      }
      /^#define SCB_HFSR_[A-Z]+_Pos/ {
        name = $2; sub(/^SCB_HFSR_/, "", name); sub(/_Pos$/, "", name)
        t = $3; gsub(/[^0-9]/, "", t)
        printf "HFSR:%s %d\n", name, t + 0
      }
    ' "$CMSIS" | sort > build/pos-header.txt

    echo "头文件：$CMSIS"
    echo "  头文件侧 $(wc -l < build/pos-header.txt) 条位号，本章侧 $(wc -l < build/pos-probe.txt) 条位号"
    # Windows 下的 probe.exe 输出 CRLF，awk 输出 LF——对账前统一成 LF
    tr -d '\r' < build/pos-header.txt > build/pos-header.norm
    tr -d '\r' < build/pos-probe.txt > build/pos-probe.norm
    if diff -u build/pos-header.norm build/pos-probe.norm > build/pos.diff; then
        echo "  ----- 对账结果：逐位一致（$(wc -l < build/pos-header.txt) 条全中） -----"
    else
        echo "  ----- 对账结果：不一致！上面这些位号不可信 -----"
        cat build/pos.diff
        exit 1
    fi
else
    echo "（跳过对账：找不到 $CMSIS）"
fi

echo
echo "############ 3. 反汇编：naked HardFault_Handler 怎么选栈指针 ############"
ARMPREFIX=arm-none-eabi-
if command -v "${ARMPREFIX}gcc" >/dev/null 2>&1; then
    MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
    echo "交叉工具链：$("${ARMPREFIX}gcc" -dumpfullversion)"
    "${ARMPREFIX}gcc" $MCU -std=c11 -Wall -Wextra -Werror -O0 -g3 \
        -nostdlib -Wl,--entry=fault_demo_entry -Wl,-Ttext=0x08000000 \
        -Wl,-Map=build/fault_ctx.map \
        fault_ctx.c -o build/fault_ctx.elf
    "${ARMPREFIX}objdump" -d build/fault_ctx.elf > build/fault_ctx.dis

    echo "----- HardFault_Handler 全文（tst lr,#4 → mrs msp|psp） -----"
    sed -n '/<HardFault_Handler>:/,/^$/p' build/fault_ctx.dis

    echo "----- .text 落址（Flash 0x08000000，对照 B1 的链接四步） -----"
    "${ARMPREFIX}objdump" -h build/fault_ctx.elf | grep -E '^ +[0-9]+ \.text ' || true

    echo "----- 三具尸体的符号地址 -----"
    "${ARMPREFIX}nm" build/fault_ctx.elf | grep -E ' (crash_null|crash_unaligned|crash_divzero|HardFault_Handler|hardfault_report)$' || true

    ADDR=$("${ARMPREFIX}nm" build/fault_ctx.elf | awk '/ crash_null$/{print $1; exit}')
    FAULT=$("${ARMPREFIX}objdump" -d build/fault_ctx.elf \
            | sed -n '/<crash_null>:/,/^$/p' \
            | awk '/[[:space:]]str[[:space:]]/{a=$1; sub(/:$/,"",a); print a; exit}')
    [ -n "$FAULT" ] || { echo "未在 crash_null 内找到 str 指令——取证段失效" >&2; exit 1; }
    echo "----- 法医全链路：nm 给的是函数入口，栈里的 PC 才是真凶指令 -----"
    echo "crash_null 入口    = 0x$ADDR（nm 给的，指向函数第一行）"
    "${ARMPREFIX}addr2line" -e build/fault_ctx.elf -f "0x$ADDR"
    echo "crash_null 的 str  = 0x$FAULT（反汇编找的，HardFault 时栈帧里躺的就是它）"
    "${ARMPREFIX}addr2line" -e build/fault_ctx.elf -f "0x$FAULT"

    echo "----- 三具尸体 + 入口：完整机身（正文引用的每一段反汇编都出自这里） -----"
    for FN in crash_null crash_unaligned crash_divzero fault_demo_entry; do
        sed -n "/<${FN}>:/,/^\$/p" build/fault_ctx.dis
    done

    echo "----- map 文件交叉验证（同一地址的另一个出处） -----"
    grep -E 'crash_null' build/fault_ctx.map | head -2

    echo
    echo "----- 机身断言：五虎里那两具『死不了的尸体』，凭机器码说话 -----"
    SEC() { sed -n "/<$1>:/,/^\$/p" build/fault_ctx.dis; }
    FAIL4=0
    chk() {  # chk 说明 grep-pattern 反相(1=必须命中)
        if SEC "$1" | grep -qE "$2"; then H=1; else H=0; fi
        if [ "$H" = "$3" ]; then
            echo "  [中] $1：$2"
        else
            echo "  [失] $1：$2（期望命中=$3，实际=$H）" >&2
            FAIL4=1
        fi
    }
    # 命案前提：CCR 的两个 trap 位（UNALIGN_TRP bit3 | DIV_0_TRP bit4 = 24）
    chk fault_demo_entry 'orr[^[:space:]]*[[:space:]]+r3,[[:space:]]+r3,[[:space:]]+#24$' 1
    chk fault_demo_entry '0xe000ed14' 1
    # 命案本身
    chk crash_null       'str[[:space:]]' 1
    chk crash_divzero    'sdiv' 1
    # 关键否定证据：除零那段里没有陷阱、也没有分支——它就是一条普通算术指令
    chk crash_divzero    '[[:space:]](bl|b\.[a-z]+|udf|bkpt|svc)[[:space:]]' 0
    if [ "$FAIL4" = 1 ]; then echo "机身断言未过——正文里那几条结论不可信" >&2; exit 1; fi

    # 未对齐那具：literal pool 里的地址必须是奇地址，且机身只有普通 str
    ODDFOUND=0
    for W in $(SEC crash_unaligned | grep -oE '\.word[[:space:]]+0x[0-9a-f]+' | grep -oE '[0-9a-f]{8}$'); do
        case "$W" in
            *1|*3|*5|*7|*9|*b|*d|*f) ODDFOUND=1; ODDLIT="0x$W" ;;
        esac
    done
    if [ "$ODDFOUND" = 1 ]; then
        echo "  [中] crash_unaligned 的字面量池里躺着奇地址 $ODDLIT（末位是奇数），机身仍是普通 str"
    else
        echo "  [失] crash_unaligned 里没找到奇地址字面量" >&2; exit 1
    fi

    echo
    echo "############ 4. 条件指令的字节学：ite 带条件，mrs 不带 ############"
    # 正确版 vs "两行都写 msp" 的笔误版——整段 handler 只差一个字节
    for V in psp msp; do
        {
            printf '    .syntax unified\n    .thumb\n    .text\n    .global h_%s\nh_%s:\n' "$V" "$V"
            printf '    tst   lr, #4\n    ite   eq\n    mrseq r0, msp\n'
            if [ "$V" = psp ]; then printf '    mrsne r0, psp\n'; else printf '    mrsne r0, msp\n'; fi
            printf '    bx    lr\n'
        } > "build/enc_$V.s"
        "${ARMPREFIX}gcc" $MCU -c "build/enc_$V.s" -o "build/enc_$V.o"
        "${ARMPREFIX}objcopy" -O binary "build/enc_$V.o" "build/enc_$V.bin"
        echo "----- $([ "$V" = psp ] && echo '正确版（ne 槽取 PSP）' || echo '笔误版（ne 槽仍写 msp）') -----"
        "${ARMPREFIX}objdump" -d "build/enc_$V.o" | sed -n "/<h_$V>:/,/^\$/p"
    done
    cmp -l build/enc_psp.bin build/enc_msp.bin > build/enc.diff || true
    NDIFF=$(grep -c . build/enc.diff || true)
    echo "----- 两份机身逐字节对比（cmp -l 给的是 octal） -----"
    echo "  正确版 hex: $(od -An -tx1 -v build/enc_psp.bin | tr -s ' ' | tr -d '\n ')"
    echo "  笔误版 hex: $(od -An -tx1 -v build/enc_msp.bin | tr -s ' ' | tr -d '\n ')"
    echo "  差异字节数 = $NDIFF，明细：$(tr '\n' ' ' < build/enc.diff)"
    [ "$NDIFF" = 1 ] || { echo "断言失败：两版应只差 1 个字节，实测 $NDIFF" >&2; exit 1; }
    VALS=$(awk 'NR==1{print $2, $3}' build/enc.diff)
    [ "$VALS" = "11 10" ] || { echo "断言失败：那一个字节应是 PSP=0x09(octal 11) → MSP=0x08(octal 10)，实测 [$VALS]" >&2; exit 1; }
    echo "  ----- 结论：PSP(0x09) 与 MSP(0x08) 只差 imm5 的 bit0——一个位，RTOS 下就从「PSP」变成「永远读 MSP」 -----"

    echo
    echo "----- MRS 编码矩阵：Rd 在 bits[11:8]，源寄存器在 imm5 -----"
    cat > build/mrs_matrix.s <<'ASM'
    .syntax unified
    .thumb
    .text
m_rd0:  tst lr, #4
    ite eq
    mrseq r0, msp
    mrsne r0, msp
    bx  lr
m_rd1:  tst lr, #4
    ite eq
    mrseq r1, msp
    mrsne r1, msp
    bx  lr
m_rd12: tst lr, #4
    ite eq
    mrseq r12, msp
    mrsne r12, msp
    bx  lr
m_psp:  tst lr, #4
    ite eq
    mrseq r0, psp
    mrsne r0, psp
    bx  lr
m_apsr: tst lr, #4
    ite eq
    mrseq r0, apsr
    mrsne r0, apsr
    bx  lr
ASM
    "${ARMPREFIX}gcc" $MCU -c build/mrs_matrix.s -o build/mrs_matrix.o
    "${ARMPREFIX}objdump" -d build/mrs_matrix.o | grep -E '[[:space:]]mrs' | sed 's/^/  /'
    MDIS=$("${ARMPREFIX}objdump" -d build/mrs_matrix.o)
    for NEED in 'f3ef 8008.*MSP' 'f3ef 8009.*PSP' 'f3ef 8c08.*MSP' 'f3ef 8000.*CPSR'; do
        echo "$MDIS" | grep -qE "$NEED" \
            || { echo "断言失败：编码矩阵缺 $NEED" >&2; exit 1; }
        echo "  [中] $NEED"
    done
    echo "  ----- 结论：eq 槽与 ne 槽的两个词字节完全相同——条件根本不在 mrs 里，它只在 ite(bf0c) 那个词里 -----"

    echo
    echo "----- 三种『想写错』：两种被 GAS 当场拒绝（原文照抄），一种它照收不误 -----"
    # 正对照：把 psp 放进 eq 槽、msp 放进 ne 槽——条件后缀合法，GAS 收了，语义整反
    cat > build/bad_slot.s <<'ASM'
    .syntax unified
    .thumb
    .text
bad_slot:
    tst   lr, #4
    ite   eq
    mrseq r0, psp
    mrsne r0, msp
    bx    lr
ASM
    if "${ARMPREFIX}gcc" $MCU -c build/bad_slot.s -o build/bad_slot.o 2>build/bad_slot.err; then
        echo "  [bad_slot 放行] eq 槽写成 psp、ne 槽写成 msp：GAS 一声不吭，语义整反"
        "${ARMPREFIX}objdump" -d build/bad_slot.o | sed -n '/<bad_slot>:/,/^$/p' | sed 's/^/    /'
    else
        echo "断言失败：bad_slot.s 条件后缀是合法的，GAS 不该拒它" >&2
        cat build/bad_slot.err >&2
        exit 1
    fi
    # 拒绝 1：照实物实验那条改法——只把 mrsne 改成 mrseq
    cat > build/bad_cond.s <<'ASM'
    .syntax unified
    .thumb
    .text
bad_cond:
    tst   lr, #4
    ite   eq
    mrseq r0, msp
    mrseq r0, psp
    bx    lr
ASM
    cat > build/bad_noite.s <<'ASM'
    .syntax unified
    .thumb
    .text
bad_noite:
    tst   lr, #4
    mrsne r0, psp
    bx    lr
ASM
    for BAD in bad_cond bad_noite; do
        if "${ARMPREFIX}gcc" $MCU -c "build/$BAD.s" -o "build/$BAD.o" 2> "build/$BAD.err"; then
            echo "断言失败：GAS 竟然收了 $BAD.s——正文里『工具链会拒绝』的说法不成立" >&2
            exit 1
        fi
        echo "  [$BAD 拒绝] $(grep -m1 -o 'Error:.*' "build/$BAD.err")"
    done
    echo "  ----- 所以真正的坑不是工具链拦得住的那种，是上面那个它照收不误的：一个位，语义整反 -----"
else
    echo "（跳过反汇编：PATH 里没有 arm-none-eabi-gcc；宿主断言不受影响）"
fi
