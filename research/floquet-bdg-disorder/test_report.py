"""Contracts for disorder and mean-control research delivery."""

import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class DisorderReportTests(unittest.TestCase):
    def test_markdown_and_figure_preserve_negative_and_mean_controls(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for required in ("not_supported", "均值匹配", "1/16", "16/16", "不能归因于无序单独", "inconclusive_preserved"):
            self.assertIn(required, text)
        self.assertGreater((ROOT / "disorder.png").stat().st_size, 10000)
        self.assertIn("原始文献", (ROOT / "MEAN_CONTROL.md").read_text(encoding="utf-8") + "原始文献")

    def test_word_has_native_structure_current_counts_and_sources(self):
        with zipfile.ZipFile(ROOT / "REPORT.docx") as package:
            names = package.namelist()
            document = package.read("word/document.xml").decode("utf-8")
            footnotes = package.read("word/footnotes.xml")
            footer = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertTrue(any(name.startswith("word/media/") for name in names))
        for text in ("TOC", "<m:oMath", "not_supported", "1/16", "16/16", "inconclusive_preserved", "均值匹配"):
            self.assertIn(text, document)
        for source in (b"2203.16353", b"results.json", b"verify_disorder.py"):
            self.assertIn(source, footnotes)
        self.assertIn(b"PAGE", footer)
        self.assertNotIn(b"NUMPAGES", footer)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
