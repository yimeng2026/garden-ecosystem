"""Contracts for the full preregistered common-embedding census."""

import hashlib
import json
import math
import re
import sys
import unittest
import zipfile
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
METHODS = ("linear_point", "cell_average")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def assignment_counts(cases, method=None, finest_only=False):
    counts = Counter()
    for case in cases:
        for method_name, method_data in case["methods"].items():
            if method is not None and method_name != method:
                continue
            grids = method_data["grids"][-1:] if finest_only else method_data["grids"]
            counts.update(grid["dominant_assignment"] for grid in grids)
    return dict(counts)


class EmbeddingCensusTests(unittest.TestCase):
    def test_full_frozen_registry_and_sources(self):
        protocol = load("embedding_census_protocol.json")
        data = load("embedding_census_analysis.json")
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "embedding_census_protocol.json"))
        self.assertEqual(data["source_sha256"], sha(ROOT / "repeated_category_analysis.json"))
        self.assertEqual(data["previous_linear_source_sha256"], sha(ROOT / "subspace_overlap_analysis.json"))
        self.assertEqual(data["previous_robustness_source_sha256"], sha(ROOT / "embedding_robustness_analysis.json"))
        self.assertEqual(protocol["seeds"], list(range(8)))
        self.assertEqual(protocol["strengths"], [0.05, 0.1])
        self.assertEqual(protocol["methods"], list(METHODS))
        self.assertEqual(protocol["common_grids"], [1200, 2400, 4800])
        self.assertEqual(len(data["cases"]), 16)
        self.assertEqual(len(data["cells"]), 32)
        self.assertEqual(data["new_physics_cells"], 0)
        self.assertTrue(data["all_preregistered_contrasts"])
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])
        self.assertIn('("embedding_census_suite"', (ROOT / "run_verification.py").read_text(encoding="utf-8"))
        self.assertIn('"--check-only"', (ROOT / "run_embedding_census_verification.py").read_text(encoding="utf-8"))

    def test_all_profiles_and_previous_three_cases_are_reproduced(self):
        data = load("embedding_census_analysis.json")
        source = load("repeated_category_analysis.json")
        previous_linear = load("subspace_overlap_analysis.json")
        previous_robust = load("embedding_robustness_analysis.json")
        for cell in data["cells"]:
            old = next(row for row in source["all_cells"] if (row["n"], row["strength"], row["seed"]) == (cell["n"], cell["strength"], cell["seed"]))
            for pair in cell["pairs"]:
                self.assertEqual(pair["stored_profile_sha256"], old["pairs"][pair["pair_index"]]["profile_sha256"])
                self.assertLessEqual(pair["max_profile_absolute_error"], 1e-10)
                self.assertLessEqual(pair["edge_weight_absolute_error"], 1e-10)
        self.assertLessEqual(data["max_profile_absolute_error"], 1e-10)
        for case in data["cases"]:
            if case["label"] not in ("near_miss_low", "near_miss_high", "reference_weakening"):
                continue
            old_linear = next(row for row in previous_linear["cases"] if row["label"] == case["label"])
            old_cell = next(row for row in previous_robust["cases"] if row["label"] == case["label"])
            for index, grid in enumerate(case["methods"]["linear_point"]["grids"]):
                old = old_linear["grids"][index]
                self.assertAlmostEqual(grid["diagonal_score"], old["diagonal_score"], places=12)
                self.assertAlmostEqual(grid["swapped_score"], old["swapped_score"], places=12)
                for i in range(2):
                    for j in range(2):
                        self.assertAlmostEqual(grid["overlap_matrix"][i][j]["overlap"], old["overlap_matrix"][i][j]["overlap"], places=12)
            for index, grid in enumerate(case["methods"]["cell_average"]["grids"]):
                old = old_cell["methods"]["cell_average"]["grids"][index]
                self.assertAlmostEqual(grid["diagonal_score"], old["diagonal_score"], places=12)
                self.assertAlmostEqual(grid["swapped_score"], old["swapped_score"], places=12)
                for i in range(2):
                    for j in range(2):
                        self.assertAlmostEqual(grid["overlap_matrix"][i][j]["overlap"], old["overlap_matrix"][i][j]["overlap"], places=12)
        self.assertLessEqual(data["previous_linear_reproduction_error"], 1e-12)
        self.assertLessEqual(data["previous_cell_reproduction_error"], 1e-12)

    def test_overlap_metrics_and_assignments_are_consistent(self):
        data = load("embedding_census_analysis.json")
        for case in data["cases"]:
            for name in METHODS:
                self.assertEqual(len(case["methods"][name]["grids"]), 3)
                for grid in case["methods"][name]["grids"]:
                    matrix = grid["overlap_matrix"]
                    for i in range(2):
                        for j in range(2):
                            entry = matrix[i][j]
                            singular = entry["singular_values"]
                            self.assertTrue(all(0 <= value <= 1 + 1e-12 for value in singular))
                            self.assertAlmostEqual(entry["overlap"], sum(value * value for value in singular) / 2, places=12)
                            angles = [math.degrees(math.acos(min(1.0, max(0.0, value)))) for value in singular]
                            self.assertAlmostEqual(entry["principal_angles_deg"][0], angles[0], places=8)
                            self.assertAlmostEqual(entry["principal_angles_deg"][1], angles[1], places=8)
                    diagonal = (matrix[0][0]["overlap"] + matrix[1][1]["overlap"]) / 2
                    swapped = (matrix[0][1]["overlap"] + matrix[1][0]["overlap"]) / 2
                    self.assertAlmostEqual(grid["diagonal_score"], diagonal, places=12)
                    self.assertAlmostEqual(grid["swapped_score"], swapped, places=12)
                    expected = "diagonal" if diagonal > swapped else "swapped" if swapped > diagonal else "tie_exact"
                    self.assertEqual(grid["dominant_assignment"], expected)

    def test_summary_counts_and_swap_candidates_are_exact(self):
        data = load("embedding_census_analysis.json")
        cases = data["cases"]
        summary = data["summary"]
        self.assertEqual(summary["method_grid_count"], 96)
        self.assertEqual(summary["diagonal_dominant_count"], assignment_counts(cases).get("diagonal", 0))
        self.assertEqual(summary["method_assignment_counts"]["linear_point"], assignment_counts(cases, "linear_point"))
        self.assertEqual(summary["method_assignment_counts"]["cell_average"], assignment_counts(cases, "cell_average"))
        self.assertEqual(summary["finest_assignment_counts"]["linear_point"], assignment_counts(cases, "linear_point", True))
        self.assertEqual(summary["finest_assignment_counts"]["cell_average"], assignment_counts(cases, "cell_average", True))
        comparisons = [row for case in cases for row in case["method_comparisons"]]
        self.assertEqual(len(comparisons), 48)
        self.assertEqual(summary["same_assignment_count"], sum(row["same_dominant_assignment"] for row in comparisons))
        self.assertEqual(summary["finest_same_assignment_count"], sum(row["m"] == 4800 and row["same_dominant_assignment"] for row in comparisons))
        self.assertEqual(summary["fully_diagonal_case_count"], sum(all(grid["dominant_assignment"] == "diagonal" for method in case["methods"].values() for grid in method["grids"]) for case in cases))
        candidates = sorted({case["label"] for case in cases for row in case["method_comparisons"] if row["m"] == 4800 and (row["linear_assignment"] == "swapped" or row["cell_average_assignment"] == "swapped")})
        self.assertEqual(summary["swapped_candidate_cases"], candidates)
        expected_max = max(abs(row["diagonal_score_change_cell_minus_linear"]) for row in comparisons)
        self.assertAlmostEqual(summary["max_absolute_diagonal_score_change"], expected_max, places=12)

    def test_full_census_does_not_change_physics_or_categories(self):
        data = load("embedding_census_analysis.json")
        source = load("repeated_category_analysis.json")
        self.assertEqual(data["original_category_counts"], source["category_counts"])
        self.assertFalse(data["representation_invariant_claim"])
        self.assertFalse(data["same_physics_state_tracking_claim"])
        self.assertFalse(data["rank_exchange_proven"])
        self.assertFalse(data["embedding_convergence_proof"])
        self.assertFalse(data["second_pair_topological_claim"])
        self.assertFalse(data["new_taxonomy_claim"])
        self.assertFalse(data["categories_changed"])
        self.assertFalse(data["statistical_significance_claim"])
        self.assertFalse(data["universal_mechanism_claim"])

    def test_figure_markdown_and_reviewed_word(self):
        with Image.open(ROOT / "embedding-census.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "EMBEDDING_CENSUS.md").read_text(encoding="utf-8")
        for phrase in ("16个", "交换候选", "共同表示", "不是", "态追踪", "不新增类别", "N=640"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-全样本共同表示审计.docx"
        with zipfile.ZipFile(docx) as package:
            document = package.read("word/document.xml").decode("utf-8")
            footer = "".join(package.read(name).decode("utf-8") for name in package.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            media = [name for name in package.namelist() if name.startswith("word/media/") and not name.endswith("/")]
        self.assertIn("m:oMath", document)
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
        qa = load("embedding-census-word-qa.json")
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])
        runner = (ROOT / "run_embedding_census_verification.py").read_text(encoding="utf-8")
        self.assertNotIn('("docx_build"', runner)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
