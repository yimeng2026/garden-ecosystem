"""Contracts for N=400 threshold data, native Word, and visual hashes."""

import hashlib
import json
import sys
import unittest
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-N400阈值诊断报告.docx"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ScaleReportTests(unittest.TestCase):
    def test_n400_result_and_independent_agreement(self):
        data = json.loads((ROOT / "scale_diagnostic.json").read_text(encoding="utf-8"))
        independent = json.loads((ROOT / "scale_independent_n400.json").read_text(encoding="utf-8"))
        self.assertTrue(data["n400_complete"])
        self.assertEqual({row["n"] for row in data["rows"]}, {400, 600})
        row = next(row for row in data["rows"] if row["n"] == 400)
        self.assertEqual(row["zero"]["status"], "ok")
        self.assertEqual(row["zero"]["nearest_integer"], 1)
        self.assertTrue(row["endpoint"]["zero"]["joint_pass"])
        self.assertTrue(independent["integer_agreement"])
        self.assertEqual(independent["independent"]["nearest_integer"], 1)

    def test_coverage_metrics_preserve_tail_distinction(self):
        metrics = json.loads((ROOT / "n400_scale.json").read_text(encoding="utf-8"))
        self.assertEqual(metrics["L50"], 24)
        self.assertEqual(metrics["L90"], 133)
        self.assertLess(metrics["envelope"]["r_squared"], 0.5)
        self.assertGreater(metrics["edge_weight"], 0.5)

    def test_markdown_and_figures(self):
        text = (ROOT / "SCALE_DIAGNOSTIC.md").read_text(encoding="utf-8")
        self.assertIn("值得，但目的不同", text)
        self.assertIn("不是恢复保证", text)
        self.assertIn("N=600", text)
        for name in ("n400-result.png", "n400-coverage.png"):
            with Image.open(ROOT / name) as image:
                self.assertGreater(image.width, 1200)
                self.assertGreater(image.height, 650)

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
        report = json.loads((ROOT / "n400-word-qa" / "report.json").read_text(encoding="utf-8"))
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
