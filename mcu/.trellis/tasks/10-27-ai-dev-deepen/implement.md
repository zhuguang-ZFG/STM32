# AI 辅助开发内容加深 实施

## Phase 0 接线准备（实施时先核实）

- [ ] 核实 package.json 在线构建脚本名（docs:build 或类似）
- [ ] 核实 test_build.py:230/232/235 硬编码位置，改为从 manifest["parts"] 推导
- [ ] 核实 prose_guard.py 的 MARKERS/prose_surface 现状，规划单文件模式

## Phase 1 外部研究（librarian/检索）

- [ ] Copilot/Claude Code/Cursor/MCP 规范官方文档事实 + URL + 访问日期 → manifest.json sources
- [ ] RM0090 对账案例具体页码（RCC/GPIO 章节）

## Phase 2 试点章 A2（用户评审门）

- [ ] manifest.json：parts 插 pa、chapter_guides +A2、sources +研究产物
- [ ] docs/ai/02-manual-reconciliation.md 成稿（含尾部骨架：记忆锚点/一句话记住/下一站）
- [ ] ai-02-manual-reconciliation.svg 题花 + anim/ai-reconcile-loop.svg 内联图
- [ ] prose_guard 单文件模式跑通；art_guard 过
- [ ] **交用户评审，通过后才继续**

## Phase 3 批量成稿（两波）

- [ ] 波 1：A0 00-pair-not-ghost.md + A1 01-prompt-patterns.md（各含题花+anim）
- [ ] 波 2：A3 03-toolflow-mcp.md + A4 04-hallucination-defense.md（各含题花+anim）
- [ ] A5 05-this-book-pipeline.md（主线执笔，file:line 引证以当期仓库为准）
- [ ] chapter_guides 补齐 A0/A1/A3/A4/A5

## Phase 4 插图全套

- [ ] art.py part_art("pa") 新分支 + manifest×part_art 覆盖测试
- [ ] 6 枚章题花 ai-NN-*.svg 全过 art_guard
- [ ] 6 张 anim ai-*.svg 全过字体门
- [ ] 修 build_html.py:790 过时 docstring

## Phase 5 站点/前言/README 联动

- [ ] config.mts 侧栏 +第十一部
- [ ] 前言阅读图加 AI 辅助开发支线
- [ ] README.md 分部/章数计数更新（:12/:116/:141 等，成稿 94 章/11 部时统一改）
- [ ] 在线构建验证（脚本名以 Phase 0 为准）

## Phase 6 印前重建 + 全套电池

- [x] `python mcu-book/build_print.py`
- [x] `python mcu-book/check_pdf.py mcu-book/dist/mcu-deep-book-print.pdf`（13 门）
- [x] `.temp/widow_detect.py` 真寡行 0
- [x] `.temp/orphan_head_check.py` 0
- [x] U+2011 grep 0
- [x] 全书 `get_drawings()` 空内联灰点 0
- [x] `pytest mcu-book/tests/` 全过（67 + 新增）
- [x] `python mcu-book/tools/art_guard.py --dir mcu-book/book/assets/chapter-art`

## Phase 7 用户验收

- [ ] 插图生动度 + 文字详细度过目（对照附录 A/F）

## 实施实录（2026-10-27 收尾）

- 六章全绿成稿：A0 401 行 / A1 400 行 / A2 214 行 / A3 400 行 / A4 404 行 / A5 197 行（主线执笔）；口癖门独立复测全过。
- 起草代理四撞 15 分钟上限 → file-first 纪律入任务书；评审通道采纳 7 条驳回 3 条。
- 新增机器门：prose_guard --single（单章口癖）、test_part_art.py（部隔页覆盖）、assert_vector_art 改 SVG 域扫描（散文误报修复）、check_pdf 索引门补折行残片 skip。
- 印前新坑三连：circled 数字已证清白（保险集含之）；真凶=字体子集未含新章罕见字 → subset_fonts 重建 2080→2141 字；code 令牌 break-word 断片续行用 Consolas（Chromium 断片字体绑定怪癖）→ A3 例句改对齐 A2 雷例避开断词点。
- 字体来源登记：provenance.json 9 支字体子集参数全记录，重跑命令在会话历史可查。

## 实施实录（2026-10-27 有趣度增量）

- 干区外科润色 5 处：A0:313 选型段改「热度是别人项目的答案，工作形态才是你的问题」；A3:128 配置文件=授权表钩子、:130 排线意象替「三个 client 各管一条连接」、:306 四问清单=入职面试/发工牌、:324 填不出的格子=空白简历不录。步骤表/答案卡/记忆锚点/常见坑/技术契约零触碰。
- 验证链：prose_guard compare 两章「不可动清单：全部一致」（事实 token 多重集零漂移）+ single 口癖预算内；新字符 ⊆ 语料域（2102 字）零缺；docs:build ✓；pytest 72 passed；anim-lint 109/109；art_guard 100 枚 0 违规。
- 印前新坑四连（续前三连）：①其他任务未提交改动引入 庭/胆/讯 三字缺子集 → SimSun 回退（首见 36 页），子集重建 2144→2147 字解决；②`C:\Windows\Fonts\CascadiaMono.ttf` 名为 static 实为可变字体（fvar/gvar/cvar 在），provenance 漂移成 axes="static" 后子集未钉轴 → 全书代码（含行内 code）被 Chromium 嵌成无名 Type3（/DAAAAA+CascadiaMono-Roman，930/1168 页），重钉 wght=400/700 后回到 CascadiaMonoRoman-Regular/-Bold 的 Type0——与 10-25-book-production research/p2-findings.md:24 记载一致。13 门重建后全绿，寡行/孤儿/U+2011/灰点全 0。
- 快照留存：`.temp/interest-orig/`（A0/A3 润色前基线 + 语料域清单；docs/ai 未入 git，此为唯一 pre-polish 副本，勿清理）。
- 评审采纳 1 条：A3:328「第六章」→「第六节」（本章第六节收尾段的错误指称，其余 7 处引用均为第六节）；修后 compare/single/字符域复绿，docs:build + 印前重排 + 13 门 + 电池复跑全绿，PDF 内确认新文在、旧文无残留。
- 第二轮有趣度增量（A1/A4）：六章全量复扫后判 A0/A2/A5 与 A1/A4 节级意象已饱和，仅余三处扁平连接句——A1:224「措辞是天气，你要看的是地形」（与 :272 稳定读数呼应不抢戏）、A4:230 窗口意象「前四类各有一个窗口要跑…先问在不在，再问对不对」（总原则的口语孪生句）、A4:260「越往下越贵」替「顺手程度按序」（对齐表格成本列与 :256 用钱逻辑）。验证链同上全绿：compare ×2 一致、single 预算内（A1 ×1 / A4 ×1）、零新字符、docs:build ✓、13 门全过、电池全 0、pytest 72 / anim-lint 109 / art_guard 100-0，三句新文确认进 PDF。A1/A4 快照为本轮 pre-edit 基线（.temp/interest-orig/ 同目录并存）。
- 删脂一处（评审 advisory 属实）：A4 §二 178-183「三个工作推论」清单整块删除——180 复读 172（语气/精确=反指标）、181 近逐句复读 155（独立采样/判据到场/上次不担保）、178 连接语撞 172「两个机制合起来」；「语气不是证据」保留 :48 埋点与 :172 收束（埋点→收束更干净），常见坑 :356 复盘属坑体例不动。块内零受保护 token；删后 compare「不可动清单：全部一致」、single 预算内、零新字符；docs:build ✓、重排后 13 门全过、电池全 0、pytest 72 / anim-lint 109 / art_guard 100-0；PDF 确认块无残留且 :48/:172 原句仍在（首验 FAIL 系 PDF 断行伪迹，空白规范化后 PASS）。
- 第四轮（复读删脂，gates 盲区类）：`.temp/fat_scan.py`（句级 LCS≥10 近重复 + 「不是X，是Y」密度计数）跑六章，命中 111/69/27/172/52/5。逐条判读全部落入合法类：链接脚手架、技术标识符、来源卡套语（访问日期/能力描述）、坑·速查·自测体例复盘、A1 三段提示词 running example、A3 L14→L102 刻意变奏书挡（步骤数→谁打字快）；R3 所删 A4 块是唯一真赘块，本轮无新增。「不是X，是Y」密度 A0=14、A1=12 最高，26 处逐条判 25 处承重。唯一外科点 A0:315：一句双叠转，前转「不是行业默契的修辞，是…事实陈述」为填充且「独立来源互证」复述前句「互不隶属」→ 删弱留强「三个来源互相印证，这本身就是本章工作观的外部证据：结对而非代笔，不是本书的口味，是工具提供者自己写下的边界」。验证链：compare「不可动清单：全部一致」、single 预算内（——×2）、零新字符、docs:build ✓、重排后 13 门全过、电池全 0、pytest 72 / anim-lint 109 / art_guard 100-0、PDF 四断言 PASS（旧句无残留/新桥在/强转留/句头留）。task_verify：project-or-git-baseline-unavailable（docs/ai 未入 git），以书管线链为证。`.temp/fat-orig/` 为本轮 pre-edit 基线。
- R4 扫描器复验（advisory 两条均实证）：原版未剥 `[text](url)`/行内代码 → ~90% 命中为链接路径噪音；`abs(len差)>40` 过滤会吞掉「短口号↔长解释」类。修正 pre_clean（剥图片/链接留锚文本/删行内码）、删长度过滤、公共串须含 ≥2 CJK，重跑六章：命中 28/12/3/59/22/2（A3 余量主要为「能力描述，访问日期 2026-10-27」引证套语对）。逐对复判全部合法类：体例复盘、running example、母题与书挡、原理→实例阶梯、事实一致性短语；A0 L325↔L329 判为原理→实例（L329 含调度器机制与内存损坏结局等新内容）保留。结论不变：六章散文面零批量目标，R4 收敛成立。本轮仅动 .temp 扫描器与档案，无章节文本改动，验证链未重跑（无变更对象）。
- R5 插图生动化（文字面 R1-R4 判维护水位后，转向 Phase 7 验收面的插图半边）：题花密度对照全书范本（范本 1900–2600B，AI 六枚 890–1448B），判 A3（三管工具流）/A4（决策树）语义完备不动，A0/A1/A2/A5 扁平——缺章母题意象。四枚重绘（`book/assets/chapter-art/`，尺寸 1602/2029/2273/2069B 入范本带）：A0 分布钟形+不均采样→草稿纸→带勾放大镜→终审印章（虚线内环+按压放射线）；A1 夹板工单（上下文/约束/验收三行带勾）→齿轮机头带笔尖「模型」→带大勾草稿；A2 摊开手册（圈定位段行）↔断开式双向箭头+三问号+带勾放大镜「对账」→板卡（MCU 带引脚/LED/双表笔扎点，「实测」作板内丝印）；A5 双层传送带三滚轮：源文→闸门（双柱横梁悬带勾圆章）→带勾文档→闸门→成书（书脊书签带）。视觉核验：`:img` 光栅对透明底线稿画黑布（工具坑，记 failure）→ 白底临时副本+3 倍尺寸+纯黑描边光栅，视觉模型逐要素确认四枚无重叠/穿字/越界；A2 首核揪出箭头穿镜片与对勾交叉、实测标签位置不一致，修后复核通过。验证链：art_guard 100 枚 0 违规、anim-lint 109（未动复跑）、docs:build ✓、重排 1168 页字体全 Type0 具名、check_pdf 13 门「全部通过」、pytest 72 passed、PDF 断言 v3 全绿（get_toc 定位章页 + 题花字号带 5.9pt 判据，e06 未动题花 7.6pt 校准，A3/A4 对照组同过；首版断言全书任意页命中判空洞、二版标题搜索误中目录页，均按 advisory 收紧后废弃）。新标签字符全部 ⊆ 字体子集域 2260 字（含 ？）。文字面本轮复扫 A3 §二/§三与 A5 零干区、零改动（prose_guard 不适用，无变更对象）。基线：`.temp/art-orig/` 四枚 pre-redraw 快照保留勿清。
- R5b 几何对位复审（advisory bbox 算术判 R5 四枚有两类实缺陷，视觉模型二次确认不能替代包围盒计算）：①A0 放大镜悬空（镜片 x201–227 与纸 x124–190 间 11u 空隙）且终审章悬空盖空气（x249–275 与纸缘差 59u）——修法=删放大镜（对账镜归 A2 专用，消 2/6 枚母题重复），纸加宽至 x124–214，章加大 r15 压纸角（章缘 x199–229 与纸交叠 15u），视觉复核揪出纸右缘竖线从「终/审」两字间穿过 → 右缘在章覆盖段 y33–63 留缺口（切点正是章圆上下顶，虚线内环与二字全净）；②A5 全图零曲线（100 枚中唯一）→ 传送带改 C 弯带、闸门柱下沉 y68 种进带里、源文/带勾文档/书底边齐落带面 y66、补底部 signature 波（滚轮底 79 与波峰 86.5 净距 7.5）。③A3 判「语义完备」撤销：三管→三空白框不够具体且底波 M30 76 穿过串口日志框（y80.7 掠过 78–80 文字基线）→ 整体重绘为自转回环+齿轮模型（8 齿+轴心），三管线各接具体站点：上线入手册文档叠左缘、中线绕叠下缘上翘入构建终端左缘（首版中线 y44 横穿文档叠中心，视觉复核抓出后改道）、下线绕终端下方接方波左端，MCP 标签移至管线出口上方 (88,20)；④A4 判「语义完备」撤销：菱形+四个同构圆角矩形（字节大≠生动，art_guard docstring 自证「预算逼着曲线复用」）→ 重绘为真落差决策树：菱形抬升 y8–38、四分支自菱形下缘多点散出带下垂弧度（首版分支近乎水平被视觉模型读成「一条水平主线」，根因=叶子与菱形底同高零落差）、四叶子各异：摊开书（两页各两行文字线，删被读成残留的侧签）、两交叠纸、上升采样线+两采样点+探针圆骑线中点、圆播放钮；标签「抽样信」经正文 6 处用例证实为章内既定术语（非截断），保留。⑤教训：首轮几何断言 19 项全过仍漏两处穿线（A0 纸缘穿章字、A3 管穿文档叠）——bbox 断言须含「线段×矩形」「线段×文字」相交类，视觉复核是必要补位而非冗余。验证链（四枚修后全量）：bbox 断言 19 项 + 白底黑描边 3 倍光栅视觉复核三枚修点全过、art_guard 100 枚 0 违规、anim-lint 109、docs:build ✓、重排 1168 页 185.3×260.3mm 字体 5 支全 Type0 具名、check_pdf 13 门全过、pytest 72 passed、PDF 断言 v4 六章标签全命中（TOC 二级定章页 A0 p985/A1 p1006/A2 p1024/A3 p1034/A4 p1054/A5 p1073，字号带 5.9pt；v3 教训承袭：level-1 是部不是章，全书检索判空洞已废）。题花用字对 sans-regular woff2 cmap 直查：45 字全在域（域 2216），零缺字。prose_guard --single 六章口癖预算全绿（本轮零文本改动；误传多文件触发成对模式报红，实为调用错误）。⑥流程事故一枚：A3 重绘首写文件名调换（ai-03-mcp-toolflow.svg），构建按章节 slug 只读 ai-03-toolflow-mcp.svg → 孤儿文件使 art_guard 计数 100→101 暴露问题，归位后复 100。六枚 720×440 主插画盘点（advisory 优先级主张）：A1 弱提示↔三段式同任务对照、A2 四节点闭环带打回、A4 四类雷决策树、A5 八工序双列门、A3 架构图带「不再凭记忆编页码」逐服务器批注、A0 工具地图为节内生态图（章决定性时刻由「先跑起来」实验段+题花承载）——六枚各司其职，本轮判不动。
