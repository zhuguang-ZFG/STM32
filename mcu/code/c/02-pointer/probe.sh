#!/bin/sh
# probe.sh —— C2《指针》章全部取证，一条命令跑完（不需要开发板）
#
#   sh probe.sh          跑全部
#   sh probe.sh asm      现场1/2/3：arm-none-eabi-gcc -O2 -S 汇编取证 + 现场3 的 objdump 补刀
#   sh probe.sh run      现场2/3/4：宿主 gcc 真跑
#   sh probe.sh const    const 反例：三个「必须编译失败」的取证
#   sh probe.sh clean
#
# 汇编取证用 arm-none-eabi-*（xPack 不在 PATH 时本脚本自动垫上，可用 ARM_PREFIX 覆盖）；
# 运行取证用宿主 gcc（可用 HOST_CC 覆盖）。产物一律落在 build/。

set -e
cd "$(dirname "$0")"

XPACK=/d/zhugu-home/tools/armgcc/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin
[ -d "$XPACK" ] && PATH="$XPACK:$PATH"
ARM_PREFIX=${ARM_PREFIX:-arm-none-eabi-}
ACC="${ARM_PREFIX}gcc"
HCC=${HOST_CC:-gcc}
MCU="-mcpu=cortex-m4 -mthumb"
CFLAGS="-std=c11 -Wall -Wextra -O2"

mkdir -p build

# show_fn <file.s> <函数名>：打印该函数的标签到返回指令为止
show_fn() {
    awk -v fn="$2:" '
        index($0, fn) == 1 { inf = 1 }
        inf { print }
        inf && ($1 == "bx" || $1 == "ret" || $1 == "pop") { exit }
    ' "$1"
}

do_asm() {
    echo "== 交叉工具链 =="
    "$ACC" --version | head -1
    echo "== 命令行: $ACC $CFLAGS $MCU -S probe.c -o build/probe.m4.s =="
    "$ACC" $CFLAGS $MCU -S probe.c -o build/probe.m4.s
    echo
    echo "-- 现场1 读：uint8_t*/uint16_t*/uint32_t* 解引用 --"
    for f in read8 read16 read32;   do show_fn build/probe.m4.s "$f"; echo; done
    echo "-- 现场1 写：三种宽度的赋值 --"
    for f in write8 write16 write32; do show_fn build/probe.m4.s "$f"; echo; done
    echo "-- 现场2：p[1]（= *(p+1)）的地址增量 --"
    for f in next8 next16 next32;   do show_fn build/probe.m4.s "$f"; echo; done
    echo "-- 现场3：BSRR 两种写法（索引 vs 宏）--"
    show_fn build/probe.m4.s led_on_indexed
    echo
    show_fn build/probe.m4.s led_on_macro
    echo
    echo "（_Static_assert 已随上面编译通过：6*sizeof(uint32_t)==0x18）"

    # 汇编文本里的 .L12 只是一个标号，真正的字面量要连机器码一起编出来才看得见。
    # 这一步把同一份源码 -c 成 .o（分段，好单独反汇编），再看 led_on_indexed 的全貌。
    echo
    echo "-- 现场3 补一刀：那个 .L12 里装的到底是什么（-c + objdump）--"
    echo "== 命令行: $ACC $CFLAGS $MCU -ffunction-sections -c probe.c -o build/probe.o =="
    "$ACC" $CFLAGS $MCU -ffunction-sections -c probe.c -o build/probe.o
    "${ARM_PREFIX}objdump" -d --no-show-raw-insn build/probe.o \
        | awk '/<led_on_indexed>:/{p=1} p&&NF==0{exit} p' | tee build/led_on_indexed.dis
    grep -qE 'str\.?[w]?\s+r2, \[r3, #1048\][[:space:]]*@ 0x418' build/led_on_indexed.dis \
        || { echo "!! 没看到那条 [r3, #1048] 的 str —— 编译器换了拆法，本章数字要重核"; exit 1; }
    grep -qE '\.word[[:space:]]+0x40021000' build/led_on_indexed.dis \
        || { echo "!! 字面量池里不是 0x40021000 —— 本章「地址被拆成两段」的说法要重核"; exit 1; }
    echo "（两条都到位：0x40021000 + 0x418 = 0x40021418，就是片头那个地址）"
}

do_run() {
    echo "== 宿主工具链 =="
    "$HCC" --version | head -1
    echo "== 命令行: $HCC $CFLAGS probe.c -o build/probe_host.exe && ./build/probe_host.exe =="
    "$HCC" $CFLAGS probe.c -o build/probe_host.exe
    ./build/probe_host.exe
}

expect_fail() {  # expect_fail <宏> <说明>
    if "$HCC" $CFLAGS -D"$1" -c probe.c -o build/bad.o 2> build/err.txt; then
        echo "!! $2 居然编译通过 —— 取证失败"; exit 1
    fi
    echo "-- $2：如期编译失败 --"
    grep -m1 "error" build/err.txt
    echo
}

do_const() {
    expect_fail BAD_WRITE_THROUGH_CONST_P "const int *p：*p = 1"
    expect_fail BAD_REPOINT_CONST_PTR     "int * const p：p = &b"
    expect_fail BAD_BOTH_CONST            "const int * const p：*p = 1"
    echo "（以上三条全是编译期拦截：const 不要钱，跑都不用跑）"
}

case "${1:-all}" in
    asm)   do_asm ;;
    run)   do_run ;;
    const) do_const ;;
    clean) rm -rf build ;;
    all)   do_asm; echo; do_run; echo; do_const ;;
    *) echo "用法: sh probe.sh [asm|run|const|clean|all]" >&2; exit 2 ;;
esac
