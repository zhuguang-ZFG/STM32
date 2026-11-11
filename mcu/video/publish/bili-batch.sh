#!/usr/bin/env bash
# 把剩下的 B站横版 master 一条条走完：一条成功才走下一条，任何一条停手就把批次停在这里。
# 用法：sh video/publish/bili-batch.sh <ep...>
# 为什么串行而不是并行：网页通道一个标签页就是一份表单，两条一起填必然互相盖字；
# 而投稿是对外可见、不可逆的动作，"错一条"的代价比"慢一点"大得多。
cd /d/Users/mcu
BLOG=.temp/bili-web-run/batch.log
for EP in "$@"; do
  echo "@@@@ $EP 开始 $(date +%H:%M:%S)" >> "$BLOG"
  if sh video/publish/bili-one.sh "$EP" >> "$BLOG" 2>&1; then
    echo "@@@@ $EP 完成 $(date +%H:%M:%S) $(cat .temp/bili-web-run/$EP.bvid 2>/dev/null)" >> "$BLOG"
  else
    echo "@@@@ $EP 失败，批次停住 $(date +%H:%M:%S)" >> "$BLOG"
    exit 1
  fi
done
echo "@@@@ 批次全部完成 $(date +%H:%M:%S)" >> "$BLOG"
