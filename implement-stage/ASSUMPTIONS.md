# Assumption Ledger — ch41 NVS blob 上限纠错

<!-- ASK mode: never -->

| ID | Under-determined by the request | Chosen | Class | Source |
|----|--------------------------------|--------|-------|--------|
| A-001 | “1984 B 上限”是版本常量、单页上限还是默认分区可用量 | 按 ESP-IDF v5.5.2 源码区分结构上限与运行时限制，不保留固定 1984 B 说法 | semantic | default |
| A-002 | 结构上限是否等于任何分区都能写出的最大值 | 明确 508,000 B 只是索引/分块结构的理论上限，实际受分区页数、剩余空间、键与索引开销限制 | semantic | default |
| A-003 | 默认 NVS 分区是否适合作为数值例子 | 引用 ch30 的默认 `nvs=0x6000`，只说明 128 B 配置远小于分区，不计算伪精确的最大 blob | semantic | default |
| A-004 | 出处放在正文还是证据表 | 正文给一个 pinned GitHub 链接，证据表保留常量与计算判据 | interface | default |
| A-005 | 是否需要新增自动回归测试 | 不新增读取正文的文本断言；用书稿契约门、渲染门与独立源码审查验证 | interface | default |

## Notes

- A-001：旧说法可能来自更早版本或特定分区估算；v5.5.2 的 `BLOB_IDX` 校验公式已变为 `(UINT8_MAX/2) * (ENTRY_COUNT-1) * ENTRY_SIZE = 508,000`。
- A-002：`writeMultiPageBlob()` 还用 `mPageManager.getPageCount()-1` 和 `CHUNK_ANY` 限制实际可写页数，因此不存在跨分区的固定“1984 B”。
- A-003：本工程只写 128 B 配置；精确讨论大 blob 前应先锁定分区表、键长度、已有 namespace 与页面状态。

## Independent sweep

- `SWEEP_UNAVAILABLE`：NVIDIA NIM `moonshotai/kimi-k2-thinking` 返回 HTTP 410，无响应体；未取得独立审查结论，不宣称外部放行。
