"""Contracts for frozen candidate evaluation on all remaining-seed-related pairs."""

import hashlib
import itertools
import json
import re
import sys
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "holdout_pair_evaluation_analysis.json"
DOCX = ROOT / "Floquet-BdG-剩余种子候选逐对方向检验.docx"
CANDIDATES = ["mean", "q01", "q02", "q05", "q25", "q50", "q98", "q99", "low_frac_0p2", "high_frac_0p85", "high_frac_0p9", "lag1", "roughness_rms", "total_variation", "sign_changes", "block_std_max"]
EXPECTED_JUMPS = {"0": 4, "1": 0, "2": 2, "3": 0, "4": 0, "5": 6, "6": 6, "7": 2}
TIE_PAIRS = {(1, 3), (1, 4), (2, 7), (3, 4), (5, 6)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def evidence(test):
    test.assertTrue(DATA.is_file(), "Holdout pair evaluation is missing")
    return load(DATA.name)


class HoldoutPairEvaluationTests(unittest.TestCase):
    def test_frozen_sources_and_complete_path_outcomes(self):
        data = evidence(self)
        protocol = load("remaining_seed_outcome_protocol.json")
        candidates = load("profile_stat_candidates_analysis.json")
        self.assertEqual(data["schema"], "floquet-bdg-holdout-pair-evaluation-v1")
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "remaining_seed_outcome_protocol.json"))
        self.assertEqual(data["candidate_source_analysis_sha256"], sha(ROOT / "profile_stat_candidates_analysis.json"))
        self.assertEqual(protocol["frozen_candidate_metrics"], CANDIDATES)
        self.assertEqual(data["comparison_seed_values"], [0, 1, 6])
        self.assertEqual(data["remaining_seed_values"], [2, 3, 4, 5, 7])
        self.assertEqual(data["jump_counts"], EXPECTED_JUMPS)
        self.assertEqual([row["metric"] for row in candidates["candidate_metrics"]], CANDIDATES)
        self.assertTrue(data["all_remaining_path_outcomes_exist"])
        self.assertTrue(data["directional_screen_completed"])
        self.assertTrue(data["candidate_evaluation_completed"])
        self.assertFalse(data["predictive_validation_completed"])
        for name in ("seed01_matrix_midpoint_analysis.json", "seed6_matrix_midpoint_analysis.json", *(f"remaining_seed{seed}_path_outcome_analysis.json" for seed in (2, 3, 4, 5, 7))):
            self.assertEqual(data["path_outcome_sources"][name], sha(ROOT / name))

    def test_pair_inventory_and_unfiltered_record_retention(self):
        data = evidence(self)
        expected_pairs = [pair for pair in itertools.combinations(range(8), 2) if not (pair[0] in (0, 1, 6) and pair[1] in (0, 1, 6))]
        self.assertEqual(len(expected_pairs), 25)
        self.assertEqual(data["candidate_count"], 16)
        self.assertEqual(data["pair_count_per_candidate"], 25)
        self.assertEqual(data["unfiltered_pair_record_count"], 400)
        self.assertEqual(len(data["pair_evaluations"]), 400)
        self.assertEqual(data["informative_pair_count"], 20)
        self.assertEqual(data["uninformative_pair_count"], 5)
        self.assertEqual(data["training_only_pair_count_excluded"], 3)
        for row in data["candidate_summaries"]:
            records = [item for item in data["pair_evaluations"] if item["metric"] == row["metric"]]
            self.assertEqual(len(records), 25)
            self.assertEqual({(item["seed_a"], item["seed_b"]) for item in records}, set(expected_pairs))
            self.assertFalse(any(a in (0, 1, 6) and b in (0, 1, 6) for a, b in {(item["seed_a"], item["seed_b"]) for item in records}))
        self.assertEqual({(row["seed_a"], row["seed_b"]) for row in data["pair_evaluations"] if not row["informative"]}, TIE_PAIRS)

    def test_pair_sign_logic_and_tie_handling(self):
        data = evidence(self)
        for row in data["pair_evaluations"]:
            a, b = row["seed_a"], row["seed_b"]
            self.assertEqual(row["jump_a"], EXPECTED_JUMPS[str(a)])
            self.assertEqual(row["jump_b"], EXPECTED_JUMPS[str(b)])
            self.assertEqual(row["jump_delta"], row["jump_b"] - row["jump_a"])
            self.assertAlmostEqual(row["candidate_delta"], row["value_b"] - row["value_a"], places=15)
            if (a, b) in TIE_PAIRS:
                self.assertFalse(row["informative"])
                self.assertIsNone(row["consistent"])
                self.assertEqual(row["reason"], "uninformative_jump_tie")
                continue
            self.assertTrue(row["informative"])
            jump_sign = 1 if row["jump_delta"] > 0 else -1
            expected_sign = jump_sign if row["direction"] == "same_as_jump_changes" else -jump_sign
            actual_sign = 1 if row["candidate_delta"] > 0 else -1 if row["candidate_delta"] < 0 else 0
            self.assertEqual(row["expected_sign"], expected_sign)
            self.assertEqual(row["actual_sign"], actual_sign)
            self.assertEqual(row["consistent"], actual_sign == expected_sign and actual_sign != 0)
            if actual_sign == 0:
                self.assertEqual(row["reason"], "candidate_tie_not_strict")

    def test_candidate_summaries_have_no_selective_filtering(self):
        data = evidence(self)
        self.assertEqual(len(data["candidate_summaries"]), 16)
        self.assertEqual([row["metric"] for row in data["candidate_summaries"]], CANDIDATES)
        for summary in data["candidate_summaries"]:
            records = [row for row in data["pair_evaluations"] if row["metric"] == summary["metric"]]
            informative = [row for row in records if row["informative"]]
            consistent = sum(row["consistent"] is True for row in informative)
            inconsistent = sum(row["consistent"] is False for row in informative)
            self.assertEqual(summary["consistent_pair_count"], consistent)
            self.assertEqual(summary["inconsistent_pair_count"], inconsistent)
            self.assertEqual(consistent + inconsistent, 20)
            self.assertEqual(summary["uninformative_pair_count"], 5)
            self.assertEqual(summary["candidate_tie_count"], sum(row["actual_sign"] == 0 for row in informative))
            expected = len(informative) > 0 and inconsistent == 0
            self.assertEqual(summary["all_informative_pairs_consistent"], expected)
            self.assertEqual(summary["assessment"], "all_informative_pairs_consistent" if expected else "not_all_informative_pairs_consistent")
        self.assertTrue(data["all_preregistered_results_retained"])
        self.assertFalse(data["failed_pairs_removed"])
        self.assertFalse(data["tie_pairs_removed"])

    def test_independent_recheck(self):
        evidence(self)
        independent = load("holdout_pair_evaluation_independent.json")
        self.assertTrue(independent["all_passed"])
        self.assertEqual(independent["candidate_count"], 16)
        self.assertEqual(independent["pair_record_count"], 400)
        self.assertEqual(independent["informative_pair_count"], 20)
        self.assertEqual(independent["uninformative_pair_count"], 5)
        self.assertEqual(independent["source_outcome_mismatch_count"], 0)
        self.assertEqual(independent["pair_record_mismatch_count"], 0)
        self.assertEqual(independent["summary_mismatch_count"], 0)
        self.assertEqual(independent["max_value_absolute_error"], 0.0)
        self.assertFalse(independent["new_floquet_spectra_recomputed"])

    def test_figure_markdown_and_global_registration(self):
        data = evidence(self)
        with Image.open(ROOT / "holdout-pair-evaluation.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "HOLDOUT_PAIR_EVALUATION.md").read_text(encoding="utf-8")
        for phrase in ("400", "25", "20", "5", "平局", "不是预测", "不是完全未触碰的外部验证集", "不补算体 winding", "N=640"):
            self.assertIn(phrase, text)
        self.assertIn(str(len(data["candidate_summaries"])), text)
        runner = (ROOT / "run_verification.py").read_text(encoding="utf-8")
        self.assertIn('("holdout_pair_evaluation_suite"', runner)
        for name in (DATA.name, "holdout_pair_evaluation_independent.json", "HOLDOUT_PAIR_EVALUATION.md", DOCX.name):
            self.assertIn(name, runner)

    def test_native_word_layout_and_visual_review(self):
        evidence(self)
        with zipfile.ZipFile(DOCX) as package:
            document = package.read("word/document.xml").decode("utf-8")
            footer = "".join(package.read(name).decode("utf-8") for name in package.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            media = [name for name in package.namelist() if name.startswith("word/media/") and not name.endswith("/")]
            root = ET.fromstring(package.read("word/document.xml"))
        for tag in ("<m:sSub", "<m:sSup", "<m:f>"):
            self.assertIn(tag, document)
        self.assertIn("TOC", document)
        self.assertIn("PAGE", footer)
        self.assertIn("400", document)
        self.assertIn("不是预测", document)
        self.assertEqual(len(media), 1)
        grids = re.findall(r"<w:tblGrid>(.*?)</w:tblGrid>", document)
        self.assertTrue(grids)
        for grid in grids:
            self.assertLessEqual(sum(int(value) for value in re.findall(r'w:w="(\d+)"', grid)), 9906)
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        attr = lambda name: f"{{{ns['w']}}}{name}"
        for table in root.findall(".//w:tbl", ns):
            for cell in table.findall(".//w:tc", ns):
                spacing = cell.find("w:p/w:pPr/w:spacing", ns)
                self.assertEqual(spacing.get(attr("after")), "40")
                self.assertEqual(spacing.get(attr("line")), "240")
                margins = cell.find("w:tcPr/w:tcMar", ns)
                for side, expected in (("top", "80"), ("bottom", "80"), ("left", "60"), ("right", "60")):
                    self.assertEqual(margins.find(f"w:{side}", ns).get(attr("w")), expected)
        qa = load("holdout-pair-evaluation-word-qa.json")
        review = qa["visualReview"]
        self.assertEqual(review["status"], "passed")
        self.assertEqual(review["pagesReviewed"], 5)
        self.assertTrue(review["contactSheetRead"])
        self.assertEqual(review["docxSha256"], sha(DOCX))
        self.assertEqual(review["nearBlankPages"], [])
        self.assertEqual(review["clippedPages"], [])

    def test_no_prediction_significance_or_new_category_is_claimed(self):
        data = evidence(self)
        self.assertTrue(data["pair_evaluation_is_not_prediction"])
        self.assertFalse(data["pristine_external_holdout_claim"])
        self.assertFalse(data["predictive_model_fitted"])
        self.assertFalse(data["correlation_claim"])
        self.assertFalse(data["predictive_accuracy_computed"])
        self.assertFalse(data["statistical_significance_claim"])
        self.assertFalse(data["causal_mechanism_proven"])
        self.assertFalse(data["continuous_path_proof"])
        self.assertFalse(data["spectral_crossing_proven"])
        self.assertFalse(data["state_exchange_proven"])
        self.assertFalse(data["new_taxonomy_claim"])
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])
        self.assertEqual(data["new_floquet_cells_computed"], 0)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
