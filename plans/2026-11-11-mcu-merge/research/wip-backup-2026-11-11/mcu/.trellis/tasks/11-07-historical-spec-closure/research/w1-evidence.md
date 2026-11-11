# W1 已有交付补证（2026-11-11，只读）

范围：B0/B1/B2/B7 的字节链、提交关联与发布路径；动画 D2 与阅读体验门的环境前置。未改生产文件、未安装依赖、未构建、未发布。

## 1. B0/B1/B2/B7 字节链

方法：对每个文件取旧历史（`cf161532` 及祖先）末次提交，比较三方：

1. `before` 快照 vs 该提交的父版本（`git show <commit>^:<path>`）逐字节；
2. 当前文件 vs `candidate` 快照逐字节；
3. 当前文件 vs 末次提交 blob（`git hash-object`）。

| 批次 | 文件 | before=父版本 | 当前=candidate | 当前=末次提交 blob | 末次提交 | 差异 |
|---|---|---|---|---|---|---|
| B0 | `docs/build/00-toolchain.md` | 是 | 是 | 是 `cee5312` | `de060be7` 2026-11-06 | +15/−13 |
| B1 | `docs/build/01-four-steps.md` | 是 | 是 | 是 `1ea5a9a` | `de060be7` 2026-11-06 | +15/−15 |
| B2 | `docs/build/02-elf.md` | 是 | 是 | 是 `ef5e363` | `de060be7` 2026-11-06 | +8/−8 |
| B7 | `docs/build/07-build-system.md` | 是 | 是 | 是 `919ce0a` | `cb3680ed` 2026-11-07（#17） | +4/−4 |

结论：四个文件自父版本以来的全部差异就是 before→candidate 的 diff，没有混入其他改动；B7 恰为四行替换。逐条 diff 见 `research/w1-language-diffs.md`。

## 2. 提交与发布关联（E2，不是 E6）

- 四个末次提交都在 `mcu-upstream/main`（迁移检查点 `cf161532`）与 `feat/mcu-subtree-merge` 上。
- 当前仓库 `main`（`b02cf3c0`）与 `mcu-upstream/main` **没有 merge-base**（两条独立历史），四个提交不是本地 `main` 的祖先。
- 根级工作流：`mcu-deploy.yml`、`mcu-book.yml` 仅在 push 到 `main` 且路径匹配 `mcu/**` 时触发；`book.yml` 明确 `paths-ignore: mcu/**`。因此这四个提交尚未经本仓库 `main` 部署。
- 未查询 CI 运行结果或线上页面；旧站是否已上线这四章属 E6，本轮未验证。

修正一条历史观察：任务卡中 B7“未提交/发布”的描述早于 `cb3680ed`（2026-11-07，PR #17）；当前状态是已提交在旧主线，但用户文字接受仍缺。

## 3. 动画/阅读门与环境前置

- 相关测试：`tests/animation-markdown.test.mjs`、`tests/a11y.test.mjs`、`tests/reading-time.test.mjs`。
- 相关脚本：`anim:lint`、`reading:check`、`a11y:check`，均被 `quality` 聚合调用。
- `animation-markdown.test.mjs:5` 直接 `import { loadConfigFromFile } from 'vite'`；`vite` 不在 `devDependencies`，但在 `package-lock.json` 中作为传递依赖存在（`node_modules/vite`，lock 第 3115 行，经 vitepress）。
- 当前检出无 `node_modules`，所以测试在模块解析阶段即失败；这不是断言失败，也不是产品回归。`npm ci` 按 lock 安装后应可消除该阻塞，但本轮未获授权、未执行。

## 4. 用户文字接受（E4，已接受）

`research/w1-language-diffs.md` 已按 B0/B1/B2/B7 汇总完整 diff。2026-11-11 用户回复「接受，授权」，对四批文字给出一致接受。范围为该文件所示 diff，不含发布、PDF 构建、整任务归档；字节链与历史提交仍未替代 E4，本次接受即 E4 记录。

## 5. W1 状态

| 项 | 状态 | 依据 |
|---|---|---|
| B0/B1/B2/B7 字节链与提交关联 | PASS（E1/E2） | 上表；4/4 三方一致 |
| B0/B1/B2/B7 用户文字接受 | PASS（E4） | 2026-11-11 用户「接受，授权」；范围见 `w1-language-diffs.md` |
| 动画 D2 回归 | UNVERIFIED | `vite` 缺失；`npm ci` 未执行 |
| D1/D3/D4 真实 surface | UNVERIFIED | 依赖未安装，未做 375px/深色/reduced-motion 实测 |
| operator 状态 | UNVERIFIED | 无合法基线，未运行 |

## 6. 授权修复与回归（2026-11-11 追加）

- `CITATION.cff` 的 `url` 由 `https://zhuguang-zfg.github.io/mcu/` 改为 `https://zhuguang-zfg.github.io/STM32/mcu/`；只改这一行，`repository-code` 与正文未动。
- `node scripts/docs-check.mjs`：exit 0，扫描 138 个 Markdown 文件，6 类检查（其中数字声明 27 条）。
- `npm ci` 已获授权执行；动画 D2/阅读相关回归结果在安装完成后补记。

## 7. 证据边界

- 本节只有 E1/E2/E3 前置事实；无 E4 用户接受、无 E6 线上回读、无 CI 运行证据。
- “当前=末次提交”只证明该文件内容与旧主线一致，不证明已部署、可访问或读者接受。
- 四批 diff 只覆盖各自文件的变更；不覆盖同批其他文件或跨章一致性。
