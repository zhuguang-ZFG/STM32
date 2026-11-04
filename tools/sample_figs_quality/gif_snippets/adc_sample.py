def adc_sample():
    """One successful sample, then the MSB compare, at 12 MHz.

    Soft-source settling failures stay on the static SVG.
    """
    g = Gif(W, H, delay=10)
    notes = (
        "SAMPLE CAP CHARGING",
        "HOLD",
        "MSB COMPARE 2048",
        "KEEP / DROP BIT",
        "NEXT WEIGHT",
        "EOC  12 MHz",
    )
    progress = (1, 2, 3, 4, 5, 6)
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "ADC SAMPLE", "12 MHZ", "AUX GIF  ONE CONVERSION")
        c.panel(16, 42, 448, 28, C.PANEL, C.STROKE)
        c.text("ADCCLK 12 MHz  SMP then SAR", 28, 52, C.MUTED, 1)
        c.panel(16, 84, 448, 24, C.BG2, C.STROKE)
        fill = int(440 * min(1.0, progress[index] / 3))
        c.fill_rect(18, 86, max(2, fill), 20, C.CYAN if index < 2 else C.GREEN)
        c.text("SAMPLE" if index < 2 else "CONVERT", 20, 120, C.MUTED, 1)
        for i, (lab, w) in enumerate((("MSB", 2048), ("b10", 1024), ("b9", 512), ("LSB", 1))):
            x = 16 + i * 114
            active = index >= 2 and i <= max(0, index - 2)
            c.panel(x, 140, 104, 48, C.PANEL, C.AMBER if active else C.STROKE)
            c.text(lab, x + 12, 152, C.AMBER if active else C.DIM, 1)
            c.text(str(w), x + 12, 170, C.TEXT if active else C.DIM, 1)
        c.text(note, 16, 212, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 232, C.MUTED, 1)
        c.text("MSB FIRST THEN LOWER WEIGHTS", 16, 252, C.GREEN, 1)
        c.text("PRINT SETTLING MISS ON THE SVG", 16, 270, C.DIM, 1)
        g.add(c)
    return g
