# 22个历史任务逐项收口卡

这是规划账，不是22项全部完成证明。原PRD/状态和父子结构未改；每条原需求以所列源锚点为准，本文件给出当前证据和真正下一动作。外部、读者、硬件和operator门独立保留。

## 01 10-16-bili-season-after-unlock

**目标**：B站合集解锁后建集并挂 17 条。原状态`planning`仅作记录。

**原合同**：`.trellis/tasks/10-16-bili-season-after-unlock/prd.md:7-39`。

**观察与历史边界**
- 历史权限位season/new_season均false；本轮未联系平台。
- series当前18正片，原任务目标17条，不能自动扩大。

**未满足验收**
- 当前合集权限未核实；17个明确目标未重新锁定；未有当前逐条回读证据。

**下一动作**
1. 只读检查平台当前账号与season/new_season，不调用create/join。
2. 从原bvid台账形成17项目标快照，解释第18集归属；用户审后才生成逐条操作计划。
3. 权限可用且每条对话授权后建集/挂入，再逐条新ID回读。

**完成检查**：seasons正常且封面线上URL；原17个aid/cid同section，每条view.ugc_season回显；简介无Markdown残留。

**依赖**：可独立准备，仍受具体审阅门约束。

**授权/外部前提**：平台登录/权益合法开放；创建及逐条join明确对话授权；17与18范围确认。

## 02 10-16-e04-board-measurement

**目标**：E04 优先级反转上板实测：两臂跑完并回填实测记录表。原状态`planning`仅作记录。

**原合同**：`.trellis/tasks/10-16-e04-board-measurement/prd.md:10-30`。

**观察与历史边界**
- docs/lab/e04-priority-inversion.md:103-108四臂实测仍为空。
- 理论值明确非实测。

**未满足验收**
- 没有可追溯四次烧录/复位/串口原始日志。
- 目标板/探针/接线/仪器尚未确认。

**下一动作**
1. 先核F407身份、HSI/USART接线和电气条件；只读确认工具与内核版本。
2. 在隔离构建目录生成两OS×两锁版并记录配置/commit/摘要，避免缓存变体混用。
3. 获可写授权后逐臂烧录复位取日志，按日志回填，不改理论表或F5模型口径。

**完成检查**：四行每项有日期/commit/内核版本/日志路径和等待时间、M实际现象；异常按cpu_work与startup两假设区分。

**依赖**：可独立准备，仍受具体审阅门约束。

**授权/外部前提**：明确板卡和接线；四臂写入/复位授权。

## 03 10-22-video-v2-remaster

**目标**：视频 v2 重制：实验室仪器风 + 全量旁白重写 + 全平台换新。原状态`in_progress`仅作记录。

**原合同**：`.trellis/tasks/10-22-video-v2-remaster/prd.md:29-59`、`.trellis/tasks/10-22-video-v2-remaster/prd.md:69-99`、`.trellis/tasks/10-22-video-v2-remaster/implement.md:2635-2656`。

**观察与历史边界**
- 当前series18正片均formatVersion=2；c3b变体排除。
- .temp/v2-final-audit/table.md存在36母版历史审计，不等于本轮声音/画面通过。
- video/publish/repost已有归档/准备/删除/发布/回读工具文件。

**未满足验收**
- 18×横竖全部AC、事实表、听感、缩略图和用户接受需对应当前hash。
- 旧/新ID回读及逐集删除发布许可不能由已写工具替代。
- spec/video/index.md:50记录ai4fw兼容schema缺口；不能删该集以令全局lint变绿。

**下一动作**
1. 先只读校验冻结清单和36母版身份、timeline/事实表/发布包；不build覆盖。
2. 按18集动态枚举lint/check/numbers；缺timeline或skip单列失败/未覆盖。
3. 逐集抽听术语与-14LUFS/漂移、336px封面，冻结母版通过后才审平台替换。

**完成检查**：18×2母版及四平台包全部当前证据；所有新增门有反例；发布逐集归档旧ID、独立删/发闸门及新ID回读，无批量删除。

**依赖**：可独立准备，仍受具体审阅门约束。

**授权/外部前提**：母版用户验收；逐集独立删除/发布授权；平台认证与频控。

## 04 10-25-bmsz-validation-depth

**目标**：BMS-Z 对齐：验证纵深（门禁/契约/产物对账）。原状态`in_progress`仅作记录。

**原合同**：`.trellis/tasks/10-25-bmsz-validation-depth/prd.md:32-81`、`.trellis/tasks/10-25-bmsz-validation-depth/prd.md:95-118`、`.trellis/tasks/10-25-bmsz-validation-depth/research/verification-log.md:5-139`。

**观察与历史边界**
- 本地门脚本、docs-check/PDF/pack/pages/search及历史24门记录存在。
- 本轮docs-check实过138文件6类27条声明；未重跑全门。

**未满足验收**
- 旧验收P3针对A4，当前check_pdf默认16开13项；需保留各原意并登记合同演进。
- 全门/故意失败样例及当前CI对应关系未本轮核全；pwsh口径历史未验。

**下一动作**
1. 按当前package/workflows和quality-contract建立门到AC矩阵，不照搬旧11项或88章。
2. 复用既有反向夹具验证各门；不在真实README临时造坏链接。
3. 获实施审阅后运行local-gates，工具缺失SKIP和operator缺基线如实列；必要新增测试单独review。

**完成检查**：原R1–R8逐项有当前成功+故意失败证据；退出码真实，缺工具不伪绿；部署验证真正artifact，测试/策略不弱化。

**依赖**：可独立准备，仍受具体审阅门约束。

**授权/外部前提**：任何测试/runner/CI修改单独review；operator配置合法入口。

## 05 10-25-book-production

**目标**：做成一本真正的书：16 开印前 PDF + EPUB3（正文冻结，只改书稿工艺）。原状态`in_progress`仅作记录。

**原合同**：`.trellis/tasks/10-25-book-production/prd.md:5-27`、`.trellis/tasks/10-25-book-production/prd.md:58-86`、`.trellis/tasks/10-25-book-production/prd.md:96-121`、`.trellis/tasks/10-25-book-production/implement.md:104-153`。

**观察与历史边界**
- 当前有build_print/check_pdf/字体来源及HTML/A4/印前文件。
- 当前不存在build_epub.py、check_epub.py及book:epub入口；不能称两件真书齐。

**未满足验收**
- EPUB3与章级内容同一性尚不可执行。
- 历史A4退役决定与当前双PDF合同冲突；旧11门不能替代当前13门。
- 完整当前内容/字体/目录/索引及重建稳定性待正式执行。

**下一动作**
1. 先对原R1–R10映射现存PDF实现和未实现EPUB，明确A4保留/退役审阅项。
2. EPUB沿既有HTML/manifest真源薄切片设计两章XHTML+nav+OPF+封面，审核新测试和CI输入后实现，不另解析一套正文。
3. 内容/图冻结后完整构建，检查185×260、13门、逐章同一性、epubcheck和两次尺寸/页数。

**完成检查**：PDF与EPUB3都满足原AC；epubcheck零error、warnings说明；94章当前manifest同源，不sample替全量，新增测试/策略review。

**依赖**：可独立准备，仍受具体审阅门约束。

**授权/外部前提**：A4合同冲突明确决策；EPUB实现与测试/CI改动审阅；封面定稿。

## 06 10-26-de-ai-polish

**目标**：去AI味精修：文字/图片/封面。原状态`planning`仅作记录。

**原合同**：`.trellis/tasks/10-26-de-ai-polish/prd.md:27-41`、`.trellis/tasks/10-26-de-ai-polish/prd.md:51-70`。

**观察与历史边界**
- 原父子关系仅prose-polish与cover-art，保留。
- 旧88/6范围、口癖指标和11门是历史目标，不足当前全书深度。

**未满足验收**
- 文字/封面各自用户验收未由状态证明。
- 原父任务没有design/implement且上下文seed。

**下一动作**
1. 补父任务集成设计，复用两子任务证据，不再派第二轮全文重写。
2. 文字技术保护和封面视觉接受分别审核，映射当前manifest/13门。
3. 与新深度任务共享一次章节修改，原精修AC仍独立对账。

**完成检查**：两子任务全部原AC接受，封面图/文来源一致、逐批抽评真实；不得用口癖或新深度计划冒充完成。

**依赖**：10-26-prose-polish、10-26-cover-art。

**授权/外部前提**：风格/封面用户选择；只规划不得擅自归档。

## 07 10-26-cover-art

**目标**：封面定制线稿插画。原状态`planning`仅作记录。

**原合同**：`.trellis/tasks/10-26-cover-art/prd.md:7-25`。

**观察与历史边界**
- research/cover有board/scope及深绿/纸色候选。
- 生产mcu-book/print/art.py:78 cover_art为现存内联主视觉，不是独立cover.svg。

**未满足验收**
- 缺两构图×两配色用户选择及正式封面接受。
- EPUB封面同源在EPUB实现前无法验收。

**下一动作**
1. 补纯矢量候选/排印接入设计，不把research图当定稿。
2. 用当前cover_art/CSS做隔离预览，两构图两配色并排请用户选；不替换生产。
3. 选定后审生产接入、完整PDF结构/字体/出血与EPUB同源。

**完成检查**：用户选定且实际封一可读；逐元素可追溯、无素材图标/生成图；185×260/页码合同及当前13门通过，EPUB同步。

**依赖**：可独立准备，仍受具体审阅门约束。

**授权/外部前提**：两版构图配色视觉选择；生产接入和EPUB依赖。

## 08 10-26-oss-influence

**目标**：从 GitHub 开源项目与社区摄取影响，补充整书项目层。原状态`planning`仅作记录。

**原合同**：`.trellis/tasks/10-26-oss-influence/prd.md:9-38`。

**观察与历史边界**
- mcu-book/book/G-开源地图.md:9-40已有30仓库表。
- research/verified-oss-projects.md仅18条核验记录，部分正文许可仍写见LICENSE；未现场核上游。

**未满足验收**
- 原P1六类各5–8条不等同已有30条总数；逐条许可/活跃/具体符号证据仍需对账。
- 47工程逐个上游映射、P3新增实战工程/CI、P4方法清单未获得完整验收证据。

**下一动作**
1. 先将现存G与原附录B计划对账：保留B工程登记、G地图真源，不复制第二表；位置差异交审。
2. 对每条保留tag/commit、LICENSE原文、符号路径和访问日期；外部证据届时用官方源核实。
3. 列47工程逐一映射缺口；P3选定题目/放置位置后另审工程登记和测试CI，不静默取消。

**完成检查**：P1–P4全部满足或用户明确批准调整：六类覆盖、真实许可/路径、47对照、可编译新增工程及有证据的方法落地。

**依赖**：可独立准备，仍受具体审阅门约束。

**授权/外部前提**：附录位置及P3章题/分部审阅；新增工程测试/CI review；上游信息当前取证。

## 09 10-26-prose-polish

**目标**：逐章文字精修88章。原状态`in_progress`仅作记录。

**原合同**：`.trellis/tasks/10-26-prose-polish/prd.md:7-17`、`.trellis/tasks/10-26-prose-polish/prd.md:37-52`、`.trellis/tasks/10-26-prose-polish/implement.md:10-46`。

**观察与历史边界**
- 已有strict guard与历史批次记录，B0/B1/B2/B7当前严格保护门均通过。
- 旧implement仍含stash/整批回退指示；本总计划禁止套用到用户WIP。

**未满足验收**
- 全书逐批before/after、风格接受及抽评不是现成checkbox可证明。
- 全书最终PDF/字体仍依赖冻结源。

**下一动作**
1. 将原章级保护与新24批路由关联，当前每批只由深度任务一个写者实施。
2. 保留原稿和本次候选的具体hash，不从HEAD还原覆盖合法后续内容。
3. 旧措辞strict先验，再对获审解释/图分层增补；字体/完整PDF统一最后验证。

**完成检查**：原全部文件精修/风格及保护证明、用户逐批2章抽评与最后原13门都齐；新技术事实另审，不刷口癖阈值。

**依赖**：可独立准备，仍受具体审阅门约束。

**授权/外部前提**：批次文字接受；不得使用旧stash/reset回滚；技术纠错单独review。

## 10 10-27-ai-dev-deepen

**目标**：AI 辅助开发内容加深：把大模型当结对工程师写进书里。原状态`in_progress`仅作记录。

**原合同**：`.trellis/tasks/10-27-ai-dev-deepen/prd.md:19-37`、`.trellis/tasks/10-27-ai-dev-deepen/implement.md:43-78`。

**观察与历史边界**
- manifest现11部；docs/ai六章存在，旧实施记录详列六章与题花完成宣称。
- 用户插图/详细度接受仍未勾。

**未满足验收**
- 六章来源、细节准确性与当前PDF电池未本轮全面核验。
- 旧试点勾选与后续实录不一致，不重建已有六章冒充新完成。

**下一动作**
1. 逐条映射原R1–R5到现存六章/manifest/sidebar/来源/图，补未解释/疑似事实。
2. AI2由新pilot唯一写者处理，其他五章由rollout；本任务保留原六章详细度/外源/印前AC。
3. 在同源最终PDF对13门、字体、寡行/孤儿/灰点与用户视觉接受留证。

**完成检查**：AI部六章/来源/导航齐，原印前电池和用户图文详细度接受真实；行数/题图数不代内容质量。

**依赖**：可独立准备，仍受具体审阅门约束。

**授权/外部前提**：六章内容视觉用户接受；事实纠错证据审阅。

## 11 10-27-book-interest-polish

**目标**：书籍趣味性提升：增强叙事、互动与记忆点。原状态`in_progress`仅作记录。

**原合同**：`.trellis/tasks/10-27-book-interest-polish/prd.md:11-49`、`.trellis/tasks/10-27-book-interest-polish/implement.md:9-35`。

**观察与历史边界**
- 历史6试点/批量勾选完成，但用户2章抽评仍空。
- 新深度样章与原趣味试点4章重合，另有DAC与GD32RCU。

**未满足验收**
- 叙事闭环/5–10分钟互动/1主线和12%增量的当前逐章证据未齐。
- 不能因为批量标x跳过原试点抽评。

**下一动作**
1. 保留旧6试点逐项评价和before/after，不用新六章直接替换其DAC/RCU范围。
2. 原互动/回扣AC纳入24批一次审阅，文字只由该批写者落盘。
3. 12%趣味增量与讲透新增解释分账；确需超过先审，不静默提高预算。

**完成检查**：原6试点全部闭环/邻近答案/一主线，用户至少2章通过；各分部抽样和原保护/全站印前验证齐。

**依赖**：可独立准备，仍受具体审阅门约束。

**授权/外部前提**：趣味2章抽评；增量边界必要调整审阅。

## 12 10-28-social-video-ai-tools

**目标**：AI 视频工具清单社媒成片（B站/抖音/小红书/视频号）。原状态`in_progress`仅作记录。

**原合同**：`.trellis/tasks/10-28-social-video-ai-tools/prd.md:9-25`、`.trellis/tasks/10-28-social-video-ai-tools/implement.md:23-40`。

**观察与历史边界**
- video/jobs/ai4fw与ai4fw-16x9有review；out有bilibili/douyin/wx，copy-ai4fw存在。
- 本轮ffprobe两版均64.1s、30fps、H264 yuv420p；横1920×1080，wx1080×1920/954399bps。
- xhs历史发布记录存在但置顶挂起，不等于当前线上状态。

**未满足验收**
- doctor/build/verify/finalize对应当前hash及四平台包映射需核，不能仅凭3个文件否认xhs复用。
- video/research/wx-plan.md不存在，真实平台约束文档video/publish/wx-plan.md。
- 常驻episode schema缺voice/platforms/cover.line1是已登记缺口，不能改runner忽略ai4fw。

**下一动作**
1. 修复单个失效context路径，保留内容快照口径。
2. 对两个job最终报告/艺术记录/字体/四平台封面与文案逐项对当前hash，不重渲已发布母版。
3. 区分本任务文件交付与后加平台义务；置顶/原创声明若要执行另核账号/新授权，不重发。

**完成检查**：两画幅同文非裁切、四平台明确映射与封面copy齐、原所有门及字体/隐私美术记录当前有效，skill源码零修改；发布不属于自动完成。

**依赖**：可独立准备，仍受具体审阅门约束。

**授权/外部前提**：常驻schema修订需独立实现审；置顶评论/声明当前授权；不自动重发。

## 13 11-06-animation-d2-closure

**目标**：动画修复收尾：D2 代码块边界与回归验证。原状态`in_progress`仅作记录。

**原合同**：`.trellis/tasks/11-06-animation-d2-closure/prd.md:19-29`、`.trellis/tasks/11-06-animation-d2-closure/implement.md:24-28`、`.trellis/tasks/11-06-animation-d2-closure/research/implementation-evidence.md:3-54`。

**观察与历史边界**
- 本轮现存renderer回归12pass/0fail/0skip，未改任何测试。
- 历史旧实现4pass8fail及三页smoke有记录，非本轮RED或UI。

**未满足验收**
- 新增回归用户审查/后续基线与operator仍需单独确认。
- 旧PRD/implement提交权限描述不一致，不能据一处自动再发PR。

**下一动作**
1. 保留当前生产修复，不重复改parser或重建故障。
2. 核原回归review和精确代码/提交范围，批准后真实三页UI与D1/D3/D4烟测。
3. operator仅实跑并分类，权限冲突交具体提交审阅。

**完成检查**：原代码块/图注/正文contract、同回归旧败新过记录、当前三页UI及operator实际状态都有；未审测试不宣称operator通过。

**依赖**：可独立准备，仍受具体审阅门约束。

**授权/外部前提**：原新增测试用户review；具体提交授权核定。

## 14 11-06-animation-reading-experience

**目标**：动画阅读体验：移动端、深色与减少动态效果。原状态`in_progress`仅作记录。

**原合同**：`.trellis/tasks/11-06-animation-reading-experience/prd.md:9-31`、`.trellis/tasks/11-06-animation-reading-experience/implement.md:5-38`。

**观察与历史边界**
- 原D1/D3/D4缺陷与实施计划存在，D2独立收尾有后续证据。
- 本轮未运行真实375px/减少动态测试。

**未满足验收**
- 当前12s/10.8s静帧、放大尺寸/焦点/滚动的实际surface需新验证。
- context仍seed；旧D2方案为html_block，已被parser-aware边界取代。

**下一动作**
1. 补真实context并明确D2以独立任务修复为唯一实现，不回退旧正则。
2. 新preview375px浅深/reduced-motion逐条测D1/D3/D4、截图与关闭焦点。
3. 复用原browser/a11y/anim/book检查，未配置operator保持unverified。

**完成检查**：D1时间/末帧、D2三页非空、D3真正放大可滚、D4焦点回退/锁滚全部实测，无更改源动画/书稿事实。

**依赖**：11-06-animation-d2-closure。

**授权/外部前提**：本轮正式UI复验需实施阶段放行。

## 15 11-06-language-batch2

**目标**：语言通俗化第二批：相邻入门章节规划。原状态`in_progress`仅作记录。

**原合同**：`.trellis/tasks/11-06-language-batch2/prd.md:26-35`、`.trellis/tasks/11-06-language-batch2/implement.md:5-22`。

**观察与历史边界**
- B1/B2当前均与checked candidate逐字节相同，本轮strict保护均过。
- 历史桌面手机/门记录存在，用户文字接受空。

**未满足验收**
- 解释易懂度接受及后续发布关联需核。
- 事实疑点不能由prose门通过推断正确。

**下一动作**
1. 交原12+7处对照与本轮identity/guard，不重新润色制造新批次。
2. 确认原发布PR/commit与当前来源；后续深度修改按新rollout而非覆旧候选。

**完成检查**：原两章AC文字/保护/实际surface/源码证据齐，用户接受；未测固件/PDF不冒充。

**依赖**：可独立准备，仍受具体审阅门约束。

**授权/外部前提**：B1/B2文字接受。

## 16 11-06-language-release-pdf

**目标**：发布 B0–B2 通俗化并生成本地印前 PDF。原状态`in_progress`仅作记录。

**原合同**：`.trellis/tasks/11-06-language-release-pdf/prd.md:4-13`、`.trellis/tasks/11-06-language-release-pdf/implement.md:3-9`。

**观察与历史边界**
- 旧计划所有待办未记执行结论；本地HTML/A4/16开文件存在且时间/摘要不同。
- 现有print文件早于当前HTML，存在性不是含最新B7或全部新文的证据。

**未满足验收**
- B0–B2精确发布CI与main同SHA证据需重新关联；不能重发已发布改动。
- 完整本地16开13门及正文命中尚缺本轮证据。

**下一动作**
1. 只读关联原PR/commit/CI与源快照；已发布项只补证，不造重复PR。
2. 独立输出目录用新源生成完整HTML/印前，不覆盖旧发布包；实际13门/文本/hash验。
3. 本任务只B0–B2旧交付；全书最终PDF仍由delivery统一，避免混源。

**完成检查**：固定B0–B2发布head全成功+main同SHA部署，完整185×260且13门/新文/hash当前证据；operator缺覆盖单列。

**依赖**：可独立准备，仍受具体审阅门约束。

**授权/外部前提**：精确提交范围/新发布前再审；完整PDF执行阶段授权。

## 17 11-06-spec-plan-continuation

**目标**：B0 工具链全景：语言通俗化试点。原状态`in_progress`仅作记录。

**原合同**：`.trellis/tasks/11-06-spec-plan-continuation/prd.md:17-29`、`.trellis/tasks/11-06-spec-plan-continuation/implement.md:5-22`。

**观察与历史边界**
- B0当前与候选逐字节一致，本轮strict保护通过。
- 旧页面下一站命中两次失败，已有证据指父div，不把目标HTTP200当点击过。

**未满足验收**
- 用户B0文字接受仍缺；下一站点击未通过历史记录。

**下一动作**
1. 保留旧文与事实疑点，不扩为本统筹总任务。
2. 文字接受后将下一站命中列独立小bug：按预期/实际与最小DOM复现、两假设区分，不顺手改CSS。

**完成检查**：原AC全文及用户文字接受；若处理链接bug则旧败新过窄回归和真实点击，未跑仍未验证。

**依赖**：可独立准备，仍受具体审阅门约束。

**授权/外部前提**：B0文字接受；链接bug独立具体方案。

## 18 11-07-book-delivery-closure

**目标**：全书交付收口：告警、验证、固件、硬件、PDF与发布。原状态`planning`仅作记录。

**原合同**：`.trellis/tasks/11-07-book-delivery-closure/prd.md:21-34`、`.trellis/tasks/11-07-book-delivery-closure/implement.md:7-24`。

**观察与历史边界**
- 三文档/上下文齐，planning；历史告警与47工程、PDF/硬件计划存在。
- operator本轮plan仍verification-baseline-unavailable/checks=[]。

**未满足验收**
- 告警、固件、硬件、完整PDF/包/CI尚未执行；无明确板卡/基线。
- 原范围未包含EPUB；须联用book-production不能悄悄删除旧EPUB承诺。

**下一动作**
1. 告警每个小实验单因定位；源/API参考完成后再改，新增测试/runner需review。
2. host/ARM/ESP配置分别实编译，不拿路径可见或SIL当HIL。
3. 内容图和EPUB/封面整合后唯一最终HTML/A4/16开/EPUB包验证，提交线上另审。

**完成检查**：C1–C6全部真实通过，operator与hardware前提满足后实验，否则阻塞；最终包同源和PR/main同SHA线上证据齐。

**依赖**：11-07-book-depth-rollout、10-25-book-production。

**授权/外部前提**：工程实施审阅；operator合法基线；设备/写入授权；提交/线上发布具体授权。

## 19 11-07-book-depth-handdraw

**目标**：全书知识讲透与手绘升级：逐点覆盖、通俗讲解与完整交付。原状态`planning`仅作记录。

**原合同**：`.trellis/tasks/11-07-book-depth-handdraw/prd.md:21-38`、`.trellis/tasks/11-07-book-depth-handdraw/implement.md:7-27`。

**观察与历史边界**
- 101源/814标题候选/24批及三子任务研究齐。
- 8选窗/23read无综合/70机械台账研究限制保留。

**未满足验收**
- 全书语义知识点/图文未实施；不能把814标题当全集或完工。

**下一动作**
1. 三个子任务依赖/单一写者与旧精修/趣味/AI验收对账。
2. 每批补无标题知识卡/先修并保留技术纠错审阅；抽评后推进。
3. 汇总全部accepted知识与正式图、所有工程交付，不以其他绿项代替。

**完成检查**：101文件所有语义知识卡accepted、图文/跨端/印前/用户理解与全部交付AC1–7均有证据。

**依赖**：11-07-book-depth-pilot、11-07-book-depth-rollout、11-07-book-delivery-closure。

**授权/外部前提**：具体图文实施及每批抽评。

## 20 11-07-book-depth-pilot

**目标**：全书图文升级：六章讲透与手绘样章。原状态`planning`仅作记录。

**原合同**：`.trellis/tasks/11-07-book-depth-pilot/prd.md:18-34`、`.trellis/tasks/11-07-book-depth-pilot/implement.md:7-21`。

**观察与历史边界**
- 六类方向和两研究草图存在，未入生产。
- 原研究图390主要标签13.56px记录不算正式集成。

**未满足验收**
- 六章全文语义审阅、正式图文与用户接受尚缺。

**下一动作**
1. 先全文C2/F3语义卡，按批准方案做两个概念薄切片，不跳到批量写书。
2. 其余B7/S11/P2/AI2全文审查、复用图+分镜，事实疑点另审。
3. strict中间稿→获审additive→真实390/1440浅深和离线HTML集成，再交六章接受。

**完成检查**：六章全部知识卡与正式手绘/原门/真实surface过，用户2章以上抽评通过再rollout。

**依赖**：11-07-language-batch5。

**授权/外部前提**：具体样章图文实施批准；用户理解/视觉验收。

## 21 11-07-book-depth-rollout

**目标**：全书图文升级：全量批次与附录一致性。原状态`planning`仅作记录。

**原合同**：`.trellis/tasks/11-07-book-depth-rollout/prd.md:107-123`、`.trellis/tasks/11-07-book-depth-rollout/implement.md:7-20`。

**观察与历史边界**
- 95余文件已有23批归属，pilot合计101无漏重；S18全部在内。

**未满足验收**
- 全部语义审阅/图文实施/抽评未开始，机械台账不算完成。

**下一动作**
1. pilot接受后逐批全文、补无标题卡和先修，最多6文件。
2. 复用旧精修/趣味/AI/OSS现有良好解释，统一一次修改/独立验收维度。
3. 按批更新真正reviewed/planned/verified-local/accepted，最终全书对账。

**完成检查**：原95文件所有语义点accepted，附录按其职责/真源，所有S章覆盖，正式图/运行/事实证据和用户抽评均齐。

**依赖**：11-07-book-depth-pilot。

**授权/外部前提**：样章接受；每批范围/事实/图文审阅。

## 22 11-07-language-batch5

**目标**：语言通俗化第五批：B7 构建系统收尾。原状态`in_progress`仅作记录。

**原合同**：`.trellis/tasks/11-07-language-batch5/prd.md:16-39`、`.trellis/tasks/11-07-language-batch5/implement.md:41-49`。

**观察与历史边界**
- B7 current==checked candidate；本轮before→docs strict通过。
- 原四行和changelog保留，历史站点手机检查有记录。

**未满足验收**
- 用户四处文字接受，未提交/发布；不能因总任务统筹推断S篇开改。

**下一动作**
1. 用原四处对照交文字接受，不复写B7。
2. 接受后若发布另核白名单与具体授权；B7更深修改仅由新pilot负责。

**完成检查**：恰四行保护/identity和原AC1–7证据+用户文字接受；没有授权不提交/扩S。

**依赖**：可独立准备，仍受具体审阅门约束。

**授权/外部前提**：B7文字接受；提交发布另审。
