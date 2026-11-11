# firmware-rtos 规范索引

`code/rtos/` 的 RTOS 工程：上游 FreeRTOS-Kernel 与 RT-Thread 的可复现移植、场景切换、对照实验与证据边界。
本层只管**内核/移植/构建**；板级外设与启动文件仍归 [firmware-stm32](../firmware-stm32/index.md)。

| 文件 | 内容 |
|---|---|
| [kernel-contract.md](kernel-contract.md) | 两个内核的版本/缓存来源、端口、配置宏、场景与构建目录、USE_MUTEX 隔离、F02 风险与上板边界 |

## 适用范围

- 改 `code/rtos/01-freertos-lab/`、`02-rt-thread-lab/`、`00-why-rtos/`、`03-scheduler/`、`05-sem-mutex/`、`06-timers/`。
- 改 `code/projects.json` 的 `rtos-*` 登记（`scenes` 只接受精确形状，见 [quality-contract](../docs-site/quality-contract.md)）。
- 改 `docs/rtos/` 的正文时：内核结论必须与本层的版本/端口口径一致，不能把 FreeRTOS V11 的行号套到 ESP-IDF 的 V10.5.1 SMP 上。

## 动手前必读

- 改任何 `Makefile`：先读 [kernel-contract.md](kernel-contract.md) 的构建目录与参数隔离一节。参数不是 make 的文件依赖，目录隔离是唯一可靠的重建边界。
- 改 `FreeRTOSConfig.h` / `rtconfig.h`：确认该宏被哪些场景使用；`INCLUDE_*` 在 V11 默认关闭，缺一个就链接失败。
- 改带锁场景：`USE_MUTEX` 只对场景 6 有意义；F02 的缓存风险未证实前，不要写"所有参数变更自动隔离"。
- 写运行时结论：先分清"宿主机模型/反汇编/芯片编译/上板实测"；板上日志与时序在回填前一律标 pending。

## 快速命令

```bash
# FreeRTOS：需先取内核源码（默认 .trellis/ref/freertos-v11/kernel，或 FREERTOS_KERNEL=…）
cd code/rtos/01-freertos-lab && make DEMO_SCENE=1
make DEMO_SCENE=6 USE_MUTEX=1          # 优先级反转·互斥量版（重建前先看 F02）
make flash                             # OpenOCD + ST-Link，有板才执行

# RT-Thread：需先稀疏检出 .trellis/ref/rt-thread，或 RT_THREAD_DIR=…
cd code/rtos/02-rt-thread-lab && make DEMO_SCENE=1
make DEMO_SCENE=6 USE_MUTEX=1          # 目录自动带 -mutex 后缀
make flash

# 宿主机取证（不需要板）
sh code/rtos/00-why-rtos/probe.sh
sh code/rtos/03-scheduler/probe.sh
sh code/rtos/05-sem-mutex/probe.sh
sh code/rtos/06-timers/probe.sh
npm run firmware:check                 # 全场景构建 + 场景/变体隔离断言（不含 ESP-IDF）
```

## 质量检查

| 改动 | 检查 |
|---|---|
| 场景/构建目录 | `npm run firmware:check`：相邻场景产物不同、切回首场景字节一致、非法场景非零退出 |
| 配置宏/内核源 | 对应 `make -B DEMO_SCENE=n` 零警告；内核源按上游原样编译，不参与 `-Werror` |
| 优先级反转实验 | 先构建两版，再上板回填 `docs/lab/e04-priority-inversion.md` 的实测表；未回填保持 pending |
| 工程登记 | `npm run projects:check`；`scenes` 必须是 `[1,2,3,4,5]`/`[1,2,3,4,5,6]`/`[1,6]` |
| 文档结论 | 与 [kernel-contract.md](kernel-contract.md) 的版本表对账；不混用 IDF 内置 FreeRTOS 的行号 |

## 金样例

- FreeRTOS 场景与日志预期：`code/rtos/01-freertos-lab/README.md`（场景 1–6、`vTaskList`、heap_4 合并）。
- RT-Thread Nano 裁剪与移植：`code/rtos/02-rt-thread-lab/README.md`（src 裁剪表、`__RT_KERNEL_SOURCE__`、E04 双跑）。
- 宿主机调度取证：`code/rtos/03-scheduler/scan_cost.c` 与对应 `probe.sh`。
- 优先级反转模型：`code/rtos/05-sem-mutex/sim_invert.c`、`lineage_probe.c`、`sizes_probe.c`。
