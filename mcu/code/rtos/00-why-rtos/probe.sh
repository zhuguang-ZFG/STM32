#!/bin/sh
# probe.sh —— F0《为什么需要 RTOS》全部取证，一条命令跑完
#
#   sh probe.sh          1) 宿主机跑"阻塞版"与"改良版"超级循环：同一张事件脚本，量 LED 迟到与丢键；
#                        2) 同一份 2 ms 的活只挪一行：burn-head / burn-tail，量"行序当优先级"的价目表；
#                        3) 交叉反汇编：同一份 superloop.c 落到 Cortex-M4 真寄存器上，数每个任务本体几条指令；
#                        4) 元凶本体：那句 while (!(USART2_SR & RXNE)) 在 -O0 / -O2 下各长什么样。
#   sh probe.sh clean    删 build/
#
# 四档共用 board_host.c 里写死的那张事件脚本表，所以几份报告可以逐行并排比。
# 产物一律落在 build/（code/**/build/ 已 gitignore）。
#
# 第 3、4 步需要交叉工具链。本机装了 xpack 15.2.1 就钉它，没装退回 PATH 里默认那把：
#   ARM_PREFIX=/path/to/arm-none-eabi- sh probe.sh
#
# 宿主机那两步每档连跑几局（REPS，默认 5）。宿主机不是真板，宿主 OS 会随机抢走
# 十几毫秒，单局读数是抽奖；跨局中位数才是能写进章里、印到屏幕上的数。
#   REPS=1 sh probe.sh    只看一局（快，但别引用它的"最坏迟到"）
#   REPS=8 sh probe.sh    更稳的中位数

set -e
cd "$(dirname "$0")"

XPACK=${XPACK:-/d/zhugu-home/tools/armgcc/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin}
[ -d "$XPACK" ] && PATH="$XPACK:$PATH"
REPS=${REPS:-5}

if [ "$1" = "clean" ]; then
    rm -rf build
    exit 0
fi

mkdir -p build

HOSTCC=${CC:-gcc}
COMMON="-std=c11 -Wall -Wextra -Werror"

echo "############ 1. 阻塞版 vs 改良版：元凶就是那一句死等 ############"
echo "宿主工具链：$HOSTCC $("$HOSTCC" -dumpfullversion 2>/dev/null || "$HOSTCC" -dumpversion)"
echo "每档连跑 $REPS 局：宿主机不是真板，宿主 OS 随时能抢走十几毫秒，"
echo "单局的\"最坏迟到\"能差一个数量级——只认跨局中位数（REPS=1 可退回单局）"
"$HOSTCC" $COMMON -O2 main_host.c superloop.c board_host.c -o build/f0.exe
./build/f0.exe block $REPS
./build/f0.exe poll $REPS

echo
echo "############ 2. 等待治好了，优先级还是没有：2 ms 的活摆第一行 / 最后一行 ############"
./build/f0.exe burn-head $REPS
./build/f0.exe burn-tail $REPS

echo
echo "############ 3. 交叉侧：同一份任务代码在 Cortex-M4 上是多少条指令 ############"
ARMPREFIX=${ARM_PREFIX:-arm-none-eabi-}
if command -v "${ARMPREFIX}gcc" >/dev/null 2>&1; then
    MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
    echo "交叉工具链：$("${ARMPREFIX}gcc" -dumpfullversion)；主频按本工程 configCPU_CLOCK_HZ = 16 MHz（HSI，不启 PLL）"
    "${ARMPREFIX}gcc" $MCU $COMMON -O2 -DBOARD_ARM -c superloop.c -o build/superloop-arm.o
    "${ARMPREFIX}objdump" -d --no-show-raw-insn build/superloop-arm.o > build/superloop-arm.objdump

    for fn in led_tick key_scan uart_echo uart_poll superloop_block superloop_poll; do
        echo "----- $fn -----"
        awk -v f="$fn" '$0 ~ "<"f">:"{p=1} p&&NF==0{exit} p{print}' build/superloop-arm.objdump \
            > build/fn.txt || true
        if [ -s build/fn.txt ]; then
            sed 's/^/  /' build/fn.txt
            echo "  → 指令条数：$(grep -cE '^[[:space:]]+[0-9a-f]+:' build/fn.txt)"
        else
            echo "  （目标文件里没有这个符号）"
        fi
    done
else
    echo "（跳过交叉取证：PATH 里没有 ${ARMPREFIX}gcc；宿主机实测不受影响）"
fi

echo
echo "############ 4. 元凶本体：死等 RXNE 那三行在两种优化档下 ############"
if command -v "${ARMPREFIX}gcc" >/dev/null 2>&1; then
    MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
    "${ARMPREFIX}gcc" $MCU -std=c11 -Wall -Wextra -O0 -DBOARD_ARM -c superloop.c -o build/superloop-arm-o0.o
    "${ARMPREFIX}objdump" -d --no-show-raw-insn build/superloop-arm-o0.o > build/superloop-arm-o0.objdump
    echo "----- -O0 uart_echo：死等就在 bl board_uart_getc 之后的板级函数里 -----"
    awk '/<uart_echo>:/{p=1} p&&NF==0{exit} p{print}' build/superloop-arm-o0.objdump || true
    echo "----- -O0 board_uart_getc：bfc 测试 + 原地 b 回跳，字节不来就永远在这两条里 -----"
    awk '/<board_uart_getc>:/{p=1} p&&NF==0{exit} p{print}' build/superloop-arm-o0.objdump || true
    echo "----- -O2 uart_echo：整个 while 被内联成任务体尾部的自旋，没有一条出口 -----"
    awk '/<uart_echo>:/{p=1} p&&NF==0{exit} p{print}' build/superloop-arm.objdump || true
fi
