#!/bin/bash
# 把一条 B站横版 master 填到"可以点投稿"的状态，全程不点「立即投稿」。
# 用法：sh video/publish/bili-prepare.sh <ep> [起始步]     起始步默认 open
# 每一步都是独立进程重连常驻浏览器（9223），中途挂了从那一步单独重跑就行。
# 创作声明固定「内容无需标注」：这一格发布后锁死，编辑页是 disabled，只能投稿前定。
# 分区那一格不碰：它写的是 human_type 不是 tid，tid 投稿后走 API 补（c2/c4 实测落地）。
set -e
cd /d/Users/mcu
EP=$1
FROM=${2:-open}
[ -n "$EP" ] || { echo "用法：sh video/publish/bili-prepare.sh <ep> [起始步]"; exit 1; }
STEPS="open feed wait fill tagsync cover setmore check descdiff"
run=0
for s in $STEPS; do
  [ "$s" = "$FROM" ] && run=1
  [ "$run" = 1 ] || continue
  echo "########## $EP / $s ##########"
  case $s in
    fill)    node video/publish/bili-web.mjs fill --ep=$EP --decl=内容无需标注 ;;
    cover)   node video/publish/bili-web.mjs cover --ep=$EP --commit ;;
    *)       node video/publish/bili-web.mjs "$s" --ep=$EP ;;
  esac
done
echo "########## $EP 填完，等点「立即投稿」 ##########"
