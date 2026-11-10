"""Independent checks against source documents, not review.json."""

import hashlib
import json
import sys
import unittest
from pathlib import Path

from pypdf import PdfReader

from test_magazine_design_audit import EXPECTED_HASHES

ROOT = Path(__file__).resolve().parent
INVENTORY = json.loads((ROOT / "sources/source-inventory.json").read_text(encoding="utf-8"))
ORGANIZED = {
    "magazine_readme": "01-杂志说明.md",
    "magazine_intro": "02-杂志简介.md",
    "pixel_system": "03-黑白像素系统.md",
    "vi_design": "04-VI设计.md",
    "layout_system": "05-排版系统.md",
    "content_architecture": "06-内容架构.md",
    "web_layout": "07-网页风格排版.md",
    "chat_culture": "08-网聊文化融入.md",
    "page_designs": "09-页面设计.md",
    "print_guide": "10-印刷指南.md",
    "design_notes": "11-设计笔记.md",
}


def roots():
    for parent in ROOT.parents:
        candidate = parent / "toe-sylva-audit/papers/room_temp_sc"
        if candidate.is_dir():
            return candidate, candidate / "organized/11-杂志设计", candidate / "magazine"
    raise FileNotFoundError("room_temp_sc source root")


PAPER, DOCS, MAGAZINE = roots()
PATHS = {key: DOCS / name for key, name in ORGANIZED.items()}
PATHS.update({
    "generator": MAGAZINE / "generate_pdf.py",
    "delivery_report": MAGAZINE / "DELIVERY_REPORT.md",
    "file_index": MAGAZINE / "file_index.json",
    "checksums": MAGAZINE / "checksums.md5",
    "handbook_review": ROOT.parent / "handbook-chapters/review.json",
    "technical_review": ROOT.parent / "technical-docs/review.json",
})


def luminance(hex_color):
    channels = [int(hex_color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
    linear = [value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def contrast(foreground, background):
    high, low = sorted((luminance(foreground), luminance(background)), reverse=True)
    return (high + 0.05) / (low + 0.05)


class PrimarySourceTests(unittest.TestCase):
    def test_frozen_sources(self):
        self.assertEqual(len(INVENTORY["sources"]), 17)
        for source_id, expected in EXPECTED_HASHES.items():
            actual = hashlib.sha256(PATHS[source_id].read_bytes()).hexdigest()
            self.assertEqual(actual, expected, source_id)

    def test_lf_md5_lineage(self):
        expected = {}
        for line in PATHS["checksums"].read_text(encoding="utf-8").splitlines():
            value, filename = line.split(maxsplit=1)
            expected[value] = filename
        matched = 0
        for row in INVENTORY["lineage"]["rows"]:
            data = PATHS[row["organized_source_id"]].read_bytes().replace(b"\r\n", b"\n")
            actual = hashlib.md5(data).hexdigest()
            self.assertEqual(actual, row["expected_md5"])
            self.assertIn(actual, expected)
            self.assertFalse((MAGAZINE / row["original_name"]).exists())
            matched += 1
        self.assertEqual(matched, 7)

    def test_pdf_readonly_inventory(self):
        expected_pages = {
            "Sylva_Magazine_Complete.pdf": 108,
            "Sylva_Magazine_Full.pdf": 22,
            "Sylva_Magazine_RoomTempSC.pdf": 15,
            "Sylva_Magazine_Volume1.pdf": 118,
            "Sylva_Magazine_Volume2.pdf": 21,
            "Sylva_Magazine_Volume3.pdf": 7,
        }
        actual = {}
        for name in expected_pages:
            reader = PdfReader(MAGAZINE / name, strict=False)
            actual[name] = len(reader.pages)
            box = reader.pages[0].mediabox
            self.assertAlmostEqual(float(box.width) * 25.4 / 72, 210, places=3)
            self.assertAlmostEqual(float(box.height) * 25.4 / 72, 297, places=3)
            self.assertNotIn("/OutputIntents", reader.trailer["/Root"])
        self.assertEqual(actual, expected_pages)
        self.assertEqual(len(INVENTORY["assets"]["pdfs"]), 6)

    def test_generator_not_executed_and_not_complete(self):
        text = PATHS["generator"].read_text(encoding="utf-8")
        self.assertIn("content[:500]", text)
        for token in ("self.create_readme()", "self.create_design_notes()", "self.create_print_guide()"):
            self.assertIn(token, text)
        for name in ("vi_design.md", "layout_system.md", "content_architecture.md", "chat_culture_integration.md", "BLACK_WHITE_PIXEL_SYSTEM.md", "web_style_layout.md", "page_designs.md"):
            self.assertFalse((MAGAZINE / name).exists(), name)
        self.assertFalse(INVENTORY["generator"]["executed"])
        self.assertFalse(INVENTORY["generator"]["complete_magazine_generator"])

    def test_layout_and_page_arithmetic(self):
        layout = PATHS["layout_system"].read_text(encoding="utf-8")
        page = PATHS["page_designs"].read_text(encoding="utf-8")
        content = PATHS["content_architecture"].read_text(encoding="utf-8")
        self.assertIn("单栏宽度: 14mm", layout)
        self.assertIn("文本区域宽度: 174mm", layout)
        self.assertIn("栏宽: 11mm | 栏间距: 4mm", page)
        self.assertIn("165 × 252mm", page)
        self.assertEqual(12 * 14 + 11 * 4, 212)
        self.assertEqual(12 * 11 + 11 * 4, 176)
        self.assertAlmostEqual((174 - 11 * 4) / 12, 10.833333333333334)
        self.assertAlmostEqual((165 - 11 * 4) / 12, 10.083333333333334)
        self.assertIn("| **总计** | **60** |", content)
        self.assertIn("| 后台进程 | 14 |", content)
        self.assertEqual(sum((2, 2, 14, 10, 4, 3, 3, 6, 6, 6, 4)), 60)
        self.assertEqual(4 * 4, 16)
        self.assertIn("**页数**：106页", PATHS["magazine_intro"].read_text(encoding="utf-8"))

    def test_accessibility_recomputation(self):
        web = PATHS["web_layout"].read_text(encoding="utf-8")
        chat = PATHS["chat_culture"].read_text(encoding="utf-8")
        self.assertAlmostEqual(contrast("#B829DD", "#0A0A0F"), 4.137746343925)
        self.assertAlmostEqual(contrast("#606070", "#0A0A0F"), 3.202043685501)
        self.assertGreaterEqual(contrast("#00D9FF", "#0A0A0F"), 4.5)
        self.assertIn("正文对比度 ≥ 4.5:1", web)
        self.assertNotIn("prefers-reduced-motion", web)
        self.assertIn("长按触发", chat)
        self.assertNotIn("键盘长按", chat)

    def test_editorial_claims_and_prior_boundaries(self):
        intro = PATHS["magazine_intro"].read_text(encoding="utf-8")
        layout = PATHS["layout_system"].read_text(encoding="utf-8")
        page = PATHS["page_designs"].read_text(encoding="utf-8")
        chat = PATHS["chat_culture"].read_text(encoding="utf-8")
        content = PATHS["content_architecture"].read_text(encoding="utf-8")
        handbook = json.loads(PATHS["handbook_review"].read_text(encoding="utf-8"))
        self.assertIn("McMillan公式严格证明", intro)
        self.assertIn("13次重复实验", intro)
        self.assertIn("理论预测与实验误差仅6%", intro)
        self.assertIn("提升到99%以上", layout)
        self.assertIn("临界磁场", page)
        self.assertIn("155 GPa", page)
        self.assertIn("绝对安全", chat)
        self.assertIn("READY_FOR_PRODUCTION", content)
        self.assertFalse(handbook["open_boundaries"]["three_conditions_proven"])
        self.assertFalse(handbook["open_boundaries"]["experimental_necessity_proven"])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
