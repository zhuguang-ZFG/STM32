#!/bin/sh
# probe.sh —— C5 章全部取证，一条命令跑完（不需要开发板）
#
#   sh probe.sh         宿主 gcc 编译运行 probe.c（断言全绿退出 0）；
#                       PATH 里有 arm-none-eabi-gcc 时，附送 Cortex-M4 反汇编（找 blx）
#   sh probe.sh clean
#
# 产物一律落在 build/（code/**/build/ 已 gitignore）。

set -e
cd "$(dirname "$0")"
mkdir -p build

HOSTCC=${CC:-gcc}

echo "############ 1. 宿主编译并运行（断言取证） ############"
echo "宿主工具链：$HOSTCC $("$HOSTCC" -dumpfullversion 2>/dev/null || "$HOSTCC" -dumpversion)"
"$HOSTCC" -std=c11 -Wall -Wextra -Werror -O2 probe.c -o build/probe.exe
./build/probe.exe

ARMPREFIX=arm-none-eabi-
if command -v "${ARMPREFIX}gcc" >/dev/null 2>&1; then
    echo
    echo "############ 2. 交叉反汇编：函数指针的调用长什么样 ############"
    MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
    echo "交叉工具链：$("${ARMPREFIX}gcc" -dumpfullversion)"
    "${ARMPREFIX}gcc" $MCU -std=c11 -Wall -Wextra -Werror -O2 -c probe.c -o build/probe.m4.o
    "${ARMPREFIX}objdump" -d build/probe.m4.o > build/probe.m4.s
    echo "----- fsm_feed 反汇编全文（查表 + 间接调用） -----"
    sed -n '/<fsm_feed>:/,/^$/p' build/probe.m4.s
    echo "----- 全文件里的间接调用指令（blx = 跳到寄存器里的地址） -----"
    grep -n 'blx' build/probe.m4.s
else
    echo
    echo "（跳过反汇编：PATH 里没有 arm-none-eabi-gcc；宿主断言不受影响）"
fi
