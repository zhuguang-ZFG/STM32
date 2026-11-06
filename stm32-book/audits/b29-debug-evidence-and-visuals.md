# B29：调试现场、信号方向与可读插图

日期：2026-11-06（Asia/Shanghai）。承接 B28 工作树，用户明确授权多 agent 并行修改。继续推进全书优化；本轮处理第 17 章及第 16 章遗留图中文字。

## 改前诊断与分工

SEPIA REVIEW / refactor stage 1 — 技术教程；author=unknown，executor=GPT-6；prose layer：author=none，executor=prior。沿用 CONTENT_GUIDE、plain-voice、professional-pass、tech-articles、discourse §1–3、style-pass 与中文规则。具体缺陷在三份 `.temp/b29-ch17-*-review.md` 记录。

- 第 17 章原手绘只有比较器一张带生成源，其余五张为不可复现 PNG。比较器图堆叠提示框、同义警告与比喻，另有“第七个假装工作”等不准确表述。六个图位保留，各自承担比较器资源、现场保存、调试接线、观测代价、故障位与性能排查任务；统一沿用纸色、普鲁士蓝、鼠尾草绿、砖红和少量琥珀色。
- 旧 SWD/SWO 动画把 SWDIO 画成单向流，NRST 像连续数据，没有分清参考电压与供电。ITM 输出被写成自动 printf，DWT 与故障列表挤在接线图中。动画改为信号方向和单个跟踪字节的完整路径；打印与减少动态效果仍需完整可读。
- “条件断点”不能绕过六个 FPB 指令比较器的限额；DWT 数据观察点也不占 FPB 的六个代码比较器。BFARVALID 只表明 BFAR 保存有效地址，不能保证栈 PC 指向原始非法访问；IMPRECISERR 与入栈错误需要分别说明。
- 旧 sample-17 动画把 HardFault 判读与一次 DWT 测量串在同一因果链，只有 VALID=1，没有弃用地址分支。应先保存现场，再解码地址有效位；周期测量是独立任务。
- 第 16 章 sample 电流尺把 14.4 mA 标为运行，实际是指定条件下的 Sleep；BRR 原始值和解码后的 USARTDIV 写成等值。旧动画和静态图保留“Happy restore”“Motion advances”“Mechanism card”等制作说明。修正标签、补解码关系，图内写观察量与判断条件。
- 保留的 sample-17 对比/性能图仍有“SWO 无代价”“F1 无预取”“收益从大到小”“FORCED 且 CFSR=0 就查 VTOR”等混淆或无依据判断。按目标芯片和可复核证据修正，不虚构实际测量。

图型：比较与资源分配用 IG-004，现场判断用 IG-008，接线关系和周期测量用 IG-009；沿用 FA-002 知识轨。动画数量与图位不靠装饰增加，原图位按原序替换。

并行所有权：文字 agent 仅改双语第 17 章；插图 agent 仅改 fig_ch17 与六组手绘源/PNG；动画 agent 仅改 debug_swo 与对应 SVG；根 agent 处理旧 sample 图、共享登记、验证和成书。所有人保留他人修改。

Protected：公开标题、代码围栏、video/links 区、既有来源 ID/revision、关键参数与双语图片顺序。Deferred：未增加板上实测；暂停的视频与旁白流水线不动；不提交或发布。

此处仅为改前诊断，验证结果待实测后追加。

## 实施与交叉修正

- 三个 agent 完成正文、六张手绘和章首动画的独立修改。根 agent 整合并复核共享资产；另由插图 agent 只读交叉审查旧 sample 图。后续工具通道断流时，文件已落盘，根 agent 接续完成余下验证，没有把子任务状态当成通过证据。
- 六张既有 ch17 PNG 全部重画，补齐五份 SVG 生成源。六比较器改为取指地址匹配的实际资源关系；接线图补 GND、VTref、双向 SWDIO 与 SWO 返回方向；故障图以有效位分支、比例寄存器分区和测量窗口分别解释任务，避免套用重复的文字卡。
- `debug-swo.svg` 区分 SWD 调试信号和固件→ITM→TPIU→PB3→探针/主机路径。只用单字符 A 表示跟踪数据，不再展示虚构温度日志。复位线不是持续数据流；VTref 不是通用供电输出；printf 需重定向且输出有开销。
- 旧 Stop 与 CFSR 两张 sample 动画重画。前者依次等待时钟就绪、确认 SWS、再发送，附真实 BRR 换算；后者展示地址有效与无效两种出口，DWT 放在独立说明栏。动态点只表达先后，文字和箭头始终完整。相应两个 GIF 改浅色、六帧与放大的状态字，去除制作说明，CFSR 和 DWT 并排呈现。
- 修正八张旧静态 sample 图及故障阶梯中的文字：Sleep 14.4 mA 标签；BRR raw=625、USARTDIV=39.0625；DWT 与 FPB 独立资源；软件断点不保证无限/自动替补；SWO 配置、F1 Flash 预取、同条件性能比较、volatile 不提供同步；地址有效性与栈完整性分别核对。
- 交叉审阅发现五处图形/语义问题后修正：DWT 差值箭头覆盖两次读数；PC 偏移写成选定 frame+0x18；STKERR 提醒移出仅无效地址分支；取消 Stop 阶段轴上的伪 0/5.4 µs 刻度；查看器填写的是目标内核频率，Flash 软件断点需具体工具支持。又修正故障阶梯的“置位后才读取”为“置位才使用已保存地址”。
- 双语正文以可观察 DWT 对照开头，精简模板图注；保留 15 个图片位置与原有顺序。代码、公开标题、来源 ID 与暂停的视频旁白不改；对代码缺少 naked 入口、栈检查、跟踪初始化及故障时 printf 的边界在相邻正文说明。未将这些代码标为可直接部署的故障记录器。

## 官方核对

- 真正的 RM0008 Rev21，本地 `.temp/rm0008b.pdf`，1136 页；物理 p1096 §31.12：2 literal + 6 instruction FPB comparators，补丁与断点用途互斥；p1097 §31.13：4 DWT comparators，独立于 FPB。p176–177、1080、1105–1108：SWJ 引脚、ITM/TPIU、异步 trace 的 Serial Wire 模式与 TRACE_IOEN/TRACE_MODE、PB3、HCLK 条件。SHA-256 沿用 B28：`4c1b8ac2729cc1f45a4685eea9e91e6139e24e58804fba21e27201dfcc2ad149`。
- 真正的 Arm Cortex-M3 Devices Generic User Guide，ARM DUI0552A，`.temp/b27-arm-dui0552a.pdf`，180 页；p151–153：BFSR/MMFSR、PRECISERR/IMPRECISERR、stacking 边界；p158 §4.3.15：先保存地址再读取对应有效位，避免更高优先级异常更新。SHA-256：`ced76c9595765af20cbe66f76eaa4c653cdd8cd935c46c8032366348d0dd90a5`。未使用同目录假 PM0056 挑战页作为验证依据。

## 已完成的验证

- 六张手绘 SVG 再生成 SHA-256 一致；六张 PNG 由 agent 逐张目视，根 agent 抽看故障位图和接线图。六图 Chromium 实际文字几何为 0 缺陷。
- 根 agent 的 10 张 sample 图初次及修正后的目标图均检查无裁切/文字重叠；故障阶梯另检查通过。全轮不同 SVG 共 18 份。SVG 文本快照与双语图注登记集中同步。
- `verify_b29_debug_swo.py`：五个跟踪节点位置，screen/reduced/print，静态独立/嵌入逐像素一致。`b29_verify_media.py`：八组时点，两种 VALID 分支，screen/reduced/print 与嵌入静态像素一致；九张静态 sample 图已渲染（含交叉审查的故障阶梯）。截图中的箭头和位宽条件已目视复核。
- `verify_b29_gifs.py`：两 GIF 各六帧、480×300；全部帧解码与生成像素一致，222 个文字框未重叠/裁切，没有缺字。根 agent 目视两张六帧合成图。帧时长分别 900 ms / 700 ms，只表达顺序。
- `slop_lint.py` 无机械命中；14 份改动章节代码/视频/显式来源锚点对 HEAD 保持。ch17 另逐项核对公开标题、来源 ID、接线表和双语 15 图序均保持。
- `check_assets.py`：426/426 SVG 合法，2014/2014 本地链接有效，GIF 解码一致；视频/字幕和照片原合同通过。海报像素比较因未安装指定 Linux 字体跳过，不列为本轮完成项目。

首次全套回归共 189 项，188 项通过，SVG 合同检查发现两张重画 sample 动画漏了“自绘矢量动画”标识。补齐生成源和 SVG 页脚后，复测又定位到两份已重做 GIF 的汇总快照尚未登记；仅更新这两份已逐帧验证资产对应的汇总摘要，没有删减断言。SVG/GIF 合同单项现已通过；动画的八组时点、两种分支和 screen/reduced/print 嵌入像素复测通过，补齐后的页脚无裁切或重叠。

完整回归和双语成书已按修正后的源重新运行，最终结果如下。

- 完整 `unittest discover -s stm32-book/tests -v`：189 项全部通过，364.303 s。
- 双语最终 HTML：中文 133,730,274 字节，英文 133,824,841 字节；390 px 手机视口均为 0 横向溢出、0 文字 Range 越界，第 17 章 17 个图位全部加载。每版 561 图注、162 个图注链接，未残留原始 Markdown。
- 双语最终 PDF：中文 570 页、116,256,403 字节，英文 606 页、116,792,343 字节；两个构建退出码均为 0。中文物理 p297/298/300/310、英文 p315/316/318/329 找到四组更新后的正文/图注，链接和图像对象存在。根 agent 目视中文 p298 和英文 p316，插图、图注、正文、页眉和页码完整，无裁切。
- 成品检查报告：`.temp/b29-final/inspection.json`；本轮未提交或发布。用户随后要求继续，下一轮在此成品之后推进第 18 章 FAQ。
