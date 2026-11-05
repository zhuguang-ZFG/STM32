# 贡献指南

这个项目只有一个质量标准：**读者看完能讲给别人听，还能在板子上做出来**。以下规范都是为这一条服务的。

## 1. 内容深度标准（四件套）

每个外设/驱动章节必须包含四件套，缺一不可：

| 件套 | 要求 |
|---|---|
| 功能配置 | 该功能全部配置位/配置字段的图解 + 配置流程（先什么后什么，为什么） |
| 引脚设置 | 引脚复用表、电气特性（速度/上下拉/驱动能力）、接线图 |
| 库文件解析 | 库/驱动源码逐行走查（SPL、ESP-IDF driver、FreeRTOS/RT-Thread 内核），引用真实函数名与文件名 |
| 代码分析 | 示例代码逐行注释；关键处下钻到汇编或寄存器位 |

事实纪律：

- 寄存器地址、引脚号必须有出处（RM0090 章节号 / datasheet / 官方原理图 / 板厂 wiki），写在正文里；
- 写不到的实事求是标注"以 XX 手册 §x.x 为准"，**禁止编造数值**；
- 引用第三方代码遵守其许可证，注明出处。

## 2. 写作风格契约

1. **钩子开场**：第一段是生活化类比或反直觉问题（≤60 字），禁止"本章将介绍"。
2. **三层递进**：直觉（类比+图）→ 机制（框图/时序）→ 实现（寄存器位/源码行）。不许跳过直觉层。
3. **记忆锚点**：每章一个（口诀/对比表/反例故事），用 `::: tip 一句话记住` 呈现。
4. **成就感闭环**：章首 10 分钟 quick win（先见现象）+ 章末"你做到了"清单 + `<div class="achievement">` 下一站引导。
5. **生动≠啰嗦**：每段必须有信息增量；禁鸡汤、禁表情轰炸、禁水字数；术语首次出现 = 类比 + 精确定义双轨。
6. **参考节奏**：野火《实战指南》式"硬件连接→逐寄存器→下载验证"的动手节奏，但我们必须讲透"为什么"。

## 3. 章节页模板

骨架页金样例：[`docs/c/06-abi-stack.md`](docs/c/06-abi-stack.md)。成稿章金样例：[`docs/stm32/00-env.md`](docs/stm32/00-env.md)。实验金样例：[`docs/lab/e01-blink.md`](docs/lab/e01-blink.md)，实验模板：[`docs/lab/template.md`](docs/lab/template.md)。

文件约定：

- 章节 `docs/<track>/<nn>-<slug>.md`，标题编号：C=c、B=build、S=stm32、F=FreeRTOS、R=RT-Thread、对比、P=esp32、实验 E=lab；
- **每章 frontmatter 必填三项**（全站进度靠它，缺项会被 `npm run docs:gen` 告警）：`status: done|building`（成稿/骨架）、`difficulty: 1|2|3`（入门/进阶/硬核）、`minutes: <int>`（预计学习时长，含动手）。`status` 判据是内容深度而不是文件长度——骨架页就算写满 300 行也是 `building`；
- 示例代码 `code/<track>/<nn>-<slug>/`，全部逐行注释，能独立构建（宿主可构建的工程照 `code/c/03-volatile` 的写法，README 里写清取证环境与版本）；
- 新页面必须登记进 `docs/.vitepress/config.mts` 的 sidebar，并更新 `docs/lab/index.md` 或板块 index 的路线表；`docs/reference/`（术语速查/FAQ/更新日志/关于我们与致谢）另有一组 sidebar 与 nav「资料」下拉；
- **数字一律不手写**：成稿篇数、动画张数、实验数、工程数由 `scripts/gen-progress.mjs` 扫描生成，首页地图与 README 状态段同源。新增章节/动画不需要改数字，改 frontmatter 即可。

## 4. 动画规范

完整细则见 `.trellis/spec/docs-site/animation.md`（色板与字号、SMIL 阶段槽位的坑、三件动效武器、站点内联机制）。要点：

- 形式：独立 `.svg` 于 `docs/public/anim/`，SMIL（`<animate>`/`<animateTransform>`，`repeatCount="indefinite"`），viewBox 宽 720；页面用 markdown 图片语法 `![一句话描述](/anim/xxx.svg)` 引用（构建期自动内联成 `<AnimFigure>`，随站点深浅主题换色；禁 raw `<img>`、禁外链播放器、禁 JS 依赖）。
- 必带 `<title>`/`<desc>`：`<desc>` 要把因果讲完，关动效的人只看得这两行。
- 颜色只能取规范色板：站点用一张固定映射表换主题 class，自造十六进制值或写 `rgba()` 底纹 = 深色模式漏网。
- **只有阶段切换不算动画**：每张图至少一处连续运动（爬线 / 生长箭头 / 节拍脉冲），且运动本身承载结论。**禁装饰性动画**——不能帮助理解的动画不如不放。
- 每个动画在 PR 描述里附"表达结论一句话"；深色模式截图一张。
- 现有动画（34 张，总数以 `npm run docs:gen` 为准）：`stack-frame`、`irq-entry`、`context-switch`、`gpio-config`、`boot-sequence`、`i2c-timing`、`queue-passing`、`semaphore-mutex`、`priority-inversion`、`dma-pingpong`、`list-insert`、`spi-timing`、`tcp-handshake`、`rcc-clock-tree`、`tim-pwm-counter`、`tim-input-capture`、`uart-frame`、`usart-txe-tc`、`dma-circular-buffer`、`task-create-stack`、`task-notification`、`event-group-wait`、`software-timer-service`、`heap4-coalesce`、`gpio-matrix-routing`、`idf-uart-events`、`ledc-timer-channel`、`gd32-rcu-clock`、`volatile-as-if`、`bus-matrix`（S1）、`memory-two-homes`（C1）、`elf-two-views`（B2）、`bitband-alias`（S1）、`sar-successive`（S9）。新增动画必须被至少一个章节引用，并在此登记。
- 视频嵌入：B 站/油管一律 `<VideoEmbed type="bilibili|youtube" id="…" title="…" />`（主题已全局注册）。**id 嵌入前必须验证真实**：B 站查 `api.bilibili.com/x/web-interface/view?bvid=<id>`、油管查 `youtube.com/oembed?url=...` 核对标题，禁止占位/猜测链接；每个视频配一句"与本章哪一段对照看"。

## 5. 实物与图片规范

- 接线图/原理图/波形：SVG 手绘，存 `docs/public/images/labs/` 或 `images/boards/`；
- **禁止伪造实物照片**。实拍照片规范：注明板卡型号、拍摄设备（示波器型号/逻辑分析仪型号），存 `docs/public/images/labs/<eid>/`；
- 实测数据（电流/波形参数）写明测量条件。

## 6. 提交流程

1. Issue 先聊：新章节/新实验先开 Issue 说清"读者能带走什么"；
2. PR 自检清单：**先跑 `bash scripts/local-gates.sh`（Windows：`powershell -File scripts/local-gates.ps1`）**，它逐项复跑 CI 的同一批门并逐条给结论（FAIL 非零退出、工具缺失记 SKIP）；
   - [ ] `npm run docs:gen` 零告警（每章 frontmatter 的 `status` / `difficulty` / `minutes` 齐备）；
   - [ ] `npm run docs:build` 零错误、零死链（锚点另由 `npm run pages:check` 对构建产物核对）；
   - [ ] `npm run docs:check` 零报错（全站链接与锚点、Markdown 卫生、仓库自链、**正文里的手写数字与真源对账**）；
   - [ ] 动过整书：`npm run book:check` + `python mcu-book/check_pdf.py` + `python mcu-book/publish_downloads.py --verify .temp/book-downloads` 全过；
   - [ ] 动过 Python：`python -m ruff check .` 零命中（只抓真错误；排除项必须在 `ruff.toml` 里写明理由）；
   - [ ] `grep -rn "TODO|待补充|placeholder" docs/` 无命中；
   - [ ] 四件套落位、风格契约六条逐项过；
   - [ ] 事实出处已标注；
   - [ ] 新页面已进 sidebar；新增路线/章节后首页地图与 README 状态段自动跟随，**不要手写数字**（手写的会被 `docs:check` 抓住）；
   - [ ] 新增板块时同步登记：`config.mts` 的 nav/sidebar + `scripts/gen-progress.mjs` 的 `TRACKS`；
   - [ ] 改了版本/引用口径：`CITATION.cff` 与根 `CHANGELOG.md` 同步（`docs:check` 会对账 manifest 与站点更新日志）。
3.  Commit message：`<板块>: <动作> <主题>`，如 `stm32: 成稿 S3 GPIO 章`。

## License

贡献即视为同意以 [Apache-2.0](LICENSE) 发布。
