# 成品书对照与本轮改进

核对日期：2026-11-21。对象是作者或项目维护者提供的在线正文、配套代码与原图，以下是抽样编辑判断，不是对整本书的评分。

## 可直接阅读的样本

| 成品与来源 | 本次实际查看 | 可借鉴之处 | 本书差异与处理 |
| --- | --- | --- | --- |
| [Bare Metal Programming Guide](https://github.com/cpq/bare-metal-programming-guide) | `Minimal firmware`、`Blinky LED`、`Blinky with SysTick interrupt`，以及逐步工程入口 | 每一步都承接上一份工程；构建、烧录命令紧贴当前可见结果 | 第 1 章先要求现成 ELF，却没说明如何获得；调整为先读随章记录，再给现有 probe 工程的复现入口 |
| [野火 STM32 库开发实战指南](https://doc.embedfire.com/mcu/stm32/f103zhinanzhe/std/zh/latest/index.html) | [GPIO 输出](https://doc.embedfire.com/mcu/stm32/f103zhinanzhe/std/zh/latest/book/GPIO_output.html)与[高级定时器](https://doc.embedfire.com/mcu/stm32/f103zhinanzhe/std/zh/latest/book/TIM_senior.html) | 点灯先给电路；定时器有接线、程序、下载验证、串口与示波器的对应关系 | 本书现有板上记录仍待完成。保留 pending，强化算例条件，不能用原理图冒充波形或把别书的实测当成本书证据 |
| [Rust Embedded Discovery](https://docs.rust-embedded.org/discovery/)、[Embedded Rust Book](https://docs.rust-embedded.org/book/) | Discovery 版本选择、micro:bit v2 版导言，以及 Embedded Rust Book 的先修说明 | 面向新手的 Discovery 与已有经验读者的参考书分流；开发板与先修要求明确 | 本书把入门、跨平台、来源历史挤在章首；第 1、10、12 章压缩入口，第 0 章给出第一次点灯的短路线 |
| [Hello 算法](https://github.com/krahets/hello-algo) | [数组](https://www.hello-algo.com/chapter_array_and_linkedlist/array/)的定义、连续地址、访问与插入操作；仓库的代码及图解说明 | 一个图解对应一个操作；索引、值、地址分清；图旁仍有可独立阅读的文字解释 | 现有内存图同时讲地址、堆栈、向量表与 ELF，中断图把文字写出卡片；重画成单一机制，大字标签配可追踪箭头 |

野火是中文板卡配套书，GitHub 两项是公开维护的完整阅读项目，Discovery 是嵌入式社区的课程型在线书；这些体裁不完全相同，比较以具体教学任务为准。没有按星标数或“手绘感”评分，也没有引入外部图片、代码或书稿。

访问记录：Hello 算法正文站点直抓遇到证书检查失败与 HTTP 429，改读[同项目数组原稿](https://github.com/krahets/hello-algo/blob/main/docs/chapter_array_and_linkedlist/array.md)；Discovery 当前入口指向 [micro:bit v2 版](https://docs.rust-embedded.org/discovery-mb2/)，并与 [Embedded Rust Book 导言](https://docs.rust-embedded.org/book/intro/index.html)核对受众与先修要求。ST 产品页直抓返回 HTTP 567，CAN 数量另以 [ST 官方 F103xB/C8 器件定义](https://github.com/STMicroelectronics/cmsis-device-f1/blob/master/Include/stm32f103xb.h)的 CAN1 定义复核；不把抓取失败算作外链通过。

## 图的实际改法

四张图沿用知识轨纸色与抖动轮廓，用清晰正体标注技术内容。技术标签约 18–30 px，来源说明单独放在底部；不修改共享画笔，避免整库插图跟着变化。

| 图 | 原问题 | 改后认知任务 | 图型与视觉登记 |
| --- | --- | --- | --- |
| `ch00-onramp-six-stops` | 原图把未配 Makefile 的例程写成 `make` / `make flash` 即可完成，与正文环境选择冲突；标签偏小 | 按 MDK / CubeIDE / PlatformIO 三选一建工程，再构建、下载、复位；保留点灯、串口与三样证据 | 六步蛇形流程；沿用既有蓝色知识轨与 1152×864 画幅；卡内技术标签由 15 px 放大到 18 px |
| `ch01-memory-two-addresses` | 十二个字节、堆栈、向量表、LOAD 同屏；正文连续三图解释同一段分配 | 跟同一个 `g_init` 看 Flash 初值经启动搬到 RAM，再区分 `.data` 搬运与 `.bss` 清零 | IG-004 双列对比 + 搬运箭头；沿用本仓库 Handraw 知识轨；普鲁士蓝、鼠尾草绿、琥珀；1152×864 |
| `ch10-exti-nvic-path` | 卡片末行落到框外；上半幅空置；优先级与请求链混在一张图 | 沿 PF6 → SYSCFG → EXTI → NVIC → ISR 找故障；把 IRQn、槽号、字节地址分别算清 | IG-008 流程步骤；沿用知识轨，蓝/琥珀/绿/红对应四环节；1152×864 |
| `ch12-counter-three-knobs` | 波形、捕获、输出位、时钟规则争夺注意力 | 同一时间轴对齐 CNT 与 PA6，直接看到 CCR 交点和占空比 | IG-002 中心标注 + 时序；沿用知识轨，绿计数/蓝输出/琥珀阈值；1152×864 |

第 2 章图中“内存屏障提供原子性”的说明同时纠正：屏障约束顺序，原子更新仍用适用的临界区或原子入口。

## 正文审校

Sepia review → refactor；作者模型未知，执行器 GPT-6（精确发行版未知）；prose layer 为 none / prior。以现有第 0、1、10、12 章及 CONTENT_GUIDE 为文体样本。命中密度、重复讲解、未定义缩写和绝对化条件，保留代码、冻结输出、来源与未实测状态。第 0 章的具体问题是入口先要求安装第一次点灯不用的命令行工具，主线被背景说明与后续排期打断。

- 第 1 章：先找一个变量的两个地址；缩写就地解释；合并重复判据；撤下两张相邻且重复的内存图引用；修正“越界必报错”的说法。
- 第 10 章：问题与导航缩短；解释输出列；明确 EXTI0 与 PF6/EXTI6 是不同算例；四环节专图不再混讲抢占。
- 第 12 章：把模式、正极性、公式与端点边界分开；图区分 84 MHz 算例与 16 MHz 工程默认值。
- 第 0 章：把第一次点灯所需步骤放在入口；先选用一种环境，GNU Arm + Make 后置到对应章节；消除“每个全局变量都有两套地址”的误导。按 ST 官方器件定义纠正 F103C8 的 CAN 数量（一路），并区分 STSW-LINK009 USB 驱动与 STSW-LINK007 固件升级工具。纸面抽查又发现旧开箱图仍要求 `make flash`，已同步改图。

新增内容执行删除检查；替换语句执行回退检查。保留技术所需条件，不为统一句长而改写。后续质量验收只记录本轮实际执行的结果，历史页数与门禁结果不自动沿用。

## 首批验收（追加补图前）

| 项目 | 实际结果 |
| --- | --- |
| 章目录、映射、教学合同 | `book.manifest --check`、`book.mapping --check`、`book.checks --check` 通过 |
| 文字机械检查 | 修改的第 0、1、10、12 章 `slop_lint` 通过；节奏另按上面的删除/回退检查复读 |
| 内容渲染与资产 | 53 页渲染通过，0 计划章缺失；555 个 public 资产检查通过 |
| 回归 | 104 项通过，无跳过；全局 Python 首次因沙箱拦截浏览器驱动报错，获准后以同一命令重跑通过；仓库内 `.venv-book` 的 104 项也已通过 |
| VitePress 站点 | 构建通过；54 页（含首页）与 manifest 一一对应，404 noindex 正常；14 个场景尺寸匹配；336 张图片均 lazy + async + 显式宽高 |
| 装配与冒烟 | 移除 223 个未引用构建资源（19.0 MB）；131 个历史跳转存根装配完成；剪枝后真实浏览器冒烟 10/10 通过 |
| 修改页的阅读检查 | 1280 px 桌面、390 px 手机 × 4 章共 8 页：文档与图片无横向溢出，目标图片全部可解码，图注与原图放大链接完整；抽看入口与图的截图 |
| 插图发布一致性 | 五个受影响图源重生成、发布后复查：missing 0、stale 0；四张图改构图或阅读路线，另纠正第 2 章一处图中文字 |

浏览器检查记录与截图在 `.temp/book-quality-20261121/`。本轮输出另存 `book/dist/quality-20261121/`，保留 `book/dist/print/` 的原有成品供比对。

### 成品与分页

完整书稿包含 47 章、6 附录。先全量生成印刷 HTML；纸面抽查发现开箱图与新正文不一致，修正图后用同一 `chapter_section` 渲染器重建第 0 章，断言除图片数据外该章文本完全一致。其余书稿及本轮已截取的动画静帧保持原样；873 个源输入在最后导出前后哈希一致。

| 验收项 | 原有成品（本轮重新扫描） | 本轮成品 |
| --- | --- | --- |
| PDF 页数 | 825 | 824 |
| 横向越界 / 孤立标题 / 孤立图注 / 近空页 | 0 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| 页底空隙 >150 pt | 147 页 | 147 页 |
| 页底空隙 ≥250 pt | 96 页 | 96 页 |
| 既有分页门 | ≤200 页 / ≤120 页 | 通过，未调整阈值 |

人工抽看新 PDF 的第 5、15、166、196 页：首次点灯路线、内存两地址、EXTI 路径及 PWM 波形；图注与对应图片在同页，技术标签可辨认。EPUB 含 64 个 spine 项、318 张图片，66 张 SVG 已转为 PNG；ZIP CRC、mimetype 及 67 个 XHTML/OPF/NCX 文档的 XML 解析通过，修改后的入口文字已进入成品。

| 文件（位于 `book/dist/quality-20261121/`） | 字节数 | SHA-256 |
| --- | ---: | --- |
| `merged-book.pdf` | 29,190,341 | `e10cc0f8006a646ac77bc2e4312161f770b5d68f16ba51d4ad253024b36ebe21` |
| `merged-book.epub` | 20,412,533 | `557c2caa550e8443ff772d7861cc2c4c597ff0824d7d1757eabcf59b04095f78` |
| `merged-book.html` | 28,518,200 | `9a77cb96619c736270572908543e86bda4d784c940b2ca40b34041ebad181013` |

首批未验证：未重新构建固件、未上板，未运行 EPUBCheck，也未在实体阅读器中检查 EPUB。VitePress 的 `ld` 高亮回退与 bundle 大小警告仍存在，不影响构建结果。以上成品记录截至追加补图前，不能作为下列新插图的成品验收结果。

## 追加 20 张机制图

针对“手绘太少”的反馈，扫描 manifest 的 47 章后新增 20 张图，分布在 19 章。与基线 `37498c8a` 相比，章内 Markdown / HTML 图片引用从 294 处变为 312 处：新增 20 处，首批去掉 2 处重复内存图。这个数字包含动画、技术图和照片，不等于手绘数量。暂存族按 SVG 实际清单为 64 → 84 张；修正了 README 原来写成 63 张的旧计数，未把其他 handraw、arch 等图族算进去。

新增图的源文件在 `assets/illustrations/staged/reading-pass/figures/`，生成器是 `tools/handraw_track/fig_reading.py`，PNG 合计 1,009,574 字节。发布器注册了新模块，既有回归检查同时覆盖新增图的源与发布目标。共享画笔 `hd.py` 保持原状。

### 视觉与点位登记

类型为知识教程，采用配图规划技能的机制图模式。风格沿用本仓库 Handraw 知识轨：以 #001 极简线稿的清晰轮廓为参考、C-22 普鲁士蓝为主色，配鼠尾草绿与琥珀表示不同对象或边界；1152×864，4:3。正文全部保留公式、代码、冻结输出、出处与待实测条件。以下每张图只补一个关系，均标注“原理示意 / 非实拍”；图注保留可脱图阅读的说明。

| 图名（省略 `.png`） | 正文点位 | 图型 | 读者应能看出的关系 |
| --- | --- | --- | --- |
| `ch00-swd-four-wires` | 第一次构建与烧录之后 | IG-002 中心标注 | 下载器四线与 F103C8 引脚对应；3V3 职能按下载器确认 |
| `ch00-uart-crossing` | 串口第一句话之后 | IG-002 中心标注 | TX/RX 交叉、共地与 3.3 V 电平 |
| `ch05-printf-hook` | newlib 钩子之后 | IG-008 流程 | 字节经过格式化与 `_write`，再选择硬件出口 |
| `ch06-size-two-budgets` | size 两条预算之后 | IG-004 双列对照 | `.data` 初值与运行值分占 Flash / RAM；292 B 与 44 B 可复算 |
| `ch07-header-dependency` | Make / CMake 机制之后 | IG-008 流程 | 头文件依赖沿边传播，漏边留下旧目标 |
| `ch13-frame-validation` | CRC 参数与算法之后 | IG-008 流程 | 帧尾之后仍要解码、查长度与校验；72 / 73 / 74 B 分开 |
| `ch14-two-completions` | UART / ADC 分工之后 | IG-004 时序对照 | DMA TC 与 USART TC 是两个完成边界 |
| `ch15-sampling-settle` | SMP 与 RC 算例之后 | IG-002 曲线标注 | 模型中 3 与 84 周期落在充电曲线的不同位置 |
| `ch16-jedec-byte-lanes` | 新的小节“W25Q64：读 ID 与写入边界” | IG-004 双泳道 | 9F 命令期间同时收到的第一字节应忽略，ID 从 rx[1] 起 |
| `ch17-parameter-erase-units` | A/B 参数备份规则之前 | IG-004 双列对照 | 同擦除单位内的两份记录无法互相保护 |
| `ch18-backup-power-island` | 备份域规则之后 | IG-002 中心标注 | VDD 与 VBAT 分域供电；F103C8 / F407 保留能力不同 |
| `ch19-debug-watchdog-freeze` | 调试器影响故障现场之后 | IG-004 时间线对照 | 调试冻结会造成“卡住却不复位”的假阴性 |
| `ch20-optimization-symbols` | 两份 nm 输出之后 | IG-004 双列对照 | 同带 -g3 仍会内联、改变尺寸与断点地址 |
| `ch22-delay-tick-phase` | tick 与延时表之后 | IG-004 时间线对照 | vTaskDelay(1) 受调用相位影响，到期就绪不等于开始运行 |
| `ch23-fpu-frame-cost` | FPU 行李之后 | IG-006 定量对比 | 基本现场 17 字、浮点现场 51 字，首帧 18 字另有对齐 |
| `ch24-fromisr-deferred-switch` | FromISR 规则之后 | IG-008 流程 | 入队与唤醒先记录，PendSV 等异常退出边界再切换 |
| `ch25-total-vs-largest` | 三种堆指标之后 | IG-002 条带标注 | 总空闲 1536 B 不代表有 1024 B 连续载荷空间 |
| `ch34-cache-line-neighbor` | Cache 故障分支之后 | IG-011 前后对照 | 整行 invalidate 可同时丢掉邻居未写回的更新 |
| `ch41-configure-save-reboot` | 配置机制与故障注入之后 | IG-008 状态流转 | 改 RAM、save 提交与重启加载有不同效果 |
| `ch45-first-failed-boundary` | 现象域分诊表之后 | IG-008 决策流程 | 按目标 ID、下载、Flash 启动逐项找第一处失败 |

逐张查看了 20 张渲染图，调整 5 张中的曲线标注、箭头与文字位置；SVG 文本边界检查无越界。新增图主标签 24–34 px，辅助条件 21–23 px，手写标题与正体技术标签分工。邻图间距按去代码、注释及空白后的字符数扫描，并检查间隔标题；把过近的构建图后移到 CMake 之后，A/B 图前移到备份规则之前，SPI 的 ID 事务增加独立小节。

不能声称全书已满足技能建议的每 1000–1200 字配图：部分长来源表、读数表与章末索引仍有数千字连续无图。新增主要针对可画出几何关系的机制，不给表格尾部堆装饰图。第 45 章最大无图跨度从 7047 降到 3777 个扫描字符，仍有后续空间；第 0 章从 5912 降到 4716。扫描记录在本地 `.temp/book-quality-20261121/illustration-inventory.json`，统计不包含站点运行时额外插入的场景图。

### 追加后的验证

- 暂存族 84 张全量重生成与逐字节发布检查通过：missing 0、stale 0；其他 191 张既有 PNG 不属于这个暂存图族，按发布器原规则报告为 note。
- Python 104 项回归、Node 32 项脚本测试通过，无跳过；manifest、mapping、章节合同、53 页渲染、575 个 public 资产与修改章的 slop_lint 通过。
- 站点 54 页、356 张图片的 lazy / async / 尺寸检查通过，14 个场景尺寸正确；131 个旧链存根装配后浏览器冒烟 10/10 通过。
- 新增 20 张图 × 1280 / 390 px 两种视口，40 次浏览器检查全部通过：图片解码、图注、放大链接完整，文档与图无横向溢出。
- 补图后的整书导出另存 `book/dist/quality-20261121-illustrated/`；最终分页与 EPUB 验收独立记录，不继承首批 824 页结果。GitHub 合并以本次质量 PR 的实际 CI 结果为准，保留原分页阈值与 MCU 历史状态。

## 仍需补齐的差异

- `examples/gpio-blink` 与 `examples/uart-dma-idle` 仍需按 README 建工程，尚未达到 cpq 各步工程直接 `make build` 的便利程度。本轮明确这个边界，没有把片段写成可直接构建的完整工程。
- 板上照片、示波器波形与原始日志仍需真实实验补齐；外书配图只能用于比较教学组织，不能作为本书实验的证据。
- 首批覆盖 4 章的阅读入口与 5 张既有图的调整，追加图覆盖 19 章；其余正文不代表均已完成人眼审校。长表与索引仍有连续无图区域，需要继续按具体认知任务补图与拆分阅读层次。
