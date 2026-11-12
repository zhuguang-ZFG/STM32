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
| 动画 D2 回归 | PASS（2026-11-12） | 回归 12/12、a11y 6/6、reading 6/6；三页真实 UI 均有 svg/按钮/`data-anim`；`anim:lint` 111 图通过；`book:check` PASS。见 §8 |
| D1/D3/D4 真实 surface | PASS（2026-11-12） | D1 末帧 10.8s/12s 字幕可见；D3 放大 680px > 行内 293px、标签有效字号 12.28 > 5.29（浅/深均测）；D4 焦点入对话框/关闭回退、滚轮与键盘锁滚。见 §8 |
| operator 状态 | UNVERIFIED | `verification-baseline-unavailable`，无合法基线；本轮未运行，不当作通过 |

## 6. 授权修复与回归（2026-11-11 追加）

- `CITATION.cff` 的 `url` 由 `https://zhuguang-zfg.github.io/mcu/` 改为 `https://zhuguang-zfg.github.io/STM32/mcu/`；只改这一行，`repository-code` 与正文未动。
- `node scripts/docs-check.mjs`：exit 0，扫描 138 个 Markdown 文件，6 类检查（其中数字声明 27 条）。
- `npm ci` 已获授权执行；动画 D2/阅读相关回归结果在安装完成后补记。

## 7. 证据边界

- 本节只有 E1/E2/E3 前置事实；无 E4 用户接受、无 E6 线上回读、无 CI 运行证据。
- “当前=末次提交”只证明该文件内容与旧主线一致，不证明已部署、可访问或读者接受。
- 四批 diff 只覆盖各自文件的变更；不覆盖同批其他文件或跨章一致性。

## 8. 2026-11-12 真实 surface 实测（W1 收尾）

环境：`D:\Users\STM32\mcu`；Node v24.14.0 / npm 11.9.0 / Python 3.13.14；`node_modules` 已按 lock 安装（`npm ci` 已获授权）。站点以 VitePress dev server 提供，base `http://localhost:5173/STM32/mcu/`；`docs:build` 因本机进程内存上限（约 550 MB）OOM 无法完成，改用 dev server 渲染同一组件与 CSS（限制见 §8.4）。

### 8.1 D1 / D3 / D4（`/c/03-volatile`）

| 项 | 实测 | 判定 |
|---|---|---|
| D1 元信息 | `12s 一轮 · 系统偏好减少动效，已停在静止帧` | PASS |
| D1 静止帧 | `reducedMotion: reduce` 下 `svg.getCurrentTime() = 10.800000190734863`（12 × 0.9）；`.anim-figure.is-paused`；按钮文案「播放」 | PASS |
| D1 结论字幕 | `④ 边界：它不保证原子、不保证顺序；跨执行流的正确性要靠别的机制`，`opacity = 1`；截图 `d1-reduced-motion.png` | PASS |
| D3 放大宽度 | 375px：行内 SVG 293px → 放大 680px（浅色与深色同值） | PASS |
| D3 标签有效字号 | 行内 5.29px → 放大 12.28px（`labelFs 13 × 680/720`）；截图 `d3-inline-375-{light,dark}.png`、`d3-d4-zoom-375-{light,dark}.png` | PASS |
| D4 打开焦点 | `document.activeElement` 为 `.anim-lightbox__close`，位于 `.anim-lightbox__card` 内，`body.style.overflow = hidden` | PASS |
| D4 锁滚 | 滚轮 400px：`scrollY 2794 → 2794`；`PageDown`/`ArrowDown`：`2794 → 2794` | PASS |
| D4 关闭回退 | `Escape` 后 `.anim-lightbox` 消失、焦点回到 `.anim-figure__zoom`、`body.style.overflow` 还原为空 | PASS |

观察（非缺陷）：`overflow: hidden` 下浏览器仍允许 `window.scrollBy/scrollTo` 程序化滚动（实测 2794 → 3194 → 0）。这不是用户可达路径（滚轮/触摸/键盘均被锁），按原生语义记录，不改实现。

### 8.2 D2 三页真实 UI 与回归

| 页 | `.anim-figure` | 详情 |
|---|---|---|
| `build/00-toolchain` | 1 | `data-anim=toolchain-relay`，svg/放大/播放按钮均在 |
| `build/06-flash-debug` | 1 | `data-anim=swd-debug-chain`，svg/放大/播放按钮均在 |
| `c/00-c-in-mcu` | 1 | `data-anim=embedded-c-diff`，svg/放大/播放按钮均在 |

回归与门禁（均 exit 0）：

- `node --test tests/animation-markdown.test.mjs`：12 pass / 0 fail（D2 parser 边界）。
- `node --test tests/a11y.test.mjs`：6 pass / 0 fail；`node --test tests/reading-time.test.mjs`：6 pass / 0 fail。
- `npm run anim:lint`：111 张图全部通过（源 SVG 未改）。
- `npm run book:check`：PASS（94 章，插图 94/94；`mcu-book/` 无改动）。

### 8.3 迁移接线缺陷与修复（归属合并批次，不并入本任务生产改动）

- 现象：`npm run docs:build` 的 `docs:gen` 步骤从仓库根执行 `git log` 时按仓库根路径解析，把根 STM32 仓的 `docs/en/**` 历史当成 MCU 已删文件，生成器以 exit 1 失败（迁移后 92fc917c 起复现）。
- 修复（2026-11-12，工作区未提交）：`mcu/scripts/gen-progress.mjs` 的 `git log` 增加 `--relative -- .`，限定到项目目录。
- 验证：`npm run docs:gen` exit 0（成稿 86/86、实验 8/8、动画 111、示例 47）；`npm run docs:check` exit 0（138 文件/6 类/27 条数字声明）；已跟踪生产文件中仅此一处脚本改动，归合并分支 P2「导读/生成路径」批次复核，不记为本任务的验收改动。

### 8.4 未完成与原因

| 项 | 状态 | 原因 |
|---|---|---|
| `npm run docs:build`（vitepress build） | NOT_RUN（环境阻塞） | 本机 Node 进程内存上限约 550 MB，vitepress build OOM；dev server（detached 进程）可运行。 |
| `npm run test:browser` | NOT_RUN | 依赖 `docs:build` 产物；且 `playwright.config.mjs` 的 `baseURL/webServer.url` 仍为旧 `/mcu/`，迁移后需随合并 P2 修复。未改测试配置（本任务边界要求单独 review）。 |
| `task_verify` / operator | UNVERIFIED | `verification-baseline-unavailable`，无合法基线；按原任务要求如实标注。 |

证据文件：`.temp/w1-surface/`（`results.json`、`d1-result.json`、6 张截图、`run.log`），位于 gitignore 的 `.temp/`。
