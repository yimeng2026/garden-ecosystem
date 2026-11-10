"""Independent reconstruction and boundary checks for the kick map."""

import csv
import hashlib
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from kick_map import evaluate_uniform  # noqa: E402
from bloch_topology import bloch_floquet  # noqa: E402
from localization_analysis import subspace_metrics  # noqa: E402
from convention_model import quasienergy_spectrum  # noqa: E402
from disorder_model import disordered_floquet  # noqa: E402


class IndependentKickMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))
        cls.sensitivity = json.loads((ROOT / "sensitivity.json").read_text(encoding="utf-8"))

    def test_selected_uniform_chain_reconstruction_and_rotation(self):
        n, a = 160, 0.1
        u, period = disordered_floquet(n, 2.5, np.ones(n), a, 7.0)
        self.assertLess(np.max(np.abs(u.T @ u - np.eye(2 * n))), 1e-12)
        spectrum = quasienergy_spectrum(u, period)
        observed = evaluate_uniform(n, a)
        recorded = next(row for row in self.data["grid"] if row["n"] == n and row["a"] == a)
        for target, value in (("zero", 1.0), ("pi", -1.0)):
            self.assertEqual(observed[target]["joint_pass"], recorded[target]["joint_pass"])
            self.assertAlmostEqual(observed[target]["edge_weight"], recorded[target]["edge_weight"], places=13)
            indices = np.argsort(np.abs(spectrum["eigenvalues"] - value))[:2]
            rotation = np.array([[1, 1], [1j, -1j]]) / np.sqrt(2)
            first = subspace_metrics(spectrum["eigenvectors"][:, indices], n)
            rotated = subspace_metrics(spectrum["eigenvectors"][:, indices] @ rotation, n)
            self.assertAlmostEqual(first["subspace_ipr"], rotated["subspace_ipr"], places=10)
            np.testing.assert_allclose(first["profile"], rotated["profile"], atol=1e-10)

    def test_both_singularities_have_correct_momentum_mapping(self):
        at_zero = bloch_floquet(0.0, mu0=2.5, mu1=0.0, omega=7.0, gamma=1.0, delta=1.0)
        np.testing.assert_allclose(at_zero, np.eye(2), atol=1e-12)
        at_critical = bloch_floquet(np.pi, mu0=2.5, mu1=np.pi / 14, omega=7.0, gamma=1.0, delta=1.0)
        np.testing.assert_allclose(at_critical, -np.eye(2), atol=1e-12)
        self.assertEqual(sum(row["endpoint"]["status"] == "gapless_or_undefined" for row in self.data["grid"]), 6)

    def test_candidate_counts_respect_the_analytic_transition(self):
        below = next(row for row in self.data["grid"] if row["n"] == 320 and row["a"] == 0.22)
        self.assertTrue(below["pi"]["joint_pass"])
        self.assertEqual(below["endpoint"]["p_pi"], 1)
        above = next(row for row in self.data["grid"] if row["n"] == 320 and row["a"] == 0.24)
        self.assertFalse(above["pi"]["joint_pass"])
        self.assertEqual(above["endpoint"]["p_pi"], 0)
        self.assertFalse(self.data["scope"]["disorder_winding_computed"])
        self.assertFalse(self.data["scope"]["thermodynamic_limit_proof"])

    def test_sensitivity_identity_categories_and_source_hash(self):
        source = ROOT.parent / "floquet-bdg-disorder" / "results.json"
        self.assertEqual(self.sensitivity["source_results_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        self.assertFalse(self.sensitivity["source_modified"])
        self.assertEqual(self.sensitivity["original_assessment"], "not_supported")
        for row in self.sensitivity["rows"]:
            self.assertAlmostEqual(row["mean_amplitude"], row["strength"] * row["mean_beta"], places=14)
        zero = [row for row in self.sensitivity["rows"] if row["n"] == 160 and row["strength"] == 0.1 and row["target"] == "zero"]
        self.assertEqual(sum(row["category"] == "fluctuation_sensitive" for row in zero), 15)
        self.assertEqual(sum(row["category"] == "both_pass" for row in zero), 1)
        pi = [row for row in self.sensitivity["rows"] if row["n"] == 160 and row["strength"] == 0.1 and row["target"] == "pi"]
        self.assertEqual(sum(row["category"] == "both_pass" for row in pi), 16)

    def test_raw_profiles_csvs_and_unitarity(self):
        self.assertLess(max(row["unitarity_error"] for row in self.data["grid"]), 1e-11)
        profiles = np.load(ROOT / "profiles.npz")
        for name in profiles.files:
            self.assertAlmostEqual(float(profiles[name].sum()), 1.0, places=9)
        for filename, count in (("uniform_grid.csv", 90), ("sensitivity.csv", 216)):
            with (ROOT / filename).open(encoding="utf-8", newline="") as stream:
                self.assertEqual(len(list(csv.DictReader(stream))), count)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
