# 执行与验收顺序

## 进入实施前

- [x] 用户已批准任务创建、规划和三条路线都做。
- [x] 总任务与三个子任务均建立 PRD、设计、执行清单及研究记录。
- [x] PRD 收敛：三路线为已确认范围；具体章节和数量为待审阅方案。
- [x] 用户审阅最终方案，确认开始实施（2026-10-06）：三条路线全量交付；授权本机安装 GNU Arm Embedded 工具链；霸天虎 F407ZGT6 与立创实战派 ESP32-S3 N16R8 均在手，可做上板实测。三个子任务的 PRD/design/implement 已按本方案补齐。
- [ ] 激活 STM32 子任务：py -V:Astral/CPython3.12.13 ./.trellis/scripts/task.py start .trellis/tasks/10-06-stm32-peripheral-lessons
- [ ] 读取 trellis-before-dev 和该子任务全部上下文。inline 模式不需要 jsonl 注入，也不派发子代理。

## 分批交付

1. STM32 子任务：工具链/官方资料→三个裸机工程→四章→六图与乒乓图修订→E02/E03 STM32 部分→验收。
2. FreeRTOS 子任务：固定内核与端口→一个可切场景工程→三章及 F8 入口同步→五图→验收。
3. ESP32-S3 子任务：IDF 与板卡引脚核验→三个工程→三章→三图→E03 ESP32 部分→验收。
4. 总任务集成：三个板块导览、docs/index.md、README.md、CONTRIBUTING.md、必要规范更新；核对跨路线链接与说法；全范围最终验收。

每个子任务的完整执行清单见其 implement.md。依赖失败时不越过门禁宣布成功，可以继续撰写不依赖硬件参数的内容。

## 检查与证据

- 章节结构与事实人工审阅；逐图列出教学结论，对照时序、计算、源文件和正文。
- 图形核验：SVG XML 解析、viewBox、字号、SMIL 时间/值列表和资源引用检查；用浏览器观察关键阶段，单靠 XML 通过不算图形验收。
- 站点：npm run docs:build；浏览器抽查 /mcu/ 子路径、360/390px 窄屏和常见桌面宽度、深浅主题。
- 固件：STM32/FreeRTOS 通过各工程 make（-Wall -Wextra）及 objdump/nm；ESP32 通过导出 IDF 5.5.x 环境后的 idf.py set-target esp32s3、idf.py build、idf.py size。
- 无板则记录“待上板实测”；有板时按实验记录条件和原始结果，不填推测的测量数据。
- 规划期只检查文档与任务结构；此时无需为尚未产生的代码执行构建。
- 改动后使用 trellis-check；最终质量检查覆盖全部受影响层。不存在的 lint/typecheck 命令不编造，docs:build 是当前站点门禁。

## 收尾

- 审阅并同步本轮确认的新知识到 .trellis/spec/，尤其图片引用、芯片型号差异和内核版本边界。
- 根据实际改动列提交计划并按现有授权/工作流执行；仅任务规划完成不应归档实现任务。
- 子任务分别验收，父任务 A1–A7 全过后才判定总交付完成。
