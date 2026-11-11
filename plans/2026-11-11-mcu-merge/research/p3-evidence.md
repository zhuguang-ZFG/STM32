# P3 执行证据（AC4）

日期：2026-11-11 · 候选 worktree `D:\Users\STM32-mcu-merge-p1`（分支 `feat/mcu-merge-p1`）

## 交付物（implement.md §5 全项）

**1. Pages staging 组装脚本** `mcu/scripts/assemble-pages.mjs`：
- staging 根 = `index.html`（临时重定向页，canonical 由 site-config 单源派生）+ `mcu/**`（完整站点产物）
- 内置三门自检，任一失败退出 1 禁传：
  - 缺 `mcu/index.html` → 失败
  - 根入口与站点首页同内容（首页顶到根）→ 失败
  - 全量资源落位：扫描 staging/mcu 下所有 HTML 的 src/href；站内绝对路径必须以 `/STM32/mcu/` 开头且按 Pages 扩展名省略口径（`/x` → `x`/`x.html`/`x/index.html`）落位；相对引用必须存在 → 任一击穿即失败

**2. 部署 workflow 改造**（`.github/workflows/mcu-deploy.yml`）：
download-artifact → 源产物双检（保留）→ `assemble-pages.mjs --dist site --out ../.temp/pages-site` → **staging 终检**（`pages-check` + `search-check --dist ../.temp/pages-site/mcu`，对真正上传的那一份）→ **挂载冒烟**（`mount-smoke.mjs --root ../.temp/pages-site --mount /STM32`）→ upload-pages-artifact `path: .temp/pages-site` → deploy-pages。

**3. 挂载冒烟** `mcu/scripts/mount-smoke.mjs`：staging 按 `/STM32/` 起真实 HTTP 服务，Chromium 断言：
- 根入口 200 且为重定向页；`/STM32/mcu/` 首页真实导航（`#app` + title）
- 章节深链真实导航（首页动态发现 → goto → h1 存在）
- 同源 requestfailed / HTTP≥400 监听（CSS/JS/图片/字体随页面加载实际触发）
- 客户端搜索交互（开搜索框 → 输入 RCC → 结果出现）
- 导读：书页 + book-guide index/manifest；book/downloads HTTP 200

**4. 回归测试**：
- `tests/assemble-pages.test.mjs` 8 用例（fixture 驱动）：三失败模式 + 正常组装 + 外部引用豁免 + 相对缺失 + parseArgs
- `tests/workflow.test.mjs` AC4 用例重写：脚本调用、staging 终检、冒烟、upload 指向、全序断言；**对上一版提交 be295998（内联 shell）反跑必红**（asmIdx=-1 / upload=mcu/public，已实测）

## 真实产物验证（非 fixture）

dist 为 `npm run quality` 构建的真实产物（90+ 页）+ 整书链产物。

| 步骤 | 结果 |
|---|---|
| assemble（初跑，未兼容 cleanUrls） | 1172 个落位问题——全部来自扩展名省略链接，口径修正后 1 个 |
| assemble（修正后） | `✖ gd32/01-rcu-clock.html: 相对引用 ./02-gpio-af.md 不存在`——抓到**预存线上 bug**：源文件 187 行 raw HTML 的 `.md` 链接（vitepress 不改写 raw HTML href），旧站同样带病 |
| 源修复 | `docs/gd32/01-rcu-clock.md` `.md`→`.html`，全仓 grep 确认仅此 1 处 |
| assemble（源修复重建后） | 见下「最终跑」 |
| staging `pages-check --dist ../.temp/pages-site/mcu` | ✓ 132 页 / 2624 锚点链接全命中 |
| staging `search-check --dist ../.temp/pages-site/mcu` | ✓ 2124 标题可被搜索翻到（64320 terms） |
| 挂载冒烟（Chromium） | 见下「最终跑」 |

## 最终跑（真实产物重建后，全绿）

dist = vitepress 重建（49s，含 gd32/adc 修复）+ 整书链（PDF 契约 PASS：1211 页、字体全可嵌；downloads 7 文件 + SHA256 自证 PASS）。

| 步骤 | 结果 |
|---|---|
| `assemble-pages.mjs --dist docs/.vitepress/dist --out ../.temp/pages-site` | **staging OK：655 文件、136 HTML、10015 条资源引用落位校验全通过**（cleanUrls 扩展名省略口径） |
| `pages-check --dist ../.temp/pages-site/mcu` | ✓ 136 页 / 8921 锚点链接全命中 |
| `search-check --dist ../.temp/pages-site/mcu` | ✓ 2124 标题可搜到（64320 terms） |
| `mount-smoke.mjs --root ../.temp/pages-site --mount /STM32`（Chromium） | **12/12 通过**：根入口重定向页、首页 200「通往单片机之路」、章节深链 200+ h1、客户端搜索「RCC」出结果、导读页+book-guide index/manifest、book HTML、downloads 4 文件（含 PDF） |

## 新门禁在真实产物上抓到的预存缺陷（已修）

| 缺陷 | 来源 | 修复 |
|---|---|---|
| `gd32/01-rcu-clock.html` 相对引用 `./02-gpio-af.md` | 源 md 187 行 raw HTML `<a href>`，vitepress 不改写 raw HTML——旧站线上即 404 | `.md`→`.html`（全仓唯一 1 处） |
| 整书 HTML 3 处坏链（href 指向 `bit25:24, 1242-1246` 这类文本） | `docs/stm32/09-adc.md` 寄存器表把字段位宽 `RES[1:0]` 与手册出处 `(bit25:24, …)` 连写，被 Python markdown 解析成链接（vitepress 侧因 URL 含逗号+空格不解析，故只烂在整书） | 位宽与出处分开写并转义括号；重建后坏 href 计数 = 0 |

## 触发矩阵核查（§5 条目）

- 分支保护：gh api 实测 `main` 与 `feat/mcu-subtree-merge` 均 **Branch not protected**——无 required checks 被路径过滤卡死的死锁面。
- 发布门内部性：deploy 的 quality 为 `workflow_call` 复用，随 deploy 强制同提交运行；`needs.quality.result == 'success'` + `refs/heads/main`。
- affected 集合：deploy push 路径 `mcu/**` + `mcu-*.yml`；book.yml `paths-ignore` 互补；组装脚本本身在 `mcu/scripts/**` 内，改动必触发。
- Pages 现状：gh api `repos/.../pages` 404——当前无线上 Pages，首次 deploy 即挂载 /STM32/，无旧站内容被覆盖风险（AC8 快照要点）。

## AC4 判定

artifact 组装 + staging 终检 + 真实挂载浏览器冒烟 + 三失败模式回归全部落地并过真实产物。**AC4 通过（本地集成部分）**；线上回读仍属 AC8/P5 关闭条件。

## 遗留

- 根重定向页为临时方案；STM32 书将来入站时扩展 assemble（workflow 注释已声明）。
- `video/jobs/**` 与 `gen_cards_batch2.py` 历史作业产物登记不修（见 p2-string-classification.md）。
- 远程 `mcu-upstream` remote 指向已消失的 `D:/Users/mcu/.git`，P5 清理。
