#!/bin/sh
# 小红书批量上传：对每一集按固定顺序跑完七个表单步 + 挂合集 + 发布（--go 才点发布，闸门逐集检查）。
# 用法：sh video/publish/xhs-batch.sh <ep> [<ep> ...]
# 前置：xhs-daemon 起着（9223）；每集的 episode.json 有 publish.xiaohongshu；每集有 .temp/xhs-run/I_HAVE_USER_OK=<ep>
# 纪律：任一步非零立即停（不把"看起来成功"当成功）；发布是逐集闸门的不可逆动作。
set -e
DIR=$(dirname "$0")
for ep in "$@"; do
  echo "================ $ep ================"
  node "$DIR/xhs-step.mjs" open       --ep="$ep"
  node "$DIR/xhs-step.mjs" upload     --ep="$ep"
  node "$DIR/xhs-step.mjs" fill       --ep="$ep"
  node "$DIR/xhs-step.mjs" topics     --ep="$ep"
  node "$DIR/xhs-step.mjs" coverset   --ep="$ep"
  node "$DIR/xhs-step.mjs" coverapply --ep="$ep"
  node "$DIR/xhs-step.mjs" attach     --ep="$ep"
  node "$DIR/xhs-step.mjs" publish    --ep="$ep" --go
  echo "---- $ep 完成 ----"
done
echo "全部完成：$#"
