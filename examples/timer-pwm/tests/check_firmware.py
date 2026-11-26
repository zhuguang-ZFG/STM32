"""Check the real PWM vector table, timer state and SRAM budget."""
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

    htim3 = symbols["htim3"]
    assert symbol_types["htim3"] == "B", f"timer handle type {symbol_types['htim3']}"
    assert 0x20000000 <= htim3 < symbols["_ebss"], "timer handle outside .bss"
    assert sizes["htim3"] >= 16, sizes["htim3"]
    assert symbols["_ebss"] <= stack - 2048, "less than 2 KiB stack reserved"

    print(
        f"PASS: {len(binary)} Flash bytes; SP={stack:#x}; reset={reset:#x}; "
        f"SysTick={systick:#x}; htim3={htim3:#x}+{sizes['htim3']} B; "
        f"RAM={symbols['_ebss'] - 0x20000000} B; >=2 KiB stack reserved"
    )


if __name__ == "__main__":
    check(*sys.argv[1:])
