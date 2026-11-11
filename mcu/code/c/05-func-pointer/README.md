# C5 取证工程：函数指针、状态机与环形缓冲

不需要开发板。宿主 gcc 编译运行 `probe.c`（560 条断言），PATH 里有
`arm-none-eabi-gcc` 时附送 Cortex-M4 反汇编（看函数指针调用 = `blx`）。

```sh
sh probe.sh          # 全部
sh probe.sh clean
```

## 本机取证记录（2026-10-07）

- 宿主：MinGW-Builds **gcc 16.1.0**（x86_64-posix-seh），命令
  `gcc -std=c11 -Wall -Wextra -Werror -O2 probe.c -o build/probe.exe`
- 交叉：xPack **arm-none-eabi-gcc 15.2.1**，`-mcpu=cortex-m4 -mthumb
  -mfpu=fpv4-sp-d16 -mfloat-abi=hard -std=c11 -Wall -Wextra -Werror -O2 -c`

宿主运行输出（全文）：

```
环形缓冲容量对照：A 派（牺牲一格）可用 7 格，B 派（单调索引）可用 8 格
== 断言通过 560/560 ==
```

交叉反汇编关键两段（`build/probe.m4.s`，objdump -d）：

`fsm_feed`（probe.c:122 查表 + 间接调用）：

```
  92: eb03 0382 add.w  r3, r3, r2, lsl #2  @ 状态*4+事件
  96: 4a05      ldr    r2, [pc, #20]       @ FSM 表基址
  9a: f852 3023 ldr.w  r3, [r2, r3, lsl #2] @ 取出动作函数地址
  9e: 4798      blx    r3                  @ 间接跳转——函数指针的真身
  a0: 7020      strb   r0, [r4, #0]        @ 返回值写回 state
```

`main` 里的回调注册表分派（probe.c:59-61，判空 + blx）：

```
  20: b103      cbz    r3, 24 <main+0x24> @ 空槽跳过
  22: 4798      blx    r3                 @ 非空才调用
  28: f854 3b04 ldr.w  r3, [r4], #4       @ 取下一个 key_table[i]
```

结论：向量表、回调表、状态机动作表，落到指令层都是同一条 `blx`——
跳到"存在表里的那个地址"。表是 `const` 时基址在 Flash（C1 的 const 经济学）。
