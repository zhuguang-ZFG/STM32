# 顶层 CMakeLists.txt —— 与 00-hello / 06-framed-protocol 同构
# 三行缺一不可：最低版本、拉进 IDF 构建系统、给工程起名
cmake_minimum_required(VERSION 3.16)

# IDF_PATH 由 ESP-IDF 环境变量提供；这一行把整套组件化构建规则拉进来
include($ENV{IDF_PATH}/tools/cmake/project.cmake)

# 工程名 = 固件文件名（build/watchdog-health.bin）
project(watchdog-health)
