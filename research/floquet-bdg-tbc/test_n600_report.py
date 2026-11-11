"""Contracts for N=600 data, native Word, and truthful visual-QA status."""

import hashlib
import json
import sys
import unittest
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-N600尾长诊断报告.docx"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class N600ReportTests(unittest.TestCase):
    def test_n600_result_and_independent_agreement(self):
        data = json.loads((ROOT / "scale_diagnostic.json").read_text(encoding="utf-8"))
        independent = json.loads((ROOT / "scale_independent_n600.json").read_text(encoding="utf-8"))
        self.assertTrue(data["n600_complete"])
        row = next(row for row in data["rows"] if row["n"] == 600)
        self.assertEqual(row["zero"]["status"], "ok")
        self.assertEqual(row["zero"]["nearest_integer"], 1)
        self.assertFalse(row["endpoint"]["zero"]["joint_pass"])
        self.assertTrue(independent["integer_agreement"])
        self.assertEqual(independent["independent"]["nearest_integer"], 1)

    def test_tail_metrics_and_markdown(self):
        metrics = json.loads((ROOT / "n600_scale.json").read_text(encoding="utf-8"))
        self.assertEqual(metrics["L50"], 85)
        self.assertEqual(metrics["L90"], 164)
        self.assertLess(metrics["envelope"]["r_squared"], 0.5)
        text = (ROOT / "N600_DIAGNOSTIC.md").read_text(encoding="utf-8")
        self.assertIn("L50 从 21→31→51→85", text)
        self.assertIn("N=600 不是自动恢复尺寸", text)
        self.assertIn("N=640", text)

    def test_figures_are_nonempty(self):
        for name in ("n600-result.png", "n600-coverage.png"):
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

    def test_visual_status_is_unavailable_not_passed(self):
        report = json.loads((ROOT / "n600-word-qa" / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["visualReview"]["status"], "unavailable_exit_6_no_retry")
        self.assertFalse(report["visualReview"]["visualPassClaimed"])
        self.assertFalse(report["visualReview"]["libreOfficeFallbackUsed"])
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
