# 本地构建修复与合并版 PDF 验收

- 日期：2026-11-18（全部时间 Asia/Shanghai）；本地 Git 根 `D:/Users/STM32`。
- HEAD：`5bbb52783a5a5a781ed5e5feb4b1af65a2d972ef`，本次未提交/暂存/推送/拉取。
- 基线：978 条 status 记录（853 修改、89 删除、36 未跟踪）；无暂存。保存外部 status 原始字节、tracked binary patch、关键文件原件/哈希与旧 PDF：`D:/Users/STM32-local-review-backup-20261118-154000`。

## WIP 审阅与边界

已有 WIP 包含手绘 SVG/PNG 及站点图发布（含 89 个现有删除）、`tools/handraw_track/publish_staged.py`、`book/checks.py` 的入口/徽标链接门、4 份新回归及各卷内容修订。没有重做、暂存或覆盖这些实现；复用既有入口/徽标/插图来源/发布测试。README/STRUCTURE 在其原有 WIP 上做定向入口说明修正。

本轮修改：`Makefile`、`tools/check_assets.py`、`book/build_print_edition.py`、`book/print_css.py`、`README.md`、`STRUCTURE.md`。新增 `book/README.md`、`book/tests/test_build_entrypoints.py`、本计划与本验收记录。历史合并计划及 B5 证据保持原样。

## 回归与修复

1. 8 项入口测试先观察到预期失败：Make 仍引用退役构建器/测试，缺失当前构建指南及合并版资产入口。
2. 现行资产门检查完整 47 章/6 附录、章节/入口链接与锚点/测验，以及 `docs/public` 全部 543 个 SVG/位图的 XML 与实际解码；坏 XML、坏 PNG、缺章、缺资源负例仍失败。不通过删除校验或空成功绕过退役英文树。旧布局的历史像素/视频检查保留，合并版不调用视频检查。
3. 用相邻用户 `.probe.png` 哨兵复现印刷器覆盖/删除风险后，改为内存截图；未修改动画或插图资产。
4. 首轮完整印刷 HTML 成功，PDF 被原有横向溢出门拦截：ch05 列表图片宽 1152px，而 li 宽约 625px。真实 Chromium 回归先红后绿；只扩展印刷 CSS 的图片容器约束，未削弱横向溢出检查。
5. 第二轮重新执行完整两阶段文档化管线（非手工跳过检查），成功输出 PDF。

## 最终验证（本次实际执行）

- `python -B -m book.manifest --check`：0。
- `python -B -m book.mapping --check`：0。
- `python -B -m book.checks --check`：0，`checks passed`。
- `python -B tools/check_assets.py`：0，543 资产 PASS。
- `python -B -m unittest discover book/tests -v`：0，87 tests OK、无跳过（含 10 项本轮入口/印刷回归及原有 WIP 测试；最小站点 CI 缺可选印刷/位图依赖时，新集成项会明确 skipped，不代表 PDF 验收）。
- `python -B -m book.build_html --check`：0，53 pages，0 planned missing；仅临时目录输出。
- 聚焦文件 `git diff --check`：0；仅 Git 的 LF→CRLF 提示，无空白错误。
- 日志与命令/退出码在外部 `final-verification.json`、`final-verify-*.log`。本机 PATH 没有 `make`，未声称执行过 Make 本身；配方由回归检查，等价 Python 阶段均实际执行。

## 当前 PDF（不覆盖唯一旧版）

- 文件：`D:\Users\STM32-local-review-backup-20261118-154000\build2\merged-book.pdf`。
- 大小：29,101,345 bytes（约 27.75 MiB）；824 页；63 条书签。
- 生成时间：2026-11-18 16:08:47（Asia/Shanghai）。
- SHA-256：`4a423fdfda12dc661146729514f0d303e0a2f7e3c35a91df41bac833cd7402fc`。
- 完整命令、阶段结束时间与日志：外部 `pdf-round2.json` / `pdf-round2-*.log`。输入 47 章 + 6 附录；源哈希核对覆盖 681 路径，第二轮构建期间到 QA 前无变化。
- 原 `book/dist/print/merged-book.pdf`（719 页）保持字节不变，原件另备份为外部 `merged-book-original.pdf`。

## 实际做过的 QA 与限制

- 抽取全文 813,651 字符；U+FFFD 数为 0；可检索书名、新上手章、GPIO/FreeRTOS/附录。
- PDF 17 个字体资源均可提取嵌入字节，含 NotoSansSC/NotoSerifSC、CascadiaMono 与中文后备字体。不是全书逐字形人工审查。
- 实际打开并目检渲染 PNG：p1 封面、p2 目录、p5/p6 新上手章、p67 代码、p74 图文、p80 原溢出工具图（按源 PNG 像素匹配定位）。样张在外部 `qa/`；抽样未见缺字、乱码或横向裁切。密集手绘图小字仍需放大阅读，未宣称全书印刷字号已逐页验收。
- 完整首轮 HTML 加载后、应用修复 CSS 的预检：0 破图、0 非嵌入 src、0 横向溢出；第二轮 PDF 的实际原生溢出/目录目的地/目录页码/空页/中文页眉门全部通过。
- 没有跑部署站点浏览器冒烟、远程 CI/Pages、EPUB 或全书逐页目检；没有连接或刷写硬件。封面原有“全程实物实验”措辞仍是旧文案，不能据此把正文 pending 项视为已实测，本轮未擅改内容口径。

## 下一步实测（只审阅，未执行）

`labs/README.md` 目前只登记以太网实验；ch09 E01 / ch12 E03 / ch13 E02 的实测表仍空。外部 `hardware-next.md` 给出具体步骤：先确认板卡/工程/时钟/接线；点灯记 10 周期与构建/烧录记录；PWM 留 PSC/ARR/CCR 回读和频率/高电平波形；UART 留 PCLK/BRR、原始位宽/解码/错误计数。所有实测值待真实执行填写。示例 README 中仍有退役章节链接，留待该批先核对，不盲目刷写。

本轮至此暂停。视频、旁白、动画/插图批量生成、`contact_sheet.py` 均未触碰；Make 的历史 assets/verify/stats 目标不属于本轮迁移或执行范围。

收尾依赖审查：既有 CI 仅安装 Markdown；新增位图/印刷集成测试显式标注可选依赖，避免把 PDF 工具链强加给站点单元门。没有改动原有测试或 CI。PDF 后仅补充说明/测试依赖注记与验收记录，章节、图片、构建器及 CSS 未再变化。

最终交付日志：外部 `delivery-verification.json` / `delivery-verify-*.log`，6 条命令全 0，87 项测试无跳过。收尾曾因本轮写入的重复 CRLF 导致新测试导入失败，已仅规范本轮新增测试/指南的换行并完整重跑；失败日志保留。电脑短暂不可达后，16:15（Asia/Shanghai）只读重试成功，HEAD 未变、986 条状态且原978条均保留。
