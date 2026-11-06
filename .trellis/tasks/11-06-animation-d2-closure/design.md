# 技术设计：将 D2 兼容转换移入已解析的非代码块

## 决策

移除 `config.mts:152-156` 的全局 `state.src` 重写。优先在 block 解析完成后的 token 边界处理独立组件行，复用现有 `emit(name, caption)`，而非手写围栏状态机或靠更多正则排除代码。

这是单一原因修正：保留输入源码，由 Markdown 解析器决定哪些内容属于代码。不要同时改动画样式、时长、模态框或印前链路。

## 处理边界与数据流

1. 本轮已使用实际 `loadConfigFromFile` + `createMarkdownRenderer` 加载项目配置，并禁用旧规则后观测 `before('inline')`：独立标签产生顶层 `html_inline`（map `[0,1]`）及空 `inline`；围栏是 `fence`，四空格代码是 `code_block`，文字同行标签则在段落 `inline.content` 中。
2. 因此选择 block 解析后、inline 解析前的 core rule：只处理带单行 map、内容完整匹配独立组件标签的顶层 `html_inline` token，复用 `emit()`。不扫描段落 inline 子节点，不假设标签为 `html_block`，不建立尚无证据需要的兼容分支。
3. 只匹配当前支持的 `/anim/[\w-]+.svg`、双引号 src、可选 caption 和自闭合形式。标签必须独占源码一行；以 token map 回看该行确认无其他文字。不匹配正文内联片段，不扫描所有 token 的 content。
4. `fence`、`code_block` 及内容完全不改。未命中标签、同行文字和原有图片动画路径保持原样；不新增验证策略或缺图 fallback。
5. 命中后通过 `emit()` 生成 `html_block` 并保留 map，避免段落结构错误与 caption 的 Markdown 二次解析；继续使用既有属性转义。

命中后替换该组件 token；对解析器紧随其后、同 map 且 content 为空的 inline token，只在行为实验确认必要时处理。所有其他 token 保持不变。若后续边界实验推翻该方案，先记录证据再调整，不叠加猜测性分支。

## 方案比较

- **选 token 边界**：借助解析器已有的围栏/缩进识别，并复用 emit；局部改动，不引入依赖。
- 不选更复杂的源码正则/围栏计数器：嵌套列表、波浪号和变长围栏容易漏。
- block rule 是备选，不与 token 方案并存；它需正确处理缩进、容器、silent 模式与规则优先级，只有实际 token 证据表明优选不可用时才采用。

## 兼容和工作区保护

- 保留图片语法与独立组件语法两个公开入口。不要改三页 md 来绕过问题。
- 只修生产配置中的转换规则和相关说明；既有 `emit`、SVG 装饰及无关插件不重构。
- `.trellis/spec/docs-site/animation.md:61-68` 当前声明 block 前源码改写且强制挂载时机，实施时改成真实 parser-aware 行为；不沿用错误的“必须全局前置改写”约束。
- 保留所有未提交工作。回退仅撤销本任务的局部改动，不 reset 整文件。

## 回归边界

测试必须调用真实配置/renderer，不复制正则作为正式回归，也不以源码字符串断言代替渲染行为。检查 code token/渲染后的代码文本、正文组件、caption 值与段落结构，而非仅统计非空输出。

新增/修改测试或 fixture 是待审查变更：保持原有断言和 runner/policy 不动，报告实际运行结果，但新用户回合建立基线前仍单独标为未验证。
