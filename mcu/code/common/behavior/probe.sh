#!/bin/sh
set -eu
cd "$(dirname "$0")"
mkdir -p build
${HOSTCC:-gcc} -std=c11 -Wall -Wextra -Werror -O2 tests.c -o build/tests.exe
./build/tests.exe
echo "capture, clocks and DMA stream behavior passed"
