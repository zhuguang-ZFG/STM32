# 第十一部「AI 辅助开发」外部官方来源采集（A0–A5）

- 采集日期（accessed）：2026-10-27（全部条目统一）
- 采集口径：只收官方一手来源（厂商官方文档 / 官方 spec / 官方博客 changelog / 官方仓库 README）。社区博客、论坛、视频均不作权威来源，仅个别作线索且不引用。
- 性质标注：每条事实注明【能力描述】【规范定义】【营销话术】；官方说法模糊处显式标「官方未明确」。
- 用法：§1 的 JSON 数组可直接并入 `mcu-book/manifest.json` 的 `sources`（并入时补 `license`/`scope` 两字段以贴齐既有 schema；id 用 `ai-` 前缀避免与既有 a1–e60 撞号）。§2 为逐条事实底稿，含可逐字引用的英文原句与版本/日期线索。
- 时效提示：五家文档均处于高频改版期（VS Code 文档 10/21 刚重组 Agents 章节、GitHub Docs 的 coding-agent 页已 301 到 Copilot on GitHub.com、MCP spec 已到协议版本 2026-07-28）。成书引用时以来源卡 + 访问日期口径「界面与版本会变，方法论不变」。

## 1. drop-in JSON 条目（14 条）

```json
[
  {
    "id": "ai-copilot-vscode-overview",
    "title": "Build with AI in VS Code（agents 总览；原 Copilot agent mode 文档现汇入此体系）",
    "authority": "Microsoft — Visual Studio Code 官方文档",
    "url": "https://code.visualstudio.com/docs/agents/overview",
    "snapshot": "页面标注 10/21/2026；docs 已将 chat/agent mode 重排为 Agents 章节，旧 /docs/copilot/chat/chat-agent-mode 已跳转",
    "accessed": "2026-10-27",
    "note": "A0 工具地图（VS Code 内 agent 定位与 harness 概念）；A3（agent loop 官方定义、permissions/approvals 权限机制、MCP servers 接入）；A4（『AI can produce incorrect code…You remain responsible』）。"
  },
  {
    "id": "ai-copilot-vscode-agentmode-blog",
    "title": "Introducing GitHub Copilot agent mode (preview) — VS Code 官方博客",
    "authority": "Microsoft — Visual Studio Code 官方博客",
    "url": "https://code.visualstudio.com/blogs/2025/02/24/introducing-copilot-agent-mode",
    "snapshot": "2025-02-24 发布；agent mode 首次以 preview 亮相的公告文",
    "accessed": "2026-10-27",
    "note": "A3 工具流：agent 模式『读错误输出—自动修正—循环直至任务完成』工作机制的一手时间锚点与机制描述。"
  },
  {
    "id": "ai-copilot-vscode-cpp",
    "title": "C/C++ for Visual Studio Code（C/C++ 语言支持页）",
    "authority": "Microsoft — Visual Studio Code 官方文档",
    "url": "https://code.visualstudio.com/docs/languages/cpp",
    "snapshot": "页面标注 10/21/2026",
    "accessed": "2026-10-27",
    "note": "A0 嵌入式 C 工作流可用性：Microsoft C/C++ 扩展（ms-vscode.cpptools）提供 IntelliSense/调试，同页确认 GitHub Copilot 在 C/C++ 工作流内提供编码建议——即嵌入式 C 开发在 VS Code 内可直接使用 Copilot 全家桶。"
  },
  {
    "id": "ai-copilot-github-cloud",
    "title": "GitHub Copilot on GitHub.com（含 Copilot cloud agent；旧 about-coding-agent 页 301 至此）",
    "authority": "GitHub 官方文档",
    "url": "https://docs.github.com/en/copilot/concepts/copilot-surfaces/copilot-on-github",
    "snapshot": "页面无显式日期（docs.github.com 持续更新），2026-10-27 抓取；文内已含 cloud agent / code review / automations 新口径",
    "accessed": "2026-10-27",
    "note": "A0 云端 agent 定位；A3（cloud agent 在 ephemeral 云开发环境编辑文件、跑测试与 linter）；A4（官方明示 59 分钟会话上限、单分支单 PR 限制，以及『Logs do not replace your own review and testing』『can produce incorrect or suboptimal code, including…security vulnerabilities』）。"
  },
  {
    "id": "ai-copilot-ccr-cpp",
    "title": "GitHub Copilot code review now supports C, C++, Kotlin, and Swift — GitHub Changelog",
    "authority": "GitHub 官方 changelog",
    "url": "https://github.blog/changelog/2025-04-23-github-copilot-code-review-now-supports-c-c-kotlin-and-swift/",
    "snapshot": "2025-04-23 发布",
    "accessed": "2026-10-27",
    "note": "A0/A4 嵌入式 C 可用性：Copilot code review 自 2025-04 起支持 C/C++（覆盖 PR 中逾 90% 文件类型）；配合 Using GitHub Copilot code review 文档（docs.github.com）可见评审入口覆盖 VS Code / Visual Studio / JetBrains（含 CLion）/ Xcode / gh CLI。"
  },
  {
    "id": "ai-claude-code-overview",
    "title": "Claude Code Docs — Overview",
    "authority": "Anthropic 官方文档（code.claude.com/docs）",
    "url": "https://code.claude.com/docs/en/overview",
    "snapshot": "页面无显式日期，2026-10-27 抓取；内容已含 Desktop/Web 表面、Agent SDK、scheduled tasks 等 2026 年新口径",
    "accessed": "2026-10-27",
    "note": "A0 工具地图（Claude Code 定义与四种表面：terminal/IDE extension/desktop/web）；A1（CLAUDE.md 官方说法）；A3（MCP 官方说法、hooks、skills、sub-agents、CLI 可管道化 `claude -p`）。"
  },
  {
    "id": "ai-claude-code-memory",
    "title": "How Claude remembers your project（memory 机制页）",
    "authority": "Anthropic 官方文档",
    "url": "https://code.claude.com/docs/en/memory",
    "snapshot": "页面无显式日期；正文引用 CLI v2.1.211–v2.1.285 行为差异，判定为 2026 年下半年现行版本",
    "accessed": "2026-10-27",
    "note": "A1/A3 记忆机制底稿：CLAUDE.md（user/project/local/managed 四作用域、目录层级加载、@import）与 auto memory（~/.claude/projects/<project>/memory/、MEMORY.md 索引首 200 行或 25KB 载入）；AGENTS.md 兼容；『Claude treats them as context, not enforced configuration』——A4 幻觉/纪律防御的制度化对照。"
  },
  {
    "id": "ai-claude-code-repo",
    "title": "anthropics/claude-code — 官方仓库 README",
    "authority": "Anthropic 官方 GitHub 仓库",
    "url": "https://github.com/anthropics/claude-code",
    "snapshot": "README 现行版，2026-10-27 抓取",
    "accessed": "2026-10-27",
    "note": "A0 agentic coding 一手定义：『an agentic coding tool that lives in your terminal, understands your codebase, edits files, runs commands』——比 overview 页营销语更贴『结对工程师』口径。"
  },
  {
    "id": "ai-cursor-docs",
    "title": "Cursor Documentation 首页（产品定位）",
    "authority": "Anysphere — Cursor 官方文档",
    "url": "https://cursor.com/docs",
    "snapshot": "页面无显式日期；Models 表已列 Claude Opus 5.5 / GPT-5.6 / Gemini 3.8 等 2026 下半年模型，判定为现行版",
    "accessed": "2026-10-27",
    "note": "A0 工具地图：『Cursor is a coding agent for building ambitious software』——官方把整款产品定位为 coding agent 而非『带 AI 的编辑器』（定位语，部分属营销口径，引用时取能力句不取形容词）。"
  },
  {
    "id": "ai-cursor-agent",
    "title": "Cursor Docs — Agent（Agent 机制总览）",
    "authority": "Anysphere — Cursor 官方文档",
    "url": "https://cursor.com/docs/agent/overview",
    "snapshot": "页面无显式日期，2026-10-27 抓取；含 /goal、side chats 等 2026 新特性",
    "accessed": "2026-10-27",
    "note": "A3 工具流：Agent 三构件（Instructions/Tools/Model）；工具清单（编辑文件、跑终端命令、浏览器、图片生成、提问澄清）；『There is no limit on the number of tool calls』；Checkpoints 快照回滚；运行中 steering/排队消息——与 VS Code/Claude Code 的工具流图互为对照。"
  },
  {
    "id": "ai-cursor-run-modes",
    "title": "Cursor Docs — Run Modes（Auto-review / Allowlist / Run Everything 与沙箱）",
    "authority": "Anysphere — Cursor 官方文档",
    "url": "https://cursor.com/docs/agent/security/run-modes",
    "snapshot": "页内 Changelog 表：v3.6（2026-05-29）Auto-review 成推荐默认、v3.23（2026-10-01）新增 Read access Workspace 模式——日期线索以此表为准",
    "accessed": "2026-10-27",
    "note": "A3 权限与安全边界主来源：三档运行模式、后端 LLM 分类器（可读 ReadFile/Grep/Glob/ListDir）、『Auto-review is not a security boundary』、macOS Seatbelt / Linux Landlock+seccomp 沙箱、Cloud Agents 不走 Run Modes。"
  },
  {
    "id": "ai-mcp-spec",
    "title": "Model Context Protocol Specification（latest，协议版本 2026-07-28）",
    "authority": "Model Context Protocol 官方规范（现隶属 Linux Foundation AAIF）",
    "url": "https://modelcontextprotocol.io/specification/latest",
    "snapshot": "协议版本 2026-07-28（latest 别名解析至此）；规范用语遵循 BCP 14 / RFC 2119",
    "accessed": "2026-10-27",
    "note": "A3 MCP 是什么的一手规范定义：开放协议、JSON-RPC 2.0、Hosts/Clients/Servers 三方、Server 三大特性 Resources/Prompts/Tools、安全原则（用户明示同意、工具调用前须授权）——ai-mcp-toolflow.svg 的规范层底稿。"
  },
  {
    "id": "ai-mcp-architecture",
    "title": "MCP — Architecture overview",
    "authority": "Model Context Protocol 官方文档",
    "url": "https://modelcontextprotocol.io/docs/learn/architecture",
    "snapshot": "对应协议版本 2026-07-28，2026-10-27 抓取",
    "accessed": "2026-10-27",
    "note": "A3 架构图底稿：host 为每个 server 建一个 client；本地 STDIO server 通常服务单 client、远程 Streamable HTTP 服务多 client；两层划分（data layer / transport layer）；三大 primitives 定义与 */list、tools/call 方法；声明 LSP 式生态标准化愿景。"
  },
  {
    "id": "ai-mcp-servers",
    "title": "modelcontextprotocol/servers — 官方参考实现仓库 README",
    "authority": "MCP steering group 官方仓库",
    "url": "https://github.com/modelcontextprotocol/servers",
    "snapshot": "README 现行版（仓库 91.6k stars，2026-10-27 抓取）；reference servers 仅 7 个，更多服务器走 MCP Registry",
    "accessed": "2026-10-27",
    "note": "A3『官方 reference servers 有哪些类别』的直接答案：在册 reference 为 Everything/Fetch/Filesystem/Git/Memory/Sequential Thinking/Time；GitHub、GitLab、Google Drive、Postgres、SQLite、Slack 等已归档至 servers-archived；官方明示其为教学示例『not as production-ready solutions』。"
  },
  {
    "id": "ai-mcp-anthropic-donation",
    "title": "Donating MCP to the Agentic AI Foundation — Anthropic 官方公告",
    "authority": "Anthropic 官方新闻",
    "url": "https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation",
    "snapshot": "2025-12 公告（Linux Foundation 2025-12-09 新闻稿口径一致）",
    "accessed": "2026-10-27",
    "note": "A0/A3 治理事实：MCP 由 Anthropic 捐赠给 Linux Foundation 下设 Agentic AI Foundation（与 Block goose、OpenAI AGENTS.md 同为创始项目；Google/Microsoft/AWS/Cloudflare/Bloomberg 支持）；官方 Registry 上线；2025-11-25 spec 引入异步操作、无状态化、server 身份与官方 extensions。"
  }
]
```

## 2. 逐工具事实底稿（断言 + URL + 版本/日期线索 + 性质标注）

### 2.1 GitHub Copilot（VS Code 内 agent / 嵌入式 C 可用性 / 云端 agent）

1. **【能力描述】VS Code 内 agent 可跨文件自主完成任务**："For a task that spans files and tools, an agent can find relevant code, make changes, and run checks without you directing each search, edit, and test run. You describe the outcome, review the changes, and verify the result."
   出处：https://code.visualstudio.com/docs/agents/overview ｜ 日期线索：页脚 10/21/2026
2. **【规范定义】agent loop 官方定义**："An agent uses a language model to reason about your request and tools to act on your development environment…This repeated reasoning, action, and validation is the **agent loop**."
   出处：https://code.visualstudio.com/docs/agents/overview ｜ 日期线索：10/21/2026 ｜ 支撑 A0/A3 概念段。
3. **【能力描述】agent mode 自主纠错循环**（首次 preview 公告）："It responds to compile and lint errors, monitors terminal and test output, and auto-corrects in a loop until the task is completed."
   出处：https://code.visualstudio.com/blogs/2025/02/24/introducing-copilot-agent-mode ｜ 日期线索：2025-02-24 ｜ 支撑 A3「把错误粘给模型」与 agent 自迭代的差异论述。
4. **【能力描述】嵌入式 C 工作流可用性**：VS Code 的 C/C++ 语言页确认 "GitHub Copilot provides coding suggestions as you type in your editor"，且 Microsoft C/C++ 扩展（ms-vscode.cpptools）提供 IntelliSense 与调试——即嵌入式 C/C++ 工程在 VS Code 内可完整使用 Copilot 补全 + chat + agent。
   出处：https://code.visualstudio.com/docs/languages/cpp ｜ 日期线索：10/21/2026 ｜ 官方未明确：未单独论述交叉编译（ARM GCC 工具链）场景下 agent 跑构建命令的专门适配，正文只宜引「C/C++ 是一等支持语言」级断言。
5. **【能力描述】Copilot code review 支持 C/C++**："GitHub Copilot code review now supports C, C++, Kotlin, Swift, and several other popular languages…covers over 90% of the file types typically found in pull requests."
   出处：https://github.blog/changelog/2025-04-23-github-copilot-code-review-now-supports-c-c-kotlin-and-swift/ ｜ 日期线索：2025-04-23。评审入口跨 VS Code / Visual Studio / JetBrains（含 CLion）/ Xcode / `gh pr create --reviewer @copilot`（https://docs.github.com/en/copilot/how-tos/use-copilot-agents/use-code-review ，2026-10-27 抓取）。
6. **【能力描述+边界】云端 Copilot cloud agent**："Copilot cloud agent can research a repository, plan changes, and implement them in the background. It can edit files and run tests and linters in an ephemeral cloud development environment"；硬限制——单仓库范围、单分支、每任务一个 PR、"Each Copilot cloud agent session has a maximum execution time of 59 minutes."
   出处：https://docs.github.com/en/copilot/concepts/copilot-surfaces/copilot-on-github ｜ 日期线索：页面无显式日期，2026-10-27 抓取（旧 /concepts/agents/coding-agent/about-coding-agent 已 301）。
7. **【纪律口径，非营销】官方明示输出不可信**："Both chat and agentic experiences on GitHub.com can produce incorrect or suboptimal code, including code that contains security vulnerabilities. Review and test the output before using it in production." 且 "Logs do not replace your own review and testing."
   出处：同上 ｜ 支撑 A4 幻觉防御与 A0「结对而非代笔」的定位引用——厂商自己的红线表述，比本书自撰更有说服力。

### 2.2 Claude Code（agentic coding 工具官方说法）

1. **【能力描述】官方定义**："Claude Code is an AI-powered coding assistant that helps you build features, fix bugs, and automate development tasks. It understands your entire codebase and can work across multiple files and tools to get things done."
   出处：https://code.claude.com/docs/en/overview ｜ 日期线索：页面无显式日期，2026-10-27 抓取。
2. **【能力描述】能跑命令/读文件的多表面形态**：官方列四种 surface——terminal、IDE extensions（VS Code / JetBrains）、desktop app、web；"Each surface connects to the same underlying Claude Code engine, so your repo's CLAUDE.md files, settings, and MCP servers work across all of them."
   出处：https://code.claude.com/docs/en/overview ｜ 支撑 A0 工具地图。
3. **【能力描述】MCP 官方说法**："The Model Context Protocol (MCP) is an open standard for connecting AI tools to external data sources. With MCP, Claude Code can read your design docs in Google Drive, update tickets in Jira, pull data from Slack, or use your own custom tooling."
   出处：https://code.claude.com/docs/en/overview ｜ 支撑 A3。
4. **【能力描述】记忆与技能机制**："CLAUDE.md is a markdown file you add to your project root that Claude Code reads at the start of every session"；另有 auto memory（跨会话自积累）、skills（"package repeatable workflows your team can share"）、hooks（在动作前后跑 shell 命令）、sub-agents（并行子代理）。机制页细节：CLAUDE.md 分 managed/user/project/local 四作用域、自 cwd 向上逐级加载、`@path` import；auto memory 存 `~/.claude/projects/<project>/memory/`，`MEMORY.md` 索引首 200 行或 25KB 进上下文；"Claude treats them as context, not enforced configuration. To block an action…use a PreToolUse hook."
   出处：https://code.claude.com/docs/en/memory ｜ 日期线索：正文引用 v2.1.211–v2.1.285 行为 → 2026 下半年现行版 ｜ 支撑 A1 提示词上下文结构 + A3 记忆机制 + A4「软约束 vs 硬门禁」对照（本书 13 门即硬门禁）。
5. **【能力描述】CLI 可组合性**："Claude Code is composable and follows the Unix philosophy. Pipe logs into it, run it in CI, or chain it with other tools"，如 `tail -200 app.log | claude -p "…"`。
   出处：https://code.claude.com/docs/en/overview ｜ 支撑 A3「模型看串口日志」工具流的正当性论证。
6. **【能力描述，agentic 口径】官方仓库 README 口径**："Claude Code is an agentic coding tool that lives in your terminal, understands your codebase, edits files, runs commands, and helps you ship faster. Claude Code can also use command line tools (like Git) and MCP."
   出处：https://github.com/anthropics/claude-code ｜ 「ship faster」四字为营销尾巴，引用时截取前半句。

### 2.3 Cursor（agent 模式定位）

1. **【定位，含营销成分】官方产品定义**："Cursor is a coding agent for building ambitious software. Use it to understand your codebase, plan and build features, fix bugs, review changes, and work with the tools you already use."
   出处：https://cursor.com/docs ｜ 日期线索：页面无日期；Models 表含 Claude Opus 5.5 / GPT-5.6 → 2026 下半年现行版。取能力分句，"ambitious" 类形容词不入书。
2. **【能力描述】Agent 定义与三构件**："Agent is Cursor's assistant that can complete complex coding tasks independently, run terminal commands, and edit code." 三构件 = Instructions（system prompt + rules）+ Tools + Model；"Cursor's agent orchestrates these components for each model we support."
   出处：https://cursor.com/docs/agent/overview ｜ 支撑 A0（与 Copilot/Claude Code 并列对照）与 A1（instructions 层即提示词工程落点）。
3. **【能力描述】工具清单与无调用上限**：工具含 search files/folders、web、read files（含图片）、edit files、run shell commands、browser、image generation、ask questions（任务中反问澄清）；"There is no limit on the number of tool calls Agent can make during a task."
   出处：https://cursor.com/docs/agent/overview ｜ 支撑 A3 工具流图。
4. **【能力描述】Checkpoint 回滚**："Checkpoints save snapshots of your codebase during an Agent session…stored locally and separate from Git. Only use them for undoing Agent changes; use Git for permanent version control."
   出处：https://cursor.com/docs/agent/overview ｜ 支撑 A3「agent 产物必须过自己的版本控制」一节。
5. **【能力描述+边界】Run Modes 权限模型**：三档——Auto-review（allowlist 直跑、其余尽量进沙箱、剩下的交后端 LLM 分类器）、Allowlist、Run Everything；"The classifier can make mistakes…Auto-review is not a security boundary"；沙箱实现 macOS Seatbelt / Linux Landlock+seccomp；版本线索：v3.6（2026-05-29）Auto-review 成推荐默认、v3.23（2026-10-01）新增 Read access Workspace 模式；"Cloud Agents do not use Run Modes."
   出处：https://cursor.com/docs/agent/security/run-modes ｜ 支撑 A3 权限边界主案例。

### 2.4 MCP（Model Context Protocol 官方 spec）

1. **【规范定义】是什么**："Model Context Protocol (MCP) is an open protocol that enables seamless integration between LLM applications and external data sources and tools." 规范用语遵循 BCP 14 / RFC 2119。
   出处：https://modelcontextprotocol.io/specification/latest ｜ 版本线索：协议版本 2026-07-28（latest 解析结果）。
2. **【规范定义】三方架构**：JSON-RPC 2.0 消息在 Hosts（发起连接的 LLM 应用）、Clients（host 内的连接器）、Servers（提供上下文与能力的服务）之间通信；server 特性三件套 Resources / Prompts / Tools，client 侧特性 Elicitation。
   出处：同上 ｜ 支撑 A3 ai-mcp-toolflow.svg 的规范层。
3. **【架构说明】连接拓扑**："an MCP host…establishes connections to one or more MCP servers…by creating one MCP client for each MCP server"；本地 STDIO server 通常服务单个 client，远程 Streamable HTTP server 通常服务多个；两层划分——data layer（JSON-RPC 协议 + server/discover 发现）与 transport layer（Stdio、Streamable HTTP）。
   出处：https://modelcontextprotocol.io/docs/learn/architecture ｜ 版本线索：对应 2026-07-28。
4. **【规范定义】安全原则**："Users must explicitly consent to and understand all data access and operations"；"Hosts must obtain explicit user consent before invoking any tool"；"Tools represent arbitrary code execution and must be treated with appropriate caution."
   出处：https://modelcontextprotocol.io/specification/latest ｜ 支撑 A3 权限边界与 A4 工具安全提醒。
5. **【能力描述】官方 reference servers 类别**：在册 reference 仅 7 个——Everything、Fetch、Filesystem、Git、Memory、Sequential Thinking、Time；"intended as reference implementations…not as production-ready solutions"；更多服务器浏览走 MCP Registry（registry.modelcontextprotocol.io）；GitHub、GitLab、Google Drive、Postgres、SQLite、Slack 等早期参考实现已归档至 servers-archived。
   出处：https://github.com/modelcontextprotocol/servers ｜ 日期线索：README 现行版，2026-10-27（91.6k stars）。
6. **【治理事实】归属**：MCP 已由 Anthropic 捐赠给 Linux Foundation 下设 Agentic AI Foundation（AAIF，2025-12-09 成立；与 Block 的 goose、OpenAI 的 AGENTS.md 同为创始项目，Google / Microsoft / AWS / Cloudflare / Bloomberg 支持）；官方 Registry 与 2025-11-25 spec（异步操作、无状态化、server 身份、官方 extensions）由此公告确认。
   出处：https://www.anthropic.com/news/donating-the-model-context-protocol-and-establishing-of-the-agentic-ai-foundation ｜ 日期线索：2025-12。

### 2.5 通用 agentic coding 概念（一手定义，服务 A0）

- **【规范定义】** VS Code 文档给出可引的 agent 工作循环定义（推理→行动→验证，见 2.1-2）与分工句式 "You describe the outcome, review the changes, and verify the result."
- **【能力描述】** GitHub Docs 对 agentic experiences 的定义："can research a repository, plan changes, and complete multi-step tasks by reading files, editing code, and running tests in a cloud development environment"（https://docs.github.com/en/copilot/concepts/copilot-surfaces/copilot-on-github ）。
- **【能力描述】** Claude Code README 的 "agentic coding tool" 三位一体口径（terminal + edits files + runs commands，见 2.2-6）。
- 三源相互独立且措辞一致（模型出方案、工具作用于环境、人负责验收），可支撑 A0「结对工程师」工作观的三角引证。

## 3. 模糊点与弃用声明（如实标注）

- **Copilot 对嵌入式 C 的专门适配**：官方只确认 C/C++ 属支持语言、code review 覆盖 C/C++；对交叉编译链、J-Link/OpenOCD 调试等嵌入式专属工作流**官方未明确**任何专门优化声明。书中只引语言支持级断言。
- **Claude Code / Cursor 文档页**：均无页面级 "Last updated"；版本线索分别取自正文 CLI 版本号（v2.1.2xx–v2.1.28x）与 run-modes 页内 Changelog 表（2026-05-29 / 2026-10-01）。快照字段已如实写「页面无显式日期」。
- **MCP spec 版本**：modelcontextprotocol.io/specification/latest 当前解析到 2026-07-28；旧文常引 2025-06-18，引用时须写 2026-07-28 以免过时。Sampling / Logging 两个 client primitive 已于 2026-07-28 起 deprecated（architecture 页明示）——旧版教程说法勿引入书。
- **GitHub Docs URL 漂移**：/concepts/agents/coding-agent/about-coding-agent 已 301 至 /concepts/copilot-surfaces/copilot-on-github；sources 卡登记新 URL。
- **营销话术清单（不入书）**："building ambitious software"（Cursor）、"helps you ship faster"（Claude Code README）、"seamless integration"（MCP 定义中的形容词，规范本体除外）。ability 句已逐条替代。
