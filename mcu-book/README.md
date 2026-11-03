# 通往单片机之路（整书版）

这是一份由仓库 94 章教程构建的**独立整书**，不是把文章拼接起来：

- 11 个分部（C 精髓 → 构建全过程 → STM32F407 寄存器 → FreeRTOS → RT-Thread → 双 OS 对照 → ESP32-S3 → GD32 双系 → 实物实验 → 双板项目 → AI 辅助开发），每部有共同目标与统计扉页；
- 94 章逐章配「本章罗盘」：问题 / 交付 / 边界 / 依据锚点（来源注册表 75 项）；
- 站点方言全部静态化：`::: tip/warning` 容器、`<AnimFigure>`、`<QuizBank>`（题目进正文、答案进附录 C）、`<LabStatus>` 实验信息卡、视频与交互计算器替换为离线卡片；
- 141 张机制动画与架构图以内嵌资源收录——HTML 版动画打开即播（SMIL），PDF 版为静态首帧，每张带图注；
- 附录七份：A 工程深读（IDLE→帧协议的五契约）· B 47 个配套工程索引 · C 自测参考答案（13 组自动汇入）· D 术语速查 · E 来源、版本与许可 · F 常见问题 · G 开源项目与社区地图；
- HTML 把所有图片内嵌为 data URI，断网单文件可读；PDF 用同一份 HTML 打印，带标题书签与页码。

当前版本：**v1.0.0 · 2026-10-23**（口径见 `manifest.json`）。

## 构建

从仓库根目录运行：

```bash
python mcu-book/build_html.py            # dist/mcu-deep-book.html
python mcu-book/build_html.py --pdf      # 追加 dist/mcu-deep-book.pdf
python mcu-book/build_html.py --check    # 临时目录验证整书契约
```

PDF 需要本机 Chrome/Edge（自动探测，也可 `--browser` 显式指定）；依赖版本见 `requirements.txt`（HTML 只需 Python-Markdown；PDF 另需 Playwright 与 PyMuPDF）。npm 侧入口：`npm run book:check / book:html / book:pdf`。

**在线阅读**：push 到 main 后，站点部署流水线会把整书一并发布到 **<https://zhuguang-zfg.github.io/mcu/book/mcu-deep-book.html>**（PDF 同目录），由 `quality.yml` 构建并随 `docs-site` artifact 一起上传。

## 质量检查

```bash
python -m unittest discover mcu-book/tests -v
python mcu-book/build_html.py --check
```

整书契约（构建期与测试双重把关）：

- manifest 与 `docs/` 的 94 个章节文件一一对应，一章不多、一章不少，全部 `status: done`；
- 94 份章节罗盘齐全（问题/交付/边界非空，来源 ID 已注册）；
- 七份附录入书；附录 B 覆盖 `code/projects.json` 的全部工程 ID；
- 13 份测验 JSON 与正文的 `<QuizBank>` 双向对账：题目嵌入正文、答案汇入附录 C，无孤儿；
- 所有本地图片/动画存在并已内嵌（data URI），无外链图；站内 `.md`/`.html` 链接全部改写为整书锚点，`#fragment` 零断链；
- 组件残留（QuizBank/AnimFigure/LabStatus/VideoEmbed/:::）会让构建直接失败。

阅读与打印行为（构建期注入）：打印/PDF 前自动展开全部 `<details>` 折叠块——章节「参考答案」等内容不许在纸书里失踪（Chromium 的 `page.pdf()` 不触发 beforeprint，构建器显式展开）；屏幕上 SMIL 动画离屏自动暂停、回视口续播，系统「减少动效」偏好下停在首帧，与在线站点 AnimFigure 同一口径。

PDF 书签由构建器把 Chromium 的扁平标题大纲重排为**部(1) → 章(2) → 节(3)** 三级树：结构条目（11 部 / 94 章 / 7 附录）逐一在 level-1 大纲中定位，找不到即构建失败；匹配忽略空白差异并跳过书内目录页的同名条目。站点章节页顶部的「本章罗盘」卡片（`docs/.vitepress/theme/ChapterCompass.vue`）读取同一份 `manifest.json`——站点展示与整书内容天然同源。

## 内容维护

| 内容 | 唯一维护位置 |
| --- | --- |
| 94 章正文 | `docs/<section>/`（站点与书同源；书不改动原文） |
| 分部、章节罗盘、来源注册表 | `mcu-book/manifest.json` |
| 七份附录 | `mcu-book/book/`（C 的题目答案由构建期从测验 JSON 注入） |
| 构建与 PDF 输出 | `mcu-book/build_html.py` |
| 整书契约回归 | `mcu-book/tests/test_build.py` |

新增/重命名章节时：先在 `docs/` 落文件，再在 `manifest.json` 对应分部登记并补罗盘——构建器拒绝"漏掉一章让构建继续"。新增来源先注册 `sources`（含权威层级、冻结点、访问日期、许可边界），再在罗盘里引用。

## 与姊妹项目的关系

整书方案（分部目标、章节罗盘、离线单文件、契约测试）参考同工作区 [STM32 知识库的 stm32-book](https://github.com/zhuguang-ZFG/STM32/tree/main/stm32-book)，未复制其正文；本书针对本站方言（VitePress 容器/组件、frontmatter、测验 JSON、SMIL 动画库）独立实现构建器。

## 许可

- 正文、版式、动画与构建器：[Apache-2.0](https://github.com/zhuguang-ZFG/mcu/blob/main/LICENSE)（与仓库一致）；
- 被引用的上游手册/规范/论文/源码只作链接与事实引用，不随书再分发，各归其权利人。
