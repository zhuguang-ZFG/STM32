# 画风选择与可绘制约定

## 风格选择（文字列表，默认模型推理）

每个新任务先确定画风路径。默认 **模型推理**（`inferred`）：按主题与内容独立推理线条、色板、明暗、材质、背景；风格目录只是软参考，**不约束模型**。

主动选择时用宿主原生选项或终端数字菜单展示文字列表（**不展示效果图**）：

0. **模型推理（默认）** — `inferred`
1…N. 目录中的风格编号 — `catalog`（软选项）
N+1. **自定义描述** — `custom`

仍支持 `catalog_auto`（模型从目录匹配）以兼容旧任务。不使用 HTML 预览墙作为主路径。

```bash
python3 scripts/style_choice.py prepare JOB --catalog-source /path/to/hand-drawn
python3 scripts/production_options.py JOB --defaults JOB/options/defaults.json
```

**模型推理审美自由，绘制物理不自由。** 目录与编号是软参考。推理结果若无法形成干净连续墨线+平涂，应投影到可绘制的执行面（`drawing_mode: draw`），或取得用户对 reveal 的明确同意（`reveal_accepted`）。模型推理路径不得自行改用 reveal。若选目录中的纯黑白 1 号，写 `monochrome_reason`。

用户明确指出某个安装路径时，以该路径的实际目录为准；不要混进另一个版本的编号。否则默认使用本包固定依赖。目录从 `STYLES.md` 动态提取，不手写固定数量；快照保存完整配方和哈希。目录以文字名称为准；预览图可选生成但不进入选择 UI。更换目录来源需要重新准备快照。

选择过程只写本任务目录，不自动生图或发布。

## 风格决策文件

`style/selection.json` 由原生选项流程或模型写入。用户在聊天中明确选择/委托时可手工记录，`confirmation` 用 `explicit_user_request` 或 `user_delegated`；等待结束后用 `timeout_default`，说明实际等待时间和模型默认方案，不制造用户确认记录。用户说“你来选”“全部自动”时，由模型选出的画风一律记为 `user_delegated`，不能写成 `explicit_user_request`。

```json
{"mode":"inferred","confirmation":"explicit_user_request","evidence":"用户明确选择不选择列表中的，模型推理产出"}
```

模型随后写 `style/resolved.json`：

```json
{
  "status":"resolved",
  "mode":"inferred",
  "selection_sha256":"selection.json 的实际 SHA-256",
  "style_name":"本片实际画风名称",
  "rationale":"为什么采用此画法",
  "content_fit":"与本片具体内容的对应关系",
  "style_spec":{"line":"可分辨的独立轮廓","palette":"具体配色","shading":"具体明暗","texture":"具体质感","background":"背景处理"},
  "drawing_mode":"draw"
}
```

库内两模式还须 `catalog_id` 和快照中的 `recipe_sha256`；库内自动匹配须 `content_fit`；模型代选 1 号须 `monochrome_reason`；`drawing_mode` 为 `reveal` 而不是用户主动选择了揭示时，须 `reveal_accepted`（用户同意的原话）。独立推理禁止这些库内字段。自定义还须 `style_basis`，逐字保留用户描述。先运行 `python3 scripts/style_choice.py verify JOB`。

库内配方的锚点、多阶段生成等既有要求仍然适用。保留所选风格的外观；若当前工具无法兼顾，要在生图前说明具体冲突，不能偷偷换画风。

### 绘制方式：逐笔绘制或揭示

- **逐笔绘制**（`drawing_mode: "draw"`）：只用于有清晰连续墨线、平涂上色的画风。引擎按部位整笔描线、再用马克笔上色，受线稿门槛和 `minimum_seconds` 约束。随包画风中 1、4、5、17、19、20 属于此类。
- **揭示**（`drawing_mode: "reveal"`）：水彩、水粉、纸雕、像素、水墨、蜡笔、厚涂、3D 等没有墨线轮廓的画风。手带宽软笔刷按部位斜向扫过，画面只在刷过处显出成图；不做线稿提取，也不受线稿门槛约束，整幅最短约2.5–3.6秒（实测2–7个部位的插画），远短于逐笔绘制。不要为这类画风硬造轮廓层。它放弃了逐笔绘制：观众看到的是成图被刷出来，不是被画出来。

库内画风的绘制方式由目录固定（`style/catalog.json` 的 `drawing_mode`，文字列表里会标明）；独立推理和自定义画风在 `resolved.json` 写明 `drawing_mode`。`job.json` 写 `"drawing": {"mode": "reveal"}`（默认 `draw`）与之保持一致，构建会核对。逐笔绘制的片子里，单张插画不能改用 `reveal`，构建会拒绝；画不出来就简化或重新生成那张图。

**揭示只由用户选。** 用户在主动选择里明确点了揭示风格，或书面同意后写入 reveal_accepted，就是知情选择。其他路径（自动匹配、超时默认、用户说“你来选”、独立推理、自定义描述）得出 `reveal` 时，`style_choice.py verify` 会拒绝，除非先告诉用户“这个画风只能刷出、不能画出”，用户同意后把答复写进 `resolved.json` 的 `reveal_accepted`。通常更好的做法是保留观感、改成可画的版本：例如“立体人物＋水墨环境”画成干净墨线轮廓＋平涂，用少量灰蓝色块和留白表现水墨气氛，`drawing_mode` 仍为 `draw`。

## 出图前的可绘制计划

每次调用图像生成或编辑前，先写计划并运行：

```bash
python3 scripts/drawing_contract.py JOB JOB/design/drawing-plan.json
```

输入含 `illustrations` 数组，每项有唯一 `id`，并包含：

- `composition`：实际主体、动作、遮挡和留白安排。
- `drawability_reason`：为什么这些部分能独立描线和上色，线条复杂度是否适合口播时长。
- `outline_strategy`：`visible_source_ink` 或 `explicit_mask`；后者在 action 提供同尺寸的灰度 `outline_mask`，白色为轮廓、黑色为填色。
- `subjects`：每个对象的 `id` 与 `kind`（human/animal/object/environment）。人物须覆盖 `head / neck / torso / left_arm / right_arm / lower_body`；不可见部分放入 `omitted_roles` 并说明裁切或遮挡，不能借此略过实际可见部位。左右指画面左右；不同观察角度保持解释一致。
- `parts`：按实际绘制顺序，每项写 `id / subject / role / stroke_groups`。`stroke_groups` 是独立笔画的简述数组，例如头部的外形弧线、左眼、右眼、鼻、嘴；不能一句“整个头连续画完”替代。
- `outline_order`、`fill_order`：均为同一有序 part id 数组。
- `spatial_order`：通常 `top_to_bottom_left_to_right`；构图/遮挡例外记录 `order_exception`。人物默认头、脖子、躯干、左臂、右臂、下半身，非默认在该 subject 写 `order_exception`。

校验通过生成同名 `.preflight.json`，绑定风格和计划哈希。计划改变后须重新预检；若图已生成，先重新评估受影响部分，不能把新计划伪称为旧图的出图前证据。

## 成图后的核对与执行

实际看图后，为 action 写 `drawing_plan_id`、按计划同顺序的 `parts` 多边形及必要排除区域，所有可见像素只能归属一个部位。多边形随实际解剖与遮挡，不用从上到下的等高横条代替语义部位。

线稿闭合良好时，可改用编号区域：运行 `region_marks.py`，看叠图把编号分配给部位（`region_map` + `part_regions`，见[运行约定](runtime-contract.md)），比手写多边形更准。

### 出图要求（让图真能被一笔一笔画出来）

引擎会用 `lineart_gate.py` 拒绝纹理型线稿，并按真实笔画计算 `minimum_seconds`。出图提示与编辑时：

- 连续、干净、粗细稳定的墨线轮廓；不要排线、交叉阴影、布纹/毛发/树皮纹理线和边缘检测感的碎线。
- 部位交界处把轮廓闭合（叶基、衣摆、袖口、领口画出完整分界线），区域才能分开编号。
- 平涂色块加柔和明暗；明暗不要用线条表达。
- 控制线条数量：按约每秒5笔估算（draw-v3 实测，与图幅大小基本无关），45—50笔的单一主体全部描线加上色最短约8—10秒（`minimum_seconds`）；口播窗口更短就简化画面或用 `visual_groups` 跨句延长窗口。引擎不淡入任何线条或色块，每一笔、每块颜色都由笔尖画出；窗口不够只会报错，不会偷偷省笔。

`job.json` 指定 `drawing_plan` 和 `drawing_review`。使用 `outline_mask` 时，审核中还须 `outline_mask_sha256`，且遮罩尺寸必须与裁切前的完整原图一致。后者结构：

```json
{"style_sha256":"resolved.json 的实际哈希","plan_sha256":"实际计划哈希","illustrations":[{
  "plan_id":"figure-01","status":"pass","source_sha256":"实际图像哈希","crop":null,
  "anatomy_and_occlusion":"看到了什么、哪些部位被遮挡",
  "part_boundaries":"各区域如何对应实际部位",
  "stroke_breaks":"哪里起笔、转折、收笔与抬笔",
  "outline_then_fill":"轮廓是否齐全且可独立追踪",
  "spatial_order":"确认部位顺序或说明构图例外"
}]}
```

`art_direction.record` 的顶层也须写入相同 `style_sha256`，绑定封面和生成素材到本次画风。换画风后不得沿用旧的图片审核。

所有插画整幅轮廓完成后才能填色，两阶段按同一部位顺序。黑白线稿可以没有填色阶段，但不可反过来省略轮廓。笔画只能沿连续像素前进，断开的笔画必须抬笔，不能用最近点跳连；颜色只在笔刷经过范围出现。短到看不出起落、画面必须疯狂跳笔才能赶上口播时，减少非必要线条或重新分镜，不能靠缩短抬笔假装自然。

### 拟人绘制步骤（引擎）

引擎按人类习惯执行，而不是匀速显影：

1. 按语义部位：轮廓 → 主结构 → 细节；部位切换有短暂停顿。
2. 线：压力起收笔、拐弯降速、抬笔快甩；每笔都由笔尖走过源图墨线像素。
3. 色（2.0）：上色跟着画面自己的闭合区域走，不按部位多边形切块。模型画的部位框只用来给笔画分组。每块颜色先沿区域内侧描一圈边，再用斜向排笔填满：长条形横跨着画，圆形用右手自然的斜度。接近的几笔连成一笔不抬笔，漏掉的角落最后补涂。刚涂上的颜色是带毡头纹理的半透明湿笔触，下一笔覆盖上来或稍后变实，所以不会整块显现。窗口很紧时才退回最宽的马克笔，用长行快涂，不描边。部位之间短暂停顿。
4. 时间预算在分镜/出图前用 presentation.mode 卡住；窗口不够就简化图，不淡入、不改 reveal。

出图时尽量提供可分离的 line 层与平涂 fill（干净墨线、部位交界闭合）；`stroke_groups` 写清独立笔画，便于引擎与门禁对齐。

构建、渲染、验证会拒绝缺少风格/计划/审核的生产任务，并校验实际路径。检查不能自动证明模型标对了人体或遵守了画风；代表段必须实际检查轮廓末帧、填色起始、关键部位切换和连续动作。旧任务没有这些证据时需按真实来源重新评估，不批量补写“通过”。运行测试 fixture 仅用于工程回归，禁止最终交付。
