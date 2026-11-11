# 内容编写执行细则

最高法是 [CONTRIBUTING.md](../../../CONTRIBUTING.md)（四件套+风格契约六条），本页是 AI 落地时的操作清单。

## 章节页必含区块（顺序固定）

对照金样例 `docs/c/06-abi-stack.md` 逐段核对：

1. frontmatter `title: <前缀+编号 标题>` 与 H1 一致，并带 `status`（done|building）/ `difficulty`（1|2|3）/ `minutes` 三项进度元数据——首页地图与 README 的数字全靠它们算出来，缺一项或值非法，`npm run docs:gen` 就失败；`minutes` 不凭感觉填：按 `正文字数/300 + 代码字数/150 + 10`（取整到 5，最少 15；`## 附录…` 整节不计），`npm run reading:check` 对偏离 ±40% 的章节报错，`node scripts/reading-time.mjs --fix` 采纳模型值（lab/ 与 projects/ 的 minutes 是上板时长，不在此列）；
2. `> 🎯` 钩子（≤60 字类比/反直觉问题，禁"本章将介绍"）；
3. 本章精髓（1–3 个"为什么"）；
4. 学习目标（可检验动词：能手算/能逐行讲清/能在板上观测）；
5. 先修（相对链接带 .md）；
6. quick win（10 分钟可见现象）；
7. 小节结构表（含"四件套"列：配置/引脚/库解析/代码分析）；动画小节（如有）放在 quick win 之后、小节表之前：`## 动画：xxx` + 一句话引导 + `![描述](/anim/xxx.svg)`；
8. 记忆锚点（`::: tip 一句话记住`，口诀/对比表/反例）；
9. 实物实验（装备/观测点/预期现象）；
10. 常见坑（≥2 条真实坑，按出现频率排序）；
11. 你做到了 + `<div class="achievement">` 下一站。

页尾的"本页由 AI 生成"声明由主题统一渲染（`theme/AiNotice.vue`，挂在 `Layout.vue` 的 `#doc-after`），**页面里不要再手写 `> AI生成`**——此前手写导致一半页面有、一半漏掉。

成稿增强件（对标金样例 S3/B4/F2）：精髓后加"怎么读这一章"（能记住/能理解/能用三层）；常见坑后加"短自测"（≥3 题，答案 `<details>` 折叠）与"对照表"（本章概念→仓库文件行/章节落点）；有合适视频时加"配套视频"（VideoEmbed，id 须先验证）；有一手文献支撑结论时，在"你做到了"之前加"延伸阅读"——每条写成 `**[\[D2\]](../reference/bibliography.md#papers)** 作者 年 — 它和本章哪一句有关`，条目必须先登记进 `docs/reference/bibliography.md`（论文要 DOI 经 Crossref 核对，手册要写修订号或明标"未核版本"），不列书单、不引二手博客。

## 事实纪律（强制执行）

- 板卡事实唯一基准：PRD/design 的"已核实板卡事实"（霸天虎 LED=PF6/7/8 共阳、立创 S3 外设清单）。除此之外的寄存器地址/引脚号：写"以 RM0090 §x.x / datasheet / 立创 wiki 原理图为准"，**禁止编造数值**。
- 已核对的数值必须给第二来源：本任务已用 ST 官方 CMSIS 头文件（github.com/STMicroelectronics/cmsis_device_f4）核对 GPIOF=0x40021400、RCC=0x40023800、AHB1ENR=0x30、GPIOFEN=bit5、BSRR=0x18。新增同类事实沿用此法（CMSIS 头文件 / 官方手册 PDF）。

## 版本与芯片边界（2026-10 批次沉淀）

- F 篇内核结论只对**上游 FreeRTOS-Kernel V11.1.0 + ARM_CM4F** 负责；ESP-IDF v5.5.2 内置的是 V10.5.1 SMP 修改版，行号/单位/调度结论不混读。
- V11 内核的 `INCLUDE_*` 宏默认全关：`vTaskDelay` 等 API 链接不上时先查 FreeRTOSConfig.h，不是代码坏了。
- 事件组清位是**汇总清**（xEventGroupSetBits 走完整个等待列表后统一清），不是"先唤醒者独占"。
- ESP32-S3 的 LEDC 是 **8 通道、14 位位宽、仅低速模式**（soc_caps.h）；经典 ESP32 的 16 通道/高速模式结论不能套。S3 模组 N16R8 的八线 PSRAM 占 IO35/36/37。
- STM32F407：Port F 没有 TIM3 通道（PF6/7/8 在 AF3 是 TIM10/11/13）；USART1 的 DMA 请求在 **DMA2**（不是 DMA1）；DMA 标志清除写 HIFCR/LIFCR（HISR/LISR 只读）；AHB 预分频没有 /32 档（HPRE 1100=/64）。
- 链接脚本的 MEMORY 区域属性合法字母只有 r/w/x/a/i/l——老教程的 `(xrwah)` 里的 `h` 在新 binutils 下是硬错误。
- C3 volatile 的取证在**两套工具链**上都跑过（2026-10-06）：宿主 MinGW-Builds gcc 16.1.0（x86_64）与 `D:/zhugu-home/tools/armgcc/xpack-arm-none-eabi-gcc-15.2.1-1.1/bin` 的 `arm-none-eabi-gcc 15.2.1`（`-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard`）。命令与反汇编记录在 `code/c/03-volatile/README.md`；六变体对照由 `blink-variants.sh` 生成。
- **板上现象仍属待实测**：写这一版时未接 F407/ST-Link，章内凡"灯闪/不闪/波形"必须标"编译期已核实、肉眼现象待回填"，不得把 objdump 结论当板上结论写。
- **本站自己写错的结论也要实测推翻**：C3 初版照抄了流行的"去掉 `delay` 参数的 volatile，`-O2` 灯就不闪"，实测 `00-blink` 才知不成立——循环体的 `__asm__ volatile ("nop")` 是另一道独立防线（必须连 `nop` 一起删才翻车，见六变体表 B/C 行）。同类"听起来对"的说法一律先跑再写。

## 动画制作

- SVG+SMIL，viewBox 宽 720，`<animate>` 用 `calcMode="discrete"` 做阶段切换（样例：`docs/public/anim/stack-frame.svg` 的四阶段 12s 循环结构，照抄其 keyTimes/values 模式）；
- 配色固定：底 #f6f8fa、主 #3451b2、强调 #3eaf7c、警示 #d97706；字号 ≥12px；
- 每个动画必须被至少一个章节页引用，并在 PR 描述写"表达结论一句话"。

## 提交前自检

```bash
npm run docs:gen                                      # 零元数据告警（title/status/difficulty/minutes 齐）
npm run reading:check                                 # 每章 minutes 与字数模型偏差在 ±40% 内
npm run docs:build                                    # 零错误（含死链）
grep -rn "TODO\|待补充\|placeholder" docs/ --include="*.md"   # 无命中（除 template.md 的元说明）
```

站点级数字（成稿篇数 / 实验数 / 动画数 / 工程数）只允许出现在 `progress.json` 消费链路上（首页地图、README 状态段），任何页面正文手写具体篇数都视为失真源。
