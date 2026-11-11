# 全书工程与产物交付收口执行计划

状态planning，尚未执行。

## 顺序

1. 审收口方案
2. start本任务
3. 固定当前runner/策略与用户源
4. 每告警一个区分实验/修复
5. 窄回归+真实运行
6. 47工程矩阵
7. 授权硬件
8. 最终全书PDF/包
9. 提交分组确认
10. PR全绿
11. 精确head合并
12. main同SHA/线上。

## 验证

采用既有quality/browser/firmware/catalog矩阵、PDF13门、package自证和CI；task_verify独立分passed/failed/unverified。新增测试/runner/策略待review且新用户回合建baseline前不算operator已验证。

每个结果附源SHA、命令/场景与实际输出；passed/failed/unverified分开。任意阶段只完成子步骤不冒充任务完成；用户当前仅批准规划，具体方案需审后才start。

## 完成与交接

按PRD逐项核验，更新父任务台账与证据；未满足依赖继续blocked且保留可达工作。不自动替其他任务提交或归档。
