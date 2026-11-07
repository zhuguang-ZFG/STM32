# 实施计划：七行白名单，两阶段审阅

当前状态：in_progress。用户审阅具体七行方案后选择“通过，开始实施”，已task.py start；仅执行本地改写与验证，不提交发布。

## 阶段 1：规划审阅门

- [x] 阅读 B5/B6 及前三批约定，确认本批只处理七行：B5 15/18/35/47，B6 19/50/101。
- [x] 保存原文行、15个来源/冻结输入SHA、现有metrics及11-02全部用户文件SHA：research/source-evidence.json。
- [x] 将技术疑点登记冻结；给出至少每章两组完整原句与方向样例、对应收益：research/reading-evidence.md。
- [x] 用户已审阅PRD/design/本计划与七组方向样例并批准实施，task.py start成功。

## 阶段 2：固定实施来源

- 对 source-evidence.json 中全部输入重新计算SHA；七行原句逐字对齐，确认无漂移。
- 对用户11-02目录核对文件集合与SHA；不将其变动纳入本批。出现漂移先重读判断来源，不覆盖用户工作。
- 从当前原文字节保存 research/b5-before.md、b6-before.md，避免Windows换行转换；记录实际基线commit。
- 候选只从上述字节复制，在 research/b5-candidate.md、b6-candidate.md 内改七行，不扩大相邻范围。

## 阶段 3：候选与落盘各自过保护门

- B5每处讲清工具/观察对象，B6每处讲清动作/角色；按reading-evidence所列问题复查因果、引文和适用范围。
- 分别执行：

```text
python mcu-book/tools/prose_guard.py <b5-before> <b5-candidate>
python mcu-book/tools/prose_guard.py <b6-before> <b6-candidate>
```

- 逐行比较只有获批的四行/三行变化；不将表格/引文/代码/数字事实写入编辑范围。失败只改候选，不能改guard或阈值。
- 已批准实施范围内将候选七处落盘docs，before→最终docs再次strict guard；确认最终文件等于已验候选。文案效果交用户验收，不以指标下降宣布通俗化成功。

## 阶段 4：原有检查与页面证明

使用已有入口，不改测试、runner、策略或baseline。Git Bash的npm shim若仍不可用，直接执行其package.json对应的node/python入口，不减少子步骤：

```text
node scripts/prose-readability.mjs --check
node scripts/reading-time.mjs --check
node scripts/docs-check.mjs
python mcu-book/build_html.py --check
node scripts/book-guide/generate.mjs --check
node scripts/gen-progress.mjs
node node_modules/vitepress/bin/vitepress.js build docs
```

- 构建完成后才启动preview；从实际ready输出确定URL，不能把日志匹配问题当构建失败。
- 桌面1440×960与手机390×844实际打开两页；每页查看新文、现有图/动画及代码，点击目录和答案折叠；确认hash/可见性/open状态、document宽度与页面错误并截图。
- task_verify(action=run)实际执行，报告passed/failed/unverified；缺项目或基线时仍未验证，手工命令结果不伪装成operator配置覆盖。
- 七行外文本、15个输入中的保护文件、用户文件集合与SHA复核。输入/事实漂移停止扩写，先回到证据。

## 阶段 5：本地文字交付门

实施后补记docs/reference/changelog.md本批实际变化，再对含日志的最终站点跑docs-check与完整docs-build入口；不复用日志前构建来冒充最终版本。

提供七处对照、理解收益、冻结项、实际命令和浏览器证据、未验证项。仅在本地交文字验收，不自动提交、推送、发布、归档本任务或推进下一批。纯散文工作不新增永久测试；临时验证进程/tab在证明完成后关闭，研究证据按本任务保留。

## 本轮实际完成记录

- [x] 实施来源15输入与七行逐字复核；保存纯LF、逐字节一致的before/candidate。
- [x] 七行候选与落盘分别对before strict guard，两章两阶段全部一致；白名单外原行不变，最终正文等于已验candidate。
- [x] prose78章、reading78篇、docs138文件、book94章题图94/94实际通过；bg_33完整站点构建62.72s成功。
- [x] 两页桌面1440×960/手机390×844实际目录、答案折叠、散文/图/代码截图、页面边界与错误检查通过；手机代码块内部滚动已实际验证。tab/service已关闭。
- [x] 配套更新日志已补；bg_34实际执行含日志最终docs-check/guide-check/docs-gen/VitePress build全过，build49.50s。
- [x] 13冻结输入、用户42文件成员及内容SHA均未变；task_verify实际unverified，未计通过。
- [x] 用户要求提交推送合并并确认三笔提交分组，本批进入发布收尾；下一批仅授权发布后建任务与规划。

完整实际证据、七处收益与验证边界见research/implementation-evidence.md。
