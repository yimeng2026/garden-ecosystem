"""Independent verification of Floquet error-bound semantics."""

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ORIGINAL = Path("C:/Users/一梦/Documents/kimi/workspace/toe-sylva-audit/papers/room_temp_sc/room_temp_sc_Formalization.lean")
EXPECTED = "1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439"


class IndependentFloquetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "floquet-approximation.json").read_text(encoding="utf-8"))
        cls.text = (ROOT / "FloquetApproximation.lean").read_text(encoding="utf-8")

    def test_original_unchanged(self):
        self.assertEqual(hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(), EXPECTED)
        self.assertEqual(self.data["original"]["sha256"], EXPECTED)
        self.assertFalse(self.data["original"]["source_modified"])
        self.assertEqual(self.data["original"]["sorry_lines"], [93, 112, 185])

    def test_error_bound_and_proof_shapes(self):
        self.assertIn("def DriveApprox", self.text)
        self.assertIn("|ω_drive - 2 * Δ / ℏ| ≤ ε", self.text)
        self.assertNotIn("HasEquiv", self.text)
        self.assertIn("le_antisymm h (abs_nonneg _)", self.text)
        self.assertIn("simp [h, DriveApprox]", self.text)
        self.assertEqual(self.text.count(":= by\n  rfl"), 1)

    def test_compile_and_dependencies(self):
        self.assertEqual(self.data["compile"]["status"], "passed")
        self.assertEqual(self.data["compile"]["exit_code"], 0)
        self.assertTrue(self.data["compile"]["machine_checked"])
        for name in ("driveApprox_unfold", "driveApprox_zero_exact", "driveApprox_of_exact"):
            row = self.data["dependencies"][name]
            self.assertFalse(row["sorryAx"])
            self.assertEqual(row["nonstandard_axioms"], [])
            self.assertEqual(row["axioms"], ["propext", "Classical.choice", "Quot.sound"])

    def test_no_floquet_or_project_completion(self):
        self.assertTrue(self.data["local_resolution"]["explicit_error_bound"])
        self.assertTrue(self.data["local_resolution"]["zero_error_exact"])
        self.assertTrue(self.data["local_resolution"]["exact_zero_error"])
        self.assertFalse(self.data["local_resolution"]["has_equiv_semantics"])
        for value in self.data["open_boundaries"].values():
            self.assertFalse(value)
        self.assertTrue(self.data["verification_scope"]["semantics_only"])
        self.assertFalse(self.data["verification_scope"]["new_axiom_or_sorry_added"])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
