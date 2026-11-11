# Makefile —— 03-uart-dma：串口收发的两级缓冲，和"可写 ≠ 发完"
#
# 用法：
#   make            构建 build/uart-dma.elf + .bin + .hex + .map
#   make flash      OpenOCD + ST-Link 烧录并复位运行
#   make clean
#
# Windows 注意：需要 PATH 上有 arm-none-eabi-gcc、mingw32-make，
# 以及 Git 的 usr\bin（Makefile 用到 mkdir -p / rm -rf）。

TARGET   := uart-dma
BUILD    := build

CC       := arm-none-eabi-gcc
OBJCOPY  := arm-none-eabi-objcopy
SIZE     := arm-none-eabi-size

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