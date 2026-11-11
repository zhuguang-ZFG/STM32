"""prose_guard 的双模式契约测试。

- compare()：逐字润色轮——受保护段字节级一致、事实 token 多重集一致、散文破折号 ≤2
- compare_additive()：内容增补轮——允许新增散文/行内代码，但禁改删除既有受保护内容、
  禁出现原文没有的事实值、破折号仍 ≤2

守卫自身出错会静默放行，所以每条判据都要有正反两面。
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import prose_guard as pg  # noqa: E402  # type: ignore[import-not-found]

BASE = """---
title: 测试章
---

# 测试章

默认组一：`0x40020000` 是 GPIOA，写 `32 位` 值。

## 本章精髓

1. 中断号 37 对应 USART1，延迟 1ms 为 27000 个 tick。

| 寄存器 | 偏移 |
|---|---|
| MODER | 0x00 |

```c
int main(void) { return 0; }
```
"""


def _write(tmp_path: Path, name: str, text: str) -> Path:
    p = tmp_path / name
    p.write_bytes(text.encode("utf-8"))
    return p


def test_prose_edit_within_limits_passes(tmp_path):
    new = BASE.replace("默认组一：", "默认组一的说明：")
    assert pg.compare(_write(tmp_path, "a.md", BASE), _write(tmp_path, "b.md", new)) == []


def test_table_edit_fails(tmp_path):
    new = BASE.replace("| MODER | 0x00 |", "| MODER | 0x04 |")
    errs = pg.compare(_write(tmp_path, "a.md", BASE), _write(tmp_path, "b.md", new))
    assert any("表格行" in e for e in errs)


def test_fence_edit_fails(tmp_path):
    new = BASE.replace("int main(void) { return 0; }", "int main(void) { return 1; }")
    errs = pg.compare(_write(tmp_path, "a.md", BASE), _write(tmp_path, "b.md", new))
    assert any("代码围栏块" in e for e in errs)


def test_invented_fact_fails(tmp_path):
    new = BASE.replace("27000 个 tick", "28000 个 tick")
    errs = pg.compare(_write(tmp_path, "a.md", BASE), _write(tmp_path, "b.md", new))
    assert any("事实 token" in e for e in errs)


def test_crlf_fails(tmp_path):
    p = tmp_path / "b.md"
    p.write_bytes(BASE.replace("\n", "\r\n").encode("utf-8"))
    errs = pg.compare(_write(tmp_path, "a.md", BASE), p)
    assert any("CR" in e for e in errs)


# ---- 内容增补模式 ----

def test_additive_new_prose_and_code_passes(tmp_path):
    """增补轮：新增解释段落、新增行内代码是合法的（讲新概念必然引新符号）。"""
    new = BASE.replace(
        "默认组一：",
        "先说为什么：门牌号不变，只是楼名从 1 号楼改叫 0 号楼。对应 `USART0_IRQn` 这个写法。\n\n默认组一：",
    )
    assert pg.compare_additive(_write(tmp_path, "a.md", BASE), _write(tmp_path, "b.md", new)) == []


def test_additive_table_rewrite_fails(tmp_path):
    new = BASE.replace("| 寄存器 | 偏移 |", "| 寄存器 | 地址 |")
    errs = pg.compare_additive(_write(tmp_path, "a.md", BASE), _write(tmp_path, "b.md", new))
    assert any("表格行" in e for e in errs)


def test_additive_removed_inline_code_fails(tmp_path):
    new = BASE.replace("写 `32 位` 值", "写值")
    errs = pg.compare_additive(_write(tmp_path, "a.md", BASE), _write(tmp_path, "b.md", new))
    assert any("行内代码" in e for e in errs)


def test_additive_invented_value_fails(tmp_path):
    """原文全文（含表格/代码）都没有的数值，增补模式也必须拦。"""
    new = BASE.replace("默认组一：", "默认组一（延迟 99 个周期）：")
    errs = pg.compare_additive(_write(tmp_path, "a.md", BASE), _write(tmp_path, "b.md", new))
    assert any("原文没有的事实值" in e for e in errs)


def test_additive_dash_limit(tmp_path):
    new = BASE.replace("默认组一：", "解释甲——补充乙——再次丙——")
    errs = pg.compare_additive(_write(tmp_path, "a.md", BASE), _write(tmp_path, "b.md", new))
    assert any("破折号" in e for e in errs)


def test_additive_verbatim_copy_passes(tmp_path):
    """原样复制应通过（增补轮允许不改）。"""
    assert pg.compare_additive(_write(tmp_path, "a.md", BASE), _write(tmp_path, "b.md", BASE)) == []


class TestSingleMode:
    """--single 新章起草门：无原文可对照，对单文件绝对计数。"""

    def _run(self, tmp_path, monkeypatch, text: str, name: str = "new.md") -> int:
        f = tmp_path / name
        f.write_text(text, encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["prose_guard.py", "--single", str(f)])
        return pg.main()

    def test_within_budget_passes(self, tmp_path, monkeypatch):
        assert self._run(tmp_path, monkeypatch, "手册说错了。位表在这里。顺序也行。\n") == 0

    def test_over_budget_fails(self, tmp_path, monkeypatch):
        text = "一句——两句——三句——四句。记住：这个。一句话搞定。\n"
        assert self._run(tmp_path, monkeypatch, text) == 1

    def test_container_label_not_counted_as_prose(self, tmp_path, monkeypatch):
        text = "::: tip 一句话记住\n**这是容器，不算散文。**\n:::\n\n正文一句。\n"
        assert self._run(tmp_path, monkeypatch, text) == 0


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
