#!/usr/bin/env bash
# 单条 B站投稿。三道闸门，顺序不能换：
#   ① 这条 master 必须先过七项核对（.temp/clip-wave-verify.mjs），像素/时长/字幕/音轨有问题就不许传；
#   ② 必须存在与成片哈希匹配的"已核对"凭证，防止拿一个改过的文件冒充刚验过的那条；
#   ③ 必须显式给出用户批准标记 I_HAVE_USER_OK=<ep>，值不等于集号就中止——这个标记只能来自对话里的点头。
# 用法：I_HAVE_USER_OK=c3-volatile sh video/publish/bili-upload.sh c3-volatile
set -eu
cd /d/Users/mcu
BILIDIR=/c/Users/zhugu/tools/biliup-rs/biliupR-v0.2.4-x86_64-windows
BILI=$BILIDIR/biliup.exe
# cookies.json 落在**执行 login 时的工作目录**——上面几个位置都可能，哪个存在用哪个，
# 别硬写一条路径然后对着另一份凭证喊"没有登录"。
COOKIE=''
for c in "$BILIDIR/cookies.json" /c/Users/zhugu/tools/biliup-rs/cookies.json /d/Users/mcu/cookies.json; do
  [ -f "$c" ] && { COOKIE=$c; break; }
done
EP=${1:?用法：sh video/publish/bili-upload.sh <episode-id>}
CFG=video/out/$EP/bili-submit.yaml
MP4=video/out/$EP/bilibili.mp4

[ -n "$COOKIE" ] || { echo "‼️ 没有 cookies.json——请先在本机执行 biliup.exe login 扫码登录（凭证不进对话）。"; exit 1; }
echo "   凭证：$COOKIE"
[ "${I_HAVE_USER_OK:-}" = "$EP" ] || { echo "‼️ 缺用户批准标记。应为：I_HAVE_USER_OK=$EP sh video/publish/bili-upload.sh $EP"; exit 1; }
[ -f "$CFG" ] || { echo "‼️ 缺投稿配置 $CFG（先跑 node video/publish/bili-submit.mjs --tid=<分区号>）"; exit 1; }

echo "═══ ① 七项核对：$EP/bilibili ═══"
node .temp/clip-wave-verify.mjs "$EP:bilibili"

SHA=$(sha256sum "$MP4" | cut -d' ' -f1)
PROOF=.temp/verified/$EP-bilibili.$SHA
if [ ! -f "$PROOF" ]; then
  mkdir -p .temp/verified
  # 原来这里只 echo 了一句"已建凭证"却没真写文件，于是第二次跑照样被拦——话说了事没做。
  printf 'verified_at %s\nsha256 %s\nbytes %s\nmp4_mtime %s\nstage1 七项核对 exit=0\n' \
    "$(date -Iseconds)" "$SHA" "$(stat -c %s "$MP4")" "$(stat -c %y "$MP4" | cut -c1-19)" > "$PROOF"
  echo "‼️ 刚核对完的这条成片哈希（$SHA）没有既往凭证，已建 $PROOF；"
  echo "    请确认上面七项核对全绿后**再跑一次**，第二次才会放行。"
  exit 1
fi
echo "═══ ② 哈希凭证对上：$SHA ═══"

echo "═══ 即将提交的稿件（事实源，逐字）═══"
cat "$CFG"
echo "═══ 提交 ═══"
cd "$BILIDIR"
# 日志级别必须压到 error：默认的 tower_http=debug,info 会把整条 LoginInfo（SESSDATA/access_token/
# refresh_token/bili_jct）打进输出，一旦 tee 进 .temp/bili-upload.log 就等于把凭证写进仓库目录。
# 再加一层 grep 兜底——就算某个错误分支自己打印了 cookie，也只留结构、不留值。
redact() { grep -viE 'SESSDATA|access_token|refresh_token|bili_jct|LoginInfo|cookie_info|token_info|"value"|DedeUserID' || true; }
OUT=.temp/bili-submit-out/$EP.txt
RAW=/d/Temp/User/bili-$EP.raw   # 原件放仓库外：万一某分支自己打了 cookie，不落进 .temp
mkdir -p /d/Users/mcu/.temp/bili-submit-out
# 退出码必须自己接住：`biliup | redact | tee` 这条管道的 $? 是 tee 的，
# 上一版就是被它骗过——21566 投稿失败照样往下走，把失败当成功排队。
# 但 set -e 会让"非零退出的那条命令"直接终止脚本，RC=$? 永远读不到，
# 于是失败连原因都印不出来（21:33 那次就是这样静消失效的）——用 if 接住才两头都对。
if "$BILI" --rust-log=error upload ${SUBMIT:+--submit "$SUBMIT"} -c "/d/Users/mcu/$CFG" > "$RAW" 2>&1; then RC=0; else RC=$?; fi
redact < "$RAW" > "/d/Users/mcu/$OUT"
rm -f "$RAW"
cat "/d/Users/mcu/$OUT"
echo "@@@@ $EP 提交返回 $(date +%H:%M:%S) exit=$RC，完整输出见 .temp/bili-submit-out/$EP.txt" >> /d/Users/mcu/.temp/bili-upload.log
# 成功判据是"看到 bvid"，不是"没报错"：biliup 成功时打印 BV 号，失败时打印 Error: ResponseData。
BVID=$(grep -aoE 'BV[0-9A-Za-z]{10}' "/d/Users/mcu/$OUT" | head -1)
if [ "$RC" != 0 ] || [ -z "$BVID" ] || grep -q 'Error:' "/d/Users/mcu/$OUT"; then
  echo "‼️ $EP 未确认投稿成功（exit=$RC，bvid=${BVID:-无}）：$(grep -aoE 'code: [0-9]+, .*message: \"[^\"]*\"' "/d/Users/mcu/$OUT" | head -1)"
  exit 1
fi
echo "✅ $EP 投稿成功 $BVID"
echo "$BVID $EP $(date -Iseconds)" >> /d/Users/mcu/.temp/bili-submitted.txt
