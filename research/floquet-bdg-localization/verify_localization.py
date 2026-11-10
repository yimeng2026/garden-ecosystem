"""Independent solver and scaling checks for the localization study."""

import csv
import hashlib
import json
import sys
import unittest
from pathlib import Path

import numpy as np
from scipy.linalg import eig

ROOT = Path(__file__).resolve().parent
CONVENTION = ROOT.parent / "floquet-bdg-convention"
sys.path.insert(0, str(CONVENTION))
sys.path.insert(0, str(ROOT))
from convention_model import kicked_floquet  # noqa: E402
from localization_analysis import subspace_metrics  # noqa: E402


class IndependentLocalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))

    def test_tail_lengths_are_recomputed_from_raw_weights(self):
        for target in ("zero", "pi"):
            weights = [study[target]["edge_weights"][0] for study in self.data["size_studies"]]
            for index, row in enumerate(self.data["tail_estimates"][target]):
                n1, n2 = self.data["sizes"][index : index + 2]
                d1, d2 = 1 - weights[index], 1 - weights[index + 1]
                xi = -0.2 * (n2 - n1) / (np.log(d2) - np.log(d1))
                self.assertAlmostEqual(row["xi_tail"], xi, places=9)
            self.assertLess(self.data["tail_estimates"][target][-1]["xi_tail"] / self.data["tail_estimates"][target][-2]["xi_tail"], 2)

    def test_scipy_solver_n640_subspace_is_basis_invariant(self):
        u, _ = kicked_floquet(640, **self.data["parameters"])
        values, vectors = eig(u)
        study = self.data["size_studies"][-1]
        for target, value in (("zero", 1.0), ("pi", -1.0)):
            distances = np.abs(values - value)
            indices = np.argsort(distances)[:2]
            metrics = subspace_metrics(vectors[:, indices], 640)
            recorded = study[target]
            profile = np.array(recorded["profile"])
            self.assertAlmostEqual(metrics["subspace_ipr"], recorded["subspace_ipr"], places=8)
            np.testing.assert_allclose(metrics["profile"], profile, atol=2e-8)
            edge_sites = 64
            edge_weight = metrics["profile"][np.r_[np.arange(edge_sites), np.arange(640 - edge_sites, 640)]].sum()
            self.assertAlmostEqual(edge_weight, recorded["edge_weights"][0], places=8)

    def test_all_preregistered_checks_pass_for_physical_reasons(self):
        self.assertEqual(self.data["assessment"]["status"], "short_chain_regime_supported")
        for target in ("zero", "pi"):
            row = self.data["assessment"]["criteria"][target]
            self.assertTrue(all(row["checks"].values()), target)
            metrics = row["metrics"]
            self.assertLess(metrics["first_pair_subspace_ipr_relative_change"], 0.1)
            self.assertGreater(metrics["second_pair_subspace_ipr_decay_factor"], 1.5)
            self.assertGreater(metrics["second_pair_n_subspace_ipr_ratio"], 0.5)
            self.assertLess(metrics["second_pair_n_subspace_ipr_ratio"], 2)

    def test_envelope_and_tail_scales_have_numerical_support(self):
        zero_fit = self.data["envelope_fits"]["zero"][-1]
        pi_fit = self.data["envelope_fits"]["pi"][-1]
        self.assertAlmostEqual(zero_fit["xi_env"], 9.695046184110538, places=6)
        self.assertAlmostEqual(pi_fit["xi_env"], 25.164968604694884, places=6)
        self.assertGreater(zero_fit["r_squared"], 0.75)
        self.assertGreater(pi_fit["r_squared"], 0.65)
        self.assertAlmostEqual(self.data["tail_estimates"]["zero"][-1]["xi_tail"], 11.721853527050074, places=7)
        self.assertAlmostEqual(self.data["tail_estimates"]["pi"][-1]["xi_tail"], 12.419694265678883, places=7)

    def test_short_chain_support_does_not_change_old_full_size_boundary(self):
        n40 = self.data["size_studies"][0]
        self.assertLess(n40["zero"]["edge_weights"][0], 0.5)
        self.assertLess(n40["pi"]["edge_weights"][0], 0.5)
        self.assertEqual(self.data["assessment"]["full_size_rule_status"], "inconclusive_preserved")
        self.assertFalse(self.data["assessment"]["thermodynamic_limit_proof"])
        self.assertFalse(self.data["scope"]["full_size_rule_status_changed"])

    def test_profiles_csv_and_convention_hashes(self):
        archive = np.load(ROOT / "profiles.npz")
        for n in self.data["sizes"]:
            for target in ("zero", "pi"):
                profile = archive[f"n{n}_{target}"]
                self.assertEqual(len(profile), n)
                self.assertAlmostEqual(float(profile.sum()), 1.0, places=10)
        with (ROOT / "localization.csv").open(encoding="utf-8", newline="") as stream:
            self.assertEqual(len(list(csv.DictReader(stream))), 10)
        corrected = CONVENTION / "results.json"
        self.assertEqual(self.data["convention_results_sha256"], hashlib.sha256(corrected.read_bytes()).hexdigest())


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
