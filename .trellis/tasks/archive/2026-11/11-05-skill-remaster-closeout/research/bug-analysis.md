# Bug Analysis：独立导读接入与静态锚点误报

## 1. Root Cause Category

- **B 跨层契约 / D 测试覆盖缺口**：独立 HTML 由文件直接打开可用，VitePress 点击时却按 SPA 页加载；原文与产物都存在，构建死链门无法发现。
- **E 隐式假设**：原 pages-check 假设 HTML 内一切 `href="…"` 都是属性，未区分 script/style 中的选择器字符串；接入内联滚动定位后误报。
- **C 样式传播**：原模板 hero 文本为浅色，外部覆盖仅改背景为浅色，标题虽在 DOM 内却不可读。

## 2. Why Fixes Failed

- 首轮 URL 等待超时，随后真点击发现 VitePress 路由拦截。按已安装 router.js 的明确条件给入口 `target="_self"`，使用相对地址正常全页载入。
- 一度考虑改脚本里的选择器串来避开扫描；发现这只是掩盖检查器缺口，未保留该改法，最终屏蔽 script/style 文本，并用合成 HTML 证明真实错误仍报第 6 行。
- 单看 DOM/宽度检查漏掉白底浅色标题。截图复核后把 hero 背景、标题、引句与照片整组覆盖，390/1440 正式浏览器回归新增标题/背景异色断言。
- PPT 验证途中出现的 700ms 导航锁、后台计时刷新、冻结时自动翻页暂停以及 switch 的隐藏 input，均为测试驱动方式或既定功能，不是生产缺陷；按用户真实控件/可见标签验证，不为测试去改演讲运行时。

## 3. Prevention Mechanisms

| 优先级 | 机制 | 动作 | 状态 |
|---|---|---|---|
| P0 | 浏览器集成回归 | 两种视口从书籍入口实际点击，断言独立页身份与标题可读 | DONE |
| P0 | 检查器回归 | script/style 伪 href 不计数，真实错误保留行号 | DONE |
| P0 | 同源摘要门 | source/generator/HTML 摘要前置 docs:build | DONE |
| P1 | 设计规范 | 独立 HTML 路由、hero 配色、临时产物与正式源码边界 | DONE |

## 4. Systematic Expansion

- 所有放进 public 的独立 HTML 都有同类路由风险，维护时按 `presentation-assets.md` 真点击验收。
- 同类内联脚本可触发锚点正则假阳性，因此修复检查器本身；不扩大全局例外，也不降低缺锚点检查。
- 用截图补几何检查的视觉盲点，不能把「DOM 存在」当「文字可读」。

## 5. Knowledge Capture

- [x] `.trellis/spec/docs-site/presentation-assets.md` 七段可执行契约。
- [x] docs-site 索引与 quality-contract 同步。
- [x] 单元测试和正式浏览器测试落盘。
- 本仓库没有 `src/templates/markdown/spec/`，不创建无关模板树；规范提交与当前任务代码同批，等待 Phase 3.4 确认。
