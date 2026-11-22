"""Check the actual vector table, memory budget, and strong HAL timebase."""
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
    assert stack == 0x20005000, hex(stack)
    assert reset == symbols["Reset_Handler"] | 1, hex(reset)
    assert systick == symbols["SysTick_Handler"] | 1, hex(systick)
    assert symbol_types["SysTick_Handler"] == "T", "weak/default SysTick handler"
    assert symbols["g_pfnVectors"] == 0x08000000
    assert 0 < len(binary) <= 64 * 1024
    assert 0x20000000 <= symbols["_sbss"] <= symbols["_ebss"] <= stack - 2048
    print(f"PASS: {len(binary)} Flash bytes; SP={stack:#x}; reset={reset:#x}; SysTick={systick:#x}; >=2 KiB stack reserved")


if __name__ == "__main__":
    check(*sys.argv[1:])
