#!/bin/sh
# probe.sh —— P4「IRAM 纪律」全部取证，一条命令跑完（不需要开发板）
#
#   sh probe.sh         ① 从 IDF 源码现挖：IRAM_ATTR / ESP_INTR_FLAG_IRAM 两个宏，
#                         中断源数量（编译器打印枚举值，不数行数），LEVEL1..6 的位号约定
#                         ——每行自带 文件:行号 引证
#                       ② idf.py build（已构建则增量）
#                       ③ 链接器实际用的分区表：直接从 .map 的 Memory Configuration 读，不写死地址
#                       ④ nm 指认七个符号的落址，并按③的区间当场判它归哪一段
#                       ⑤ .map 里每个符号真正所在的输入段（段名是链接器排的，不是猜的）
#                       ⑥ objdump 实拆：两条链的 call 目标地址，看断在哪一步
#                       ⑦ idf.py size 的整本账
#                       ⑧ 断言：四条链各归各位 + 级别位号 + 源数量，错一条就 exit 1
#   sh probe.sh clean   删掉 build/
#
# 产物一律落在 build/（code/**/build/ 已 gitignore）。
# 屏上每一个地址、每一行段名都必须出自这里，不许手抄。

set -e
cd "$(dirname "$0")"

if [ "${1:-}" = "clean" ]; then rm -rf build; echo "已清理 build/"; exit 0; fi

IDF="${IDF_PATH:-C:/Users/zhugu/.espressif/v5.5.2/esp-idf}"
[ -d "$IDF" ] || { echo "找不到 IDF_PATH：$IDF" >&2; exit 1; }

SYMS="isr_plain isr_leaky isr_tight isr_rodata helper_far helper_near k_table"

# Windows 上 IDF 的坑，逐条写死在这里，别再让下一个人踩：
#   1) export.ps1 里的 idf_tools.py 一看到 MSYSTEM 就 refuse（'MSys/Mingw is not supported'），
#      而 Git Bash 会把 MSYSTEM 塞进每一个子进程，env -u 也删不掉，只能在 PowerShell 里 Remove-Item。
#   2) 本机 IDF_TOOLS_PATH 里的 ccache/4.11.2 是个 msys 符号链接，Windows 侧解析不了，
#      export 会报 "tool ccache has no installed versions"；把任意一个能跑的 ccache.exe
#      放进 PATH，--prefer-system 那条路就通了（版本不符由 SKIP_VERSION_CHECK 放行）。
#   3) export.sh 在 msys 下根本走不通，所以构建这一步交给 PowerShell，取证这一步留在 sh 里。
run_idf() {
    IDF_PATH="$IDF" powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
        Remove-Item Env:\MSYSTEM -ErrorAction SilentlyContinue;
        \$env:IDF_TOOLS_SKIP_VERSION_CHECK = '1';
        if (-not (Get-Command ccache -ErrorAction SilentlyContinue)) {
            foreach (\$root in @(\"C:\Espressif\tools\ccache\", \"\$env:USERPROFILE\.espressif\tools\ccache\")) {
                \$cc = Get-ChildItem \$root -Recurse -Filter ccache.exe -ErrorAction SilentlyContinue | Select-Object -First 1;
                if (\$cc) { \$env:PATH = \$cc.DirectoryName + ';' + \$env:PATH; break }
            }
        }
        . (Join-Path \$env:IDF_PATH 'export.ps1') *>&1 | Out-Null;
        if (-not (Get-Command idf.py -ErrorAction SilentlyContinue)) { Write-Error 'export.ps1 没把 idf.py 送进 PATH'; exit 1 }
        idf.py $*;
        exit \$LASTEXITCODE"
}

# fact <文件> <grep锚> <sed提取式> <名字>
# 值从 stdout 返回，引证行打到 stderr 直接显示（和 S4 的 probe.sh 同一套路）
fact() {
    _l=$(grep -n "$2" "$1" | head -1)
    [ -n "$_l" ] || { echo "提取失败：$4（$1 里没有锚 $2）" >&2; exit 1; }
    _n=${_l%%:*}
    _v=$(printf '%s' "${_l#*:}" | sed -n "$3")
    printf '  %s:%s  %s\n' "$(basename "$1")" "$_n" \
        "$(printf '%s' "${_l#*:}" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')" >&2
    printf '%s\n' "$_v"
}

# 头文件位置随 IDF 版本挪过家，先找再引用，别写死路径
find_idf() {
    _f=$(find "$IDF/components" -path "*$1" 2>/dev/null | head -1)
    [ -n "$_f" ] || { echo "IDF 里没有 $1" >&2; exit 1; }
    printf '%s\n' "$_f"
}
ATTR_H=$(find_idf "esp_common/include/esp_attr.h")
ALLOC_H=$(find_idf "esp_intr_alloc.h")

echo "############ 1. 从 IDF 源码现挖两个宏 + 中断矩阵的规模（每行自带 文件:行号 引证） ############"
IRAM_ATTR_DEF=$(fact "$ATTR_H" 'define IRAM_ATTR' 's/.*define[[:space:]]*IRAM_ATTR[[:space:]]*//p' 'IRAM_ATTR')
IRAM_FLAG=$(fact "$ALLOC_H" 'ESP_INTR_FLAG_IRAM' 's/.*define[[:space:]]*ESP_INTR_FLAG_IRAM[[:space:]]*\([^ ]*\).*/\1/p' 'ESP_INTR_FLAG_IRAM')
echo "  → IRAM_ATTR 展开 = $IRAM_ATTR_DEF"
echo "  → ESP_INTR_FLAG_IRAM = $IRAM_FLAG"

# 中断源数量不数行数——行数会骗人：枚举里有三行是 EDGE 别名（与各自 TARGET 同值），
# 还有显式赋值把编号跳着写。让宿主机编译器把枚举值原样打出来才算数。
INT_H=$(find_idf "soc/esp32s3/include/soc/interrupts.h")
SOC_INC=$(dirname "$(dirname "$INT_H")")
# 计数用的临时目录放在系统 tmp，不进 build/——那会儿 cmake 还没配置过
CNT="${TMPDIR:-/tmp}/iram-count"; mkdir -p "$CNT"
# 枚举边界从文件里现读，不写死行号——换 IDF 版本时行号会挪，写死了就数错还看不出来
EB=$(grep -n '^typedef enum {' "$INT_H" | head -1 | cut -d: -f1)
EE=$(grep -n 'ETS_MAX_INTR_SOURCE' "$INT_H" | head -1 | cut -d: -f1)
[ -n "$EB" ] && [ -n "$EE" ] || { echo "认不出 $INT_H 的枚举边界" >&2; exit 1; }
awk -v a="$EB" -v b="$EE" 'NR>a && NR<b' "$INT_H" | grep -oE '^\s*ETS_[A-Z0-9_]+' | tr -d ' \t' > "$CNT/names.txt"
{
    cat <<'EOF'
#include <stdio.h>
#include "soc/interrupts.h"
int main(void){
EOF
    # puts("") 收尾而不是 \n：这段 C 源码是当场生成的，少一层转义就少一处炸
    awk '{ printf "    printf(\"%%3d  %%s\", (int)%s, \"%s\"); puts(\"\");\n", $1, $1 }' "$CNT/names.txt"
    cat <<'EOF'
    printf("%3d  %s", (int)ETS_MAX_INTR_SOURCE, "ETS_MAX_INTR_SOURCE ← 注释：number of interrupt sources"); puts("");
    return 0;
}
EOF
} > "$CNT/s.c"
gcc -I "$SOC_INC" "$CNT/s.c" -o "$CNT/s.exe"
"$CNT/s.exe" > "$CNT/vals.txt"
echo "  中断源枚举（编译器实测打印，不是数行）：$INT_H 第 $((EB + 1))–$((EE - 1)) 行"
sed -e 's/^/    /' "$CNT/vals.txt"
echo "  —— $(( $(wc -l < "$CNT/names.txt") )) 个名字，$(awk 'NF==2{print $1}' "$CNT/vals.txt" | sort -n -u | wc -l) 个不同编号，最后一行 99 是 ETS_MAX 本身"
awk 'NF==2 { u[$1] = 1 }
     END {
         gap = ""
         for (i = 0; i < 99; i++) if (!(i in u)) gap = gap " " i
         printf "    编号 0–98 里没有名字的几个（保留位）：%s\n", gap
     }' "$CNT/vals.txt"
awk 'NF == 2 { v[$1] = $1; n[$1] = n[$1] " " $2 }
     END { for (k in n) { c = split(n[k], a, " "); if (c > 1) printf "    同值别名：%s 同时是 %s\n", k, n[k] } }' "$CNT/vals.txt"

# 中断级别：源码里那句 "LEVELx 的值就是 (1<<level)" 是可以当场验的接口约定
echo "  中断级别标志（$ALLOC_H）："
grep -nE 'define ESP_INTR_FLAG_(LEVEL[1-6]|NMI)\b' "$ALLOC_H" \
    | sed -e 's/^[0-9]*:[[:space:]]*//' -e 's/^/    /'

echo "############ 2. idf.py build ############"
run_idf build > build.log 2>&1 || { echo "  构建失败，最后 30 行：" >&2; tail -30 build.log >&2; exit 1; }
echo "  构建完成（全量输出在 build.log）"

ELF=$(find build -name "iram-discipline.elf" | head -1)
MAP=$(find build -name "iram-discipline.map" | head -1)
[ -n "$ELF" ] && [ -f "$ELF" ] || { echo "没有 iram-discipline.elf" >&2; exit 1; }
# 取证用的 binutils 从构建自己的 CMakeCache 里认，不猜版本也不猜路径
BIN=$(tr -d '\r' < build/CMakeCache.txt | awk -F= '/^CMAKE_C_COMPILER_(AR|RANLIB):.*\.exe$/{print $2; exit}' | xargs dirname)
[ -d "$BIN" ] || { echo "从 build/CMakeCache.txt 认不出工具链目录（BIN=$BIN）" >&2; exit 1; }
resolve() {
    if [ -f "$BIN/$1.exe" ]; then printf '%s\n' "$BIN/$1.exe"
    elif command -v "$1" >/dev/null 2>&1; then command -v "$1"
    else echo "找不到 $1（构建用的编译器在 $BIN，那里没有它，PATH 里也没有）" >&2; exit 1
    fi
}
NM=$(resolve xtensa-esp-elf-nm)
OBJDUMP=$(resolve xtensa-esp-elf-objdump)
echo "  取证用的 binutils 目录：$BIN"

echo "############ 3. 链接器实际用的分区表（出自 $MAP 的 Memory Configuration） ############"
awk '/^Memory Configuration/{f=1;next} f&&/^Linker script and memory map/{exit}
     f&&/^[a-zA-Z_][a-zA-Z_0-9]*[[:space:]]+0x/{print $1, $2, $3}' "$MAP" > build/regions.txt
sed -e 's/^/  /' build/regions.txt
# 区间从上面这张表当场算，脚本里一个地址都不写死
has_region() { awk -v r="$1" '$1==r{f=1} END{exit !f}' build/regions.txt; }
IRAM_REG=iram0_0_seg; IROM_REG=iram0_2_seg; DROM_REG=drom0_0_seg
for r in $IRAM_REG $IROM_REG $DROM_REG; do
    has_region "$r" || { echo "分区表里没有 $r，断言无从下手" >&2; exit 1; }
done

echo "############ 4. nm 指认七个符号的落址，并按第 3 段的区间当场归类 ############"
addr_of() { $NM -n "$ELF" | awk -v s="$1" '$3 == s { print $1; exit }'; }
which_reg() { # 符号 地址(nm 给的裸 hex) → 命中哪个区（没命中打 ?）
    _a=$((0x$2))
    while read -r name org len; do
        _o=$((org)); _h=$((org + len))
        [ "$_a" -ge "$_o" ] && [ "$_a" -lt "$_h" ] && { printf '%s\n' "$name"; return; }
    done < build/regions.txt
    printf '?\n'
}
for s in $SYMS; do
    a=$(addr_of "$s")
    [ -n "$a" ] || { echo "  ❌ nm 里找不到 $s" >&2; exit 1; }
    printf '  0x%-8s  %-12s → %s\n' "$a" "$s" "$(which_reg "$s" "$a")"
done

echo "############ 5. 每个符号在 map 里真正落在哪个输入段 ############"
awk -v want="$SYMS" '
    BEGIN { n = split(want, w, " "); for (i = 1; i <= n; i++) { want_[w[i]] = 1; got[w[i]] = "(map 里没找到)"} }
    { raw = $0; sub(/^[ \t]+/, "", raw) }
    raw ~ /^[.*]/ && raw !~ /^\*fill\*/ { sec = raw; sub(/[ \t].*$/, "", sec) }
    raw ~ /^0x[0-9a-fA-F]+[ \t]+[^ \t]+$/ {
        split(raw, a, "[ \t]+"); s = a[2]
        if ((s in want_) && !seen[s]) { seen[s] = 1; got[s] = sec }
    }
    END { for (i = 1; i <= n; i++) printf "  %-12s  %s\n", w[i], got[w[i]] }
' "$MAP"

echo "############ 6. 实拆反汇编：四个 ISR 的整段指令，看跳转落在哪 ############"
$OBJDUMP -d "$ELF" > build/disasm.txt
awk 'BEGIN { split("isr_plain isr_leaky isr_tight isr_rodata", f, " "); for (i in f) want[f[i]] = 1 }
     /^[0-9a-f]+ </ { name = $2; sub(/^</, "", name); sub(/>:$/, "", name); show = (name in want); if (show) printf "\n  ── %s\n", $0; next }
     show && NF { printf "    %s\n", $0 }' build/disasm.txt

# 段名和地址之外，还要一句话把"链断没断"钉死：函数体里出现的 42xx/3cxx 目标地址就是 Flash
flash_refs() {
    awk -v fn="$1" '
        $0 ~ "^4?[0-9a-f]+ <" fn">:" { infn = 1; next }
        infn && /^[0-9a-f]+ </ { infn = 0 }
        infn { print }' build/disasm.txt | grep -oE '\((3|4)[0-9a-f]{7} <[^>]*>\)' | sort -u
}
for f in isr_leaky isr_tight isr_rodata; do
    printf '  %s 体内引用的绝对地址：%s\n' "$f" "$(flash_refs "$f" | tr '\n' ' ')"
done

echo "############ 7. idf.py size 的整本账 ############"
run_idf size 2>&1 | sed -e 's/^/  /' | tail -25

echo "############ 8. 断言（区间全部取自第 3 段那张表） ############"
fail=0
check() { # 符号 期望分区 人话
    _a=$(addr_of "$1")
    _r=$(which_reg "$1" "$_a")
    if [ "$_r" = "$2" ]; then
        printf '  ✅ %-12s 0x%s → %s（%s）\n' "$1" "$_a" "$2" "$3"
    else
        printf '  ❌ %-12s 0x%s 落在 %s，期望 %s（%s）\n' "$1" "$_a" "$_r" "$2" "$3"
        fail=1
    fi
}
check isr_plain   "$IROM_REG"  "不标 IRAM_ATTR → 留在 Flash，取指要靠 Cache"
check helper_far  "$IROM_REG"  "被 IRAM 里的 ISR 调用却没标 → 链子在这断了"
check isr_leaky   "$IRAM_REG"  "标了 IRAM_ATTR，自己确实在 IRAM"
check isr_tight   "$IRAM_REG"  "整条链都标 → 全程不碰 Flash"
check helper_near "$IRAM_REG"  "被 IRAM 调用且自己标了 → 在 IRAM"
check k_table     "$DROM_REG"  "函数进 IRAM 不等于常量也进 RAM，rodata 还在 Flash"

# 光看落址还不够：断链的现场在调用指令的目标地址里
leak=$(flash_refs isr_leaky | grep -oE '\((42|3c)[0-9a-f]{6}' | wc -l)
tight=$(flash_refs isr_tight | grep -oE '\((42|3c)[0-9a-f]{6}' | wc -l)
rod=$(flash_refs isr_rodata | grep -oE '\(3c[0-9a-f]{6}' | wc -l)
printf '  反汇编连带责任：isr_leaky 往 Flash 伸手 %s 处（应 >0，这就是断链）\n' "$leak"
printf '                   isr_tight 往 Flash 伸手 %s 处（应 =0）\n' "$tight"
printf '                   isr_rodata 读 DROM 常量 %s 处（应 >0）\n' "$rod"
[ "$leak" -gt 0 ] && [ "$tight" -eq 0 ] && [ "$rod" -gt 0 ] || fail=1

# 第 1 段挖出来的两个数也当堂对账：级别标志的位号必须等于级别号，源数量必须是 99
lvl_bad=0
for n in 1 2 3 4 5 6; do
    v=$(grep -E "define ESP_INTR_FLAG_LEVEL$n\b" "$ALLOC_H" | sed -n 's/.*(1<<\([0-9]*\)).*/\1/p')
    [ "$v" = "$n" ] || { printf '  ❌ LEVEL%s 的值是 1<<%s，不等于 %s\n' "$n" "$v" "$n"; lvl_bad=1; }
done
[ "$lvl_bad" = 0 ] && echo "  ✅ LEVEL1..6 的位号就是级别号（源码注释那句约定，当场验过）"
maxsrc=$("$CNT/s.exe" | grep ETS_MAX | tr -dc '0-9')
[ "$maxsrc" = 99 ] && echo "  ✅ ETS_MAX_INTR_SOURCE = $maxsrc（章节里那句 99 个源，编译器认这个数）" \
    || { printf '  ❌ ETS_MAX_INTR_SOURCE = %s，章节说的 99 对不上\n' "$maxsrc"; fail=1; }

[ "$fail" = 0 ] || { echo "断言未过：落址和 P4 章讲的纪律不一致，先查构建再改脚本（build/disasm.txt 留着给你查）" >&2; exit 1; }
rm -f build/regions.txt build/disasm.txt
echo "  ✅ 四条链各归各位：标了的在 IRAM，没标的在 Flash，常量在 DROM"
