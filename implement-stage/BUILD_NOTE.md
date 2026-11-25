# Build Note — ch41 NVS blob 上限纠错

| Rung | Feature | Acceptance check (ONE command) | Tier | Status |
|------|---------|-------------------------------|------|--------|
| F0 | 修正 ch41 的固定 1984 B 说法与证据身份 | `python -X utf8 -m book.checks --check && python -X utf8 tools/slop_lint.py` | MUST | PASS |
| F1 | 补 v5.5.2 pinned 源码、508,000 B 结构上限与分区边界 | `python -X utf8 -m book.build_html --check` | MUST | PASS |
| F2 | 站点构建与 ch41 页面目检 | `npm run docs:build && npm run site:pages` | MUST | PASS |
| F3 | 独立 silent-assumption sweep | saved `SILENT_ASSUMPTION_SWEEP.json` or `SWEEP_UNAVAILABLE` | MUST | PASS (unavailable recorded) |

## Run record

- F0: `book.checks --check` + `slop_lint` exit 0；ch41 第 94/125 行已改；fix attempts 0。
- F1: `book.build_html --check` exit 0；53 页、0 missing；508,000 B/v5.5.2/0x6000 边界断言通过；fix attempts 0。
- F2: `docs:build`/`site:images`/`site:pages` exit 0；363 图、54 页；ch41 页面 508,000 B/1984 B 否定句/0x6000/两个 pinned 链接均渲染，无横向溢出；fix attempts 0。
- F3: NVIDIA NIM `moonshotai/kimi-k2-thinking` 返回 HTTP 410；已写 `SILENT_ASSUMPTION_SWEEP.json=SWEEP_UNAVAILABLE`，未宣称独立放行。
- Final recheck: `book.checks`/`book.build_html`/`slop_lint`/124 pytest all exit 0；GitHub API 验证 `nvs_types.cpp` blob `81379c8…` 与 `nvs_storage.cpp` blob `f776404…`；`task_verify=unverified`。

## Deferred

- 默认分区下的精确最大 blob 计算：需要锁定分区表、键、namespace 与页面状态，且不是本段教学结论。

## Blockers

- None.
