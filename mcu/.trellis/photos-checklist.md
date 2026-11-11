# 上板验证照片清单

> 本文件是施工指引（不进 docs/），列出每个实验上板时需要拍摄的照片/截图。
> 拍摄后放到 `docs/public/photos/eXX-*.jpg`，在对应实验章插入 `![](/photos/eXX-*.jpg)`。
> 拍完一批后把 `hardware_status: pending` 改成 `verified`，并在实验章"实测记录"表填日期/数据。
>
> ⚠️ 注意与**资料参考图**区分：`docs/public/images/boards/` 下已有三张互联网开源许可照片
> （实战派整板 MIT、WROOM-1 模组 CC BY-SA 4.0、第三方 F407 板 CC0，来源见 guide/hardware.md
> "图片来源与许可"），它们是帮读者认板子的资料图，**不能**充当上板验证证据，
> 也不改变 hardware_status。霸天虎无合法授权照片（野火官方仓库无许可证），继续用官方链接。

## E01 点亮 RGB 红灯
- [ ] 板子全景（霸天虎 + LED 亮红灯）
- [ ] 串口日志截图（如果有 printf）

## E02 逻辑分析仪抓 UART 帧
- [ ] 分析仪截图：完整 UART 帧（起始位+8数据+停止位）
- [ ] 板子接线照片（UART TX→分析仪探针）

## E03 示波器看 PWM
- [ ] 示波器截图：PWM 波形（占空比可变）
- [ ] 改占空比前后对比截图

## E04 优先级反转复现
- [ ] 串口日志截图：信号量版（H 等待时间长）
- [ ] 串口日志截图：互斥量版（H 等待时间短）
- [ ] 两组日志并排对比

## E05 I2C 抓包读 EEPROM
- [ ] 分析仪截图：写事务（START+地址+ACK+数据+STOP）
- [ ] 分析仪截图：读事务（重复 START+NACK+STOP）
- [ ] 串口日志：read=0x5A PASS

## E06 低功耗电流实测
- [ ] 万用表接线照片（串联在供电上）
- [ ] 霸天虎三档电流读数照片（mA/µA/µA）
- [ ] S3 三档电流读数照片
- [ ] 续航估算表填实测数据

## E07 读 QMI8658
- [ ] 串口日志截图：WHO_AM_I=0x05
- [ ] 串口日志截图：六轴数据流（摇板子看数据变）
- [ ] 板子照片（S3 + IMU 芯片位置）

## E08 音频放音
- [ ] 串口日志截图：1kHz 1s + 旋律播放
- [ ] 板子照片（喇叭/功放位置）
- [ ] （可选）音频录制确认发声

## 照片命名规范
- `docs/public/photos/e01-blink-led.jpg`
- `docs/public/photos/e02-uart-frame.png`（分析仪截图可用 png）
- 文件名小写、kebab-case、编号在前

## 插入实验章格式
```markdown
## 实测照片

![LED 亮红灯](/photos/e01-blink-led.jpg)

![UART 帧](/photos/e02-uart-frame.png)
```

## 改 hardware_status
拍完一组照片并填实测记录后，把实验章 frontmatter 的 `hardware_status: pending` 改成 `verified`。

> AI生成