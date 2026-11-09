import unittest

from surface_code_stats import crossing, estimate_crossings, protocol_digest, validate_protocol, wilson_interval


class StatisticsTests(unittest.TestCase):
    def test_protocol_digest_is_line_ending_and_whitespace_independent(self):
        compact = b'{"shots":20000,"distances":[3,5]}'
        expanded = b'{\r\n  "distances": [3, 5],\r\n  "shots": 20000\r\n}\r\n'
        self.assertEqual(protocol_digest(compact), protocol_digest(expanded))

    def test_wilson_handles_boundaries_and_center(self):
        self.assertEqual(wilson_interval(0, 100)[0], 0.0)
        self.assertEqual(wilson_interval(100, 100)[2], 1.0)
        rate, low, high = wilson_interval(50, 100)
        self.assertEqual(rate, 0.5)
        self.assertLess(low, 0.5)
        self.assertGreater(high, 0.5)

    def test_wilson_rejects_invalid_counts(self):
        for errors, shots in [(-1, 100), (101, 100), (1, 0), (True, 100), (1, True)]:
            with self.subTest(errors=errors, shots=shots):
                with self.assertRaises(ValueError):
                    wilson_interval(errors, shots)

    def test_crossing_is_exact_on_synthetic_lines(self):
        xs = [0.006, 0.008]
        small = [-0.3, -1.3]
        large = [-1.3, -0.3]
        self.assertAlmostEqual(crossing(xs, small, large), 0.007)

    def test_crossing_rejects_non_crossing_lines(self):
        with self.assertRaises(ValueError):
            crossing([0.006, 0.008], [-0.3, -0.4], [-1.3, -1.4])

    def test_protocol_rejects_even_distance_and_bad_probability(self):
        with self.assertRaises(ValueError):
            validate_protocol({"distances": [4], "probabilities": [0.005], "shots": 10})
        with self.assertRaises(ValueError):
            validate_protocol({"distances": [3], "probabilities": [1.2], "shots": 10})

    def test_protocol_rejects_duplicates_and_invalid_shots(self):
        with self.assertRaises(ValueError):
            validate_protocol({"distances": [3, 3], "probabilities": [0.005], "shots": 10})
        with self.assertRaises(ValueError):
            validate_protocol({"distances": [3], "probabilities": [0.005], "shots": True})

    def test_crossing_estimator_preserves_pair_and_range(self):
        points = []
        curves = {3: [-0.3, -1.3], 5: [-1.3, -0.3]}
        for distance, log_rates in curves.items():
            for index, p in enumerate([0.006, 0.008]):
                points.append({"distance": distance, "p": p,
                               "log10_rate": log_rates[index]})
        result = estimate_crossings(points)
        self.assertEqual(result["crossings"][0]["pair"], [3, 5])
        self.assertAlmostEqual(result["median"], 0.007)
        self.assertAlmostEqual(result["minimum"], 0.007)
        self.assertAlmostEqual(result["maximum"], 0.007)


if __name__ == "__main__":
    unittest.main()
