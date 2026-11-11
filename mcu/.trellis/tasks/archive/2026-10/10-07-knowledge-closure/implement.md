# 总体执行计划

## 进入实施前

- [x] 用户确认四阶段处理顺序。
- [x] 用户确认两块板都做完整综合项目。
- [ ] 用户审阅父任务与四份子任务方案。
- [ ] 审阅通过后按顺序 task.py start 对应子任务；父任务保持总体追踪。
- [ ] 加载 trellis-before-dev，读取各子 artifacts 与 docs-site/firmware/guides 规范；inline 模式不整理 jsonl。

## 交付顺序

1. knowledge-fact-corrections：先复现 TIM/DMA 问题，再修代码、正文、图与断言，建立学习关系口径。
2. knowledge-prerequisites：按内部依赖完成 16 篇前置；每组完成即核对先修、源码与测试。
3. knowledge-reliability：先固定公共协议和测试向量，再完成两板协议/看门狗示例、主机工具和教材。
4. knowledge-capstone：分别完成两板完整数据流及配置恢复；对同一主机测试矩阵给出结果。
5. 父任务集成：核对全部验收、知识点覆盖、版本/引脚/状态、主机工具、清单和导航；提交推送后确认远端 CI 全绿。

## 每批质量检查

~~~text
npm run quality
npm run firmware:check
npm run test:browser
git diff --check
~~~

IDF 新工程逐个 set-target esp32s3、build、size；主机公共逻辑在 CI 的 Linux 上启用可用的 AddressSanitizer/UndefinedBehaviorSanitizer，同时保留 Windows 普通构建。已有代码未变且已通过的检查不无故重复，新更改影响的链路必须重跑。

## 证据与记录

- 各子任务保存来源、版本、回归输入/输出、构建记录；父任务汇总需求→子任务→验收→CI。
- 模型和硬件结果不能互换。硬件不可用时继续完成代码与模型，并明确未验证项。
- 提交/推送沿用用户已授权流程；不 force push，不提交本轮之外的未审阅改动。
- 完成后使用 trellis-check、trellis-update-spec 与 trellis-finish-work；只归档实际完成的任务。
