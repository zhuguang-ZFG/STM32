# 双书合并执行记录

设计规格：[docs/superpowers/specs/2026-11-12-merged-book-design.md](../../docs/superpowers/specs/2026-11-12-merged-book-design.md)

## 批次状态

| 批次 | 内容 | 状态 |
| --- | --- | --- |
| B0 | manifest、mapping、契约检查器、跳转存根、CI 门 | 本批完成（本地） |
| B1 | 卷 0–1（17 章）改写 | 本批完成（本地） |
| B2 | 卷 2–3（10 章） | 本批完成（本地） |
| B3 | 卷 4–5（12 章 + motor 合流） | 待开始 |
| B4 | 卷 6–7 + 6 附录 | 待开始 |
| B5 | `/STM32/` 切换、旧链归档 | 待开始；需发布指令 |

## 本批校验命令

```bash
python -m book.manifest --check
python -m book.mapping --check
python -m unittest discover book/tests -v
python -m book.checks --check
python tools/slop_lint.py docs/v0-foundations/*.md docs/v1-drivers/*.md docs/v2-reliability/*.md docs/v3-rtos/*.md
python -m book.build_html --check
node --test scripts/tests/legacy-redirects.test.mjs
```

## 数据文件

- `book/data/toc.tsv`：46 章 + 6 附录的目录数据。
- `book/data/mapping.tsv`：两书 123 章 + 附录 + motor 草稿的逐文件去向；含 `purpose`、`status`（planned/partial/migrated），状态必须与章节文件存在性一致。
- `book/requirements.txt`：固定 `markdown==3.11`。
- `docs/manifest.json`、`mapping.json`：由脚本生成，不手工编辑。
- B2 结束时迁移状态：B1 各章（`docs/01–17`）与 B2 涉及的根书章（`docs/11`、`docs/15`、`docs/16`、`docs/17`、`docs/28`）及 RTOS 深潜源（`mcu/docs/rtos/freertos/00–08`、`mcu/docs/rtos/rtthread/00–06`、`mcu/docs/rtos/compare/00–01`）均已 `migrated`；`mcu/docs/lab/e04-priority-inversion.md` 与 `e06-lowpower-current.md` 仍 `partial`（等 B4 的 ch40）。

## 说明

- 英文版策略固定为 `archive`，B5 删除前打 tag。
- 旧 URL 跳转的站点级页面（guide/reference 等）在 B5 扩展，本批只覆盖 94 个 MCU 章节。
- 临时静态站由 `book/build_html.py` 生成到 `book/dist/site/`（已 gitignore）；VitePress 站点切换仍归 B5。
