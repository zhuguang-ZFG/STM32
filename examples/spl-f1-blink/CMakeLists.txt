cmake_minimum_required(VERSION 3.24)
project(spl_f1_blink LANGUAGES C ASM)

if(NOT SPL_ROOT)
  message(FATAL_ERROR "Set SPL_ROOT to STM32F10x StdPeriph V3.5.0 commit afa743577f2784e95be2d5003380fdb84a702519")
endif()
file(TO_CMAKE_PATH "${SPL_ROOT}" SPL_ROOT)

set(CMSIS_DEVICE "${SPL_ROOT}/Libraries/CMSIS/CM3/DeviceSupport/ST/STM32F10x")
set(CMSIS_CORE "${SPL_ROOT}/Libraries/CMSIS/CM3/CoreSupport")
set(SPL_DRIVER "${SPL_ROOT}/Libraries/STM32F10x_StdPeriph_Driver")
set(SPL_TEMPLATE "${SPL_ROOT}/Project/STM32F10x_StdPeriph_Template")
set(STARTUP "${CMSIS_DEVICE}/startup/TrueSTUDIO/startup_stm32f10x_md.s")

foreach(required
    "${CMSIS_DEVICE}/stm32f10x.h"
    "${SPL_DRIVER}/inc/stm32f10x_gpio.h"
    "${SPL_DRIVER}/src/stm32f10x_gpio.c"
    "${SPL_DRIVER}/src/stm32f10x_rcc.c"
    "${SPL_TEMPLATE}/system_stm32f10x.c"
    "${STARTUP}")
  if(NOT EXISTS "${required}")
    message(FATAL_ERROR "Pinned SPL file is missing: ${required}")
  endif()
endforeach()

set(CORE_INCLUDE "${CMSIS_CORE}")
if(NOT EXISTS "${CMSIS_CORE}/core_cm3.h")
  if(EXISTS "${CMSIS_CORE}/core_cm3.h.old")
    file(MAKE_DIRECTORY "${CMAKE_BINARY_DIR}/generated")
    configure_file("${CMSIS_CORE}/core_cm3.h.old" "${CMAKE_BINARY_DIR}/generated/core_cm3.h" COPYONLY)
    set(CORE_INCLUDE "${CMAKE_BINARY_DIR}/generated")
  else()
    message(FATAL_ERROR "Neither core_cm3.h nor the frozen mirror's core_cm3.h.old exists")
  endif()
endif()

add_executable(spl-f1-blink
  src/main.c
  src/stm32f10x_it.c
  src/runtime.c
  "${SPL_TEMPLATE}/system_stm32f10x.c"
  "${SPL_DRIVER}/src/stm32f10x_gpio.c"
  "${SPL_DRIVER}/src/stm32f10x_rcc.c"
  "${STARTUP}"
)
set_target_properties(spl-f1-blink PROPERTIES SUFFIX ".elf")

target_include_directories(spl-f1-blink PRIVATE
  include
  "${CORE_INCLUDE}"
  "${CMSIS_DEVICE}"
  "${SPL_DRIVER}/inc"
)
target_compile_definitions(spl-f1-blink PRIVATE STM32F10X_MD USE_STDPERIPH_DRIVER)
target_compile_options(spl-f1-blink PRIVATE
  -mcpu=cortex-m3
  -mthumb
  -ffunction-sections
  -fdata-sections
  $<$<COMPILE_LANGUAGE:C>:-std=c11;-Wall;-Wextra>
)
set_source_files_properties(src/main.c src/stm32f10x_it.c src/runtime.c
  PROPERTIES COMPILE_OPTIONS -Werror
)
target_link_options(spl-f1-blink PRIVATE
  -mcpu=cortex-m3
  -mthumb
  -nostartfiles
  -specs=nano.specs
  -specs=nosys.specs
  "-T${CMAKE_CURRENT_SOURCE_DIR}/linker/stm32f103c8.ld"
  "-Wl,-Map=${CMAKE_CURRENT_BINARY_DIR}/spl-f1-blink.map,--gc-sections,--print-memory-usage"
)

add_custom_command(TARGET spl-f1-blink POST_BUILD
  COMMAND "${CMAKE_OBJCOPY}" -O ihex "$<TARGET_FILE:spl-f1-blink>" "${CMAKE_CURRENT_BINARY_DIR}/spl-f1-blink.hex"
  COMMAND "${CMAKE_OBJCOPY}" -O binary "$<TARGET_FILE:spl-f1-blink>" "${CMAKE_CURRENT_BINARY_DIR}/spl-f1-blink.bin"
  COMMAND "${CMAKE_SIZE}" "$<TARGET_FILE:spl-f1-blink>"
  VERBATIM
)
