#!/bin/sh
# probe.sh —— B2 章全部取证，一条命令跑完（不需要开发板，也不需要 make）
#
#   sh probe.sh            跑全部五刀
#   sh probe.sh head       第 1 刀：ELF 头（入口点 + Thumb 位）
#   sh probe.sh sect       第 2 刀：节表（分类视角）
#   sh probe.sh seg        第 3 刀：程序头（装车视角，VMA/LMA 分家）
#   sh probe.sh sym        第 4 刀：符号表（nm 一排序就是地图）
#   sh probe.sh dis        第 5 刀：反汇编（main 的 prologue + 字面量池 + 向量表）
#   sh probe.sh tag        实物实验：tag 加不加 const，ELF 里哪几行变了
#   sh probe.sh clean
#
# 编译必须用 arm-none-eabi-*（交叉工具链）；nm/size/readelf/objdump 优先用交叉那一套，
# 缺了退回宿主 binutils——两者都读得了 ARM ELF32。产物一律落在 build/（已 gitignore）。
#
# 标本两件：
#   blink.elf    —— 00-blink 的原样产物（照它的 Makefile 逐条命令敲，不依赖 make）
#   elf_probe.elf —— 本目录 elf_probe.c，刻意让 .data/.bss/.rodata 同时在场

set -e

ARM_PREFIX=${ARM_PREFIX:-arm-none-eabi-}
CC="${ARM_PREFIX}gcc"
BOARD=../../stm32/00-blink
LDSCRIPT=$BOARD/stm32f407xx.ld
STARTUP=$BOARD/startup_stm32f407xx.s
MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
CFLAGS="$MCU -O0 -g3 -Wall -Wextra -ffunction-sections -fdata-sections"
LDFLAGS="$MCU -T $LDSCRIPT -Wl,--gc-sections -nostartfiles"

cd "$(dirname "$0")"
mkdir -p build

tool() {
    if command -v "${ARM_PREFIX}$1" >/dev/null 2>&1; then echo "${ARM_PREFIX}$1"; else echo "$1"; fi
}
NM=$(tool nm); SIZE=$(tool size); RE=$(tool readelf); OD=$(tool objdump); OC=$(tool objcopy)

need() {
    command -v "$CC" >/dev/null 2>&1 || {
        echo "找不到 $CC —— 先把工具链加进 PATH（见 docs/build/00-toolchain.md）" >&2
        exit 1
    }
}

build_all() {
    # 标本一：blink.elf（与 00-blink/Makefile 完全相同的三条命令）
    "$CC" $MCU -g3 -c "$STARTUP" -o build/startup_stm32f407xx.o
    "$CC" $CFLAGS -c "$BOARD/main.c" -o build/main.o
    "$CC" build/startup_stm32f407xx.o build/main.o $LDFLAGS -Wl,-Map=build/blink.map -o build/blink.elf
    "$OC" -O binary build/blink.elf build/blink.bin
    # 标本二：elf_probe.elf（带 .data 镜像，VMA/LMA 才看得见）
    "$CC" $CFLAGS -c elf_probe.c -o build/elf_probe.o
    "$CC" $MCU -g3 $LDFLAGS -Wl,-Map=build/elf_probe.map \
        build/elf_probe.o build/startup_stm32f407xx.o -o build/elf_probe.elf
}

head_probe() {
    echo "############ 第 1 刀：ELF 头（readelf -h） ############"
    "$RE" -h build/blink.elf | grep -E 'Magic|Class|Type|Machine|Entry point|Number of program|Number of section'
    echo
    echo "----- 入口点 0x8000189 是谁？符号表里 Reset_Handler 在 0x08000188 -----"
    "$NM" -n build/blink.elf | grep -E ' Reset_Handler$| g_pfnVectors$'
    echo "差的那个 1 = Thumb 位。Cortex-M 只跑 Thumb，所以低位为 1 才合法。"
    echo
    echo "----- 向量表前两个字（CPU 复位后读的第一口数据） -----"
    "$RE" -x .isr_vector build/blink.elf | sed -n '3p'
    echo "小端读法：00000220 → 0x20020000 = _estack；89010008 → 0x08000189 = Reset_Handler|1"
}

sect_probe() {
    echo
    echo "############ 第 2 刀：节表（分类视角） ############"
    echo "----- blink.elf：太干净，.data/.bss 都是 0 字节 -----"
    "$RE" -W -S build/blink.elf | sed -n '/\[ 1\]/,/\[ 5\]/p'
    echo
    echo "----- elf_probe.elf：故意留了初值，五个段各有各的活法 -----"
    "$RE" -W -S build/elf_probe.elf | sed -n '/\[ 1\]/,/\[ 5\]/p'
    echo
    echo "读法：Addr 是'住址'（VMA），Off 是'文件里的货架号'。blink 里 .text 的"
    echo "Addr=08000188 而 Off=001188 —— 差 0x1000，别把两者当一个。"
    echo "Flg 列：A=alloc（要装进内存才生效）、X=可执行、W=可写；Type=NOBITS 表示文件里不给货。"
    echo
    echo "----- size：把节表汇成三本账 -----"
    "$SIZE" build/blink.elf
    "$SIZE" build/elf_probe.elf
    echo "bin 只装 ALLOC 段里有货的部分：blink.bin $(wc -c < build/blink.bin) 字节"
}

seg_probe() {
    echo
    echo "############ 第 3 刀：程序头（装车视角） ############"
    echo "----- blink.elf：两个 LOAD -----"
    "$RE" -W -l build/blink.elf | sed -n '/Program Header/,/^$/p'
    "$RE" -W -l build/blink.elf | sed -n '/Section to Segment/,$p'
    echo
    echo "----- elf_probe.elf：三个 LOAD，第二个就是 VMA/LMA 分家现场 -----"
    "$RE" -W -l build/elf_probe.elf | sed -n '/Program Header/,/^$/p'
    "$RE" -W -l build/elf_probe.elf | sed -n '/Section to Segment/,$p'
    echo
    echo "----- 同一份 .data：objdump -s 打的是 VMA，readelf -x 也是 VMA -----"
    "$OD" -s -j .data build/elf_probe.elf | tail -3
    echo "Flash 里那份镜像的实际位置在 PhysAddr（LMA），不是左边这个 20000000。"
    echo
    echo "----- 链接脚本里给出这对地址的那几行 -----"
    grep -n -E 'AT> FLASH|_sidata|_sdata|_edata|_sbss|_ebss' "$LDSCRIPT"
}

sym_probe() {
    echo
    echo "############ 第 4 刀：符号表（nm 一排序就是地图） ############"
    echo "----- nm -n --print-size：elf_probe.elf 的按地址流水账 -----"
    "$NM" -n --print-size build/elf_probe.elf | grep -vE '_IRQHandler'
    echo "（省略 91 行 *_IRQHandler 弱别名——它们全指向同一个 Default_Handler）"
    echo
    echo "----- 弱符号到底有几个 -----"
    "$NM" -n build/blink.elf | awk '$1=="080001e8" && $2=="W"{c++} END{print "指向 0x080001e8 的 W 别名：" c " 个"}'
    echo
    echo "----- readelf -s 看得见 Thumb 位，nm 会抹掉 -----"
    "$RE" -W -s build/blink.elf | grep -E ' (Reset_Handler|Default_Handler|main)$'
    echo "同一个人：readelf 说 08000189/0800020d，nm 说 08000188/0800020c。差 1，都是 Thumb 位。"
}

dis_probe() {
    echo
    echo "############ 第 5 刀：反汇编（objdump -d） ############"
    echo "----- main 的开头三条：C6 讲的 prologue 现场 -----"
    "$OD" -d build/blink.elf | sed -n '/<main>:/,/^.*orr\.w/p'
    echo
    echo "----- 寄存器地址不在指令里，在 .text 末尾的字面量池 -----"
    "$OD" -d --start-address=0x8000274 --stop-address=0x8000294 build/blink.elf | tail -8
    echo "0x40023830=RCC_AHB1ENR、0x40021400…1418=GPIOF 五个寄存器、0x001e8480=2000000（延时常数）"
    echo
    echo "----- Reset_Handler：搬 .data、清 .bss 的那个循环（B4 主角） -----"
    "$OD" -d build/elf_probe.elf | sed -n '/<Reset_Handler>:/,/bx/p'
}

tag_probe() {
    echo
    echo "############ 实物实验：一个 8 字节的数组，加不加 const -----"
    "$CC" $CFLAGS -DTAG_RAM -c elf_probe.c -o build/elf_probe_ram.o
    "$CC" $MCU -g3 $LDFLAGS build/elf_probe_ram.o build/startup_stm32f407xx.o -o build/elf_probe_ram.elf
    echo
    echo "----- 不加 const（-DTAG_RAM）：tag 进 .data -----"
    "$NM" -n --print-size build/elf_probe_ram.elf | grep -E ' tag$'
    "$SIZE" -A build/elf_probe_ram.elf | grep -E '^\.text|^\.data|^\.bss'
    "$RE" -W -l build/elf_probe_ram.elf | grep LOAD | sed -n '2p'
    echo
    echo "----- 加 const（默认）：tag 进 .rodata，被脚本并进 .text -----"
    "$NM" -n --print-size build/elf_probe.elf | grep -E ' tag$'
    "$SIZE" -A build/elf_probe.elf | grep -E '^\.text|^\.data|^\.bss'
    "$RE" -W -l build/elf_probe.elf | grep LOAD | sed -n '2p'
    echo
    echo "读法：.data 大 8 字节、.text 小 8 字节；RAM 里多出 8 字节本体，Flash 里那份镜像也在。"
    echo "const 买的不是'只读'两个字，是'别再往 RAM 搬一遍'。"
}

case "${1:-all}" in
    head) need; build_all; head_probe ;;
    sect) need; build_all; sect_probe ;;
    seg)  need; build_all; seg_probe ;;
    sym)  need; build_all; sym_probe ;;
    dis)  need; build_all; dis_probe ;;
    tag)  need; build_all; tag_probe ;;
    clean) rm -rf build; echo "已清理 build/" ;;
    all)
        need; build_all
        head_probe; sect_probe; seg_probe; sym_probe; dis_probe; tag_probe ;;
    *) echo "用法：sh probe.sh [head|sect|seg|sym|dis|tag|all|clean]" >&2; exit 2 ;;
esac
