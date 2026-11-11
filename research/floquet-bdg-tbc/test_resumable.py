"""Contracts for nested randomness and resumable TBC winding chunks."""

import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from run_disorder import beta_for  # noqa: E402
from resumable_winding import resumable_winding  # noqa: E402
from run_scale_diagnostic import diagnostic_registry  # noqa: E402
from tbc_model import half_chiral_block, winding  # noqa: E402


class NestedSequenceTests(unittest.TestCase):
    def test_extended_streams_are_exactly_nested(self):
        self.assertEqual(len(beta_for(0, 400)), 400)
        np.testing.assert_array_equal(beta_for(0, 400)[:320], beta_for(0, 320))
        self.assertEqual(len(beta_for(0, 600)), 600)
        np.testing.assert_array_equal(beta_for(0, 600)[:400], beta_for(0, 400))
        np.testing.assert_array_equal(beta_for(0, 80), beta_for(0, 400)[:80])


class OneThetaTests(unittest.TestCase):
    def test_half_chiral_block_matches_contract(self):
        beta = beta_for(0, 20)
        parameters = {
            "n": 20, "mu0": np.full(20, 2.5), "mu1": 0.1 * beta,
            "omega": 7.0, "gamma": 1.0, "delta": 1.0,
        }
        result = half_chiral_block(parameters, 0.037, 0.0, free_method="eigh")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["block"].shape, (20, 20))
        self.assertGreater(result["bulk_gap"], 1e-8)
        self.assertLess(result["unitarity_error"], 1e-9)
        self.assertLess(result["max_condition"], 1e12)


class ResumableWindingTests(unittest.TestCase):
    def parameters(self, n=20):
        beta = beta_for(0, n)
        return {
            "n": n, "mu0": np.full(n, 2.5), "mu1": 0.1 * beta,
            "omega": 7.0, "gamma": 1.0, "delta": 1.0,
        }

    def test_chunk_resume_and_reference_equality(self):
        for method in ("expm", "eigh"):
            with self.subTest(method=method), tempfile.TemporaryDirectory(dir=ROOT) as folder:
                work_path = Path(folder) / "winding.json"
                parameters = self.parameters()
                first = resumable_winding(parameters, 0.2, 0.0, work_path, free_method=method, chunk_size=2, max_chunks=1)
                self.assertEqual(first["status"], "partial")
                self.assertEqual(first["next_index"], 2)
                self.assertIsNone(first["nearest_integer"])
                second = resumable_winding(parameters, 0.2, 0.0, work_path, free_method=method, chunk_size=2, max_chunks=1)
                self.assertEqual(second["next_index"], 4)
                self.assertEqual(len(second["integrands"]), 2)
                for _ in range(20):
                    final = resumable_winding(parameters, 0.2, 0.0, work_path, free_method=method, chunk_size=2, max_chunks=1)
                    if final["status"] != "partial":
                        break
                reference = winding(parameters, 0.2, 0.0, free_method=method)
                self.assertEqual(final["status"], reference["status"])
                self.assertAlmostEqual(final["value"], reference["value"], delta=1e-10)
                self.assertEqual(final["nearest_integer"], reference["nearest_integer"])
                self.assertAlmostEqual(final["min_bulk_gap"], reference["min_bulk_gap"], delta=1e-12)
                self.assertAlmostEqual(final["max_block_condition"], reference["max_block_condition"], delta=1e-6)
                indices = [row["index"] for row in final["integrands"]]
                self.assertEqual(len(indices), len(set(indices)))
                cache = np.load(final["cache_file"])
                self.assertEqual(set(cache.files), {"first0", "first1", "previous_previous", "previous"})
                self.assertEqual(cache["first0"].shape, (20, 20))

    def test_metadata_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as folder:
            work_path = Path(folder) / "winding.json"
            parameters = self.parameters()
            resumable_winding(parameters, 0.2, 0.0, work_path, chunk_size=2, max_chunks=1)
            with self.assertRaises(ValueError):
                resumable_winding(parameters, 0.1, 0.0, work_path, chunk_size=2, max_chunks=1)


class DiagnosticRegistryTests(unittest.TestCase):
    def test_n400_and_n600_have_distinct_rationales(self):
        cases = diagnostic_registry()
        self.assertEqual([case["n"] for case in cases], [400, 600])
        self.assertEqual(cases[0]["strength"], 0.1)
        self.assertEqual(cases[1]["strength"], 0.05)
        self.assertNotEqual(cases[0]["rationale"], cases[1]["rationale"])
        self.assertTrue(all(case["seed"] == 0 and case["target"] == "zero" for case in cases))


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
