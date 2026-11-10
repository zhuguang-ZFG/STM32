# 视觉锚点反推（image-prompt-reverse 用途证据）

日期：2026-11-10。对应 `BOOK_CLASSIC_CONVERGE_SPECS.md` §6.4
（新系列仍先反推 3–5 个视觉锚点）与 `BOOK_VIDEO_CLASSIC_SPECS.md`
SP-08 第 3 项（五个技能留下可审查用途）。

## 方法

- 按 `image-prompt-reverse` 流程执行：以本地最高质量查看目标图，
  内部完成媒介/主体/构图分析，产物只保留正向提示词与负面提示词。
- 五张锚点覆盖四条视觉轨：AI Handraw 知识轨（锚点 1）、脚本 Handraw
  板绘轨（锚点 2）、stack-diagram 工程轨（锚点 3）、实拍真证轨（锚点 4）、
  视频课件帧（锚点 5）。
- 全部图片仅本地读取，**未上传任何第三方服务**。
- 提示词只复现视觉机制，**不是事实来源**：不从图片反推寄存器值、型号、
  参数或实验结论；文字内容以源文件为准，生成模型只负责版式与图形语言。
- 锚点 5 为视频帧，可按下列命令从源视频确定性重建（`.temp/` 为
  gitignore 临时目录，哈希为本次分析时的取值）：

  ```bash
  ffmpeg -hide_banner -loglevel error -ss 30 -i assets/video/ch16-lp.mp4 \
    -frames:v 1 -q:v 2 .temp/visual-anchors/ch16-frame-30s.jpg
  ```

## 锚点 1：AI Handraw 知识插图（ch13 CAN 位时序）

- 源：`assets/illustrations/handraw/ch13-can-bit.png`
- SHA256：`a8f9f02493559f96fe112f3276771c2afb3645b274f924ba2582f294e29c426a`
- 媒介边界：二维手绘白板风知识插图（数字绘制的墨线示意图），
  非摄影、非三维渲染、非写实。
- 复现锚点：米白纸底 + 深藏青细墨线；绿框 OK / 黄框 FAIL 的双卡
  对照结构；波形草图只用方波、双向箭头、虚线参考线与小方框；
  无阴影无渐变，整幅像纸面扫描。

### 正向 Prompt

中文：
手绘白板风教学示意插画，米白纸底，全部图形用深藏青细墨线勾画，线条粗细均匀、略带手绘的轻微弯曲但整体工整。竖版画面顶部是一行深藏青粗体标题占位文字。其下分成上下两张宽圆角矩形卡片：上卡细绿色描边，左上角有草绿色大写标签占位；下卡细芥末黄描边，左上角有黄色大写标签占位。上卡内部，左侧是一个深藏青描边的说明方框，框内排列多行等宽手写体文字占位；方框右侧引出上下两条水平线，每条线上方各有一个小型文字标注块，两线接入画面中央一个空白大矩形作为收发器示意；该矩形右侧再引出两条水平线，各串一个锯齿状电阻符号，向东终止于短横线，线端上方有小文字。下卡内部从左至右是三段波形草图：左段为一根方波电平线，中央压一个竖直双向箭头，箭头上下方各配文字；中段为单个方波脉冲，配一条向右延伸的虚线水平参考线，脉冲上方有文字；右段为三个高低错落的小空方框，各配斜向引线与采样文字。全部文字均为无衬线手写感占位，不承载真实资讯。平视正投影构图，无阴影无渐变，光线均匀如同纸面扫描，主色米白，辅色深藏青，点缀草绿与芥末黄，饱和度中庸，留白充足，气质是工程师在白板上画的对照草图，理性克制；后期不锐化不噪点，边缘清晰，媒介为二维手绘知识插图，非摄影非三维渲染。

English:
Hand-drawn whiteboard-style instructional diagram on an off-white paper background, all shapes drawn with fine navy ink lines of even weight, slightly hand-drawn but tidy. A vertical composition: one bold navy title placeholder along the top; below it two wide rounded-rectangle cards stacked vertically, the upper card outlined in thin green with a grass-green uppercase label placeholder at its top-left, the lower card outlined in thin mustard yellow with a yellow uppercase label placeholder at its top-left. Inside the upper card, a navy-outlined explanation box on the left holds several rows of monospaced handwritten text placeholders; two horizontal lines leave the box's right edge, each with a small text label above, and enter a large empty rectangle in the center acting as a transceiver; two more horizontal lines leave that rectangle's right side, each passing through a zigzag resistor glyph and ending at a short terminal dash with small text above. Inside the lower card, three waveform sketches sit left to right: a square-wave level line with a vertical double-headed arrow at its center and labels above and below; a single square pulse with a dashed horizontal reference line running right and a label above; three small empty rectangles at staggered heights with diagonal leader lines and sampling labels. All text is sans-serif handwritten-style placeholder, carrying no real information. Straight-on orthographic view, no shadows, no gradients, even lighting like a paper scan, cream base with navy lines and green/yellow accents at moderate saturation, generous whitespace, the calm rational feel of an engineer's comparison sketch on a whiteboard; no sharpening or noise in post, crisp edges; medium is a two-dimensional hand-drawn knowledge illustration, not photography and not 3D rendering.

Negative:
photorealistic, 3D render, gradient shading, drop shadow, glossy highlights, watercolor wash, chalk texture, paper crease, coffee stain, neon colors, blurry strokes, wobbly hand tremor, dense clutter, brand logo, watermark

## 锚点 2：脚本 Handraw 板绘信息卡（ch16 电流格子核对）

- 源：`assets/illustrations/handraw/ch16-cell-triage.png`
- SHA256：`b2afe0933c675e328a81478d688c418186686f680b268926ce299e9ccdf400b5`
- 媒介边界：二维板绘信息卡（脚本生成的排版 + 手绘感描边），
  非摄影、非三维渲染，卡底自带「原理示意 / 非实拍」口径。
- 复现锚点：奶油纸底 + 芥末黄手绘标题下划线；四张同宽堆叠卡、
  各自一种描边色（藏青/砖红/赭黄/松绿）；底部灰胶囊印章
  + 花括号装饰线；全图无图标无阴影。

### 正向 Prompt

中文：
手绘板绘风知识信息卡，奶油米色纸底，竖版单列构图。顶部一组手写衬线感的大标题占位文字，标题下压一条芥末黄色的手绘粗下划线，下划线两端微微收笔露出笔锋；标题下方一行浅灰色细体副标题占位。主体是四张上下堆叠的宽幅圆角矩形卡片，卡片间距均匀并留出左右页边；每张卡片用细而略不规则的墨线描边，描边颜色各不相同，从上到下依次为深藏青、砖红、赭黄、松绿；卡片四角为手工圆角，四张卡片的宽度严格一致，形成稳定的竖向节奏；每张卡片内部左上为一行该色粗体小标题占位，其下为一行深灰细体说明文字占位，行距宽松，无图标无插画。四张卡片下方居中一行砖红色小字占位。画面底部中央是一个浅米灰色圆角胶囊形印章框，框内深灰小字占位，胶囊左右两端各配一段手绘花括号式装饰线。整幅画面平视正投影构图，无阴影无渐变，光线均匀如纸面扫描，色彩只有奶油底、深灰墨线、砖红、赭黄、松绿与深藏青五种，低饱和高留白，气质像一页认真手抄的核对清单，克制、秩序、可逐行阅读；后期无锐化无噪点，边缘干净，媒介为二维板绘信息卡，非摄影非三维渲染，非实拍。

English:
Hand-drawn board-illustration knowledge card on a creamy off-white paper background, vertical single-column layout. At the top, a large serif-ish handwritten title placeholder underlined by a thick mustard-yellow hand-drawn stroke whose ends taper like a brush lift; a thin light-grey subtitle placeholder sits below. The body is four wide rounded-rectangle cards stacked vertically with even gaps and generous side margins; each card is outlined with a thin, slightly irregular ink line in a different color — navy, brick red, ochre, pine green from top to bottom; all four cards share identical width and hand-rounded corners, forming a steady vertical rhythm; inside each card, a bold small title placeholder in that same ink color at the top-left, followed by one line of dark-grey body text placeholder, wide leading, no icons and no spot illustrations. Below the four cards, a single centered line of brick-red small text placeholder. At the bottom center, a pale greige rounded pill-shaped stamp box containing small dark-grey text placeholder, with hand-drawn curly-brace flourishes on both ends of the pill. Straight-on orthographic view, no shadows, no gradients, even lighting like a paper scan; only five colors — cream base, dark-grey ink, brick red, ochre, pine green, navy — low saturation, high whitespace, the temperament of a carefully hand-copied checklist, restrained, orderly, readable line by line; no sharpening or noise in post, clean edges; medium is a two-dimensional board-drawn information card, not photography, not 3D rendering, not a real object.

Negative:
photorealistic, 3D render, drop shadow, glossy surfaces, gradient background, neon palette, torn paper edges, crayon scribbles, shaky hand tremor, crooked card alignment, mixed typefaces, dense clutter, gibberish pseudo-text, watermark, brand logo

## 锚点 3：stack-diagram 工程示意图（PC13 点灯链路）

- 源：`assets/diagrams/stack-gpio-pc13-led.png`
- SHA256：`3677daa7780d086868437f41450664e8d2faa6c58ed07ccbadeb188c1fa960d9`
- 媒介边界：现代扁平矢量工程示意图（UI 风图标 + 蓝图网格），
  非手绘、非摄影、非三维渲染。
- 复现锚点：浅灰细网格蓝图底；橙框（固件侧）/ 蓝框（板载灯路）
  上下两块半透明面板；白色圆角方形图标 + 水平实线箭头；
  一条垂直虚线箭头跨面板连接两张图。

### 正向 Prompt

中文：
扁平矢量工程示意图，浅灰色细网格蓝图底纹铺满整幅横版画面，网格线极细、等距、低对比。画面由上下两块半透明白色圆角面板构成：上方面板细橙色描边，左上角一组小图标配深灰标题占位；面板内左端一个白色圆角方形图标，内为代码文档与尖括号符号，右端一个白色圆角方形图标，内为芯片方形轮廓与引脚点，两图标之间一条灰色水平实线箭头，箭头上方一行浅灰小字占位，图标下方各两行文字占位。下方面板细蓝色描边，左上角小圆形图标配蓝色标题占位；面板内从左至右等距排列四个白色圆角方形图标：闪电状电源符号、灯泡轮廓、同心圆加输出点、接地符号，四者以蓝色水平箭头依次相连，每段箭头上方有极小的蓝色标注文字，每个图标下方两行文字占位。一条垂直灰色虚线箭头从上面板右端图标底边垂下，穿过面板间隙指向下方面板第三枚图标顶边，虚线中点旁有一枚浅灰小标签。整体正投影俯视，无倾斜无透视，无阴影无渐变，主色为白与浅灰，点缀橙与蓝两色，浅色低饱和，构图工整对称，情绪冷静、说明性强，像一页系统架构图的局部；后期无噪点，线条锐利，媒介为现代扁平矢量示意图，非手绘非摄影非三维渲染。

English:
Flat vector engineering diagram over a light-grey fine grid blueprint texture that covers the whole landscape frame, the grid lines extremely thin, evenly spaced and low contrast. Two translucent white rounded panels stack vertically: the upper panel has a thin orange border, a small icon cluster and dark-grey title placeholder at its top-left; inside, a white rounded-square icon on the left containing a code-document glyph with angle brackets, and a white rounded-square icon on the right containing a chip outline with pin dots, joined by a horizontal grey solid arrow with one line of pale-grey text placeholder above it and two lines of placeholder text beneath each icon. The lower panel has a thin blue border, a small round icon and blue title placeholder at its top-left; four evenly spaced white rounded-square icons run left to right — a lightning power glyph, a light-bulb outline, a concentric circle with an output dot, and a ground symbol — connected in sequence by blue horizontal arrows, each arrow carrying a tiny blue label above it and each icon two lines of placeholder text below. A vertical grey dashed arrow drops from the bottom edge of the upper panel's right icon, crosses the gap between panels and points at the top edge of the third icon in the lower panel, with a small pale-grey tag beside the middle of the dashes. Straight-on orthographic top view, no tilt, no perspective, no shadows, no gradients, white and pale grey dominant with orange and blue accents, light low-saturation palette, tidy symmetric composition, a calm explanatory mood like part of a system architecture page; no noise in post, crisp lines; medium is a modern flat vector schematic, not hand-drawn, not photography, not 3D rendering.

Negative:
photorealistic, 3D isometric render, hand-drawn sketch style, paper texture, drop shadow, glossy icons, gradient mesh, neon colors, thick black outlines, misaligned arrows, crossed connectors, dense clutter, gibberish pseudo-text, brand logo, watermark

## 锚点 4：实拍真证照片（Blue Pill 板）

- 源：`assets/photos/bluepill-stm32f103c8t6.jpg`
- SHA256：`73b1887438eefaf0766bef50dbd3f631d7fd80e1f3ca392cde4c29fabb5c03c7`
- 媒介边界：真实静物产品摄影（俯拍微距），非三维渲染、非插画。
  该图为书内真证照片；丝印文字只作占位，型号与参数以正文和
  数据手册为准，禁止从照片反推。
- 复现锚点：白色无缝背景 + 深蓝绿矩形板身；上下两排黑色排针
  + 白色丝印细字行；左端 Micro-USB、两枚黄色跳线帽；中央 QFP
  芯片与椭圆金属晶振；均匀漫射光、近无影。

### 正向 Prompt

中文：
实拍微距产品照片，白色无缝背景上俯拍一块矩形深蓝色电路板，板面平整，四角略圆，边缘有浅色倒角。画面上边缘与下边缘各有一排等距的黑色双排针座，针座内侧平行排列两行细小的白色丝印文字占位，字符极小且不要求可读。电路板左端边缘是一个银色金属外壳的微型 USB 接口，开口朝左，金属壳边缘有一圈细窄接缝；接口右侧偏上位置是两枚黄色塑料跳线帽，插在竖直的黑色三针排座上。板面中央偏左是一枚方形黑色贴片集成电路，四边密布细密银色鸥翼引脚，芯片顶面有浅浅的激光蚀刻标记；芯片右侧是一枚银白色椭圆金属外壳晶振。板面右端是四枚一组的黑色短排针，左近处有一枚黑色小轻触按键与两枚绿豆大小的发光二极管，另散布若干极小的贴片电阻电容。全部元件焊盘干净、无飞线无灰尘。均匀柔和的漫射光从左上方铺下，几乎无投影，景深覆盖整块板面，色彩以深蓝绿板身为主，辅助白色丝印、黑色塑料与银色金属，少量黄色与红色点缀，饱和真实；画面整洁、克制、像一张元件清单核对用参考照，后期轻微提亮但不磨皮，保留真实细微纹理，媒介为真实静物产品摄影，非三维渲染非插画。

English:
Real macro product photograph, top-down view of a rectangular deep blue-green circuit board on a plain continuous white background, flat surface with slightly rounded corners and a pale chamfer along the edge. A row of evenly spaced black double-row pin headers runs along the top edge and another along the bottom edge, with two parallel rows of tiny white silkscreen text placeholders just inside each header, characters minute and not required to be legible. At the left edge sits a micro-USB connector in a silver metal shell opening leftward with a thin seam line around the shell; up and to its right, two yellow plastic jumper caps sit on a vertical black three-pin header. Slightly left of the board's center is a square black surface-mount integrated circuit with dense fine silver gull-wing leads on all four sides and faint laser-etched markings on top; to its right is a silver-white oval metal-can crystal. At the right edge, a short black four-pin header; nearby, a small black tactile push button, two pea-sized LEDs and assorted tiny chip resistors and capacitors. All pads are clean, no jumper wires, no dust. Soft even diffused light falls from the upper left with almost no shadow, depth of field covering the whole board; the palette is dominated by the deep blue-green board with white silkscreen, black plastic and silver metal, small yellow and red accents, truthful saturation; the frame is tidy and restrained like a reference shot for checking a parts list, lightly brightened in post but not smoothed, retaining true fine texture; medium is real still-life product photography, not 3D rendering and not illustration.

Negative:
3D render, CGI, illustration, cartoon, stylized, dramatic shadows, strong specular highlights, warm color cast, shallow portrait blur, fingerprints, dust specks, scratches, tangled jumper wires, readable brand text, watermark

## 锚点 5：视频课件帧（ch16 低功耗，30s 处）

- 源：`.temp/visual-anchors/ch16-frame-30s.jpg`（由
  `assets/video/ch16-lp.mp4` 在 30s 处截帧，命令见上文）
- SHA256：`8e0c10f31e580dea8301fdffb8356256bb984bd58b5539cf40bdbca2e7874e95`
- 媒介边界：平面排版的视频课件帧（16:9 屏幕输出），
  非实拍、非三维渲染，画面自带「程序生成画面 · 不是实拍」口径。
- 复现锚点：深藏青纯色底 + 白色纸张卡片悬浮；琥珀橙大标题
  + 青绿短下划线；卡片内「圆圈对勾 + 虚线弧 + 淡蓝圆角矩形」
  的概念连线图；底部字幕带 + 细青绿进度条。

### 正向 Prompt

中文：
平面排版的横版十六比九视频课件帧，深藏青色纯色背景，无渐变。左上角一行浅灰色小号章节标签占位，右上角一枚青绿色页码数字占位。画面左侧中上部是一行大号琥珀橙色粗体标题占位，标题首词组下方压一条青绿色短横线。画面中央偏右悬浮一张大尺寸白色圆角矩形纸张卡片，卡片带极细浅灰描边，内部为手绘感线条示意图：卡片左半上下各一个空心圆圈，圈内一个对勾，圈下极小的灰色标注；中央一个淡蓝色圆角矩形，矩形内部一条波浪短线与三个小写字母占位，矩形两侧各伸出数条短平行横线；卡片右端一个空心圆圈内对勾；三个圆圈分别以虚线弧线连向中央矩形；卡片内上下边缘各有一条若隐若现的浅灰波浪分隔线，卡片四角有极小灰色角标占位。画面底部是一条覆盖全宽的深色字幕带，带上两行白色大号字幕文字占位，字幕带右上方一行小号浅灰注释占位。画面最底部边缘是一条细长的青绿色进度条。整体正投影平面构图，无阴影无立体透视，光效为零，色彩仅深藏青、白、琥珀橙、青绿与浅灰，对比清晰、留白充分，气质克制、教学化、像一页安静的课件；后期无噪点无锐化，边缘干净，媒介为屏幕排版的课件帧，非实拍非三维渲染。

English:
Flatly composed 16:9 video-lesson frame on a solid dark navy background with no gradient. A pale-grey small chapter label placeholder sits at the top-left; a teal page-number glyph at the top-right. Upper-left of the frame carries a large amber-orange bold title placeholder with a short teal underline beneath its first phrase. Center-right floats a large white rounded-rectangle paper card with a hairline pale-grey border, containing a hand-drawn-feel line diagram: two hollow circles stacked on the card's left, each with a check mark inside and a tiny grey caption below; a pale-blue rounded rectangle at the center holding one wavy short line and three lowercase letter placeholders, with several short parallel horizontal lines protruding from its left and right sides; one more hollow check-mark circle at the card's right end; dashed curved lines connect the three circles to the central rectangle; faint pale-grey wavy divider lines run near the card's top and bottom margins, and tiny grey corner captions sit at the card's four corners. Across the bottom of the frame, a full-width dark subtitle band carries two lines of large white subtitle text placeholders, with one small pale-grey annotation placeholder above its right end. A thin teal progress bar hugs the very bottom edge. Straight-on flat composition, no shadows, no perspective, zero lighting effects; the palette is only dark navy, white, amber orange, teal and pale grey, crisp contrast, ample whitespace, restrained and instructional like a quiet slide page; no noise or sharpening in post, clean edges; medium is a screen-composed lesson frame, not live-action footage and not 3D rendering.

Negative:
live-action footage, photographic film frame, 3D render, camera shake blur, lens flare, gradient background, neon glow, drop shadows, glossy cards, cursive handwriting fonts, dense text paragraphs, gibberish pseudo-text, brand logo, watermark, stretched aspect ratio

## 使用约束（与 §6.4 对齐）

1. 上述提示词是新系列插图的「视觉锚点」，不是事实来源；生图结果不得
   充当实拍、实测或数据证据（与 `b50-hardware-evidence.md` 同口径）。
2. 新系列生成前先对照本文件 3–5 个锚点校色、校线宽、校留白；
   生成后仍须走 `slop_lint.py` 与人工目检。
3. 文字区域一律先当占位，最终文字以源文件/生成脚本为准；
   不让生图模型拼写正文。
