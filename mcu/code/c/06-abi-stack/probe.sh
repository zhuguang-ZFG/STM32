#!/bin/sh
# probe.sh —— C6《调用约定与栈帧》全部取证，一条命令跑完
#
#   sh probe.sh   1) 宿主 gcc 真跑 probe.c（打印活的 sp/参数落位，断言全绿）；
#                 2) PATH 里有 arm-none-eabi-gcc 时，-O2 -S 编出汇编，
#                    核对 AAPCS 的三条铁律：参数 r0-r3、第 5 个参数走栈、
#                    64 位参数占偶奇寄存器对、非叶子函数 push {r4, lr}/pop {r4, pc}。
#   sh probe.sh clean   删 build/
#
# 产物一律落在 build/（code/**/build/ 已 gitignore）。
#
# 想让第 2 步跑起来：把交叉工具链的 bin 目录加进 PATH，例如
#   PATH="/d/zhugu-home/tools/armgcc/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:$PATH"
# 本机 PATH 里默认那把是 10.3.1，章内/片内引用的汇编就是它跑的（第 38 行会打印版本号）。
# 两把都对，只是寄存器分配不同形：sum6 取第 5 个参数，15.2.1 给 ldr r1, [sp]，10.3.1 给 ldr r2, [sp]。
# AAPCS 只承诺"第 5 个起在栈上 [sp]/[sp,#4]"，用哪个寄存器接是编译器的自由。

set -e
cd "$(dirname "$0")"

if [ "$1" = "clean" ]; then
    rm -rf build
    exit 0
fi

mkdir -p build

HOSTCC=${CC:-gcc}

echo "############ 1. 宿主：活的栈布局（断言取证） ############"
echo "宿主工具链：$HOSTCC $("$HOSTCC" -dumpfullversion 2>/dev/null || "$HOSTCC" -dumpversion)"
"$HOSTCC" -std=c11 -Wall -Wextra -Werror -O2 probe.c -o build/probe.exe
./build/probe.exe
echo "  （上面每一条都是真跑出来的数：sp 实差、buf 实址、第 5 参数确实经栈传递）"

echo
echo "############ 2. 交叉汇编：AAPCS 三条铁律 vs 真实代码 ############"
ARMPREFIX=arm-none-eabi-
if command -v "${ARMPREFIX}gcc" >/dev/null 2>&1; then
    MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
    echo "交叉工具链：$("${ARMPREFIX}gcc" -dumpfullversion)"
    "${ARMPREFIX}gcc" $MCU -std=c11 -Wall -Wextra -Werror -O2 -S \
        probe.c -o build/probe.s

    echo "----- 叶子函数 add2：没调用任何人 → 不 push lr -----"
    sed -n '/^add2:/,/\.size[[:space:]]*add2/p' build/probe.s | grep -E "add|bx|^add2:|link register" || true

    echo "----- sum6：前 4 个参数 r0-r3；第 5、6 个由调用方 str 上栈 -----"
    sed -n '/^sum6:/,/\.size[[:space:]]*sum6/p' build/probe.s | head -14

    echo "----- sum6 调用方：bl sum6 之前的 8 条（第 5、6 个参数走 strd） -----"
    sed -n '/^main:/,/\.size[[:space:]]*main/p' build/probe.s \
        | awk '/bl[[:space:]]+sum6/{exit} {print}' | tail -8

    echo "----- add64：64 位参数占偶奇寄存器对（r0:r1 / r2:r3） -----"
    sed -n '/^add64:/,/\.size[[:space:]]*add64/p' build/probe.s | head -10

    echo "----- mix(int, long long)：64 位必须落在偶数寄存器 → r1 被跳过 -----"
    echo "  [被调方] 只读 r0（tag）与 r2:r3（v），从没读入参 r1；r1 只作 64 位返回值的高半："
    sed -n '/^mix:/,/\.size[[:space:]]*mix/p' build/probe.s | grep -E "r0|r1|r2|r3|bx" | grep -v "^\s*@" || true
    echo "  [调用方] r0=tag，r2:r3=v（注意 r1 压根没被赋值）——这就是「跳过 r1」："
    sed -n '/^main:/,/\.size[[:space:]]*main/p' build/probe.s \
        | awk '/bl[[:space:]]+add64/{f=1;next} /bl[[:space:]]+mix/{exit} f' \
        | grep -E "movs?[[:space:]]+r[0-3]," || true

    echo "----- 非叶子 non_leaf：push {r4, lr} … pop {r4, pc}（返回地址直接弹进 PC） -----"
    sed -n '/^non_leaf:/,/\.size[[:space:]]*non_leaf/p' build/probe.s | grep -E "push|pop|sub[[:space:]]+sp|bl[[:space:]]" | head -8

    echo "----- 计数核对（与章内"铁律"逐条对照） -----"
    printf '  push {r4, lr} 出现次数 = %s\n' "$(grep -c 'push	{r4, lr}' build/probe.s || true)"
    printf '  pop {r4, pc}  出现次数 = %s\n' "$(grep -c 'pop	{r4, pc}' build/probe.s || true)"
    printf '  调用方把第 5、6 个入参写上栈：strd , [sp] 次数 = %s\n' "$(grep -c 'strd	.*\[sp\]' build/probe.s || true)"
    printf '  str 落盘到 [sp…] 总次数 = %s（含编译器溢出暂存，不都等于栈传参）\n' "$(grep -c 'str	.*\[sp' build/probe.s || true)"
else
    echo "（跳过汇编核对：PATH 里没有 arm-none-eabi-gcc；宿主断言不受影响）"
fi
