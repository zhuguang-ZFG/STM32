#!/bin/sh
# probe.sh —— F3《调度器：一条 CLZ 选出下一个任务》全部取证，一条命令跑完
#
#   sh probe.sh          七步取证（见下面每一步的标题）
#   sh probe.sh clean    删 build/
#
# 这一集的取证对象是上游 FreeRTOS-Kernel 的 tasks.c 与 list.c 本身：
# 只编不链、不要开发板——同一条选择逻辑的两副面孔，是编译期由一个配置宏分出来的，
# 所以把那个宏掰成 0 / 1 / 不写，就能拿到两份可以逐条对照的机身。
#
# 旋钮都在 FreeRTOSConfig.h 里读这两个 -D：
#   -DSCHED_SEL=0|1   → configUSE_PORT_OPTIMISED_TASK_SELECTION
#   -DNPRIO=n         → configMAX_PRIORITIES
#
# 需要：arm-none-eabi-gcc / objdump / size 与 FreeRTOS-Kernel V11.1.0。
#   内核路径默认 ../../../.trellis/ref/freertos-v11/kernel，可用 FREERTOS_KERNEL=... 覆盖。
#   本机装了 xpack 15.2.1 就钉它，没装退回 PATH 里默认那把。
#
# 产物一律落在 build/（code/**/build/ 已 gitignore）。

set -e
cd "$(dirname "$0")"

XPACK=${XPACK:-/d/zhugu-home/tools/armgcc/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin}
[ -d "$XPACK" ] && PATH="$XPACK:$PATH"

if [ "$1" = "clean" ]; then
    rm -rf build
    exit 0
fi

ARMPREFIX=${ARM_PREFIX:-arm-none-eabi-}
K=${FREERTOS_KERNEL:-../../../.trellis/ref/freertos-v11/kernel}

# 这两样缺任何一样，本取证就没有存在意义（宿主侧那一步不足以支撑这一集），
# 所以是硬失败，不静默跳过——CI 的 arm-host 作业两样都装了。
command -v "${ARMPREFIX}gcc" >/dev/null 2>&1 || { echo "找不到 ${ARMPREFIX}gcc"; exit 1; }
[ -f "$K/tasks.c" ] || { echo "找不到内核 $K/tasks.c（FREERTOS_KERNEL= 可覆盖）"; exit 1; }
KC=$(grep -n '#define tskKERNEL_VERSION_NUMBER' "$K/include/task.h" | head -1)

mkdir -p build/opt build/omit build/gen build/gen33 build/opt_o2

MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
INC="-I. -I$K/include -I$K/portable/GCC/ARM_CM4F"
# 内核源文件按上游原样编：-Wall -Wextra 的零警告口径只管我们自己的代码。
# 刻意 -O0：优化会把两条路的形状抹平（-O2 下通用版也不再像循环），
# 逐条对照要的是源码结构本身。第 2 步末尾另编一份 -O2 专门验这句话。
# 优化档位【不在】BASE 里：-O 是"最后一个说了算"的开关，写进 BASE 会把
# build_tasks 传进来的那一档吃掉，两份产物长得一模一样还以为是巧合。
BASE="$MCU -std=c11 $INC -ffunction-sections -fdata-sections"

build_tasks() {  # build_tasks 目录名 OPTDEF NPRIO OPTLEVEL
    "${ARMPREFIX}gcc" -O${4:-0} $BASE ${2:+$2} -DNPRIO=$3 -c "$K/tasks.c" -o "build/$1/tasks.o"
}

FAIL=0
need() { # need 说明 命令…：命令成功＝[中]
    _d=$1; shift
    if "$@" >/dev/null 2>&1; then
        echo "  [中] $_d"
    else
        echo "  [失] $_d" >&2; FAIL=1
    fi
}
have() { # have 反汇编文件 正则 说明：机身里必须有
    _d=$1; _re=$2; _w=$3
    if grep -qE "$_re" "$_d"; then
        echo "  [中] $_w"
    else
        echo "  [失] $_w（$_d 里没有 $_re）" >&2; FAIL=1
    fi
}
lack() { # lack 反汇编文件 正则 说明：机身里必须没有
    _d=$1; _re=$2; _w=$3
    if grep -qE "$_re" "$_d"; then
        echo "  [失] $_w（$_d 里居然有 $_re）" >&2; FAIL=1
    else
        echo "  [中] $_w"
    fi
}
# 后向跳转 = 循环。-O0 + 分段的 objdump 不印 .L 标号，而是印
# "当前地址: 助记符 目标地址 <函数+偏移>"，所以拿目标地址和当前地址比大小。
back_edges() {
    awk '
        function h2d(s, i, c, v) {
            v = 0
            for (i = 1; i <= length(s); i++) {
                c = substr(s, i, 1)
                v = v * 16 + index("0123456789abcdef", tolower(c)) - 1
            }
            return v
        }
        /^[[:space:]]*[0-9a-f]+:[[:space:]]/ {
            cur = $1; sub(/:$/, "", cur)
            m = $2; sub(/\.[nw]$/, "", m)
            if (m ~ /^(b|beq|bne|bcs|bcc|bhs|blo|bmi|bpl|bvs|bvc|bhi|bls|bge|bgt|ble|blt|bal|cbz|cbnz)$/ &&
                $3 ~ /^[0-9a-f]+$/ && h2d($3) <= h2d(cur)) print
        }' "$1"
}
N_INS() { grep -cE '^[[:space:]]+[0-9a-f]+:' "$1"; }
cred() { # cred 说明 内核原文：打印行号，并且【找不到就失败】
    _d=$1; _re=$2
    if grep -q "$_re" "$K/tasks.c"; then
        grep -n "$_re" "$K/tasks.c" | head -3 | sed "s|^|  凭据($_d) tasks.c:|"
    else
        echo "  [失] 内核里没有『$_re』——$_d 那句话的来源要重核" >&2; FAIL=1
    fi
}
noloop() { # noloop 反汇编文件 说明
    if [ -z "$(back_edges "$1")" ]; then echo "  [中] $2"; else echo "  [失] $2（$1 里有后向跳转）" >&2; FAIL=1; fi
}
loop() { # loop 反汇编文件 说明
    if [ -n "$(back_edges "$1")" ]; then echo "  [中] $2"; else echo "  [失] $2（$1 里找不到循环）" >&2; FAIL=1; fi
}

echo "== F3 调度器取证 =="
echo "交叉工具链：$("${ARMPREFIX}gcc" -dumpfullversion)；内核：$KC"
echo "内核路径：$K"
echo

echo "############ 1. 走哪条路，是谁说了算 ############"
echo "----- tasks.c 里的分岔口 -----"
grep -n "configUSE_PORT_OPTIMISED_TASK_SELECTION == 0" "$K/tasks.c" | sed 's|^|  |'
echo "----- 端口层的默认值（ARM_CM4F portmacro.h）-----"
grep -n -A3 "^#ifndef configUSE_PORT_OPTIMISED_TASK_SELECTION" "$K/portable/GCC/ARM_CM4F/portmacro.h" | sed 's|^|  |'
echo "----- 但通用层 FreeRTOS.h 也留了一份默认值 -----"
grep -n -A2 "^#ifndef configUSE_PORT_OPTIMISED_TASK_SELECTION" "$K/include/FreeRTOS.h" | sed 's|^|  |'
echo "----- 谁先生效？看 FreeRTOS.h 的 include 顺序 -----"
grep -n "#include \"FreeRTOSConfig.h\"\|#include \"portable.h\"" "$K/include/FreeRTOS.h" | sed 's|^|  |'
echo "----- 两条路共用的那一个变量（同一行声明，两种语义）-----"
grep -n "uxTopReadyPriority = tskIDLE_PRIORITY;" "$K/tasks.c" | sed 's|^|  |'
echo
echo "----- 实测：配置文件里【不写】这一行，和【写 1】是不是同一份机身 -----"
build_tasks omit "" 5 0
build_tasks opt  "-DSCHED_SEL=1" 5 0
build_tasks gen  "-DSCHED_SEL=0" 5 0
for v in opt omit gen; do
    "${ARMPREFIX}objdump" -d --no-show-raw-insn "build/$v/tasks.o" > "build/$v/tasks.dis"
done
need "不写 = 写 1：两份 tasks.o 逐字节相同" cmp "build/opt/tasks.o" "build/omit/tasks.o"
need "写 0 是另一份机身：opt 与 gen 不同" sh -c 'cmp -s build/opt/tasks.o build/gen/tasks.o; test $? = 1'
printf '  三者的 .text.vTaskSwitchContext 大小：'
for v in opt omit gen; do
    printf '%s=%s ' "$v" "$("${ARMPREFIX}size" -A "build/$v/tasks.o" | awk '/\.text\.vTaskSwitchContext/{print $2}')"
done
echo "字节"

echo
echo "############ 2. 机身对照：一条 clz vs 一个往下摸的循环 ############"
"${ARMPREFIX}objdump" -d --no-show-raw-insn --section=.text.vTaskSwitchContext \
    build/opt/tasks.o | sed -n '/<vTaskSwitchContext>:/,/^$/p' > build/opt/vsc.dis
"${ARMPREFIX}objdump" -d --no-show-raw-insn --section=.text.vTaskSwitchContext \
    build/gen/tasks.o | sed -n '/<vTaskSwitchContext>:/,/^$/p' > build/gen/vsc.dis
echo "----- 位图路（SCHED_SEL=1）：选出最高优先级那几条 -----"
sed -n '/str	r3, \[r7, #4\]/,/lsls	r3, r3, #2/p' build/opt/vsc.dis | sed 's|^|  |'
echo "----- 通用路（SCHED_SEL=0）：判空 + 递减那个循环 -----"
sed -n '/ldr	r1, \[pc,/,/beq\.n/p' build/gen/vsc.dis | sed 's|^|  |'
echo "----- 账 -----"
printf '  位图路 vTaskSwitchContext：%s 条指令，后向跳转 %s 条\n' \
    "$(N_INS build/opt/vsc.dis)" "$(back_edges build/opt/vsc.dis | grep -c . || true)"
printf '  通用路 vTaskSwitchContext：%s 条指令，后向跳转 %s 条\n' \
    "$(N_INS build/gen/vsc.dis)" "$(back_edges build/gen/vsc.dis | grep -c . || true)"
have build/opt/vsc.dis 'clz\s+r[0-9]+, *r[0-9]+' '位图路里真的有 clz'
have build/opt/vsc.dis 'rsb\s+r[0-9]+, *r[0-9]+, *#31' '位图路里真的有 31 - clz（rsb #31）'
noloop build/opt/vsc.dis '位图路整个函数没有往回绕的边：选优不循环'
lack build/opt/vsc.dis 'sub(s|\.w)?\s+r[0-9]+, *(r[0-9]+, *)?#1' '位图路里没有 --uxTopPriority'
have build/gen/vsc.dis 'sub(s|\.w)?\s+r[0-9]+, *(r[0-9]+, *)?#1' '通用路里确实逐层减 1'
loop build/gen/vsc.dis '通用路有往回绕的边（= 那个往下摸的循环）'
back_edges build/gen/vsc.dis | sed 's|^|  后向边：|'
lack build/gen/vsc.dis 'clz' '通用路里一个 clz 都没有'
echo "----- 那句『clz 之后要过一遍 uint8_t』：ucPortCountLeadingZeros 返回 uint8_t -----"
grep -n -A5 "static inline uint8_t ucPortCountLeadingZeros" "$K/portable/GCC/ARM_CM4F/portmacro.h" | sed 's|^|  |'
have build/opt/vsc.dis 'strb\s+r[0-9]+, \[r' 'clz 的结果 -O0 先按字节存一次（uint8_t 返回类型留的疤）'
echo "----- 换个优化档验一次：形状不是 -O0 的产物 -----"
build_tasks opt_o2 "-DSCHED_SEL=1" 5 2
"${ARMPREFIX}objdump" -d --no-show-raw-insn --section=.text.vTaskSwitchContext \
    build/opt_o2/tasks.o | sed -n '/<vTaskSwitchContext>:/,/^$/p' > build/opt_o2/vsc.dis
sed -n '/clz/,/rsb/p' build/opt_o2/vsc.dis | sed 's|^|  |'
have build/opt_o2/vsc.dis 'clz' '-O2 下 clz 还在：一条指令选优不是 -O0 才有的形状'
have build/opt_o2/vsc.dis '(uxtb|strb)' '那次 uint8_t 截断在 -O2 也活着（搬进寄存器 uxtb，或仍落内存 strb）'
B0=$("${ARMPREFIX}size" -A build/opt/tasks.o | awk '/\.text\.vTaskSwitchContext/{print $2}')
B2=$("${ARMPREFIX}size" -A build/opt_o2/tasks.o | awk '/\.text\.vTaskSwitchContext/{print $2}')
need "-O2 的机身比 -O0 短（$B2 < $B0 字节）" test "$B2" -lt "$B0"
lack build/opt_o2/vsc.dis 'sub(s|\.w)?\s+r[0-9]+, *(r[0-9]+, *)?#1' '-O2 也没有凭空长出递减循环'
printf '  同一函数两种档的段大小：-O0 %s 字节，-O2 %s 字节\n' "$B0" "$B2"

echo
echo "############ 3. 循环到底跑几遍：把两条路的规则抄成模拟器跑一遍 ############"
HOSTCC=${CC:-gcc}
"$HOSTCC" -std=c11 -Wall -Wextra -Werror -O2 scan_cost.c -o build/scan_cost.exe
./build/scan_cost.exe | tee build/scan_cost.txt | sed -n '/场景二/,/^$/p'
echo "----- 一致性门禁：模拟器里两条路每一次选出的优先级都必须相同 -----"
need "n=5：两条路分歧 0 次" grep -F "（configMAX_PRIORITIES = 5）" build/scan_cost.txt
awk '/configMAX_PRIORITIES = 5）/{f=1} f&&/不同优先级的次数/{print; exit}' build/scan_cost.txt \
    | grep -q "= 0$" && echo "  [中] n=5 分歧次数 = 0" || { echo "  [失] n=5 两条路选出了不同的优先级" >&2; FAIL=1; }
awk '/configMAX_PRIORITIES = 32）/{f=1} f&&/不同优先级的次数/{print; exit}' build/scan_cost.txt \
    | grep -q "= 0$" && echo "  [中] n=32 分歧次数 = 0" || { echo "  [失] n=32 两条路选出了不同的优先级" >&2; FAIL=1; }
echo "----- 累计次数（同一张事件表）-----"
grep -E "通用路累计|位图路累计|最坏那一次" build/scan_cost.txt | sed 's|^|  |'

echo
echo "############ 4. RAM 账：每多一个优先级收多少租 ############"
build_tasks gen33 "-DSCHED_SEL=0" 33 0
S5=$("${ARMPREFIX}size" -A build/gen/tasks.o | awk '/\.bss\.pxReadyTasksLists/{print $2}')
S33=$("${ARMPREFIX}size" -A build/gen33/tasks.o | awk '/\.bss\.pxReadyTasksLists/{print $2}')
P5=$("${ARMPREFIX}size" -A build/gen/tasks.o | awk '/\.bss\.uxTopReadyPriority/{print $2}')
P33=$("${ARMPREFIX}size" -A build/gen33/tasks.o | awk '/\.bss\.uxTopReadyPriority/{print $2}')
printf '  configMAX_PRIORITIES=5  → .bss.pxReadyTasksLists = %s 字节；uxTopReadyPriority = %s 字节\n' "$S5" "$P5"
printf '  configMAX_PRIORITIES=33 → .bss.pxReadyTasksLists = %s 字节；uxTopReadyPriority = %s 字节\n' "$S33" "$P33"
PER=$(( (S33 - S5) / (33 - 5) ))
echo "  不查文档，用两个测量反推：sizeof(List_t) = ($S33 − $S5) ÷ (33 − 5) = $PER 字节"
need "每级一条链表，链表体 20 字节" test "$PER" -eq 20
need "两个 configMAX_PRIORITIES 都整除" sh -c "test $((S5 % 20)) -eq 0 -a $((S33 % 20)) -eq 0"
echo "  这 20 字节的构成（list.h:172-179，configUSE_LIST_DATA_INTEGRITY_CHECK_BYTES=0）："
sed -n '/^typedef struct xLIST/,/^} List_t;/p' "$K/include/list.h" | grep -vE "^\s*/\*\*|^\s*$" | sed 's|^|    |'
echo "  = uxNumberOfItems 4 + pxIndex 4 + xListEnd(MiniListItem_t) 12 = 20"
echo "  速查器本身两边都是 $P5 字节：位图也好标量也好，都只是那个 volatile UBaseType_t。"
echo "----- 索引算术在机身里长什么样：i*20 拆成 (i*4+i)*4 -----"
sed -n '/lsls	r3, r3, #2/,/add	r3, r1/p' build/gen/vsc.dis | sed 's|^|  |'

echo
echo "############ 5. 位图只有 32 位：33 级优先级会被谁拦下来 ############"
echo "----- 通用路：33 级编得过（第 4 步刚编的）-----"
printf '  gen33/tasks.o 编出来了，pxReadyTasksLists = %s 字节\n' "$S33"
echo "----- 位图路：同一个 NPRIO=33 交给编译器 -----"
if "${ARMPREFIX}gcc" $BASE -DSCHED_SEL=1 -DNPRIO=33 -c "$K/tasks.c" -o build/should_fail.o 2> build/err.txt; then
    echo "  [失] NPRIO=33 + SCHED_SEL=1 竟然编过了" >&2; FAIL=1
else
    echo "  [中] 编译器当场拒绝，原文："
    sed 's|^|    |' build/err.txt | head -4
fi
need "被拒的那一次没有留下目标文件" test ! -f build/should_fail.o
echo "----- 拦人的是哪一行 -----"
grep -n "can only be set to 1 when configMAX_PRIORITIES is less than or equal to 32" \
    "$K/portable/GCC/ARM_CM4F/portmacro.h" | sed 's|^|  |'
echo "  注意这条 #error 在【端口头文件】里，不在 tasks.c 里；"
echo "  同一条约束在 RT-Thread 那边是两套位图（32×8 = 256 级），本站 F5 有对照。"

echo
echo "############ 6. tick 干的三件事，在机身里就这三段 ############"
for v in opt gen; do
    "${ARMPREFIX}objdump" -d --no-show-raw-insn --section=.text.xTaskIncrementTick \
        "build/$v/tasks.o" | sed -n '/<xTaskIncrementTick>:/,/^$/p' > "build/$v/tick.dis"
done
echo "----- 第一段：节拍++（xTickCount = xConstTickCount）-----"
cred "节拍++" "xTickCount = xConstTickCount;"
awk '$2 ~ /^add/ && $0 ~ /#1/ {print "  机身：" $0; exit}' build/opt/tick.dis
have build/opt/tick.dis 'add(s|\.w)?\s+r[0-9]+, *(r[0-9]+, *)?#1' 'tick 函数里确实有一条 +1'
echo "----- 第二段：剪枝那一句比较，出现在函数前半段就跳走 -----"
cred "剪枝" "if( xConstTickCount >= xNextTaskUnblockTime )"
TOTAL=$(grep -cE '^[[:space:]]+[0-9a-f]+:' build/opt/tick.dis)
IDX=$(awk '/^[[:space:]]*[0-9a-f]+:/{n++} $2=="cmp" && $4 ~ /^r/{print n; exit}' build/opt/tick.dis)
: "${IDX:=0}"
awk -v n="$IDX" 'n>0 && NR>=n && NR<=n+4' build/opt/tick.dis | sed 's|^|  剪枝现场：|'
# 谁在谁前面，是源码说的；机身里排第几条，是编译器版本说的。所以顺序押源码，
# 位置只报数不判分——换一把编译器不至于把这条断言变红。
L_PRUNE=$(grep -n "if( xConstTickCount >= xNextTaskUnblockTime )" "$K/tasks.c" | head -1 | cut -d: -f1)
L_WAKE=$(grep -n "pxTCB = listGET_OWNER_OF_HEAD_ENTRY( pxDelayedTaskList )" "$K/tasks.c" | head -1 | cut -d: -f1)
L_SWITCH=$(grep -n "xSwitchRequired = pdTRUE" "$K/tasks.c" | head -1 | cut -d: -f1)
printf '  那次寄存器间比较是函数第 %s 条指令，整个 xTaskIncrementTick 在 -O0 机身上共 %s 条。\n' "$IDX" "$TOTAL"
printf '  源码顺序：剪枝 %s 行 → 醒人循环 %s 行 → 请求切换 %s 行。\n' "$L_PRUNE" "$L_WAKE" "$L_SWITCH"
need "机身里找得到那次剪枝比较" test "$IDX" -gt 0
need "剪枝判空在醒人循环之前（$L_PRUNE < $L_WAKE）" test "$L_PRUNE" -lt "$L_WAKE"
need "醒人循环在请求切换之前（$L_WAKE < $L_SWITCH）" test "$L_WAKE" -lt "$L_SWITCH"
echo "----- 队首才是关键：延时链表按 xItemValue 排序，所以只看队首 -----"
grep -n "listLIST_IS_EMPTY( pxDelayedTaskList )" "$K/tasks.c" | head -3 | sed 's|^|  |'
grep -n "pxDelayedTaskList->xListEnd\|pxNext->xItemValue" "$K/tasks.c" | head -4 | sed 's|^|  |'
echo "----- 第三段：请求切换（V11 里是 xSwitchRequired，PendSV 的挂法见 F2）-----"
cred "请求切换" "xSwitchRequired = pdTRUE"
echo "----- 调度器被暂停时这一拍只记账不选人：看函数开头那十几条 -----"
sed -n '1,13p' build/opt/tick.dis | sed 's|^|  |'
cred "暂停期记账" "xPendedTicks++"
echo "----- vTaskDelay：挂表 → 恢复调度 → 让出，没有一句「等」-----"
cred "vTaskDelay 定义" "void vTaskDelay( const TickType_t xTicksToDelay )"
grep -n "prvAddCurrentTaskToDelayedList( xTicksToDelay, pdFALSE )\|taskYIELD_WITHIN_API();" "$K/tasks.c" | head -4 | sed 's|^|  |'
"${ARMPREFIX}objdump" -t build/opt/tasks.o | grep -E "xNextTaskUnblockTime|pxDelayedTaskList|xTickCount|uxTopReadyPriority|pxReadyTasksLists" | sed 's|^|  符号表：|'

echo
echo "############ 7. 链表两兄弟：一个管轮转，一个管守时 ############"
for v in opt gen; do
    "${ARMPREFIX}gcc" -O0 $BASE -DNPRIO=5 -c "$K/list.c" -o "build/$v/list.o"
    "${ARMPREFIX}objdump" -d --no-show-raw-insn --section=.text.vListInsertEnd --section=.text.vListInsert \
        "build/$v/list.o" > "build/$v/lists.dis"
done
sed -n '/<vListInsertEnd>:/,/^$/p' build/opt/lists.dis > build/lend.dis
sed -n '/<vListInsert>:/,/^$/p' build/opt/lists.dis > build/lins.dis
LEND=build/lend.dis
LINS=build/lins.dis
echo "----- vListInsertEnd：就绪链表用，插队尾，四根指针 -----"
sed 's|^|  |' "$LEND"
echo "----- vListInsert：延时链表用，按 xItemValue 找位置 -----"
sed 's|^|  |' "$LINS"
echo "----- 账 -----"
printf '  vListInsertEnd：%s 条指令，后向跳转 %s 条\n' "$(N_INS "$LEND")" "$(back_edges "$LEND" | grep -c . || true)"
printf '  vListInsert   ：%s 条指令，后向跳转 %s 条\n' "$(N_INS "$LINS")" "$(back_edges "$LINS" | grep -c . || true)"
noloop "$LEND" 'vListInsertEnd 没有循环：插就绪链表队尾是 O(1)'
loop   "$LINS" 'vListInsert 有循环：按 xItemValue 找位置是 O(n)'
back_edges "$LINS" | sed 's|^|  后向边：|'
echo "----- 为什么延时表敢只查队首：插入按 xItemValue 排 -----"
grep -n -B2 -A6 "for( pxIterator = ( ListItem_t \* ) &( pxList->xListEnd )" "$K/list.c" | sed 's|^|  |'

echo
if [ "$FAIL" = 0 ]; then
    echo "== 全部断言通过 =="
else
    echo "== 有断言失败 ==" >&2
    exit 1
fi
