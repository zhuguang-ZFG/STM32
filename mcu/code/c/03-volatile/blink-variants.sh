#!/bin/sh
# blink-variants.sh —— 把 00-blink 的 main.c 拆成六个 volatile 变体，逐个出 -O2 汇编
#
#   用法：sh blink-variants.sh [path/to/00-blink]     （默认 ../../stm32/00-blink）
#   依赖：arm-none-eabi-gcc + arm-none-eabi-objdump
#
# 每个变体只改"少哪一处 volatile"，其余完全相同；输出 main 的反汇编前 12 条指令。
# 正文 C3 第五节的六行对照表就是这里跑出来的（引证环境见 README"本机实测记录"）。

SRC=${1:-../../stm32/00-blink/main.c}
CC=${CC:-arm-none-eabi-gcc}
OBJDUMP=${OBJDUMP:-arm-none-eabi-objdump}
MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
CFLAGS="-std=c11 -Wall -Wextra -O2"
OUT=blink-variants

[ -f "$SRC" ] || { echo "找不到 $SRC（第一个参数传 00-blink 目录或 main.c 路径）"; exit 1; }
command -v "$CC" >/dev/null || { echo "找不到 $CC，先装 ARM 工具链"; exit 1; }

rm -rf $OUT && mkdir -p $OUT
base=$(basename "$SRC")

# 变体定义：V=寄存器宏的 volatile，D=delay 参数的 volatile，N=循环体里的 asm nop
mk() { # $1=名字 $2=宏volatile(y/n) $3=参数volatile(y/n) $4=nop(y/n)
    cp "$SRC" "$OUT/$1.c"
    [ "$2" = n ] && sed -i 's/\*(volatile uint32_t \*)/\*(uint32_t \*)/g' "$OUT/$1.c"
    [ "$3" = n ] && sed -i 's/delay(volatile uint32_t count)/delay(uint32_t count)/' "$OUT/$1.c"
    [ "$4" = n ] && sed -i 's/__asm__ volatile ("nop");/;   \/* nop 已删 *\//' "$OUT/$1.c"
    $CC $MCU $CFLAGS -c "$OUT/$1.c" -o "$OUT/$1.o" || return 1
    echo "======== $1 （宏volatile=$2 参数volatile=$3 nop=$4）========"
    $OBJDUMP -d --no-show-raw-insn "$OUT/$1.o" | sed -n '/<main>:/,$p' | sed -n '2,13p'
    echo
}

mk A y y y   # 仓库现状
mk B y n y   # 只去掉 delay 参数的 volatile
mk C y n n   # 再去掉 nop：延时整个消失
mk D y y n   # 只去掉 nop，参数仍 volatile
mk F n y y   # 只把寄存器宏的 volatile 去掉
mk E n n n   # 三处全去

echo "产物在 $OUT/，改 -O 档：CFLAGS 自己加 -O0/-O1/-O3 重跑即可。"
