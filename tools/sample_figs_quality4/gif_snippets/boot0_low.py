def boot0_low():
    """Pin 44 is 0 and the probe sits on pins 34 and 37.

    The high BOOT pin and an optimizer edit stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("PA13 SWDIO", True, False, False, False, False),
        ("PA14 SWCLK", True, True, False, False, False),
        ("GND COMMON", True, True, True, False, False),
        ("3.3 V SENSE", True, True, True, True, False),
        ("BOOT0 PIN44", True, True, True, True, True),
        ("BOOT0 = 0", True, True, True, True, True),
    ]
    for index, (line, io, clk, gnd, vcc, boot) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "BOOT0", "SWD", "AUX GIF  TARGET")
        c.panel(16, 42, 140, 70, C.PANEL, C.CYAN if io else C.STROKE)
        c.text("PA13", 56, 58, C.CYAN if io else C.DIM, 1)
        c.text("pin 34", 40, 84, C.TEXT if io else C.DIM, 1)
        c.panel(168, 42, 140, 70, C.PANEL, C.GREEN if clk else C.STROKE)
        c.text("PA14", 208, 58, C.GREEN if clk else C.DIM, 1)
        c.text("pin 37", 192, 84, C.TEXT if clk else C.DIM, 1)
        c.panel(320, 42, 140, 70, C.PANEL, C.AMBER if boot else C.STROKE)
        c.text("BOOT0", 350, 58, C.AMBER if boot else C.DIM, 1)
        c.text("pin 44", 348, 84, C.TEXT if boot else C.DIM, 1)
        c.panel(16, 126, 220, 36, C.PANEL2 if gnd else C.PANEL, C.STROKE)
        c.text("GND SHARED" if gnd else "GND ?", 28, 140, C.TEXT if gnd else C.DIM, 1)
        c.panel(248, 126, 212, 36, C.PANEL, C.GREEN if vcc else C.STROKE)
        c.text("3.3 V SENSE" if vcc else "VCC ?", 260, 140, C.TEXT if vcc else C.DIM, 1)
        c.text(line, 16, 190, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 214, C.MUTED, 1)
        c.text("BOOT0 = 0", 16, 240, C.GREEN, 1)
        c.text("TARGET SEEN AT 0x08000000", 16, 262, C.CYAN, 1)
        c.text("PRINT HIGH BOOT ON THE STATIC SVG", 16, 284, C.DIM, 1)
        g.add(c)
    return g
