"""Independently verify source excerpts and arithmetic for the audit."""

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class PrimarySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))
        cls.text = (ROOT / "sources/primary-source-excerpts.md").read_text(encoding="utf-8")
        path = ROOT / "numeric_spotcheck.py"
        spec = importlib.util.spec_from_file_location("validation_numeric_spotcheck", path)
        cls.numeric = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.numeric)

    def test_lanio2_source_and_dome(self):
        self.assertIn("未掺杂和低掺杂", self.text)
        self.assertIn("均绝缘", self.text)
        self.assertIn("0.15 < x < 0.3", self.text)
        row = self.data["evidence"]["lanio2"]
        self.assertTrue(row["undoped_insulating"])
        self.assertEqual(row["superconducting_dome"], [0.15, 0.3])

    def test_grockowiak_source_and_role(self):
        for text in ("初始 Tc 为 294 K", "不可逆地达到 556 K", "没有 Meissner 测量", "非零电阻背景"):
            self.assertIn(text, self.text)
        row = self.data["evidence"]["grockowiak"]
        self.assertTrue(row["irreversible_higher_order"])
        self.assertFalse(row["binary_lah10_routine_validation"])

    def test_cl_source_values(self):
        self.assertIn("6.25% Cl 掺杂将其降至 161 K", self.text)
        self.assertIn("12.5% Cl 掺杂在 200 GPa 时为 136 K", self.text)
        rows = self.data["evidence"]["cl_doping"]["results"]
        self.assertEqual([row["tc_k"] for row in rows], [161, 136])
        self.assertTrue(all(row["pressure_gpa"] == 200 for row in rows))

    def test_independent_arithmetic(self):
        h3s, _ = self.numeric.simplified_tc(1200.0, 2.0, 0.13)
        hscl, _ = self.numeric.simplified_tc(1500.0, 2.5, 0.12)
        self.assertAlmostEqual(h3s, self.data["evidence"]["formula_spotcheck"]["h3s"]["computed_tc_k"])
        self.assertAlmostEqual(hscl, self.data["evidence"]["formula_spotcheck"]["h_s_cl"]["computed_tc_k"])

    def test_scoring_rubric_absent(self):
        self.assertIn("没有给出指标定义、权重、样本集、误差模型或复算公式", self.text)
        self.assertFalse(self.data["evidence"]["scoring"]["rubric_available"])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
