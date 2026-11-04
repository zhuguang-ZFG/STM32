def usb_48m():
    """D+ is pulled up, the clock is 48 MHz, then 18 and 67 bytes.

    The undivided clock and the pull-up on DM stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("D+ PULL-UP", True, False, False, False, False),
        ("HOST SEES D+", True, True, False, False, False),
        ("USBPRE = 0", True, True, True, False, False),
        ("48 MHz", True, True, True, True, False),
        ("18 bytes", True, True, True, True, True),
        ("67 bytes", True, True, True, True, True),
    ]
    for index, (line, dp, host, pre, clk, desc) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "USB 48M", "FS", "AUX GIF  D+")
        c.panel(16, 42, 140, 70, C.PANEL, C.CYAN if dp else C.STROKE)
        c.text("PA12", 60, 58, C.CYAN if dp else C.DIM, 1)
        c.text("D+ UP", 50, 84, C.TEXT if dp else C.DIM, 1)
        c.panel(168, 42, 140, 70, C.PANEL, C.GREEN if host else C.STROKE)
        c.text("HOST", 210, 58, C.GREEN if host else C.DIM, 1)
        c.text("SEES FS", 195, 84, C.TEXT if host else C.DIM, 1)
        c.panel(320, 42, 140, 70, C.PANEL, C.AMBER if pre else C.STROKE)
        c.text("USBPRE", 350, 58, C.AMBER if pre else C.DIM, 1)
        c.text("= 0", 365, 84, C.TEXT if pre else C.DIM, 1)
        c.panel(16, 126, 210, 36, C.PANEL, C.VIOLET if clk else C.STROKE)
        c.text("48 MHz USBCLK" if clk else "CLOCK PENDING", 28, 140, C.TEXT if clk else C.DIM, 1)
        c.panel(250, 126, 210, 36, C.PANEL2 if desc else C.PANEL, C.STROKE)
        label = "18 bytes THEN 67 bytes" if index >= 5 else ("18 bytes" if index == 4 else "DESC IDLE")
        c.text(label, 258, 140, C.TEXT if desc else C.DIM, 1)
        c.text(line, 16, 190, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 214, C.MUTED, 1)
        c.text("18 bytes THEN 67 bytes", 16, 240, C.GREEN, 1)
        c.text("48 MHz", 16, 262, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 16, 284, C.DIM, 1)
        g.add(c)
    return g
