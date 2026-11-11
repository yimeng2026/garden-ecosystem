"""Contracts for targeted, non-promotional analysis of sign-reversal cells."""

import hashlib
import json
import sys
import unittest
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def case(data, seed, strength, n):
    if n not in (400, 600):
        raise ValueError("unexpected comparison size")
    return next(row for row in data["cases"] if (row["seed"], row["strength"]) == (seed, strength))


class ReversalUnitTests(unittest.TestCase):
    def test_registry_is_bounded_to_existing_evidence(self):
        data = json.loads((ROOT / "reversal_unit_analysis.json").read_text(encoding="utf-8"))
        self.assertEqual(data["source_sha256"], sha(ROOT / "multi_seed_profile_control.json"))
        self.assertEqual(data["independent_source_sha256"], sha(ROOT / "multi_seed_independent.json"))
        self.assertEqual(data["new_seed_count"], 0)
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])
        self.assertEqual(data["analysis_role"], "exploratory_decomposition_not_universal_law")
        self.assertEqual({(row["seed"], row["strength"]) for row in data["cases"]}, {(0, 0.05), (1, 0.05), (0, 0.1), (2, 0.1)})

    def test_left_right_decomposition_matches_profiles(self):
        data = json.loads((ROOT / "reversal_unit_analysis.json").read_text(encoding="utf-8"))
        for row in data["cases"]:
            comparison = row["comparison"]
            self.assertAlmostEqual(comparison["left_delta"] + comparison["right_delta"], comparison["edge_delta"])
            self.assertTrue(comparison["profile_metrics_recomputed"])
            self.assertLessEqual(comparison["max_recompute_error"], 1e-12)
            self.assertIn(comparison["dominant_end"], ("left", "right"))

    def test_seed1_is_right_driven_symmetrization(self):
        data = json.loads((ROOT / "reversal_unit_analysis.json").read_text(encoding="utf-8"))
        comparison = case(data, 1, 0.05, 600)["comparison"]
        self.assertEqual(comparison["delta_L50"], -31)
        self.assertGreater(comparison["right_delta"], comparison["left_delta"])
        self.assertLess(comparison["asymmetry_delta"], 0)
        self.assertEqual(comparison["mechanism"], "right_end_driven_symmetrization")
        self.assertFalse(comparison["isolation_explains_everything"])

    def test_seed2_is_broadening_not_endpoint_loss(self):
        data = json.loads((ROOT / "reversal_unit_analysis.json").read_text(encoding="utf-8"))
        comparison = case(data, 2, 0.1, 600)["comparison"]
        self.assertEqual(comparison["delta_L50"], 12)
        self.assertLess(comparison["right_delta"], 0)
        self.assertGreater(comparison["asymmetry_delta"], 0)
        self.assertEqual(comparison["mechanism"], "right_end_weakening_with_broadening")
        self.assertTrue(comparison["both_sizes_joint_pass"])
        self.assertFalse(comparison["endpoint_loss"])
        self.assertLess(comparison["n600_first"]["max_separation_ratio"], comparison["n400_first"]["max_separation_ratio"])

    def test_seed0_reference_roles_are_preserved(self):
        data = json.loads((ROOT / "reversal_unit_analysis.json").read_text(encoding="utf-8"))
        low = case(data, 0, 0.05, 600)["comparison"]
        high = case(data, 0, 0.1, 600)["comparison"]
        self.assertEqual(low["mechanism"], "tail_growth_without_endpoint_recovery")
        self.assertEqual(high["mechanism"], "left_end_driven_threshold")
        self.assertGreater(high["left_delta"], high["right_delta"])
        self.assertGreater(high["delta_L50"], 0)

    def test_figure_markdown_and_word_visual_gate(self):
        with Image.open(ROOT / "reversal-units.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 700)
        text = (ROOT / "REVERSAL_UNITS.md").read_text(encoding="utf-8")
        for phrase in ("右端驱动", "尾部变宽", "不追加种子", "不补算体 winding", "N=640", "端点消失"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-反转单元机制诊断.docx"
        with zipfile.ZipFile(docx) as package:
            document = package.read("word/document.xml").decode("utf-8")
            footer = "".join(package.read(name).decode("utf-8") for name in package.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            media = [name for name in package.namelist() if name.startswith("word/media/") and not name.endswith("/")]
        self.assertIn("m:oMath", document)
        self.assertIn("TOC", document)
        self.assertIn("PAGE", footer)
        self.assertEqual(len(media), 1)
        qa = json.loads((ROOT / "reversal-word-qa.json").read_text(encoding="utf-8"))
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])
        runner = (ROOT / "run_reversal_verification.py").read_text(encoding="utf-8")
        self.assertNotIn('("docx_build"', runner)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
