# 素材生成工具

本目录里画 SVG 和 GIF 的脚本只用 Python 标准库。
`gen_narrated.py` 是例外：海报要 Pillow，成片还要 edge-tts、ffmpeg，以及能访问微软语音服务的网络。
`assets/photos/` 的两张 CC0 实拍是带来源、许可和 SHA-256 记录的外部二进制资产，不由这些生成脚本重建。`make assets` 只重画海报，不重跑配音（在线语音不是逐比特稳定的）。

## 快速开始

```bash
python3 tools/gen_animations.py     # SVG 动画（CSS @keyframes / SMIL）
python3 tools/gen_boards.py         # 板卡实物结构图
python3 tools/gen_pinouts.py        # G0 / L4 / H7 引脚图
python3 tools/gen_diagrams.py       # 6 张静态框图
python3 tools/gen_gifs.py           # 6 个教学 GIF（ASCII）
python3 tools/gen_narrated.py --posters   # 每章讲解海报（需 Pillow）
python3 tools/gen_narrated.py --speak     # 配音 MP4 + SRT（还需 edge-tts、ffmpeg、联网）
python3 tools/check_assets.py       # 自检：SVG、GIF、实拍哈希、讲解 MP4、链接
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
| `anim_comm.py` | UART 帧、I2C 事务、SPI 移位、CAN 仲裁、USB 枚举、Ethernet/lwIP/MQTT 分层 |
| `anim_sys.py` | 定时器/PWM、定时器模式、SAR ADC、DMA 循环、看门狗、IAP、FreeRTOS、低功耗、L4 Stop 2 证据链与 RTOS 系统分层 |
| `gen_boards.py` | BluePill / BlackPill / Nucleo-F411RE / F4-Discovery / F103ZET6 大板 / LQFP48 引脚图 / 外设接线总览 |
| `gen_pinouts.py` | G071 / L476 / H743 的 LQFP 引脚图（脚序来自数据手册，不补脚） |
| `gen_diagrams.py` | 分层架构、工程目录、外设总线、中断优先级、L4 JP6 IDD 接线、网络排错阶梯 |
| `minigfx.py` | 位图绘制（含 5×7 点阵字体）+ **手写 GIF89a/LZW 编码器**（差分帧 + 透明索引） |
| `gen_gifs.py` | 6 个教学 GIF：LED 闪烁、PWM 呼吸灯、UART 逐位、I2C 时序、DMA 环形缓冲、SAR ADC |
| `gen_videos.py` | **已停用。** 五帧 ASCII 幻灯。`make assets` 不调用它。直接运行会写出 `assets/video/chNN-*.gif`（自检会失败），`--patch-docs` 会改写章节里的讲解视频。要重放旧幻灯才设 `GEN_VIDEOS_I_KNOW=1` |
| `narration.py` | 第 00–28 章的分镜、口诀和旁白稿，输出 `assets/video/chNN-*.mp4` |
| `narration_ai.py` | AI 续集分镜。`NARRATED_MODULE=narration_ai` 时输出 `assets/video/chsNN-*.mp4` |
| `gen_narrated.py` | 讲解 MP4：晓晓配音、烧录进画面的字幕、SRT、海报 |
| `svg2gif.py` | 把动画 SVG 采样成 `assets/gif/<名字>-zh.gif`（需本机 Chrome、Pillow） |
| `md2mp.py` | 把 `docs/NN-*.md` 和中文速查表转成公众号 HTML，写到 `wechat-mp/`（该目录不进 git） |
| `gen_mp_covers.py` | 从 `final-videos/` 的封面裁公众号头图，写到 `wechat-mp/covers/` |
| `gen_tietu.py` | 公众号竖版贴图，写到 `final-videos/`（该目录不进 git） |
| `gen_animations.py` | 动画总入口（自动跳过不存在的模块） |
| `check_assets.py` | 自检：SVG、教学 GIF 回验、CC0 实拍哈希/尺寸、正片 MP4、引脚图手册号、Wokwi/Renode 配置、Markdown 链接 |
| `ethernet_soak.py` | 共享单调截止点的 TCP echo 长稳探针，以及 close/stall/delay 故障注入对端；协议与 24 h 验收见 `labs/ethernet-24h/` |

`wechat-mp/` 和 `final-videos/` 在根目录 `.gitignore` 里。克隆下来的仓库没有这两个目录；要跑公众号脚本，先在本机准备它们的输入（封面在 `final-videos/`）。目录怎么分，见 [STRUCTURE.md](../STRUCTURE.md)。

## 设计约定

1. **自包含 SVG**：样式写在 `<style>` 里，动画只用 CSS `@keyframes` 或 SMIL，
   不含 `<script>`、外链资源、外部字体 —— 这样用 `<img>` 引用也能播放动画。
2. **深色卡片主题**：在 GitHub 亮色/暗色主题下都可读。
3. **教学 GIF 的文字只能是 ASCII**：`gen_gifs.py` 的位图字体只覆盖 5×7 英文字形。`*-zh.gif` 是 SVG 截帧，可以有中文，不要把它改回 ASCII。
4. **诚实标注**：所有图都是自绘/程序生成，页脚统一标注「自绘矢量图 · STM32 知识库」。

## 想加一张新图？

见 [CONTRIBUTING.md](../CONTRIBUTING.md) 第五节「新增一个动画的模板」。
