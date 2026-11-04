def one_slot():
    """Fill 16 KB, 2 KB, and one 0xB800 image up to 0x08010000.

    The second image and the oversized SRAM array stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("BOOT 16 KB", True, False, False, False, False),
        ("END 0x08004000", True, True, False, False, False),
        ("GAP 2 KB", True, True, True, False, False),
        ("APP 0x08004800", True, True, True, True, False),
        ("LEN 0xB800", True, True, True, True, True),
        ("END 0x08010000", True, True, True, True, True),
    ]
    for index, (line, boot, end16, gap, app, length) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "ONE SLOT", "64 KB", "AUX GIF  APP")
        c.panel(16, 42, 140, 70, C.PANEL, C.CYAN if boot else C.STROKE)
        c.text("BOOT", 56, 58, C.CYAN if boot else C.DIM, 1)
        c.text("16 KB", 48, 84, C.TEXT if boot else C.DIM, 1)
        c.panel(168, 42, 140, 70, C.PANEL, C.GREEN if gap else C.STROKE)
        c.text("GAP", 214, 58, C.GREEN if gap else C.DIM, 1)
        c.text("2 KB", 208, 84, C.TEXT if gap else C.DIM, 1)
        c.panel(320, 42, 140, 70, C.PANEL, C.AMBER if app else C.STROKE)
        c.text("APP", 360, 58, C.AMBER if app else C.DIM, 1)
        c.text("0xB800", 344, 84, C.TEXT if app else C.DIM, 1)
        c.panel(16, 126, 300, 36, C.PANEL2 if end16 else C.PANEL, C.STROKE)
        c.text("0x08004000 MARK" if end16 else "BOOT WINDOW", 28, 140, C.TEXT if end16 else C.DIM, 1)
        c.panel(328, 126, 132, 36, C.PANEL, C.GREEN if length else C.STROKE)
        c.text("FIT" if length else "...", 370, 140, C.TEXT if length else C.DIM, 1)
        c.text(line, 16, 190, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 214, C.MUTED, 1)
        c.text("16 KB + 2 KB + 0xB800", 16, 240, C.GREEN, 1)
        c.text("ENDS AT 0x08010000", 16, 262, C.CYAN, 1)
        c.text("PRINT SLOT-2 ON THE STATIC SVG", 16, 284, C.DIM, 1)
        g.add(c)
    return g
