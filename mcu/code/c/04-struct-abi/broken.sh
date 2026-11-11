#!/bin/sh
# C4 struct-abi "写错一位"取证脚本
# 用法：
#   本机宿主 gcc：sh broken.sh
#   ARM 交叉编译：CC=arm-none-eabi-gcc sh broken.sh（无法链接 hosted 程序时自动退化为编译期验证）
# 最后一节故意让编译失败，把编译器原话打出来——这就是 _Static_assert 在日常开发里的样子。

set -e
cd "$(dirname "$0")"

CC=${CC:-gcc}
CFLAGS="-std=c11 -Wall -Wextra -O0"

echo "CC: $CC"
echo "CFLAGS: $CFLAGS"
echo ""

if $CC $CFLAGS -o broken.exe broken.c 2>/dev/null; then
    ./broken.exe
    rm -f broken.exe
else
    echo "note: link failed (likely cross-compiler without syscalls); falling back to compile-only check"
    $CC $CFLAGS -c broken.c -o broken.o
    echo "broken.c compiles clean (布局事实由 sizeof/offsetof 现场打印)"
    rm -f broken.o
fi

echo ""
echo "--- 故意让编译失败一次：把断言压回 Short_t ---"
cat > assert-fail.c <<'EOF'
#include <stdint.h>
#include <stddef.h>
typedef struct {
    volatile uint32_t MODER, OTYPER, OSPEEDR, PUPDR, IDR, ODR, BSRR, LCKR, AFR;
} Short_t;
_Static_assert(sizeof(Short_t) == 0x28, "GPIO_TypeDef size must be 0x28 (10 x uint32)");
EOF
if $CC $CFLAGS -c assert-fail.c -o assert-fail.o 2>assert-fail.log; then
    echo "意外：编译通过了（说明断言没起作用）"
else
    echo "编译失败，编译器原话："
    grep -m1 "static assertion failed" assert-fail.log
fi
rm -f assert-fail.c assert-fail.o assert-fail.log
