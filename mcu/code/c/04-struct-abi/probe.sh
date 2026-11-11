#!/bin/sh
# C4 struct-abi 取证脚本
# 用法：
#   本机宿主 gcc：sh probe.sh
#   ARM 交叉编译：CC=arm-none-eabi-gcc sh probe.sh
# 交叉编译器无法链接 hosted 程序（缺 _exit/_write 等），自动退化为“编译期断言通过”。

set -e
cd "$(dirname "$0")"

CC=${CC:-gcc}
CFLAGS="-std=c11 -Wall -Wextra -O0"

echo "=== C4 struct-abi probe ==="
echo "CC: $CC"
echo "CFLAGS: $CFLAGS"
echo ""

# 先试编译+链接；失败则视为交叉编译器，仅做编译期断言验证
if $CC $CFLAGS -o probe.exe probe.c 2>/dev/null; then
    ./probe.exe
    rm -f probe.exe
else
    echo "note: link failed (likely cross-compiler without syscalls); falling back to compile-only assertions"
    $CC $CFLAGS -c probe.c -o probe.o
    echo "compile-time _Static_assert PASSED (GPIO_TypeDef offsets & sizes verified)"
    rm -f probe.o
fi
