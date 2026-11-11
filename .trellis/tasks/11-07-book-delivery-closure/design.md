# 全书工程与产物交付收口设计

以总任务delivery-closure.md为逐项故障假设/实验、源锚点与硬件/权限边界。现有API只有plan/run/status，不自行伪造配置；当前仅见蓝牙串口，不主动reset/flash。每项失败保存最小复现，两个假设，小实验，修一个原因；新回归必须旧失败新通过，不削弱断言。

## 合同与依赖

工程告警修复可独立审后实施；最终PDF/发布等内容图冻结；operator基线与明确硬件/可写授权为外部前提。

父任务research/teaching-contract、illustration-plan、planning-baseline为共用接口；不复制新测试或守卫实现。范围外错误先记录再审，不实施多处猜测修补。回退只本子任务写入，遇并发改变先重读，不stash/reset/clean。
