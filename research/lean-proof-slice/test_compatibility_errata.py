import hashlib
import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_ORIGINAL = "1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439"
ISSUE_MARKERS = {
    "euler_mascheroni": "eulerMascheroni",
    "lambda_identifier": "unexpected token 'λ'",
    "omega_d_binding": "ω_D",
    "has_equiv_real": "HasEquiv ℝ",
}


class CompatibilityErrataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "compatibility-issues.json").read_text(encoding="utf-8"))
        cls.log = (ROOT / "original-compile.log").read_text(encoding="utf-8")

    def test_original_hash_and_failed_compile(self):
        self.assertEqual(self.data["original"]["sha256"], EXPECTED_ORIGINAL)
        self.assertFalse(self.data["original"]["source_modified"])
        self.assertNotEqual(self.data["original_compile"]["exit_code"], 0)
        self.assertEqual(self.data["original_compile"]["status"], "source_incompatible")
        self.assertEqual(self.data["original_compile"]["log_sha256"], hashlib.sha256((ROOT / "original-compile.log").read_bytes()).hexdigest())

    def test_four_open_issues_with_direct_evidence(self):
        issues = self.data["issues"]
        self.assertEqual(len(issues), 4)
        self.assertEqual({row["id"] for row in issues}, set(ISSUE_MARKERS))
        for row in issues:
            self.assertEqual(row["status"], "open")
            self.assertIn(ISSUE_MARKERS[row["id"]], self.log)
            self.assertIn(ISSUE_MARKERS[row["id"]], row["evidence"])
            self.assertTrue(row["next"])

    def test_remediation_is_specific_and_honest(self):
        rows = {row["id"]: row for row in self.data["issues"]}
        self.assertIn("Real.eulerMascheroniConstant", rows["euler_mascheroni"]["next"])
        self.assertIn("lam", rows["lambda_identifier"]["next"])
        self.assertIn("ω_D : ℝ → ℝ", rows["omega_d_binding"]["next"])
        self.assertIn("ω₀ : ℝ", rows["omega_d_binding"]["next"])
        self.assertIn("不构造虚假实例", rows["has_equiv_real"]["next"])
        self.assertFalse(self.data["verification_scope"]["new_axiom_or_sorry_added"])

    def test_open_boundaries(self):
        for key in ("original_file_compiled", "original_theorems_proven", "physical_validity_verified", "all_errata_resolved"):
            self.assertFalse(self.data["open_boundaries"][key])
        self.assertTrue(self.data["verification_scope"]["errata_only"])

    def test_markdown_and_word_contract(self):
        markdown = (ROOT / "COMPATIBILITY_ERRATA.md").read_text(encoding="utf-8")
        for text in ("Real.eulerMascheroniConstant", "lam", "ω_D : ℝ → ℝ", "不构造虚假实例", "未解决"):
            self.assertIn(text, markdown)
        with zipfile.ZipFile(ROOT / "COMPATIBILITY_ERRATA.docx") as package:
            names = package.namelist()
            document = package.read("word/document.xml")
            header = b"".join(package.read(name) for name in names if name.startswith("word/header") and name.endswith(".xml"))
            footer = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn("word/footnotes.xml", names)
        self.assertIn(b"TOC", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 3)
        self.assertIn(b"PAGE", footer)
        self.assertIn("Lean 兼容性勘误", header.decode("utf-8"))


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
