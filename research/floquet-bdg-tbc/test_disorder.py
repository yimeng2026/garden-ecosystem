"""Contracts for preregistered TBC disorder and matched-mean evaluation."""

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from run_disorder import (  # noqa: E402
    beta_for,
    evaluate_realization,
    merge_checkpoints,
    require_baseline,
    run_strength,
    run_strength_incremental,
)


class DisorderContractTests(unittest.TestCase):
    def test_fixed_sequence_and_full_kick_amplitude(self):
        beta = beta_for(0, 80)
        expected = np.random.default_rng(20261111).random(320)[:80]
        np.testing.assert_array_equal(beta, expected)
        row = evaluate_realization(8, 0, 0.05, "disorder", (0.2, 0.1))
        self.assertEqual(row["full_kick_parameter"], "2*r*beta")
        self.assertEqual(row["kind"], "disorder")
        self.assertEqual(row["seed"], 0)
        self.assertEqual(row["beta_sha256"], hashlib.sha256(beta_for(0, 8).tobytes()).hexdigest())
        json.dumps(row)

    def test_uniform_control_is_separate(self):
        row = evaluate_realization(8, 0, 0.05, "uniform_mean", (0.2, 0.1))
        self.assertEqual(row["kind"], "uniform_mean")
        self.assertEqual(row["beta_sha256"], hashlib.sha256(np.ones(8).tobytes()).hexdigest())
        json.dumps(row)

    def test_baseline_failure_blocks_promotion(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            path = Path(folder) / "results.json"
            path.write_text(json.dumps({"status": "clean_floquet_baseline_failed"}), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                require_baseline(path)

    def test_current_baseline_admits_disorder(self):
        data = require_baseline(ROOT / "results.json")
        self.assertEqual(data["status"], "clean_floquet_baseline_passed")
        self.assertTrue(data["static"]["passed"])

    def test_strength_checkpoint_row_counts(self):
        result = run_strength(0.05, n=8, seeds=(0, 1), nominal_steps=(0.2, 0.1))
        self.assertEqual(len(result["rows"]), 4)
        self.assertEqual({(row["seed"], row["kind"]) for row in result["rows"]}, {
            (0, "disorder"), (0, "uniform_mean"),
            (1, "disorder"), (1, "uniform_mean"),
        })
        self.assertTrue(all(row["n"] == 8 for row in result["rows"]))

    def test_partial_checkpoints_cannot_complete(self):
        with self.assertRaisesRegex(ValueError, "incomplete preregistered disorder checkpoints"):
            merge_checkpoints([Path("missing-r0p05.json")])

    def test_incremental_checkpoint_resumes_without_recomputing(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            path = Path(folder) / "checkpoint.json"
            first = run_strength_incremental(0.05, n=8, seeds=(0,), nominal_steps=(0.2, 0.1), path=path, expected_seeds=(0, 1))
            self.assertEqual(len(first["rows"]), 2)
            self.assertFalse(first["complete"])
            original = json.dumps(first["rows"], sort_keys=True)
            second = run_strength_incremental(0.05, n=8, seeds=(0, 1), nominal_steps=(0.2, 0.1), path=path, expected_seeds=(0, 1))
            self.assertEqual(len(second["rows"]), 4)
            self.assertTrue(second["complete"])
            retained = [row for row in second["rows"] if row["seed"] == 0]
            self.assertEqual(json.dumps(retained, sort_keys=True), original)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
