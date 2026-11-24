# STM32 知识库 —— 素材生成与自检
#
# 常用命令：
#   make assets    重新生成全部图片（纯 Python，零依赖）
#   make check     校验现行合并版章节、链接、测验与站点 SVG/位图
#   make clean     清理 __pycache__ 等临时文件
#   make stats     统计仓库内容规模

PY ?= python3

.PHONY: assets animations boards diagrams stack-diagrams gpio-classic illustrations samples gifs videos lesson-check book book-html book-pdf book-epub book-check site-check check lint-voice verify clean stats audit

assets: animations boards diagrams illustrations samples gifs videos

# 合并版：book 构建站点（VitePress，base /STM32/，产物 docs/.vitepress/dist）。
# book-html 是单文件印刷书稿（PDF/EPUB 的同源输入）；book-pdf / book-epub 依次生成。
# PDF 需要 Playwright Chromium、Pillow、PyMuPDF 与中文字体，见 book/README.md。
book:
	npm run docs:build

book-html:
	$(PY) -m book.build_print_edition

book-pdf: book-html
	$(PY) -m book.print_pdf --html book/dist/print/merged-book.html --meta book/dist/print/merged-book.meta.json --out book/dist/print/merged-book.pdf

book-epub: book-html
	$(PY) -m book.build_epub

book-check:
	$(PY) -m book.manifest --check
	$(PY) -m book.mapping --check
	$(PY) -m book.checks --check
	$(PY) -m unittest discover book/tests -v
	$(PY) -m book.build_html --check

# 站点门：构建 + 页面集合对账 + 旧链存根 + /STM32/ 冒烟（需要 npm ci 与 Chromium）
site-check:
	npm run docs:build
	npm run site:pages
	npm run site:stubs
	npm run site:assemble
	npm run site:smoke

animations:
	$(PY) tools/gen_animations.py

boards:
	$(PY) tools/gen_boards.py
	$(PY) tools/gen_pinouts.py

diagrams:
	$(PY) tools/gen_diagrams.py

stack-diagrams:
	$(PY) tools/gen_stack_diagrams.py --render

gpio-classic:
	$(PY) tools/gen_gpio_classic.py

illustrations:
	$(PY) tools/gen_handdraw_illustrations.py

samples: gpio-classic
	$(PY) tools/gen_sample_figures.py

gifs:
	$(PY) tools/gen_gifs.py

# 海报是确定性的。配音成片用 python3 tools/gen_narrated.py --speak（要联网）。
videos:
	$(PY) tools/gen_narrated.py --posters

lesson-check:
	$(PY) tools/gen_long_lesson.py --check

check:
	$(PY) tools/check_assets.py

# 文风硬门：查 Markdown 里的 AI 味（套话、营销词、判定符号、装饰 emoji）
lint-voice:
	$(PY) tools/slop_lint.py

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
	@echo "chapters : $$(python -c \"import json; d=json.load(open('docs/manifest.json',encoding='utf-8')); print(sum(len(p['chapters']) for p in d['parts']))\") chapters + $$(python -c \"import json; print(len(json.load(open('docs/manifest.json',encoding='utf-8'))['appendices']))\") appendices"
	@echo "examples : $$(ls -d examples/*/ 2>/dev/null | wc -l) dirs"
	@echo "cheatsheets: $$(ls cheatsheets/*.md 2>/dev/null | wc -l) files"
	@echo "SVG      : $$(find assets -name '*.svg' 2>/dev/null | wc -l) files"
	@echo "GIF      : $$(find assets/gif -name '*.gif' 2>/dev/null | wc -l) files"
	@echo "video    : $$(find assets/video -name '*.mp4' 2>/dev/null | wc -l) mp4"
	@echo "Renode   : $$(ls sim/renode/*.resc 2>/dev/null | wc -l) scripts"
	@echo "size     : $$(du -sh assets 2>/dev/null | cut -f1) (assets/)"

audit:
	$(PY) tools/audit_book.py
