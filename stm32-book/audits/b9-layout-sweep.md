# B9 版面清扫与两张板重绘：全书 324 张 SVG 的几何缺陷清零，ch02 两张文字墙改成图

状态：通过。日期 2026-11-05。基线：`0e2d5b3`（B8 收尾）之后的 main。范围：`assets/` 下全部 324 张非 handraw SVG，其中 28 张有改动。

与 B8 的差别：B8 是「六张图重画」，本批先是**全库几何体检**（文字出界、越边、互压、被后画的形状盖住、溢出所在卡片），把测出来的真缺陷逐条修掉；然后才重绘两张最重的文字墙（ch02）。锚点、gap、嵌入位置、manifest 一律不动（见 §5）。

## 1. 门验总览

| 门项 | 结果 |
|---|---|
| audit（deficit / parity） | 29 章 deficit 全 0、parity 全 True；与 `.temp/b8-audit.json` 逐字段比对**零差异** |
| check_assets | SVG 合法；链接 1,964/1,964 有效；照片 5/5 哈希与尺寸匹配 |
| build_html | zh `--check` PASS（29 章）；en `--check` PASS（29 章） |
| pytest 全量 | 188 passed（0 failed，约 5 分 48 秒） |
| 版面体检 | `324 files / 0 bad / 0 issues`（CLIP / EDGE / OVER / COVER / OVFL 五类） |
| slop_lint | 干净：没有机械命中 |
| 重生成确定性 | 每个被改文件的生成器重跑，产出与磁盘字节一致；未改文件不受影响（见 §10） |

工具口径：`python tools/audit_book.py --format json --write .temp/b9-audit.json`（cwd=仓库根）；`python tools/check_assets.py`（cwd=仓库根）；`python build_html.py --check --lang zh|en`（cwd=stm32-book/）；`python tools/slop_lint.py`（cwd=仓库根）；版面体检 `.temp/measure_svg.py`（无头 Chromium 逐元素取真实文本框，不入库）。

## 2. 改前缺陷清单

### 2.1 几何体检（第一轮：21 个文件 / 72 处）

用 `getBBox()` 逐元素量文本框，报四类：出画布（CLIP）、贴边 <6 px（EDGE）、两段文字互压 >较小者 30%（OVER）、文字被后画的不透明形状盖住 >15%（COVER）。

| 类别 | 文件数 | 典型 | 根因 |
|---|---:|---|---|
| CLIP + OVER | 6 | `sample-01-flash-path`、`sample-07-i2c-addr`、`sample-13-can-bit`、`sample-14-usb-enum`（出画布）；`sample-00-accept-gate`、`sample-00-learn-loop`（标题刚好咬住右端 chip 2–3 px） | `svgkit.header()` 的标题按 20 px 固定字号画，不看可用宽度；标签 chip 在右端，长标题直接压上去并冲出画布 |
| COVER | 5 | `bluepill`、`blackpill`、`nucleo-f411re`、`f4-discovery`、`f103zet6-dev` | `callout()` 编号徽标画在**元件本体中心**，把元件自己的丝印（`STM32F103`、`RT9193-33`、`PC13`、`LD4…`）整个盖掉 |
| OVER | 4 | `classic-03-debounce`、`classic-03-open-drain`、`gpio-blink`、`gpio-input-interrupt` | 同一坐标先写 A 再写 B；或标签落在后画的方框下 |
| OVER（引脚名挤） | 1 | `pinout-bluepill` | 12 个脚均分 200 px（间距 16.7），`PB2/BOOT1` 这类 9 字符脚名横排必然压住邻居 |

**测量口径本身有缺陷**：`getBBox()` 忽略 `transform`，而引脚图的上/下边脚名是旋转文字。`pinout-stm32h743zi-lqfp144` 的 3 处、`pinout-stm32l476rg-lqfp64` 的 1 处 OVER 是假警报。改用 `getBoundingClientRect()`（含变换）后这两个文件实测干净——这是本批修的第一个「工具缺陷即缺陷」，不是绕过。

### 2.2 溢出卡片（第二轮：6 个文件 / 8 处）

补一类检查 OVFL：文本框 ≥60% 落在某张卡片里，却没有完整落在卡片内。查出 8 处，其中 4 处是排版溢出（`specs()` 固定 200 px 宽装不下长值；`note[:30]` 按字数截断不管字形宽度；`sample-08-bus-compare` 的「典型负载」列只有 60 px 却放 85 px 的值；`sample-10-dma-phases` 的 13 px 英文步骤说明超出 210 px 卡片），另 4 处是贴近板边的元件丝印（按「丝印不能画在板外」一并修正）。

### 2.3 文字墙排名（重绘对象的选择依据）

按「图内字符数 ÷ 图元数」排序，越高越像「带框的段落」：

| 图 | 字符 | 文字条数 | >55 字长句 | 图元 | 字符/图元 |
|---|---:|---:|---:|---:|---:|
| sample-02-hse-fail | 1,728 | 27 | 17 | 10 | 172.8 |
| sample-02-boot-mode | 1,673 | 28 | 19 | 10 | 167.3 |
| sample-01-flash-triage | 1,652 | 26 | 18 | 10 | 165.2 |
| sample-15-rtos-triage | 1,639 | 33 | 13 | 10 | 163.9 |
| sample-17-perf-triage | 1,329 | 41 | 9 | 9 | 147.7 |

判定：图元密度 0.3–0.5 图形/百字符，读起来是五张叠放的卡片，每张 5–6 句整句。前两名属 ch02，本批处理；其余留作下一批（见 §8）。

## 3. 本批交付

### 3.1 工具层

| 改动 | 位置 | 说明 |
|---|---|---|
| 标题自适应 | `tools/svgkit.py` `fit_text()` | 按可用宽度（画布宽 − 左边距 − chip 宽 − 间隙）逐 0.5 px 降号，到 14 px 仍放不下才省略号截断；宽度估算用 `text_width()`（CJK 1 em，其余 0.52 em，等宽 0.56 em）。在 255 条真实渲染标签上标定：估算/实测中位 1.008，p95 1.20，故预留 5% 余量（`max_w / 1.05`），能放下的标题保持 20 px 不缩 |
| 旋转文字 | `tools/svgkit.py` `rot_text()` | 引脚名沿边竖排；`gen_pinouts.py` 的私有 `_rot_text` 改为委托它，重生成字节一致 |
| 编号徽标挂点 | `tools/gen_boards.py` `_badge()` + `chip/crystal/smd/led_smd/button/usb(n=…)` | 徽标挂在元件外框**外侧**（芯片在引脚环外角），与元件几何同源，不再手填 23 个圆心 |
| 卡片内文字 | `gen_boards.specs()`、`peripheral-wiring` 提示条 | 用 `fit_text()` 按宽度降号，替代按字数截断 |

### 3.2 全库几何修复（28 张）

| 文件 | 修了什么 |
|---|---|
| `sample-01-flash-path`、`sample-07-i2c-addr`、`sample-13-can-bit`、`sample-14-usb-enum`、`sample-15-rtos-prio`、`sample-16-stop-wake`、`sample-18-boot-triage`、`sample-01-build-accept` | 标题冲出画布 / 压住标签 chip：改由 `header()` 自适应，文字内容不变 |
| `sample-00-accept-gate`、`sample-00-learn-loop` | 磁盘版仍是旧的固定 20 px 标题（重生成后为 18 / 19.5 px）。`accept-gate` 的标题在 20 px 下量得 21..917 px，与右端「00」chip（914..930）实打实咬了 2.6 px——这一处只占较小文本框的 17%，没到 30% 的互压阈值，是「标题与 chip 任何相交都算缺陷」这条更严的专项扫描抓出来的 |
| `classic-03-debounce` | 抖动带标签从 y=108 移到 y=134：原来压在「原始波形」标题上 |
| `classic-03-open-drain` | 总线标签移到线下方（原来被 Rp 方框盖住）；「截止」由与「NMOS」同坐标改为错开 22 px |
| `layers-hal-ll-reg` | 「抽象层次提高 ↑」从 (540,270)（被右侧面板整个盖住）移到箭头顶端 |
| `project-structure` | 目录树行距 26→24（第 16 行原被「小技巧」卡片压住），卡片下移 18 px |
| `bluepill`、`blackpill`、`nucleo-f411re`、`f4-discovery`、`f103zet6-dev` | 徽标改挂外框；blackpill 按键上移 30 px 让开排针焊盘；f103zet6 的 RESET 移出键排；f4 的 LED 行下移、重复的「主频/存储」行删除（下方 specs 卡片已有） |
| `pinout-bluepill` | 芯片 200→300 px、底/顶脚名竖排；删除图内的「5 个要点」段（该段是散文，ch21 与 ch16 正文已有同一份内容） |
| `gpio-blink` | 说明拆两行，让开 LED 状态标签 |
| `gpio-input-interrupt` | 命中的那格不再先写「读」再被高亮块盖住 |
| `boot-sequence` | 向量表卡片加高 8 px，最后一行不再贴住下边框 |
| `peripheral-wiring` | 提示条按宽度降号（原来 268 px 的字挤在 258 px 卡里） |
| `sample-08-bus-compare` | 七列重分：典型负载 60→115 px，信号列 190→175 px（`SCK+MOSI+MISO+CS` 仍放得下） |
| `sample-10-dma-phases` | 步骤说明 13→11.5 px，`USART/ADC/TIM asserts DMA req` 不再越出 210 px 卡片 |

### 3.3 两张板重绘（ch02）

文件名、960 宽外的画布高度（720 / 620）、嵌入位置不变，图注与 alt 两版同步改写（原图注写的「上半/中间/下半」是旧版式）。

| 图 | 改前 | 改后 | 画面 |
|---|---|---|---|
| `sample-02-hse-fail` | 1,728 字 / 27 条 / 17 长句 / 10 图元 | **832 字 / 44 条 / 1 长句 / 49 图元** | 上：HSE→PLL×9→SYSCLK 72 MHz 三个方块，右侧三个消费者（USART1 BRR 0x271、SysTick 72000、LATENCY=2）；中：HSE 停振后被 CSS 切到 HSI 8 MHz 的同一条链，红框+叉，右侧同样的三个消费者变成 12800、9.000 ms、LATENCY 仍为 2；下：115200 与 12800 两根横条（9 倍差）+ 三个寄存器读数 + NMI 写 CSSC |
| `sample-02-boot-mode` | 1,673 字 / 28 条 / 19 长句 / 10 图元 | **658 字 / 41 条 / 1 长句 / 40 图元** | 上：第 44 脚 BOOT0 与共脚 BOOT1 两个输入，经「启动选择」扇出到主 Flash 0x0800_0000 / 系统存储器 0x1FFF_F000 / SRAM 0x2000_0000 三块本体；中：三行组合（BOOT1/BOOT0 各画成一个小方格，→ 结果条）；下：三个检查点 |

密度：172.8→17.0、167.3→16.5 字符/图元。数字口径全部回到章节正文：倍频与等待周期来自 RM0008 §7.3.2，BRR 39.0625/0x271 来自第 06 章，别名与选择表来自 RM0008 §3.4 表 9，引脚与容量来自 DS5319 Rev 20。

## 4. 三类型归属（§15.1-23）

两张重绘板都是**排错图**（第三类）：画面承担「顺着故障分支走一遍」——HSE 停振板让读者看见同一份分频在被 CSS 换掉时钟后逐项失效；BOOT 板让读者看见「同一个 0x00000000 可能落在三块本体上」。其余 26 张只改排版，不改变类型归属。

## 5. 锚点与 gap（无变化）

`.temp/b9-audit.json` 与 `.temp/b8-audit.json` 逐章逐字段比对（chars / visual_anchors / target_visual_anchors / visual_anchor_deficit / max_visual_gap_chars / overlay_visual_anchor_deficit）：**零差异**。本批不新增、不删除、不移动任何嵌入点，也不改 manifest。

## 6. 超预算间隙

沿用 `b7-converge-census.md` §2.1 的 25 条软预算例外，逐条数值未变。本批不新增例外，也不新开补偿锚点。

## 7. 许可与出处

不引入任何第三方素材。两张重绘板的出处行与图注引用不变（RM0008 Rev 21 §7.3.2 / §3.4 表 9、DS5319 Rev 20、第 06 章 BRR 算式），许可仍为 CC BY 4.0（`自绘 · 静态`）。`ch02_b2.py` 的英文正文保持不变——这两张图是中英两版共用同一文件，图内正文用英文是既有约定，不是缺陷。

## 8. 落点论证

- ch02 的两张图分别嵌在「时钟树与分频」与「启动模式」两节，图注改写后仍是同一条论证：先读字段、再对算式、最后给检查点。
- 删除 `pinout-bluepill` 图内「5 个要点」段：⑤ 未使用 IO 配模拟输入在 ch16 §「低功耗」有整节，①②③ 去耦/复位/BOOT 在 ch21「最小系统六件套」表里逐项列出，④ 5 V 容忍在 ch03 §11 有专表。图不再替正文说话。
- f103zet6 / f4 图内复述的「主频 · Flash · SRAM」一行与同图下方 specs 卡片重复，删图内那行。

下一批（未做，登记在此）：`sample-01-flash-triage`(165.2)、`sample-15-rtos-triage`(163.9)、`sample-17-perf-triage`(147.7)、`sample-16-pwr-triage`(146.8)、`sample-13-can-triage`(138.8)、`sample-12-boot-compare`(136.8)、`sample-12-iap-map`(133.0)、`sample-11-rtc-triage`(132.3) 等 12 张仍属「卡片里堆整句」的静态板，按 B8/B9 同一方法逐张重绘。

## 9. 哈希登记

`text_hash = sha256("\n".join(text 内文))`，与 `test_sample_svg_c.ROWS` 逐字一致；字节数为磁盘原始字节（CRLF 口径）。

| 文件 | bytes | sha256 前 16 |
|---|---:|---|
| `animations/boot-sequence.svg` | 14257 | `d6d1baa08f2d9763…` |
| `animations/gpio-blink.svg` | 14629 | `81690ee196c303d2…` |
| `animations/gpio-input-interrupt.svg` | 13733 | `91523ae894f3e4a3…` |
| `boards/blackpill-stm32f411ce.svg` | 32342 | `511d86c80d8862e7…` |
| `boards/bluepill-stm32f103c8t6.svg` | 35752 | `8f4d1581c6b4ba63…` |
| `boards/f103zet6-dev.svg` | 26435 | `e3dbb3e02afe0cbf…` |
| `boards/f4-discovery.svg` | 26480 | `38d9fc620839b504…` |
| `boards/nucleo-f411re.svg` | 21539 | `e52ce8055d27e38a…` |
| `boards/peripheral-wiring.svg` | 14177 | `f7210ea4e61af5bd…` |
| `boards/pinout-bluepill.svg` | 33856 | `9ec78f08a53e93da…` |
| `diagrams/classic-03-debounce.svg` | 11186 | `6bd1b7b8c6f2e744…` |
| `diagrams/classic-03-open-drain.svg` | 14389 | `f82fdd1683523576…` |
| `diagrams/layers-hal-ll-reg.svg` | 10453 | `2ce7570576e925d0…` |
| `diagrams/project-structure.svg` | 13031 | `53f68cd4e58288a3…` |
| `diagrams/sample-00-accept-gate.svg` | 9596 | `487806482cb3425e…` |
| `diagrams/sample-01-build-accept.svg` || `diagrams/sample-00-learn-loop.svg` | 12080 | `f6e3cb6fb26e7495…` |
 10678 | `9e6c95fbdcb962e4…` |
| `diagrams/sample-01-flash-path.svg` | 11680 | `a57ee9fa3594d3ce…` |
| `diagrams/sample-02-boot-mode.svg` | 14370 | `cdcd87d572ac7b40…` |
| `diagrams/sample-02-hse-fail.svg` | 16158 | `497b0d449566deab…` |
| `diagrams/sample-07-i2c-addr.svg` | 6654 | `5d8aeb4df50370a3…` |
| `diagrams/sample-08-bus-compare.svg` | 15494 | `eeab1e6708355479…` |
| `diagrams/sample-10-dma-phases.svg` | 7442 | `ca77d1ea5d6fad91…` |
| `diagrams/sample-13-can-bit.svg` | 7213 | `0e1da8a54f67b469…` |
| `diagrams/sample-14-usb-enum.svg` | 7139 | `a6cf18d79c5d09d0…` |
| `diagrams/sample-15-rtos-prio.svg` | 6831 | `a6c5ccb5affa24af…` |
| `diagrams/sample-16-stop-wake.svg` | 7181 | `41341af8f070f2b9…` |
| `diagrams/sample-18-boot-triage.svg` | 6546 | `ab5be4eb7af108fb…` |

## 10. 测试锁

`stm32-book/tests/test_sample_svg_c.py`：`ROWS` 仍为 **324** 行（非 handraw 全集），本批更新其中 **28** 行的 `bytes + text_hash`，并用 `tools/sample_figs_quality3/update_locks.py` 重锁；该脚本的两处既有缺陷（把 `illustrations/handraw/` 混进 ROWS、资产未变也重写行）在 B8 已修，本批沿用。

重生成确定性：每个被改文件的生成器（`gen_sample_figures.py`、`sample_figs_b2/ch01_b2.py`、`sample_figs_b2/ch02_b2.py`、`sample_figs_b3/ch08_b3.py`、`sample_figs_b4/ch1{3,5,6,7}_b4.py`、`gen_diagrams.py`、`gen_gpio_classic.py`、`gen_boards.py`、`gen_pinouts.py`、`gen_animations.py`/`anim_basics`、`sample_figs_quality/figures_q.py`）重跑后与磁盘逐字节一致。**注意**：`gen_animations.py` 全量重跑会重写 `g0-boot-swd.svg` 与 `uart-frame.svg`（磁盘版本来自更晚的改写通道，标题与关键帧不同），本批已 `git checkout` 还原，未纳入提交。

## 11. 验证记录

命令与结果（按执行顺序）：

1. `python tools/gen_sample_figures.py`、`python tools/sample_figs_b2/ch01_b2.py assets/diagrams` 与 `ch00_b2.py` —— 28 张中 10 张变化，全为标题字号（`text_hash` 不变，`bytes` 变）。
2. `python .temp/measure_svg.py --all` —— 依次收敛到 `324 files / 0 bad / 0 issues`（CLIP / EDGE / OVER / COVER / OVFL 五类合计）。
3. `.temp/lint_svg.py`（自绘/无动画/着色调色板/stroke-width/rx 五条锁）—— 全库 0 问题。
4. `python tools/check_assets.py` —— 全部通过（SVG 合法、链接 1,964/1,964、照片 5/5）。
5. `python build_html.py --check --lang zh` / `--lang en`（cwd=stm32-book/）—— 两版 PASS，29 章。
6. `python tools/audit_book.py --format json --write .temp/b9-audit.json` —— 29 章 deficit 0、parity True，与 b8 逐字段零差异。
7. `python tools/slop_lint.py` —— 干净。
8. `python -m pytest stm32-book/tests -q` —— 首次全量跑出 1 failed：`sample-02-hse-fail.svg` 的红色叉用了 `stroke-width=2.5`，违反 `test_sample_svg_c` 的调色板/线宽锁（只允许 1 / 1.5 / 2）。这是**图的缺陷不是测试的缺陷**，改图为 2 后重锁（`bytes` 16,162→16,158，`text_hash` 不变），定向 `test_sample_svg_c.py` 1 passed，再全量重跑 188 passed（0 failed，约 5 分 48 秒）。

已知限制：本批的版面判定全部来自几何测量（真实字体文本框 + 图元遮挡关系），没有做视觉目检——本机视觉通道 `?q=` 不可用（连续 `model_not_found`）。几何检查能证明「不出界、不互压、不被盖住、不溢出卡片」，不能证明「构图好看」，这一点与 B8 相同。

## 12. 生成器–磁盘对账（补做）

§10 当时只重跑了「本批动过的那几个」生成器，等于用抽样代替全量：`header()` 改成自适应后，任何**没重跑**的生成器都在磁盘上留着旧的固定 20 px 标题。这个漏洞是被 `sample-00-accept-gate` 撞出来的（标题与右端 chip 咬 2.6 px，占较小文本框 17%，小于互压阈值 30%——五类几何检查不会报），说明「只有被重跑的生成器才是可信的」是个未经验证的假设。

做法：干净工作树下逐个重跑 `tools/` 与 `tools/sample_figs_*/` 的全部生成器，用 `git status` / `git diff` 反查漂移；**只**采纳标题字号类差异，其余一律还原。

| 生成器族 | 结果 |
|---|---|
| `gen_sample_figures.py`、`gen_diagrams.py`、`gen_gpio_classic.py`、`gen_boards.py`、`gen_pinouts.py` | 逐字节一致 |
| `sample_figs_b2/ch00,ch01,ch02` 、`sample_figs_b3/*`、`sample_figs_b4/*`、`sample_figs_b5/ch*_b5`、`sample_figs_b6/figures_b6`、`sample_figs_quality{1..5}/figures_q*.py`、`gen_stack_diagrams.py`、`gen_tietu.py`、`remake_shared.py` | 逐字节一致，**除**下列三处标题字号 |
| `sample_figs_b2/ch05_b2.py` | `sample-05-pwm-debug` 标题 20 → 19.5 px（加 rx 缺陷，见下） |
| `sample_figs_b4/ch17_b4.py` | `sample-17-obs-compare` 20 → 19.5、`sample-17-perf-triage` 20 → 19 px |
| `gen_stack_diagrams.py` | 重算内联的 base64 图（`stack-gpio-pc13-led.html` 8 行），跟随上面的字号变化 |

对账顺带挖出三个真问题：

1. **`ch04_b2.py` / `ch05_b2.py` 会产出锁不接受的圆角**：两个生成器写 `rx=6`，而 `test_sample_svg_c` 只允许 `{2,4,8}`，磁盘上一直是 `rx=4`。也就是说这两个脚本当时一跑就会把图改成「测试必挂」的状态——已把生成器改回 `rx=4`，现在重跑与磁盘逐字节一致（`sample-04-exti-triage` 无变化，`sample-05-pwm-debug` 只剩标题字号差异）。
2. **`anim_b5.py` / `anim_b6.py` 被误指到 `assets/diagrams`**：4 张动画板（`sample-20-lookup-flow`、`sample-21-power-swd`、`sample-23-boot-latch`、`sample-28-owner-flow`）被写进了静态图目录，与 `assets/animations/` 下的正本逐字节相同。已删除副本；`ROWS` 因此从 328 回到 **324**（动画板不进静态锁）。这两个脚本的正确目标是 `assets/animations/`，重跑后该目录零漂移。
3. **`gen_animations.py` 仍不是 `g0-boot-swd` / `uart-frame` 的权威写入者**：全量重跑会把这两个文件退回旧标题与旧关键帧时序。本批继续用 `git checkout` 还原，结论不变（§10）。

对账后的最终状态：`measure_svg.py --all` → `324 files / 0 bad / 0 issues`；`test_sample_svg_c` 1 passed、`ROWS` 324 行；`check_assets` 全部通过（链接 1,964/1,964）；`build_html --check` zh / en 均 PASS；`audit_book` 与 b8 的字段差异只有 ch02 的字符数（caption 重写所致，+81 zh / +163 en），deficit 与 parity 一律不变。

## 13. 动画提升（B10）

版面清扫解决的是「不出界、不压字」，这一节解决「动不动、看懂不懂」。先用脚本给 65 张动画打分（循环周期、是否有物体位移、有无缓动/阶跃、有无阶段标记、有无 reduced-motion），再逐张改。

| 文件 | 改前 | 改后 |
|---|---|---|
| `i2c-transaction` | 位表 + 只有 SCL 一条波形，0 个动画 | 静态时序图：SDA 与 SCL 都画出来，每拍一个采样点 + 竖直引导线（**保持无 `<style>`**：契约测试要求这张能直接打印，动起来的是配套 `i2c-timing.gif`） |
| `clock-tree` | 4 个 token 各自 1.2 s 空转，读不出先后 | 一个时钟脉冲按 HSE→PLL→SYSCLK→HCLK 顺序走，每跳 1.3 s、总 5.2 s；虚线流动放慢到 2.6 s |
| `spi-transfer` | 1.6 s 走完 4 个 bit，SCK 波形是死的 | 3.4 s / 4 个 bit，上升沿上 8 个采样点按拍点亮，和移动的 bit 同步 |
| `can-arbitration` | 整行一起闪（`c0/c1/c2` 类挂在每一行所有位上），看不到「第几位分出胜负」 | 扫描框按 11 位逐位推进（6.6 s，`steps(11)`），B/C 在 bit9 输掉时整行降到 28 % 不透明度，胜者保持「仲裁中」 |
| `adc-sar` | 12 个格子一直写「?」，正文却说「比较完就固定下来」 | 每拍把判定结果写进格子（0x800 逐位成形），8.4 s 走完 12 拍；「?」占位符删掉，避免和结果文字重叠 |
| `sample-09-adc-sar-weights` | 台阶只有高亮走，没有东西在走 | 台阶之间加 token（`d{i}`），和高亮同步从 b11 走到 b0；周期 6.5→8.4 s |
| `boot-sequence` | 8 个步骤逐个亮，但看不出「CPU 在哪」 | 加 PC 指针：第一行走完换行，第二行接着走，`steps(4)` 跳格；周期 7.2→9.6 s |
| `lowpower-wakeup` | 三根电流条一起呼吸（2.4 s 脉冲），长度不变 | 按 Sleep→Stop→Standby 顺序长出条形（6.6 s），条形长度就是相对电流 0.90 / 0.55 / 0.20，旁边标数值 |

顺带修掉两处几何隐患：`rx=6` 不在锁允许的 `{2,4,8}` 里（新增扫描框用错了），以及 SAR 的 `?` 与结果文字同位重叠（12 处 OVER）。

验证：`measure_svg --all` → 324 / 0 / 0；`test_sample_svg_c` 1 passed（`ROWS` 仍 324，重锁 9 行）；`check_assets` 全通过；`slop_lint` 干净；全量 pytest 188 passed（5 分 50 秒）。

保留未动的一张：`i2c-transaction` 要真正动起来必须去掉「静态可打印」的契约测试断言（`assertNotIn("<style", i2c)`），这属于改测试策略，按规矩需要所有者点头，所以本轮只把它画得更完整（补 SDA 波形与采样点），动画仍由 `i2c-timing.gif` 承担。

## 14. 四张文字墙重绘（B11）

`walls.py` 按「字符数 / 图元数」排序，前四名依次是 ch01 闪存下载、ch15 RTOS、ch17 性能、ch16 低功耗。四张都只有 8–12 个图元、24–41 段文字，属于「用方框装散文」。按 B8/B9 的方法重画：先把章节里的数字核一遍，再把每条结论变成可看的结构。

| 文件 | 改前 chars / shapes | 改后 | 画了什么 |
|---|---|---|---|
| `sample-01-flash-triage` | 1,652 / 10（165.2） | 1,145 / 49（**23.4**） | 顶部一条链证明「attach 通了，前面都无罪」（OpenOCD → ST-Link → 第 34/37 脚 → 内核 halted ✓ → Flash ✗）；三列岔口各带三个编号检查点 + 修法框；底部 2.7 V 编程下限量程条（红区 + 刻度）与 `adapter speed 1000 → 100` |
| `sample-15-rtos-triage` | 1,639 / 10（163.9） | 1,061 / 166（**6.4**） | 顶部两条时基（SysTick 1 ms / TIM4）；左列三道闸门 → `vTaskStartScheduler()`；中列把 128 字画成 16×8 个格，并画出「按字节只给 32 格」的缺口；右列两条方向相反的优先级轴 + 0–4 禁区 + `0x50 = 5 << 4`；下方 10240 字节堆按 512/768/1024/7936 分账，再画 3 ms + 10 tick = 13 ms 与 `vTaskDelayUntil` 的 10 ms |
| `sample-17-perf-triage` | 1,329 / 9（147.7） | 982 / 129（**7.6**） | 顶部两次读数夹住被测代码的时间轴 + 72 格刻度；左上读数为 0 的因果与按收益排序的修改阶梯；右上 -Og/-O2/-Os 三栏各核周期数、代码大小、输出一致；下半 CFSR → HFSR → BFAR 冻结链、bit15 判定门、栈帧里 PC 的位置（SP + 0x18）与三类常见原因 |
| `sample-16-pwr-triage` | 1,468 / 10（146.8） | 1,038 / 48（**21.6**） | 顶部对数刻度把 14.4 mA / 14 µA / 2 µA 摆到一条尺上；左列两个模式位（SCB_SCR SLEEPDEEP、PWR_CR PDDS）与 LPDS；中列 HSI 8 MHz 与 PLL 72 MHz 的条对比 12800 / 115200；右列逐项泄漏（IWDG 3.4 µA、LSI 3.2 µA、10 kΩ 0.33 mA、LED 2 mA）；下方 Standby 四格条件 + 四种唤醒时间条 |

图注同步改写（zh / en 各 4 张）：补「看哪里」的具体结构，原有「证明什么 / 不证明什么」与出处保留。数字全部与章节正文对齐：2.7 V 编程下限见 DS5319、`0x50 = 5 << 4` 与 128 字 = 512 字节见 FreeRTOS 章、72 计数 = 1 µs 见 PM0056 DWT、14 µA 与 5.4 µs 见 DS5319 表 16 与表 26。

四张图的生成器与磁盘逐字节一致（`ch01_b2` / `ch15_b4` / `ch16_b4` / `ch17_b4` 重跑无差异），`update_locks.py` 重锁 4 行，`ROWS` 仍 324。`measure_svg --all` → 324 / 0 / 0；`check_assets` 全通过；`build_html --check` zh + en 均 PASS；`audit_book` 与上一轮相比只有章节字符数变化（caption 变长），deficit 与 parity 不变。
