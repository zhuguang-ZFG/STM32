# S5《SysTick：内核的心跳》事实底稿

本文件是 `video/episodes/s5-systick/episode.json` 的上屏数字对账底稿。所有输出行都从**本次**运行
`.temp/v2-facts/s5-probe.log` 原样复制，不转述旧结论；旧的对账脚本 `.temp/s5-numbers.mjs`
只用来提醒「哪些 token 曾经出现过」，每个 token 都在下面重新落到本次日志行。

## 1. 取证信息

| 项 | 值 |
|---|---|
| 源文档 | `docs/stm32/05-systick.md` |
| 取证脚本 | `code/stm32/05-systick/probe.sh`（调用 `probe.c`） |
| 运行命令 | `(cd code/stm32/05-systick && sh probe.sh) > .temp/v2-facts/s5-probe.log 2>&1` |
| 退出码 | `0`（`.temp/v2-facts/s5-probe.exit` 内容为 `0`） |
| 本次日志 | `.temp/v2-facts/s5-probe.log`（28 行） |
| 宿主工具链 | `gcc 16.1.0` |
| 交叉工具链 | `arm-none-eabi-gcc 10.3.1`（本次在 PATH 中，交叉段真的跑了，不是跳过） |
| 宿主断言 | `HOST_ASSERTS=42`，`[宿主] 断言通过 42/42` |
| 上屏数字审计 | `npm run video:numbers -- s5-systick` → `✅ s5-systick: 89 个数字都有依据`（codeLabel 已纳入） |

交叉段实际执行的命令（`probe.sh` 第 2 段）：

```bash
arm-none-eabi-gcc -mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard \
  -std=c11 -Wall -Wextra -Werror -O2 -c probe.c -o build/probe-arm.o
arm-none-eabi-size build/probe-arm.o
arm-none-eabi-objdump -d build/probe-arm.o | grep -E "16777215|0xff, 0xff, 0xff|movw|movt" | head -6
```

## 2. 本集必须回答的 5 个问题

1. 写 `167999` 还是 `168000`？为什么重载次数一模一样，一天却差 514 毫秒？
2. `CTRL/LOAD/VAL/CALIB` 四个寄存器各管什么？为什么 `COUNTFLAG` 读一次就没了？
3. 24 位的 `LOAD` 装不下 100 ms 时，`SysTick_Config` 怎么失败？不查返回值会怎样？
4. 毫秒计数回绕时，为什么无符号减法是安全的，而 `now >= then + timeout` 会漏报？
5. SysTick 的优先级为什么必须压到最低？它和 RTOS 调度器、串口接收中断是什么关系？

## 3. 上屏数字逐项对账

> 场景写法：`B:` = bilibili，`D:` = douyin，`封面` = 主封面/平台封面，`发行` = publish 文案。
> 同一行日志里的多个 token 共用一个证据行；每个 token 都列出它实际出现的场景。

### 3.1 寄存器版图（probe `[1]`）

命令：`sh probe.sh`（宿主段）

```text
[1] 布局：CTRL/LOAD/VAL/CALIB 偏移 = 0x0/0x4/0x8/0xC，SysTick_BASE = 0xE000E010（内核外设，所有 Cortex-M 通用）
```

| 上屏 token | 场景 |
|---|---|
| `0x0` | B: card-01, code-01, code-02；D: card-01；封面；发行（B站/抖音/小红书/知乎） |
| `0x4` | B: card-01, code-01, code-02；D: card-01；封面；发行（B站/抖音/小红书/知乎） |
| `0x8` | B: card-01, code-01, code-02；D: card-01；封面；发行（B站/抖音/小红书/知乎） |
| `0xC` | B: card-01, code-01, code-02；D: card-01；封面；发行（B站/抖音/小红书/知乎） |
| `0xE000E010` | B: card-01, code-01；D: card-01；封面；发行（B站/抖音/小红书/知乎） |

### 3.2 168 MHz 的三个 LOAD 值（probe `[2]`）

```text
[2] 168MHz：1ms → LOAD=167999，100us → LOAD=16799，10ms → LOAD=1679999（= 周期周期数-1）
```

| 上屏 token | 场景 |
|---|---|
| `168MHz` | B: code-01, card-03, code-05, card-04；D: card-03；发行（B站/小红书） |
| `1ms` | B: code-01, card-03, code-05, card-04；D: card-03, card-04；发行（B站/抖音/小红书） |
| `167999` | B: hook-01, code-01, card-03, code-05, card-06, code-13, punch；D: hook-01, card-03, punch；发行（B站/抖音/小红书/知乎） |
| `100us` | B: code-01, card-03, code-05, code-09；发行（B站） |
| `16799` | B: code-01, card-03, code-05, code-09；发行（B站） |
| `10ms` | B: code-01, card-03, code-05；发行（B站） |
| `1679999` | B: code-01, card-03, code-05；发行（B站） |
| `-1` | B: code-01, code-05, code-13（`周期周期数-1` 与 `(1<<4)-1` 的同一个减一） |

### 3.3 重载次数与相位（probe `[3]`）

```text
[3] 模型：LOAD=167999 跑 1680000 周期 → 归零重载 10 次（周期 = LOAD+1 = 168000 周期 = 1.000000ms）
    忘减一：同跑 1680000 周期两者都重载 10 次——差别不在次数在相位；每个 tick 慢 1/168000（5.95ppm），日漂移 514ms
    相位：第 10 次重载——正确配置在第 1512001 个时钟，忘减一在第 1512010 个，9 个间隔共欠 9 个时钟
```

| 上屏 token | 场景 |
|---|---|
| `1680000` | B: hook-01, card-03, code-05, code-06；D: card-03, code-06；封面；发行（B站/抖音/小红书） |
| `10` | B: hook-01, card-03, code-05, code-06；D: hook-01, card-03, code-06；封面；发行（B站/抖音/小红书） |
| `1.000000ms` | B: code-05 |
| `168000` | B: hook-01, card-03, code-05, code-06, card-06；D: hook-01, card-03；发行（B站/抖音/小红书/知乎） |
| `5.95ppm` | B: code-06；D: code-06；发行（B站/小红书） |
| `514ms` | B: hook-01, code-06, punch；D: hook-01, code-06, punch；封面；发行（B站） |
| `514` | B: hook-01, code-06, punch, cta；D: hook-01, code-06；封面；发行（B站/抖音/小红书/知乎） |
| `1512001` | B: code-06；D: code-06；发行（B站） |
| `1512010` | B: code-06；D: code-06；发行（B站） |
| `9` | B: code-06；D: code-06 |

### 3.4 24 位上限与拒配（probe `[4]`）

```text
[4] 24 位上限：LOAD 最大 16777215（0xFFFFFF）→ 最长单次 99864us（≈99.86ms，1ms tick 无压力，100ms 单次不行）
    请求 100ms（ticks=16800000）：SysTick_Config 返回 1 拒配；若强行 &0xFFFFFF → LOAD=22783，tick 变成 135.6us，ISR 狂跳 737 倍速
```

| 上屏 token | 场景 |
|---|---|
| `24` | B: card-04, code-07, punch；D: card-04, punch；封面；发行（B站/抖音/小红书/知乎） |
| `16777215` | B: card-04；D: card-04；发行（B站） |
| `0xFFFFFF` | B: card-04, code-08；D: card-04, code-08；发行（B站/小红书） |
| `99864` | B: card-04, cta；D: card-04 |
| `99864us` | B: card-04；D: card-04；发行（B站） |
| `99.86` | B: card-04 |
| `99.86ms` | B: card-04；D: card-04；发行（B站） |
| `100ms` | B: card-04, code-07；D: card-04, code-08；封面；发行（B站/抖音/小红书） |
| `16800000` | B: code-07；D: code-08 |
| `100` | B: code-04（`sim_run(&b, 100UL)` 的模型长度）、card-04（“100 毫秒”）、code-07（100ms 的数值） |
| `22783` | B: code-08, code-09；D: code-08；发行（B站） |
| `135.6` | B: code-08 |
| `135.6us` | B: code-08；D: code-08；发行（B站/小红书） |
| `737` | B: code-08, punch, cta；D: code-08, punch；封面；发行（B站/抖音/小红书） |

注：`100` 是 `100ms` 的数值部分，证据行同上；`code-04` 里的 `100UL` 是模型运行 100 个时钟的循环上界，
不是测量结论，删掉不影响断言。

### 3.5 换算与回绕（probe `[5]`）

```text
[5] 换算：1 周期 = 125/21 ns ≈ 5.952ns；整数公式 ns=c*1000/168：c=1 → 5ns、c=168 → 1000ns=1us（整 us 无损）、c=1000 → 5952ns=5.952us（按整数 us 取 5us，丢 0.952us）
    回绕：uint32_t ms 计数 49.7 天绕一圈；then=0xFFFFFC18 now=5000 → (now-then)=6000ms（无符号减法跨回绕正确）；而 now>=then+timeout 在 now=2000 时漏报未超时
```

| 上屏 token | 场景 |
|---|---|
| `125` | B: card-05 |
| `21` / `21ns` | B: card-05；`21ns` 另见 B: code-10 |
| `5.952` / `5.952ns` | B: card-05；`5.952ns` 另见 B: code-10 |
| `5952ns` / `5.952us` / `0.952us` / `0.952` | B: code-10（code 与旁白） |
| `1000ns` / `1us` | B: code-10 |
| `168` | B: card-03, card-04, card-05, code-10；发行（B站） |
| `1000` | B: card-05, code-10, code-12；发行（B站） |
| `5ns` | B: card-05, code-10；发行（B站） |
| `5us` | B: code-10；发行（B站） |
| `49.7` | B: card-05, code-11, punch, cta；D: code-11, punch；发行（B站/抖音/小红书/知乎） |
| `0xFFFFFC18` | B: code-11, code-12；D: code-11 |
| `5000` | B: code-11, code-12；D: code-11 |
| `6000` | B: code-09（objdump 里的 `#6000`）, code-11, code-12 |
| `6000ms` | B: code-11；D: code-11 |
| `2000` | B: code-11；D: code-11 |

注：`49.7 天` 是 `2^32 ms` 的算术结论（`4294967296 / 86400000 = 49.71…`），由模型算出，不是板上连续观察 49.7 天。旧版把 1000 周期写成「5us 无损」，本次修正为「1000 周期 = 5.952us；5us 是整数微秒截断」。整微秒无损的例子是 168 周期 = 1000ns。

### 3.6 Config 全貌与优先级（probe `[6]`）

```text
[6] SysTick_Config(168000)：LOAD=167999 VAL=0 CTRL=0x00000007，SHP[11]=0xF0 → 逻辑优先级 15（4 位里的最低档，RTOS 就要它在最低）
```

| 上屏 token | 场景 |
|---|---|
| `0x7` | B: card-06, code-13；发行（B站） |
| `0xF0` | B: card-06, code-13；发行（B站/小红书） |
| `11` | B: card-06, code-13；发行（B站/小红书） |
| `15` | B: card-06, code-13, code-14；发行（B站/小红书） |
| `4` | B: code-07（probe 段号）, card-06（“4 位里的最低档”）, code-13（`(1<<4)-1`）；封面（4 个寄存器）。注：这里的 4 不是 `[4]` 段的读数，语义分别来自 `[6]` 与位宽 |
| `0` | B: code-04（循环下标）, card-03, code-09（data 0）, code-12, card-06（`VAL=0`）, code-13, card-07；发行（B站/抖音/小红书） |

### 3.7 COUNTFLAG 读清（probe `[7]`）

```text
[7] COUNTFLAG：周期到后第一次读 CTRL=0x00010005（有标志），紧接第二次读=0x00000005（标志已被上一次读清掉）
    对照：5 个周期里单读法数到 5 次；「先偷看再查」双读法数到 0 次
```

| 上屏 token | 场景 |
|---|---|
| `0x00010005` | B: code-03；D: code-03；发行（B站/小红书） |
| `0x00000005` | B: code-03；D: code-03；发行（B站/小红书） |
| `5` | B: code-03, code-04, code-10, card-07；D: code-03；发行（B站/抖音/小红书） |
| `16` | 寄存器位号（bit16 COUNTFLAG），见 `docs/stm32/05-systick.md:94`；probe `[7]` 只打印 `0x00010005`，不打印 `16`。归入 `exceptions`，不是测量值 |

### 3.8 交叉编译（probe 第 2 段）

命令见 §1。

```text
交叉工具链：10.3.1
   text	   data	    bss	    dec	    hex	filename
   3361	      0	      8	   3369	    d29	build/probe-arm.o
  3a:	f244 129f 	movw	r2, #16799	; 0x419f
  b6:	f240 2202 	movw	r2, #514	; 0x202
 1a8:	f645 01ff 	movw	r1, #22783	; 0x58ff
 1d2:	f241 7670 	movw	r6, #6000	; 0x1770
```

| 上屏 token | 场景 |
|---|---|
| `10.3.1` | B: code-09 |
| `3361` | B: code-09；发行（B站） |
| `3369` | B: code-09 |
| `0xd29` | B: code-09（屏上注释把原表的 `d29` 补成 `0xd29`，已明示是改写）；B 站简介未写 hex 列 |
| `8` | B: code-09（bss 列）；发行（B站） |
| `0x419f` | B: code-09 |
| `0x58ff` | B: code-09 |
| `0x1770` | B: code-09 |
| `16799` / `22783` / `6000` | B: code-09（同时出现在 objdump 操作数与 size 段） |

注：`movw r2, #514`（`0x202`）也在日志里，但正片没有用它，不加进 numbers JSON。
`size` 的 hex 列原样是 `d29`（GNU size 不带 `0x`）；屏上照抄原表，并加一行「d29 就是 0xd29」，
审计按 `0xd29` 记账，不把补前缀当成原始输出。

### 3.9 工具链版本、断言总数与发行文案

```text
宿主工具链：gcc 16.1.0
HOST_ASSERTS=42
[宿主] 断言通过 42/42
```

| 上屏 token | 场景 |
|---|---|
| `16.1.0` | B: code-01；发行（B站 intro） |
| `42` | B: route-01, code-01, cta；D: route-01；封面；发行（B站/抖音/小红书/知乎） |

### 3.10 编号/下标类 token（非测量）

以下 token 是 probe 段号、循环下标或章号，不是读数；它们在本次日志里有对应的 `[N]` 段，故仍可追溯：

| 上屏 token | 场景与含义 |
|---|---|
| `1` | probe `[1]` 段号；`LOAD+1`；`(ticks - 1UL)`；`(1<<4)-1`；封面 1 个条件。B: code-01, code-02, card-03, code-05, code-06, code-07, card-05, code-10, code-13, punch；D: card-03, code-08, punch；封面；发行 |
| `2` | probe `[2]` 段号。B: code-01, code-05 |
| `3` | probe `[3]` 段号。B: code-01, code-05；封面 |
| `5` | probe `[5]` 段号；也见 3.7 的 `5 次`。B: code-03, code-04, code-10, card-07；D: code-03；发行 |
| `6` | probe `[6]` 段号。B: code-13 |
| `7` | probe `[7]` 段号。B: code-01（“到 [7] 是后面五节”） |

## 4. 不能删的技术断言（删了会让章节断链）

1. **寄存器版图与基址**：`CTRL/LOAD/VAL/CALIB` 偏移 `0x0/0x4/0x8/0xC`，基址 `0xE000E010`；
   SCS 属 ARM 内核，不是 STM32 私有。删掉这条，后文所有寄存器操作失去坐标。
2. **周期 = LOAD + 1**：168 MHz 下 `1ms → 167999`。删掉这条，514 ms 漂移与相位差全部无源。
3. **忘减一只亏相位、不亏次数**：同跑 1680000 周期都重载 10 次，第 10 次分别落在
   1512001 / 1512010；每 tick 慢 1/168000（5.95ppm）。这是本集的“反直觉钩子”，不能删。
4. **24 位硬顶**：`LOAD` 最大 16777215；单次最长 99864us；请求 100ms 时 `SysTick_Config`
   返回 1 且**一个寄存器都不写**；强行 `&0xFFFFFF` 得 LOAD=22783、135.6us、737 倍速。
   删掉这条，工程里“不查返回值”的后果就没有证据。
5. **COUNTFLAG 读清**：第一次读 `0x00010005`、第二次读 `0x00000005`；单读法 5 次、双读法 0 次。
   删掉这条，中断里“先偷看再判断”的坑讲不成。
6. **回绕先减再比**：`(uint32_t)(now - then)` 跨回绕得 6000ms；`now >= then + timeout`
   在 now=2000 时漏报未超时。删掉这条，超时模板与 S9/F 篇的复用链断掉。
7. **优先级 15 是最低档**：`SysTick_Config(168000)` 写 `CTRL=0x7`、`SHP[11]=0xF0`；
   15 = `(1<<4)-1`，4 位里的最低。删掉这条，与 S4“数字越小越优先”的章节链断掉。
8. **同一份源码进 Cortex-M4 目标文件**：text 3361 / data 0 / bss 8，`movw #16799/#22783/#6000`
   真的在机器码里。删掉这条，“宿主机模型不是纸上算术”的证明就没了。

## 5. 已知未取证项（明确「不上屏」）

| 项 | 状态 | 处理 |
|---|---|---|
| 逻辑分析仪夹 PF6 测 tick 翻转周期得出的百分比 | 需要真板子与逻辑分析仪；本轮板子不在位 | **不上屏**：正片只保留接线/命令的弱化提示，不给百分数，不写具体读数 |
| 双读法在真实开发板上的复现 | 本轮只在本机模型上验证（单读 5 次、双读 0 次） | **不上屏**：不写“板上复现”，发行文案明确写“不是板上复现过” |
| 切到参考时钟（HCLK/8）后的实际周期 | 数据手册有写，本轮未测 | **不上屏**：正片只说“数据手册写的、本集没测”，屏上弱化、不给数 |
| 32 位定时器替代方案的实际效果 | 属于“定时器那一章”的范围，本轮未测 | **不上屏**：只作为章节路标出现，`32` 在 numbers JSON 里列为 exceptions，不是测量值 |
| 49.7 天连续运行 | 由 `2^32 ms` 算术推得（49.71…），不是连续观察 | 可上屏，但口径是“算术结论”；不说“实测 49.7 天” |
| 板上真实中断延迟/抖动 | 本轮无板 | **不上屏**：不出现具体 ns/us 延迟数字 |

## 6. 与旧对账的关系

- 起点：`.temp/s5-numbers.mjs` 曾把多位数字与 `.trellis/tasks/10-17-s5-systick-episode/research/probe-20261017-1705.md` 对账；
  本文件不复用那份日志的结论，所有行来自本次 `.temp/v2-facts/s5-probe.log`。
- `npm run video:numbers -- s5-systick` 的口径比旧脚本更严：十六进制按数值规范化（`0x00000005` → `0x5`），
  单位大小写不敏感，中文逗号会归一化成 ASCII 逗号。正片已避开 `数字，数字` 的写法（改用 `；`），
  避免两个数被并成一个 token。
- `14`（F3 集号）、`32`（位宽类型）、`05`（章节路径号）在 `s5-systick-numbers.json` 的 `exceptions` 里，
  明确标注“不是测量值”，不冒充 probe 读数。
- `codeLabel` 自 Task 10 起纳入审计。`core_cm4.h:764-770` 与 `probe.c:249-257` 的行号是源码位置，
  `249/257/764/770` 在 `exceptions` 里标注为“源码行号，不是测量值”。
- `16`（bit16 COUNTFLAG）同理：它是寄存器位号，probe 只打印 `0x00010005`，不打印 `16`，
  因此放在 `exceptions` 而不是 `evidence`，避免拿十六进制输出冒充位号出处。
