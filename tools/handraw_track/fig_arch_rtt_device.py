# -*- coding: utf-8 -*-
"""RT-Thread device framework plate (ch26).

Pinned to the chapter: one RT_Object_Class_Device container, name-based linear
find; RT_USING_DEVICE_OPS is off in the default F407 BSP, so function pointers
are inline unless the macro is enabled; open does init then open and only then
increments ref_count; read/write return signed rt_ssize_t, negative = error.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hd import *  # noqa: E402,F401,F403


def _chip(f, x, y, w, h, text, color, size=16):
    f.rect(x, y, w, h, color=color, fill=WHITE, sw=2.0)
    f.text(x + 10, y + h / 2 + 5, text, size=size, color=INK)


def rtt_device():
    f = Fig("arch-rtt-device-ops",
            "RT-Thread 设备框架 / one container, two dispatch modes")

    # object container
    lx, ly, lw, lh = 48, 120, 520, 246
    f.rect(lx, ly, lw, lh, color=GREEN_D, fill=PAPER, sw=2.8)
    f.htext(lx + 16, ly + 34, "① 对象容器：按名字找", size=23, color=GREEN_D,
            weight="bold")
    f.text(lx + 18, ly + 62, "rt_device_find(\"uart1\")", size=17, color=BLUE_D)
    f.arrow(lx + 18, ly + 80, lx + 18, ly + 114, color=BLUE, sw=2.2, bend=0.0)
    f.rect(lx + 18, ly + 116, 120, 46, color=BLUE_D, fill=WHITE, sw=2.0)
    f.text(lx + 28, ly + 146, "rt_device_t", size=16, color=BLUE_D)
    # container nodes
    nx = lx + 180
    for i, name in enumerate(("uart1", "i2c1", "spi0")):
        c = RED if name == "uart1" else MUTED
        f.rect(nx, ly + 112, 86, 54, color=c, fill=WHITE, sw=2.0)
        f.text(nx + 12, ly + 145, name, size=16, color=c, weight="bold")
        if i < 2:
            f.arrow(nx + 88, ly + 139, nx + 108, ly + 139, color=INK,
                    sw=1.8, bend=0.0)
        nx += 108
    f.text(lx + 18, ly + 198,
           "所有设备进同一个容器；Char/Block/… 只是分类标签，查找不按类。", size=15,
           color=MUTED)
    f.text(lx + 18, ly + 222,
           "find 在链表上线性比对名字；名字是 BSP 与应用的契约。", size=15,
           color=MUTED)

    # device object + dispatch fork
    rx, ry, rw, rh = 588, 120, 516, 246
    f.rect(rx, ry, rw, rh, color=BLUE_D, fill=WHITE, sw=2.8)
    f.htext(rx + 16, ry + 34, "② 设备对象：两种分发", size=23, color=BLUE_D,
            weight="bold")
    f.rect(rx + 18, ry + 52, 210, 58, color=BLUE_D, fill=PAPER, sw=2.0)
    f.text(rx + 30, ry + 76, "rt_device", size=17, color=BLUE_D, weight="bold")
    f.text(rx + 30, ry + 98, "type / flag / ref_count", size=14, color=MUTED)
    f.line(rx + 228, ry + 81, rx + 258, ry + 81, color=INK, sw=2.0, amp=0.8)
    f.text(rx + 268, ry + 86, "分发", size=15, color=MUTED)

    f.text(rx + 18, ry + 132, "默认（宏关）：函数指针内联", size=16,
           color=RED, weight="bold")
    _chip(f, rx + 18, ry + 146, 168, 34, "init/open/close", AMBER_STROKE, size=12)
    _chip(f, rx + 194, ry + 146, 132, 34, "read/write", AMBER_STROKE, size=13)
    _chip(f, rx + 334, ry + 146, 132, 34, "control", AMBER_STROKE, size=13)

    f.text(rx + 18, ry + 198, "开 RT_USING_DEVICE_OPS：共享 ops 表", size=16,
           color=GREEN_D, weight="bold")
    f.rect(rx + 18, ry + 212, 200, 24, color=GREEN_D, fill=PAPER, sw=1.8)
    f.text(rx + 28, ry + 229, "dev->ops->…", size=14, color=GREEN_D)
    f.text(rx + 232, ry + 230, "多个设备共享一张表，省 RAM", size=14, color=MUTED)

    # lifecycle
    qx, qy, qw, qh = 48, 398, 1056, 186
    f.rect(qx, qy, qw, qh, color=AMBER_STROKE, fill=PAPER, sw=2.8)
    f.htext(qx + 16, qy + 34, "③ 生命周期：open 的顺序不能反", size=22,
            color=AMBER_STROKE, weight="bold")
    steps = [
        ("register", "挂进容器", GREEN_D),
        ("find", "线性找名", BLUE_D),
        ("open", "未激活 init；同 flag 跳过", RED),
        ("read/write", "signed；0+errno", BLUE_D),
    ]
    x = qx + 16
    for i, (name, sub, c) in enumerate(steps):
        f.rect(x, qy + 54, 230, 62, color=c, fill=WHITE, sw=2.0)
        f.text(x + 10, qy + 78, name, size=16, color=c, weight="bold")
        f.text(x + 10, qy + 100, sub, size=13, color=MUTED)
        if i < 3:
            f.arrow(x + 232, qy + 84, x + 250, qy + 84, color=INK, sw=1.8,
                    bend=0.0)
        x += 250
    f.text(qx + 16, qy + 140,
           "RT_EOK 或 -RT_ENOSYS 才 ref_count++；同 flag 再开跳过 open。", size=14,
           color=RED)
    f.text(qx + 16, qy + 164,
           "read/write 的 0 不一定是成功：框架错误路径返回 0 并设 errno。", size=14,
           color=MUTED)

    # closing
    f.htext(576, 682, "先看 RT_USING_DEVICE_OPS：宏关时 dev->ops 不是无条件成员。",
            size=21, color=AMBER_STROKE, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    return f


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[2] / "assets" / "illustrations" / "handraw"
    save(rtt_device(), str(out / "arch-device-ops.svg"))
    print("wrote arch-device-ops.svg")
