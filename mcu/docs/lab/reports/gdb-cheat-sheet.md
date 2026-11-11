# GDB 调试 FreeRTOS 速查表

> 🎯 本速查表列出 FreeRTOS 调试最常用的 GDB 命令，按场景分类  
> 📖 配套章节：[F1 任务与 TCB](../../rtos/freertos/01-task-tcb.md)、[F6 通知与事件组](../../rtos/freertos/06-notify-event-timer.md)、[F7 堆与栈](../../rtos/freertos/07-heap.md)

---

## 一、连接与基础

### 启动 OpenOCD

```bash
# STM32F407
openocd -f interface/stlink.cfg -f target/stm32f4x.cfg

# ESP32-S3（需 OpenOCD ESP32 版本）
openocd -f interface/ftdi/esp32s3-usb-jtag.cfg -f target/esp32s3.cfg
```

### 连接 GDB

```bash
arm-none-eabi-gdb build/firmware.elf
(gdb) target remote :3333

# 或 ESP32
xtensa-esp32s3-elf-gdb build/firmware.elf
(gdb) target remote :3333
```

### 基础控制

```bash
(gdb) continue              # 继续运行
(gdb) interrupt             # 暂停（Ctrl+C）
(gdb) step                  # 单步进入
(gdb) next                  # 单步跳过
(gdb) finish                # 执行到当前函数返回
(gdb) info registers        # 查看所有寄存器
(gdb) backtrace             # 查看调用栈
```

---

## 二、任务与 TCB（F1）

### 查看当前任务

```bash
# 当前任务 TCB 指针
(gdb) p pxCurrentTCB
$1 = (tskTCB *) 0x20001a80

# 任务名
(gdb) p pxCurrentTCB->pcTaskName
$2 = "high\000\000\000..."

# 优先级
(gdb) p pxCurrentTCB->uxPriority
$3 = 2

# 栈顶指针
(gdb) p pxCurrentTCB->pxTopOfStack
$4 = (StackType_t *) 0x20001b80

# 栈底（溢出检查用）
(gdb) p pxCurrentTCB->pxStack
$5 = (StackType_t *) 0x20001800
```

### 查看栈内容（指认"中断妆"）

```bash
# 看栈顶 16 个字
(gdb) x/16xw pxCurrentTCB->pxTopOfStack
0x20001b80:	0x01000000	0x08000189	0x080002a1	0x00000000
0x20001b90:	0x00000000	0x00000000	0x00000000	0x00000000
...

# 证据链：
# 0x01000000 = xPSR（Thumb 位 = 1）
# 0x08000189 = PC（任务入口）
# 0x080002a1 = LR（prvTaskExitError）
```

### 查看所有任务（需 FreeRTOS-GDB 插件）

```bash
# 安装插件（一次性）
# 下载 freertos.py 放到 ~/.gdbinit 或项目 .gdbinit

# 查看任务列表
(gdb) info tasks
ID      Name            Priority    State
0       idle            0           Ready
1       low             1           Blocked
2       high            2           Running
3       rpt             1           Ready
```

**无插件替代**：串口输出 `vTaskList`

```c
// 代码中调用
vTaskList(statusBuffer);
printf("%s", statusBuffer);
```

---

## 三、通知与事件组（F6）

### 查看任务通知

```bash
# 通知值（计数语义）
(gdb) p pxCurrentTCB->ulNotifiedValue[0]
$1 = 3    # 欠了 3 次没取

# 通知状态
(gdb) p pxCurrentTCB->ucNotifyState[0]
$2 = 1 '\001'    # 1 = 已通知待取，0 = 未通知
```

### 查看事件组

```bash
# 事件组位
(gdb) p xEventGroup->uxEventBits
$1 = 5    # bit0 + bit2 置位

# 等待列表
(gdb) p xEventGroup->xTasksWaitingForAllBits
(gdb) p xEventGroup->xTasksWaitingForAnyBits
```

### Watchpoint（值变化自动暂停）

```bash
# 监控通知值变化
(gdb) watch pxCurrentTCB->ulNotifiedValue[0]
Hardware watchpoint 1: pxCurrentTCB->ulNotifiedValue[0]

(gdb) continue
# 值变化时自动暂停

# 监控事件组位
(gdb) watch xEventGroup->uxEventBits
```

---

## 四、堆与栈溢出（F7）

### 查看堆状态

```bash
# 当前剩余
(gdb) p xPortGetFreeHeapSize()
$1 = 12480    # 还剩 12KB

# 历史最低
(gdb) p xPortGetMinimumEverFreeHeapSize()
$2 = 8192     # 最紧张时 8KB

# 堆池地址（heap_4）
(gdb) p ucHeap
$3 = (uint8_t[16384]) @ 0x20004000
```

### 检查栈溢出（0xA5 水位线）

```bash
# 看栈底 32 字节
(gdb) x/32xb pxCurrentTCB->pxStack
0x20001800:	0xa5	0xa5	0xa5	0xa5	0xa5	0xa5	0xa5	0xa5
0x20001808:	0xa5	0xa5	0xa5	0xa5	0x48	0x65	0x6c	0x6c
                ↑ 被踩了！正常应该全是 0xa5
```

### 栈溢出 Hook 断点

```bash
# 在溢出处理函数打断点
(gdb) break vApplicationStackOverflowHook

(gdb) continue
# 触发后

(gdb) backtrace
#0  vApplicationStackOverflowHook
#1  vTaskSwitchContext
#2  PendSV_Handler

(gdb) p pxCurrentTCB->pcTaskName
$1 = "sensor_task\000..."    # 肇事者
```

---

## 五、断点与观察点

### 函数断点

```bash
# 在任务函数打断点
(gdb) break high_task
Breakpoint 1 at 0x8000189

# 在库函数打断点
(gdb) break xTaskNotifyGive
(gdb) break xQueueSend

# 带条件的断点
(gdb) break main if loop_count > 100
```

### 断点命令（命中时自动执行）

```bash
(gdb) break xTaskNotifyGive
(gdb) commands 1
> p xTaskToNotify->pcTaskName
> continue
> end
```

### 硬件断点（不暂停 CPU）

```bash
# Cortex-M 支持 4-8 个硬件断点
(gdb) hbreak main
Hardware assisted breakpoint 1 at 0x8000189
```

---

## 六、内存查看

### 查看内存

```bash
# x/格式 地址
(gdb) x/16xw 0x20001b80    # 16 个字（32 位）
(gdb) x/32xb 0x20001800    # 32 个字节
(gdb) x/s 0x20001a80       # 字符串

# 格式：x(十六进制) d(十进制) u(无符号) t(二进制) c(字符) s(字符串)
# 大小：b(字节) h(半字) w(字) g(双字)
```

### 修改变量

```bash
# 直接赋值
(gdb) set var sensor_value = 100

# 强制返回
(gdb) return

# 调用函数
(gdb) call vTaskDelete(NULL)
```

---

## 七、调试纪律

### ⚠️ 断点会改变时序

- 实时任务调试时，断点暂停会让其他任务"饿死"
- 观察到的行为可能失真
- **对策**：用 `info tasks` 看任务状态，不要长时间暂停

### ⚠️ 看门狗会咬人

- 调试暂停时 TWDT 可能超时复位
- **对策**：调试前禁用看门狗或延长超时

```bash
# 代码中禁用（调试时）
#define configTASK_WDT_TIMEOUT_MS   0    // 禁用
```

### ⚠️ 栈内容会变

- 每次暂停看到的栈顶不同
- **对策**：多抓几次，找规律

### ✓ 用 watchpoint 抓变量

- `watch sensor_value` → 值变化时自动暂停
- 比断点更精准

---

## 八、常见场景速查

### 场景 1：任务不运行

```bash
# 1. 看当前任务是谁
(gdb) p pxCurrentTCB->pcTaskName

# 2. 看任务状态
(gdb) info tasks    # 或串口 vTaskList

# 3. 在任务函数打断点
(gdb) break my_task
(gdb) continue
```

### 场景 2：通知丢失

```bash
# 1. 查看通知值
(gdb) p pxCurrentTCB->ulNotifiedValue[0]

# 2. 设 watchpoint
(gdb) watch pxCurrentTCB->ulNotifiedValue[0]
(gdb) continue

# 3. 看谁在发通知
(gdb) backtrace
```

### 场景 3：堆溢出

```bash
# 1. 查看堆剩余
(gdb) p xPortGetFreeHeapSize()

# 2. 在分配失败处打断点
(gdb) break pvPortMalloc
(gdb) commands 1
> if xWantedSize > xPortGetFreeHeapSize()
>   printf "Alloc failed: %u bytes\n", xWantedSize
>   backtrace
> end
> continue
> end
```

### 场景 4：栈溢出

```bash
# 1. 在溢出 hook 打断点
(gdb) break vApplicationStackOverflowHook
(gdb) continue

# 2. 看谁溢出了
(gdb) p pxCurrentTCB->pcTaskName

# 3. 看栈底有没有被踩
(gdb) x/32xb pxCurrentTCB->pxStack
```

---

## 九、QEMU 替代（无硬件时）

```bash
# 安装 QEMU
sudo apt install qemu-system-arm

# 跑固件
qemu-system-arm -M stm32vldiscovery -kernel build/firmware.elf -s -S

# 另开终端，GDB 连接
arm-none-eabi-gdb build/firmware.elf
(gdb) target remote :1234

# 所有命令与真实硬件一致
```

**注意**：QEMU 模拟的栈内容可能与真实硬件略有差异，但 GDB 命令与证据链一致。

---

## 十、参考链接

- [GDB 官方文档](https://sourceware.org/gdb/documentation/)
- [FreeRTOS-Kernel 仓库](https://github.com/FreeRTOS/FreeRTOS-Kernel)
- [OpenOCD 文档](https://openocd.org/doc/doxygen/html/index.html)
- [QEMU ARM 文档](https://www.qemu.org/docs/master/system/target-arm.html)

> **FreeRTOS-GDB 插件已从上游移除**，所以本表不再引用它。2026-10-25 实测：`tools/pc/FreeRTOS_GDB_Plugin/freertos.py` 在 `main` 与 `V10.4.3` / `V10.5.1` / `V11.1.0` 上均返回 404（这条死链是外链巡检门第一次跑时抓出来的）。
> 要看内核对象布局，用第二节那几条 `pxCurrentTCB` / `xTasks` 的原生 GDB 命令，配合第六节的内存查看即可，不依赖任何插件。

---

**编制者**：____  
**日期**：____-__-__
