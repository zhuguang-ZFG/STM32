# 硬件实测报告目录

本目录存放硬件实测报告模板与采集指南。

---

## 文件说明

| 文件 | 用途 |
|---|---|
| `e01-test-report.md` | E01 点亮 RGB 红灯实测报告模板 |
| `j1-test-report.md` | J1 F407 传感器记录器实测报告模板 |
| `gdb-screenshot-guide.md` | GDB 调试截图采集指南（F1/F6/F7 章节用） |
| `first-round-test-report.md` | 首轮实测报告模板（E01-E03 基础三件套） |

---

## 使用流程

### 1. 实测前

- 阅读对应实验的章节（如 `docs/lab/e01-blink.md`）
- 准备装备清单中的硬件
- 复制报告模板到工作目录

### 2. 实测中

- 按模板逐项填写数据
- 拍照/截图时参考 `gdb-screenshot-guide.md`
- 遇到问题立即记录（现象、原因、解决）

### 3. 实测后

- 完成报告所有字段
- 将照片/截图存入 `docs/public/images/lab/`
- 更新实验章节的 `hardware_status: verified`
- 提交 PR

---

## 命名规范

### 报告文件
```
<experiment-id>-test-report.md
```

示例：
- `e01-test-report.md`
- `j1-test-report.md`

### 图片文件
```
<experiment-id>-<description>.<ext>
```

示例：
- `e01-wiring.jpg`
- `e02-uart-0x41.png`
- `e03-pwm-pa6.png`
- `j1-adc-log.png`

---

## 验收标准

每份报告需满足：
- [ ] 所有必填字段已填写
- [ ] 至少 1 张接线照片
- [ ] 实测数据与理论对比表
- [ ] 至少 1 条排错记录（如有问题）
- [ ] 结论明确（通过/部分通过/失败）

---

## 相关链接

- [硬件实测计划](../../hardware-test-plan.md)
- [上板验证指南](../../guide/verify-on-hardware.md)
- [实验模板](../template.md)
