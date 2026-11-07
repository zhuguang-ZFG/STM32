# 第四批阅读证据与方向样例

状态：仅规划。以下七个样例是供用户审阅的方向，不是最终候选或已实施正文；docs原文未改。准确来源SHA与原句见source-evidence.json。

## 阅读诊断

SEPIA REVIEW — 中文嵌入式教程，本仓B篇

- Loaded: professional-pass、tech-articles、discourse-pass §1–3、style-pass（不采用小说词表）、zh、GPT prose-layer priors。
- Model: author=unknown；executor=GPT-6.1 Sol（宿主模型标识zg-newapi/gpt-6.1-sol）。Prose layer: author=none；executor=prior，无匹配此版本的operative表；不从文风推断作者模型。
- Venue corpus: 本仓已接受的B3:236/240、B4:98/124。它们提供“先说观察对象、保留工程口语”的风格，不证明作者身份或事实正确。
- Failed #2 density: B5:18“为什么……；为什么……”把两个学习问题挤在一行；47中后续需求与章节去向连续叠放。
- Failed #5 specificity: B5:15括号内才说明区块用途；35“一目了然”未把工具与当前问题对应；B6:50“走过的链路”缺具体读图动作。
- Failed #10 fluency: B6:101“monitor 前缀是发给 OpenOCD 的命令”主宾不对应；B6:19“常驻 + 连上”的加号隐藏了次序。
- Style scan §2–3: 处理上述对象、主语与回指，不替换作者“三板斧/户口本”等常用比喻。§5 rhythm: 未据独立的等长句群诊断整章节奏问题；长句占比不是AI归因证据或改写目标。
- Protected: B5:89/91/93/97的推论与排序，B6:59–66/70–82/96–112的协议、烧录和断点结论等按design冻结；不借语言诊断宣布技术错误。
- Passed: 1、3、4、6、7、8、9（本批白名单范围；章节固定区块与真正可枚举条目豁免，不对全书泛化）。
- Verdict: isolated hits → 七处最小改写；不全章重构。

## 观测指标

| 章节 | 句数 | 长句占比 | 平均句长 |
|---|---:|---:|---:|
| B5 | 96 | 8.3% | 32.1 |
| B6 | 84 | 15.5% | 40.2 |

来自现有scripts/prose-readability.mjs的metrics()，只读调用，未更新基线。长度不是通俗程度验收，也不设本批目标百分比。

## B5-A · docs/build/05-map-size.md:15

原句：

```markdown
2. map 文件的三板斧：Archive member 表（谁被从库里捞出来）、Memory Map（每个符号的落位）、 discarded 段（被 gc-sections 辞退的）。
```

卡点：区块用途藏在三组括号中；读者知道三个名字，但需要把名字和要查的问题重新配对。

方向样例：

```markdown
2. map 文件的三板斧各查一件事：Archive member 表查谁被从库里捞出来，Memory Map 查每个符号的落位， discarded 段查谁被 gc-sections 辞退。
```

编辑动作：用原有三板斧顺序直接说各查什么，不新增Archive/GC证据或调用关系结论。

理解收益：读者能指出“查引进谁/落哪/丢谁”分别看哪个区块。

## B5-B · docs/build/05-map-size.md:18

原句：

```markdown
- **能理解**：为什么带初值的数组让 Flash 和 RAM 双涨、加 const 后 data 回落 text 涨；为什么 bin 比 text+data 大。
```

卡点：两个为什么挤在分号两边，第一组又有数组、const、data/text多个对象。

方向样例：

```markdown
- **能理解**：解释为什么带初值的数组让 Flash 和 RAM 双涨，加 const 后 data 回落、text 涨；再解释为什么 bin 比 text+data 大。
```

编辑动作：标明先解释第一组现象，再解释bin的另一组问题；不改其原有结论或加入单位数字。

理解收益：学习目标变为两个可复述的问题；不让读者把bin体积问题和data归属混成一个原因。

## B5-C · docs/build/05-map-size.md:35

原句：

```markdown
`size` 一行三列就把 Flash/RAM 占用算清；`nm --size-sort` 把符号按体积排队，最大几个一目了然；`map` 的 Discarded 段告诉你 gc-sections 辞退了谁。
```

卡点：读完三条命令后，三个“就清楚/一目了然”仍未明确何时选哪个结果。

方向样例：

```markdown
`size` 的三列用来算 Flash/RAM 占用；要找体积最大的几个符号，就看 `nm --size-sort`；要查 gc-sections 辞退了谁，就看 `map` 的 Discarded 段。
```

编辑动作：保留size/nm/map三个行内片段及顺序，将“要查什么”与观察对象对应；不添加输出精度或排序方向。

理解收益：初次审计时能按占用/大符号/丢弃段定位现有命令，而非记三把刀的标签。

## B5-D · docs/build/05-map-size.md:47

原句：

```markdown
**map 分析的下游应用**：审计完体积，下一步通常是"Flash 不够装"或"要做 IAP 双区"，这时回看 [S13 Flash 与 IAP](../stm32/13-flash-iap.md) 的分区布局，以及 [B3 链接脚本](03-linker-script.md) 的段排布。map 文件告诉你"现在住哪"，链接脚本决定"将来搬哪"。
```

卡点：后续需求、两个章节链接和现在/将来两种任务挤在同一串过渡中。

方向样例：

```markdown
**map 分析的下游应用**：审计完体积，遇到"Flash 不够装"或"要做 IAP 双区"，就回看 [S13 Flash 与 IAP](../stm32/13-flash-iap.md) 的分区布局，以及 [B3 链接脚本](03-linker-script.md) 的段排布。这里分清两件事：map 文件告诉你"现在住哪"，链接脚本决定"将来搬哪"。
```

编辑动作：两个既有需求仍指向S13/B3，链接顺序不变；明确查现状与改布局两件事，引号内原文原样保留。

理解收益：读者知道审计后的问题为什么需要回看分区布局和段排布，避免把map当成修改布局的工具。

## B6-A · docs/build/06-flash-debug.md:19

原句：

```markdown
- **能用**：OpenOCD 常驻 + GDB 连上，完成 halt/load/读写内存/单步/断点一整套调试流。
```

卡点：“常驻 + 连上”把先后藏在加号里，后面动作密集并列。

方向样例：

```markdown
- **能用**：先让 OpenOCD 常驻，再用 GDB 连上；随后完成 halt/load/读写内存/单步/断点这一整套调试流。
```

编辑动作：将前两项写为先/再，其余调试流用原顺序保留；不补新的连接/复位步骤。

理解收益：读者先知道哪一个程序常驻、哪一个程序连入，再看本章已有操作清单。

## B6-B · docs/build/06-flash-debug.md:50

原句：

```markdown
一条命令（如 `x/4xw 0x20000000` 读 RAM）走过的链路：
```

卡点：“走过的链路”只宣告有一张图，没有说明要沿图观察什么。

方向样例：

```markdown
以 `x/4xw 0x20000000` 读 RAM 为例：从左边的 GDB 开始，沿箭头看到最右边的内存地址：
```

编辑动作：只引用既有读RAM命令并指定从左到右读现有箭头；不声称GDB直接产生SWD包。

理解收益：读者带着命令和目标地址看图，而非先记八个名词；该行不替后文协议职责背书。

## B6-C · docs/build/06-flash-debug.md:101

原句：

```markdown
`monitor` 前缀是发给 OpenOCD 的命令（reset/flash/sleep）；不带 monitor 是发给 GDB 自己的（break/x/continue）。区分这条线：`monitor reset halt` 是 OpenOCD 让芯片复位停住，`break main` 是 GDB 设断点。
```

卡点：“前缀是……命令”主语和宾语不对应；“区分这条线”回指抽象。

方向样例：

```markdown
带 `monitor` 前缀时，命令发给 OpenOCD（reset/flash/sleep）；不带 monitor 时，由 GDB 自己处理（break/x/continue）。对照这两个例子：`monitor reset halt` 是 OpenOCD 让芯片复位停住，`break main` 是 GDB 设断点。
```

编辑动作：用带/不带前缀对应接收对象，之后沿用两条例子；三个行内代码片段顺序不变。

理解收益：读者能区分命令由OpenOCD还是GDB处理；不在这里改变break类型或回退判断。

## 冻结与验证边界

完整待核表见design.md。原句与样例均不意味着技术事实已核实；未查询上游手册、未运行章内shell/调试/烧录命令，也不对硬件现象作保证。若改善解释必须跨入疑点或修改代码/表格，先冻结该处，不要求检查工具让步。

规划只校验来源、白名单、样例保护结构和context有效性；strict before/candidate/final guard、构建与真实浏览器检查必须在获批实施后的实际版本执行，不能把本轮计划当通过证据。

## 本轮规划校验结果

- task.py validate实际成功：implement.jsonl 8条、check.jsonl 7条，均真实spec/research引用，无示例seed。list-context实际列出同一组引用。
- 七组原句与来源证据逐字一致；调用现有guard的extract_protected、prose_surface与fact_tokens对方向样例片段检查，七组保护集合、数字token及原有引号内容均保持。没有调用完整before→candidate的strict compare，也没有创建完整候选；片段检查不替代实施门禁。
- 本轮保存的15个来源输入SHA复核均未变，七行原句逐字仍匹配。11-02目录的42文件成员及内容SHA均未变。
- task.json仍为planning，未运行task.py start；正文、日志、测试、runner、CI、策略与基线均未编辑。
- 规划材料完成后须由用户审阅；整章strict guard、构建与真实页面检查仍待获批实施时运行，不记为本轮通过。
