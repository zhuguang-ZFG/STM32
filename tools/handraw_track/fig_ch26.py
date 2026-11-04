# -*- coding: utf-8 -*-
"""ch26 knowledge-track figures (facts from docs/26, SPL V3.5.0 / STSW-STM32054)."""
from hd import *


def four_layers():
    f = Fig("ch26-four-layers", "SPL 的四层 / four layers, one boundary")
    rows = [
        ("stm32f10x.h", "设备、寄存器地址和位定义", GREEN_D),
        ("stm32f10x_gpio.h", "配置结构体、常量与函数声明", BLUE_D),
        ("stm32f10x_gpio.c", "把结构体字段写进寄存器", AMBER_STROKE),
        ("你的工程", "时钟 · 引脚 · 调用顺序 · 中断 · 超时 · 业务", RED),
    ]
    y0 = 138
    for i, (name, note, c) in enumerate(rows):
        y = y0 + i * 106
        f.rect(150, y, 700, 78, color=c, fill=WHITE)
        f.text(180, y + 34, name, size=27, color=c, weight="bold")
        f.text(180, y + 64, note, size=22, color=INK)
        if i < 3:
            f.arrow(500, y + 78, 500, y + 104, color=MUTED, sw=2.4, head=9)
    f.htext(W / 2, 618, "背函数名没有价值，看清每一层管什么才有", size=27,
            color=INK, anchor="middle", weight="bold", hl=True)
    f.text(W / 2, 662, "第 4 层缺哪样，前三层都救不回来", size=23, color=MUTED,
           anchor="middle")
    return f


def defines():
    f = Fig("ch26-defines", "两个宏 + assert_param / defines and assert")
    y0 = 140
    f.rect(90, y0, 480, 210, color=GREEN, fill=WHITE)
    f.htext(330, y0 + 44, "STM32F10X_MD", size=27, color=GREEN_D,
            anchor="middle", weight="bold")
    f.multi(330, y0 + 86, ["按确切料号选密度宏", "C8/B 是中容量 MD", "配错 = 中断号与启动文件", "跟芯片不匹配"],
            size=22, color=INK, lh=33, anchor="middle")
    f.rect(582, y0, 480, 210, color=BLUE, fill=WHITE)
    f.htext(822, y0 + 44, "USE_STDPERIPH_DRIVER", size=25, color=BLUE_D,
            anchor="middle", weight="bold")
    f.multi(822, y0 + 86, ["让 stm32f10x.h 引入", "stm32f10x_conf.h", "漏了 = GPIO_InitTypeDef", "等声明不可见"],
            size=22, color=INK, lh=33, anchor="middle")
    f.rect(90, 396, 972, 148, color=AMBER_STROKE, fill=WHITE)
    f.htext(W / 2, 438, "assert_param() 不是产品故障处理", size=26, color=AMBER_STROKE,
            anchor="middle", weight="bold", hl=True)
    f.multi(W / 2, 480, ["开发期 USE_FULL_ASSERT → assert_failed()；发布版关闭后通常不执行",
                         "通信超时、传感器离线、DMA 错误、Flash 写失败要自己的运行时处理"],
            size=22, color=INK, lh=35, anchor="middle")
    f.text(W / 2, 600, "头文件路径、实际编译的 src/*.c、启动文件、链接脚本、晶振 — 一个都不能少",
           size=23, color=MUTED, anchor="middle")
    return f


def init_steps():
    f = Fig("ch26-init-steps", "时钟 → 默认值 → 覆盖 → 使能 / init order")
    steps = [
        ("1 开时钟", "RCC_APB2PeriphClockCmd(..., ENABLE)", "没有时钟，寄存器写入不按预期生效", GREEN_D),
        ("2 填默认值", "GPIO_StructInit(&io)", "局部变量未赋值字段是随机值", BLUE_D),
        ("3 覆盖字段", "GPIO_Pin / Mode / Speed", "每个字段和接线、时钟、协议对上", AMBER_STROKE),
        ("4 显式使能", "USART_Cmd() / SPI_Cmd() / TIM_Cmd()", "配置完成之后才调用", RED),
    ]
    y0 = 138
    for i, (t, code, note, c) in enumerate(steps):
        y = y0 + i * 108
        f.rect(110, y, 930, 84, color=c, fill=WHITE)
        f.text(140, y + 36, t, size=26, color=c, weight="bold")
        f.text(350, y + 36, code, size=23, color=INK)
        f.text(140, y + 68, note, size=21, color=MUTED)
        if i < 3:
            f.line(575, y + 84, 575, y + 106, color=MUTED, sw=2.2, amp=1.0)
    f.htext(W / 2, 618, "函数名可能不同 — 回到头文件原型和 RM0008，别凭印象补 *_Cmd",
            size=24, color=INK, anchor="middle", weight="bold", hl=True)
    return f


def spl_hal():
    f = Fig("ch26-spl-hal", "同一硬件，两条库路 / HAL vs SPL V3.5.0")
    rows = [
        ("GPIO 时钟", "__HAL_RCC_GPIOA_CLK_ENABLE()", "RCC_APB2PeriphClockCmd(...)", "RCC_APB2ENR", GREEN_D),
        ("GPIO 配置", "HAL_GPIO_Init()", "GPIO_Init()", "GPIOx_CRL/CRH", GREEN_D),
        ("GPIO 输出", "HAL_GPIO_WritePin()", "GPIO_SetBits()/ResetBits()", "GPIOx_BSRR/BRR", BLUE_D),
        ("USART 收发", "HAL_UART_Transmit(...,t)", "USART_SendData()+轮询", "USARTx_SR/DR", BLUE_D),
        ("DMA 剩余", "__HAL_DMA_GET_COUNTER()", "DMA_GetCurrDataCounter()", "DMA_CNDTR", AMBER_STROKE),
    ]
    y0 = 134
    f.text(155, y0 - 14, "目标", size=20, color=MUTED, anchor="middle")
    f.text(440, y0 - 14, "HAL 入口", size=20, color=MUTED, anchor="middle")
    f.text(790, y0 - 14, "SPL V3.5.0 入口", size=20, color=MUTED, anchor="middle")
    f.text(1032, y0 - 14, "硬件边界", size=20, color=MUTED, anchor="middle")
    for i, (t, h, s, hw, c) in enumerate(rows):
        y = y0 + i * 80
        f.rect(66, y, 178, 58, color=c, fill=WHITE)
        f.text(155, y + 36, t, size=21, color=c, anchor="middle", weight="bold")
        f.text(440, y + 36, h, size=17, color=INK, anchor="middle")
        f.text(790, y + 36, s, size=17, color=INK, anchor="middle")
        f.rect(944, y, 178, 58, color=MUTED, fill=WHITE)
        f.text(1033, y + 36, hw, size=17, color=INK, anchor="middle")
    f.htext(W / 2, 616, "只换函数名、保留旧状态机 = “能跑一会儿”的工程", size=26,
            color=RED, anchor="middle", weight="bold", hl=True)
    f.text(W / 2, 660, "新项目优先 HAL/LL；只有维护锁定版本的 F1 旧工程才继续 SPL",
           size=24, color=INK, anchor="middle")
    f.text(W / 2, 700, "同一外设只允许一个驱动体系负责", size=22, color=MUTED,
           anchor="middle")
    return f


def timeout_poll():
    f = Fig("ch26-timeout-poll", "轮询自己带超时 / poll with a limit")
    f.rect(110, 132, 560, 250, color=BLUE, fill=WHITE)
    f.multi(140, 176, ["while (USART_GetFlagStatus(", "  USART1, USART_FLAG_TXE",
                       "  ) == RESET) {", "  if (spin_limit-- == 0U)", "    return -1;",
                       "}", "USART_SendData(USART1, byte);"],
            size=22, color=INK, lh=34)
    f.htext(880, 176, "SPL 不会替你超时", size=27, color=RED, anchor="middle",
            weight="bold", hl=True)
    f.multi(880, 222, ["USART_SendData() 只写 DR", "没有 HAL 那种", "timeout 参数", "", "等 TXE 的循环", "自己写边界"],
            size=23, color=INK, lh=36, anchor="middle")
    f.panel(110, 448, 952, 106, AMBER_FILL)
    f.rect(110, 448, 952, 106, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 490, "spin_limit 只是教学上的有界等待", size=26, color=INK,
           anchor="middle", weight="bold")
    f.text(W / 2, 528, "产品换成可靠时基的截止时间，并写清超时后的恢复动作", size=23,
           color=INK, anchor="middle")
    f.text(W / 2, 610, "死等一个永远不来的标志 = 看门狗复位或任务卡死", size=24,
           color=RED, anchor="middle", weight="bold")
    return f


FIGS = {
    "ch26-four-layers": four_layers,
    "ch26-defines": defines,
    "ch26-init-steps": init_steps,
    "ch26-spl-hal": spl_hal,
    "ch26-timeout-poll": timeout_poll,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
