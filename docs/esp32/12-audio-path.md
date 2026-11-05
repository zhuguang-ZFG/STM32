---
title: P12 音频链路：从 I2S 时序到"hello 语音"
status: done
difficulty: 3
minutes: 45
---

# P12 音频链路：小智板的看家本领

> 🎯 立创实战派 S3 不是普通开发板——它天生是"会说话的终端"：双麦克风 + 1W 喇叭 + ES8311 解码 + ES7210 采集。打通这条音频链路，你就站在了"小智 AI 语音助手"的家门口。

## 本章精髓

1. I2S 是音频的"传送带协议"：三根线（BCK 位时钟/WS 声道选择/DATA 数据）按帧传输：**采样率×位宽×声道数=带宽**（16kHz×16bit×1=256kbps 有效 PCM 数据；两个 16bit 槽位的 I2S 帧时钟为 512kHz），MCLK 供给 codec 的 PLL（与 [S12 SPI](../stm32/12-spi.md) 对照：都是同步移位，I2S 多了"帧=左右声道"的语义）。
2. codec 是"模拟↔数字翻译官"：ES8311（DAC：数字→喇叭）与 ES7210（ADC：麦克风→数字）都挂 I2C 配置、走 I2S 传数据：**控制面（I2C）与数据面（I2S）分离**是音频芯片的通用范式（这就是四件套的完整用武之地）。
3. 功放与麦是"最后一厘米"：NS4150B D 类功放放大功率推喇叭；双模拟麦经 ES7210 四通道（用其三）采集：回声消除/波束成形的算法空间就藏在这"双麦"里。

- **能理解**：为什么 codec 要分控制面和数据面；为什么 stereo 双槽位要填同一份单声道样本；为什么 PA_EN 不在 ESP32 GPIO 上而在 I2C 扩展器。
- **能用**：照 E08 配出 16kHz/16bit 的 I2S + ES8311，让喇叭"滴"一声；看懂 main.c 里初始化链路的每一步在干什么。

## 先修

- [P6 I2C/SPI 驱动](06-spi-i2c-driver.md)（控制面）、[S12 SPI](../stm32/12-spi.md)（同步移位）、[F4 队列](../rtos/freertos/04-queue.md)（音频流缓冲）。

## 先跑起来（10 分钟 quick win）

播"滴"：内置一段 1kHz 正弦 PCM 数组（const，回 [C1](../c/01-memory-model.md)），I2S 写出：喇叭第一次在你代码控制下发声。

让喇叭滴之前先押个数量级：采样率、位宽、声道数相乘，这条传送带每秒要走掉多少 bit？心里先按下一个数量级，再拿精髓第一行的算式对账。差一位，后面 I2S 的时钟账就全对不上。

## 动画：实战派音频全链路

采集链与播放链一条传送带画完：麦 → ES7210 → I2S RX → S3（DMA→PSRAM）→ I2S TX → ES8311 → 功放 → 喇叭；I2C 控制面与 I2S 数据面分离，样本令牌在链路上持续流动。

![实战派音频全链路：控制走 I2C，声音走 I2S](/anim/esp32-audio-path.svg)

## 板卡事实

- 音频 codec：ES8311（DAC，I2C 配置+I2S 数据）；ES7210（四通道 ADC，I2C+I2S）；功放 NS4150B（D 类，单声道）；双麦 ZTS6216（模拟）。
- **全部 I2C 地址、I2S 引脚分配、功放使能脚以立创 wiki 原理图页为准**，成稿时逐项核对标注。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| I2S 协议 | BCK/WS/DATA/MCLK 时序；帧与声道语义 | 配置 |
| 控制面 vs 数据面 | I2C 配 codec（音量/使能/格式）+ I2S 跑数据 | 配置 |
| ES8311 播放 | 初始化序列→I2S TX→正弦发声 | 代码分析 |
| ES7210 采集 | I2S RX 读 PCM；RMS 能量计算 | 代码分析 |
| 全双工回环 | 采集→直通播放（耳返实验）；缓冲与延迟账 | 代码分析 |
| 通往小智 | 语音链路之后：Opus 编码/AEC/唤醒词的位置地图 | 库解析 |

## 一、I2S 协议：音频的"传送带"

![I2S 时钟账：MCLK/BCK/LRCK 的比例](/figures/esp32-12-i2s-clock.svg)

I2S（Inter-IC Sound）是飞利浦定下的芯片间音频串行协议，本质是"按帧移位"，和 [S12 SPI](../stm32/12-spi.md) 同源（都是同步移位），但多了一层"帧=左右声道"的语义。

四根线：

- **BCK（Bit Clock）位时钟**：每一个 bit 一拍，移位基准。
- **WS（Word Select）声道选择**：又叫 LRCK。WS=0 传左声道，WS=1 传右声道。WS 频率 = 采样率 fs。
- **DATA（Serial Data）数据线**：按 BCK 节拍移位，MSB first。
- **MCLK（Master Clock）主时钟**：给 codec 内部 PLL 用，通常是 fs 的整数倍（256×fs 最常见）。

带宽公式：

```text
BCK 频率 = 采样率 × 位宽 × 声道数
MCLK 频率 = 采样率 × mclk_multiple（常用 256/384/512）
```

举例（E08 实测，main.c:18 `SAMPLE_RATE=16000`）：

- 16kHz × 16bit × 2ch(stereo) = 512kHz 的 BCK
- MCLK = 256 × 16000 = 4.096MHz（main.c:95 `I2S_MCLK_MULTIPLE_256`，main.c:126 日志 `MCLK=4096000`）

为什么 MCLK 是 256×fs：codec 内部有个 PLL，要从 MCLK 分频出 fs 的所有内部时钟（DAC 转换、滤波器等）。MCLK 必须是 fs 的高倍整数，PLL 才能稳锁。256 是历史惯用值（也兼容 384/512）。MCLK 没给或给错频率，codec PLL 锁不住，这是常见坑第一名。

帧与声道语义：一个 WS 周期是一"帧"，包含左槽位 + 右槽位。Philips 标准里 WS 在 BCK 下降沿提前一个 BCK 切换（给 codec 时间对齐）。stereo 模式两槽位都传；mono 模式只传一个，但 I2S 硬件通常仍按 stereo 跑，软件把同一份样本填两槽位（ES8311 就是这么干的，见第三节）。

## 二、控制面 vs 数据面：I2C 配、I2S 跑

音频 codec 不是"配一次就忘"的简单外设，它有两个截然不同的接口：

| 接口 | 走什么 | 干什么 | 频率 |
|---|---|---|---|
| 控制面（I2C） | 寄存器读写 | 配音量/使能/格式/PLL/mute | 偶发（初始化+调音量） |
| 数据面（I2S） | PCM 样本流 | 实时音频数据 | 持续（按 fs 流） |

为什么分离：I2C 慢（100kHz/400kHz），适合"偶尔改个寄存器"；I2S 快（MHz 级 BCK），适合"连续流数据"。如果控制也走 I2S，每次改音量都要打断数据流，不现实。所以业内通用范式就是"控制面 I2C + 数据面 I2S"，[P6 I2C/SPI 驱动](06-spi-i2c-driver.md) 的 I2C 在这里是 codec 的"遥控器"。

E08 实测（main.c:71-80）：

- I2C 总线：SDA=1, SCL=2（main.c:72），与 [P6](06-spi-i2c-driver.md) 同一套 I2C master 驱动
- ES8311 挂这条 I2C，地址 `ES8311_CODEC_DEFAULT_ADDR`（main.c:99）
- PCA9557 扩展器也挂这条 I2C，地址 0x19（main.c:78）：PA_EN 不在 ESP32 GPIO 上，而在扩展器的 bit1（main.c:81 注释明说"PA_EN 是 PCA9557 bit1，不是 ESP32 GPIO1"）

esp_codec_dev 把这套"控制面+数据面"封装成统一接口：`audio_codec_new_i2c_ctrl`（控制面，main.c:101）+ `audio_codec_new_i2s_data`（数据面，main.c:103）+ `es8311_codec_new`（芯片抽象，main.c:112）：你只跟 `esp_codec_dev_open/write` 打交道，I2C/I2S 的细节藏在下面。

## 三、ES8311 播放：从初始化到"滴"一声

ES8311 是单声道音频 codec（DAC+ADC，但板子上只用 DAC 路径推喇叭）。E08 的初始化链路（main.c:84-122）：

1. **建 I2S TX 通道**（main.c:84-87）：`I2S_NUM_0`、master 角色、`auto_clear=true`（写不动时自动输出静音，避免残留噪声）。
2. **配 I2S std 模式**（main.c:88-96）：
   - `I2S_STD_CLK_DEFAULT_CONFIG(16000)`：fs=16kHz
   - `I2S_STD_PHILIPS_SLOT_DEFAULT_CONFIG(16BIT, STEREO)`：Philips 标准、16bit、stereo
   - 引脚：mclk=38/bclk=14/ws=13/dout=45（main.c:92），din 未用（只播不采）
   - `mclk_multiple = 256`（main.c:95）
3. **建 codec 控制面+数据面+GPIO 抽象**（main.c:98-105）：I2C 控制面接 ES8311，I2S 数据面接 TX 通道。
4. **建 ES8311 实例**（main.c:106-112）：`codec_mode = DAC`、`master_mode = false`（ESP32 当 I2S master，codec 当 slave）、`use_mclk = true`、`mclk_div = 256`。
5. **包成 esp_codec_dev**（main.c:114-122）：`ESP_CODEC_DEV_TYPE_OUT`、采样信息 bits=16/channel=2/channel_mask=3/fs=16000。
6. **开 codec + 设音量**（main.c:122-123）：`esp_codec_dev_open` + `set_out_vol(40)`。

发声核心是 `tone()` 函数（main.c:48-67）：

```c
int16_t pcm[BLOCK_FRAMES * 2];   /* 双槽位：左右各一份 */
for (unsigned i = 0; i < count; ++i) {
    int16_t value = (int16_t)(3000.0f * envelope *
        sinf(6.28318530718f * frequency * n / SAMPLE_RATE));
    pcm[2*i] = value;      /* 左槽位 */
    pcm[2*i+1] = value;    /* 右槽位：同一份单声道样本 */
}
esp_codec_dev_write(codec, pcm, count * 2U * sizeof(int16_t));
```

关键细节：

- **stereo 双槽位放同一份单声道样本**（main.c:50 注释、main.c:62-63）：ES8311 是单声道 DAC，但 I2S 配的是 stereo，所以左右槽位填同一个值，否则只有一边出声。
- **首尾 10ms 淡入淡出**（main.c:59）：`envelope = fminf(n/160, (frames-1-n)/160)`，160 个样本 = 10ms（16000/1000×10）。避免方波边沿的"啪"声。
- **先静音 100ms 让 DMA 稳定**（main.c:124 `tone(0, 100)`）：DMA 启动有填充延迟，直接发声会丢头。
- **PA_EN 静音-发声-静音三段**（main.c:81/125/137）：上电先静音防爆音，发声前才 `amplifier(true)`，结束先静音再关功放。

## 四、ES7210 采集：双麦 PCM 与 RMS 能量

ES7210 是四通道音频 ADC，板子上用其中两个通道接双麦（见[板卡事实](#板卡事实)）。E08 工程只演示了播放（ES8311 DAC 路径），采集路径需要照同一套 esp_codec_dev 范式扩展：**引脚分配以立创 wiki 原理图与器件手册为准**，下面给骨架。

采集链路与播放镜像对称：

1. **建 I2S RX 通道**：`i2s_new_channel(&channel_cfg, NULL, &rx)`（第二参数 TX 给 NULL，第三参数 RX）。
2. **配 std 模式**：和 TX 同样 fs=16000/16bit，但 `din` 接 ES7210 的数据脚，`dout` 未用（引脚以立创 wiki 为准）。
3. **建 ES7210 codec 实例**：`es7210_codec_new`，`codec_mode = ESP_CODEC_DEV_WORK_MODE_ADC`，控制面挂同一 I2C 总线（地址以器件手册为准）。
4. **包成 esp_codec_dev**：`ESP_CODEC_DEV_TYPE_IN`。
5. **open + read** 循环读 PCM。

RMS 能量计算（判断"有没有人说话"的最简算法）：

```c
int16_t pcm[BLOCK_FRAMES * 2];   /* 双麦：左右槽位是两路麦 */
esp_codec_dev_read(codec, pcm, count * 2 * sizeof(int16_t));
float sum_sq = 0;
for (unsigned i = 0; i < count; ++i) {
    int16_t mic0 = pcm[2*i];     /* 麦 0 */
    int16_t mic1 = pcm[2*i+1];   /* 麦 1 */
    sum_sq += (float)mic0 * mic0;
}
float rms = sqrtf(sum_sq / count);
ESP_LOGI(TAG, "mic RMS=%.1f", rms);
```

RMS 越大说明能量越高：对着板子说话，RMS 跳动；安静时 RMS 接近本底噪声。这是"语音活动检测"（VAD）的最朴素形态，也是唤醒词的前置门槛。

双麦的意义：两个麦同一时刻采到不同相位的声波，波束成形（beamforming）靠相位差定向声源，回声消除（AEC）靠双通道互相关分离回声。这块板子天生为"小智类语音终端"准备，双麦不是冗余，是算法空间。

## 五、全双工回环：耳返实验与延迟账

"耳返"=采集到的声音实时从喇叭放出来，像歌手戴耳机听自己。这是音频链路最苛刻的测试：延迟超过 150ms 人耳就能察觉"回声感"，超过 300ms 就没法说话了。

回环结构（E08 扩展，待上板实测）：

```c
while (1) {
    esp_codec_dev_read(rx_codec, pcm, BLOCK_FRAMES * 2 * sizeof(int16_t));
    esp_codec_dev_write(tx_codec, pcm, BLOCK_FRAMES * 2 * sizeof(int16_t));
}
```

延迟账（每一段都是延迟来源）：

| 延迟来源 | 估算 | 说明 |
|---|---|---|
| 采集 DMA 缓冲 | BLOCK_FRAMES/fs | 一块填满才能读出 |
| 处理（直通≈0） | ≈0 | 不做 AEC/编码 |
| 播放 DMA 缓冲 | BLOCK_FRAMES/fs | 一块填满才能开始放 |
| codec 内部延迟 | ~几 ms | ES8311/ES7210 数字滤波器 |
| **总往返** | ~2×BLOCK_FRAMES/fs + 几 ms | |

E08 的 `BLOCK_FRAMES=160`（main.c:19），160/16000=10ms，往返约 20ms+：耳返能听见自己但不至于回声感。如果 BLOCK 拉到 512（32ms），往返 64ms+，开始难受。

缓冲与丢样本：采集端缓冲太小（[F4 队列](../rtos/freertos/04-queue.md) 账复用）会溢出丢样本，播放端没数据时出"嗤啦"杂音。容量按"采样率×容忍延迟"算：16kHz×50ms=800 样本，留 2 倍余量 = 1600 样本队列。

## 六、通往小智：Opus/AEC/唤醒词的位置地图

这条音频链路打通后，"小智 AI 语音助手"的剩下拼图在哪里：

| 模块 | 在链路哪一段 | 干什么 |
|---|---|---|
| AEC（回声消除） | 采集后、编码前 | 用播放参考信号减掉喇叭回采，避免"自己说的被听进去" |
| VAD（语音活动检测） | 采集后 | RMS/神经网络判断"有人说话吗"，没人就不上传省带宽 |
| 唤醒词（KWS） | 采集后 | "小智小智"本地关键词检测，触发上传 |
| Opus 编码 | VAD/KWS 后 | PCM→Opus 压缩，16kHz×16bit 单声道 → ~10kbps，省上传带宽 |
| 网络上传 | Opus 后 | 走 [P8 Wi-Fi](08-wifi.md) 的 socket，发到云端 ASR/TTS |
| Opus 解码 | 网络下行后 | Opus→PCM，喂给 ES8311 播放 |
| TTS（文本转语音） | 云端 | 云端把回答文本转 PCM/Opus |

整条链路：麦→ES7210→I2S RX→AEC→VAD/KWS→Opus 编码→Wi-Fi 上传→云端 ASR→LLM→TTS→Opus 下行→Wi-Fi 下载→Opus 解码→I2S TX→ES8311→NS4150B→喇叭。本章打通的是首尾两端（采集+播放），中间的 AEC/VAD/Opus 是"语音终端"的软件层：那是另一个故事，本章只给你"音频管道"的物理基础。

## 记忆锚点

::: tip 一句话记住
**控制走 I2C，数据走 I2S，codec 是翻译官，功放推喇叭；先滴一声，再听见自己——全双工一回环，小智就在眼前。**
:::

**延伸**：音频全链路动画见 [P12 动画](/anim/esp32-audio-path.svg)；I2S 与 SPI/I2C 的总线对比见 [P6](06-spi-i2c-driver.md)；DMA 搬运在 STM32 的对照见 [S8](../stm32/08-dma.md)。

## 实物实验

- [E08 音频放音](../lab/e08-audio-play.md)：正弦"滴"→PCM 小音乐片段；
- 耳返实验：采集直通播放，拍手听延迟，缓冲深度与延迟的取舍一手掌握。

## 常见坑

- **MCLK 没给/给错频率**：codec PLL 锁不住，无声或变调：256×fs 的经典关系先核对。
- **I2S 位宽/声道与 codec 配置不一致**：左右串、杂音、速度错：两边参数对齐表逐项打勾。
- **功放使能脚忘拉高**：I2S 数据在跑，喇叭无声：原理图上 PA_EN 脚是新手盲区。
- **采集缓冲太小溢出**：I2S RX 环形缓冲深度不足丢样本：按"采样率×容忍延迟"算容量（F4 队列账复用）。

## 短自测

1. I2S 的四根线各是什么？为什么 MCLK 通常是 256×fs？
<details><summary>看答案</summary>四根线：BCK（位时钟，每 bit 一拍）、WS（声道选择，又叫 LRCK，频率=fs）、DATA（串行数据，MSB first）、MCLK（主时钟，给 codec PLL）。MCLK 是 256×fs 因为 codec 内部 PLL 要从 MCLK 分频出 fs 的所有内部时钟（DAC 转换、滤波器），MCLK 必须是 fs 的高倍整数才能稳锁。256 是历史惯用值（兼容 384/512）。MCLK 没给或给错，codec PLL 锁不住，无声或变调。</details>

2. 为什么音频 codec 要分"控制面（I2C）+ 数据面（I2S）"？能不能只用 I2S？
<details><summary>看答案</summary>I2C 慢（100k/400k），适合偶发改寄存器（音量/使能/格式）；I2S 快（MHz 级 BCK），适合连续流 PCM。如果控制也走 I2S，每次改音量都要打断数据流，不现实。两套接口各司其职：I2C 当"遥控器"，I2S 当"传送带"。这是音频芯片的通用范式，不是 ES8311 独有。</details>

3. E08 里 stereo 双槽位为什么填同一份单声道样本？不填会怎样？
<details><summary>看答案</summary>ES8311 是单声道 DAC，但 I2S 配的是 stereo 模式（I2S_SLOT_MODE_STEREO），硬件按左右槽位取数。如果只填左槽位、右槽位留 0，codec 只在一半帧拿到数据，音量减半或失真；如果左右填不同值，codec 取哪个取决于内部路由。填同一份样本保证两槽位等价，codec 任取都对：这是"单声道内容走 stereo 通道"的标准做法。</details>

4. PA_EN 不在 ESP32 的 GPIO 上，而在哪？为什么这样设计？
<details><summary>看答案</summary>PA_EN 在 PCA9557 I2C 扩展器的 bit1（I2C 地址 0x19），不是 ESP32 GPIO。E08 main.c 第 81 行注释明说"PA_EN 是 PCA9557 bit1，不是 ESP32 GPIO1"。这样设计是因为 ESP32 的 GPIO 资源紧张（音频链路已占了 mclk/bclk/ws/dout 4 个），用 I2C 扩展器省 GPIO：代价是功放使能要走 I2C 总线，比直接 GPIO 慢，但功放开关不频繁，可接受。</details>

5. 耳返实验的延迟从哪里来？BLOCK_FRAMES=160 时往返延迟约多少？
<details><summary>看答案</summary>延迟来源：采集 DMA 缓冲（一块填满才能读出，BLOCK_FRAMES/fs）+ 播放 DMA 缓冲（一块填满才能放，BLOCK_FRAMES/fs）+ codec 内部数字滤波器延迟（几 ms）。直通处理约等于 0。BLOCK_FRAMES=160、fs=16000 时，单段 10ms，往返约 20ms 加几 ms codec 延迟，约 25ms：人耳能听见自己但不至于回声感（大于 150ms 才明显）。BLOCK 拉到 512（32ms）往返 64ms+，开始难受。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| I2S 四线协议 | 飞利浦 I2S 标准；与 [S12 SPI](../stm32/12-spi.md) 同源（同步移位） |
| 控制面 vs 数据面 | [P6 I2C/SPI 驱动](06-spi-i2c-driver.md) I2C 当遥控器；esp_codec_dev 封装 |
| ES8311 播放 | E08 工程 main.c；esp_codec_dev 接口 |
| ES7210 采集 | 立创 wiki 原理图；esp_codec_dev ADC 范式 |
| 全双工回环 | [F4 队列](../rtos/freertos/04-queue.md) 缓冲账；耳返延迟实测 |
| 通往小智 | Opus/AEC/KWS 软件层；[P8 Wi-Fi](08-wifi.md) 上传 |
| MCLK=256×fs | E08 main.c:95 `I2S_MCLK_MULTIPLE_256`、main.c:126 日志 |
| PA_EN=PCA9557 bit1 | E08 main.c:81 注释；I2C 地址 0x19 |

## 你做到了

- 板子在你代码下"能听会说"；
- P 篇收官：从 GPIO 到 Wi-Fi 到音频，立创 S3 的每一寸都被你点亮：综合项目（小智类终端）的门槛已经踏平。

带宽对完账：控制面 I2C 只在开工前把 codec 的家什摆好，声音本身一刻不停走 I2S。两条面各司其职，这声"滴"才算落了地；采集那一侧的麦克风，走的也是同一套分工。

<div class="achievement">
✅ P 篇收官。下一站：<a href="../lab/index.html">实验中心</a> 把散落各章的实验串成项目；或回 <a href="../rtos/index.html">RTOS 篇</a> 深化系统内功。
</div>

## 可独立运行的最小实验

[ES8311 提示音与旋律](../lab/e08-audio-play.md) 已提供独立工程、配置说明和完整源码。本章仍在建设中，最小实验不依赖本章其余内容；板上现象待实测。
