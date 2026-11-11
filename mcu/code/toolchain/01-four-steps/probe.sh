#!/bin/sh
# probe.sh —— B1 四步构建取证（不需要开发板，也不需要 make）
#
#   sh probe.sh          跑全部：四步 + 三个错误现场
#   sh probe.sh steps    只跑四步，保留 .i/.s/.o/.elf 全部中间产物
#   sh probe.sh errors   只跑三个错误现场（预处理/编译/链接）
#   sh probe.sh clean
#
# 只需要交叉工具链在 PATH 里（或 ARM_PREFIX=/路径/arm-none-eabi-）。
# 标本：code/stm32/00-blink 的 main.c / 启动文件 / 链接脚本。
# 产物落在 build/（已 gitignore）。

set -e

ARM_PREFIX=${ARM_PREFIX:-arm-none-eabi-}
CC="${ARM_PREFIX}gcc"
BOARD=../../stm32/00-blink
MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
CFLAGS="$MCU -O0 -g3 -Wall -Wextra"
LDFLAGS="$MCU -T $BOARD/stm32f407xx.ld -Wl,--gc-sections -nostartfiles"

cd "$(dirname "$0")"
mkdir -p build

need() {
    command -v "$CC" >/dev/null 2>&1 || {
        echo "找不到 $CC —— 先把工具链加进 PATH（见 docs/build/00-toolchain.md）" >&2
        exit 1
    }
}

steps() {
    need

    echo "############ 第 1 步：预处理 -E（cpp 展开头文件与宏）############"
    "$CC" $CFLAGS -E "$BOARD/main.c" -o build/main.i
    printf 'main.c %s 行  →  main.i %s 行（#include <stdint.h> 与所有宏都被摊平）\n' \
        "$(wc -l < "$BOARD/main.c")" "$(wc -l < build/main.i)"
    echo "----- 展开后 main 的签名（宏没了，只剩真类型）-----"
    grep -n '^int main(void)' build/main.i || echo "(未找到)"
    echo "----- 源码里的 RCC_BASE 宏，展开后直接摊成算术式 -----"
    grep -n '0x3800UL' build/main.i | head -3 || echo "(未找到)"

    echo
    echo "############ 第 2 步：编译 -S（cc1 把 C 翻成汇编）############"
    "$CC" $CFLAGS -S build/main.i -o build/main.s
    printf 'main.s %s 行\n' "$(wc -l < build/main.s)"
    echo "----- main 的开场：函数序言 + 开时钟那条 |= -----"
    sed -n '/^main:/,/^\.L[0-9]*:/p' build/main.s | head -20

    echo
    echo "############ 第 3 步：汇编 -c（as 把 .s 变机器码，符号还没有地址）############"
    "$CC" $CFLAGS -c build/main.s -o build/main.o
    "$CC" $CFLAGS -c "$BOARD/startup_stm32f407xx.s" -o build/startup_stm32f407xx.o
    echo "----- nm：U = 本文件没定义、留给链接器填地址的符号 -----"
    MAIN_U=$("${ARM_PREFIX}nm" build/main.o | grep -E ' U ' || true)
    printf '  main.o：%s\n' "${MAIN_U:-（一个 U 都没有——外设访问是硬编码地址常量，不需要符号决议）}"
    echo "  startup_stm32f407xx.o（段边界来自链接脚本，main 来自应用）："
    "${ARM_PREFIX}nm" build/startup_stm32f407xx.o | grep -E ' U ' | sed 's/^ *U /    U /'
    echo "----- 可重定位：段的地址栏还是 0，因为位置还没定 -----"
    "${ARM_PREFIX}objdump" -h build/main.o | grep -E '\.text|\.data|\.bss' || true

    echo
    echo "############ 第 4 步：链接（ld 决议符号 + 按脚本排座）############"
    "$CC" build/main.o build/startup_stm32f407xx.o $LDFLAGS -Wl,-Map=build/blink.map -o build/blink.elf
    echo "----- objdump -h：段有了 VMA，向量表钉在 0x0800_0000 -----"
    "${ARM_PREFIX}objdump" -h build/blink.elf | grep -E '^ *[0-9]+ \.(isr_vector|text|data|bss) ' || true
    echo "----- size：Flash/RAM 各占多少字节（text=代码+常量，data/bss=变量）-----"
    "${ARM_PREFIX}size" build/blink.elf
    echo "----- 符号有地址了：Reset_Handler / main 都落在 Flash 0x0800_0000 段 -----"
    "${ARM_PREFIX}nm" -n build/blink.elf | grep -E ' (Reset_Handler|main)$' || true
}

errors() {
    need

    echo "############ 错误现场 1：预处理阶段（头文件找不到）############"
    printf '#include <no_such_header_xyz.h>\nint main(void){ return 0; }\n' > build/bad_pp.c
    if "$CC" $CFLAGS -E build/bad_pp.c -o build/bad_pp.i 2> build/err_pp.txt; then
        echo "（意外通过）"
    else
        echo "报错原文："; sed -n '1,3p' build/err_pp.txt
        echo "→ fatal error: ... No such file or directory = 死在预处理（cpp）"
    fi

    echo
    echo "############ 错误现场 2：编译阶段（语法错）############"
    printf 'int f(void){ int x = ; return x; }\n' > build/bad_cc.c
    if "$CC" $CFLAGS -S build/bad_cc.c -o build/bad_cc.s 2> build/err_cc.txt; then
        echo "（意外通过）"
    else
        echo "报错原文："; sed -n '1,3p' build/err_cc.txt
        echo "→ error: expected expression = 死在编译（cc1）"
    fi

    echo
    echo "############ 错误现场 3：链接阶段（undefined reference）############"
    printf 'extern int SystemInit(void);\nint main(void){ return SystemInit(); }\n' > build/bad_ld.c
    "$CC" $CFLAGS -c build/bad_ld.c -o build/bad_ld.o
    # 故意不带 --gc-sections：否则没有入口符号时 main 会被整段回收，
    # 对 SystemInit 的引用一并消失，反而"链接成功"——那是个假阴性。
    if "$CC" build/bad_ld.o $MCU -T "$BOARD/stm32f407xx.ld" -nostartfiles \
            -o build/bad_ld.elf 2> build/err_ld.txt; then
        echo "（意外通过）"
    else
        echo "报错原文："; sed -n '1,4p' build/err_ld.txt
        echo "→ undefined reference = 死在链接（ld）；编译早过了，符号才是问题"
    fi
}

case "${1:-all}" in
    steps)  steps ;;
    errors) errors ;;
    clean)  rm -rf build; echo "已清理 build/" ;;
    all)    steps; errors ;;
    *)      echo "用法：sh probe.sh [steps|errors|all|clean]" >&2; exit 2 ;;
esac
