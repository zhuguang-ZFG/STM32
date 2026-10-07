# STM32 知识库 —— 素材生成与自检
#
# 常用命令：
#   make assets    重新生成全部图片（纯 Python，零依赖）
#   make check     校验 SVG 与 GIF（GIF 会解码回像素比对）
#   make clean     清理 __pycache__ 等临时文件
#   make stats     统计仓库内容规模

PY ?= python3

.PHONY: assets animations boards diagrams gifs videos check verify clean stats

assets: animations boards diagrams gifs videos

animations:
	$(PY) tools/gen_animations.py

boards:
	$(PY) tools/gen_boards.py

diagrams:
	$(PY) tools/gen_diagrams.py

gifs:
	$(PY) tools/gen_gifs.py

videos:
	$(PY) tools/gen_videos.py

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
	@echo "文档   : $$(ls docs/*.md | wc -l) 篇，共 $$(cat docs/*.md | wc -l) 行"
	@echo "示例   : $$(ls -d examples/*/ | wc -l) 个"
	@echo "速查表 : $$(ls cheatsheets/*.md 2>/dev/null | wc -l) 份"
	@echo "SVG    : $$(find assets -name '*.svg' | wc -l) 张（动画 $$(ls assets/animations/*.svg | wc -l)）"
	@echo "GIF    : $$(find assets/gif -name '*.gif' | wc -l) 个"
	@echo "讲解片 : $$(find assets/video -name '*.gif' 2>/dev/null | wc -l) 个"
	@echo "体积   : $$(du -sh assets | cut -f1) (assets/)"
