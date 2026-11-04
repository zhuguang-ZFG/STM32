def iap_jump():
    """Write the two keys in order, then read MSP and Reset_Handler.

    A reversed key and the address past 64 KB stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("KEY1 0x45670123", True, False, False, False, False),
        ("KEY2 0xCDEF89AB", True, True, False, False, False),
        ("HALF-WORD IN APP", True, True, True, False, False),
        ("READ MSP", True, True, True, True, False),
        ("READ Reset_Handler", True, True, True, True, True),
        ("VTOR 0x08004800", True, True, True, True, True),
    ]
    for index, (line, k1, k2, prog, msp, vtor) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "IAP JUMP", "APP", "AUX GIF  KEY ORDER")
        c.panel(16, 42, 210, 56, C.PANEL, C.CYAN if k1 else C.STROKE)
        c.text("KEY1", 90, 56, C.CYAN if k1 else C.DIM, 1)
        c.text("0x45670123", 40, 78, C.TEXT if k1 else C.DIM, 1)
        c.panel(250, 42, 210, 56, C.PANEL, C.GREEN if k2 else C.STROKE)
        c.text("KEY2", 324, 56, C.GREEN if k2 else C.DIM, 1)
        c.text("0xCDEF89AB", 274, 78, C.TEXT if k2 else C.DIM, 1)
        c.panel(16, 110, 210, 36, C.PANEL, C.AMBER if prog else C.STROKE)
        c.text("HALF-WORD" if prog else "PROG IDLE", 28, 124, C.TEXT if prog else C.DIM, 1)
        c.panel(250, 110, 210, 36, C.PANEL, C.VIOLET if msp else C.STROKE)
        c.text("MSP + Reset_Handler" if msp else "VECTOR IDLE", 258, 124, C.TEXT if msp else C.DIM, 1)
        c.panel(16, 158, 444, 28, C.PANEL2 if vtor else C.PANEL, C.STROKE)
        c.text("VTOR 0x08004800  0xB800" if vtor else "VTOR PENDING", 28, 170, C.TEXT if vtor else C.DIM, 1)
        c.text(line, 16, 210, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 232, C.MUTED, 1)
        c.text("MSP THEN Reset_Handler", 16, 254, C.GREEN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 16, 276, C.DIM, 1)
        g.add(c)
    return g
