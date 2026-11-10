"""Contracts for the uniform kick map and exact disorder decomposition."""

import csv
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent / "floquet-bdg-convention"))
from convention_model import kicked_floquet  # noqa: E402
from kick_map import safe_endpoint_counts, uniform_floquet  # noqa: E402
from bloch_topology import bloch_floquet  # noqa: E402


class UniformModelTests(unittest.TestCase):
    def test_two_gapless_amplitudes_are_rejected(self):
        for a in (0.0, np.pi / 14):
            row = safe_endpoint_counts(a)
            self.assertEqual(row["status"], "gapless_or_undefined")
            self.assertIsNone(row["p0"])
            self.assertIsNone(row["p_pi"])

    def test_gapped_counts_and_negative_hopping_endpoint_map(self):
        row = safe_endpoint_counts(0.1)
        self.assertEqual((row["p0"], row["p_pi"]), (1, 1))
        self.assertEqual(safe_endpoint_counts(0.25)["p_pi"], 0)
        for k, key in ((0.0, "b_pi"), (np.pi, "b0")):
            u = bloch_floquet(k, mu0=2.5, mu1=0.1, omega=7.0, gamma=1.0, delta=1.0)
            b = row[key]
            np.testing.assert_allclose(u, np.diag([np.exp(1j * np.pi * b), np.exp(-1j * np.pi * b)]), atol=2e-13)

    def test_uniform_model_matches_validated_clean_model(self):
        actual, _ = uniform_floquet(8, 0.1)
        expected, _ = kicked_floquet(8, 2.5, 0.1, 7.0)
        np.testing.assert_allclose(actual, expected, atol=1e-14)


class UniformArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))

    def test_grid_has_45_records_and_two_unique_singular_amplitudes(self):
        self.assertEqual(len(self.data["grid"]), 45)
        self.assertEqual(sum(row["endpoint"]["status"] == "gapless_or_undefined" for row in self.data["grid"]), 6)
        self.assertEqual(len(self.data["analytic_singularities"]), 2)
        self.assertEqual(self.data["sizes"], [80, 160, 320, 640])
        with (ROOT / "uniform_grid.csv").open(encoding="utf-8", newline="") as stream:
            self.assertEqual(len(list(csv.DictReader(stream))), 90)

    def test_profiles_and_island_semantics(self):
        archive = np.load(ROOT / "profiles.npz")
        for row in self.data["grid"]:
            for target in ("zero", "pi"):
                self.assertAlmostEqual(float(archive[f"n{row['n']}_a{row['a']}_{target}"].sum()), 1.0, places=9)
        for row in self.data["pass_islands"]:
            if row["n"] == 640:
                self.assertTrue(row["selected_amplitudes_only"])
            else:
                self.assertEqual(row["interval_semantics"], "grid_samples_not_a_precision_boundary")


class SensitivityArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "sensitivity.json").read_text(encoding="utf-8"))

    def test_all_216_rows_and_exact_mean_identity(self):
        self.assertEqual(len(self.data["rows"]), 216)
        for row in self.data["rows"]:
            self.assertAlmostEqual(row["mean_amplitude"], row["strength"] * row["mean_beta"], places=14)
        with (ROOT / "sensitivity.csv").open(encoding="utf-8", newline="") as stream:
            self.assertEqual(len(list(csv.DictReader(stream))), 216)

    def test_mechanical_categories_match_previous_raw_outcomes(self):
        rows = self.data["summary"]
        zero_sensitive = next(row for row in rows if row["n"] == 160 and row["strength"] == 0.1 and row["target"] == "zero" and row["category"] == "fluctuation_sensitive")
        zero_both = next(row for row in rows if row["n"] == 160 and row["strength"] == 0.1 and row["target"] == "zero" and row["category"] == "both_pass")
        pi_both = next(row for row in rows if row["n"] == 160 and row["strength"] == 0.1 and row["target"] == "pi" and row["category"] == "both_pass")
        self.assertEqual((zero_sensitive["count"], zero_both["count"], pi_both["count"]), (15, 1, 16))


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
