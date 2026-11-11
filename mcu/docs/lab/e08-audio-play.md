---
title: 实验 E08 S3 音频链路放音
status: done
difficulty: 3
minutes: 60
code_status: ready
hardware_status: pending
code_note: 独立 IDF 音频工程，含 codec 与扩展器功放控制。
projects: ["esp32-05-audio-play"]

---

# 实验 E08 让 S3 开口：从正弦"滴"到一段音乐

> 🎯 这是立创 S3 的"加冕实验"：codec 配置、I2S 时序、DMA 缓冲，全部章节知识汇聚成一声清脆的"滴"——然后是第一段在你代码控制下播放的旋律。小智，从这一声开始。

## 实验信息卡

<LabStatus />

| 项 | 内容 |
|---|---|
| 编号 | E08 |
| 对应章节 | [P12 音频链路](../esp32/12-audio-path.md) |
| 目标板 | 立创实战派 S3 |

## 实验目标

- 现象：喇叭播放 1kHz 正弦"滴"声（1 秒），随后播放一段 8 音符旋律；串口打印播放进度。
- 能力：codec 初始化、I2S TX 配置、PCM 数据组织、缓冲深度与断音的关系。

## 装备

| 装备 | 数量 | 备注 |
|---|---|---|
| 立创实战派 S3 | 1 | 喇叭板载（1W） |
| Type-C 数据线 | 1 | |
| 耳机/示波器（可选） | 1 | 观察输出波形 |

## 原理一句话

I2S 把内存里的 PCM 样本按"位时钟×声道帧"的节奏推给 codec，codec 转成模拟电压，功放放大后喇叭发声：**你写什么波形，它唱什么歌**。

开播前先押耳朵的判断：DMA 缓冲一次次减半，第几次开始断音？断音是周期性的还是随机的？答案在喇叭里。

## 接线

板载全集成，零接线；引脚与 PCA9557 功放控制见下面的已核对接线说明。

![E08 音频链路：PCM 经 I2S（GPIO38/14/13/45）送 ES8311，再经功放到喇叭；I2C GPIO1/2 配 codec，PCA9557 bit1 开功放；下方为 Philips 帧](/images/labs/e08-audio-chain.svg)

控制走 I2C、声音走 I2S 的动态过程见 [P12 音频链路](../esp32/12-audio-path.md)。

## 步骤

1. 进入 `code/esp32/05-audio-play`，在 IDF 5.5.2 终端运行 `idf.py set-target esp32s3`、`idf.py build`、`idf.py -p COMx flash monitor`，COMx 换为实际串口。首次构建自动下载固定版本 esp_codec_dev 1.3.4。
2. 工程用 GPIO1/2 的 I2C 配置 ES8311，PCA9557（0x19）的 bit1 控制功放；不是直接拉高 ESP32 的 GPIO1。
3. I2S 使用 Philips 格式：16kHz、16bit、两个槽位各放同一份单声道样本；MCLK=4.096MHz，BCLK=512kHz。MCLK/BCLK/WS/DOUT 分别为 GPIO38/14/13/45。
4. 程序生成 1kHz 正弦播放 1 秒，再播放 8 个音符；串口显示音符进度，结束自动关闭功放。首尾有淡入淡出，无需下载音乐文件。
5. 完成基本验证后再研究 DMA 缓冲与断音；本示例不宣称已测出缓冲临界值。

板卡控制路径依据：[立创官方音频教程](https://wiki.lckfb.com/zh-hans/szpi-esp32s3/beginner/audio-output-es8311.html)。

## 预期现象

- "滴"声清晰无杂音；旋律可辨；
- 缓冲过小时出现断音，恢复后正常（缓冲/延迟关系亲测）。

## 实测记录

| 日期 | 板子 | 观测手段 | 结果 | 备注 |
|---|---|---|---|---|
| | | | | |

## 故障排查

| 症状 | 最可能原因 | 处置 |
|---|---|---|
| 完全无声 | PA_EN 没拉/codec 初始化失败 | 查使能脚与 I2C 应答 |
| 声音变调 | MCLK 与采样率不配 | 核对 256×fs |
| 杂音爆裂 | 缓冲下溢/位宽错配 | 加大缓冲；核对 16bit 对齐 |
| 声音极小 | codec 音量寄存器默认值 | 调音量寄存器 |

## 思考题

1. 16kHz 采样率对语音够用吗？电话音质 vs CD 音质的采样率差多少、为什么？
2. 如果要边采边放（耳返），单向缓冲与全双工缓冲的设计差在哪？

## 你做到了

- 音频链路全通，立创 S3 的"灵魂功能"归你指挥；
- 集 P 篇大成的一战：你离自己的语音终端只差应用层创意。

## 附录：工程完整源码

构建、接线与排查见[工程 README](https://github.com/zhuguang-ZFG/STM32/tree/main/mcu/code/esp32/05-audio-play)。

<<< ../../code/esp32/05-audio-play/main/main.c
