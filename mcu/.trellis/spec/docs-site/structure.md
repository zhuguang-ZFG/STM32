# 站点结构规范

## 目录与文件约定

- 综合项目使用 `docs/projects/`、`J1/J2` 前缀；同样进入课程计划、sidebar、TRACKS 和源码导入检查。J页独立显示代码就绪与待上板状态。

- 章节页：`docs/<track>/<nn>-<slug>.md`，track ∈ `guide/c/build/stm32/rtos/esp32/gd32/lab`；`reference/` 放读者支撑页（术语速查/FAQ/关于/更新日志），无编号前缀，但同样要进 nav 与 sidebar。
- 编号前缀（frontmatter title 与 H1 一致）：`C`=c、`B`=build、`S`=stm32、`F`=rtos/freertos、`R`=rtos/rtthread、`对比`=rtos/compare、`P`=esp32、`G`=gd32、`实验 E`=lab。实例见 `docs/stm32/03-gpio.md`（"S3 GPIO"）。
- 每个 track 有 `index.md` 导览（路线表+精髓一句话），实例 `docs/rtos/index.md`。
- **每章 frontmatter 必填四项**：`title` / `status`（`done` 成稿 | `building` 骨架）/ `difficulty`（1|2|3）/ `minutes`。数字由 `scripts/gen-progress.mjs` 扫描这些字段生成 `docs/.vitepress/data/progress.json`（已 gitignore 的生成物，`docs:dev`/`docs:build` 自动前置执行），首页 `<LearningMap />` 与 README 状态段都从这里取数——**禁止在任何文档里手写"成稿 N 篇 / 动画 N 张"**，那是本站数字失真的根因。脚本对缺字段或非法值直接报错并非零退出，`npm run docs:gen` 必须成功；实验验证字段见 quality-contract.md。新增板块要同步登记 `scripts/gen-progress.mjs` 的 `TRACKS`（子路线共用导览页时给 `landing` 字段，否则地图生成死链）。
- 动画：`docs/public/anim/*.svg`（SMIL）；图片：`docs/public/images/{labs,boards}/`。页面一律用 **Markdown 图片语法** `![一句话描述](/anim/xx.svg)` 引用 public 内文件。原因不是风格：Markdown 图片引用会被 Vite 当作 import 处理——**构建时检查文件存在性并自动加 `/mcu/` base**（本批次构建曾因引用了不存在的 SVG 被这道门拦下）；raw `<img src="...">` 不被 Vite 解析，缺文件只在运行时 404。
- 相对链接必须带 `.md` 后缀且深度正确：rtos 子目录（freertos/rtthread/compare）跨板块链接用 `../../<track>/`（本任务曾集体写错成 `../`，靠死链检查兜住）。
- **工程完整源码必须站内内嵌，不许让读者跳 GitHub 读代码**：成稿章在"记忆锚点"前设 `## 附录：工程完整源码`，用 VitePress 代码导入 `<<< <相对路径>/code/<proj>/<file>`：路径相对**当前 md 文件**定位仓库根下的 code/（`docs/<track>/` 用 `../../`，`docs/rtos/freertos/` 等三层目录用 `../../../`；多一层会解析到仓库外 ENOENT，已踩过两次）。GitHub 链接只作"去仓库 star/提 issue"的附属入口，不作阅读路径。

## config.mts 纪律

- `docs/.vitepress/config.mts` 是唯一导航事实源：nav（八板块 + 「资料」下拉）、sidebar 按板块分组全量列出；搜索用 `provider: 'local'`（离线自建索引，不依赖外部服务）。
- **新页面必须同步四处**：① sidebar 对应组；② 本板块 `index.md` 路线表；③ 该章 frontmatter 四项元数据（缺项会让 `docs:gen` 告警）；④ 如涉及实验，`docs/lab/index.md` 实验总览。首页学习地图与 README 状态段**不需要**手工同步——它们读 `progress.json`。
- `ignoreDeadLinks: false` 是验收门禁，不得为通过构建改回 true；仓库内链接一律用真实地址（`https://github.com/zhuguang-ZFG/mcu/...`），禁止 `https://github.com/` 空占位。

## 主题

- `docs/.vitepress/theme/` = `index.ts`（继承默认主题）+ `custom.css` + 组件。
- 已有组件：`LearningMap.vue`（首页学习地图，`index.ts` 全局注册，数据源 `../data/progress.json`；骨架/成稿用 `status` 区分，点击跳板块导览页）。
- 已有专用类：`.memory-anchor`（记忆锚点框）、`.achievement`（成就清单）、`.lab-card`、动画 img 卡片化（`img[src*="/anim/"]`）。新样式沿用 BEM 风格的 `mcu-` 前缀或类语义名，勿改 VitePress 变量体系。
