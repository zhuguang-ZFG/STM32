# firmware-esp32 规范

`code/esp32/` 下的 ESP-IDF 工程（基准：立创实战派 S3，N16R8）。CI 固定 `espressif/idf:v5.5.2`；
IDF 内置的是 FreeRTOS **V10.5.1 SMP 修改版**，与 `code/rtos/01-freertos-lab` 的上游 V11.1.0 不同源，
行号/栈参数单位/调度结论不得混读。

## 动手前必读与跨层路由

- 改 IDF 工程结构、target、组件、IRAM/双核：本合同。
- 改共用协议/健康监测/串口 CLI：读 [firmware-common](../firmware-common/index.md)；平台 port 仍归本层。
- 改 logger 或 SAMPLE/TLV：读 [logger-contract](../docs-site/logger-contract.md)。
- 改 FreeRTOS/RT-Thread 内核结论：读 [firmware-rtos](../firmware-rtos/index.md)；IDF 内置版本只按本层的 v5.5.2/V10.5.1 口径写。
- 改 `faults`/`variants`/CI 矩阵：读 [quality-contract](../docs-site/quality-contract.md)；矩阵字段真源是 `scripts/project-catalog.mjs --matrix`。
- 写"已验证"前：芯片编译（IDF build）与上板测量分开；无板时只写构建/体积证据。

## 工程结构

照 `code/esp32/00-hello/`：

```
<demo>/
├── CMakeLists.txt          # cmake_minimum_required + include(project.cmake) + project()
├── main/
│   ├── CMakeLists.txt      # idf_component_register(SRCS ... INCLUDE_DIRS "")
│   └── <demo>_main.c       # app_main，逐行注释
└── （sdkconfig 为构建产物，不进 git；差异配置写 sdkconfig.defaults）
```

## 纪律

- `set-target esp32s3` 永远是第一步（换 target 会重置 sdkconfig）；
- 新组件显式声明依赖：`REQUIRES`（公开）/`PRIV_REQUIRES`（私有），不依赖间接拉入；
- 使用 ESP_INTR_FLAG_IRAM 时，可达代码放内部 IRAM/ROM，可达数据放内部 RAM；普通非 IRAM-safe 中断在 Flash 操作期间可被延后；ISR 里禁 printf/malloc/Flash 写（详见 `docs/esp32/04-irq-dualcore.md`）；
- 双核共享数据用 portMUX 自旋锁或原子内建，**禁裸 volatile 跨核**；
- 引脚号/外设 GPIO 分配一律以立创 wiki 原理图为准并在注释注明出处，禁止编造；
- Kconfig 选项进组件自带 `Kconfig` 文件；配置改动走 menuconfig，不手改 sdkconfig。

## 质量检查

```bash
idf.py set-target esp32s3 && idf.py build     # 必须零错误；有板时 idf.py -p COMx flash monitor
idf.py size                                    # 记录体积
npm run projects:check
node scripts/project-catalog.mjs --matrix      # 核对 normal/faults 行与 defaults
```

- 无板环境：build 通过 + `idf.py size` 记录体积；
- 未上板验证的在工程 README 标注"待上板实测"。

## 可复现检查

CI 使用 `build/ci-$VARIANT` 独立 sdkconfig，显式 `set-target esp32s3`；普通与 `faults:true` 工程分别用矩阵给出的
`sdkconfig.defaults` / `sdkconfig.defaults;sdkconfig.defaults.faults`，命令为
`idf.py -B build/ci-$VARIANT -D SDKCONFIG=$PWD/build/ci-$VARIANT/sdkconfig -D SDKCONFIG_DEFAULTS=$DEFAULTS set-target esp32s3`，
随后同一组参数 `build size`；验收读取 `project_description.json` 的 target，不以旧 build 缓存证明芯片正确。
依赖组件固定版本，新音频工程提交 `dependencies.lock`。PCA9557 bit1 才是本板 PA_EN，不是 ESP32 GPIO1。
GPIO Matrix 换脚必须断开旧输出，禁止在 PSRAM 占用脚做输出实验。

质量检查：改工程/组件先跑 `idf.py build`（有 IDF 环境时）并记录 `idf.py size`；改登记/矩阵跑
`npm run projects:check` 与 `node scripts/project-catalog.mjs --matrix`；改共用代码另跑
[firmware-common](../firmware-common/index.md) 的 probe。工程清单/CI 接口见 [quality-contract](../docs-site/quality-contract.md)。
