"""Regression checks for technical figure text staying on-canvas."""
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
TRACK = ROOT / "tools" / "handraw_track"
sys.path.insert(0, str(TRACK))

import fig_ch32  # noqa: E402
from hd import H, W, text_w  # noqa: E402

TUNING_STEPS = [
    ("1 极性/CPR 确认", "手转方向与符号一致", "回第 31 章查接线"),
    ("2 开环扫速域", "20–400 rpm 可控", "降负载/查限流"),
    ("3 Ki=0 升 Kp", "变快不持续振荡", "振荡→Kp 减半"),
    ("4 小幅加 Ki", "静差收敛无低频摆动", "摆动→Ki 减半"),
    ("5 饱和恢复", "深阶跃退出无大超调", "调 i_limit/条件积分"),
    ("6 重做阶跃/扰动/反转", "指标与重复性达标", "回第 3 步"),
]


class HandrawLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._playwright = sync_playwright().start()
        cls.browser = cls._playwright.chromium.launch()
        cls.page = cls.browser.new_page(viewport={"width": 1180, "height": 900})

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls._playwright.stop()

    def _load_figure(self, figure):
        self.page.set_content(figure.svg())
        self.page.evaluate("document.fonts.ready")

    def test_ch32_pi_step_text_fits_canvas_width(self):
        root = ET.fromstring(fig_ch32.pi_step().svg())
        anchor_offsets = {"start": 0, "middle": 0.5, "end": 1}
        for node in root.iter("{http://www.w3.org/2000/svg}text"):
            text = "".join(node.itertext())
            x = float(node.attrib["x"])
            width = text_w(text, float(node.attrib["font-size"]))
            left = x - width * anchor_offsets[node.get("text-anchor", "start")]
            with self.subTest(text=text):
                self.assertGreaterEqual(left, 0)
                self.assertLessEqual(left + width, W)


    def test_ch32_tuning_ladder_text_stays_inside_cards(self):
        self._load_figure(fig_ch32.tuning_ladder())
        geometry = self.page.evaluate(
            """() => {
              const box = el => {
                const b = el.getBBox();
                return {x: b.x, y: b.y, width: b.width, height: b.height,
                        right: b.x + b.width, bottom: b.y + b.height};
              };
              const cards = [...document.querySelectorAll("path")]
                .filter(el => el.getAttribute("fill") === "#FFFFFF")
                .map(box)
                .filter(b => b.width >= 170 && b.width <= 600 &&
                             b.height >= 75 && b.height <= 95 &&
                             b.y >= 130 && b.y <= 730)
                .sort((a, b) => Math.round(a.y / 100) - Math.round(b.y / 100) || a.x - b.x);
              const texts = [...document.querySelectorAll("text")]
                .map(el => ({text: el.textContent, ...box(el)}));
              const rows = [];
              for (let i = 0; i < cards.length; i += 3) {
                const rowCards = cards.slice(i, i + 3);
                const owned = [];
                for (const text of texts) {
                  const cx = text.x + text.width / 2;
                  const cy = text.y + text.height / 2;
                  const cardIndex = rowCards.findIndex(card =>
                    cx >= card.x && cx <= card.right &&
                    cy >= card.y && cy <= card.bottom);
                  if (cardIndex < 0) continue;
                  const card = rowCards[cardIndex];
                  owned.push({...text, cardIndex,
                    padding: Math.min(text.x - card.x,
                                      card.right - text.right,
                                      text.y - card.y,
                                      card.bottom - text.bottom)});
                }
                rows.push({cards: rowCards, texts: owned});
              }
              return {cards, texts, rows};
            }"""
        )
        self.assertEqual(len(geometry["cards"]), 18)
        for text in geometry["texts"]:
            with self.subTest(text=text["text"], boundary="canvas"):
                self.assertGreaterEqual(text["x"], 4)
                self.assertGreaterEqual(text["y"], 4)
                self.assertLessEqual(text["right"], W - 4)
                self.assertLessEqual(text["bottom"], H - 4)
        for card in geometry["cards"]:
            with self.subTest(card=card, boundary="canvas"):
                self.assertGreaterEqual(card["x"], 4)
                self.assertGreaterEqual(card["y"], 4)
                self.assertLessEqual(card["right"], W - 4)
                self.assertLessEqual(card["bottom"], H - 4)

        self.assertEqual(len(geometry["rows"]), len(TUNING_STEPS))
        for row_index, (row, expected) in enumerate(
                zip(geometry["rows"], TUNING_STEPS), start=1):
            name, ok, back = expected
            self.assertEqual(len(row["cards"]), 3)
            by_card = {index: [] for index in range(3)}
            for text in row["texts"]:
                by_card[text["cardIndex"]].append(text)
                with self.subTest(row=row_index, text=text["text"], boundary="card"):
                    self.assertGreaterEqual(text["padding"], 12)
            self.assertEqual([text["text"] for text in by_card[0]], [name])
            self.assertEqual([text["text"] for text in by_card[1]], [ok])
            fallback = "".join(text["text"] for text in by_card[2])
            fallback = fallback.replace(" ", "").replace("：", ":")
            self.assertEqual(fallback, ("回退:" + back).replace(" ", ""))

    def test_ch32_state_machine_arrow_clears_timeout_label(self):
        self._load_figure(fig_ch32.state_machine())
        geometry = self.page.evaluate(
            """() => {
              const box = el => {
                const b = el.getBBox();
                return {x: b.x, y: b.y, width: b.width, height: b.height,
                        right: b.x + b.width, bottom: b.y + b.height};
              };
              const texts = [...document.querySelectorAll("text")]
                .map(el => ({text: el.textContent,
                             baseline: +el.getAttribute("y"), ...box(el)}));
              const labelEl = [...document.querySelectorAll("text")]
                .find(el => el.textContent === "3s 超时 / 故障位");
              const label = box(labelEl);
              const candidates = [...document.querySelectorAll("path")]
                .filter(el => {
                  const b = box(el);
                  return el.getAttribute("stroke") === "#B3392F" &&
                         el.getAttribute("fill") === "none" &&
                         b.width > 250 && b.height < 100;
                })
                .map(el => ({el, opacity: el.getAttribute("opacity")}));
              const shaft = candidates.find(item =>
                item.opacity === null || +item.opacity === 1).el;
              const length = shaft.getTotalLength();
              const start = shaft.getPointAtLength(0);
              const end = shaft.getPointAtLength(length);
              let insideCount = 0;
              let minDistance = Infinity;
              for (let distance = 0; distance <= length; distance += 0.25) {
                const point = shaft.getPointAtLength(distance);
                const dx = Math.max(label.x - point.x, 0,
                                    point.x - label.right);
                const dy = Math.max(label.y - point.y, 0,
                                    point.y - label.bottom);
                const gap = Math.hypot(dx, dy);
                if (gap === 0) insideCount += 1;
                minDistance = Math.min(minDistance, gap);
              }
              return {texts, labelText: labelEl.textContent,
                      baseline: +labelEl.getAttribute("y"), label,
                      start: {x: start.x, y: start.y},
                      end: {x: end.x, y: end.y}, insideCount, minDistance};
            }"""
        )
        self.assertEqual(geometry["labelText"], "3s 超时 / 故障位")
        self.assertEqual(geometry["baseline"], 410)
        self.assertGreater(geometry["start"]["x"], geometry["end"]["x"])
        self.assertAlmostEqual(geometry["start"]["y"], geometry["end"]["y"], places=1)
        self.assertEqual(geometry["insideCount"], 0)
        self.assertGreaterEqual(geometry["minDistance"], 8)
        for text in geometry["texts"]:
            with self.subTest(text=text["text"], boundary="canvas"):
                self.assertGreaterEqual(text["x"], 4)
                self.assertGreaterEqual(text["y"], 4)
                self.assertLessEqual(text["right"], W - 4)
                self.assertLessEqual(text["bottom"], H - 4)

if __name__ == "__main__":
    unittest.main()
