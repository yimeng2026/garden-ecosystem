"""Contracts for N=320 registry, independent checks, native Word, and visual hashes."""

import hashlib
import json
import sys
import unittest
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-TBC-N320定向报告.docx"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class N320ReportTests(unittest.TestCase):
    def test_registry_and_independent_counts(self):
        data = json.loads((ROOT / "n320_zero.json").read_text(encoding="utf-8"))
        independent = json.loads((ROOT / "n320_independent.json").read_text(encoding="utf-8"))
        self.assertTrue(data["complete"])
        self.assertEqual(len(data["rows"]), 7)
        self.assertTrue(all(row["zero"]["status"] == "ok" and row["zero"]["nearest_integer"] == 1 for row in data["rows"]))
        self.assertEqual(independent["selected_count"], 7)
        self.assertTrue(independent["passed"])
        self.assertTrue(all(row["integer_agreement"] for row in independent["checks"]))

    def test_group_summary(self):
        summary = json.loads((ROOT / "n320_summary.json").read_text(encoding="utf-8"))
        groups = {row["class"]: row for row in summary["groups"]}
        self.assertEqual(groups["recovered"]["endpoint_pass"], 3)
        self.assertEqual(groups["not_recovered"]["endpoint_pass"], 0)
        self.assertEqual(groups["uniform_control"]["endpoint_pass"], 2)
        self.assertTrue(all(row["winding_valid"] == row["winding_one"] for row in groups.values()))

    def test_markdown_and_figures(self):
        text = (ROOT / "N320.md").read_text(encoding="utf-8")
        self.assertIn("两个未恢复样本", text)
        self.assertIn("体边对应并未对所有样本闭合", text)
        self.assertIn("N=640", text)
        for name in ("n320-winding.png", "n320-endpoints.png"):
            with Image.open(ROOT / name) as image:
                self.assertGreater(image.width, 1200)
                self.assertGreater(image.height, 900)

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
        report = json.loads((ROOT / "n320-word-qa" / "report.json").read_text(encoding="utf-8"))
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
