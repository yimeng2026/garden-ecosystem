"""Contracts for batch B, single-anchor reuse and unique A+B descriptive coverage."""

import hashlib
import json
import math
import re
import sys
import unittest
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "matched_beta_batch_b_analysis.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def evidence(test):
    test.assertTrue(DATA.is_file(), "Preregistered batch-B analysis is missing")
    return load(DATA.name)


class MatchedBetaBatchBTests(unittest.TestCase):
    def test_protocol_new_and_reused_counts_and_exact_coarsening(self):
        data = evidence(self)
        protocol = load("matched_beta_batch_b_protocol.json")
        self.assertEqual(data["schema"], "floquet-bdg-matched-beta-batch-b-analysis-v1")
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "matched_beta_batch_b_protocol.json"))
        self.assertTrue(protocol["registered_before_analysis"])
        self.assertEqual(protocol["seed_values"], [4, 5, 6, 7])
        self.assertEqual(protocol["strength_values"], [0.05, 0.1])
        self.assertEqual(data["new_realization_count"], 7)
        self.assertEqual(data["reused_anchor_realization_count"], 1)
        self.assertEqual(data["reported_realization_count"], 8)
        self.assertEqual(data["new_control_cells"], 14)
        self.assertEqual(data["reused_anchor_control_cells"], 2)
        self.assertEqual(data["reported_control_cells"], 16)
        self.assertEqual(data["new_seed_count"], 0)
        self.assertEqual(len(data["realizations"]), 8)
        expected_keys = [(seed, strength) for seed in (4, 5, 6, 7) for strength in (0.05, 0.1)]
        self.assertEqual([(row["seed"], row["strength"]) for row in data["realizations"]], expected_keys)
        roles = Counter(row["evidence_role"] for row in data["realizations"])
        self.assertEqual(roles, {"new_batch_b": 7, "reused_anchor": 1})
        anchor = next(row for row in data["realizations"] if row["evidence_role"] == "reused_anchor")
        self.assertEqual((anchor["seed"], anchor["strength"]), (6, 0.05))
        self.assertFalse(anchor["recomputed_for_new_analysis"])
        source = load("matched_beta_control_analysis.json")
        self.assertEqual(anchor["source_analysis_sha256"], sha(ROOT / "matched_beta_control_analysis.json"))
        self.assertEqual(anchor["master_profile"], source["master_profile"])
        self.assertEqual(anchor["cells"], source["cells"])
        self.assertEqual(anchor["methods"], source["methods"])
        for realization in data["realizations"]:
            master = np.random.default_rng(20261111 + realization["seed"]).random(4800)
            self.assertEqual(realization["master_profile_sha256"], hashlib.sha256(master.tobytes()).hexdigest())
            self.assertTrue(realization["strength_pair_master_reused"])
            self.assertEqual(len(realization["cells"]), 2)
            for cell in realization["cells"]:
                n = cell["n"]
                expected = master.reshape(n, 4800 // n).mean(axis=1)
                self.assertEqual(cell["coarsening_max_absolute_error"], 0.0)
                self.assertTrue(np.array_equal(np.asarray(cell["beta"]), expected))
        self.assertIn('("matched_beta_batch_b_suite"', (ROOT / "run_verification.py").read_text(encoding="utf-8"))

    def test_spectrum_and_pair_metrics_are_consistent(self):
        data = evidence(self)
        for realization in data["realizations"]:
            for cell in realization["cells"]:
                self.assertEqual(len(cell["pairs"]), 2)
                self.assertEqual(len(cell["spectrum_first_six"]), 6)
                self.assertGreater(cell["center_separation"], 0)
                for pair in cell["pairs"]:
                    self.assertEqual(len(pair["distances"]), 2)
                    self.assertAlmostEqual(pair["center"], float(np.mean(pair["distances"])), places=15)
                    self.assertAlmostEqual(pair["within_distance_difference"], abs(pair["distances"][1] - pair["distances"][0]), places=15)
                expected = abs(cell["pairs"][1]["center"] - cell["pairs"][0]["center"])
                self.assertAlmostEqual(cell["center_separation"], expected, places=15)
        self.assertFalse(data["spectral_crossing_proven"])
        self.assertFalse(data["avoided_crossing_claim"])

    def test_cross_size_overlap_direction_and_descriptive_counts(self):
        data = evidence(self)
        observed = {method: Counter() for method in ("linear_point", "cell_average")}
        for realization in data["realizations"]:
            for method in ("linear_point", "cell_average"):
                grids = realization["methods"][method]["grids"]
                self.assertEqual([grid["m"] for grid in grids], [1200, 2400, 4800])
                for grid in grids:
                    observed[method][grid["dominant_assignment"]] += 1
                    matrix = grid["overlap_matrix"]
                    diagonal = (matrix[0][0]["overlap"] + matrix[1][1]["overlap"]) / 2
                    swapped = (matrix[0][1]["overlap"] + matrix[1][0]["overlap"]) / 2
                    self.assertAlmostEqual(grid["diagonal_score"], diagonal, places=12)
                    self.assertAlmostEqual(grid["swapped_score"], swapped, places=12)
                    expected = "diagonal" if diagonal > swapped else "swapped" if swapped > diagonal else "tie_exact"
                    self.assertEqual(grid["dominant_assignment"], expected)
                    for row in matrix:
                        for entry in row:
                            self.assertAlmostEqual(entry["overlap"], sum(value * value for value in entry["singular_values"]) / 2, places=12)
                            angles = [math.degrees(math.acos(min(1.0, max(0.0, value)))) for value in entry["singular_values"]]
                            self.assertTrue(np.allclose(entry["principal_angles_deg"], angles, rtol=0, atol=1e-8))
        self.assertEqual(data["summary"]["assignment_counts"], {method: dict(observed[method]) for method in observed})
        self.assertEqual(sum(observed["linear_point"].values()), 24)
        self.assertEqual(sum(observed["cell_average"].values()), 24)
        self.assertLessEqual(data["summary"]["max_direction_absolute_error"], 1e-12)
        self.assertTrue(data["all_preregistered_results_retained"])

    def test_representation_and_native_rank_controls(self):
        data = evidence(self)
        for realization in data["realizations"]:
            fidelity = realization["representation_fidelity"]
            self.assertEqual(len(fidelity), 12)
            for row in fidelity:
                self.assertAlmostEqual(row["forward"], row["reverse"], places=12)
                self.assertAlmostEqual(row["forward"], sum(value * value for value in row["singular_values"]) / 2, places=12)
            self.assertEqual(len(realization["native_rank_controls"]), 2)
        self.assertLessEqual(data["summary"]["max_native_off_diagonal"], 1e-12)
        self.assertLessEqual(data["summary"]["max_cell_average_off_diagonal"], 1e-12)
        self.assertFalse(data["normalization_correction_applied"])
        self.assertFalse(data["representation_invariant_claim"])

    def test_strength_pairs_anchor_and_interpretation_boundaries(self):
        data = evidence(self)
        protocol = load("matched_beta_batch_b_protocol.json")
        self.assertEqual(len(data["strength_pair_comparisons"]), 4)
        by_key = {(row["seed"], row["strength"]): row for row in data["realizations"]}
        for comparison in data["strength_pair_comparisons"]:
            seed = comparison["seed"]
            self.assertEqual(comparison["master_profile_sha256"], by_key[(seed, 0.05)]["master_profile_sha256"])
            self.assertEqual(comparison["master_profile_sha256"], by_key[(seed, 0.1)]["master_profile_sha256"])
            self.assertTrue(comparison["identical_master_profile"])
            for n in (400, 600):
                low = next(row for row in by_key[(seed, 0.05)]["cells"] if row["n"] == n)
                high = next(row for row in by_key[(seed, 0.1)]["cells"] if row["n"] == n)
                key = f"n{n}_center_separation_delta"
                self.assertAlmostEqual(comparison[key], high["center_separation"] - low["center_separation"], places=15)
        self.assertTrue(protocol["anchor_case"]["batch_membership"])
        self.assertEqual(protocol["anchor_case"]["count_weight"], 1)
        self.assertEqual(data["anchor_control_analysis_sha256"], sha(ROOT / "matched_beta_control_analysis.json"))
        self.assertEqual(data["anchor_control_analysis_sha256"], protocol["anchor_case"]["source_analysis_sha256"])
        self.assertTrue(data["anchor_reused_exactly_once"])
        self.assertTrue(data["old_candidate_is_different_realization"])
        self.assertTrue(data["difference_from_original_is_not_size_effect"])
        for key in ("universal_size_law_claim", "continuous_path_proof", "state_exchange_proven", "second_pair_topological_claim", "statistical_significance_claim", "thermodynamic_limit_proof", "new_taxonomy_claim", "new_winding_computed", "n640_computed"):
            self.assertFalse(data[key])
        self.assertEqual(data["size_effect_separated"], "matched_nested_profile_descriptive_only")

    def test_independent_new_and_anchor_spectrum_recheck(self):
        path = ROOT / "matched_beta_batch_b_independent.json"
        self.assertTrue(path.is_file(), "Independent batch-B spectrum recheck is missing")
        independent = load(path.name)
        self.assertTrue(independent["all_passed"])
        self.assertEqual(independent["protocol_sha256"], sha(ROOT / "matched_beta_batch_b_protocol.json"))
        self.assertEqual(independent["realization_count"], 8)
        self.assertEqual(independent["cell_count"], 16)
        self.assertEqual(independent["new_rebuilt_cell_count"], 14)
        self.assertEqual(independent["anchor_rechecked_cell_count"], 2)
        self.assertEqual(independent["max_master_profile_absolute_error"], 0.0)
        self.assertEqual(independent["max_coarsening_absolute_error"], 0.0)
        self.assertLessEqual(independent["max_spectrum_absolute_error"], 1e-12)
        self.assertLessEqual(independent["max_pair_center_absolute_error"], 1e-12)
        self.assertEqual(independent["anchor_independent_source_sha256"], sha(ROOT / "matched_beta_independent.json"))
        self.assertTrue(independent["anchor_independent_source_all_passed"])
        self.assertFalse(independent["new_winding_computed"])
        self.assertFalse(independent["n640_computed"])

    def test_unique_combined_a_plus_b_coverage(self):
        data = evidence(self)
        a = load("matched_beta_batch_a_analysis.json")
        combined = data["combined_with_batch_a"]
        self.assertEqual(data["batch_a_analysis_sha256"], sha(ROOT / "matched_beta_batch_a_analysis.json"))
        self.assertEqual(combined["realization_count"], 16)
        self.assertEqual(combined["control_cells"], 32)
        keys_a = {(row["seed"], row["strength"]) for row in a["realizations"]}
        keys_b = {(row["seed"], row["strength"]) for row in data["realizations"]}
        self.assertFalse(keys_a & keys_b)
        self.assertEqual(len(keys_a | keys_b), 16)
        for method in ("linear_point", "cell_average"):
            expected = Counter(a["summary"]["assignment_counts"][method])
            expected.update(data["summary"]["assignment_counts"][method])
            self.assertEqual(combined["assignment_counts"][method], dict(expected))
            self.assertEqual(sum(expected.values()), 48)
        self.assertEqual(combined["anchor_count"], 1)
        self.assertFalse(combined["statistical_significance_claim"])

    def test_figure_markdown_and_native_word_review(self):
        evidence(self)
        with Image.open(ROOT / "matched-beta-batch-b.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "MATCHED_BETA_BATCH_B.md").read_text(encoding="utf-8")
        for phrase in ("共同无序剖面", "嵌套块平均", "不归一化", "不能外推", "不补算体 winding", "N=640", "不筛选", "复用锚点", "联合"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-共同无序剖面第二批尺寸隔离.docx"
        with zipfile.ZipFile(docx) as package:
            document = package.read("word/document.xml").decode("utf-8")
            footer = "".join(package.read(name).decode("utf-8") for name in package.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            media = [name for name in package.namelist() if name.startswith("word/media/") and not name.endswith("/")]
        self.assertIn("<m:sSub", document)
        self.assertIn("<m:sSup", document)
        self.assertIn("<m:f>", document)
        self.assertIn("TOC", document)
        self.assertIn("PAGE", footer)
        self.assertEqual(len(media), 1)
        grids = re.findall(r"<w:tblGrid>(.*?)</w:tblGrid>", document)
        self.assertTrue(grids)
        for grid in grids:
            self.assertLessEqual(sum(int(value) for value in re.findall(r'w:w="(\d+)"', grid)), 9906)
        qa = load("matched-beta-batch-b-word-qa.json")
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 5)
        self.assertTrue(qa["visualReview"]["contactSheetRead"])
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])

    def test_word_layout_and_analysis_scope(self):
        from xml.etree import ElementTree as ET

        data = evidence(self)
        docx = ROOT / "Floquet-BdG-共同无序剖面第二批尺寸隔离.docx"
        with zipfile.ZipFile(docx) as package:
            root = ET.fromstring(package.read("word/document.xml"))
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        attr = lambda name: f"{{{ns['w']}}}{name}"
        for table in root.findall(".//w:tbl", ns):
            for cell in table.findall(".//w:tc", ns):
                spacing = cell.find("w:p/w:pPr/w:spacing", ns)
                self.assertEqual(spacing.get(attr("after")), "40")
                self.assertEqual(spacing.get(attr("line")), "240")
                self.assertEqual(spacing.get(attr("lineRule")), "auto")
                margins = cell.find("w:tcPr/w:tcMar", ns)
                for side, expected in (("top", "80"), ("bottom", "80"), ("left", "60"), ("right", "60")):
                    self.assertEqual(margins.find(f"w:{side}", ns).get(attr("w")), expected)
        self.assertEqual(data["new_control_cells"], 14)
        self.assertEqual(data["reused_anchor_control_cells"], 2)
        self.assertTrue(data["all_preregistered_results_retained"])
        self.assertFalse(data["statistical_significance_claim"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
