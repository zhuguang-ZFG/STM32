# 仿真

没有板子时从这里进。原理、模型边界和跑不完的外设写在 [第 22 章](../docs/22-仿真实验Wokwi与Renode.md)（English: [chapter 22](../docs/en/22-simulation-wokwi-renode.md)）。

## Renode

脚本在 [`renode/`](renode/)，都加载官方 `platforms/cpus/stm32f103.repl`：

| 脚本 | 对应示例 |
| --- | --- |
| [gpio-blink.resc](renode/gpio-blink.resc) | [examples/gpio-blink](../examples/gpio-blink/) |
| [uart-usart1.resc](renode/uart-usart1.resc) | [examples/uart-dma-idle](../examples/uart-dma-idle/) |

## Wokwi

浏览器工程不在这个目录。`diagram.json` 和 `wokwi.toml` 放在示例旁边，目前有：

`gpio-blink`、`exti-key`、`timer-pwm`、`uart-dma-idle`、`i2c-oled`、`adc-dma`。

示例总表和接线在 [examples/README.md](../examples/README.md)。
