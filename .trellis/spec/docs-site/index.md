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

## 快速命令

```bash
npm run docs:dev      # 本地预览
npm run docs:build    # 验收门禁：死链检查开启，必须零错误
```

## 金样例（模仿对象）

- 骨架章：`docs/c/06-abi-stack.md`
- 成稿章：`docs/stm32/00-env.md`、`docs/esp32/00-env.md`
- 实验：`docs/lab/e01-blink.md`（模板 `docs/lab/template.md`）
