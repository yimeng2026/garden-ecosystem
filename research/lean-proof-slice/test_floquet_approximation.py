import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_ORIGINAL = "1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439"
THEOREMS = ("driveApprox_unfold", "driveApprox_zero_exact", "driveApprox_of_exact")


class FloquetApproximationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "floquet-approximation.json").read_text(encoding="utf-8"))

    def test_definition_has_error_bound_not_has_equiv(self):
        text = (ROOT / "FloquetApproximation.lean").read_text(encoding="utf-8")
        self.assertIn("def DriveApprox", text)
        self.assertIn("|ω_drive - 2 * Δ / ℏ| ≤ ε", text)
        self.assertNotIn("HasEquiv", text)
        self.assertEqual(text.count(":= by\n  rfl"), 1)
        self.assertIn("le_antisymm h (abs_nonneg _)", text)
        self.assertIn("simp [h, DriveApprox]", text)

    def test_zero_error_exact_equivalence(self):
        self.assertEqual(self.data["compile"]["status"], "passed")
        self.assertEqual(self.data["compile"]["exit_code"], 0)
        self.assertTrue(self.data["compile"]["machine_checked"])
        for name in THEOREMS:
            row = self.data["dependencies"][name]
            self.assertFalse(row["sorryAx"])
            self.assertEqual(row["nonstandard_axioms"], [])
            self.assertEqual(row["axioms"], ["propext", "Classical.choice", "Quot.sound"])

    def test_original_and_physical_boundaries(self):
        self.assertEqual(self.data["original"]["sha256"], EXPECTED_ORIGINAL)
        self.assertEqual(self.data["original"]["sorry_lines"], [93, 112, 185])
        self.assertFalse(self.data["original"]["source_modified"])
        self.assertFalse(self.data["original_compile"]["original_theorem_axiom_audit_available"])
        for key in ("floquet_enhancement_proven", "physical_validity_verified", "original_file_compiled", "original_theorems_proven"):
            self.assertFalse(self.data["open_boundaries"][key])

    def test_semantic_resolution(self):
        resolution = self.data["local_resolution"]
        self.assertTrue(resolution["explicit_error_bound"])
        self.assertTrue(resolution["zero_error_exact"])
        self.assertTrue(resolution["exact_zero_error"])
        self.assertFalse(resolution["has_equiv_semantics"])
        self.assertTrue(self.data["verification_scope"]["semantics_only"])
        self.assertFalse(self.data["verification_scope"]["new_axiom_or_sorry_added"])

    def test_markdown_and_word_contract(self):
        markdown = (ROOT / "FLOQUET_APPROXIMATION.md").read_text(encoding="utf-8")
        for text in ("DriveApprox", "零误差", "不是 Floquet 增强证明", "HasEquiv", "未验证"):
            self.assertIn(text, markdown)
        with zipfile.ZipFile(ROOT / "FLOQUET_APPROXIMATION.docx") as package:
            names = package.namelist()
            document = package.read("word/document.xml")
            header = b"".join(package.read(name) for name in names if name.startswith("word/header") and name.endswith(".xml"))
            footer = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn("word/footnotes.xml", names)
        self.assertIn(b"TOC", document)
        self.assertIn(b"<m:oMath", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 3)
        self.assertIn(b"PAGE", footer)
        self.assertIn("Floquet 误差界", header.decode("utf-8"))
        self.assertTrue(any(name.startswith("word/media/") for name in names))

    def test_toc_and_footnote_mapping(self):
        import xml.etree.ElementTree as ET

        namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        ns = {"w": namespace}
        with zipfile.ZipFile(ROOT / "FLOQUET_APPROXIMATION.docx") as package:
            root = ET.fromstring(package.read("word/document.xml"))

        def text_of(element):
            return "".join(node.text or "" for node in element.findall(".//w:t", ns))

        toc = root.find(".//w:sdt", ns)
        self.assertIsNotNone(toc)
        cached = [text_of(p) for p in toc.findall(".//w:p", ns)]
        titles = ["一、显式误差界与零误差证明", "二、原文件与物理命题边界", "三、工具链与后续"]
        for title, page in zip(titles, [2, 3, 3]):
            self.assertIn(f"{title}{page}", cached)
        expected = {
            "DriveApprox 在真实 Lean": {"1"},
            "原文件未修改，原文件直译仍不兼容": {"2"},
            "Lean、Lake 和 Mathlib": {"3"},
        }
        referenced = set()
        for marker, expected_ids in expected.items():
            matches = [p for p in root.findall(".//w:p", ns) if marker in text_of(p) and p.find(".//w:footnoteReference", ns) is not None]
            self.assertEqual(len(matches), 1, marker)
            actual = {node.attrib[f"{{{namespace}}}id"] for node in matches[0].findall(".//w:footnoteReference", ns)}
            self.assertEqual(actual, expected_ids, marker)
            referenced.update(actual)
        self.assertEqual(referenced, {"1", "2", "3"})


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
