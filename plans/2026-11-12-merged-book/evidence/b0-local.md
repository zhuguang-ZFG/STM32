# B0 本地验收证据

- 日期：2026-11-12
- 分支：feat/merged-book-b0
- commit：`a06d76e0a7e4db5d12e0195531b0ff2c5e346e10`
- 环境：Windows + Git Bash；Python 3.13.14；Node 24.14.0

| 命令 | 退出码 | 结果 |
| --- | --- | --- |
| `python -m book.manifest --check` | 0 | manifest 与 toc.tsv 一致 |
| `python -m book.mapping --check` | 0 | 141 行映射覆盖全部源 |
| `python -m unittest discover book/tests -v` | 0 | 16 passed |
| `node --test scripts/tests/legacy-redirects.test.mjs` | 0 | 2 passed；94 存根 |

未验证：CI 远程运行结果（本批只做本地；推送需另行授权）。
