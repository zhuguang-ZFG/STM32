# -*- coding: utf-8 -*-
"""批 7 金句卡生成器：16 张（零改写，文字全部取自各章「一句话记住」原文）。"""
import io, os, re

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = ROOT
CSS_SRC = r'D:/Users/mcu/.temp/social-cards-2026-11-03/cards.html'

CARDS = [
 dict(sid='s2-rcc', chap='STM32 · S2', giant='先电压、再等待<br>后<span class="em">切钟</span>',
      rows=[('先','先降总线','再提主频'),('验','写完 SW','要看 SWS'),('倍','APB 分频不是一','定时器时钟自己乘二')], src='docs/stm32/02-rcc-clock'),
 dict(sid='s4-nvic', chap='STM32 · S4', giant='先 SYSCFG 选门<br>再 EXTI <span class="em">设沿</span>',
      rows=[('放','后 NVIC 放行',''),('清','ISR 进门先清挂起',''),('诀','四层口诀','中断永不丢')], src='docs/stm32/04-nvic-exti'),
 dict(sid='s14-pwr', chap='STM32 · S14', giant='Sleep 停脑<br>Stop 停钟（<span class="em">记忆在</span>）',
      rows=[('深','Standby 断电','只留遗言'),('配','唤醒源','睡前配'),('查','醒来','先查钟')], src='docs/stm32/14-pwr'),
 dict(sid='p3-idf', chap='ESP32 · P3', giant='组件<span class="em">自报家门</span>',
      rows=[('声','SRCS / INCLUDE_DIRS / REQUIRES','自报三项'),('变','Kconfig 三段变身','菜单→sdkconfig→sdkconfig.h'),('令','idf.py','只当司令不搬砖')], src='docs/esp32/03-idf-anatomy'),
 dict(sid='p8-wifi', chap='ESP32 · P8', giant='Wi-Fi 是<span class="em">状态机</span><br>事件循环是播报员',
      rows=[('联','GOT_IP','才算联网'),('备','DISCONNECTED','必须安排后路')], src='docs/esp32/08-wifi'),
 dict(sid='p10-flash', chap='ESP32 · P10', giant='分区表是<span class="em">地产证</span>',
      rows=[('存','NVS','带掉电保护的抽屉'),('升','OTA','双槽轮流坐庄'),('保','新固件不自证清白','旧槽随时复位')], src='docs/esp32/10-flash-nvs-ota'),
 dict(sid='f2-switch', chap='FreeRTOS · F2', giant='PendSV <span class="em">最后上场</span>',
      rows=[('存','r4-r11 手工进栈','栈顶藏进 TCB'),('换','换个指针换个魂',''),('新','异常返回','新人生')], src='docs/rtos/freertos/02-context-switch'),
 dict(sid='f5-sem', chap='FreeRTOS · F5', giant='同步二值 · 资源计数<br>保护互斥 · <span class="em">嵌套递归</span>',
      rows=[('钥','互斥锁出生带钥匙','被等就继承 · 还锁即回落'),('裸','二值信号量没有继承','拿它护数据等于裸奔')], src='docs/rtos/freertos/05-sem-mutex'),
 dict(sid='f6-notify', chap='FreeRTOS · F6', giant='通知写 TCB<br><span class="em">一步到位</span>',
      rows=[('栏','事件组','位公告栏'),('守','软定时器','住守护任务 · 回调里只办事不等待'),('清','清位','是汇总清，不是先醒者独占')], src='docs/rtos/freertos/06-notify-event-timer'),
 dict(sid='r2-ipc', chap='RT-Thread · R2', giant='一副骨架<span class="em">五张皮</span>',
      rows=[('五','令牌 · 带主令牌 · 旗语','定长池 · 变长队'),('排','排队要么 FIFO 要么 PRIO','创建时一锤定音')], src='docs/rtos/rtthread/02-ipc'),
 dict(sid='r4-device', chap='RT-Thread · R4', giant='驱动填表（ops）<br>应用<span class="em">喊名</span>（find）',
      rows=[('换','换板只换表','应用纹丝不动'),('价','解耦的代价是一张表','回报是整个生态')], src='docs/rtos/rtthread/04-device'),
 dict(sid='g1-rcu', chap='GD32 · G1', giant='先电压三件套<br>再 FMC 等待、<span class="em">后切钟</span>',
      rows=[('验','写完 SCS','看 SCSS'),('量','CK_OUT0 一量','自欺现形')], src='docs/gd32/01-rcu-clock'),
 dict(sid='b3-linker', chap='构建篇 · B3', giant='链接脚本不产代码<br>产三份<span class="em">地址契约</span>',
      rows=[('圈','MEMORY','圈地'),('房','SECTIONS','分房'),('牌','符号','留门牌')], src='docs/build/03-linker-script'),
 dict(sid='b4-startup', chap='构建篇 · B4', giant='上电两读定生死<br>开门搬家再<span class="em">清零</span>',
      rows=[('进','bl 一声进 main',''),('栈','向量表头不是代码','是栈顶'),('口','第二条','才是入口')], src='docs/build/04-startup'),
 dict(sid='b5-map', chap='构建篇 · B5', giant='Flash=text+data<br>RAM=<span class="em">data+bss</span>',
      rows=[('审','优化先审账',''),('排','nm','按大小排队'),('户','map','查户口本')], src='docs/build/05-map-size'),
 dict(sid='c7-ub', chap='C 语言精髓 · C7', giant='UB <span class="em">三兄弟</span>',
      rows=[('一','溢出','今天跑通不等于明天安全'),('二','移位',''),('三','别名',''),('规','加括号不丢人','显式转换不寒碜')], src='docs/c/07-ub-misra'),
]

TPL = '''  <div class="poster" id="card-{sid}">
    <span class="corner c-tl"></span><span class="corner c-tr"></span><span class="corner c-bl"></span><span class="corner c-br"></span>
    <div class="kicker">御舆 <span class="no">· {chap}</span></div>
    <div class="hr"></div>
    <div class="giant">{giant}</div>
    <div class="rows">
{rows}
    </div>
    <div class="foot"><span class="brand">一句话记住</span><span>{src}</span></div>
  </div>
'''

rows_html = ''
for c in CARDS:
    r = ''
    for mark, t, d in c['rows']:
        dd = f'<span class="d">{d}</span>' if d else ''
        r += f'      <div class="row"><span class="mark" style="color:var(--accent)">{mark}</span><span class="t">{t}</span>{dd}</div>\n'
    rows_html += TPL.format(sid=c['sid'], chap=c['chap'], giant=c['giant'], rows=r.rstrip('\n'), src=c['src'])

style = re.search(r'<style>[\s\S]*?</style>', io.open(CSS_SRC, encoding='utf-8').read()).group(0)
style = style.replace('.giant { font-size:76px;', '.giant { font-size:56px;')

page = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>御舆金句卡批 7 ×16</title>
{style}
</head>
<body style="padding:40px;display:flex;flex-direction:column;gap:40px;align-items:center;">
{rows_html}</body>
</html>
'''
io.open(f'{OUT}/batch7.html', 'w', encoding='utf-8', newline='\n').write(page)
print('batch7.html written,', len(CARDS), 'cards')
