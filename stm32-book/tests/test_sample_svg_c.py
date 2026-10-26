from __future__ import annotations

import hashlib
import importlib.util
import re
import unittest
from pathlib import Path


BOOK_DIR = Path(__file__).resolve().parents[1]
REPO = BOOK_DIR.parent
BUILD_PATH = BOOK_DIR / "build_html.py"

ROWS = """
animations/adc-sar.svg 900x620 19409 ebd3127f7efde5d3c25f5a82dea6ae36eaff2a4c3a87c698f95f0d329a0ca807
animations/boot-sequence.svg 900x620 14058 d6d1baa08f2d9763ef5971f4701775db3905d34a7d6998310b127dd21beaddfc
animations/can-arbitration.svg 900x620 23362 6a68426929c8ad0f4046b091ae4be6db894eba2e4125f1e03c41c695167a3176
animations/clock-tree.svg 900x620 10921 c0e07c5c01bffae9769331541bdf87dcfc4ea61e3b4081b6f72834b476fbed08
animations/debug-swo.svg 900x620 12545 e44f13c22225782401c9b3d44f376781297c0103040118786626621476a6ffdd
animations/dma-circular.svg 900x620 16488 7deb7de9dc81e1a01c1c2e01827c131661f5b6d45bb5c2fb1d0473e126041fd1
animations/flash-iap.svg 900x620 12795 55ad4b20f25654a8bb6a705303a99d5fb513f5b125b70a4545278f84d63ad0cb
animations/freertos-scheduler.svg 900x620 15775 fe1bebd106b7c825a5d815edc67842821a8298e6e98036153641ca928c098bb3
animations/g0-boot-swd.svg 900x620 12398 e9121dfb6e5290afd5d192048fa7d7409a821c7651538c80bde3237df535155f
animations/gpio-blink.svg 900x620 14249 811377a9c3b65dd99cbeb8a1ff720b0e4e6410bc852726ac98f9aa20619175ea
animations/gpio-input-interrupt.svg 900x620 13740 4b97aeb339eb046f0091312b6caf918b1acdc176cc72e4295cc7c116792c6697
animations/i2c-transaction.svg 900x620 17483 e5c5b2aca2aae67cc607e3eb929cc0f20c184deceb8815f32a9d4e96f4bef55a
animations/iwdg-window.svg 900x620 10675 324f8c83215265a9e4b9c256552019165c14adb914c3fc9189f054f264751444
animations/l4-stop2-evidence.svg 900x620 13976 ae6b68a3a26ee3995d72dc29bcfcb2bab733a2e54637e4d9a6a8581b9f577e28
animations/lowpower-wakeup.svg 900x620 10766 7a5fe86d6e1a29c7f8e00d177f0ec928c85f7405e8427e8f27209720cc0a22b6
animations/memory-map.svg 900x620 7846 82e9be18ac7ecbe388e478b995ef9bcf8e876a2373406565469fda41e911b11f
animations/network-packet-journey.svg 900x620 18648 0081c4c6270e94527deba9ea9365811c22de28130ee343d8df68797eb36f1016
animations/nvic-interrupt-flow.svg 900x620 12972 07a38a7e7d4b430809683b2beb00f98b3cac0a17fc45bb1a5d066d20c22c9dc4
animations/rtos-system-layers.svg 900x620 13996 1a44f6f16dcc08a20467d946a35a22ef968582f37faf99b5b74f5107deaf31e9
animations/spi-transfer.svg 900x620 18861 579ddd86d159809dc4c667a0bf1faf652c1c0538d4d155f6f7187896df7a3968
animations/timer-modes.svg 900x620 11712 c8a1e34469293d5f4a02a5703271bcf62fc4e9f2f1e89429dbcaa02b56ebeabf
animations/timer-pwm.svg 900x620 10046 54833bf0841b1569cb993934699473b2ee4d2f0ed56b858a4fb9b5855bb8532f
animations/toolchain-flow.svg 900x620 15176 e131ad994e16c099c15d4d941c0e7aade4865c53c912248a73590e939645e0bd
animations/uart-frame.svg 900x620 18533 a696fc8932d337f1b22dacef54ecfe01dd37aa963b41d67111c584122f6b3400
animations/usb-enumeration.svg 900x620 10874 b531c1c1278ee8560a2a4297dd4f36e8dfb5934fc09f7df494faf9d5e455e20d
boards/blackpill-stm32f411ce.svg 900x620 32264 511d86c80d8862e78be2a0c7e6ca7e24e1db11d30ea66d47b3b2f1e8cdec0494
boards/bluepill-stm32f103c8t6.svg 900x620 35647 272634dc07da80d8c5d7e6471d9778310292318aace55acbecfcd92a8d9d4c25
boards/f103zet6-dev.svg 900x620 26509 8d52a625b72cef5f53be80091fc870d3bcf9537b0c178c5aa4ebfcb810ded612
boards/f4-discovery.svg 900x620 26524 d0d4d756b30de2d1a11a43bd78abd0f733dcf2696cc88f708de8cde63cfe659f
boards/nucleo-f411re.svg 900x620 21385 434fa875affbab6a0d987df16919de7b6cfaf88c3703da29593bef68b5006c8b
boards/peripheral-wiring.svg 900x620 13970 a5517214a0d7efcb8721fa41c8fee6224a7deca98f193bf39147ccc3f36fd166
boards/pinout-bluepill.svg 900x620 35176 4de478b58c8d278166311b99311183121ccf1ecb38a50c99450b35e60893cabd
boards/pinout-stm32g071rb-lqfp64.svg 620x750 34523 7ccc8b702e15d0473bfc1d4c956397dfbb5bd50363d4e762bd100c794d1d2193
boards/pinout-stm32h743zi-lqfp144.svg 840x970 75786 4d71ec5cab732513073bac6721ae4c688a36f18ab11fcae4b5e6e927433b7a96
boards/pinout-stm32l476rg-lqfp64.svg 620x750 34508 a5a8468d7b087956a4635ac7c88412f1e7920570c53e388e0a10a44fbe5f8adf
diagrams/interrupt-priority.svg 900x560 11877 7f3d8b282ed7342a56b598694137c3091ca4bd4a10acc73cd5a651a9b0c7fe05
diagrams/l4-idd-bench.svg 900x560 8673 32e1a5b195562947e04d2da8efc2f0c89dd97aed9f7cacbb3c5914ce52f8ec96
diagrams/layers-hal-ll-reg.svg 900x560 10401 60098b25b368c2f6acefb4e9a3152f816506cae44e68b2fb8ffbf0878c049f78
diagrams/network-debug-ladder.svg 900x560 11278 a1405054a5ba593090ad0bc6fdb104a5c8e513dd9695bd35767867faeeaec2e8
diagrams/peripheral-bus.svg 900x560 14071 80d659d44758f54a352b8447fb4a49e6fa880a47cb981bc487c1d69aaa6ae2f6
diagrams/project-structure.svg 900x560 13014 53f68cd4e58288a346e7cd09867724a75daa564e3b527a46a67627250def2acf
diagrams/sample-00-boot-state.svg 960x620 7103 41eff7ecd092c9f1d0e41629b4b87f337ea9d27e4b63f3ddda1d03e96c3eb3b1
diagrams/sample-01-swd-vectors.svg 960x980 7328 2e08712dfff9ee901d17be08e83d3496b7d34b02f3ddd73a7565d230a6291b56
diagrams/sample-02-clock-tree.svg 960x860 7402 41c1657ce8a1e34119ae2946ab5f10034fe5c83ef21fa50b4a1520861a1a98f2
diagrams/sample-03-gpio-led.svg 960x660 8221 932244c2053d317d50bf5106192a79fbf9d1546f16dd00bcf99110b7bd11a8ad
diagrams/sample-04-exception-stack.svg 960x780 7528 bc969846347daca2048bf5b355139a73f55e436f5c5779f9ac69a92e5d458d3e
diagrams/sample-05-pwm-1khz.svg 960x820 6845 48d92b03384bf3ac51e52c7d54c8a2bedd68b1a20ec405c21fbbc9287999217e
diagrams/sample-06-uart-frame.svg 960x820 12448 2da90d7d086d7eabf7a11f50cbe53f3387f1b0e3ed8b97b7781ff4a41be516ee
diagrams/sample-07-i2c-addr.svg 960x920 6620 5d8aeb4df50370a3885d46d17f086e582dab7875ce914911efb247b07e8d7e5a
diagrams/sample-08-spi-jedec.svg 960x860 6850 717ba67544302d5517bffdbfe23deec414d5f52c49993a9eba0260fd4952fd4c
diagrams/sample-09-adc-sar.svg 960x860 6656 3d193aa429c4f707ea7f82cf4e6e44c2f128bc032e59d43a7e2334c5882dc65e
diagrams/sample-10-dma-cndtr.svg 960x900 6552 6a887f553de8b9d8744527a71b0c86217ccbea32b2f4f65ff3519f519cfb92f5
diagrams/sample-11-iwdg-1s.svg 960x980 7169 226d77d6f316c4b5ce1a1580507c95b96d69a8c3a35f7601475794dc279b18eb
diagrams/sample-12-iap-map.svg 960x980 7450 017cfc1406a5ad4843bcdf80666eaa5636e3186fa60008f61cef514cf26f60dd
diagrams/sample-13-can-bit.svg 960x980 7175 0e1da8a54f67b46946b959799eb301cf07baa63b6494fd196c00cc6514654cc8
diagrams/sample-14-usb-enum.svg 960x980 7101 a6cf18d79c5d09d0257f7c8a210c9a82df4387dfac9b1239fdc1df46359bd93b
diagrams/sample-15-rtos-prio.svg 960x960 6794 a6c5ccb5affa24af61ec70b68a8fff13810af20309f0a3cf1549a59b3b24a842
diagrams/sample-16-stop-wake.svg 960x980 7143 41341af8f070f2b9413b8d4fc6f3dff0d5c6afc2d767d5a36b656a1c17ef3ac4
diagrams/sample-17-cfsr.svg 960x980 6727 5afb78ba8d0be29fa1bbfd8c497919296d991d9112ee2eae24f89fd9413b4d6d
diagrams/sample-18-boot-triage.svg 960x960 6512 ab5be4eb7af108fbd513303dd1d1bf4ab24978018966c98fa80fcb46a9d83091
diagrams/sample-19-flash-fit.svg 960x980 6499 d2cf0662543657786e0dc4d3341cffdffe459035fb80771ffc5b3fe474e7cc42
""".strip().splitlines()

SEMANTIC = {
    "#fbfaf7",
    "#f1f5f7",
    "#e5f3f8",
    "#5e6872",
    "#d7dce1",
    "#17202a",
    "#075e84",
    "#1e4d63",
    "#1b5c45",
    "#7a4e00",
    "#9a3412",
    "#8f2d2d",
    "#5b3a8c",
    "#8e2f5b",
}
PARTS = {
    "#00000055",
    "#00000066",
    "#00000088",
    "#08214a",
    "#08224a",
    "#0a0d13",
    "#0a1f5e",
    "#0a2a52",
    "#0b2c4c",
    "#0c0f16",
    "#0c2242",
    "#0d2b22",
    "#0e3b6e",
    "#0f2f8a",
    "#0f3f6b",
    "#123057",
    "#123a2e",
    "#141821",
    "#151922",
    "#153a9e",
    "#1b1f28",
    "#1d4ed8",
    "#2a3242",
    "#2b3038",
    "#39424f",
    "#4a5260",
    "#59606c",
    "#5b6472",
    "#5d6470",
    "#7aa2ff",
    "#7fd4ff",
    "#808a9a",
    "#8b98b0",
    "#8d7420",
    "#8d949e",
    "#9aa4b2",
    "#9db8ff",
    "#bcd8ff",
    "#c4b5fd",
    "#c9ced6",
    "#cfe0ff",
    "#d8b23a",
    "#dbeafe",
    "#dfe6f0",
    "#e2b23c",
    "#e7ebf0",
    "#e8f1ff",
    "#ffffff22",
}
ALLOWED = SEMANTIC | PARTS | {"#ffffff"}
BANNED = {
    "#0b1220",
    "#0e1626",
    "#111c31",
    "#16233c",
    "#243354",
    "#1a2742",
    "#e6edf3",
    "#93a4c0",
    "#64748b",
    "#22d3ee",
    "#60a5fa",
    "#34d399",
    "#fbbf24",
    "#fb923c",
    "#f87171",
    "#a78bfa",
    "#f472b6",
    "#f8fafc",
    "#c4552a",
    "#9a3d1c",
}
SOURCE_FILES = (
    "tools/svgkit.py",
    "tools/gen_sample_figures.py",
    "tools/gen_diagrams.py",
    "tools/anim_basics.py",
    "tools/anim_gpio.py",
    "tools/anim_comm.py",
    "tools/anim_sys.py",
    "tools/gen_boards.py",
    "tools/gen_pinouts.py",
)


def load_builder():
    spec = importlib.util.spec_from_file_location("stm32_book_builder", BUILD_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load builder: {BUILD_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def text_hash(svg: str) -> str:
    parts = re.findall(r"<text\b[^>]*>(.*?)</text>", svg, flags=re.DOTALL)
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


class SampleSvgCTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.builder = load_builder()

    def test_sample_svg_c_contract(self) -> None:
        self.assertEqual(
            "98c0de3fa53e331b308db6d8f094aab76ec7b11159a1056fc16fd6acd7dce025",
            hashlib.sha256(self.builder.CSS.encode("utf-8")).hexdigest(),
        )
        self.assertEqual(
            "9d07dad497b824c9e2038ddf1e28cb77974451acb6c3b9773863df7c8c90d0bd",
            hashlib.sha256((BOOK_DIR / "styles" / "tokens.json").read_bytes()).hexdigest(),
        )
        self.assertEqual(
            "fe03b80f2e50acf03bc17e0950e8aad52c4c90bb418b40956612de9bc719a942",
            hashlib.sha256((BOOK_DIR / "styles" / "book.css").read_bytes()).hexdigest(),
        )
        self.assertEqual(
            "37dbedd70d2be8e94f4cdf05b60541f69d0107af6374902f8062c8e0bf74dedd",
            hashlib.sha256((BOOK_DIR / "cover.svg").read_bytes()).hexdigest(),
        )

        found = sorted(
            path.relative_to(REPO / "assets").as_posix()
            for path in (REPO / "assets").rglob("*.svg")
        )
        expected = []
        for line in ROWS:
            rel, wh, _old_size, digest = line.split()
            width, height = (int(part) for part in wh.split("x"))
            expected.append(rel)
            path = REPO / "assets" / rel
            raw = path.read_bytes()
            text = raw.decode("utf-8")
            limit = 80 * 1024 if rel.endswith("pinout-stm32h743zi-lqfp144.svg") else 60 * 1024
            self.assertLess(len(raw), limit, rel)
            attrs = re.search(r"<svg\b([^>]*)>", text)
            self.assertIsNotNone(attrs, rel)
            self.assertEqual(str(width), re.search(r'\bwidth="(\d+)"', attrs.group(1)).group(1), rel)
            self.assertEqual(str(height), re.search(r'\bheight="(\d+)"', attrs.group(1)).group(1), rel)
            self.assertIn(f'viewBox="0 0 {width} {height}"', text, rel)
            self.assertEqual(digest, text_hash(text), rel)
            colors = {
                item.lower()
                for item in re.findall(
                    r"#(?:[0-9A-Fa-f]{8}|[0-9A-Fa-f]{6})(?![0-9A-Fa-f])",
                    text,
                )
            }
            self.assertFalse(colors - ALLOWED, (rel, sorted(colors - ALLOWED)))
            self.assertFalse(colors & BANNED, rel)
            strokes = set(re.findall(r'stroke-width="([^"]+)"', text))
            self.assertTrue(strokes <= {"1", "1.5", "2"}, (rel, strokes))
            self.assertFalse("stroke-width:" in text, rel)
            radii = set(re.findall(r'\brx="([^"]+)"', text))
            self.assertTrue(radii <= {"2", "4", "8"}, (rel, radii))
            if Path(rel).name.startswith("sample-"):
                self.assertNotIn("<animate", text, rel)
                self.assertNotIn("@keyframes", text, rel)
                self.assertNotIn("animation:", text, rel)
                self.assertNotIn("矢量动画", text, rel)
                self.assertIn("自绘", text, rel)
            else:
                self.assertIn("自绘矢量动画", text, rel)
        self.assertEqual(expected, found)
        self.assertEqual(61, len(found))

        i2c = (REPO / "assets" / "animations" / "i2c-transaction.svg").read_text(encoding="utf-8")
        self.assertNotIn("<style", i2c)
        self.assertNotIn("<animate", i2c)

        gifs = sorted((REPO / "assets" / "gif").glob("*.gif"), key=lambda path: path.name)
        self.assertEqual(48, len(gifs))
        listing = "".join(
            f"{path.name} {hashlib.sha256(path.read_bytes()).hexdigest()}\n"
            for path in gifs
        )
        self.assertEqual(
            "f33185dc945c57ba1f4ac6e17a8ac5b218fee3ee0f85b5ffddf8080ec74d3b3a",
            hashlib.sha256(listing.encode("utf-8")).hexdigest(),
        )

        svgkit = (REPO / "tools" / "svgkit.py").read_text(encoding="utf-8")
        self.assertIn('BG = "#fbfaf7"', svgkit)
        self.assertIn('CYAN = "#075e84"', svgkit)
        self.assertNotIn("WHITE", svgkit)
        self.assertNotIn("#0b1220", svgkit)
        self.assertNotIn("#22d3ee", svgkit)
        self.assertIn("PingFang SC", svgkit)
        self.assertIn("Hiragino Sans GB", svgkit)

        for rel in SOURCE_FILES:
            source = (REPO / rel).read_text(encoding="utf-8")
            self.assertNotIn('fill="#0b1220"', source, rel)
            self.assertNotIn("T.WHITE", source, rel)
        sample_src = (REPO / "tools" / "gen_sample_figures.py").read_text(encoding="utf-8")
        self.assertNotIn("rx=10", sample_src)
        self.assertNotIn("rx=6", sample_src)


if __name__ == "__main__":
    unittest.main()
