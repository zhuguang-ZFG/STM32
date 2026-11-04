def dma_cndtr():
    """Eight half-words, CNDTR falls to 3: 5 samples, 10 bytes.

    Treating the remainder as bytes stays on the static SVG.
    """
    g = Gif(W, H, delay=10)
    counts = (8, 8, 6, 4, 3, 3)
    notes = (
        "8 HALF-WORDS",
        "CNDTR 8",
        "CNDTR 6",
        "CNDTR 4",
        "CNDTR 3",
        "5 samples  10 bytes",
    )
    for index, note in enumerate(notes):
        c = Canvas(W, H)
        chrome(c, "DMA CNDTR", "DMA1", "AUX GIF  HALF-WORDS")
        c.panel(16, 42, 448, 28, C.PANEL, C.STROKE)
        c.text("channel 4  HALF-WORD", 28, 52, C.MUTED, 1)
        for i in range(8):
            x = 20 + i * 56
            filled = i < (8 - counts[index])
            c.panel(x, 88, 48, 40, C.PANEL2 if filled else C.PANEL,
                    C.GREEN if filled else C.STROKE)
            c.text(str(i), x + 18, 104, C.DIM, 1)
        c.panel(16, 144, 200, 48, C.PANEL, C.AMBER)
        c.text(f"CNDTR {counts[index]}", 36, 162, C.AMBER, 1)
        done = 8 - counts[index]
        c.panel(232, 144, 232, 48, C.PANEL, C.CYAN)
        c.text(f"DONE {done}  BYTES {done*2}", 248, 162, C.CYAN, 1)
        c.text(note, 16, 216, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 236, C.MUTED, 1)
        c.text("5 samples IS 10 bytes", 16, 256, C.GREEN, 1)
        c.text("PRINT THE BYTE CUT ON THE SVG", 16, 274, C.DIM, 1)
        g.add(c)
    return g
