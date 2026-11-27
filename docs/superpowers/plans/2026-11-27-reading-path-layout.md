# 阅读路线、入门事实与站点版式

本轮范围：ch00/ch01/ch05 的基础概念，ch46 的学习入口、资料阅读与关系图，以及站点宽表和单章打印。延续用户已授权的改进、提交、推送、CI、合并与发布流程。

## Sepia review（改写前）

- 类型：中文技术教程；作者模型未知，prose layer 为 none；执行器 GPT-6、具体变体未知，GPT prose layer 为 prior。
- 读取：Sepia professional-pass、tech-articles、discourse-pass §1–3、style-pass、languages/zh、model-fingerprints 的 GPT prose 层。
- 缺陷：ch46 开头先解释双书合并；罗盘重复目录且承诺不存在的六维对比、仪器两表；“星标见本章上表”无目标；“F1 DMAF1 DMA”重字。审稿过程遮住了读者该采取的下一步。
- 版式证据：390px 视口正文 342px，旧 47 行索引表高 8328px、阶段列仅 35px。打印媒体下站点导航仍显示，表容器仍为 overflow:auto；beforeprint 展开 details 后不恢复。
- 事实缺陷：寄存器位被写成独立地址、向量表被写成指令入口首行；函数内 static 被写成文件作用域；自动变量位置被绝对化；ST-Link 电源输出与 VTref 检测输入混用。
- 保护区：47 章依赖记录、历史采样日期、代码/地址/命令、来源与未实测边界；不改硬件测试历史。
- 结论：cluster → 最小 refactor。删除悬空承诺，补具体入口；不为文风扩写正确段落。

## 实施约束

- 47 行索引按既有五阶段分组，保留各行事实。折叠只用于屏幕查阅，印刷展开。
- 新图显示关系和顺序；SVG 与生成器一同入库，标明自绘示意；正文保留可复制的链接与判据。
- 外部材料核对书目、实际公开内容、版本、许可；来源发现与全文阅读分开记录。直接复用时须保留上游许可。
- 手机宽表可局部横向滚动，页面本身不溢出；打印后恢复原展开状态。

## 验证

- 原 47 条依赖记录与 HEAD 逐字比对一致，按 1/18/15/6/7 分组；Python Markdown 渲染得到五张表，印刷构建器会展开 details。
- `book.checks`、`slop_lint`、Markdown 链接扫描（139 篇，0 问题）、53 页内容渲染、586 个公共资产检查通过；脚本单测 32 项通过。
- 书稿单测 145 项通过、1 个审计类因缺少本地快照跳过；随后生成快照并单跑审计类 2 项通过。曾发现 ch46 无图段 9064 字超原 8846 字上限，移动路线图至章节索引入口后降至 8023 字，不改阈值。
- 新阅读/打印浏览器断言 10 项在开发站通过，覆盖 390/768/1440px、键盘滚动、重复 beforeprint、原状态恢复、暗色转白纸打印。
- Chromium A4 单章打印抽查 23 页版本（补书目前）：第 1/5/7/9 页可读，全部文字块无左右 40pt 边界溢出；两幅 342px 宽手机图人工检查无碰撞。
- 最终 `npm.cmd run site:build` 通过（54 页、365 张图、14 个场景、131 个旧链存根），`site:smoke` 22/22 通过；窄屏参考表第一列 150px，390/768/1440px 均无整页横向溢出。
- 远程 CI 与发布结果以 PR 和工作流记录为准。不以文档审阅代替固件或硬件验证。

## 参考资料与使用范围

- Z-Library：Brown `5150636:b18726`（2013，STM32VL Discovery）；White `28123430:bf69ab`（第二版 2024，ISBN 9781098151546）。实际只读取书目与简介，未下载/声称读完全文，未复制书中图文。
- `cpq/bare-metal-programming-guide` @ `4f6b45ba25eec45bb50cb027365fa381465bb9e8`：实际阅读 README、MIT LICENSE、step-1-blinky。借鉴每步完整工程、逐项增加能力的编排；联网 Mongoose 依赖许可另计。
- `rust-embedded/discovery` @ `4ecc57b97299ef81b5b806279dcb6f8e6e77f1b4`：实际阅读 README、F3 目录、LED challenge 与循环延时实验。修正文档维护状态与板型边界；文档 CC BY 4.0、代码 MIT/Apache-2.0。
- `libopencm3/libopencm3-examples` @ `15637e291b8ca228e35d5f657ed15f3b8958fa0c`：实际阅读 STM32VL Discovery miniblink 的源码、README、Makefile；文件头 LGPL-3.0-or-later。新增原创建议实验，未复制源码，未声称上板完成。
- `geoffreymbrown/STM32-Template` @ `ae8bfe8e951a6c12192a05fd031ef0647d721fe6`：README 指定 STM32VL Discovery/CodeSourcery/SPL，根无统一 LICENSE。仅链接；失效的旧官方 PDF 地址未加入正文。
- 新图为 `tools/gen_reading_path.py` 原创确定性 SVG，图型 FA-029 / IG-008，沿用 svgkit 配色；无第三方图版复制。

## 删除与回退复读

删掉双书合并过程导语、未兑现的六维表/仪器两表/IDE preset 承诺、错误 RDP 泛化句与重复图中文字；保留依赖事实、测量边界和历史采样日期。新增内容用于选择入口、完成源码实验、区分板型或限定许可，未为统一语气改写正确段落。
