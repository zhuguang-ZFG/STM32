cmake_minimum_required(VERSION 3.20)
project(motor-dc-speed C ASM)

set(CMAKE_C_STANDARD 11)
set(CMAKE_C_STANDARD_REQUIRED ON)

set(CORE_SOURCES
    src/encoder.c
    src/speed_estimator.c
    src/pi_controller.c
    src/motor_state.c
    src/motor_bridge.c
    src/telemetry.c
    src/command.c
    src/control_tick.c
)

set(CORE_INCLUDES ${CMAKE_CURRENT_SOURCE_DIR}/include)

if(MOTOR_TARGET STREQUAL "host")
    add_executable(host_tests tests/host_tests.c ${CORE_SOURCES})
    target_include_directories(host_tests PRIVATE ${CORE_INCLUDES})
    target_link_libraries(host_tests PRIVATE m)
    enable_testing()
    add_test(NAME host_tests COMMAND host_tests)
elseif(MOTOR_TARGET STREQUAL "stm32f103")
    set(CUBEF1_PATH "" CACHE PATH "Path to STM32CubeF1 (see dependencies.lock.json)")
    if(NOT CUBEF1_PATH)
        message(FATAL_ERROR "Set -DCUBEF1_PATH=<STM32CubeF1 checkout> (fixed version in dependencies.lock.json)")
    endif()
    set(BOARD_DIR ${CMAKE_CURRENT_SOURCE_DIR}/boards/f103c8-tb6612)
    set(DEVICE_SRC ${CUBEF1_PATH}/Drivers/CMSIS/Device/ST/STM32F1xx)
    set(HAL_SRC ${CUBEF1_PATH}/Drivers/STM32F1xx_HAL_Driver)

    add_definitions(-DSTM32F103xB -DUSE_HAL_DRIVER)

    set(HAL_MODULES
        ${HAL_SRC}/Src/stm32f1xx_hal.c
        ${HAL_SRC}/Src/stm32f1xx_hal_rcc.c
        ${HAL_SRC}/Src/stm32f1xx_hal_gpio.c
        ${HAL_SRC}/Src/stm32f1xx_hal_tim.c
        ${HAL_SRC}/Src/stm32f1xx_hal_tim_ex.c
        ${HAL_SRC}/Src/stm32f1xx_hal_uart.c
        ${HAL_SRC}/Src/stm32f1xx_hal_cortex.c
        ${HAL_SRC}/Src/stm32f1xx_hal_dma.c
        ${HAL_SRC}/Src/stm32f1xx_hal_flash.c
        ${HAL_SRC}/Src/stm32f1xx_hal_pwr.c
        ${DEVICE_SRC}/Source/Templates/system_stm32f1xx.c
        ${DEVICE_SRC}/Source/Templates/gcc/startup_stm32f103xb.s
    )

    add_executable(motor-dc-speed.elf
        src/main.c src/board_init.c src/stm32f1xx_it.c
        ${CORE_SOURCES} ${HAL_MODULES}
    )
    target_include_directories(motor-dc-speed.elf PRIVATE
        ${CORE_INCLUDES} ${BOARD_DIR}
        ${CUBEF1_PATH}/Drivers/CMSIS/Include
        ${DEVICE_SRC}/Include
        ${HAL_SRC}/Inc
        ${HAL_SRC}/Inc/Legacy
    )
    target_link_options(motor-dc-speed.elf PRIVATE
        -T${BOARD_DIR}/stm32f103c8.ld
        -Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/motor-dc-speed.map
    )
    add_custom_command(TARGET motor-dc-speed.elf POST_BUILD
        COMMAND ${CMAKE_OBJCOPY} -O ihex $<TARGET_FILE:motor-dc-speed.elf> motor-dc-speed.hex
        COMMAND ${CMAKE_OBJCOPY} -O binary $<TARGET_FILE:motor-dc-speed.elf> motor-dc-speed.bin
        COMMAND ${CMAKE_SIZE} $<TARGET_FILE:motor-dc-speed.elf>
    )
else()
    message(FATAL_ERROR "Unknown MOTOR_TARGET=${MOTOR_TARGET}")
endif()
