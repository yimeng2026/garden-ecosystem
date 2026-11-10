import json
import math
import sys
import unittest
from pathlib import Path

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
        cls.inventory = json.loads((ROOT / "sources/artifact-inventory.json").read_text(encoding="utf-8"))
        cls.delivery = (SOURCE_ROOT / "10-技术文档/01-交付摘要.md").read_text(encoding="utf-8")
        cls.final = (SOURCE_ROOT / "10-技术文档/02-最终报告.md").read_text(encoding="utf-8")
        cls.progress = (SOURCE_ROOT / "10-技术文档/03-进度报告.md").read_text(encoding="utf-8")
        cls.quality = (SOURCE_ROOT / "10-技术文档/04-质量进展.md").read_text(encoding="utf-8")
        cls.checklist = (SOURCE_ROOT / "10-技术文档/05-整合检查清单.md").read_text(encoding="utf-8")
        cls.main = load_review("main-claims")
        cls.validation = load_review("validation-materials")
        cls.methods = load_review("room-temp-methods")

    def test_status_contradiction(self):
        self.assertIn("完成状态：100%", self.final)
        self.assertIn("运行中", self.progress)
        self.assertIn("进行中（3路质量深化）", self.quality)
        self.assertIn("TEMPLATE", self.checklist)
        self.assertIn("PARTIAL", self.checklist)
        self.assertIn("PLACEHOLDERS", self.checklist)

    def test_artifact_inventory(self):
        self.assertFalse(self.inventory["tar_exists"])
        self.assertFalse(self.inventory["md5_verifiable"])
        self.assertEqual(self.inventory["figures_found"], 0)
        self.assertEqual(self.inventory["references_enhanced_found"], 0)
        self.assertFalse(self.inventory["prl_tex_exists"])
        self.assertTrue(self.inventory["claimed_markdown_missing"])
        self.assertEqual(self.inventory["tex_variants_present"], 4)
        self.assertFalse(self.inventory["expected_lean_exists"])
        self.assertTrue(self.inventory["alternate_lean_exists"])
        self.assertTrue(self.inventory["alternate_si_exists"])
        self.assertEqual(self.inventory["si_placeholder_count"], 31)
        self.assertTrue(self.inventory["negative_result_scope_limited"])

    def test_formula_and_scoring(self):
        exponent = -1.04 * (1 + 2.0) / (2.0 - 0.13 * (1 + 0.62 * 2.0))
        computed = 1200 / 1.2 * math.exp(exponent)
        self.assertAlmostEqual(computed, 161.08184379177882)
        self.assertFalse(self.validation["evidence"]["scoring"]["rubric_available"])

    def test_lean_and_si(self):
        lean = self.methods["evidence"]["lean"]
        si = self.methods["evidence"]["si"]
        self.assertFalse(lean["build_attempted"])
        self.assertFalse(lean["build_passed"])
        self.assertEqual(lean["standalone_sorry_count"], 3)
        self.assertEqual(si["placeholder_count"], 31)
        self.assertFalse(si["dft_inputs_provided"])
        self.assertFalse(si["phonon_spectra_provided"])

    def test_song_and_pnas_roles(self):
        song = self.main["evidence"]["song"]
        pnas = self.main["evidence"]["pnas_prediction"]
        self.assertEqual(song["onset_tc_k"], [271, 298])
        self.assertFalse(song["direct_meissner_completed"])
        self.assertFalse(song["independent_positive_replication"])
        self.assertEqual(pnas["role"], "2024 理论预测")
        self.assertIn("完美验证论文核心预测", self.final)

    def test_delivery_date_and_breakthrough(self):
        self.assertIn("**交付时间**: 2025-04-19", self.delivery)
        self.assertIn("2025年10月突破", self.delivery)
        self.assertIn("交付状态**: 完成", self.delivery)
        self.assertIn("**核心突破**: LaSc₂H₂₄室温超导实验验证（2025.10）", self.delivery)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
