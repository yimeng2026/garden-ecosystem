import json
import sys
import unittest
from pathlib import Path

from numeric_checks import critical_tc, mev_to_kelvin, tc, theta_threshold

ROOT = Path(__file__).resolve().parent
SOURCE_ROOT = next(
    parent / "toe-sylva-audit/papers/room_temp_sc/organized"
    for parent in ROOT.parents
    if (parent / "toe-sylva-audit/papers/room_temp_sc/organized").is_dir()
)


def load_review(name):
    return json.loads((ROOT.parent / name / "review.json").read_text(encoding="utf-8"))


class PrimarySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intro = (SOURCE_ROOT / "08-手册章节/01-第1-2章_超导入门与科普.md").read_text(encoding="utf-8")
        cls.theorem = (SOURCE_ROOT / "08-手册章节/02-第3章_必然性定理.md").read_text(encoding="utf-8")
        cls.foundations = (ROOT / "sources/physics-foundations.md").read_text(encoding="utf-8")
        cls.main = load_review("main-claims")
        cls.theory = load_review("theory-breakthrough")
        cls.governance = load_review("data-governance")

    def test_bcs_is_coherent_pairs_not_simple_boson_gas(self):
        self.assertIn("formed from a linear combination of normal state configurations", self.foundations)
        self.assertIn("virtually excited in pairs of opposite spin and momentum", self.foundations)
        self.assertIn("只能作为有限类比", self.foundations)

    def test_mcmillan_cap_is_not_universal(self):
        self.assertIn("empirical values of the coupling constants", self.foundations)
        self.assertIn("one can predict a maximum superconducting transition temperature", self.foundations)
        self.assertIn("不能把特定模型与经验背景下的“最大 Tc”", self.foundations)

    def test_formula4_and_correct_example(self):
        self.assertAlmostEqual(tc(2.5, 0.15, 2100), 259.594501207478)
        self.assertAlmostEqual(tc(3.6, 0.12, 2100), 326.617107973496)
        self.assertAlmostEqual(theta_threshold(2.5, 0.15), 2426.861882935184)
        self.assertIn("λ_min = 2.5, μ*_max = 0.15, Θ_D = 2100 K", self.theorem)
        self.assertIn("**计算结果**：T_c > 326 K > 300 K ✅", self.theorem)

    def test_frequency_temperature_conversion(self):
        self.assertAlmostEqual(mev_to_kelvin(210), 2436.948806, places=5)
        self.assertAlmostEqual(mev_to_kelvin(150), 1740.677718, places=5)
        self.assertIn("ℏω_max ≈ 210 meV", self.theorem)
        self.assertIn("Θ_D ≈ 2100 K", self.theorem)

    def test_condition_sets_are_not_equivalent(self):
        self.assertIn("电子-声子耦合强度 λ > 2", self.theorem)
        self.assertIn("准二维层状或笼形结构", self.theorem)
        self.assertIn("光学支声子频率 ℏω > 150 meV", self.theorem)
        self.assertIn("电声耦合常数 λ ≥ 2.5", self.theorem)
        self.assertIn("Debye温度 Θ_D ≥ 1800 K", self.theorem)
        self.assertIn("Coulomb赝势 μ* ≤ 0.15", self.theorem)

    def test_song_semenok_and_meissner_roles(self):
        song = self.main["evidence"]["song"]
        semenok = self.main["evidence"]["semenok"]
        self.assertEqual(song["onset_tc_k"], [271, 298])
        self.assertFalse(song["direct_meissner_completed"])
        self.assertFalse(song["independent_positive_replication"])
        self.assertEqual(semenok["unsuccessful_attempts"], 7)
        self.assertFalse(self.governance["evidence"]["song"]["first_four_standards_met"])
        self.assertIn("Liu等人", self.theorem)

    def test_critical_anchor_scope(self):
        critical = self.main["evidence"]["critical_manifold"]
        anchor = critical["temperature_anchors"][0]
        self.assertAlmostEqual(critical_tc(100, anchor["lambda"], anchor["mu_star"]), anchor["tc_K"])
        self.assertLess(anchor["tc_K"], 300)
        self.assertFalse(critical["full_eliashberg_theory_refuted"])
        self.assertFalse(critical["material_prediction"])

    def test_intro_timeline_formula_and_author_claims(self):
        self.assertIn("1986年：铜基超导体突破液氮温区（77K）", self.theorem)
        self.assertIn("1986 | La-Ba-Cu-O（镧钡铜氧） | 35 K", self.intro)
        self.assertIn("1987 | Y-Ba-Cu-O（钇钡铜氧，YBCO） | 93 K", self.intro)
        self.assertIn("H₂S", self.intro)
        self.assertIn("麦克米兰极限", self.intro)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
