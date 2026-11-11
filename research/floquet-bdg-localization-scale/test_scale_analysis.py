"""Synthetic and data-independent contracts for endpoint recovery-scale analysis."""

import sys
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from scale_analysis import assess_recovery, center_mass, coverage_lengths, end_cumulative, fixed_width_masses  # noqa: E402
from analyze_scale import analyze_all  # noqa: E402


class CoverageTests(unittest.TestCase):
    def test_direct_two_end_coverage_has_no_extra_half(self):
        profile = np.zeros(10)
        profile[0], profile[1], profile[-2], profile[-1] = 0.4, 0.1, 0.2, 0.3
        cumulative = end_cumulative(profile)
        self.assertAlmostEqual(cumulative[1], 1.0)
        self.assertEqual(coverage_lengths(profile), {"L50": 1, "L90": 2, "L99": 2})

    def test_nonuniform_coverages_and_ipr(self):
        profile = np.array([0.2, 0.1, 0.05, 0.05, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
        self.assertEqual(coverage_lengths(profile), {"L50": 2, "L90": 5, "L99": 5})
        self.assertAlmostEqual(center_mass(profile, fraction=0.2), 0.2)
        self.assertAlmostEqual(10 * float(np.sum(profile**2)), 1.15)

    def test_fixed_width_masses(self):
        profile = np.full(100, 0.01)
        self.assertAlmostEqual(fixed_width_masses(profile, widths=(5, 20))["5"], 0.1)
        self.assertAlmostEqual(fixed_width_masses(profile, widths=(5, 20))["20"], 0.4)
        self.assertAlmostEqual(center_mass(profile, fraction=0.2), 0.2)

    def test_profile_validation(self):
        with self.assertRaises(ValueError):
            end_cumulative(np.full(10, 0.2))


class RecoveryTests(unittest.TestCase):
    @staticmethod
    def row(n, l50, mass20, separation, joint_pass=False):
        return {
            "n": n, "L50": l50, "mass20": mass20,
            "separation": separation, "joint_pass": joint_pass,
        }

    def test_plateau_is_bounded_diagnostic(self):
        rows = [self.row(80, 20, 0.4, 0.08), self.row(160, 32, 0.5, 0.05), self.row(320, 31, 0.47, 0.04)]
        result = assess_recovery(rows)
        self.assertEqual(result["status"], "bounded_diagnostic")
        self.assertEqual(result["next_size"], 400)
        self.assertEqual(result["l50_bracket_times_ten"], [310, 320])

    def test_growth_is_not_established(self):
        rows = [self.row(80, 21, 0.4, 0.08), self.row(160, 31, 0.4, 0.05), self.row(320, 51, 0.4, 0.04)]
        result = assess_recovery(rows)
        self.assertEqual(result["status"], "not_established")
        self.assertIsNone(result["l50_bracket_times_ten"])
        self.assertEqual(result["next_size"], 600)

    def test_measured_recovery_is_not_an_estimate(self):
        rows = [self.row(80, 20, 0.4, 0.08), self.row(160, 35, 0.4, 0.05), self.row(320, 26, 0.6, 0.04, True)]
        result = assess_recovery(rows)
        self.assertEqual(result["status"], "measured_recovered")
        self.assertIsNone(result["next_size"])


class OriginalProfileTests(unittest.TestCase):
    def test_registry_and_actual_recovery_classes(self):
        data = analyze_all()
        self.assertEqual(data["case_count"], 5)
        self.assertEqual(data["profile_count"], 15)
        cases = {(case["strength"], case["seed"]): case for case in data["cases"]}
        self.assertEqual(cases[(0.05, 0)]["assessment"]["status"], "not_established")
        self.assertEqual(cases[(0.05, 0)]["assessment"]["next_size"], 600)
        self.assertEqual(cases[(0.1, 0)]["assessment"]["status"], "bounded_diagnostic")
        self.assertEqual(cases[(0.1, 0)]["assessment"]["next_size"], 400)
        self.assertEqual(cases[(0.1, 0)]["assessment"]["l50_bracket_times_ten"], [330, 380])
        for key in ((0.05, 2), (0.05, 3), (0.1, 2)):
            self.assertEqual(cases[key]["assessment"]["status"], "measured_recovered")
        self.assertEqual(cases[(0.05, 2)]["rows"][-1]["L50"], 26)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
