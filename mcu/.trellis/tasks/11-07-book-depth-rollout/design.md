# 全量推广与附录一致性设计

按manifest现有分部、batches.json中的B01–B23顺序选批，不重排教材。附录C答案来自quizzes:auto，不在附录里维护副本；B工程目录、D术语、E来源许可、FFAQ各自核真源。每批收敛独立PRD/来源/允许增量，不一次向所有文件铺模板。

## 合同与依赖

样章6章用户验收；每批具体范围/来源/图计划另审后才能实施。

父任务research/teaching-contract、illustration-plan、planning-baseline为共用接口；不复制新测试或守卫实现。范围外错误先记录再审，不实施多处猜测修补。回退只本子任务写入，遇并发改变先重读，不stash/reset/clean。
