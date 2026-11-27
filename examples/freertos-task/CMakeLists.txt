cmake_minimum_required(VERSION 3.21)
project(freertos-task C)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

# Sprint A: host regression only. Firmware still targets BluePill F103 in main.c;
# chapter 22–24 board of record is F407 — CubeF4 ARM build is a follow-up.
option(FREERTOS_TASK_HOST_TESTS "Build host regression tests (no board)" OFF)
if(FREERTOS_TASK_HOST_TESTS)
    enable_testing()
    add_executable(freertos-task-tests tests/freertos_task_tests.c)
    target_include_directories(freertos-task-tests PRIVATE tests)
    target_compile_options(freertos-task-tests PRIVATE -Wall -Wextra -Werror)
    add_test(NAME freertos-task-host COMMAND freertos-task-tests)
    add_executable(freertos-task-priority6-tests tests/freertos_task_tests.c)
    target_include_directories(freertos-task-priority6-tests PRIVATE tests)
    target_compile_definitions(freertos-task-priority6-tests PRIVATE TEST_SYSCALL_RAW=0x60U)
    target_compile_options(freertos-task-priority6-tests PRIVATE -Wall -Wextra -Werror)
    add_test(NAME freertos-task-host-priority6 COMMAND freertos-task-priority6-tests)
    return()
endif()

message(FATAL_ERROR
    "Firmware CMake for freertos-task is not in this sprint. "
    "Configure with -DFREERTOS_TASK_HOST_TESTS=ON (see README.md).")
