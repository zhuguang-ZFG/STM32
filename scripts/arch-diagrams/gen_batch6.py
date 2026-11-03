# -*- coding: utf-8 -*-
"""批 6 架构图生成器。铁律同前：边坐标逐条手工核算。
批 6 新增：tile dark（深底）表示断电域，由 build_html 注入 CSS。"""
import io, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = io.open(os.path.join(ROOT, 'boot-sequence.html'), encoding='utf-8').read()

DARK_CSS = '.tile.dark { background: var(--color-graphite); border-color: var(--color-graphite); } .tile.dark img { opacity: .35; }'

def group(x, y, w, h, label, icon=None, kind='ga'):
    img = f'<img src="%%ICON_{icon}%%" alt="">' if icon else ''
    return f'    <div class="group {kind}" style="left:{x}px; top:{y}px; width:{w}px; height:{h}px;">\n      <div class="g-label">{img}{label}</div>\n    </div>'

def node(name, cx, top, icon, role, dark=False):
    cls = 'tile dark' if dark else 'tile'
    return (f'    <div class="node" style="left:{cx-66}px;top:{top}px">\n'
            f'      <div class="{cls}"><img src="%%ICON_{icon}%%" alt=""></div>\n'
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
    html = html.replace('.tile img { width:34px; height:34px; object-fit:contain; }',
                        '.tile img { width:34px; height:34px; object-fit:contain; }\n' + DARK_CSS)
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

# ── 图 19 · J1 数据记录器：五站数据流 ───────────────────
SPECS.append(dict(
    file='logger-flow', size=(1020, 620),
    title='传感器记录器：从电位器到主机的五站接力', kicker='御舆 MCU 书 · J1 数据记录器 · 配图',
    lede='每一站的缓冲多大、锁持多久，都是设计决策：16 槽队列、4 帧槽、影子拷贝。',
    groups=[
        (20, 80, 980, 210, '采样到上报 · 数据主路', 'workflow', 'ga'),
    ],
    nodes=[
        ('ADC1 · PA0', 120, 140, 'radio', 'TIM2 TRGO 定时触发'),
        ('DMA2 S0', 310, 140, 'workflow', '双半字缓冲'),
        ('采样任务', 500, 140, 'cpu', 'IRQ56 通知唤醒'),
        ('样本队列 16 槽', 690, 140, 'database', '满则丢新并计数'),
        ('USART1 TX', 890, 140, 'cable', 'DMA2 S5 · 4 帧槽'),
        ('AT24C02', 500, 420, 'box', '配置双槽 · 页写 5-10ms'),
    ],
    edges=[
        ('e', 'M154 170 H244', None, None, None),
        ('e', 'M376 170 H434', None, None, None),
        ('e', 'M566 170 H624', None, None, None),
        ('e', 'M756 170 H824', None, None, None),
        ('n dash', 'M500 240 V416', '读配置 · 影子拷贝回写', 510, 330, 'start'),
    ],
    legend=[('数据主路', ''), ('配置通路', ' dash')],
    foot='影子拷贝原则：锁只覆盖读取-修改，不覆盖 5-10ms 页写 · 16 槽丢新样本是显式过载保护 · 原始 12 位码值未经 VDDA 实测不得声称校准电压',
))

# ── 图 20 · S14 三档睡眠的供电域矩阵 ────────────────────
SPECS.append(dict(
    file='pwr-domains', size=(1020, 760),
    title='三档睡眠的供电域：谁在睡时还活着', kicker='御舆 MCU 书 · S14 低功耗 · 配图',
    lede='深底=断电。Run 全活；Stop 停 1.2V 域时钟但 SRAM/RTC 还在；Standby 只留备份域——睡前遗言写在备份 SRAM。',
    groups=[
        (100, 80, 260, 630, 'Run · 全速', 'cpu', 'ga'),
        (420, 80, 260, 630, 'Stop · 1.2V 域时钟停', 'settings', 'gb'),
        (740, 80, 260, 630, 'Standby · 只留备份域', 'database', 'ga'),
    ],
    nodes=[
        ('CPU', 190, 140, 'cpu', '全速'),
        ('SRAM', 190, 280, 'memory', '192KB 全保留'),
        ('RTC', 190, 420, 'bell', '照走'),
        ('备份 SRAM', 190, 560, 'database', '4KB 可用'),
        ('CPU', 510, 140, 'cpu', '时钟停', True),
        ('SRAM', 510, 280, 'memory', '寄存器也保留'),
        ('RTC', 510, 420, 'bell', '唤醒源'),
        ('备份 SRAM', 510, 560, 'database', '4KB 可用'),
        ('CPU', 830, 140, 'cpu', '断电 · 复位式唤醒', True),
        ('SRAM', 830, 280, 'memory', '全丢', True),
        ('RTC', 830, 420, 'bell', '备份域 · 照走'),
        ('备份 SRAM', 830, 560, 'database', '1024 字守夜'),
    ],
    edges=[
        ('n dash', 'M334 170 H416', None, None, None),
        ('n dash', 'M654 170 H736', None, None, None),
        ('el a', None, None, None, None),
    ],
    legend=[],
    foot='唤醒矩阵：Sleep 任意中断 / Stop RTC·EXTI / Standby WKUP 引脚 · PWR_CR 关键位 LPDS·PDDS·DBP·FPDS（CMSIS 逐位核对）· 睡前先押个失忆：主 SRAM 和备份 SRAM 谁守夜',
))
SPECS[-1]['edges'] = [e for e in SPECS[-1]['edges'] if e[1] is not None]
SPECS[-1]['legend'] = [('睡得更深 →', ' n dash')]

for spec in SPECS:
    html = build_html(spec)
    out = os.path.join(ROOT, spec['file'] + '.html')
    io.open(out, 'w', encoding='utf-8', newline='\n').write(html)
    print('written', out)
