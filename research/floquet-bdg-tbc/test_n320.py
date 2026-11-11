"""Contracts for accelerated free propagation and targeted N=320 cases."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from run_disorder import beta_for as beta_sequence  # noqa: E402
from run_n320 import merge_n320, n320_registry, run_n320  # noqa: E402
from tbc_model import free_evolution, twisted_majorana_k, winding_convergence  # noqa: E402


class SpectralBackendTests(unittest.TestCase):
    def parameters(self, n=20):
        beta = beta_sequence(2, n)
        return {"n": n, "mu0": np.full(n, 2.5), "mu1": 0.05 * beta, "omega": 7.0, "gamma": 1.0, "delta": 1.0}

    def test_eigh_free_propagator_matches_expm(self):
        n = 40
        k0 = twisted_majorana_k(np.full(n, 2.5), 0.037)
        time = np.pi / 7
        accelerated = free_evolution(k0, time, method="eigh")
        reference = free_evolution(k0, time, method="expm")
        self.assertLess(np.max(np.abs(accelerated - reference)), 1e-10)
        self.assertLess(np.max(np.abs(accelerated.conj().T @ accelerated - np.eye(2 * n))), 1e-10)

    def test_backend_winding_values_match(self):
        parameters = self.parameters()
        accelerated = winding_convergence(parameters, 0.0, (0.2, 0.1), free_method="eigh")
        reference = winding_convergence(parameters, 0.0, (0.2, 0.1), free_method="expm")
        self.assertEqual(accelerated["status"], reference["status"])
        self.assertEqual([row["status"] for row in accelerated["rows"]], [row["status"] for row in reference["rows"]])
        for fast_row, reference_row in zip(accelerated["rows"], reference["rows"]):
            self.assertIsNotNone(fast_row["value"])
            self.assertIsNotNone(reference_row["value"])
            self.assertLess(abs(fast_row["value"] - reference_row["value"]), 1e-9)

    def test_single_grid_cannot_claim_convergence(self):
        with self.assertRaises(ValueError):
            winding_convergence(self.parameters(), 0.0, (0.05,))


class N320RegistryTests(unittest.TestCase):
    def test_exact_seven_case_registry(self):
        cases = n320_registry()
        identities = {(row["strength"], row["seed"], row["kind"], row["target"]) for row in cases}
        self.assertEqual(len(cases), 7)
        self.assertEqual(len(identities), 7)
        self.assertTrue(all(row["target"] == "zero" for row in cases))
        self.assertIn((0.05, 2, "disorder", "zero"), identities)
        self.assertIn((0.05, 3, "disorder", "zero"), identities)
        self.assertIn((0.1, 2, "disorder", "zero"), identities)
        self.assertIn((0.05, 0, "disorder", "zero"), identities)
        self.assertIn((0.1, 0, "disorder", "zero"), identities)
        self.assertIn((0.05, 0, "uniform_mean", "zero"), identities)
        self.assertIn((0.1, 0, "uniform_mean", "zero"), identities)

    def test_incremental_checkpoint_and_incomplete_merge(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            path = Path(folder) / "n320.json"
            selector = lambda case: case["kind"] == "uniform_mean" and case["strength"] == 0.05
            first = run_n320(n=8, selector=selector, path=path, grid="0.05")
            self.assertEqual(len(first["rows"]), 0)
            self.assertEqual(len(first["partial"]["grid_results"]), 1)
            self.assertFalse(first["complete"])
            original = first["partial"]["grid_results"]["0.05"]["value"]
            second = run_n320(n=8, selector=selector, path=path, grid="0.025")
            self.assertEqual(len(second["rows"]), 1)
            self.assertNotIn("partial", second)
            self.assertFalse(second["complete"])
            self.assertEqual(second["rows"][0]["free_method"], "eigh")
            self.assertEqual(second["rows"][0]["zero"]["rows"][0]["value"], original)
            with self.assertRaisesRegex(ValueError, "incomplete N320 case registry"):
                merge_n320(path)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
