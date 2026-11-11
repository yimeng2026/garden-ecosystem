"""Contracts for preregistered midpoint refinement and step-size stability checks."""

import hashlib
import json
import re
import sys
import unittest
import zipfile
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "seed6_matrix_midpoint_analysis.json"
STRENGTHS = [0.1, 0.1125, 0.125, 0.13125, 0.1375, 0.14375, 0.15, 0.1625, 0.175, 0.18125, 0.1875, 0.19375, 0.2]
MIDPOINTS = [0.13125, 0.14375, 0.18125, 0.19375]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def evidence(test):
    test.assertTrue(DATA.is_file(), "Seed-6 midpoint analysis is missing")
    return load(DATA.name)


class Seed6MatrixMidpointTests(unittest.TestCase):
    def test_protocol_cells_counts_and_nested_profiles(self):
        data = evidence(self)
        protocol = load("seed6_matrix_midpoint_protocol.json")
        self.assertEqual(data["schema"], "floquet-bdg-seed6-matrix-midpoint-analysis-v1")
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "seed6_matrix_midpoint_protocol.json"))
        self.assertTrue(protocol["registered_before_analysis"])
        self.assertEqual(protocol["strengths"], STRENGTHS)
        self.assertEqual(protocol["new_midpoint_strengths"], MIDPOINTS)
        self.assertEqual(len(data["cells"]), 26)
        self.assertEqual(len(data["path_matrices"]), 78)
        self.assertEqual(len(data["links"]), 24)
        self.assertEqual(len(data["method_grid_links"]), 72)
        self.assertEqual(len(data["entry_links"]), 288)
        self.assertEqual(len(data["representation_fidelity"]), 156)
        self.assertEqual(len(data["rank_controls"]), 182)
        self.assertEqual(data["new_midpoint_control_cells"], 8)
        self.assertEqual(data["reused_path_control_cells"], 18)
        self.assertEqual(data["evaluated_control_cells"], 26)
        self.assertTrue(data["not_merged_into_batch_counts"])
        self.assertEqual([(row["strength"], row["n"]) for row in data["cells"]], [(strength, n) for strength in STRENGTHS for n in (400, 600)])
        self.assertEqual(sum(row["new_for_path"] for row in data["cells"]), 8)
        master = np.random.default_rng(20261117).random(4800)
        for cell in data["cells"]:
            n = cell["n"]
            self.assertTrue(np.array_equal(np.asarray(cell["beta"]), master.reshape(n, 4800 // n).mean(axis=1)))
            self.assertEqual(cell["coarsening_max_absolute_error"], 0.0)
        self.assertIn('("seed6_matrix_midpoint_suite"', (ROOT / "run_verification.py").read_text(encoding="utf-8"))

    def test_spectra_and_original_path_binding(self):
        data = evidence(self)
        for cell in data["cells"]:
            self.assertEqual(len(cell["spectrum_first_six"]), 6)
            for pair in cell["pairs"]:
                self.assertAlmostEqual(pair["center"], float(np.mean(pair["distances"])), places=15)
            self.assertAlmostEqual(cell["center_separation"], abs(cell["pairs"][1]["center"] - cell["pairs"][0]["center"]), places=15)
        binding = data["original_path_binding"]
        self.assertEqual(binding["original_matrix_count"], 54)
        self.assertEqual(binding["original_cell_count"], 18)
        self.assertLessEqual(binding["max_matrix_absolute_error"], 1e-12)
        self.assertLessEqual(binding["max_singular_absolute_error"], 1e-12)
        self.assertLessEqual(binding["max_spectrum_absolute_error"], 1e-12)
        self.assertEqual(data["original_path_analysis_sha256"], sha(ROOT / "seed6_matrix_path_analysis.json"))

    def test_cross_size_matrices_and_assignment_counts(self):
        data = evidence(self)
        observed = {method: Counter() for method in ("linear_point", "cell_average")}
        for row in data["path_matrices"]:
            matrix = row["overlap_matrix"]
            diagonal = (matrix[0][0]["overlap"] + matrix[1][1]["overlap"]) / 2
            swapped = (matrix[0][1]["overlap"] + matrix[1][0]["overlap"]) / 2
            self.assertAlmostEqual(row["diagonal_score"], diagonal, places=12)
            self.assertAlmostEqual(row["swapped_score"], swapped, places=12)
            expected = "diagonal" if diagonal > swapped else "swapped" if swapped > diagonal else "tie_exact"
            self.assertEqual(row["dominant_assignment"], expected)
            observed[row["method"]][expected] += 1
            for entry_row in matrix:
                for entry in entry_row:
                    self.assertAlmostEqual(entry["overlap"], sum(value * value for value in entry["singular_values"]) / 2, places=12)
        self.assertEqual(data["summary"]["cross_size_assignment_counts"], {method: dict(observed[method]) for method in observed})
        self.assertEqual(sum(observed["linear_point"].values()), 39)
        self.assertEqual(sum(observed["cell_average"].values()), 39)
        self.assertFalse(data["normalization_correction_applied"])

    def test_extrema_and_jump_comparisons(self):
        data = evidence(self)
        old = load("seed6_matrix_path_analysis.json")
        self.assertEqual(len(data["entry_extrema"]), 8)
        self.assertEqual(len(data["jump_comparisons"]), 8)
        for comparison in data["jump_comparisons"]:
            method, entry = comparison["method"], comparison["entry"]
            old_row = next(row for row in old["entry_extrema"] if row["method"] == method and row["entry"] == entry)
            new_row = next(row for row in data["entry_extrema"] if row["method"] == method and row["entry"] == entry)
            self.assertEqual(comparison["old_max_adjacent_absolute_jump"], old_row["max_adjacent_absolute_jump"])
            self.assertEqual(comparison["refined_max_adjacent_absolute_jump"], new_row["max_adjacent_absolute_jump"])
            self.assertEqual(comparison["old_jump_from"], old_row["max_jump_from"])
            self.assertEqual(comparison["old_jump_to"], old_row["max_jump_to"])
            self.assertEqual(comparison["refined_jump_from"], new_row["max_jump_from"])
            self.assertEqual(comparison["refined_jump_to"], new_row["max_jump_to"])
            expected_changed = (old_row["max_jump_from"], old_row["max_jump_to"], old_row["max_adjacent_absolute_jump"]) != (new_row["max_jump_from"], new_row["max_jump_to"], new_row["max_adjacent_absolute_jump"])
            self.assertEqual(comparison["jump_changed"], expected_changed)
            links = [row for row in data["entry_links"] if row["method"] == method and row["m"] == 4800 and row["entry"] == entry]
            self.assertEqual(len(links), 12)
            jump = max(links, key=lambda row: abs(row["delta_overlap"]))
            self.assertEqual(new_row["max_adjacent_absolute_jump"], abs(jump["delta_overlap"]))
        self.assertFalse(data["continuous_path_proof"])

    def test_driver_comparisons_and_singular_channels(self):
        data = evidence(self)
        old = load("seed6_matrix_path_analysis.json")
        self.assertEqual(len(data["driver_comparisons"]), 4)
        for comparison in data["driver_comparisons"]:
            old_row = next(row for row in old["driver_summary"] if row["method"] == comparison["method"] and row["score_group"] == comparison["score_group"])
            self.assertEqual(comparison["old_dominant_entry_counts"], old_row["dominant_entry_counts"])
            self.assertEqual(comparison["old_link_count"], 8)
            self.assertEqual(comparison["refined_link_count"], 12)
            rows = [row for row in data["method_grid_links"] if row["method"] == comparison["method"] and row["m"] == 4800]
            group = comparison["score_group"]
            for entry, count in comparison["refined_dominant_entry_counts"].items():
                self.assertEqual(count, sum(row[f"dominant_{group}_entry"] == entry for row in rows))
        for row in data["entry_links"]:
            self.assertAlmostEqual(row["score_contribution"], row["delta_overlap"] / 2, places=15)
            delta_sum = 0.0
            for channel in row["singular_channels"]:
                self.assertAlmostEqual(channel["score_contribution"], channel["delta_s_squared"] / 2, places=15)
                delta_sum += channel["score_contribution"]
            self.assertAlmostEqual(delta_sum, row["delta_overlap"], places=15)
            expected = max((0, 1), key=lambda k: abs(row["singular_channels"][k]["score_contribution"]))
            self.assertEqual(row["dominant_singular_channel_index"], expected)
        self.assertFalse(data["causal_mechanism_proven"])

    def test_representation_fidelity_and_rank_controls(self):
        data = evidence(self)
        self.assertEqual(len(data["representation_fidelity"]), 156)
        for row in data["representation_fidelity"]:
            self.assertAlmostEqual(row["forward"], row["reverse"], places=12)
            self.assertAlmostEqual(row["forward"], sum(value * value for value in row["singular_values"]) / 2, places=12)
        self.assertLessEqual(data["summary"]["max_native_off_diagonal"], 1e-12)
        self.assertLessEqual(data["summary"]["max_cell_average_off_diagonal"], 1e-12)
        self.assertLessEqual(data["summary"]["max_direction_absolute_error"], 1e-12)
        self.assertFalse(data["representation_invariant_claim"])

    def test_native_adjacent_links_and_finite_path_boundaries(self):
        data = evidence(self)
        self.assertEqual(len(data["links"]), 24)
        for link in data["links"]:
            matrix = link["overlap_matrix"]
            diagonal = (matrix[0][0]["overlap"] + matrix[1][1]["overlap"]) / 2
            swapped = (matrix[0][1]["overlap"] + matrix[1][0]["overlap"]) / 2
            self.assertAlmostEqual(link["diagonal_score"], diagonal, places=12)
            self.assertAlmostEqual(link["swapped_score"], swapped, places=12)
            expected = "diagonal" if diagonal > swapped else "swapped" if swapped > diagonal else "tie_exact"
            self.assertEqual(link["dominant_assignment"], expected)
            self.assertAlmostEqual(link["center_separation_delta"], link["center_separation_after"] - link["center_separation_before"], places=15)
        self.assertEqual(len(data["link_summary"]), 2)
        for n in (400, 600):
            rows = [row for row in data["links"] if row["n"] == n]
            summary = next(row for row in data["link_summary"] if row["n"] == n)
            self.assertEqual(summary["link_count"], 12)
            self.assertEqual(summary["min_diagonal_score"], min(row["diagonal_score"] for row in rows))
            self.assertEqual(summary["max_swapped_score"], max(row["swapped_score"] for row in rows))
        for key in ("continuous_path_proof", "spectral_crossing_proven", "avoided_crossing_claim", "state_exchange_proven", "statistical_significance_claim", "thermodynamic_limit_proof"):
            self.assertFalse(data[key])

    def test_independent_midpoint_recheck(self):
        path = ROOT / "seed6_matrix_midpoint_independent.json"
        self.assertTrue(path.is_file(), "Independent midpoint recheck is missing")
        independent = load(path.name)
        self.assertTrue(independent["all_passed"])
        self.assertEqual(independent["protocol_sha256"], sha(ROOT / "seed6_matrix_midpoint_protocol.json"))
        self.assertEqual(independent["cell_count"], 26)
        self.assertEqual(independent["cross_size_path_matrix_count"], 78)
        self.assertEqual(independent["native_adjacent_link_count"], 24)
        self.assertEqual(independent["entry_link_count"], 288)
        self.assertLessEqual(independent["max_spectrum_absolute_error"], 1e-12)
        self.assertLessEqual(independent["max_pair_center_absolute_error"], 1e-12)
        self.assertLessEqual(independent["max_matrix_absolute_error"], 1e-12)
        self.assertLessEqual(independent["max_entry_delta_absolute_error"], 1e-12)
        self.assertLessEqual(independent["max_native_link_absolute_error"], 1e-12)
        self.assertFalse(independent["new_winding_computed"])
        self.assertFalse(independent["n640_computed"])

    def test_figure_markdown_and_native_word_review(self):
        evidence(self)
        with Image.open(ROOT / "seed6-matrix-midpoint.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "SEED6_MATRIX_MIDPOINT.md").read_text(encoding="utf-8")
        for phrase in ("中点", "步长", "主奇异", "不归一化", "不能外推", "不补算体 winding", "N=640", "不筛选", "数值贡献"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-固定种子跳变窗口中点复核.docx"
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
        qa = load("seed6-matrix-midpoint-word-qa.json")
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 5)
        self.assertTrue(qa["visualReview"]["contactSheetRead"])
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])

    def test_word_layout_and_analysis_scope(self):
        from xml.etree import ElementTree as ET

        data = evidence(self)
        docx = ROOT / "Floquet-BdG-固定种子跳变窗口中点复核.docx"
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
        self.assertEqual(data["new_midpoint_control_cells"], 8)
        self.assertTrue(data["all_preregistered_results_retained"])
        self.assertFalse(data["statistical_significance_claim"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
