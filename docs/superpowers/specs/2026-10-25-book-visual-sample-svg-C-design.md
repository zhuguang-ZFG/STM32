# 整书样本图 C 设计

日期：2026-10-25  
状态：待人审。人接受这份规格之前不实施  
基线：`main` 上的整书 **v1.2.6**（`10a01ec`，PR #44，2026-10-25）  
上一份封面设计：[2026-10-25-book-visual-cover-imprint-D-design.md](2026-10-25-book-visual-cover-imprint-D-design.md)（PR #42，实施计划 PR #43，实施合入 PR #44）。样式抽出是 [2026-10-25-book-visual-css-token-extract-B-design.md](2026-10-25-book-visual-css-token-extract-B-design.md)（PR #39，实施合入 PR #41）。排版设计是 [2026-10-25-book-visual-typography-E-design.md](2026-10-25-book-visual-typography-E-design.md)（PR #35，实施合入 PR #38）。  
本文件只记录刀 C 的设计。它不改 `assets/`，不改 `tools/`，不改 `cover.svg`，不改 `book.css`，不改 `tokens.json`，不改正文，不升版本号，不打 tag，不发布 Release，不新增 `docs/superpowers/plans/` 下的实施计划。

整书视觉升级的顺序是 **E → B → D → C**。E 已在 `f537a94` 合入，B 已在 `b7ff335` 合入，D 已在 `10a01ec` 合入。本文件是这一序列的最后一刀。它不点名下一刀。

## 背景

刀 E 收了字号阶梯。刀 B 把令牌抽到 `stm32-book/styles/tokens.json`，并写明样本图留在仓库根 `assets/`，不读样式目录。刀 D 改了 `stm32-book/cover.svg` 和扉页两条规则，并写明样本 SVG 是刀 C。这一刀只统一 `assets/` 里那 53 张 SVG 的描边、圆角和调色。

对照 `10a01ec` 核对过的事实：

1. **拼好的 CSS 仍是刀 D 的哈希。** `load_css()` 把四个哨兵填进 `stm32-book/styles/book.css`。`builder.CSS` 的 SHA-256 是 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。`book.css` 源文件 19838 字节，SHA-256 是 `7c821dba13bebb86123def3f243a480af460d897358d548c364860038fb563f5`。`tokens.json` 的 SHA-256 是 `c5bb7846ed74c394f59634b1b40c99d1264c9dd41b018dfb7bfad8a08bea014b`，`schema` 仍是 `1`。亮色 `--paper` 是 `#fbfaf7`，`--ink` 是 `#17202a`，`--muted` 是 `#5e6872`，`--line` 是 `#d7dce1`，`--panel` 是 `#f1f5f7`，`--accent` 是 `#075e84`，`--accent-soft` 是 `#e5f3f8`，`--warn` 是 `#9a3d1c`，`--tip` 是 `#1b5c45`，`--spine` 是 `#c4552a`。
2. **封面不在这 53 张里。** `stm32-book/cover.svg` 是 3880 字节，SHA-256 是 `37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd`。刀 D 已经把它收成无文字铜版。本刀不读、不改这个文件。
3. **53 张 SVG 都是生成器的输出，而且和源码逐字节相同。** 在 `10a01ec` 上调用现有函数写到临时目录，和 `assets/` 里的 53 张比较，53 张相同，0 张不同。没有手改过的孤本。分布是 `assets/animations/` 25 张、`assets/boards/` 10 张、`assets/diagrams/` 18 张。18 张框图里 12 张是 `sample-*.svg`，6 张是其余静态框图。10 张板卡里 7 张来自 `tools/gen_boards.py`，3 张 LQFP 引脚图来自 `tools/gen_pinouts.py`。
4. **画布和体积。** 动画都是 `900x620`。六张非样本框图是 `900x560`。十二张样本图宽度都是 `960`，高度从 `620` 到 `980` 不等，见下表。除了 `pinout-stm32h743zi-lqfp144.svg` 的 75786 字节，其余 52 张都小于 60 KB。最大的另外几张是 Blue Pill 35647 字节、Blue Pill 引脚图 35176 字节、G071 引脚图 34523 字节、L476 引脚图 34508 字节。H743 这张在本刀之前就已经超过 60 KB，超出 14346 字节。
5. **现在的调色是一套深底霓虹，写在 `tools/svgkit.py` 的 `T` 里。** 每张图都用到 `#0b1220`、`#0e1626`、`#243354`、`#1a2742`、`#e6edf3`、`#93a4c0`、`#64748b`、`#22d3ee`。字是浅色，底是深色。图不读 `tokens.json`，也不写 `var(--*)`。`T.FONT` 和 `T.MONO` 是 SVG 属性里的字体族字符串，没有 `@font-face`。
6. **描边和圆角没有一档。** 属性 `stroke-width` 的计数是：`1` 有 164、`1.2` 有 51、`1.4` 有 20、`1.5` 有 569、`1.6` 有 324、`1.8` 有 8、`2` 有 143、`2.2` 有 25、`2.4` 有 20、`2.6` 有 5、`3` 有 4。`rx` 从 `1` 到 `16` 都有，其中卡片常用 `8`（209 处）和 `10`（130 处）。`svgkit` 里矩形默认 `sw=1.5`，`panel()` 默认 `rx=12`，`box()` 默认 `rx=10`，`chip()` 默认 `rx=8`，`waveform()` 默认 `sw=2.4`，`axis()` 默认 `sw=1.4`。
7. **板卡上还有一套零件色，不走 `T`。** 阻焊、焊盘、丝印、芯片体一共 48 个十六进制，只出现在板卡图和 `l4-idd-bench.svg` 的那块板岛上。Blue Pill 的蓝、Black Pill 的黑、绿板的 `#123a2e` 都属于这套。引脚图芯片体用 `#1b1f28` 和 `#dfe6f0`，不把脚名画在芯片体上。
8. **有四段字用旧底色当字色，因为当时的色条是亮的。** `anim_gpio.py` 的「命中」「ISR」、`anim_sys.py` 的「CNT」、`gen_diagrams.py` 的优先级色条，填充都是字面量 `#0b1220`。`memory_map()` 有一枚 `fill=T.WHITE` 的圆点。`iwdg_window()` 的 `0xFFF` 和 `0` 也是 `T.WHITE`。`T.WHITE` 现在是 `#f8fafc`。
9. **样本图的句子已经被试锁住，颜色没有。** `stm32-book/tests/test_sample_chapters.py` 和三份 batch 测试要求十二张 `sample-*.svg` 含「自绘」，不含 `<animate`、`@keyframes`、`animation:`、「矢量动画」、「实拍」，并且小于 60 KB。它们核对的是寄存器名、脚号和手册句子，不核对 `#22d3ee`。静态主图用 `_credit()`，不用 `Svg.footer()`。`Svg.footer()` 会写下「自绘矢量动画」，那一行留在动画、框图和板卡图里。
10. **GIF 有两条来路，都不是这 53 张的派生副本。** `assets/gif/` 里 16 张 ASCII GIF 由 `tools/gen_gifs.py` 用 `tools/minigfx.py` 的 `C` 画出来。`C` 的 RGB 与现在的 `T` 一一对应。`tools/check_assets.py` 会把这 16 张解码后和 `BUILDERS` 逐像素比较。另外 24 张 `*-zh.gif` 由 `tools/svg2gif.py` 从动画 SVG 采样。其中 17 张已经大于 500 KB，最大的 `dma-circular-zh.gif` 超过 4 MB。`svg2gif.py` 把 Chrome 写死在 `C:\Program Files\Google\Chrome\Application\chrome.exe`。`i2c-transaction.svg` 没有 `<style>`、没有 `@keyframes`、没有 `<animate`，所以没有 `i2c-transaction-zh.gif`。`assets/README.md` 仍写「5 张 SVG 还没有对应动图」，和仓库现状不一致；本刀不改那句清单。
11. **版本字面量是 1.2.6。** `revisions.json` 第一条是刀 D 的两句，日期 `2026-10-25`。两份 manifest 的 `version` 是 `1.2.6`。`stm32-book/README.md` 当前版本句是 **v1.2.6 · 2026-10-25**。Book CI 跑单元测试和 `build_html.py --check`，不跑 `tools/check_assets.py`。

对比算法与 `stm32-book/tests/test_build.py` 里的 `_contrast_ratio` 相同。（较亮 + 0.05）/（较暗 + 0.05）。`#17202a` 对 `#fbfaf7` 约 15.8。`#5e6872` 对 `#fbfaf7` 约 5.4。`#075e84` 对 `#fbfaf7` 约 6.8，对 `#e5f3f8` 约 6.3。`#9a3d1c` 对 `#fbfaf7` 约 6.6。`#1b5c45` 对 `#fbfaf7` 约 7.6。`#c4552a` 对 `#fbfaf7` 约 4.3，不够 4.5，所以书脊色继续只当封面和扉页的色条，不进样本图的字。`#d7dce1` 对 `#fbfaf7` 约 1.3，只能当发丝线，不能当字，也不能当卡片唯一的边界。

文本哈希的算法：按文档顺序取出每个 `<text>…</text>` 的原始内部文本（不反转义），用 `\n` 连接，再做 UTF-8 的 SHA-256。下表是 `10a01ec` 上的值。实施时这些哈希必须保持，因为句子不许改。

```text
animations/adc-sar.svg 900x620 19409 ebd3127f7efde5d3c25f5a82dea6ae36eaff2a4c3a87c698f95f0d329a0ca807
animations/boot-sequence.svg 900x620 14058 d6d1baa08f2d9763ef5971f4701775db3905d34a7d6998310b127dd21beaddfc
animations/can-arbitration.svg 900x620 23362 6a68426929c8ad0f4046b091ae4be6db894eba2e4125f1e03c41c695167a3176
animations/clock-tree.svg 900x620 10921 c0e07c5c01bffae9769331541bdf87dcfc4ea61e3b4081b6f72834b476fbed08
animations/debug-swo.svg 900x620 12545 e44f13c22225782401c9b3d44f376781297c0103040118786626621476a6ffdd
animations/dma-circular.svg 900x620 16488 7deb7de9dc81e1a01c1c2e01827c131661f5b6d45bb5c2fb1d0473e126041fd1
animations/flash-iap.svg 900x620 12795 55ad4b20f25654a8bb6a705303a99d5fb513f5b125b70a4545278f84d63ad0cb
animations/freertos-scheduler.svg 900x620 15775 fe1bebd106b7c825a5d815edc67842821a8298e6e98036153641ca928c098bb3
animations/g0-boot-swd.svg 900x620 12398 e9121dfb6e5290afd5d192048fa7d7409a821c7651538c80bde3237df535155f
animations/gpio-blink.svg 900x620 14249 811377a9c3b65dd99cbeb8a1ff720b0e4e6410bc852726ac98f9aa20619175ea
animations/gpio-input-interrupt.svg 900x620 13740 4b97aeb339eb046f0091312b6caf918b1acdc176cc72e4295cc7c116792c6697
animations/i2c-transaction.svg 900x620 17483 e5c5b2aca2aae67cc607e3eb929cc0f20c184deceb8815f32a9d4e96f4bef55a
animations/iwdg-window.svg 900x620 10675 324f8c83215265a9e4b9c256552019165c14adb914c3fc9189f054f264751444
animations/l4-stop2-evidence.svg 900x620 13976 ae6b68a3a26ee3995d72dc29bcfcb2bab733a2e54637e4d9a6a8581b9f577e28
animations/lowpower-wakeup.svg 900x620 10766 7a5fe86d6e1a29c7f8e00d177f0ec928c85f7405e8427e8f27209720cc0a22b6
animations/memory-map.svg 900x620 7846 82e9be18ac7ecbe388e478b995ef9bcf8e876a2373406565469fda41e911b11f
animations/network-packet-journey.svg 900x620 18648 0081c4c6270e94527deba9ea9365811c22de28130ee343d8df68797eb36f1016
animations/nvic-interrupt-flow.svg 900x620 12972 07a38a7e7d4b430809683b2beb00f98b3cac0a17fc45bb1a5d066d20c22c9dc4
animations/rtos-system-layers.svg 900x620 13996 1a44f6f16dcc08a20467d946a35a22ef968582f37faf99b5b74f5107deaf31e9
animations/spi-transfer.svg 900x620 18861 579ddd86d159809dc4c667a0bf1faf652c1c0538d4d155f6f7187896df7a3968
animations/timer-modes.svg 900x620 11712 c8a1e34469293d5f4a02a5703271bcf62fc4e9f2f1e89429dbcaa02b56ebeabf
animations/timer-pwm.svg 900x620 10046 54833bf0841b1569cb993934699473b2ee4d2f0ed56b858a4fb9b5855bb8532f
animations/toolchain-flow.svg 900x620 15176 e131ad994e16c099c15d4d941c0e7aade4865c53c912248a73590e939645e0bd
animations/uart-frame.svg 900x620 18533 a696fc8932d337f1b22dacef54ecfe01dd37aa963b41d67111c584122f6b3400
animations/usb-enumeration.svg 900x620 10874 b531c1c1278ee8560a2a4297dd4f36e8dfb5934fc09f7df494faf9d5e455e20d
boards/blackpill-stm32f411ce.svg 900x620 32264 511d86c80d8862e78be2a0c7e6ca7e24e1db11d30ea66d47b3b2f1e8cdec0494
boards/bluepill-stm32f103c8t6.svg 900x620 35647 272634dc07da80d8c5d7e6471d9778310292318aace55acbecfcd92a8d9d4c25
boards/f103zet6-dev.svg 900x620 26509 8d52a625b72cef5f53be80091fc870d3bcf9537b0c178c5aa4ebfcb810ded612
boards/f4-discovery.svg 900x620 26524 d0d4d756b30de2d1a11a43bd78abd0f733dcf2696cc88f708de8cde63cfe659f
boards/nucleo-f411re.svg 900x620 21385 434fa875affbab6a0d987df16919de7b6cfaf88c3703da29593bef68b5006c8b
boards/peripheral-wiring.svg 900x620 13970 a5517214a0d7efcb8721fa41c8fee6224a7deca98f193bf39147ccc3f36fd166
boards/pinout-bluepill.svg 900x620 35176 4de478b58c8d278166311b99311183121ccf1ecb38a50c99450b35e60893cabd
boards/pinout-stm32g071rb-lqfp64.svg 620x750 34523 7ccc8b702e15d0473bfc1d4c956397dfbb5bd50363d4e762bd100c794d1d2193
boards/pinout-stm32h743zi-lqfp144.svg 840x970 75786 4d71ec5cab732513073bac6721ae4c688a36f18ab11fcae4b5e6e927433b7a96
boards/pinout-stm32l476rg-lqfp64.svg 620x750 34508 a5a8468d7b087956a4635ac7c88412f1e7920570c53e388e0a10a44fbe5f8adf
diagrams/interrupt-priority.svg 900x560 11877 7f3d8b282ed7342a56b598694137c3091ca4bd4a10acc73cd5a651a9b0c7fe05
diagrams/l4-idd-bench.svg 900x560 8673 32e1a5b195562947e04d2da8efc2f0c89dd97aed9f7cacbb3c5914ce52f8ec96
diagrams/layers-hal-ll-reg.svg 900x560 10401 60098b25b368c2f6acefb4e9a3152f816506cae44e68b2fb8ffbf0878c049f78
diagrams/network-debug-ladder.svg 900x560 11278 a1405054a5ba593090ad0bc6fdb104a5c8e513dd9695bd35767867faeeaec2e8
diagrams/peripheral-bus.svg 900x560 14071 80d659d44758f54a352b8447fb4a49e6fa880a47cb981bc487c1d69aaa6ae2f6
diagrams/project-structure.svg 900x560 13014 53f68cd4e58288a346e7cd09867724a75daa564e3b527a46a67627250def2acf
diagrams/sample-00-boot-state.svg 960x620 7103 41eff7ecd092c9f1d0e41629b4b87f337ea9d27e4b63f3ddda1d03e96c3eb3b1
diagrams/sample-01-swd-vectors.svg 960x980 7328 2e08712dfff9ee901d17be08e83d3496b7d34b02f3ddd73a7565d230a6291b56
diagrams/sample-02-clock-tree.svg 960x860 7402 41c1657ce8a1e34119ae2946ab5f10034fe5c83ef21fa50b4a1520861a1a98f2
diagrams/sample-03-gpio-led.svg 960x660 8221 932244c2053d317d50bf5106192a79fbf9d1546f16dd00bcf99110b7bd11a8ad
diagrams/sample-04-exception-stack.svg 960x780 7528 bc969846347daca2048bf5b355139a73f55e436f5c5779f9ac69a92e5d458d3e
diagrams/sample-05-pwm-1khz.svg 960x820 6845 48d92b03384bf3ac51e52c7d54c8a2bedd68b1a20ec405c21fbbc9287999217e
diagrams/sample-06-uart-frame.svg 960x820 12448 2da90d7d086d7eabf7a11f50cbe53f3387f1b0e3ed8b97b7781ff4a41be516ee
diagrams/sample-07-i2c-addr.svg 960x920 6620 5d8aeb4df50370a3885d46d17f086e582dab7875ce914911efb247b07e8d7e5a
diagrams/sample-08-spi-jedec.svg 960x860 6850 717ba67544302d5517bffdbfe23deec414d5f52c49993a9eba0260fd4952fd4c
diagrams/sample-09-adc-sar.svg 960x860 6656 3d193aa429c4f707ea7f82cf4e6e44c2f128bc032e59d43a7e2334c5882dc65e
diagrams/sample-10-dma-cndtr.svg 960x900 6552 6a887f553de8b9d8744527a71b0c86217ccbea32b2f4f65ff3519f519cfb92f5
diagrams/sample-11-iwdg-1s.svg 960x980 7169 226d77d6f316c4b5ce1a1580507c95b96d69a8c3a35f7601475794dc279b18eb
```

GIF 汇总哈希的算法：把 `assets/gif/*.gif` 按文件名排序，每行写成 `{文件名} {该文件字节的 SHA-256}\n`，再对这整段 UTF-8 做 SHA-256。`10a01ec` 上 40 个文件的汇总是 `bd674b4aaf427c36ec54f92853f13d52cf160e41acd2a06f89c2479b9f31c26f`。

## 目标与非目标

### 目标

- 实施时让 53 张 SVG 共用浅色纸底和同一档描边、圆角。字色和语义色对齐整书亮色令牌里对比过关的那几个；过不了 4.5 的书脊色不拿来写字。
- 图仍然由 `tools/` 生成，再写回仓库根 `assets/`。不手改 SVG 成品。不读 `stm32-book/styles/`。
- 十二张样本图继续是静态主图：句子、坐标、`viewBox`、`_credit()` 都留着。动画继续能播，类名不改。
- 零件色留在板卡和那一块板岛上。Blue Pill 仍是蓝板，Black Pill 仍是黑板。
- 拼好的 CSS 保持 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。
- 实施时的建议版本是 **1.2.7**。本设计 PR 不升版本。
- 实施 PR 在 `book` 与 `book-en` 都变绿之后 squash 合入 `main`。合入后在本机 `D:\Users\STM32` 拉取这次 `main`。拉取不产生仓库 diff。

### 非目标

- 不改 `docs/00`–`28`、`docs/en/`、附录 Markdown、`CONTENT_GUIDE.md` 中英、罗盘文案。不改两份 manifest 里除 `version` 和 `date` 以外的字段。
- 不改 `stm32-book/cover.svg`，不改封面 HTML 顺序，不改扉页规则，不改 `.cover` 的 `clamp`。
- 不改 `tokens.json`、`book.css`、`load_css()`。不升 `schema`。不加 `<link>`，不加 `@font-face`，不写 `url(`。
- 不把 SVG 挪进 `stm32-book/styles/` 或 `stm32-book/assets/`。不新建第二套暗色 SVG。
- 不改 `T.FONT` 和 `T.MONO`。把整书等宽栈抄进引脚图会让 H743 那张从 75786 字节再长大约 19 KB，而 SVG 又不能内嵌字体。
- 不改 `tools/gen_gifs.py`、`tools/minigfx.py`、`tools/svg2gif.py`、`tools/gen_tietu.py`、`tools/gen_narrated.py`、`tools/gen_videos.py`、`tools/gen_mp_covers.py`。不重生成 `assets/gif/`、`assets/photos/`、`assets/video/`、`assets/wechat/`。
- 不改 `assets/README.md` 里那句过时的「5 张还没有动图」。只加下面写死的一句颜色说明。
- 不改章节里的图路径、图注和替代文本。不把 H743 引脚图拆成两张，也不把 60 KB 改成仓库新默认值。
- 不加图目录或表目录。出版书签仍是 44 条。章号显示仍是文件名前缀加 1。
- 不打 tag，不创建 GitHub Release。
- 不写实施计划。本设计 PR 也不跑生成器。

## 方案

比较过三种做法。

| 做法 | 图怎么来 | 结果 |
| --- | --- | --- |
| 1. 手改 53 张 SVG | 成品与生成器分叉 | 下次跑 `gen_animations.py` 会把改动盖掉。`10a01ec` 上成品和生成器还是逐字节相同的 |
| 2. 只改 `T` 的十六进制，描边和圆角不动 | 再生全部 | 深底换成浅底，但 `1.2` 到 `3` 的线宽和 `1` 到 `16` 的圆角还在。刀 C 要求的是一套画法 |
| 3. 改 `T`、改默认线宽和圆角、改下面点名的几处填充，再按三波再生 | 生成器仍是唯一来源 | 浅底、三档线宽、三档圆角。零件色和句子不动。GIF 字节不动 |

采用做法 3。做法 1 留下无法再生的图。做法 2 把霓虹换成令牌色，却保留现在的线宽散度。1.2.7 不拆文件，不升 token schema，不让 SVG 跟随 `prefers-color-scheme`。暗色页面上这些图仍是浅色纸片。印刷也按图里的浅色走。封面继续是那一块深色铜版。

所有权是一条单向的抄写，不是运行时读取：`tokens.json` 的亮色值 → 本文件写死的十六进制 → `svgkit.T` 的字面量 → 生成的属性。组件不 `import` 令牌文件。以后令牌若改值，图不会跟着变，要另写设计。

## 调色

`T` 只改下面这些赋值。字体两行保持原文。删除 `WHITE`。`led()` 里的 `#ffffff` 高光和 `#00000066` 描边保持原文，它们是灯珠上的高光，不是纸色。

| 名字 | 现在 | 实施后 | 角色 |
| --- | --- | --- | --- |
| `BG` | `#0b1220` | `#fbfaf7` | 画布。亮色 `--paper` |
| `BG2` | `#0e1626` | `#f1f5f7` | 页眉带、次级底。亮色 `--panel` |
| `PANEL` | `#111c31` | `#f1f5f7` | 卡片填充。与 `BG2` 同值。卡片靠描边分开，不靠第二块深色 |
| `PANEL2` | `#16233c` | `#e5f3f8` | 强调浅底。亮色 `--accent-soft` |
| `STROKE` | `#243354` | `#5e6872` | 卡片和结构线。亮色 `--muted`。`--line` 对纸色只有约 1.3，不能当卡片框 |
| `GRID` | `#1a2742` | `#d7dce1` | 发丝线、页脚线。亮色 `--line` |
| `TEXT` | `#e6edf3` | `#17202a` | 正文。亮色 `--ink` |
| `MUTED` | `#93a4c0` | `#5e6872` | 次要字。亮色 `--muted` |
| `DIM` | `#64748b` | `#5e6872` | 与 `MUTED` 同值。不新增一个灰阶 |
| `CYAN` | `#22d3ee` | `#075e84` | 信号、PA、默认眉题。亮色 `--accent` |
| `GREEN` | `#34d399` | `#1b5c45` | 正常路径、PB。亮色 `--tip` |
| `RED` | `#f87171` | `#8f2d2d` | 失败路径、电源脚。对纸色约 7.8 |
| `AMBER` | `#fbbf24` | `#7a4e00` | 注意、NRST、BOOT、PH。对纸色约 6.9 |
| `ORANGE` | `#fb923c` | `#9a3412` | PF、PG。对纸色约 7.0 |
| `VIOLET` | `#a78bfa` | `#5b3a8c` | 锁、备份域、PC。对纸色约 8.3 |
| `PINK` | `#f472b6` | `#8e2f5b` | PD。对纸色约 7.4 |
| `BLUE` | `#60a5fa` | `#1e4d63` | PE、第二路信息。对纸色约 8.8。封面用过这个青色，这里只作字色 |
| `WHITE` | `#f8fafc` | 删除 | 三处调用改成 `T.TEXT` |

`#c4552a` 不进入 `T`，也不进入这 53 张图。`#9a3d1c` 同样不进入。失败和注意若共用警告色，正常路径、失败路径和注意就只剩两档。`#8f2d2d` 与 `#7a4e00` 是为了在浅底上保住这三档，并且都超过 4.5。它们只出现在 `T` 里，不写进 `tokens.json`。

色条上的字改用纸色，不用墨色。下面四处字面量 `#0b1220` 改成 `#fbfaf7`。纸色对强调色、提示色、`#7a4e00`、`#5e6872`、`#5b3a8c` 都超过 5.4。

- `anim_gpio.py` 里「命中」和「ISR」的 `fill="#0b1220"`
- `anim_sys.py` 里「CNT」的 `fill="#0b1220"`
- `gen_diagrams.py` 里 `interrupt_priority()` 色条标签的 `fill="#0b1220"`

`memory_map()` 的圆点和 `iwdg_window()` 的 `0xFFF`、`0` 从 `T.WHITE` 改成 `T.TEXT`。圆点画在浅纸上。那两个数字画在半透明红条上，红条底下是浅的 `--panel`，所以用墨色，不用纸色。

板岛上的字不能跟着 `T.TEXT` 变成墨色。`l4_idd_bench()` 里这块板的填充保持 `#123a2e`、`#0d2b22`、`#123057`、`#151922`。只改落在这块板上的字和框：

| 现在的调用 | 改成 | 原因 |
| --- | --- | --- |
| 「ST-LINK 区」`fill=T.TEXT` | `fill="#dfe6f0"` | `#dfe6f0` 对 `#0d2b22` 约 12.1 |
| 「功能调试可接；功耗测量需排查回灌」`fill=T.AMBER` | `fill="#e2b23c"` | 金黄对 `#0d2b22` 约 7.7 |
| 「目标 MCU 供电域」`fill=T.TEXT` | `fill="#dfe6f0"` | 对 `#123057` 约 10.5 |
| 「STM32L476RG」`fill=T.TEXT` | `fill="#dfe6f0"` | 对 `#151922` 约 14.0 |
| 「VDD / VSS」`fill=T.MUTED` | `fill="#8b98b0"` | 对 `#151922` 约 6.0 |
| 内框 `fill="#0d2b22"` 的 `stroke=T.STROKE` | `stroke="#8b98b0"` | `#5e6872` 对 `#0d2b22` 约 2.7 |
| `fill="#123057"` 的 `stroke=T.CYAN` | `stroke="#7aa2ff"` | `#075e84` 对 `#123057` 约 1.9，`#7aa2ff` 对它约 5.3 |

`gen_boards.header()` 的脚名现在用 `SILK`（`#e8f1ff`）。脚名落在板外的纸上，`#e8f1ff` 对 `#fbfaf7` 约 1.1。这一处改成 `fill=T.TEXT`。板上的丝印文字继续用 `SILK`，`#e8f1ff` 对 `#123a2e` 约 11.1，对蓝板 `#123057` 约 11.6。不要把 `SILK` 常量本身改成墨色。

`_color()` 继续按端口返回 `T` 的成员。电源脚走 `RED`，NRST 和 BOOT 走 `AMBER`，PA 到 PG 仍是青、绿、紫、粉、蓝、橙。不在 `_color()` 里再写一套十六进制。

禁止再出现的旧色是：`#0b1220`、`#0e1626`、`#111c31`、`#16233c`、`#243354`、`#1a2742`、`#e6edf3`、`#93a4c0`、`#64748b`、`#22d3ee`、`#60a5fa`、`#34d399`、`#fbbf24`、`#fb923c`、`#f87171`、`#a78bfa`、`#f472b6`、`#f8fafc`。

允许留下的零件色恰好是这 48 个，另加灯珠高光 `#ffffff`：

```text
#00000055 #00000066 #00000088 #08214a #08224a #0a0d13 #0a1f5e #0a2a52
#0b2c4c #0c0f16 #0c2242 #0d2b22 #0e3b6e #0f2f8a #0f3f6b #123057
#123a2e #141821 #151922 #153a9e #1b1f28 #1d4ed8 #2a3242 #2b3038
#39424f #4a5260 #59606c #5b6472 #5d6470 #7aa2ff #7fd4ff #808a9a
#8b98b0 #8d7420 #8d949e #9aa4b2 #9db8ff #bcd8ff #c4b5fd #c9ced6
#cfe0ff #d8b23a #dbeafe #dfe6f0 #e2b23c #e7ebf0 #e8f1ff #ffffff22
```

不新增这张清单以外的零件色。不把 `#123a2e` 改成 `--tip`。阻焊要和提示色分开，蓝板和黑板也要彼此分开。

## 线宽与圆角

全库只留三档描边和三档圆角。`svgkit` 的默认值先改，再把各生成器里越档的实参按同一张表收进来。

描边：

| 现在的实参 | 改成 |
| --- | --- |
| `1` | `1` |
| `1.2` | `1` |
| `1.4`、`1.5`、`1.6` | `1.5` |
| `1.8`、`2`、`2.2`、`2.4`、`2.6`、`3` | `2` |

圆角：

| 现在的实参 | 改成 |
| --- | --- |
| `1`、`1.5`、`2`、`2.5`、`3` | `2` |
| `4`、`5`、`6`、`7` | `4` |
| `8`、`9`、`10`、`11`、`12`、`14`、`16` | `8` |

`rx=0` 或省略 `rx` 的写法保持。圆没有 `rx`。

`svgkit` 里同时改这些默认值：`panel()` 的 `rx=12` 改为 `8`，`box()` 的 `rx=10` 改为 `8`，`legend()` 的 `rx=3` 改为 `2`，`waveform()` 的 `sw=2.4` 改为 `2`，`axis()` 的 `sw=1.4` 改为 `1.5`。矩形、线、路径、圆的默认 `sw=1.5` 不变。`arrow()` 的默认 `sw=2` 不变。`chip()` 的默认 `rx=8` 不变。`header()` 左边的 4 用户单位色条是矩形宽度，不是描边，保持。`gen_boards.board()` 的默认 `r=14` 改为 `8`，这样内框的 `r - 4` 是 `4`，仍在允许档里。五个调用都不传 `r`。

样本图里越档的只有圆角：`gpio_led()` 的 `rx=10` 改为 `8`、`rx=6` 改为 `4`；`uart_frame()` 的 `rx=6` 改为 `4`。其余样本矩形已经是 `rx=8`。`_credit()` 的 `sw=1` 保持。

不改坐标、宽高、`viewBox`、字号、句子、引脚顺序、`pitch`、`label_room`。不改动画时长、类名和 `@keyframes` 正文。不给 `i2c-transaction.svg` 补动画。

## 文件与三波

三波是实施 PR 里的顺序，不是三个版本。三波都进 1.2.7，合入前要一起出现。前一波的测试没过，就不开始下一波。

| 波 | 生成器 | 成品 | 张数 |
| --- | --- | --- | --- |
| 1 | `tools/svgkit.py`、`tools/gen_sample_figures.py`、`tools/gen_diagrams.py` | `assets/diagrams/sample-00` 到 `sample-11`，以及 `layers-hal-ll-reg.svg`、`project-structure.svg`、`peripheral-bus.svg`、`interrupt-priority.svg`、`l4-idd-bench.svg`、`network-debug-ladder.svg` | 18 |
| 2 | `tools/anim_basics.py`、`tools/anim_gpio.py`、`tools/anim_comm.py`、`tools/anim_sys.py` | `assets/animations/*.svg` | 25 |
| 3 | `tools/gen_boards.py`、`tools/gen_pinouts.py` | `assets/boards/*.svg` | 10 |

`gen_animations.py` 只负责调用，本身不改。波次 2 改的是四个 `anim_*.py`。

再生命令，在仓库根目录、按这个顺序：

```bash
python3 tools/gen_sample_figures.py
python3 tools/gen_diagrams.py
python3 tools/gen_animations.py
python3 tools/gen_boards.py
python3 tools/gen_pinouts.py
```

不运行 `gen_gifs.py`、`svg2gif.py`、`gen_tietu.py`、`gen_narrated.py`。

`assets/README.md` 在生成命令那一块下面加一句，只加这一句：

`图内纸色、墨色和语义色写在 tools/svgkit.py 的字面量里，数值与整书亮色令牌相同，生成时不读 stm32-book/styles/tokens.json。`

## 谁必须改，谁只再生

| 路径 | 实施 PR |
| --- | --- |
| `tools/svgkit.py` | 必须改。只改 `T` 的颜色、删除 `WHITE`、以及上一节列出的默认 `rx` / `sw`。不改 `render()` 的标签顺序、属性顺序和 `opacity="1"` 的写法。不改 `FONT`、`MONO`、动画助手和 `led()` |
| `tools/gen_sample_figures.py` | 必须改。只收 `gpio_led()` 和 `uart_frame()` 的 `rx`。不改句子和坐标 |
| `tools/gen_diagrams.py` | 必须改。按表收 `sw` / `rx`，并改优先级色条和 `l4_idd_bench()` 里点名的填充与描边。零件色字面量其余保持 |
| `tools/anim_basics.py`、`anim_gpio.py`、`anim_comm.py`、`anim_sys.py` | 必须改。按表收 `sw` / `rx`，并改点名的 `#0b1220` 和 `T.WHITE` |
| `tools/gen_boards.py` | 必须改。`board()` 的 `r`、按表收 `sw` / `rx`、`header()` 脚名改 `T.TEXT`。`PCB`、`SILK`、`GOLD` 和其余零件色常量保持 |
| `tools/gen_pinouts.py` | 必须改。只按表收 `sw` / `rx`。`_color()` 仍返回 `T` 的成员。芯片体的 `#1b1f28`、`#dfe6f0`、`#8b98b0` 保持。脚名和手册号不改 |
| `assets/**/*.svg` 这 53 张 | 只再生。不手改 |
| `tools/gen_gifs.py`、`tools/minigfx.py` | 不改。16 张 ASCII GIF 保持深色霓虹，和浅色 SVG 并排时允许不一致 |
| `tools/svg2gif.py`、`assets/gif/*-zh.gif` | 不改。动画 SVG 变了之后，这 24 张动图会和源图不一致。它们里 17 张已经超过 500 KB，本刀不重采样，也不放宽 500 KB |
| `tools/check_assets.py` | 不改。像素比对继续锁住 16 张 ASCII GIF。新的画法契约放在单元测试里，不在这里抄第二份色表 |
| `stm32-book/cover.svg`、`stm32-book/styles/*` | 不改 |

`gen_tietu.py` 也 `import` 了 `T`，但成品不在 `assets/`。本刀不改它，也不运行它。以后若有人用它出公众号贴图，会继承这套浅色；那不是 1.2.7 的验收面。

## 体积

- 除 `assets/boards/pinout-stm32h743zi-lqfp144.svg` 以外，每张 SVG 的 UTF-8 长度必须小于 `60 * 1024`。
- H743 这张保持小于 `80 * 1024`。现在是 75786。字体族不改，所以它不该靠近 80 KB。它继续可以大于 60 KB。实施 PR 写上再生后的字节数。不拆图，不提高仓库默认的 60 KB。
- `assets/gif/` 的 40 个文件一个字节都不改。汇总哈希保持 `bd674b4aaf427c36ec54f92853f13d52cf160e41acd2a06f89c2479b9f31c26f`。
- 16 张 ASCII GIF 仍由 `check_assets.py` 按小于 500 KB 告警。本刀不把已经超过 500 KB 的 `*-zh.gif` 收进这个告警，也不把它们重新压小。

## 与令牌和 CSS 的边界

这一刀不改样式。决定写在这里，避免实施时顺手把图的颜色收进 JSON。

| 对象 | 现在 | 刀 C |
| --- | --- | --- |
| `tokens.json` | `schema` 为 `1`，亮色 40 个键 | 不改。哈希保持 `c5bb7846…` |
| `book.css` 源文件 | 19838 字节，`7c821dba…` | 不改 |
| 拼好的 `builder.CSS` | `a4ccd140…` | 不改。测试里的期望也不改 |
| 画板三色、封面 `clamp`、扉页 `::after` | 刀 D 已经锁住 | 不改 |
| 样本图颜色 | `svgkit.T` 的深底霓虹 | 改成上表的字面量。运行时不读 JSON |
| `#c4552a` | 封面色条和 `--spine` | 不进入这 53 张图 |
| `figure` 的浅底和 `1px` 边 | `book.css` | 不改。图自己用 `#fbfaf7` 铺满，和框内的混合底可以差一阶 |
| 暗色查询 | 只重写 `:root` 的 15 个颜色 | SVG 不跟随。暗色页面上图仍是浅纸 |

不把 `T` 改成 `var(--paper)`。单独打开 SVG 时没有令牌表。构建仍只做内嵌，不生成 SVG。

## 版本与修订文案

本设计 PR 不改版本。实施 PR 才写。

实施开始时先读 `main` 上的 `stm32-book/manifest.json`。

- `version` 仍是 `1.2.6`：实施版写成 `1.2.7`。
- `version` 已经高于 `1.2.6`：实施版写成下一条修订号，不把本文件里的 `1.2.7` 硬套上去。修订句子仍用下面四句。

日期用实施当天的 ISO 日期。`revisions.json`、两份 manifest、`stm32-book/README.md` 写同一个日期。新条目插在最前，已有句子一字不改。

- `version`: 按上面的规则
- `date`: 实施当天
- `zh`:
  - 仓库里的样本图、框图、动画和板卡图改成浅色纸底，语义色与正文的强调色、提示色对齐。描边只留 1、1.5 和 2，圆角只留 2、4 和 8。
  - 封面、样式令牌和章节正文不改。光栅 GIF 仍是原来的深色，不随这批矢量图重画。
- `en`:
  - The sample drawings, diagrams, animations, and board drawings in the repository now use light paper. Their semantic colors line up with the text accent and tip. Strokes are only 1, 1.5, and 2. Corners are only 2, 4, and 8.
  - The cover, the style tokens, and the chapter text stay as they are. The raster GIFs keep the previous dark palette and are not redrawn with these vectors.

`stm32-book/README.md`：

- 当前版本句改为 **v{新版本} · {实施日期}**。
- 发布节的版本句改为已经是这个版本。tag 名改为 `v{新版本}`。在现有误标句子的最后再加一句「也不要把 1.2.6 的产物标成 {新版本}」。已有的误标句子保留，包括「也不要把 1.2.5 的产物标成 1.2.6」。
- 构建节里关于 `tokens.json` 和 `book.css` 的那一句保留。
- 这一步仍不创建 tag，也不创建 Release。

## 测试

新文件 `stm32-book/tests/test_sample_svg_c.py`。不把色表塞进 `test_build.py`，也不改 `test_css_token_extract_contract` 里的哈希字符串。不增加依赖。

既有的样本章和三份 batch 测试不改断言。它们继续锁句子、禁动画标记和 60 KB。`test_cover_svg_stays_self_contained` 和 `test_cover_imprint_d_contract` 不改。

新测试核对：

- `builder.CSS` 的 SHA-256 仍是 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。
- `stm32-book/styles/tokens.json` 的 SHA-256 仍是 `c5bb7846ed74c394f59634b1b40c99d1264c9dd41b018dfb7bfad8a08bea014b`。`book.css` 源文件的 SHA-256 仍是 `7c821dba13bebb86123def3f243a480af460d897358d548c364860038fb563f5`。`cover.svg` 的 SHA-256 仍是 `37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd`。
- `assets/` 下的 SVG 恰好 53 张，路径与上表一致。每张的 `width`、`height` 和文本哈希与上表一致。
- 除 H743 引脚图外，每张小于 `60 * 1024`。H743 小于 `80 * 1024`。
- 每张图里的 `#` 后 6 位或 8 位十六进制，小写后都属于下面这 14 个语义色，加调色一节那 48 个零件色，加 `#ffffff`。14 个语义色是 `#fbfaf7`、`#f1f5f7`、`#e5f3f8`、`#5e6872`、`#d7dce1`、`#17202a`、`#075e84`、`#1e4d63`、`#1b5c45`、`#7a4e00`、`#9a3412`、`#8f2d2d`、`#5b3a8c`、`#8e2f5b`。8 位的只有 `#00000055`、`#00000066`、`#00000088`、`#ffffff22`。禁止上一节列出的 18 个旧色，也禁止 `#c4552a` 和 `#9a3d1c`。
- 每个 `stroke-width` 属性的值只是 `1`、`1.5` 或 `2`。每个 `rx` 属性的值只是 `2`、`4` 或 `8`。
- 十二张 `sample-*.svg` 不含 `<animate`、`@keyframes`、`animation:`、「矢量动画」。含「自绘」。
- `assets/animations/i2c-transaction.svg` 仍不含 `<style` 和 `<animate`。
- `assets/gif/*.gif` 恰好 40 个，汇总哈希仍是 `bd674b4aaf427c36ec54f92853f13d52cf160e41acd2a06f89c2479b9f31c26f`。
- `svgkit.py` 的源文件含 `BG = "#fbfaf7"`，含 `CYAN = "#075e84"`，不含 `WHITE`，不含 `#0b1220`，不含 `#22d3ee`。`FONT` 那一行仍含 `PingFang SC` 和 `Hiragino Sans GB`。
- 源码里不再有 `fill="#0b1220"` 和 `T.WHITE`。`gen_sample_figures.py` 不含 `rx=10` 和 `rx=6`。

停手条件：实施开始时若还没改生成器，就把五个生成命令跑一遍。`git diff -- assets` 必须为空。若不为空，说明 `main` 上的 SVG 已经和生成器分叉，先停，不要在分叉上套这套调色。若 `builder.CSS` 的 SHA-256 已经不是 `a4ccd140…`，也先停。本刀不重新计算样式哈希，因为本刀不改样式。

版本断言按实施时的实际版本改，不在设计 PR 里改：

- `assert_version_history_and_index` 的元组在 `1.2.6` 前加上新版本，并断言 `>{新版本}<` 出现在 `>1.2.6<` 之前。
- `test_revision_file_lists_1_0_0_through_manifest_version` 的列表以新版本起头，下一项仍是 `1.2.6`。
- 两处 `<strong>v1.2.6</strong>` 改为新版本。英文 manifest 的版本等式一并改。
- `test_visual_polish_version_is_1_2_0` 把现在的 `entries[0]` 到 `entries[6]` 各后移一位。1.2.6 的刀 D 两句改去核对 `entries[1]`，其后的 1.2.5 直到 1.2.0 顺延。句子原文不改。新的 `entries[0]` 用上一节的四句，日期等于两份 manifest 的 `date`。
- README 断言改为新的当前版本句、`版本号已经是 {新版本}`、新的误标句子，以及 `打 tag \`v{新版本}\``。`也不要把 1.2.5 的产物标成 1.2.6` 这句保留。

不删 `0x271`、`167 ns`、出版书签长度为 44、样本章和各批加厚的断言。

## 工作流与 PR 节奏

刀 C 沿用刀 D 的节奏：设计 PR 等人审阅后再合；实施 PR 在 Book CI 变绿后 squash 合入。这一刀不改正文章。

### 本 PR（设计）

只新增本文件。不改 `docs/` 章节、`docs/en/`、`stm32-book/`、`assets/`、`tools/`、`CREDITS.md`、`.github/`。不升版本，不打 tag，不发 Release。不新增实施计划。本 PR 等人审阅规格后再合入，不在 CI 变绿后自动合。

### 实施 PR（下一轮，不在本 PR）

顺序固定：

1. **确认基线。** 按「测试」一节的停手条件跑一遍生成器。`assets/` 的 diff 必须为空，CSS 哈希必须仍是 `a4ccd140…`。
2. **波次 1。** 改 `svgkit.py`、`gen_sample_figures.py`、`gen_diagrams.py`。只跑前两个生成命令。这 18 张里不得再出现 `#0b1220`，十二张样本图仍小于 60 KB。动画和板卡这时还可以是旧色。不要在这一步提交那份最终测试，它要等 53 张都再生完。
3. **波次 2。** 改四个 `anim_*.py`，跑 `gen_animations.py`。不跑 `svg2gif.py`。
4. **波次 3。** 改 `gen_boards.py` 和 `gen_pinouts.py`，跑这两个生成器。
5. **索引句。** 按「文件与三波」一节给 `assets/README.md` 加那一句。
6. **测试。** 加上 `test_sample_svg_c.py`。四个既有视觉方法和封面两个方法不改。版本断言留到下一步一起改。
7. **版本。** 同一 PR 内改 `revisions.json`、两份 manifest、`stm32-book/README.md`，并把版本断言改到实施时的实际新版本。修订说明只用上一节的四句。
8. **验证。** 下面四条里，前三条通过，并且 GIF 汇总哈希不变之后，再请求合入。第四条用来确认 16 张 ASCII GIF 仍能逐像素对上；若视频探测因环境缺 ffmpeg 或 Pillow 失败，不要改 `assets/video/`。

```bash
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
python3 stm32-book/build_html.py --lang en --check
python3 tools/check_assets.py
```

9. **合入。** `book` 与 `book-en` 都变绿之后，把实施 PR squash 合入 `main`。合入后在 `D:\Users\STM32` 拉取这次 `main`。不打 tag，不创建 Release。

实施 PR 的 diff 可以碰：`tools/svgkit.py`、`tools/gen_sample_figures.py`、`tools/gen_diagrams.py`、`tools/anim_basics.py`、`tools/anim_gpio.py`、`tools/anim_comm.py`、`tools/anim_sys.py`、`tools/gen_boards.py`、`tools/gen_pinouts.py`、`assets/animations/`、`assets/boards/`、`assets/diagrams/` 里上表的 53 张 SVG、`assets/README.md` 的那一句、`stm32-book/tests/test_sample_svg_c.py`、`stm32-book/tests/test_build.py` 里的版本断言、`stm32-book/revisions.json`、`stm32-book/manifest.json`、`stm32-book/manifest-en.json`、`stm32-book/README.md`。不碰 `tokens.json`、`book.css`、`cover.svg`、章节正文、`assets/gif/`、`assets/photos/`、`assets/video/`、`minigfx.py`、`gen_gifs.py`、`svg2gif.py`、`check_assets.py`、`.github/workflows/book.yml`。

合入前的最终 diff 必须同时有浅色 `T`、53 张再生的 SVG 和版本戳。不要把仍含 `#0b1220` 的 SVG 留成 PR 的最终内容。

## 风险

- **若手改 SVG 而不改生成器，下一次生成会把浅色盖回深色。** 成品只许由上表的命令写出。
- **若把 `T.TEXT` 用在 `#123a2e` 那块板岛上，字会沉进阻焊。** 板上的字用已经在零件色清单里的 `#dfe6f0`、`#8b98b0`、`#e2b23c`。
- **若脚名继续用 `SILK`，浅纸上会看不见。** 只有 `header()` 的脚名改成 `T.TEXT`。板上丝印仍用 `SILK`。
- **若把 `#c4552a` 拿来写 13px 的注意，对比大约 4.3。** 注意用 `#7a4e00`。书脊色留在封面和扉页。
- **若把整书等宽栈写进每个 `<text>`，H743 引脚图会再长大约 19 KB。** `FONT` 和 `MONO` 保持原文。
- **若重跑 `svg2gif.py`，公众号动图会换掉，而且 17 张仍然过不了 500 KB。** 不运行它。动画 SVG 与 `*-zh.gif` 的暂时不一致是这一刀接受的结果。
- **若顺手改 `minigfx.C`，`check_assets.py` 的逐像素比对会失败，16 张 GIF 也会离开汇总哈希。** `C` 保持深色。
- **若改 `book.css` 来「让图和框同色」，刀 D 的哈希会失效。** 框保持原样。图用自己的 `#fbfaf7`。
- **若给 `gen_tietu.py` 一起收圆角，就超出了 `assets/` 的 53 张。** 不改、不运行。

## 验收

### 本设计 PR

- 新增文件只有 `docs/superpowers/specs/2026-10-25-book-visual-sample-svg-C-design.md`。
- `stm32-book/`、`docs/` 章节、`docs/en/` 章节、资产、工具、workflow 和基线 `10a01ec` 相同。
- 版本号仍是 1.2.6。没有 tag，没有 Release。没有实施计划。

### 实施 PR

- 中文与英文 `python3 stm32-book/build_html.py --check` 以及 `--lang en` 通过。`python3 -m unittest discover stm32-book/tests -v` 通过。`book` 与 `book-en` 都绿。
- `builder.CSS` 的 SHA-256 仍是 `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`。`tokens.json`、`book.css`、`cover.svg` 的哈希仍是背景一节的三个值。
- 53 张 SVG 的画布和文本哈希与本文件的表一致。除 H743 外都小于 60 KB。H743 小于 80 KB，实施说明里写上实际字节数。
- 图内不再出现 `#0b1220` 和 `#22d3ee`。`stroke-width` 只有 `1`、`1.5`、`2`。`rx` 只有 `2`、`4`、`8`。
- `assets/gif/` 的汇总哈希不变。`docs/` 与 `docs/en/` 的正文 diff 为空。`cover.svg` 的 diff 为空。
- 出版书签条数仍是 44。没有 tag，没有 Release。

人工打开构建出的中文 HTML，看这几处：

- 第 00 章主图 `sample-00-boot-state.svg`：浅纸上能读出 BOOT0=0 和系统存储器。正常路径是深绿，失败路径是暗红。图里没有深色满版底。句子仍是现在的手册句。
- 第 03 章主图：PA0 与 PC13 仍是两块。圆角不再出现 10 和 6 这两档以外的卡片语言；卡片是 8 或 4。
- 任选一张动画，例如 `gpio-blink.svg`：浅底上灯仍会闪，类名还在。页脚仍有「自绘矢量动画」。
- 任选 Blue Pill 结构图：板身仍是蓝的，排针脚名在纸上是墨色，板上的丝印仍是浅色。
- 暗色：页面变暗时，这张图仍是浅纸，不跟随 `prefers-color-scheme`。封面仍是深色铜版。
- 印刷预览：任选一张样本图，纸面上是浅底线框，不是一块深色矩形。

英文书看同一张样本图即可。图与中文相同。不要求把 29 章逐页看完。

## 未决问题

没有会挡住样本图实施的未决项。下面几项按此处的默认执行。复审规格时可以改口。改「浅底还是深底」或「GIF 要不要重画」要在实施开始前定。只把某一个已经落在同一档里的 `1.6` 收成 `1.5`，不必再写一版设计：

1. **53 张一起改，分成三波，同一次 1.2.7。** 不把动画或板卡留到下一个版本。这一序列到刀 C 结束。
2. **浅纸，不跟随暗色。** 语义色用亮色令牌里过得了 4.5 的值。失败、注意、端口紫粉橙和 PE 用本文件写死的深色近亲。不用 `#c4552a` 做字。
3. **描边只留 1、1.5、2。圆角只留 2、4、8。** 板轮廓从 14 收到 8。零件色不收进这三档语义色。
4. **字体族字符串不改。** 不把 `--font-sans` 抄进 SVG。
5. **GIF 不重画。** 16 张 ASCII GIF 保持深色。24 张 `*-zh.gif` 保持字节，即使动画源已经变浅。
6. **H743 引脚图允许继续大于 60 KB，上限 80 KB。** 不拆图，不改 60 KB 这条仓库默认。
7. **不读 `tokens.json`。** 颜色是 `svgkit.T` 里的字面量。样式哈希保持 `a4ccd140…`。
8. **版本。** 建议实施 PR 写成 1.2.7。本设计 PR 不升。实施合入不打 tag，不创建 Release。设计 PR 等人审；实施 PR 在 `book` 与 `book-en` 变绿后 squash 合入。

## 英文提要

Sample-figure paint only, on v1.2.6 (`10a01ec`, PR #44). All 53 SVGs under `assets/` are byte-identical to their generators. Repaint them by editing `svgkit.T` and the stroke and corner literals, then regenerate. Do not hand-edit the SVG files. The canvas becomes paper `#fbfaf7`, ink `#17202a`, muted `#5e6872`, hairline `#d7dce1`, accent `#075e84`, and tip `#1b5c45`. Failure text is `#8f2d2d` and caution text is `#7a4e00`, because spine `#c4552a` is about 4.3 on paper and stays on the cover. Strokes are only 1, 1.5, and 2. Corner radii are only 2, 4, and 8. Board soldermask, gold, and silk stay on a frozen 48-hex list. Pin names that sit on the paper switch from silk to ink. Do not change sentences, coordinates, `viewBox`, font-family strings, `cover.svg`, `tokens.json`, or `book.css`. The assembled CSS hash stays `a4ccd1403ab742e82f67c39053c2609da1c9a8afa126d4f6b988a5b9559a5ac4`. Do not regenerate GIFs. The H743 pinout may stay above 60 KB and must stay under 80 KB. The provisional implementation version is 1.2.7. This design PR does not bump the version. Review this PR before merge. The later implementation PR squash-merges after the `book` and `book-en` jobs are green. This design PR only adds this file.
