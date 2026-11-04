def nvic_preempt():
    """TIM2 is running. EXTI0 at a higher preemption interrupts it, then returns.

    The equal-preemption failure stays on the static SVG. This GIF does not draw it.
    """
    g = Gif(W, H, delay=12)
    stages = [
        ("TIM2 RUN  PREEMPT 2", True, False, False, False),
        ("EXTI0 ARRIVES  PREEMPT 1", True, True, False, False),
        ("STACK EIGHT REGS", True, True, True, False),
        ("EXTI0 ISR RUNS", True, True, True, True),
        ("UNSTACK AND RETURN", True, False, False, False),
        ("TIM2 RESUMES", True, False, False, False),
    ]
    for index, (line, tim_on, exti_on, stack_on, isr_on) in enumerate(stages):
        c = Canvas(W, H)
        chrome(c, "NVIC PREEMPT", "GROUP4", "AUX GIF  STATIC SVG HAS THE FAILURE")
        c.panel(16, 42, 210, 70, C.PANEL, C.AMBER if tim_on else C.STROKE)
        c.text("TIM2", 90, 58, C.AMBER if tim_on else C.DIM, 1)
        c.text("PREEMPT 2", 55, 84, C.TEXT if tim_on else C.DIM, 1)
        c.panel(250, 42, 210, 70, C.PANEL, C.GREEN if exti_on else C.STROKE)
        c.text("EXTI0", 320, 58, C.GREEN if exti_on else C.DIM, 1)
        c.text("PREEMPT 1", 295, 84, C.TEXT if exti_on else C.DIM, 1)
        c.line(226, 76, 248, 76, C.STROKE, 2)
        c.panel(16, 126, 444, 36, C.PANEL2 if stack_on else C.PANEL, C.STROKE)
        c.text("STACK  R0-R3 R12 LR PC xPSR" if stack_on else "STACK  IDLE", 28, 140, C.TEXT if stack_on else C.DIM, 1)
        c.panel(16, 172, 444, 28, C.PANEL, C.VIOLET if isr_on else C.STROKE)
        c.text("EXTI0 ISR  ACTIVE" if isr_on else "EXTI0 ISR  WAIT", 28, 184, C.TEXT if isr_on else C.DIM, 1)
        c.text(line, 16, 220, C.TEXT, 1)
        c.text(f"FRAME {index + 1} OF 6", 16, 242, C.MUTED, 1)
        c.text("HIGHER PREEMPTION INTERRUPTS TIM2", 16, 262, C.GREEN, 1)
        c.text("PRINT THE FAILURE ON THE STATIC SVG", 16, 282, C.DIM, 1)
        g.add(c)
    return g
