# 19 A set of real projects

> 中文：[19 项目实战合集](../19-项目实战合集.md)

> From a Bluetooth car to a FreeRTOS gateway: 10 projects, easy then harder. Each one gives you the requirements, the bill of materials, the approach, the key code, and a time estimate. Follow them and you can finish.

<p align="center">
  <img src="../../assets/boards/peripheral-wiring.svg" width="760" alt="Wiring overview for common parts: LED, button, OLED, sensors">
  <br><sub>▲ Figure: a wiring overview for the parts most projects start from (author-drawn vector, not a photograph)</sub>
</p>

<!-- video:ch19 -->
<p align="center">
  <video width="640" controls poster="../../assets/video/ch19-projects.png">
    <source src="../../assets/video/ch19-projects.mp4" type="video/mp4">
  </video>
  <br><sub>▲ Chinese voice-over, 2.4 min. Voice: Microsoft Edge neural voice zh-CN-XiaoxiaoNeural via edge-tts (library mostly LGPLv3; the voice model is an online Microsoft service, not an open model). Pictures are generated from this repo's SVGs, not photographs. Video: <a href="../../assets/video/ch19-projects.mp4">MP4</a> · subtitles: <a href="../../assets/video/ch19-projects.srt">SRT</a>. Rebuild with <code>python3 tools/gen_narrated.py --speak</code>.</sub>
</p>

**Narration script (Chinese, same text as the subtitles)**

1. 做项目最容易散的地方，是一个周末同时加上蓝牙、显示和存储。规矩只有一条：每一轮新增加的不确定，只允许有一个外设。坏了，你知道是谁。
2. 动手前用一句话写完完成标准。比如温度每分钟记一条，掉电不丢。没有这句话，你会一直调，不知道哪天算做完。失败怎样看出来，也要先写下来。
3. 不要从空白文件开始堆。先让仓库里对应的示例在你的板上跑起来，再加这一个项目需要的外设。示例和你的板子不一致时，先改时钟和引脚，别改算法。
4. 这一帧是仓库画的工程结构。应用、板级、驱动分开，后面你才敢换一颗芯片。所有代码堆在一个 main 里，项目做完你也不敢再打开它。
5. 温湿度记录仪先保证读数和时间是对的，掉电不丢，再去画曲线。曲线很好看，但是如果时间是错的，记录就没有意义。显示是最后一层糖。
6. 蓝牙小车先让两个轮子按你的命令转，再加遥控。自平衡是挑战题，不要当第一周的作业。底盘力学和编码器还没稳，算法只会放大抖动。
7. 多机 CAN 先做通两个节点，USB 采集先做通枚举和回显，再把采样挂上去。链路不通时叠协议，你无法判断是包错了还是采样错了。
8. 口诀：你的下一个项目，新增加的外设只有哪一个？说不出名字，就还没准备好开工。说得出，就先把别的欲望写进下一轮。
9. 做完不是指灯亮过一次。别人按你的说明能复现，你能说出还没做的部分。仓库里的十个题目，选一个做到这个程度，比十个都开了头有用。
10. 合上书，三问。你下一轮只允许新加哪一个外设？怎样算做完？板上的时钟和示例不一致时，你先改哪一部分？
<!-- /video:ch19 -->
## 📌 Learning goals

- [ ] Turn "an idea" into the engineering path: requirements, then hardware, then approach, then modules, then tests.
- [ ] Through 10 projects that build on each other, use GPIO, UART, I2C, SPI, ADC, DMA, TIM, and an RTOS in one place.
- [ ] For each project, know the minimum version that actually runs. Get that working, then iterate.
- [ ] Know the difficulty, the time, and where each project can grow, so you can choose one.

> Difficulty and time are **one person who already knows C, looking things up in the manual as they go**. Use them to plan, not as a promise. Every project should start as a minimum usable version (an MVP).

## 1. Bluetooth car (★★ beginner)

**Requirements**: a phone drives the car forward, back, left, right, and stop over Bluetooth, and the speed is adjustable.

| Item | Contents |
| --- | --- |
| Bill of materials | BluePill + HC-05 Bluetooth module + L298N motor driver + 2 or 4 geared DC motors + 18650 battery + chassis |
| Key peripherals | USART1 (Bluetooth), TIM3/TIM4 (PWM speed), GPIO (direction) |
| Time | 2~4 days |
| Difficulty | ★★ |

**Approach**: the phone app sends a one-character command (`F`/`B`/`L`/`R`/`S`). A UART interrupt, or the idle-line interrupt, receives the byte. You parse it and set motor direction and PWM duty. On the `L298N`, `IN1`/`IN2` set direction and `ENA` takes the PWM for speed.

**Key code**:

```c
/* Parse a Bluetooth command and drive the motors (F103, TIM3 CH1/CH2 PWM) */
void Car_HandleCmd(char c)
{
    switch (c)
    {
    case 'F': SetMotor(1, 60); SetMotor(2, 60); break;   /* forward 60% */
    case 'B': SetMotor(1, -60); SetMotor(2, -60); break; /* reverse */
    case 'L': SetMotor(1, 0); SetMotor(2, 60); break;    /* turn left */
    case 'R': SetMotor(1, 60); SetMotor(2, 0); break;    /* turn right */
    case 'S': SetMotor(1, 0); SetMotor(2, 0); break;     /* stop */
    default: break;
    }
}

/* duty: -100~100, the sign is direction */
static void SetMotor(uint8_t id, int8_t duty)
{
    uint32_t pwm = (uint32_t)((duty < 0 ? -duty : duty) * 999 / 100); /* 0~999 */
    if (id == 1) {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_0, duty >= 0 ? GPIO_PIN_SET : GPIO_PIN_RESET);
        __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_1, pwm);
    } else {
        HAL_GPIO_WritePin(GPIOA, GPIO_PIN_1, duty >= 0 ? GPIO_PIN_SET : GPIO_PIN_RESET);
        __HAL_TIM_SET_COMPARE(&htim3, TIM_CHANNEL_2, pwm);
    }
}
```

**Where it can grow**: ultrasonic obstacle avoidance, encoders for distance or a closed loop, an OLED that shows speed, or a PS2 / 2.4 GHz remote instead of Bluetooth.

## 2. Temperature and humidity logger (★★ beginner)

**Requirements**: sample temperature and humidity on a schedule, show them, store the history, and export it over the serial port.

| Item | Contents |
| --- | --- |
| Bill of materials | BluePill + DHT11/DHT22 or SHT30 + SSD1306 OLED + W25Q64 Flash + RTC crystal + coin cell |
| Key peripherals | 1-Wire or I2C (sensor), I2C (OLED), SPI (Flash), RTC |
| Time | 3~5 days |
| Difficulty | ★★ |

**Approach**: the RTC wakes the chip on a period (see [chapter 11](11-rtc-watchdog.md)). Read the sensor, draw it on the OLED, append it to a circular log in the W25Q64, and export CSV when a UART command arrives. The SHT30 is I2C, and it is more accurate and more stable than a DHT11.

**Key code**:

```c
/* Log one record every 5 minutes: RTC timestamp + temperature + humidity, into a circular Flash region */
typedef struct __attribute__((packed)) {
    uint32_t ts;        /* Unix timestamp */
    int16_t  temp_x10;  /* temperature ×10, e.g. 253 = 25.3℃ */
    uint16_t humi_x10;  /* humidity ×10 */
} Record_t;

void Log_Append(const Record_t *r)
{
    static uint32_t wr = LOG_BASE;               /* current write pointer */
    if (wr + sizeof(Record_t) > LOG_END) {
        wr = LOG_BASE;                           /* wrap around (simple wear leveling) */
        Flash_EraseSector(LOG_BASE);
    }
    Flash_Write(wr, (const uint8_t *)r, sizeof(Record_t));
    wr += sizeof(Record_t);
}
```

**Where it can grow**: an SD card for more data, LoRa or NB-IoT up to a cloud, or a drop into Stop for low power ([chapter 16](16-low-power.md)).

## 3. DMA + ADC mini oscilloscope (★★★ intermediate)

**Requirements**: capture one channel from 0 to 3.3 V, draw a live waveform, and show peak-to-peak and frequency.

| Item | Contents |
| --- | --- |
| Bill of materials | Nucleo-F411RE or an F103 + OLED or SPI TFT + the signal you want to measure |
| Key peripherals | ADC + DMA (circular), TIM (trigger), SPI (display) |
| Time | 1~2 weeks |
| Difficulty | ★★★ |

**Approach**: a timer triggers the ADC at even intervals. DMA copies samples into a buffer in a circle. In the half-transfer and transfer-complete interrupts, draw the half that is already full. The sample rate is the timer trigger frequency, so the time base is a timer setting.

**Key code**:

```c
#define ADC_BUF_LEN 512
static uint16_t adc_buf[ADC_BUF_LEN];

/* DMA circular + half-transfer: draw the back half while the front half fills, for a seamless refresh */
void HAL_ADC_ConvHalfCpltCallback(ADC_HandleTypeDef *hadc)
{
    Scope_Draw(&adc_buf[0], ADC_BUF_LEN / 2);
}
void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *hadc)
{
    Scope_Draw(&adc_buf[ADC_BUF_LEN / 2], ADC_BUF_LEN / 2);
}

/* Voltage conversion: V = code × Vref / 4095 (12-bit ADC) */
static float Code2Volt(uint16_t code)
{
    return (float)code * 3.3f / 4095.0f;
}
```

**Where it can grow**: a trigger level and edge, an FFT for the spectrum, two channels to compare, or a DWT cycle count of the refresh rate.

## 4. USB data-acquisition card (★★★ intermediate)

**Requirements**: stream multi-channel ADC data to a PC over USB (CDC, or a vendor bulk endpoint) and plot it on the host.

| Item | Contents |
| --- | --- |
| Bill of materials | F103 or F411 (with USB) + sensors or a signal source |
| Key peripherals | ADC + DMA + USB device (CDC, or a vendor-specific class) |
| Time | 1~2 weeks |
| Difficulty | ★★★ |

**Approach**: ADC plus DMA captures one frame. Pack it (header, sequence number, CRC) and send it with `CDC_Transmit_FS`. For more speed, a vendor-specific class with a bulk endpoint skips the CDC overhead. The host is Python (`pyserial` or `pyusb`): parse the frames and plot them live.

**Key code**:

```c
/* One frame: header + sequence + N samples + checksum */
#define FRAME_N 64
static void Upload_Frame(uint16_t *samples, uint16_t seq)
{
    uint8_t frame[4 + FRAME_N * 2 + 1];
    frame[0] = 0xAA; frame[1] = 0x55;
    frame[2] = (uint8_t)(seq >> 8);
    frame[3] = (uint8_t)(seq & 0xFF);
    for (int i = 0; i < FRAME_N; i++) {
        frame[4 + i * 2]     = (uint8_t)(samples[i] & 0xFF);
        frame[4 + i * 2 + 1] = (uint8_t)(samples[i] >> 8);
    }
    frame[4 + FRAME_N * 2] = Checksum8(frame, 4 + FRAME_N * 2);
    CDC_Transmit_FS(frame, sizeof(frame));   /* see chapter 14 */
}
```

**Where it can grow**: timestamps and a trigger, saving the stream to disk, synchronized extra channels, or a live FFT on the host.

## 5. Remote IAP update (★★★ intermediate)

**Requirements**: after the device leaves the factory, it receives new firmware over UART, CAN, or a network and updates itself. A failed update rolls back. The board does not become a brick.

| Item | Contents |
| --- | --- |
| Bill of materials | BluePill (or any part with Flash) + a host or a gateway |
| Key peripherals | USART or CAN + internal Flash |
| Time | 1~2 weeks |
| Difficulty | ★★★ |

**Approach**: split Flash into a bootloader, a parameter block, APP_A, and APP_B (see [chapter 12](12-flash-iap.md)). During an update, write the new image into the idle slot, check the CRC, write the "boot flag", and reset. The bootloader jumps to the slot the flag names. If that image is bad, it falls back.

**Key code**:

```c
/* Parameter block: the slot that is valid now, and any upgrade request */
typedef struct {
    uint32_t magic;       /* 0x5A5A0001 means valid */
    uint32_t active;      /* 0 = slot A, 1 = slot B */
    uint32_t pending;     /* the slot requested for the switch */
    uint32_t app_size[2];
    uint32_t app_crc[2];
} BootParam_t;

/* Bootloader picks the slot to jump to */
uint32_t Boot_SelectApp(void)
{
    BootParam_t p;
    Flash_Read(PARAM_ADDR, (uint8_t *)&p, sizeof(p));
    if (p.magic != 0x5A5A0001) return APP_A_ADDR;
    if (p.pending != 0xFFFFFFFF && Crc32(p.pending) == p.app_crc[p.pending]) {
        p.active = p.pending; p.pending = 0xFFFFFFFF;   /* the upgrade takes effect */
        Flash_EraseParam(); Flash_WriteParam(&p);
    }
    return (p.active == 0) ? APP_A_ADDR : APP_B_ADDR;
}
```

**Where it can grow**: YMODEM or your own packet format, a signature check, CAN for updating many nodes at once, or resume after a dropped transfer.

## 6. WS2812 LED-strip controller (★★ intermediate)

**Requirements**: drive a WS2812/WS2812B strip with chase, breathe, and rainbow effects, and let brightness and length be adjusted.

| Item | Contents |
| --- | --- |
| Bill of materials | BluePill + WS2812 strip + a 5 V supply sized for the strip current |
| Key peripherals | TIM + DMA (precise 800 kHz timing), or SPI |
| Time | 3~5 days |
| Difficulty | ★★ |

**Approach**: a WS2812 uses a **single-wire return-to-zero code** (`T0H=0.4µs`, `T1H=0.8µs`, period 1.25µs) to send 24-bit GRB. **TIM+DMA** produces that waveform: encode each bit as two compare values, and let DMA stream them out.

**Key code**:

```c
/* WS2812 timing from TIM2 CH1 PWM + DMA (simplified sketch) */
#define LED_NUM     60
#define RESET_SLOTS 50                      /* number of low slots for reset */

static uint16_t pwm_buf[LED_NUM * 24 * 2 + RESET_SLOTS];

/* Encode GRB into pwm_buf: 1 bit = a high compare value plus a low one */
void WS2812_Encode(const uint8_t *grb, uint16_t n)
{
    uint32_t idx = 0;
    for (uint16_t i = 0; i < n * 3; i++) {
        for (int b = 7; b >= 0; b--) {
            uint8_t bit = (grb[i] >> b) & 1;
            pwm_buf[idx++] = bit ? T1H : T0H;   /* high-time width */
            pwm_buf[idx++] = bit ? (PERIOD - T1H) : (PERIOD - T0H);
        }
    }
    for (int i = 0; i < RESET_SLOTS; i++) pwm_buf[idx++] = 0;  /* reset */
    HAL_TIM_PWM_Start_DMA(&htim2, TIM_CHANNEL_1, (uint32_t *)pwm_buf, idx);
}
```

**Where it can grow**: sound-reactive patterns, infrared or Bluetooth control, several strips in a chain, or SPI+DMA to use less RAM.

## 7. A simple logic analyzer (★★★★ a challenge)

**Requirements**: sample 4 to 8 digital lines, upload them over USB, and decode UART, I2C, and SPI on the host.

| Item | Contents |
| --- | --- |
| Bill of materials | F411 or F407 (high clock) + USB, with series protection resistors on the inputs |
| Key peripherals | TIM + DMA (sample GPIO on a timer), USB upload, a ring buffer |
| Time | 2~4 weeks |
| Difficulty | ★★★★ |

**Approach**: a timer fires quickly. In the ISR, read a whole GPIO port's IDR as one byte into a ring buffer. When the trigger condition is met, stop, then bulk-upload over USB. The host decodes protocols and draws the traces (a small cousin of PulseView).

**Key code**:

```c
#define LA_DEPTH  (64 * 1024)
static uint8_t la_buf[LA_DEPTH];
static volatile uint32_t la_wr = 0;
static volatile uint8_t  la_run = 0;

/* TIM period interrupt: sample 8 lines at once (the whole port) */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (!la_run) return;
    la_buf[la_wr++ & (LA_DEPTH - 1)] = (uint8_t)(GPIOC->IDR & 0xFF);
}

/* After stop, upload in chunks over USB (see chapter 14) */
void LA_Upload(void)
{
    for (uint32_t off = 0; off < LA_DEPTH; off += 512)
        CDC_Transmit_FS(&la_buf[off], 512);
}
```

**Where it can grow**: an adjustable sample rate and trigger, an analog channel, protocol-decoder plugins, or double buffering for a higher rate.


## 8. A multi-node CAN network (★★★★ a challenge)

**Requirements**: three or more nodes on one CAN bus. The master polls. The slaves report sensor data. You need an ID plan and error handling.

| Item | Contents |
| --- | --- |
| Bill of materials | 3× BluePill + 3× TJA1050/SN65HVD230 + twisted pair + 2×120Ω termination resistors |
| Key peripherals | CAN1, USART (debug) |
| Time | 1~2 weeks |
| Difficulty | ★★★★ |

**Approach**: plan the ID space (for example `0x100~0x1FF` for slave reports and `0x200` for a master broadcast). Split traffic with filters (see [chapter 13](13-can.md)), and use the same sample point on every node. Add a heartbeat and a way to notice a node that has gone quiet.

**Key code**:

```c
/* ID plan: low 4 bits = node number, high 7 bits = function code */
#define ID_FUNC_STATUS 0x100u
#define ID_FUNC_CMD    0x200u

#define MAKE_ID(func, node)  ((uint16_t)(((func) & 0x7F0u) | ((node) & 0x0Fu)))
#define GET_NODE(id)         ((id) & 0x0Fu)

void Node_Report(uint8_t node, int16_t temp_x10, uint16_t humi_x10)
{
    uint8_t data[4];
    data[0] = (uint8_t)(temp_x10 >> 8);
    data[1] = (uint8_t)(temp_x10 & 0xFF);
    data[2] = (uint8_t)(humi_x10 >> 8);
    data[3] = (uint8_t)(humi_x10 & 0xFF);
    CAN_Send(MAKE_ID(ID_FUNC_STATUS, node), data, 4);   /* see chapter 13 */
}
```

**Where it can grow**: CANopen, a bootloader update over the bus, or a gateway to Ethernet or 4G.

## 9. A self-balancing car (★★★★ a challenge)

**Requirements**: a two-wheel self-balancing car that stands up, recovers after a shove, and can drive and turn from a remote.

| Item | Contents |
| --- | --- |
| Bill of materials | F103 or F411 + MPU6050 (gyro and accelerometer) + TB6612 or L298N + motors with encoders + chassis + battery |
| Key peripherals | I2C (MPU6050), TIM (encoder and PWM), UART (remote), a control loop at a high rate |
| Time | 3~6 weeks |
| Difficulty | ★★★★ |

**Approach**: an attitude estimate (complementary filter or Kalman) gives the tilt angle. A **cascaded PID** follows: an outer angle loop, an inner rate loop, then an encoder speed loop on top. The output is PWM. The control period is fixed (for example 5 ms), in a timer interrupt or an RTOS task, so it stays real-time.

**Key code**:

```c
/* Upright-loop PID (angle error to PWM), period 5ms */
static float g_kp = 25.0f, g_kd = 0.8f;
static float target_angle = 0.0f;      /* target tilt 0° */

float Balance_Update(float angle, float gyro)
{
    float err = target_angle - angle;
    /* PD: P corrects tilt, D uses the gyro to damp oscillation */
    float out = g_kp * err - g_kd * gyro;
    return out;                        /* clamp, then send to the motors */
}

/* Fixed-period control loop: call this from the TIM interrupt */
void Control_Loop_5ms(void)
{
    float angle = IMU_GetAngle();      /* tilt after the complementary filter */
    float gyro  = IMU_GetGyroY();
    float pwm   = Balance_Update(angle, gyro);
    Motor_SetBoth((int16_t)Clamp(pwm, -1000, 1000));
}
```

**Where it can grow**: a Bluetooth remote, an OLED for tuning the gains, line following with a camera, or a Kalman filter in place of the complementary filter.

## 10. A FreeRTOS smart gateway (★★★★ a challenge)

**Requirements**: a multi-protocol gateway. It samples local sensors, draws an OLED, forwards over UART or CAN, and manages low power. Several tasks cooperate.

| Item | Contents |
| --- | --- |
| Bill of materials | F411 or F407 + sensors + OLED + CAN transceiver + USB-TTL |
| Key peripherals | several peripherals + FreeRTOS (tasks, queues, event groups, semaphores) |
| Time | 3~6 weeks |
| Difficulty | ★★★★ |

**Approach**: split the work into a sample task, a display task, a communications task, and a supervisor task. A **queue** carries data. An **event group** waits for several conditions at once. A **mutex** protects a shared peripheral (the I2C bus). The supervisor feeds the watchdog and schedules low power (Stop when the system is idle).

**Key code**:

```c
/* Sample task to queue to comm task; the event group syncs "sample done" */
static QueueHandle_t      g_data_q;
static EventGroupHandle_t g_evt;

#define EVT_OLED_READY  (1 << 0)

static void vSampleTask(void *arg)
{
    SensorData_t d;
    for (;;) {
        d.temp = Sensor_ReadTemp();
        xQueueSend(g_data_q, &d, portMAX_DELAY);      /* hand off to the comm task */
        xEventGroupSetBits(g_evt, EVT_OLED_READY);    /* notify the display task */
        vTaskDelay(pdMS_TO_TICKS(1000));              /* block for 1 s and yield the CPU */
    }
}

static void vCommTask(void *arg)
{
    SensorData_t d;
    for (;;) {
        if (xQueueReceive(g_data_q, &d, portMAX_DELAY) == pdTRUE) {
            Comm_SendFrame(&d);                       /* forward over UART or CAN */
        }
    }
}
```

**Where it can grow**: an MQTT or Modbus stack, OTA updates, task runtime stats (`vTaskGetRunTimeStats`), or saving data across power loss.

## 🧪 Hands-on labs (picking a project and moving it forward)

1. **Build the MVP first**: pick any project and do only the smallest version that runs (for the Bluetooth car, forward and stop are enough). You should see something happen within half a day to 1 day.
2. **Split it into modules**: break the project into 3 to 5 pieces you can test alone, and prove each one. Each module should run on its own.
3. **Add one harder feature**: take one direction from "where it can grow" (an OLED, for example) and put it on the MVP. The product should grow one step at a time.
4. **Write a short retrospective**: record the traps and the fixes (add them to [chapter 18](18-faq.md)). You should start a personal notebook of engineering lessons.

## 🔗 Related resources

- The technical detail is in [chapters 03 through 17](03-gpio-and-led.md) (GPIO, UART, I2C, SPI, ADC, DMA, TIM, RTC, Flash, CAN, USB, RTOS, low power, and debug): [03](03-gpio-and-led.md), [04](04-interrupts-nvic.md), [05](05-timer-pwm.md), [06](06-uart.md), [07](07-i2c.md), [08](08-spi.md), [09](09-adc-dac.md), [10](10-dma.md), [11](11-rtc-watchdog.md), [12](12-flash-iap.md), [13](13-can.md), [14](14-usb.md), [15](15-freertos.md), [16](16-low-power.md), [17](17-debug.md).
- Example projects: [`examples/`](../../examples/) (gpio-blink, uart-dma-idle, i2c-oled, adc-dma, rtc-alarm, freertos-task, iap-bootloader).
- Reference manuals: RM0008 / RM0090 (peripheral registers and buses).
- Related chapters: [chapter 12, IAP](12-flash-iap.md), [chapter 13, CAN](13-can.md), [chapter 14, USB](14-usb.md), [chapter 15, FreeRTOS](15-freertos.md).
- Figure: `../../assets/boards/peripheral-wiring.svg` (author-drawn vector).
