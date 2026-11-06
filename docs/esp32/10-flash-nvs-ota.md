---
title: P10 Flash、分区表、NVS 与 OTA
status: done
difficulty: 3
minutes: 45
---

# P10 16MB 的版图：分区表、NVS 与 OTA

> 🎯 STM32 的 Flash 布局是你链接脚本里画的；ESP32 的 16MB Flash 归一张 **CSV 分区表** 管：哪块放 bootloader、哪块放 app、哪块存参数。而 OTA 的全部秘密，就是"两个 app 分区轮流坐庄 + 一个 otadata 记票"。

## 本章精髓

1. 分区表 CSV 逐字段 name/type/subtype/offset/size/flags：`factory`（出厂 app）、`ota_0/ota_1`（升级候选）、`nvs`（键值存储）、`phy_init`（射频校准）、`spiffs/fatfs`（文件系统）。16MB 的每一 KB 都有户口。
2. NVS 是"磨损均衡的键值库"：nvs_set/get 背后是按页管理+CRC 校验+掉电安全的迷你文件系统。Wi-Fi 凭据、设备配置、计数器的标准住所（别再自己写 Flash 扇区了，对照 [S13](../stm32/13-flash-iap.md) 的手工方案）。
3. OTA 双槽机制：新固件写进另一个 ota 分区→校验→otadata 指向新槽→重启。**新固件自检通过后 esp_ota_mark_app_valid_cancel_rollback**，这一步只在启用 CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE 时需要；否则下次启动才会回滚旧槽。"防变砖"不是口号，是这套状态机。

回滚选项默认未启用；先配置 bootloader，再验证 NEW → PENDING_VERIFY → VALID/ABORTED 状态。不能将不开回滚时的行为套入此流程。

- **能理解**：为什么 app 分区 offset 要 0x10000 对齐而 size 只需 4KB 对齐；为什么"追加写"一个动作同时买到磨损均衡、掉电安全、页满整理；回滚选项为什么默认不开：不开时 NEW/PENDING_VERIFY 状态根本不会被使用，不能把默认行为套进回滚流程。
- **能用**：改 partitions.csv 并用 `idf.py partition-table` 验证；写出 boot_count 掉电持久化最小例；走通"写入另一槽 → set_boot_partition → 重启 → 自检 → mark valid"全流程，并亲手演示一次 PENDING_VERIFY 自动回滚。

## 先修

- [P1 启动](01-arch-boot.md)（分区表登场）、[S13 Flash](../stm32/13-flash-iap.md)（手工方案对照）。

## 先跑起来（10 分钟 quick win）

hello 工程加 NVS：每次启动 `boot_count++` 存回，断电重启后打印：你的第一笔"持久化资产"。

跑之前先押一笔：拔电再上电，boot_count 是从零重数，还记得上次的数？押完就拔，这是全书少有的敢拿断电当判分的实验。

## 动画：OTA 双槽轮流坐庄

ota_0/ota_1 两个槽轮流上岗、otadata 记票；升级期间旧固件一直在岗，新固件先过"试用期"，自检通过转正，失败自动回滚。双槽的保险机制一图演完。

![OTA 双槽轮流坐庄：下载 → 切槽 → 自检 → 回滚](/anim/esp32-ota-rollback.svg)

## 板卡事实

- 立创实战派 S3：16MB Flash（N16R8 模组），默认分区表多为 factory + 大容量存储区布局，以 `idf.py partition-table` 实际读出为准。

## 小节结构

| 小节 | 内容 | 四件套 |
|---|---|---|
| CSV 逐字段 | 默认表逐行；offset 对齐与 size 约束 | 配置 |
| NVS 机制 | 页/条目/CRC；命名空间与类型 API | 库解析 |
| boot_count 实战 | 掉电持久化最小例 | 代码分析 |
| OTA 状态机 | 双槽+otadata+valid/pending 状态全图 | 库解析 |
| 本地 OTA 演练 | 版本号/切槽/回滚三步实操 | 代码分析 |
| 安全选项 | Flash 加密与安全启动的概念地图（生产话题） | 配置 |

## 一、CSV 逐字段：16MB 的户口本

版图先看图：左边静态资产，右边双槽轮流坐庄。

![分区表、NVS 与 OTA 双槽：记账定庄、下载写入、自证失败回滚](/arch/ota-slots.png)

对照 [S13](../stm32/13-flash-iap.md)：STM32 的 Flash 布局画在链接脚本里，是"编译期契约"；ESP32 反过来：布局写在一张 CSV 里，bootloader 每次启动读它（[P1](01-arch-boot.md)），换布局不动链接脚本，换张表就行。

16MB 的头部有三块"公摊面积"，不归 CSV 管：

- 0x0 起：第二级 bootloader 的地皮（S3 的 bootloader 基址就是 0x0）；
- 0x8000：分区表本身（默认 CONFIG_PARTITION_TABLE_OFFSET）。表长 0xC00、最多 95 条，结尾跟一个 MD5 完整性校验，正好占满一个 0x1000 扇区；
- 所以 CSV 里第一个分区必须从 0x9000 或更靠后起步。

一张适配 16MB 的教学示例表（数值按项目需要调整；立创实战派 S3 的实际默认表以 `idf.py partition-table` 读出为准）：

```csv
# Name,   Type, SubType,  Offset,  Size,     Flags
nvs,      data, nvs,      0x9000,  0x5000,
otadata,  data, ota,      0xE000,  0x2000,
phy_init, data, phy,      0x10000, 0x1000,
ota_0,    app,  ota_0,    0x20000, 0x300000,
ota_1,    app,  ota_1,    0x320000,0x300000,
spiffs,   data, spiffs,   0x620000,0x9E0000,
```

16MB = 0x1000000：两个 3MB 的 ota 槽 + 约 9.8MB 文件系统，首尾相接正好铺满。立创实战派的默认布局多为 factory + 大存储区、往往没有 ota 槽，要玩 OTA，第一件事就是换一张这样的双槽表。

逐字段（对齐约束是工具链硬性检查，写错构建期直接报错）：

| 字段 | 作用 | 约束/事实 |
|---|---|---|
| name | 分区名，esp_partition_find_first 按名查 | 最长 16 字节（含结尾空字符，即 15 字符） |
| type | app / data 两大类（0x00/0x01，0x40 起留自定义） | bootloader 只认 app 和 data |
| subtype | app：factory/ota_0~ota_15/test；data：ota/nvs/phy/spiffs/fat/nvs_keys/coredump | 决定库把这块地当什么用 |
| offset | 起始地址 | 可留空自动分配；所有分区至少 0x1000（一个扇区）对齐；app 分区必须 0x10000 对齐 |
| size | 大小 | 支持 K/M 后缀；app 分区大小须 4KB 对齐 |
| flags | encrypted / readonly | app、bootloader、分区表、otadata、nvs_keys 五类无条件加密，与 flags 无关 |

subtype 户口本（本章主角全在这）：

- **factory**：出厂 app 槽，otadata 无效时 bootloader 的兜底（第四节）；不参与 anti-rollback（第六节）。
- **ota_0 / ota_1**：升级双槽，轮流坐庄，OTA 的前提配置。
- **ota（data 子类型，名字常叫 otadata）**：记票板，存"下次启动谁坐庄"。
- **nvs**：键值库（第二节）。官方建议至少 0x3000，至少三页（含一个空页）才能边写边整理；0x1000/0x2000 的小分区会被库按只读对待。
- **phy**：射频初始化数据（名字常写 phy_init）；按设备校准的射频数据另住 NVS（[P8](08-wifi.md) 第五节）。
- **spiffs / fat**：文件系统分区，网页、语音、配置文件的家（大文件别塞 NVS，塞这）。

三条工具链事实：

1. 启用自定义表：menuconfig → Partition Table 选 "Custom partition table CSV"（CONFIG_PARTITION_TABLE_CUSTOM_FILENAME，默认文件名 partitions.csv）。
2. 构建时 gen_esp32part.py 把 CSV 编译成二进制烧进 0x8000；`idf.py partition-table` 打印解析结果，改完表先跑它，对齐、越界当场报错，不用等烧录翻车。
3. 内置的 "Factory app, two OTA definitions" 是 4MB 视角的参考布局（factory/ota_0/ota_1 各 1M），16MB 板照着扩容即可。

实践铁律：**两个 ota 槽等大**。轮流坐庄的两个庄家地位必须对称。不等大不会立刻报错，但构建系统会在"固件只装得进部分 app 槽"时警告（Partition Size Checks），OTA 轮转的隐患从第一天就埋下。

![ESP32 Flash 分区与 OTA：otadata 指向当前 app 槽，新固件写入另一槽；失败可回滚](/figures/esp32-10-flash-nvs-ota.svg)

## 二、NVS 机制：磨损均衡的键值库

在 STM32 上手写 Flash 存储（[S13](../stm32/13-flash-iap.md)），三件事全得自己扛：擦除粒度、掉电半写、寿命摊薄。ESP-IDF 把它们打包成了 NVS（Non-Volatile Storage），**带磨损均衡的键值库**，Wi-Fi 凭据、设备配置、计数器的标准住所。官方定位说得很直白：为"大量小值"设计，别拿它塞大 blob（大文件走文件系统分区）。

三层结构，官方 Internals 章节给了精确解剖图：

- 分区（subtype nvs）按 4096 字节一页切，一页正好一个物理扇区；
- 页 = 页头 32 字节（状态 4 + 序号 4 + 版本 1 + 保留 19 + CRC32 4）+ 条目状态位图 32 字节 + 126 个条目；
- 条目 32 字节：命名空间索引 + 类型 + 跨度 + CRC32 + key（最长 15 字符）+ 数据（整型 8 字节；字符串/blob 可跨多个条目）。

核心机制是**追加写（append-only）**。官方 Internals 原话：键值对顺序存放、新对加在日志尾部；**更新一个 key 不是改旧条目，而是尾部追加新条目、把旧条目标记为 erased**。一个设计买到三样东西：

1. **磨损均衡**：每次写都落在不同位置，擦写压力摊到整个分区（官方量化说法：页+条目组织让擦除频率相对写入频率降低 126 倍）。对照 S13 的单扇区方案：同一个地址反复擦写，寿命按那个扇区单点烧。
2. **掉电安全**：条目和页头都带 CRC32。写一半断电，半条目校验不过，被当作不存在，读到的是上一个完整条目。官方承诺：任意时刻断电，除"正在写的那个键值对"外不丢数据；Flash 里是随机数据也能正常初始化。
3. **页满整理**：页状态机 Active（唯一活动页，只往这写）→ Full（写满，只能标记删除）→ Erasing（整理中：把页里仍然有效的最新条目搬去别的页，再整页擦除回收）。整理全自动，断电打断也会在上电后接着完成。

页状态机还有 Corrupted（页头 CRC 不过、整页弃用），这是库的"自愈"边界：坏一页不至于起不来。

命名空间与类型 API：

```c
nvs_handle_t h;
nvs_open("counter", NVS_READWRITE, &h);  /* 命名空间=姓、key=名；同名 key 在不同命名空间互不打架（上限 254 个） */
nvs_set_i32(h, "boot_count", 42);        /* i8/i16/i32/i64、u8/u16/u32/u64、str、blob 全套 */
char buf[32]; size_t len = sizeof(buf);
nvs_get_str(h, "ssid", buf, &len);       /* str/blob：带缓冲直接读；不知道长度先传 NULL 问大小再二次取值 */
nvs_erase_key(h, "ssid");
nvs_commit(h);                           /* 官方文档原话：nvs_commit 之前不真正落盘 */
nvs_close(h);
```

三条纪律：

- **commit 是句号**：`nvs_set_*` 的 API 文档明说"实际存储直到 nvs_commit 才更新"，每批写入后必调；断电前没 commit 的写全部不算数。
- **读不存在的 key 不是错误**：返回 ESP_ERR_NVS_NOT_FOUND，调用方据此区分"第一次"（第三节正这么用）。类型对不上才是错误（存的是 str、按 i32 读，直接报错）。
- **初始化要接住错误码**：`ESP_ERR_NVS_NO_FREE_PAGES`（没有空页，常见于分区被改小）或 `ESP_ERR_NVS_NEW_VERSION_FOUND`（NVS 格式版本变了，多半是别的固件写的）→ `nvs_flash_erase()` 擦了重新 init。会丢凭据和校准数据，但校准数据下次校准会重新生成（[P8](08-wifi.md) 第五节）。

（进阶储备：NVS 在 RAM 里维护查找缓存，开销随分区和键数增长：官方口径约 1MB 分区 22KB RAM、每 1000 个键再加 5.5KB；带 PSRAM 的项目可开 CONFIG_NVS_ALLOCATE_CACHE_IN_SPIRAM 把缓存挪出内部 RAM。）

## 三、boot_count 实战：第一笔持久化资产

IDF 官方 examples/storage/nvs_rw_value 就是一个"重启计数器"（键名 restart_cnt）。我们把它还原成最小形态：

```c
#include <stdio.h>
#include "nvs.h"
#include "nvs_flash.h"

void app_main(void)
{
    /* ① 初始化：接住两个错误码（第二节纪律 3） */
    esp_err_t err = nvs_flash_init();
    if (err == ESP_ERR_NVS_NO_FREE_PAGES || err == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        err = nvs_flash_init();
    }
    ESP_ERROR_CHECK(err);

    /* ② 打开命名空间 */
    nvs_handle_t h;
    ESP_ERROR_CHECK(nvs_open("counter", NVS_READWRITE, &h));

    /* ③ 读旧值：首次没有这个 key，返回 NOT_FOUND，count 保持 0 */
    int32_t count = 0;
    (void)nvs_get_i32(h, "boot_count", &count);

    /* ④ 加一写回 + commit 收尾 */
    count++;
    ESP_ERROR_CHECK(nvs_set_i32(h, "boot_count", count));
    ESP_ERROR_CHECK(nvs_commit(h));
    printf("boot count: %d\n", (int)count);

    nvs_close(h);
}
```

烧录后连续断电重启五次，monitor 里看到 1→2→3→4→5。三个关键点值得逐行咂摸：

- **首次启动**：第 ③ 步 NOT_FOUND，count 保持初值 0，打印 1："读不到旧值"被翻译成"第一次"，不需要额外的标志位。
- **重启不等于丢数据**：断电、按 EN 复位、monitor 里 Ctrl-T Ctrl-R 热复位，三种方式对 NVS 毫无区别——重启后读到的都是上次 commit 落盘的那个值。掉电安全不靠运气，靠的是第二节"半条目 CRC 不过被当不存在"的机制。
- **第 ④ 步在 Flash 里发生了什么**：set 没有碰旧条目，而是在活动页追加了一个新条目（同 key 以最新为准）；重启几十次后活动页写满，库自动做 Erasing 整理（页满后的自动整理行为），你一行代码都不用写。

举一反三：把"每次启动 +1"换成"上次连的 Wi-Fi""累计运行秒数""报警次数"：所有"断电要记住的事"都是这一个模式的变体。

泼一瓢冷水（呼应常见坑 2）：boot_count 的写入频率是"每次启动一次"，NVS 毫无压力；把同样的代码搬进主循环每秒 +1，Flash 寿命就开始燃烧：高频数据先进 RAM，定期落盘。

## 四、OTA 状态机：双槽轮流坐庄

为什么必须两个 app 槽？单 app 分区没法自我升级，总不能把正在运行的那块地当场铲掉。双槽的本质：**运行的槽和接收新固件的槽永远不是同一个**。

- **ota_0 / ota_1**：两个等大的 app 分区，一个坐庄（运行中），一个备选（收新固件）。
- **factory**（可选）：出厂槽。
- **otadata**（data/ota，0x2000）：记票板。注意它的掉电安全设计：官方文档明说这分区是"两个扇区"，各写一份同样的票、带计数器轮流写，断电后两份不一致就按计数器裁决谁更新。给记票板自己做双备份，比给固件买保险还讲究。

启动决策（bootloader 每次上电重演一遍）：

1. 读 otadata：票指向 ota_X 就启动 ota_X；
2. 记票板全空（全 0xFF，从未 OTA 过）→ 启动 factory；表里没有 factory → 启动第一个 ota 槽（通常 ota_0）。

写入流程的 API 五步（数据来源随意：HTTP 下载、预烧分区、SD 卡，都汇入同一条管道）：

```c
const esp_partition_t *next = esp_ota_get_next_update_partition(NULL); /* 自动轮转挑"另一个槽" */
esp_ota_handle_t ota;
esp_ota_begin(next, OTA_SIZE_UNKNOWN, &ota);  /* 大小未知则先整槽擦除 */
esp_ota_write(ota, chunk, len);               /* 循环分块写 */
esp_ota_end(ota);                              /* 校验闸：镜像不合法在此拦下 */
esp_ota_set_boot_partition(next);              /* 改票：下次启动坐庄的是新槽 */
esp_restart();
```

两处设计值得品味：

- `esp_ota_get_next_update_partition()` 从当前运行槽出发轮转找下一个，你不用算"现在 0 号所以写 1 号"。
- `esp_ota_end()` 是校验闸门：刚写完的镜像不是合法 app（或开了安全启动后签名不过），直接返回 ESP_ERR_OTA_VALIDATE_FAILED。坏 bin 在这被拦下，而不是变砖后才发现。

**然后是本章最重要的一段事实**：上面五步只是"换庄"。防变砖的"自证清白"状态机，**只在 CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE 打开后才存在（默认未启用）**。官方文档的 App OTA State 全图：

| 状态 | bootloader 会选它吗 | 谁设置 |
|---|---|---|
| ESP_OTA_IMG_VALID | 正常选 | esp_ota_mark_app_valid_cancel_rollback()：自检通过、转正 |
| ESP_OTA_IMG_UNDEFINED | 正常选 | esp_ota_set_boot_partition()，**未开回滚时**设的就是它 |
| ESP_OTA_IMG_INVALID | 永不选 | esp_ota_mark_app_invalid_rollback_and_reboot()：主动判死 |
| ESP_OTA_IMG_ABORTED | 永不选 | bootloader：发现上次停在 PENDING_VERIFY，改写为 ABORTED |
| ESP_OTA_IMG_NEW | 只给一次启动机会，且立即被改写为 PENDING_VERIFY | esp_ota_set_boot_partition()，**开了回滚时**设它 |
| ESP_OTA_IMG_PENDING_VERIFY | 不选，改写为 ABORTED 后弃用 | bootloader 首次启动 NEW 镜像时设置 |

开了回滚之后，一次 OTA 的完整生命周期：

1. `esp_ota_set_boot_partition()` 把新镜像标 **NEW**；
2. 重启，bootloader 看到 NEW → 改写为 **PENDING_VERIFY** → 启动新固件（"临时工上岗"）；
3. 新固件自检（点灯、联网、关键外设应答，任选）：
   - 通过 → `esp_ota_mark_app_valid_cancel_rollback()` → **VALID**，转正；
   - 失败 → `esp_ota_mark_app_invalid_rollback_and_reboot()` → **INVALID**，立即重启回旧槽；
4. 若 PENDING_VERIFY 没确认就断电/崩溃/看门狗复位，**下次启动** bootloader 发现它还停在 PENDING_VERIFY，改写为 **ABORTED**、弃用，自动回滚旧槽。只要不重启，PENDING_VERIFY 可以一直挂着；回滚永远发生在"下次启动"，不在运行中。

而**默认配置（未开回滚）时，这套状态机根本不启用**。官方文档原话：此时两个 mark 函数"是可选的"，`ESP_OTA_IMG_NEW` 和 `ESP_OTA_IMG_PENDING_VERIFY` 两个状态"不会被使用"；set_boot_partition 设的是 UNDEFINED，bootloader 直接启动新槽、立即视为有效。新固件是坏的也照样坐庄，不会自动回滚，只能人工重烧。所以精髓第 3 条反复划的边界："自检通过后 mark valid"是**开回滚后的强制环节**，不是 OTA 的默认流程；不开回滚时，你在固件里调不调 mark valid，启动决策一个字都不会变。

三个附带事实（第五节的演练里都会碰到）：

- 回滚状态记在 otadata 分区里，不在固件镜像里：镜像不变，变的只是"票"。
- 只有 ota 槽会回滚，factory 槽不参与回滚（官方明确）。
- 开了回滚、当前固件还停在 PENDING_VERIFY 时就发起下一次 OTA，`esp_ota_begin()` 直接报 ESP_ERR_OTA_ROLLBACK_INVALID_STATE：先把上一版转正，再升级下一版。

最后一条工具链事实：CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE 编译在 **bootloader** 里。menuconfig 改完必须 `idf.py flash` 连 bootloader 一起重烧，只烧 app 不生效，与常见坑 4"分区表与 boot 不同步"是同一类失配。

## 五、本地 OTA 演练：切庄、转正与回滚三连

"本地 OTA"= 新 bin 不出局域网：起一个局域网 HTTP(S) 服务放 bin，或干脆把新 bin 预烧进数据分区，设备自己搬进 ota 槽。官方 examples/system/ota/native_ota_example 演示的就是 app_update 原生 API 全流程；网络侧想省事用 esp_https_ota 组件（内部包着同一套 esp_ota_* 管道）。骨架说的"版本号/切槽/回滚"三件事，这里分五步走：

**第 0 步：开回滚 + 换双槽表。** menuconfig：Bootloader config 打开 CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE；Partition Table 选 Custom、指向第一节的示例 CSV（两个 3MB ota 槽）。`idf.py flash` 全量烧录（bootloader 一起），`idf.py partition-table` 确认 ota_0/ota_1/otadata 三块地皮都挂牌。**没这步就没有回滚可演示**：默认配置下第 3 步什么都不会发生。

**第 1 步：版本号，这出戏的角色名牌。** CMakeLists.txt 里 `set(PROJECT_VER "1.0.0")`（不设则由 git 推导，再不行默认 1），运行时打印版本和当前槽位，分清谁在坐庄：

```c
#include "esp_app_desc.h"

const esp_partition_t *running = esp_ota_get_running_partition();
printf("ver=%s, running=%s\n",
       esp_app_get_description()->version, running->label);
/* 首次烧录：ver=1.0.0, running=ota_0 */
```

**第 2 步：把 1.1.0 写进另一个槽并切庄。** 改 PROJECT_VER 为 1.1.0 构建新 bin，喂给设备（本地分区或局域网服务器），核心管道就一段：

```c
#include "esp_ota_ops.h"

const esp_partition_t *next = esp_ota_get_next_update_partition(NULL); /* ota_1 */
esp_ota_handle_t ota;
ESP_ERROR_CHECK(esp_ota_begin(next, OTA_SIZE_UNKNOWN, &ota));
char buf[512];
int n;
while ((n = src_read(buf, sizeof(buf))) > 0) {  /* src：本地分区/HTTP，随你 */
    ESP_ERROR_CHECK(esp_ota_write(ota, buf, n)); /* 分块搬进 ota_1 */
}
ESP_ERROR_CHECK(esp_ota_end(ota));               /* 校验闸门 */
ESP_ERROR_CHECK(esp_ota_set_boot_partition(next)); /* 改票 */
esp_restart();
```

重启后日志：`ver=1.1.0, running=ota_1`，庄家换了，但此刻它只是 PENDING_VERIFY 的"临时工"。

**第 3 步：自检转正。** app_main 尽早的位置跑一段自检（官方推荐的骨架）：

```c
const esp_partition_t *running = esp_ota_get_running_partition();
esp_ota_img_states_t st;
if (esp_ota_get_state_partition(running, &st) == ESP_OK
        && st == ESP_OTA_IMG_PENDING_VERIFY) {
    if (self_test_ok()) {   /* 点灯/联网/外设应答，任选一招 */
        ESP_ERROR_CHECK(esp_ota_mark_app_valid_cancel_rollback());
        /* PENDING_VERIFY → VALID，正式坐庄 */
    } else {
        ESP_ERROR_CHECK(esp_ota_mark_app_invalid_rollback_and_reboot());
        /* INVALID，立刻回旧槽 */
    }
}
```

**第 4 步：故意不转正，看自动回滚。** 再 OTA 一版 2.0.0，但这版**故意删掉第 3 步的自检代码**。2.0.0 跑起来很欢（版本号都打印出来了），此时手动 `esp_restart()`，下次启动 bootloader 发现 ota_1 还停在 PENDING_VERIFY：改写为 ABORTED、弃用、回滚，日志回到 `ver=1.1.0, running=ota_0`，**防变砖机制亲手验证完毕**（实物实验留档）。想演"主动回滚"，把 self_test_ok 换成永远返回假，走 INVALID 那条立即回滚的路。

对照组（事实纪律）：如果第 0 步没开回滚选项，同样的"故意不转正"什么也不会发生：重启后照样是 2.0.0 坐庄，bootloader 根本不查这套状态。回滚不是玄学魔法，是 bootloader 多做的一次查票；不开回滚，就没有这次查票。

## 六、安全选项：从"明文裸奔"到量产的概念地图

到这一节为止，你的 Flash 是明文的：拆下 Flash 芯片用编程器能读走固件，改个 bin 就能刷进去。量产前要补的板子，这里只建概念地图不实操（细节以 IDF Security 文档为准；eFuse 烧错没有后悔药，先拿测试板练手）：

- **Flash 加密**：Flash 落盘密文、运行时由硬件透明加解密，密钥固化在 eFuse（一次性烧写），防"拆片读固件"。menuconfig 分 Development/Release 两档：前者可反复试错，后者一次性烧死。第一节 flags 提过：app、bootloader、分区表、otadata、nvs_keys 这五类**无条件加密**，其余分区要落密文得标 encrypted。
- **安全启动（Secure Boot）**：信任链 ROM→bootloader→app：bootloader 用 eFuse 里的公钥摘要验 app 签名。效果：**没签名的 bin bootloader 直接拒收**。配合 OTA：esp_ota_end 的校验闸从"拦坏镜像"升级到"拦未签名镜像"（签名验证失败同样返回 ESP_ERR_OTA_VALIDATE_FAILED）。
- **anti-rollback**：第四节的状态机防"新固件挂了"（可用性），防不了"故意刷旧版"（安全性：旧版的漏洞还没修）。CONFIG_BOOTLOADER_APP_ANTI_ROLLBACK（与回滚选项配套使用）在镜像描述符 esp_app_desc_t 里引入 secure_version。bootloader 只选"版本号不低于芯片内已固化值"的镜像，只许升不许降。两个细节：secure_version 只有 16 位（升级次数有限）；factory/test 槽不参与这套机制。
- **NVS 加密**：前门上了锁（固件加密），后门还敞着（Wi-Fi 密码明文躺在 NVS）：nvs_keys 分区存密钥，把参数也密文化。官方提醒：NVS 加密防篡改防读取，但防不了"整分区擦除"这种暴力。
- **不开安全启动也要签 OTA**：CONFIG_SECURE_SIGNED_APPS_NO_SECURE_BOOT，不上安全启动硬件链，但 OTA 镜像仍要求签名验证，性价比很高的中间档。

这张地图的作用：让你在"量产"这个词出现时知道去哪查。学习期到第五节为止，明文 + 回滚已够用；真要发产品，Flash 加密、安全启动、anti-rollback 的开启顺序和 Release 模式的不可逆性，IDF Security 章节有保姆级流程：**先在测试板上练**。

## 记忆锚点

::: tip 一句话记住
**分区表是地产证，NVS 是带掉电保护的抽屉，OTA 是双槽轮流坐庄——新固件不自证清白，旧槽随时复位。**
:::

## 实物实验

- 本地 OTA 全流程 + 故意"不标 valid"看自动回滚，亲手验证防变砖机制（日志存档）。

## 常见坑

- **app 超分区大小**：build 过但烧录/启动失败，改 CSV 给 app 扩容或开 -Os 瘦身（B5 方法）。
- **nvs 当高频日志存储**：Flash 寿命按擦写次数计，高频数据先入 RAM 定期落盘。
- **OTA 后忘调 mark_valid**：新固件跑挺欢，重启回旧版：自检+标记是 OTA 的最后一公里。
- **分区表与 boot 不同步**：改了 CSV 只烧 app，`idf.py flash` 全套重烧解决。

## 短自测

1. 分区表 CSV 的六个字段是什么？app 分区与 data 分区在 offset/size 对齐上各有什么硬约束？写错了什么时候会暴露？
<details><summary>看答案</summary>六字段：name/type/subtype/offset/size/flags。约束：所有分区 offset 至少 0x1000（一个 4KB 擦除扇区）对齐；app 分区 offset 必须对齐 0x10000，size 只需 4KB 对齐；offset 可留空由 gen_esp32part 自动分配对齐。写错不用等烧录翻车：构建期、`idf.py partition-table` 解析时就直接报错。</details>

2. NVS 更新同一个 key 时，Flash 里到底发生了什么？为什么说追加写"一个设计买到三样东西"？
<details><summary>看答案</summary>更新 = 在日志尾部追加一个新条目，旧条目标记为 erased，读取以最新为准。三样：磨损均衡（写压力摊到整个分区，官方量化：擦除频率相对写入频率降低 126 倍）；掉电安全（半写条目 CRC32 不过被当不存在，任意时刻断电只丢"正在写的那个键值对"）；页满整理（页状态 Active→Full→Erasing：有效条目搬走、整页擦除回收，全自动且断电可续）。</details>

3. OTA 写入的 API 五步顺序是什么？esp_ota_end 和 esp_ota_set_boot_partition 各把哪道闸？
<details><summary>看答案</summary>esp_ota_get_next_update_partition（自动轮转挑另一个 ota 槽）→ esp_ota_begin（OTA_SIZE_UNKNOWN 时先整槽擦除）→ esp_ota_write 循环分块写 → esp_ota_end → esp_ota_set_boot_partition → esp_restart。esp_ota_end 是校验闸：验证刚写完的镜像是不是合法 app（开安全启动还要验签），坏 bin 返回 ESP_ERR_OTA_VALIDATE_FAILED 当场拦下；set_boot_partition 是改票闸：更新 otadata，让下次启动换庄。</details>

4. 开了回滚后，新镜像的完整状态生命周期怎么走？关键事实题：默认不开回滚时，"故意不 mark valid"会发生什么？
<details><summary>看答案</summary>开回滚：set_boot_partition 标 NEW → 重启后 bootloader 把 NEW 改写为 PENDING_VERIFY 并启动 → 自检通过调 esp_ota_mark_app_valid_cancel_rollback 转 VALID（转正）；自检失败调 esp_ota_mark_app_invalid_rollback_and_reboot 标 INVALID 立即回滚；没确认就重启（断电/崩溃/看门狗），下次启动 bootloader 把 PENDING_VERIFY 改写为 ABORTED、弃用，自动回滚旧槽。默认不开回滚：NEW 和 PENDING_VERIFY 两个状态根本不被使用，set_boot_partition 设的是 UNDEFINED，重启直接启动新固件、立即视为有效，坏固件不会自动回滚，只能人工重烧；mark valid 调不调都不影响启动决策。</details>

5. otadata 为什么定 0x2000、内部怎么防掉电？记票板全空时 bootloader 启动谁？回滚选项为什么必须重烧 bootloader？
<details><summary>看答案</summary>otadata 是两个扇区（0x2000）：写票时两份轮流写、各带计数器，断电后两份不一致按计数器裁决谁更新，记票板自己的掉电安全。全空（全 0xFF，从未 OTA）→ 启动 factory 槽；没有 factory 则启动第一个 ota 槽（通常 ota_0）。回滚选项 CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE 编译在 bootloader 二进制里，menuconfig 改完必须 idf.py flash 连 bootloader 一起重烧，只烧 app 不生效，与"改了分区表只烧 app"是同一类失配。</details>

## 对照表：本章概念 → 仓库与上游落点

| 概念 | 落点 |
|---|---|
| 分区表 CSV 六字段与对齐规则 | IDF components/partition_table（gen_esp32part.py）；实际读数以 `idf.py partition-table` 为准 |
| 0x8000 分区表（0xC00 条目区 + MD5，占满 0x1000 扇区） | IDF《Partition Tables》；[P1 启动](01-arch-boot.md) |
| NVS 页/条目/CRC 内部结构（页头 32B、条目 32B、126 条目/页） | IDF《NVS Internals》；`nvs_flash.h`/`nvs.h` |
| boot_count 掉电持久化 | IDF examples/storage/nvs/nvs_rw_value（官方重启计数示例）；本节第三节 |
| OTA 五步 API 与双槽机制 | IDF `esp_ota_ops.h`（app_update 组件）；examples/system/ota/native_ota_example |
| 回滚状态机 + otadata 双扇区计数器 | IDF《OTA》App Rollback 一节；CONFIG_BOOTLOADER_APP_ROLLBACK_ENABLE（默认未启用） |
| anti-rollback（secure_version 单调门槛） | CONFIG_BOOTLOADER_APP_ANTI_ROLLBACK；esp_app_desc_t.secure_version |
| Flash 加密 / 安全启动 / NVS 加密 | IDF Security 章节（Flash Encryption、Secure Boot、NVS Encryption）；nvs_keys 分区 |
| NVS 与 Wi-Fi 校准数据的渊源 | [P8 Wi-Fi 第五节](08-wifi.md) |
| 手工 Flash 方案对照（擦除粒度/掉电/寿命） | [S13 Flash](../stm32/13-flash-iap.md) |

## 延伸阅读

NVS 页头与条目的 CRC32 不是装饰：

- **[\[D9\]](../reference/bibliography.md#papers)** Koopman & Chakravarty 2004 — 多项式与报文长度决定检错能力；这篇解释了 32 位 CRC 对几十字节记录"够用"的边界在哪。

## 你做到了

- 16MB 的每一寸都归你规划；
- 持久化与远程升级两大产品能力原理到手，小智板离"产品"只差你的应用。

断电判分的结果：数没丢。CPU、内存、寄存器全体失忆，只有 Flash 里那页条目还记得你数到几。公摊面积之外，这是你在这张版图上划出的头一块自留地。

<div class="achievement">
✅ 下一站：<a href="11-lowpower.html">P11 低功耗</a>：睡眠矩阵、ULP 与电流实测。
</div>
