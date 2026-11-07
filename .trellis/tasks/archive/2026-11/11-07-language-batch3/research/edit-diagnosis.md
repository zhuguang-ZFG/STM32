# 实施前文字诊断

SEPIA REVIEW — 技术教程，docs/build 既有工程口语

Loaded: professional-pass、tech-articles、discourse-pass §1–3、style-pass、zh、GPT prose priors。

Model: author=unknown；executor=GPT 6.1 Sol。Prose layer: author=none；executor=prior（没有对应 release 的 operative 表）。

Venue corpus: 已接受的 B0/B1/B2 及 B3/B4 当前上下文；保留图纸、门牌、搬家比喻和直给语气。

Style scan: 不把破折号、短句数或平均长度当缺陷；不新增统一排比节奏。局部问题是责任对象不清、长句内关系挤压、回指读者需返看。

## 完整处理列表

- B3-A / 16：MEMORY、SECTIONS、符号的分工埋在括号里。只把已有解释接成明确动作，原结论不动。
- B3-B / 83：“不是分配，是额度”后紧跟后文代码。将预算记账与实际分配分成两句，不添加运行时安全保证。
- B3-C / 180：“取的是后一个”需要回看两处地址。直接指明 LMA，保留原行全部代码与比喻。
- B3-D / 236：“对着 nm 看”未说对照什么。明确是上面的字面量池值，不触碰后面的三个事实句。
- B3-E / 240：改图纸、字面量跟着变、启动文件不需要知道变量数挤在一个因果句。分开链接后的变化与使用者。
- B4-A / 18：“善意的谎言”概括学习目标。改成能指出初值位置及搬运者，第三节引用保留。
- B4-B / 98：C 的承诺、两处位置和循环责任挤在同一段。分清位置后再承接循环；不改硬件论断。
- B4-C / 124：三个符号和脚本语法挤在括号内。先说源与目标头尾，再对照语法，代码 token 顺序不变。

Failed: #10 fluency / 指代与长句关系，证据见上八项及 reading-evidence.md 原句；#2 density / 用具体对象替代抽象回指，而非增加背景段。

Protected: 所有非白名单行；代码、表格、标题、数字事实、链接、HTML/容器；design.md 的技术疑点。原文引号里的短语不改内容。

Passed: 1,3,4,5,6,7,8,9（不把既有章节模板或作者比喻当 AI 痕迹）。

Verdict: isolated hits → 仅八处最小修订。逐句执行删除/回置检查，不引入新术语、经历、观点或结论。
