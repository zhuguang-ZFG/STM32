# 封面插画 brief 包（handraw-style 路线）

> 2026-11-03 由 handraw-style skill（001–367 画风库）产出。给「御舆」视频线的封面插画提供**可直接投喂生图模型的提示词**与**可自绘 SVG 时的风格规范**。

## 使用方法

- **有生图模型**：把对应 brief 的「中文提示词」或「English prompt」整段投喂即可；pure-image 模式，画风参考图路径已写在 brief 里（`images/individual/…`，位于 skill 安装包根）。
- **无生图模型（当前环境默认）**：把 brief 的「构图骨架」交给 SVG 手绘路线（sweety-handdraw 线），核心特征一节当验收清单用：粗黑轮廓/寥寥几笔/大留白等要素逐条对照。
- 品牌统一色：**C-04 钴蓝**（与站点动画主色 #3451b2 同族，封面与站点/书视觉同源）；点缀色 C-10 鼠尾草绿（≈站点强调绿 #3eaf7c）。

## 三条风格路线（审美推理结论）

| 路线 | 画风 | 为什么是它 |
|---|---|---|
| 涂鸦信息图（默认） | **FA-013** Jean Jullien · Bold Flat Everyday Satire | 粗黑轮廓+扁平色块+五官少而有力——与 sweety-handdraw「涂鸦信息图：白底、黑墨线、扁平色块、小豆人」同源，续作零风格漂移 |
| 视觉双关（单梗封面） | **FE-038** Tango · Minimal Visual-Pun | 寥寥几笔、大留白、看懂后一笑——适合「一图讲一个梗」的机制类单集（时钟门/节拍/睡眠档） |
| 几何信息图（盘点叙事） | **FA-029** Chris Ware · Geometric Diagrammatic | 几何精密线条+信息图式留白——适合多对象并置的盘点/对比（ai4fw 四框架） |

## 诚实边界

本包只产**提示词与风格规范**；出图需要外部生图模型。SVG 手绘路线不需要生图——brief 的核心特征即验收标准。所有 brief 均为 1920×1920 白底 PNG 规格、图内文字极简（真文字走 sweety 的 job text action，楷体），与 `video/` 的 lineart 精神一致：闭合区域、连续墨线、文字不穿线。

## 各集 brief

| 集 | 主题 | 路线 | 文件 |
|---|---|---|---|
| ai4fw | 369 个 AI 视频工具，这四个最能打 | FA-029 | [ai4fw.md](ai4fw.md) |
| s2-rcc | 168MHz 先 LATENCY 再切 SYSCLK | FE-038 | [s2-rcc.md](s2-rcc.md) |
| s4-nvic | 中断五幕戏，硬件排好 | FA-013 | [s4-nvic.md](s4-nvic.md) |
| s5-systick | 谁在给 RTOS 数毫秒 | FE-038 | [s5-systick.md](s5-systick.md) |
| s7-usart-baud | 波特率是算出来的 | FA-013 | [s7-usart-baud.md](s7-usart-baud.md) |
| s14-pwr | 三种睡眠三种醒法 | FA-013 | [s14-pwr.md](s14-pwr.md) |
| s16-hardfault | HardFault 法医开到行号 | FE-038 | [s16-hardfault.md](s16-hardfault.md) |
