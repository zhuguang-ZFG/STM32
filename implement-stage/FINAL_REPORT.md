# Final Report — ch41 NVS blob 上限纠错

## What runs now

- `python -X utf8 -m book.checks --check`：exit 0。
- `python -X utf8 -m book.build_html --check`：53 页，0 missing。
- `python -X utf8 tools/slop_lint.py`：无机械命中。
- `python -X utf8 -m pytest book/tests -q --confcutdir=book/tests -p no:cacheprovider`：124 passed。
- `npm run docs:build`、`site:images`、`site:pages`：exit 0；363 图、54 页。
- ch41 构建页目检：508,000 B、1984 B 否定句、0x6000 与两个 pinned 源码链接均渲染，无横向溢出。

## Semantic assumptions

- A-001：不把 1984 B 当作通用上限；按 ESP-IDF v5.5.2 区分结构上限与运行时限制。
- A-002：508,000 B 只是索引/分块结构理论上限，不是任何分区都能写出的最大值；实际还受页数、剩余空间、键与索引开销影响。
- A-003：默认 `nvs=0x6000` 只作为分区容量例子；128 B 配置本身小于分区，但是否可写仍看当时剩余空间。

## Ladder status

- F0：PASS。
- F1：PASS。
- F2：PASS。
- F3：PASS，独立审查不可用已如实记录。

## Live stubs

- None.

## Sweep outcome

- `SWEEP_UNAVAILABLE`：NVIDIA NIM `moonshotai/kimi-k2-thinking` 返回 HTTP 410，无响应体；没有取得独立审查结论，也不宣称外部放行。

## Interface assumptions

- A-004：正文放 pinned GitHub 链接，证据表放常量与计算判据。
- A-005：不新增读取正文的文本断言；使用书稿契约门、渲染门和源码核对。

## Verification status

- 通过：书稿契约、渲染、文风、124 项回归、站点构建与页面目检。
- 失败：无未解决失败。
- `task_verify`：unverified，原因是项目无 operator-configured Git baseline/checks。

## Deferred

- 默认分区下的精确最大 blob 计算：需要锁定分区表、键、namespace 与页面状态，不属于本次事实纠错。
