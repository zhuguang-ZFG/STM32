# -*- coding: utf-8 -*-
"""批 4 架构图生成器：数据 → stack-diagram 源 HTML。
铁律同批 3：边坐标逐条手工核算（节点 132×100、tile mid=+30、肘形走廊走空带、
横边 tile 缘 ±34/4、竖边 box-bottom→tile-top / 反向终点 box底+4）。"""
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

# ── 图 12 · S4 中断四层关卡 ─────────────────────────────
SPECS.append(dict(
    file='exti-chain', size=(1020, 480),
    title='按键到 ISR：四层关卡依次放行', kicker='御舆 MCU 书 · S4 NVIC 与 EXTI · 配图',
    lede='先 SYSCFG 选门，再 EXTI 设沿，后 NVIC 放行，ISR 进门先清挂起——四层口诀，中断永不丢。',
    groups=[
        (20, 80, 980, 210, '从引脚到服务函数 · 四层关卡', 'list-tree', 'ga'),
    ],
    nodes=[
        ('SYSCFG', 130, 140, 'settings', '选门 · 引脚→EXTI 线'),
        ('EXTI', 390, 140, 'radio', '设沿 · 升/降/双边'),
        ('NVIC', 650, 140, 'list-tree', '放行 · 优先级 4 位'),
        ('ISR', 910, 140, 'file-code', '进门先清挂起'),
    ],
    edges=[
        ('e', 'M164 170 H356', None, None, None),
        ('e', 'M456 170 H616', None, None, None),
        ('e', 'M716 170 H876', None, None, None),
    ],
    legend=[('放行主路', '')],
    foot='寻址公式 IRQn/32 与 IRQn%32 · 优先级 4 位左移 4 位 · 写 AIRCR 必须带钥匙 0x5FA · HardFault 优先级不能设',
))

# ── 图 13 · P1 上电三棒接力 ─────────────────────────────
SPECS.append(dict(
    file='boot-relay', size=(1020, 620),
    title='上电三棒：ROM 认路、bootloader 验货、app 开工', kicker='御舆 MCU 书 · P1 S3 架构与启动 · 配图',
    lede='STM32 是一条直线，S3 是三棒接力——每棒交接都有仪式：验货、选槽、才交给 app。',
    groups=[
        (20, 80, 980, 210, '三棒接力 · 每棒有交接仪式', 'workflow', 'ga'),
    ],
    nodes=[
        ('ROM', 150, 140, 'cpu', '认路 · 烧死在芯片里'),
        ('bootloader', 500, 140, 'box', '验货 + 选货'),
        ('app', 870, 140, 'file-code', '开工'),
        ('分区表', 500, 420, 'list-tree', '地产证 · 选槽凭它'),
        ('main task', 870, 420, 'workflow', 'app_main 是它的一次调用'),
    ],
    edges=[
        ('e', 'M184 170 H434', None, None, None),
        ('e', 'M566 170 H804', None, None, None),
        # bootloader ↓ 分区表：box 底 240 → tile 顶 420-4
        ('n dash', 'M500 240 V416', '读地产证 · 选槽', 510, 330, 'start'),
        # app ↓ main task：box 底 240 → tile 顶 416
        ('n dash', 'M870 240 V416', 'app_main 返回即被回收', 880, 330, 'start'),
    ],
    legend=[('接力主路', ''), ('依赖关系', ' dash')],
    foot='与 STM32 对照：一条直线（Reset→main）vs 三棒接力 · 分区表布局写在 CSV，换布局不动链接脚本',
))

# ── 图 14 · G1 RCU 时钟树 ───────────────────────────────
SPECS.append(dict(
    file='rcu-tree', size=(1020, 620),
    title='RCU 时钟树：200MHz 是怎么算出来的', kicker='御舆 MCU 书 · G1 RCU 时钟树 · 配图',
    lede='时钟源倍频上 200MHz，再逐级分发给 AHB 与 APB——写完 SCS 看 SCSS，CK_OUT0 一量，自欺现形。',
    groups=[
        (20, 80, 980, 490, 'RCU · 让 200MHz 有据可查', 'workflow', 'ga'),
    ],
    nodes=[
        ('IRC16M / HXTAL', 150, 140, 'radio', '内部 16M / 外部晶振'),
        ('PLL', 400, 140, 'workflow', '倍频上 200MHz'),
        ('SYSCLK', 650, 140, 'cpu', '200MHz · SCSS 验收'),
        ('AHB 预分频', 900, 140, 'list-tree', 'HCLK'),
        ('APB1 · APB2', 900, 420, 'box', '外设时钟两级'),
    ],
    edges=[
        ('e', 'M184 170 H366', None, None, None),
        ('e', 'M466 170 H616', None, None, None),
        ('e', 'M716 170 H866', None, None, None),
        ('n', 'M900 240 V416', None, None, None),
    ],
    legend=[('时钟分发主路', '')],
    foot='切换顺序铁律：先电压三件套（LDOVS→HDEN→HDS 带回执）、再 FMC 等待、后切钟',
))

for spec in SPECS:
    html = build_html(spec)
    out = os.path.join(ROOT, spec['file'] + '.html')
    io.open(out, 'w', encoding='utf-8', newline='\n').write(html)
    print('written', out)
