#!/usr/bin/env bash
# 本地一键复跑 CI 全部门（与 .github/workflows/quality.yml + book.yml + links.yml 对齐）。
#
# 语义：FAIL 让退出码非零；工具缺失记 SKIP（附安装提示）但**不算失败**——
#       CI 才是真门禁，本脚本只为提交前自查省时。
#
# 为什么逐项跑而不是直接 `npm run quality`：那条链是 && 串联，第一个失败就停，
# 一次只能看到一个待修项；这里把每道门都跑完，一次给全清单。
#
# 用法：bash scripts/local-gates.sh [--only <label>]
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

ONLY=""
if [ "${1:-}" = "--only" ]; then ONLY="${2:-}"; fi

PASS=0
FAIL=0
SKIP=0
LOG="$(mktemp -t local-gates.XXXXXX)"
trap 'rm -f "$LOG"' EXIT

report() { # $1=label $2=PASS|FAIL|SKIP $3=备注
  printf '[%-4s] %s%s\n' "$2" "$1" "${3:+  —— $3}"
  case "$2" in
    PASS) PASS=$((PASS + 1)) ;;
    FAIL) FAIL=$((FAIL + 1)) ;;
    SKIP) SKIP=$((SKIP + 1)) ;;
  esac
}

# 跑一道门：失败时把输出前 40 行打出来（够定位，又不至于刷屏）
gate() { # $1=label $2..=command
  local label="$1"
  shift
  if [ -n "$ONLY" ] && [ "$ONLY" != "$label" ]; then return 0; fi
  local start=$SECONDS
  if "$@" >"$LOG" 2>&1; then
    report "$label" PASS "$((SECONDS - start))s"
  else
    report "$label" FAIL "$((SECONDS - start))s"
    sed -n '1,40p' "$LOG" | sed 's/^/    /'
  fi
}

skip() { # $1=label $2=原因（含安装提示）
  if [ -n "$ONLY" ] && [ "$ONLY" != "$1" ]; then return 0; fi
  report "$1" SKIP "$2"
}

have() { command -v "$1" >/dev/null 2>&1; }

echo "== 本地门禁（与 CI 对齐；FAIL 才算失败，SKIP 是工具不在本机）=="

# ---- 运行时探测 -------------------------------------------------------------
if ! have node; then
  report "node" FAIL "装 Node.js 24 再来"
  echo "共 $PASS pass / $FAIL fail / $SKIP skip"
  exit 1
fi
report "node" PASS "$(node -v)"

PY=""
for c in python3 python; do
  if have "$c"; then PY="$c"; break; fi
done

# ---- 站点与文档门（npm 脚本，与 quality.yml 的 npm run quality 同集合）-----
for s in test projects:check docs:build anim:lint readme:check reading:check \
  links:check docs:check nav:check seo:check perf:budget a11y:check pages:check search:check; do
  gate "$s" npm run --silent "$s"
done

gate "anim:audit" npm run --silent anim:audit

if npx --no-install playwright --version >/dev/null 2>&1; then
  gate "test:browser" npm run --silent test:browser
else
  skip "test:browser" "缺 Playwright：npm i && npx playwright install chromium"
fi

# ---- 固件：ARM 工具链不在本机时只做 SKIP（CI 的 arm-host job 才是真门禁）----
if have arm-none-eabi-gcc; then
  gate "firmware:check" npm run --silent firmware:check
else
  skip "firmware:check" "缺 arm-none-eabi-gcc（Windows 可先跑 scripts/arm-env.sh 配 mingw32-make）"
fi

# ---- 整书：构建 → 契约门 → 打包 ----
gate "book:check" npm run --silent book:check
if [ -n "$PY" ]; then
  gate "book:unittest" "$PY" -m unittest discover mcu-book/tests
  gate "book:pack" "$PY" mcu-book/publish_downloads.py --out-dir .temp/book-downloads
  gate "book:pack-verify" "$PY" mcu-book/publish_downloads.py --verify .temp/book-downloads
  # PDF 契约门要有 PDF 才跑得动；本地重建一次约 8 分钟，故只在产物已存在时跑，缺就 SKIP
  if [ -f mcu-book/dist/mcu-deep-book.pdf ]; then
    gate "book:pdfcheck" "$PY" mcu-book/check_pdf.py
  else
    skip "book:pdfcheck" "先跑 npm run book:pdf 生成 PDF（约 8 分钟），再跑这一项"
  fi
else
  skip "book:unittest" "缺 Python 3"
  skip "book:pack" "缺 Python 3"
  skip "book:pack-verify" "缺 Python 3"
  skip "book:pdfcheck" "缺 Python 3"
fi

# ---- Python 静态检查：只抓真错误，不做格式/lint 风格 ----
if [ -n "$PY" ] && "$PY" -m ruff --version >/dev/null 2>&1; then
  gate "ruff" "$PY" -m ruff check .
else
  skip "ruff" "缺 ruff：python -m pip install ruff==0.15.21"
fi

echo "共 $PASS pass / $FAIL fail / $SKIP skip"
exit $((FAIL > 0 ? 1 : 0))