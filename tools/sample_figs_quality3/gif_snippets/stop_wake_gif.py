def stop_wake_gif():
    """Wake from Stop, move the clock from 8 MHz back to 72 MHz, then mark 115200.

    The failed baud and the other Stop cell stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("STOP", True, False, False, False, False),
        ("WAKE ON HSI", True, True, False, False, False),
        ("8 MHz", True, True, True, False, False),
        ("PLL ON", True, True, True, True, False),
        ("72 MHz", True, True, True, True, True),
        ("115200", True, True, True, True, True),
    ]
    for index, (line, stop, wake, hsi, pll, uart) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "STOP WAKE", "HSI", "AUX GIF  115200")
        c.panel(16, 42, 140, 70, C.PANEL, C.CYAN if stop else C.STROKE)
        c.text("STOP", 55, 58, C.CYAN if stop else C.DIM, 1)
        c.text("LP REG", 45, 84, C.TEXT if stop else C.DIM, 1)
        c.panel(168, 42, 140, 70, C.PANEL, C.GREEN if wake else C.STROKE)
        c.text("WAKE", 210, 58, C.GREEN if wake else C.DIM, 1)
        c.text("PA0/RTC", 190, 84, C.TEXT if wake else C.DIM, 1)
        c.panel(320, 42, 140, 70, C.PANEL, C.AMBER if hsi else C.STROKE)
        c.text("HSI", 365, 58, C.AMBER if hsi else C.DIM, 1)
        c.text("8 MHz", 350, 84, C.TEXT if hsi else C.DIM, 1)
        c.panel(16, 126, 210, 36, C.PANEL, C.VIOLET if pll else C.STROKE)
        c.text("PLL 72 MHz" if pll else "PLL OFF", 28, 140, C.TEXT if pll else C.DIM, 1)
        c.panel(250, 126, 210, 36, C.PANEL2 if uart else C.PANEL, C.STROKE)
        c.text("UART 115200" if uart else "UART HOLD", 262, 140, C.TEXT if uart else C.DIM, 1)
        c.text("0x271", 16, 180, C.MUTED, 1)
        c.text(line, 16, 206, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 228, C.MUTED, 1)
        c.text("8 MHz THEN 72 MHz", 16, 252, C.GREEN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 16, 274, C.DIM, 1)
        g.add(c)
    return g
