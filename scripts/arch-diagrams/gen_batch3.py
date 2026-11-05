"""批 3 架构图生成器：数据 → stack-diagram 源 HTML。
坐标规则内建（geometry.md）：节点 132×100、tile mid=+30、组框 bottom≥last tile top+150、
竖边 box-bottom→tile-top（反向则终点=box底+4）、肘形边走空带走廊、横边 tile 缘 ±34/4。
边坐标逐条手工核算，生成器只做确定性渲染。"""
import os
import re

ROOT = os.path.dirname(os.path.abspath(__file__))

TEMPLATE = open(os.path.join(ROOT, 'boot-sequence.html'), encoding='utf-8').read()

def group(x, y, w, h, label, icon=None, kind='ga'):
    img = f'<img src="%%ICON_{icon}%%" alt="">' if icon else ''
    return f'    <div class="group {kind}" style="left:{x}px; top:{y}px; width:{w}px; height:{h}px;">\n      <div class="g-label">{img}{label}</div>\n    </div>'

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
    html = re.sub(r'\.canvas \{ position: relative; width: \d+px; height: \d+px;', f'.canvas {{ position: relative; width: {W}px; height: {H}px;', html)
    html = re.sub(r'svg\.edges \{ position:absolute; inset:0; width:\d+px; height:\d+px;', f'svg.edges {{ position:absolute; inset:0; width:{W}px; height:{H}px;', html)
    html = re.sub(r'viewBox="0 0 \d+ \d+"', f'viewBox="0 0 {W} {H}"', html)
    m = re.search(r'(<div class="canvas">)([\s\S]*?)(\n  </div>\n  </div>)', html)
    body = '\n\n    <!-- GROUPS -->\n' + groups + '\n\n    <!-- EDGES -->\n' + \
           f'    <svg class="edges" viewBox="0 0 {W} {H}" aria-hidden="true">\n      <defs>\n        <marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">\n          <path d="M0 0 L10 5 L0 10 z" fill="context-stroke"/>\n        </marker>\n      </defs>\n' + edges + '\n    </svg>' + \
           '\n\n    <!-- NODES -->\n' + nodes
    html = html[:m.start(2)] + body + html[m.start(3):]
    legend = '\n'.join(f'    <span><span class="sw{c}"></span>{t}</span>' for t, c in spec['legend'])
    html = re.sub(r'  <div class="legend">[\s\S]*?</div>\n\n  <div class="foot">',
                  f'  <div class="legend">\n{legend}\n  </div>\n\n  <div class="foot">', html)
    html = re.sub(r'<span>[^<]*实测口径[^<]*</span>', f'<span>{spec["foot"]}</span>', html)
    return html

SPECS = []

# ── 图 8 · S8 DMA 转运通路（直线链，tile 缘 ±34）─────────
SPECS.append(dict(
    file='dma-paths', size=(1020, 480),
    title='DMA 转运通路：外设、流、内存各管一段', kicker='御舆 MCU 书 · S8 DMA · 配图',
    lede='外设固定、内存自增，NDTR 倒数到零敲个铃；DMA 只管搬，不替你还债。',
    groups=[
        (20, 80, 220, 210, '外设侧 · 固定地址', 'cpu', 'ga'),
        (300, 80, 420, 210, 'DMA 控制器 · 8 流 × 8 通道', 'workflow', 'gb'),
        (780, 80, 220, 210, '内存侧 · 自增', 'database', 'ga'),
    ],
    nodes=[
        ('USART_TX 等', 130, 140, 'cpu', '外设固定 · 不自增'),
        ('流 × 通道', 400, 140, 'list-tree', '选定流和通道'),
        ('NDTR 计数器', 610, 140, 'binary', '倒数到零 · 敲铃 TC'),
        ('SRAM 缓冲', 890, 140, 'database', '内存自增'),
    ],
    edges=[
        ('e', 'M164 170 H366', '请求', 265, 162),
        ('e', 'M466 170 H576', None, None, None),
        ('e', 'M676 170 H856', '转运', 766, 162),
    ],
    legend=[('数据转运主路', '')],
    foot='循环搬流水 · 双缓冲不停机，但都不替你还债 · 清标志写 HIFCR/LIFCR，别碰 HISR/LISR',
))

# ── 图 9 · B3 三契约（复用 memory-map 成熟骨架，双地址=同名段连线）──
SPECS.append(dict(
    file='linker-map', size=(1000, 760),
    title='链接脚本三契约：圈地、分房、留门牌', kicker='御舆 MCU 书 · B3 链接脚本 · 配图',
    lede='MEMORY 圈地（两个组框）、SECTIONS 分房（段住进圈）、符号留门牌。.data 一个段两个住址——一条线讲完 &gt;RAM AT&gt; FLASH。',
    groups=[
        (135, 80, 330, 630, 'FLASH · ORIGIN=0x08000000', 'binary', 'ga'),
        (609, 80, 330, 630, 'RAM · ORIGIN=0x20000000', 'memory', 'gb'),
    ],
    nodes=[
        ('.isr_vector', 225, 140, 'list-tree', 'KEEP · 向量表住头排'),
        ('.text', 225, 280, 'file-code', '代码本体'),
        ('.data 初值 · LMA', 225, 420, 'binary', '初值存放 · 粮票'),
        ('.data · VMA', 775, 140, 'box', '运行位置 · RAM 住人'),
        ('.bss', 775, 280, 'box', '清零段 · 只分房不带行李'),
        ('heap', 775, 420, 'workflow', '_sbrk 向上长'),
        ('stack', 775, 560, 'cpu', 'MSP 向下长'),
    ],
    edges=[
        ('e', 'M259 450 H380 V170 H741', None, None, None),
    ],
    legend=[('.data 的双住址：>RAM AT> FLASH', '')],
    foot='符号留门牌：_sidata / _sdata / _edata 由脚本导出，Reset_Handler 按门牌干活 · 少写 AT>，bin 胀 134MB',
))

# ── 图 10 · F3 调度器结构 ───────────────────────────────
SPECS.append(dict(
    file='scheduler-structs', size=(1020, 660),
    title='调度器的家当：速查器、两条链表与 tick', kicker='御舆 MCU 书 · F3 调度器 · 配图',
    lede='位图置位 CLZ 秒选是优化路径，标量递减慢扫是通用路径；tick 三事：醒人、轮转、换片场。',
    groups=[
        (20, 80, 460, 210, '速查器 · 谁下一个上', 'list-tree', 'ga'),
        (540, 80, 460, 210, '链表两兄弟', 'workflow', 'gb'),
        (280, 350, 460, 220, 'tick · xTaskIncrementTick', 'cpu', 'ga'),
    ],
    nodes=[
        ('位图 + CLZ', 150, 140, 'binary', '优化路径 · 秒选'),
        ('标量递减', 350, 140, 'settings', '通用路径 · 慢扫'),
        ('就绪列表', 670, 140, 'workflow', '同优先级轮转'),
        ('延时列表', 870, 140, 'bell', '守时 · 到期唤醒'),
        ('tick 中断', 510, 420, 'cpu', '每个毫秒报到一次'),
    ],
    edges=[
        # tick → 延时列表：tile 右缘出（y=450），走廊横段 544..870 空，竖段 x=870 上行至延时列表 box 底+4
        ('n', 'M544 450 H870 V244', '守时唤醒', 720, 442),
        # tick → 就绪列表：box 左缘出（x=444, y=450），左走廊 x=350 上行至 y=330（G1/G3 之间空带），横段至 x=670 上行指就绪 box 底
        ('e', 'M444 450 H350 V330 H670 V244', '醒人 · 搬回就绪', 470, 322),
    ],
    legend=[('tick 到期唤醒主路', '')],
    foot='vTaskDelay 是挂表睡觉，不是原地死等 · 醒人、轮转、（必要时）换片场',
))

# ── 图 11 · P10 分区与 OTA 双槽 ─────────────────────────
SPECS.append(dict(
    file='ota-slots', size=(1020, 660),
    title='16MB 的版图：分区表、NVS 与 OTA 双槽', kicker='御舆 MCU 书 · P10 Flash/NVS/OTA · 配图',
    lede='分区表是地产证，NVS 是带掉电保护的抽屉，OTA 是双槽轮流坐庄——新固件不自证清白，旧槽随时复位。',
    groups=[
        (20, 80, 300, 490, '静态资产', 'database', 'ga'),
        (560, 80, 440, 490, 'OTA 双槽轮流坐庄', 'workflow', 'gb'),
    ],
    nodes=[
        ('分区表 CSV', 170, 140, 'list-tree', '地产证 · 16MB 户口本'),
        ('NVS', 170, 280, 'database', '磨损均衡键值库'),
        ('otadata', 170, 420, 'binary', '庄位记账'),
        ('Slot A · app0', 690, 140, 'box', '当前庄家'),
        ('Slot B · app1', 910, 140, 'box', '候选庄家'),
        ('新固件', 790, 420, 'file-code', '下载 · 验签 · 翻庄'),
    ],
    edges=[
        # otadata → Slot A：tile 右缘出，走廊 x=380 上行，横段至 Slot A tile 左缘 656
        ('n', 'M236 450 H380 V170 H656', '记账定庄', 505, 162),
        # 新固件 → Slot B：box 右缘出（y=450），横段 856..910，竖段上行指 Slot B box 底
        ('e', 'M856 450 H910 V244', None, None, None),
        # Slot A → Slot B：tile mid 水平直连
        ('e', 'M724 170 H876', 'OTA 写入', 800, 162),
        # Slot B → Slot A 回滚（虚线）：box 底出，下走廊 y=330，x=690 上行指 Slot A box 底
        ('n dash', 'M910 240 V330 H690 V244', '自证失败 → 回滚', 812, 322),
    ],
    legend=[('OTA 升级主路', ''), ('回滚保险', ' n dash')],
    foot='新固件不自证清白，旧槽随时复位 · NVS 带掉电保护',
))

for spec in SPECS:
    html = build_html(spec)
    out = os.path.join(ROOT, spec['file'] + '.html')
    open(out, 'w', encoding='utf-8', newline='\n').write(html)
    print('written', out)
