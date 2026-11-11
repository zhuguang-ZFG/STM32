# 设计：88 章手绘题图流水线

## 1. 规格（试点 3 枚已评审冻结）

- 画布 `viewBox="0 0 320 88"` 横幅；元素 1-3 个；标签 ≤3 个，font-size ≥7，sans-serif
- 线宽：主干 2 / 细节 1.1；圆角 rect rx 2-7；箭头用两段式（干线 + 小箭头羽）
- 颜色一律 `var(--cover-ink, #123b33)`；**不写死色值**（暗色主题靠变量）
- 滤镜：`<filter id="hw-<章id>">`（feTurbulence baseFrequency **0.013** + feDisplacementMap **scale 3.2**，seed 用章号保留纹理差异），文字在滤镜组外。低频大幅抖动读作"手画的线"，高频小幅只读作"抖"——全册与封面/分部隔页同参数
- 结构断言（机器门）：viewBox 正确 + filter id 配对唯一 + 无 `<image>`/`<script>`/外链

## 2. 选题原则

题图是"题花"不是图解：取本章**一个**核心意象，一眼可辨即可，不承担教学。
优先级：机制符号（栈帧/波形/寄存器）> 物件（芯片/探头/线缆）> 抽象构图（箭头/循环）。
正文已有 109 张机制插图 + 13 张动画，题图不许复述它们的图，只许取"图标级"意象。

## 3. 分批与验收

- CA1（14 枚）：c/00,01,04,05,07,08 + build/00-07（02/03/06 试点已就位）
- CA2-CA9 跟随精修批节奏；每批渲染 contact sheet（题图+章题并列）给用户抽评
- 代理契约：只写 `mcu-book/book/assets/chapter-art/`；逐枚过结构断言脚本 `tools/art_guard.py`（待写）；每枚附一句"意象说明"
- 装一批重建一批：`build_html.py` 输出「题图 N/88」必须涨数

## 4. 意象分配表（CA1，其余批次照此格式续）

| 章 | 意象 | 元素 |
|---|---|---|
| c/00-c-in-mcu | 交叉编译：宿主机→箭头→芯片 | 笔记本轮廓 + 箭嘴 + 芯片 |
| c/01-memory-model | 五段内存条带 | 竖排 5 格条带标 FLASH/RAM/堆/栈 |
| c/04-struct-abi | 结构体填充空隙 | 三个不等宽格子 + 阴影填充块 + sizeof 标注 |
| c/05-func-pointer | 函数指针跳转表 | 表格数组 + 索引箭头跳进函数框 |
| c/07-ub-misra | UB 陷阱 | INT_MAX 悬崖边 + 警示三角 |
| c/08-framed-protocol | 帧结构 | 帧头/长度/载荷/CRC 四段条 |
| build/00-toolchain | 交叉工具链 | 扳手+螺丝刀交叉，一头 x86 一头 ARM |
| build/01-four-steps | 编译四步 | .c→.i→.s→.o→.elf 五格链 |
| build/02-elf | ELF 文件剖面 | 文件盒开盖露出段头表 |
| build/03-linker-script | 链接脚本图纸 | 图纸卷轴 + FLASH/RAM 两个分区框 |
| build/04-startup | 启动流程 | 复位按钮 → 向量表 → main 三连箭头 |
| build/05-map-size | map 审计 | 放大镜照 text/data/bss 三列 |
| build/06-flash-debug | 烧录调试 | SWD 两根线从调试器到芯片 |
| build/07-build-system | 构建依赖图 | 源文件→目标文件→固件的有向图 |
