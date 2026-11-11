TARGET ?= watchdog-health
MODE ?= 0
FAULTS ?= 0
ifeq ($(filter $(MODE),0 1 2 3),)
$(error MODE must be 0 1 2 3)
endif
ifeq ($(filter $(FAULTS),0 1),)
$(error FAULTS must be 0 or 1)
endif
ifneq ($(words $(MODE) $(FAULTS)),2)
$(error Exactly one MODE and FAULTS value required)
endif
BUILD := build/mode-$(MODE)-faults-$(FAULTS)
KERNEL ?= ../../../.trellis/ref/freertos-v11/kernel
CC := arm-none-eabi-gcc
MCU := -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard
CFLAGS := $(MCU) -O2 -g3 -Wall -Wextra -Werror -MMD -MP -ffunction-sections -fdata-sections -I. -I$(KERNEL)/include -I$(KERNEL)/portable/GCC/ARM_CM4F -DMODE=$(MODE) -DFAULTS=$(FAULTS)
OBJ_NAMES := startup main uart protocol transport service query health record tasks queue list timers event_groups port heap_4 syscalls $(EXTRA_OBJECTS)
OBJS := $(addprefix $(BUILD)/,$(addsuffix .o,$(OBJ_NAMES)))
.DEFAULT_GOAL := all
vpath %.c . ../platform ../../common/reliability $(KERNEL) $(KERNEL)/portable/GCC/ARM_CM4F $(KERNEL)/portable/MemMang $(EXTRA_DIRS)
-include $(OBJS:.o=.d)
$(OBJS): Makefile ../platform/rtos.mk FreeRTOSConfig.h
all: $(BUILD)/$(TARGET).elf $(BUILD)/$(TARGET).bin $(BUILD)/$(TARGET).hex
	arm-none-eabi-size $(BUILD)/$(TARGET).elf
$(BUILD):
	mkdir -p $(BUILD)
$(BUILD)/%.o: %.c | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@
$(addprefix $(BUILD)/,tasks.o queue.o list.o timers.o event_groups.o port.o heap_4.o): CFLAGS := $(filter-out -Wall -Wextra -Werror,$(CFLAGS))
$(BUILD)/startup.o: startup_stm32f407xx.s | $(BUILD)
	$(CC) $(MCU) -g3 -c $< -o $@
$(BUILD)/$(TARGET).elf: $(OBJS) stm32f407xx.ld
	$(CC) $(MCU) -nostartfiles -T stm32f407xx.ld -Wl,--gc-sections -Wl,-Map=$(BUILD)/$(TARGET).map $(OBJS) -o $@
$(BUILD)/%.bin: $(BUILD)/%.elf
	arm-none-eabi-objcopy -O binary $< $@
$(BUILD)/%.hex: $(BUILD)/%.elf
	arm-none-eabi-objcopy -O ihex $< $@
flash: all
	openocd -f interface/stlink.cfg -f target/stm32f4x.cfg -c "program $(BUILD)/$(TARGET).elf verify reset exit"
.PHONY: all flash
