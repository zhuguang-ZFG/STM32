# Makefile —— 01-rcc-clock：把时钟树从图纸变成方波
#
# 用法：
#   make                  构建（默认留在 HSI 16MHz，板上没晶振也能跑）
#   make USE_HSE_PLL=1    构建 HSE + PLL 到 168MHz 版本
#   make HSE_VALUE_HZ=25000000 USE_HSE_PLL=1
#                          板上晶振不是 8MHz 时必须显式传值
#   make flash            OpenOCD + ST-Link 烧录并复位运行
#   make clean
#
# Windows 注意：Makefile 用了 mkdir -p / rm -rf，需要 PATH 里有
# mingw64 的 bin（例如 D:\zhugu-home\mingw64\mingw64\bin），
# 否则 make 与 make clean 都会因找不到命令失败。

TARGET   := rcc-clock
BUILD    := build

USE_HSE_PLL  ?= 0
HSE_VALUE_HZ ?= 8000000

CC       := arm-none-eabi-gcc
OBJCOPY  := arm-none-eabi-objcopy
SIZE     := arm-none-eabi-size

MCU      := -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard

CFLAGS   := $(MCU) -O0 -g3 -Wall -Wextra \
            -ffunction-sections -fdata-sections \
            -DUSE_HSE_PLL=$(USE_HSE_PLL) -DHSE_VALUE_HZ=$(HSE_VALUE_HZ)UL
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