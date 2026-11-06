# 实施计划与执行记录

## 顺序

1. 用户已审阅并批准实施，`task.py start` 已将状态变为 in_progress；当前保留该状态等待新增回归审查，不自动归档或提交。
2. 加载开发/TDD规范；使用实际 VitePress renderer 与当前项目配置建立行为回归。建议新增 `tests/animation-markdown.test.mjs`，沿用 Node test harness；不改 package.json、runner、已有断言或 CI。
3. 先证明同一回归在当前旧规则失败：围栏文本被改变，四空格代码丢失 code_block。保留原始输出。新增测试/fixture 必须请求用户审查；新回合基线建立前不宣称其为 operator 验证通过。
4. 只替换 config.mts 的源码全局改写为设计中的 token 边界转换，复用 emit。先按一个原因修改，再运行相同回归；不得同时加新语法、fallback、门禁或其他体验修复。
5. 边界矩阵：反引号/波浪号围栏、四空格与 tab 代码、混合正文代码、LF/CRLF、0–3 空格正文组件、普通/带 caption 组件、图片语法、同行正文不被改写。caption 检查中文、方括号、&、< 的字面值与转义。不扩大属性顺序/引号形式契约。
6. 正式回归使用 `loadConfigFromFile`（vite）和 `createMarkdownRenderer`（vitepress），直接加载生产配置，不复制规则。对 fence/code_block 的内容、组件 name/markup/caption、段落结构作行为断言；失败信息必须指向消费者可见结果。
7. 运行窄范围命令 `node --test tests/animation-markdown.test.mjs`，然后既有 `npm run test`、`npm run docs:build`、`npm run book:check`。构建会执行 docs:gen，产生的无关改动必须调查，不覆盖用户工作。
8. 启动新的 preview 实例（不要沿用 rebuild 前的缓存服务），真实浏览三页：toolchain-relay / swd-debug-chain / embedded-c-diff，逐页检查 SVG、控件、data-anim、caption 和控制台。只为 smoke 使用临时内容时须先说明其 runner-input 审查属性；优先内存 renderer，不改正文。
9. 保留 D1/D3/D4：窄屏放大横向可滚、关闭焦点恢复、主时长不回退。优先复用现有 browser suite；实际 UI smoke 用新证据，不沿用聊天历史。
10. 修复验证后局部更新 `.trellis/spec/docs-site/animation.md` 的实现描述。调用 `task_verify run`，分开记录 passed/failed/unverified；测试新增未审查、baseline unavailable 或空 checks 都不能当作通过。
11. 保存 problem_checkpoint；交付变更与证据并请求测试审查。不提交、不推送、不合并，不自动启动印前工作。

## 回退与风险

- config.mts 与规范已有前轮修改；只撤销本任务新增的 hunk，禁止整文件 checkout/reset。
- 不安装独立 markdown-it：已验证 VitePress 自带 renderer 可直接用于探针。
- 不接受只匹配 html_block 的方案：真实 VitePress 在 before-inline 边界产生顶层 html_inline。
- 若两次同类动作失败，先记录拒绝假设、改查证据再继续；权限或认证不能旁路。

## 当前证据状态

- 单因生产修复、规范更新、同一回归 RED→GREEN、Node 全套与 build/book/browser/a11y/anim 检查及真实三页 smoke 均已完成；准确输出见 `research/implementation-evidence.md`。
- 新增 `tests/animation-markdown.test.mjs`：有效旧实现 4 pass/8 fail，修复后 12 pass/0 fail，未改 runner/policy 或既有断言。仍待用户审查与新回合基线。
- `task_verify run` 返回 unverified / project-or-git-baseline-unavailable，checks=[]；不宣称 operator-configured checks 通过。
