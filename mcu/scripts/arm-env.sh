#!/bin/sh
# scripts/arm-env.sh —— 给 build/取证命令补上 ARM 交叉工具链与 make 的 PATH。
# 本机工具链（2026-10-07 实测）：
#   xPack GNU Arm Embedded 15.2.1.1：D:\zhugu-home\tools\armgcc\...（README 01-rcc-clock 记录）
#   mingw32-make 4.4.1 / gcc 16.1.0：D:\zhugu-home\mingw64\mingw64\bin
export PATH="/d/zhugu-home/tools/armgcc/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin:/d/zhugu-home/mingw64/mingw64/bin:/c/Program Files/Git/usr/bin:$PATH"
exec "$@"
