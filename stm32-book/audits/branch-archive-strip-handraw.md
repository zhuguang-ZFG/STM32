# Branch archive: feat/strip-spec-voice & feat/handraw-sketch-system

**Date (America/Adak):** 2026-11-04  
**Status:** **停更 / 归档** — 价值已按 Spec §9 Port A/B 抽进 `main`；sole development line = `main` + Overlay `stm32-book/BOOK_CLASSIC_CONVERGE_SPECS.md`。

## Tip SHAs (frozen reference)

| Branch | Tip SHA | Tip date (commit tz) | Tip subject |
| --- | --- | --- | --- |
| `feat/strip-spec-voice` | `b1f03cb20477098e0c251841d6e8be833218d8fa` | 2026-11-01 21:57:17 +0800 | docs(book): 前四节改成写给读者的话，文风硬门拦审稿用语 |
| `feat/handraw-sketch-system` | `23e319e0ed9676bf481a1ae6f7604daee1d693d9` | 2026-11-01 09:25:59 +0800 | docs(book): 平实文风与 sepia 去 AI 味，重写 00–19 章并补齐 14、28 章 |

Local + `origin/` tips match the SHAs above at archive time (`git rev-parse` / `git fetch`).

## What landed on main (not a full merge)

- **Port A (strip):** `tools/slop_lint.py` 审稿用语；`docs/CONTENT_GUIDE.md` / `docs/en/CONTENT_GUIDE.md` 读者规则；classic tip 已是 strip 审稿门禁超集。未整支 `git merge`（merge-tree ≈20 CONFLICT）。
- **Port B (handraw):** `.claude/skills/sepia*` 整树拷贝；`plain-voice` 并入第二遍 Sepia；节奏/分层/自测写入 CONTENT_GUIDE；Handraw 双轨合同在 Overlay §6。未整支 merge `docs/`（merge-tree ≈76 CONFLICT）。

## Remote policy (this archive)

- **Do not delete** `origin/feat/strip-spec-voice` or `origin/feat/handraw-sketch-system` in this pass.
- Branches remain as **read-only historical pointers**. No further feature work on them.
- README + Overlay §9.5 point readers to `main` as the only active line.
- Re-opening a parallel「去 AI 味」fork is forbidden (Overlay §9.5 item 3).

## Spec ticks

- Overlay §9.5 retirement steps 1–3 recorded here + Spec/README.
- Overlay §11.3 item「strip 与 handraw 按 §9 方式完成且旧支停更归档」→ **ticked**.
