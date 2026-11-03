# -*- coding: utf-8 -*-
"""批 5 架构图生成器。铁律同前：边坐标逐条手工核算。"""
import io, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = io.open(os.path.join(ROOT, 'boot-sequence.html'), encoding='utf-8').read()

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
    html = re.sub(r'<span>[^<]*Boot 引脚[^<]*</span>', f'<span>{spec["foot"]}</span>', html)
    return html

SPECS = []

# ── 图 15 · F5 信号量与互斥量：同一底座的马甲家族 ────────
SPECS.append(dict(
    file='sem-mutex', size=(1020, 620),
    title='信号量 × 互斥量：同一底座的马甲家族', kicker='御舆 MCU 书 · F5 信号量与互斥量 · 配图',
    lede='semphr.h 没有函数，只有马甲：同步二值、资源计数、保护互斥、嵌套递归——差别全在继承与回落。',
    groups=[
        (100, 80, 380, 210, '信号量家族 · 无继承', 'list-tree', 'ga'),
        (560, 80, 380, 210, '互斥家族 · 优先级继承', 'settings', 'gb'),
    ],
    nodes=[
        ('二值信号量', 190, 140, 'bell', '同步 · 护数据=裸奔'),
        ('计数信号量', 370, 140, 'database', '资源计数'),
        ('互斥锁', 670, 140, 'settings', '出生带钥匙 · 被等就继承'),
        ('递归互斥', 850, 140, 'box', '嵌套 · 还几次拿几次'),
        ('Queue 底座', 510, 420, 'workflow', 'xQueue 骨架 · 创建即白送'),
    ],
    edges=[
        ('n dash', 'M190 240 V330 H480 V416', None, None, None),
        ('n dash', 'M650 240 V330 H540 V416', None, None, None),
        ('el a', None, None, None, None),
    ],
    legend=[],
    foot='互斥锁出生带钥匙（创建即白送一次 give）· 被等就继承 · 还锁即回落 · 二值信号量没有继承',
))
SPECS[-1]['edges'] = [e for e in SPECS[-1]['edges'] if e[1] is not None]
SPECS[-1]['legend'] = [('四件马甲 · 同一 Queue 底座', ' dash')]
SPECS[-1]['foot'] = '互斥锁出生带钥匙（创建即白送一次 give）· 被等就继承 · 还锁即回落 · 二值信号量没有继承'

# ── 图 16 · R4 设备框架：驱动填表，应用喊名 ─────────────
SPECS.append(dict(
    file='device-ops', size=(1020, 480),
    title='设备框架调用链：驱动填表，应用喊名', kicker='御舆 MCU 书 · R4 设备框架 · 配图',
    lede='驱动填 ops 表，应用按名 find——换板只换表，应用纹丝不动。',
    groups=[
        (20, 80, 980, 210, '四层调用链 · 解耦的代价是一张表', 'workflow', 'ga'),
    ],
    nodes=[
        ('应用', 150, 140, 'file-code', 'rt_device_find("uart1")'),
        ('rt_device', 420, 140, 'box', 'ops 指针 · register/find'),
        ('驱动 ops 表', 700, 140, 'list-tree', 'init/open/read/write/control'),
        ('硬件', 950, 140, 'cpu', 'UART1 实例'),
    ],
    edges=[
        ('e', 'M184 170 H354', '喊名', 269, 162),
        ('e', 'M486 170 H634', '调表', 560, 162),
        ('e', 'M766 170 H884', None, None, None),
    ],
    legend=[('调用链', '')],
    foot='换板只换表，应用纹丝不动 · 解耦的代价是一张表，回报是整个生态 · 软件包依赖 rt_device 接口而非具体硬件',
))

# ── 图 17 · S11 I2C 两线总线 ────────────────────────────
SPECS.append(dict(
    file='i2c-bus', size=(1020, 620),
    title='I2C 总线拓扑：两线开漏，各挂各的地址', kicker='御舆 MCU 书 · S11 I2C · 配图',
    lede='两根线挂一串设备：开漏所以必须上拉，地址各不相同所以能点名。',
    groups=[
        (20, 80, 980, 490, 'I2C 总线 · 两线开漏', 'cable', 'ga'),
    ],
    nodes=[
        ('主机 STM32', 150, 140, 'cpu', '出 SCL · 出/收 SDA'),
        ('两线总线', 480, 140, 'cable', 'SCL+SDA · 各一只上拉'),
        ('从机 A', 300, 420, 'box', '7 位地址 · ACK 点头'),
        ('从机 B', 660, 420, 'box', '另一个地址 · 各应各的'),
    ],
    edges=[
        ('e', 'M184 170 H414', None, None, None),
        ('n', 'M480 240 V330 H300 V416', None, None, None),
        ('n', 'M480 240 V330 H660 V416', None, None, None),
    ],
    legend=[('总线挂载', ' n')],
    foot='先 START 后地址，ACK 点头再继续 · 数据只在 SCL 低区变 · 清 ADDR 先 SR1 后 SR2 · 收尾 NACK 再 STOP',
))

# ── 图 18 · B5 size 公式与两块介质的账 ──────────────────
SPECS.append(dict(
    file='map-audit', size=(1020, 620),
    title='size 三列的账：Flash 与 RAM 各吃哪几份', kicker='御舆 MCU 书 · B5 map 与体积审计 · 配图',
    lede='Flash=text+data，RAM=data+bss——三列输入两条公式，账目一目了然。',
    groups=[
        (20, 80, 980, 490, 'size 三列 → 两块介质', 'binary', 'ga'),
    ],
    nodes=[
        ('text', 190, 140, 'file-code', '代码 + 常量'),
        ('data', 510, 140, 'database', '有初值'),
        ('bss', 830, 140, 'box', '零初始化'),
        ('Flash', 350, 420, 'binary', '= text + data'),
        ('RAM', 670, 420, 'memory', '= data + bss'),
    ],
    edges=[
        ('e', 'M190 240 V330 H350 V416', None, None, None),
        ('e', 'M510 240 V330 H378 V416', None, None, None),
        ('e', 'M544 240 V330 H654 V416', None, None, None),
        ('e', 'M830 240 V330 H686 V416', None, None, None),
    ],
    legend=[('账目汇入', '')],
    foot='优化先审账，nm 按大小排队，map 查户口本 · 四把刀按顺序用 · CCM 可腾挪大缓冲',
))

for spec in SPECS:
    html = build_html(spec)
    out = os.path.join(ROOT, spec['file'] + '.html')
    io.open(out, 'w', encoding='utf-8', newline='\n').write(html)
    print('written', out)
