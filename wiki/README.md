# Code Wiki：通往单片机之路（mcu-road）

> 本 Wiki 面向开发者，系统梳理仓库的整体架构、模块职责、关键函数、依赖关系与运行方式。
> 阅读顺序建议：01 → 02 → 03 → 04 → 05。

| 文档 | 内容 |
|---|---|
| [01-项目总览与架构](01-项目总览与架构.md) | 项目定位、五大子系统、内容生产数据流、质量哲学 |
| [02-模块详解](02-模块详解.md) | docs 站点 / code 固件 / scripts 闸门 / video 产线 / mcu-book 整书 / tests 与 CI / .trellis |
| [03-关键函数与数据契约](03-关键函数与数据契约.md) | 各子系统核心函数（含文件与行号）、frontmatter / projects.json / manifest / episode 等数据契约 |
| [04-依赖关系](04-依赖关系.md) | npm / Python / 外部工具链依赖，模块间调用关系，CI 工作流依赖 |
| [05-运行与开发指南](05-运行与开发指南.md) | 环境准备、全部 npm scripts、本地预览、质量门禁、固件/整书/视频构建、CI 流程 |

## 一分钟速览

- **这是什么**：开源深度教学书《通往单片机之路》的内容仓库 —— 寄存器级 STM32F407 × ESP32-S3 双路线、C 语言精髓、FreeRTOS/RT-Thread 双精讲、实物实验。在线站点 <https://zhuguang-zfg.github.io/mcu/>。
- **不是什么**：不是一个 Web 应用或固件库；代码服务于"内容生产与质量验收"。
- **技术底座**：VitePress 1.6（站点）· Node ESM 脚本（质量闸门）· Python（整书构建）· Playwright/puppeteer + ffmpeg（视频产线与 PDF）。
- **核心入口**：`package.json` 的 scripts 是几乎所有操作的统一入口；`npm run quality` 是发布前的完整闸门。
- **管理体系**：仓库由 Trellis 管理（`.trellis/`），AI 协作规范见 `AGENTS.md` 与 `.trellis/workflow.md`。
