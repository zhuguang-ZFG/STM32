# cover 生成提示

cover 封面氛围：白纸底黑线涂鸦（胶片条、画笔、箭头、星形）围绕中央留白，纯图形无文字。

风格：白纸（#FFFFFF）黑线（#26221E）手绘涂鸦信息图；全图唯一橙色焦点 #F08900；箭头仅用红 #C6432F / 蓝 #2A5FA8；纯图形无文字，一切文字与数字由视频文字层承担；线条带手绘抖动，无填充渐变、无阴影堆叠。

建造方式：tools/make_art.py 以 zlib.crc32 种子确定性生成 SVG，svg2png.mjs 出 1080×1920 PNG；parts 边界见 inputs/images/parts.json 与 design/drawing-plan.json。
