"""Contracts for entry-resolved overlap and singular-channel response decomposition."""

import hashlib
import json
import math
import re
import sys
import unittest
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "overlap_matrix_response_analysis.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def evidence(test):
    test.assertTrue(DATA.is_file(), "Overlap-matrix response analysis is missing")
    return load(DATA.name)


def source_matrix(seed, strength, method, m):
    rows = load("matched_beta_batch_a_analysis.json")["realizations"] + load("matched_beta_batch_b_analysis.json")["realizations"] + load("matched_beta_batch_c_analysis.json")["realizations"]
    row = next(row for row in rows if row["seed"] == seed and row["strength"] == strength)
    return next(grid for grid in row["methods"][method]["grids"] if grid["m"] == m)["overlap_matrix"]


class OverlapMatrixResponseTests(unittest.TestCase):
    def test_protocol_sources_counts_and_entry_bindings(self):
        data = evidence(self)
        protocol = load("overlap_matrix_response_protocol.json")
        self.assertEqual(data["schema"], "floquet-bdg-overlap-matrix-response-analysis-v1")
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "overlap_matrix_response_protocol.json"))
        self.assertTrue(protocol["registered_before_analysis"])
        self.assertEqual(data["new_floquet_cells_computed"], 0)
        self.assertEqual(data["new_seed_count"], 0)
        self.assertEqual(len(data["method_grid_transitions"]), 48)
        self.assertEqual(len(data["entry_transitions"]), 192)
        self.assertEqual(len(data["representation_delta_agreements"]), 96)
        self.assertEqual(sum(len(row["singular_channels"]) for row in data["entry_transitions"]), 384)
        for name in ("batch_a", "batch_b", "batch_c"):
            self.assertEqual(data[f"{name}_analysis_sha256"], sha(ROOT / f"matched_beta_{name}_analysis.json"))
        for row in data["entry_transitions"]:
            matrix = source_matrix(row["seed"], 0.1, row["method"], row["m"])
            before = matrix[row["i"]][row["j"]]
            matrix_after = source_matrix(row["seed"], 0.2, row["method"], row["m"])
            after = matrix_after[row["i"]][row["j"]]
            self.assertEqual(row["before"], before)
            self.assertEqual(row["after"], after)
        self.assertIn('("overlap_matrix_response_suite"', (ROOT / "run_verification.py").read_text(encoding="utf-8"))

    def test_entry_overlap_ratio_and_singular_identities(self):
        data = evidence(self)
        for row in data["entry_transitions"]:
            before, after = row["before"], row["after"]
            self.assertAlmostEqual(before["overlap"], sum(value * value for value in before["singular_values"]) / 2, places=15)
            self.assertAlmostEqual(after["overlap"], sum(value * value for value in after["singular_values"]) / 2, places=15)
            self.assertAlmostEqual(row["delta_overlap"], after["overlap"] - before["overlap"], places=15)
            expected_group = "diagonal" if row["i"] == row["j"] else "swapped"
            self.assertEqual(row["score_group"], expected_group)
            self.assertAlmostEqual(row["score_contribution"], row["delta_overlap"] / 2, places=15)
            if before["overlap"] > 0:
                self.assertAlmostEqual(row["ratio"], after["overlap"] / before["overlap"], places=12)
                self.assertAlmostEqual(row["log2_ratio"], math.log2(row["ratio"]), places=12)
            else:
                self.assertIsNone(row["ratio"])
                self.assertIsNone(row["log2_ratio"])
            channel_delta_sum = 0.0
            for k, channel in enumerate(row["singular_channels"]):
                expected = after["singular_values"][k] ** 2 - before["singular_values"][k] ** 2
                self.assertAlmostEqual(channel["delta_s_squared"], expected, places=15)
                self.assertAlmostEqual(channel["score_contribution"], expected / 2, places=15)
                channel_delta_sum += channel["score_contribution"]
            self.assertAlmostEqual(channel_delta_sum, row["delta_overlap"], places=15)
            expected_driver = max((0, 1), key=lambda k: abs(row["singular_channels"][k]["score_contribution"]))
            self.assertEqual(row["dominant_singular_channel_index"], expected_driver)
        self.assertFalse(data["normalization_correction_applied"])
        self.assertFalse(data["causal_mechanism_proven"])

    def test_method_grid_score_changes_and_entry_drivers(self):
        data = evidence(self)
        entries = {(row["seed"], row["method"], row["m"], row["i"], row["j"]): row for row in data["entry_transitions"]}
        for row in data["method_grid_transitions"]:
            seed, method, m = row["seed"], row["method"], row["m"]
            before = source_matrix(seed, 0.1, method, m)
            after = source_matrix(seed, 0.2, method, m)
            old_diagonal = (before[0][0]["overlap"] + before[1][1]["overlap"]) / 2
            new_diagonal = (after[0][0]["overlap"] + after[1][1]["overlap"]) / 2
            old_swapped = (before[0][1]["overlap"] + before[1][0]["overlap"]) / 2
            new_swapped = (after[0][1]["overlap"] + after[1][0]["overlap"]) / 2
            self.assertAlmostEqual(row["delta_diagonal_score"], new_diagonal - old_diagonal, places=15)
            self.assertAlmostEqual(row["delta_swapped_score"], new_swapped - old_swapped, places=15)
            self.assertAlmostEqual(row["diagonal_score_ratio"], new_diagonal / old_diagonal, places=12)
            self.assertAlmostEqual(row["swapped_score_ratio"], new_swapped / old_swapped, places=12)
            for group, pairs in (("diagonal", ((0, 0), (1, 1))), ("swapped", ((0, 1), (1, 0)))):
                expected = max(pairs, key=lambda ij: abs(entries[(seed, method, m, *ij)]["score_contribution"]))
                self.assertEqual(row[f"dominant_{group}_entry"], f"O{expected[0]}{expected[1]}")
        self.assertFalse(data["spectral_crossing_proven"])
        self.assertFalse(data["state_exchange_proven"])

    def test_entry_summary_and_representation_sign_agreements(self):
        data = evidence(self)
        self.assertEqual(len(data["entry_summary"]), 24)
        for summary in data["entry_summary"]:
            rows = [row for row in data["entry_transitions"] if row["method"] == summary["method"] and row["m"] == summary["m"] and row["entry"] == summary["entry"]]
            self.assertEqual(len(rows), 8)
            expected = {
                "positive": sum(row["delta_overlap"] > 0 for row in rows),
                "negative": sum(row["delta_overlap"] < 0 for row in rows),
                "zero_exact": sum(row["delta_overlap"] == 0 for row in rows),
            }
            self.assertEqual(summary["delta_sign_counts"], expected)
            ratios = [row["ratio"] for row in rows if row["ratio"] is not None]
            self.assertAlmostEqual(summary["ratio_range"][0], min(ratios), places=12)
            self.assertAlmostEqual(summary["ratio_range"][1], max(ratios), places=12)
            self.assertEqual(summary["before_overlap_range"], [min(row["before"]["overlap"] for row in rows), max(row["before"]["overlap"] for row in rows)])
            self.assertEqual(summary["after_overlap_range"], [min(row["after"]["overlap"] for row in rows), max(row["after"]["overlap"] for row in rows)])
        self.assertEqual(len(data["representation_delta_agreements"]), 96)
        for row in data["representation_delta_agreements"]:
            lp = next(item for item in data["entry_transitions"] if item["seed"] == row["seed"] and item["m"] == row["m"] and item["entry"] == row["entry"] and item["method"] == "linear_point")
            ca = next(item for item in data["entry_transitions"] if item["seed"] == row["seed"] and item["m"] == row["m"] and item["entry"] == row["entry"] and item["method"] == "cell_average")
            sign = lambda value: 1 if value > 0 else -1 if value < 0 else 0
            self.assertEqual(row["linear_point_sign"], sign(lp["delta_overlap"]))
            self.assertEqual(row["cell_average_sign"], sign(ca["delta_overlap"]))
            self.assertEqual(row["agreement"], row["linear_point_sign"] == row["cell_average_sign"])
        self.assertEqual(data["summary"]["representation_sign_agreement_count"], sum(row["agreement"] for row in data["representation_delta_agreements"]))
        self.assertFalse(data["representation_invariant_claim"])

    def test_fidelity_rank_controls_and_interpretation_boundaries(self):
        data = evidence(self)
        c = load("matched_beta_batch_c_analysis.json")
        controls = data["high_strength_controls"]
        self.assertEqual(controls["representation_fidelity_range"], [c["summary"]["min_representation_fidelity"], c["summary"]["max_representation_fidelity"]])
        self.assertEqual(controls["max_linear_point_off_diagonal"], c["summary"]["max_linear_point_off_diagonal"])
        self.assertEqual(controls["max_cell_average_off_diagonal"], c["summary"]["max_cell_average_off_diagonal"])
        self.assertEqual(controls["max_native_off_diagonal"], c["summary"]["max_native_off_diagonal"])
        for key in ("universal_size_law_claim", "continuous_path_proof", "spectral_crossing_proven", "state_exchange_proven", "new_taxonomy_claim", "new_winding_computed", "n640_computed", "statistical_significance_claim", "thermodynamic_limit_proof", "causal_mechanism_proven"):
            self.assertFalse(data[key])

    def test_independent_decomposition_recheck(self):
        path = ROOT / "overlap_matrix_response_independent.json"
        self.assertTrue(path.is_file(), "Independent overlap-matrix recheck is missing")
        independent = load(path.name)
        self.assertTrue(independent["all_passed"])
        self.assertEqual(independent["protocol_sha256"], sha(ROOT / "overlap_matrix_response_protocol.json"))
        self.assertEqual(independent["method_grid_transition_count"], 48)
        self.assertEqual(independent["entry_transition_count"], 192)
        self.assertEqual(independent["singular_channel_transition_count"], 384)
        self.assertEqual(independent["representation_delta_comparison_count"], 96)
        self.assertLessEqual(independent["max_delta_absolute_error"], 1e-15)
        self.assertLessEqual(independent["max_singular_delta_absolute_error"], 1e-15)
        self.assertLessEqual(independent["max_ratio_absolute_error"], 1e-12)
        self.assertEqual(independent["driver_mismatch_count"], 0)
        self.assertTrue(independent["source_independent_rechecks_all_passed"])
        self.assertFalse(independent["new_floquet_spectra_recomputed"])

    def test_figure_markdown_and_native_word_review(self):
        evidence(self)
        with Image.open(ROOT / "overlap-matrix-response.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "OVERLAP_MATRIX_RESPONSE.md").read_text(encoding="utf-8")
        for phrase in ("2×2", "主奇异值", "不归一化", "不能外推", "不补算体 winding", "N=640", "不筛选", "数值贡献"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-重叠矩阵响应分解.docx"
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
        qa = load("overlap-matrix-response-word-qa.json")
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 5)
        self.assertTrue(qa["visualReview"]["contactSheetRead"])
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])

    def test_word_layout_and_analysis_scope(self):
        from xml.etree import ElementTree as ET

        data = evidence(self)
        docx = ROOT / "Floquet-BdG-重叠矩阵响应分解.docx"
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
        self.assertEqual(data["new_floquet_cells_computed"], 0)
        self.assertTrue(data["all_preregistered_results_retained"])
        self.assertFalse(data["statistical_significance_claim"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
