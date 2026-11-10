import re
import sys
import unittest
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

AUDIT = Path(__file__).resolve().parent
MD = AUDIT / "STRENGTH_SERIES_REVIEW.md"
DOCX = AUDIT / "STRENGTH_SERIES_REVIEW.docx"
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def supplement_headings():
    return [
        line[3:].strip()
        for line in MD.read_text(encoding="utf-8").splitlines()
        if re.match(r"^## (K1a |K1b |K2 )", line)
    ]


def docx_text():
    with zipfile.ZipFile(DOCX) as package:
        root = ET.fromstring(package.read("word/document.xml"))
        paragraphs = []
        for paragraph in root.iter(W + "p"):
            paragraphs.append("".join(node.text or "" for node in paragraph.iter(W + "t")))
        return "\n".join(paragraphs)


class WordContentTests(unittest.TestCase):
    def test_markdown_has_exactly_17_supplements(self):
        headings = supplement_headings()
        self.assertEqual(len(headings), 17)
        self.assertEqual(len(set(headings)), 17)

    def test_docx_contains_every_supplement_in_order_without_duplicates(self):
        text = docx_text()
        headings = supplement_headings()
        missing = [heading for heading in headings if heading not in text]
        self.assertEqual(missing, [])
        positions = [text.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))
        self.assertTrue(all(text.count(heading) == 1 for heading in headings))

    def test_final_range_class_and_60_regression_are_present(self):
        text = docx_text()
        self.assertIn("K2 商层像模同构类复核补记（2026-11-10）", text)
        self.assertIn("60/60", text)

    def test_native_ooxml_structure(self):
        with zipfile.ZipFile(DOCX) as package:
            names = package.namelist()
            document = package.read("word/document.xml")
            headers = b"".join(
                package.read(name)
                for name in names
                if name.startswith("word/header") and name.endswith(".xml")
            )
            footers = b"".join(
                package.read(name)
                for name in names
                if name.startswith("word/footer") and name.endswith(".xml")
            )
        self.assertIn(b"TOC", document)
        self.assertIn(b"<m:oMath", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 2)
        self.assertIn("55篇逐篇初审", headers.decode("utf-8"))
        self.assertIn(b"PAGE", footers)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
