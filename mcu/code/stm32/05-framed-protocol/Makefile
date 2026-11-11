# Makefile —— 05-framed-protocol：USART1 二进制帧协议
#
# 用法：
#   make            构建 build/framed-protocol.elf + .bin + .hex + .map
#   make flash      OpenOCD + ST-Link 烧录并复位运行
#   make clean
#
# Windows 注意：需要 PATH 上有 arm-none-eabi-gcc、mingw32-make，
# 以及 Git 的 usr\bin（Makefile 用到 mkdir -p / rm -rf）。
# 协议/服务源码直接复用公共模块（不复制）。

TARGET   := framed-protocol
BUILD    := build
COMMON   := ../../common/reliability

CC       := arm-none-eabi-gcc
OBJCOPY  := arm-none-eabi-objcopy
SIZE     := arm-none-eabi-size

MCU      := -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard

CFLAGS   := $(MCU) -O2 -g3 -Wall -Wextra \
            -ffunction-sections -fdata-sections
ASFLAGS  := $(MCU) -g3
LDFLAGS  := $(MCU) -T stm32f407xx.ld \
            -Wl,--gc-sections -Wl,-Map=$(BUILD)/$(TARGET).map \
            -nostartfiles

OBJS     := $(BUILD)/startup_stm32f407xx.o $(BUILD)/main.o \
            $(BUILD)/protocol.o $(BUILD)/transport.o $(BUILD)/service.o $(BUILD)/query.o $(BUILD)/uart.o

all: $(BUILD)/$(TARGET).elf $(BUILD)/$(TARGET).bin $(BUILD)/$(TARGET).hex
	$(SIZE) $(BUILD)/$(TARGET).elf

$(BUILD):
	mkdir -p $(BUILD)

$(BUILD)/%.o: %.c | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/startup_stm32f407xx.o: startup_stm32f407xx.s | $(BUILD)
	$(CC) $(ASFLAGS) -c $< -o $@

$(BUILD)/main.o: main.c $(COMMON)/service.h $(COMMON)/transport.h $(COMMON)/protocol.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/protocol.o: $(COMMON)/protocol.c | $(BUILD)
	$(CC) $(CFLAGS) -I$(COMMON) -c $< -o $@

$(BUILD)/transport.o: $(COMMON)/transport.c | $(BUILD)
	$(CC) $(CFLAGS) -I$(COMMON) -c $< -o $@

$(BUILD)/service.o: $(COMMON)/service.c | $(BUILD)
	$(CC) $(CFLAGS) -I$(COMMON) -c $< -o $@

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

$(BUILD)/uart.o: ../platform/uart.c ../platform/uart.h | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/query.o: $(COMMON)/query.c | $(BUILD)
	$(CC) $(CFLAGS) -I$(COMMON) -c $< -o $@
