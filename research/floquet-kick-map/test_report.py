"""Contracts for the homogeneous kick map and sensitivity report."""

import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class KickMapReportTests(unittest.TestCase):
    def test_markdown_has_correct_singularities_and_transition(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for required in ("U(0)=+I", "U(π)=−I", "a=0.22", "pπ=1", "a=0.24", "pπ=0", "not_supported", "inconclusive_preserved"):
            self.assertIn(required, text)
        self.assertGreater((ROOT / "kick-map.png").stat().st_size, 10000)

    def test_word_contains_current_counts_sources_and_native_structure(self):
        with zipfile.ZipFile(ROOT / "REPORT.docx") as package:
            names = package.namelist()
            document = package.read("word/document.xml").decode("utf-8")
            footnotes = package.read("word/footnotes.xml")
            footer = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertTrue(any(name.startswith("word/media/") for name in names))
        for text in ("TOC", "<m:oMath", "U(π)=−I", "gapless_or_undefined", "fluctuation_sensitive", "15/16", "16/16", "inconclusive_preserved"):
            self.assertIn(text, document)
        for source in (b"1303.2300", b"2203.16353", b"results.json", b"sensitivity.json", b"verify_kick_map.py"):
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
