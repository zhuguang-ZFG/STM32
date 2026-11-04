def rtos_tick():
    """A 1 ms tick keeps priority 2 on the CPU and priority 1 waiting.

    The assert stop and a SysTick clash stay on the static SVG.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("TICK 1 ms", True, False, False, False),
        ("TICK 1 ms", True, True, False, False),
        ("priority 2 RUNS", True, True, True, False),
        ("priority 1 WAITS", True, True, True, True),
        ("128 words", True, True, True, True),
        ("512 bytes", True, True, True, True),
    ]
    for index, (line, tick, ready, p2, p1) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "RTOS TICK", "1 ms", "AUX GIF  WORDS")
        c.panel(16, 42, 140, 70, C.PANEL, C.CYAN if tick else C.STROKE)
        c.text("1000 Hz", 45, 58, C.CYAN if tick else C.DIM, 1)
        c.text("1 ms", 60, 84, C.TEXT if tick else C.DIM, 1)
        c.panel(168, 42, 140, 70, C.PANEL, C.AMBER if p2 else C.STROKE)
        c.text("PRIO 2", 200, 58, C.AMBER if p2 else C.DIM, 1)
        c.text("RUNS" if p2 else "IDLE", 210, 84, C.TEXT if p2 else C.DIM, 1)
        c.panel(320, 42, 140, 70, C.PANEL, C.VIOLET if p1 else C.STROKE)
        c.text("PRIO 1", 352, 58, C.VIOLET if p1 else C.DIM, 1)
        c.text("WAITS" if p1 else "IDLE", 358, 84, C.TEXT if p1 else C.DIM, 1)
        c.panel(16, 126, 444, 36, C.PANEL2 if ready else C.PANEL, C.STROKE)
        stack = "128 words = 512 bytes" if index >= 5 else ("128 words" if index == 4 else "STACK LED TASK")
        c.text(stack if index >= 4 else ("READY LIST" if ready else "SCHEDULER"), 28, 140, C.TEXT, 1)
        c.text(line, 16, 190, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 214, C.MUTED, 1)
        c.text("priority 2 BEFORE priority 1", 16, 240, C.GREEN, 1)
        c.text("128 words = 512 bytes", 16, 262, C.CYAN, 1)
        c.text("PRINT THE ASSERT ON THE STATIC SVG", 16, 284, C.DIM, 1)
        g.add(c)
    return g
