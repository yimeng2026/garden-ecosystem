import hashlib
import json
import re
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_ORIGINAL_SHA256 = "1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439"
EXPECTED_ELAN_SHA256 = "fad2e980a191c15884cc1d80d170ffc5fa84f3774541020145b66d1a644c6111"
EXPECTED_MATHLIB_REV = "56a005855ea17e0b0958f73ec801ae140b0a1679"
THEOREMS = ("allenDynesTc_unfold", "h3s_tc_prediction_unfold", "lah10_tc_prediction_unfold")
DEBT_THEOREMS = ("allenDynes_weak_coupling_limit", "bcs_isotope_effect", "floquet_enhanced_tc")


class LeanSliceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "proof-slice.json").read_text(encoding="utf-8"))

    def test_original_copy_and_existing_debt(self):
        original = self.data["original"]
        self.assertEqual(original["sha256"], EXPECTED_ORIGINAL_SHA256)
        self.assertEqual(original["copy_sha256"], EXPECTED_ORIGINAL_SHA256)
        self.assertEqual(original["sorry_lines"], [93, 112, 185])
        self.assertEqual(hashlib.sha256((ROOT / "RoomTempSC_Formalization.lean").read_bytes()).hexdigest(), EXPECTED_ORIGINAL_SHA256)
        self.assertFalse(original["source_modified"])

    def test_new_slice_has_only_three_rfl_proofs(self):
        text = (ROOT / "ProofSlice.lean").read_text(encoding="utf-8")
        self.assertEqual(text.count(":= by\n  rfl"), 3)
        for forbidden in (r"(?m)^\s*axiom\b", r"(?m)^\s*postulate\b", r"(?m)^\s*sorry\b", r"(?m)^\s*admit\b", r"\bnative_decide\b"):
            self.assertNotRegex(text, forbidden)
        for theorem in THEOREMS:
            self.assertIn(f"theorem {theorem}", text)
            self.assertIn(f"#print axioms {theorem}", text)
        for theorem in DEBT_THEOREMS:
            self.assertIn(f"#print axioms {theorem}", text)

    def test_toolchain_pins(self):
        toolchain = self.data["toolchain"]
        self.assertIn("4.35.0", toolchain["lean_version"])
        self.assertEqual(toolchain["mathlib_rev"], EXPECTED_MATHLIB_REV)
        self.assertEqual(toolchain["elan_asset_sha256"], EXPECTED_ELAN_SHA256)
        self.assertTrue(toolchain["path_unchanged"])

    def test_real_compile(self):
        compile_result = self.data["compile"]
        self.assertEqual(compile_result["status"], "passed")
        self.assertEqual(compile_result["exit_code"], 0)
        self.assertTrue(compile_result["machine_checked"])

    def test_dependency_separation(self):
        dependencies = self.data["dependencies"]
        for theorem in THEOREMS:
            self.assertFalse(dependencies["new_theorems"][theorem]["sorryAx"])
            self.assertFalse(dependencies["new_theorems"][theorem]["depends_on_axioms"])
        for theorem in DEBT_THEOREMS:
            self.assertTrue(dependencies["original_theorems"][theorem]["sorryAx"])
        self.assertTrue(dependencies["debt_preserved"])
        self.assertFalse(dependencies["physical_theorems_proven"])

    def test_report_and_word_contract(self):
        markdown = (ROOT / "PROOF_SLICE.md").read_text(encoding="utf-8")
        for text in ("定义展开", "不是物理证明", "3 处既有", "sorryAx", "未验证"):
            self.assertIn(text, markdown)
        with zipfile.ZipFile(ROOT / "PROOF_SLICE.docx") as package:
            names = package.namelist()
            document = package.read("word/document.xml")
            header = b"".join(package.read(name) for name in names if name.startswith("word/header") and name.endswith(".xml"))
            footer = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
        self.assertIn(b"TOC", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 3)
        self.assertIn(b"PAGE", footer)
        self.assertIn("Lean 定义切片", header.decode("utf-8"))


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
