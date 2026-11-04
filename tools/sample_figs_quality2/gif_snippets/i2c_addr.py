def i2c_addr():
    """START, shift 0x78, then ACK on the 9th clock.

    A raw address byte and a missing pull-up stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("START", True, False, False, False),
        ("SHIFT 0x78", True, True, False, False),
        ("BIT 7 TO BIT 0", True, True, False, False),
        ("9TH CLOCK", True, True, True, False),
        ("SDA LOW  ACK", True, True, True, True),
        ("0x801E  4.7 k", True, True, True, True),
    ]
    for index, (note, st, sh, ninth, ack) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "I2C ADDR", "0x78", "AUX GIF  ACK")
        c.panel(16, 42, 448, 28, C.PANEL, C.STROKE)
        c.text("PB6 SCL  PB7 SDA", 28, 52, C.MUTED, 1)
        c.panel(16, 80, 100, 54, C.PANEL, C.AMBER if st else C.STROKE)
        c.text("START", 35, 110, C.AMBER if st else C.DIM, 1)
        c.panel(130, 80, 120, 54, C.PANEL, C.CYAN if sh else C.STROKE)
        c.text("0x78", 165, 110, C.CYAN if sh else C.DIM, 1)
        c.panel(264, 80, 100, 54, C.PANEL, C.VIOLET if ninth else C.STROKE)
        c.text("9TH", 292, 110, C.VIOLET if ninth else C.DIM, 1)
        c.panel(378, 80, 86, 54, C.PANEL, C.GREEN if ack else C.STROKE)
        c.text("ACK", 398, 110, C.GREEN if ack else C.DIM, 1)
        c.text(note, 16, 170, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 194, C.MUTED, 1)
        c.text("0x78 THEN ACK", 16, 220, C.GREEN, 1)
        c.text("0x801E AND 4.7 k", 16, 242, C.CYAN, 1)
        c.text("PRINT THE NACK ON THE STATIC SVG", 16, 266, C.DIM, 1)
        g.add(c)
    return g
