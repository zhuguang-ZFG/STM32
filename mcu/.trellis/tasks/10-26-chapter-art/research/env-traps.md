# 行尾与环境陷阱

2026-10-26 量产批记录。

## docs/lab 的 CRLF 假阳性

`docs/lab/` 多章工作树是 CRLF（`git ls-files --eol` 显示 `i/lf w/crlf`），但 `.gitattributes` 要求 `* text=auto eol=lf`——索引是 LF，CRLF 是机器 checkout 的残留。`prose_guard` 的 frontmatter 正则 `\A---\n` 在 CRLF 源上不匹配，会误报「frontmatter 不一致 + 事实 token 丢失」。

**正确基线**：`git show HEAD:docs/lab/<章>.md | tr -d '\r'`，不是工作树文件。

## chapter-art 与并发写者

`mcu-book/book/assets/chapter-art/` 是 untracked 目录（git 无副本）。本日另一会话（并行线）在该目录反复写入滤镜版题图，三次覆盖本会话产物（含 3 枚已评审试点）。防护：

1. 量产期一律写 `.temp/art/`，收编由 `Main` 单点执行；
2. 收编后 `chmod -w` 全部 88 枚 + 6 枚附录图，阻断后续覆盖；
3. `mcu-book/print/art.py`、`mcu-book/tools/art_guard.py` 也各被回退一次——**构建前必须重 grep**：`art.py` 无 `_hw_filter`、`art_guard.py` 含 `--yuyu`。

## unicode em-dash 的 grep 陷阱

`grep "49.7"` 会命中表格行 `:49、75`（点号未转义）。核数字事实时用 python `str.count` 或转义点号。

## 校验工具的缓存

`tools/__pycache__/art_guard.cpython-313.pyc` 会在源被回退后继续呈现旧行为。改 guard 后 `rm -rf mcu-book/tools/__pycache__`，否则「绿」测的是旧规则。
