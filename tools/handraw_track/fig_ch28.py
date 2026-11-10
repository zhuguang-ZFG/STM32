# -*- coding: utf-8 -*-
"""ch28 knowledge-track figures (handraw grammar, real chapter facts)."""
from hd import *


def box_text(f, x, y, w, lines, color, size=26, lh=None, pad=20):
    lh = lh or size * 1.46
    f.multi(x + pad, y + pad + size * 0.9, lines, size=size, color=color, lh=lh)
    need = pad * 2 + size * 0.9 + (len(lines) - 1) * lh
    return need


def col_head(f, cx, y, s, color, size=28):
    f.htext(cx, y, s, size=size, color=color, anchor="middle", weight="bold")


# ---------------------------------------------------------------- fig 1
def four_concepts():
    f = Fig("ch28-four-concepts", "先把四个概念分开 / four concepts first")
    cols = [
        ("裸机", "bare-metal", GREEN_D,
         ["while(1){", " 查标志 → 动作 }", "一个大循环", "没有并行"]),
        ("前后台", "main + ISR", BLUE_D,
         ["ISR 置标志", "主循环兜底", "响应快", "共享数据要小心"]),
        ("RTOS", "kernel + tasks", AMBER_STROKE,
         ["内核管调度与 IPC", "任务各管一段", "并发是假象", "单核同一刻只跑一个"]),
        ("Linux", "process + drivers", RED,
         ["进程 + 驱动子系统", "要 MMU", "启动与内存预算", "和 MCU 完全不同"]),
    ]
    cw, gap = 258, 16
    x0 = (W - (cw * 4 + gap * 3)) / 2
    y0 = 150
    for i, (zh, en, c, lines) in enumerate(cols):
        x = x0 + i * (cw + gap)
        f.rect(x, y0, cw, 236, color=c, fill=WHITE)
        f.htext(x + cw / 2, y0 + 46, zh, size=30, color=c, anchor="middle",
                weight="bold", hl=(c == AMBER_STROKE))
        f.text(x + cw / 2, y0 + 74, en, size=19, color=MUTED, anchor="middle")
        f.multi(x + 22, y0 + 112, lines, size=24, color=INK, lh=37)
    f.htext(W / 2, 486, "内核只负责：调度 · IPC · 软件定时器 · 临界区 · 内存分配",
            size=27, color=BLUE_D, anchor="middle", weight="bold",
            hl=True, hl_fill=AMBER_FILL)
    f.text(W / 2, 536, "板级驱动、文件系统、网络、升级策略 — 都不是内核白送的",
           size=25, color=MUTED, anchor="middle")
    f.text(W / 2, 580, "四概念分清之后，才轮到挑内核名字", size=23,
           color=MUTED, anchor="middle")
    return f


# ---------------------------------------------------------------- fig 2
def os_compare():
    f = Fig("ch28-os-compare", "选哪一种 / which kernel", title_color=INK)
    cols = [
        ("FreeRTOS", "11.3.2", GREEN_D,
         ["小内核", "网络 / TLS / OTA", "项目自行组合"]),
        ("RT-Thread", "5.3.0", BLUE_D,
         ["设备框架", "FinSH · DFS · SAL", "软件包生态"]),
        ("Zephyr", "4.4.2", AMBER_STROKE,
         ["Kconfig", "Devicetree", "子系统统一构建"]),
        ("CMSIS-RTOS2", "2.3.0", RED,
         ["统一接口", "≠ 统一实现", "语义要逐条对"]),
    ]
    cw, gap = 258, 16
    x0 = (W - (cw * 4 + gap * 3)) / 2
    y0 = 148
    for i, (name, ver, c, lines) in enumerate(cols):
        x = x0 + i * (cw + gap)
        f.rect(x, y0, cw, 226, color=c, fill=WHITE)
        f.htext(x + cw / 2, y0 + 48, name, size=29, color=c, anchor="middle",
                weight="bold", hl=(c == AMBER_STROKE))
        f.htext(x + cw / 2, y0 + 82, "v" + ver, size=22, color=MUTED,
                anchor="middle")
        f.multi(x + 22, y0 + 122, lines, size=24, color=INK, lh=37)
    f.htext(W / 2, 448, "选型表不是排行榜", size=30, color=INK, anchor="middle",
            weight="bold", hl=True)
    f.multi(W / 2, 496, ["先列硬约束 → 再看现有驱动与维护周期 → 最后才看 API 熟不熟"],
            size=26, color=BLUE_D, anchor="middle")
    f.text(W / 2, 540, "已有稳定 FreeRTOS 证据的产品，为“生态”换内核，迁移风险常大于收益",
           size=23, color=MUTED, anchor="middle")
    return f


# ---------------------------------------------------------------- fig 3
def owner_task():
    f = Fig("ch28-owner-task", "所有者任务 / one owner per peripheral")
    # BEFORE (red, left)
    f.htext(290, 142, "before", size=30, color=RED, anchor="middle",
            weight="bold")
    f.rect(90, 168, 400, 286, color=RED, fill=WHITE)
    f.multi(116, 214, ["task A、task B", "都直接调", "HAL_SPI_TransmitReceive()"],
            size=25, color=INK, lh=38)
    f.multi(116, 350, ["片选 / DMA / 恢复", "被拆开 — 锁只护住", "单次 API 调用"],
            size=25, color=RED, lh=38)
    # AFTER (green, right)
    f.htext(862, 142, "after", size=30, color=GREEN_D, anchor="middle",
            weight="bold")
    f.rect(620, 168, 440, 286, color=GREEN, fill=WHITE)
    f.multi(646, 214, ["task A / task B → 队列", "flash_task 唯一所有者", "碰 SPI + CS + DMA"],
            size=25, color=INK, lh=38)
    f.multi(646, 350, ["xTaskNotify 回执 requester", "busy / queued / timeout", "结果可预期"],
            size=25, color=GREEN_D, lh=38)
    # middle arrow
    f.arrow(500, 306, 610, 306, color=INK, sw=3.4, head=13)
    f.text(555, 284, "改成", size=26, color=INK, anchor="middle", weight="bold")
    # bottom rule strip
    f.panel(160, 520, 832, 96, AMBER_FILL)
    f.rect(160, 520, 832, 96, color=AMBER_STROKE, sw=2.8)
    f.text(W / 2, 560, "一个有状态外设只有一个所有者", size=28, color=INK,
           anchor="middle", weight="bold")
    f.text(W / 2, 598, "其他任务发命令，不直接并发调 HAL", size=24, color=INK,
           anchor="middle")
    f.text(W / 2, 668, "请求自带 sequence 与 requester —— 回执可以逐条对账",
           size=24, color=MUTED, anchor="middle")
    return f


# ---------------------------------------------------------------- fig 4
def three_times():
    f = Fig("ch28-three-times", "R = B + C + S，截止点只有一个 / one deadline")
    y = 300
    x0, x1 = 96, 1030
    # axis
    f.stroke([(x0, y), (x1, y)], color=INK, sw=3.0, amp=1.4)
    f.arrowhead(x1, y, 60, 0, color=INK, head=13)
    # milestones
    pts = [
        (x0 + 40, "release", "事件发生", INK),
        (x0 + 300, "B", "被更高优先级 / 锁阻塞", RED),
        (x0 + 520, "C", "自己真正执行", GREEN_D),
        (x0 + 760, "S", "ISR 与突发干扰", AMBER_STROKE),
        (x0 + 940, "deadline", "截止点 D", BLUE_D),
    ]
    for px, name, note, c in pts:
        f.line(px, y - 14, px, y + 14, color=c, sw=3.0, amp=0.8)
        f.text(px, y - 30, name, size=27, color=c, anchor="middle",
               weight="bold")
        f.text(px, y + 48, note, size=21, color=MUTED, anchor="middle")
    # braces-ish segments
    f.htext(x0 + 170, y - 84, "响应时间从这里起算", size=23, color=MUTED,
            anchor="middle")
    f.arrow(x0 + 120, y - 66, x0 + 38, y - 22, color=MUTED, sw=2.2, head=8)
    # bracket B..S under axis
    f.stroke([(x0 + 300, y + 92), (x0 + 300, y + 112), (x0 + 760, y + 112),
              (x0 + 760, y + 92)], color=RED, sw=2.2, amp=1.2)
    f.htext((x0 + 300 + x0 + 760) / 2, y + 148, "R = B + C + S（不是一段纯执行）",
            size=27, color=RED, anchor="middle", weight="bold", hl=True)
    # three rules
    rules = [
        ("周期任务用绝对唤醒点", "执行时间不会累积成周期漂移"),
        ("一个事务一个单调时钟截止点", "每次等待都算剩余时间"),
        ("超时返回给策略层", "底层不擅自“再试一次”"),
    ]
    bw, gap = 340, 26
    bx0 = (W - (bw * 3 + gap * 2)) / 2
    for i, (t1, t2) in enumerate(rules):
        x = bx0 + i * (bw + gap)
        f.rect(x, 560, bw, 128, color=GREEN, fill=WHITE)
        f.multi(x + 24, 604, [t1], size=21, color=GREEN_D, weight="bold")
        f.multi(x + 24, 648, [t2], size=20, color=INK)
    return f


# ---------------------------------------------------------------- fig 5
def fault_triage():
    f = Fig("ch28-fault-triage", "系统故障三岔口 / fault triage")
    # hub
    f.panel(386, 330, 380, 150, AMBER_FILL)
    f.rect(386, 330, 380, 150, color=AMBER_STROKE, sw=3.0)
    f.multi(406, 372, ["看门狗不复位", "但业务已经死了", "— 第一条假设 —"],
            size=26, color=INK, lh=36)
    # branch boxes
    f.rect(84, 96, 330, 168, color=GREEN, fill=WHITE)
    f.multi(104, 138, ["(1) 队列满", "丢最新 / 丢最旧 /", "背压 / 进故障 —", "满时策略必须写明"],
            size=24, color=GREEN_D, lh=34)
    f.rect(738, 96, 330, 168, color=RED, fill=WHITE)
    f.multi(758, 138, ["(2) 冻结任务仍喂狗", "错误上下文还在刷新", "→ 只允许健康", "监督者喂狗"],
            size=24, color=RED, lh=34)
    f.rect(110, 570, 330, 168, color=BLUE, fill=WHITE)
    f.multi(130, 612, ["(3) 驱动超时", "返回码回到策略层", "策略层才知道", "能不能重试"],
            size=24, color=BLUE_D, lh=34)
    f.rect(712, 570, 340, 168, color=MUTED, fill=WHITE)
    f.multi(732, 612, ["验收不是“复位了”", "而是复位后能区分", "哪一个健康条件", "先失败"],
            size=24, color=INK, lh=34)
    f.arrow(300, 264, 430, 324, color=GREEN)
    f.arrow(840, 264, 720, 324, color=RED)
    f.arrow(360, 570, 460, 490, color=BLUE)
    f.arrow(770, 570, 680, 490, color=MUTED)
    return f



def wdg_supervisor():
    f = Fig("ch28-wdg-supervisor", "看门狗由健康监督者喂 / one supervisor, all epochs")
    # 左：三个任务各自汇报 epoch
    f.text(96, 140, "epoch 是工作进度计数：做完有效工作才加一，每个任务按自己的期限检查", size=21,
           color=MUTED)
    tasks = [("任务 A（采样）", GREEN_D), ("任务 B（协议）", BLUE_D),
             ("任务 C（存储）", AMBER_STROKE)]
    y = 168
    for index, (name, c) in enumerate(tasks):
        f.rect(96, y, 340, 76, color=c, fill=WHITE)
        f.text(116, y + 46, name, size=22, color=c, weight="bold")
        f.rect(330, y + 22, 84, 34, color=c, fill=WHITE, sw=1.8)
        f.text(372, y + 45, ("12→13", "7→8", "25→26")[index], size=16, color=INK, anchor="middle")
        y += 92
    f.arrow(440, 300, 560, 300, color=INK, bend=0.06)
    # 中：监督任务
    f.rect(566, 170, 330, 260, color=GREEN_D, fill=WHITE)
    f.htext(731, 210, "监督任务", size=26, color=GREEN_D, anchor="middle",
            weight="bold")
    f.multi(590, 252, ["按各任务期限检查进度，", "再看队列、内存和状态机；", "全部健康才刷新 IWDG"], size=20,
            color=INK, lh=32)
    f.arrow(731, 434, 731, 486, color=GREEN_D, bend=0.0, head=11)
    f.rect(600, 492, 262, 56, color=GREEN_D, fill=WHITE, sw=2.2)
    f.text(731, 528, "IWDG 刷新", size=22, color=GREEN_D, anchor="middle",
           weight="bold")
    # 右：假健康
    f.rect(924, 170, 132, 260, color=RED, fill=WHITE)
    f.multi(990, 210, ["假健康：", "B 已卡住，", "A 或中断", "仍在喂狗"], size=19,
            color=RED, lh=30, anchor="middle")
    f.panel(96, 600, 960, 82, AMBER_FILL)
    f.rect(96, 600, 960, 82, color=AMBER_STROKE, sw=3.0)
    f.text(W / 2, 632, "任一关键任务超期未前进：停止喂狗，尽力保存最小摘要",
           size=23, color=INK, anchor="middle", weight="bold")
    f.text(W / 2, 665, "摘要写入也有截止点；写入失败不妨碍看门狗复位",
           size=19, color=INK, anchor="middle")
    return f


def memory_regions():
    f = Fig("ch28-memory-regions",
            "五块内存不是一回事 / five memory regions, five risk lists")

    regions = [
        (84, "线程栈", ["调用帧 · 局部变量", "保存上下文"],
         ["最坏调用链、", "printf/浮点、嵌套中断"], ["填充水位 · 溢出钩子"], GREEN_D),
        (275, "内核对象池/堆", ["TCB · 队列 · 定时器"],
         ["动态创建失败、碎片"], ["启动前预算 ·", "最小空闲记录"], BLUE_D),
        (466, "C 库堆", ["malloc/new · 部分 libc"],
         ["线程安全、与 RTOS", "堆重复计数"], ["唯一分配器与锁策略"], RED),
        (657, "DMA 缓冲", ["外设与 CPU 共享"],
         ["可达性、对齐、", "Cache 一致性"], ["链接 map · 地址断言"], AMBER_STROKE),
    ]
    by, bh = 168, 210
    for x, title, who, risk, verify, col in regions:
        f.rect(x, by, 172, bh, color=col, fill=WHITE, sw=2.6)
        f.text(x + 12, by + 30, title, size=19, color=col, weight="bold")
        f.multi(x + 12, by + 52, ["谁用："] + who, size=13, color=INK, lh=18)
        f.multi(x + 12, by + 106, ["风险："] + risk, size=13, color=INK, lh=18)
        f.multi(x + 12, by + 162, ["验证："] + verify, size=13, color=col, lh=18)
    # 持久化区横条
    f.rect(84, 402, 745, 96, color=MUTED, fill=WHITE, sw=2.6)
    f.multi(104, 424,
            ["持久化区（Flash / 备份 SRAM）：掉电撕裂 · 版本不兼容 · 写放大",
             "验证：双副本 · CRC · 版本管理 · 故障注入"],
            size=17, color=INK, lh=26)
    # 结论
    f.rect(84, 530, 984, 168, color=GREEN_D, fill=WHITE, sw=2.6)
    f.multi(104, 560,
            ["量产系统：长期对象在初始化阶段静态创建",
             "确需动态生命周期：谁分配、谁释放、失败回滚、重复释放怎么发现",
             "malloc 失败改成返回空数据 = 隐藏资源耗尽，不是恢复策略"],
            size=20, color=INK, lh=32)
    f.text(104, 668, "五块区域各自的风险与验证方法不同 —— 别用一张台账管全部",
           size=20, color=GREEN_D, weight="bold")
    return f

# ---------------------------------------------------------------- fig 8
def isr_divergence():
    f = Fig("ch28-isr-divergence",
            "任务没打印：先定位第一处分歧 / first divergence")
    gates = [
        ("1", "硬件 pending 位出现了吗？",
         "读 EXTI->PR / 外设 SR；先确认事件真的发生过", BLUE_D),
        ("2", "NVIC 使能、优先级放行了吗？",
         "ISER 位、BASEPRI、configMAX_SYSCALL_INTERRUPT_PRIORITY", BLUE_D),
        ("3", "ISR 真的进了吗？",
         "ISR 首行翻转 GPIO 或计数；别拿 printf 当证据", GREEN_D),
        ("4", "事件成功入队了吗？",
         "xQueueSendFromISR 返回 pdTRUE / pdFALSE；通知同理", GREEN_D),
        ("5", "目标线程就绪了吗？",
         "被更高优先级占用、优先级数值填错、被锁阻塞", AMBER_STROKE),
        ("6", "调度器切换了吗？",
         "看 portYIELD_FROM_ISR 的调用点与临界区长度", RED),
    ]
    y = 138
    for num, q, evidence, col in gates:
        f.rect(84, y, 984, 72, color=col, fill=WHITE)
        f.circle(126, y + 36, 20, color=col, sw=2.2, fill=WHITE)
        f.text(126, y + 44, num, size=21, color=col, anchor="middle",
               weight="bold")
        f.text(160, y + 30, q, size=21, color=INK, weight="bold")
        f.text(160, y + 58, "证据：" + evidence, size=16, color=MUTED)
        y += 82
    f.htext(W / 2, 654,
            "任务「数值越大越高」，NVIC「数值越小越高」：两套空间不能互填",
            size=20, color=RED, anchor="middle", weight="bold", hl=True)
    f.text(W / 2, 694,
           "从「任务没打印」直接跳到「RTOS 坏了」，等于跳过六道闸门里的五道",
           size=18, color=INK, anchor="middle")
    f.text(W / 2, 728,
           "每道闸门留一条可读证据：计数、返回码、优先级、切换次数",
           size=17, color=MUTED, anchor="middle")
    return f


# ---------------------------------------------------------------- fig 9
def h745_contracts():
    f = Fig("ch28-h745-contracts",
            "H745 双核：五层契约分别冻结 / five contracts")
    layers = [
        ("共享存储", "SRAM / 链接段", GREEN_D,
         "两核都能访问的 SRAM 区域：起始、长度、对齐和结构体布局",
         "不得藏进某一核私有的栈或链接段",
         "注入越界长度、错误对齐和非法状态"),
        ("所有权与可见性", "屏障 / Cache", GREEN_D,
         "单写者/读者切换；交接边界的发布/获取顺序与内存屏障",
         "映射可缓存区时按所有权 clean/invalidate",
         "连更两代序号与 payload，读端只接受同一代"),
        ("同步", "HSEM", AMBER_STROKE,
         "HSEM ID 分配、持有者、最长持有、通知路径与超时降级",
         "释放 HSEM 不等于业务消息已处理",
         "占住一个 HSEM 或丢一次通知，另一核须超时并留因"),
        ("消息协议", "线上格式", AMBER_STROKE,
         "magic、版本、长度、序号、状态和兼容规则",
         "共享 C 结构体也属于线上协议",
         "注入未知版本、截断长度和重复序号"),
        ("启动与恢复", "代际 / 心跳", RED,
         "谁先初始化共享区、ready/代际号、心跳、单核复位重同步",
         "整机复位责任必须显式指定",
         "分别冻结或复位 M7/M4，存活核进预定降级态"),
    ]
    y = 128
    for name, sub, col, freeze, own, inject in layers:
        f.rect(84, y, 196, 104, color=col, fill=WHITE)
        f.text(182, y + 48, name, size=19, color=col, anchor="middle",
               weight="bold")
        f.text(182, y + 76, sub, size=14, color=MUTED, anchor="middle")
        f.text(300, y + 32, "冻结：" + freeze, size=16, color=INK)
        f.text(300, y + 58, "补充：" + own, size=15.5, color=MUTED)
        f.text(300, y + 86, "注入：" + inject, size=15.5, color=col)
        y += 112
    f.htext(W / 2, 706,
            "HSEM 只给原子占用和中断通知：不搬 payload，也不替 M7 管 Cache",
            size=19, color=RED, anchor="middle", weight="bold", hl=True)
    f.text(W / 2, 740, "「继续等」不是恢复策略：重试、重启单核、复位整机、保持安全输出，必须显式选一个",
           size=16, color=INK, anchor="middle")
    return f


# ---------------------------------------------------------------- fig 10
def experiment_evidence():
    f = Fig("ch28-experiment-evidence",
            "四组实验：每组交一份可验收证据 / four labs")
    f.text(84, 126, "实验", size=16, color=MUTED, weight="bold")
    f.text(384, 126, "动作", size=16, color=MUTED, weight="bold")
    f.text(756, 126, "验收证据", size=16, color=MUTED, weight="bold")
    rows = [
        ("实验一", ["对象语义对账"],
         ["队列深度 2 发三条消息：", "非阻塞 / 限时 / 永久等待"],
         ["返回码、耗时、最终顺序", "知道队列满怎么进策略层"], GREEN_D),
        ("实验二", ["所有者任务对比"],
         ["两任务抢同一 SPI/I2C，", "DMA 完成前再发一次请求"],
         ["稳定 busy / queued / timeout", "无片选或状态机交叉"], GREEN_D),
        ("实验三", ["故障注入"],
         ["依次冻结控制、", "网络、日志任务"],
         ["监督者识别失败并停喂狗", "复位后能指认先失败项"], AMBER_STROKE),
        ("实验四", ["跨系统垂直切片"],
         ["GPIO 中断 → 定长事件 →", "工作线程 → UART"],
         ["对象语义/配置/栈预算/ISR", "只用切片，不动网络与文件系统"], RED),
    ]
    y = 148
    for label, sub, action, evidence, col in rows:
        f.rect(84, y, 984, 104, color=col, fill=WHITE)
        f.text(104, y + 40, label, size=19, color=col, weight="bold")
        f.multi(104, y + 70, sub, size=16, color=INK)
        f.multi(384, y + 40, action, size=15.5, color=INK, lh=24)
        f.multi(756, y + 40, evidence, size=15, color=col, lh=24)
        y += 116
    f.text(84, 636, "共同前提：固定输入频率与日志格式；先做最小切片，再谈迁移与替换。",
           size=19, color=INK)
    f.htext(W / 2, 684,
            "验收看返回码、时序和切换次数，不看「看起来正常」",
            size=20, color=GREEN_D, anchor="middle", weight="bold", hl=True)
    f.text(W / 2, 720, "实验三的验收不是「最后复位了」，而是复位后能区分哪个健康条件先失败",
           size=16, color=MUTED, anchor="middle")
    return f


# ---------------------------------------------------------------- fig 11
def review_evidence():
    f = Fig("ch28-review-evidence",
            "选型评审十条，收敛成四条证据线 / four evidence lines")
    quads = [
        (90, 138, "版本与维护", GREEN_D,
         ["可维护的 BSP 与关键驱动", "冻结内核 / BSP / 组件 /", "工具链 / 依赖仓库",
          "CVE、勘误、上游修复", "有持续评估与升级流程"]),
        (582, 138, "预算", BLUE_D,
         ["Flash / SRAM / 线程栈", "网络与 TLS 峰值", "升级缓冲",
          "队列、池、重试的上限", "与满时策略"]),
        (90, 402, "时间证据", AMBER_STROKE,
         ["最坏响应与端到端时延", "有测量方案，不只写「实时」",
          "ISR 可调用 API", "NVIC 优先级与", "内核临界区规则"]),
        (582, 402, "所有权与恢复", RED,
         ["有状态外设与协议连接", "各有唯一所有者",
          "启动依赖 / 降级态 /", "恢复预算 / 看门狗健康条件", "迁移用同一组输入复测"]),
    ]
    for x, y, head, col, items in quads:
        f.rect(x, y, 480, 244, color=col, fill=WHITE)
        f.htext(x + 24, y + 44, head, size=21, color=col, weight="bold", hl=True)
        f.multi(x + 24, y + 84, items, size=16, color=INK, lh=27)
    f.htext(W / 2, 684, "清单不是打分表：任一条答不出证据，这一项就是未通过",
            size=20, color=RED, anchor="middle", weight="bold", hl=True)
    f.text(W / 2, 720, "证据要能复测；否则只是口头承诺，迁移时第一个失效",
           size=17, color=MUTED, anchor="middle")
    return f


FIGS = {
    "ch28-four-concepts": four_concepts,
    "ch28-os-compare": os_compare,
    "ch28-owner-task": owner_task,
    "ch28-three-times": three_times,
    "ch28-fault-triage": fault_triage,
    "ch28-memory-regions": memory_regions,
    "ch28-wdg-supervisor": wdg_supervisor,
    "ch28-isr-divergence": isr_divergence,
    "ch28-h745-contracts": h745_contracts,
    "ch28-experiment-evidence": experiment_evidence,
    "ch28-review-evidence": review_evidence,
}

if __name__ == "__main__":
    import sys
    names = sys.argv[1:] or list(FIGS)
    for n in names:
        f = FIGS[n]()
        OUT.mkdir(parents=True, exist_ok=True)
        save(f, str(OUT / (n + ".svg")))
        print("wrote", OUT / (n + ".svg"))
