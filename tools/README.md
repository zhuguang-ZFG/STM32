# 素材生成工具

本目录的脚本用**纯 Python 标准库**（零第三方依赖）生成 `assets/` 下的全部图片。
设计目标是：任何环境 `git clone` 之后都能一键复现素材，不需要装 PIL、ImageMagick 或浏览器。

## 快速开始

```bash
python3 tools/gen_animations.py     # 21 个 SVG 动画（CSS @keyframes / SMIL）
python3 tools/gen_boards.py         # 7 张板卡实物结构图
python3 tools/gen_diagrams.py       # 4 张静态框图
python3 tools/gen_gifs.py           # 6 个光栅 GIF
python3 tools/gen_videos.py        # 每章讲解幻灯 GIF（assets/video/）
python3 tools/check_assets.py       # 自检：SVG 合法性/超界/死类 + GIF 逐像素回验 + 链接校验
```

只生成某一个：

```bash
python3 tools/gen_animations.py gpio-blink     # 支持文件名或去掉后缀
python3 tools/gen_gifs.py led-blink
```

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `svgkit.py` | SVG 画布（`Svg`）、配色（`T`）、图元（`rect/text/arrow/waveform/box/chip/legend/header/footer`）与动画片段（`anim_blink/anim_flow/anim_tx/anim_draw/anim_width/smil_motion` …） |
| `anim_basics.py` | 工具链流程、启动流程、存储器映射、时钟树 |
| `anim_gpio.py` | GPIO 点灯、轮询 vs 中断、NVIC 中断流程、SWD/SWO 调试 |
| `anim_comm.py` | UART 帧、I2C 事务、SPI 移位、CAN 仲裁、USB 枚举 |
| `anim_sys.py` | 定时器/PWM、定时器模式、SAR ADC、DMA 循环、看门狗、IAP、FreeRTOS、低功耗 |
| `gen_boards.py` | BluePill / BlackPill / Nucleo-F411RE / F4-Discovery / F103ZET6 大板 / LQFP48 引脚图 / 外设接线总览 |
| `gen_diagrams.py` | 分层架构、工程目录结构、外设总线、中断优先级 |
| `minigfx.py` | 位图绘制（含 5×7 点阵字体）+ **手写 GIF89a/LZW 编码器**（差分帧 + 透明索引） |
| `gen_gifs.py` | LED 闪烁、PWM 呼吸灯、UART 逐位、DMA 环形缓冲、SAR ADC |
| `gen_videos.py` | 每章 5 帧讲解幻灯（ASCII 画面 + 章节旁白标记） |
| `gen_animations.py` | 动画总入口（自动跳过不存在的模块） |
| `check_assets.py` | 自检工具：SVG XML 校验、元素超界检测、动画 class 死链检测、GIF 解码逐像素回验、Markdown 链接与图片引用校验、体积告警 |

## 设计约定

1. **自包含 SVG**：样式写在 `<style>` 里，动画只用 CSS `@keyframes` 或 SMIL，
   不含 `<script>`、外链资源、外部字体 —— 这样用 `<img>` 引用也能播放动画。
2. **深色卡片主题**：在 GitHub 亮色/暗色主题下都可读。
3. **GIF 文字只能是 ASCII**：位图字体只覆盖 5×7 英文字形（中文讲解放在 SVG 与文档里）。
4. **诚实标注**：所有图都是自绘/程序生成，页脚统一标注「自绘矢量图 · STM32 知识库」。

## 想加一张新图？

见 [CONTRIBUTING.md](../CONTRIBUTING.md) 第五节「新增一个动画的模板」。
