# Makefile —— 02-rt-thread-lab：RT-Thread 5.x（src/ + libcpu/arm/cortex-m4）手动移植
#
# 用法：
#   make                            场景 1（双线程异频闪灯，R7 验收点）
#   make DEMO_SCENE=6               场景 6（优先级反转·信号量版）
#   make DEMO_SCENE=6 USE_MUTEX=1   场景 6（优先级反转·互斥量版）
#   make flash / make clean
#
# 内核源码：默认取本仓库的忽略缓存 .trellis/ref/rt-thread（RT-Thread 5.x
#   master；获取方式见 README.md）。也可用 RT_THREAD_DIR=<你的路径> 覆盖。
#
# 裁剪说明：src/ 只编 Nano 最小集（线程/调度/IPC/内存/tick），标准版
#   （设备框架/finsh/DFS）不参与构建——R7 "Nano 四件套" 路线。
#
# 注意：内核源文件（src/ 与 libcpu）编译时必须定义 __RT_KERNEL_SOURCE__，
#   否则 rtsched.h 里的内部调度 API（rt_sched_tick_increase 等）不可见——
#   官方 scons 构建同样注入该宏。

TARGET := rt-thread-lab
RT_THREAD_DIR ?= ../../../.trellis/ref/rt-thread

DEMO_SCENE ?= 1
ifeq ($(filter $(DEMO_SCENE),1 6),)
$(error DEMO_SCENE must be 1 or 6)
endif
BUILD := build/scene-$(DEMO_SCENE)$(if $(USE_MUTEX),-mutex)
.DEFAULT_GOAL := all

CC       := arm-none-eabi-gcc
OBJCOPY  := arm-none-eabi-objcopy
SIZE     := arm-none-eabi-size

MCU      := -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard

INC      := -I. -Iboard -Iapplications \
            -I$(RT_THREAD_DIR)/include \
            -I$(RT_THREAD_DIR)/libcpu/arm/cortex-m4

CFLAGS   := $(MCU) -O0 -g3 -Wall -Wextra -MMD -MP $(INC) \
            -ffunction-sections -fdata-sections \
            -DDEMO_SCENE=$(DEMO_SCENE)
ifneq ($(USE_MUTEX),)
CFLAGS += -DUSE_MUTEX=1
endif
ASFLAGS  := $(MCU) -g3
LDFLAGS  := $(MCU) -T stm32f407xx.ld \
            -Wl,--gc-sections -Wl,-Map=$(BUILD)/$(TARGET).map \
            -nostartfiles

# 工程源码在子目录：让模式规则能找到 applications/main.c 与 board/board.c
vpath %.c applications board

# 内核源文件：Nano 最小集（见 README.md 的裁剪表）。
# 内核代码按上游原样编译，不参与 -Wall -Wextra 的零警告口径（同 01-freertos-lab）。
RT_SRCS := $(RT_THREAD_DIR)/src/clock.c \
           $(RT_THREAD_DIR)/src/cpu_up.c \
           $(RT_THREAD_DIR)/src/defunct.c \
           $(RT_THREAD_DIR)/src/idle.c \
           $(RT_THREAD_DIR)/src/ipc.c \
           $(RT_THREAD_DIR)/src/irq.c \
           $(RT_THREAD_DIR)/src/kservice.c \
           $(RT_THREAD_DIR)/src/mem.c \
           $(RT_THREAD_DIR)/src/object.c \
           $(RT_THREAD_DIR)/src/scheduler_comm.c \
           $(RT_THREAD_DIR)/src/scheduler_up.c \
           $(RT_THREAD_DIR)/src/thread.c \
           $(RT_THREAD_DIR)/src/timer.c \
$(RT_THREAD_DIR)/src/klibc/kstring.c \
           $(RT_THREAD_DIR)/src/klibc/kstdio.c \
           $(RT_THREAD_DIR)/src/klibc/rt_vsnprintf_std.c

OBJS     := $(BUILD)/startup_stm32f407xx.o $(BUILD)/main.o $(BUILD)/syscalls.o \
            $(BUILD)/board.o \
            $(patsubst %.c,$(BUILD)/%.o,$(notdir $(RT_SRCS))) \
            $(BUILD)/cpuport.o $(BUILD)/context_gcc.o

-include $(OBJS:.o=.d)

$(OBJS): Makefile rtconfig.h

all: $(BUILD)/$(TARGET).elf $(BUILD)/$(TARGET).bin $(BUILD)/$(TARGET).hex
	$(SIZE) $(BUILD)/$(TARGET).elf

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/%.o: %.c | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/%.o: %.s | $(BUILD)
	$(CC) $(ASFLAGS) -c $< -o $@

# 内核对象：宽松告警 + __RT_KERNEL_SOURCE__，其余参数一致
$(BUILD)/clock.o: $(RT_THREAD_DIR)/src/clock.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/cpu_up.o: $(RT_THREAD_DIR)/src/cpu_up.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/defunct.o: $(RT_THREAD_DIR)/src/defunct.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/idle.o: $(RT_THREAD_DIR)/src/idle.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/ipc.o: $(RT_THREAD_DIR)/src/ipc.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/irq.o: $(RT_THREAD_DIR)/src/irq.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/kservice.o: $(RT_THREAD_DIR)/src/kservice.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/mem.o: $(RT_THREAD_DIR)/src/mem.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/object.o: $(RT_THREAD_DIR)/src/object.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/scheduler_comm.o: $(RT_THREAD_DIR)/src/scheduler_comm.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/scheduler_up.o: $(RT_THREAD_DIR)/src/scheduler_up.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/thread.o: $(RT_THREAD_DIR)/src/thread.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/timer.o: $(RT_THREAD_DIR)/src/timer.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/kstring.o: $(RT_THREAD_DIR)/src/klibc/kstring.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/kstdio.o: $(RT_THREAD_DIR)/src/klibc/kstdio.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/rt_vsnprintf_std.o: $(RT_THREAD_DIR)/src/klibc/rt_vsnprintf_std.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/cpuport.o: $(RT_THREAD_DIR)/libcpu/arm/cortex-m4/cpuport.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -D__RT_KERNEL_SOURCE__ -ffunction-sections -fdata-sections -c $< -o $@
$(BUILD)/context_gcc.o: $(RT_THREAD_DIR)/libcpu/arm/cortex-m4/context_gcc.S | $(BUILD)
	$(CC) $(ASFLAGS) -I. -c $< -o $@

$(BUILD)/$(TARGET).elf: $(OBJS) stm32f407xx.ld
	$(CC) $(OBJS) $(LDFLAGS) -o $@

$(BUILD)/$(TARGET).bin: $(BUILD)/$(TARGET).elf
	$(OBJCOPY) -O binary $< $@

$(BUILD)/$(TARGET).hex: $(BUILD)/$(TARGET).elf
	$(OBJCOPY) -O ihex $< $@

OPENOCD_CFG := -f interface/stlink.cfg -f target/stm32f4x.cfg

flash: all
	openocd $(OPENOCD_CFG) -c "program $(BUILD)/$(TARGET).elf verify reset exit"

clean:
	rm -rf $(BUILD)

.PHONY: all flash clean