def can_500k():
    """Eight 250 ns quanta make one 2 us bit at 500 kbit/s.

    The failed prescaler row and the crystal pins stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("TQ 1  250 ns", 1),
        ("TQ 2  250 ns", 2),
        ("TQ 3  250 ns", 3),
        ("TQ 6  SAMPLE 75%", 6),
        ("TQ 8  2 us", 8),
        ("500 kbit/s", 8),
    ]
    for index, (line, lit) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "CAN 500K", "36 MHz", "AUX GIF  8 QUANTA")
        c.text("prescaler 9", 16, 50, C.MUTED, 1)
        x0 = 16
        for q in range(8):
            on = q < lit
            col = C.AMBER if (q == 5 and lit >= 6) else (C.GREEN if on else C.STROKE)
            c.panel(x0 + q * 56, 70, 50, 50, C.PANEL, col)
            c.text(f"T{q+1}", x0 + q * 56 + 12, 90, C.TEXT if on else C.DIM, 1)
        c.panel(16, 140, 444, 36, C.PANEL2, C.STROKE)
        c.text("SAMPLE AT 75%  /  1.5 us" if lit >= 6 else "BUILDING BIT TIME", 28, 154, C.TEXT, 1)
        c.text(line, 16, 200, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 222, C.MUTED, 1)
        c.text("75% AT 1.5 us", 16, 246, C.GREEN, 1)
        c.text("250 ns TIMES 8 IS 2 us", 16, 268, C.CYAN, 1)
        c.text("PRINT THE MISS ON THE STATIC SVG", 16, 288, C.DIM, 1)
        g.add(c)
    return g
