#!/bin/sh
# probe.sh —— F2《上下文切换：PendSV 换魂术》取证，一条命令跑完
#
#   sh probe.sh        用已编好的 build/scene-1 产物做五步取证（缺产物会自动 make）
#   sh probe.sh clean  删 build/
#
# 五步：
#   1) 名字的两层：内核源码里叫 xPortPendSVHandler，编出来叫 PendSV_Handler，
#      中间靠 FreeRTOSConfig.h 的一行 #define 接到启动文件的向量表上；
#   2) PendSV_Handler 全反汇编 + 指令条数 + 字节数（"百周期量级"的分母就在这）；
#   3) 三行铁账：一条 stmdb 压 9 个字、str 写进 TCB 偏移 0、basepri 立即数 #80；
#   4) 优先级账：configKERNEL_INTERRUPT_PRIORITY=255 与 configMAX_SYSCALL=5<<4；
#   5) 没跑过的任务怎么被"造"出来：pxPortInitialiseStack 伪造的 18 个字。
#
# 需要：arm-none-eabi-gcc / objdump / nm 在 PATH 里（本站交叉工具链 10.3.1 或 15.2.1 均可，
# naked 汇编不受编译器版本影响）。产物一律落在 build/（code/**/build/ 已 gitignore）。

set -e
cd "$(dirname "$0")"

if [ "$1" = "clean" ]; then
    rm -rf build
    exit 0
fi

K=${FREERTOS_KERNEL:-../../../.trellis/ref/freertos-v11/kernel}
PORT="$K/portable/GCC/ARM_CM4F/port.c"
OBJ=build/scene-1/port.o
[ -f "$OBJ" ] || make DEMO_SCENE=1 >/dev/null

echo "############ 1. 名字的两层：源码名 → #define → 向量表名 ############"
echo "内核源码（$PORT）："
grep -n "^void xPortPendSVHandler( void )" "$PORT"
echo "本工程的映射（FreeRTOSConfig.h）："
grep -n "define xPortPendSVHandler\|define vPortSVCHandler" FreeRTOSConfig.h
echo "启动文件向量表（startup_stm32f407xx.s）："
grep -n "word PendSV_Handler" startup_stm32f407xx.s
echo "编出来的实际符号（nm $OBJ）——大写 T 是被宏改过名的 handler，小写 t 是 static 局部符号："
arm-none-eabi-nm "$OBJ" | grep -E "PendSV_Handler|SVC_Handler|vTaskSwitchContext|prvTaskExitError|pxPortInitialiseStack"

echo
echo "############ 2. PendSV_Handler 反汇编全文（一次切换要走的每一条） ############"
arm-none-eabi-objdump -d --section=.text.PendSV_Handler "$OBJ" \
    | sed -n '/<PendSV_Handler>:/,/^$/p' | grep -v "^\s*$"
N=$(arm-none-eabi-objdump -d --section=.text.PendSV_Handler "$OBJ" \
    | awk '/<PendSV_Handler>:/{f=1;next} f&&/bx[[:space:]]+lr/{print n+1;exit} f&&/^[[:space:]]+[0-9a-f]+:/{n++}')
B=$(arm-none-eabi-size -A "$OBJ" | awk '/\.text\.PendSV_Handler/{print $2}')
echo "----- 账 -----"
printf '  正文指令条数 = %s 条（数到 bx lr 为止，后面的 nop 填充与字面量池不算）\n' "$N"
printf '  段大小 = %s 字节（含对齐填充和 pxCurrentTCBConst 字面量）\n' "$B"

echo
echo "############ 3. 三行铁账 ############"
D=$(arm-none-eabi-objdump -d --section=.text.PendSV_Handler "$OBJ")
echo "----- ① 一条 stmdb 把 r4-r11 + EXC_RETURN 压进任务栈：9 个字 = 36 字节 -----"
echo "$D" | grep -E "stmdb|ldmia" || true
echo "----- ② 栈顶存进 TCB 的偏移 0（'封棺'为什么敢写 #0）-----"
echo "$D" | grep -E "str\s+r0, \[r2|ldr\s+r2, \[r3|ldr\s+r1, \[r3" || true
grep -n "pxTopOfStack; /\*\*< Points to the location" "$K/tasks.c" \
    | sed -E 's/^([0-9]+): +/\1  /; s|^|  凭据 tasks.c:|'
echo "----- ③ 临界区的 basepri 立即数：#80 = 5 << 4 -----"
echo "$D" | grep -E "BASEPRI|mov.w\s+r0, #80" || true

echo
echo "############ 4. 优先级账：执刑官为什么永远最后上场 ############"
grep -n "configKERNEL_INTERRUPT_PRIORITY\|configMAX_SYSCALL_INTERRUPT_PRIORITY\|configPRIO_BITS\|configTICK_RATE_HZ" FreeRTOSConfig.h
echo "----- 但内核根本不读 configKERNEL_INTERRUPT_PRIORITY -----"
echo "port.c 自己硬写的最低优先级（$PORT）："
grep -n "define portMIN_INTERRUPT_PRIORITY\|define portNVIC_PENDSV_PRI\|define portNVIC_SYSTICK_PRI" "$PORT"
grep -n "portNVIC_SHPR3_REG |= portNVIC_.*_PRI" "$PORT"
echo "整个 ARM_CM4F 移植层里 configKERNEL_INTERRUPT_PRIORITY 出现的次数："
grep -rc "configKERNEL_INTERRUPT_PRIORITY" "$(dirname "$PORT")" | sed 's|^|  |'
echo "内核自己的变更记录："
grep -n -A1 "configKERNEL_INTERRUPT_PRIORITY is now obsolete" "$K/History.txt" | head -4
echo "----- 真正被内核连查三遍的是 configMAX_SYSCALL_INTERRUPT_PRIORITY -----"
grep -n "configASSERT( ucMaxSysCallPriority )\|configMAX_SYSCALL_INTERRUPT_PRIORITY & ( ~ucMaxPriorityValue )\|configMAX_SYSCALL_INTERRUPT_PRIORITY & 0x1U" "$PORT" | sed 's|^|  |'
echo "----- handler 是否真接进向量表（改名那三行宏的意义）-----"
grep -n "pxVectorTable\[ portVECTOR_INDEX_" "$PORT" | sed 's|^|  |'
echo "  → PendSV/SysTick 由内核硬设成 255（4 位域全 1）＝全系统最低；"
echo "    临界区只抬到 5<<4 = 80，高于 5 的中断照样进得来，切换排队等它们服完。"

echo
echo "############ 5. 没跑过的任务，第一帧是伪造的 ############"
sed -n '/^StackType_t \* pxPortInitialiseStack/,/^}/p' "$PORT" | grep -vE "^[[:space:]]*(/\*|\*)"
echo "----- 三个立即数的来历 -----"
grep -n "define portINITIAL_XPSR\|define portINITIAL_EXC_RETURN\|define portSTART_ADDRESS_MASK" "$PORT"
echo "----- 帧有多长：把源码里的回退量当场加起来 -----"
sed -n '/^StackType_t \* pxPortInitialiseStack/,/^}/p' "$PORT" \
    | awk '/pxTopOfStack -= /{ s += $3 + 0; next } /pxTopOfStack--/ { s += 1 }
           END { printf "  指针回退 %d 个字，加上最后停住的那个落点共 %d 个字 = %d 字节\n", s, s + 1, (s + 1) * 4;
                 print  "  对得上账：硬件帧 8（xPSR/PC/LR/R12/R3/R2/R1/R0）+ 软件帧 9（r4-r11 + EXC_RETURN）+ 对齐 1 = 18" }'
echo "  注意 portINITIAL_EXC_RETURN = 0xfffffffd 的 bit4 = 1：初始帧里没有 FPU 行李，"
echo "  任务第一次跑出彩点（用到浮点）时才由硬件扩展成 26 个字。"
echo "----- 编译产物里能看到 0x01000000 这条装载 -----"
arm-none-eabi-objdump -d --section=.text.pxPortInitialiseStack "$OBJ" \
    | grep -E "16777216|0x1000000|bic" | head -4
