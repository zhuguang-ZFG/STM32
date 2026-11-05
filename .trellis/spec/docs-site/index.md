# docs-site 规范索引

VitePress 站点的一切（页面、侧边栏、主题、动画、图片）。

| 文件 | 内容 |
|---|---|
| [logger-contract.md](logger-contract.md) | 双板综合项目、SAMPLE/TLV、配置恢复与运行期并发合同 |
| [quality-contract.md](quality-contract.md) | 工程清单、严格元数据、实验验证状态、CI 与浏览器回归合同 |
| [structure.md](structure.md) | 目录约定、config/sidebar 纪律、frontmatter 与编号体系 |
| [content.md](content.md) | 章节页模板执行细则、风格落地检查、动画与图片操作 |
| [animation.md](animation.md) | 动画视觉与时间轴规范：色板/字号、SMIL 阶段槽位、三件动效武器、站点内联机制、`anim-audit.html` 版式审计（墨水盒判压字） |
| [architecture-diagram.md](architecture-diagram.md) | 架构图层规范：动画/架构图/题图三分工、stack-diagram 产图工作流、图标来源契约、印刷兼容与 CLAIMS 口径 |
| [presentation-assets.md](presentation-assets.md) | 精排导读与金句卡：同源生成、独立 HTML 入口、过期检查、文字基线、截图与浏览器验收 |

## 动手前必读

- 改页面/导航/frontmatter：先读 [structure.md](structure.md)，再三处同步（文件、sidebar、板块路线表）。
- 改正文写法/动画/图片：读 [content.md](content.md) 与 [animation.md](animation.md)；寄存器/引脚事实按 `CONTRIBUTING.md` 给出处。
- 改工程登记、实验状态、CI 或质量门：读 [quality-contract.md](quality-contract.md)；字段真源是 `code/projects.json` + `scripts/project-catalog.mjs`。
- 改导读或金句卡：读 [presentation-assets.md](presentation-assets.md)；不要另建一套截图/过期检查。
- 改架构图：读 [architecture-diagram.md](architecture-diagram.md)；本书印前复用同一组矢量源，不复制制图规范。
- 改跨层接口（共用代码、整书、RTOS、GD32、视频）：先看 [总索引](../index.md) 的"修改路径 → 必读层"。

## 质量检查

| 改动 | 检查 |
|---|---|
| 页面/导航/链接 | `npm run docs:build`（死链零错误）、`npm run nav:check`、`npm run pages:check` |
| 元数据/实验状态 | `npm run docs:gen`、`npm run docs:check`、`npm run reading:check` |
| 搜索/分享/性能/无障碍 | `npm run seo:check`、`npm run search:check`、`npm run perf:budget`、`npm run a11y:check`（均需先构建） |
| 导读/金句卡 | `npm run guide:check`、`npm run cards:check` |
| 整站回归 | `npm run quality`；浏览器层另跑 `npm run test:browser` |

## 快速命令

```bash
npm run docs:dev      # 本地预览
npm run docs:build    # 验收门禁：死链检查开启，必须零错误
```

## 金样例（模仿对象）

- 骨架章：`docs/c/06-abi-stack.md`
- 成稿章：`docs/stm32/00-env.md`、`docs/esp32/00-env.md`
- 实验：`docs/lab/e01-blink.md`（模板 `docs/lab/template.md`）
