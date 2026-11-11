"""Contracts for descriptive recurrence of endpoint mechanism categories."""

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


class RepeatedCategoryTests(unittest.TestCase):
    def test_protocol_and_new_cell_registry(self):
        protocol = json.loads((ROOT / "repeated_category_protocol.json").read_text(encoding="utf-8"))
        cells = json.loads((ROOT / "category_new_cells.json").read_text(encoding="utf-8"))
        self.assertEqual(cells["protocol_sha256"], sha(ROOT / "repeated_category_protocol.json"))
        self.assertEqual(cells["new_seeds"], [4, 5, 6, 7])
        self.assertEqual(len(cells["cases"]), 16)
        self.assertEqual({(row["n"], row["strength"], row["seed"]) for row in cells["cases"]}, {(n, r, s) for n in (400, 600) for r in (0.05, 0.1) for s in (4, 5, 6, 7)})
        self.assertTrue(all(len(row["pairs"]) == 2 for row in cells["cases"]))
        self.assertFalse(cells["new_winding_computed"])
        self.assertFalse(cells["n640_computed"])
        self.assertFalse(protocol["post_hoc_seed_or_threshold_selection"])

    def test_old_cells_and_reference_categories_are_unchanged(self):
        data = json.loads((ROOT / "repeated_category_analysis.json").read_text(encoding="utf-8"))
        self.assertEqual(data["source_sha256"], sha(ROOT / "multi_seed_profile_control.json"))
        self.assertEqual(data["reversal_source_sha256"], sha(ROOT / "reversal_unit_analysis.json"))
        self.assertEqual(data["new_cells_sha256"], sha(ROOT / "category_new_cells.json"))
        old = json.loads((ROOT / "multi_seed_profile_control.json").read_text(encoding="utf-8"))
        for row in old["cases"]:
            stored = next(case for case in data["all_cells"] if (case["n"], case["strength"], case["seed"]) == (row["n"], row["strength"], row["seed"]))
            self.assertEqual(stored["pairs"][0]["profile_sha256"], row["pairs"][0]["profile_sha256"])
        references = {(row["seed"], row["strength"]): row["category"] for row in data["cases"] if (row["seed"] == 1 and row["strength"] == 0.05) or (row["seed"] == 2 and row["strength"] == 0.1)}
        self.assertEqual(references[(1, 0.05)], "right_end_driven_symmetrization")
        self.assertEqual(references[(2, 0.1)], "right_end_weakening_with_broadening")

    def test_every_contrast_has_one_frozen_category(self):
        data = json.loads((ROOT / "repeated_category_analysis.json").read_text(encoding="utf-8"))
        protocol = json.loads((ROOT / "repeated_category_protocol.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["cases"]), 16)
        self.assertEqual(set(data["category_counts"]), set(protocol["category_order"]))
        self.assertEqual(sum(data["category_counts"].values()), 16)
        for row in data["cases"]:
            comparison = row["comparison"]
            self.assertIn(row["category"], protocol["category_order"])
            self.assertAlmostEqual(comparison["left_delta"] + comparison["right_delta"], comparison["edge_delta"])
            if row["category"] == "right_end_weakening_with_broadening":
                self.assertLess(comparison["right_delta"], 0)
                self.assertGreater(comparison["delta_L50"], 0)
                self.assertGreater(comparison["asymmetry_delta"], 0)
            if row["category"] == "right_end_driven_symmetrization":
                self.assertGreater(comparison["left_delta"], 0)
                self.assertGreater(comparison["right_delta"], comparison["left_delta"])
                self.assertLess(comparison["asymmetry_delta"], 0)
            if row["category"] == "left_end_driven_threshold":
                self.assertGreater(comparison["left_delta"], comparison["right_delta"])
                self.assertGreater(comparison["edge_delta"], 0)
                self.assertLess(comparison["asymmetry_delta"], 0)
            if row["category"] == "tail_growth_without_endpoint_recovery":
                self.assertLess(comparison["edge_delta"], 0)
                self.assertGreater(comparison["delta_L50"], 0)
                self.assertFalse(comparison["both_sizes_joint_pass"])

    def test_new_cells_have_independent_backend_verification(self):
        result = json.loads((ROOT / "category_new_cells_independent.json").read_text(encoding="utf-8"))
        self.assertTrue(result["all_passed"])
        self.assertEqual(result["eigensolver"], "scipy.linalg.eig")
        self.assertEqual(result["projector"], "direct_gram_inverse")
        self.assertEqual(result["analysis_sha256"], sha(ROOT / "category_new_cells.json"))
        self.assertIn('"--check-only"', (ROOT / "run_category_verification.py").read_text(encoding="utf-8"))
        self.assertEqual(len(result["cases"]), 16)
        for row in result["cases"]:
            self.assertGreaterEqual(row["seed"], 4)
            for pair in row["pairs"]:
                self.assertLessEqual(pair["max_profile_absolute_error"], 1e-10)

    def test_figure_markdown_and_word_visual_gate(self):
        with Image.open(ROOT / "repeated-categories.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 700)
        text = (ROOT / "REPEATED_CATEGORIES.md").read_text(encoding="utf-8")
        for phrase in ("未归类", "不追加阈值", "不补算体 winding", "N=640", "可重复"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-端部机制类别检验.docx"
        with zipfile.ZipFile(docx) as package:
            document = package.read("word/document.xml").decode("utf-8")
            footer = "".join(package.read(name).decode("utf-8") for name in package.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            media = [name for name in package.namelist() if name.startswith("word/media/") and not name.endswith("/")]
        self.assertIn("m:oMath", document)
        self.assertIn("TOC", document)
        self.assertIn("PAGE", footer)
        self.assertEqual(len(media), 1)
        qa = json.loads((ROOT / "category-word-qa.json").read_text(encoding="utf-8"))
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])
        runner = (ROOT / "run_category_verification.py").read_text(encoding="utf-8")
        self.assertNotIn('("docx_build"', runner)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
