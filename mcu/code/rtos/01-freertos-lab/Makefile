# Makefile —— 01-freertos-lab：上游 V11.1.0 + ARM_CM4F 单核端口
#
# 用法：
#   make                        场景 1（任务与 TCB）
#   make DEMO_SCENE=2           场景 2（任务通知）
#   make DEMO_SCENE=3           场景 3（事件组）
#   make DEMO_SCENE=4           场景 4（软件定时器）
#   make DEMO_SCENE=5           场景 5（堆）
#   make DEMO_SCENE=6           场景 6（优先级反转·信号量版）
#   make DEMO_SCENE=6 USE_MUTEX=1  场景 6（优先级反转·互斥量版）
#   make flash / make clean
#
# 内核源码：默认取本仓库的忽略缓存 .trellis/ref/freertos-v11/kernel
#   （FreeRTOS-Kernel tag V11.1.0；获取方式见 README.md）。
#   也可以用 FREERTOS_KERNEL=<你的路径> 覆盖。

TARGET   := freertos-lab
FREERTOS_KERNEL ?= ../../../.trellis/ref/freertos-v11/kernel
DEMO_SCENE      ?= 1
ifneq ($(words $(DEMO_SCENE)),1)
$(error DEMO_SCENE must be one of 1 2 3 4 5 6)
endif
ifeq ($(filter $(DEMO_SCENE),1 2 3 4 5 6),)
$(error DEMO_SCENE must be one of 1 2 3 4 5 6)
endif
# 参数变化不是 make 的文件依赖；每场景独立产物，切换无需 clean。
BUILD    := build/scene-$(DEMO_SCENE)
.DEFAULT_GOAL := all

CC       := arm-none-eabi-gcc
OBJCOPY  := arm-none-eabi-objcopy
SIZE     := arm-none-eabi-size

MCU      := -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard

INC      := -I. -I$(FREERTOS_KERNEL)/include \
            -I$(FREERTOS_KERNEL)/portable/GCC/ARM_CM4F

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

# 内核源文件：warning 门禁只管我们自己的代码；内核源文件按上游原样编译，
# 不参与 -Wall -Wextra 的零警告口径（上游 GCC 构建在 portable 层有已知告警）。
KERNEL_SRCS := $(FREERTOS_KERNEL)/tasks.c \
               $(FREERTOS_KERNEL)/queue.c \
               $(FREERTOS_KERNEL)/list.c \
               $(FREERTOS_KERNEL)/event_groups.c \
               $(FREERTOS_KERNEL)/timers.c \
               $(FREERTOS_KERNEL)/portable/GCC/ARM_CM4F/port.c \
               $(FREERTOS_KERNEL)/portable/MemMang/heap_4.c

OBJS     := $(BUILD)/startup_stm32f407xx.o $(BUILD)/main.o $(BUILD)/syscalls.o \
            $(patsubst %.c,$(BUILD)/%.o,$(notdir $(KERNEL_SRCS)))

-include $(OBJS:.o=.d)

# 工程配置/内核配置/规则变化都必须重建，不只观察 .c 的时间戳。
$(OBJS): Makefile FreeRTOSConfig.h

all: $(BUILD)/$(TARGET).elf $(BUILD)/$(TARGET).bin $(BUILD)/$(TARGET).hex
	$(SIZE) $(BUILD)/$(TARGET).elf

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/%.o: %.c | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/%.o: %.s | $(BUILD)
	$(CC) $(ASFLAGS) -c $< -o $@

# 内核对象：宽松告警（上游原样），其余参数一致
$(BUILD)/tasks.o: $(FREERTOS_KERNEL)/tasks.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -ffunction-sections -fdata-sections -DDEMO_SCENE=$(DEMO_SCENE) -c $< -o $@
$(BUILD)/queue.o: $(FREERTOS_KERNEL)/queue.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -ffunction-sections -fdata-sections -DDEMO_SCENE=$(DEMO_SCENE) -c $< -o $@
$(BUILD)/list.o: $(FREERTOS_KERNEL)/list.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -ffunction-sections -fdata-sections -DDEMO_SCENE=$(DEMO_SCENE) -c $< -o $@
$(BUILD)/event_groups.o: $(FREERTOS_KERNEL)/event_groups.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -ffunction-sections -fdata-sections -DDEMO_SCENE=$(DEMO_SCENE) -c $< -o $@
$(BUILD)/timers.o: $(FREERTOS_KERNEL)/timers.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -ffunction-sections -fdata-sections -DDEMO_SCENE=$(DEMO_SCENE) -c $< -o $@
$(BUILD)/port.o: $(FREERTOS_KERNEL)/portable/GCC/ARM_CM4F/port.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -ffunction-sections -fdata-sections -DDEMO_SCENE=$(DEMO_SCENE) -c $< -o $@
$(BUILD)/heap_4.o: $(FREERTOS_KERNEL)/portable/MemMang/heap_4.c | $(BUILD)
	$(CC) $(MCU) -O0 -g3 $(INC) -ffunction-sections -fdata-sections -DDEMO_SCENE=$(DEMO_SCENE) -c $< -o $@

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
