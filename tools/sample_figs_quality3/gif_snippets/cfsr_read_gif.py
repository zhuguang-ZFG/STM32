def cfsr_read_gif():
    """Read CFSR, see bit 15 set, then let 72 counts finish 1 us.

    A clear bit 15 and a cycle delta of 0 stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("READ CFSR", True, False, False, False),
        ("0xE000ED28", True, True, False, False),
        ("bit 15 = 1", True, True, True, False),
        ("COUNT 24", True, True, True, True),
        ("COUNT 72", True, True, True, True),
        ("1 us", True, True, True, True),
    ]
    for index, (line, cfsr, addr, bit, dwt) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "CFSR", "DWT", "AUX GIF  1 us")
        c.panel(16, 42, 210, 70, C.PANEL, C.CYAN if cfsr else C.STROKE)
        c.text("CFSR", 90, 58, C.CYAN if cfsr else C.DIM, 1)
        c.text("0xE000ED28" if addr else "READ", 40, 84, C.TEXT if cfsr else C.DIM, 1)
        c.panel(250, 42, 210, 70, C.PANEL, C.GREEN if bit else C.STROKE)
        c.text("BFARVALID", 290, 58, C.GREEN if bit else C.DIM, 1)
        c.text("bit 15 = 1" if bit else "PENDING", 290, 84, C.TEXT if bit else C.DIM, 1)
        c.panel(16, 126, 444, 36, C.PANEL2 if dwt else C.PANEL, C.STROKE)
        dlabel = "72 COUNTS = 1 us" if index >= 5 else ("COUNT 72" if index == 4 else ("COUNT 24" if index == 3 else "DWT IDLE"))
        c.text(dlabel, 28, 140, C.TEXT if dwt else C.DIM, 1)
        c.text("72 MHz", 16, 180, C.MUTED, 1)
        c.text(line, 16, 206, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 228, C.MUTED, 1)
        c.text("bit 15 = 1", 16, 252, C.GREEN, 1)
        c.text("72 COUNTS = 1 us", 16, 274, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 16, 294, C.DIM, 1)
        g.add(c)
    return g
