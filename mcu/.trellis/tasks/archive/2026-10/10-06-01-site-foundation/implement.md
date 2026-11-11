# 实施计划：站点奠基

## 执行顺序

- [ ] 1. 脚手架：`package.json`（vitepress）→ `npm install` → `docs/index.md` 首页 → `docs/.vitepress/theme/`（index.ts + custom.css）→ `docs/.vitepress/config.mts` 最小骨架（先跑通 dev/build）
- [ ] 2. 金标准样例 `docs/c/06-abi-stack.md`（含 stack-frame.svg 引用）+ 动画 `docs/public/anim/stack-frame.svg`
- [ ] 3. 分派 4 worker（A/B/C/D，范围见 design.md §8），附上 design.md 路径+样例路径
- [ ] 4. 并行亲写：动画 irq-entry.svg、context-switch.svg；`docs/stm32/00-env.md` + `code/stm32/00-blink/` 全套（startup/ld/Makefile/main.c）；`docs/esp32/00-env.md` + `code/esp32/00-hello/`；`docs/lab/template.md` + `docs/lab/e01-blink.md` + SVG 接线图
- [ ] 5. 门面：README.md、CONTRIBUTING.md（含章节模板/风格契约/动画规范/实物规范）
- [ ] 6. worker 产出回收 → 主 agent 抽查（每 worker ≥3 页：钩子/锚点/四件套/坑是否实质）→ 不合格打回重写要点
- [ ] 7. `config.mts` 全量 sidebar（按 design.md §3）
- [ ] 8. 构建验证（见下）→ 修复
- [ ] 9. `.trellis/spec/` 重写（任务 00）：按真实结构出 docs-site / firmware-stm32 / firmware-esp32 / content-guides 四层规范，删除 fullstack 模板
- [ ] 10. journal 记录 → git commit（本地，不推送）→ 归档任务 00 与本任务

## 验证命令

```bash
# 构建（主验收）
npm run docs:build

# 死链/占位
grep -rn "TODO\|待补充\|placeholder\|本章将介绍" docs/ --include="*.md"   # 期望无命中

# 页面计数（≈70 + 首页/索引）
find docs -name "*.md" | wc -l                                          # 期望 ≥ 75

# 动画就位
ls docs/public/anim/                                                    # 3 个 svg

# dev 冒烟（手动浏览侧边栏全展开无 404）
npm run docs:dev
```

抽查清单：每板块随机 1 页对照 §2 模板逐项打勾；stm32/00-env 与 e01 的寄存器地址逐位对 RM0090（GPIOF base 0x40021400、RCC_AHB1ENR 0x40023830、BSRR 偏移 0x18）。

## 回滚点

- 步骤 1 完成后 commit 一次（脚手架基线）；worker 回收前 commit 一次；最终一次。任何大规模返工回到前一基线。

## 备注

- 子代理上下文：worker 通过 omp `task` 工具分派，上下文直接引用 `.trellis/tasks/10-06-01-site-foundation/design.md` 与样例页路径（本仓库文件，worker 可读）；不额外维护 implement.jsonl。
- 上板验证不在本任务；stm32/00-env、e01 标注"待上板验证"，用户持板可实测。
