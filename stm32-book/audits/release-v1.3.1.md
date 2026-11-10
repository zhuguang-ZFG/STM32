中英离线整书 **1.3.1**（HTML + PDF）。附件为 tag `v1.3.1` 所指 main 提交的 Book CI 产物（CI 双 job 绿）。

> 「Book 2.0」是视觉体验收敛计划（spec B46–B51）的内部代号；书内版本号沿 1.x 线，本版即 **v1.3.1**（封面/版权页/修订历史一致）。

## 下载

| 文件 | 说明 |
| --- | --- |
| `stm32-practical-book.html` / `.pdf` | 中文整书（528 页） |
| `stm32-practical-book-en.html` / `.pdf` | English whole book（551p） |

## 相对 1.0.7：视觉体验收敛（spec B46–B52 + 整书验收 B51）

- 排版三档层级（页标题/节标题/小节标题）落地，打印样式 token 化（B47）
- 三类图覆盖：图档 fixture 共 514 条；无图区间硬门 ≤1200 字（唯一批准例外 ch26=1231，已登记）
- 新增 37 张知识轨插图（B49 十四张 + B52 收口二十三张，覆盖 16 章），全部图注四要素：看哪里 / 证明什么 / 不能证明什么 / 出处
- 实拍证据：ch21 补三张准确型号照片（Avandalen CC BY-SA 4.0 / Popolon CC BY-SA 4.0 / Ordercrazy CC0，含 SHA-256）；实拍章 2→4
- 事实修正：ch09 ADC 分频补 ÷8 合法档、ch12 F4 RDP Level 1 条件图、ch06 UART 测量目标口径
- 中英同序列；版式门 0 硬缺陷（无溢出 / 孤标题 / 孤图注 / 近空白）
- 整书回归 196 项通过；check_assets 2176/2176 + 照片哈希 5/5

## 审计索引

`stm32-book/audits/`：b47-typography-tiers、b48/b49-gap-figures、b50-hardware-evidence、b52-gap-close、b51-final-acceptance（含 B46→B51 前后对比与 15 页抽样目检记录）。
