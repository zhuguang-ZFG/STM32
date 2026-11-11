cmake_minimum_required(VERSION 3.16)
include($ENV{IDF_PATH}/tools/cmake/project.cmake)
project(qmi8658)

# Reject stale sdkconfig files that silently target the classic ESP32.
if(NOT IDF_TARGET STREQUAL "esp32s3")
    message(FATAL_ERROR "This example requires ESP32-S3. Run: idf.py set-target esp32s3")
endif()
