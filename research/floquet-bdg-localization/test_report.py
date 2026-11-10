"""Delivery contracts for the basis-invariant localization report."""

import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class LocalizationReportTests(unittest.TestCase):
    def test_method_markdown_and_figure(self):
        method = (ROOT / "METHOD.md").read_text(encoding="utf-8")
        self.assertIn("方法修正记录", method)
        self.assertIn("I₂", method)
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for required in ("short_chain_regime_supported", "inconclusive", "11.721854", "12.419694", "N×IPR 保持有限", "不是材料"):
            self.assertIn(required, text)
        self.assertGreater((ROOT / "localization.png").stat().st_size, 10000)

    def test_word_has_current_metrics_and_native_structure(self):
        data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
        with zipfile.ZipFile(ROOT / "REPORT.docx") as package:
            names = package.namelist()
            document = package.read("word/document.xml").decode("utf-8")
            footnotes = package.read("word/footnotes.xml")
            footer = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertTrue(any(name.startswith("word/media/") for name in names))
        for text in ("TOC", "<m:oMath", "short_chain_regime_supported", "inconclusive", "0.495972", "11.721854", "12.419694"):
            self.assertIn(text, document)
        for target in ("zero", "pi"):
            value = data["envelope_fits"][target][-1]["xi_env"]
            self.assertIn(f"{value:.6f}", document)
        for source in (b"1303.2300", b"results.json", b"verify_localization.py"):
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
