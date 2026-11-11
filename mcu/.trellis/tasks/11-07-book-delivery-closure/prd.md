# 全书工程与产物交付收口

## 目标与授权

隶属11-07-book-depth-handdraw。当前仅规划授权，不start、不实施或发布。总需求以父任务PRD为准，本任务独立验收，不能用别的子任务绿色代替。

## 范围

- docs/.vitepress/config.mts
- docs/.vitepress/code-languages.mjs
- docs/.vitepress/theme/RegisterExplorer.vue
- docs/animations.md
- scripts/check-firmware.mjs
- code/projects.json
- mcu-book/build_html.py
- mcu-book/build_print.py
- mcu-book/check_pdf.py

## 需求

- C1 逐个定位并消除h/kconfig、重复import、chunk体积告警，不提高阈值或吞告警
- C2 operator合法基线与检查覆盖
- C3 47工程分ARM/host和ESP矩阵验证
- C4 设备/探针/授权到位后真实硬件证据
- C5 完整HTML/A4/16开与下载物原合同
- C6 白名单提交PR全绿合并与同SHA线上验证。

## 验收

告警根因修正并窄回归/真实组件路径过；47工程所有配置实际成功且硬件另记；operator实际checks记录可核，无基线不得算绿；HIL逐实验/项目预期实际和照片日志波形齐；完整PDF13门/图文位置/包摘要一致；PR当前head和main同SHA运行成功，未夹带用户WIP。

## 依赖与外部前提

工程告警修复可独立审后实施；最终PDF/发布等内容图冻结；operator基线与明确硬件/可写授权为外部前提。

## 保护

保留既有B7四行与用户42文件，214验证输入固定。代码/表格/标题/数字/引文/链接变更需显式证据review，不降低守卫策略。无设备不称HIL过，无operator基线保持unverified。与其他任务职责不重叠覆盖。
