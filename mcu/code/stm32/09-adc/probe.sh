#!/bin/sh
# probe.sh —— S9 逐次逼近（SAR）取证（宿主机就能跑，不需要开发板，也不需要 make）
#   sh probe.sh            跑全部（sar + vin + ts + cross），结尾打印断言汇总
#   sh probe.sh sar        12 轮二分表 + 最终码值 + 量化误差 + 自检
#   sh probe.sh vin        换输入电压再看一轮（对照动画里的 2.00 V）
#   sh probe.sh ts         采样时间 vs 源阻抗：RC 推导算最少周期数 + 选档
#   sh probe.sh cross      只用交叉工具链编一遍，证明算法在 Cortex-M4 上编得出
#   sh probe.sh clean
#
# 用宿主 gcc 编 sar_probe.exe / ts_probe.exe（产物落 build/，已 gitignore）。交叉编译
# 那份也顺手造出来，证明这段代码在目标板上同样跑得动——但它不代替板上实测。

set -e
cd "$(dirname "$0")"
mkdir -p build

HOSTCC=${HOSTCC:-gcc}
ARM_PREFIX=${ARM_PREFIX:-arm-none-eabi-}
ARMCC="${ARM_PREFIX}gcc"
ARMFLAGS="-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard -Os -ffunction-sections"

have() { command -v "$1" >/dev/null 2>&1; }

sar_probe() {
    have "$HOSTCC" || { echo "找不到 $HOSTCC —— 装一个宿主 gcc（或 HOSTCC=... sh probe.sh）" >&2; exit 1; }
    "$HOSTCC" -std=c11 -O2 -Wall -Wextra -Werror sar_probe.c -o build/sar_probe.exe
    ./build/sar_probe.exe
}

ts_probe() {
    have "$HOSTCC" || { echo "找不到 $HOSTCC —— 装一个宿主 gcc（或 HOSTCC=... sh probe.sh）" >&2; exit 1; }
    "$HOSTCC" -std=c11 -O2 -Wall -Wextra -Werror ts_probe.c -lm -o build/ts_probe.exe
    ./build/ts_probe.exe
}

vin_probe() {
    have "$HOSTCC" || { echo "找不到 $HOSTCC" >&2; exit 1; }
    for v in 1.65 2.00 3.29; do
        "$HOSTCC" -std=c11 -O2 -Wall -Wextra -Werror -DVIN=$v sar_probe.c -o "build/sar_$v.exe"
        printf '%s\n' "----- Vin=$v V -----"
        out=$("./build/sar_$v.exe")   # 失败时 set -e 在此拦下（不能走管道，管道吃掉退出码）
        printf '%s\n' "$out" | tail -3
    done
    echo "1.65 V 恰好落在半量程 0x800（误差 0.00 LSB）；3.29 V 停在 0xFF3，离满量程 0xFFF 还差 12 个码，量化误差 0.59 LSB。"
}

cross_probe() {
    have "$ARMCC" || { echo "找不到 $ARMCC —— 交叉那步跳过（本取证不依赖它）"; return 0; }
    "$ARMCC" $ARMFLAGS -c sar_probe.c -o build/sar_cross.o
    "$ARMCC" $ARMFLAGS -c ts_probe.c -o build/ts_cross.o
    echo "交叉目标文件已生成：两段算法在 Cortex-M4 上同样编得出来（printf 由 libc 提供）。"
}

case "${1:-all}" in
    sar)   sar_probe ;;
    vin)   vin_probe ;;
    ts)    ts_probe ;;
    cross) cross_probe ;;
    all)   sar_probe; echo; vin_probe; echo; ts_probe; echo; cross_probe
           echo "== 断言通过 5/5 ==（sar×1 + vin×3 + ts×1，任一失败 set -e 都会让本行到不了）" ;;
    clean) rm -rf build ;;
    *)     echo "用法：sh probe.sh [sar|vin|ts|cross|clean]" >&2; exit 1 ;;
esac
