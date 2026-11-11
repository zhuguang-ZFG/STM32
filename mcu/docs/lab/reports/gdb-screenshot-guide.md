# GDB 调试截图采集指南

> 📸 本指南说明 FreeRTOS GDB 调试章节需要哪些截图、如何采集、命名规范

---

## 一、需要的截图清单

### F1 任务与 TCB（`docs/rtos/freertos/01-task-tcb.md`）

| 编号 | 截图内容 | GDB 命令 | 用途 |
|---|---|---|---|
| F1-01 | TCB 指针与任务名 | `p pxCurrentTCB`<br>`p pxCurrentTCB->pcTaskName` | 展示"当前任务是谁" |
| F1-02 | 栈内容（xPSR/PC/LR） | `x/16xw pxCurrentTCB->pxTopOfStack` | 指认"中断妆"的物理证据 |
| F1-03 | 任务状态表 | `info tasks`（需 FreeRTOS-GDB 插件）<br>或 `vTaskList` 串口输出 | 展示多任务状态 |

### F6 通知与事件组（`docs/rtos/freertos/06-notify-event-timer.md`）

| 编号 | 截图内容 | GDB 命令 | 用途 |
|---|---|---|---|
| F6-01 | 通知值（计数语义） | `p pxCurrentTCB->ulNotifiedValue[0]` | 展示"欠账"累积 |
| F6-02 | 事件组位 | `p xEventGroup->uxEventBits` | 展示位状态 |
| F6-03 | watchpoint 触发 | `watch ulNotifiedValue[0]`<br>`continue` → 命中 | 展示"值变化自动暂停" |

### F7 堆与栈溢出（`docs/rtos/freertos/07-heap.md`）

| 编号 | 截图内容 | GDB 命令 | 用途 |
|---|---|---|---|
| F7-01 | 堆剩余与历史最低 | `p xPortGetFreeHeapSize()`<br>`p xPortGetMinimumEverFreeHeapSize()` | 展示堆监控 |
| F7-02 | 栈底 0xA5 水位线 | `x/32xb pxCurrentTCB->pxStack` | 展示"没被踩"的证据 |
| F7-03 | 栈溢出 hook 触发 | `break vApplicationStackOverflowHook`<br>`bt` | 展示"谁溢出了" |

---

## 二、采集环境准备

### 硬件
- F407 霸天虎开发板
- ST-Link V2（或 J-Link / DAP-Link）
- USB 线 × 2（板卡供电 + 仿真器）

### 软件
- OpenOCD（`openocd -f interface/stlink.cfg -f target/stm32f4x.cfg`）
- arm-none-eabi-gdb（V15.2.1 或更新）
- 终端截图工具：
  - **Windows**：Windows Terminal + Snipping Tool
  - **macOS**：iTerm2 + Cmd+Shift+4
  - **Linux**：tmux + `script` 命令或 Flameshot

### 固件
```bash
cd code/rtos/01-freertos-lab
make clean
make
make flash
```

---

## 三、采集流程

### 步骤 1：启动 OpenOCD

```bash
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg
```

**截图**：OpenOCD 启动成功，显示 `Info : Listening on port 3333 for gdb connections`

### 步骤 2：连接 GDB

```bash
arm-none-eabi-gdb build/freertos-lab.elf
(gdb) target remote :3333
```

**截图**：GDB 连接成功，显示 `Remote debugging using :3333`

### 步骤 3：执行目标命令

按上方清单逐项执行 GDB 命令，每条命令执行后截图。

**截图要求**：
- 终端窗口宽度 ≥ 100 字符
- 字体清晰（推荐 14px+ 等宽字体）
- 包含命令输入 + 输出
- 关键数据用红色框标注（后期用图片编辑工具加）

### 步骤 4：命名与归档

**命名规范**：
```
gdb-<chapter>-<id>.png
```

示例：
- `gdb-f1-01-tcb-pointer.png`
- `gdb-f1-02-stack-content.png`
- `gdb-f6-01-notify-value.png`
- `gdb-f7-03-stack-overflow-hook.png`

**存放位置**：
```
docs/public/images/rtos/gdb/
```

---

## 四、截图示例（文字版）

### F1-02 栈内容示例

```
(gdb) x/16xw pxCurrentTCB->pxTopOfStack
0x20001b80:	0x01000000	0x08000189	0x080002a1	0x00000000
0x20001b90:	0x00000000	0x00000000	0x00000000	0x00000000
0x20001ba0:	0x00000000	0x00000000	0x00000000	0x00000000
0x20001bb0:	0x00000000	0x00000000	0x00000000	0x00000000
```

**标注**：
- `0x01000000` → 红框标注，注释"xPSR（Thumb 位 = 1）"
- `0x08000189` → 红框标注，注释"PC（任务入口）"
- `0x080002a1` → 红框标注，注释"LR（prvTaskExitError）"

---

## 五、替代方案（无硬件时）

如果暂时没有硬件，可以用 **QEMU 模拟**：

```bash
# 安装 QEMU for ARM
sudo apt install qemu-system-arm

# 用 QEMU 跑固件
qemu-system-arm -M stm32vldiscovery -kernel build/freertos-lab.elf -s -S

# 另开终端，GDB 连接
arm-none-eabi-gdb build/freertos-lab.elf
(gdb) target remote :1234
```

**注意**：QEMU 模拟的栈内容可能与真实硬件略有差异，但 GDB 命令与证据链一致。

---

## 六、后期处理

### 图片编辑
- 工具：GIMP / Photoshop / Preview（macOS）
- 操作：
  1. 裁剪多余空白
  2. 红框标注关键数据
  3. 添加文字注释（箭头 + 说明）
  4. 压缩到 < 200KB（`tinypng.com` 或 `pngquant`）

### 插入文档

```markdown
![GDB 查看栈内容](/images/rtos/gdb/gdb-f1-02-stack-content.png)

**证据链**：`0x01000000` 是 xPSR（Thumb 位 = 1），`0x08000189` 是 PC（任务入口），`0x080002a1` 是 LR（prvTaskExitError）——对照 `port.c:202` 的 `pxPortInitialiseStack`，每行代码都能在栈里找到对应的字。
```

---

## 七、验收标准

每张截图需满足：
- [ ] 终端窗口完整，无截断
- [ ] 命令输入 + 输出清晰可读
- [ ] 关键数据用红框标注
- [ ] 文件名符合命名规范
- [ ] 文件大小 < 200KB
- [ ] 配套文字说明（证据链解读）

---

**采集者**：____  
**日期**：____-__-__
