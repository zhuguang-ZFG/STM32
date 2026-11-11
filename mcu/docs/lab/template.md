---
title: 实验模板
---

# 实验模板：每个实验都长这样

> 🎯 好实验 = 看一遍就想动手，动手一次就能成，成了还想改参数。下面这套结构就是为此设计的——写新实验时整段复制，逐项填实。

## 使用说明（写完新实验请删除本节）

- 所有字段都必须填**真实内容**，没有"待补充"字段；
- 接线图一律 SVG（`docs/public/images/labs/`），实物照片欢迎实拍补充（规范见 [CONTRIBUTING](https://github.com/zhuguang-ZFG/mcu/blob/main/CONTRIBUTING.md)）；
- 板卡外观与引脚分配见各板官方资料页：[野火霸天虎](https://doc.embedfire.com/products/link/zh/latest/mcu/stm32/stm32f407_batianhu.html)、[立创实战派 S3](https://wiki.lckfb.com/zh-hans/szpi-esp32s3/)；
- 预期现象必须可观测（肉眼/串口/逻辑分析仪/万用表），禁止"应该可以了吧"；
- 故障排查 ≥3 条，按"出现频率"排序；
- 思考题 2–4 个，答案藏在对应章节里。

新实验 frontmatter 必须包含以下字段（标题、时长、难度填写真实值）：

```yaml
title: 实验 E 编号与标题
status: building
difficulty: 2
minutes: 60
code_status: planned
hardware_status: pending
code_note: 说明当前配套工程和复现条件
projects: []
```

`status` 只表示文稿状态；提供完整工程后将 `code_status` 改成 `ready` 并在 `projects` 填 `code/projects.json` 中的 ID。`hardware_status: verified` 必须附 `evidence`（相对 docs/ 的实测记录文件路径）。时长和难度由 `<LabStatus />` 展示，不在正文重复手写。

---

## 实验信息卡

复制新实验时在这里插入 `<LabStatus />`（模板页本身不实例化）。

| 项 | 内容 |
|---|---|
| 编号 | E xx |
| 对应章节 | [章节链接](../stm32/index.md) |
| 目标板 | 霸天虎 / 立创 S3（或两者） |

## 实验目标

做完能得到什么（一句话现象 + 一句话能力）。

## 装备

| 装备 | 数量 | 备注 |
|---|---|---|

## 原理一句话

本实验背后的一句话原理（详细理论回对应章节）。

## 接线

```markdown
![接线图](/images/labs/<eid>-<name>.svg)
```

接线要点表（哪根线插哪个孔，电源纪律）。

## 步骤

编号步骤，每步一个动作 + 一个检查点。

## 预期现象

明确写出"成功长什么样"（灯的频率/串口的字/波形的参数）。

## 实测记录

| 日期 | 板子 | 观测手段 | 结果 | 备注 |
|---|---|---|---|---|
| | | | | |

## 故障排查

| 症状 | 最可能原因 | 处置 |
|---|---|---|
| | | |

## 思考题

1.
2.

## 你做到了

能力清单（成就感闭环）。
