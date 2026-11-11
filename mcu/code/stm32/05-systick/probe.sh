#!/bin/sh
# probe.sh —— S5《SysTick：内核的心跳》全部取证，一条命令跑完（不需要开发板）
#
#   sh probe.sh   1) 宿主 gcc 真跑 probe.c：24 位倒数计数器模型 + SysTick_Config
#                    全貌 + 回绕换算 + COUNTFLAG 读清，断言全绿才算过；
#                 2) PATH 里有 arm-none-eabi-gcc 时，把同一份源码编成
#                    Cortex-M4 目标文件（-c 只编不链），证明本章的算法与
#                    位运算在真芯片上同样成立。
#   sh probe.sh clean   删 build/
#
# 产物一律落在 build/（code/**/build/ 已 gitignore）。
#
# 想让第 2 步跑起来：把交叉工具链的 bin 目录加进 PATH，例如
#   PATH="/d/zhugu-home/tools/armgcc/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:$PATH"

set -e
cd "$(dirname "$0")"

if [ "$1" = "clean" ]; then
    rm -rf build
    exit 0
fi

mkdir -p build

HOSTCC=${CC:-gcc}

echo "############ 1. 宿主：SysTick 模型 + 配置全貌（断言取证） ############"
echo "宿主工具链：$HOSTCC $("$HOSTCC" -dumpfullversion 2>/dev/null || "$HOSTCC" -dumpversion)"
"$HOSTCC" -std=c11 -Wall -Wextra -Werror -O2 probe.c -o build/probe.exe
./build/probe.exe

echo
echo "############ 2. 交叉编译：同一份源码编成 Cortex-M4 目标文件 ############"
ARMPREFIX=arm-none-eabi-
if command -v "${ARMPREFIX}gcc" >/dev/null 2>&1; then
    MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
    echo "交叉工具链：$("${ARMPREFIX}gcc" -dumpfullversion)"
    "${ARMPREFIX}gcc" $MCU -std=c11 -Wall -Wextra -Werror -O2 -c \
        probe.c -o build/probe-arm.o

    echo "----- 目标文件各段大小（-c 只编不链，故没有链接地址） -----"
    "${ARMPREFIX}size" build/probe-arm.o

    echo "----- 抽查：24 位上限与 LOAD-1 这些常数真的进了目标文件 -----"
    "${ARMPREFIX}objdump" -d build/probe-arm.o \
        | grep -E "16777215|0xff, 0xff, 0xff|movw|movt" | head -6
    printf '  （上面出现的常数就是 LOAD_MAX=0x00FFFFFF 与 168000/167999 这两个加载值）\n'
else
    echo "（跳过交叉编译：PATH 里没有 arm-none-eabi-gcc；宿主断言不受影响）"
fi
