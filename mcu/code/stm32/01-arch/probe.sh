#!/bin/sh
# probe.sh —— S1 位带别名取证（不需要开发板，也不需要 make）
#
#   sh probe.sh              跑全部
#   sh probe.sh bitband      别名地址：式子 → 编译期断言 → 反汇编三种写法
#   sh probe.sh clean
#
# 只需要交叉工具链在 PATH 里（或 ARM_PREFIX=/路径/arm-none-eabi-）。
# 产物落在 build/（已 gitignore）。

set -e

ARM_PREFIX=${ARM_PREFIX:-arm-none-eabi-}
CC="${ARM_PREFIX}gcc"
MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"

cd "$(dirname "$0")"
mkdir -p build

tool() {
    if command -v "${ARM_PREFIX}$1" >/dev/null 2>&1; then echo "${ARM_PREFIX}$1"; else echo "$1"; fi
}
OD=$(tool objdump)

need() {
    command -v "$CC" >/dev/null 2>&1 || {
        echo "找不到 $CC —— 先把工具链加进 PATH（见 docs/build/00-toolchain.md）" >&2
        exit 1
    }
}

bitband_probe() {
    need
    echo "----- ① 别名地址是算出来的 -----"
    echo "GPIOF_BASE=0x40021400  ODR 偏移=0x14  →  字节地址 0x40021414"
    printf '算式  0x42000000 + (0x40021414 - 0x40000000) * 32 + 6 * 4 = 0x%X\n' \
        $(( 0x42000000 + (0x40021414 - 0x40000000) * 32 + 6 * 4 ))
    echo "同一字节 8 位的别名地址（每字 4 字节，8 个字正好 32 字节）："
    i=0
    while [ $i -lt 8 ]; do
        printf '  bit%d → 0x%X\n' $i $(( 0x42000000 + (0x40021414 - 0x40000000) * 32 + i * 4 ))
        i=$((i + 1))
    done
    echo
    echo "----- ② 编译期断言：源码里的 _Static_assert 全部通过才编得下去 -----"
    "$CC" $MCU -O2 -c bb_probe.c -o build/bb_probe.o
    echo "三条 _Static_assert（ODR 地址 / PF6 别名 0x42428298 / 别名区跨度）无告警。"
    echo
    echo "----- ③ 读-改-写的窗口：|=、&=、^= 全是三条指令 -----"
    "$OD" -d --no-show-raw-insn build/bb_probe.o | sed -n '/<or_bits>:/,/<alias_set>:/p'
    echo
    echo "读法：orr/bic/eor 都夹在 ldr 与 str 中间——从读到写这段间隙里，"
    echo "任何中断改过同一个寄存器，它写回的就是**过期的那份**。"
    echo
    echo "----- ④ 一条 str 写完的两种写法 -----"
    "$OD" -d --no-show-raw-insn build/bb_probe.o | sed -n '/<alias_set>:/,$p'
    echo "alias_set 里 str.w 的偏移 0x298 加在字面量 0x42428000 上 = 0x42428298，"
    echo "与 ① 算出来的别名地址同一个数；bsrr_set 连读都没读。"
}

case "${1:-all}" in
    bitband) bitband_probe ;;
    all)     bitband_probe ;;
    clean)   rm -rf build ;;
    *)       echo "用法：sh probe.sh [bitband|clean]" >&2; exit 1 ;;
esac
