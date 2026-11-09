import math
import unittest

from plot_surface_code_threshold import render_svg
from surface_code_stats import wilson_interval
from verify_surface_code_threshold import verify_payload


class OutputTests(unittest.TestCase):
    def test_verifier_recomputes_rates(self):
        rate, low, high = wilson_interval(2, 100)
        payload = {"protocol_sha256": "abc", "points": [
            {"distance": 3, "p": 0.005, "shots": 100, "errors": 2,
             "rate": rate, "wilson95_low": low, "wilson95_high": high,
             "log10_rate": math.log10(rate), "seed": 7}
        ], "crossing_summary": {"crossings": [], "skipped_pairs": [], "median": None,
                                 "minimum": None, "maximum": None}}
        self.assertEqual(verify_payload(payload, "abc")["mismatches"], [])

    def test_verifier_rejects_tampered_rate(self):
        rate, low, high = wilson_interval(2, 100)
        payload = {"protocol_sha256": "abc", "points": [
            {"distance": 3, "p": 0.005, "shots": 100, "errors": 2,
             "rate": 0.03, "wilson95_low": low, "wilson95_high": high,
             "log10_rate": math.log10(rate), "seed": 7}
        ], "crossing_summary": {"crossings": [], "skipped_pairs": [], "median": None,
                                 "minimum": None, "maximum": None}}
        self.assertTrue(verify_payload(payload, "abc")["mismatches"])

    def test_svg_contains_real_coordinates_and_labels(self):
        svg = render_svg([{"distance": 3, "p": 0.005, "rate": 0.02,
                           "wilson95_low": 0.01, "wilson95_high": 0.03}])
        self.assertIn("Logical error rate per shot", svg)
        self.assertIn("0.005", svg)
        self.assertIn("d=3", svg)
        self.assertNotIn("<script", svg)


if __name__ == "__main__":
    unittest.main()
