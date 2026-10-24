# STM32 知识库 —— 素材生成与自检
#
# 常用命令：
#   make assets    重新生成全部图片（纯 Python，零依赖）
#   make check     校验 SVG 与 GIF（GIF 会解码回像素比对）
#   make clean     清理 __pycache__ 等临时文件
#   make stats     统计仓库内容规模

PY ?= python3

.PHONY: assets animations boards diagrams gifs videos book book-pdf book-check check verify clean stats

assets: animations boards diagrams gifs videos

# 整书版：离线单文件 HTML；book-pdf 还需要 Chrome/Edge、Playwright 与 PyMuPDF。
book:
	$(PY) stm32-book/build_html.py

book-pdf:
	$(PY) stm32-book/build_html.py --pdf

book-check:
	$(PY) -m unittest discover stm32-book/tests -v
	$(PY) stm32-book/build_html.py --check

animations:
	$(PY) tools/gen_animations.py

boards:
	$(PY) tools/gen_boards.py
	$(PY) tools/gen_pinouts.py

diagrams:
	$(PY) tools/gen_diagrams.py

gifs:
	$(PY) tools/gen_gifs.py

# 海报是确定性的。配音成片用 python3 tools/gen_narrated.py --speak（要联网）。
videos:
	$(PY) tools/gen_narrated.py --posters

check:
	$(PY) tools/check_assets.py

# 一键验证「素材可由脚本复现」：重新生成后检查工作区是否有差异
verify: assets
	@if [ -n "$$(git status --porcelain assets/)" ]; then \
		echo "素材与脚本生成结果不一致，请提交生成结果："; \
		git --no-pager diff --stat assets/; exit 1; \
	else echo "素材与脚本一致 ✅"; fi
	$(PY) tools/check_assets.py

clean:
	find . -name '__pycache__' -type d -prune -exec rm -rf {} +
	find . -name '*.pyc' -delete

stats:
	@echo "章节   : $$(ls docs/[0-9][0-9]-*.md | wc -l) 章中文 + $$(ls docs/en/[0-9][0-9]-*.md | wc -l) 章英文，中文正文 $$(cat docs/[0-9][0-9]-*.md | wc -l) 行"
	@echo "示例   : $$(ls -d examples/*/ | wc -l) 个"
	@echo "速查表 : $$(ls cheatsheets/*速查表.md 2>/dev/null | wc -l) 份中文 + $$(ls docs/en/cheatsheets/*.md 2>/dev/null | wc -l) 份英文"
	@echo "SVG    : $$(find assets -name '*.svg' | wc -l) 张（动画 $$(ls assets/animations/*.svg | wc -l)）"
	@echo "GIF    : $$(find assets/gif -name '*.gif' | wc -l) 个"
	@echo "讲解片 : $$(find assets/video -name '*.mp4' 2>/dev/null | wc -l) 个 MP4"
	@echo "Renode : $$(ls sim/renode/*.resc 2>/dev/null | wc -l) 个脚本"
	@echo "体积   : $$(du -sh assets | cut -f1) (assets/)"
