# J1 STM32F407 传感器记录器

PA0 为 ADC1_IN0：外接电位器中间脚，另外两端接3.3V和GND；先移除旧 PA6→PA0 测频跳线。PB6/PB7 接 AT24C02 SCL/SDA、各4.7k上拉至3.3V，A0–A2和WP接地。模块256字节全部作为配置双槽使用，会覆盖旧EEPROM实验数据。USART1 PA9 TX/PA10 RX接3.3V USB-TTL。

## 构建与运行

进入本目录，在 ARM GCC/FreeRTOS11.1.0 或 IDF5.5.2 环境执行：

~~~sh
make MODE=0 FAULTS=0
make MODE=0 FAULTS=0 flash
~~~

F407需ST-Link与外接AT24C02/电位器；S3使用板载IMU，数据口另接USB-TTL。F407从HSI16复位状态启动。
主机在仓库根运行 scripts/device-console.py 的 info/status/configure/save/start/stop/record。示例：

~~~sh
python3 scripts/device-console.py configure --period 200 --filter-shift 2 --port COMx
python3 scripts/device-console.py save --port COMx
python3 scripts/device-console.py record --seconds 10 --output samples.csv --port COMx
~~~

协议和运行流程详见 [站内教程](../../../docs/projects/01-f407-logger.md)，公共核心在 code/common/logger。record覆盖指定CSV，请使用新路径。

## 验证与边界

共享核心覆盖每个写入切点的配置恢复、端序、滤波、队列与无效数据。硬件驱动真实接入，但物理采样、复位与掉电结果仍待上板实测。
默认不开故障注入。F407 FAULTS=1 或S3 sdkconfig.defaults.faults仅允许显式故障命令，不上电自动卡死。
UART不保证接收端确认或无限离线缓存；丢弃有计数。STOP保留通信/监督，SAVED只在存储完成后应答。
