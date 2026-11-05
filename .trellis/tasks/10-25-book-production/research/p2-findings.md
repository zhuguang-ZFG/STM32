# P2 全量印前排版：字体净化五连击 + 评审修回两条（2026-10-25 实测）

产物：`.temp/book-p2-final2/mcu-deep-book-print.pdf`（1119 页，185.3×260.3 mm ✓，末页 1119/1119 ✓）。
全部判定数据来自真实产物的 PyMuPDF 逐页 span 审计，不是报告脚本的前 6 页抽样。

## 最终字体清单（全书）

| 字体 | 类型 | 说明 |
|---|---|---|
| NotoSerifSC Regular/Bold | Type0 | 正文 |
| NotoSansSC Regular/Bold | Type0 | 标题/页眉/图内文字 |
| CascadiaMonoRoman Regular/Bold | Type0 | 代码（含粗代码） |
| NotoEmoji | Type0 | 单色 emoji |
| NotoSansSymbols2 / NotoSansMath | Type0 | 符号/数学 |
| **Type3** | — | **0 处** |
| **系统字体** | — | 仅 `⁷`（U+2077，见 G2 未决项） |
| **重复 SVG id** | — | 0（81 个 marker 定义全部作用域化） |

图内文字实样：C0 四象限图的「① 运行时环境」以 NotoSansSC-Bold 嵌入（改前是 MicrosoftYaHei-Bold + Type3）。

## 五个根因 + 两条评审修回

1. **图（SVG）走 `<img>` data-URI，父文档样式进不去** → `inline_svg_images()` 内联 103 张。
2. **Cascadia Mono 是变量字体未钉轴** → 子集钉 `wght=400/700`。
3. **子集保留 hinting（prep/fpgm/cvt）** → `drop_tables` 剥掉（印刷不需要 hinting）。
4. **粗代码/粗 emoji 合成加粗 → Type3** → 补真 700 + `font-synthesis: none`。
5. **子集用字集漏收构建器文案/SVG/quiz JSON** → 根与后缀扩齐。

**评审修回 A（误删图形描边）**：第一版 halo 剥除按整个 SVG 删 `stroke`，把
`stack-frame.svg` 里 `fill="none"` 的虚线栈槽边框也抹了（字体审计抓不到图形内容损失）。
改为只剥携带 `paint-order="stroke"` 的 `<g>/<text>` 标签上的 stroke 三件套；
八章样本确认 3 条虚线栈槽仍在、Type3 仍为 0。

**评审修回 B（SVG id 冲突）**：103 张图各自定义 `id="arr"` 等引用，内联后 `url(#arr)`
只解析到第一个定义（实测 12 个互不相同的 `arr` marker：fill #666/#94a3b8/#3eaf7c、
markerWidth 7/8）。内联时按图序号给 id 与 `url(#)/href` 引用统一加前缀，
全书重复 id 归零。

另有印刷顺带修：SMIL 动画在分页前统一 `setCurrentTime(0)+pauseAnimations()`，
印刷帧与「静态首帧」口径一致。

## 验证证据

| 验证 | 结果 |
|---|---|
| 全书 1119 页逐 span 审计 | Type3 = 0，系统字体仅 1 处（⁷），重复 id = 0 |
| 八章样本（111 页，含 stack-frame） | Type3 = 0，虚线栈槽 3 条保留，hex 标签完整 |
| `ruff check build_print.py subset_fonts.py` | PASS |
| `python mcu-book/build_html.py --check` | PASS |
| `node --test tests/workflow.test.mjs` | fail 0 |
| `task_verify` | unverified（无配置门可跑） |

## G2 未决项（需要你定）

1. **`⁷`（U+2077，全书 1 处，`docs/stm32/14-pwr.md` 的 2⁷）**：本机四族 OFL 字体
   都没有这个字形，现落系统微软雅黑。
   选项：(a) 印前把上标字符转 `<sup>n</sup>`（视觉等价，内容同一性门的归一化口径
   要加一条）；(b) 接受并在 provenance 记录；(c) 再找一个含 U+2077 的 OFL 字体挂回退族。
   默认建议 (a)。
2. **P1 遗留**：目录点线视觉对齐与体检模块目录解析器（`pdf_audit.check_contents`
   正则漏读）——改体检模块属于策略变更，待复核门放行后做。

