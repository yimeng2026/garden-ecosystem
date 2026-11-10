"""Independent numerical and scope checks for the finite Floquet-BdG artifacts."""

import csv
import json
import math
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from floquet_bdg import (  # noqa: E402
    candidate_modes,
    kicked_floquet,
    majorana_k,
    quasienergy_spectrum,
    static_null_vectors,
)


class IndependentFloquetBdGTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))

    def test_majorana_generator_and_static_null_space(self):
        for n in (4, 9, 20):
            k = majorana_k(n, 0.0)
            np.testing.assert_allclose(k, -k.T, atol=0)
            for vector in static_null_vectors(n):
                np.testing.assert_allclose(k @ vector, np.zeros(2 * n), atol=1e-15)

    def test_every_recorded_size_reproduces_unitary_spectrum(self):
        for study in self.data["size_studies"]:
            n = study["n"]
            u, period = kicked_floquet(n, 2.5, 0.2, 7.0)
            self.assertLess(np.max(np.abs(u.T @ u - np.eye(2 * n))), 1e-12)
            spectrum = quasienergy_spectrum(u, period)
            self.assertTrue(np.isrealobj(u))
            for label, target in (("zero", 1.0), ("pi", -1.0)):
                candidate = candidate_modes(spectrum, n, target)
                recorded = study[label]
                np.testing.assert_allclose(candidate["distances"], recorded["distances"], rtol=1e-10, atol=1e-14)
                np.testing.assert_allclose(candidate["edge_weights"], recorded["edge_weights"], rtol=1e-10, atol=1e-14)
                self.assertAlmostEqual(candidate["bulk_distance"], recorded["bulk_distance"], places=14)

    def test_pi_mode_passes_preregistered_finite_size_contract(self):
        row = self.data["convergence"]["pi"]
        self.assertEqual(row["finite_size_status"], "supported_finite_size")
        self.assertTrue(row["strictly_decreasing"])
        self.assertTrue(row["all_candidates_localized"])
        self.assertTrue(row["all_candidates_separated"])
        self.assertGreater(row["first_to_last_reduction_factor"], 19000)
        n160 = self.data["size_studies"][-1]["pi"]
        self.assertLess(max(n160["distances"]), 1e-6)
        self.assertGreater(min(n160["edge_weights"]), 0.9)
        self.assertLess(max(n160["separation_ratios"]), 0.1)

    def test_zero_mode_is_not_promoted_past_failed_separation(self):
        row = self.data["convergence"]["zero"]
        self.assertEqual(row["finite_size_status"], "inconclusive")
        self.assertTrue(row["strictly_decreasing"])
        self.assertFalse(row["all_candidates_localized"])
        self.assertFalse(row["all_candidates_separated"])
        n160 = self.data["size_studies"][-1]["zero"]
        self.assertLess(max(n160["distances"]), 1e-6)
        self.assertGreater(min(n160["edge_weights"]), 0.9)
        self.assertGreater(max(n160["separation_ratios"]), 0.1)

    def test_dense_sparse_crosscheck_is_real_and_close(self):
        comparison = self.data["dense_sparse_comparison"]
        self.assertEqual(comparison["n"], 160)
        for target in ("zero", "pi"):
            row = comparison[target]
            self.assertTrue(row["passed_tolerance_1e-8"])
            self.assertLess(row["max_absolute_difference"], 1e-12)
            self.assertTrue(any(abs(value) > 0 for value in row["sparse_pair_imag"]))

    def test_static_trivial_control_fails_joint_edge_rule(self):
        control = self.data["static_trivial_control"]
        for target in ("zero", "pi"):
            row = control[target]
            accepted = [local and separated for local, separated in zip(row["localized"], row["separated"])]
            self.assertFalse(any(accepted), target)
            self.assertLess(max(row["edge_weights"]), 0.5)

    def test_raw_npz_and_csv_match_candidate_records(self):
        archive = np.load(ROOT / "spectra.npz")
        for study in self.data["size_studies"]:
            n = study["n"]
            self.assertEqual(len(archive[f"n{n}_eigenvalues"]), 2 * n)
            np.testing.assert_allclose(np.abs(archive[f"n{n}_eigenvalues"]), 1, atol=1e-12)
        with (ROOT / "candidates.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 12)
        self.assertEqual({int(row["n"]) for row in rows}, {40, 80, 160})

    def test_no_physics_or_completion_overclaim(self):
        self.assertFalse(self.data["convergence"]["zero"]["thermodynamic_limit_proof"])
        self.assertFalse(self.data["convergence"]["pi"]["thermodynamic_limit_proof"])
        for key in ("interactions", "dissipation", "self_consistent_pairing", "material_tc_prediction", "experimental_validation", "thermodynamic_limit_proof", "fourier_truncation_applicable"):
            self.assertFalse(self.data["scope"][key])
        self.assertTrue(self.data["scope"]["exact_piecewise_matrix_exponential"])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
