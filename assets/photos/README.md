# 实拍照片来源与许可

本目录只存放许可允许再分发的第三方实拍照片。章节必须同时写明**照片中的确切板卡型号**，不得把同系列外形图冒充目标板。

| 本地文件 | 实拍对象 | 作者 / 来源 | 许可 | 本地处理 |
| --- | --- | --- | --- | --- |
| `nucleo-f411re-embedded-world.jpg` | Embedded World 2016 展出的 STM32 Nucleo-F411RE | Ordercrazy / Thomas Springer，[Wikimedia Commons 原图页](https://commons.wikimedia.org/wiki/File:Embedded_World_2016,_Stm32_Nucleo.jpg) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | 从 Commons 960 px 预览缩至 760×884，JPEG quality 82；SHA-256 `f023915c238b9ca49ce68b349542b2a2ecae377f14c28b4e4334292f09c4a5e8` |
| `nucleo-f401re-embedded-world.jpg` | Embedded World 2016 展出的 STM32 Nucleo-F401RE | Ordercrazy / Thomas Springer，[Wikimedia Commons 原图页](https://commons.wikimedia.org/wiki/File:Embedded_World_2016,_STM_Nucleo_401.jpg) | [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/) | 从 Commons 960 px 预览缩至 760×852，JPEG quality 82；SHA-256 `4fdea7be65c35d96ee9dbeebfc1a5475dcb65b758b5c0dea3cc5a529fe093815` |
| `bluepill-stm32f103c8t6.jpg` | Blue Pill 开发板（STM32F103C8T6） | Avandalen，[Wikimedia Commons 原图页](https://commons.wikimedia.org/wiki/File:Blue_Pill.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0)（署名—相同方式共享） | 从 Commons 原图 874×362 缩至 760×315，JPEG quality 82；SHA-256 `73b1887438eefaf0766bef50dbd3f631d7fd80e1f3ca392cde4c29fabb5c03c7` |
| `bluepill-stm32f103c8t6-popolon.jpg` | Blue Pill / Core Learning Board（STM32F103C8T6） | Popolon，[Wikimedia Commons 原图页](https://commons.wikimedia.org/wiki/File:Core_Learning_Board_module_Arduino_STM32_F103_C8T6.jpg) | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0)（署名—相同方式共享） | 原图拍摄 2018-09-08；从 Commons 原图缩至 760×513，JPEG quality 82；SHA-256 `ece8ef0b4f76c21688532b43c86ba5663ec7a3bc042f16107bc7b5eecc470a57` |
| `bluepill-stm32f103c8t6-tardate-usb.jpg` | Blue Pill 开发板（STM32F103C8T6），USB 供电，板载 LED 点亮 | Paul Gallagher，[tardate/LittleArduinoProjects `ARM/STM32F103C8T6/BluePill/assets/BluePill_usb_powered.jpg`](https://github.com/tardate/LittleArduinoProjects/blob/master/ARM/STM32F103C8T6/BluePill/assets/BluePill_usb_powered.jpg) | [MIT](https://github.com/tardate/LittleArduinoProjects/blob/master/LICENSE)（Copyright (c) 2014 Paul Gallagher） | 从原图 1280×706 缩至 760×419，JPEG quality 82；SHA-256 `7284c0fe3701a912973934b2b643c89091c6d292f9ad058aa9064af768c27843` |

`bluepill-stm32f103c8t6-tardate-usb.jpg` 只证明“USB 供电下有一颗板载 LED 点亮”；图中丝印不可辨，**不能据此判定该灯是 PC13 用户灯还是电源灯**，因此不当作 PC13 LED 特写。MIT 许可要求随副本保留上方版权声明与许可链接。

Nucleo 两张照片用于识别 Nucleo-64 家族的 ST-LINK 上半区、目标 MCU 下半区和排针布局，**都不是 NUCLEO-L476RG**。L476RG 的确切板卡照片、原理图和最新硬件版本以 [ST 官方产品页](https://www.st.com/en/evaluation-tools/nucleo-l476rg.html) 与 UM1724 为准。三张 Blue Pill 照片均为**硬件参照照**（Avandalen + Popolon 两张俯视板卡全貌，均为 CC BY-SA 4.0；Paul Gallagher 一张 USB 供电、板载 LED 点亮，MIT）：只用于识别板卡整体外观与引脚排布；板载 PC13 LED 位于 USB 座一侧（据板卡原理图/丝印，图中过小难以分辨，MIT 那张点亮的灯也无法判定是否为 PC13）。**PC13 LED 特写与万用表/逻辑分析仪截图仍缺**——不得用 AI 生成图冒充。上述实拍不含测量画面，不能当作实验测量证据。PC13 电流路径见章内 Handraw/stack（知识轨，标注「原理示意/非实拍」），不得登记为真证轨。
