"""Contracts for seed-4 path outcomes and their native Word evidence."""

import hashlib
import json
import re
import sys
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "remaining_seed4_path_outcome_analysis.json"
DOCX = ROOT / "Floquet-BdG-seed4-剩余种子路径结局.docx"
CANDIDATES = ["mean", "q01", "q02", "q05", "q25", "q50", "q98", "q99", "low_frac_0p2", "high_frac_0p85", "high_frac_0p9", "lag1", "roughness_rms", "total_variation", "sign_changes", "block_std_max"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def evidence(test):
    test.assertTrue(DATA.is_file(), "Seed-4 remaining-path outcome is missing")
    return load(DATA.name)


class RemainingSeed4OutcomeTests(unittest.TestCase):
    def test_protocol_freezes_holdout_candidates_and_pair_rule(self):
        data = evidence(self)
        protocol = load("remaining_seed_outcome_protocol.json")
        self.assertEqual(protocol["schema"], "floquet-bdg-remaining-seed-outcome-protocol-v1")
        self.assertTrue(protocol["registered_before_any_remaining_path_outcome"])
        self.assertEqual(protocol["seed_values"], [2, 3, 4, 5, 7])
        self.assertEqual(protocol["comparison_seed_values"], [0, 1, 6])
        self.assertEqual(protocol["frozen_candidate_metrics"], CANDIDATES)
        self.assertEqual(protocol["candidate_source"]["sha256"], sha(ROOT / "profile_stat_candidates_analysis.json"))
        self.assertEqual(protocol["holdout_pair_policy"]["training_only_pair_count_excluded"], 3)
        self.assertEqual(protocol["holdout_pair_policy"]["maximum_pairs_involving_holdout"], 25)
        self.assertEqual(protocol["holdout_pair_policy"]["jump_ties_are_uninformative"], True)
        self.assertEqual(protocol["holdout_pair_policy"]["required_direction"], "all informative pairs involving at least one remaining seed")
        self.assertEqual(protocol["holdout_pair_policy"]["zero_informative_pairs_result"], "not_assessable")
        self.assertFalse(protocol["holdout_pair_policy"]["pristine_external_holdout_claim"])
        self.assertTrue(protocol["candidate_evaluation_deferred_until_all_remaining_outcomes_exist"])
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "remaining_seed_outcome_protocol.json"))
        self.assertEqual(data["candidate_source_analysis_sha256"], sha(ROOT / "profile_stat_candidates_analysis.json"))

    def test_seed4_profile_and_preregistered_inventory(self):
        data = evidence(self)
        self.assertEqual(data["schema"], "floquet-bdg-remaining-seed-path-outcome-v1")
        self.assertEqual(data["seed"], 4)
        master = np.random.default_rng(20261115).random(4800)
        self.assertTrue(np.array_equal(np.asarray(data["master_profile"]), master))
        self.assertEqual(data["master_profile_sha256"], hashlib.sha256(master.tobytes()).hexdigest())
        self.assertEqual(len(data["cells"]), 26)
        self.assertEqual(len(data["path_matrices"]), 78)
        self.assertEqual(len(data["links"]), 24)
        self.assertEqual(len(data["method_grid_links"]), 72)
        self.assertEqual(len(data["entry_links"]), 288)
        self.assertEqual(len(data["representation_fidelity"]), 156)
        self.assertEqual(len(data["rank_controls"]), 182)
        self.assertEqual(data["new_control_cells"], 26)
        self.assertEqual(data["evaluated_control_cells"], 26)
        self.assertEqual(data["new_path_seed_count"], 1)
        self.assertEqual(data["new_disorder_realization_count"], 0)
        self.assertTrue(data["all_preregistered_results_retained"])

    def test_jump_and_driver_outcomes_match_stored_comparisons(self):
        data = evidence(self)
        self.assertEqual(len(data["jump_comparisons"]), 8)
        self.assertEqual(len(data["driver_comparisons"]), 4)
        self.assertEqual(len(data["entry_extrema"]), 8)
        self.assertEqual(len(data["original_entry_extrema"]), 8)
        summary = data["summary"]
        self.assertEqual(summary["jump_change_count"], sum(row["jump_changed"] for row in data["jump_comparisons"]))
        self.assertGreaterEqual(summary["jump_change_count"], 0)
        self.assertLessEqual(summary["jump_change_count"], 8)
        self.assertEqual(summary["driver_comparison_change_count"], sum(row["driver_counts_changed"] for row in data["driver_comparisons"]))
        self.assertGreaterEqual(summary["driver_comparison_change_count"], 0)
        self.assertLessEqual(summary["driver_comparison_change_count"], 4)
        for row in data["jump_comparisons"]:
            self.assertEqual(row["seed"], 4)
            self.assertIn(row["method"], {"linear_point", "cell_average"})
            self.assertIn(row["entry"], {"O00", "O01", "O10", "O11"})

    def test_endpoint_sources_bind_to_existing_batches(self):
        data = evidence(self)
        self.assertEqual(data["batch_b_analysis_sha256"], sha(ROOT / "matched_beta_batch_b_analysis.json"))
        self.assertEqual(data["batch_c_analysis_sha256"], sha(ROOT / "matched_beta_batch_c_analysis.json"))
        endpoint = data["endpoint_binding"]
        self.assertLessEqual(endpoint["max_matrix_absolute_error"], 1e-12)
        self.assertLessEqual(endpoint["max_singular_absolute_error"], 1e-12)
        self.assertLessEqual(endpoint["max_spectrum_absolute_error"], 1e-12)
        self.assertTrue(endpoint["endpoint_recomputation_is_not_new_realization"])

    def test_independent_recheck_is_complete(self):
        evidence(self)
        independent = load("remaining_seed4_path_outcome_independent.json")
        self.assertTrue(independent["all_passed"])
        self.assertEqual(independent["seed"], 4)
        self.assertEqual(independent["cell_count"], 26)
        self.assertEqual(independent["cross_size_path_matrix_count"], 78)
        self.assertEqual(independent["native_adjacent_link_count"], 24)
        self.assertEqual(independent["entry_link_count"], 288)
        self.assertEqual(independent["max_master_absolute_error"], 0.0)
        self.assertEqual(independent["max_spectrum_absolute_error"], 0.0)
        self.assertLessEqual(independent["max_matrix_absolute_error"], 1e-12)
        self.assertLessEqual(independent["max_entry_delta_absolute_error"], 1e-12)
        self.assertLessEqual(independent["max_native_link_absolute_error"], 1e-12)
        self.assertEqual(independent["jump_outcome_mismatch_count"], 0)
        self.assertEqual(independent["driver_outcome_mismatch_count"], 0)
        self.assertFalse(independent["new_floquet_spectra_recomputed"])

    def test_figure_markdown_and_global_registration(self):
        evidence(self)
        with Image.open(ROOT / "remaining-seed4-outcome.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "REMAINING_SEED4_OUTCOME.md").read_text(encoding="utf-8")
        for phrase in ("seed=4", "路径结局", "不作候选验证", "不补算体 winding", "N=640", "不是完全未触碰的外部验证集"):
            self.assertIn(phrase, text)
        runner = (ROOT / "run_verification.py").read_text(encoding="utf-8")
        self.assertIn('("remaining_seed4_outcome_suite"', runner)
        for name in ("remaining_seed_outcome_protocol.json", "remaining_seed4_path_outcome_analysis.json", "remaining_seed4_path_outcome_independent.json", "REMAINING_SEED4_OUTCOME.md", DOCX.name):
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
        qa = load("remaining-seed4-outcome-word-qa.json")
        review = qa["visualReview"]
        self.assertEqual(review["status"], "passed")
        self.assertEqual(review["pagesReviewed"], 4)
        self.assertTrue(review["contactSheetRead"])
        self.assertEqual(review["docxSha256"], sha(DOCX))
        self.assertEqual(review["nearBlankPages"], [])
        self.assertEqual(review["clippedPages"], [])

    def test_no_candidate_validation_or_new_category_is_claimed(self):
        data = evidence(self)
        self.assertTrue(data["candidate_evaluation_deferred"])
        self.assertFalse(data["candidate_validation_completed"])
        self.assertEqual(data["holdout_pair_evaluations"], [])
        self.assertFalse(data["pristine_external_holdout_claim"])
        self.assertFalse(data["predictive_model_fitted"])
        self.assertFalse(data["correlation_claim"])
        self.assertFalse(data["statistical_significance_claim"])
        self.assertFalse(data["causal_mechanism_proven"])
        self.assertFalse(data["continuous_path_proof"])
        self.assertFalse(data["spectral_crossing_proven"])
        self.assertFalse(data["state_exchange_proven"])
        self.assertFalse(data["new_taxonomy_claim"])
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
