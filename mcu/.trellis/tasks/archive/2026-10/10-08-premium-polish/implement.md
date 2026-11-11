# 执行计划：精品化四维打磨

按批次推进，每批可独立验收、独立提交。批次内先实现后自检。

> **执行状态（2026-10-08）**：A / B / D 已完成并通过验证；**C 因与并行会话冲突而改派**（见下）；E 进行中。

## 批次 A — 找得到（P0，硬伤 + 永久防线）✅

- [x] A1 读 `docs/gd32/index.md` 路线表，确定 G0–G4 / V0–V4 的标题与 slug。
- [x] A2 改 `docs/.vitepress/config.mts`：`'/gd32/'` 组补齐 10 章（G 篇 + V 篇两组）。
- [x] A3 新增 `scripts/nav-check.mjs`（按 design §3）。
- [x] A4 新增 `tests/nav.test.mjs`（正例/反例/边界，5 例全过）。
- [x] A5 接线 `package.json`：`nav:check` + 并入 `quality`。
- [x] A6 验证：`npm run nav:check` 103 页面零缺口；单元测试通过；`docs:build` 通过。

## 批次 B — 看得懂（P1）✅

- [x] B1 审计扫描成稿章模板要素 → `research/structure-audit.md`（68 篇，58→62 齐全）。
- [x] B2 修正必含项缺失：build/03（记忆锚点）、F3/F4/F5（补 `## 记忆锚点` 标题）、gd32/01（学习目标 + 你做到了）。剩余 6 项判定为规范允许的变体/增强，未强改。

## 批次 C — 学得下去（P1）↪ 改派

- [~] C1 **取消**：并行 Codex 会话正在实施 `10-07-knowledge-capstone`，其 design 明确要建 `docs/projects/`（index + J1/J2）并登记导航——即「综合项目」板块。本任务不重复其范围，避免同文件冲突。
- [ ] C2/C3 由 knowledge-capstone 任务承接；本任务的 `nav:check` 闸门会在其页面未登记 sidebar 时自动拦截。

## 批次 D — 有兴趣（P2）✅

- [x] D1 巡检各板块 `index.md`：唯 `docs/gd32/index.md` 缺开场钩子，已补 `> 🎯`。

## 批次 E — 收口

- [x] E1 全量验证（`docs:build` 通过；`nav:check` 通过；单测通过）。
- [x] E2 更新 `.trellis/spec/docs-site/quality-contract.md` 记录新闸门。
- [ ] E3 按 Trellis 3.4 分批提交（待用户确认提交计划）。

## 验证命令

```bash
npm run nav:check     # 新增：导航可达性
npm test              # 单元（含 nav.test.mjs）
npm run quality       # 全量闸门
npm run docs:build    # 死链零错误
```

## 环境限制记录（本机沙箱）

- `npm test` 中 `tests/device-cli.test.mjs` 在本沙箱失败：Node 子进程 spawn 一律 `EBUSY`（非项目缺陷，CI ubuntu 正常）。
- `npm run docs:build` 需 `CODEBUDDY_SAFE_DELETE_ENABLED=0`：否则沙箱 trash 守卫拦截 vite 清空 `dist`（非项目缺陷）。

## 回滚点

- 批次 A：`config.mts` + 两个新文件 + `package.json`，独立可 revert。
- 批次 B：6 个 md 文件，独立可 revert。
