#!/bin/sh
# probe.sh —— F5《信号量与互斥量：同一个 Queue_t，和它唯一的那点区别》全部取证
#
#   sh probe.sh          八步取证（见每一步的标题）
#   sh probe.sh clean    删 build/
#
# 这一集的取证对象是上游 FreeRTOS-Kernel V11.1.0 的 queue.c / tasks.c / list.h，
# 外加本工程 01-freertos-lab 的 scene 6 剧本。前七步只编不链、不要开发板：
#   「xSemaphore* 到底是什么」是预处理器和符号表的事；
#   「互斥量和信号量差在哪」是结构体偏移和一句 str 的事；
#   「优先级继承长什么样」是控制流和机身指令顺序的事。
# 全都不需要板子。唯一要跑起来的是第 8 步的反转模型（宿主机 gcc，见 sim_invert.c）。
#
# 第 8 步要划清一条界：E04 那两个反转数（≈6000ms / ≈2500ms）在
# docs/lab/e04-priority-inversion.md:78 里明写着是「按剧本参数推出的理论值，不是实测」，
# 实测记录那张表到今天还是空的。所以模型跑出来的只能叫【模型值】，屏上得说全这句话。
#
# 旋钮（都在 FreeRTOSConfig.h 里读这几个 -D）：
#   -DMUTEX=0|1   → configUSE_MUTEXES（第 7 步拿它证明"继承是编译期的事"）
#   -DTRACE=0|1   → configUSE_TRACE_FACILITY（第 6 步拿它证明"ucQueueType 只是标签"）
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
command -v gcc >/dev/null 2>&1 || { echo "找不到宿主机 gcc（第 8 步的反转模型要跑它）"; exit 1; }
[ -f "$K/queue.c" ] || { echo "找不到内核 $K/queue.c（FREERTOS_KERNEL= 可覆盖）"; exit 1; }
[ -f "$K/tasks.c" ] || { echo "找不到内核 $K/tasks.c"; exit 1; }
[ -f "$K/include/semphr.h" ] || { echo "找不到 $K/include/semphr.h"; exit 1; }
KC=$(grep -n '#define tskKERNEL_VERSION_NUMBER' "$K/include/task.h" | head -1)

mkdir -p build/sizes build/queue build/tasks build/lin build/mutex0 build/trace0 \
         build/inherit build/sim build/labcfg

MCU="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard"
# -I$K 是为了 sizes_probe.c 能 #include "queue.c"：Queue_t 是文件内类型，
# queue.h 里只有一个前置声明，公开头文件看不见它——唯一能"问内核自己"的路子
# 就是把 .c 原文拿进来。
INC="-I. -I$K -I$K/include -I$K/portable/GCC/ARM_CM4F"
# 刻意 -O0：这一集比的是结构体形状与源码控制流，优化会把手型抹平。
BASE="$MCU -std=c11 $INC -ffunction-sections -fdata-sections"
QC="$K/queue.c"
TSKC="$K/tasks.c"
LISTC="$K/list.c"
SEMH="$K/include/semphr.h"
LISTH="$K/include/list.h"

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
sizeof_of() { # sizeof_of .o文件 probe名 → 十进制字节数（符号的 size 字段就是数组长度）
    _o=$1; _s=$2
    _h=$("${ARMPREFIX}nm" --print-size "$_o" | awk -v n="$_s" '$4==n {print $2}')
    if [ -z "$_h" ]; then echo "NOSYM"; else h2d "$_h"; fi
}
off_of() { # off_of .o文件 probe名 → 十进制【偏移】。sizes_probe.c 里每个数组都写成
           # [1 + offsetof(...)]（0 长度数组编不过，而 pcHead 的偏移恰好是 0），
           # 所以读回来的数要统一减 1。
    _v=$(sizeof_of "$1" "$2")
    case "$_v" in NOSYM) echo NOSYM; return;; esac
    echo $((_v - 1))
}
sz_of() { # sz_of .o文件 section前缀 → 这些段的字节数之和
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
at_line() { # at_line 文件 行号 正则：第 8 步用；行号漂了就失败，不许悄悄给错的数
    _f=$1; _n=$2; _re=$3
    if sed -n "${_n}p" "$_f" | grep -q "$_re"; then
        echo "  [中] $(basename "$_f"):$_n 仍是『$_re』"
    else
        echo "  [失] $(basename "$_f"):$_n 已经不是『$_re』了——模拟器抄的规则要重核" >&2; FAIL=1
    fi
}
N_of() { grep -c "$1" "$2" || true; }   # N_of 固定串 文件：零命中也是合法答案，
                                        # 所以 || true 兜住 grep 的退出码，交给 eq 去判
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
N_INS() { grep -cE '^[[:space:]]+[0-9a-f]+:' "$1"; }
line_of() { # line_of 文件 正则 → 第一次命中的行号（没有则 0），用来判两句的先后
    _n=$(grep -nE "$2" "$1" | head -1 | cut -d: -f1)
    echo "${_n:-0}"
}
line_of_heap() { # line_of_heap 文件 正则 → 第一次【不写在栈帧上】的命中行号（没有则 0）。
                 # -O0 的机身把局部变量放成 str rX,[r7,#off]，而 TCB 里某些字段偏移
                 # 正好也是同一个数（xStateListItem.pvContainer = 4+16 = 20）。
                 # 要找「往结构体里写」那一句，就得把 r7 做基址的几条剔掉——
                 # 只剔基址寄存器，不改判据（偏移、方向、还是那一条 str）。
    _n=$(grep -nE "$2" "$1" | grep -v '\[r7,' | head -1 | cut -d: -f1)
    echo "${_n:-0}"
}

# ---- 先把仪器编出来：纯编译期，永不参与链接 ----
build_sizes() { # build_sizes 目录名 其余 -D…
    _d=$1; shift
    "${ARMPREFIX}gcc" -O0 $BASE "$@" -c sizes_probe.c -o "build/$_d/s.o"
}
build_sizes_labcfg() { # 同一件仪器，只把配置文件换成 lab 那一份。
    # -Ibuild/labcfg 必须排在最前：内核 FreeRTOS.h 里那句 #include "FreeRTOSConfig.h"
    # 是按 -I 的先后顺序找文件的，本目录那份（-I.）排在后面才让得出去。
    # 这件事不靠推断，第 4 步用 probe_configUSE_TIMERS 量出来两个档各读到几。
    "${ARMPREFIX}gcc" -O0 $MCU -std=c11 -Ibuild/labcfg -I$K -I$K/include \
        -I$K/portable/GCC/ARM_CM4F -ffunction-sections -fdata-sections \
        -c sizes_probe.c -o build/labcfg/s.o
}
build_queue() { # build_queue 目录名 其余 -D…
    _d=$1; shift
    "${ARMPREFIX}gcc" -O0 $BASE "$@" -c "$QC" -o "build/$_d/queue.o"
}
build_tasks() { # build_tasks 目录名 其余 -D…
    _d=$1; shift
    "${ARMPREFIX}gcc" -O0 $BASE "$@" -c "$TSKC" -o "build/$_d/tasks.o"
}
dis_func() { # dis_func .o文件 函数名 输出文件：只取那一个函数的机身（-dr 才带得上被调名字）
    _f=$1; _n=$2; _o=$3
    "${ARMPREFIX}objdump" -dr --no-show-raw-insn --section=".text.$_n" "$_f" \
        | sed -n "/<$_n>:/,/^\$/p" > "$_o"
}

build_sizes sizes
build_sizes trace0 -DTRACE=0
build_queue queue
build_tasks tasks
build_queue mutex0 -DMUTEX=0
build_tasks mutex0 -DMUTEX=0

echo "== F5 信号量与互斥量取证 =="
echo "交叉工具链：$("${ARMPREFIX}gcc" -dumpfullversion)；宿主机 gcc：$(gcc -dumpversion)"
echo "内核：$KC"
echo "内核路径：$K"
echo

echo "############ 1. 五个 API（外加中断版那一条）的名字是谁给的：semphr.h 里那几条 #define ############"
echo "----- 创建：三条路，各自指向不同的队列入口 -----"
cred "$SEMH" "创建二值"   '#define xSemaphoreCreateBinary()'
cred "$SEMH" "创建互斥"   '#define xSemaphoreCreateMutex()'
cred "$SEMH" "创建计数"   '#define xSemaphoreCreateCounting('
echo "----- 两个动作：一个 take，一个 give -----"
cred "$SEMH" "拿"         '#define xSemaphoreTake('
cred "$SEMH" "还"         '#define xSemaphoreGive('
cred "$SEMH" "拿（中断版）" '#define xSemaphoreTakeFromISR('
echo "----- 中断那条 take 的落点里【没有】互斥量那三样东西 -----"
echo "       屏上 code-15 那句『中断里不该拿互斥锁，凭据不在这两行』靠的是这一条。"
echo "       它不能拿 tasks.c:6589 那一问当理由——理由在这儿：这条路根本不登记持有者。"
ISR_FROM=$(grep -n '^BaseType_t xQueueReceiveFromISR' "$QC" | head -1 | cut -d: -f1)
need "读到了 xQueueReceiveFromISR 的定义行（读不到就换不掉行号，本步作废）" test -n "$ISR_FROM"
ISR_TO=$(awk -v s="$ISR_FROM" 'NR>s && /^}/ {print NR; exit}' "$QC")
ISR_REF=$(awk -v a="$ISR_FROM" -v b="$ISR_TO" 'NR>=a && NR<=b' "$QC" \
          | grep -c -E 'xMutexHolder|uxQueueType|xTaskPriorityInherit' || true)
printf '  函数体范围：%s → %s（共 %s 行，行号是现读的，没写死）\n' \
    "$ISR_FROM" "${ISR_TO:-NONE}" "$(( ${ISR_TO:-0} - ${ISR_FROM:-0} + 1 ))"
eq "整条 ISR 取锁路上 xMutexHolder / uxQueueType / xTaskPriorityInherit 的引用次数" "$ISR_REF" 0
# 尺子自检：同一条正则拿去量任务那条 take，必须数得出东西来。
# 不然这个 0 可能是"范围取空了"或"模式写瞎了"，而不是"那段真没有"。
TSK_FROM=$(grep -n '^BaseType_t xQueueSemaphoreTake' "$QC" | head -1 | cut -d: -f1)
TSK_TO=$(awk -v s="$TSK_FROM" 'NR>s && /^}/ {print NR; exit}' "$QC")
TSK_REF=$(awk -v a="$TSK_FROM" -v b="$TSK_TO" 'NR>=a && NR<=b' "$QC" \
          | grep -c -E 'xMutexHolder|uxQueueType|xTaskPriorityInherit' || true)
printf '  同一把尺子量任务那条 take（queue.c:%s-%s）：引用 %s 次\n' "$TSK_FROM" "$TSK_TO" "$TSK_REF"
gt "尺子没瞎：任务那条路上这三样至少数得出一处" "$TSK_REF" 0
cred "$QC" "对照：任务那条 take 才走继承" 'xInheritanceOccurred = xTaskPriorityInherit'
echo "----- 展开时会带出来的那两个 0：长度写死 1、每项 0 字节、give 永远不阻塞 -----"
cred "$SEMH" "每项 0 字节" '#define semSEMAPHORE_QUEUE_ITEM_LENGTH'
cred "$SEMH" "give 不阻塞" '#define semGIVE_BLOCK_TIME'
echo "----- 同一件事在 queue.c 内部还有第二个名字：两个 0 是不同宏、同一个值 -----"
cred "$QC" "queue.c 自己的 0" '#define queueSEMAPHORE_QUEUE_ITEM_LENGTH'
cred "$QC" "mutex give 的 0"  '#define queueMUTEX_GIVE_BLOCK_TIME'
echo "----- 递归/计数那几条门控：configUSE_MUTEXES=0 时名字直接不存在 -----"
# 这条负例成立的条件是「隐式函数声明」被判成错误。GCC 14+ 默认就是错误，
# 而 CI 装的 apt 版是 13.2.1——它只给警告，照样编得过，负例就反过来变成 [失]。
# severity 写死在命令行上，不赌某个编译器版本的默认值。
if "${ARMPREFIX}gcc" -O0 $BASE -Werror=implicit-function-declaration \
        -DMUTEX=0 -c lineage_probe.c -o build/mutex0/lin.o 2> build/mutex0/lin.err; then
    echo "  [失] -DMUTEX=0 竟然还编得过 lineage_probe.c" >&2; FAIL=1
else
    echo "  [中] -DMUTEX=0 时 xSemaphoreCreateMutex 这个名字不存在，编译器当场拒绝："
    grep -m2 -E "implicit declaration|error:" build/mutex0/lin.err | sed 's|^|    |'
fi
need "被拒的那一次没留下目标文件" test ! -f build/mutex0/lin.o

echo
echo "############ 2. 预处理器说了算：展开文本里一个 xSemaphore 都不剩 ############"
echo "----- 量法：-E 只展开不调，展开结果里再数名字。看到 #define 不等于证明落点，"
echo "       展开文本才是落点。-----"
"${ARMPREFIX}gcc" $BASE -E lineage_probe.c -o build/lin/lin.i
need "展开产物存在" test -s build/lin/lin.i
eq "展开文本里 xSemaphore 字样还剩几个" "$(N_of xSemaphore build/lin/lin.i)" 0
for s in xQueueGenericCreate xQueueCreateMutex xQueueCreateCountingSemaphore xQueueSemaphoreTake xQueueGenericSend; do
    ge "$s 在展开文本里出现" "$(N_of "$s" build/lin/lin.i)" 1
done
echo "----- 五个调用点展开后长这样（这一屏就是这一集第一页的正文）-----"
awk '/^void use_semaphore_create_binary/,/^BaseType_t use_semaphore_give/' build/lin/lin.i \
    | sed 's|^|  |'
echo "----- 读一下这五行：长度 1、每项 0、类型标签 3/1；give 那个 NULL 就是"
echo "       「不拷贝任何数据」这件事在源码里的写法。-----"

echo
echo "############ 3. 符号表说了算：宏不留符号，函数才留 ############"
"${ARMPREFIX}gcc" -O0 $BASE -c lineage_probe.c -o build/lin/lin.o
echo "----- lin.o 的未定义引用（这就是它真正依赖的东西）-----"
"${ARMPREFIX}nm" -u build/lin/lin.o | sed 's|^|  |'
eq "lin.o 里未定义的 xSemaphore* 有几个" \
   $("${ARMPREFIX}nm" -u build/lin/lin.o | grep -c xSemaphore || true) 0
ge "lin.o 里未定义的 xQueue* 至少有几个" \
   $("${ARMPREFIX}nm" -u build/lin/lin.o | grep -c xQueue || true) 5
echo "----- 逐函数配对：每个 probe 函数只调一个队列入口，靠重定位表读，不靠我猜 -----"
"${ARMPREFIX}objdump" -dr build/lin/lin.o > build/lin/lin.dis
pair() { # pair 探针函数名 期望的队列符号名
    _f=$1; _want=$2
    _got=$("${ARMPREFIX}objdump" -dr --section=".text.$_f" build/lin/lin.o \
           | grep -oE 'R_ARM_THM_CALL[[:space:]]+[A-Za-z_]+' | awk '{print $2}' | head -1)
    eq "$_f → $_want" "$_got" "$_want"
}
pair use_semaphore_create_binary     xQueueGenericCreate
pair use_semaphore_create_mutex      xQueueCreateMutex
pair use_semaphore_create_counting   xQueueCreateCountingSemaphore
pair use_semaphore_take              xQueueSemaphoreTake
pair use_semaphore_give              xQueueGenericSend
echo "----- 反向也查：内核自己有没有把 xSemaphore* 实现成函数？-----"
eq "queue.o + tasks.o 里 xSemaphore* 定义符号的个数" \
   $("${ARMPREFIX}nm" build/queue/queue.o build/tasks/tasks.o | grep -c ' T xSemaphore\| W xSemaphore' || true) 0
cred "$SEMH" "句柄类型就是队列句柄" 'typedef QueueHandle_t'
grep -n "SemaphoreHandle_t" "$SEMH" | head -3 | sed 's|^|  凭据(句柄类型) semphr.h:|'

echo
echo "############ 4. 形状与账：一把锁到底占多少字节 ############"
echo "----- 量法同 F6：探针数组落在 .bss，nm --print-size 读到的就是 sizeof / 偏移+1 -----"
SQ_Q=$(sizeof_of build/sizes/s.o probe_sizeof_Queue_t)
SQ_S=$(sizeof_of build/sizes/s.o probe_sizeof_StaticQueue_t)
SQ_TCB=$(sizeof_of build/sizes/s.o probe_sizeof_TCB_t)
SQ_SEMD=$(sizeof_of build/sizes/s.o probe_sizeof_SemaphoreData_t)
SQ_QP=$(sizeof_of build/sizes/s.o probe_sizeof_QueuePointers_t)
SQ_PTR=$(sizeof_of build/sizes/s.o probe_sizeof_ptr)
SQ_UB=$(sizeof_of build/sizes/s.o probe_sizeof_UBaseType_t)
SQ_LIST=$(sizeof_of build/sizes/s.o probe_sizeof_List_t)
SQ_LITEM=$(sizeof_of build/sizes/s.o probe_sizeof_ListItem_t)
NPRIO=$(sizeof_of build/sizes/s.o probe_configMAX_PRIORITIES)
NPRIO=$((NPRIO - 1))
printf '  sizeof(Queue_t)=%s  sizeof(TCB_t)=%s  指针=%s  UBaseType_t=%s  List_t=%s  ListItem_t=%s\n' \
    "$SQ_Q" "$SQ_TCB" "$SQ_PTR" "$SQ_UB" "$SQ_LIST" "$SQ_LITEM"
printf '  configMAX_PRIORITIES（量出来的，不抄配置）= %s\n' "$NPRIO"
eq "StaticQueue_t 与 Queue_t 同大小（内核自己也是这么断言的）" "$SQ_S" "$SQ_Q"
cred "$QC" "那条断言" 'configASSERT( xSize == sizeof( Queue_t ) )'
echo "----- 偏移表：这一集要摸的槽位全在这 -----"
O_PCHEAD=$(off_of build/sizes/s.o probe_off_pcHead)
O_PCWRITE=$(off_of build/sizes/s.o probe_off_pcWriteTo)
O_U=$(off_of build/sizes/s.o probe_off_u)
O_PCTAIL=$(off_of build/sizes/s.o probe_off_u_pcTail)
O_HOLDER=$(off_of build/sizes/s.o probe_off_u_xMutexHolder)
O_PREAD=$(off_of build/sizes/s.o probe_off_u_pcReadFrom)
O_RECUR=$(off_of build/sizes/s.o probe_off_u_uxRecursive)
O_MSG=$(off_of build/sizes/s.o probe_off_uxMessagesWaiting)
O_LEN=$(off_of build/sizes/s.o probe_off_uxLength)
O_ITEM=$(off_of build/sizes/s.o probe_off_uxItemSize)
O_PRIO=$(off_of build/sizes/s.o probe_off_T_uxPriority)
O_BASE=$(off_of build/sizes/s.o probe_off_T_uxBasePriority)
O_HELD=$(off_of build/sizes/s.o probe_off_T_uxMutexesHeld)
O_STATE=$(off_of build/sizes/s.o probe_off_T_xStateListItem)
O_EVENT=$(off_of build/sizes/s.o probe_off_T_xEventListItem)
O_PVCONT=$(off_of build/sizes/s.o probe_off_L_pvContainer)
printf '  pcHead=%s  pcWriteTo=%s  u=%s（pcTail=%s / xMutexHolder=%s 同槽；pcReadFrom=%s / uxRecursiveCallCount=%s 同槽）\n' \
    "$O_PCHEAD" "$O_PCWRITE" "$O_U" "$O_PCTAIL" "$O_HOLDER" "$O_PREAD" "$O_RECUR"
printf '  uxMessagesWaiting=%s  uxLength=%s  uxItemSize=%s\n' "$O_MSG" "$O_LEN" "$O_ITEM"
printf '  TCB：uxPriority=%s  uxBasePriority=%s  uxMutexesHeld=%s  xStateListItem=%s  xEventListItem=%s\n' \
    "$O_PRIO" "$O_BASE" "$O_HELD" "$O_STATE" "$O_EVENT"
eq "联合体重叠（第一槽）：pcTail 与 xMutexHolder 偏移相同" "$O_PCTAIL" "$O_HOLDER"
eq "联合体重叠（第二槽）：pcReadFrom 与 uxRecursiveCallCount 偏移相同" "$O_PREAD" "$O_RECUR"
eq "两个联合体一样大" "$SQ_SEMD" "$SQ_QP"
echo "----- RAM 账：创建一把锁实际要多少钱 -----"
cred "$QC" "分配那句" 'pvPortMalloc( sizeof( Queue_t ) + xQueueSizeInBytes )'
cred "$QC" "乘的就是长度与项大小" 'xQueueSizeInBytes = ( size_t ) ( ( size_t ) uxQueueLength'
echo "  互斥量与二值信号量都是 uxLength=1、uxItemSize=0 → 载荷 1×0 = 0 字节，"
echo "  所以一把锁的账就是 sizeof(Queue_t) = $SQ_Q 字节，一字节载荷都不多。"
echo "----- 换个独立路子验一次：objdump 里那句 pvPortMalloc 的实参怎么算出来的 -----"
dis_func build/queue/queue.o xQueueGenericCreate build/queue/gc.dis
sed -n '/mul/,/pvPortMalloc/p' build/queue/gc.dis | sed 's|^|  |'
IMM=$(grep -B3 -E 'R_ARM_THM_CALL[[:space:]]+pvPortMalloc' build/queue/gc.dis \
      | grep -oE '#[0-9]+' | head -1 | grep -oE '[0-9]+' || true)
printf '  机身里加在乘积上的那个立即数（结构体那部分）= %s\n' "${IMM:-NONE}"
need "机身里读到了那个立即数" test -n "$IMM"
eq "两条独立路子给出同一个 sizeof(Queue_t)" "$IMM" "$SQ_Q"
have build/queue/gc.dis 'mul' '载荷那部分是现算的乘法：uxQueueLength × uxItemSize'
echo "----- 第 4 步最后一道：把配置文件换成 lab 那一份，同一件仪器再量一次 -----"
echo "       本 probe 的 FreeRTOSConfig.h 唯一有意偏离 lab 的地方是 configUSE_TIMERS"
echo "       （这里 0、lab 1，见 FreeRTOSConfig.h:17 与 :64）。这张偏移表该由内核决定，"
echo "       不该由我这份配置决定——所以按 lab 的原样配置重编一遍，逐项比读数。"
cp ../01-freertos-lab/FreeRTOSConfig.h build/labcfg/
build_sizes_labcfg
echo "       先证明那份配置真的被吃进去了。不证明这条，下面一整串相等都只是自我安慰："
eq "默认档量到的 configUSE_TIMERS" "$(off_of build/sizes/s.o probe_configUSE_TIMERS)" 0
eq "lab 档量到的 configUSE_TIMERS"  "$(off_of build/labcfg/s.o probe_configUSE_TIMERS)" 1
_pnum() { # _pnum .o 探针名：sizeof_ 前缀就是数组长度本身，其余按 +1 约定减 1
    case "$2" in
        probe_sizeof_*) sizeof_of "$1" "$2" ;;
        *)              off_of "$1" "$2" ;;
    esac
}
_LABDIFF=''; _LABN=0
for _p in probe_sizeof_Queue_t probe_sizeof_StaticQueue_t probe_sizeof_TCB_t \
          probe_sizeof_SemaphoreData_t probe_sizeof_QueuePointers_t \
          probe_sizeof_List_t probe_sizeof_ListItem_t probe_sizeof_ptr \
          probe_sizeof_UBaseType_t probe_configMAX_PRIORITIES \
          probe_off_pcHead probe_off_pcWriteTo probe_off_u \
          probe_off_u_pcTail probe_off_u_xMutexHolder probe_off_u_pcReadFrom \
          probe_off_u_uxRecursive probe_off_uxMessagesWaiting probe_off_uxLength \
          probe_off_uxItemSize probe_off_xTasksWaitingToReceive probe_off_ucQueueType \
          probe_off_T_uxPriority probe_off_T_uxBasePriority probe_off_T_uxMutexesHeld \
          probe_off_T_xStateListItem probe_off_T_xEventListItem \
          probe_off_L_xItemValue probe_off_L_pxNext probe_off_L_pxPrevious \
          probe_off_L_pvOwner probe_off_L_pvContainer; do
    _a=$(_pnum build/labcfg/s.o "$_p"); _b=$(_pnum build/sizes/s.o "$_p")
    _LABN=$((_LABN + 1))
    [ "$_a" = "$_b" ] || _LABDIFF="$_LABDIFF $_p(lab=$_a 默认=$_b)"
done
printf '  lab 档量到：sizeof(Queue_t)=%s  sizeof(TCB_t)=%s  uxPriority=%s  uxBasePriority=%s  uxMutexesHeld=%s\n' \
    "$(_pnum build/labcfg/s.o probe_sizeof_Queue_t)" \
    "$(_pnum build/labcfg/s.o probe_sizeof_TCB_t)" \
    "$(_pnum build/labcfg/s.o probe_off_T_uxPriority)" \
    "$(_pnum build/labcfg/s.o probe_off_T_uxBasePriority)" \
    "$(_pnum build/labcfg/s.o probe_off_T_uxMutexesHeld)"
echo "       （上面第 4 步那张偏移表的全部数字，两个配置档一项不差；下面这条就是这句话的断言）"
eq "lab 配置档与默认档逐项读数相同（$_LABN 项全比）" "${_LABDIFF:-NONE}" "NONE"

echo
echo "############ 5. 出生那一发 give：互斥量天生就是「满」的 ############"
echo "----- 源码：xQueueCreateMutex 把 1 和 0 写成两个具名常量再传下去 -----"
cred "$QC" "长度 1 项 0" 'const UBaseType_t uxMutexLength = ( UBaseType_t ) 1, uxMutexSize = ( UBaseType_t ) 0;'
cred "$QC" "先建队列"   'xNewQueue = xQueueGenericCreate( uxMutexLength, uxMutexSize, ucQueueType );'
cred "$QC" "再贴 mutex 标签" 'prvInitialiseMutex( ( Queue_t \* ) xNewQueue );'
echo "----- prvInitialiseMutex 最后那句：创建即 send 一次，这就是「白送的 1」-----"
cred "$QC" "出生 give" '( void ) xQueueGenericSend( pxNewQueue, NULL, ( TickType_t ) 0U, queueSEND_TO_BACK );'
echo "----- 机身里的顺序：建 → 贴标签 → 白送一次，三句都在 -----"
dis_func build/queue/queue.o xQueueCreateMutex build/queue/cm.dis
sed 's|^|  |' build/queue/cm.dis
L_GC=$(line_of build/queue/cm.dis 'R_ARM_THM_CALL[[:space:]]+xQueueGenericCreate')
L_IM=$(line_of build/queue/cm.dis 'R_ARM_THM_CALL[[:space:]]+prvInitialiseMutex')
need "机身里找得到 bl xQueueGenericCreate" test "$L_GC" -gt 0
need "机身里找得到 bl prvInitialiseMutex" test "$L_IM" -gt 0
lt "先建队列再贴标签（xQueueGenericCreate 的行号 < prvInitialiseMutex 的行号）" "$L_GC" "$L_IM"
echo "----- 那两句的实参在机身里就是 1 和 0 两个立即数 -----"
have build/queue/cm.dis 'movs	r[0-9]+, #1' '送进 xQueueGenericCreate 的长度是立即数 1'
have build/queue/cm.dis 'movs	r[0-9]+, #0' '送进 xQueueGenericCreate 的每项大小是立即数 0'
echo "----- give 那句的两个 0：blockTime=0，所以创建时的还锁永不阻塞 -----"
dis_func build/queue/queue.o prvInitialiseMutex build/queue/im.dis
L_SEND=$(line_of build/queue/im.dis 'R_ARM_THM_CALL[[:space:]]+xQueueGenericSend')
gt "prvInitialiseMutex 里确实有一次 xQueueGenericSend 调用" "$L_SEND" 0
sed -n "$((L_SEND - 5)),$((L_SEND))p" build/queue/im.dis | sed 's|^|  送参数：|'
echo "----- 对照：二值信号量没有这一发。main.c:352-353 是自己补的一句 give -----"
cred ../01-freertos-lab/main.c "剧本补 give" 'xSemaphoreGive(g_lock);'
cred ../01-freertos-lab/main.c "剧本建二值" 'g_lock = xSemaphoreCreateBinary();'
cred ../01-freertos-lab/main.c "剧本建互斥" 'g_lock = xSemaphoreCreateMutex();'

echo
echo "############ 6. 唯一的那点区别：互斥量的身份就是 pcHead 这个指针是不是 NULL ############"
echo "----- 先记下这两行宏：所谓「队列类型」根本不是成员，是 pcHead 的别名 -----"
cred "$QC" "别名" '#define uxQueueType               pcHead'
cred "$QC" "身份值" '#define queueQUEUE_IS_MUTEX       NULL'
echo "----- 内核自己把这件事写在注释里 -----"
sed -n '/^\/\* When the Queue_t structure is used to represent a base queue/,/being used for\.\s*\*\//p' "$QC" \
    | sed 's|^|  |'
echo "----- prvInitialiseNewQueue：项大小 0 时，pcHead 不指向存储区，而是【自指】-----"
cred "$QC" "自指那句" 'pxNewQueue->pcHead = ( int8_t \* ) pxNewQueue;'
cred "$QC" "为什么不能是 NULL" 'NULL is used as a key to say the queue is used as'
echo "----- 然后 prvInitialiseMutex 把同一个槽覆盖成 NULL：这就是「变成互斥量」的全部 -----"
cred "$QC" "覆盖成 NULL" 'pxNewQueue->uxQueueType = queueQUEUE_IS_MUTEX;'
echo "----- 机身对得上偏移表：三个写 0 的槽，就是第 4 步量到的那三个数 -----"
dis_func build/queue/queue.o prvInitialiseMutex build/queue/im.dis
have build/queue/im.dis "str	r[0-9]+, \[r[0-9]+, #$O_PCHEAD\]" \
     "往 pcHead（偏移 $O_PCHEAD）写 0——这一句就是互斥量的身份本身"
have build/queue/im.dis "str	r[0-9]+, \[r[0-9]+, #$O_HOLDER\]" \
     "往 u.xSemaphore.xMutexHolder（偏移 $O_HOLDER）写 NULL"
have build/queue/im.dis "str	r[0-9]+, \[r[0-9]+, #$O_RECUR\]" \
     "往 u.xSemaphore.uxRecursiveCallCount（偏移 $O_RECUR）写 0"
echo "----- 反过来：普通队列那条路把 pcHead 写成结构体自己的地址（偏移同为 $O_PCHEAD）-----"
dis_func build/queue/queue.o prvInitialiseNewQueue build/queue/inq.dis
have build/queue/inq.dis "str	r[0-9]+, \[r[0-9]+, #$O_PCHEAD\]" \
     "prvInitialiseNewQueue 里对同一个槽的写：不是自指就是指向存储区"
sed -n "/uxItemSize/,+2p" "$QC" | head -4 | sed 's|^|  |'
echo "----- 那个 0/1/3/4 的 ucQueueType 只是标签：TRACE=0 时它连同成员一起消失 -----"
cred "$QC" "参数被丢掉" '( void ) ucQueueType;'
cred "$QC" "标签只在 TRACE 下写" 'pxNewQueue->ucQueueType = ucQueueType;'
grep -n "define queueQUEUE_TYPE_BASE\|define queueQUEUE_TYPE_MUTEX\|define queueQUEUE_TYPE_BINARY_SEMAPHORE" \
    "$K/include/queue.h" | sed 's|^|  标签值（第 2 步展开里看到的 3 和 1）queue.h:|'
SQ_T0=$(sizeof_of build/trace0/s.o probe_sizeof_Queue_t)
# 先钉 instrument 本身：读回的不是十进制数，就是那份 .o 没编出来或符号没落地。
# 这一步以前写错了路径（build/sizes/trace0/，真实路径是 build/trace0/），
# 于是 SQ_T0=NOSYM，$((80 - NOSYM)) 在 shell 里当成 0，差额"80"照样大于 0——
# 一条永远为真的断言。缺文件绝不能被算术吞成一个好看的数。
case "$SQ_T0" in
    ''|*[!0-9]*)
        echo "  [失] TRACE=0 档没量到 sizeof(Queue_t)（读回『$SQ_T0』）——文件没编出来，不许当结论" >&2
        FAIL=1; SQ_T0=$SQ_Q ;;
    *) echo "  [中] TRACE=0 档量到 sizeof(Queue_t)（= $SQ_T0）" ;;
esac
O_UCTYPE=$(off_of build/sizes/s.o probe_off_ucQueueType)
printf '  sizeof(Queue_t)：TRACE=1 %s 字节，TRACE=0 %s 字节，标签税 = %s 字节\n' \
    "$SQ_Q" "$SQ_T0" "$((SQ_Q - SQ_T0))"
gt "标签确实要付字节" $((SQ_Q - SQ_T0)) 0
need "TRACE=0 的档里那个偏移探针根本不存在" \
    test "$(sizeof_of build/trace0/s.o probe_off_ucQueueType)" = NOSYM
printf '  标签 ucQueueType 落在偏移 %s（是 UBaseType_t uxQueueNumber 之后的一字节）\n' "$O_UCTYPE"
echo "----- 机身侧对照：TRACE=0 编一份 queue.o，那句按字节写的标签应当一起没了 -----"
build_queue trace0 -DTRACE=0
dis_func build/trace0/queue.o prvInitialiseNewQueue build/trace0/inq.dis
dis_func build/queue/queue.o prvInitialiseNewQueue build/queue/inq.dis
lack build/trace0/inq.dis "strb.*\[r[0-9]+, #$O_UCTYPE\]" \
     "TRACE=0 的 prvInitialiseNewQueue 里没有往偏移 $O_UCTYPE 的字节写"
have build/queue/inq.dis "strb.*\[r[0-9]+, #$O_UCTYPE\]" \
     "TRACE=1 的同一函数里有那句按字节写的标签（strb，不是 str）"
echo "----- 身份检查在机身里长什么样：所有 mutex 判断都是拿 pcHead 跟 0 比 -----"
grep -n "uxQueueType == queueQUEUE_IS_MUTEX" "$QC" | sed 's|^|  判断点 queue.c:|'
ge "take/give/ISR 路上总共有几处这样的判断" "$(N_of 'uxQueueType == queueQUEUE_IS_MUTEX' "$QC")" 4

echo
echo "############ 7. 继承三步「判 → 改 → 搬」，和它的镜像回落 ############"
echo "----- 判 -----"
cred "$TSKC" "没有持有者就不继承" 'if( pxMutexHolder != NULL )'
cred "$TSKC" "持锁者更低才抬" 'if( pxMutexHolderTCB->uxPriority < pxCurrentTCB->uxPriority )'
echo "----- 改（事件表值 + 当前优先级）-----"
cred "$TSKC" "事件表值" 'listSET_LIST_ITEM_VALUE( &( pxMutexHolderTCB->xEventListItem ), ( TickType_t ) configMAX_PRIORITIES'
cred "$TSKC" "抬优先级" 'pxMutexHolderTCB->uxPriority = pxCurrentTCB->uxPriority;'
echo "----- 搬（摘旧表 → 复位位图 → 挂新表）-----"
cred "$TSKC" "摘" 'uxListRemove( &( pxMutexHolderTCB->xStateListItem ) )'
cred "$TSKC" "位图复位" 'portRESET_READY_PRIORITY( pxMutexHolderTCB->uxPriority, uxTopReadyPriority );'
cred "$TSKC" "挂" 'prvAddTaskToReadyList( pxMutexHolderTCB );'
echo "----- 只有继承没有回落是残缺的：镜像那半边 -----"
cred "$TSKC" "回落条件" 'if( pxTCB->uxMutexesHeld == ( UBaseType_t ) 0 )'
cred "$TSKC" "回落基准" 'pxTCB->uxPriority = pxTCB->uxBasePriority;'
cred "$TSKC" "回落也是摘挂一对" 'if( uxListRemove( &( pxTCB->xStateListItem ) ) == ( UBaseType_t ) 0 )'
echo "----- uxBasePriority 是谁写进去的：出生那一次 -----"
cred "$TSKC" "base 记在原处" 'pxNewTCB->uxBasePriority = uxPriority;'
cred "$TSKC" "base 的定义" 'UBaseType_t uxBasePriority'
dis_func build/tasks/tasks.o xTaskPriorityInherit build/inherit/inh.dis
dis_func build/tasks/tasks.o xTaskPriorityDisinherit build/inherit/dis.dis
echo "----- 机身里的判：两次读同一个偏移 $O_PRIO（uxPriority），再比 -----"
L_NULL=$(line_of build/inherit/inh.dis 'cmp	r[0-9]+, #0')
L_CMP=$(line_of build/inherit/inh.dis 'cmp	r[0-9]+, r[0-9]+')
gt "判空前先验了持有者不是 NULL" "$L_NULL" 0
gt "两处 uxPriority 之间有一次寄存器间比较" "$L_CMP" 0
ge "读偏移 $O_PRIO（uxPriority）的指令至少两句" \
   "$(N_of "\[r[0-9]*, #$O_PRIO\]" build/inherit/inh.dis)" 2
echo "----- 机身里的改：R4 那颗 configMAX_PRIORITIES 就是 rsb 的立即数 $NPRIO -----"
have build/inherit/inh.dis "rsb	r[0-9]+, r[0-9]+, #$NPRIO" \
     "configMAX_PRIORITIES - 等待者优先级，在机身里是一条 rsb #$NPRIO"
have build/inherit/inh.dis "str	r[0-9]+, \[r[0-9]+, #$O_EVENT\]" \
     "写回 xEventListItem.xItemValue（偏移 $O_EVENT）"
echo "----- 机身里的搬：摘是唯一的函数调用，挂是就地改指针（因为 listINSERT_END 是宏）-----"
eq "xTaskPriorityInherit 里的函数调用个数" \
   "$(grep -c 'R_ARM_THM_CALL' build/inherit/inh.dis)" 1
have build/inherit/inh.dis 'R_ARM_THM_CALL[[:space:]]+uxListRemove' '那唯一一次调用就是 uxListRemove（摘）'
cred "$LISTH" "挂为什么不产生调用" '#define listINSERT_END('
L_DET=$(line_of build/inherit/inh.dis 'uxListRemove')
L_SET=$(line_of build/inherit/inh.dis "str	r[0-9]+, \[r[0-9]+, #$O_PRIO\]")
L_CON=$(line_of_heap build/inherit/inh.dis "str	r[0-9]+, \[r[0-9]+, #$((O_STATE + O_PVCONT))\]")
gt "机身里找到了「改 uxPriority」那一句（偏移 $O_PRIO）" "$L_SET" 0
gt "机身里找到了「挂进新表」的那根 pvContainer（偏移 $((O_STATE + O_PVCONT))）" "$L_CON" 0
lt "顺序对得上：摘（$L_DET）→ 改（$L_SET）→ 搬（$L_CON）" "$L_DET" "$L_SET"
lt "顺序对得上：改（$L_SET）→ 搬（$L_CON）" "$L_SET" "$L_CON"
echo "----- 位图那两句在机身里是 lsl/mvns/ands（摘空才复位）与 lsl/orrs（挂上就立位）-----"
have build/inherit/inh.dis 'mvns' 'portRESET_READY_PRIORITY：&= ~(1 << prio) 的那个 mvns'
have build/inherit/inh.dis 'orrs' 'taskRECORD_READY_PRIORITY：|= (1 << prio) 的那个 orrs'
echo "----- 回落的方向正好相反：从 $O_BASE 读（uxBasePriority），往 $O_PRIO 写（uxPriority）-----"
L_B=$(line_of build/inherit/dis.dis "ldr	r[0-9]+, \[r[0-9]+, #$O_BASE\]")
L_W=$(line_of build/inherit/dis.dis "str	r[0-9]+, \[r[0-9]+, #$O_PRIO\]")
gt "回落里读到了 uxBasePriority（偏移 $O_BASE）" "$L_B" 0
gt "回落里写到了 uxPriority（偏移 $O_PRIO）" "$L_W" 0
have build/inherit/dis.dis "subs	r[0-9]+, r[0-9]+, #1" 'uxMutexesHeld-- 那句减 1'
have build/inherit/dis.dis 'R_ARM_THM_CALL[[:space:]]+uxListRemove' '回落也是先摘表'
echo "----- 最后把「继承是编译期的事」钉死：-DMUTEX=0 那批机身里这些函数不存在 -----"
eq "mutex0/tasks.o 里 xTaskPriorityInherit 的符号数" \
   $("${ARMPREFIX}nm" build/mutex0/tasks.o | grep -c xTaskPriorityInherit || true) 0
eq "mutex0/tasks.o 里 xTaskPriorityDisinherit 的符号数" \
   $("${ARMPREFIX}nm" build/mutex0/tasks.o | grep -c xTaskPriorityDisinherit || true) 0
ge "同一批 queue.o 机身里 xQueueSemaphoreTake 还在（拿锁这件事没被拿掉）" \
   $("${ARMPREFIX}nm" build/mutex0/queue.o | grep -c ' T xQueueSemaphoreTake' || true) 1
eq "正常档里 xTaskPriorityInherit 有定义" \
   $("${ARMPREFIX}nm" build/tasks/tasks.o | grep -c ' T xTaskPriorityInherit' || true) 1
B0=$(sz_of build/mutex0/tasks.o .text.xTaskPriorityInherit)
B1=$(sz_of build/tasks/tasks.o .text.xTaskPriorityInherit)
printf '  .text.xTaskPriorityInherit 的字节数：TRACE/MUTEX 默认档 %s，MUTEX=0 档 %s\n' "$B1" "$B0"
eq "MUTEX=0 档里这段机身一个字节都不占" "$B0" 0

echo
echo "############ 8. 反转的两个数：把继承规则抄成模型，再逐条核对规则本身 ############"
echo "----- 先上护栏：sim_invert.c 头注释里标了内核行号，行号一漂本步即失败 -----"
echo "       （内核一升级行号就会漂；漂了这份取证要报错，而不是悄悄给出一个错的数）"
at_line "$QC"  1784 'pxQueue->uxQueueType == queueQUEUE_IS_MUTEX'
at_line "$QC"  1788 'xTaskPriorityInherit( pxQueue->u.xSemaphore.xMutexHolder )'
at_line "$QC"  2405 'pxQueue->uxQueueType == queueQUEUE_IS_MUTEX'
at_line "$QC"  2408 'xTaskPriorityDisinherit( pxQueue->u.xSemaphore.xMutexHolder )'
at_line "$TSKC" 6589 'if( pxMutexHolder != NULL )'
at_line "$TSKC" 6594 'if( pxMutexHolderTCB->uxPriority < pxCurrentTCB->uxPriority )'
at_line "$TSKC" 6601 'listSET_LIST_ITEM_VALUE( &( pxMutexHolderTCB->xEventListItem ), ( TickType_t ) configMAX_PRIORITIES'
at_line "$TSKC" 6612 'uxListRemove( &( pxMutexHolderTCB->xStateListItem ) )'
at_line "$TSKC" 6617 'portRESET_READY_PRIORITY( pxMutexHolderTCB->uxPriority, uxTopReadyPriority );'
at_line "$TSKC" 6625 'pxMutexHolderTCB->uxPriority = pxCurrentTCB->uxPriority;'
at_line "$TSKC" 6626 'prvAddTaskToReadyList( pxMutexHolderTCB );'
at_line "$TSKC" 6641 'pxMutexHolderTCB->uxPriority = pxCurrentTCB->uxPriority;'
at_line "$LISTC" 192 'pxIterator->pxNext->xItemValue <= xValueOfInsertion'
echo "----- 剧本参数也得核：模型里那几个数是抄 main.c 的，main.c 改了模型就该报错 -----"
at_line ../01-freertos-lab/main.c 315 'cpu_work_ms(3000);'
at_line ../01-freertos-lab/main.c 324 'vTaskDelay(pdMS_TO_TICKS(500));'
at_line ../01-freertos-lab/main.c 326 'busy_until(pdMS_TO_TICKS(4500));'
at_line ../01-freertos-lab/main.c 334 'vTaskDelay(pdMS_TO_TICKS(1000));'
at_line ../01-freertos-lab/main.c 356 'xTaskCreate(task_low,  "L", configMINIMAL_STACK_SIZE, NULL, 1, NULL);'
at_line ../01-freertos-lab/main.c 358 'xTaskCreate(task_high, "H", configMINIMAL_STACK_SIZE, NULL, 3, NULL);'
at_line ../01-freertos-lab/main.c 339 '理论值：信号量版 ≈6000，互斥量版 ≈2500'
echo "----- 编模型：宿主机 gcc，-Wall -Wextra -Werror（这份规则抄得干不干净，编译器先过一遍）-----"
# 可执行文件名由平台决定：MinGW 的 gcc 会把 -o build/sim/sim 自动补成 sim.exe，
# Linux 的 gcc 不会——之前「编 sim、跑 sim.exe」在 CI 上是 exit 127。
case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*) SIMX=build/sim/sim.exe ;;
    *)                    SIMX=build/sim/sim ;;
esac
gcc -std=c11 -O0 -Wall -Wextra -Werror -o "$SIMX" sim_invert.c
need "模型编得过（$SIMX）" test -x "$SIMX"
"$SIMX" > build/sim/run.txt
"$SIMX" > build/sim/run2.txt
need "同一个二进制连跑两次输出逐字节相同（事件表写死，没有真时钟）" \
    cmp -s build/sim/run.txt build/sim/run2.txt
SIM=build/sim/run.txt
res() { # res tag 字段 → 那一幕 RES 行里该字段的值
    awk -v t="tag=$1" -v k="$2" '$1=="RES" && $2==t {
        for (i = 3; i <= NF; i++) { e = index($i, "="); if (substr($i,1,e-1)==k) print substr($i,e+1) }
    }' "$SIM"
}
echo "----- 读数器先自检：读不到字段就是 RES 格式变了，不能让它静默变成空串 -----"
ge "读数器没漂：binary 那幕的 waited 读得到" "$(res binary waited)" 0
ge "读数器没漂：mutex 那幕的 m_end 读得到" "$(res mutex m_end)" 0
echo "----- 两幕的结论行 -----"
grep '^RES' "$SIM" | sed 's|^|  |'
eq "二值信号量档：H 等了 6000 拍（模型值，不是板子毫秒）" "$(res binary waited)" 6000
eq "互斥量档：H 等了 2500 拍（模型值，不是板子毫秒）" "$(res mutex waited)" 2500
DIFF=$(( $(res binary waited) - $(res mutex waited) ))
eq "两档之差 = 3500 拍，就是继承在这出剧本里省下来的那段" "$DIFF" 3500
gt "继承确实省了时间（6000 > 2500）" "$(res binary waited)" "$(res mutex waited)"
echo "----- 判别式一：不继承时，H 得等 M 把 CPU 用完 -----"
gt "二值档 l_give 晚于 m_end（锁一直压在 L 手里，M 跑完才轮到）" \
   "$(res binary l_give)" "$(res binary m_end)"
echo "----- 判别式二：继承时，L 抬到 3 级，M 拦不住它 -----"
lt "互斥量档 l_give 早于 m_end（L 借到优先级，提前收工）" \
   "$(res mutex l_give)" "$(res mutex m_end)"
echo "----- 临界区工作量在两档里必须一样：3000 拍是剧本写死的，不是模型凑的 -----"
eq "二值档 L 真跑到 3000 拍" "$(res binary l_ran)" 3000
eq "互斥量档 L 真跑到 3000 拍" "$(res mutex l_ran)" 3000
eq "二值档 M 真跑到 4000 拍（3000+4000 正好等于 7000 拍收摊）" "$(res binary m_ran)" 4000
echo "----- 三档事件序列里最关键的那一步：只有互斥量档才出现 prio_inherited -----"
gt "互斥量档里出现了 prio_inherited" "$(N_of prio_inherited "$SIM")" 0
eq "整份日志里 inherit_skipped 只出现在二值档，共 1 次" "$(N_of inherit_skipped "$SIM")" 1
gt "互斥量档里出现了 prio_disinherited（还锁回落）" "$(N_of prio_disinherited "$SIM")" 0
printf '  继承那三步在日志里的现场（判 → 改 → 搬），互斥量档 t=1000 那一刻：\n'
INHERIT_SLICE=$(grep -E '^EVT tag=mutex[[:space:]]+t=1000' "$SIM" || true)
need "这一片切片非空（EVT 行的 tag/t 格式没漂）" test -n "$INHERIT_SLICE"
printf '%s\n' "$INHERIT_SLICE" | sed 's|^|    |'
printf '  二值档同一刻的现场（同一条规则走另一扇门）：\n'
grep -E '^EVT tag=binary[[:space:]]+t=1000' "$SIM" | sed 's|^|    |'
printf '  还锁那一步的现场，互斥量档 l_give=%s：\n' "$(res mutex l_give)"
grep -E "^EVT tag=mutex[[:space:]]+t=$(res mutex l_give)([^0-9]|$)" "$SIM" | sed 's|^|    |'
echo "----- 这两个数的身份：模型值。文档里「理论值」那句话得原样带过去 -----"
cred ../../../docs/lab/e04-priority-inversion.md "文档自称理论值" '不是实测'
NUMROWS=$(awk '/^## 实测记录/{f=1;next} /^## /{f=0} f' ../../../docs/lab/e04-priority-inversion.md \
          | grep -c '[0-9]' || true)
eq "E04 的实测记录那张表里一个数字都没有（模型值不许冒充实测）" "$NUMROWS" 0

echo
if [ "$FAIL" = 0 ]; then
    echo "== 全部断言通过 =="
else
    echo "== 有断言失败 ==" >&2
    exit 1
fi
