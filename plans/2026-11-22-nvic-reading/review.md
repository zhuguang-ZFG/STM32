# 第 10 章：把抢占过程留在纸上

日期：2026-11-22。范围：NVIC 抢占小节、原创静态手绘及其生成链，以及 EPUB 标准检查发现的两类格式错误。现有 841 页 PDF 的物理第 167 页是本次抽样起点。

## 编辑前审校

SEPIA REVIEW — 中文技术教程，STM32 合并书。

- Loaded：Sepia canonical、professional-pass、domains/tech-articles、discourse-pass §1–3、style-pass、languages/zh、model-fingerprints 的 GPT prose layer；先 review，再 refactor。
- Model：author=unknown；executor=GPT-6，具体 release 未知。Prose layer：author=none；executor=prior。
- Venue corpus：第 10 章 IRQn 寻址、EXTI 六步与第 14 章缓冲区寿命小节；沿用条件、算例、失败信号相邻的教程语气。
- Failed #2 密度：“把‘谁能打断谁’演成五幕的是下面这张动画……”用一个长句串起多个时间点，纸上只有单帧，读者需反复回读。
- Failed #5 具体性：“同时挂起”容易被理解为必须同时到达；应说明仲裁时均处于挂起状态。IABR 的 active 与 CPU 此刻正在运行哪个 ISR 需要区分。
- Failed #6 图文组织：动画的静帧保留大画布和小标签，等待、抢占、恢复不能同时对照；图片内部留白不在现有页底留白门的检测范围内。
- Style scan：相邻优先级说明包含多层括注和编号体系切换；不按单个术语或句长判断作者身份。
- Protected：原代码块、地址公式、表数据、现有来源定位、平台边界、待上板状态。
- Deferred：第 22/24 章抽样未发现同类失读问题，本轮不为凑图改动；硬件读数仍待记录。
- Passed：1、3、4、7、8、9、10（本次编辑范围）。Verdict：isolated hits → refactor。

## 图文设计

- 模式：知识教程，模式 A；用一张静态时间轴替换正文中的抢占动画图片，供网页、PDF、EPUB 共用；原动画资产保留。
- Anchor：优先级编码与分组之后，独立小节“谁能抢占：先比较抢占级”。
- Layout：IG-008 流程步骤，三条共用时间轴的 ISR 泳道；画风 #001 清晰手绘线，主题 C-22 普鲁士蓝，辅以鼠尾草绿与琥珀色；1152×864，4:3。
- 认知任务：EXTI9_5 同级等候；EXTI1 抢占；EXTI0 从断点恢复；EXTI0 退出后 EXTI9_5 执行。实线表示执行，虚线表示暂停或挂起，颜色之外仍能区分状态。
- 数字条件：F407，PRIGROUP=4，3 位抢占 + 1 位子优先级；EXTI0=(2,0)，EXTI1=(1,0)，EXTI9_5=(2,1)。所有请求已使能、未被屏蔽；时间轴不表示实测时长。
- 关系：替换单帧展示，不复制参考书图文，不增加相邻的同义图；正文保留数值和执行次序。
- 间距：前图是优先级 4 位窗口，后图是 PF6→EXTI6 链路；按最终章节顺序检查，优先保留完成认知任务的点位。

## 一手资料

- Arm 官方 `CMSIS_6`，`CMSIS/Documentation/Doxygen/Core/src/ref_nvic.txt`，Git blob `b1ba140f4082334d7711b7e89a3960a872c5f11c`：L405–412 说明 PRIGROUP 与实现位宽共同决定拆分；L584–602 的 `NVIC_GetActive` 明确被抢占的 ISR 仍为 active。
- PM0214 是本章已有依据。本轮 ST 官网 PDF 下载返回 HTTP 567，未将其记作重新查阅成功；抢占级与子优先级的已有规则保留，新增 active 说明以上述 Arm 原始文档核验。

## 验证记录

### 图文与生成链

- 原抢占动画图片替换为一张完整的静态时间轴；图中文字说明运行、暂停、挂起，正文区分 pending、active 与当前执行位置，并补一条失败分支及第 9 道自测。
- 分组编号解释删去重复表述；删除检查保留分组数字、执行次序、屏蔽条件与 active 语义，回退检查保留原公式、代码和表数据。程序逐块对比确认原代码块逐字相同，原表格行全部保留。
- 新 PNG 为 1152×864、53,475 B；reading 图由 21 增至 22，staged 图由 85 增至 86。完整重渲比对：缺图 0、漂移 0；191 张没有 staged 源的旧图仍只作提示。既有 PNG 未修改。
- 原图与新图分别在实际 PDF 中抽样；新图不再把纸面用于显示单帧周围的大块空白。SVG 文字越界 0、正文标签相互重叠 0。

### 本地验证

- Python 测试 106/106（含新增的两项 EPUB 回归，无跳过）；Node 脚本测试 32/32；manifest、mapping、book checks、slop lint 与 53 页内容渲染检查通过。
- VitePress 54 页与清单一致；357 张图片的 lazy、async 和尺寸通过，14 个场景尺寸通过；131 条旧链生成完成；挂载站点 smoke 10/10。
- 新图在 1280 px 和 390 px 视口内完整显示，无横向溢出，原图链接返回同一份 PNG。
- 第一轮印刷为 842 页；发现图前留白后，将长解释移至图后，留下短结论紧接图。最终为 841 页，第 166 页标题、短结论、手绘和图注相邻；第 10 章样章 22 页（物理 160–181 页）。
- 最终 PDF：margin_overflow、orphan_heading、caption_orphan、near_blank 均为 0；bottom_gap 155 页，≥250pt 大留白 104 页，沿用 200/120 门槛。上一版为 157/107，本轮分别减少 2/3 页。
- 最终 EPUB：64 spine，339 张正文图片加 1 张封面；ZIP、XML 及无 SVG 图片检查通过。
- EPUBCheck 5.4.0 首轮找到 5 处 RSC-005：附录 C 的 4 个 `p align` 属性，以及第 37 章 `CNT<CCR` 被 HTML 解析成 `ccr` 标签。导出器将段落对齐转换为 CSS 类，保留原 class、子节点和居中效果；第 37 章把比较式写进代码跨度。新增回归覆盖四种对齐和实际章节的公式保留。重导后 EPUBCheck：fatal 0、error 0、warning 0、info 0。
- EPUBCheck 来自 W3C 官方 GitHub release `v5.4.0`，下载包 SHA-256：`33350c61038e71dfb3d45a76aed04bf5481e6d5500cb780f6e98db8bbd15a28c`。检查输出位于 `.temp/book-quality-20261122-nvic/epubcheck-final.json`。
- 本地重新装配正文、静态图片和样式时，复用了上一轮标准构建的 81 张动画静帧；基线 HTML 的 SHA-256 为 `67f5ff29280c0267c503f19e94d058655b317ac787320d31aac1553fcc9e48c5`，逐张源 SVG 与 `8157d35d` 规范化比对一致，alt 映射唯一。本轮移除的一张动画未复用；远程标准全量构建以对应提交的 Book CI 为准。

成品目录：`book/dist/quality-20261122-nvic/`。完整证据在被忽略的 `.temp/book-quality-20261122-nvic/`。

| 成品 | 字节 | SHA-256 |
| --- | ---: | --- |
| HTML | 29,969,769 | `7bd2fb229bc81c3f2f9f7da1f3fb05ceab87f3503b3bd3ff91606febd0aa13af` |
| PDF | 30,953,553 | `4e4fba4bc5764585ed632cee3aff8f4d073083d8efc8fe66b1c3357bb46a2642` |
| EPUB | 21,473,840 | `bc6f677482b349606f767559858c21389fd427c46e2118e106391aa3a94f514a` |

未完成项：新增上板实验、实体阅读器验证；本轮不将其记为通过。
