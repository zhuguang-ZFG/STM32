# 实施计划：B7四行，两阶段文字校验

状态：in_progress；用户要求继续改进优化后已按原四行方案实施。以下步骤保留原计划，实际记录在末尾。

## 1. 规划审阅门

- 阅读prd/design与reading/source证据，确认仅B7原27/51/116/134及配套changelog。
- 用户先审具体四处方向、收益、冻结范围与验收设计；未批准前不task.py start、不写候选、不动docs。
- curate implement.jsonl/check.jsonl真实规范和研究条目，task.py validate通过后仍等待审阅授权。

## 2. 来源和快照

- 重读四行、27输入及214固定验证输入SHA；B0–B6与用户42文件成员/内容应保持。
- 现有before必须在开始实施时从当前docs保存，纯LF且逐字节同源；不拿方向样例冒充整章候选。
- 遇到来源漂移先报告证据并修规划，不套旧行号；任何新事实需求退回R4。

## 3. 四处改写与双门

- 只在本任务research中制作b7-before.md/b7-candidate.md；仅四行内按获审方向改。
- 实跑python mcu-book/tools/prose_guard.py <before> <candidate>（strict，无additions）；额外核对四行外文本/代码顺序/数字/引文/容器，交文字检查。
- 落盘仅四行；独立再跑before→docs strict guard并核最终docs==candidate，记录各输出及逐处理解收益。

## 4. 既有检查与真实页面

- node scripts/prose-readability.mjs --check
- node scripts/reading-time.mjs --check
- node scripts/docs-check.mjs
- python mcu-book/build_html.py --check
- node scripts/book-guide/generate.mjs --check && node scripts/gen-progress.mjs && node node_modules/vitepress/bin/vitepress.js build docs
- task_verify(action=run)：passed/failed/unverified分列；缺基线不算通过。测试/runner/CI/策略固定，不为变绿修改。
- 启动本任务独占preview端口，实际B7桌面/手机按design跑目录/答案交互、截图正文/图/代码，验证真实视口与内部滚动及错误情况。不执行章内工程/烧录实验。

## 5. 本地交文字验收

- 烟测通过后仅补配套changelog，并重跑含日志最终docs检查/build；复核固定来源和用户工作。
- 提供四处前后对照、理解收益、既有门禁与页面的实际证据、冻结问题与未验证项，task_verify状态单列。
- 关闭本任务tab/preview；等待用户文字验收。不自动提交、推送、合并、归档本任务或开始S篇。

## 本轮实际完成记录

- [x] 27来源、214验证输入与42用户文件成员/内容复核，激活既有第五批任务；before/candidate初始逐字节同源、纯LF。
- [x] 候选与落盘分别对before strict CLI全部一致；恰四行变化、引文/结构相同、最终docs字节等于已验candidate。
- [x] prose78章、reading78篇、docs138文件、book94章题图94/94实际通过；bg_40站点构建40.01s成功。
- [x] 桌面1440×960/手机390×844实际目录/答案、四处新文、图/代码/表格截图、宽度/内部滚动/图片和页面错误验收通过；tab/preview已关闭。
- [x] 烟测后配套changelog已补，26冻结输入、214验证输入与42用户文件保持；task_verify实际unverified，未计通过。
- [x] bg_41含日志最终docs-check/guide-check/docs-gen/build实际全过，build48.78s；未用日志前build冒充。
- [ ] 用户文字验收；无提交推送发布、归档或进入S篇授权。

完整逐处理解收益、实际命令与页面证据见research/implementation-evidence.md。
