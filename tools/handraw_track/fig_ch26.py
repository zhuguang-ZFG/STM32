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
            size=18, color=INK, lh=30)
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


def irq_no_callback():
    f = Fig("ch26-irq-no-callback", "SPL 中断：没有回调替你分发 / no callback layer")
    f.text(96, 128, "学习目标原话：SPL 中断没有 HAL 回调，必须在 IRQHandler 中检查并清除标志",
           size=20, color=MUTED)
    # 左：HAL 车道
    f.rect(90, 156, 460, 330, color=BLUE, fill=WHITE)
    f.text(110, 190, "HAL：库替你分发", size=23, color=BLUE_D, weight="bold")
    f.rect(130, 210, 380, 46, color=BLUE_D, fill=WHITE, sw=2.0)
    f.text(320, 240, "EXTI0_IRQHandler", size=20, color=INK, anchor="middle")
    f.arrow(320, 256, 320, 276, color=MUTED, sw=2.2, head=8)
    f.rect(130, 280, 380, 46, color=BLUE_D, fill=WHITE, sw=2.0)
    f.text(320, 310, "HAL_GPIO_EXTI_Callback()", size=19, color=INK,
           anchor="middle")
    f.arrow(320, 326, 320, 346, color=MUTED, sw=2.2, head=8)
    f.rect(130, 350, 380, 46, color=BLUE_D, fill=WHITE, sw=2.0)
    f.text(320, 380, "你的代码在回调里跑", size=20, color=INK, anchor="middle")
    f.text(110, 430, "事件由库一路转发到回调", size=18, color=MUTED)
    # 右：SPL 车道
    f.rect(610, 156, 460, 330, color=GREEN, fill=WHITE)
    f.text(630, 190, "SPL：没有回调替你分发", size=23, color=GREEN_D,
           weight="bold")
    f.rect(650, 210, 380, 46, color=GREEN_D, fill=WHITE, sw=2.0)
    f.text(840, 240, "EXTI0_IRQHandler（stm32f10x_it.c）", size=18, color=INK,
           anchor="middle")
    f.arrow(840, 256, 840, 276, color=MUTED, sw=2.2, head=8)
    f.text(858, 272, "① 查真实来源", size=18, color=RED, weight="bold")
    f.rect(650, 280, 380, 46, color=GREEN_D, fill=WHITE, sw=2.0)
    f.text(840, 310, "EXTI_GetITStatus(EXTI_Line0)", size=19, color=INK,
           anchor="middle")
    f.arrow(840, 326, 840, 346, color=MUTED, sw=2.2, head=8)
    f.text(858, 342, "② 清挂起", size=18, color=RED, weight="bold")
    f.rect(650, 350, 380, 46, color=GREEN_D, fill=WHITE, sw=2.0)
    f.text(840, 380, "EXTI_ClearITPendingBit(EXTI_Line0)", size=18, color=INK,
           anchor="middle")
    f.arrow(840, 396, 840, 416, color=MUTED, sw=2.2, head=8)
    f.text(858, 412, "③ 只交接事件", size=18, color=RED, weight="bold")
    f.rect(650, 420, 380, 46, color=GREEN_D, fill=WHITE, sw=2.0)
    f.text(840, 450, "g_key_event = 1U（事件给主循环）", size=19, color=INK,
           anchor="middle")
    # 下：对账清单
    f.text(90, 522, "必须逐项对账：", size=22, color=INK, weight="bold")
    checks = [
        (90, 538, AMBER_STROKE, "EXTI_Init 只配线；端口映射要", "GPIO_EXTILineConfig()"),
        (596, 538, BLUE_D, "NVIC 分组与通道", "NVIC_PriorityGroupConfig() + NVIC_Init()"),
        (90, 606, RED, "向量可能共用", "IRQHandler 必须查真实来源"),
        (596, 606, MUTED, "清除规则按外设不同", "ORE：读 SR 再读 DR"),
    ]
    for x, y, c, t, d in checks:
        f.rect(x, y, 486, 58, color=c, fill=WHITE, sw=2.2)
        f.text(x + 18, y + 24, t, size=17, color=c, weight="bold")
        f.text(x + 18, y + 46, d, size=17, color=INK)
    f.htext(W / 2, 700, "ISR 只交接事件：不做阻塞发送、完整 I2C 事务、Flash 擦除或长延时",
            size=22, color=INK, anchor="middle", weight="bold", hl=True)
    return f



def call_chains():
    f = Fig("ch26-call-chains",
            "SPL 调用链：骨架一样，坑各不同 / one skeleton, different traps")
    steps = ["RCC 开时钟", "GPIO 配脚", "XXX_Init", "XXX_Cmd", "标志/事件对账"]
    for i, s in enumerate(steps):
        x = 84 + i * 200
        f.rect(x, 128, 172, 64, color=BLUE_D, fill=WHITE, sw=2.6)
        f.text(x + 86, 168, s, size=19, color=BLUE_D, anchor="middle", weight="bold")
        if i:
            f.arrow(x - 26, 160, x - 2, 160, color=BLUE, bend=0.0, head=9)
    f.text(576, 228, "每个外设都是这条骨架的变体；真正出事的是右边那一格",
           size=19, color=MUTED, anchor="middle")
    traps = [("GPIO", "复用重映射还要开 AFIO 时钟"),
             ("EXTI", "挂起位不清会反复进中断"),
             ("TIM PWM", "TIM1/TIM8 还要 CtrlPWMOutputs"),
             ("USART", "TXE 与 TC 不是同一个完成边界"),
             ("I2C", "超时和总线恢复要自己写"),
             ("SPI", "发一字节收一字节，收尾等 BSY"),
             ("ADC", "F1 先复位校准、再校准，再转换"),
             ("DMA", "请求映射固定，计数单位看宽度"),
             ("Flash", "Unlock…Lock，页对齐、半字对齐"),
             ("CAN", "单节点正常模式无人 ACK")]
    for i, (p, t) in enumerate(traps):
        col, row = i % 2, i // 2
        x, y = 84 + col * 504, 256 + row * 96
        f.rect(x, y, 480, 80, color=GREEN_D if col == 0 else RED, fill=WHITE,
               sw=2.2, double=False)
        f.text(x + 18, y + 49, p, size=20, color=GREEN_D if col == 0 else RED,
               weight="bold")
        f.text(x + 128, y + 49, t, size=18, color=INK)
    f.text(576, 754, "这张图只给顺序；时钟、GPIO、NVIC、各外设细节回到对应章节",
           size=18, color=MUTED, anchor="middle")
    return f


def migrate_steps():
    f = Fig("ch26-migrate-steps",
            "旧工程：先冻结，再一次迁一个外设 / freeze, then migrate")
    steps = [("1 冻结基线", "料号·SPL版本·密度宏·编译器·晶振"),
             ("2 画所有权表", "SPL / 裸寄存器 / 第三方，各管哪个外设"),
             ("3 一次迁一个", "接线、时钟、输入和仪器条件都不变"),
             ("4 对比可见结果", "电平·PWM 周期·UART 帧·Flash 校验"),
             ("5 清掉旧所有权", "删旧初始化和 IRQ，不能双初始化")]
    for i, (t, s) in enumerate(steps):
        x, y = 84 + i * 150, 128 + i * 82
        c = RED if i == 4 else BLUE_D
        f.rect(x, y, 384, 70, color=c, fill=WHITE, sw=2.6)
        f.text(x + 16, y + 30, t, size=20, color=c, weight="bold")
        f.text(x + 16, y + 58, s, size=16, color=INK)
        if i:
            f.arrow(x - 110, y - 12, x - 8, y + 26, color=MUTED, bend=-0.25, head=9)
    f.text(84, 548, "迁移不是全局替换函数名：每一步都要能回到上一步的可见结果",
           size=19, color=MUTED)
    f.rect(84, 574, 470, 180, color=GREEN_D, fill=WHITE, sw=2.6)
    f.text(104, 610, "保留 SPL", size=22, color=GREEN_D, weight="bold")
    f.multi(104, 648, ["已量产 F1，测试都围绕 V3.5.0",
                       "改动小，全量回归成本高",
                       "团队能锁定编译器和库包"],
            size=18, color=INK, lh=32)
    f.rect(578, 574, 490, 180, color=BLUE_D, fill=WHITE, sw=2.6)
    f.text(598, 610, "迁到 HAL / LL", size=22, color=BLUE_D, weight="bold")
    f.multi(598, 648, ["新系列没有对应 SPL",
                       "要 CubeMX、中间件或跨系列 BSP",
                       "SPL 副本来源不明，版本已说不清"],
            size=18, color=INK, lh=32)
    return f


def dma_wiring():
    f = Fig("ch26-dma-wiring",
            "SPL 不会替你接线：USART1_TX 要亲手接到 DMA1 Channel 4 / wire it yourself")
    f.text(84, 130, "三件事全做完，USART 的 DMA 请求才真的到达缓冲区；只做两件，CNDTR 一动不动",
           size=20, color=MUTED)

    # data path
    f.rect(84, 168, 260, 96, color=BLUE_D, fill=WHITE, sw=2.6)
    f.text(214, 204, "USART1", size=22, color=BLUE_D, anchor="middle", weight="bold")
    f.text(214, 236, "DR 数据寄存器", size=17, color=INK, anchor="middle")
    f.arrow(352, 216, 452, 216, color=INK, sw=3.0)
    f.text(402, 196, "请求", size=16, color=MUTED, anchor="middle")
    f.rect(462, 168, 280, 96, color=GREEN_D, fill=WHITE, sw=2.6)
    f.text(602, 200, "DMA1 Channel 4", size=20, color=GREEN_D, anchor="middle",
           weight="bold")
    f.text(602, 234, "CPAR→DR · CMAR→buf · CNDTR 递减", size=15, color=INK,
           anchor="middle")
    f.arrow(750, 216, 850, 216, color=INK, sw=3.0)
    f.text(800, 196, "搬运", size=16, color=MUTED, anchor="middle")
    f.rect(860, 168, 208, 96, color=RED, fill=WHITE, sw=2.6)
    f.text(964, 204, "tx_buffer", size=20, color=RED, anchor="middle", weight="bold")
    f.text(964, 236, "完成前必须一直存在", size=15, color=INK, anchor="middle")

    steps = [
        ("1", "RCC_AHBPeriphClockCmd(RCC_AHBPeriph_DMA1)", "先给 DMA1 开时钟"),
        ("2", "DMA_DeInit / StructInit / Init(Ch4)", "地址·方向·宽度·增量一次说清"),
        ("3", "USART_DMACmd(USART1, USART_DMAReq_Tx) + DMA_Cmd(Ch4)", "请求开关 + 通道开关，两个都要"),
    ]
    y = 320
    for n, code, note in steps:
        f.circle(112, y + 24, 22, color=GREEN_D, fill=WHITE, sw=2.4)
        f.text(112, y + 33, n, size=21, color=GREEN_D, anchor="middle", weight="bold",
               halo=True)
        f.rect(150, y, 640, 52, color=INK, fill=WHITE, sw=2.2)
        f.text(166, y + 34, code, size=18, color=INK, halo=True)
        f.text(810, y + 34, note, size=17, color=MUTED)
        y += 70
    f.panel(84, y + 12, 984, 96, AMBER_FILL)
    f.rect(84, y + 12, 984, 96, color=AMBER_STROKE, sw=2.6)
    f.multi(108, y + 44, ["边界：缓冲区在完成前必须继续存在；方向、宽度、增量要和真实寄存器匹配；",
                          "DMA_GetCurrDataCounter() 读到的是剩余项数，不是新增长度；F1 无 D-Cache，搬到 H7 要另算"],
            size=18, color=INK, lh=30)
    return f


FIGS = {
    "ch26-dma-wiring": dma_wiring,
    "ch26-call-chains": call_chains,
    "ch26-migrate-steps": migrate_steps,
    "ch26-four-layers": four_layers,
    "ch26-defines": defines,
    "ch26-init-steps": init_steps,
    "ch26-spl-hal": spl_hal,
    "ch26-timeout-poll": timeout_poll,
    "ch26-irq-no-callback": irq_no_callback,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
