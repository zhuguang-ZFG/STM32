def spi_jedec():
    """CS falls, MOSI shifts 0x9F, then MISO returns 0xEF 0x40 0x17 at 9 MHz.

    The swapped-wire failure stays on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("CS LOW", True, "", ""),
        ("MOSI 0x9F", True, "0x9F", ""),
        ("MISO 0xEF", True, "0x9F", "EF"),
        ("MISO 0x40", True, "0x9F", "EF 40"),
        ("MISO 0x17", True, "0x9F", "EF 40 17"),
        ("CS HIGH  9 MHz", False, "0x9F", "EF 40 17"),
    ]
    for index, (note, cs_low, mosi, miso) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "SPI JEDEC", "MODE 0", "AUX GIF  9 MHz")
        c.panel(16, 42, 448, 28, C.PANEL, C.STROKE)
        c.text("PA5 SCK  PA7 MOSI  PA6 MISO", 28, 52, C.MUTED, 1)
        c.panel(16, 80, 100, 54, C.PANEL, C.AMBER if cs_low else C.STROKE)
        c.text("CS", 50, 96, C.AMBER if cs_low else C.DIM, 1)
        c.text("LOW" if cs_low else "HIGH", 40, 120, C.TEXT if cs_low else C.DIM, 1)
        c.panel(130, 80, 150, 54, C.PANEL, C.CYAN if mosi else C.STROKE)
        c.text("MOSI", 175, 96, C.CYAN if mosi else C.DIM, 1)
        c.text(mosi or "-", 170, 120, C.TEXT if mosi else C.DIM, 1)
        c.panel(294, 80, 170, 54, C.PANEL, C.GREEN if miso else C.STROKE)
        c.text("MISO", 350, 96, C.GREEN if miso else C.DIM, 1)
        c.text(miso or "-", 320, 120, C.TEXT if miso else C.DIM, 1)
        c.text(note, 16, 170, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 194, C.MUTED, 1)
        c.text("0x9F THEN 0xEF 0x40 0x17", 16, 220, C.GREEN, 1)
        c.text("9 MHz  BR=010", 16, 242, C.CYAN, 1)
        c.text("PRINT THE SWAP ON THE STATIC SVG", 16, 266, C.DIM, 1)
        g.add(c)
    return g
