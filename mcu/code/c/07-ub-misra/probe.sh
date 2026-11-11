#!/bin/sh
# probe.sh —— C7《未定义行为与 MISRA-C》全部取证，一条命令跑完
#
#   sh probe.sh   1) 宿主双档对照：probe.c 用 -O0 与 -O2 各编一份，同一行代码当众变脸；
#                 2) -fwrapv 对照：加一个编译旗，-O2 的"恒真"当场收回；
#                 3) 编译器防线现场：-Wstrict-aliasing / -Warray-bounds / -Wuninitialized 抓人实录；
#                 4) UBSan 运行期点名（工具链支持时）；
#                 5) 交叉汇编：arm-none-eabi-gcc -O2 -S 看 is_bigger_after_inc 被折叠成几条指令；
#                 6) 宿主汇编：同一件事在 x86 上的两份铁证——-O0 函数体已是 movl $1，-O2 连 call 都没了。
#   sh probe.sh clean   删 build/
#
# 产物一律落在 build/（code/**/build/ 已 gitignore）。
#
# 第 5 步需要交叉工具链。章内两段汇编出自 15.2.1，所以下面把它的 bin 目录钉进 PATH
# （本机装了就用它，没装就退回 PATH 里默认那把，并把实际版本号打印出来）。
#   也可以自己指定：ARM_PREFIX=/path/to/arm-none-eabi- sh probe.sh
# 版本差异只改形状不改结论：10.3.1 的 -fwrapv 段给成 adds/cmp/ite/movle/movgt，
# 而 -O2 折叠段两把一模一样，见章内引文。

set -e
cd "$(dirname "$0")"

XPACK=${XPACK:-/d/zhugu-home/tools/armgcc/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin}
[ -d "$XPACK" ] && PATH="$XPACK:$PATH"

if [ "$1" = "clean" ]; then
    rm -rf build
    exit 0
fi

mkdir -p build

HOSTCC=${CC:-gcc}

echo "############ 1. 宿主多档对照：同一行代码的几张脸 ############"
echo "宿主工具链：$HOSTCC $("$HOSTCC" -dumpfullversion 2>/dev/null || "$HOSTCC" -dumpversion)"
"$HOSTCC" -std=c11 -Wall -Wextra -Werror -O0 probe.c -o build/probe-o0.exe
"$HOSTCC" -std=c11 -Wall -Wextra -Werror -O2 probe.c -o build/probe-o2.exe
echo "----- -O0 -----"
./build/probe-o0.exe || true
echo "----- -O2 -----"
./build/probe-o2.exe || true

echo
echo "############ 2. -fwrapv 对照：一个编译旗让恒真收回 ############"
"$HOSTCC" -std=c11 -Wall -Wextra -Werror -O2 -fwrapv probe.c -o build/probe-wrapv.exe
./build/probe-wrapv.exe || true

echo
echo "############ 3. 编译器防线现场：三条警告抓人实录 ############"
echo "----- -Wstrict-aliasing：float* 强转 uint32_t* 解引用（alias-violate.c）-----"
"$HOSTCC" -std=c11 -O2 -Wstrict-aliasing -c alias-violate.c -o build/alias-violate.o 2>&1 || true
echo "----- -Warray-bounds / -Wuninitialized（oob-static.c）-----"
"$HOSTCC" -std=c11 -O2 -Wall -Wextra -c oob-static.c -o build/oob-static.o 2>&1 || true

echo
echo "############ 4. UBSan 运行期点名（工具链支持时） ############"
if "$HOSTCC" -std=c11 -O2 -fsanitize=undefined ub.c -o build/ub.exe 2>/dev/null; then
    ./build/ub.exe 2>&1 || true
else
    echo "（跳过：本工具链没有 UBSan 运行库——嵌入式交叉链上这很常见，靠第 3 步的编译期防线）"
fi

echo
echo "############ 5. 交叉汇编：is_bigger_after_inc 在 -O2 下被折叠成什么 ############"
ARMPREFIX=arm-none-eabi-
if command -v "${ARMPREFIX}gcc" >/dev/null 2>&1; then
    MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
    echo "交叉工具链：$("${ARMPREFIX}gcc" -dumpfullversion)"
    "${ARMPREFIX}gcc" $MCU -std=c11 -O2 -S probe.c -o build/probe-arm.s
    echo "----- -O2：编译器假定溢出永不发生 → 函数体只剩"恒真"-----"
    sed -n '/^is_bigger_after_inc:/,/\.size[[:space:]]*is_bigger_after_inc/p' build/probe-arm.s | grep -Ev "^\s*(@|\.)" || true
    "${ARMPREFIX}gcc" $MCU -std=c11 -O2 -fwrapv -S probe.c -o build/probe-arm-wrapv.s
    echo "----- -fwrapv -O2：溢出按回绕定义 → 必须真算 -----"
    sed -n '/^is_bigger_after_inc:/,/\.size[[:space:]]*is_bigger_after_inc/p' build/probe-arm-wrapv.s | grep -Ev "^\s*(@|\.)" || true
else
    echo "（跳过汇编取证：PATH 里没有 arm-none-eabi-gcc；宿主对照不受影响）"
fi

echo
echo "############ 6. 宿主侧折叠铁证：-O0 的函数体已经是常量，-O2 连调用都没了 ############"
"$HOSTCC" -std=c11 -O0 -S probe.c -o build/host-o0.s
"$HOSTCC" -std=c11 -O2 -S probe.c -o build/host-o2.s
echo "----- -O0 is_bigger_after_inc 函数体：加法和比较都被吃掉 -----"
awk '/^is_bigger_after_inc:/{f=1} f{print} f&&/^\tret$/{exit}' build/host-o0.s | grep -Ev "^[[:space:]]*\.seh" || true
echo "----- -O0 shift_oob 函数体：真发一条 sall %cl（33 被移位器截成 1 → 结果 2）-----"
awk '/^shift_oob:/{f=1} f{print} f&&/^\tret$/{exit}' build/host-o0.s | grep -Ev "^[[:space:]]*\.seh" || true
echo "----- -O2 main：is_bigger/shift/两种位读法的 call 全部消失，打印参数就是立即数 -----"
echo "     \$1 = 恒真折叠；\$0（xorl %edx,%edx）= UB 之后编译器爱给什么给什么；\$1065353216 = 0x3F800000"
awk '/^main:/{f=1} f{print} f&&/^\tret$/{exit}' build/host-o2.s | grep -Ev "^[[:space:]]*\.seh" || true
