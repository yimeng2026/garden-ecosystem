"""Contracts for the kicked-chemical-potential disorder study."""

import csv
import json
import sys
import unittest
from pathlib import Path

import numpy as np
from scipy.linalg import expm

ROOT = Path(__file__).resolve().parent
CONVENTION = ROOT.parent / "floquet-bdg-convention"
sys.path.insert(0, str(CONVENTION))
sys.path.insert(0, str(ROOT))
from convention_model import kicked_floquet, majorana_k  # noqa: E402
from disorder_model import beta_sequence, chemical_kick, disordered_floquet  # noqa: E402


class DisorderModelTests(unittest.TestCase):
    def test_analytic_kick_matches_clean_matrix_exponential(self):
        amplitudes = np.array([0.11, 0.22, 0.33])
        kick = chemical_kick(amplitudes)
        blocks = [expm(-2 * majorana_k(1, value, gamma=0.0, delta=0.0)) for value in amplitudes]
        for index, block in enumerate(blocks):
            np.testing.assert_allclose(kick[2 * index : 2 * index + 2, 2 * index : 2 * index + 2], block, atol=2e-15)
        np.testing.assert_allclose(kick.T @ kick, np.eye(6), atol=2e-14)

    def test_zero_and_uniform_disorder_match_correct_clean_model(self):
        n = 8
        zero, _ = disordered_floquet(n, 2.5, np.zeros(n), 0.0, 7.0)
        expected_zero, _ = kicked_floquet(n, 2.5, 0.0, 7.0)
        np.testing.assert_allclose(zero, expected_zero, atol=1e-14)
        uniform, _ = disordered_floquet(n, 2.5, np.ones(n), 0.2, 7.0)
        expected_clean, _ = kicked_floquet(n, 2.5, 0.2, 7.0)
        np.testing.assert_allclose(uniform, expected_clean, atol=1e-14)

    def test_sequences_are_reproducible_nested_and_seed_specific(self):
        first = beta_sequence(0, 80)
        np.testing.assert_allclose(first, np.random.default_rng(20261111).random(320)[:80])
        np.testing.assert_allclose(first, beta_sequence(0, 320)[:80])
        np.testing.assert_allclose(first, beta_sequence(0, 80))
        self.assertFalse(np.array_equal(first, beta_sequence(1, 80)))


class DisorderArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))

    def test_full_factorial_realizations_and_raw_csv(self):
        self.assertEqual(self.data["sizes"], [80, 160, 320])
        self.assertEqual(self.data["strengths"], [0.05, 0.1, 0.2])
        self.assertEqual(self.data["seed_counts"], {"80": 16, "160": 16, "320": 4})
        self.assertEqual(len(self.data["realizations"]), 108)
        with (ROOT / "realizations.csv").open(encoding="utf-8", newline="") as stream:
            self.assertEqual(len(list(csv.DictReader(stream))), 216)

    def test_assessment_scope_and_preserved_boundaries(self):
        self.assertIn(self.data["assessment"]["status"], {"supported", "partial", "not_supported"})
        self.assertEqual(self.data["assessment"]["main_strengths"], [0.05, 0.1])
        self.assertEqual(self.data["assessment"]["stress_strength"], 0.2)
        self.assertEqual(self.data["assessment"]["full_size_rule_status"], "inconclusive_preserved")
        for key in ("disorder_winding_computed", "thermodynamic_limit_proof", "material_tc_prediction", "experimental_validation"):
            self.assertFalse(self.data["scope"][key])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
