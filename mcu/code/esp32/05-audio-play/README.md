# ES8311 音频

基准：**ESP-IDF v5.5.2、ESP32-S3、立创实战派 N16R8**。不要把启动器 idf.py.exe 的版本当框架版本；用 IDF 源码版本或构建中的 project_description.json 核对。

组件管理器下载 **espressif/esp_codec_dev 1.3.4**（固定版本），初始化接口参照 IDF 同版本 i2s_es8311 示例；不混用旧 I2C 驱动。

## 引脚与配置

I2C SDA/SCL=1/2；I2S MCLK/BCLK/WS/DOUT=38/14/13/45；PCA9557 地址 0x19 bit1 控功放。

来源：[立创官方资料](https://wiki.lckfb.com/zh-hans/szpi-esp32s3/beginner/audio-output-es8311.html)。工程 main/main.c 顶部或配置结构集中定义。不同板卡修订先核对接线；八线 PSRAM 占用脚不用于测试输出。

## 构建与运行

先进入 ESP-IDF 5.5.2 已激活终端，再从仓库根执行：

~~~sh
cd code/esp32/05-audio-play
idf.py set-target esp32s3
idf.py build
idf.py size
idf.py -p COMx flash monitor
~~~

COMx 换成真实串口，Linux 例如 /dev/ttyACM0；退出监视器用 Ctrl+]。set-target 会重新生成本地 sdkconfig，切换目标前保存个人配置。CI 使用 build/ci 下独立 sdkconfig，避免旧 esp32 构建缓存影响 S3 验证。

## 观察与排查

1kHz 1秒，再播放 8 音符后关闭功放。16kHz/16bit 两槽位重复同一单声道数据，无版权音乐依赖。

无声先看 I2C 报错与 PCA9557 功放；变调查采样率/MCLK；不能用 ESP32 GPIO1 代替扩展器 bit1。

## 验证状态

目标芯片由干净构建验证为 esp32s3。构建结果与体积记录在本任务验收记录中；板上读数、波形或听感仍 **待上板实测**，上面的现象是预期而非实测记录。
