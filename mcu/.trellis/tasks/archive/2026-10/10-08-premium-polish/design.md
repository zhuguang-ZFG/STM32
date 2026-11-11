# 技术设计：精品化四维打磨

## 1. 边界与契约

本任务只动**站点层**：`docs/.vitepress/config.mts`（导航）、`scripts/`（新增检查）、`tests/`（新增用例）、`package.json`（脚本接线）、`docs/gd32/`（不新增章节，只补入口）、新增 `docs/capstone/`（综合项目落地页）、各板块 `index.md`（路线表/导览钩子）。

不动：章节技术结论、`code/` 固件、`.trellis/spec/` 既有条款。

## 2. R1 补齐 GD32 侧边栏

**契约**：`.trellis/spec/docs-site/structure.md` 规定「sidebar 按板块分组全量列出」；GD32 现有 10 章（`00-env`…`09-gpio-minimal`）+ `index`，侧边栏须全列。

**做法**：把 `config.mts` 的 `'/gd32/'` 组从 `[导览, G1]` 扩为完整 G 篇（G0–G4）+ V 篇（V0–V4）两组，标题与 `docs/gd32/index.md` 路线表一致（G0 环境与工具链 / G1 RCU 时钟树 / G2 GPIO 与 AF / G3 USART 增强点 / G4 外设差异 / V0 RISC-V 工具链 / V1 Bumblebee 与 CLIC / V2 RCU 与 108MHz / V3 MTIME 与延时 / V4 GPIO 最小系统）。编号前缀 `G`/`V` 遵循 frontmatter H1。

## 3. R2 导航可达性闸门（核心）

**新文件 `scripts/nav-check.mjs`**：

- **输入**：`docs/.vitepress/config.mts` 抽取全部 `link: '<path>'`（去锚点、规范化尾斜杠）。
- **页面集**：遍历 `docs/**/*.md`，路由 = `/` + 相对 docs 的路径去掉 `.md`；`index.md` 归一为所在目录（`docs/gd32/index.md` → `/gd32`）；`docs/index.md`（首页）为 `/` 特例。
- **判定**：每个页面路由必须在 nav/sidebar 链接集合中（同时接受 `route` 与 `route/`）。缺失即收集。
- **输出**：缺失清单 → `console.error` 并非零退出；全通过打印 `✓ 全站 N 个页面均可从导航到达`；支持 `--quiet`。
- **风格**：对齐 `scripts/links-check.mjs`（顶部注释写「为什么」，`--quiet`，exit 1）。

**为什么是脚本而非只靠 VitePress 死链门禁**：VitePress 死链检查方向是「链接→页面」（页面不存在报错），不检查「页面→入口」（页面存在但没入口）。本闸门补的正是后者，且项目历史上正是靠「肉眼」发现总览页漏登记（见提交 `e139622`）。

**接线**：`package.json` 的 `quality` 串在 `links:check` 之后加 `nav:check`；新增 `"nav:check": "node scripts/nav-check.mjs"`。CI 无需改（`npm run quality` 已在 `quality.yml` 内）。

**测试 `tests/nav.test.mjs`**（`node:test`）：
- 正例：用临时目录造 `docs/a/b.md` + 含 `link: '/a/b'` 的 config → 通过。
- 反例：删掉该 link → 抛错/非零。
- 边界：`index.md` 归一、锚点剥离、尾斜杠容忍。

## 4. R4 结构一致性审计

**做法**：写一次性审计脚本（或 node 内联）扫描成稿章（`status: done`），统计统一模板要素出现率：`本章精髓 / 怎么读这一章 / 学习目标 / 先修 / 记忆锚点 / 常见坑 / 短自测 / 你做到了`。产出报告到 `.trellis/tasks/10-08-premium-polish/research/structure-audit.md`，缺项按「真缺 / 模板演进差异」分类，真缺的补。

## 5. R5 综合项目落地页

**做法**：新增 `docs/capstone/index.md`，定位为「项目 hub」：
- 讲清「为什么要有综合项目」——把散落的实验串成一条可交付路线；
- 给出两条路线（F407 电位器记录器 / S3 板载传感器记录器）的骨架与依赖章节映射；
- 明确状态：**规划中**，实体工程由 `knowledge-capstone` 交付，**不伪造已完成**；
- 链接进 `config.mts` 的 nav 与 sidebar，并把 README/首页 roadmap 的 `H[综合项目]` 指向它。

**诚实边界**：页面显式标注「工程规划中，上板验证待做」，与项目既有「待上板实测」诚实文化一致。

## 6. R6 导览钩子巡检

检查各 `docs/<track>/index.md` 是否有「为什么值得学」的开场钩子与「下一步去哪」。缺的补一句，不重写。

## 7. 验证与回滚

- 验证：`npm run nav:check`、`npm test`、`npm run quality`、`npm run docs:build`（死链零错误）。
- 回滚点：每批独立提交；config.mts 与新增文件互不耦合，单批可 revert。
