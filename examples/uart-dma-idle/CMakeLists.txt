cmake_minimum_required(VERSION 3.21)
project(uart-dma-idle C ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

option(UART_DMA_HOST_TESTS "Build host regression tests with a simulated HAL" OFF)
if(UART_DMA_HOST_TESTS)
    enable_testing()
    add_executable(uart-dma-tests tests/uart_dma_tests.c)
    target_include_directories(uart-dma-tests PRIVATE tests)
    target_compile_options(uart-dma-tests PRIVATE -Wall -Wextra -Werror)
    add_test(NAME uart-dma-host COMMAND uart-dma-tests)
    return()
endif()

set(CUBEF1_PATH "" CACHE PATH "STM32CubeF1 v1.8.6 checkout with HAL and CMSIS device submodules")
if(NOT CUBEF1_PATH)
    message(FATAL_ERROR "Set -DCUBEF1_PATH=<STM32CubeF1 v1.8.6 checkout>; see README.md")
endif()
find_package(Git REQUIRED)
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/dependencies.lock.json" DEPENDENCIES)
foreach(COMPONENT IN ITEMS commit hal cmsis_device)
    if(COMPONENT STREQUAL "hal")
        set(COMPONENT_PATH "${CUBEF1_PATH}/Drivers/STM32F1xx_HAL_Driver")
    elseif(COMPONENT STREQUAL "cmsis_device")
        set(COMPONENT_PATH "${CUBEF1_PATH}/Drivers/CMSIS/Device/ST/STM32F1xx")
    else()
        set(COMPONENT_PATH "${CUBEF1_PATH}")
    endif()
    string(JSON EXPECTED_COMMIT GET "${DEPENDENCIES}" STM32CubeF1 ${COMPONENT})
    execute_process(COMMAND "${GIT_EXECUTABLE}" -C "${COMPONENT_PATH}" rev-parse HEAD
        OUTPUT_VARIABLE ACTUAL_COMMIT OUTPUT_STRIP_TRAILING_WHITESPACE
        RESULT_VARIABLE GIT_RESULT ERROR_QUIET)
    if(NOT GIT_RESULT EQUAL 0 OR NOT ACTUAL_COMMIT STREQUAL EXPECTED_COMMIT)
        message(FATAL_ERROR "${COMPONENT}: expected ${EXPECTED_COMMIT}, got '${ACTUAL_COMMIT}'; initialize the locked submodules")
    endif()
endforeach()

set(DEVICE_DIR "${CUBEF1_PATH}/Drivers/CMSIS/Device/ST/STM32F1xx")
set(HAL_DIR "${CUBEF1_PATH}/Drivers/STM32F1xx_HAL_Driver")
add_executable(uart-dma-idle.elf
    main.c stm32f1xx_it.c
    "${DEVICE_DIR}/Source/Templates/system_stm32f1xx.c"
    "${DEVICE_DIR}/Source/Templates/gcc/startup_stm32f103xb.s"
    "${HAL_DIR}/Src/stm32f1xx_hal.c"
    "${HAL_DIR}/Src/stm32f1xx_hal_cortex.c"
    "${HAL_DIR}/Src/stm32f1xx_hal_gpio.c"
    "${HAL_DIR}/Src/stm32f1xx_hal_rcc.c"
    "${HAL_DIR}/Src/stm32f1xx_hal_flash.c"
    "${HAL_DIR}/Src/stm32f1xx_hal_uart.c"
    "${HAL_DIR}/Src/stm32f1xx_hal_dma.c"
)
target_compile_definitions(uart-dma-idle.elf PRIVATE STM32F103xB USE_HAL_DRIVER)
target_compile_options(uart-dma-idle.elf PRIVATE -Wall -Wextra)
target_include_directories(uart-dma-idle.elf PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
    "${CUBEF1_PATH}/Drivers/CMSIS/Include"
    "${DEVICE_DIR}/Include" "${HAL_DIR}/Inc"
)
target_link_options(uart-dma-idle.elf PRIVATE
    "-T${CMAKE_CURRENT_SOURCE_DIR}/stm32f103c8.ld"
    "-Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/uart-dma-idle.map"
    -Wl,--print-memory-usage
)
set_property(TARGET uart-dma-idle.elf APPEND PROPERTY LINK_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/stm32f103c8.ld")
add_custom_command(TARGET uart-dma-idle.elf POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O ihex $<TARGET_FILE:uart-dma-idle.elf> "${CMAKE_CURRENT_BINARY_DIR}/uart-dma-idle.hex"
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE:uart-dma-idle.elf> "${CMAKE_CURRENT_BINARY_DIR}/uart-dma-idle.bin"
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE:uart-dma-idle.elf>
    COMMAND ${CMAKE_COMMAND} -E make_directory "${CMAKE_CURRENT_BINARY_DIR}/licenses"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${HAL_DIR}/LICENSE.md" "${CMAKE_CURRENT_BINARY_DIR}/licenses/HAL-LICENSE.md"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${DEVICE_DIR}/License.md" "${CMAKE_CURRENT_BINARY_DIR}/licenses/CMSIS-DEVICE-LICENSE.md"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${CUBEF1_PATH}/Drivers/CMSIS/LICENSE.txt" "${CMAKE_CURRENT_BINARY_DIR}/licenses/CMSIS-CORE-LICENSE.txt"
)
