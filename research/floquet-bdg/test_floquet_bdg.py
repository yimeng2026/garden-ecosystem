"""Contracts for the finite kicked-Kitaev Floquet-BdG study."""

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
    endpoint_mode_counts,
    kicked_floquet,
    majorana_k,
    quasienergy_spectrum,
    site_weights,
    static_null_vectors,
)


class AnalyticFloquetBdGTests(unittest.TestCase):
    def test_static_open_chain_has_exact_end_null_vectors(self):
        n = 12
        k = majorana_k(n, mu=0.0, gamma=1.0, delta=1.0)
        left, right = static_null_vectors(n)
        np.testing.assert_allclose(k @ left, np.zeros(2 * n), atol=1e-14)
        np.testing.assert_allclose(k @ right, np.zeros(2 * n), atol=1e-14)
        self.assertEqual(np.flatnonzero(left).tolist(), [0])
        self.assertEqual(np.flatnonzero(right).tolist(), [2 * n - 1])
        self.assertGreater(np.linalg.norm(majorana_k(n, 2.5) @ left), 1.0)

    def test_floquet_is_real_orthogonal_and_particle_hole_paired(self):
        u, period = kicked_floquet(10, mu0=2.5, mu1=0.2, omega=7.0)
        self.assertTrue(np.isrealobj(u))
        np.testing.assert_allclose(u.T @ u, np.eye(20), atol=2e-13)
        self.assertAlmostEqual(period, 2 * math.pi / 7)
        result = quasienergy_spectrum(u, period)
        np.testing.assert_allclose(np.abs(result["eigenvalues"]), np.ones(20), atol=3e-13)
        phases = np.sort(result["phase"])
        np.testing.assert_allclose(phases, np.sort((2 * np.pi - phases) % (2 * np.pi)), atol=2e-12)

    def test_endpoint_invariants_predict_one_zero_and_one_pi_per_edge(self):
        counts = endpoint_mode_counts(mu0=2.5, mu1=0.2, gamma=1.0, omega=7.0)
        self.assertAlmostEqual(counts["b0"], 6 / 7 + 0.4 / math.pi)
        self.assertAlmostEqual(counts["b_pi"], 2 + 0.4 / math.pi)
        self.assertEqual(counts["even_integers"], [2])
        self.assertEqual(counts["odd_integers"], [1])
        self.assertEqual((counts["p0"], counts["p_pi"]), (1, 1))

    def test_site_weights_and_candidates_are_derived_not_hardcoded(self):
        n = 20
        u, period = kicked_floquet(n, mu0=2.5, mu1=0.2, omega=7.0)
        spectrum = quasienergy_spectrum(u, period)
        weights = site_weights(spectrum["eigenvectors"], n)
        self.assertEqual(weights.shape, (n, 2 * n))
        np.testing.assert_allclose(weights.sum(axis=0), np.ones(2 * n), atol=1e-12)
        for target in (1.0, -1.0):
            candidate = candidate_modes(spectrum, n, target=target, edge_fraction=0.1)
            self.assertEqual(len(candidate["indices"]), 2)
            self.assertEqual(len(candidate["edge_weights"]), 2)
            self.assertGreater(candidate["bulk_distance"], 0)
            self.assertTrue(np.isfinite(candidate["separation_ratios"]).all())


class StudyArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))

    def test_study_grid_and_analytic_prediction(self):
        self.assertEqual(self.data["parameters"], {"gamma": 1.0, "delta": 1.0, "mu0": 2.5, "mu1": 0.2, "omega": 7.0})
        self.assertEqual(self.data["sizes"], [40, 80, 160])
        self.assertEqual((self.data["endpoint_invariants"]["p0"], self.data["endpoint_invariants"]["p_pi"]), (1, 1))
        self.assertEqual(len(self.data["size_studies"]), 3)
        self.assertFalse(self.data["scope"]["material_tc_prediction"])

    def test_candidates_contain_raw_evidence_and_separate_controls(self):
        for study in self.data["size_studies"]:
            self.assertGreaterEqual(study["unitarity_error"], 0)
            for target in ("zero", "pi"):
                row = study[target]
                self.assertEqual(len(row["eigenvalues_real"]), 2)
                self.assertEqual(len(row["eigenvalues_imag"]), 2)
                self.assertEqual(len(row["distances"]), 2)
                self.assertEqual(len(row["edge_weights"]), 2)
                self.assertGreater(row["bulk_distance"], 0)
        self.assertIn("static_trivial_control", self.data)
        self.assertIn("dense_sparse_comparison", self.data)

    def test_no_overclaim_and_reproducibility_metadata(self):
        for key in ("interactions", "dissipation", "self_consistent_pairing", "material_tc_prediction", "experimental_validation", "thermodynamic_limit_proof"):
            self.assertFalse(self.data["scope"][key])
        self.assertFalse(self.data["scope"]["fourier_truncation_applicable"])
        self.assertTrue(self.data["scope"]["exact_piecewise_matrix_exponential"])
        self.assertIn("numpy", self.data["environment"])
        self.assertIn("scipy", self.data["environment"])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
