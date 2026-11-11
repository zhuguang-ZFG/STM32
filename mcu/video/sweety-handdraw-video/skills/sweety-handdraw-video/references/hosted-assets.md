# 托管素材与安装体积

v1.3 起，运行预设重新随包提供：7 张手部 PNG、21 张画风预览、2 段逼真声音试听 WAV，共 30 个文件，均为原始字节。装好即可离线使用；画风选择器直接读包内预览，不访问网络。原片女声录音、提取的人声、用户个人音色目录不公开。

`assets/hosted-manifest.json` 为每个文件固定字节数、SHA-256 和有序镜像 `urls`（jsDelivr CDN → jsDelivr Fastly → GitHub Release）。`validate_package.py` 逐个核对包内副本与清单一致，并限制安装包总量 ≤50 MB、单文件 ≤10 MB。

## 读取顺序

1. 包内副本，大小与 SHA-256 一致即使用。
2. 缓存 `~/.cache/sweety-handdraw-video/<sha256>/<文件名>`（`HANDDRAW_ASSET_CACHE` 可改），同样校验。
3. 两者都缺失或损坏时才联网修复：先试 `HANDDRAW_MIRROR`（https:// 或 file:// 前缀，目录结构与包相同，例如 Gitee 镜像），再按清单顺序逐个尝试，每个地址 15 秒超时。只有大小和 SHA-256 一致的内容才写入缓存；不会退回另一张图或另一种声音。
4. 全部失败时报错列出每个地址及其错误，以及应手动保存到的缓存路径。`HANDDRAW_OFFLINE=1` 跳过联网，直接说明缺失文件和可放置的两个路径。

```bash
python scripts/hosted_assets.py --all
HANDDRAW_MIRROR=https://gitee.com/<owner>/<repo>/raw/<tag>/skills/sweety-handdraw-video python scripts/hosted_assets.py assets/hands/pen-only.png
```

jsDelivr 地址固定到 `@v1.3` 标签，推送该标签后才可用；发布的标签不同则需同步替换清单中的 `@v1.3`。Release 地址沿用 v1.2 / v1.2.3 已发布附件，作为最后一级回退。

## 画风库参考图

画风配方文本沿用上游 `hand-drawn-styles` 轻量提交 `4132988b8596bfa36321c970a4472d4e3bb25d96`。原 Netlify 图床因额度耗尽返回 503，参考图链接（文档中的全部图片链接与 `assets/image-manifest.json`）改为 jsDelivr 固定上游含图提交 `cdfd004c89164096c861ad06ebab2aa1527d1710`。五张运行参考锚点另有 GitHub Release `fallback_url`；其中三张清理了来源与模拟相机字段，逐像素一致，jsDelivr 返回上游原字节时校验不符，会转用 Release 清理版。清单保留上游字节校验值以便追溯。

## README 展示素材

README 的封面、手部总览与动态节选（GIF 转为 animated WebP）放在仓库 `docs/media/`，画风预览与试听直接引用包内文件，均为相对路径，不依赖 Release 下载。完整 1080p 成片仍是 Release 下载附件（只能下载，不能在页面内播放）；可在线播放的 720p 版本需作者通过 GitHub 编辑器上传为 user-attachments。清单见仓库 `docs/media-manifest.json`。

## 安装体积

随包恢复的 30 个预设共约 8.8 MB；同时按 `omitted_showcase_media` 机制移除 omniailab 导演依赖中的 `examples/motion` 与 `examples/images` 宣传示例（533 个文件），方法文档与运行代码保留。减小当前代码包不等于清理 Git 历史；没有改写历史提交。
