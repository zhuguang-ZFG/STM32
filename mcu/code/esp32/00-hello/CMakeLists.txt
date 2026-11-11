# 顶层 CMakeLists.txt —— ESP-IDF 工程的"出生证明"
# 三行缺一不可：最低版本、拉进 IDF 构建系统、给工程起名
cmake_minimum_required(VERSION 3.16)

# IDF_PATH 由 ESP-IDF 环境变量提供；这一行把整套组件化构建规则拉进来
include($ENV{IDF_PATH}/tools/cmake/project.cmake)

# 工程名 = 固件文件名（build/hello-mcu.bin）
project(hello-mcu)

# Reject stale sdkconfig files that silently target the classic ESP32.
if(NOT IDF_TARGET STREQUAL "esp32s3")
    message(FATAL_ERROR "This example requires ESP32-S3. Run: idf.py set-target esp32s3")
endif()
