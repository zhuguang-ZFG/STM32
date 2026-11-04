def iwdg_1s():
    """A 625 Hz count is fed before it reaches 0.

    Off-by-one reload and the window watchdog stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("40 kHz TYPICAL", True, False, False, False, False),
        ("prescaler 64", True, True, False, False, False),
        ("625 Hz", True, True, True, False, False),
        ("COUNT DOWN", True, True, True, True, False),
        ("FEED BEFORE ZERO", True, True, True, True, True),
        ("Reload = 624", True, True, True, True, True),
    ]
    for index, (line, lsi, psc, tick, count, feed) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "IWDG 1S", "624", "AUX GIF  TYPICAL 40 kHz")
        c.panel(16, 42, 140, 70, C.PANEL, C.CYAN if lsi else C.STROKE)
        c.text("LSI", 60, 58, C.CYAN if lsi else C.DIM, 1)
        c.text("40 kHz", 40, 84, C.TEXT if lsi else C.DIM, 1)
        c.panel(168, 42, 140, 70, C.PANEL, C.GREEN if psc else C.STROKE)
        c.text("/64", 214, 58, C.GREEN if psc else C.DIM, 1)
        c.text("PSC", 214, 84, C.TEXT if psc else C.DIM, 1)
        c.panel(320, 42, 140, 70, C.PANEL, C.AMBER if tick else C.STROKE)
        c.text("625 Hz", 350, 58, C.AMBER if tick else C.DIM, 1)
        c.text("TICK", 360, 84, C.TEXT if tick else C.DIM, 1)
        c.panel(16, 126, 300, 36, C.PANEL2 if count else C.PANEL, C.STROKE)
        c.text("COUNT  N .. 1" if count else "COUNT  IDLE", 28, 140, C.TEXT if count else C.DIM, 1)
        c.panel(328, 126, 132, 36, C.PANEL, C.GREEN if feed else C.STROKE)
        c.text("FEED" if feed else "WAIT", 360, 140, C.TEXT if feed else C.DIM, 1)
        c.text(line, 16, 190, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 214, C.MUTED, 1)
        c.text("Reload = 624", 16, 240, C.GREEN, 1)
        c.text("625 Hz UNTIL THE FEED", 16, 262, C.CYAN, 1)
        c.text("PRINT ZERO AND THE WINDOW ON THE SVG", 16, 284, C.DIM, 1)
        g.add(c)
    return g
