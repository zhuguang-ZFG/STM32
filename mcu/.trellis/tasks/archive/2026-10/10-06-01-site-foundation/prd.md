# PRD: MCU 教学站点奠基（VitePress 骨架 + 七板块深度大纲 + 双路线第 0 章）

## 背景

空仓库（仅 LICENSE/README），目标建成"通往AGI之路"式的开源 MCU 深度学习库。教学性质、中文、Apache-2.0。

## 已决决策（用户拍板，不可回退）

| 项 | 决策 |
|---|---|
| 内容形态 | VitePress 站点（可部署 GitHub Pages） |
| STM32 主线 | 寄存器级编程 + SPL 标准库源码解析（非 HAL/CubeMX） |
| STM32 基准板 | 野火 F407 霸天虎（STM32F407ZGT6，用户实持） |
| ESP32 基准板 | 立创·实战派 ESP32-S3 开发板（小智板，ESP32-S3-WROOM-1-N16R8，用户实持） |
| ESP32 框架 | ESP-IDF（基准 v5.5.x） |
| RTOS | 双精讲：FreeRTOS 内核 + RT-Thread |
| 工作流 | Trellis（本任务即按 Trellis 流程执行） |

## 内容契约（用户四次明确，逐条落实）

1. **挖掘精髓**：C 语言（嵌入式视角）、RTOS 内核、构建与运行全过程是一等板块，不是附录。
2. **四件套**：每个外设/驱动章节强制包含——功能配置（全部配置位/字段图解）、引脚设置（复用表/电气特性/接线图）、库文件解析（SPL、ESP-IDF driver、RT-Thread 源码逐行走查）、代码分析（示例逐行注释，关键处下钻汇编/寄存器）。
3. **RTOS 双精讲**：FreeRTOS（内核源码级）与 RT-Thread（内核+设备框架+finsh+生态）各自成单元，另设双 OS 对照与选型单元；RTOS 动态机制（上下文切换、调度、优先级反转）**必须配动画演示**。
4. **动画**：用动画表达动态过程（栈帧、中断现场、上下文切换、调度、时序波形）。技术形式为内联 SVG+SMIL，禁止外链播放器。
5. **实物**：每个实验可在用户实持板卡上照做——装备清单、接线图（SVG）、预期现象、实测要点、故障排查。**禁止伪造实物照片**；照片由贡献者实拍补充，规范见 CONTRIBUTING。
6. **写作风格**（参考野火《实战指南》等优秀教程的节奏，但更进一步）：生动活泼（每章一个生活化钩子/类比）、浅显易懂（直觉→图示→寄存器/源码三层递进）、记忆深刻（每章一个记忆锚点：口诀/对比表/反例）、成就感十足（章首 10 分钟 quick win 先见现象，章末"你做到了"清单）。生动≠啰嗦：每段必须有信息增量，禁鸡汤、禁表情轰炸、禁水字数。

## 已核实板卡事实（写作唯一基准，注明出处）

- 野火 F407 霸天虎：RGB LED 红=PF6 / 绿=PF7 / 蓝=PF8，共阳接 3.3V、低电平点亮；GPIOF 时钟=RCC_AHB1ENR bit5。出处：野火《STM32 库开发实战指南·使用寄存器点亮 LED 灯》(doc.embedfire.com) + 霸天虎硬件规格书。HSE 频率以规格书为准（用时核对）。
- 立创·实战派 ESP32-S3：模组 ESP32-S3-WROOM-1-N16R8（16MB Flash/8MB PSRAM，LX7 双核 240MHz）；ST7789 2.0 寸 320×240 SPI 屏；FT6336 触摸（I2C）；QMI8658 姿态（I2C）；ES8311 音频 DAC + ES7210 四通道 ADC + NS4150B 功放 + 双模拟麦 + 1W 喇叭；CH340K USB 转串口；CH334F HUB；GH1.25 扩展口 ×2（5V/3.3V，GPIO/CAN/I2C/UART/PWM）；TF 卡（1-SD）；复位键+用户键各一。出处：wiki.lckfb.com/zh-hans/szpi-esp32s3/。引脚分配表以该 wiki 原理图页为准（用到即核对）。

## 交付范围（本任务）

1. VitePress 站点骨架：`docs/.vitepress/config.mts`（导航+全量侧边栏）、首页、自定义主题样式，`npm run docs:build` 通过。
2. 七板块大纲骨架（约 70 页）：`guide / c / build / stm32 / rtos(freertos+rtthread+对照) / esp32 / lab`。每章骨架含实质内容：钩子、学习目标、本章精髓问题、小节结构（四件套落位）、实物实验锚点、记忆锚点、常见坑、前置链接——**非 TODO 占位**。
3. 第 0 章成稿 ×2：
   - `stm32/00-env.md`：Windows 下 arm-none-eabi-gcc + make + OpenOCD + ST-Link + VSCode 全流程，含最小寄存器点灯工程（启动文件/链接脚本/Makefile/main.c 全套真实代码，目标板=霸天虎 PF6 红灯）与验证步骤。
   - `esp32/00-env.md`：ESP-IDF v5.5 安装、idf.py 工作流、hello_world 烧录验证（CH340K 串口）、工程结构首览。
4. 动画基建：`docs/public/anim/` 规范 + 成品动画 3 个（函数调用栈帧生长；中断响应现场保护与返回；RTOS 上下文切换）。
5. 实物实验：`lab/template.md` 实验模板 + `lab/e01-blink.md` 成稿（霸天虎 RGB 红灯，寄存器代码 + SVG 原理/接线图 + 实测要点）。
6. 仓库门面：README 重写（定位/路线图/目录/参与方式）+ CONTRIBUTING（深度标准、风格契约、动画规范、实物实验规范、章节页模板）。
7. `.trellis/spec/` 重写（并行任务 00-bootstrap-guidelines）：删除 fullstack 模板，按真实结构（docs-site / firmware-stm32 / firmware-esp32 / content-guides）写规范。

## 非目标

- 章节正文全部成稿（骨架即完成；第 0 章与 E01 除外）。
- 真实硬件上板验证（第 0 章代码经静态审查 + 与手册/公开资料核对，标注"待上板验证"；用户持板可实测反馈）。
- GitHub Pages 部署流水线、ESP-IDF v6.0 差异附录、RT-Thread 内核之外的软件包逐个精讲（生态章节给地图与方法）。

## 验收标准

- [ ] `npm run docs:build` 零错误通过；`npm run docs:dev` 浏览无死链。
- [ ] 七板块侧边栏与设计大纲一致；每章页含风格契约要素（钩子/记忆锚点/你做到了），四件套落位；`grep -rn "TODO\|待补充\|placeholder" docs/` 无命中。
- [ ] RTOS 板块含 FreeRTOS、RT-Thread、双 OS 对照三单元，骨架齐整。
- [ ] 两章第 0 章按步骤可复现（命令、路径、代码完整；寄存器地址/位定义与 RM0090 核对）。
- [ ] 3 个 SVG 动画在构建产物中可访问且 Chrome/Firefox 播放。
- [ ] E01 实验含完整接线图、逐行注释代码（PF6）、预期现象与排查清单。
- [ ] README/CONTRIBUTING 成稿且与真实目录一致。
- [ ] `.trellis/spec/` 无模板残留，index 与文件集一致，规则指向真实文件。
- [ ] 关键寄存器地址/引脚定义经第二来源核对并注明出处。
