# -*- coding: utf-8 -*-
"""批 8 架构图生成器（G3 / S15 / R0 / F7）。铁律同前：边坐标逐条手工核算。

坐标依据 stack-diagram/references/geometry.md：节点框 132×100（left=cx-66），
水平边走 tile 中线 y=top+30（端点 cx±30 外再留 6px），垂直边走「上框底 top+100 →
下 tile 顶 top-4」，肘形的横段一律放在两行之间的空带里，逐条确认该 x 走廊在
y1..y2 之间不穿过任何节点框。
"""
import io, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = io.open(os.path.join(ROOT, 'boot-sequence.html'), encoding='utf-8').read()


def group(x, y, w, h, label, icon=None, kind='ga'):
    img = f'<img src="%%ICON_{icon}%%" alt="">' if icon else ''
    return (f'    <div class="group {kind}" style="left:{x}px; top:{y}px; width:{w}px; height:{h}px;">\n'
            f'      <div class="g-label">{img}{label}</div>\n    </div>')


def node(name, cx, top, icon, role):
    return (f'    <div class="node" style="left:{cx-66}px;top:{top}px">\n'
            f'      <div class="tile"><img src="%%ICON_{icon}%%" alt=""></div>\n'
            f'      <div class="name"><span>{name}</span></div><div class="role"><span>{role}</span></div>\n'
            f'    </div>')


def edge(cls, d, label=None, lx=None, ly=None, anchor='middle'):
    s = f'      <path class="{cls}" d="{d}" marker-end="url(#ar)"/>'
    if label:
        a = ' a' if cls.startswith('e') else ''
        s += f'\n      <text class="el{a}" x="{lx}" y="{ly}" text-anchor="{anchor}">{label}</text>'
    return s


def build_html(spec):
    W, H = spec['size']
    groups = '\n'.join(group(*g) for g in spec['groups'])
    nodes = '\n'.join(node(*n) for n in spec['nodes'])
    edges = '\n'.join(edge(*e) for e in spec['edges'])
    html = TEMPLATE
    html = html.replace('<title>复位之后一毫秒：五站流水线</title>', f"<title>{spec['title']}</title>")
    html = html.replace('复位之后一毫秒：五站流水线</h1>', f"{spec['title']}</h1>")
    html = html.replace('御舆 MCU 书 · B4 启动过程 · 配图', spec['kicker'])
    html = re.sub(r'<p class="lede">.*?</p>', f'<p class="lede">{spec["lede"]}</p>', html, flags=re.S)
    html = re.sub(r'\.canvas \{ position: relative; width: \d+px; height: \d+px;',
                  f'.canvas {{ position: relative; width: {W}px; height: {H}px;', html)
    html = re.sub(r'svg\.edges \{ position:absolute; inset:0; width:\d+px; height:\d+px;',
                  f'svg.edges {{ position:absolute; inset:0; width:{W}px; height:{H}px;', html)
    html = re.sub(r'viewBox="0 0 \d+ \d+"', f'viewBox="0 0 {W} {H}"', html)
    m = re.search(r'(<div class="canvas">)([\s\S]*?)(\n  </div>\n  </div>)', html)
    body = '\n\n    <!-- GROUPS -->\n' + groups + '\n\n    <!-- EDGES -->\n' + \
           f'    <svg class="edges" viewBox="0 0 {W} {H}" aria-hidden="true">\n      <defs>\n' \
           f'        <marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">\n' \
           f'          <path d="M0 0 L10 5 L0 10 z" fill="context-stroke"/>\n        </marker>\n      </defs>\n' + edges + \
           '\n    </svg>' + '\n\n    <!-- NODES -->\n' + nodes
    html = html[:m.start(2)] + body + html[m.start(3):]
    legend = '\n'.join(f'    <span><span class="sw{c}"></span>{t}</span>' for t, c in spec['legend'])
    html = re.sub(r'  <div class="legend">[\s\S]*?</div>\n\n  <div class="foot">',
                  f'  <div class="legend">\n{legend}\n  </div>\n\n  <div class="foot">', html)
    html = re.sub(r'<span>[^<]*Boot 引脚[^<]*</span>', f'<span>{spec["foot"]}</span>', html)
    return html


SPECS = []

# ── 图 21 · G3 寄存器改名对照：七列偏移轨，上下两套牌 ──────────
# 1 列厂商行首 + 7 列寄存器：cx 110 / 260..1100 步长 140（同列上下对齐，垂直边落在列心）。
# 组框只留一整块（label 在 y≈92..112），两套牌的身份由行首砖承担——
# 若按厂商拆成上下两个组框，下框的左上角标签会被 x=130 那条竖边穿过（竖边走 y 240..416）。
COLS = [260, 400, 540, 680, 820, 960, 1100]
OFFSETS = ['0x00', '0x04', '0x08', '0x0C', '0x10', '0x14', '0x18']
STM32 = [('CR1', 'settings', '使能 · 帧格式 · 中断'),
         ('CR2', 'settings', '时钟 · 停止位 · 地址'),
         ('CR3', 'settings', '流控 · DMA · 智能卡'),
         ('BRR', 'binary', '波特率分频'),
         ('GTPR', 'box', '保护时间 · 预分频'),
         ('SR', 'bell', '状态标志'),
         ('DR', 'cable', '数据读写')]
GD32 = [('CTL0', 'settings', 'UEN · REN · TEN'),
        ('CTL1', 'settings', 'CLEN 不连续时钟'),
        ('CTL2', 'settings', 'SCEN · NKEN · IREN'),
        ('BAUD', 'binary', '分频职责不变'),
        ('GP', 'box', '保护时间'),
        ('STAT', 'bell', 'RBNE · TBE'),
        ('DATA', 'cable', '数据职责不变')]

SPECS.append(dict(
    file='usart-rename-map', size=(1210, 620),
    title='八个串口两套牌：偏移不动，名字全换', kicker='御舆 MCU 书 · G3 GD32 USART 增强点 · 配图',
    lede='CR1/CR2/CR3 改姓 CTL0/CTL1/CTL2，BRR 换 BAUD，SR/DR 换 STAT/DATA。0x00 到 0x18 逐行对齐，迁移按偏移不按名字。',
    groups=[(20, 80, 1170, 490, '寄存器名对照 · 上下两排同一偏移', None, 'gb')],
    nodes=[('STM32F407', 110, 140, 'cpu', 'RM0090 命名'),
           ('GD32F4xx', 110, 420, 'cpu', '全系统一纪律')] +
          [(STM32[i][0], COLS[i], 140, STM32[i][1], STM32[i][2]) for i in range(7)] +
          [(GD32[i][0], COLS[i], 420, GD32[i][1], GD32[i][2]) for i in range(7)],
    # 行首砖→本行第一列：走 tile 中线 y=170 / y=450，端点 146→224 之间是空地，不穿任何框。
    # 垂直边：上框底 140+100=240 → 下 tile 顶 420-4=416，列心即走廊；偏移标签挂右侧 10px（< 66px 半框宽）
    edges=[('n dash', 'M146 170 H224', None, None, None),
           ('n dash', 'M146 450 H224', None, None, None)] + \
          [('e', f'M{cx} 240 V416', OFFSETS[i], cx + 10, 330, 'start') for i, cx in enumerate(COLS)],
    legend=[('同一偏移 · 功能等价', ''), ('行首=该排归属', ' n dash')],
    foot='USART0 与 USART5 挂 APB2（时钟使能位在 RCU_APB2EN），其余六路在 APB1 · GD32 独有 USART5 / UART6 / UART7 · '
         'IRQ 37·38·39 / 52·53 / 71 / 82·83 不连续 · 编号从 0 起是与中断号对齐，找对应看总线加中断号，别按编号',
))

# ── 图 22 · S15 SPL 三板斧 → GPIO_Init → 四段寄存器 ────────────
SPECS.append(dict(
    file='spl-anatomy', size=(1020, 700),
    title='库没有魔法：三板斧喂给 GPIO_Init，四段寄存器落位', kicker='御舆 MCU 书 · S15 SPL 解剖 · 配图',
    lede='基址宏把地址变成名字，结构体把地址掰成字段，位掩码把位段变成宏；GPIO_Init 只是把它们按 pinpos 移位写进四段寄存器。',
    groups=[(100, 80, 820, 210, 'stm32f4xx.h 三板斧 · CMSIS 设备头逐字可见', None, 'gb')],
    nodes=[
        ('基址宏', 190, 140, 'binary', 'GPIOA = 0x40020000'),
        ('GPIO_TypeDef', 510, 140, 'braces', '9 字段 = RM0090 布局'),
        ('位掩码', 830, 140, 'settings', '枚举值 = 位段值'),
        ('GPIO_Init', 300, 380, 'workflow', '逐 pin 循环 · 先清后置'),
        ('assert_param', 700, 380, 'bell', 'Debug 体检 · Release 空宏'),
        ('MODER 0x00', 150, 560, 'box', '2 位/引脚 · 移 pinpos×2'),
        ('OTYPER 0x04', 390, 560, 'box', '1 位/引脚 · 推挽/开漏'),
        ('OSPEEDR 0x08', 630, 560, 'box', '2 位/引脚 · 仅 OUT/AF'),
        ('PUPDR 0x0C', 870, 560, 'box', '2 位/引脚 · Analog 清 0'),
    ],
    # 三条供料边分用 y=300/330/360 三条走廊，避免横段重叠成一根粗线；
    # 入 tile 处按 tile 跨度 cx±30 错开：GPIO_Init 收 278 与 310，assert_param 收 678。
    edges=[
        ('n', 'M190 240 V300 H278 V376', None, None, None),
        ('n', 'M830 240 V360 H310 V376', None, None, None),
        ('n', 'M510 240 V330 H678 V376', None, None, None),
        # 四段落位共用 y=510 空带（GPIO_Init 框底 480 与 row3 tile 顶 560 之间），
        # assert_param 框占 380..480，横段在其下方，不相碰。
        ('e', 'M300 480 V510 H150 V556', None, None, None),
        ('e', 'M300 480 V510 H390 V556', None, None, None),
        ('e', 'M300 480 V510 H630 V556', None, None, None),
        ('e', 'M300 480 V510 H870 V556', None, None, None),
    ],
    legend=[('翻译落位四段寄存器', ''), ('三板斧供料', ' n')],
    foot='直接赋值会覆盖其他 15 个引脚，所以先清后置 · 移位量由寄存器布局决定（2 位/引脚移 pinpos×2，OTYPER 1 位移 pinpos）· '
         'RCC_AHB1PeriphClockCmd 写完读回 AHB1ENR（某些版本用 __DSB()），替我们踩了「时钟生效延迟」这个坑 · 枚举值即位段值，翻译零查表',
))

# ── 图 23 · R0 RT-Thread 三层楼 ─────────────────────────────
SPECS.append(dict(
    file='rtt-three-floors', size=(1020, 840),
    title='RT-Thread 三层楼：内核打地基、组件当水电、软件包是家具', kicker='御舆 MCU 书 · R0 RT-Thread 架构 · 配图',
    lede='FreeRTOS 只给内核，RT-Thread 把组件层和软件包生态做进了主线；组件靠 INIT_*_EXPORT 自己登记，finsh 的 list_* 一把梭才有根。',
    groups=[(100, 130, 820, 210, '软件包 · packages/ —— 拎包入住', None, 'ga'),
            (100, 370, 820, 210, '组件层 · components/ —— 水电', None, 'gb'),
            (100, 610, 820, 210, '内核层 · src/ + include/ + libcpu/ —— 地基', None, 'ga')],
    nodes=[
        ('传感器驱动包', 190, 190, 'box', 'menuconfig 勾选'),
        ('MQTT 客户端', 510, 190, 'network', 'pkgs --update 拉源码'),
        ('JSON 解析', 830, 190, 'file-code', '三方生态'),
        ('finsh 控制台', 190, 430, 'terminal', 'list_thread · list_device'),
        ('设备框架', 510, 430, 'workflow', 'rt_device 注册与查找'),
        ('dfs · lwip', 830, 430, 'folder', '文件系统 · 网络'),
        ('调度 · IPC · 内存', 190, 670, 'cpu', '线程 · 信号量 · 事件'),
        ('对象容器', 510, 670, 'list-tree', '按类型分链 · 统一登记'),
        ('libcpu · BSP', 830, 670, 'arm', '上下文切换 · 中断接管'),
    ],
    # 软件包→组件：竖直边走 x=190 / x=830 两条列心走廊（290→426 之间无其他框）。
    # 组件→内核：登记边走 x=534（tile 510±30 内偏右），遍历边走 y=600 层间空带后在 x=486 入 tile 左半，
    # 两条箭头分落 486 与 534，同在 tile 顶但错开 48px。
    edges=[
        ('n dash', 'M190 290 V426', '勾选即用', 200, 358, 'start'),
        ('n dash', 'M830 290 V426', None, None, None),
        ('e', 'M534 530 V666', 'INIT_*_EXPORT 登记', 544, 600, 'start'),
        ('n', 'M190 530 V600 H486 V666', None, None, None),
    ],
    legend=[('自动登记 · 统一遍历', ''), ('按需挂接', ' n dash')],
    foot='对照 FreeRTOS：内核一一对应，但 FreeRTOS 没有组件层这一档（ESP-IDF 相当于替它配了一层）· '
         'Nano 只到内核层，没有设备框架/文件系统/网络 · 漏调 rt_components_init() 就 list_device 一片空 · '
         '段内顺序由链接顺序定（回 B3）· 5.x 主线，Apache-2.0',
))

# ── 图 24 · F7 heap_4 空闲链表与合并判据 ─────────────────────
SPECS.append(dict(
    file='heap-free-list', size=(1020, 580),
    title='heap_4 的地契：空闲链表按地址排，相邻才拼', kicker='御舆 MCU 书 · F7 内存管理 · 配图',
    lede='总空闲和最大连续块经常不一样大：链表按地址排序，只有相邻的空闲块会被焊成一块，隔着已用块的洞永远拼不上。',
    groups=[(60, 80, 900, 210, 'ucHeap[configTOTAL_HEAP_SIZE] · 本工程 16KB', None, 'gb')],
    nodes=[
        ('块 A · 已用', 150, 140, 'box', '占着不动'),
        ('空闲块', 330, 140, 'memory', '被 A 隔开'),
        ('块 B · 已用', 510, 140, 'box', '中间这根钉子'),
        ('空闲块', 690, 140, 'memory', '后邻就是空闲'),
        ('空闲块', 870, 140, 'memory', '一焊成一片'),
        ('总空闲', 150, 420, 'file-code', 'FreeHeapSize'),
        ('xFreeList', 510, 420, 'list-tree', '按地址从小到大排序'),
        ('历史最小剩余', 870, 420, 'bell', '只在 heap_4/5 有'),
    ],
    # 相邻判据走 tile 中线 y=170，端点 30+6 让位；
    # 汇入链表：x=330 用 y=330 走廊入 482，x=870 用同走廊入 538，x=690 改走 y=300 走廊入列心 510，
    # 三条横段分处 300/330 两层且互不重叠；两个指标读链表走 row2 tile 中线 y=450。
    edges=[
        ('n dash', 'M366 170 H474', '隔着已用 · 不并', 420, 162),
        ('e', 'M726 170 H834', '前后邻接上 · 并', 780, 162),
        ('n', 'M330 240 V330 H482 V416', None, None, None),
        ('n', 'M690 240 V300 H510 V416', None, None, None),
        ('n', 'M870 240 V330 H538 V416', None, None, None),
        ('n', 'M474 450 H186', None, None, None),
        ('n', 'M546 450 H834', None, None, None),
    ],
    legend=[('相邻合并 · 链表按地址', ''), ('链表喂指标', ' n'), ('隔着的两块', ' n dash')],
    foot='prvInsertBlockIntoFreeList（V11.1.0 heap_4.c）三步：按地址找插入位 → 前邻尾接上我就并进前邻 → 后邻首接上我也并进来 · '
         '能力阶梯 heap_1 只分不放 → heap_2 放不合 → heap_3 包 libc → heap_4 相邻合并 → heap_5 多区（SRAM+CCM）· '
         '历史最小剩余是水位最低点，不是碎片率',
))

for spec in SPECS:
    html = build_html(spec)
    out = os.path.join(ROOT, spec['file'] + '.html')
    io.open(out, 'w', encoding='utf-8', newline='\n').write(html)
    print('written', out)
