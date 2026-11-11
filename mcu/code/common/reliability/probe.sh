#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p build
cc="${HOSTCC:-gcc}"
python="${PYTHON:-python3}"
flags="-std=c11 -Wall -Wextra -Werror -O2"
sources="protocol.c health.c transport.c service.c query.c record.c"
"$cc" $flags $sources tests.c -o build/tests.exe
./build/tests.exe
"$cc" $flags protocol.c codec-tool.c -o build/codec-tool.exe
# Windows 的 python3 是原生解释器：MSYS 路径必须先转成 Windows 路径
helper="$(pwd)/build/codec-tool.exe"
case "$(uname -s)" in
    *MINGW*|*MSYS*|*CYGWIN*) helper="$(cygpath -w "$helper")" ;;
esac
"$python" ../../../scripts/device-console.py self-test --c-helper "$helper"
if [ "$(uname -s)" = Linux ]; then
    "$cc" -std=c11 -Wall -Wextra -Werror -O1 -g -fno-omit-frame-pointer -fsanitize=address,undefined $sources tests.c -o build/sanitized
    ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=halt_on_error=1 ./build/sanitized
fi
