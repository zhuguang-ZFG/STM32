#!/usr/bin/env bash
# Prepare the local render environment for sweety-handdraw-video (macOS: Homebrew; Linux: apt, dnf or pacman).
#
#   bash scripts/setup.sh            install FFmpeg (+ CJK fonts on Linux) and a Python venv with requirements
#   bash scripts/setup.sh --check    report only, install nothing
#   bash scripts/setup.sh --venv DIR use another venv (default: ~/.local/share/sweety-handdraw-video/venv)
#   bash scripts/setup.sh --voxcpm   Apple Silicon only: also create an MLX venv and download
#                                    mlx-community/VoxCPM2-8bit (about 3.2 GB); never done without this flag
#   bash scripts/setup.sh --web-motion  also install Playwright and its headless Chromium (about 150 MB) for web
#                                    motion layers (titles, charts, maps, morphs); without it those layers are refused
set -euo pipefail
SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/sweety-handdraw-video"
VENV="$DATA_DIR/venv"
CHECK=0
VOXCPM=0
WEB_MOTION=0
PROBLEMS=0
while [ $# -gt 0 ]; do
  case "$1" in
    --check) CHECK=1 ;;
    --venv) VENV="$2"; shift ;;
    --voxcpm) VOXCPM=1 ;;
    --web-motion) WEB_MOTION=1 ;;
    -h|--help) sed -n '2,11p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1"; sed -n '2,11p' "$0"; exit 2 ;;
  esac
  shift
done
OS="$(uname -s)"
SUDO="$( [ "$(id -u)" = 0 ] || echo sudo)"
have() { command -v "$1" >/dev/null 2>&1; }
step() { printf '\n== %s\n' "$*"; }
problem() { echo "MISSING: $*"; PROBLEMS=$((PROBLEMS + 1)); }

step "System packages ($OS)"
NEED_FFMPEG=0; NEED_FONTS=0
{ have ffmpeg && have ffprobe; } || NEED_FFMPEG=1
if [ "$OS" = Linux ] && ! { have fc-list && [ -n "$(fc-list :lang=zh 2>/dev/null | head -n 1)" ]; }; then NEED_FONTS=1; fi
if [ "$NEED_FFMPEG$NEED_FONTS" = 00 ]; then
  echo "ok: ffmpeg $(ffmpeg -version | head -n 1 | cut -d' ' -f3)$( [ "$OS" = Linux ] && echo ', Chinese fonts via fontconfig')"
else
  INSTALL=""
  if [ "$OS" = Darwin ]; then
    have brew && INSTALL="brew install ffmpeg" || echo "Install Homebrew first: https://brew.sh"
  elif have apt-get; then
    PACKAGES="$( [ $NEED_FFMPEG = 1 ] && echo ffmpeg) $( [ $NEED_FONTS = 1 ] && echo fonts-noto-cjk fontconfig)"
    INSTALL="$SUDO apt-get update -qq && DEBIAN_FRONTEND=noninteractive $SUDO apt-get install -y -qq $PACKAGES"
  elif have dnf; then
    INSTALL="$SUDO dnf install -y ffmpeg-free google-noto-sans-cjk-fonts fontconfig"
  elif have pacman; then
    INSTALL="$SUDO pacman -S --needed ffmpeg noto-fonts-cjk fontconfig"
  fi
  if [ $CHECK = 1 ] || [ -z "$INSTALL" ]; then
    problem "ffmpeg/ffprobe or Chinese fonts -> ${INSTALL:-install them with your package manager}"
  else
    echo "+ $INSTALL"; eval "$INSTALL"
  fi
fi

step "Python render environment ($VENV)"
PYTHON="${PYTHON:-python3}"
if ! "$PYTHON" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
  problem "Python 3.9+ -> brew install python | sudo apt-get install -y python3 python3-venv"
elif [ $CHECK = 1 ]; then
  if "$VENV/bin/python" -c 'import PIL, numpy, scipy, requests, fontTools' 2>/dev/null; then echo "ok: $VENV"
  else problem "render venv -> bash scripts/setup.sh"; fi
else
  [ -x "$VENV/bin/python" ] || "$PYTHON" -m venv "$VENV" || { problem "python venv -> sudo apt-get install -y python3-venv"; exit 1; }
  "$VENV/bin/python" -m pip install -q --upgrade pip
  "$VENV/bin/python" -m pip install -q -r "$SKILL_DIR/scripts/requirements.txt"
  echo "ok: $VENV"
fi
if [ -x "$VENV/bin/python" ] && [ $PROBLEMS = 0 ]; then
  if "$VENV/bin/python" "$SKILL_DIR/scripts/validate_package.py" >/dev/null; then echo "ok: package integrity"
  else problem "package integrity -> reinstall the whole skill folder (see the validate_package.py error above)"; fi
  "$VENV/bin/python" "$SKILL_DIR/scripts/fonts.py" | "$VENV/bin/python" -c 'import json,sys; d=json.load(sys.stdin); [print("ok: %s font %s#%s" % (k, *v["selected"])) for k, v in d.items()]' \
    || problem "Chinese font -> see the fonts.py error above"
fi

step "Web motion layers (optional)"
if [ -x "$VENV/bin/python" ] && "$VENV/bin/python" "$SKILL_DIR/scripts/web_motion.py" check 2>/dev/null | grep -q '"available": true'; then
  echo "ok: Playwright + Chromium"
elif [ $WEB_MOTION = 1 ] && [ $CHECK = 0 ] && [ -x "$VENV/bin/python" ]; then
  "$VENV/bin/python" -m pip install -q 'playwright>=1.40'
  "$VENV/bin/python" -m playwright install chromium
  "$VENV/bin/python" "$SKILL_DIR/scripts/web_motion.py" check | grep -q '"available": true' && echo "ok: Playwright + Chromium" \
    || problem "web motion -> see the Playwright error above"
else
  echo "not installed (only needed for overlays): bash scripts/setup.sh --web-motion"
fi

if [ $VOXCPM = 1 ]; then
  step "VoxCPM2 MLX (explicitly requested)"
  if [ "$OS" != Darwin ] || [ "$(uname -m)" != arm64 ]; then
    problem "VoxCPM2 MLX needs Apple Silicon macOS; use VoiceStudio or supply narration + alignment"
  elif [ $CHECK = 0 ]; then
    VOX_VENV="$DATA_DIR/voxcpm-venv"; MODEL="$DATA_DIR/models/VoxCPM2-8bit"
    [ -x "$VOX_VENV/bin/python" ] || "$PYTHON" -m venv "$VOX_VENV"
    "$VOX_VENV/bin/python" -m pip install -q mlx-audio soundfile huggingface_hub pypinyin
    "$VOX_VENV/bin/python" -c "from huggingface_hub import snapshot_download; snapshot_download('mlx-community/VoxCPM2-8bit', local_dir='$MODEL')"
    echo "ok: job.json \"voxcpm\": {\"model_path\": \"$MODEL\"}; run: $VOX_VENV/bin/python scripts/voxcpm_voice.py JOB"
  fi
fi

step "Optional (not installed by this script)"
if [ "$OS" = Darwin ]; then
  echo "- Handwriting font: Font Book > search \"Hannotate SC\" > Download (Hiragino Sans GB is used otherwise)"
else
  echo "- Handwriting font: LXGW WenKai (https://github.com/lxgw/LxgwWenKai) into ~/.local/share/fonts, then fc-cache -f"
fi
echo "- Narration: local VoiceStudio service (http://127.0.0.1:3900); VoxCPM2 on Apple Silicon (bash scripts/setup.sh --voxcpm);"
echo "  or a checked narration file + alignment (references/continuous-narration.md)"
echo "- Images: Codex has built-in image generation; Claude Code needs an image-generation tool/MCP or user-provided images."
echo "  Without one, stop: never deliver a text-only film."
echo "- Use the venv: source \"$VENV/bin/activate\" && python scripts/handdraw_video.py doctor JOB"
[ $PROBLEMS = 0 ] || { echo; echo "$PROBLEMS item(s) need attention (see MISSING lines)."; exit 1; }
