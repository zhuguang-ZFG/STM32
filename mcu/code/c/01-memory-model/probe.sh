#!/bin/sh
# probe.sh —— C1 章全部取证，一条命令跑完（不需要开发板）
#
#   sh probe.sh          跑全部
#   sh probe.sh mem      段归属：size -A / nm -n / readelf -S / readelf -l / 查无此人
#   sh probe.sh lut      const 经济学：加不加 const 的 256 字节对照
#   sh probe.sh boot     搬运工：Reset_Handler 反汇编 + 链接脚本关键行 + .data 镜像字节
#   sh probe.sh clean
#
# 编译必须用 arm-none-eabi-*（交叉工具链）；nm/size/readelf/objdump 优先用交叉那一套，
# 缺了退回宿主 binutils——两者都读得了 ARM ELF32。产物一律落在 build/（已 gitignore）。

set -e

ARM_PREFIX=${ARM_PREFIX:-arm-none-eabi-}
CC="${ARM_PREFIX}gcc"
BOARD=../../stm32/00-blink
LDSCRIPT=$BOARD/stm32f407xx.ld
STARTUP=$BOARD/startup_stm32f407xx.s
MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
CFLAGS="$MCU -O0 -g3 -ffunction-sections -fdata-sections"
LDFLAGS="$MCU -T $LDSCRIPT -Wl,--gc-sections -nostartfiles"

cd "$(dirname "$0")"
mkdir -p build

# nm/size/readelf/objdump 优先用交叉工具链里的那一套（对 ELF32 最稳），
# 缺了就退回宿主 binutils（MinGW 的 nm 也读得了 ARM ELF）。
tool() {
    if command -v "${ARM_PREFIX}$1" >/dev/null 2>&1; then echo "${ARM_PREFIX}$1"; else echo "$1"; fi
}
NM=$(tool nm); SIZE=$(tool size); RE=$(tool readelf); OD=$(tool objdump); OC=$(tool objcopy)

need() {
    command -v "$CC" >/dev/null 2>&1 || {
        echo "找不到 $CC —— 先把工具链加进 PATH（见本目录 README）" >&2
        exit 1
    }
}

link_objs() {  # link_objs <elf 名> <map 名> <obj...>
    out=$1; shift
    map=$1; shift
    "$CC" $MCU -g3 $LDFLAGS -Wl,-Map=build/"$map" "$@" -o build/"$out"
}

build_startup() {
    [ -f build/startup_stm32f407xx.o ] || \
        "$CC" $CFLAGS -Wall -Wextra -c "$STARTUP" -o build/startup_stm32f407xx.o
}

mem_probe() {
    echo "############ 1. 段归属取证：mem_probe.c ############"
    "$CC" $CFLAGS -Wall -Wextra -c mem_probe.c -o build/mem_probe.o
    build_startup
    link_objs mem_probe.elf mem_probe.map build/mem_probe.o build/startup_stm32f407xx.o

    echo
    echo "----- size -A：每个段多大、住在哪个地址 -----"
    "$SIZE" -A build/mem_probe.elf | grep -vE '^\.debug|^\.comment|^\.ARM\.attributes'

    echo
    echo "----- nm -n --print-size：按地址排序的符号表（VMA；省略 91 行同名 IRQ 别名）-----"
    "$NM" -n --print-size build/mem_probe.elf | awk '$1!="0800028c" || $4=="Default_Handler"'

    echo
    echo "----- readelf -S：段类型（PROGBITS=文件里有货，NOBITS=只登记不给货）-----"
    "$RE" -W -S build/mem_probe.elf | grep -E '\] \.(isr_vector|text|data|bss|_user)'

    echo
    echo "----- readelf -l：ELF 程序头（VMA / LMA 分家的地方）-----"
    "$RE" -W -l build/mem_probe.elf | sed -n '/Program Header/,/Section to Segment/p'

    echo
    echo "----- 字面量住哪：\"flash\" 这几个字节在 .text 里（没有符号名）-----"
    "$OD" -s -j .text build/mem_probe.elf | grep -i 666c6173

    echo
    echo "----- 查无此人：nm 里搜 auto_var -----"
    if "$NM" build/mem_probe.elf | grep -q auto_var; then
        echo "有符号（与预期不符，检查编译档）"
    else
        echo "没有 auto_var 这个符号 —— 它活在栈上，链接期不存在"
    fi
}

lut_probe() {
    echo
    echo "############ 2. const 经济学：256 字节的表，加不加 const ############"
    build_startup
    "$CC" $CFLAGS -c lut_probe.c -o build/lut_rw.o
    "$CC" $CFLAGS -DLUT_CONST -c lut_probe.c -o build/lut_ro.o
    link_objs lut_rw.elf lut_rw.map build/lut_rw.o build/startup_stm32f407xx.o
    link_objs lut_ro.elf lut_ro.map build/lut_ro.o build/startup_stm32f407xx.o

    for k in rw ro; do
        if [ "$k" = rw ]; then label="uint8_t lut[256]     （可写）"; else label="const uint8_t lut[256] （只读）"; fi
        echo
        echo "----- $label -----"
        "$SIZE" -A build/lut_$k.elf | grep -E '^\.text|^\.data|^\.bss'
        "$NM" -n --print-size build/lut_$k.elf | grep -E ' lut$'
        "$RE" -W -l build/lut_$k.elf | grep 'LOAD'
    done
    echo
    echo "读法：lut 的 nm 字母 D=数据段 / T=代码段；可写版 .data 有 256 字节，只读版是 0。"
}

boot_probe() {
    echo
    echo "############ 3. 上电到 main：搬运工是谁 ############"
    [ -f build/mem_probe.elf ] || { need; mem_probe; }

    echo
    echo "----- Reset_Handler 反汇编（.data 拷贝 + .bss 清零 + 字面量池）-----"
    "$OD" -d build/mem_probe.elf | sed -n '/<Reset_Handler>:/,/^$/p'

    echo
    echo "----- 链接脚本里的关键行 -----"
    grep -n -E 'ORIGIN|_sidata|LOADADDR|AT> FLASH|_Min_Heap_Size|_Min_Stack_Size|\.rodata' "$LDSCRIPT"

    echo
    echo "----- Flash 里那份 .data 初值镜像 -----"
    "$OC" -j .data -O binary build/mem_probe.elf build/data.bin
    "$OD" -s -j .data build/mem_probe.elf
    echo "镜像文件 build/data.bin：$(wc -c < build/data.bin) 字节 = .data 的 FileSiz"
}

# rodata_probe —— 把 .rodata 从 .text 里分出去，看 nm 的字母怎么变
# 做法：从 00-blink 的链接脚本现场生成一份变体（不改动原件），只做一件事：
#   删掉 .text 里的 *(.rodata) / *(.rodata*)，在 .text 之后单开一个 .rodata 输出段。
rodata_probe() {
    echo
    echo "############ 4. 字母会骗人：.rodata 单列时 g_ro 从 T 变 R ############"
    awk '
        /^[ \t]*\*\(\.rodata/ { next }                    # 从 .text 里摘走
        /^    _etext = \.;$/  { etext = 1 }
        etext && /^  \} >FLASH$/ {
            print
            print ""
            print "  /* 变体：只读数据单列一个输出段 */"
            print "  .rodata : { *(.rodata) *(.rodata*) . = ALIGN(4); } >FLASH"
            etext = 0; next
        }
        { print }
    ' "$LDSCRIPT" > build/stm32f407xx-rodata-sep.ld

    "$CC" $MCU -g3 -T build/stm32f407xx-rodata-sep.ld -Wl,--gc-sections -nostartfiles \
        build/mem_probe.o build/startup_stm32f407xx.o -o build/mem_probe-sep.elf

    echo "生成的变体脚本：build/stm32f407xx-rodata-sep.ld（原件未改动）"
    echo
    echo "----- 同一批符号，两种脚本的字母与地址 -----"
    echo "原脚本（.rodata 并进 .text）："
    "$NM" build/mem_probe.elf | grep -E ' (g_ro|k_tab)$'
    echo "变体脚本（.rodata 单列）："
    "$NM" build/mem_probe-sep.elf | grep -E ' (g_ro|k_tab)$'
    echo
    echo "----- readelf -S 里多出的一行 -----"
    "$RE" -W -S build/mem_probe-sep.elf | grep -E '\] \.(text|rodata)'
    echo
    echo "读法：地址一格没动（还是 0x08000298 / 0x0800029c），字母却从 T 变成 R。"
    echo "T/R 说的是『在哪个输出段、什么属性』，不是『是函数还是数据』——所以本章只看地址。"
}

case "${1:-all}" in
    mem)    need; mem_probe ;;
    lut)    need; lut_probe ;;
    boot)   need; boot_probe ;;
    rodata) need; mem_probe; rodata_probe ;;
    clean)  rm -rf build; echo "已清理 build/" ;;
    all)    need; mem_probe; lut_probe; boot_probe; rodata_probe ;;
    *)      echo "用法：sh probe.sh [mem|lut|boot|rodata|all|clean]" >&2; exit 2 ;;
esac
