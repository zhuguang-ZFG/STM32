# opt_probe —— volatile 取证工程（C3 章配套）：宿主 gcc + ARM 交叉两套
#
#   make asm O=0        生成 -O0 宿主汇编 opt_probe.O0.s
#   make asm O=2        生成 -O2 宿主汇编 opt_probe.O2.s
#   make asm-arm        生成 Cortex-M4 汇编 opt_probe.m4.O2.s（+ .O0.s）← 板上同一优化决策
#   make run            编译并运行（只跑不会死等/不会段错误的现场）
#   make clean
#
# 取证环境（2026-10-06 本机实测，两套均 -std=c11 -Wall -Wextra 零告警）：
#   宿主：MinGW-Builds gcc 16.1.0 x86_64-posix-seh，binutils objdump 2.46
#   交叉：xPack GNU Arm Embedded GCC 15.2.1 20251203，-mcpu=cortex-m4 -mthumb

CC      ?= gcc
CFLAGS  ?= -std=c11 -Wall -Wextra
O       ?= 2

ARM_CC    ?= arm-none-eabi-gcc
ARM_FLAGS ?= -std=c11 -Wall -Wextra -mcpu=cortex-m4 -mthumb

all: run

asm:
	$(CC) $(CFLAGS) -O$(O) -S -o opt_probe.O$(O).s opt_probe.c
	@echo "汇编已输出到 opt_probe.O$(O).s —— 搜 poll_plain / poll_volatile / cfg_plain / cfg_volatile"

# 交叉两套一起出，方便逐条对账：-O0 是"-O0 能跑"的真相，-O2 是翻车现场
asm-arm:
	$(ARM_CC) $(ARM_FLAGS) -O0 -S -o opt_probe.m4.O0.s opt_probe.c
	$(ARM_CC) $(ARM_FLAGS) -O2 -S -o opt_probe.m4.O2.s opt_probe.c
	@echo "Cortex-M4 汇编：opt_probe.m4.O0.s / opt_probe.m4.O2.s"

run: opt_probe
	./opt_probe

opt_probe: opt_probe.c
	$(CC) $(CFLAGS) -O$(O) -o $@ $<

clean:
	rm -f opt_probe opt_probe.exe opt_probe.O0.s opt_probe.O2.s \
	      opt_probe.m4.O0.s opt_probe.m4.O2.s

.PHONY: all asm asm-arm run clean
