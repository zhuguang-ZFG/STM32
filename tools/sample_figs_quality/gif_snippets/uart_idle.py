def uart_idle():
    """After one frame, RX stays high for one frame time, then IDLE is marked.

    Framing-error samples stay on the static SVG. This GIF does not replay 0xA5 bit by bit.
    """
    g = Gif(W, H, delay=10)
    notes = (
        "FRAME END  STOP HIGH",
        "RX STAYS HIGH",
        "RX STAYS HIGH",
        "RX STAYS HIGH",
        "ONE FRAME OF IDLE",
        "IDLE  86.8 us",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "UART IDLE", "8N1", "AUX GIF  86.8 us IS ONE FRAME")
        c.panel(16, 42, 448, 28, C.PANEL, C.STROKE)
        c.text("RX AFTER ONE FRAME @ 115200", 28, 52, C.MUTED, 1)
        c.hline(24, 120, 432, C.GREEN, 2)
        for t in range(11):
            x = 24 + t * 39
            c.vline(x, 112, 16, C.GRID, 1)
        mark = 24 + int(432 * index / 5)
        c.vline(mark, 96, 48, C.AMBER, 2)
        c.circle(mark, 120, 3, C.AMBER, True)
        c.panel(16, 150, 200, 40, C.PANEL, C.CYAN)
        c.text("BIT  8.68 us", 28, 166, C.CYAN, 1)
        c.panel(232, 150, 232, 40, C.PANEL, C.AMBER)
        c.text("FRAME  86.8 us", 248, 166, C.AMBER, 1)
        c.text(note, 16, 212, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 232, C.MUTED, 1)
        c.text("IDLE IS THE LINE HIGH FOR 86.8 us", 16, 252, C.CYAN, 1)
        c.text("NOT A PROTOCOL LENGTH FIELD", 16, 270, C.AMBER, 1)
        g.add(c)
    return g
