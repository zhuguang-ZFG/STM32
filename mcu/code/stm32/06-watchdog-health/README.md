# F407 健康监督与看门狗

两个任务完成一轮有界工作后上报进展；监督是唯一喂狗者。普通构建不支持TEST_FAULT，开启测试选项也需主机显式命令。硬件现象待上板实测。

## 构建

~~~sh
make MODE=0 FAULTS=0
make MODE=1 FAULTS=0
make MODE=2 FAULTS=1
make MODE=3 FAULTS=1
~~~

F407：FreeRTOS V11.1.0/ARM_CM4F，HSI16，产物 build/mode-N-faults-N；同参数 make flash 用 ST-Link。S3：IDF5.5.2，flash monitor 的端口必须显式指定。故障构建使用独立 sdkconfig，并合并 sdkconfig.defaults.faults。

## 接线与命令

3.3V USB-TTL TX接板RX，RX接板TX，GND共地。F407 PA9/PA10，S3 GPIO10/11；F407调试走SWD，S3日志走默认控制台，不把文本混入二进制口。

仓库根运行 python3 scripts/device-console.py info --port COMx 或 status --port COMx。
测试固件运行 fault --fault 1 --task 0 --port COMx 暂停worker进展，fault 2停止监督服务；200ms延迟后生效。没有收到响应不代表故障没有执行，故障命令不自动重试。

## 边界

IWDG名义2秒不代表实测精度；WWDG窗口跟PCLK1相关。断开调试器并重新启动后测复位，先读原因再清标志。noinit/RTC数据仅带CRC辅助暖复位诊断，不保证掉电保存。
普通通信空闲不会造成健康超时。重启锁存不会被迟到心跳解除。配置错误或驱动失败不能静默忽略。

完整配置、原理与自测见站内 S17 或 P13；数据口和协议见 C8。
