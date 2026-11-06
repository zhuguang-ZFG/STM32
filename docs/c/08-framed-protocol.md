---
title: C8 串口协议：从字节流到可恢复的消息
status: done
difficulty: 3
minutes: 55
---

# C8 串口协议：从字节流到可恢复的消息

> 🎯 UART 只保证"字节按顺序到"，从不告诉你一条命令在哪结束。丢一个字节之后，下一帧还认得出来吗？

## 本章精髓

1. **帧边界要协议自己画**：UART_DATA 事件、IDLE 中断、一次 `read()` 拿到多少字节，都不是一条命令的边界。COBS 把数据里的 0 全部换掉，让 0x00 只当帧尾，丢字节后等到下一个 0 就能重新对齐。
2. **每道检查只管一件事**：CRC 管随机损坏，管不了篡改；序号只用来配对响应，不是安全凭据；所有检查都通过之前，不往调用方的输出里写一个字节。
3. **失败要有出口和计数**：超时、超长、已知丢字节一律进 DISCARD，八种结局各自计数；发送队列满了丢新帧并计数，确认帧发不出去就不执行命令。"出错后仍知道发生了什么"靠的就是这些计数。

- **能理解**：EMPTY 态收到 0 为什么什么都不做；transport loss 之后为什么第一帧可能被牺牲；为什么"确认帧入队失败"等于"命令不执行"。
- **能用**：主机上用分块、粘包、错误流跑生产 codec；用 `device-console.py` 在两块板上查 INFO/STATUS。

## 先修

- 必需：[C5 函数指针与状态机](05-func-pointer.md)（状态机、环形缓冲）、[S7 USART](../stm32/07-usart.md)（波特率、IDLE+DMA）。
- 建议：[S8 DMA](../stm32/08-dma.md)、[P5 UART 驱动解析](../esp32/05-uart-driver.md)。

## 先跑起来（10 分钟 quick win）

在仓库根执行：

```sh
sh code/common/reliability/probe.sh
```

跑之前先押开场那一问：往字节流中间丢一个字节，接收端是从此再也对不上，还是能重新找回边界？若能找回，第一帧是完好无损，还是先被牺牲？答案就藏在下面的断言里。

脚本用 `-std=c11 -Wall -Wextra -Werror` 编译生产用的 codec/health/transport/service，跑 `tests.c` 的边界断言；再编一个 `codec-tool`，交给 `scripts/device-console.py self-test` 和独立的 Python 实现互相编解码。在 Linux 上还会加跑一遍 ASan/UBSan。看到下面两行就算通过，不需要串口库和开发板：

```text
protocol, health, TX/RX backpressure, service and reset-record tests passed
self-test passed: codec vectors + session matching + sync/retry + C cross-validation
```
## 动画：逐字节解析状态机

字节流如何变成可恢复的消息：EMPTY → COLLECT → 验证 → DISCARD 的每一步，游标沿字节流连续前进、状态随之切换，坏帧路径与重新同步一图看完。

![C8 帧协议：逐字节解析状态机与重新同步](/anim/c08-frame-parse.svg)

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| 一、为什么要定界 | 长度前缀 / 转义 / COBS 三种定界法的失步代价 | 配置 |
| 二、帧布局与容量 | 6+N+2 字节逐字段、74 字节上限从哪来 | 配置 |
| 三、CRC-16/CCITT-FALSE | 四个参数、逐位实现、独立实现交叉验证 | 库解析 |
| 四、COBS 手算一帧 | seq=7 的 INFO 请求逐字节编码，解码的四个拒绝条件 | 代码分析 |
| 五、接收状态机 | 三态、八计数、超时回绕、丢失后的第一帧 | 代码分析 |
| 六、两板的字节来源 | F407 DMA 环形 + 字节队列；S3 驱动环形 + 周期取数 | 引脚 |
| 七、发送与背压 | 4 槽 TX、部分写、100ms 放弃与补同步零 | 代码分析 |
| 八、服务层与主机 | 响应配对、INFO/STATUS 布局、确认先于执行 | 库解析 |

## 一、为什么要定界：一次 read 不是一条命令

UART 硬件只管一个字节：起始位、8 个数据位、停止位。它不知道哪几个字节组成一条命令。驱动层给的 UART_DATA 事件、IDLE 中断、`read()` 返回的长度，都只说明"此刻手里有这些字节"。主机一次写出的命令可能分三次到，三条命令也可能一次全到。[S7](../stm32/07-usart.md) 的波形和 [P5](../esp32/05-uart-driver.md) 的驱动源码都演示过这一点。

所以边界必须由协议写进字节流本身。常见的三种做法：

| 定界法 | 做法 | 丢一个字节之后 |
|---|---|---|
| 长度前缀 | 帧头写"后面还有 N 字节" | 长度字段本身错位，之后每一帧都按错的长度切，一路错下去；得再加魔数和超时才能找回同步 |
| 转义（SLIP/HDLC） | 保留一个帧标志字节，数据里出现它就转义成两字节 | 等到下一个帧标志就重新对齐；但最坏情况数据长度翻倍 |
| COBS | 把数据里的所有 0 换掉，0x00 只当帧尾 | 等到下一个 0 就重新对齐；开销固定，每 254 字节最多多 1 字节 |

本协议的 raw 最长 72 字节，小于 254，COBS 开销恒为 1 字节，缓冲区大小可以在编译期写死并用 `_Static_assert` 锁住。选 COBS 的理由就是这两条：能重新同步，最坏开销可以提前算进预算。

## 二、帧布局与容量

raw 帧共 8+N 字节，多字节字段都是小端：

| 偏移 | 字段 | 长度 | 含义 |
|---|---|---|---|
| 0 | version | 1 | 固定为 1；解码见到别的值就报 VERSION，给将来改格式留余地 |
| 1 | type | 1 | 最高位 0=请求、1=响应（请求类型 \| 0x80）；设备收到响应型帧直接忽略，两边不会互相回声 |
| 2 | sequence | 2 | 主机递增，设备原样带回，主机靠它配对响应 |
| 4 | length | 2 | 负载长度 0~64 |
| 6 | payload | N | 负载 |
| 6+N | crc | 2 | CRC-16/CCITT-FALSE，覆盖偏移 0 到 5+N 的全部字节 |

解码时要求 COBS 还原出的字节数**恰好等于** length+8，多一个少一个都报 LENGTH。容量一路推下来：raw 最大 6+64+2=72，COBS 后 73，加帧尾 0x00 共 74。三个数在 `protocol.h` 里是 `PROTOCOL_RAW_MAX / ENCODED_MAX / WIRE_MAX`，`protocol.c` 开头的两条 `_Static_assert` 把它们和布局绑在一起。

响应的状态字节也占负载容量。INFO、STATUS 的 payload[0] 就是状态码，不能把它当成 64 字节之外的"额外一字节"。

多字节字段一律显式移位读写，不把 `frame_t` 直接 `memcpy` 上线：

```c
uint16_t read_le16(const uint8_t *p) { return (uint16_t)((uint16_t)p[0] | (uint16_t)p[1]<<8); }
void write_le16(uint8_t *p, uint16_t v) { p[0]=(uint8_t)v; p[1]=(uint8_t)(v>>8); }
```

结构体的填充和端序由编译器和 ABI 决定（[C4](04-struct-abi.md)）。直接发结构体内存，等于让编译器替你定了一份没写在任何地方的协议。

![raw 帧布局：version、type、sequence、length、payload、CRC-16 共 8+N 字节，COBS 编码后以 0x00 收尾；每 254 字节最多多 1 字节开销](/figures/c-08-framed-protocol.svg)

## 三、CRC-16/CCITT-FALSE：先把名字叫全

"CRC-16"不是一个算法，而是一族算法。要确定是哪一个，得给全多项式、初值、是否反转输入输出、结果是否再异或这几个参数。本协议用的是：

| 参数 | 值 |
|---|---|
| 多项式 | 0x1021 |
| 初值 | 0xFFFF |
| 输入/输出反转 | 都不反转 |
| 结果异或 | 0x0000 |
| 检查值（ASCII `123456789`） | **0x29B1** |

检查值就是验收标准：哪个实现对 `123456789` 算出 0x29B1，才和本协议一致。`protocol.c` 用逐位实现，没有查表，72 字节以内一帧只需要几百次循环：

```c
uint16_t protocol_crc(const uint8_t *data, size_t n)
{
    uint16_t crc=0xffffU;
    for (size_t i=0;i<n;i++) {
        crc ^= (uint16_t)((uint16_t)data[i]<<8);          /* 新字节对齐到高 8 位 */
        for (unsigned bit=0;bit<8;bit++)
            crc=(uint16_t)((crc&0x8000U) ? ((uint32_t)crc<<1)^0x1021U : (uint32_t)crc<<1);
    }
    return crc;
}
```

主机侧的 `device-console.py` 没有照抄这段 C，而是用 Python 标准库的 `binascii.crc_hqx(data, 0xFFFF)`。这是一份参数相同、但独立写成的实现，两边互相校验，才能排除"同一个 bug 写了两遍"。`tests.c` 和 `self-test` 都先断言检查值 0x29B1。

CRC 的边界要说清：

- 它能检出随机损坏（单比特错、突发错），**防不住有意篡改**：改了数据的人顺手重算一遍 CRC 就行。要防篡改得用带密钥的 MAC。
- 它覆盖的是 COBS **之前**的 raw 字节，所以接收端的顺序是先 COBS 解码、再验 CRC。

## 四、COBS 手算一帧

COBS 的规则：把数据按 0 切成若干段，每段前面放一个"段长+1"的码字，原来的 0 不再出现在输出里。

以主机发出的第一条请求为例：INFO（type=0x01），seq=7，无负载。

**第 1 步，拼 raw。** `01 01 07 00 00 00`，依次是 version、type、seq 低字节、seq 高字节、length 低字节、length 高字节。

**第 2 步，算 CRC。** 对这 6 字节算出 0xB0CC，小端追加，raw 变成 8 字节：

```text
01 01 07 00 00 00 CC B0
```

**第 3 步，按 0 切段，加码字。**

| 段 | 内容 | 码字 = 段长+1 |
|---|---|---|
| 1 | `01 01 07` | 04 |
| 2 | （空，两个 0 之间） | 01 |
| 3 | （空） | 01 |
| 4 | `CC B0`（帧末） | 03 |

**第 4 步，拼起来，加帧尾。**

```text
04 01 01 07 01 01 03 CC B0 00
```

10 字节 = 8 raw + 1 COBS 开销 + 1 帧尾，和第二节的公式一致。可以在仓库根用 Python 复核：

```sh
python3 -c "import importlib.util as u;s=u.spec_from_file_location('d','scripts/device-console.py');d=u.module_from_spec(s);s.loader.exec_module(d);print(d.build_frame(1,7,b'').hex(' '))"
# 04 01 01 07 01 01 03 cc b0 00
```

解码倒过来走：读码字 c，原样拷贝后面 c-1 字节；c 不等于 255 且后面还有数据时，补一个 0。`protocol_cobs_decode` 有四个拒绝条件，任何一个成立就返回 0：

```c
if (!code || (size_t)(code-1)>n-in) return 0;   /* 码字为 0，或声称的段长超过剩余字节 */
...
if (!src[in] || out==capacity) return 0;        /* 段内出现 0，或输出已满 */
```

段内出现 0 说明这一段被截断或拼接过，长度对不上说明有字节丢了。两种情况都不能"尽量解出一点"。

`protocol_decode` 在 COBS 之后依次检查：字节数 ≥8 → version==1 → length≤64 且字节数恰为 length+8 → CRC。全部通过才写 `frame_t`：

```c
/* Publish only after every check. A rejected frame leaves the caller's output untouched. */
f->type=raw[1]; f->sequence=read_le16(raw+2); f->length=length;
```

`tests.c` 专门验证了这一点：先放一个 `type=99` 的哨兵帧，喂进 VERSION/LENGTH/CRC 三种坏帧，断言哨兵原封不动。

## 五、接收状态机：三个状态，八个计数

`protocol_rx_feed` 每次吃一个字节。状态转移如下：

| 当前状态 | 收到 | 动作 | 计数 |
|---|---|---|---|
| EMPTY | 0x00 | 什么都不做 | — |
| EMPTY / COLLECT | 非零，缓冲未满 | 存入缓冲，记下 `last_ms`，进 COLLECT | — |
| COLLECT | 非零，缓冲已满 73 字节 | 清空，进 DISCARD | oversize |
| COLLECT | 0x00 | 调 `protocol_decode`，回 EMPTY | ok / cobs / version / length / crc 之一 |
| COLLECT | 距 `last_ms` ≥100ms 后的任意字节 | 先超时：清空，进 DISCARD | timeout |
| DISCARD | 非零 | 吞掉 | — |
| DISCARD | 0x00 | 回 EMPTY | — |
| 任意 | 传输层报丢失 | 清空，进 DISCARD | transport_loss |

几处值得逐行看的细节：

- **EMPTY 收 0 不计数是有意的。** 主机重试前会多发一个 0x00 做同步。如果它落在 EMPTY 态，只是个空操作，不会污染错误统计。
- **超时用无符号减法判断**：`(uint32_t)(now-rx->last_ms)>=rx->timeout_ms`。毫秒计数回绕时差值仍然正确。`tests.c` 从 `UINT32_MAX-50` 起跑，分别验证间隔 99、100、101ms：99 能收到完整帧，100 和 101 计一次 timeout；紧接着的下一帧仍能收到，因为超时帧自己的帧尾 0 把 DISCARD 结束了。
- **超时按适配层看到字节的时间算。** F407 的一次 DMA 中断可能一下子交出几十个字节，它们共用同一个 `now`。100ms 量的是"解析器多久没收到新字节"，不是线上每个字节的物理到达时间。
- **计数器是饱和加法** `sat_add`：加到 `UINT32_MAX` 就停住，不会回绕成 0，把"错过很多次"伪装成"从没错过"。

### 丢失之后，第一帧为什么可能被牺牲

传输层确认丢了字节时，会调 `protocol_rx_loss`，解析器进 DISCARD，等下一个 0。如果丢掉的恰好是上一帧的帧尾 0，那么解析器遇到的"下一个 0"其实是**下一帧**的帧尾，下一帧会被整个当成残段吞掉。

所以主机侧的规矩是：info/status 有限重试，每次重试前先单独发一个 0x00。那个 0 落在 DISCARD 态，就提前结束了丢弃；落在 EMPTY 态，就是空操作。

### 为什么丢失必须先于新字节交付

F407 的字节队列溢出时，不是丢掉一个字节，而是把整段不确定的数据清空，并置一个 `loss` 标志。`byte_queue_pop` 先把这个标志交出去，再交新字节：

```c
bool byte_queue_pop(byte_queue_t *q, uint8_t *byte, bool *loss)
{
    *loss=q->loss; q->loss=false;
    if (!q->count) return false;
    ...
}
```

通信任务看到 `loss` 就先调 `protocol_rx_loss`，再喂这个字节。顺序反了，解析器会把溢出前的半截帧和溢出后的半截帧拼成一段。拼出来的东西 CRC 大概率不对，但"大概率"不是保证。

## 六、两板的字节来源

同一个解析器，两块板的字节从不同的路上来。

**F407：USART1 + DMA2 Stream5 环形 + 字节队列**（`code/stm32/platform/uart.c`）

- PA9 TX / PA10 RX，AF7。`BRR=139`，按复位后的 HSI16 计算，16MHz/139≈115108 波特，误差约 0.08%。`f407_uart_init` 先检查 RCC_CFGR 里时钟源和三个预分频都还是复位值，不是就返回失败，不让一个错的 BRR 静默跑起来。
- DMA 把字节搬进 256 字节环形区。HT、TC、TE 中断和 USART 的 IDLE 中断都调 `receive()`，把新到的一段推进 512 字节的 `byte_queue_t`。Stream5 的标志在 HISR 的第 10/11/9 位（HT/TC/TE），不是常被误抄的 28/29/27 位；HISR 只读，清标志写 HIFCR。
- `dma_consume` 有三种判定丢失的情况：TE；HT 和 TC 同时挂着（说明服务晚了至少半圈，数据可能已被覆盖）；位置没动却来了 TC（正好被套了一整圈）。USART 的 PE/FE/NF/ORE 也走同一条丢失路径。

**S3：IDF UART 驱动环形 + 周期取数**（`code/esp32/06-framed-protocol`）

- UART1，GPIO10 TX / GPIO11 RX，驱动的 RX 环形区 1024 字节。
- 驱动的事件队列满了只写日志，没有公开的精确计数，所以任务不能只等 UART_DATA。它每轮最多等 5ms 事件，然后不管有没有事件，都用 `uart_get_buffered_data_len` + `uart_read_bytes` 取一次数兜底；每轮最多处理 512 字节，防止 RX 洪水把 TX 饿死。
- UART_FIFO_OVF、UART_BUFFER_FULL、帧错、校验错、BREAK 都按传输丢失处理：`uart_flush_input` 清掉驱动缓冲，`xQueueReset` 清掉积压的事件，再调 `protocol_rx_loss`。

**接线**：3.3V USB-TTL，TX 接板子 RX、RX 接板子 TX，GND 共地。协议口上不混入任何 printf：F407 的调试走 SWD，S3 的文本日志走默认控制台。

## 七、发送与背压：加大数组解决不了问题

`protocol_tx_t` 只有 4 个槽，每槽 74 字节，入队时就编码好：

- **队列满了丢新帧**，`dropped` 加一，已经排着的帧不受影响。编码失败也算丢。
- `protocol_tx_step` 每轮只推进底层 `write` **实际接受**的字节数。F407 的 `f407_uart_write` 只在 TXE=1 时写 DR，写不进就返回已写的数量；S3 用非阻塞的 `uart_tx_chars`。
- **一帧发了 100ms 还没发完，就放弃剩下的部分**，计一次丢，并置 `sync`：下一帧之前先单独发一个 0x00，把对端可能残留的半帧结束掉。`sync` 初值就是 true，所以开机后的第一件事是发一个同步 0。
- `write` 返回的数量超过请求值，说明底层违反了接口约定，同样按丢失处理，不让 `offset` 越界。

```c
if ((uint32_t)(now-q->start_ms)>=100) {
    q->dropped=sat_add(q->dropped,1); tx_pop(q); q->sync=true; return;
}
```

为什么不把队列加大？加多大都会有满的时候，真正要设计的是"满了怎么办"。这里的答案是丢新帧、计数，主机靠超时重试兜底。STATUS 里的 `tx dropped` 在涨，主机就知道是设备发不出去，而不是没收到。

## 八、服务层与主机：确认先于执行

`device_service_feed` 每收到一个合法帧：

1. type 最高位是 1（响应帧）→ 忽略。
2. type 1/2（INFO/STATUS）→ 交给 `device_service_query` 组装响应；请求带了负载就回 BAD_PAYLOAD(2)。
3. type 0x7F（TEST_FAULT）→ 普通固件没有 fault 回调，回 UNSUPPORTED(1)；测试固件校验参数，不合法回 2。
4. 其他类型 → UNSUPPORTED(1)。

最关键的是最后一行：

```c
/* No accepted command side effect if its acknowledgement cannot be queued. */
if (protocol_tx_enqueue(&s->tx,&response) && invoke)
    s->fault(s->fault_user,request.payload[0],request.payload[1]);
```

反过来写会怎样？命令先执行了，确认帧因为 TX 队列满被丢掉。主机看到的是超时，以为没执行，于是重试，同一条不可重试的命令就执行了两次。主机侧也守着这条线：info/status 最多重试两次，fault 只发一次，绝不自动重试。

两种查询响应的布局（payload[0] 都是状态码，0=OK）：

| 响应 | 长度 | 字段 |
|---|---|---|
| INFO | 5 | [1] schema=1 · [2] 平台（1=F407，2=S3）· [3..4] 能力位：bit0 协议、bit1 健康监督、bit2 允许故障注入 |
| STATUS | 25 | [1] schema · [2..5] 运行毫秒 · [6..9] 复位原因原值 · [10] 必需任务 mask · [11] 过期任务 mask · [12] 标志（bit0 宽限期、bit1 已锁存重启）· [13..16] 合法帧数 · [17..20] 接收错误总数 · [21..24] TX 丢帧数 |

主机脚本 `device-console.py` 一次只挂一个请求：生成 seq，在**绝对期限**内等 type\|0x80 且 seq 相同的帧；收到无关帧只记日志，不延长期限。超时就先发 0x00，再重发。所有收发都写进 CSV 日志，事后可以复盘。

## 两板命令实操

```sh
# F407（ST-Link 烧录 build 产物）
cd code/stm32/05-framed-protocol && make

# S3（IDF 5.5.2 环境）
cd code/esp32/06-framed-protocol
idf.py set-target esp32s3 && idf.py build flash

# 主机
pip install -r scripts/device-console-requirements.txt
python3 scripts/device-console.py info   --port COMx
python3 scripts/device-console.py status --port COMx
```

`info` 打印 schema、平台号和能力位；`status` 先问 INFO 拿平台号，再打印运行状态、复位原因和三个计数。

## 附录：工程完整源码

<<< ../../code/common/reliability/protocol.c

## 记忆锚点

::: tip 一句话记住
**0 只当帧尾，CRC 只管损坏，序号只管配对；失步就等下一个 0，丢了就计数，确认发不出去就不执行。**
:::

## 实物实验

- **装备**：3.3V USB-TTL、杜邦线；逻辑分析仪选配。
- **观测点 1**：`info` 返回的平台号，F407 是 1，S3 是 2；连续执行两次 `status`，合法帧数应该增加。
- **观测点 2**：用逻辑分析仪抓 `info` 请求，线上应该恰好是第四节手算的 10 个字节 `04 01 01 07 … 00`（seq 以主机实际发出的为准）。
- **观测点 3（翻车实验）**：用串口助手往协议口发一行文本（不带 0x00），再执行 `status`。预期：文本被当成半帧，主机第一次请求可能超时，重试前补的 0 让解析器恢复，之后 STATUS 里的接收错误数加一。

## 实验记录

模型/编译验证不等于上板实测。当前待上板；请记录日期、板版本、固件版本、接线、输入、原始输出与结论。

| 日期 | 板卡/版本 | 故障输入 | 原始结果 | 结论 |
|---|---|---|---|---|
| 待实测 | | | | |

## 常见坑

- **协议口里混了 printf**：文本没有 0x00 结尾，会和下一帧拼在一起。表现为偶发 CRC 错，越调试越多。
- **TX/RX 没交叉或没共地**：完全没有响应。先查线、端口和波特率，再怀疑代码。
- **直接发结构体内存**：填充和端序变成隐藏协议，换个编译选项就不兼容（第二节）。
- **只测"一次完整到达"**：真实链路会分块、粘包、断在中间。`tests.c` 对每个负载长度、每个切分点都测了分两次到达。
- **出错时也写了输出**：调用方可能把半截数据当结果用。本实现所有检查通过之前不写 `frame_t`（第四节）。

## 短自测

1. 一帧分 10 次到达，结果会和一次到达不同吗？
<details><summary>参考答案</summary>只要相邻两次之间不超过 100ms 就不会。COLLECT 态逐字节累积，遇到帧尾 0 才解码，结果和一次到达完全相同。tests.c 对每个切分点都验证了这一点。</details>

2. 坏 CRC 的帧后面紧跟一个合法帧，能收到合法帧吗？
<details><summary>参考答案</summary>能。坏帧有自己的帧尾 0，解码失败只计一次 crc 并回到 EMPTY，下一段从头收集。只有已知传输丢失（可能丢的正是帧尾）时，才可能牺牲紧接着的一帧，所以主机重试前要补一个 0。</details>

3. 为什么确认帧入队失败时不能执行故障命令？
<details><summary>参考答案</summary>否则命令已经生效，确认却没发出去。主机看到超时会重试，同一条不可重试的命令就执行了两次。对这类操作，"没执行但主机知道失败"比"执行了但主机不知道"安全。</details>

4. raw 长 200 字节时 COBS 开销是多少？本协议为什么可以把 74 写成常量？
<details><summary>参考答案</summary>200 小于 254，开销仍是 1 字节；超过 254 字节，每 254 字节至少多 1 字节。本协议的 raw 最长 72 字节，所以开销恒为 1，加帧尾后线上最长 74 字节，可以在编译期确定并用 _Static_assert 锁住。</details>

## 对照表：本章概念 → 仓库落点

| 概念 | 落点 |
|---|---|
| 容量常量与布局断言 | `code/common/reliability/protocol.h` 的 enum；`protocol.c` 开头两条 `_Static_assert` |
| CRC 与检查值 | `protocol.c` `protocol_crc()`；`tests.c` 断言 0x29B1；Python 侧 `binascii.crc_hqx` |
| COBS 编解码 | `protocol.c` `protocol_cobs_encode/decode()` |
| 三态八计数 | `protocol.c` `protocol_rx_feed/poll/loss()` |
| 丢失先于新字节 | `transport.c` `byte_queue_pop()`；`code/stm32/platform/uart.c` `receive()` |
| 4 槽 TX 与补同步 0 | `transport.c` `protocol_tx_step()` |
| 确认先于执行 | `service.c` `device_service_feed()` 最后一行 |
| 主机配对与重试 | `scripts/device-console.py` `Transport.request()` |

## 延伸阅读

定界与校验都有一手出处：

- **[\[D13\]](../reference/bibliography.md#papers)** Cheshire & Baker 1999：COBS 的原始论文。本章"开销固定、可以提前算进预算"这条选型理由，出处就是它。
- **[\[D9\]](../reference/bibliography.md#papers)** Koopman & Chakravarty 2004：按报文长度给出各多项式的汉明距离表。CRC-16/CCITT 对本章这种短帧能检出几位错，是查表查出来的，不用凭经验猜。

## 你做到了

- 字节流 → 帧 → 命令，每一层都有明确的失败出口和对应计数；
- 能手算一帧的 74 字节上限从哪来，也能在线上逐字节核对；
- [S17 看门狗](../stm32/17-watchdog-reset.md)、[P13 健康监督](../esp32/13-watchdog-health.md) 和两个记录器项目用的都是这一份 codec，STATUS 是它们共同的观察窗口。

回到开场那一问：丢一个字节之后，下一帧还认得出来吗？现在你不仅能答「认得」，还能说清代价——等下一个帧尾重新对齐、残帧可能被牺牲、每一笔失败都有计数可查。字节流从此不是「希望能对上」，是一条逐字节可审计的流水线。

<div class="achievement">
✅ 下一站：<a href="../stm32/17-watchdog-reset.html">S17 看门狗</a>：协议负责说清"出了什么错"，看门狗负责"卡住就重来"。
</div>
