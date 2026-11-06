# 实施记录：B0语言通俗化

## 已完成

- [x] 用户审阅具体B0范围并选择“通过，启动 B0 试点”；task.py start成功，状态in_progress。
- [x] 核对既有精修保护合同与当前章节，按入口/命令/角色/newlib列诊断。
- [x] 保存原文before快照与SHA256，候选稿独立编辑后严格prose_guard通过，落盘唯一正文B0。
- [x] 保留代码/行内代码/表格/标题/frontmatter/链接与数字事实；未改测试、runner、CI、阈值或prose基线。
- [x] 最终原文对正文prose_guard通过；prose:check、reading:check、book:check、docs:build通过。
- [x] 真实浏览器1440与390宽截图检查；图片、动画、命令与折叠答案正常，无文档横向溢出或page errors。
- [x] task_verify实际运行，结果unverified / project-or-git-baseline-unavailable / checks=[]，不算通过。
- [x] 原文疑点和改写对照记录于research/pilot-evidence.md。
- [x] 关闭本任务tab与预览服务；未提交推送或发布。

## 验证限制

下一站链接click助手两次未送达，滚入后也失败；换命中检查发现中心命中父div。href目标实际HTTP200且含B1标题，只证明目标可达，不证明实际鼠标导航成功。本轮未修改CSS或扩展问题范围。

## 待用户验收

- [ ] 用户评价B0是否更易理解，决定保留、调整或回退本试点。
- [ ] 验收后另行选择下一批，不自动扩展全书。

所有实测命令、输出摘要、原文事实审查遗留及before/candidate在research/pilot-evidence.md；历史checkpoint不作为测试证据。
