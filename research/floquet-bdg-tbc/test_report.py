"""Cross-artifact contracts for corrected TBC data, figures, DOCX, and visual QA."""

import hashlib
import json
import sys
import unittest
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-TBC无序对照报告.docx"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class ReportContractTests(unittest.TestCase):
    def test_ensemble_counts(self):
        data = json.loads((ROOT / "disorder_results.json").read_text(encoding="utf-8"))
        independent = json.loads((ROOT / "disorder_independent.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["realizations"]), 24)
        counts = [row[target]["status"] for row in data["realizations"] for target in ("zero", "pi")]
        self.assertEqual(counts.count("ok"), 46)
        self.assertEqual(counts.count("not_converged"), 2)
        self.assertEqual(independent["selected_count"], 14)
        self.assertTrue(independent["passed"])

    def test_markdown_matches_failures_and_control_scope(self):
        text = (ROOT / "REPORT.md").read_text(encoding="utf-8")
        self.assertIn("0.998984412", text)
        self.assertIn("0.998296305", text)
        self.assertIn("不能当作 4 个独立随机样本", text)
        self.assertIn("46 个有效结果", text)
        self.assertNotIn("\x0c", text)

    def test_figures_are_nonempty(self):
        for name in ("disorder-winding.png", "disorder-gaps.png"):
            path = ROOT / name
            self.assertGreater(path.stat().st_size, 10000)
            with Image.open(path) as image:
                self.assertGreater(image.width, 1200)
                self.assertGreater(image.height, 1200)

    def test_docx_native_structure(self):
        with zipfile.ZipFile(DOCX) as package:
            document = package.read("word/document.xml").decode("utf-8")
            footnotes = package.read("word/footnotes.xml").decode("utf-8")
            footers = "".join(
                package.read(name).decode("utf-8")
                for name in package.namelist()
                if name.startswith("word/footer") and name.endswith(".xml")
            )
            media = [name for name in package.namelist() if name.startswith("word/media/") and not name.endswith("/")]
        self.assertIn("m:oMath", document)
        self.assertIn("TOC", document)
        self.assertIn("w:footerReference", document)
        self.assertIn("PAGE", footers)
        self.assertNotIn("NUMPAGES", footers)
        self.assertIn("cantSplit", document)
        self.assertEqual(len(media), 2)
        self.assertIn("ERRATA.md", footnotes)
        self.assertIn("disorder_independent.json", footnotes)
        self.assertNotIn('footnote("reserved")', (ROOT / "build_report.js").read_text(encoding="utf-8"))

    def test_visual_review_hashes_are_current(self):
        report = json.loads((ROOT / "word-qa" / "report.json").read_text(encoding="utf-8"))
        self.assertEqual(report["rendered"], 6)
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
