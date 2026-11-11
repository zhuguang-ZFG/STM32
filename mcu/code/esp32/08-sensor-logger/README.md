# J2 ESP32-S3 传感器记录器

板载 QMI8658：GPIO1 SDA、GPIO2 SCL，7位地址0x6A。GPIO10 UART1 TX、GPIO11 RX接3.3V USB-TTL；默认控制台单独输出调试日志。NVS只访问 mcu_logger 命名空间的 config 键，不自动擦整个分区。

## 构建与运行

进入本目录，在 ARM GCC/FreeRTOS11.1.0 或 IDF5.5.2 环境执行：

~~~sh
idf.py set-target esp32s3
idf.py build
idf.py -p COMx flash monitor
~~~

F407需ST-Link与外接AT24C02/电位器；S3使用板载IMU，数据口另接USB-TTL。F407从HSI16复位状态启动。
主机在仓库根运行 scripts/device-console.py 的 info/status/configure/save/start/stop/record。示例：

~~~sh
python3 scripts/device-console.py configure --period 200 --filter-shift 2 --port COMx
python3 scripts/device-console.py save --port COMx
python3 scripts/device-console.py record --seconds 10 --output samples.csv --port COMx
~~~

协议和运行流程详见 [站内教程](../../../docs/projects/02-s3-logger.md)，公共核心在 code/common/logger。record覆盖指定CSV，请使用新路径。

## 验证与边界

共享核心覆盖每个写入切点的配置恢复、端序、滤波、队列与无效数据。硬件驱动真实接入，但物理采样、复位与掉电结果仍待上板实测。
默认不开故障注入。F407 FAULTS=1 或S3 sdkconfig.defaults.faults仅允许显式故障命令，不上电自动卡死。
UART不保证接收端确认或无限离线缓存；丢弃有计数。STOP保留通信/监督，SAVED只在存储完成后应答。
