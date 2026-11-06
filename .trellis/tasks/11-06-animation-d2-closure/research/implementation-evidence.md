# D2 实施证据与审查记录

## RED：本轮直接执行

命令：`node --test tests/animation-markdown.test.mjs`。

新增测试通过真实 VitePress renderer 加载生产 config；不复制实现正则。第二次、有效的旧实现运行：12 tests，4 pass / 8 fail，0 skipped。

- 三类围栏失败：代码文本中的标签变成 `![](/anim/toolchain-relay.svg)`。
- 四空格/tab 失败：预期 code_block，实际 html_block。
- 混排失败：期望正文动画 1 个，实际 2 个。
- caption 失败：`满]空 & <边界>` 经图片语法二次解析后没有生成组件。
- 注释失败：注释内组件被改写。
- LF/CRLF 的 0–3 空格正文正例、既有图片路径、同行文字正例均通过。

首次运行中，新增正例断言误禁 markup 属性里的换行，造成额外三项无关失败；依据实际多行 SVG 属性纠正该断言，使其检查同一个属性中的完整 SVG。该纠正不削弱代码块、图注或段落结构的行为断言。之后才取得上述有效 RED，生产代码当时未改。

## 审查边界

新增 `tests/animation-markdown.test.mjs`（12 个行为测试，内存输入），无 runner/CI/policy/现有断言改动。新增测试仍待用户审查；本轮手工运行的 RED/GREEN 不等于 operator 配置检查通过。

GitNexus 本轮 list_repos 只有无关 clideck、behind 11，当前项目无索引；不使用该图谱作为调用影响证据。

`task_verify plan`：unverified / verification-baseline-unavailable，changes=[] checks=[]。

## GREEN 与构建（本轮实际运行）

- 同一 `node --test tests/animation-markdown.test.mjs`：12 pass / 0 fail / 0 skipped（775ms）。生产修复仅改 config 的 tag 转换入口，未改变上述有效 RED 测试。
- `npm run test`：134 pass / 0 fail / 0 skipped（1812ms），含新测试；新测试审批状态仍独立标记未验证。
- `npm run docs:build`：52.70s 成功；guide:check PASS。保留构建警告：h/kconfig 高亮 fallback、gpiof-moder 混合静/动态导入、>500kB chunk，不抑制或顺手改动。
- `npm run book:check`：whole-book HTML contract PASS；94 chapters，题图 94/94。未重建 PDF。
- 既有 `npm run test:browser`：7 passed（41.9s）。
- `npm run a11y:check`：132 页基线通过。
- `npm run anim:lint`：111 图通过。

## 真实 UI smoke（新服务 4187）

用 browser.open 的独立浏览器载入新构建，不复用旧 preview 缓存。

| 页面 | data-anim | SVG | 按钮 | 段落误嵌套 | page errors |
|---|---|---:|---:|---|---|
| build/00-toolchain.html | toolchain-relay | 1 | 2 | 无 | 0 |
| build/06-flash-debug.html | swd-debug-chain | 1 | 2 | 无 | 0 |
| c/00-c-in-mcu.html | embedded-c-diff | 1 | 2 | 无 | 0 |

三页当前源标签未指定 caption，真实页面 figcaption 为 null，符合输入；带 caption 由 renderer 回归验证。

375px 下 C3 既有行为：12s 一轮；减少动效 paused=true，getCurrentTime=10.800000190734863；放大 SVG 680px、scrollWidth 680 > clientWidth 321；焦点在 close、body overflow hidden。Esc 后新 AX/DOM 证据：dialog=false，焦点回 anim-figure__zoom，overflow visible。误用 waitFor hidden 选项导致一次 harness 错误，随后只读 observe 确认关闭已完成，未重复发送 Escape 或修改生产代码。

已查看 embedded-c-diff 桌面图及 C3 窄屏放大截图。规格改成 parser-aware 行为，删除了错误的全局前置源码改写要求。

## Operator 配置验证

本轮 `task_verify run` 返回 `status=unverified`，`reason=project-or-git-baseline-unavailable`，`checks=[]`。没有任何 operator 配置检查执行，不计为通过；新增回归仍待用户审查与后续新回合基线。

## 根因与防复发

类型：隐含假设（源码独立行等于正文）+ 回归覆盖缺口。上一轮只验证三页正例，没有代码块负例；更早只扫描 html_block 的方案又依赖了错误 token 假设。

本次以真实 renderer 的 block 边界作为架构隔离，代码 token 不进入兼容转换；新增真实配置行为回归，规范明确禁止全局源码替换。没有新增 lint/门禁策略，也没有扩张到其他语法或印前链路。

可选独立测试审阅 job 未返回结论，已取消，不计审阅通过；用户审查仍为待办。浏览器 tab 已关闭。预览服务停止超时后原父 PID 已退出；检查 4187 listener 的 child PID 20540，命令行确认为本任务 vitepress preview，原生 Stop-Process 后再次查询端口无 listener，清理完成。
