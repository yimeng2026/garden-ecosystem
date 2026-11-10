"""Independent checks of the corrected convention, topology and open-chain artifacts."""

import csv
import hashlib
import json
import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
LEGACY = ROOT.parent / "floquet-bdg" / "results.json"
EXPECTED_LEGACY = "c9c9fda60775bd5e509b7a07e44a6f196c7a58ef7365ebe28cd7eab7b17fe15c"
sys.path.insert(0, str(ROOT))

from convention_model import candidate_modes, kicked_floquet, majorana_k, quasienergy_spectrum  # noqa: E402
from fock_reference import fermion_operators, fock_hamiltonian, majorana_fock_hamiltonian, majorana_operators  # noqa: E402


class IndependentCorrectedTopologyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "results.json").read_text(encoding="utf-8"))

    def test_fock_matrix_and_legacy_preservation(self):
        c = fermion_operators(2)
        gammas = majorana_operators(c)
        reference = fock_hamiltonian(c, 0.37, 0.81, 0.53)
        represented = majorana_fock_hamiltonian(majorana_k(2, 0.37, 0.81, 0.53), gammas)
        np.testing.assert_allclose(reference, represented, atol=2e-13)
        self.assertEqual(hashlib.sha256(LEGACY.read_bytes()).hexdigest(), EXPECTED_LEGACY)
        self.assertEqual(self.data["convention"]["legacy_results_sha256"], EXPECTED_LEGACY)
        self.assertFalse(self.data["convention"]["legacy_results_modified"])
        self.assertFalse(self.data["convention"]["legacy_conclusions_inherited"])

    def test_winding_grid_and_controls(self):
        rows = self.data["winding"]["rows"]
        self.assertEqual([row["nk"] for row in rows], [512, 1024, 2048, 4096])
        for row in rows:
            self.assertEqual(row["nearest_integer"], 2)
            self.assertLess(abs(row["winding"] - 2), 1e-12)
            self.assertGreater(row["min_sin_phi"], 0.04)
        self.assertLess(self.data["winding"]["max_adjacent_difference"], 1e-12)
        self.assertEqual(self.data["winding"]["controls"]["static_trivial_omega17"]["nearest_integer"], 0)
        self.assertEqual(self.data["winding"]["controls"]["static_topological_mu0"]["nearest_integer"], -1)
        for row in self.data["winding"]["logm_direction_checks"]:
            self.assertAlmostEqual(row["direction_dot"], 1.0, places=10)

    def test_open_chain_n160_recomputation(self):
        study = self.data["size_studies"][-1]
        self.assertEqual(study["n"], 160)
        u, period = kicked_floquet(160, **self.data["parameters"])
        spectrum = quasienergy_spectrum(u, period)
        self.assertLess(np.max(np.abs(u.T @ u - np.eye(320))), 1e-12)
        for target, value in (("zero", 1.0), ("pi", -1.0)):
            candidate = candidate_modes(spectrum, 160, value)
            recorded = study[target]
            np.testing.assert_allclose(candidate["distances"], recorded["distances"], atol=1e-14)
            np.testing.assert_allclose(candidate["edge_weights"], recorded["edge_weights"], atol=1e-13)
            self.assertLess(max(recorded["distances"]), 1e-7)
            self.assertLess(max(recorded["separation_ratios"]), 1e-5)
            self.assertGreater(min(recorded["edge_weights"]), 0.9)

    def test_second_pair_is_not_another_edge_pair_at_n160(self):
        study = self.data["size_studies"][-1]
        for target in ("zero", "pi"):
            pairs = study[f"{target}_nearest_pairs"]
            self.assertEqual(len(pairs), 4)
            first, second = pairs[:2]
            self.assertGreater(second["max_distance"], 0.04)
            self.assertLess(max(second["edge_weights"]), 0.13)
            self.assertLess(first["max_distance"] / second["max_distance"], 1e-5)
            self.assertGreater(min(first["edge_weights"]), 0.9)

    def test_full_size_rule_remains_honest_about_short_chains(self):
        self.assertEqual(self.data["sizes"], [40, 80, 160])
        n40 = self.data["size_studies"][0]
        self.assertLess(min(n40["zero"]["edge_weights"]), 0.5)
        self.assertLess(min(n40["pi"]["edge_weights"]), 0.5)
        for target in ("zero", "pi"):
            row = self.data["convergence"][target]
            self.assertEqual(row["finite_size_status"], "inconclusive")
            self.assertTrue(row["all_candidates_separated"])
            self.assertFalse(row["all_candidates_localized"])
            self.assertTrue(row["strictly_decreasing"])
            self.assertGreater(row["first_to_last_reduction_factor"], 28000)
            self.assertFalse(row["thermodynamic_limit_proof"])

    def test_static_trivial_open_control_and_raw_artifacts(self):
        for target in ("zero", "pi"):
            control = self.data["static_trivial_control"][target]
            accepted = [local and separated for local, separated in zip(control["localized"], control["separated"])]
            self.assertFalse(any(accepted))
        archive = np.load(ROOT / "spectra.npz")
        for n in self.data["sizes"]:
            self.assertEqual(len(archive[f"n{n}_eigenvalues"]), 2 * n)
            np.testing.assert_allclose(np.abs(archive[f"n{n}_eigenvalues"]), 1, atol=1e-12)
        with (ROOT / "candidates.csv").open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 24)

    def test_no_material_or_experimental_overclaim(self):
        for key in ("interactions", "dissipation", "self_consistent_pairing", "material_tc_prediction", "experimental_validation", "thermodynamic_limit_proof", "legacy_results_overwritten"):
            self.assertFalse(self.data["scope"][key])
        self.assertTrue(self.data["scope"]["fock_convention_checked"])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
