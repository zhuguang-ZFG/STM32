def swd_fetch():
    """SWD writes Flash, then the CPU reads MSP and Reset_Handler.

    Pin reuse and the failure byte stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("WRITE IMAGE", True, False, False, False, False),
        ("SWDIO pin34", True, True, False, False, False),
        ("SWCLK pin37", True, True, True, False, False),
        ("READ MSP", True, True, True, True, False),
        ("READ Reset", True, True, True, True, True),
        ("BOOT0 = 0", True, True, True, True, True),
    ]
    for index, (line, wr, dio, clk, msp, rst) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "SWD FETCH", "BOOT0=0", "AUX GIF  STATIC SVG HAS THE FAILURE")
        c.panel(16, 42, 140, 70, C.PANEL, C.CYAN if dio else C.STROKE)
        c.text("SWDIO", 48, 58, C.CYAN if dio else C.DIM, 1)
        c.text("pin 34", 40, 84, C.TEXT if dio else C.DIM, 1)
        c.panel(168, 42, 140, 70, C.PANEL, C.GREEN if clk else C.STROKE)
        c.text("SWCLK", 200, 58, C.GREEN if clk else C.DIM, 1)
        c.text("pin 37", 192, 84, C.TEXT if clk else C.DIM, 1)
        c.panel(320, 42, 140, 70, C.PANEL, C.AMBER if wr else C.STROKE)
        c.text("FLASH", 350, 58, C.AMBER if wr else C.DIM, 1)
        c.text("0x0800..", 336, 84, C.TEXT if wr else C.DIM, 1)
        c.panel(16, 126, 220, 36, C.PANEL2 if msp else C.PANEL, C.STROKE)
        c.text("MSP WORD0" if msp else "MSP IDLE", 28, 140, C.TEXT if msp else C.DIM, 1)
        c.panel(248, 126, 212, 36, C.PANEL, C.GREEN if rst else C.STROKE)
        c.text("Reset_Handler" if rst else "RH WAIT", 260, 140, C.TEXT if rst else C.DIM, 1)
        c.text(line, 16, 190, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 214, C.MUTED, 1)
        c.text("MSP THEN Reset_Handler", 16, 240, C.GREEN, 1)
        c.text("BOOT0 STAYS 0", 16, 262, C.CYAN, 1)
        c.text("PRINT PIN REUSE ON THE STATIC SVG", 16, 284, C.DIM, 1)
        g.add(c)
    return g
