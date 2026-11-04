def clock_css():
    """HSE enters the PLL, SYSCLK sits at 72 MHz, then HSE vanishes and SYSCLK returns to HSI.

    The fetch failure stays on the static SVG.
    """
    g = Gif(W, H, delay=10)
    stages = [
        ("HSE 8 MHz INTO PLL", True, False, "8", "HSI"),
        ("PLL x9 LOCKS", True, True, "8", "PLL"),
        ("SYSCLK 72 MHz", True, True, "72", "PLL"),
        ("HSE GONE", False, True, "72", "PLL"),
        ("PLL OFF", False, False, "8", "HSI"),
        ("SYSCLK IS HSI 8 MHz", False, False, "8", "HSI"),
    ]
    for index, (line, hse_on, pll_on, mhz, src) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "CLOCK CSS", "HSE", "AUX GIF  STATIC SVG HAS THE FAILURE")
        c.panel(16, 42, 140, 70, C.PANEL, C.CYAN if hse_on else C.STROKE)
        c.text("HSE", 60, 58, C.CYAN if hse_on else C.DIM, 1)
        c.text("8 MHz" if hse_on else "OFF", 48, 84, C.TEXT if hse_on else C.DIM, 1)
        c.panel(170, 42, 140, 70, C.PANEL, C.GREEN if pll_on else C.STROKE)
        c.text("PLL", 220, 58, C.GREEN if pll_on else C.DIM, 1)
        c.text("x9" if pll_on else "OFF", 222, 84, C.TEXT if pll_on else C.DIM, 1)
        c.panel(324, 42, 140, 70, C.PANEL, C.AMBER)
        c.text("SYSCLK", 350, 58, C.AMBER, 1)
        c.text(f"{mhz} MHz", 348, 84, C.TEXT, 1)
        c.line(156, 76, 168, 76, C.STROKE, 2)
        c.line(310, 76, 322, 76, C.STROKE, 2)
        c.panel(16, 126, 448, 36, C.PANEL2 if src == "PLL" else C.PANEL, C.STROKE)
        c.text(f"SOURCE  {src}   SWS={'10' if src == 'PLL' else '00'}", 28, 140, C.TEXT, 1)
        c.text(line, 16, 184, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 208, C.MUTED, 1)
        c.text("CSS RETURNS SYSCLK TO HSI", 16, 232, C.GREEN, 1)
        c.text("PRINT THE FETCH FAILURE ON THE SVG", 16, 252, C.DIM, 1)
        g.add(c)
    return g
