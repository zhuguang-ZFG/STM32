#!/bin/sh
set -eu
cd "$(dirname "$0")"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
CC=${CC:-gcc}
echo "== host gcc =="
$CC --version | head -1
$CC -std=c11 -Wall -Wextra -O2 -S opt_probe.c -o "$TMP/opt_probe.s"
for fn in poll_plain poll_volatile delay_plain delay_volatile cfg_plain cfg_volatile isr_toggle; do
  echo "-- $fn --"
  awk -v fn="$fn:" '
    index($0, fn) == 1 { inf = 1 }
    inf { print }
    inf && (/\.seh_endproc/ || /^[[:space:]]*\.size/) { exit }
  ' "$TMP/opt_probe.s" | head -20
done
$CC -std=c11 -Wall -Wextra -O2 opt_probe.c -o "$TMP/opt_probe"
"$TMP/opt_probe"
echo "== arm cross (optional) =="
if command -v arm-none-eabi-gcc >/dev/null 2>&1 && command -v arm-none-eabi-objdump >/dev/null 2>&1; then
  sh blink-variants.sh
else
  echo "~arm-none-eabi-gcc/objdump 不在 PATH，交叉段不跑"
fi
