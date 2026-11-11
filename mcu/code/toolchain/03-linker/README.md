# 03-linker —— B3 链接脚本取证（六刀）

配套章节：[B3 链接脚本](../../../docs/build/03-linker-script.md)。
**不需要开发板，也不需要 make**，只要交叉工具链在 PATH 里；图纸一律从
`code/stm32/00-blink/stm32f407xx.ld` 用 `sed` 现改一刀，diff 打在输出里，原文不动。

```bash
sh probe.sh            # 六刀全跑
sh probe.sh keep       # 删掉 KEEP(*(.isr_vector))
sh probe.sh at         # 删掉 AT> FLASH
sh probe.sh overflow   # RAM LENGTH 改小 / 栈预算撑大
sh probe.sh flags      # 区域属性写成 (xrwah)
sh probe.sh ccm        # CCM 三态（中间那态会写 128MB 文件，量完即删）
sh probe.sh trace      # --print-memory-usage / --trace / ld --verbose
sh probe.sh clean
CCM_GAP=0 sh probe.sh ccm   # 不让 128MB 落盘，只报换算式
```

## 六刀各自证什么（数字全部实测）

1. **`KEEP` 是向量表的护身符**：只把 `KEEP(*(.isr_vector))` 的 `KEEP` 去掉，`--gc-sections`
   就把整张表搬走——`blink.bin` 660 字节 → `nokeep.bin` 268 字节，差 **392 = 0x188**，正好是
   段表里 `.isr_vector` 的尺寸。更阴的是 `readelf -S` 仍列出 `.isr_vector`，尺寸 0：段名还在、
   字节没了。硬件上电从 `0x08000000` 连读两个字，正常是 `20020000 / 08000189`（栈顶 / 复位入口），
   这一刀之后变成 `d040f8df / 68014810`——那是 `.text` 头两条指令的机器码，第一次压栈就飞。
2. **`AT> FLASH` 是 .data 的快递单**：删掉它，程序头从三条变两条，`.data` 那行
   `PhysAddr` 从 `0x08000218` 塌成 `0x20000000`，`nm` 里 `_sidata == _sdata == 0x20000000`。
   启动文件的拷贝循环于是变成"把 `_sdata` 拷到 `_sdata`"，Flash 里那 4 个初值字节没人来取，
   而上电瞬间 RAM 里是随机值。
3. **图纸在链接期就拦住你**：`--print-memory-usage` 报 `FLASH 540 B / RAM 5640 B`，
   5640 = `.data` 4 + `.bss` 4100 + 检查段 1536（手算得到，与工具一字不差）。
   `RAM LENGTH` 改 2K → `region 'RAM' overflowed by 3592 bytes`（5640 − 2048 = 3592）；
   数据一个不加、只把 `_Min_Stack_Size` 从 `0x400` 撑到 `0x20000` →
   点名 `._user_heap_stack`、`overflowed by 4616 bytes`、`RAM 135688 B = 103.52%`。
   那个检查段一字节真实数据都不占，却能在链接期把爆栈拦下来。
4. **区域属性没有 `h`**：`RAM (xrwah)` → `invalid character %c (104) in flags`。
   104 是字母 `h` 的 ASCII；合法字母只有 `r w x a i l`。那句 `%c` 是 binutils 2.45.1
   自己的格式串漏了参数，不是抄错——原文照抄才有价值。
5. **CCM 的三态**：
   - 图纸没留房间：`.ccmram` 成 orphan，被 ld 塞到 **VMA `0x20000004`**（普通 SRAM 的第 5 个字节），
     零警告零报错——"我以为它在 CCM"是假的。
   - 留了房间但只写 `>CCM`：第三条 LOAD 的 `VirtAddr = PhysAddr = 0x10000000`，
     `objcopy -O binary` 安静地把 `0x0800xxxx → 0x10000000` 整段补零，
     bin 从 660 字节变 **134,217,744 字节**（`0x10000000 − 0x08000000 = 134,217,728` + 16 字节初值）。
   - 补上 `AT> FLASH`：`.ccmram` 的 `PhysAddr` 回到 Flash（`0x0800022c`），bin 收回 **576 字节**。
   - 可还是用不了：`grep -c` 数启动文件里的符号引用，`_sidata` 出现 3 次、`_siccm` **0 次**；
     `Reset_Handler` 反汇编只有一对 `ldr/str` 循环 + 一段清零循环。`_sccm/_eccm` 是两块没人认领的门牌，
     带初值的 CCM 全局上电仍是随机值——要真用，得自己在启动文件补第二段拷贝。
6. **让链接器自己交代**：`--trace` 里库那几行的目录是 `thumb/v7e-m+fp/hard`——
   这串名字就是 `-mfpu=fpv4-sp-d16 -mfloat-abi=hard` 换来的多架构子目录，
   换 soft-float 会去别的目录找，"明明装了库却报 cannot find"多半栽在这里；
   `ld --verbose` 打印不写 `-T` 时的内置图纸（`OUTPUT_FORMAT("elf32-littlearm"...)`、`ENTRY(_start)`），
   顺带能看见 `Supported emulations: armelf`。

## 工具链口径

xPack GNU Arm Embedded GCC **15.2.1** / binutils **2.45.1.20251203**，
`-mcpu=cortex-m4 -mthumb -mfpu=fpv4-sp-d16 -mfloat-abi=hard -O0 -g3 -ffunction-sections -fdata-sections`，
链接带 `-Wl,--gc-sections -nostartfiles`。报错文本照抄，只把 `ld.exe` 的机器绝对路径前缀省掉
（`collect2.exe:` 前缀也省掉），其余一字未改；换 binutils 版本时第 4 刀的措辞可能不同。

## 还没上的板

六刀全是链接期与文件期的证据。**向量表被吃掉之后板子到底怎么死、CCM 里的随机值长什么样**
——这些板上现象待接板回填。
