import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_ORIGINAL = "1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439"
THEOREMS = ("bcsCriticalTemp_unfold", "debyeModel_unfold")


class CompatibleDefinitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "compatible-definitions.json").read_text(encoding="utf-8"))

    def test_original_unchanged(self):
        self.assertEqual(self.data["original"]["sha256"], EXPECTED_ORIGINAL)
        self.assertFalse(self.data["original"]["source_modified"])
        self.assertEqual(self.data["original"]["sorry_lines"], [93, 112, 185])
        self.assertFalse(self.data["original_compile"]["original_theorem_axiom_audit_available"])

    def test_two_definitions_and_two_rfl(self):
        text = (ROOT / "CompatibleDefinitions.lean").read_text(encoding="utf-8")
        self.assertIn("Real.eulerMascheroniConstant", text)
        self.assertIn("debyeModel", text)
        self.assertIn("ω₀ : ℝ", text)
        self.assertIn("ω₀ / Real.sqrt M", text)
        self.assertNotIn("HasEquiv", text)
        self.assertEqual(text.count(":= by\n  rfl"), 2)
        for theorem in THEOREMS:
            self.assertIn(f"theorem {theorem}", text)
            self.assertIn(f"#print axioms {theorem}", text)
        for forbidden in (r"(?m)^\s*axiom\b", r"(?m)^\s*postulate\b", r"(?m)^\s*sorry\b", r"(?m)^\s*admit\b", r"\bnative_decide\b"):
            self.assertNotRegex(text, forbidden)

    def test_real_compile_and_dependencies(self):
        self.assertEqual(self.data["compile"]["status"], "passed")
        self.assertEqual(self.data["compile"]["exit_code"], 0)
        self.assertTrue(self.data["compile"]["machine_checked"])
        for theorem in THEOREMS:
            row = self.data["dependencies"][theorem]
            self.assertFalse(row["sorryAx"])
            self.assertEqual(row["nonstandard_axioms"], [])
            self.assertEqual(row["axioms"], ["propext", "Classical.choice", "Quot.sound"])

    def test_local_resolution_and_open_boundaries(self):
        resolution = self.data["local_resolution"]
        self.assertTrue(resolution["euler_constant"])
        self.assertTrue(resolution["ascii_lambda"])
        self.assertTrue(resolution["debye_types"])
        self.assertFalse(resolution["has_equiv_semantics"])
        for key in ("original_file_compiled", "original_theorems_proven", "physical_validity_verified", "all_compatibility_complete"):
            self.assertFalse(self.data["open_boundaries"][key])

    def test_markdown_and_word_contract(self):
        markdown = (ROOT / "COMPATIBLE_DEFINITIONS.md").read_text(encoding="utf-8")
        for text in ("Real.eulerMascheroniConstant", "debyeModel", "lam", "不是物理证明", "HasEquiv"):
            self.assertIn(text, markdown)
        with zipfile.ZipFile(ROOT / "COMPATIBLE_DEFINITIONS.docx") as package:
            names = package.namelist()
            document = package.read("word/document.xml")
            header = b"".join(package.read(name) for name in names if name.startswith("word/header") and name.endswith(".xml"))
            footer = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn("word/footnotes.xml", names)
        self.assertIn(b"TOC", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 3)
        self.assertIn(b"PAGE", footer)
        self.assertIn("Lean 兼容定义", header.decode("utf-8"))


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
