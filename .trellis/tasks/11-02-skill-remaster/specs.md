# Specs：三 skill 全面改造书籍+视频质量

> 2026-11-02 立项。三个新装 skill：stack-diagram（架构图）、歸藏设计五件套（社交卡片/PPT/排版/去AI味/语气档案）、handraw-style（367 号手绘画风提示词库）。
> 目标：经典级、趣味可读、生动形象、简单易懂、过目不忘、由浅入深。
> 现状基线：批 1–10 趣味润色已闭环（78 章、137 md、1174 页 PDF、13 印前门全过）；video v2 remaster Wave C 在途。所有改造在基线上**叠加**，不回滚不重排。

## 0. 不可破坏的既有契约（改造红线）

| 红线 | 依据 |
|---|---|
| 书籍内页与封面**纯矢量/手工 SVG，无 AI 生图** | 10-26-cover-art PRD、纯矢量路线收敛（c6f133d） |
| 动画配色固定 #f6f8fa/#3451b2/#3eaf7c/#d97706，SMIL 四武器 | .trellis/spec/docs-site/content.md |
| 事实纪律：寄存器地址/引脚号必须 RM0090/CMSIS 二源核对 | content.md 事实纪律节 |
| 视频 v1 逐字节回归 + v2 schema 不许动 | .trellis/spec/video/v2-contract.md |
| 站点数字只走 progress.json 链路；docs:check CLAIMS 对账 | quality-contract.md |
| 章节 12 区块顺序、minutes 模型 ±40% | content.md 章节区块节 |

## 1. skill → 项目映射（能力盘点结论）

| skill | 能给项目什么 | 本环境可用性 | 落点 |
|---|---|---|---|
| **stack-diagram** | 白底瓷砖+官方 logo+正交连线的**静态架构图**（HTML→PNG @2x） | ✅ 全可用（Python+网络+Playwright 已备） | 站点+书内新增「架构图」图层 |
| **guizang-social-card-skill** | 小红书 3:4 图文组、微信 21:9/1:1 封面（HTML→截图） | ✅（需 Chromium，项目已有 playwright） | 视频传播物料 + 书籍金句卡 |
| **humanizer-zh** | 中文空话/模板腔/重复表达的**规则化审查器** | ✅（纯文本规则，无外部依赖） | 全书 78 章 + 18 集旁白复查 |
| **handraw-style** | 001–367 手绘画风**提示词**（需外部生图模型执行） | ⚠️ 只出 brief/提示词包，本环境无生图模型——诚实标注，不虚报出图 | 视频封面插画 brief（ai4fw 线及后续） |
| guizang-page-skill | 文档→精排单页 HTML/PDF | ✅ | 学习路径导读页（L3） |
| guizang-ppt-skill | 网页 PPT（杂志/瑞士风） | ✅ | 课程速览版（L3，可选） |
| guizang-voice | 语气档案（学习用户口吻） | ✅（需用户旧文样本） | 可选，待样本 |

## 2. 分级迭代计划（每级独立验收，逐级推进）

### L1 架构图层（stack-diagram）——书籍最大缺口 ✅ 2026-11-03 完成（批 1+2+3 共 11 张）

现状：动画管**动态因果**、题图管**情绪**，但「静态结构全景」没有专属图层——工具链四步、IDF 组件层次、WiFi 协议栈、内核宿主关系全靠文字。

- [x] 批 1（4 张）：`toolchain-pipeline`（B0）、`idf-anatomy`（P3）、`wifi-stack`（P8）、`rtos-side-by-side`（对比 0 五层解剖台）
- [x] 批 2（3 张）：`memory-map`（C1 内存地图，Flash/SRAM 双域+Reset_Handler 搬运）、`boot-sequence`（B4 启动五站）、`context-switch`（F2 换魂软硬分工）
- [x] 批 3（4 张，11-03 深夜）：`dma-paths`（S8 转运通路）、`linker-map`（B3 三契约·双地址连线）、`scheduler-structs`（F3 速查器/链表/tick）、`ota-slots`（P10 双槽轮流坐庄）——`gen_batch3.py` 数据驱动生成，**边坐标逐条手工核算**（第一版自动坐标连标签都叠，全部重算）
- [x] 批 4（3 张，11-03 深夜）：`exti-chain`（S4 四层关卡）、`boot-relay`（P1 三棒静态版图——P1 已有同主题接力动画，改插「和 STM32 对照」节做结构互补）、`rcu-tree`（G1 200MHz 时钟树）——`gen_batch4.py`
- [x] 批 5（4 张，11-03 深夜）：`sem-mutex`（F5 马甲家族·双族汇入 Queue 底座）、`device-ops`（R4 四层调用链）、`i2c-bus`（S11 两线开漏拓扑·总线扇出双从机）、`map-audit`（B5 size 三列两条公式汇入 Flash/RAM）——`gen_batch5.py`
- [x] 批 6（2 张，11-03 深夜）：`logger-flow`（J1 记录器五站数据流——项目篇首图）、`pwr-domains`（S14 三档供电域矩阵，tile dark 深底=断电域，与三档对比动画差异化）；S2/F6/A3 经查已有同主题动画**主动跳过**——为铺而铺的诱惑要挡
- [x] 批 8（4 张，11-03 午后）：`usart-rename-map`（G3 八串口两套牌·0x00–0x18 七条偏移轨）、`spl-anatomy`（S15 三板斧供料→GPIO_Init→四段寄存器落位）、`rtt-three-floors`（R0 三层楼·INIT_*_EXPORT 登记进对象容器）、`heap-free-list`（F7 空闲链表按地址排·相邻才拼）——`gen_batch8.py`；选型按「整章零配图」扫描，G3 是全书唯一无图成稿章，其余三张补静态结构（各自已有动画演过程）；首版 G3 按厂商拆上下两组框，下框左上角标签被 x=130 竖边穿过，改「整块对照框 + 每行行首厂商砖」后清
- [x] 每章正文插入 1 张 + 一句话引导，图注写「表达结构一句话」
- [x] 图内事实全部对账章节原文（NDTR/HIFCR、KEEP/AT>、CLZ 位图/延时列表、otadata 双槽回滚、四层口诀、三棒接力、LDOVS→HDEN→HDS、出生带钥匙/被等就继承、ops 表 init/open/read/write/control、数据只在 SCL 低区变、Flash=text+data）
- [x] 验收：docs:check ✓、reading:check ✓、docs:build ✓、test 116/116 ✓、**PDF 1188 页 13 门全过**（批 3 1183 / 批 4 1184 / 批 5 1188）；CLAIMS → 134 三处同步
- [x] 光栅预算门改真源公式：批 5 后位图 24 > 旧常数 20 报红——按 quality-contract「合理增长上调并说明」流程，`check_pdf.py` 的 RASTER_BUDGET 改为 `6 照片 + len(docs/public/arch/*.png) + 10 余量` 动态对账（架构图=注册位图源自动跟随；题图栅格化事故仍会爆红）；test_check_pdf 16 项全过

### L2 去 AI 味增量复查（humanizer-zh）✅ 2026-11-03 完成

现状：10-26-de-ai-polish 与批 1–10 已做过两轮，但 humanizer-zh 提供了第三方规则表，可查残留。

- [x] 31 条模式提炼为 19 个高信号正则，扫 78 章（去代码围栏）+ 18 集 narration：书 4 处「无缝」+ 旁白 1 处「无缝继续」
- [x] 逐条核对全部为技术语义准确用法（ABI 等价互换 / 中断返回继续 / 低功耗醒来保状态），按 skill §12「工程术语不因命中词表而删除」零修复；扫描脚本与结论存 `.temp/humanizer-scan/`
- [x] 验收：docs:check ✓、npm test 116/116 ✓（正文未改，prose 门状态不变）

### L3 传播物料（guizang-social-card-skill）✅ 2026-11-03 样张 4 + 批量 10，共 14 张，停机等目检

- [x] 书籍金句卡样张 3 张（小红书 3:4）：C3 volatile「把总线动作写进合同」/ B1「E·S·c·T 四步走」/ C1「一个全局变量的三段旅程」——文字全部取自各章「一句话记住」原文零改写
- [x] 视频推广卡 1 张（B站 16:9）：c3-volatile「你的 volatile 白加了？」Swiss 亮色版，与现有深底程序封面形成明暗两版对照
- [x] 批量 10 张（11-03 晚，goal 重发后继续）：C0「出错弹窗 vs 冒烟」、C2「指针三板斧」、C4「结构体罩寄存器」、C5「中断只做快递分拣」、C6「AAPCS 口诀」、C8「0 只当帧尾」、F0「一人阻塞全家堵」、B2「头说我是谁」、S7「起始拉低数据八位」、P2「专线与总机」——同款 Swiss 版式，`batch/batch.html` 单源生成
- [x] 批 7（16 张，11-03 深夜）：S2/S4/S14、P3/P8/P10、F2/F5/F6、R2/R4、G1、B3/B4/B5、C7——`gen_cards_batch2.py` 数据驱动，六条板线核心章全覆盖，产线移 `scripts/arch-diagrams/`（可复现）；入库 `deliverables/cards-batch7/`
- [ ] 用户目检 → 定发布平台与存放位置后入库正式区（现共 30 张：14 样张/批 2 + 16 批 7）；一屏联系表已备 `deliverables/review-sheet.html`（30 图全载、路径校验通过）
- [x] 验收（机械对账，脚本 `.temp/card-fidelity-check.py`，29 张 HTML 源逐片段回查章节正文）：**29 张 giant 主句全部原样命中**；9 处「行内小注」是卡面自造压缩短语（c3 三处 / b2 三处 / s7「帧格式」/ p3「自报三项」/ f6 去逗号），c3 样张钩子句截断——待用户拍板：A 放宽口径为「主句零改写、小注允许压缩」，B 逐张改回原句重渲
- [ ] 版式硬伤 3 张（截图逐张看到）：f0 三行重复「RTOS 三件宝」、c8 与 b2 的 mark 列按 1–2 字设计导致「序号/丢了/程序头」竖排拆字；批 2 源是一次性手写的 `.temp/social-cards-2026-11-03/batch/batch.html`，改后同目录 `shoot.mjs` 重渲
- [x] 验收：配色即站点色系（#3451b2/#3eaf7c/#d97706）

### L4 视频插画 brief 包（handraw-style）✅ 2026-11-03 完成

- [x] `video/assets/art-briefs/`：README 总纲 + 7 集 brief（ai4fw、s2/s4/s5/s7、s14、s16），每份含画风编号、核心特征验收清单、构图骨架、中英双语提示词（pure-image + 参考图隔离指令）
- [x] 明确标注执行需外部生图模型；SVG 手绘路线按「核心特征」清单直接自绘；品牌统一色 C-04 钴蓝（≈站点 #3451b2）
- [x] SVG 手绘路线落地（11-03 深夜）：7 集封面全部自绘完成——s2 六道门立柜 / s4 叠罗汉冷脸小豆人 / s5 怀表滴答 / s7 秒表对看 / s14 三张床 / s16 现场勘察 / ai4fw 几何机器；粗黑轮廓 14px + 钴蓝扁平色块 + 大留白 + 图内无文字（sweety 契约）；SVG 源 + 1920² PNG 在 `video/assets/art-briefs/covers/`，提交 786b9bf
- [x] 验收：三条路线（FA-013 涂鸦信息图 / FE-038 视觉双关 / FA-029 几何信息图）与 sweety-handdraw 白底黑墨线规范同源不冲突；图内文字极简契约写入每份 brief

### L5 精排导读 + 沉淀（guizang-page / specs 沉淀）✅ 2026-11-03 完成

- [x] 新图层规范沉淀：`.trellis/spec/docs-site/architecture-diagram.md`（动画/架构图/题图三分工、产图工作流、图标契约、CLAIMS 口径），已登记 spec 索引
- [x] guizang-page 精排单页：`docs/reference/book.md` → 瑞士风 + 品牌 #3451b2（忠实模式，gallery+checklist 标注零警告）→ `.temp/page-book-guide/book-guide.html`；learning-path.md 经查为 Vue 交互组件页不适合散文精排，对象改为书籍导读页
- [ ] guizang-voice 语气档案：待用户提供旧文样本后启用；精排页挂站点待目检

## 3. 执行顺序与停机点

L1 → L2 → L3（样张停机等目检）→ L4 → L5。每级完成后跑站点全量门（quality / docs:check / pytest / docs:build），全绿才进下一级。
