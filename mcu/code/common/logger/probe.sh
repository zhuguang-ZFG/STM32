#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p build
flags="-std=c11 -O2 -Wall -Wextra -Werror"
${HOSTCC:-gcc} $flags logger.c store.c ../reliability/protocol.c tests.c -o build/tests.exe
./build/tests.exe
if [ "$(uname -s)" = Linux ]; then
  ${HOSTCC:-gcc} $flags -g -fsanitize=address,undefined logger.c store.c ../reliability/protocol.c tests.c -o build/sanitized
  ASAN_OPTIONS=detect_leaks=1 UBSAN_OPTIONS=halt_on_error=1 ./build/sanitized
fi
