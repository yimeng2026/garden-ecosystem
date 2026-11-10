"""Contracts for targeted finite-size TBC zero-gap evaluation."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from run_disorder import beta_for, evaluate_realization  # noqa: E402
from run_finite_size import case_registry, merge_complete, run_cases  # noqa: E402


class FiniteSizeTargetTests(unittest.TestCase):
    def test_zero_only_evaluation_preserves_amplitude_contract(self):
        row = evaluate_realization(8, 0, 0.05, "disorder", (0.2, 0.1), targets=("zero",))
        self.assertIn("zero", row)
        self.assertNotIn("pi", row)
        self.assertLess(row["half_kick_convention_error"], 1e-12)

    def test_preregistered_registry(self):
        cases = case_registry()
        self.assertEqual(len(cases), 11)
        identities = {(row["strength"], row["seed"], row["kind"], row["target"]) for row in cases}
        self.assertEqual(len(identities), 11)
        self.assertTrue(all(row["target"] == "zero" for row in cases))
        uniform = [row for row in cases if row["kind"] == "uniform_mean"]
        disorder = [row for row in cases if row["kind"] == "disorder"]
        self.assertEqual({row["strength"] for row in uniform}, {0.05, 0.1, 0.2})
        self.assertEqual(len(uniform), 3)
        self.assertEqual(len(disorder), 8)
        self.assertEqual({row["strength"] for row in disorder}, {0.05, 0.1})

    def test_nested_beta_sequence(self):
        for seed in range(4):
            np.testing.assert_array_equal(
                beta_for(seed, 160),
                np.random.default_rng(20261111 + seed).random(320)[:160],
            )

    def test_incremental_case_checkpoint_and_incomplete_merge(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            path = Path(folder) / "finite.json"
            selector = lambda case: case["kind"] == "uniform_mean" and case["strength"] == 0.05
            first = run_cases(n=8, selector=selector, path=path)
            self.assertEqual(len(first["rows"]), 1)
            self.assertFalse(first["complete"])
            original = json.dumps(first["rows"], sort_keys=True)
            second = run_cases(n=8, selector=selector, path=path)
            self.assertEqual(json.dumps(second["rows"], sort_keys=True), original)
            with self.assertRaisesRegex(ValueError, "incomplete finite-size case registry"):
                merge_complete(path)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
