cmake_minimum_required(VERSION 3.21)
project(dma-memcopy C ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

option(DMA_MEMCOPY_HOST_TESTS "Build host regression tests with a simulated HAL" OFF)
if(DMA_MEMCOPY_HOST_TESTS)
    enable_testing()
    add_executable(dma-memcopy-tests tests/dma_memcopy_tests.c)
    target_include_directories(dma-memcopy-tests PRIVATE tests)
    target_compile_options(dma-memcopy-tests PRIVATE -Wall -Wextra -Werror)
    add_test(NAME dma-memcopy-host COMMAND dma-memcopy-tests)
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
add_executable(dma-memcopy.elf
    main.c stm32f1xx_it.c
    "${DEVICE_DIR}/Source/Templates/system_stm32f1xx.c"
    "${DEVICE_DIR}/Source/Templates/gcc/startup_stm32f103xb.s"
    "${HAL_DIR}/Src/stm32f1xx_hal.c"
    "${HAL_DIR}/Src/stm32f1xx_hal_cortex.c"
    "${HAL_DIR}/Src/stm32f1xx_hal_gpio.c"
    "${HAL_DIR}/Src/stm32f1xx_hal_rcc.c"
    "${HAL_DIR}/Src/stm32f1xx_hal_flash.c"
    "${HAL_DIR}/Src/stm32f1xx_hal_dma.c"
)
target_compile_definitions(dma-memcopy.elf PRIVATE STM32F103xB USE_HAL_DRIVER)
target_compile_options(dma-memcopy.elf PRIVATE -Wall -Wextra -Werror)
target_include_directories(dma-memcopy.elf PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
    "${CUBEF1_PATH}/Drivers/CMSIS/Include"
    "${DEVICE_DIR}/Include" "${HAL_DIR}/Inc"
)
target_link_options(dma-memcopy.elf PRIVATE
    "-T${CMAKE_CURRENT_SOURCE_DIR}/stm32f103c8.ld"
    "-Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/dma-memcopy.map"
    -Wl,--print-memory-usage
)
set_property(TARGET dma-memcopy.elf APPEND PROPERTY LINK_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/stm32f103c8.ld")
add_custom_command(TARGET dma-memcopy.elf POST_BUILD
    COMMAND ${CMAKE_OBJCOPY} -O ihex $<TARGET_FILE:dma-memcopy.elf> "${CMAKE_CURRENT_BINARY_DIR}/dma-memcopy.hex"
    COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE:dma-memcopy.elf> "${CMAKE_CURRENT_BINARY_DIR}/dma-memcopy.bin"
    COMMAND ${CMAKE_SIZE} $<TARGET_FILE:dma-memcopy.elf>
    COMMAND ${CMAKE_COMMAND} -E make_directory "${CMAKE_CURRENT_BINARY_DIR}/licenses"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${HAL_DIR}/LICENSE.md" "${CMAKE_CURRENT_BINARY_DIR}/licenses/HAL-LICENSE.md"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${DEVICE_DIR}/License.md" "${CMAKE_CURRENT_BINARY_DIR}/licenses/CMSIS-DEVICE-LICENSE.md"
    COMMAND ${CMAKE_COMMAND} -E copy_if_different "${CUBEF1_PATH}/Drivers/CMSIS/LICENSE.txt" "${CMAKE_CURRENT_BINARY_DIR}/licenses/CMSIS-CORE-LICENSE.txt"
)
