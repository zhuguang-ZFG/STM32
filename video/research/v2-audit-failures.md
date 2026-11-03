# v2 节拍审计故意失败原文

采集方式：用与 `video/tests/timeline-beats.test.mjs` 四个失败用例相同的 plan，前三个直接调用
`validateBeats(plan)`、第四个调用 `deriveBeats(sc, captions)`，捕获 `e.message` 原样输出（未改写、未截断）。

## (a) 静止 9s（用例实际构造 9.5s）

用例 `静止 9s 必须报错`：code 场 duration 10s，两拍在 0s / 9.5s（场尾 10s，实际最大静止 9.5s）。

```text
节拍审计未通过:
  - code-01: 静止 9.5s > 6s
  - code-01: line:1 永远不会揭示
  - code-01: line:2 永远不会揭示
  - code-01: line:3 永远不会揭示
  - code-01: line:4 永远不会揭示
  - code-01: line:5 永远不会揭示
  - code-01: line:6 永远不会揭示
  - code-01: line:7 永远不会揭示
  - code-01: line:8 永远不会揭示
  - code-01: line:9 永远不会揭示
```

## (b) 永远不会揭示

用例 `永远不揭示必须报错`：两拍只揭示 `title`，`line:0..9` 没有任何拍覆盖。

```text
节拍审计未通过:
  - code-01: 静止 18.0s > 6s
  - code-01: line:0 永远不会揭示
  - code-01: line:1 永远不会揭示
  - code-01: line:2 永远不会揭示
  - code-01: line:3 永远不会揭示
  - code-01: line:4 永远不会揭示
  - code-01: line:5 永远不会揭示
  - code-01: line:6 永远不会揭示
  - code-01: line:7 永远不会揭示
  - code-01: line:8 永远不会揭示
  - code-01: line:9 永远不会揭示
```

## (c) 钩子 16s

用例 `钩子超过 15s 必须报错`：开场连续两个 hook 场，各 8s，合计 16s。

```text
节拍审计未通过:
  - 钩子 16.0s > 15s
```

2026-10-22 Task 6 复跑确认与上文逐字一致（未改写）。

## (d) beatMap.at 超出本场字幕数（构建期失败）

用例 `beatMap.at 超出本场字幕数必须报错`：本场只有 2 句字幕，`beatMap[1].at = 3` 没有落点；
`deriveBeats` 直接抛错并中止构建，不进入 `validateBeats` 的审计汇总。

```text
beatMap[1].at=3 超出本场字幕数 2
```

## (e) 静止 9.0s（Task 6 审计夹具）

用例 `v2 静止 9.0s 必须报错`（`video/tests/audit-v2.test.mjs`）：code 场 duration 10s，两拍在 0s / 9.0s，
其余目标全部被这两拍覆盖。

```text
节拍审计未通过:
  - code-01: 静止 9.0s > 6s
```

## (f) 审计时仍不可见（Task 6）

用例 `v2 审计抓到 showAll 后仍不可见的节拍目标`：v2 hook 舞台经 `page.addStyleTag` 强制
`[data-beat-target="sub"]{opacity:0!important}`，`MCU.showAll()` 之后 sub 的计算不透明度仍是 0。

```text
排版审计未通过:
  - h: 审计时仍不可见 div "sub" opacity=0
```

## (g) v2 封面 42 字标题装不下（Task 9）

夹具固定为 `.temp/task9-fail.mjs` 里的临时 episode（`id: 'task9-fail'`、`formatVersion: 2`、`badge: 'T9'`，
`cover.line1 = '装不下'.repeat(14)` 即 42 字，`cover.line2 = '第二行'`，另有
`vs: { left: '看着装得下', right: '其实装不下' }`、`proof: '![1] 这一行是短的'`、`num: '42 字'`、
`numNote: '故意超长'`），douyin 1080×1440，直接调 `buildCover(browser, ep, 'douyin', …)`，
捕获 `e.message` 原样输出。未改 `video/episodes/**`。2026-10-22 Task 9 修复轮用同一夹具复跑，
输出与首轮逐字一致。

```text
douyin 封面装不下：head 超出 2130px（950×157 右1015 底617 / 界1015×1386 文宽3080，已缩到 75.6px）——把 cover.proof/num/line 改短，别指望裁掉
```

`.head` 的 157px 高 = 42 字整段（`keep-all` 不许在汉字之间断行）占一行 + `line2` 一行，两行都在
75.6px 地板下；`底617` 就是这个两行盒在 1440 高画布上居中后的下沿。缩字已到 `.head` 地板
`u*7 = 75.6px`，`scrollWidth 3080 > clientWidth 950` 仍是 2130px 出界；这里必须是硬失败，
不能靠截图把右半句裁掉。

## (h) 小红书标题 21 字（Task 9）

同一临时 episode 路径，`publish.xiaohongshu.title = '一'.repeat(21)`，其余字段合法；捕获原文：

```text
发布文案 task9-xhs/xiaohongshu：标题 21 字 > 20
```

## (i) codeLabel 行号未放行（Task 11 修复轮）

用例 `codeLabel 纳入审计，源码行号可用 exceptions 放行`（`video/tests/numbers.test.mjs`）：临时 episode 的
`codeLabel = 'probe.c:247-255'`，evidence/exceptions 均为空；用与 `cmdNumbers` 相同的逐行格式输出未命中项。
修复前的清册漏掉 `codeLabel` 字段，这类行号根本不会进审计；现在它必须像上屏文本一样有依据或显式例外。

```text
❌ task11-codeLabel: 2 个数字未命中
   - 247  @bilibili:a/codeLabel「probe.c:247-255」
   - 255  @bilibili:a/codeLabel「probe.c:247-255」
```

