# SPEC — ch41 NVS blob 上限纠错

## Target

修正 `docs/v6-labs-projects/41-dual-board-logger-project.md` 中“单 blob 最大 1984 B”的待核说法，使读者知道 ESP-IDF v5.5.2 的结构上限与实际分区限制。

## Inputs

- 当前 ch41 正文与证据表。
- ESP-IDF `v5.5.2`：`nvs_constants.h`、`nvs_page.cpp`、`nvs_storage.cpp`、`nvs_types.cpp`、`nvs_types.hpp`。
- ch30 已登记的默认 `nvs` 分区 `0x6000`。

## Outputs

- ch41 第 5 节：删除固定 1984 B 上限，写出结构上限、实际限制与 128 B 配置的安全边界。
- ch41 证据表：把“来源说法待核”改成带版本和源码出处的结论。
- `implement-stage/`：SPEC、假设账本、构建记录、独立审查结果。

## Success command

```bash
python -X utf8 -m book.checks --check && python -X utf8 tools/slop_lint.py
```

## Base commit

`bbdbb95577511bd4aa724cf9afb83ccfe9bb3a06`

## Scope cuts

- 不修改 ESP-IDF 或本仓库 NVS 实现。
- 不宣称默认分区下存在一个可复用的固定最大 blob 字节数。
- 不扩展成 NVS 教程；只修正这一处事实边界。
- 不做硬件、掉电或分区写入实验。
