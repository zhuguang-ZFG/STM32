# main 组件的 CMakeLists.txt —— 声明"我有哪些源文件"
# ESP-IDF 约定：叫 main 的组件是特殊组件，自动链接进 app
idf_component_register(SRCS "hello_main.c"
                    INCLUDE_DIRS "")
