# E04 优先级反转上板实测：两臂跑完并回填实测记录表

## Goal

`docs/lab/e04-priority-inversion.md:101` 那张四行表（FreeRTOS/RT-Thread × 信号量/互斥量）从建章至今一行数字都没有。
本任务的唯一产出是把它填成**串口读出来的实测值**。

## Requirements

- 四臂各跑一次：`make DEMO_SCENE=6`（信号量）/ `make DEMO_SCENE=6 USE_MUTEX=1`（互斥量），
  FreeRTOS 侧 `code/rtos/01-freertos-lab`（scene 6 在 `main.c:271`，`USE_MUTEX` 分支在 `:347`），
  RT-Thread 侧 `code/rtos/02-rt-thread-lab/applications/main.c`（scene 6 在 `:82`）。
- 剧本是单次的（三任务演完一轮就睡），每臂**复位重演**再取数，别让上一轮的日志搅进来。
- 每行记：日期 / 版本（FreeRTOS-Kernel V11.1.0 与 RT-Thread 实际版本号 + 仓库 commit）/ H 等待时间 / M 是否插足 / 备注。
- 硬件口径：STM32F407，HSI 16MHz 不走 PLL，USART1 PA9/PA10 @115200。HSI 的精度直接进备注。

## 硬约束

- **模型值和理论值一律不得当作实测填进表里**。6000/2500 目前是宿主机调度模型 `sim_invert.c` 推出来的
  （F5 成片里已逐处标成「模型值」，文档 `:78` 也写明「不是实测数据」）。表里只允许串口日志读出的数。
- 允许在备注里写「实测 vs 剧本理论值 的偏差及原因」，但不许改 `:82` 那张理论表的任何一格。

## Acceptance Criteria

- [ ] 四行都有实测数字，且每行能追溯到一次具体烧录（日期 + commit + 串口日志留档路径）。
- [ ] 「M 是否插足」按日志实际现象填，不按剧本预期填。
- [ ] 若某臂与理论值差得离谱，先排两个已知陷阱（文档 `:73`）：
      L 的临界区若写成 `vTaskDelay(3000)` 则两臂等待一样长（必须用 `cpu_work_ms`）；
      RT-Thread 侧 `rt_thread_create` 后漏 `rt_thread_startup` 会编译链接全过但线程永不跑。
- [ ] F5 成片与 `docs/rtos/` 章节里「模型值」的措辞不因本次实测而回改；实测若与模型值吻合，另起一句注明。

## Notes

- 顺手修一处过期注释：`code/rtos/01-freertos-lab/main.c:2` 写着「五个场景（编译开关 DEMO_SCENE=1..5）」，
  实际 scene 6 已存在。
