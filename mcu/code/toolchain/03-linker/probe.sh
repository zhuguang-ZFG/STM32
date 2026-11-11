#!/bin/sh
# probe.sh —— B3 链接脚本六刀取证（不需要开发板，也不需要 make）
#
#   sh probe.sh            跑全部六刀
#   sh probe.sh keep       第 1 刀：删掉 KEEP(*(.isr_vector)) —— 段还在，字节没了
#   sh probe.sh at         第 2 刀：删掉 AT> FLASH —— _sidata 变成一个 RAM 地址
#   sh probe.sh overflow   第 3 刀：RAM LENGTH 改小 / 栈预算撑大 —— 链接期就拦住
#   sh probe.sh flags      第 4 刀：区域属性写 (xrwah) —— invalid character (104)
#   sh probe.sh ccm        第 5 刀：CCM 三态 —— orphan 撒谎 / 128MB 空洞 / AT> 收场
#   sh probe.sh trace      第 6 刀：--trace / --print-memory-usage / ld --verbose
#   sh probe.sh clean
#
# 图纸一律从 code/stm32/00-blink/stm32f407xx.ld 用 sed 改一刀生成到 build/，
# 每刀都先把 diff 打出来——原文不动，改动可见，结果可复跑。
# 产物落 build/（已 gitignore）。第 5 刀中间那态会写出 128MB 的 bin，量完立刻删；
# 不想让它落盘就 CCM_GAP=0 sh probe.sh ccm（改跑换算式）。

set -e

ARM_PREFIX=${ARM_PREFIX:-arm-none-eabi-}
CC="${ARM_PREFIX}gcc"
BOARD=../../stm32/00-blink
LDSCRIPT=$BOARD/stm32f407xx.ld
STARTUP=$BOARD/startup_stm32f407xx.s
MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
CFLAGS="$MCU -O0 -g3 -Wall -Wextra -ffunction-sections -fdata-sections"
LDFLAGS="$MCU -Wl,--gc-sections -nostartfiles"
CCM_GAP=${CCM_GAP:-1}

cd "$(dirname "$0")"
mkdir -p build

tool() {
    if command -v "${ARM_PREFIX}$1" >/dev/null 2>&1; then echo "${ARM_PREFIX}$1"; else echo "$1"; fi
}
NM=$(tool nm); RE=$(tool readelf); OD=$(tool objdump); OC=$(tool objcopy); LD=$(tool ld)

need() {
    command -v "$CC" >/dev/null 2>&1 || {
        echo "找不到 $CC —— 先把工具链加进 PATH（见 docs/build/00-toolchain.md）" >&2
        exit 1
    }
    [ -f "$LDSCRIPT" ] || { echo "找不到图纸 $LDSCRIPT" >&2; exit 1; }
}

# ld 的报错原文前面带它自己的绝对路径（每台机器不同），这里统一省掉，
# 其余字符照抄——包括 binutils 2.45.1 那句自带的 "%c"。
# 注意 lmsg 永远返回 0：这几刀的"失败"本来就是要看的输出。
lmsg() {
    sed -e 's#^.*/ld\.exe: ##' -e 's#^ld: ##' -e 's#^collect2\.exe: ##' \
        | { grep -v '^[[:space:]]*$' || true; }
}

build_base() {
    "$CC" $MCU -g3 -c "$STARTUP" -o build/startup.o
    "$CC" $CFLAGS -c "$BOARD/main.c" -o build/main.o
    "$CC" $CFLAGS -c link_probe.c -o build/link_probe.o
    "$CC" $CFLAGS -DWITH_CCM -c link_probe.c -o build/ccm_probe.o
    "$CC" build/startup.o build/main.o $MCU -T "$LDSCRIPT" -Wl,--gc-sections -nostartfiles \
        -o build/blink.elf
    "$OC" -O binary build/blink.elf build/blink.bin
    "$CC" build/startup.o build/link_probe.o $MCU -T "$LDSCRIPT" $LDFLAGS -o build/base.elf
    echo "标本就位：blink.bin $(wc -c < build/blink.bin) 字节；base.elf 是 link_probe.o 用原图纸链接的基线。"
}

keep_probe() {
    echo "############ 第 1 刀：删掉向量表的 KEEP ############"
    sed 's/KEEP(\*(\.isr_vector))/\*(.isr_vector)/' "$LDSCRIPT" > build/nokeep.ld
    diff "$LDSCRIPT" build/nokeep.ld || true
    "$CC" build/startup.o build/main.o $MCU -T build/nokeep.ld $LDFLAGS -o build/nokeep.elf
    "$OC" -O binary build/nokeep.elf build/nokeep.bin
    echo "--- bin 尺寸：向量表那 0x188 字节整个蒸发 ---"
    echo "blink.bin  = $(wc -c < build/blink.bin) 字节"
    echo "nokeep.bin = $(wc -c < build/nokeep.bin) 字节"
    echo "差 = $(( $(wc -c < build/blink.bin) - $(wc -c < build/nokeep.bin) )) 字节 = 0x$(printf %X $(( $(wc -c < build/blink.bin) - $(wc -c < build/nokeep.bin) )))"
    echo "--- 段表：.isr_vector 还在，尺寸成 0（一具空壳）---"
    "$RE" -S build/blink.elf  | grep isr_vector
    "$RE" -S build/nokeep.elf | grep isr_vector
    echo "--- 硬件上电从 0x08000000 读的两个字（SP / PC）---"
    printf 'blink.bin  头两个字: '; od -A n -t x4 -N 8 build/blink.bin
    printf 'nokeep.bin 头两个字: '; od -A n -t x4 -N 8 build/nokeep.bin
    echo "前一个字段本该是栈顶 20020000，现在是一条指令的机器码——第一次 push 就飞。"
    echo "--- 向量表符号还在哪 ---"
    "$NM" build/blink.elf  | grep -i g_pfnVectors
    "$NM" build/nokeep.elf | grep -i g_pfnVectors || echo "(nokeep.elf 里已经没有 g_pfnVectors)"
}

at_probe() {
    echo "############ 第 2 刀：删掉 AT> FLASH ############"
    sed 's/>RAM AT> FLASH/>RAM/' "$LDSCRIPT" > build/noat.ld
    diff "$LDSCRIPT" build/noat.ld || true
    "$CC" build/startup.o build/link_probe.o $MCU -T build/noat.ld $LDFLAGS -o build/noat.elf
    echo "--- 基线：.data 的 VMA 在 RAM，LMA(PhysAddr) 在 Flash ---"
    "$RE" -l build/base.elf | grep LOAD
    "$NM" build/base.elf | grep -E "_sidata|_sdata|_edata"
    echo "--- 删掉 AT> FLASH：LMA 塌回 RAM，_sidata == _sdata ---"
    "$RE" -l build/noat.elf | grep LOAD
    "$NM" build/noat.elf | grep -E "_sidata|_sdata|_edata"
    echo "搬运循环变成『把 _sdata 拷到 _sdata』：Flash 里那 4 个初值字节成了没人取的快递，"
    echo "而上电瞬间 RAM 里是随机值——g_live 读到什么全看天。"
}

overflow_probe() {
    echo "############ 第 3 刀：图纸在链接期拦住你 ############"
    echo "--- 先量一次实际占用（手算：.data 4 + .bss 4100 + 检查段 1536 = 5640）---"
    "$CC" build/startup.o build/link_probe.o $MCU -T "$LDSCRIPT" $LDFLAGS \
        -Wl,--print-memory-usage -o build/usage.elf 2>&1 | lmsg
    sed 's/LENGTH = 128K/LENGTH = 2K/' "$LDSCRIPT" > build/tinyram.ld
    diff "$LDSCRIPT" build/tinyram.ld | tail -4
    echo "--- 3a：RAM 只留 2K（5640 − 2048 = 3592）---"
    "$CC" build/startup.o build/link_probe.o $MCU -T build/tinyram.ld $LDFLAGS \
        -o build/tinyram.elf 2>&1 | lmsg
    sed 's/_Min_Stack_Size = 0x400;/_Min_Stack_Size = 0x20000;/' "$LDSCRIPT" > build/bigstack.ld
    diff "$LDSCRIPT" build/bigstack.ld | tail -4
    echo "--- 3b：数据一个没多，只把栈预算从 1K 撑到 128K ---"
    "$CC" build/startup.o build/link_probe.o $MCU -T build/bigstack.ld $LDFLAGS \
        -Wl,--print-memory-usage -o build/bigstack.elf 2>&1 | lmsg
    echo "点名的是 ._user_heap_stack——那段一个真实字节都不占，纯粹是图纸立的界碑。"
}

flags_probe() {
    echo "############ 第 4 刀：区域属性写错 ############"
    sed 's/RAM   (xrw)  /RAM   (xrwah)  /' "$LDSCRIPT" > build/badflag.ld
    diff "$LDSCRIPT" build/badflag.ld | tail -4
    "$CC" build/startup.o build/link_probe.o $MCU -T build/badflag.ld $LDFLAGS \
        -o build/badflag.elf 2>&1 | lmsg
    echo "104 就是字母 h 的 ASCII 码；合法属性字母只有 r w x a i l，没有 h。"
    echo "原文里那句 %c 不是我们漏了字——是 binutils 2.45.1 自己的格式串没带参数。"
}

ccm_probe() {
    echo "############ 第 5 刀：CCM 的三态 ############"
    echo "--- 态一：C 里加了 __attribute__((section(\".ccmram\")))，图纸没留房间 ---"
    "$CC" build/startup.o build/ccm_probe.o $MCU -T "$LDSCRIPT" $LDFLAGS -o build/orphan.elf
    "$OD" -h build/orphan.elf | grep -E "Idx|ccmram"
    echo "VMA 落在 0x2000_0004——它就在普通 SRAM 第 5 个字节，不是 CCM；ld 一声不响。"
    sed -e '/RAM   (xrw)  /a\  CCM   (rw)   : ORIGIN = 0x10000000, LENGTH = 64K' \
        -e '/^  _sidata = LOADADDR/i\  .ccmram : { _siccm = .; _sccm = .; KEEP(*(.ccmram)) _eccm = .; } >CCM\n' \
        "$LDSCRIPT" > build/ccmgap.ld
    echo "--- 态二：图纸加了 CCM 房间，但 .ccmram 只写 >CCM（没有 AT> FLASH）---"
    "$CC" build/startup.o build/ccm_probe.o $MCU -T build/ccmgap.ld $LDFLAGS -o build/ccmgap.elf
    "$RE" -l build/ccmgap.elf | grep LOAD
    if [ "$CCM_GAP" = 1 ]; then
        "$OC" -O binary build/ccmgap.elf build/ccmgap.bin
        echo "objcopy  exit=$? —— 它一声不响地把 0x0800_xxxx 到 0x1000_0000 之间的空洞全填成零"
        echo "bin 尺寸 = $(wc -c < build/ccmgap.bin) 字节"
        rm -f build/ccmgap.bin
        echo "（128MB 的文件量完即删；换算：0x1000_0000 − 0x0800_0000 = 134,217,728，再加 16 字节的 .ccmram 初值）"
    else
        echo "CCM_GAP=0：跳过落盘，换算式照旧：0x1000_0000 − 0x0800_0000 = $((0x10000000 - 0x08000000)) 字节空洞 + 16 字节初值"
    fi
    echo "--- 态三：同一个位置补上 AT> FLASH，空洞立刻收回来 ---"
    sed -e '/RAM   (xrw)  /a\  CCM   (rw)   : ORIGIN = 0x10000000, LENGTH = 64K' \
        -e '/^  _sidata = LOADADDR/i\  .ccmram : { _siccm = .; _sccm = .; KEEP(*(.ccmram)) _eccm = .; } >CCM AT> FLASH\n' \
        "$LDSCRIPT" > build/ccmat.ld
    "$CC" build/startup.o build/ccm_probe.o $MCU -T build/ccmat.ld $LDFLAGS -o build/ccmat.elf
    "$OC" -O binary build/ccmat.elf build/ccmat.bin
    "$RE" -l build/ccmat.elf | grep LOAD
    echo "bin 尺寸 = $(wc -c < build/ccmat.bin) 字节（对比态二的 134,217,744）"
    echo "--- 可是初值到得了 CCM 吗？启动文件里只有一个拷贝循环 ---"
    "$NM" build/ccmat.elf | grep -E "_siccm|_sccm|_eccm|_sidata|_sdata|_edata"
    echo "startup 里引用过这些符号的次数：_sidata=$(grep -c '_sidata' "$STARTUP" || true) / _siccm=$(grep -c '_siccm' "$STARTUP" || true)"
    "$OD" -d --no-show-raw-insn build/ccmat.elf | sed -n '/<Reset_Handler>:/,/^$/p' | head -24
    echo "循环只有一对 ldr/str（_sdata.._edata ← _sidata）；_siccm 三个门牌立在那儿没人走。"
    echo "=> CCM 里放带初值的全局 = 上电读到随机值。要真用，得自己在启动文件补第二段拷贝。"
}

trace_probe() {
    echo "############ 第 6 刀：链接器自己交代它干了什么 ############"
    echo "--- 6a：--print-memory-usage（每块地的账）---"
    "$CC" build/startup.o build/main.o $MCU -T "$LDSCRIPT" $LDFLAGS \
        -Wl,--print-memory-usage -o build/trace.elf 2>&1 | lmsg
    echo "这一刀用的是 blink：FLASH 660 B 正好等于 blink.bin 的字节数（0x188 向量表 + 0x10c 代码），"
    echo "RAM 1536 B 却一个真实变量都没有——全部来自 ._user_heap_stack 那笔预留。"
    echo "--- 6b：--trace（谁被链进来了；库那几行只留 thumb/ 以后，前面是机器路径）---"
    "$CC" build/startup.o build/main.o $MCU -T "$LDSCRIPT" $LDFLAGS \
        -Wl,--trace -o build/trace.elf 2>&1 | head -8 \
        | awk '{ i = index($0, "thumb/"); if (i) print "  …" substr($0, i); else print }'
    echo "thumb/v7e-m+fp/hard —— 这就是 -mfpu=fpv4-sp-d16 -mfloat-abi=hard 换来的多架构目录，"
    echo "换成 soft-float 会去另一个目录找库；找不到就是那一类'明明装了库却报 cannot find -lgcc'的坑。"
    echo "--- 6c：ld --verbose（不 -T 时它默认用哪张图纸）---"
    "$LD" --verbose | sed -n '/Supported emulations/,/ENTRY/p' | head -12
}

case "${1:-all}" in
    keep)     need; build_base; keep_probe ;;
    at)       need; build_base; at_probe ;;
    overflow) need; build_base; overflow_probe ;;
    flags)    need; build_base; flags_probe ;;
    ccm)      need; build_base; ccm_probe ;;
    trace)    need; build_base; trace_probe ;;
    all)      need; build_base; keep_probe; echo; at_probe; echo; overflow_probe; echo;
              flags_probe; echo; ccm_probe; echo; trace_probe ;;
    clean)    rm -rf build ;;
    *)        echo "用法：sh probe.sh [keep|at|overflow|flags|ccm|trace|clean]" >&2; exit 1 ;;
esac
