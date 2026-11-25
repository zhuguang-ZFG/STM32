"""Check the actual vector table, interrupt entries, and memory budget."""
import struct
import subprocess
import sys
from pathlib import Path


def check(elf_path, binary_path):
    symbols = {}
    symbol_types = {}
    output = subprocess.check_output(["arm-none-eabi-nm", "-n", str(elf_path)], text=True)
    for line in output.splitlines():
        fields = line.split()
        if len(fields) == 3:
            address, symbol_type, name = fields
            symbols[name] = int(address, 16)
            symbol_types[name] = symbol_type
    binary = Path(binary_path).read_bytes()
    stack, reset = struct.unpack_from("<II", binary)
    systick = struct.unpack_from("<I", binary, 15 * 4)[0]
    dma1_ch5 = struct.unpack_from("<I", binary, (15 + 16) * 4)[0]
    usart1 = struct.unpack_from("<I", binary, (37 + 16) * 4)[0]
    assert stack == 0x20005000, hex(stack)
    assert reset == symbols["Reset_Handler"] | 1, hex(reset)
    assert systick == symbols["SysTick_Handler"] | 1, hex(systick)
    assert dma1_ch5 == symbols["DMA1_Channel5_IRQHandler"] | 1, hex(dma1_ch5)
    assert usart1 == symbols["USART1_IRQHandler"] | 1, hex(usart1)
    for name in ("SysTick_Handler", "DMA1_Channel5_IRQHandler", "USART1_IRQHandler"):
        assert symbol_types[name] == "T", f"weak/default {name}"
    assert symbols["g_pfnVectors"] == 0x08000000
    assert 0 < len(binary) <= 64 * 1024
    assert 0x20000000 <= symbols["_sbss"] <= symbols["_ebss"] <= stack - 2048
    assert 0x20000000 <= symbols["g_dma_rx_buf"] < stack - 2048
    print(
        f"PASS: {len(binary)} Flash bytes; SP={stack:#x}; reset={reset:#x}; "
        f"SysTick={systick:#x}; DMA1_CH5={dma1_ch5:#x}; USART1={usart1:#x}; "
        "DMA buffer in SRAM; >=2 KiB stack reserved"
    )


if __name__ == "__main__":
    check(*sys.argv[1:])
