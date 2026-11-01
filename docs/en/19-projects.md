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
  <br><sub>▲ Chapter video with Chinese voice-over (2.4 min). <a href="../../assets/video/ch19-projects.mp4">MP4</a> · <a href="../../assets/video/ch19-projects.srt">subtitles</a></sub>
</p>

<details>
<summary>Narration script (Chinese, same text as the subtitles)</summary>

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

</details>
<!-- /video:ch19 -->

## Learning goals

Before this chapter: for the peripherals each project uses, read the matching chapters among 03–17 first (the "Which chapters first" table below says which project needs which chapters); the five debugging steps from chapter 18 come up throughout. For basics such as Ohm's law, hexadecimal, bit operations, C pointers, and `volatile`, see "Zero-background primer" in chapter 00.

- [ ] Before you start, write one sentence each for "what counts as done" and "how you can tell it is broken".
- [ ] Split a project into 3 to 5 modules you can verify on their own, and add only one new peripheral per round.
- [ ] Start from the matching example in the repository, get it running unchanged on your own board, then change it into what the project needs.
- [ ] Use `arm-none-eabi-size` to work out how much Flash and SRAM a program takes, and decide whether it fits in the C8's 64 KB and 20 KB.
- [ ] Spot where a piece of code does not suit the C8 (a buffer too large, a pin that does not exist, an image past the Flash map), and rewrite it so it does.
- [ ] Write a retrospective when a project is done, so someone else can reproduce it from your notes alone.

## How to build a project

**In one sentence: add only one new peripheral per round, and before you start, write down "what counts as done" and "how you can tell it is broken".**

### An analogy first

Nobody cooking a new dish for the first time pours ten seasonings into the pot at once. You cook the rice first, then add one thing at a time and taste after each. If it comes out too salty, you know it was the spoonful of salt you just added.

A project works the same way. Run the whole thing after each new peripheral, and when something breaks, the suspect is the one you just added. Wire up Bluetooth, a display, and storage in one weekend, and when it breaks the three are tangled together and you can hardly tell which one is at fault.

The analogy stops here: a salty dish can be watered down, but wrong wiring can burn out a chip or a module. Wiring and power-up give you no chance to taste first, so check the pin table and the supply voltage before you switch on.

### 1. From idea to acceptance: five steps

Fill in the table from the top, one row at a time, and finish a row before you move to the next. The right-hand column is how project 2 (the temperature and humidity logger) fills it in; change it for your own project.

| Step | What to write down | Example: the logger |
| --- | --- | --- |
| Requirement | A one-sentence done criterion, plus "how you can tell it is broken" | One temperature and humidity record every 5 minutes, kept through a power cut; a gap in the exported times means it is broken |
| Hardware | A parts list and a pin table, with the use of every pin | The SHT30 and the OLED share one I2C bus, the W25Q64 is on SPI, the coin cell goes to VBAT |
| Plan | Where the data comes from and where it goes | RTC alarm wakes the chip → read the sensor → write Flash → refresh the screen |
| Modules | 3 to 5 modules you can test on their own, each with its interface written down | `rtc_now()`, `sht30_read()`, `log_append()`, `oled_show()` |
| Test | One test per module, and a last test for the whole device | Pull the power, power up again, and the exported record count and times still join up |

Write the done criterion as a sentence you can check. "One record every 5 minutes, kept through a power cut" can be checked on the board; "a logger that works well" cannot.

After each round that works, keep a fallback point: save a copy of the whole project that builds and runs, or tag it if you use git. If the next round breaks something, going back is faster than hunting from scratch.

Write down what "done" means too: someone else can reproduce it from your notes, and you can name the parts that are not done yet. An LED that lit once does not count as done.

### 2. How to read each project

All ten projects follow the same layout. **Requirements** says what you are building; a small table lists the bill of materials, the key peripherals, the time, and the difficulty; **Approach** explains how the data flows and which numbers must come out right; **Key code** gives the part that is easiest to get wrong, followed by a walk-through; **Where it can grow** is left for the next round.

In the small table, read "Key peripherals" first: it decides which chapters you need. The "Time" row and the stars in the heading are rules of thumb, estimated for someone who knows C and reads the manual as they go. Use them to plan, not as a promise.

The code snippets are not complete projects:

- Clocks, pins, and peripheral initialization are generated by CubeMX (chapters 01 and 02).
- Handles in a snippet, such as `htim3` and `huart1`, are global variables that CubeMX generates in `main.c`. When you put a snippet in another file, first add a declaration such as `extern TIM_HandleTypeDef htim3;`.
- Functions such as `Flash_Write()` and `Scope_Draw()` are drivers you wrote in earlier chapters; use your own names.

The code is written for the STM32F103C8T6: 64 KB of Flash, 20 KB of SRAM, and the pins of the LQFP48 package ([DS5319](#source-ds5319-swd)). On another part, look up its capacity and pins in that part's own datasheet.

### 3. Which chapters first, and which example to start from

Read by row: "Read first" lists the chapters for the peripherals the project uses; the "Starting example" is under `examples/` in the repository, and you get it running unchanged on your board first; "Minimum viable version" is the done criterion for round one, and you reach it before you add anything else.

| Project | Read first | Starting example | Minimum viable version |
| --- | --- | --- | --- |
| 1 Bluetooth car | 05, 06 | timer-pwm, uart-dma-idle | Send `F` and `S` over the serial port; both wheels turn and stop |
| 2 Temperature and humidity logger | 07, 08, 11 | rtc-alarm, i2c-oled, spi-flash | The serial port prints one line of time and temperature every 5 minutes |
| 3 Mini oscilloscope | 05, 09, 10 | adc-dma | The serial port prints the maximum and minimum of one screen of samples |
| 4 USB data-acquisition card | 09, 10, 14 | usb-cdc, adc-dma | A serial terminal on the PC receives frames with consecutive sequence numbers |
| 5 Remote IAP update | 06, 12 | iap-bootloader | Send a blink application over the serial port; after reset it runs |
| 6 WS2812 strip | 05, 10 | timer-pwm | One LED lights in the color you chose |
| 7 Logic analyzer | 05, 10, 14 | usb-cdc | Capture a stretch of UART waveform and see the 0s and 1s on the PC |
| 8 Multi-node CAN | 13 | can-bxcan | Two nodes receive each other's frames |
| 9 Self-balancing car | 05, 07 | i2c-oled, timer-pwm | The serial port prints the tilt angle; while you hold the car, the wheels turn toward the side it leans |
| 10 FreeRTOS gateway | 15, 16 | freertos-task | Two tasks pass data through a queue, visible on the serial port |

## 1. Bluetooth car (★★ beginner)

**Requirements**: a phone drives the car forward, back, left, right, and stop over Bluetooth, and the speed is adjustable.

| Item | Contents |
| --- | --- |
| Bill of materials | BluePill + HC-05 Bluetooth module + L298N motor driver + 2 geared DC motors (with 4, wire the two on each side in parallel) + two 18650 cells in series + chassis |
| Key peripherals | USART1 (Bluetooth), TIM3 CH1/CH2 (PWM speed), GPIO (direction) |
| Time | 2~4 days |
| Difficulty | ★★ |

**Approach**: the phone app sends a one-character command (`F`/`B`/`L`/`R`/`S`). USART1 takes an interrupt for every byte it receives; you parse it and set each motor's direction and PWM duty.

Each motor on the L298N has two direction inputs: `IN1`/`IN2` drive motor A and `IN3`/`IN4` drive motor B; `ENA`/`ENB` take the PWM for speed. According to ST's L298 datasheet, with EN high, one input high and the other low turns the motor one way, and swapping them turns it the other way; both inputs equal brakes the motor fast; with EN low the motor coasts to a stop.

Wire it as in the table below. The first two columns are the BluePill side; the third is the silkscreen on the module.

| Signal | BluePill pin | Goes to | Notes |
| --- | --- | --- | --- |
| PWM A | PA6 (TIM3_CH1, pin 16) | ENA on the L298N | Remove the jumper on ENA first |
| PWM B | PA7 (TIM3_CH2, pin 17) | ENB on the L298N | Remove the jumper on ENB first |
| Direction A | PB12, PB13 | IN1, IN2 | Example setting; motor A is on the left |
| Direction B | PB14, PB15 | IN3, IN4 | Example setting; motor B is on the right |
| Bluetooth | PA9 (TX), PA10 (RX) | RXD, TXD on the HC-05 | Crossed over |

PA6 and PA7 are the default pins of TIM3's first two channels (DS5319 Rev 20 Table 5; with TIM3_REMAP = 00, CH1 is on PA6, see [RM0008 timers](#source-rm0008-tim)). On common L298N modules, ENA and ENB carry jumpers that tie them to 5 V, so the motors only run at full speed; remove them before you connect the PWM. In this project PB12–PB15 are plain outputs, and any other free pins will do, as long as you avoid pin 10, PA0: chapter 03's external LED is there, and it is also the WKUP and ADC input pin.

Three more things about power:

- The L298's motor supply must be at least 2.5 V above its input high level (the electrical characteristics table in ST's L298 datasheet). One 18650 gives only about 3.7 V, which is not enough, so use at least two in series.
- Connect the BluePill's GND to the L298N's GND, or the direction and PWM signals have no common reference.
- USART1's baud rate must match the HC-05's data baud rate. Many modules ship at 9600; check the module's documentation.

**Key code**:

```c
/* Parse Bluetooth commands and drive two motors (F103, PWM on TIM3 CH1/CH2, ARR = 999) */
#include "main.h"

extern TIM_HandleTypeDef  htim3;     /* generated by CubeMX in main.c */
extern UART_HandleTypeDef huart1;

/* Direction pins are an example setting: motor A on PB12/PB13, motor B on PB14/PB15. Not on pin 10, PA0 */
#define MOTOR_DIR_PORT  GPIOB
static const uint16_t MOTOR_DIR_PIN[2][2] = {
    { GPIO_PIN_12, GPIO_PIN_13 },    /* motor A: IN1, IN2 */
    { GPIO_PIN_14, GPIO_PIN_15 },    /* motor B: IN3, IN4 */
};
static const uint32_t MOTOR_PWM_CH[2] = { TIM_CHANNEL_1, TIM_CHANNEL_2 };

static uint8_t rx_byte;

/* id: 0 = motor A (left), 1 = motor B (right); duty: -100~100, the sign is the direction */
static void SetMotor(uint8_t id, int8_t duty)
{
    uint32_t mag = (uint32_t)(duty < 0 ? -duty : duty);
    if (mag > 100U) mag = 100U;
    HAL_GPIO_WritePin(MOTOR_DIR_PORT, MOTOR_DIR_PIN[id][0], duty > 0 ? GPIO_PIN_SET : GPIO_PIN_RESET);
    HAL_GPIO_WritePin(MOTOR_DIR_PORT, MOTOR_DIR_PIN[id][1], duty < 0 ? GPIO_PIN_SET : GPIO_PIN_RESET);
    __HAL_TIM_SET_COMPARE(&htim3, MOTOR_PWM_CH[id], mag * 999U / 100U);   /* 0~999 */
}

static void Car_HandleCmd(char c)
{
    switch (c) {
    case 'F': SetMotor(0, 60);  SetMotor(1, 60);  break;   /* forward at 60% */
    case 'B': SetMotor(0, -60); SetMotor(1, -60); break;   /* back */
    case 'L': SetMotor(0, 0);   SetMotor(1, 60);  break;   /* left: left wheel stops, right wheel turns */
    case 'R': SetMotor(0, 60);  SetMotor(1, 0);   break;   /* right */
    case 'S': SetMotor(0, 0);   SetMotor(1, 0);   break;   /* stop */
    default: break;
    }
}

void Car_Start(void)                 /* call once in main() after peripheral init */
{
    HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_1);
    HAL_TIM_PWM_Start(&htim3, TIM_CHANNEL_2);
    HAL_UART_Receive_IT(&huart1, &rx_byte, 1);
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
    if (huart == &huart1) {
        Car_HandleCmd((char)rx_byte);
        HAL_UART_Receive_IT(&huart1, &rx_byte, 1);   /* arm again for the next byte */
    }
}
```

A walk through it:

- `MOTOR_DIR_PIN` is a two-dimensional array with two direction pins per motor. Each motor on the L298N needs both inputs driven together; with only one connected and the other floating or tied, the motor can turn only one way.
- `SetMotor()` is defined before `Car_HandleCmd()`. C requires a declaration before use; in the reverse order GCC first complains about an implicit declaration and then reports `static declaration of 'SetMotor' follows non-static declaration`, and the build fails.
- With `duty` at 0 both direction pins are low and the compare value is 0, so EN stays low and the motor coasts to a stop.
- The compare value is `mag * 999 / 100`: ARR = 999 (example setting, chapter 05), so 60% duty is 599. PSC sets the PWM frequency; chapter 05's PSC = 71 with a 72 MHz timer clock gives 1 kHz ([RM0008 timers](#source-rm0008-tim)).
- The serial port receives 1 byte at a time with `HAL_UART_Receive_IT()`, handles it in the callback, and arms the next one. The callback runs in the interrupt and only writes a few registers here, so it is quick; for slow work, set a flag in the callback and leave the work to the main loop.

**Where it can grow**: ultrasonic obstacle avoidance, encoders for distance or a closed loop, an OLED that shows speed, or a PS2 / 2.4 GHz remote instead of Bluetooth.

## 2. Temperature and humidity logger (★★ beginner)

**Requirements**: sample temperature and humidity on a schedule, show them, store the history, and export it over the serial port.

| Item | Contents |
| --- | --- |
| Bill of materials | BluePill + DHT11/DHT22 or SHT30 + SSD1306 OLED + W25Q64 Flash + 32.768 kHz crystal + coin cell |
| Key peripherals | Single-wire timing or I2C (sensor), I2C (OLED), SPI (Flash), RTC |
| Time | 3~5 days |
| Difficulty | ★★ |

**Approach**: the RTC alarm wakes the chip on a schedule, you read one temperature and humidity pair, draw it on the OLED, and append it to a circular log in the W25Q64. A command on the serial port exports the log as CSV.

- The F1 RTC compares its alarm register with its counter, and the counter is usually set to count once per second (chapter 11). Each time the alarm fires, set it to "current count + 300", which gives one record every 5 minutes (example setting).
- The coin cell goes to VBAT (pin 1, [DS5319](#source-ds5319-swd)), so the RTC keeps running after the main supply is cut.
- The DHT11/DHT22 uses its maker's own single-wire timing, not the 1-Wire protocol of the DS18B20, so you decode it yourself with a GPIO and a timer, following its datasheet. The SHT30 is I2C and can share one bus with the OLED; their addresses do not clash. For the accuracy of either sensor, go by its own datasheet.
- The W25Q64's smallest erase unit is a 4 KB sector, and a page is 256 bytes (Winbond W25Q64 datasheet). Programming NOR Flash can only turn 1s into 0s; the only way back to 1 is to erase the whole sector.

**Key code**:

```c
/* One record every 5 minutes: RTC timestamp + temperature + humidity, into a circular area of the W25Q64 */
#define W25Q_SECTOR_SIZE  4096U          /* smallest W25Q64 erase unit: 4 KB */
#define LOG_BASE          0x000000U      /* start of the log; must be 4 KB aligned */
#define LOG_END           0x100000U      /* example setting: the first 1 MB holds the log */

typedef struct __attribute__((packed)) {
    uint32_t ts;        /* Unix timestamp; reads 0xFFFFFFFF after an erase */
    int16_t  temp_x10;  /* temperature ×10, e.g. 253 = 25.3 °C */
    uint16_t humi_x10;  /* humidity ×10 */
} Record_t;             /* 8 bytes: 4096 / 8 = 512 records fill one sector exactly */

static uint32_t wr = LOG_BASE;           /* where the next record goes */

void Log_Append(const Record_t *r)
{
    if (wr + sizeof(Record_t) > LOG_END) {
        wr = LOG_BASE;                       /* full circle: back to the start, over the oldest records */
    }
    if (wr % W25Q_SECTOR_SIZE == 0U) {
        Flash_EraseSector(wr);               /* erase each new sector as you enter it */
    }
    Flash_Write(wr, (const uint8_t *)r, sizeof(Record_t));
    wr += sizeof(Record_t);
}

/* Call once at power-up: find the record with the largest timestamp; the next one goes after it */
void Log_Recover(void)
{
    Record_t r;
    uint32_t newest = 0U;
    wr = LOG_BASE;
    for (uint32_t a = LOG_BASE; a < LOG_END; a += sizeof(Record_t)) {
        Flash_Read(a, (uint8_t *)&r, sizeof(r));
        if (r.ts != 0xFFFFFFFFU && r.ts >= newest) {
            newest = r.ts;
            wr = a + sizeof(Record_t);
        }
    }
}
```

A walk through it:

- Erase each new sector as you enter it. Erasing only the first sector when you wrap is not enough: from the second sector on, the places you write still hold last round's data, and writing NOR Flash over data that was not erased ANDs the old and new bits together, which ruins the record.
- A record is 8 bytes, and 256 and 4096 are both multiples of 8, so no record crosses a page or a sector. Keep that true if you change the record length.
- The write pointer `wr` lives in RAM and is lost at power-off. "Kept through a power cut" comes from `Log_Recover()`: at power-up it scans the log for the record with the largest timestamp. That assumes the RTC time only moves forward, so do not leave out the coin cell.
- 1 MB holds 1048576 / 8 = 131072 records; at one every 5 minutes that is about 455 days per lap.

**Where it can grow**: an SD card for more data, LoRa or NB-IoT up to a cloud platform, or Stop mode when idle to save power (chapter 16).

## 3. DMA + ADC mini oscilloscope (★★★ intermediate)

**Requirements**: capture one channel from 0 to 3.3 V, draw a live waveform on a screen, and show peak-to-peak and frequency.

| Item | Contents |
| --- | --- |
| Bill of materials | BluePill + OLED or SPI TFT + a signal to measure (start with PWM from another timer as the signal) |
| Key peripherals | ADC1 + DMA1 channel 1 (circular), TIM3 (trigger), I2C or SPI (screen) |
| Time | 1~2 weeks |
| Difficulty | ★★★ |

**Approach**: TIM3's update event triggers ADC1 through TRGO, so the sampling interval is TIM3's period. DMA1 channel 1 copies the conversions into a 512-point buffer in a circle. When DMA fills the first half it calls the half-transfer callback, and when it fills the second half it calls the transfer-complete callback. The callbacks only note which half is full; drawing happens in the main loop.

- Trigger: the external trigger of ADC1's regular channels can be TIM3_TRGO (EXTSEL = 100, RM0008 Rev 21 Table 67). In CubeMX, set TIM3's TRGO to the update event and turn off the ADC's continuous mode, so each trigger gives one conversion. ADC1's DMA request is only on DMA1 channel 1 (Table 78).
- Sample-rate ceiling: one conversion = sampling time + 12.5 ADC clock cycles ([RM0008 ADC](#source-rm0008-adc)). The ADC clock must not exceed 14 MHz (RM0008 Rev 21 section 11.1); with PCLK2 = 72 MHz, the fastest setting at or below 14 MHz is divide by 6, which gives 12 MHz (ADCPRE in section 7.3.2). The shortest sampling time of 1.5 cycles plus 12.5 cycles is 14 cycles, about 1.17 µs, and TIM3's trigger interval must be longer than that. The shorter the sampling time, the lower the source impedance has to be (chapter 09).
- Example setting: PSC = 0, ARR = 719, 72 MHz / 720 = 100 kHz, so half the buffer, 256 points, is 2.56 ms.
- The input must stay between 0 and 3.3 V. None of PA0–PA7 is an FT pin (DS5319 Rev 20 Table 5), so a signal outside that range needs a divider or an offset first. The example uses PA4, which is ADC12_IN4 ([DS5319 ADC](#source-ds5319-adc)).

**Key code**:

```c
#define ADC_BUF_LEN 512
static uint16_t adc_buf[ADC_BUF_LEN];
static uint16_t *volatile ready_half = NULL;    /* which half is full and waiting for the main loop */

extern ADC_HandleTypeDef hadc1;
extern TIM_HandleTypeDef htim3;

void Scope_Start(void)
{
    HAL_ADCEx_Calibration_Start(&hadc1);                       /* calibrate the F1 ADC after power-up (chapter 09) */
    HAL_ADC_Start_DMA(&hadc1, (uint32_t *)adc_buf, ADC_BUF_LEN);
    HAL_TIM_Base_Start(&htim3);                                /* the triggers start once the timer runs */
}

void HAL_ADC_ConvHalfCpltCallback(ADC_HandleTypeDef *hadc)
{
    (void)hadc;
    ready_half = &adc_buf[0];                    /* first half full; DMA is filling the second half */
}

void HAL_ADC_ConvCpltCallback(ADC_HandleTypeDef *hadc)
{
    (void)hadc;
    ready_half = &adc_buf[ADC_BUF_LEN / 2];      /* second half full; DMA goes back to the first half */
}

void Scope_Poll(void)                            /* call repeatedly from the main loop */
{
    uint16_t *p = ready_half;
    if (p != NULL) {
        ready_half = NULL;
        Scope_Draw(p, ADC_BUF_LEN / 2);          /* must finish before DMA comes back to this half */
    }
}

/* Voltage: V = code × Vref / 4096 (12-bit ADC). Code 2048 at a nominal 3.3 V is 1.65 V. A denominator of 4095 is off by one LSB at full scale. */
static float Code2Volt(uint16_t code)
{
    return (float)code * 3.3f / 4096.0f;
}
```

A walk through it:

- Each callback covers one half: the half-transfer callback means the first half is full and can be drawn; the transfer-complete callback means the second half is full and can be drawn.
- The callbacks run in the DMA interrupt and only record a pointer. Drawing a screen takes from a few milliseconds to tens of milliseconds, and doing it in the interrupt would hold off other interrupts. `ready_half` is a pointer passed between the interrupt and the main loop, and the pointer itself must be `volatile`, hence `uint16_t *volatile`.
- In CubeMX set the DMA to Circular, with Half Word on both the peripheral and the memory side to match the `uint16_t` buffer.
- The main loop must finish drawing before DMA comes back to that half, which is only 2.56 ms with the example setting. An I2C OLED frame is 1024 bytes, and at 400 kHz just moving the data takes 1024 × 9 / 400 kHz ≈ 23 ms, which does not fit. In that case stop after one screen of samples (`HAL_ADC_Stop_DMA()`), draw, then start again; on an oscilloscope this is called single-shot triggering.
- The denominator in `Code2Volt()` is 4096, the same reckoning as chapter 09. Code 2048 is 1.65 V; with 4095 as the denominator the error grows from 0 at code 0 to exactly one LSB (about 0.8 mV) at full scale.

**Where it can grow**: a trigger level and edge, an FFT for the spectrum, two channels to compare, or a DWT cycle count of the refresh rate (chapter 17).

## 4. USB data-acquisition card (★★★ intermediate)

**Requirements**: stream multi-channel ADC data to a PC over USB (CDC, or a vendor bulk endpoint) and plot it on the host.

| Item | Contents |
| --- | --- |
| Bill of materials | BluePill (its micro-USB goes to PA11/PA12) + sensors or a signal source |
| Key peripherals | ADC + DMA + USB Device (CDC, or a vendor-specific class) |
| Time | 1~2 weeks |
| Difficulty | ★★★ |

**Approach**: ADC plus DMA captures one frame, you pack it with a header, a sequence number and a checksum, and `CDC_Transmit_FS()` sends it out over USB. The host parses it in Python (`pyserial` or `pyusb`) and plots it live. The two USB pins are pin 32, PA11, and pin 33, PA12 ([DS5319 USB/CAN](#source-ds5319-usbcan)).

`CDC_Transmit_FS()` is asynchronous: it hands the buffer address to the USB stack and returns, and the USB interrupt sends the data out one packet at a time (chapter 14). So while a send is in progress the buffer must not be on the stack and must not be overwritten. Call it again before the last frame is out and it returns `USBD_BUSY`.

The code below is written for the USB_DEVICE middleware that CubeMX generates, where the send function is `CDC_Transmit_FS()` (chapter 14). The repository's `usb-cdc` example does not link ST's middleware: its `usb_cdc_write()` takes at most 64 bytes per call and copies them into its own 64-byte buffer before sending. If you start from that example, hand a 133-byte frame over in three calls yourself, 64, 64, and 5, waiting for each packet to finish before the next.

For more speed, check two things first: whether each piece you hand to USB is too short, and whether the host reads only a few bytes at a time. CDC data already travels over a bulk endpoint; a vendor-specific class removes the virtual serial-port driver on the host side, and the bulk transfers on the wire stay the same.

**Key code**:

```c
/* One frame: 2-byte header + 2-byte sequence number + 64 samples (2 bytes each) + 1-byte checksum */
#include "usbd_cdc_if.h"

#define FRAME_N    64
#define FRAME_LEN  (4 + FRAME_N * 2 + 1)        /* 4 + 128 + 1 = 133 */

static uint8_t frame[2][FRAME_LEN];             /* two buffers in turn: one on USB, the other taking new data */
static uint8_t fill = 0;                        /* which buffer this frame fills */

static uint8_t Checksum8(const uint8_t *p, uint32_t n)
{
    uint8_t s = 0;
    while (n--) s += *p++;
    return s;
}

/* Returns 1: this frame is handed to USB. Returns 0: the last frame is still going; call again later with the same samples */
int Upload_Frame(const uint16_t *samples, uint16_t seq)
{
    uint8_t *f = frame[fill];                   /* the other buffer may be sending; leave it alone */
    f[0] = 0xAA; f[1] = 0x55;
    f[2] = (uint8_t)(seq >> 8);
    f[3] = (uint8_t)(seq & 0xFF);
    for (int i = 0; i < FRAME_N; i++) {
        f[4 + i * 2]     = (uint8_t)(samples[i] & 0xFF);
        f[4 + i * 2 + 1] = (uint8_t)(samples[i] >> 8);
    }
    f[4 + FRAME_N * 2] = Checksum8(f, 4 + FRAME_N * 2);
    if (CDC_Transmit_FS(f, FRAME_LEN) != USBD_OK) return 0;   /* USBD_BUSY: the other buffer is not out yet */
    fill ^= 1U;                                 /* handed over; the next frame uses the other buffer */
    return 1;
}
```

A walk through it:

- A local array inside the function is the wrong place for the buffer: it lives on the stack, and once the function returns that stack space is reused by other functions while the USB interrupt is still reading from it, so the PC receives garbage. Hence two static buffers used in turn.
- When `CDC_Transmit_FS()` returns `USBD_OK`, the previous send has finished; otherwise it would have returned busy. Switching back to fill the other buffer is safe at that point.
- Do not drop the return value. `USBD_BUSY` means this frame did not go out; ignore it and frames vanish silently, and the host only sees gaps in the sequence numbers.
- A frame is 133 bytes and a full-speed bulk packet is at most 64 bytes, so the USB stack splits it into three packets, 64 + 64 + 5. `wMaxPacketSize` stays 64; do not write 133 there (chapter 14).
- The trailer is an 8-bit additive checksum, which catches only some errors; for more reliability, use a CRC.

**Where it can grow**: timestamps and a trigger, saving the stream to disk on the host, synchronized channels, a live FFT on the host, or a CRC in place of the checksum.

## 5. Remote IAP update (★★★ intermediate)

**Requirements**: after the device leaves the factory, it receives new firmware over UART, CAN, or a network and updates itself. If an update fails, it stays in the bootloader and waits for the next download, so the board does not become a brick. On the C8 it cannot fall back to the old version; the reason is below.

| Item | Contents |
| --- | --- |
| Bill of materials | BluePill (or any part with Flash) + a host PC or gateway |
| Key peripherals | USART or CAN + internal Flash |
| Time | 1~2 weeks |
| Difficulty | ★★★ |

**Approach**: on the C8, bring up the one application from chapter 12 first. The bootloader starts at `0x08000000` for 16 KB, the parameter block starts at `0x08004000` for 2 KB, and the application starts at `0x08004800` with length `0xB800`, ending before `0x08010000`. Chapter 12 has no second slot. A second image of the same `0xB800` is 110 KB and ends at `0x0801B800`. Cutting the 46 KB into two 23 KB images is a different design. Do not write it as "see chapter 12".

The parameter block holds four things: a valid marker, the application length, the application checksum, and an "update request". Whether a power cut is safe depends on the order you write them:

1. The application receives an update command, writes 0 to the "update request" word, and resets in software.
2. The bootloader sees the request and erases the parameter page first, which removes the valid marker; then it erases the application area and writes the new application.
3. Once the new application is written, the bootloader computes its checksum, and only if it matches does it write the length and checksum back to the parameter page, with the valid marker written last.

Whichever step the power fails in, the valid marker is absent, so at the next power-up the bootloader stays put and waits for a new download instead of jumping into half an application. The cost is that the old application is erased in step 2. To fall back to the old version after a failure you need a second slot; another 46 KB makes 110 KB, which does not fit in the C8's 64 KB.

**Key code**:

```c
/* These two parts are built into the bootloader and the application; put the macros and the struct in a header both share */
#include <stddef.h>
#include "stm32f1xx_hal.h"

#define PARAM_ADDR   0x08004000UL     /* start of the parameter block, 2 KB (chapter 12's map) */
#define APP_ADDR     0x08004800UL     /* the one and only application */
#define APP_MAX      0xB800UL         /* 46 KB: APP_ADDR + APP_MAX = 0x08010000 */
#define PARAM_MAGIC  0x5A5A0001UL     /* this chapter's own valid marker, not chapter 12's flag value */

typedef struct {
    uint32_t magic;           /* equals PARAM_MAGIC, or the fields below cannot be trusted */
    uint32_t app_size;        /* actual application size in bytes, at most APP_MAX */
    uint32_t app_sum;         /* 32-bit additive sum of the whole application */
    uint32_t update_request;  /* erased value 0xFFFFFFFF = no request; written as 0 = update requested */
} BootParam_t;

/* Same as checksum32() in examples/iap-bootloader: a byte-by-byte sum */
static uint32_t checksum32(const uint8_t *data, uint32_t len)
{
    uint32_t sum = 0U;
    while (len--) sum += *data++;
    return sum;
}

/* The bootloader asks this first at power-up: 1 = jump to the application, 0 = stay and wait for new firmware */
int Boot_AppIsValid(void)
{
    const BootParam_t *p = (const BootParam_t *)PARAM_ADDR;   /* internal Flash can be read directly by address */

    if (p->magic != PARAM_MAGIC)                     return 0;   /* empty, or power failed mid-update */
    if (p->update_request != 0xFFFFFFFFUL)           return 0;   /* the application asked for an update */
    if (p->app_size == 0U || p->app_size > APP_MAX)  return 0;   /* impossible length */
    return checksum32((const uint8_t *)APP_ADDR, p->app_size) == p->app_sum;
}

/* The application calls this after an update command: it writes one word and erases nothing */
void App_RequestUpdate(void)
{
    HAL_FLASH_Unlock();
    HAL_FLASH_Program(FLASH_TYPEPROGRAM_WORD,
                      PARAM_ADDR + offsetof(BootParam_t, update_request), 0U);
    HAL_FLASH_Lock();
    NVIC_SystemReset();                      /* the bootloader runs first after reset */
}
```

A walk through it:

- The parameter block and the application are both in internal Flash, so the CPU can read them by address like an array, with no driver call.
- The "update request" uses the erased value `0xFFFFFFFF` for "none", so the application only has to write it as 0. F1 Flash is programmed a half-word at a time, and before programming it checks that the location is erased; if not, it skips the write and sets PGERR. Writing 0x0000 is the one exception (PM0075 Rev 2 section 2.3.3). So this one word can be written without erasing the page first.
- `0x5A5A0001` is just a value this chapter chose; the bootloader and the application only need to agree on it. It is not chapter 12's flag value, and the two chapters' parameter formats must not be mixed.
- How to jump (check the stack pointer, disable interrupts, reset peripherals, stop SysTick, set VTOR and MSP) follows chapter 12 and is not repeated here.
- The checksum is the same byte-by-byte sum as `checksum32()` in `examples/iap-bootloader`; the example's comment also suggests CRC32 for production.

**Where it can grow**: YMODEM or your own packet format, a signature check, CAN for updating many nodes at once, or resume after a dropped transfer. Two slots and a fallback to the old version need a part with more Flash.

## 6. WS2812 LED-strip controller (★★ intermediate)

**Requirements**: drive a WS2812/WS2812B strip with chase, breathe, and rainbow effects, with adjustable brightness and number of lit LEDs.

| Item | Contents |
| --- | --- |
| Bill of materials | BluePill + WS2812 strip + 5 V supply (sized for the strip's current) + a 74HCT-family level-shifter chip |
| Key peripherals | TIM2 + DMA (precise 800 kHz timing), or SPI |
| Time | 3~5 days |
| Difficulty | ★★ |

**Approach**: a WS2812 uses a **single-wire return-to-zero code** to send 24-bit GRB data: every bit is high then low, and a short high is 0 while a long high is 1. The LED vendor's timing is `T0H=0.4µs`, `T1H=0.8µs`, and a 1.25µs bit period. These are the LED vendor's numbers, not RM0008; different datasheet revisions give different windows, so go by the revision you have.

**TIM2 + DMA** produces that waveform: encode each bit as one compare value, and let DMA send one to CCR1 every PWM period.

- Timer clock: TIM2 sits on APB1. When the APB1 prescaler is not 1, the timer clock is twice APB1 (RM0008 Rev 21 section 7.2); with a 72 MHz system clock APB1 = 36 MHz, so TIM2's timer clock is 72 MHz; with PSC = 0 the counter clock is 72 MHz too.
- One bit, 1.25 µs, is 90 counts, so ARR = 89. The high time of a 0, 0.4 µs, is about 29 counts; the high time of a 1, 0.8 µs, is about 58 counts.
- DMA: the TIM2_CH1 request is on DMA1 channel 5 (RM0008 Rev 21 Table 78). The direction is memory to peripheral, with half-word width on both sides to match the `uint16_t` buffer; use Normal mode, so it stops after one frame.
- Pin: TIM2_CH1's default pin is pin 10, PA0 (DS5319 Rev 20 Table 5). Chapter 03's external LED is on the same pin, so remove it for this project.
- Levels: a WS2812B powered from 5 V needs an input high of at least 0.7 × VDD = 3.5 V (WS2812B datasheet), which the BluePill's 3.3 V output does not reach. Put a 74HCT level shifter powered from 5 V in between.
- Current: as a rule of thumb one LED at full white draws about 60 mA, so 60 LEDs need a 3.6 A supply. Connect the strip's GND to the BluePill's GND.

**Key code**:

```c
/* WS2812 timing from TIM2 CH1 (PA0) PWM + DMA. PSC = 0, counter clock 72 MHz, ARR = 89 */
extern TIM_HandleTypeDef htim2;

#define LED_NUM      60U
#define WS_T0H       29U          /* 29 / 72 MHz ≈ 0.40 µs: sends a 0 */
#define WS_T1H       58U          /* 58 / 72 MHz ≈ 0.81 µs: sends a 1 */
#define RESET_SLOTS  240U         /* 240 × 1.25 µs = 300 µs low: end of frame */

static uint16_t pwm_buf[LED_NUM * 24U + RESET_SLOTS];   /* one compare value per bit */
static volatile uint8_t ws_busy = 0;

/* grb: 3 bytes per LED in the order G, R, B; n: how many LEDs this frame lights. Returns 0 once sending has started */
int WS2812_Show(const uint8_t *grb, uint16_t n)
{
    uint32_t idx = 0;
    if (ws_busy || n > LED_NUM) return -1;          /* last frame still going, or past the buffer */
    for (uint32_t i = 0; i < n * 3U; i++) {
        for (int b = 7; b >= 0; b--) {              /* most significant bit first */
            pwm_buf[idx++] = ((grb[i] >> b) & 1U) ? WS_T1H : WS_T0H;
        }
    }
    for (uint32_t i = 0; i < RESET_SLOTS; i++) {
        pwm_buf[idx++] = 0;                         /* compare value 0: low for the whole period */
    }
    ws_busy = 1;
    if (HAL_TIM_PWM_Start_DMA(&htim2, TIM_CHANNEL_1, (uint32_t *)pwm_buf, (uint16_t)idx) != HAL_OK) {
        ws_busy = 0;
        return -1;
    }
    return 0;
}

/* HAL calls this when DMA has sent the last compare value */
void HAL_TIM_PWM_PulseFinishedCallback(TIM_HandleTypeDef *htim)
{
    if (htim == &htim2) {
        HAL_TIM_PWM_Stop_DMA(&htim2, TIM_CHANNEL_1);
        ws_busy = 0;
    }
}
```

A walk through it:

- One bit needs only one compare value: PWM makes "high then low" by itself every period, and the compare value only sets how long the high lasts. Split a bit into two compare values, "high" and "low", and DMA sends two bits, so the LEDs receive garbage. The buffer is therefore `LED_NUM * 24` compare values plus the reset, 1680 half-words or 3360 bytes for 60 LEDs.
- The reset is 300 µs: older WS2812B datasheets give a reset low of more than 50 µs, newer revisions require more than 280 µs, and 300 µs meets both. The reset slots have one more use: when the callback stops the PWM, the last periods are low anyway, so cutting them off does not touch the data.
- `ws_busy` stops you from changing the buffer while the last frame is still going. When DMA finishes, the callback stops the PWM and then clears the flag.
- The compare values are half-words. `HAL_TIM_PWM_Start_DMA()` takes a `uint32_t *`, and the cast only matches the prototype; how many bytes each transfer moves is set by the DMA width settings.

**Where it can grow**: sound-reactive patterns, infrared or Bluetooth control, several strips on separate timer channels, or SPI + DMA to use less RAM.

## 7. A simple logic analyzer (★★★★ a challenge)

**Requirements**: sample 4 to 8 digital lines, upload them to a PC over USB, and decode UART, I2C, and SPI on the host.

| Item | Contents |
| --- | --- |
| Bill of materials | BluePill + USB, with series protection resistors on the inputs; for a deeper buffer and a higher sample rate, a part with more SRAM and a faster clock |
| Key peripherals | TIM2 (sample timing), GPIOA input, USB CDC upload, ring buffer |
| Time | 2~4 weeks |
| Difficulty | ★★★★ |

**Approach**: TIM2 takes an update interrupt at the sample rate; the interrupt reads the low 8 bits of GPIOA's input data register IDR as one byte into a ring buffer. When the trigger condition is met, sampling stops and the data goes up over USB in chunks. The host decodes the protocols and draws the traces (a small cousin of PulseView).

- The eight inputs are PA0–PA7 (pins 10–17). The C8 in LQFP48 has no PC0–PC7; port C brings out only PC13–PC15 (DS5319 Rev 20 Table 5), so code written for an F4 board that reads `GPIOC->IDR` sees no signal on this board.
- None of PA0–PA7 is an FT pin, so divide signals above 3.3 V or use a level-shifter chip. Put a resistor of a few hundred ohms in series with each line (rule of thumb) to limit the current if something is wired wrong.
- Buffer: the C8 has 20480 bytes of SRAM in all; the example setting uses an 8 KB sample buffer.
- Sample-rate ceiling: every sample costs an interrupt entry and exit plus HAL's dispatch. Measure the cycles spent in the interrupt with chapter 17's DWT and you know the ceiling. To go faster, let TIM2's update event trigger DMA directly: TIM2_UP is on DMA1 channel 2 (RM0008 Rev 21 Table 78); the peripheral side reads `GPIOA->IDR` as a word, because GPIO registers allow 32-bit access only (section 9.1); the memory side writes bytes, and DMA keeps only the low 8 bits (Table 76), which are exactly PA0–PA7, with no CPU involved.

**Key code**:

```c
/* The C8 has only 20480 bytes of SRAM; 64 * 1024 = 65536 does not fit. Start with 8 KB */
#include "usbd_cdc_if.h"

extern TIM_HandleTypeDef htim2;

#define LA_DEPTH  (8U * 1024U)              /* must be a power of 2 so & can wrap it below */
static uint8_t la_buf[LA_DEPTH];
static volatile uint32_t la_wr = 0;
static volatile uint8_t  la_run = 0;

/* TIM2 update interrupt: read the eight lines PA0–PA7 at once */
void HAL_TIM_PeriodElapsedCallback(TIM_HandleTypeDef *htim)
{
    if (htim != &htim2 || !la_run) return;
    la_buf[la_wr++ & (LA_DEPTH - 1U)] = (uint8_t)(GPIOA->IDR & 0xFFU);
}

/* After sampling stops, upload in chunks over USB CDC (chapter 14) */
void LA_Upload(void)
{
    for (uint32_t off = 0; off < LA_DEPTH; off += 512U) {
        while (CDC_Transmit_FS(&la_buf[off], 512U) == USBD_BUSY) {
            /* the last chunk is not out yet; wait for it */
        }
    }
}
```

A walk through it:

- `LA_DEPTH` must be a power of 2. `la_wr & (LA_DEPTH - 1)` equals the remainder modulo 8192, so the write pointer keeps counting up and the index wraps by itself.
- After a wrap, the oldest sample is at `la_wr & (LA_DEPTH - 1)`, and the host must start assembling the waveform there.
- Every timer's update interrupt comes into this one callback, so check `htim` first. In a bare-metal project HAL's timebase is SysTick and this callback is yours; when CubeMX moves the timebase to a TIM (common with FreeRTOS, chapter 15), `main.c` already has a callback of the same name, so merge these two lines into it rather than defining a second one.
- During the upload, wait for each chunk until `CDC_Transmit_FS()` stops returning `USBD_BUSY` before handing over the next. After the last chunk, wait for it to finish too before you restart sampling, or the buffer is overwritten while it is being sent. If the serial port on the PC is not open, USB cannot send and this loop waits forever; a real version needs a timeout. If you start from the repository's `usb-cdc` example, replace `CDC_Transmit_FS()` with `usb_cdc_write()` and make each chunk 64 bytes; a return of -1 means the last packet is not out yet or enumeration is not done, so wait a moment and try again.

**Where it can grow**: an adjustable sample rate and trigger, an analog channel, protocol-decoder plugins, or DMA sampling for a higher rate.

## 8. A multi-node CAN network (★★★★ a challenge)

**Requirements**: three or more nodes on one CAN bus. The master polls, the slaves report sensor data, and there is an ID plan and error handling.

| Item | Contents |
| --- | --- |
| Bill of materials | 3× BluePill + 3× TJA1050 or SN65HVD230 + twisted pair + 2× 120 Ω termination resistors |
| Key peripherals | CAN1 (PB8/PB9), USART (debug) |
| Time | 1~2 weeks |
| Difficulty | ★★★★ |

**Approach**: keep the same reckoning as chapter 13 and `examples/can-bxcan`: 500 kbit/s, that is, the 36 MHz APB1 through a prescaler of 9, with 1 + 5 + 2 = 8 time quanta per bit and the sample point at 75%; working pins PB8/PB9; one 120 Ω resistor at each end of the bus. Every node uses the same bit timing, so the sample points agree.

- Pins: putting CAN on PB8/PB9 means setting the two CAN_REMAP bits in AFIO_MAPR to 10 (RM0008 Rev 21 section 9.4.2; 01 is a reserved value). If you start from the example, look at these two bits with the debugger first.
- Transceivers: the TJA1050 needs a 5 V supply and the SN65HVD230 runs from 3.3 V (go by each datasheet). With a TJA1050, its RXD output can swing close to 5 V, and that pin goes to PB8; PB8 is an FT pin (DS5319 Rev 20 Table 5) and can take it.
- ID plan: a standard ID has 11 bits; as an example setting the low 4 bits hold the node number and the high 7 bits the function code; slave reports use the `0x100` range and master commands the `0x200` range. In arbitration the frame with the smaller ID wins (RM0008 Rev 21 section 24.7.1, chapter 13), so the more urgent a frame, the smaller its ID.
- Filters split the traffic: each node receives only the commands addressed to it, and the master receives only the reports it cares about (chapter 13).
- Heartbeat and lost nodes: every slave sends one status frame per second, and the master marks a node lost after 3 seconds (example setting) without one.
- Debugging with a single node: nobody sends the ACK, so the frame never gets out. The example has automatic retransmission on, so the sender retries forever; once its transmit error counter passes 127 it is error passive, and under the CAN specification's fault-confinement rules an ACK error alone no longer raises the counter, so the node stays error passive and does not go bus-off (thresholds in RM0008 Rev 21 section 24.7.6). Use at least two nodes, or loopback mode first.

**Key code**:

```c
/* ID plan (example setting): low 4 bits = node number, high 7 bits = function code */
#define ID_FUNC_STATUS 0x100u
#define ID_FUNC_CMD    0x200u

#define MAKE_ID(func, node)  ((uint16_t)(((func) & 0x7F0u) | ((node) & 0x0Fu)))
#define GET_NODE(id)         ((id) & 0x0Fu)

void CAN_Send(uint16_t std_id, uint8_t *data, uint8_t len);   /* written in chapter 13 */

void Node_Report(uint8_t node, int16_t temp_x10, uint16_t humi_x10)
{
    uint8_t data[4];
    data[0] = (uint8_t)(temp_x10 >> 8);
    data[1] = (uint8_t)(temp_x10 & 0xFF);
    data[2] = (uint8_t)(humi_x10 >> 8);
    data[3] = (uint8_t)(humi_x10 & 0xFF);
    CAN_Send(MAKE_ID(ID_FUNC_STATUS, node), data, 4);
}

/* Master: note the time of each node's report; 3 s of silence means the node is lost */
static uint32_t last_seen[16];

void Master_OnStatus(uint16_t std_id)              /* call from the CAN receive callback */
{
    last_seen[GET_NODE(std_id)] = HAL_GetTick();
}

int Master_NodeAlive(uint8_t node)
{
    return (HAL_GetTick() - last_seen[node & 0x0Fu]) < 3000U;
}
```

A walk through it:

- `MAKE_ID()` joins the function code and the node number into an 11-bit standard ID: `0x7F0` keeps bits 4–10 and `0x0F` keeps bits 0–3. Node 3's status frame is `0x103`.
- 4 node bits allow at most 16 nodes; for more, split the bits between function code and node number differently.
- `HAL_GetTick() - last_seen[]` uses unsigned subtraction, so the difference stays right after the millisecond count wraps.

**Where it can grow**: CANopen, firmware updates for each node over the bus, or a gateway to Ethernet or 4G.

## 9. A self-balancing car (★★★★ a challenge)

**Requirements**: a two-wheel self-balancing car that stands up, recovers after a shove, and can drive and turn from a remote.

| Item | Contents |
| --- | --- |
| Bill of materials | BluePill + MPU6050 (gyro and accelerometer) + TB6612 or L298N + motors with encoders + chassis + battery |
| Key peripherals | I2C (MPU6050), TIM (encoder and PWM), UART (remote), a control loop with a fixed period |
| Time | 3~6 weeks |
| Difficulty | ★★★★ |

**Approach**: an attitude estimate (complementary filter or Kalman filter) turns acceleration and angular rate into a tilt angle, and the control loop turns the tilt angle into PWM. A common arrangement adds the outputs of two loops:

- Upright loop (PD): the P term corrects the tilt error, and the D term uses the gyro's angular rate directly to damp oscillation. The code below is this loop.
- Speed loop (PI): slowly corrects with the speed measured by the encoders, so the car does not run off faster and faster in one direction.
- The two outputs are added and sent to the motors. Some builds instead feed the speed loop's output in as the upright loop's target angle; only that arrangement is called a cascade.

The control period is fixed, 5 ms as an example setting. The 5 ms timer interrupt only sets a flag; reading the MPU6050, computing, and writing the PWM happen in the main loop, or in an RTOS task timed with `vTaskDelayUntil` (chapter 15). The reason is that HAL's blocking I2C reads time out using `HAL_GetTick()`: if the timer interrupt's priority is not lower than SysTick's, SysTick cannot preempt it, the tick does not advance inside that interrupt, and a stuck bus waits forever.

**Key code**:

```c
/* Upright loop, PD (tilt error to PWM), period 5 ms. The gains are an example setting; retune them for your car */
static float g_kp = 25.0f, g_kd = 0.8f;
static float target_angle = 0.0f;      /* target tilt 0° */
static volatile uint8_t tick_5ms = 0;

static float Clamp(float x, float lo, float hi)
{
    return (x < lo) ? lo : ((x > hi) ? hi : x);
}

float Balance_Update(float angle, float gyro)
{
    float err = target_angle - angle;
    /* P corrects the tilt; D damps oscillation with the gyro's angular rate. The sign of gyro must match angle */
    return g_kp * err - g_kd * gyro;
}

/* The 5 ms timer interrupt does only this */
void Control_Tick_ISR(void)
{
    tick_5ms = 1;
}

/* Call repeatedly from the main loop */
void Control_Loop(void)
{
    if (!tick_5ms) return;
    tick_5ms = 0;
    float angle = IMU_GetAngle();      /* tilt after the complementary filter */
    float gyro  = IMU_GetGyroY();      /* angular rate about the wheel axle */
    float pwm   = Balance_Update(angle, gyro);
    Motor_SetBoth((int16_t)Clamp(pwm, -1000.0f, 1000.0f));
}
```

A walk through it:

- The code has only the upright loop. A car with only the upright loop stands for a while but runs off faster and faster in one direction; the speed loop pulls it back.
- The gains and the 5 ms are example settings, and a different motor, wheel, or battery means retuning. A common way to tune (a rule of thumb) is P alone first, raised until the car starts rocking back and forth, then D to calm the rocking.
- Get two signs right first. The gyro and the tilt must agree: when the car falls forward and the tilt grows, the gyro reading should also be positive; if not, negate `gyro`, or the D term works against you. The MPU6050's mounting decides this. The motor direction must match the tilt: falling forward, the wheels must drive forward to catch up. The motor wiring decides this.
- `Clamp()` limits the output to ±1000, since values beyond full-scale PWM mean nothing. `IMU_GetAngle()`, `IMU_GetGyroY()`, and `Motor_SetBoth()` are your own drivers.

**Where it can grow**: Bluetooth remote control, an OLED for tuning, line following with a camera, or a Kalman filter in place of the complementary filter.

## 10. A FreeRTOS smart gateway (★★★★ a challenge)

**Requirements**: a multi-protocol gateway. It samples local sensors, draws an OLED, forwards over UART or CAN, and manages low power. Several tasks cooperate.

| Item | Contents |
| --- | --- |
| Bill of materials | BluePill (F103C8T6, one CAN) or F407 (two CAN) + sensors + OLED + CAN transceiver + USB-TTL |
| Key peripherals | I2C, USART, CAN + FreeRTOS (tasks, queues, event groups, mutexes) |
| Time | 3~6 weeks |
| Difficulty | ★★★★ |

Pick the part by CAN first: the F103C8 has one CAN interface (DS5319 Rev 20), the F407 has two (DS8626), and the F411 has no CAN controller at all (ST DS10314), so a transceiver on it would be useless. On the C8, remember also that USB and CAN share a dedicated 512-byte SRAM and cannot work at the same time (RM0008 Rev 21 sections 23.2 and 24.2). That is why the PC connection here goes through a USB-TTL serial adapter, not the C8's own USB.

**Approach**: split the work into a sample task, a display task, a communications task, and a supervisor task. A **queue** carries data, an **event group** waits for several conditions, and a **mutex** protects the shared I2C bus (the sensor and the OLED both sit on it). The supervisor feeds the watchdog and handles low power:

- Do not feed the watchdog unconditionally. Have each task set its own bit in an event group every round, and let the supervisor feed the independent watchdog only once all the bits are in; if any task hangs, the watchdog bites (chapter 11).
- Entering Stop when idle takes one more step. In Stop mode all clocks in the 1.8 V domain stop (RM0008 Rev 21 section 5.3.4), so SysTick stops and so does the FreeRTOS tick. FreeRTOS's built-in tickless implementation (`configUSE_TICKLESS_IDLE` set to 1) keeps time with SysTick and only enters sleep mode with WFI (the ARM_CM3 port in FreeRTOS V11.3.2). To use Stop, write the Stop entry and exit yourself: wake with an RTC alarm; after wake-up the system clock is HSI (same section), so reconfigure the PLL; then add back the ticks that were slept through (chapter 16).

**Key code**:

```c
/* Sample task -> queue -> communications task; an event group tells the display task "new data" */
#include "main.h"
#include "FreeRTOS.h"
#include "task.h"
#include "queue.h"
#include "event_groups.h"

typedef struct {
    int16_t temp_x10;                 /* temperature ×10 */
} SensorData_t;

static QueueHandle_t      g_data_q;
static EventGroupHandle_t g_evt;

#define EVT_OLED_READY  (1U << 0)

static void vSampleTask(void *arg)
{
    SensorData_t d;
    TickType_t last = xTaskGetTickCount();
    (void)arg;
    for (;;) {
        d.temp_x10 = Sensor_ReadTemp_x10();
        if (xQueueSend(g_data_q, &d, pdMS_TO_TICKS(100)) != pdPASS) {
            /* still full after 100 ms: the comms task is stuck; record it for the supervisor */
        }
        xEventGroupSetBits(g_evt, EVT_OLED_READY);    /* tell the display task */
        vTaskDelayUntil(&last, pdMS_TO_TICKS(1000));  /* one round every 1000 ms, not stretched by the work */
    }
}

static void vCommTask(void *arg)
{
    SensorData_t d;
    (void)arg;
    for (;;) {
        if (xQueueReceive(g_data_q, &d, portMAX_DELAY) == pdTRUE) {
            Comm_SendFrame(&d);                       /* forward over UART or CAN */
        }
    }
}

/* Call in main() after peripheral init; normally it does not return */
void Gateway_Start(void)
{
    g_data_q = xQueueCreate(8, sizeof(SensorData_t));
    g_evt    = xEventGroupCreate();
    if (g_data_q == NULL || g_evt == NULL) Error_Handler();        /* heap too small */
    if (xTaskCreate(vSampleTask, "sample", 256, NULL, 2, NULL) != pdPASS) Error_Handler();
    if (xTaskCreate(vCommTask,   "comm",   256, NULL, 3, NULL) != pdPASS) Error_Handler();
    vTaskStartScheduler();
}
```

A walk through it:

- The queue and the event group are created before the scheduler starts, and the return values are checked. They come from the FreeRTOS heap, which returns `NULL` when it runs out; send or receive on a `NULL` handle and the program stops at an assert or runs wild (chapter 15).
- `vTaskDelayUntil()` keeps sampling at one round every 1000 ms; `vTaskDelay(1000)` waits 1000 ms from the moment of the call, so the time spent reading the sensor adds on (chapter 15).
- The stack depth of 256 is in words, which is 1024 bytes (chapter 15). The queue length of 8 and both priorities are example settings.
- The communications task has a higher priority than the sample task, so as soon as data enters the queue the communications task wakes up and forwards it.
- The send uses a 100 ms timeout (example setting) rather than `portMAX_DELAY`. If the communications task hangs, the sample task keeps running and keeps reporting to the supervisor, so the problem can be noticed.

**Where it can grow**: an MQTT or Modbus stack, OTA updates, `vTaskGetRunTimeStats` to see each task's CPU share, or protection for data across a power cut.

## Hands-on labs (picking a project and moving it forward)

1. **Lab 1: Build the minimum viable version first.** Pick any project and do only its "Minimum viable version" cell from the "Which chapters first" table. For the Bluetooth car, do forward and stop only, sending characters from the PC through a USB-TTL adapter; wire in the Bluetooth module in round two.
   - Expected: within half a day to a day (rule of thumb) you see what that cell describes.
   - How to check: hold the done criterion you wrote before you started up against the board, word by word.
   - If it fails, check first: whether the starting example runs unchanged on your board; if it does not, work through the five steps in chapter 18, starting with reproduce and minimize.
2. **Lab 2: Connect one module at a time.** Split the project into 3 to 5 modules and write one test for each that runs on its own. For the logger: print the time on the serial port, print a reading, write and read back, show a fixed string on the OLED.
   - Expected: each module passes its own test before it joins the others.
   - How to check: keep a table of modules, and mark each cell "pass" or "fail" with the date.
   - If it fails, check first: only one module is new this round. Go back to the last fallback point, confirm the old parts still work, then look at the new one.
3. **Lab 3: Add one extension to the minimum viable version.** Pick one item from "Where it can grow", such as an OLED display, and add it to the version that already works.
   - Expected: the new feature works, and every test from lab 2 still passes.
   - How to check: rerun all the lab 2 tests.
   - If it fails, check first: whether the new and old peripherals fight over the same thing, such as one pin (PA0 for the WS2812 and chapter 03's LED), one DMA channel (RM0008 Rev 21 Table 78), or one timer. On the C8, USB and CAN cannot work at the same time.
4. **Lab 4: Work out whether it fits.** After a build, run `arm-none-eabi-size` on the `.elf`.
   - Expected: you get three numbers, `text`, `data`, and `bss`.
   - How to check: `text + data` is the Flash used, which must be below 64 KB, or below `0xB800` for an IAP application; `data + bss` is the static variables in RAM, and with the stack and the heap added it must stay below 20480 bytes.
   - If it fails, check first: if the linker reports that the `FLASH` or `RAM` region overflowed, it already does not fit. Look first for big arrays (the logic analyzer's buffer), the FreeRTOS heap `configTOTAL_HEAP_SIZE`, and floating-point support turned on for `printf` (chapter 18).
5. **Lab 5: Write a retrospective.** Write down the pitfalls you hit in chapter 18's table format: symptom, cause, fix, how you confirmed it.
   - Expected: someone else can reproduce the project from your notes and wiring table alone.
   - How to check: give it to a classmate to follow, or rebuild it yourself from an empty project a week later.
   - If it fails, check first: whether your notes give the CubeMX and HAL versions, the clock configuration, the wiring of every pin, and the parts not yet done.

## Self-test

1. You are building the temperature and humidity logger and have an RTC, an SHT30, a W25Q64, and an OLED. Order them by "one new peripheral per round", and say how you know each round works.
2. Project 5's application starts at `0x08004800` with length `0xB800`. Where does it end? If you add a second application of the same size, where does that one end? Does the C8 have room?
3. The oscilloscope reads code 2048 with a nominal 3.3 V reference. How many volts do you get with a denominator of 4096, and with 4095? How far apart are they?
4. The DAQ card's frame is 133 bytes, and a full-speed bulk packet is at most 64 bytes. How many packets go on the wire, and how many bytes are in the last one?
5. A WS2812 runs from TIM2 counting at 72 MHz, with a 1.25 µs bit. What goes in ARR, and roughly what compare value sends a 1?

Answers:

1. One reasonable order: RTC → SHT30 → W25Q64 → OLED. The RTC works when the serial port prints the time and the time carries on after a reset. The SHT30 works when the serial port prints readings and the temperature rises when you cup the sensor in your hand. The W25Q64 works when data written, powered off, and powered up reads back the same, and a full lap wraps back to the start. The OLED comes last, since display is the top layer: the time and the data must be right before showing them means anything. Other orders work too, as long as each round adds one thing and the display comes last.
2. `0x08004800 + 0xB800 = 0x08010000`, exactly the end of the 64 KB Flash. A second one right after ends at `0x08010000 + 0xB800 = 0x0801B800`, and the total is `16 + 2 + 46 + 46 = 110` KB, more than 64 KB, so it does not fit.
3. 2048 × 3.3 / 4096 = 1.65 V; 2048 × 3.3 / 4095 ≈ 1.6504 V, about 0.4 mV apart, half an LSB. The gap grows with the code and reaches exactly one LSB (about 0.8 mV) at full scale, 4095.
4. 133 = 64 + 64 + 5: three packets, and the last one is 5 bytes. The USB stack does the splitting, and `wMaxPacketSize` is still 64.
5. 1.25 µs × 72 MHz = 90 counts, so ARR = 90 − 1 = 89. The high time of a 1, 0.8 µs × 72 MHz = 57.6, rounds to 58 counts, about 0.81 µs; the high time of a 0, 0.4 µs × 72 MHz = 28.8, rounds to 29.

## Principle and scope

> [!NOTE]
> From this section to "Pitfalls and sources" is the deep part. It pins the conclusions above to one part number, one manual section, and numbers you can recompute. On a first read you can skip it and come back after the labs.

**Scope of this chapter.** All the code in this chapter is written for the STM32F103C8T6, the chip on the BluePill. Every number written for this part must fit this part: the Flash map is the same one as chapter 12, and the ADC conversion is the same reckoning as chapter 09. The ten projects are ten practice routes, not ten finished products.

**One application.** The bootloader starts at `0x08000000` for 16 KB, the parameter block starts at `0x08004000` for 2 KB, and the application starts at `0x08004800` for 46 KB, length `0xB800`, ending before `0x08010000`. `16 + 2 + 46 = 64`. This is the map of chapter 12 and `examples/iap-bootloader`; see [repository examples](#source-project-examples).

**A second one does not fit.** Add another image of the same `0xB800` and the total is `16 + 2 + 46 + 46 = 110` KB. `0x08000000 + 0x1B800 = 0x0801B800`, past `0x08010000`. Flash ends at `0x08010000`; see [DS5319](#source-ds5319-swd). Chapter 12 has no second slot. Cutting the 46 KB into two 23 KB images is a different design, not the normal path of this map.

**The SRAM budget.** `64 * 1024 = 65536`. The C8 has 20 KB of SRAM, which is 20480 bytes; see [DS5319](#source-ds5319-swd). 65536 is larger than 20480, so that array does not fit on the STM32F103C8T6, and that is why project 7 uses 8 KB. On another part, look up its SRAM in that part's own datasheet.

**The ADC denominator.** The ADCs of medium-density devices are 12-bit; see [DS5319 ADC](#source-ds5319-adc). That is 4096 codes. The denominator is 4096, and code 2048 at a nominal 3.3 V is 1.65 V. With 4095 as the denominator the result is off by exactly one LSB at full scale, the same reckoning as chapter 09. For how to choose the sampling time and what the source impedance does, see chapter 09.

**ADC conversion time.** One conversion = sampling time + 12.5 ADC clock cycles; see [RM0008 ADC](#source-rm0008-adc). With a 12 MHz ADC clock, the shortest conversion is 1.5 + 12.5 = 14 cycles. The oscilloscope's trigger interval must not be shorter than one conversion.

**One USB packet.** The application frame is `4 + 128 + 1 = 133` bytes. Chapter 14's full-speed bulk packet limit is 64 bytes, so 133 goes out as three packets, 64 + 64 + 5; the bulk endpoints of the `usb-cdc` example are exactly 64 bytes; see [repository examples](#source-project-examples). Do not write 133 into `wMaxPacketSize`. For the 48 MHz clock USB needs and the example's VID/PID `0x1209/0x0001`, see chapter 14.

**The CAN reckoning.** Project 8's 120 Ω at each end, working pins PB8/PB9, 500 kbit/s, and prescaler of 9 are the same as chapter 13 and `examples/can-bxcan`; see [repository examples](#source-project-examples). Whether the transceiver runs from 5 V or 3.3 V, see project 8's bill of materials and the transceiver's own datasheet.

**PA0 is not a direction pin.** Do not put a direction pin on pin 10, PA0. That pin is PA0-WKUP and also ADC12_IN0; see [DS5319 ADC](#source-ds5319-adc). The direction pins that project 1 moves to are an example setting, and any other free pins will do.

**One peripheral per round is a method.** Adding only one new peripheral per round is a way of working, not an electrical limit of the chip. The time and the stars are rules of thumb and appear only in each project's small table. The WS2812 microsecond figures are the LED vendor's numbers, not RM0008, and appear only in project 6.

## Key figures

<p align="center">
  <img src="../../assets/diagrams/sample-19-flash-fit.svg" width="760" alt="The C8 has one application of length 0xB800. Two of them are 110 KB. 65536 bytes is larger than 20 KB of SRAM.">
  <br><sub>▲ Drawn for this book. The normal path is 16 KB, 2 KB, and one 0xB800 image ending before 0x08010000. SRAM is 20 KB, which is 20480 bytes. The failure path draws a second 0xB800 from 0x08010000 to 0x0801B800, and a 65536-byte array past 20480. The notes are a denominator of 4095, and treating 133 bytes as one USB packet. Sources: the map already frozen in chapter file 12, and the 64 KB / 20 KB cells in [DS5319](#source-ds5319-swd).</sub>
</p>

<p align="center">
  <img src="../../assets/gif/one-slot.gif" width="640" alt="16 KB, 2 KB, and one 0xB800 image fill up to 0x08010000">
  <br><sub>▲ Auxiliary figure for the web and for posts. It plays only the normal path: 16 KB, 2 KB, and one 0xB800 image fill up to 0x08010000. Print from the static figure. The second application and the 65536-byte array are not on this GIF.</sub>
</p>

`peripheral-wiring.svg` stays as an auxiliary figure. The wiring overview does not replace this map.

## Timing and state

This chapter has no timing diagram; this block records each object's size, boundary, and verdict. Read by row. The first three rows are the normal path through Flash, laid out from `0x08000000`, and each row's end address is the next row's start; the fourth row is the second image that does not fit. The next three rows are SRAM. The last four rows are the reckoning for three peripherals.

| Object | Size | Boundary | Verdict |
| --- | --- | --- | --- |
| Bootloader | 16 KB | ends at `0x08004000` | Fits |
| Parameter block | 2 KB | ends at `0x08004800` | Fits |
| One application | `0xB800` | ends at `0x08010000` | Fits |
| Two `0xB800` images | 110 KB | ends at `0x0801B800` | Does not fit. This is not chapter 12's map |
| Total SRAM | 20480 bytes | on chip | All variables, the stack, and the heap together must not exceed it |
| A 65536-byte array | `64 * 1024` | past SRAM | Does not fit on the C8 |
| An 8 KB sample buffer | `8 * 1024 = 8192` bytes | inside SRAM | Fits, leaving 12288 bytes for other variables, the stack, and the heap |
| ADC conversion to volts | denominator 4096 | code 2048 is 1.65 V | A denominator of 4095 is off by one LSB at full scale |
| ADC conversion time | sampling time + 12.5 cycles | at least 14 cycles at 12 MHz | The trigger interval must be longer than one conversion |
| USB | 133-byte application frame | 64-byte packet limit | Split into three packets, 64 + 64 + 5 |
| CAN | 500 kbit/s, prescaler 9 | PB8/PB9 | 120 Ω at each end |

## Pitfalls and sources

Read each row left to right: the symptom first, then the cause and what to do; the last two columns say where the conclusion comes from and how far that source goes.

| Symptom | Cause | What to do | Source | What the source supports |
| --- | --- | --- | --- | --- |
| The update plan has two applications and says "see chapter 12" | A different design written up as this chapter's map | On the C8, get one `0xB800` image working first | [repository examples](#source-project-examples) | The application length in `examples/iap-bootloader` is `0xB800`. Chapter 12 has no second slot |
| The second image is linked past `0x08010000` | The 64 KB has already ended | Stop at `0x08010000` | [DS5319](#source-ds5319-swd) | STM32F103x8 Flash is 64 KB. 110 KB is computed from `16 + 2 + 46 + 46`; it is not a number in the manual |
| The logic-analyzer buffer will not link on the C8 | `64 * 1024` is more than this part's SRAM | Do not build 65536 bytes into the C8; start with 8 KB | [DS5319](#source-ds5319-swd) | SRAM is 20 KB, that is 20480 bytes. This row gives no capacity for any other part |
| The oscilloscope voltage is off by one LSB | The denominator was 4095 | Use 4096 | [DS5319 ADC](#source-ds5319-adc) | The ADCs of medium-density devices are 12-bit, so there are 4096 codes. Code 2048 being 1.65 V is computed from 4096 and a nominal 3.3 V |
| The oscilloscope's trigger interval is set shorter than one conversion | Only the timer's speed was considered, not how long one ADC conversion takes | Make the trigger interval longer than one conversion; at a 12 MHz ADC clock the minimum is 14 cycles | [RM0008 ADC](#source-rm0008-adc) | Conversion time = sampling time + 12.5 cycles; at 12 MHz, 1.5 cycles is 125 ns. The 14 cycles is the sum of the two. The card does not say what happens to a trigger that arrives mid-conversion, so do not rely on it |
| The DAQ card writes 133 bytes as the endpoint packet length | The application frame taken for the packet limit | A full-speed bulk packet is at most 64 bytes; split 133 into 64 + 64 + 5 | [repository examples](#source-project-examples) | The bulk endpoints of the `usb-cdc` example are 64 bytes. 133 is `4 + 128 + 1`, not chapter 14's packet limit |
| The car's direction pin is on PA0 | It collides with the other uses of pin 10 | Move off pin 10 | [DS5319 ADC](#source-ds5319-adc) | Pin 10 is PA0-WKUP and also ADC12_IN0. This row does not assign new motor pins |
| Two CAN nodes disagree on the bit rate | Chapter 13's reckoning was not followed | Use 500 kbit/s, with 120 Ω at each end | [repository examples](#source-project-examples) | The example's prescaler is 9 and its working pins are PB8/PB9. This row does not say whether the transceiver runs from 5 V or 3.3 V |
| Power fails mid-update, and at the next power-up the chip jumps into half an application | Only the stack pointer is checked, and that cannot catch an application whose stack pointer is written but whose rest is not | Erase the parameter page first and write the valid marker last | [repository examples](#source-project-examples) | Before jumping, `examples/iap-bootloader` only checks that the stack pointer falls in the `0x20000000` region; that example does not use the parameter block |
| On the C8, USB and CAN are both turned on and one of them receives nothing | The two share a dedicated 512-byte SRAM | Turn on only one at a time; for both, change parts | [DS5319 USB/CAN](#source-ds5319-usbcan) | PA11/PA12 carry both USB and CAN among their alternate functions, and one pair of pins cannot do both at once. The shared SRAM is in RM0008 Rev 21 sections 23.2 and 24.2, not on this card |
| Code from an F4 board reads the low 8 bits of `GPIOC->IDR` on the C8 and sees no signal | The C8 in LQFP48 has no PC0–PC7 | Read the low 8 bits of `GPIOA->IDR` instead, that is PA0–PA7 | DS5319 Rev 20 Table 5 (no source card) | In the LQFP48 column of Table 5, port C has only PC13, PC14, and PC15 |

A row whose source column has no link cites a manual section that does not have a source card yet. This chapter gives a learning path, not a statement of safety, EMC, production testing, or regulatory compliance; batteries, motors, and 5 V LED strips draw far more current than the board, so for wiring, fuses, and heat, go by each device's own datasheet.

## Related resources

- The technical detail is in [chapters 03 through 17](03-gpio-and-led.md) (GPIO, UART, I2C, SPI, ADC, DMA, TIM, RTC, Flash, CAN, USB, RTOS, low power, and debug): [03](03-gpio-and-led.md), [04](04-interrupts-nvic.md), [05](05-timer-pwm.md), [06](06-uart.md), [07](07-i2c.md), [08](08-spi.md), [09](09-adc-dac.md), [10](10-dma.md), [11](11-rtc-watchdog.md), [12](12-flash-iap.md), [13](13-can.md), [14](14-usb.md), [15](15-freertos.md), [16](16-low-power.md), [17](17-debug.md).
- Example projects: [`examples/`](../../examples/) (gpio-blink, uart-dma-idle, i2c-oled, adc-dma, rtc-alarm, freertos-task, iap-bootloader).
- Reference manuals: RM0008 / RM0090 (peripheral registers and buses).
- Related chapters: [chapter 12, IAP](12-flash-iap.md), [chapter 13, CAN](13-can.md), [chapter 14, USB](14-usb.md), [chapter 15, FreeRTOS](15-freertos.md).
- Figure: `../../assets/boards/peripheral-wiring.svg` (author-drawn vector).
