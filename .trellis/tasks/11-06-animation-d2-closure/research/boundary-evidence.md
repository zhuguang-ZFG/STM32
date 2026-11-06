# D2 边界调查（本轮直接证据）

## 最小复现

当前 `docs/.vitepress/config.mts:152-156` 的 `anim-figure-tag` 在 block 前执行 `state.src.replace`。本轮 Node 内存探针从文件读取原正则与替换回调（只去掉回调参数的 TypeScript 注解），未编辑生产文件、测试或正文。

输入中的标签：`<AnimFigure src="/anim/toolchain-relay.svg" />`。

| 输入环境 | 预期 | 当前探针实际 |
|---|---|---|
| 普通独立行 | 转成动画 | 转为 `![](/anim/toolchain-relay.svg)` |
| 三反引号 vue 围栏内 | 保留组件原文 | 代码内容被改为 `![](/anim/toolchain-relay.svg)` |
| 四空格缩进 | 保留代码内容及代码块语义 | 变为无缩进 `![](/anim/toolchain-relay.svg)` |

该探针定位了首个偏离边界，但不替代真实 VitePress 渲染回归。尚未运行修改后的实现，不能宣称修复通过。

## 两个初始假设与区分实验

- H1：全局源码替换无视代码块上下文，在解析前已经改坏文本。
- H2：源码保持不变，是后续组件/内联解析阶段误认代码内容。
- 区分实验：仅调用从当前文件提取的替换规则，比较进入 block 前的文本。
- 结果：围栏与缩进例都已改变，H1 得到支持；H2 不能解释此最小复现，拒绝把后续渲染当成首因。不排除其他独立缺陷。

## 运行环境发现

两次直接解析器加载探针失败：Eval 的 createRequire 无法找到 vitepress；仓库 cwd 下 Node 可以解析 vitepress，但无法解析独立 markdown-it。因此拒绝“当前环境能从根目录直接 require markdown-it”的假设，不再重复解析器加载调用。

实际 `node_modules/vitepress/package.json:1-24` 显示已安装 1.6.4，导出 dist/node/index.js；`:59-78` 运行时依赖没有独立 markdown-it。后续应使用项目实际 VitePress 入口/renderer，避免新增依赖来绕过问题。

## 验证边界

- 当前仅源规则最小复现成功，不是完整渲染测试通过。
- `task_verify plan` 本轮返回 `unverified`、`verification-baseline-unavailable`、`changes=[]`、`checks=[]`。
- GitNexus list_repos 仅列出无关 clideck，索引 behind 11；没有本项目图谱证据，不重建无关索引。
- 旧任务和历史聊天中的门禁通过不计入本轮测试结果。

## 实际 VitePress renderer 探针（本轮随后执行成功）

使用 Node ESM `loadConfigFromFile`（vite）加载真实 config.mts，并通过 `createMarkdownRenderer`（vitepress）建立 renderer，内存输入，无生产文件修改。

- 旧规则启用：围栏 token 为 fence，但 content 已变为 `![](/anim/toolchain-relay.svg)`；四空格输入变为包含 name/markup 的 html_block，确实丢失代码语义。
- 仅在探针 renderer 上禁用 anim-figure-tag，并在 before-inline 观测：独立标签为顶层 html_inline，map [0,1]，紧随空 inline；围栏为 fence，内容是原标签；四空格为 code_block，内容是原标签；同行文字为 paragraph_open / inline / paragraph_close。
- 该证据拒绝“裸组件必为 html_block，可只扫描 html_block”方案。优选处理 block 后、inline 前完整独立 html_inline，不扫代码 token。
- scout 返回的 caption 方括号风险仍是未验证假设；不把它当作额外已确认缺陷，不引入门禁或语法扩展。

测试入口调查：package.json:40 使用 `node --test tests/*.test.mjs`；tests/docs-check.test.mjs 提供 Node fixture 风格；tests/browser/site.spec.mjs:39-74 为动画控件回归，playwright.config.mjs:12-17 使用 preview 24318。尚未实跑这些测试，本轮不报告它们通过。
