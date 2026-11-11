#!/bin/sh
# probe.sh —— S2《RCC 时钟树》全部取证，一条命令跑完（不需要开发板）
#
#   sh probe.sh   1) 宿主 gcc 真跑 probe.c：probe.c 里把 RCC_PLLCFGR/RCC_CFGR
#                    改指一对假寄存器再 #include "main.c"，所以下面断言跑的是
#                    固件那几段真代码（pll_params_from_hse / flash_latency /
#                    clock_tree_readback / mco1_pre_for），不是另抄一遍算术；
#                 2) 同一份 probe.c 换个宏再跑一遍：HSE_VALUE_HZ=25MHz 而板上
#                    焊的是 8MHz，看程序怎样一声不吭地把 53.76MHz 当成 168MHz；
#                 3) PATH 里有 arm-none-eabi-gcc 时，把 main.c 编成 Cortex-M4
#                    的 -O2 目标文件并反汇编，证明源码算出来的 PLLCFGR 字
#                    0x07405408 就是落到寄存器里的那一个字。
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
MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
ARMPREFIX=arm-none-eabi-

echo "############ 1. 宿主：晶振→M/N/P/Q→等待周期→时钟树回读（断言取证） ############"
echo "宿主工具链：$HOSTCC $("$HOSTCC" -dumpfullversion 2>/dev/null || "$HOSTCC" -dumpversion)"
"$HOSTCC" -std=c11 -Wall -Wextra -Werror -O1 \
    -DHSE_VALUE_HZ=8000000UL -DBOARD_HSE_HZ=8000000UL \
    probe.c -o build/probe.exe
./build/probe.exe

echo
echo "############ 2. 宿主：把 HSE_VALUE_HZ 填成 25MHz（板上其实 8MHz） ############"
"$HOSTCC" -std=c11 -Wall -Wextra -Werror -O1 \
    -DHSE_VALUE_HZ=25000000UL -DBOARD_HSE_HZ=8000000UL \
    probe.c -o build/probe-wrongmacro.exe
./build/probe-wrongmacro.exe 6

echo
echo "############ 3. 交叉编译 -O2：反汇编看 PLLCFGR 那个字真的落地 ############"
if command -v "${ARMPREFIX}gcc" >/dev/null 2>&1; then
    echo "交叉工具链：$("${ARMPREFIX}gcc" -dumpfullversion)"
    "${ARMPREFIX}gcc" $MCU -std=c11 -Wall -Wextra -O2 \
        -DUSE_HSE_PLL=1 -DHSE_VALUE_HZ=8000000UL \
        -c main.c -o build/main_o2.o

    echo "----- 代码/数据段大小（-c 只编不链，故没有链接地址） -----"
    "${ARMPREFIX}size" build/main_o2.o

    echo "----- 汇编里那一次对 RCC_PLLCFGR（偏移 0x804）的写入 -----"
    "${ARMPREFIX}objdump" -d build/main_o2.o \
        | grep -E "str.*\[.*#2052|0x804" | head -4

    echo "----- literal pool：源码算出的 M=8/N=336/P=/2/Q=7 = 0x07405408 -----"
    "${ARMPREFIX}objdump" -d build/main_o2.o | grep -E "07405408" | head -2
    printf '  （0x07405408 = Q7<<24 | SRC<<22 | P0<<16 | N336<<6 | M8，与 probe.c 第 2 节的断言同一个字）\n'

    echo "----- 提频顺序在指令流里的样子：先 HSEON，再等 HSERDY，再写 PLLCFGR -----"
    "${ARMPREFIX}objdump" -d build/main_o2.o \
        | grep -E "65536|131072|#2052|16777216" | head -6
    printf '  （65536=HSEON bit16，131072=HSERDY bit17，#2052=RCC_PLLCFGR 偏移 0x804，16777216=PLLON bit24）\n'
else
    echo "（跳过：PATH 里没有 ${ARMPREFIX}gcc）"
fi
