def pwm_1khz():
    """CNT walks to ARR and the level flips at CCR=500.

    The slow path stays on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("CNT 0  HIGH", 0, True),
        ("CNT 250  HIGH", 250, True),
        ("CCR=500  EDGE", 500, True),
        ("CNT 750  LOW", 750, False),
        ("CNT 999  LOW", 999, False),
        ("1000 Hz  500 us HIGH", 0, True),
    ]
    for index, (note, cnt, high) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "PWM 1 KHZ", "TIM3", "AUX GIF  1000 Hz")
        c.panel(16, 42, 448, 28, C.PANEL, C.STROKE)
        c.text("PSC=71 ARR=999 CCR=500", 28, 52, C.MUTED, 1)
        c.panel(16, 80, 140, 60, C.PANEL, C.CYAN)
        c.text("CNT", 60, 96, C.CYAN, 1)
        c.text(str(cnt), 55, 122, C.TEXT, 1)
        c.panel(170, 80, 140, 60, C.PANEL, C.AMBER)
        c.text("CCR", 215, 96, C.AMBER, 1)
        c.text("500", 215, 122, C.TEXT, 1)
        c.panel(324, 80, 140, 60, C.PANEL, C.GREEN if high else C.STROKE)
        c.text("OUT", 370, 96, C.GREEN if high else C.DIM, 1)
        c.text("HIGH" if high else "LOW", 360, 122, C.TEXT if high else C.DIM, 1)
        # crude duty bar
        c.hline(24, 160, 220 if high else 40, C.GREEN if high else C.AMBER, 2)
        c.text(note, 16, 190, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 212, C.MUTED, 1)
        c.text("1000 Hz FROM A 72 MHz CLOCK", 16, 236, C.CYAN, 1)
        c.text("500 us HIGH THEN LOW", 16, 256, C.GREEN, 1)
        c.text("PRINT THE SLOW PATH ON THE STATIC SVG", 16, 278, C.DIM, 1)
        g.add(c)
    return g
