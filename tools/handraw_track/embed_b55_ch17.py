# -*- coding: utf-8 -*-
"""B55: embed four chapter 17 knowledge plates, bottom-up (4 -> 1).

Each anchor is a full source line and must appear exactly once in its doc.
"""
import subprocess
from pathlib import Path

from embed import embed_after_text

ROOT = Path(__file__).resolve().parents[2]

SPECS = [
    # 4. ch17-fault-record — recipe ④ intro paragraph, above its code fence
    ("docs/17-调试与性能优化.md",
     "这版用于已验证栈帧和日志通道的受控调试。故障现场里的 `printf` 可能阻塞、再次触发异常或使用已损坏的栈；正式故障记录应先保存固定长度数据，再在安全环境输出。",
     "ch17-fault-record.png",
     "Handraw：先存记录的故障记录器（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：异常入口后的四步——先存定长记录（栈 PC/LR、CFSR/HFSR、有效位、ELF 哈希），再离场，最后在安全环境输出并配 addr2line；证明什么：故障现场的 printf 可能阻塞、再次异常或用到已损坏的栈，记录必须先于输出；不能证明什么：不是某次 HardFault 的实录，记录能否留存取决于存放位置与复位方式。出处：[PM0056](#source-pm0056)。"),
    ("docs/en/17-debug.md",
     "Use this version in controlled debugging after checking the frame and log channel. A fault-time `printf` can block, fault again, or use an already damaged stack. A deployed fault recorder should first save a fixed amount of data, then output it in a safe context.",
     "ch17-fault-record.png",
     "Handraw: save-first fault recorder (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: the four steps after exception entry — save a fixed-length record (stacked PC/LR, CFSR/HFSR, valid flags, ELF hash), leave the handler, then print in a safe context and run addr2line; Proves a fault-time printf can block, fault again, or use an already damaged stack, so the record comes before any output; Cannot show a real HardFault capture, and survival depends on where the record is stored and how the part resets. See [PM0056](#source-pm0056)."),

    # 3. ch17-recover-ladder — hardware/wiring paragraph, before the WARNING
    ("docs/17-调试与性能优化.md",
     "表中 3V3 在探针端通常是目标电压参考 VTref，是否兼作供电要查具体探针；不要把两个电源输出直接相连。SWO 支持也不限于表中两个型号，仍需核对具体硬件、固件和接线。Nucleo 的 SWO 路径是否连通，应按板卡版本与焊桥配置确认。",
     "ch17-recover-ladder.png",
     "Handraw：连不上时的四级恢复阶梯（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：共地并给 VTref → 接 NRST 复位下连接 → 保留 SWD 引脚 → 按启动配置进系统存储器；证明什么：先补电气前提与复位时序，应用关掉调试时最后才用启动配置让它不跑；不能证明什么：不是某块板或某支探针的连接实测，能否连上仍取决于固件、探针和接线。出处：[DS5319](#source-ds5319-swd)、[PM0056](#source-pm0056)。"),
    ("docs/en/17-debug.md",
     "The probe's 3V3 connection is usually target-voltage reference VTref; check the specific probe before using it as a power source. Do not connect two power outputs together. SWO support is not limited to the two models in the table: check the actual hardware, firmware, and wiring. On a Nucleo, verify the SWO route against the board revision and solder bridges.",
     "ch17-recover-ladder.png",
     "Handraw: the four-step recovery ladder (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: the four-step ladder — common GND with VTref, NRST for connect under reset, SWD kept on PA13/PA14, and the boot configuration that enters system memory; Proves the electrical prerequisites and reset timing come first, with the boot configuration as the last resort when the application disables debug; Cannot show a real attach on any board or probe, which still depends on firmware, probe and wiring. See [DS5319](#source-ds5319-swd), [PM0056](#source-pm0056)."),

    # 2. ch17-comp-pools — final row of the timing/state table
    ("docs/17-调试与性能优化.md",
     "| 脚位 | 第 34 脚 PA13，第 37 脚 PA14 | SWD。第 39 脚 PB3 默认 JTDO |",
     "ch17-comp-pools.png",
     "Handraw：FPB 与 DWT 两个比较器池（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：两个互不共享名额的池子——FPB 的 6 个指令地址比较器与 DWT 的 4 个数据地址比较器；证明什么：断点与观察点分开计数，条件断点仍占 1 个 FPB 名额，第 7 个代码断点只能先释放旧断点；不能证明什么：不是本机占用实测，软件断点（BKPT）和 M7 的 8 个都不在这两个池子里。出处：[PM0056 DWT](#source-pm0056-dwt)。"),
    ("docs/en/17-debug.md",
     "| Pins | pin 34 PA13, pin 37 PA14 | SWD. Pin 39 PB3 is JTDO by default |",
     "ch17-comp-pools.png",
     "Handraw: the FPB and DWT comparator pools (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: two pools that never share slots — the FPB's 6 instruction-address comparators and the DWT's 4 data-address comparators; Proves the budgets count separately, a conditional hardware breakpoint still takes one FPB slot, and a 7th code breakpoint means releasing an old one; Cannot show this chip's real occupancy, and neither pool counts a software BKPT or an M7's 8 comparators. See [PM0056 DWT](#source-pm0056-dwt)."),

    # 1. ch17-stack-frame — principle paragraph after the frame sentence
    ("docs/17-调试与性能优化.md",
     "正常完成异常压栈后，基本栈帧依次为 R0、R1、R2、R3、R12、LR、PC、xPSR。以 R0 为第 0 个字，PC 在 `stack[6]`，即该栈帧起点 SP + 0x18。`PRECISERR` 对应的 PC 指向出错指令；`IMPRECISERR` 的 PC 可能已经越过原始写操作。若有 `STKERR` 或 `MSTKERR`，压栈可能不完整，应先核对栈地址与内容，不能直接解引用。",
     "ch17-stack-frame.png",
     "Handraw：异常栈帧八格与 PC 位置（原理示意）",
     "▲ 知识轨（Handraw · 原理示意/非实拍）。看哪里：八格栈帧卡 R0–R3、R12、LR、PC、xPSR，PC 在第 6 格、帧首 +0x18；证明什么：只有帧完整且故障类型支持时 PC 才指向出错指令，PRECISERR 指向原指令，IMPRECISERR 可能已越过原始写，STKERR/MSTKERR 要先核对栈；不能证明什么：不是某次故障的实测栈内容，帧是否完整仍由 CFSR 与栈地址判定。出处：[PM0056](#source-pm0056)。"),
    ("docs/en/17-debug.md",
     "After exception stacking completes normally, the basic frame contains R0, R1, R2, R3, R12, LR, PC, xPSR. Counting R0 as word 0, PC is `stack[6]`, or SP + 0x18 from the start of that frame. For `PRECISERR`, PC points to the faulting instruction; with `IMPRECISERR`, it may have advanced past the original write. `STKERR` or `MSTKERR` means the frame might be incomplete: check its address and contents before dereferencing it.",
     "ch17-stack-frame.png",
     "Handraw: the eight-word exception frame and where PC sits (原理示意)",
     "▲ Knowledge track (Handraw · 原理示意 / not a photo). Where to look: the eight-word frame card (R0–R3, R12, LR, PC, xPSR) with PC as word 6 at frame start + 0x18; Proves PC locates the faulting instruction only when the frame is complete and the fault type supports it — PRECISERR points at it, IMPRECISERR may have advanced, STKERR/MSTKERR needs the stack checked first; Cannot show any one fault's real stack contents, and completeness still comes from CFSR and the stack address. See [PM0056](#source-pm0056)."),
]


def check_anchor(doc: str, anchor: str) -> None:
    """grep -Fxc -- <anchor> <doc> must report exactly 1."""
    path = ROOT / doc
    res = subprocess.run(
        ["grep", "-Fxc", "--", anchor, str(path)],
        capture_output=True, text=True, encoding="utf-8",
    )
    count = (res.stdout or "").strip()
    if res.returncode not in (0, 1) or count != "1":
        raise SystemExit(
            f"STOP {doc}: grep -Fxc count={count!r} rc={res.returncode} "
            f"for anchor: {anchor[:70]}..."
        )
    print(f"CHECK {doc}: anchor appears exactly once")


if __name__ == "__main__":
    for spec in SPECS:
        check_anchor(spec[0], spec[1])
    bad = 0
    for spec in SPECS:
        if not embed_after_text(*spec):
            bad += 1
    if bad:
        raise SystemExit(f"{bad} embed(s) failed")
