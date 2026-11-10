"""Contracts for corrected errata, Markdown, figure and native Word delivery."""

import json
import sys
import unittest
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent


class CorrectedReportTests(unittest.TestCase):
    def test_errata_and_markdown_preserve_short_chain_boundary(self):
        errata = (ROOT.parent / "floquet-bdg" / "ERRATA.md").read_text(encoding="utf-8")
        for text in ("暂停适用", "0.5702416578408517", "0.2987666363611303", "不删除、不改写"):
            self.assertIn(text, errata)
        markdown = (ROOT / "README.md").read_text(encoding="utf-8")
        for text in ("W=2", "p0=1", "pπ=1", "0.495972", "inconclusive", "不继承旧", "不是材料"):
            self.assertIn(text, markdown)
        with Image.open(ROOT / "topology.png") as image:
            self.assertGreater(image.width, 1200)
            self.assertGreater(image.width / image.height, 1.3)

    def test_word_contains_current_values_and_native_structure(self):
        data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
        with zipfile.ZipFile(ROOT / "REPORT.docx") as package:
            names = package.namelist()
            document = package.read("word/document.xml").decode("utf-8")
            footnotes = package.read("word/footnotes.xml")
            header = b"".join(package.read(name) for name in names if name.startswith("word/header") and name.endswith(".xml"))
            footer = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertTrue(any(name.startswith("word/media/") for name in names))
        for text in ("TOC", "<m:oMath", "cantSplit", "inconclusive", "0.495972", "0.5702416578408517"):
            self.assertIn(text, document)
        for target in ("zero", "pi"):
            value = max(data["size_studies"][-1][target]["distances"])
            self.assertIn(f"{value:.6e}", document)
        for source in (b"1303.2300", b"ERRATA.md", b"convention-red.log", b"results.json"):
            self.assertIn(source, footnotes)
        self.assertIn("Floquet-BdG".encode(), header)
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
