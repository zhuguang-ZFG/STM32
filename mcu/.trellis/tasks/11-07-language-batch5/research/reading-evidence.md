# 第五批阅读证据与方向样例

状态：仅规划。四处方向没有落盘docs，也没有生成整章before/candidate文件；原文来源由source-evidence.json锁定。实施前需再次核对。研究中调用现有guard.compare只证明方向在内存中可遵守保护合同，不是候选或最终正文验收。

## 阅读诊断

SEPIA REVIEW — 中文嵌入式教程，本仓B篇

- Loaded: professional-pass、tech-articles、discourse-pass §1–3、style-pass（不采用小说词表）、zh、GPT prose-layer priors。
- Model: author=unknown；executor=GPT-6.1 Sol（宿主标识zg-newapi/gpt-6.1-sol）。Prose layer: author=none；executor=prior，没有匹配版本的operative表；不从文风推断作者模型。
- Venue corpus: 已接受B5:35/47、B6:19/50/101，以及同页B7:36/57；只据这些文本校准“对象具体、保留工单口语”的语域，不据此证明作者身份或技术结论。
- Failed #5 specificity: B7:27“只有一条路径变脏”、51“哪些路径被重建”把实际目标藏在行话中；134“圈组件”未直接说明工作分工。
- Failed #10 fluency: 116中“多一层生成步骤”用括号接两个命令，生成与构建的先后只靠位置暗示；51把依赖关系、比较与观察三个动作挤在同句。
- Style scan §2–3: 只处理上述对象和先后，不把所有比喻、反问和三项真实分工当AI痕迹；四处以外不全章压字。§5 rhythm: 没有据三句近等长的独立证据诊断整章节奏问题；metrics仅防退化旁证。
- Protected: design五组技术疑点、章内代码/表格/标题/答案与实验；这些疑点不借语言诊断宣布为已复现bug。
- Passed: 1、2、3、4、6、7、8、9（四处白名单的局部诊断，不对全书泛化；固定教程区块和真实枚举豁免）。
- Verdict: isolated hits → 四处最小改写；保留开场工单，不全章重构。

## 观测指标

| 状态 | 句数 | 长句占比 | 平均句长 |
|---|---:|---:|---:|
| 当前B7原文 | 95 | 9.5% | 35.2 |
| 四方向仅内存替换 | 96 | 9.4% | 34.9 |

只读调用scripts/prose-readability.mjs原metrics()；未刷新.prose-baseline.json。方向数字不等于实施/验收效果，不设置目标降幅。

## B7-A · docs/build/07-build-system.md:27

原句：

```markdown
先预测再执行：第一次干跑会列出哪些命令？只碰一下源文件后，是全部重建，还是只有一条路径变脏？如果你的预测是“构建系统会自己理解文件内容”，这十分钟会把这个直觉推翻。
```

卡点：“一条路径变脏”需要先懂构建系统行话，无法直接对应预期观察。

方向样例（供审阅，尚非候选）：

```markdown
先预测再执行：第一次干跑会列出哪些命令？只碰一下源文件后，会全部重建，还是只重建受它影响的目标？如果你的预测是“构建系统会自己理解文件内容”，这十分钟会把这个直觉推翻。
```

理解收益：预测对象变成会重建的目标，不用先理解“脏路径”的比喻。

边界：原引文保持，不写干跑已证实局部重建。

## B7-B · docs/build/07-build-system.md:51

原句：

```markdown
依赖图画出"谁影响谁"，mtime 比对决定"要不要重建"，touch 改一个文件看只有哪些路径被重建。盯住"局部重建"三个字，这是构建系统的核心价值。
```

卡点：三种动作挤在一句里，结尾只强调价值，没有给读图对象。

方向样例（供审阅，尚非候选）：

```markdown
依赖图画出"谁影响谁"，mtime 比对决定"要不要重建"。touch 改一个文件后，沿图看看哪些目标会受影响。读这张图时，盯住"局部重建"三个字。
```

理解收益：按关系、判断、受影响目标的顺序看图；不再重复抽象价值判断。

边界：只给原图的读法，不改SVG或声称完整依赖图。

## B7-C · docs/build/07-build-system.md:116

原句：

```markdown
CMake 的价值在"规模"：两百个文件分二十个目录，`add_subdirectory` 递归管理，每个目录一个 `CMakeLists.txt`，比手写一个大 Makefile 好维护。代价是多一层"生成"步骤（`cmake -B build` 生成，`make -C build` 构建）。
```

卡点：规模例子与生成代价靠名词短语和括号连接，两个命令的动作顺序不够直接。

方向样例（供审阅，尚非候选）：

```markdown
CMake 的价值在"规模"：两百个文件分在二十个目录，用 `add_subdirectory` 递归管理，每个目录各有一个 `CMakeLists.txt`，不用把所有内容挤进一个大 Makefile。代价是多一步"生成"：先用 `cmake -B build` 生成，再用 `make -C build` 构建。
```

理解收益：保留原规模例子和四段行内代码，读者能区分目录管理与先生成后构建。

边界：保留两百/二十与四段行内代码及顺序，原生成器示例不升级技术保证。

## B7-D · docs/build/07-build-system.md:134

原句：

```markdown
IDF 用 CMake 圈组件、Kconfig 管配置、idf.py 调度，三层叠在一起，底层还是 B1 那四步（预处理→编译→汇编→链接）。
```

卡点：“圈组件”和“调度”连用，把角色分工压成口号。

方向样例（供审阅，尚非候选）：

```markdown
IDF 的三层分工：CMake 管组件，Kconfig 管配置，idf.py 负责调度。三层叠在一起，底层还是 B1 那四步（预处理→编译→汇编→链接）。
```

理解收益：把原有三个工具与三个工作对应，保留 B1 四步联系，不补新API语义。

边界：保持原三层/B1/四步，不追加组件或配置API规则。

## 技术冻结与入口

冻结问题按design逐组列位置，范围包括make -n前提、自动变量数量、教学图与Makefile差异、CMake试编译及组件配置绝对说法；本批不事实纠错、不执行工程修改或烧录。

B7入口：docs/build/index.md:22、docs/.vitepress/config.mts:292、docs/curriculum.json:181–189、mcu-book/manifest.json:43；B6章末174已链接B7。相关P3/R6及对照篇仅作阅读上下文，不改链接或调用方。

## 实际研究验证与待执行项

- 原页SHA为3de591b83b328e2358ea050aa665387186f15f293f2df59b55af9715ebb1176d，源文件未修改。
- 现有prose_guard.compare在内存字节适配器中比较原文与四方向，返回零违规；逐行差异恰好27/51/116/134，写文件0。没有新增测试、runner或策略，也未用additions。
- 正式方向文件落盘后仍需核对原引文、四段行内代码、四行外不变；这些规划可行性不能替代获批后的两阶段strict CLI。
- 已打开线上未改B7只读研究：桌面1440文档宽1440；手机实际390/文档390/散文不越界；原页7个pre、2个svg、4个details，无失败img（img计数0）。已关闭研究tab。这里只观察原页面，不冒充新文或目录/答案交互验收。
- 规划材料需用户审阅；整章候选、正式正文、最终构建和新文浏览器验收全部待获批实施时执行，不记为本次通过。

## 规划落盘后核验

- task.py validate本任务实际通过：implement.jsonl 8条、check.jsonl 7条；task.py current确认当前为11-07-language-batch5，task.json仍planning，未start。
- 27来源输入SHA、214验证/runner/CI输入SHA均保持；用户42文件成员与内容均保持。source-evidence.userWork.files为42计数，成员另列paths，不将计数字段当数组比较。
- 内存四方向额外核对：原引文序列一致、行内代码顺序一致、数字事实多重集一致；四行外逐行相同。正式B7 SHA未变，research没有before/candidate完整稿文件。
- 本轮task_verify实际unverified / project-or-git-baseline-unavailable / checks=[]，没有operator通过项；不将规划可行性或手动验证冒充该覆盖。
- 第四批发布已独立完成：PR16的18项检查全SUCCESS后合并3083db1；该SHA的Book CI/外链/Pages三run均success，线上七处新文在、旧文无，四视口目录/答案与代码内部滚动正常。详细远端证据：https://github.com/zhuguang-ZFG/mcu/pull/16#issuecomment-6702978610 。这些是前批发布结果，不是本任务正文实施的通过项。
