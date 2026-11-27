"""Check the real EXTI0 vector table, key state layout and SRAM budget."""
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
    exti0 = struct.unpack_from("<I", binary, (6 + 16) * 4)[0]

    assert stack == 0x20005000, hex(stack)
    assert reset == symbols["Reset_Handler"] | 1, hex(reset)
    assert systick == symbols["SysTick_Handler"] | 1, hex(systick)
    assert exti0 == symbols["EXTI0_IRQHandler"] | 1, hex(exti0)
    for name in ("SysTick_Handler", "EXTI0_IRQHandler"):
        assert symbol_types[name] == "T", f"weak/default {name}"
    assert symbols["g_pfnVectors"] == 0x08000000
    assert 0 < len(binary) <= 64 * 1024

    for name, size in (("g_key_event", 1), ("g_key_count", 4)):
        assert symbol_types[name] in ("b", "B"), f"{name} type {symbol_types[name]}"
        assert sizes[name] == size, f"{name} size {sizes[name]}"
        assert 0x20000000 <= symbols[name] < symbols["_ebss"], f"{name} outside .bss"
    assert symbols["_ebss"] <= stack - 2048, "less than 2 KiB stack reserved"

    print(
        f"PASS: {len(binary)} Flash bytes; SP={stack:#x}; reset={reset:#x}; "
        f"SysTick={systick:#x}; EXTI0={exti0:#x}; "
        f"g_key_event={symbols['g_key_event']:#x}+1; g_key_count={symbols['g_key_count']:#x}+4; "
        f"RAM={symbols['_ebss'] - 0x20000000} B; >=2 KiB stack reserved"
    )


if __name__ == "__main__":
    check(*sys.argv[1:])
