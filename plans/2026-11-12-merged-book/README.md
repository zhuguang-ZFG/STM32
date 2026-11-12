# 双书合并执行记录

设计规格：[docs/superpowers/specs/2026-11-12-merged-book-design.md](../../docs/superpowers/specs/2026-11-12-merged-book-design.md)

## 批次状态

| 批次 | 内容 | 状态 |
| --- | --- | --- |
| B0 | manifest、mapping、契约检查器、跳转存根、CI 门 | 本批完成（本地） |
| B1 | 卷 0–1（17 章）改写 | 待开始 |
| B2 | 卷 2–3（10 章） | 待开始 |
| B3 | 卷 4–5（12 章 + motor 合流） | 待开始 |
| B4 | 卷 6–7 + 6 附录 | 待开始 |
| B5 | `/STM32/` 切换、旧链归档 | 待开始；需发布指令 |

## 本批校验命令

```bash
python -m book.manifest --check
python -m book.mapping --check
python -m unittest discover book/tests -v
node --test scripts/tests/legacy-redirects.test.mjs
```

## 数据文件

- `book/data/toc.tsv`：46 章 + 6 附录的目录数据。
- `book/data/mapping.tsv`：两书 123 章 + 附录 + motor 草稿的逐文件去向。
- `docs/manifest.json`、`mapping.json`：由脚本生成，不手工编辑。

## 说明

- 英文版策略固定为 `archive`，B5 删除前打 tag。
- 旧 URL 跳转的站点级页面（guide/reference 等）在 B5 扩展，本批只覆盖 94 个 MCU 章节。
