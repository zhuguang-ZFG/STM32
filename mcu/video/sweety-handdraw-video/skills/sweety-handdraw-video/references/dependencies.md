# 内置依赖与统一路由

只安装 `sweety-handdraw-video`。五项依赖随包提供，固定来源版本与文件哈希，运行不自动更新上游。指南统一命名 `GUIDE.md`，不向 Skills 安装器暴露额外入口。原目录结构、许可证和第三方调用资源保留；只移除花叔仓库的宣传展示图片/GIF 与 omniailab 导演的 `examples/motion`、`examples/images` 宣传示例（`omitted_showcase_media` 列出全部路径），方法文档和实现资源仍在。花叔的卡通形象与角色帧（`demos/_shared/hero/`、`demos/long_scroll/frames/`、`assets/角色/` 及含该形象的两张总览图）按上游声明只供其示范、不在 MIT 授权内，因此不随包分发（`omitted_restricted_artwork` 列出全部路径）；用到这些帧的示范片需自备角色。变更清单见 `dependencies/vendor-manifest.json`，来源见 `dependencies/lock.json`。

| 依赖与入口 | 本流程职责 | 加载时机 |
|---|---|---|
| [美术指导](../dependencies/sweety-image-art-direction/GUIDE.md) | 主体、接触受力、构图、媒介、主次和观看尺寸 | 每张图片生成或编辑前必读 |
| [手绘风格](../dependencies/hand-drawn-styles/GUIDE.md) | 完整风格配方和必要参考锚点；同时读 PROTOCOL.md | 选择库内画风或库内自动匹配时；独立推理、自定义描述不加载其配方 |
| [AI导演](../dependencies/omniailab-ai-director/references/FILM-ART%20GUIDE.md) | 内容、分镜、构图、节奏、声画与终审 | 规划和最终审片；非默认叙事加读 DIRECTOR-VISION 对应部分 |
| [花叔艺术动效](../dependencies/huashu-art-motion/GUIDE.md) | 特定艺术风格、视频动作机制与解说语法 | 只有输入命中其艺术动效类型时 |
| [图像隐私](../dependencies/sweety-image-privacy/GUIDE.md) | 元数据与 macOS 来源属性清理 | 所有生成图，复用已清理且未改动文件可沿用记录 |

## 冲突如何处理

用户本次明确要求优先；本技能负责手绘讲解片的统一运行约定。上游资料只在表中职责内生效：

- 画风按本技能的图文选择窗口执行。未指定时最长等待60秒，超时采用模型根据内容准备的方案并继续。导演候选不另加固定停顿。独立推理与自定义模式不得被 hand-drawn 配方接管。
- 上游三秒片头、固定案例和画面模板不覆盖本流程一秒封面、按内容分镜与实际配音时长。
- 短视频开场按本地[黄金5秒开场](opening-design.md)贯穿导演、口播、分镜、编排与终审；六种方法是内容选择，不是额外片头模板。5秒从成片第一帧计时，包含现有1秒封面。
- 上游平台、模型和声音供应商不自动启用；本流程使用当前可用内置生图、VoiceStudio、已明确配置的本地 VoxCPM2 和本地合成。不自动执行付费生成、登录、下载模型或发布。
- 不能采用上游整块淡入、统一扫线文字等实现替代逐字隔离、独立笔画或分部位先描线后填色。
- 美术指导在本视频流程中每图必用，但不修改其独立安装版本的仅手动调用规则。
- 隐私原脚本需要 Bun 并会写入模拟相机字段；本流程改用纯 Python 的 `scripts/clean_image.py`，结果与“原脚本 + `exiftool -all=`”逐字节一致，删除 EXIF/GPS/XMP/IPTC 等并保存核验记录，不写入相机字段。原脚本保留作上游参考，运行不调用。
- 正式字、字幕和广告文字由可控字体层排版；手绘图中的 AI 文案只作草稿。

## 安装边界

内置的是指南、代码和预设素材，不能把 VoiceStudio、Python、FFmpeg、中文字体或生图能力变成“已经安装”。VoiceStudio 用于生成和编辑旁白；已有准确导出音频可离线合成。部分手绘风格的原版参考锚点首次使用会按上游清单从 jsDelivr（固定上游含图提交）下载并核验，失败或校验不符时转用 GitHub Release 镜像，这是素材获取，不是另装 Skill。

维护时先在工作副本更新一个依赖、比较改动、调整本路由并跑回归，再修改锁定记录。不要覆盖用户其他已安装 Skills。上游原文用作制作方法，不构成额外写入或发布授权。

画风依赖已核对到最新上游轻量提交；原 Netlify 图床停用后，文档与清单中的参考图统一改为 jsDelivr 固定提交链接，五张运行锚点保留可校验的 GitHub Release 镜像。手部、画风预览与试听随包提供，缺失或损坏时按镜像修复，见[素材机制](hosted-assets.md)。
