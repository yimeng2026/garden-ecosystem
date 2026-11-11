"""Cross-artifact contracts for localization-scale data, Word, and visual QA."""

import hashlib
import json
import sys
import unittest
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-局域恢复尺度报告.docx"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LocalizationReportTests(unittest.TestCase):
    def test_profile_counts_and_recovery_classes(self):
        data = json.loads((ROOT / "localization_scale.json").read_text(encoding="utf-8"))
        self.assertEqual(data["profile_count"], 15)
        cases = {(case["strength"], case["seed"]): case for case in data["cases"]}
        self.assertEqual(cases[(0.05, 0)]["assessment"]["status"], "not_established")
        self.assertEqual(cases[(0.05, 0)]["assessment"]["next_size"], 600)
        self.assertEqual(cases[(0.1, 0)]["assessment"]["status"], "bounded_diagnostic")
        self.assertEqual(cases[(0.1, 0)]["assessment"]["next_size"], 400)
        self.assertEqual(cases[(0.1, 0)]["assessment"]["l50_bracket_times_ten"], [330, 380])
        for key in ((0.05, 2), (0.05, 3), (0.1, 2)):
            self.assertEqual(cases[key]["assessment"]["status"], "measured_recovered")

    def test_markdown_preserves_diagnostic_boundaries(self):
        text = (ROOT / "REPORT.md").read_text(encoding="utf-8")
        self.assertIn("N=400", text)
        self.assertIn("N=600", text)
        self.assertIn("N=640 尚未计算", text)
        self.assertIn("不能作为 localization length", text)
        self.assertIn("不是恢复承诺", text)
        self.assertIn("不能证明整体局域化", text)

    def test_figures_are_nonempty(self):
        for name in ("coverage-scale.png", "scale-diagnostics.png"):
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

    def test_visual_review_hashes_are_current(self):
        report = json.loads((ROOT / "word-qa" / "report.json").read_text(encoding="utf-8"))
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
