# Makefile —— gd32/01-rcu-clock（xPack arm-none-eabi-gcc）

TARGET   := gd32-rcu-clock
BUILD    := build
CC       := arm-none-eabi-gcc
OBJCOPY  := arm-none-eabi-objcopy
SIZE     := arm-none-eabi-size
CFLAGS   := -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard \
            -g3 -O1 -Wall -Wextra -std=c11 -ffreestanding -fno-builtin \
            -DGD32F450 \
            -Wa,--noexecstack
# 只有 startup 的 .s 声明了 .note.GNU-stack，C 的 main.o 没有，ld 见到不一致就警告
# "implies executable stack"。让 as 给 C 目标文件写同一节，两边对齐——比用
# --no-warn-execstack 关掉检查诚实（后者连真的不一致也看不见）。产物逐字节不变。
LDSCRIPT := gd32f4xx.ld
LD_FLAGS := -T $(LDSCRIPT) -nostartfiles -Wl,--gc-sections -Wl,-Map=$(BUILD)/$(TARGET).map

SRCS := startup_gd32f4xx.s main.c
OBJS := $(patsubst %,$(BUILD)/%,$(SRCS:.c=.o))
OBJS := $(OBJS:.s=.o)

all: $(BUILD)/$(TARGET).bin

$(BUILD)/%.o: %.c | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/%.o: %.s | $(BUILD)
	$(CC) $(CFLAGS) -c $< -o $@

$(BUILD)/$(TARGET).elf: $(OBJS)
	$(CC) $(CFLAGS) $(OBJS) $(LD_FLAGS) -o $@

$(BUILD)/$(TARGET).bin: $(BUILD)/$(TARGET).elf
	$(OBJCOPY) -O binary $< $@
	$(SIZE) $<

$(BUILD):
	mkdir -p $(BUILD)

clean:
	rm -rf $(BUILD)

.PHONY: all clean