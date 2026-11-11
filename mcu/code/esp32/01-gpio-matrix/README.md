# GPIO Matrix 换脚

基准：**ESP-IDF v5.5.2、ESP32-S3、立创实战派 N16R8**。不要把启动器 idf.py.exe 的版本当框架版本；用 IDF 源码版本或构建中的 project_description.json 核对。

## 引脚与配置

GPIO10/11，每 3 秒切换 1kHz、50% PWM；旧脚先断开。

来源：[立创官方资料](https://wiki.lckfb.com/zh-hans/szpi-esp32s3/beginner/introduction.html)。工程 main/main.c 顶部或配置结构集中定义。不同板卡修订先核对接线；八线 PSRAM 占用脚不用于测试输出。

## 构建与运行

先进入 ESP-IDF 5.5.2 已激活终端，再从仓库根执行：

~~~sh
cd code/esp32/01-gpio-matrix
idf.py set-target esp32s3
idf.py build
idf.py size
idf.py -p COMx flash monitor
~~~

COMx 换成真实串口，Linux 例如 /dev/ttyACM0；退出监视器用 Ctrl+]。set-target 会重新生成本地 sdkconfig，切换目标前保存个人配置。CI 使用 build/ci 下独立 sdkconfig，避免旧 esp32 构建缓存影响 S3 验证。

## 观察与排查

逻辑分析仪或示波器分别接 GPIO10/11、GND 共地；示例不驱动板载 LED。

两个脚同时有波形：确认固件含 gpio_reset_pin；无波形：核对引脚/地线；不要使用 IO35/36/37。

## 验证状态

目标芯片由干净构建验证为 esp32s3。构建结果与体积记录在本任务验收记录中；板上读数、波形或听感仍 **待上板实测**，上面的现象是预期而非实测记录。
