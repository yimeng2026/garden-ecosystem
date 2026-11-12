"""Contracts for descriptive structure of candidate-inconsistent pairs."""

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
DATA = ROOT / "pair_inconsistency_structure_analysis.json"
DOCX = ROOT / "Floquet-BdG-候选不一致对结构分析.docx"
CANDIDATES = ["mean", "q01", "q02", "q05", "q25", "q50", "q98", "q99", "low_frac_0p2", "high_frac_0p85", "high_frac_0p9", "lag1", "roughness_rms", "total_variation", "sign_changes", "block_std_max"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def evidence(test):
    test.assertTrue(DATA.is_file(), "Pair-inconsistency structure analysis is missing")
    return load(DATA.name)


class PairInconsistencyStructureTests(unittest.TestCase):
    def test_protocol_and_source_binding(self):
        data = evidence(self)
        protocol = load("pair_inconsistency_structure_protocol.json")
        self.assertEqual(protocol["schema"], "floquet-bdg-pair-inconsistency-structure-protocol-v1")
        self.assertTrue(protocol["registered_before_structure_analysis"])
        self.assertEqual(protocol["source_pair_evaluation"]["path"], "holdout_pair_evaluation_analysis.json")
        self.assertEqual(protocol["source_pair_evaluation"]["sha256"], sha(ROOT / "holdout_pair_evaluation_analysis.json"))
        self.assertEqual(protocol["informative_pair_count"], 20)
        self.assertEqual(protocol["candidate_count"], 16)
        self.assertEqual(protocol["overlap_pair_count"], 120)
        self.assertEqual(protocol["closest_candidate_names"], ["q99", "block_std_max"])
        self.assertTrue(protocol["zero_candidate_difference_retained_separately"])
        self.assertTrue(protocol["empty_union_jaccard_is_null"])
        self.assertFalse(protocol["causal_attribution_allowed"])
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "pair_inconsistency_structure_protocol.json"))
        self.assertEqual(data["source_pair_evaluation_sha256"], sha(ROOT / "holdout_pair_evaluation_analysis.json"))
        self.assertEqual(data["candidate_names"], CANDIDATES)

    def test_all_twenty_pair_summaries_and_spectrum(self):
        data = evidence(self)
        self.assertEqual(data["schema"], "floquet-bdg-pair-inconsistency-structure-v1")
        self.assertEqual(len(data["pair_summaries"]), 20)
        self.assertEqual(len(data["shared_failure_spectrum"]), 17)
        self.assertEqual(data["total_inconsistent_assignments"], 104)
        self.assertEqual(sum(row["pair_count"] for row in data["shared_failure_spectrum"]), 20)
        self.assertEqual(sum(row["inconsistent_candidate_count"] * row["pair_count"] for row in data["shared_failure_spectrum"]), 104)
        for row in data["pair_summaries"]:
            self.assertEqual(row["consistent_count"] + row["inconsistent_count"], 16)
            self.assertEqual(row["all_candidates_inconsistent"], row["inconsistent_count"] == 16)
            self.assertEqual(row["all_candidates_consistent"], row["inconsistent_count"] == 0)
            spectrum = data["shared_failure_spectrum"][row["inconsistent_count"]]
            self.assertIn([row["seed_a"], row["seed_b"]], spectrum["pairs"])
        self.assertEqual(data["source_pair_record_count"], 400)
        self.assertEqual(data["source_uninformative_pair_count"], 5)
        self.assertTrue(data["source_records_unchanged"])

    def test_failure_sets_and_overlap_records(self):
        data = evidence(self)
        self.assertEqual(len(data["candidate_failure_sets"]), 16)
        failure_sets = {}
        source_summaries = {row["metric"]: row for row in load("holdout_pair_evaluation_analysis.json")["candidate_summaries"]}
        for row in data["candidate_failure_sets"]:
            failure_sets[row["metric"]] = {(pair[0], pair[1]) for pair in row["failing_pairs"]}
            self.assertEqual(len(row["failing_pairs"]), source_summaries[row["metric"]]["inconsistent_pair_count"])
            self.assertEqual(len(row["zero_diff_pairs"]), source_summaries[row["metric"]]["candidate_tie_count"])
        self.assertEqual(len(data["overlap_records"]), 120)
        self.assertEqual({(row["metric_a"], row["metric_b"]) for row in data["overlap_records"]}, set(itertools.combinations(CANDIDATES, 2)))
        for row in data["overlap_records"]:
            a, b = failure_sets[row["metric_a"]], failure_sets[row["metric_b"]]
            intersection = a & b
            union = a | b
            self.assertEqual(row["intersection_count"], len(intersection))
            self.assertEqual(row["union_count"], len(union))
            self.assertEqual(row["only_a_count"], len(a - b))
            self.assertEqual(row["only_b_count"], len(b - a))
            self.assertEqual({tuple(pair) for pair in row["shared_pairs"]}, intersection)
            expected_jaccard = len(intersection) / len(union) if union else None
            self.assertEqual(row["jaccard"], expected_jaccard)
        closest = data["closest_candidate_comparison"]
        self.assertEqual(closest["metric_a"], "q99")
        self.assertEqual(closest["metric_b"], "block_std_max")
        self.assertEqual(closest["intersection_count"], len(failure_sets["q99"] & failure_sets["block_std_max"]))
        self.assertEqual(closest["union_count"], len(failure_sets["q99"] | failure_sets["block_std_max"]))

    def test_no_rule_change_or_selective_filtering(self):
        data = evidence(self)
        self.assertTrue(data["all_preregistered_results_retained"])
        self.assertFalse(data["strict_rule_changed"])
        self.assertFalse(data["failed_pairs_removed"])
        self.assertFalse(data["tie_pairs_removed"])
        self.assertFalse(data["new_metric_proposed"])
        self.assertFalse(data["ensemble_rule_proposed"])
        self.assertFalse(data["predictive_model_fitted"])
        self.assertFalse(data["correlation_claim"])
        self.assertFalse(data["predictive_accuracy_computed"])
        self.assertFalse(data["statistical_significance_claim"])
        self.assertFalse(data["causal_mechanism_proven"])
        self.assertFalse(data["new_taxonomy_claim"])
        self.assertEqual(data["new_floquet_cells_computed"], 0)
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])

    def test_independent_recheck(self):
        evidence(self)
        independent = load("pair_inconsistency_structure_independent.json")
        self.assertTrue(independent["all_passed"])
        self.assertEqual(independent["pair_summary_count"], 20)
        self.assertEqual(independent["overlap_record_count"], 120)
        self.assertEqual(independent["total_inconsistent_assignments"], 104)
        self.assertEqual(independent["pair_summary_mismatch_count"], 0)
        self.assertEqual(independent["failure_set_mismatch_count"], 0)
        self.assertEqual(independent["overlap_mismatch_count"], 0)
        self.assertEqual(independent["spectrum_mismatch_count"], 0)
        self.assertEqual(independent["closest_comparison_mismatch_count"], 0)
        self.assertFalse(independent["new_floquet_spectra_recomputed"])

    def test_figure_markdown_and_global_registration(self):
        evidence(self)
        with Image.open(ROOT / "pair-inconsistency-structure.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "PAIR_INCONSISTENCY_STRUCTURE.md").read_text(encoding="utf-8")
        for phrase in ("20", "120", "104", "q99", "block_std_max", "共同失败", "不是因果归因", "不是预测", "不补算体 winding", "N=640"):
            self.assertIn(phrase, text)
        runner = (ROOT / "run_verification.py").read_text(encoding="utf-8")
        self.assertIn('("pair_inconsistency_structure_suite"', runner)
        for name in (DATA.name, "pair_inconsistency_structure_independent.json", "PAIR_INCONSISTENCY_STRUCTURE.md", DOCX.name):
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
        self.assertIn("120", document)
        self.assertIn("不是因果归因", document)
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
        qa = load("pair-inconsistency-structure-word-qa.json")
        review = qa["visualReview"]
        self.assertEqual(review["status"], "passed")
        self.assertEqual(review["pagesReviewed"], 5)
        self.assertTrue(review["contactSheetRead"])
        self.assertEqual(review["docxSha256"], sha(DOCX))
        self.assertEqual(review["nearBlankPages"], [])
        self.assertEqual(review["clippedPages"], [])

    def test_analysis_does_not_claim_prediction_or_external_validation(self):
        data = evidence(self)
        self.assertTrue(data["structure_is_descriptive_only"])
        self.assertFalse(data["predictive_validation_completed"])
        self.assertFalse(data["pristine_external_holdout_claim"])
        self.assertFalse(data["causal_attribution_completed"])
        self.assertFalse(data["continuous_path_proof"])
        self.assertFalse(data["spectral_crossing_proven"])
        self.assertFalse(data["state_exchange_proven"])
        self.assertFalse(data["thermodynamic_limit_proof"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
