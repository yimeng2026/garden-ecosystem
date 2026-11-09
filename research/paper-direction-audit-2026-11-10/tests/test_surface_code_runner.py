import unittest

from run_surface_code_threshold import build_circuit, run_point


class RunnerTests(unittest.TestCase):
    def test_zero_noise_has_no_logical_errors(self):
        circuit = build_circuit(3, 0.0)
        self.assertGreater(circuit.num_detectors, 0)
        result = run_point(3, 0.0, shots=20, seed=7)
        self.assertEqual(result["errors"], 0)
        self.assertEqual(result["shots"], 20)
        self.assertIsNone(result["log10_rate"])

    def test_real_small_run_has_verifiable_counts(self):
        result = run_point(3, 0.01, shots=20, seed=11)
        self.assertGreaterEqual(result["errors"], 0)
        self.assertLessEqual(result["errors"], 20)
        self.assertEqual(result["rate"], result["errors"] / 20)

    def test_same_seed_is_reproducible(self):
        first = run_point(3, 0.01, shots=30, seed=19)
        second = run_point(3, 0.01, shots=30, seed=19)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
