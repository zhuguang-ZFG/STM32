# 贡献指南

感谢你愿意一起把这个知识库做得更好。

## 一、你能贡献什么

| 类型 | 做法 | 门槛 |
| --- | --- | --- |
| 纠错 | 指出错误的寄存器位 / 参数 / 公式 / 引脚，附上手册页码或实测截图 | 低 |
| 补动画 | 用 `tools/svgkit.py` 写一个新原理动画，并在 `assets/README.md` 登记 | 中 |
| 补示例 | 新增 `examples/<名字>/`，含 `main.c` + `README.md`，要求真实可编译 | 中 |
| 补文档 | 新增或扩写 `docs/NN-xxx.md`，遵循 [写作规范](docs/CONTENT_GUIDE.md) | 中 |
| 补实物结构图 | 用 `tools/gen_boards.py` 加一块板子的矢量结构图 | 高 |

## 二、动手前的四条约定

1. **先读规范**：[docs/CONTENT_GUIDE.md](docs/CONTENT_GUIDE.md)（文章骨架、命名、图片引用方式）。目录各管什么见 [STRUCTURE.md](STRUCTURE.md)。
2. **图片只能用仓库内的**：引用 `../assets/...` 下的相对路径，不要外链图床（GitHub 会代理失败）。
3. **诚实标注**：自绘矢量图不能说成「实拍照片」；数据要能追溯到手册章节。
4. **写人话**：见下面「文风约定」。`make lint-voice` 会把机械可查的部分拦住。

## 文风约定

正文按书来写，不按生成的文案来写。`tools/slop_lint.py` 查下面这几类，CI 也跑同一份规则。

| 不写 | 写 | 为什么 |
| --- | --- | --- |
| `✅` `❌` 当判定格 | `支持` / `不支持`、`可以` / `不能`、`必需` / `可选` | 表格那一列本来就是文字，符号读不出程度，也过不了读屏 |
| `> ⚠️ 文字` | `> [!WARNING]` 换行再写正文 | GitHub 原生渲染成警告框，整书构建也认这个标记 |
| 标题里加 emoji（`## 📌 学习目标`） | `## 学习目标` | 标题说清内容就够了 |
| 不写语言的代码块 | 写上语言；ASCII 图、公式、终端输出用 `text` | 不写语言时高亮器会把箭头和运算符涂成代码 |
| `赋能` `一站式` `轻松搞定` | 直接说它做什么 | 这类词不带信息 |
| `让我们` `综上所述` `值得注意的是` | 删掉，直接说下一句 | 这是过场，不是内容 |
| `delve` `robust` `comprehensive` `seamless` | 换成具体的词 | 同上，英文版一样 |

留着不改的：第 19 章的 `★` 难度星级（有契约测试）、表格空格里的 `—`、数字区间里的 `48–72 MHz`、中文正文里的破折号。这些是排版，不是文案。

单行要破例时，行尾加 `<!-- slop-lint: ignore -->`；整段破例用 `<!-- slop-lint: off -->` 和 `<!-- slop-lint: on -->` 夹起来。代码块、行内代码、链接和引号里的词本来就不查。

改写整段或整章时，`slop_lint.py` 之外再用仓库里的 sepia 过一遍。它查复述、口号、过场句这类句子和段落上的问题，做法见 [CONTENT_GUIDE](docs/CONTENT_GUIDE.md) 第 13 条。

## 三、本地检查（提交前必做）

```bash
# 1) 如果你改了 tools/ 里的生成脚本，重新生成素材
python3 tools/gen_animations.py
python3 tools/gen_boards.py
python3 tools/gen_diagrams.py
python3 tools/gen_gifs.py

# 2) 自检：SVG 是否为合法 XML、GIF 解码回验是否逐像素一致
python3 tools/check_assets.py

# 3) 改了任何 Markdown：查文风（纯标准库，很快）
python3 tools/slop_lint.py

# 4) 改了章节正文时，再跑整书契约（只改导航文档可以跳过）
python3 -m unittest discover stm32-book/tests -v
python3 stm32-book/build_html.py --check
```

相对链接由 `tools/check_assets.py` 检查。它还会检查讲解正片，因此需要本机有 Pillow、ffmpeg、ffprobe。只改了 Markdown 导航时，至少确认新链接指向的文件存在。

`tools/md2mp.py`、`gen_mp_covers.py`、`gen_tietu.py` 会把产物写到 `.gitignore` 里的 `wechat-mp/` 和 `final-videos/`。不要把这两个目录提交上来。

## 四、提交规范

```text
docs(05): 补充 PWM 占空比公式与呼吸灯动画
fix(gpio): 修正推挽输出灌电流上限描述
feat(anim): 新增 CAN 非破坏性仲裁动画
feat(board): 新增 STM32H750 开发板结构图
chore(tools): check_assets 支持体积告警阈值
```

- 一次提交只做一件事；
- 新增/修改图片时，请确认体积：SVG < 60 KB，GIF < 500 KB；
- PR 描述里请写清：改了什么、为什么、如何验证（贴 `check_assets.py` 的输出最好）。

## 五、新增一个动画的模板

```python
# tools/anim_xxx.py
from svgkit import Svg, T, anim_flow, anim_tx

def my_animation() -> Svg:
    s = Svg(900, 520, "标题", "副标题（一句话说明它演示什么）")
    s.header(tag="章节标签", tag_color=T.CYAN)
    # ... 画图：s.rect / s.text / s.waveform / s.arrow ...
    s.add_style(anim_flow(".myline", dur="1.5s"))
    s.footer("一句话结论")
    return s

ALL = [my_animation]
NAMES = {"my_animation": "my-animation"}   # 函数名 -> 输出文件名
```

然后把模块名加进 `tools/gen_animations.py` 的 `MODULES` 列表，运行即可。

## 六、行为准则

- 对事不对人，技术讨论请给依据（手册、实测、可复现的最小例子）；
- 不发布他人有版权的图片/文字；引用他人内容请注明来源与许可；
- 不接受任何形式的广告、课程引流与付费社群推广。
