# 验收记录 · 2026-11-05

本轮实现验收完成。2026-11-05 用户回复「继续下一步」确认 Phase 3.4 提交计划，按三项分组提交并归档。用户审美终验、外部投稿与语气旧文样本不在本轮实现范围。

## 交付

| 项目 | 正式路径 | 验收结果 |
|---|---|---|
| 卡片源码 | `scripts/social-cards/` | 29 张接收基线，源文/布局/截图可复现，无临时输入和个人绝对路径 |
| 正式卡片 | `video/assets/social-cards/book/` | 29 张 1500×2000、1 张 2560×1440，30 图联系表全部载入 |
| 导读产线 | `scripts/book-guide/` | LF 归一化 source/generator 摘要 + HTML 字节摘要，docs:build 前置检查 |
| 导读 | `docs/public/book-guide/index.html` | 原文完整重渲、当前 141 张插图口径；书籍入口真点击成功 |
| PPT | 旧任务 `deliverables/ppt/` | 13 页/13 备注/13.0 分钟；本轮验证，未修改既有 PPT 文件 |

卡片正文块间距均为 36 CSS px；边界、列内文字、页脚距离检查通过。主句比对允许原有排版标点差异；G1 的既有主句省略原文括注，按两段原文前后顺序核对。所有卡面文字与本轮接收基线一致，空白折叠不作为文字变化。横版封面摘要与旧交付逐字节相同：`5ebbeea2d65a1f774e68a8417b704119b0a43b58dcbca9891aef40aee2545464`。

## 验证命令与结果

| 命令 | 结果 |
|---|---|
| `npm run quality` | 完整通过；122 单元测试、47 工程、111 动画、78 篇阅读时长、138 Markdown、130 导航页、132 产物页、2616 锚点链接、2116 可检索标题 |
| `npm run cards:render` / `cards:check` | 29 卡文字/主句/安全区/36px 间距、30 图摘要和尺寸通过 |
| `npm run guide:generate` / `guide:check` | source/generator/HTML、SEO、a11y 和本地资源检查通过 |
| `python -m pytest mcu-book/tests -q` | 72 passed（25.14s） |
| `npx playwright test book-guide.spec.mjs --config .temp/skill-closeout/playwright.config.mjs` | 2 passed；390px/1440px 真点击、独立 HTML 标识、标题/背景异色、目录与手机收起、无横向溢出 |
| `node <任务目录>/research/browser-check.mjs` | 全部通过；归档后任务目录为 `.trellis/tasks/archive/2026-11/11-05-skill-remaster-closeout`，依赖 preview 在 24318 端口启动，截图/报告输出 `.temp/skill-closeout/` |
| skill `validate-swiss-deck.mjs` | 13 页通过，2 条保留警告 |
| skill `validate-presenter-mode.mjs --target-minutes 15` | 13 页/13 备注/13 分钟，0 error / 0 warning |
| skill `check-presenter-runtime-sync.mjs` | 两份 skill 模板间 CSS/JS 同步通过；该命令检查模板，不接受传入 deck 作为验证对象，deck 本体由浏览器链路另验 |

完整 quality 末次构建 33.97s。性能：首屏外壳+CSS Brotli 139.7KB / 140KB，最大搜索块 723.0KB / 760KB，预算全部通过。此次未抬高阈值。

## 浏览器软件链路

详见 `browser-report.json`。禁用外网请求后：导读照片与目录在 390/1440px 正常；联系表 30/30 图正常；PPT 实测前后页、首页/尾页、宫格选页、备注修改保存、计时启停重置、黑/白屏、冻结/恢复、排练记录、圈选/激光/清除、自动翻页冻结时暂停与恢复后继续、关闭观众窗口后的断连及重开同步。PPT 未做实体投影线缆验证。

截图在 `.temp/skill-closeout/guide-390.png`、`guide-1440.png`、`cards/contact.png`、`ppt-presenter.png`，已人工查看卡片联系表及两种导读整页截图。卡片按原 spec A 方案保留上下留白，没有添加填充文案。

## 保留告警与限制

- PPT S14 自建 fr/fr 标题网格、最后一页全出血 half 色块触底，均为原有可解释警告。
- 构建原有 h/kconfig 高亮 fallback、静态/动态导入同源 JSON 与搜索大块警告仍在，现有硬门均绿。
- Python 测试只有缓存目录权限告警，不影响 72 项结果；未为消除告警改目录权限。
- 本轮没有重排整本 PDF；没有修改章文、书稿 CSS、manifest 或印前工具，书稿回归以既有 72 项测试验证。
- `trellis-brainstorm/before-dev/check` 在全局技能目录只有缺失入口，已按 workflow step 1.1/2.1/2.2 的项目指南完成对应操作；未虚报调用成功。`trellis-start/update-spec/break-loop` 已读并应用。
- 旧任务 13 张 PNG、旧联系表/spec 的会话前差异以及未跟踪 PPT 是既有工作，未还原或静默提交。旧 spec 与联系表仅增加本轮收口记录。

## 提交分组

1. `feat(content): 收口金句卡产线与精排导读入口`：scripts/social-cards、scripts/book-guide、video/assets/social-cards/book、docs/public/book-guide、docs/reference/book.md、package.json；本轮单元/浏览器测试与 pages-check 修复；docs-site 规范；本轮任务规划与验收。
2. `fix(checks): 忽略内联脚本和样式中的伪锚点`：`scripts/pages-check.mjs` 与 `tests/pages-check.test.mjs` 独立成提交，不混入卡片构图差异。
3. `docs(trellis): 登记传播资产契约与实现验收`：`.trellis/spec/docs-site/` 的本轮规范与本轮任务目录。
4. 旧 spec 与历史联系表包含会话前修改且与本轮更新相交，不整文件暂存；所有变更保留在工作区，差量基线在 `.temp/skill-closeout/specs-before.md` 与 `review-sheet-before.html`。旧 13 张 PNG 与未跟踪 PPT 也不加入本轮提交。
5. 用户已确认，产线 `afd543f`、检查器 `08d0c3c`、规范/任务 `696c194` 已提交；本轮任务已归档，journal 另行登记以上三个 work commit。
