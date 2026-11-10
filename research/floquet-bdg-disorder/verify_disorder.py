"""Independent checks for disorder, mean-matched controls and basis invariance."""

import csv
import json
import sys
import unittest
from pathlib import Path

import numpy as np
from scipy.linalg import expm

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from disorder_model import beta_sequence, chemical_kick, disordered_floquet, observe_candidate  # noqa: E402
from convention_model import majorana_k, quasienergy_spectrum  # noqa: E402
from localization_analysis import subspace_metrics  # noqa: E402


class IndependentDisorderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))

    def test_selected_realization_rebuilt_independently(self):
        n, seed, strength = 160, 0, 0.1
        beta = beta_sequence(seed, n)
        period = 2 * np.pi / 7
        free = expm(-4 * majorana_k(n, 2.5) * period)
        kick = chemical_kick(strength * beta)
        u = kick @ free @ kick
        expected, _ = disordered_floquet(n, 2.5, beta, strength, 7.0)
        np.testing.assert_allclose(u, expected, atol=2e-13)
        self.assertLess(np.max(np.abs(u.T @ u - np.eye(2 * n))), 1e-12)
        spectrum = quasienergy_spectrum(u, period)
        for target, value in (("zero", 1.0), ("pi", -1.0)):
            observed = observe_candidate(spectrum, n, value)
            recorded = next(row for row in self.data["realizations"] if row["n"] == n and row["seed"] == seed and row["strength"] == strength)[target]
            self.assertAlmostEqual(observed["edge_weight"], recorded["edge_weight"], places=12)
            self.assertAlmostEqual(observed["subspace_ipr"], recorded["subspace_ipr"], places=12)
            self.assertEqual(observed["joint_pass"], recorded["joint_pass"])
            vectors = spectrum["eigenvectors"]
            indices = np.argsort(np.abs(spectrum["eigenvalues"] - value))[:2]
            rotation = np.array([[1, 1], [1j, -1j]]) / np.sqrt(2)
            first = subspace_metrics(vectors[:, indices], n)
            rotated = subspace_metrics(vectors[:, indices] @ rotation, n)
            self.assertAlmostEqual(first["subspace_ipr"], rotated["subspace_ipr"], places=10)
            np.testing.assert_allclose(first["profile"], rotated["profile"], atol=1e-10)

    def test_mean_control_is_exactly_mean_matched_for_selected_case(self):
        n, seed, strength = 160, 0, 0.1
        beta = beta_sequence(seed, n)
        _, observed = __import__("run_disorder").evaluate(n, np.full(n, beta.mean()), strength)
        recorded = next(row for row in self.data["mean_matched"] if row["n"] == n and row["seed"] == seed and row["strength"] == strength)
        for target in ("zero", "pi"):
            observed[target].pop("profile")
            self.assertEqual(observed[target], recorded[target])

    def test_raw_pass_counts_reproduce_negative_main_verdict(self):
        for summary in self.data["summary"]:
            subset = [row for row in self.data["realizations"] if row["n"] == summary["n"] and row["strength"] == summary["strength"]]
            self.assertEqual(summary["pass_count"], sum(row[summary["target"]]["joint_pass"] for row in subset))
        self.assertEqual(self.data["assessment"]["status"], "not_supported")
        self.assertTrue(self.data["mean_control"]["original_assessment_unchanged"])
        self.assertEqual(self.data["assessment"]["full_size_rule_status"], "inconclusive_preserved")

    def test_mode_and_parameter_specific_mean_comparison(self):
        rows = {(row["n"], row["strength"], row["target"]): row for row in self.data["comparisons"]}
        zero160 = rows[(160, 0.1, "zero")]
        self.assertEqual((zero160["disorder_pass_count"], zero160["uniform_mean_pass_count"]), (1, 16))
        pi160 = rows[(160, 0.1, "pi")]
        self.assertEqual((pi160["disorder_pass_count"], pi160["uniform_mean_pass_count"]), (16, 16))
        zero320 = rows[(320, 0.1, "zero")]
        self.assertEqual((zero320["disorder_pass_count"], zero320["uniform_mean_pass_count"]), (1, 4))
        pi320 = rows[(320, 0.1, "pi")]
        self.assertEqual((pi320["disorder_pass_count"], pi320["uniform_mean_pass_count"]), (4, 4))

    def test_all_unitarity_profiles_and_csvs(self):
        self.assertLess(max(row["unitarity_error"] for row in self.data["realizations"]), 1e-11)
        profiles = np.load(ROOT / "profiles.npz")
        for name in profiles.files:
            self.assertAlmostEqual(float(profiles[name].sum()), 1.0, places=9)
        for filename in ("realizations.csv", "mean_matched.csv"):
            with (ROOT / filename).open(encoding="utf-8", newline="") as stream:
                self.assertEqual(len(list(csv.DictReader(stream))), 216)

    def test_no_disorder_topology_or_material_overclaim(self):
        for key in ("disorder_winding_computed", "thermodynamic_limit_proof", "material_tc_prediction", "experimental_validation", "interactions", "dissipation"):
            self.assertFalse(self.data["scope"][key])
        self.assertTrue(self.data["scope"]["mean_matched_control_included"])
        self.assertTrue(self.data["scope"]["zero_kick_reference_included"])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
