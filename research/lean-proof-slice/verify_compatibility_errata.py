"""Independently verify compatibility errata against original evidence."""

import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ORIGINAL = Path("C:/Users/一梦/Documents/kimi/workspace/toe-sylva-audit/papers/room_temp_sc/room_temp_sc_Formalization.lean")
EXPECTED = "1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439"
MATHLIB_DIGAMMA = Path("D:/migration/lean-proof-slice-build/.lake/packages/mathlib/Mathlib/Analysis/SpecialFunctions/Gamma/Digamma.lean")


class IndependentErrataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "compatibility-issues.json").read_text(encoding="utf-8"))
        cls.log = (ROOT / "original-compile.log").read_text(encoding="utf-8")

    def test_source_and_log_hash(self):
        self.assertEqual(hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(), EXPECTED)
        self.assertEqual(self.data["original"]["sha256"], EXPECTED)
        self.assertEqual(self.data["original_compile"]["log_sha256"], hashlib.sha256((ROOT / "original-compile.log").read_bytes()).hexdigest())
        self.assertFalse(self.data["original"]["source_modified"])
        self.assertNotEqual(self.data["original_compile"]["exit_code"], 0)

    def test_direct_markers_and_open_status(self):
        markers = {
            "euler_mascheroni": "eulerMascheroni",
            "lambda_identifier": "unexpected token 'λ'",
            "omega_d_binding": "ω_D",
            "has_equiv_real": "HasEquiv ℝ",
        }
        self.assertEqual(len(self.data["issues"]), 4)
        for row in self.data["issues"]:
            marker = markers[row["id"]]
            self.assertIn(marker, self.log)
            self.assertEqual(row["log_marker"], marker)
            self.assertEqual(row["status"], "open")

    def test_actual_constant_and_specific_actions(self):
        self.assertTrue(MATHLIB_DIGAMMA.exists())
        self.assertIn("Real.eulerMascheroniConstant", MATHLIB_DIGAMMA.read_text(encoding="utf-8"))
        rows = {row["id"]: row for row in self.data["issues"]}
        self.assertIn("Real.eulerMascheroniConstant", rows["euler_mascheroni"]["next"])
        self.assertIn("lam", rows["lambda_identifier"]["next"])
        self.assertIn("ω_D : ℝ → ℝ", rows["omega_d_binding"]["next"])
        self.assertIn("ω₀ : ℝ", rows["omega_d_binding"]["next"])
        self.assertIn("不构造虚假实例", rows["has_equiv_real"]["next"])

    def test_no_completion_claims(self):
        for value in self.data["open_boundaries"].values():
            self.assertFalse(value)
        self.assertTrue(self.data["verification_scope"]["errata_only"])
        self.assertFalse(self.data["verification_scope"]["new_axiom_or_sorry_added"])
        self.assertFalse(self.data["verification_scope"]["source_modified"])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
