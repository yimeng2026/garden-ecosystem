"""Contracts for N=160 registry, size trends, native Word, and visual hashes."""

import hashlib
import json
import sys
import unittest
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-TBC有限尺寸报告.docx"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class FiniteSizeReportTests(unittest.TestCase):
    def test_registry_and_independent_counts(self):
        finite = json.loads((ROOT / "finite_size_zero.json").read_text(encoding="utf-8"))
        independent = json.loads((ROOT / "finite_size_independent.json").read_text(encoding="utf-8"))
        self.assertTrue(finite["complete"])
        self.assertEqual(len(finite["rows"]), 11)
        self.assertTrue(all(row["zero"]["status"] == "ok" and row["zero"]["nearest_integer"] == 1 for row in finite["rows"]))
        self.assertEqual(independent["selected_count"], 7)
        self.assertTrue(independent["passed"])
        self.assertTrue(all(row["integer_agreement"] for row in independent["checks"]))

    def test_size_trend_table(self):
        from build_finite_size_report import trend
        expected = {
            (0.05, 80): 0, (0.05, 160): 0, (0.05, 320): 2,
            (0.1, 80): 0, (0.1, 160): 0, (0.1, 320): 1,
            (0.2, 80): 0, (0.2, 160): 4, (0.2, 320): 4,
        }
        for key, count in expected.items():
            self.assertEqual(trend(*key)["pass_count"], count)

    def test_markdown_and_figures_preserve_missing_n320(self):
        text = (ROOT / "FINITE_SIZE.md").read_text(encoding="utf-8")
        self.assertIn("N=320 的 TBC winding 尚未计算", text)
        self.assertIn("全部 11 个主积分结果有效", text)
        self.assertIn("r=0.05、seed=2/3", text)
        for name in ("finite-size-winding.png", "finite-size-endpoints.png"):
            with Image.open(ROOT / name) as image:
                self.assertGreater(image.width, 1200)
                self.assertGreater(image.height, 800)

    def test_docx_native_structure(self):
        with zipfile.ZipFile(DOCX) as package:
            document = package.read("word/document.xml").decode("utf-8")
            footers = "".join(package.read(name).decode("utf-8") for name in package.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            media = [name for name in package.namelist() if name.startswith("word/media/") and not name.endswith("/")]
        self.assertIn("m:oMath", document)
        self.assertIn("TOC", document)
        self.assertIn("cantSplit", document)
        self.assertIn("PAGE", footers)
        self.assertNotIn("NUMPAGES", footers)
        self.assertEqual(len(media), 2)

    def test_visual_hash_binding(self):
        report = json.loads((ROOT / "finite-word-qa" / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["rendered"], 4)
        self.assertEqual(report["manualReview"]["status"], "passed")
        self.assertEqual(report["finalValidation"]["docxSha256"], sha(DOCX))
        for name, expected in report["sourceSha256"].items():
            self.assertEqual(sha(ROOT / name), expected)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
