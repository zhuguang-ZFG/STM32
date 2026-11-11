#!/usr/bin/env bash
# 15 条横版的排队投稿。为什么不是"立刻重跑批量"：
#   biliup 的 upload 是"先把整条成片传完，再调投稿接口"，21566 出在最后一步——
#   每次重试都白传 38~48 MB，而且重试本身会把"投稿过于频繁"喂得更死。
# 所以这里只做两件事：先隔够久探一次，判明 21566 是滚动窗口还是当日上限；
#   滚动窗口 → 按 GAP 一条条发完；连续 PROBE_MAX 次仍 21566 → 整批停手，等人决定。
# 非 21566 的失败（分区、标题、封面、核对没过）一律立刻停——那类错误等多久都不会自己好。
set -u
cd /d/Users/mcu
LOG=.temp/bili-queue.log
EPISODES='c4-struct-abi c5-func-pointer c6-abi-stack c7-ub f2-context-switch f0-why-rtos s16-hardfault s2-rcc s14-pwr p4-iram s4-nvic c2-pointer f3-scheduler s7-usart-baud f6-timers'
# 走 biliup 的默认 submit 通道（client）——c3 20:46:37 就是从这条通道成功发出的，
# 这是本机唯一有既往成功证据的一条；app 通道和它一样撞 21566，不多一个变量。
FIRST_WAIT=${FIRST_WAIT:-3600}   # 第一次探测前等多久（秒），默认 60 分钟（距上次 21566 再退一小时）
GAP=${GAP:-1800}                 # 成功一条之后隔多久发下一条：15 条约 7.5 小时，整批过夜
PROBE_MAX=${PROBE_MAX:-4}        # 连探几次仍是 21566 就认输
note() { echo "[$(date +%F' '%T)] $*" | tee -a "$LOG"; }

note "队列启动：15 条，首探前等 ${FIRST_WAIT}s，条间 ${GAP}s，连探上限 ${PROBE_MAX}"
sleep "$FIRST_WAIT"

probes=0
for EP in $EPISODES; do
  while :; do
    note "▸ $EP 投稿中（累计探测 $probes/$PROBE_MAX）"
    I_HAVE_USER_OK=$EP sh video/publish/bili-upload.sh "$EP" >>"$LOG" 2>&1
    RC=$?
    [ "$RC" = 0 ] && { note "✅ $EP 已确认投稿：$(grep -aoE 'BV[0-9A-Za-z]{10}' .temp/bili-submit-out/$EP.txt | head -1)"; probes=0; sleep "$GAP"; break; }
    OUT=.temp/bili-submit-out/$EP.txt
    if grep -qa '21566' "$OUT" 2>/dev/null; then
      probes=$((probes+1))
      if [ "$probes" -ge "$PROBE_MAX" ]; then
        note "‼️ 连探 $probes 次仍是 21566 投稿过于频繁——不像滚动窗口，更像账号当日/长期上限。整批停手，等人决定。"
        exit 1
      fi
      note "… $EP 撞 21566（第 $probes 次），等 $((GAP*2))s 再探"
      sleep $((GAP*2))
      continue
    fi
    note "‼️ $EP 失败但不是 21566（exit=$RC），末 6 行："
    tail -6 "$OUT" 2>/dev/null | tee -a "$LOG"
    exit 1
  done
done
note "@@@@@@ 15 条全部确认投稿成功 @@@@@@"
