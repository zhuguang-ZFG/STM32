---
title: 导读·上板验证与回填指南
---

# 上板验证与回填指南：从「看懂」到「做实」

> 🎯 本站每一章都配有**实物实验**，但「成稿」不等于「上板验证通过」。
> 这一页教你：拿到板子后怎么跑实验、怎么记录证据、怎么把验证结果回填进站点，
> 让后来的读者知道「这一章有人真跑过」。

## 你需要什么

| 角色 | 装备 | 参考章节 |
|---|---|---|
| 验证者 | 野火 STM32F407 霸天虎 + ST-Link / ESP32-S3 板 | [实物装备清单](./hardware.md) |
| 记录者 | 手机拍照 / 逻辑分析仪截图 / 串口日志 | 下文「证据格式」 |

## 四步验证流程

### ① 读信息卡，确认先修

每个实验页顶部有 `<LabStatus />` 信息卡：

- **配套代码**：`ready` 表示工程已提供，按实验正文构建即可；`planned` 表示还在建设中，暂无法验证。
- **上板验证**：`verified` 表示已有人提交证据；`pending` 表示等你来第一个验证。
- **先修章节**：信息卡下方列出的「先修」必须读过，否则现象对不上。

### ② 构建并烧录

按实验正文的操作步骤：

1. 打开对应工程（`code/<board>/<project>/`）
2. `make flash`（STM32）或 `idf.py flash`（ESP32）
3. 确认串口有预期输出，LED/蜂鸣器/屏幕按正文描述响应

::: tip 遇到构建失败先检查
- STM32：是否安装了 [Arm GNU Toolchain](../stm32/00-env.md)？OpenOCD 能否识别 ST-Link？
- ESP32：`idf.py set-target esp32s3` 是否正确？SDKCONFIG 是否匹配当前板？
:::

### ③ 观察与记录

把「预期现象」变成「实际证据」：

| 实验类型 | 建议记录方式 | 最低证据 |
|---|---|---|
| 点灯/蜂鸣器 | 手机拍 5 秒视频或 2–3 张照片 | 板子运行时的真实状态 |
| UART/逻辑分析仪 | PulseView 截图 + 串口助手日志 | 波形或文本输出 |
| 传感器/I2C/SPI | 数据抓屏 + 寄存器值照片 | 可读数值 |
| RTOS 调度/互斥 | 串口打印时间戳 + 现象描述 | 时序符合预期 |
| 低功耗/电流 | 万用表/电源截图 | 电流值与预期范围 |

::: warning 证据必须「可复现」
不要只写「成功了」。写清楚：
- 板卡型号与固件版本
- 接线图（或引用正文中的接线）
- 操作步骤（与正文一致可省略，差异必须说明）
- 实际观察到的现象（与正文预期对比）
:::

### ④ 撰写证据文件并回填

#### 创建证据文件

在 `docs/lab/evidence/` 下新建 Markdown：

```text
docs/lab/evidence/
  e01-blink-verified.md        ← 实验 E01 的验证记录
  e05-i2c-eeprom-verified.md   ← 实验 E05 的验证记录
```

文件名规律：`e<nn>-<slug>-verified.md`，与实验页一一对应。

#### 证据文件模板

```markdown
---
title: 实验 E01 上板验证记录
author: 你的 GitHub ID
date: 2026-10-08
board: 野火 STM32F407 霸天虎
firmware: stm32-00-blink（commit abc1234）
---

# 实验 E01 点亮霸天虎的 RGB 红灯 —— 上板验证

## 验证环境

- 板卡：野火 STM32F407 霸天虎
- 调试器：ST-Link V2
- 固件：code/stm32/00-blink（commit abc1234）
- 工具链：arm-none-eabi-gcc 13.2.1

## 操作步骤

按 [E01 正文](../e01-blink.md)「实物实验」节执行，无差异。

## 实际现象

烧录后 PF6（RGB 红灯）以 1Hz 频率闪烁，与正文预期一致。

## 证据

![PF6 红灯闪烁](./evidence/e01-blink-photo.jpg)

## 结论

✅ 验证通过。现象与正文描述一致，无异常。
```

#### 更新实验页 frontmatter

打开对应实验的 `.md`（如 `docs/lab/e01-blink.md`），修改 frontmatter：

```yaml
hardware_status: verified
evidence: lab/evidence/e01-blink-verified.md
```

`evidence` 是**相对 docs/** 的文件路径。提交 PR 后，CI 的 `metadata.test.mjs` 会自动检查 `evidence` 文件是否存在。

#### 更新 README 与总览

运行 `npm run docs:gen` 重新生成 `docs/curriculum.json` 与进度统计，确保 [实验总览](../lab/index.md) 的验证计数正确。

## 常见疑问

**Q：我没有板子，能不能只改 `hardware_status`？**

不行。`hardware_status: verified` 必须有对应的 `evidence` 文件，且 metadata 测试会强制检查文件存在。**没有实物验证就标记 verified 属于伪造数据**，CI 会拦下。

**Q：验证失败了怎么办？**

这正是最有价值的反馈！在 evidence 文件中如实记录：
- 失败的步骤
- 错误输出或现象
- 你排查过的方向

然后提交 PR 更新实验正文（修正操作步骤或补充排错提示），frontmatter 保持 `hardware_status: pending`，但正文因为这次失败而变得更可靠。

**Q：一个实验被多个人验证，怎么处理？**

以**最新一次**的 evidence 文件为准，文件名不变，内容覆盖。如果你想保留历史，可以在 evidence 文件内追加验证记录（保留日期与作者）。

**Q：综合项目（J1/J2）怎么验证？**

综合项目有更长的 checklist，验证方式同上，但 evidence 文件应覆盖全部 checklist 项。见 [J1](../projects/01-f407-logger.md) / [J2](../projects/02-s3-logger.md) 正文末尾的「验证清单」。
