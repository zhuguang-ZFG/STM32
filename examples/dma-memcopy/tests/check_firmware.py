"""Check the real DMA vector table, buffer layout and SRAM budget."""
import struct
import subprocess
import sys
from pathlib import Path


def check(elf_path, binary_path):
    symbols = {}
    sizes = {}
    symbol_types = {}
    output = subprocess.check_output(
        ["arm-none-eabi-nm", "-n", "-S", str(elf_path)], text=True
    )
    for line in output.splitlines():
        fields = line.split()
        if len(fields) == 4:
            address, size, symbol_type, name = fields
            symbols[name] = int(address, 16)
            sizes[name] = int(size, 16)
            symbol_types[name] = symbol_type
        elif len(fields) == 3:
            address, symbol_type, name = fields
            symbols[name] = int(address, 16)
            symbol_types[name] = symbol_type

    binary = Path(binary_path).read_bytes()
    stack, reset = struct.unpack_from("<II", binary)
    systick = struct.unpack_from("<I", binary, 15 * 4)[0]
    dma1_ch1 = struct.unpack_from("<I", binary, (11 + 16) * 4)[0]

    assert stack == 0x20005000, hex(stack)
    assert reset == symbols["Reset_Handler"] | 1, hex(reset)
    assert systick == symbols["SysTick_Handler"] | 1, hex(systick)
    assert dma1_ch1 == symbols["DMA1_Channel1_IRQHandler"] | 1, hex(dma1_ch1)
    for name in ("SysTick_Handler", "DMA1_Channel1_IRQHandler"):
        assert symbol_types[name] == "T", f"weak/default {name}"
    assert symbols["g_pfnVectors"] == 0x08000000
    assert 0 < len(binary) <= 64 * 1024

    src = symbols["g_dma_src"]
    dst = symbols["g_dma_dst"]
    assert sizes["g_dma_src"] == 4096, sizes["g_dma_src"]
    assert sizes["g_dma_dst"] == 4096, sizes["g_dma_dst"]
    assert src % 4 == 0 and dst % 4 == 0
    assert src + 4096 <= dst or dst + 4096 <= src, "DMA buffers overlap"
    assert 0x20000000 <= src < symbols["_ebss"]
    assert 0x20000000 <= dst < symbols["_ebss"]
    assert symbols["_ebss"] <= stack - 2048, "less than 2 KiB stack reserved"

    print(
        f"PASS: {len(binary)} Flash bytes; SP={stack:#x}; reset={reset:#x}; "
        f"SysTick={systick:#x}; DMA1_CH1={dma1_ch1:#x}; "
        f"src={src:#x}+4096; dst={dst:#x}+4096; "
        f"RAM={symbols['_ebss'] - 0x20000000} B; >=2 KiB stack reserved"
    )


if __name__ == "__main__":
    check(*sys.argv[1:])
