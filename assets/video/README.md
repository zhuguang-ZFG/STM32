# 讲解视频

每条片子是同名的 `.mp4`、`.srt`、`.png`。画面是脚本画的，不是实拍。生成方式见 [assets/README.md](../README.md) 第六节。

## 正片 `ch00`–`ch28`

文件名是 `ch{章号}-{slug}`，由 [tools/narration.py](../../tools/narration.py) 决定，例如 `ch00-learn`、`ch28-rtos-system`。

标题和阅读顺序在 [docs/README.md](../../docs/README.md)（English: [docs/en/contents.md](../../docs/en/contents.md)）。每一章正文里已经嵌了对应的播放器。

## 续集 `chs01`–`chs12`

正片之后的「STM32 × AI 写代码」。旁白在 [tools/narration_ai.py](../../tools/narration_ai.py)，用 `NARRATED_MODULE=narration_ai` 调用 `tools/gen_narrated.py`。集号 `s01` 会变成文件名前缀 `chs01`。这些片子没有单独的章节文档。

| 文件 | 标题 |
| --- | --- |
| [chs01-ai-basics.mp4](chs01-ai-basics.mp4) | AI 写代码：正确用法 |
| [chs02-ai-uart.mp4](chs02-ai-uart.mp4) | 让 AI 写串口并自测 |
| [chs03-ai-manual.mp4](chs03-ai-manual.mp4) | 把手册喂给 AI |
| [chs04-ai-hal2ll.mp4](chs04-ai-hal2ll.mp4) | 把 HAL 改成 LL |
| [chs05-ai-pwm.mp4](chs05-ai-pwm.mp4) | 让 AI 写 PWM 并验证 |
| [chs06-ai-i2c.mp4](chs06-ai-i2c.mp4) | AI 写 I2C 驱动 |
| [chs07-ai-debug.mp4](chs07-ai-debug.mp4) | 让 AI 帮你调 bug |
| [chs08-ai-rtos.mp4](chs08-ai-rtos.mp4) | AI 写 FreeRTOS 模板 |
| [chs09-ai-boot.mp4](chs09-ai-boot.mp4) | AI 写 Bootloader 跳转 |
| [chs10-ai-errata.mp4](chs10-ai-errata.mp4) | 同名不同位：型号差异 |
| [chs11-ai-templates.mp4](chs11-ai-templates.mp4) | 提示词模板总集 |
| [chs12-ai-capstone.mp4](chs12-ai-capstone.mp4) | 毕业项目：AI 协作写小产品 |

## 已取代

`chai01-ai-gpio` 是上面第一集的早期成片，已移到 [superseded/](superseded/README.md)。续集第一集只认 `chs01-ai-basics`。
