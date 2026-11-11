# Makefile —— 00-blink：把四个步骤摆在明面上（预处理→编译→汇编→链接）
#
# 用法：
#   make            构建 build/blink.elf + .bin + .hex + .map
#   make flash      用 OpenOCD + ST-Link 烧录并复位运行
#   make debug      启动 OpenOCD GDB 服务（另开终端跑 make gdb）
#   make gdb        连上调试
#   make clean

TARGET   := blink
BUILD    := build

CC       := arm-none-eabi-gcc
OBJCOPY  := arm-none-eabi-objcopy
SIZE     := arm-none-eabi-size

# Cortex-M4 带硬件 FPU：硬浮点 ABI，中断/任务切换才有得聊
MCU      := -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard

CFLAGS   := $(MCU) -O0 -g3 -Wall -Wextra \
            -ffunction-sections -fdata-sections
ASFLAGS  := $(MCU) -g3
LDFLAGS  := $(MCU) -T stm32f407xx.ld \
            -Wl,--gc-sections -Wl,-Map=$(BUILD)/$(TARGET).map \
            -nostartfiles

OBJS     := $(BUILD)/startup_stm32f407xx.o $(BUILD)/main.o

all: $(BUILD)/$(TARGET).elf $(BUILD)/$(TARGET).bin $(BUILD)/$(TARGET).hex
	$(SIZE) $(BUILD)/$(TARGET).elf

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/%.o: %.c | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/%.o: %.s | $(BUILD)
	$(CC) $(ASFLAGS) -c $< -o $@

$(BUILD)/$(TARGET).elf: $(OBJS) stm32f407xx.ld
	$(CC) $(OBJS) $(LDFLAGS) -o $@

$(BUILD)/$(TARGET).bin: $(BUILD)/$(TARGET).elf
	$(OBJCOPY) -O binary $< $@

$(BUILD)/$(TARGET).hex: $(BUILD)/$(TARGET).elf
	$(OBJCOPY) -O ihex $< $@

# ---- 烧录与调试（OpenOCD + ST-Link） ----
OPENOCD_CFG := -f interface/stlink.cfg -f target/stm32f4x.cfg

flash: all
	openocd $(OPENOCD_CFG) -c "program $(BUILD)/$(TARGET).elf verify reset exit"

debug: all
	openocd $(OPENOCD_CFG)

gdb:
	arm-none-eabi-gdb $(BUILD)/$(TARGET).elf \
	  -ex "target remote localhost:3333" \
	  -ex "monitor reset halt" \
	  -ex "load" \
	  -ex "break main" \
	  -ex "continue"

clean:
	rm -rf $(BUILD)

.PHONY: all flash debug gdb clean
