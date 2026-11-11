#!/usr/bin/env bash
# 一条 B站横版 master 走完全程：填到可投稿 → 点「立即投稿」→ 投稿后用 API 补字段。
# 用法：sh video/publish/bili-one.sh <ep>
# 前提：.temp/bili-web-run/I_HAVE_USER_OK=<ep> 存在，内容是对话里用户对这一条的点头——脚本不自己造。
# 为什么连点按钮也交给脚本：API 通道投稿仍然撞 21566，浏览器是唯一发得出去的路；
# 而剩下十几条靠人手点，标签页被人关掉过一次（c5），点错页就是给上一条稿件填下一条的字。
# 任何一步失败就停在那儿，绝不带着半填的表单往下走：publish 之前有锁定项核对，publish 之后才 repair。
set -e
cd /d/Users/mcu
EP=${1:?用法：sh video/publish/bili-one.sh <ep>}
GATE=.temp/bili-web-run/I_HAVE_USER_OK=$EP
[ -f "$GATE" ] || { echo "‼️ 缺闸门文件 $GATE（只能来自对话里的点头）"; exit 1; }
LOG=.temp/bili-web-run/$EP-one.log
BV0=$(cat ".temp/bili-web-run/$EP.bvid" 2>/dev/null || true)
if [ -n "$BV0" ] && [ -z "${FORCE_RESUBMIT:-}" ]; then
  echo "‼️ $EP 账上已经有稿件 $BV0（线上就在这儿）。再跑一遍会重传视频、再投一份重复稿。"
  echo "   只想补字段：node video/publish/bili-cover-edit.mjs repair $BV0 video/out/$EP/bili-submit.yaml"
  echo "   确实要再投一条，自己确认后再 FORCE_RESUBMIT=1 sh video/publish/bili-one.sh $EP"
  exit 1
fi
echo "▶ $EP 填表（open→feed→wait→fill→tagsync→cover→setmore→check→descdiff）"
sh video/publish/bili-prepare.sh "$EP" open > "$LOG" 2>&1
echo "▶ $EP 点「立即投稿」（退出码不参与判定，见下）"
# 这一句不能带 set -e 的"非零即中止"：s2-rcc 那次 add/v3 已经 code=0、BV 号也落了盘，
# 崩的是后面 repair 的一条 API 调用被代理掐断。脚本退出码非零 ≠ 没投出去，
# 拿 .bvid 文件判真假：有稿就去补字段，没有才停手。硬要重试投稿才会生出重复稿。
set +e
node video/publish/bili-web.mjs publish --ep=$EP --decl=内容无需标注 >> "$LOG" 2>&1
PUBRC=$?
set -e
BV=$(cat ".temp/bili-web-run/$EP.bvid" 2>/dev/null || true)
[ -n "$BV" ] || { echo "‼️ 投稿后没拿到 BV 号（publish 退出码 $PUBRC），停手不 repair（见 $LOG）"; exit 1; }
[ "$PUBRC" = 0 ] || echo "  ⚠ publish 退出码 $PUBRC，但已拿到 $BV——按已投稿处理，只补字段，不重投"
echo "▶ $BV 补字段（tid/copyright/标签/封面/cover43）"
node video/publish/bili-cover-edit.mjs repair "$BV" "video/out/$EP/bili-submit.yaml" >> "$LOG" 2>&1
OK=$(grep -c '✓' "$LOG" || true)
ST=$(grep -oE '状态 -?[0-9]+' "$LOG" | tail -1)
echo "✅ $EP $BV ｜回读核对 $OK 项 ✓｜$ST｜日志 $LOG"
