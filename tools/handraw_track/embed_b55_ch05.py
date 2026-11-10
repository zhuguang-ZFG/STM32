# -*- coding: utf-8 -*-
"""B55: embed the ch05 timer-class ladder plate into zh/en docs."""
from embed import embed_after_text

PNG = "ch05-timer-ladder.png"

ZH_ANCHOR = (
    "定时器说穿了就是一个跟着时钟往上数的计数器，再配几个比较器。区别在于配件多少："
    "基本定时器只会数数，适合当闹钟；通用定时器多了 4 个通道，能出 PWM、能测脉宽；"
    "高级定时器再加上互补输出和死区，专门给电机驱动用。SysTick 是内核自带的那一个，"
    "HAL 和 RTOS 都拿它当心跳。"
)
ZH_ALT = "Handraw：定时器等级阶梯（原理示意）"
ZH_CAPTION = (
    "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：自下而上三级台阶——基本只计数，"
    "通用加 4 通道（PWM/捕获/编码器），高级再加互补输出、死区与刹车，MOE 标在最高一级；"
    "SysTick 与看门狗在旁支，C8 的通用定时器带 16 位标签；证明什么：每一级就是下一级加配件，"
    "按需要的功能选最低的一级就够；不能证明什么：不画寄存器偏移与实测波形，"
    "实例与位宽以正文分类表为准。出处：[RM0008 Rev 21 第 15 章](#source-rm0008-tim)。"
)

EN_ANCHOR = (
    "A timer is a counter that ticks along with a clock, plus a few comparators. "
    "The classes differ in how many extras they carry. A basic timer only counts, "
    "which makes it a good alarm clock. A general-purpose timer adds 4 channels, "
    "so it can drive PWM and measure pulses. An advanced timer adds complementary "
    "outputs and dead time for motor drives. SysTick is the one built into the core, "
    "and HAL and RTOS both use it as their heartbeat."
)
EN_ALT = "Handraw: the timer class ladder (原理示意)"
EN_CAPTION = (
    "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: three "
    "ascending rungs — basic counts only, general-purpose adds 4 channels "
    "(PWM / capture / encoder), advanced adds complementary outputs, dead time and "
    "break, with MOE on the top rung; SysTick and the watchdog sit on a side branch, "
    "and the C8's general-purpose timers carry a 16-bit tag; Proves each class is the "
    "one below plus extras, so pick the lowest rung that has the feature you need; "
    "Cannot show register offsets or measured waveforms, and the class table stays "
    "the lookup; See [RM0008 Rev 21 chapter 15](#source-rm0008-tim)."
)

if __name__ == "__main__":
    ok_zh = embed_after_text("docs/05-定时器与PWM.md", ZH_ANCHOR, PNG,
                             ZH_ALT, ZH_CAPTION)
    ok_en = embed_after_text("docs/en/05-timer-pwm.md", EN_ANCHOR, PNG,
                             EN_ALT, EN_CAPTION)
    if not (ok_zh and ok_en):
        raise SystemExit("embed failed")
