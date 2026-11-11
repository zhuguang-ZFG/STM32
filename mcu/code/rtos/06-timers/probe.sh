#!/bin/sh
# probe.sh —— F6《软件定时器：这笔 RAM 账与那一条串行队列》全部取证，一条命令跑完
#
#   sh probe.sh          七步取证（见每一步的标题）
#   sh probe.sh clean    删 build/
#
# 这一集的取证对象是上游 FreeRTOS-Kernel V11.1.0 的 timers.c 本身，外加它调用的
# tasks.c / queue.c / heap_4.c。只编不链、不要开发板：
# "打开定时器要多少字节"是编译期就能量出来的事，"回调为什么必然串行"是控制流的事，
# 两样都不需要板子。唯一要跑起来的是第 7 步的分派模拟（宿主机 gcc，见 sim_daemon.c）。
#
# 旋钮都在 FreeRTOSConfig.h 里读这几个 -D：
#   -DPEND=0|1    → INCLUDE_xTimerPendFunctionCall（不传就交给内核默认值）
#   -DTRACE=n     → configUSE_TRACE_FACILITY
#   -DSTATS=n     → configUSE_STATS_FORMATTING_FUNCTIONS（默认跟着 TRACE）
#   -DQLEN=n      → configTIMER_QUEUE_LENGTH
#   -DSTACKW=n    → configTIMER_TASK_STACK_DEPTH（单位是字）
#
# 需要：arm-none-eabi-gcc / objdump / nm / size、宿主机 gcc 与 FreeRTOS-Kernel V11.1.0。
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

# 这几样缺任何一样，本取证就没有存在意义（宿主侧那一步不足以支撑这一集），
# 所以是硬失败，不静默跳过——CI 的 arm-host 作业全都装了。
command -v "${ARMPREFIX}gcc" >/dev/null 2>&1 || { echo "找不到 ${ARMPREFIX}gcc"; exit 1; }
command -v gcc >/dev/null 2>&1 || { echo "找不到宿主机 gcc（第 7 步的分派模拟要跑它）"; exit 1; }
[ -f "$K/timers.c" ] || { echo "找不到内核 $K/timers.c（FREERTOS_KERNEL= 可覆盖）"; exit 1; }
[ -f "$K/portable/MemMang/heap_4.c" ] || { echo "找不到 $K/portable/MemMang/heap_4.c"; exit 1; }
KC=$(grep -n '#define tskKERNEL_VERSION_NUMBER' "$K/include/task.h" | head -1)

mkdir -p build/sizes build/omit build/p0 build/p1 build/t0 build/q16 build/stats build/sim

MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
# -I$K 是为了 sizes_probe.c 能 #include "timers.c"：这些类型是文件内 static，
# 公开头文件里没有，唯一能"问内核自己"的路子就是把 .c 原文拿进来。
INC="-I. -I$K -I$K/include -I$K/portable/GCC/ARM_CM4F"
# 刻意 -O0：这一集比的是结构体形状与源码控制流，优化会把手型抹平。
# 注意 -O 不在 BASE 里：它是"最后一个说了算"的开关，写进 BASE 会把传进来的档位吃掉。
BASE="$MCU -std=c11 $INC -ffunction-sections -fdata-sections"
TC="$K/timers.c"
QC="$K/queue.c"
TSKC="$K/tasks.c"
HEAPC="$K/portable/MemMang/heap_4.c"
LISTC="$K/list.c"
FREH="$K/include/FreeRTOS.h"

FAIL=0
need() { # need 说明 命令…：命令成功＝[中]
    _d=$1; shift
    if "$@" >/dev/null 2>&1; then
        echo "  [中] $_d"
    else
        echo "  [失] $_d" >&2; FAIL=1
    fi
}
eq() { # eq 说明 实际 期望
    if [ "$2" = "$3" ]; then echo "  [中] $1（= $3）"; else echo "  [失] $1：实测 $2，期望 $3" >&2; FAIL=1; fi
}
ge() { # ge 说明 实际 下限
    if [ "$2" -ge "$3" ] 2>/dev/null; then echo "  [中] $1（$2 ≥ $3）"; else echo "  [失] $1：$2 不小于 $3" >&2; FAIL=1; fi
}
lt() { # lt 说明 实际 上限（严格小于）
    if [ "$2" -lt "$3" ] 2>/dev/null; then echo "  [中] $1（$2 < $3）"; else echo "  [失] $1：$2 不小于 $3" >&2; FAIL=1; fi
}
le() { # le 说明 实际 上限（小于等于）
    if [ "$2" -le "$3" ] 2>/dev/null; then echo "  [中] $1（$2 ≤ $3）"; else echo "  [失] $1：$2 超过 $3" >&2; FAIL=1; fi
}
gt() { # gt 说明 实际 下限（严格大于）
    if [ "$2" -gt "$3" ] 2>/dev/null; then echo "  [中] $1（$2 > $3）"; else echo "  [失] $1：$2 不大于 $3" >&2; FAIL=1; fi
}
h2d() { # h2d 十六进制串：自己换算，不依赖 gawk 的 strtonum
    printf '%s' "$1" | awk '
        function hv(s, i, c, v) {
            v = 0
            for (i = 1; i <= length(s); i++) {
                c = substr(s, i, 1)
                v = v * 16 + index("0123456789abcdef", tolower(c)) - 1
            }
            return v
        } { print hv($0) }'
}
sizeof_of() { # sizeof_of .o文件 probe名 → 十进制字节数（符号的 size 字段就是 sizeof）
    _o=$1; _s=$2
    _h=$("${ARMPREFIX}nm" --print-size "$_o" | awk -v n="$_s" '$4==n {print $2}')
    if [ -z "$_h" ]; then echo "NOSYM"; else h2d "$_h"; fi
}
sz_of() { # sz_of .o文件 section前缀 → 这些段的字节数之和（-fdata-sections 会把
          # 每个 static 拆成独立的 .bss.名字，所以必须按前缀求和，不能只认 .bss）
    "${ARMPREFIX}size" -A "$1" | awk -v s="$2" 'index($1, s)==1 { t += $2 } END { print t+0 }'
}
cred() { # cred 文件 说明 内核原文：打印行号，并且【找不到就失败】
    _f=$1; _d=$2; _re=$3
    if grep -q "$_re" "$_f"; then
        grep -n "$_re" "$_f" | head -3 | sed "s|^|  凭据($_d) $(basename "$_f"):|"
    else
        echo "  [失] $(basename "$_f") 里没有『$_re』——『$_d』那句话的来源要重核" >&2; FAIL=1
    fi
}
at_line() { # at_line 文件 行号 正则：第 7 步用；行号漂了就失败，不许悄悄给错的数
    _f=$1; _n=$2; _re=$3
    if sed -n "${_n}p" "$_f" | grep -q "$_re"; then
        echo "  [中] $(basename "$_f"):$_n 仍是『$_re』"
    else
        echo "  [失] $(basename "$_f"):$_n 已经不是『$_re』了——模拟器抄的规则要重核" >&2; FAIL=1
    fi
}
N_of() { grep -c "$1" "$2" || true; }   # N_of 固定串 文件：零命中也是合法答案，
                                        # 所以 || true 兜住 grep 的退出码，交给 eq 去判

# ---- 先把六个配置档全编出来（sizes_probe.c 是纯编译期仪器，不参与链接）----
build_sizes() { # build_sizes 目录名 其余 -D…
    _d=$1; shift
    "${ARMPREFIX}gcc" -O0 $BASE "$@" -c sizes_probe.c -o "build/$_d/s.o"
}
build_timers() { # build_timers 目录名 其余 -D…：把 timers.c 单独编一份，供逐字节比对与反汇编
    _d=$1; shift
    "${ARMPREFIX}gcc" -O0 $BASE "$@" -c "$TC" -o "build/$_d/timers.o"
}
queue_imm() { # queue_imm .o文件 r0|r1 → prvCheckForValidListAndQueue 送进
               # xQueueGenericCreate 的那颗立即数。timers.o 里这个调用点全文只有一处
               # （第 4 步会 assert），所以 -B2 取到的就是它的前两句 movs。
    "${ARMPREFIX}objdump" -drS "$1" \
        | grep -B2 'bl.*xQueueGenericCreate' \
        | grep -oE "movs[[:space:]]+$2, #[0-9]+" | head -1 | grep -oE '[0-9]+$' || true
}

echo "== F6 软件定时器取证 =="
echo "交叉工具链：$("${ARMPREFIX}gcc" -dumpfullversion)；宿主机 gcc：$(gcc -dumpversion)"
echo "内核：$KC"
echo "内核路径：$K"
echo

echo "############ 1. 配置里的数：让编译器报数，不抄配置 ############"
echo "----- 量法：在 include 了内核 .c 原文的探测文件里声明 char probe_x[sizeof(T)]；"
echo "       这个数组落在 .bss，nm --print-size 读到的符号大小就是 sizeof。"
echo "       不查文档、不数成员、不看优化：问内核自己。-----"
build_sizes sizes
build_sizes omit
build_sizes p0  -DPEND=0
build_sizes p1  -DPEND=1
build_sizes t0  -DTRACE=0
build_sizes q16 -DQLEN=16
QLEN=$(sizeof_of build/sizes/s.o probe_configTIMER_QUEUE_LENGTH)
STACKW=$(sizeof_of build/sizes/s.o probe_configTIMER_TASK_STACK_DEPTH)
MINS=$(sizeof_of build/sizes/s.o probe_configMINIMAL_STACK_SIZE)
NAMEL=$(sizeof_of build/sizes/s.o probe_configMAX_TASK_NAME_LEN)
eq "configTIMER_QUEUE_LENGTH" "$QLEN" 8
eq "configTIMER_TASK_STACK_DEPTH（单位是字）" "$STACKW" 256
eq "configMINIMAL_STACK_SIZE（单位是字）" "$MINS" 128
eq "configMAX_TASK_NAME_LEN + 1" "$NAMEL" 13
echo "----- 三个数在 timers.c 里到底是干什么用的 -----"
grep -n "configTIMER_TASK_STACK_DEPTH\|configTIMER_TASK_PRIORITY\|configTIMER_QUEUE_LENGTH" "$TC" \
    | sed 's|^|  |'
echo "----- 整套定时器只新增一个任务：建任务的调用点全在同一个函数里，且实参只有 prvTimerTask -----"
grep -n "xTaskCreate" "$TC" | sed 's|^|  |'
awk '/^    BaseType_t xTimerCreateTimerTask\( void \)$/{f=1} f{print} f&&/^    }$/{exit}' "$TC" \
    > build/ctt.txt
# 队列和两条到期表链表在另一个函数里，第 6 步要用它的体做对照
awk '/^    static void prvCheckForValidListAndQueue\( void \)$/{f=1} f{print} f&&/^    }$/{exit}' "$TC" \
    > build/cfvsq.txt
NALL=$(N_of 'xTaskCreate' "$TC")
NIN=$(N_of 'xTaskCreate' build/ctt.txt)
NEP=$(N_of 'prvTimerTask,' build/ctt.txt)
echo "  全文 xTaskCreate 调用点：$NALL ；xTimerCreateTimerTask 函数体内：$NIN"
eq "建任务调用点【全都在】xTimerCreateTimerTask 里（定时器系统不会为你多建任务）" "$NIN" "$NALL"
eq "这些调用点的第一个实参只有 prvTimerTask 一个名字" "$NEP" "$NIN"
ge "守护任务的优先级得来自配置而不是硬编码" "$(N_of 'configTIMER_TASK_PRIORITY' "$TC")" 1
cred "$TC" "守护任务的名字" '"Tmr Svc"'
echo

echo "############ 2. 回调只有一个执行线程 ############"
echo "----- 全内核唯一会调用用户回调的那四处 -----"
grep -n "pxCallbackFunction(" "$TC" | sed 's|^|  |'
eq "回调调用点总数" "$(N_of 'pxCallbackFunction(' "$TC")" 4
echo "----- 这四句分别落在哪三个 static 函数里 -----"
for f in prvReloadTimer prvProcessExpiredTimer prvProcessReceivedCommands; do
    cred "$TC" "回调调用点所属函数" "    static .*$f("
done
echo "----- 这三个函数又分别被谁调用：都只在 prvTimerTask 的调用树里 -----"
grep -n "prvProcessReceivedCommands();\|prvProcessTimerOrBlockTask(\|prvReloadTimer(\|prvProcessExpiredTimer(" "$TC" \
    | sed 's|^|  |'
cred "$TC" "守护任务主循环只调这一个" "prvProcessTimerOrBlockTask( xNextExpireTime, xListWasEmpty );"
cred "$TC" "排空命令队列" "prvProcessReceivedCommands();"
echo "----- 睡到下一拍到期，就是这一句 -----"
cred "$TC" "睡到下一拍" "vQueueWaitForMessageRestricted( xTimerQueue, ( xNextExpireTime - xTimeNow )"
echo "----- 一轮只处理到期表头部的那【一个】定时器 -----"
cred "$TC" "只取表头" "listGET_OWNER_OF_HEAD_ENTRY( pxCurrentTimerList )"
echo "----- 命令怎么进来：任务上下文会阻塞，调度器没跑就不等，中断上下文会丢 -----"
cred "$TC" "任务上下文发命令会阻塞" "xQueueSendToBack( xTimerQueue, &xMessage, xTicksToWait )"
cred "$TC" "调度器没跑起来就不等" "xQueueSendToBack( xTimerQueue, &xMessage, tmrNO_DELAY )"
cred "$TC" "中断上下文发命令" "xQueueSendToBackFromISR( xTimerQueue, &xMessage"
cred "$TC" "pend 的函数也在守护任务里跑" "pxCallback->pxCallbackFunction( pxCallback->pvParameter1"
echo

echo "############ 3. RAM 账：每个字节都是量出来的 ############"
echo "----- 本工程（照抄 01-freertos-lab 的配置）实测 -----"
for s in Timer_t StaticTimer_t DaemonTaskMessage_t List_t ListItem_t Queue_t StaticQueue_t TCB_t BlockLink_t; do
    printf '  %-26s %s B\n' "sizeof($s)" "$(sizeof_of build/sizes/s.o probe_sizeof_$s)"
done
S_TIMER=$(sizeof_of build/sizes/s.o probe_sizeof_Timer_t)
S_MSG=$(sizeof_of build/sizes/s.o probe_sizeof_DaemonTaskMessage_t)
S_LIST=$(sizeof_of build/sizes/s.o probe_sizeof_List_t)
S_QUEUE=$(sizeof_of build/sizes/s.o probe_sizeof_Queue_t)
S_TCB=$(sizeof_of build/sizes/s.o probe_sizeof_TCB_t)
S_LINK=$(sizeof_of build/sizes/s.o probe_sizeof_BlockLink_t)
S_ALIGN=$(sizeof_of build/sizes/s.o probe_portBYTE_ALIGNMENT)
eq "sizeof(List_t) 与 F3 独立量到的同一个数对齐（20）" "$S_LIST" 20
echo "----- 交叉核对：另一条完全独立的路子——反汇编里 pvPortMalloc 的那颗立即数 -----"
build_timers omit
"${ARMPREFIX}objdump" -drS build/omit/timers.o > build/omit/timers.dis
IMM=$(grep -B2 'bl.*pvPortMalloc' build/omit/timers.dis \
      | grep -oE 'movs[[:space:]]+r0, #[0-9]+' | head -1 | grep -oE '[0-9]+$')
echo "  xTimerCreate 里 pvPortMalloc( sizeof( Timer_t ) ) 的立即数：$IMM"
cred "$TC" "那句 malloc 本身" "pvPortMalloc( sizeof( Timer_t ) )"
eq "nm 量到的 sizeof(Timer_t) 与反汇编立即数一致" "$S_TIMER" "$IMM"
echo "----- 第三条路子：静态对象的段大小（这两条到期表链表根本不走堆）-----"
"${ARMPREFIX}nm" --print-size build/omit/timers.o | grep ' b ' | sed 's|^|  |'
BSS=$(sz_of build/omit/timers.o .bss)
printf '  timers.o 的 .bss：%s 字节（编译期就钉死，configTOTAL_HEAP_SIZE 管不到它）\n' "$BSS"
NEED_BSS=$(( S_LIST * 2 + 4 * 4 ))
ge "两条到期表链表 + 四个指针，至少占 .bss 的这么多" "$BSS" "$NEED_BSS"
echo "----- heap_4 每笔 malloc 的抽头（两个输入都是量出来的，不是查表的）-----"
cred "$HEAPC" "抽头公式" "xWantedSize += xHeapStructSize"
cred "$HEAPC" "对齐补头" "xWantedSize += xAdditionalRequiredSize"
cred "$HEAPC" "块结构体" "} BlockLink_t;"
printf '  sizeof(BlockLink_t)=%s  portBYTE_ALIGNMENT=%s\n' "$S_LINK" "$S_ALIGN"
need "抽头 = (BlockLink_t 向上取整到对齐边界) 的算式在源码里" \
    sh -c "grep -q 'sizeof( BlockLink_t ) + ( ( size_t ) ( portBYTE_ALIGNMENT - 1 ) )' '$HEAPC'"
echo

echo "############ 4. PEND 那一档：默认值是谁定的，开它要付多少 ############"
echo "----- 内核自己留的默认值（lab 的 FreeRTOSConfig.h 一个字都没写这一行）-----"
cred "$FREH" "INCLUDE_xTimerPendFunctionCall 的默认值" "#define INCLUDE_xTimerPendFunctionCall    0"
echo "----- 于是【不写】必须和【写 0】逐字节相同：这是默认值的直接证据 -----"
build_timers omit
build_timers p0 -DPEND=0
build_timers p1 -DPEND=1
need "不写 PEND 的 timers.o 与 -DPEND=0 的 timers.o 逐字节相同（＝默认就是 0）" \
    cmp -s build/omit/timers.o build/p0/timers.o
if cmp -s build/omit/timers.o build/p1/timers.o; then
    echo "  [失] -DPEND=1 的 timers.o 竟然和不写一样大——这一档没有开关作用，取证前提塌了" >&2; FAIL=1
else
    echo "  [中] -DPEND=1 的 timers.o 与不写的逐字节不同（开关确实改机器码）"
fi
printf '  体积：不写 %s B，-DPEND=0 %s B，-DPEND=1 %s B\n' \
    "$(wc -c < build/omit/timers.o | tr -d ' ')" \
    "$(wc -c < build/p0/timers.o | tr -d ' ')" \
    "$(wc -c < build/p1/timers.o | tr -d ' ')"
echo "----- 开了 PEND 才存在的两个对外 API -----"
# 这里的 diff 用两个临时文件而不是 <(…)：本脚本是 #!/bin/sh，进程替换是 bash 方言，
# CI 上的 /bin/sh 未必认。
"${ARMPREFIX}nm" build/omit/timers.o | awk '{print $3}' | sort > build/nm-omit.txt
"${ARMPREFIX}nm" build/p1/timers.o  | awk '{print $3}' | sort > build/nm-p1.txt
PDIFF=$(diff build/nm-omit.txt build/nm-p1.txt | grep '^> ' | awk '{print $2}' | tr '\n' ' ')
echo "  p1 相对不写多出的符号：$PDIFF"
need "多出来的正是 xTimerPendFunctionCall / xTimerPendFunctionCallFromISR 两个" \
    sh -c "printf '%s' '$PDIFF' | grep -q 'xTimerPendFunctionCall xTimerPendFunctionCallFromISR'"
eq "多出的符号个数" "$(printf '%s' "$PDIFF" | wc -w | tr -d ' ')" 2
echo "----- 消息体为什么变大：上游在结构体里写明了原因 -----"
cred "$TC" "上游自己说明为什么默认不带回调参数" "it makes the structure (and therefore the timer queue) larger"
cred "$TC" "那个条件编译就是按 INCLUDE 开关切的" "#if ( INCLUDE_xTimerPendFunctionCall == 1 )"
MSG0=$(sizeof_of build/omit/s.o probe_sizeof_DaemonTaskMessage_t)
MSG1=$(sizeof_of build/p1/s.o probe_sizeof_DaemonTaskMessage_t)
MSGP0=$(sizeof_of build/p0/s.o probe_sizeof_DaemonTaskMessage_t)
eq "不写的 sizeof(DaemonTaskMessage_t)" "$MSG0" 12
eq "-DPEND=0 与不写同值" "$MSGP0" "$MSG0"
eq "-DPEND=1 的 sizeof(DaemonTaskMessage_t)" "$MSG1" 16
echo "----- 第三条路子：队列建起来那两句的立即数（长度 × 消息大小直接写在机器码里）-----"
eq "timers.o 全文只有一处 xQueueGenericCreate 调用点（所以 -B2 取的必然是它）" \
   "$(N_of 'bl.*xQueueGenericCreate' build/omit/timers.dis)" 1
echo "  不写：xQueueGenericCreate( $(queue_imm build/omit/timers.o r0), $(queue_imm build/omit/timers.o r1) )"
echo "  PEND=1：xQueueGenericCreate( $(queue_imm build/p1/timers.o r0), $(queue_imm build/p1/timers.o r1) )"
eq "反汇编里的队列长度 = 配置值（PEND 不改长度）" "$(queue_imm build/p1/timers.o r0)" "$QLEN"
eq "反汇编里的消息大小 = nm 量到的 sizeof（不写）" "$(queue_imm build/omit/timers.o r1)" "$MSG0"
eq "反汇编里的消息大小 = nm 量到的 sizeof（PEND=1）" "$(queue_imm build/p1/timers.o r1)" "$MSG1"
PAY0=$(( QLEN * MSG0 )); PAY1=$(( QLEN * MSG1 ))
printf '  这笔开关费：%d × %d = %d B 变成 %d × %d = %d B，队列数据区涨 %d B（第 6 步把它算进总账）\n' \
    "$QLEN" "$MSG0" "$PAY0" "$QLEN" "$MSG1" "$PAY1" $(( PAY1 - PAY0 ))
echo "----- 队列长度是另一个独立旋钮：-DQLEN ----- "
QL16=$(sizeof_of build/q16/s.o probe_configTIMER_QUEUE_LENGTH)
eq "-DQLEN=16 确实把配置读成了 16" "$QL16" 16
build_timers q16 -DQLEN=16
eq "-DQLEN=16 的队列长度立即数跟着变（消息大小不变）" "$(queue_imm build/q16/timers.o r0)" "$QL16"
eq "-DQLEN=16 的消息大小仍是 $MSG0" "$(queue_imm build/q16/timers.o r1)" "$MSG0"
printf '  长度费：%d × %d = %d B 变成 %d × %d = %d B，涨 %d B\n' \
    "$QLEN" "$MSG0" "$PAY0" "$QL16" "$MSG0" "$(( QL16 * MSG0 ))" \
    $(( QL16 * MSG0 - PAY0 ))
echo

echo "############ 5. TRACE 那一档：编号税，和一条会把你拦在外面的 #error ############"
echo "----- configUSE_TRACE_FACILITY 给每个对象挂一个"
echo "       供 trace 工具反查的编号；对象一个都没被 trace 时，这笔钱也照收 -----"
cred "$TC" "Timer_t 里那个字段就是它" "UBaseType_t uxTimerNumber;"
cred "$QC" "Queue_t 里对应的那一个" "UBaseType_t uxQueueNumber;"
cred "$TSKC" "TCB_t 里对应的那一个" "UBaseType_t uxTCBNumber;"
echo "----- 实测：同一份探测文件，只把 TRACE 从 1 改成 0 -----"
printf '  %-24s %10s %10s %8s\n' 对象 TRACE=1 TRACE=0 差
for s in Timer_t StaticTimer_t Queue_t StaticQueue_t TCB_t; do
    A=$(sizeof_of build/sizes/s.o probe_sizeof_$s)
    B=$(sizeof_of build/t0/s.o probe_sizeof_$s)
    printf '  %-24s %8s B %8s B %6s B\n' "sizeof($s)" "$A" "$B" "$(( A - B ))"
done
eq "Timer_t：TRACE=1 44 / TRACE=0 40" "$(sizeof_of build/t0/s.o probe_sizeof_Timer_t)" 40
eq "TCB_t：TRACE=1 88 / TRACE=0 80" "$(sizeof_of build/t0/s.o probe_sizeof_TCB_t)" 80
eq "Queue_t：TRACE=1 80 / TRACE=0 72" "$(sizeof_of build/t0/s.o probe_sizeof_Queue_t)" 72
eq "静态版和动态版同尺寸（Timer_t）" \
   "$(sizeof_of build/t0/s.o probe_sizeof_StaticTimer_t)" "$(sizeof_of build/t0/s.o probe_sizeof_Timer_t)"
eq "TRACE=0 不影响消息体" "$(sizeof_of build/t0/s.o probe_sizeof_DaemonTaskMessage_t)" "$MSG0"
eq "TRACE=0 不影响链表" "$(sizeof_of build/t0/s.o probe_sizeof_List_t)" "$S_LIST"
echo "----- 反汇编那第三只眼睛：xTimerCreate 的 malloc 立即数也跟着掉 -----"
build_timers t0 -DTRACE=0
"${ARMPREFIX}objdump" -drS build/t0/timers.o > build/t0/timers.dis
IMMT0=$(grep -B2 'bl.*pvPortMalloc' build/t0/timers.dis \
        | grep -oE 'movs[[:space:]]+r0, #[0-9]+' | head -1 | grep -oE '[0-9]+$')
printf '  TRACE=0 时 pvPortMalloc 的立即数：%s（nm 量到 %s）\n' "$IMMT0" "$(sizeof_of build/t0/s.o probe_sizeof_Timer_t)"
eq "两条路子再次对上" "$IMMT0" "$(sizeof_of build/t0/s.o probe_sizeof_Timer_t)"
echo "----- 两个宏是一对：TRACE 关了 STATS 不跟着关，内核直接把构建拦停 -----"
cred "$FREH" "拦住它的那条 #error" "#error configUSE_STATS_FORMATTING_FUNCTIONS is 1 but"
if "${ARMPREFIX}gcc" -O0 $BASE -DTRACE=0 -DSTATS=1 -c sizes_probe.c -o build/stats/s.o \
        > build/stats/err.txt 2>&1; then
    echo "  [失] -DTRACE=0 -DSTATS=1 居然编过了——正文里那句『这两个宏是一对』没有依据" >&2; FAIL=1
else
    echo "  [中] -DTRACE=0 -DSTATS=1 编不过（就是那条 #error 拦的）"
fi
NERR=$(N_of 'error: #' build/stats/err.txt)
eq "拦下来的正是 #error 而不是别的编译错误" "$NERR" 1
sed -n 's/^.*error: #error/error: #error/p' build/stats/err.txt | head -2 | sed 's|^|  |'
need "TRACE=0 时 STATS 也跟着关（本工程的默认写法）能编过" \
    "${ARMPREFIX}gcc" -O0 $BASE -DTRACE=0 -c sizes_probe.c -o build/stats/ok.o
echo

echo "############ 6. 总账：把上面量到的数加回一笔 RAM ############"
echo "----- 先补最后一块输入：栈的深度单位到底多大、池子总额是多少 -----"
STKW=$(sizeof_of build/sizes/s.o probe_sizeof_StackType_t)
TICKW=$(sizeof_of build/sizes/s.o probe_sizeof_TickType_t)
PTRW=$(sizeof_of build/sizes/s.o probe_sizeof_ptr)
HEAPT=$(sizeof_of build/sizes/s.o probe_configTOTAL_HEAP_SIZE)
eq "指针宽度：Cortex-M4 上 4 字节（.bss 那笔账按它算）" "$PTRW" 4
printf '  sizeof(StackType_t) = %s B（所以 configTIMER_TASK_STACK_DEPTH=%s 字 = %s B）\n' \
    "$STKW" "$STACKW" $(( STACKW * STKW ))
printf '  configTOTAL_HEAP_SIZE = %s B（分母也是量出来的，不是抄 FreeRTOSConfig.h）\n' "$HEAPT"
HEAP_TAP=$(( ( S_LINK + S_ALIGN - 1 ) & ~ ( S_ALIGN - 1 ) ))
printf '  heap_4 每笔 malloc 的抽头 xHeapStructSize = (%s + %s - 1) & ~(%s - 1) = %s B\n' \
    "$S_LINK" "$S_ALIGN" "$S_ALIGN" "$HEAP_TAP"
tapn() { # tapn 请求字节数 → heap_4 实付：加抽头，再向上取整到 portBYTE_ALIGNMENT
         # 这就是 heap_4.c:187 与 :191-198 那两段 C 的逐句翻译
    _n=$(( $1 + HEAP_TAP ))
    _r=$(( _n % S_ALIGN ))
    if [ "$_r" -ne 0 ]; then _n=$(( _n + S_ALIGN - _r )); fi
    printf '%s\n' "$_n"
}
cred "$HEAPC" "抽头的加法" "xWantedSize += xHeapStructSize"
cred "$HEAPC" "抽头的取整" "xWantedSize += xAdditionalRequiredSize"
echo "----- 一个定时器对象：一笔 malloc 就够了，因为它自己就是链表节点 -----"
FSUM=0
for f in name item period id cb status number; do
    _v=$(sizeof_of build/sizes/s.o probe_field_Timer_$f)
    if [ "$_v" != "NOSYM" ]; then FSUM=$(( FSUM + _v )); fi
done
printf '  成员逐个量：名字 %s + 链表项 %s + 周期 %s + ID %s + 回调指针 %s + 编号 %s + 状态 %s = %s B\n' \
    "$(sizeof_of build/sizes/s.o probe_field_Timer_name)" \
    "$(sizeof_of build/sizes/s.o probe_field_Timer_item)" \
    "$(sizeof_of build/sizes/s.o probe_field_Timer_period)" \
    "$(sizeof_of build/sizes/s.o probe_field_Timer_id)" \
    "$(sizeof_of build/sizes/s.o probe_field_Timer_cb)" \
    "$(sizeof_of build/sizes/s.o probe_field_Timer_number)" \
    "$(sizeof_of build/sizes/s.o probe_field_Timer_status)" "$FSUM"
printf '  sizeof(Timer_t) 实测 %s B ⇒ 尾部对齐补了 %s B\n' "$S_TIMER" "$(( S_TIMER - FSUM ))"
ge "成员之和不能超过结构体本身" "$S_TIMER" "$FSUM"
lt "补白小于一台机器的对齐粒度（4 字节自然对齐）" "$(( S_TIMER - FSUM ))" 4
eq "链表项的大小就是独立量到的那个 sizeof(ListItem_t)" \
   "$(sizeof_of build/sizes/s.o probe_field_Timer_item)" \
   "$(sizeof_of build/sizes/s.o probe_sizeof_ListItem_t)"
echo "----- 三笔固定开销，一笔一笔摆出来（每一行的数都由上面的实测值算出）-----"
PAID_TCB=$(tapn "$S_TCB")
PAID_STACK=$(tapn $(( STACKW * STKW )))
PAYLOAD=$(( QLEN * MSG0 ))
PAID_QUEUE=$(tapn $(( S_QUEUE + PAYLOAD )))
printf '  守护任务 TCB   ：pvPortMalloc(%s)              → 实付 %s B\n' "$S_TCB" "$PAID_TCB"
printf '  守护任务栈     ：pvPortMallocStack(%s×%s=%s) → 实付 %s B\n' "$STACKW" "$STKW" \
    "$(( STACKW * STKW ))" "$PAID_STACK"
printf '  命令队列       ：pvPortMalloc(%s+%s×%s=%s) → 实付 %s B\n' \
    "$S_QUEUE" "$QLEN" "$MSG0" "$(( S_QUEUE + PAYLOAD ))" "$PAID_QUEUE"
FIXED=$(( PAID_TCB + PAID_STACK + PAID_QUEUE ))
PER_TIMER=$(tapn "$S_TIMER")
PER_TASK=$(( PAID_TCB + $(tapn $(( MINS * STKW ))) ))
printf '  ── 固定那笔合计：%s B（一个定时器都没建就要付）\n' "$FIXED"
printf '  ── 每建一个定时器：%s B ｜ 每开一个最小任务：%s B（栈 %s 字）\n' \
    "$PER_TIMER" "$PER_TASK" "$MINS"
DUTY_FIXED=$(( FIXED * 1000 / HEAPT ))
printf '  ── 固定那笔占 configTOTAL_HEAP_SIZE 的千分比：%s‰，也就是 %s.%s%%\n' \
    "$DUTY_FIXED" "$(( DUTY_FIXED / 10 ))" "$(( DUTY_FIXED % 10 ))"
echo "----- 回归护栏：期望值就是上面三笔之和，写死它是为了『谁改了配置必须被看见』-----"
eq "固定开销（lab 配置 + CM4F + V11.1.0 实测）" "$FIXED" 1312
eq "每个定时器" "$PER_TIMER" 56
eq "每个最小任务（比价基准）" "$PER_TASK" 616
eq "固定那笔的千分比（8.0% of 16 KiB）" "$DUTY_FIXED" 80
le "固定那笔确实在池子装得下" "$FIXED" "$HEAPT"
echo "----- 正文那句『软件定时器 RAM 开销：零』，两个方向都不成立 -----"
echo "  方向一：0 个定时器也要付上面那 $FIXED B（守护任务 + 命令队列），不是零。"
echo "  方向二：另外 $BSS B 落在 .bss，configTOTAL_HEAP_SIZE 调多大都管不到它——"
echo "          它根本不在这笔账的池子里。这 $BSS B 逐项对得上第 3 步 nm 打的那张表，"
echo "          而项数是从源码数出来的（不是把 nm 的输出加起来——那会是自己证自己）："
NL=$(N_of 'PRIVILEGED_DATA static List_t xActiveTimerList' "$TC")
NP=$(N_of 'PRIVILEGED_DATA static List_t \*' "$TC")
NP=$(( NP + $(N_of 'PRIVILEGED_DATA static QueueHandle_t' "$TC") \
           + $(N_of 'PRIVILEGED_DATA static TaskHandle_t' "$TC") ))
NT=$(N_of 'PRIVILEGED_DATA static TickType_t xLastTime' "$TC")
printf '  两条到期表 List_t×%s ＋ %s 个指针 ＋ xLastTime 一个 TickType_t×%s\n' "$NL" "$NP" "$NT"
printf '  = %s×%s + %s×%s + %s×%s = %s B\n' \
    "$S_LIST" "$NL" "$PTRW" "$NP" "$TICKW" "$NT" \
    "$(( S_LIST * NL + PTRW * NP + TICKW * NT ))"
BSS_PRED=$(( S_LIST * NL + PTRW * NP + TICKW * NT ))
eq "预测和实测的 .bss 对上（说明 timers.c 的 static 就这几个，没有漏项）" "$BSS" "$BSS_PRED"
echo "----- 和『开一个任务』比价：这才是『共用守护任务所以便宜』那句话的真实刻度-----"
R1=$(( PER_TASK / PER_TIMER ))
printf '  一个最小任务的字节数 = %s 个定时器的名额（%s ÷ %s，向下取整）\n' "$R1" "$PER_TASK" "$PER_TIMER"
ge "结论方向：定时器确实比任务便宜一个数量级" "$R1" 10
R2=$(( FIXED * 100 / PER_TASK ))
printf '  固定那笔 = %s.%s 个最小任务的名额（%s ÷ %s，向下取整）\n' \
    "$(( R2 / 100 ))" "$(printf '%02d' $(( R2 % 100 )))" "$FIXED" "$PER_TASK"
printf '  换句话说：为了用定时器，你先付了 %s 个任务的价钱；只用 1、2 个定时器时这笔最不划算。\n' \
    "$(( R2 / 100 ))"
echo "----- 换一档配置，账怎么动（同一个函数、只换实测输入）-----"
account() { # account 目录名：把这个档的固定开销与每定时器开销重算一遍
    _d=$1
    _tcb=$(sizeof_of build/$_d/s.o probe_sizeof_TCB_t)
    _stk=$(sizeof_of build/$_d/s.o probe_configTIMER_TASK_STACK_DEPTH)
    _w=$(sizeof_of build/$_d/s.o probe_sizeof_StackType_t)
    _q=$(sizeof_of build/$_d/s.o probe_sizeof_Queue_t)
    _l=$(sizeof_of build/$_d/s.o probe_configTIMER_QUEUE_LENGTH)
    _m=$(sizeof_of build/$_d/s.o probe_sizeof_DaemonTaskMessage_t)
    _tm=$(sizeof_of build/$_d/s.o probe_sizeof_Timer_t)
    printf '%s %s\n' "$(( $(tapn $_tcb) + $(tapn $(( _stk * _w ))) + $(tapn $(( _q + _l * _m ))) ))" "$(tapn $_tm)"
}
for d in sizes t0 p1 q16; do
    set -- $(account "$d")
    printf '  %-6s 固定 %5s B ｜ 每定时器 %s B ｜ 相对 lab 那档 %+d B\n' \
        "$d" "$1" "$2" $(( $1 - FIXED ))
done
set -- $(account t0);  eq "TRACE=0 省下的固定那笔" $(( FIXED - $1 )) 16
                   eq "TRACE=0 省下的每定时器"   $(( PER_TIMER - $2 )) 8
set -- $(account p1);  eq "开 PEND 的固定那笔涨幅 = 长度 × 消息增重" \
                   $(( $1 - FIXED )) $(( QLEN * ( MSG1 - MSG0 ) ))
set -- $(account q16); eq "队列 8→16 的固定那笔涨幅 = 长度增量 × 消息大小" \
                   $(( $1 - FIXED )) $(( ( QL16 - QLEN ) * MSG0 ))
echo "----- 那笔 .bss 里为什么没有队列的 8 条消息：静态分配那一档整个被 #if 掉了 -----"
cred "$TC" "lab 配置下走的是动态那一支" "xTimerQueue = xQueueCreate( ( UBaseType_t ) configTIMER_QUEUE_LENGTH, ( UBaseType_t ) sizeof( DaemonTaskMessage_t ) )"
if "${ARMPREFIX}nm" build/omit/timers.o | grep -q 'ucStaticTimerQueueStorage'; then
    echo "  [失] 静态队列存储竟然在符号表里——lab 的 configSUPPORT_STATIC_ALLOCATION 不是 0" >&2; FAIL=1
else
    echo "  [中] 符号表里没有 ucStaticTimerQueueStorage（静态那 96 B 确实没编进来）"
fi
echo "----- 上界（不是预算）：整池只用来放定时器时塞得下的个数 -----"
printf '  (%s - %s) ÷ %s = %s 个。真实工程里这笔钱还要给任务、队列、栈，所以它是上界。\n' \
    "$HEAPT" "$FIXED" "$PER_TIMER" $(( ( HEAPT - FIXED ) / PER_TIMER ))
echo

echo "############ 7. 回调为什么必然串行：把分派规则抄成模拟器，再逐条核对规则本身 ############"
echo "----- 先上护栏：sim_daemon.c 头注释里标了七条规则的源码行号，行号一漂本步即失败 -----"
echo "       （内核一升级行号就会漂；漂了这份取证要报错，而不是悄悄给出一个错的数）"
at_line "$TC" 859 "listGET_ITEM_VALUE_OF_HEAD_ENTRY( pxCurrentTimerList )"
at_line "$TC" 800 "xNextExpireTime <= xTimeNow"
at_line "$TC" 803 "prvProcessExpiredTimer( xNextExpireTime, xTimeNow )"
at_line "$TC" 820 "vQueueWaitForMessageRestricted( xTimerQueue, ( xNextExpireTime - xTimeNow )"
at_line "$TC" 735 "prvReloadTimer( pxTimer, xNextExpireTime, xTimeNow )"
at_line "$TC" 706 "while( prvInsertTimerInActiveList( pxTimer"
at_line "$TC" 709 "xExpiredTime += pxTimer->xTimerPeriodInTicks"
at_line "$TC" 904 "if( xNextExpiryTime <= xTimeNow )"
at_line "$TC" 908 "( xTimeNow - xCommandTime ) ) >= pxTimer->xTimerPeriodInTicks"
at_line "$TC" 795 "xTimeNow = prvSampleTimeNow( &xTimerListsWereSwitched )"
at_line "$LISTC" 192 "pxIterator->pxNext->xItemValue <= xValueOfInsertion"
echo "----- R6 的本体就是那个 <=：等于也跳过，所以同值的项里【先入表的离表头更近】-----"
sed -n '192p' "$LISTC" | sed 's|^\s*|  原文 |'
echo "----- R4 的本体：下一拍锚在【原到期时刻 + 周期】，不是锚在回调结束的那一刻 -----"
sed -n '706p' "$TC" | sed 's|^\s*|  原文 |'
echo "----- 编模拟器：宿主机 gcc，-Wall -Wextra -Werror（这份规则抄得干不干净，编译器先过一遍）-----"
gcc -std=c11 -O0 -Wall -Wextra -Werror -o build/sim/sim sim_daemon.c
need "模拟器编得过" test -x build/sim/sim
build/sim/sim > build/sim/run.txt
build/sim/sim > build/sim/run2.txt
need "同一个二进制连跑两次输出逐字节相同（事件表写死，没有真时钟）" \
    cmp -s build/sim/run.txt build/sim/run2.txt
SIM=build/sim/run.txt
res() { # res tag timer 字段 → 那一行 RES 里该字段的值
    awk -v t="tag=$1" -v m="timer=$2" -v k="$3" '$1=="RES" && $2==t && $3==m {
        for (i = 4; i <= NF; i++) { e = index($i, "="); if (substr($i,1,e-1)==k) print substr($i,e+1) }
    }' "$SIM"
}
restag() { # restag tag 字段 → 那一幕的汇总行（第 3 列是 iters=…，定时器行那列是 timer=…）
    awk -v t="tag=$1" -v k="$2" '$1=="RES" && $2==t && $3 ~ /^iters=/ {
        for (i = 3; i <= NF; i++) { e = index($i, "="); if (substr($i,1,e-1)==k) print substr($i,e+1) }
    }' "$SIM"
}
logat() { # logat tag 动手时刻 → 那一刻按顺序被服务的定时器名（空格分隔，一行）
    awk -v t="tag=$1" -v w="wake=$2" '$1=="LOG" && $2==t && $4==w {
        for (i = 5; i <= NF; i++) if ($i ~ /^who=/) s = s substr($i, 5) " "
    } END { print s }' "$SIM"
}
ge "读数器 res/restag 没漂：幕 A 的占空比读得到（读不到就是 RES 格式变了）" \
   "$(restag A duty_permille)" 0
eq "读数器 logat 没漂：幕 A 的 t=100 那一刻只有 fast" \
   "$(logat A 100 | tr -s ' ' | sed 's/ *$//')" "fast"
echo "----- 五幕各自的数（横版旁白要念的就是这几行）-----"
for tag in A B C E; do
    d=$(restag "$tag" duty_permille)
    lm=$(res "$tag" fast late_max)
    ct=$(res "$tag" slow cost)
    if [ "$d" -lt 1000 ]; then
        eq "幕 $tag：占空比 $d‰ 不满 → 耗时 0 的 fast 最大迟到恰好是那个耗时本身（$ct）" "$lm" "$ct"
    else
        gt "幕 $tag：占空比 $d‰ 满了 → fast 的最大迟到超过那个耗时（$ct）" "$lm" "$ct"
    fi
done
for tag in A B C D E; do
    eq "幕 $tag：循环上限没触顶（数字是算完的，不是截出来的）" "$(restag "$tag" truncated)" 0
done
eq "幕 A（对照组，两个回调都零耗时）：fast 一次不迟到" "$(res A fast late_n)" 0
eq "幕 A：fast 实拍 = 应拍" "$(res A fast served)" "$(res A fast should)"
eq "幕 A：slow 实拍 = 应拍" "$(res A slow served)" "$(res A slow should)"
eq "幕 A：收工时谁都不欠拍" "$(res A fast owed)" 0
eq "幕 B（lab 场景 4）：fast 慢的次数" "$(res B fast late_n)" 5
eq "幕 B：fast 一次都没被【补拍】——它不是丢拍，是被压住" "$(res B fast catchup)" 0
eq "幕 B：fast 收工时还欠着" "$(res B fast owed)" 50
le "幕 B：欠的不足一整拍（100），所以确实没有哪一拍被扔掉" "$(res B fast owed)" "$(res B fast period)"
eq "幕 B：slow 自己一次都不迟到（它是那个压别人的人）" "$(res B slow late_n)" 0
eq "幕 C：耗时 200 > 自己的周期 120 → 连环补拍，同一时刻最多连开" "$(res C fast burst_max)" 6
gt "幕 C：fast 的最大迟到（520）早就盖过了那个耗时本身" "$(res C fast late_max)" "$(res C slow cost)"
eq "幕 C：耗时 0 的 fast 也被拖去补拍" "$(res C fast catchup)" 6
eq "幕 D：比 C 更狠，收工时 fast 欠 970 拍时长" "$(res D fast owed)" 970
eq "幕 E：耗时 200 大于别人的周期 100、小于自己的周期 300 → 迟到恰好是 200" \
   "$(res E fast late_max)" "$(res E slow cost)"
lt "幕 E：这一幕占空比仍不满（666‰）" "$(restag E duty_permille)" 1000
eq "幕 E：slow 自己一次都不迟到" "$(res E slow late_n)" 0
ge "幕 E：fast 被压住的拍后来都当场补开了（补拍 6 次）" "$(res E fast catchup)" 1
echo "----- 一句话规则：欠拍要么不足一整拍（只是还没到），要么补拍数 > 0（已经还上了）-----"
for tag in A B C D E; do
    for t in fast slow; do
        o=$(res "$tag" "$t" owed); pd=$(res "$tag" "$t" period); cu=$(res "$tag" "$t" catchup)
        if [ "$o" -ge "$pd" ] && [ "$cu" -eq 0 ]; then
            echo "  [失] 幕 $tag/$t：欠 $o ≥ 周期 $pd 却一次没补——这才有真丢拍" >&2; FAIL=1
        else
            echo "  [中] 幕 $tag/$t：欠 $o（周期 $pd，补拍 $cu）——没有拍被扔掉"
        fi
    done
done
echo "----- R6 的实测长相：600 这一拍 fast 与 slow 撞车，先动的是【先入表】的那个 -----"
AT600=$(logat A 600 | tr -s ' ' | sed 's/ *$//')
printf '  t=600 的动手顺序：%s\n' "$AT600"
eq "撞车时先服务的是 slow（它在 480 那一拍就被插进 600 这个位置，比 fast 早）" "$AT600" "slow fast"
eq "t=1200 再撞一次，顺序一样" "$(logat A 1200 | tr -s ' ' | sed 's/ *$//')" "slow fast"
printf '  ⇒ 『先入表者先服务』里的【入表】是被插进链表的那一刻，不是 xTimerCreate 的先后；\n'
echo '     自动重装一跑，两者的插入时刻就交错分了，创建顺序只在第一轮管用。'
eq "第一轮没有交错：t=100 只有 fast" "$(logat A 100 | tr -s ' ' | sed 's/ *$//')" "fast"
echo

echo "== 结论 =="
if [ "$FAIL" -eq 0 ]; then
    echo "七步全部命中：这一集每个数字都能在本目录里重跑出来（sh probe.sh）。"
else
    echo "有 [失] 项：正文引用的数不再成立，改配置或内核版本后必须重核。" >&2
fi
exit "$FAIL"
