"""Contracts for tail, envelope and IPR localization analysis."""

import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from localization_analysis import fit_envelope, subspace_metrics, tail_deficit_lengths  # noqa: E402


class LocalizationEstimatorTests(unittest.TestCase):
    def test_tail_estimator_recovers_synthetic_length(self):
        sizes = [40, 80, 160, 320]
        expected = 12.0
        weights = [1 - 0.8 * np.exp(-0.2 * n / expected) for n in sizes]
        rows = tail_deficit_lengths(sizes, weights, edge_fraction=0.1)
        for row in rows:
            self.assertAlmostEqual(row["xi_tail"], expected, places=10)
            self.assertEqual(row["status"], "ok")

    def test_tail_estimator_rejects_nonphysical_sign(self):
        rows = tail_deficit_lengths([40, 80], [0.4, 0.2], edge_fraction=0.1)
        self.assertEqual(rows[0]["status"], "undefined")

    def test_envelope_fit_recovers_synthetic_localization(self):
        n = 240
        j = np.arange(n)
        expected = 8.0
        weights = 2e-5 + 0.03 * (np.exp(-2 * j / expected) + np.exp(-2 * (n - 1 - j) / expected))
        weights /= weights.sum()
        result = fit_envelope(weights)
        self.assertAlmostEqual(result["xi_env"], expected, delta=0.1)
        self.assertGreater(result["r_squared"], 0.999)

    def test_subspace_metrics_are_invariant_under_basis_rotation(self):
        left = np.zeros(8, dtype=complex)
        right = np.zeros(8, dtype=complex)
        left[:2] = [1 / np.sqrt(2), 1 / np.sqrt(2)]
        right[-2:] = [1 / np.sqrt(2), 1 / np.sqrt(2)]
        vectors = np.column_stack([left, right])
        rotation = np.array([[1, 1], [1j, -1j]]) / np.sqrt(2)
        reference = subspace_metrics(vectors, n=4)
        rotated = subspace_metrics(vectors @ rotation, n=4)
        self.assertAlmostEqual(reference["subspace_ipr"], rotated["subspace_ipr"], places=12)
        np.testing.assert_allclose(reference["profile"], rotated["profile"], atol=1e-12)
        np.testing.assert_allclose(reference["profile"].sum(), 1.0, atol=1e-12)


class LocalizationArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))

    def test_grid_and_three_independent_evidence_channels(self):
        self.assertEqual(self.data["sizes"], [40, 80, 160, 320, 640])
        self.assertEqual(len(self.data["size_studies"]), 5)
        for target in ("zero", "pi"):
            self.assertEqual(len(self.data["tail_estimates"][target]), 4)
            self.assertEqual(len(self.data["envelope_fits"][target]), 5)
        self.assertIn(self.data["assessment"]["status"], {"short_chain_regime_supported", "partial_or_inconclusive"})
        self.assertIn("first_pair_subspace_ipr_plateau", self.data["assessment"]["criteria"]["zero"]["checks"])
        self.assertFalse(self.data["scope"]["thermodynamic_limit_proof"])
        self.assertFalse(self.data["scope"]["material_tc_prediction"])

    def test_raw_profiles_and_previous_convention_evidence_preserved(self):
        for study in self.data["size_studies"]:
            self.assertEqual(len(study["zero"]["profile"]), study["n"])
            self.assertEqual(len(study["pi"]["profile"]), study["n"])
            self.assertIn("second_pair_ipr", study["zero"])
        corrected = ROOT.parent / "floquet-bdg-convention" / "results.json"
        self.assertEqual(self.data["convention_results_sha256"], __import__("hashlib").sha256(corrected.read_bytes()).hexdigest())


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
