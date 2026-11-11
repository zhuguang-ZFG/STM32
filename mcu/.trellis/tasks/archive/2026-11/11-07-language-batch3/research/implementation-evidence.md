# 第三批实施与阅读验证证据

## 授权与范围

用户先批准建任务与规划，后在具体规划审阅中选择“通过，开始实施”。task.py start 已将 11-07-language-batch3 从 planning 转为 in_progress。

只改 B3 五行、B4 三行获批散文及配套站点更新日志；无提交、推送或发布授权。原文 before 与候选 candidate 在本目录保留供审阅，准确来源 SHA、最终 SHA 与修改行见 source-evidence.json / final-source-evidence.json。

## 八处前后对照与理解收益

| ID / 原行 | 原表达 | 最终改法 | 解决的阅读卡点 |
|---|---|---|---|
| B3-A / 16 | 分工挤在“圈地（…）、分房（…）、符号门牌（…）”里 | 原解释接为“圈地，规定…；分房，规定…；符号门牌则留给启动代码兑现” | 三类对象各负责什么，不用从括号拼关系 |
| B3-B / 83 | “不是分配，是额度：稍后…” | “先记的是额度，并没有分配空间。稍后…” | 先分预算与分配，再看检查段如何记账，不增加运行时保证 |
| B3-C / 180 | LOADADDR“取的是后一个（LMA）” | 直接说“取 LMA”，接到 _sidata 的取货地址 | 不必返看“后一个”指哪处位置 |
| B3-D / 236 | “对着 nm 看” | “把上面字面量池里的值和 nm 逐项对照” | 明确对照对象，后面三条技术细节原样保留 |
| B3-E / 240 | 改图纸、字面量跟着变、启动文件不用知道变量数连成一句 | 分开常量的变化与启动文件使用这些值 | 链接阶段与启动阶段不混作一次查询 |
| B4-A / 18 | 学习目标概括为“善意的谎言” | 指出初值存在哪、由谁搬到变量位置 | 读者知道自己要追踪什么，第三节引用未变 |
| B4-B / 98 | C 承诺、Flash/RAM 性质、搬运工挤在一段 | 先说“两处位置”，再接到负责搬运的循环 | 从位置关系自然接到下面的原汇编 |
| B4-C / 124 | 三个地址符号与链接语法挤在括号里 | 先解释 Flash 源与 RAM 头尾，再对应脚本语法 | 读每个符号时知道它属于源还是目标，行内代码顺序未动 |

## 保护核验

- 候选 B3/B4 对各自 before 的 strict prose_guard 均成功，输出“不可动清单：全部一致”。
- 最终 docs 正文对同一 before 再验，两章仍全部一致；没有改为 additions 模式。
- 额外逐行比较精确命中 B3 16/83/180/236/240、B4 18/98/124，除此之外所有原行逐字节相同。最终正文与已验候选逐字节相同。
- baseline、guard、readability、reading、package.json 及三个 workflow 共八个验证输入 SHA 均未变。未编辑任何测试、runner、策略或阈值；用户 11-02 产物未触碰。
- design.md 冻结的事实疑点均原样保留；没有运行固件 probe、烧录、上板或验证原实物实验。

## 指标（防退化旁证）

| 章节 | 句数前→后 | 长句占比前→后 | 平均句长前→后 |
|---|---|---|---|
| B3 | 143→147 | 1.4%→1.4% | 32.3→31.6 |
| B4 | 75→77 | 6.7%→6.5% | 33.9→33.8 |

句子变多来自解释拆分，不代表理解质量已获用户验收。未更新 .prose-baseline.json。

## 本轮实际命令结果

- 最终正文 strict guard：两章通过。
- prose:check：78 章通过，平均长句占比 10.1%。
- reading:check：78 篇均在模型容差内。
- docs:check：138 文件、6 类检查通过。
- book:check：94 章、题图 94/94，whole-book HTML contract PASS。
- bg_26：完整 docs:build 等效入口（guide:check → docs:gen → VitePress build），38.44 秒构建成功。保留 h/kconfig 高亮回退、JSON 静动态 import 和 chunk 大小告警，未改策略。
- 配套 changelog 后的 bg_27：docs-check 138 文件通过，guide-check PASS，docs-gen 成功，VitePress build 39.59 秒成功；实际最终入口完整执行，未复用日志前构建结果。
- task_verify 实际调用返回 unverified / project-or-git-baseline-unavailable / checks=[]，不计通过。

## 真实页面与交互

本任务预览地址为 localhost:4196/mcu/，真实浏览器打开 B3/B4 页面，不以 HTTP 请求代替导航。

- 桌面 1440×960：两页新正文存在；实际点击 B3 的 .data 双地址目录链接与 B4 的 .data 搬家目录链接，URL hash 均改变并显示对应章节。
- 两页答案折叠均实际点击，从 open=false 变为 true，参考答案内容可见。
- B3 页面有 34 个代码块、2 个内联 SVG、1 个答案折叠；B4 为 7、2、1。观察时未发现已加载图片失败。
- 手机 390×844：两页 scrollWidth=innerWidth=390，散文段落均不越出视口。B3 的 24 个、B4 的 6 个长代码块保留内部横向滚动，不构成文档级溢出。
- 桌面已截图观察代码和段落；手机已截图观察两章改写段落、B3 地址图及 B4 启动动画。页内目录的同名文字可能先命中隐藏项，后用实际 h2 id 定位并等待可见，再截图，不把未滚动截图算作图片验证。
- 两页 page errors 均为空。本任务两 tab 与预览进程已关闭。

## 预览启动问题与验证边界

第一次预览启动早于构建完成，缺 dist/404.html；等待 bg_26 成功后启动的进程正常服务。第二次 readiness 等待未通过是日志匹配写成 127.0.0.1、实际输出 localhost，未再重启；直接浏览器打开现有进程验证成功。未修改站点配置或放宽检查。

本批未运行完整 PDF、固件、上板或整站浏览器测试套件，未自动提交发布。技术事实未重新认证，文字效果仍待用户验收。

## 本轮提交发布交接

- 用户选择“按计划提交并发布”，确认三份正文/日志、仅本批任务归档、仅本轮会话记录的提交清单；原有 11-02 工作全部排除。
- 正文工作提交：755ff3f，三文件 14 行新增、8 行删除。独立分支 docs/language-b3-b4-release，从 a35ca683 起步，fetch 后 origin/main 与该基线相同。
- 本轮重新实际执行：两章 before→最终正文 strict prose_guard 全部一致；prose:check 78 章、reading:check 78 篇、docs:check 138 文件、task context 8+7 全过。
- 本轮两章 SHA 与 final-source-evidence.json 相同；八个验证输入 SHA 与原始 source-evidence.json 相同。本轮未重复实施或修改检查输入。
- 对原有 11-02 任务的全部 42 个现存文件保存 SHA，结束时按同一清单复核；不以 git status 替代内容不变证明。
- task_verify 本轮实际仍返回 unverified / project-or-git-baseline-unavailable / checks=[]，未计通过。
- PR、CI、合并与正式部署结果以本轮实际远端结果为准，本地构建及历史 checkpoint 均不替代它们。
