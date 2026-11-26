"""Check the real ADC/DMA firmware: vector table, buffer layout and SRAM budget."""
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

    assert stack == 0x20005000, hex(stack)
    assert reset == symbols["Reset_Handler"] | 1, hex(reset)
    assert systick == symbols["SysTick_Handler"] | 1, hex(systick)
    assert symbol_types["SysTick_Handler"] == "T", "weak/default SysTick_Handler"
    assert symbols["g_pfnVectors"] == 0x08000000
    assert 0 < len(binary) <= 64 * 1024

    for name in ("hadc1", "hdma_adc1"):
        assert symbol_types[name] in ("b", "B"), f"{name} type {symbol_types[name]}"
        assert sizes[name] > 0, f"{name} has no storage"

    # 3 ranks × 16 samples of halfword data, DMA-aligned inside .bss.
    for name, size in (("g_adc_buf", 96), ("g_ma_buf", 96)):
        assert symbol_types[name] in ("b", "B"), f"{name} type {symbol_types[name]}"
        assert sizes[name] == size, f"{name} size {sizes[name]}"
        assert 0x20000000 <= symbols[name] < symbols["_ebss"], f"{name} outside .bss"
    assert symbols["g_adc_buf"] % 2 == 0, "DMA halfword buffer is not halfword aligned"
    for name in ("g_ma_idx", "g_ma_filled"):
        assert symbol_types[name] in ("b", "B"), f"{name} type {symbol_types[name]}"
        assert sizes[name] == 1, f"{name} size {sizes[name]}"

    assert symbols["_ebss"] <= stack - 2048, "less than 2 KiB stack reserved"

    print(
        f"PASS: {len(binary)} Flash bytes; SP={stack:#x}; reset={reset:#x}; "
        f"SysTick={systick:#x}; g_adc_buf={symbols['g_adc_buf']:#x}+96; "
        f"g_ma_buf={symbols['g_ma_buf']:#x}+96; "
        f"RAM={symbols['_ebss'] - 0x20000000} B; >=2 KiB stack reserved"
    )


if __name__ == "__main__":
    check(*sys.argv[1:])
