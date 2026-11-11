"""Contracts for condition auditing of unclassified and near-miss contrasts."""

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


def case(data, seed, strength):
    return next(row for row in data["unclassified_cases"] if (row["seed"], row["strength"]) == (seed, strength))


class UnclassifiedSignatureTests(unittest.TestCase):
    def test_registry_preserves_sources_and_scope(self):
        data = json.loads((ROOT / "unclassified_signature_analysis.json").read_text(encoding="utf-8"))
        self.assertEqual(data["source_sha256"], sha(ROOT / "repeated_category_analysis.json"))
        self.assertEqual(data["new_independent_source_sha256"], sha(ROOT / "category_new_cells_independent.json"))
        self.assertEqual(data["analysis_role"], "condition_audit_not_new_taxonomy")
        self.assertEqual(data["new_seed_count"], 0)
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])
        self.assertEqual(len(data["unclassified_cases"]), 7)
        self.assertTrue(data["unclassified_not_homogeneous"])

    def test_unclassified_has_three_descriptive_signatures(self):
        data = json.loads((ROOT / "unclassified_signature_analysis.json").read_text(encoding="utf-8"))
        counts = data["signature_counts"]
        self.assertEqual(counts["positive_edge_tail_shorter_or_asymmetry_up"], 2)
        self.assertEqual(counts["mixed_nonmatching_sign_combinations"], 4)
        self.assertEqual(counts["right_weakening_with_symmetrization"], 1)
        self.assertEqual(sum(counts.values()), 7)
        for row in data["unclassified_cases"]:
            self.assertEqual(row["original_category"], "other_unclassified")
            self.assertIn("blocking_conditions", row)
            self.assertGreater(len(row["blocking_conditions"]), 0)

    def test_near_misses_explain_zero_weakening_recurrence(self):
        data = json.loads((ROOT / "unclassified_signature_analysis.json").read_text(encoding="utf-8"))
        low = case(data, 5, 0.05)
        self.assertLess(low["comparison"]["right_delta"], 0)
        self.assertGreater(low["comparison"]["edge_delta"], 0)
        self.assertGreater(low["comparison"]["asymmetry_delta"], 0)
        self.assertIn("edge_delta_not_negative", low["blocking_conditions"])
        high = case(data, 5, 0.1)
        self.assertLess(high["comparison"]["right_delta"], 0)
        self.assertLess(high["comparison"]["edge_delta"], 0)
        self.assertGreater(high["comparison"]["delta_L50"], 0)
        self.assertLess(high["comparison"]["asymmetry_delta"], 0)
        self.assertTrue(high["comparison"]["both_sizes_joint_pass"])
        self.assertIn("asymmetry_delta_not_positive", high["blocking_conditions"])
        self.assertEqual(data["reference_weakening_new_seed_recurrences"], 0)
        self.assertFalse(data["new_taxonomy_claim"])

    def test_signatures_do_not_change_original_categories(self):
        data = json.loads((ROOT / "unclassified_signature_analysis.json").read_text(encoding="utf-8"))
        original = json.loads((ROOT / "repeated_category_analysis.json").read_text(encoding="utf-8"))
        self.assertEqual(data["original_category_counts"], original["category_counts"])
        for row in data["cases"]:
            old = next(case for case in original["cases"] if (case["seed"], case["strength"]) == (row["seed"], row["strength"]))
            self.assertEqual(row["category"], old["category"])
        for row in data["unclassified_cases"]:
            self.assertNotEqual(row["signature"], "other_unclassified")

    def test_figure_markdown_and_word_visual_gate(self):
        with Image.open(ROOT / "unclassified-signatures.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 700)
        text = (ROOT / "UNCLASSIFIED_SIGNATURES.md").read_text(encoding="utf-8")
        for phrase in ("未归类不是单一机制", "近 miss", "不新增类别", "不补算体 winding", "N=640", "右端减弱但更对称"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-未归类与未复现诊断.docx"
        with zipfile.ZipFile(docx) as package:
            document = package.read("word/document.xml").decode("utf-8")
            footer = "".join(package.read(name).decode("utf-8") for name in package.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            media = [name for name in package.namelist() if name.startswith("word/media/") and not name.endswith("/")]
        self.assertIn("m:oMath", document)
        self.assertIn("TOC", document)
        self.assertIn("PAGE", footer)
        self.assertEqual(len(media), 1)
        qa = json.loads((ROOT / "unclassified-word-qa.json").read_text(encoding="utf-8"))
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])
        runner = (ROOT / "run_unclassified_verification.py").read_text(encoding="utf-8")
        self.assertNotIn('("docx_build"', runner)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
