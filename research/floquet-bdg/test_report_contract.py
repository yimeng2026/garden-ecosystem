"""Delivery contracts for the numerical Floquet-BdG Markdown and native Word report."""

import json
import sys
import unittest
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent


class FloquetBdGReportTests(unittest.TestCase):
    def test_actual_figure_and_markdown_boundaries(self):
        with Image.open(ROOT / "quasienergy.png") as image:
            self.assertGreater(image.width, 1200)
            aspect = image.width / image.height
            # Tight bounding boxes legitimately change the original canvas ratio.
            self.assertGreater(aspect, 1.4)
            self.assertLess(aspect, 1.6)
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for required in ("π 模", "0 模", "inconclusive", "supported_finite_size", "静态平凡控制", "没有 Fourier 截断", "不是材料", "独立稀疏"):
            self.assertIn(required, text)
        data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
        self.assertEqual(data["convergence"]["zero"]["finite_size_status"], "inconclusive")
        self.assertEqual(data["convergence"]["pi"]["finite_size_status"], "supported_finite_size")

    def test_native_word_package_and_citations(self):
        import xml.etree.ElementTree as ET

        with zipfile.ZipFile(ROOT / "REPORT.docx") as package:
            names = package.namelist()
            document = package.read("word/document.xml")
            header = b"".join(package.read(name) for name in names if name.startswith("word/header") and name.endswith(".xml"))
            footer = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
            footnotes = package.read("word/footnotes.xml")
            self.assertIn(b"TOC", document)
            self.assertIn(b"<m:oMath", document)
            self.assertGreaterEqual(document.count(b"<w:tbl>"), 4)
            self.assertGreaterEqual(document.count(b"cantSplit"), 10)
            self.assertIn(b"PAGE", footer)
            self.assertNotIn(b"NUMPAGES", footer)
            self.assertIn("Floquet-BdG".encode(), header)
            self.assertTrue(any(name.startswith("word/media/") for name in names))
        for source in (b"1303.2300", b"2203.16353", b"results.json"):
            self.assertIn(source, footnotes)
        root = ET.fromstring(document)
        extent = root.find(".//{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}extent")
        self.assertIsNotNone(extent)
        embedded_aspect = int(extent.attrib["cx"]) / int(extent.attrib["cy"])
        with Image.open(ROOT / "quasienergy.png") as image:
            self.assertAlmostEqual(embedded_aspect, image.width / image.height, delta=0.002)
        data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
        visible = document.decode("utf-8")
        for target in ("zero", "pi"):
            difference = data["dense_sparse_comparison"][target]["max_absolute_difference"]
            self.assertIn(f"{difference:.6e}", visible, f"stale Word value for {target}")


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
