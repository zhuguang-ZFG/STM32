# B52：全章无图区间收口（gap ≤ 1,200 收尾批次）

日期：2026-11-10。基线：`test_book_audit.py` 分布门（GAP_CAP_CHARS=1200）登记
15 个暂存超限章；本批逐章补图收口，收口后 `GAP_TRANSIENT_OVERAGES` 清空，
仅保留 ch26 已批例外（1231，见 `audits/b48-gap-figures.md`）。

## 交付清单（每章 1–4 张新 Handraw 图，zh/en 同序列嵌入）

| 章 | 新图 | 落点 | 回答的正文问题 |
| --- | --- | --- | --- |
| 00 | ch00-rtos-worth-it | 阶段三表后 | 「什么场景才值得上 RTOS」 |
| 01 | ch01-boot-first-words（自 :46 移到 时序表后）/ ch01-one-elf-evidence / ch01-rdp-unlock-paths / ch01-main-skeleton | 时序与状态表后 / CLion 第 5 步后 / OpenOCD 块后 / main.c 块后 | 复位取指链+两失败出口 / 四调用方同一 ELF / RDP 解锁两条路径 / 骨架四步合同 |
| 02 | ch02-flash-latency / ch02-part-number-decode | LATENCY 段后 / 命名规则表后 | 升频先加等待周期 / 料号七段解码 |
| 04 | ch04-preempt-timeline | 时序表注后 | 抢占何时发生、同抢占不嵌套、PRIMASK |
| 06 | ch06-baud-budget（agent） | uart-idle.gif 后 | 波特率分频与误差预算 |
| 07 | ch07-ccr-timing（agent） | 章首视频后 | CCR→SCL 取值链 |
| 08 | ch08-cs-triage（agent） | nss-multi 后 | 软件/硬件 NSS 与 CS 时机分诊 |
| 09 | ch09-adcclk-budget / ch09-pa0-analog-config（agent）/ ch09-dac-buffer（agent） | 分频段后 / §5 表后 / §6 末 | ADCCLK 合法档（见下「事实修正」）/ PA0 两种配置 / DAC 缓冲器取舍 |
| 11 | ch11-backup-path（agent） | iwdg-1s.gif 后 | VBAT 后备供电路径 |
| 14 | ch14-cdc-vs-hid | §6 表后 | CDC/HID 五维对照与选型 |
| 17 | ch17-dwt-window（agent）/ ch17-swo-path（fig_ch17 既有未渲函数） | 优化表后 / SWO 重定向前 | DWT 计时窗口构成 / printf 上 SWO 链路 |
| 19 | ch19-log-ring | 项目 2 技术方案后 | 循环日志区结构与「示例做到了/还缺」 |
| 20 | ch20-dma-f1-vs-f4 | 示例 3 后 | F1/F4 DMA 三差异，跨系列结论先核对 |
| 21 | ch21-identity-triage | 常见坑表后 | 兼容板三处核对、证据优先 |
| 25 | ch25-hal-clock-values / ch25-clock-evidence | 「软件读回」段后 / 自测 Q6 后 | 480/240 读回归属 / 时钟验收三列证据 |

## 事实修正（blocker advisory）

- **ch09-adcclk-budget**：初版漏 `ADCPRE=11`（÷8 = 9 MHz，亦 ≤14 MHz 合法）。
  依据 `cheatsheets/寄存器速查表.md`（RCC_CFGR `[15:14]` 表）修正：图加第四行
  「÷8 也合法，只是转换更慢」，「唯一合法档」全部改为「最高合法档（速度优先）」；
  涉及生成器 `fig_ch09.py`、docs/09 与 docs/en/09 正文、zh/en 图注、
  `figure-types.json` 登记 caption。重渲染后目检通过。

## 其他修正

- en/25 `ch25-clock-evidence` 重复嵌入了两次（实验 5 后 + 自测 Q6 后），
  删除实验 5 后那份，与 zh 落点（自测 Q6 后、`## 相关资源` 前）对齐。

## 测试锁更新（等值重钉 + 新增登记）

- `test_advanced_visuals.py` CHAPTERS：00 16→17、01 18→22、09 17→20、
  11 17→18、14 17→18、17 16→18、19 18→19、20 17→18、21 18→19、25 18→20。
- `test_book_audit.py` PHASE 序：06/07/08/09/11/14/17/19/20/21/25 各 +1~3 项；
  ch19 第二份本地 tuple 同步 +1；ch01 `pdf_visual_anchors` 18→22、asset_sequence +4。
- `GAP_TRANSIENT_OVERAGES`：15 项全部删除，字典置空（门保留，拒绝新增超限）；
  ch26 例外保留。
- `figure-types.json`：+23 条（ch01×4、ch06、ch07、ch08、ch09×3、ch11、
  ch17×2、ch25×2、ch00、ch02×2、ch04、ch14、ch19、ch20、ch21）。

## 验证记录

- 分布门：29 章全 ≤1200（唯一例外 ch26=1231 已批）。
- `pytest test_figure_type_coverage test_book_audit test_advanced_visuals`：24 passed。
- handraw 轨道/图层测试 26 passed（生成器改动未破确定性哈希锁）。
- 全量 gates 与构建见 B51 终态批次统一记录。
