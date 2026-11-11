# 前置章节执行计划

## 硬依赖

knowledge-fact-corrections 已验收；其学习关系、计数、同步和 DMA 结论为本批基础。

## 顺序

1. [x] 读取全部 16 篇现有页面与必需一手资料，画 must/parallel 学习关系。
2. [x] B1/C0/C2/C4/C6：宿主/ARM 探针和正文同时完成，核对优化级别差异。
3. [x] S1/S4/S5/C5：完成中断、时基、状态机示例，修正输入/输出引脚和嵌套延时前提。
4. [x] F0/F8/S16：移植、故障取证和排查流程完整；验证栈帧/优先级解释。
5. [x] P1/P3/P4 与 S9：完成 S3 机制和双板记录器输入前置。
6. [x] 每章验收后才标 done；更新 sidebar/index/计划/前置关系/工程清单。
7. [x] 完整门禁、样例 CI、来源与待测项审查；提交推送。

## 验证

- 宿主编译与断言、ARM 编译链接与符号/反汇编、IDF set-target/build/size。
- 先修图不允许 must 环，parallel 不误报；生成统计与 README 一致。
- npm run quality、firmware:check、test:browser。
- 仅抽查动画图片不算时序验证；新增/修改动画按现有 animation 规范做阶段检查。

## 完成与回退

research/validation.md 按 P-A1–P-A7 记录，未达某章要求则保留 building 并继续完成，不把缺内容转为“后续再补”而声称本批完成。每组提交可独立回退，但前置关系和引用同时处理。
