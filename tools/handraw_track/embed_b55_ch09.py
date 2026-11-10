# -*- coding: utf-8 -*-
"""Embed ch09 B55 handraw knowledge-track PNGs (ZH+EN), bottom-up."""
from embed import embed_after_text

ZH = "docs/09-ADC与DAC.md"
EN = "docs/en/09-adc-dac.md"

# ---- ZH: insert 4 -> 1 ----
embed_after_text(
    ZH,
    "四种模式的区别是 ADC 什么时候停手。",
    "ch09-mode-stops.png",
    "Handraw：四种模式的停手点（原理示意）",
    "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：四条道从同一次触发出发——单次转一次就停、连续转完立即重启、扫描按 SQR 走完清单、间断走 n 个就暂停，最下面一条把扫描、连续与 DMA 循环叠在一起；证明什么：四种模式的差别只在「什么时候停、什么让它再开始」，与分辨率和采样时间无关；不能证明什么：不给出寄存器位值和通道顺序，也不是实测波形。出处：[RM0008](#source-rm0008-adc)。",
)
embed_after_text(
    ZH,
    "- [ ] 掌握 DAC 的输出模式、缓冲器开关对精度与噪声的影响。",
    "ch09-evidence-lanes.png",
    "Handraw：三份证据（原理示意）",
    "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：三条证据道——引脚上的输入电压、ADC 配置与状态（ADON/EOC、SMPR、ADCCLK）、内存里的码值数组（顺序、HT/TC、CNDTR），中间划掉的是「只打印一个电压」；证明什么：一个数分不开量化误差、源阻抗与缓冲区顺序，三条道各排除一类；不能证明什么：不能替代万用表或示波器，本身不记录任何实测。出处：[RM0008](#source-rm0008-adc)。",
)
embed_after_text(
    ZH,
    "ADC 时钟 12 MHz。出处是 [RM0008 Rev 21 第 11 章]",
    "ch09-tconv-floor.png",
    "Handraw：一次转换的 14 周期下限（原理示意）",
    "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：三道闸串联——ADCCLK 上限 14 MHz（这里 ÷6 得 12 MHz）、采样段要够采样电容充电（1.5 周期只有 125 ns，100 kΩ 源约需 7.8 µs）、再加固定的 12.5 周期转换段；证明什么：12 MHz 下最短一次转换是 14 周期，约 1.167 µs，继续削采样也到不了这个下限以下；不能证明什么：不是实测转换时间，也没有计入触发与 DMA 开销。出处：[RM0008](#source-rm0008-adc)。",
)
embed_after_text(
    ZH,
    "DS5319 写明中密度器件都有两个 12 位 ADC",
    "ch09-part-scope.png",
    "Handraw：三种型号的四行能力（原理示意）",
    "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：三列型号（F103C8 中容量、F103 大容量、F4）对四行能力——DAC 有无、转换加 12.5 还是 12 周期、上电是否要校准、有没有出厂校准值；证明什么：DAC 与校准两段只对带这些功能的型号成立，C8 上调 HAL_DAC_Start 没有输出；不能证明什么：不是选型表，也不是实测。出处：[DS5319](#source-ds5319-adc)。",
)

# ---- EN: insert 4 -> 1 ----
embed_after_text(
    EN,
    "The four modes differ in when the ADC stops.",
    "ch09-mode-stops.png",
    "Handraw: where the four modes stop (原理示意)",
    "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: four lanes leaving the same trigger — single stops after one conversion, continuous restarts at once, scan walks the SQR list, discontinuous pauses after n channels — and a bottom lane stacking scan, continuous, and circular DMA; Proves the four modes differ only in when the ADC stops and what starts it again, not in resolution or sample time; Cannot prove register bit values or channel order, and it is not a captured waveform. See [RM0008](#source-rm0008-adc).",
)
embed_after_text(
    EN,
    "- [ ] Know the DAC output modes, and how the output buffer changes accuracy and noise.",
    "ch09-evidence-lanes.png",
    "Handraw: three evidence lanes (原理示意)",
    "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: three evidence lanes — input voltage at the pin, ADC configuration and status (ADON/EOC, SMPR, ADCCLK), and the code array in memory (order, HT/TC, CNDTR) — with a single printed voltage crossed out between them; Proves one number cannot separate quantization, source impedance, and buffer order, while each lane rules out its own class of error; Cannot replace a meter or an oscilloscope, and it records no measurement. See [RM0008](#source-rm0008-adc).",
)
embed_after_text(
    EN,
    "ADC clock 12 MHz. Source: [RM0008 Rev 21 chapter 11]",
    "ch09-tconv-floor.png",
    "Handraw: the 14-cycle conversion floor (原理示意)",
    "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: the three gates in series — ADCCLK capped at 14 MHz (÷6 gives 12 MHz here), a sample segment long enough to charge the sample capacitor (1.5 cycles is only 125 ns, a 100 kΩ source needs about 7.8 µs), and the fixed 12.5-cycle adder; Proves the shortest conversion at 12 MHz is 14 cycles, about 1.167 µs, and that shortening the sample cannot go below that floor; Cannot give a measured conversion time and leaves out trigger and DMA overhead. See [RM0008](#source-rm0008-adc).",
)
embed_after_text(
    EN,
    "DS5319 says every medium-density device has two 12-bit ADCs",
    "ch09-part-scope.png",
    "Handraw: three parts, four capability rows (原理示意)",
    "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: three columns (F103C8 medium density, high-density F103, F4) against four rows — DAC present, conversion adder 12.5 or 12 cycles, power-up calibration, factory calibration values; Proves the DAC and calibration passages apply only to parts that have them, so HAL_DAC_Start produces no output on the C8; Cannot serve as a selection table, and it is not a measurement. See [DS5319](#source-ds5319-adc).",
)
