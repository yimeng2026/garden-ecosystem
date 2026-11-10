"""Independently check review.json against saved primary-source evidence."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class PrimarySourceConsistencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))
        cls.xie = (ROOT / "sources/xie-floquet-fulltext.txt").read_text(encoding="utf-8")
        cls.official = (ROOT / "sources/official-source-excerpts.md").read_text(encoding="utf-8")

    def test_xie_high_pressure_mapping(self):
        self.assertIn("Tc from 258 K at equilibrium to 320 K", self.xie)
        self.assertIn("Tc rises from 237 K to 322 K", self.xie)
        rows = self.data["evidence"]["floquet"]["dfpt_estimates"]
        self.assertEqual(
            {row["pressure_gpa"]: (row["equilibrium_tc_k"], row["driven_tc_k"]) for row in rows},
            {220: (258, 320), 250: (237, 322)},
        )

    def test_xie_lower_bound_and_hydride_scope(self):
        self.assertIn("the Tc rises from 249 K to 285 K for 150 GPa", self.xie)
        self.assertIn("from 240 K to 301 K", self.xie)
        self.assertIn("should not be regarded as an accurate prediction", self.xie)
        self.assertIn("it acts as the lower bound", self.xie)
        self.assertIn("However, not all of", self.xie)
        self.assertIn("these hydrides achieve superconductivity above room temperature", self.xie)
        rows = self.data["evidence"]["floquet"]["dos_scaling_estimates"]
        self.assertTrue(all(row["role"] == "lower_bound_not_accurate_prediction" for row in rows))
        self.assertTrue(self.data["evidence"]["floquet"]["not_all_hydrides_above_room_temperature"])

    def test_aps_bibliography_and_scope(self):
        for excerpt in (
            "Phys. Rev. Lett. 133 , 256003 – Published 19 December, 2024",
            "widths up to W = 6",
            "about 0.15 J",
            "pairing correlations are much weaker",
        ):
            self.assertIn(excerpt, self.official)
        row = self.data["evidence"]["dmrg"]
        self.assertEqual((row["volume"], row["article"]), (133, "256003"))
        self.assertEqual(row["max_cylinder_width"], 6)
        self.assertEqual(row["max_characteristic_tc_star_over_j"], 0.15)

    def test_pnas_prediction_and_issue(self):
        for excerpt in (
            "121 (26) e2401840121",
            "we report the prediction",
            "331 K at 250 GPa and 316 K at 167 GPa",
            "dynamically stable down to 150 GPa",
        ):
            self.assertIn(excerpt, self.official)
        row = self.data["evidence"]["lasc2h24"]
        self.assertEqual(row["issue"], 26)
        self.assertTrue(row["theoretical_prediction"])
        self.assertFalse(row["experimental_confirmation"])

    def test_kiessling_constant_roles(self):
        self.assertIn("Although not optimal", self.official)
        self.assertIn("2.034", self.official)
        self.assertIn("0.1827262477", self.official)
        self.assertIn("sharp constant", self.official)
        row = self.data["evidence"]["eliashberg"]
        self.assertFalse(row["upper_bound_is_sharp"])
        self.assertAlmostEqual(row["upper_bound_coefficient"], row["sharp_constant"] * 2.034)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
