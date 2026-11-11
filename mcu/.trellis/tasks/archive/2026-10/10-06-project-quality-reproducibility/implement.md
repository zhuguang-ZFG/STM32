# 执行与验收计划

## 当前状态

- 用户授权评估中八项问题全部处理；用户已审阅，任务已激活；本地代码与验证完成，集成提交和远端 CI 已完成；硬件仍明确标待实测。
- python 命令不可用，但 python3 可运行 Trellis；mingw32-make、IDF 启动器存在。ARM 编译器候选路径见规范，实施时确认。
- 所有工作由主会话实施。步骤依赖为 1→2→3→4→5→6。

## 执行步骤

1. [x] 审阅三份规划后激活任务，加载 trellis-before-dev、docs-site、firmware-stm32、firmware-esp32 与 guides 规范。记录原始 git diff/B3 变更，核实工具链与一手资料。
2. [x] D1：复现场景切换复用旧对象，改为场景隔离；验证 1→2→1 和 flash 路径。登记全部工程/probe，建立清单校验与统计。
3. [x] D2：补三个既有 ESP32 README 并干净构建；逐个完成 E05/E07/E08 工程、固定依赖、编译/size 证据、源码导入和实验说明。每个完成即验证，有硬件再执行上板并留证。
4. [x] D2：审计 E01–E08 的入口、先修、状态与证据；统一时长难度及严格元数据检查；修复 P12 算式/时钟说明。
5. [x] D3：复用质量工作流和固件矩阵，发布显式依赖同一提交的门禁。核对失败/取消/跳过、权限和 concurrency。
6. [x] D3：高亮配置、性能基线和针对性优化；同步统计，全部门禁通过，检查改动边界，更新规范与验收记录。

## 验证命令

以下已有命令继续保留；新测试入口实现后再登记 package.json。

~~~text
python3 ./.trellis/scripts/get_context.py
python3 ./.trellis/scripts/task.py start .trellis/tasks/10-06-project-quality-reproducibility  # 仅方案审阅后
npm run docs:gen
npm run readme:sync
npm run readme:check
npm run links:check
npm run anim:lint
npm run docs:build
node --test <新增清单/元数据/场景选择回归测试>
mingw32-make -C code/rtos/01-freertos-lab DEMO_SCENE=1
mingw32-make -C code/rtos/01-freertos-lab DEMO_SCENE=2
mingw32-make -C code/rtos/01-freertos-lab DEMO_SCENE=1
mingw32-make -n -C code/rtos/01-freertos-lab DEMO_SCENE=2 flash
idf.py set-target esp32s3
idf.py build
idf.py size
~~~

## 必要验证

- 场景：检查各场景真实产物/编译宏差异，覆盖五场景、连续切换与非法值，不能只检查 Makefile 文本。
- 清单/元数据：临时 fixture 覆盖空目录、缺失入口、重复登记、缺字段、非法枚举/数字和正常输出，不改真实教程造测试数据。
- 固件：实际编译链接；按规范验证 ARM 向量表/告警，IDF 六工程分别干净构建并 size 留证；上板命令前核对设备与串口。
- CI：YAML/依赖图验证，有可用远端运行时再验证失败禁止发布；只完成静态检查时不称远端通过。
- 浏览器：首页、代表动画页、搜索、主题、暂停播放、减少动效、移动视口；递归产物清点和真实初始请求，不能从构建警告直接推导页面慢。

## 证据与完成门槛

- research/validation.md 保存版本/命令/结果/未通过项与 A1–A8 映射；research/performance.md 保存基线和优化前后测量。
- 硬件无证据保留 pending；工程实现和必需构建未完成时不标 completed。
- 最终确认 B3 原工作未覆盖，统计同步，保留各检查退出状态。
- 代码写完加载 trellis-check，收尾加载 trellis-finish-work，记录实际完成范围与残余验证项。

## 最终状态

B3 与质量修复已提交推送。远端全部 9 个 jobs（含 Pages）成功：[运行记录](https://github.com/zhuguang-ZFG/mcu/actions/runs/37492733587)。上板测量仍为独立后续事项，不影响本次软件/CI 修复验收。
