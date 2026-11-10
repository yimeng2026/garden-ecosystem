"""Independent checks for the two compatible definitions."""

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ORIGINAL = Path("C:/Users/一梦/Documents/kimi/workspace/toe-sylva-audit/papers/room_temp_sc/room_temp_sc_Formalization.lean")
EXPECTED = "1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439"
DIGAMMA = Path("D:/migration/lean-proof-slice-build/.lake/packages/mathlib/Mathlib/Analysis/SpecialFunctions/Gamma/Digamma.lean")


class IndependentCompatibleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "compatible-definitions.json").read_text(encoding="utf-8"))
        cls.text = (ROOT / "CompatibleDefinitions.lean").read_text(encoding="utf-8")

    def test_original_and_actual_constant(self):
        self.assertEqual(hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(), EXPECTED)
        self.assertIn("Real.eulerMascheroniConstant", DIGAMMA.read_text(encoding="utf-8"))
        self.assertIn("Real.eulerMascheroniConstant", self.text)
        self.assertFalse(self.data["original"]["source_modified"])

    def test_debye_types_and_two_rfl(self):
        self.assertIn("debyeModel (ω₀ : ℝ) : ℝ → ℝ", self.text)
        self.assertIn("ω₀ / Real.sqrt M", self.text)
        self.assertNotIn("HasEquiv", self.text)
        self.assertEqual(self.text.count(":= by\n  rfl"), 2)

    def test_compile_and_dependencies(self):
        self.assertEqual(self.data["compile"]["exit_code"], 0)
        self.assertTrue(self.data["compile"]["machine_checked"])
        for name in ("bcsCriticalTemp_unfold", "debyeModel_unfold"):
            row = self.data["dependencies"][name]
            self.assertFalse(row["sorryAx"])
            self.assertEqual(row["nonstandard_axioms"], [])
            self.assertEqual(row["axioms"], ["propext", "Classical.choice", "Quot.sound"])

    def test_no_completion_claims(self):
        self.assertTrue(self.data["local_resolution"]["euler_constant"])
        self.assertTrue(self.data["local_resolution"]["ascii_lambda"])
        self.assertTrue(self.data["local_resolution"]["debye_types"])
        self.assertFalse(self.data["local_resolution"]["has_equiv_semantics"])
        for value in self.data["open_boundaries"].values():
            self.assertFalse(value)
        self.assertTrue(self.data["verification_scope"]["definitions_only"])
        self.assertFalse(self.data["verification_scope"]["new_axiom_or_sorry_added"])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
