"""Contracts for comparing common-grid embeddings without changing physics input."""

import hashlib
import json
import math
import re
import sys
import unittest
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
METHODS = ("linear_point", "cell_average")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class EmbeddingRobustnessTests(unittest.TestCase):
    def test_frozen_registry_and_sources(self):
        protocol = load("embedding_robustness_protocol.json")
        data = load("embedding_robustness_analysis.json")
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "embedding_robustness_protocol.json"))
        self.assertEqual(data["source_sha256"], sha(ROOT / "repeated_category_analysis.json"))
        self.assertEqual(data["previous_linear_source_sha256"], sha(ROOT / "subspace_overlap_analysis.json"))
        self.assertEqual(protocol["methods"], list(METHODS))
        self.assertEqual(protocol["common_grids"], [1200, 2400, 4800])
        self.assertEqual(protocol["new_physics_cells"], 0)
        self.assertEqual(len(data["cases"]), 3)
        self.assertEqual(len(data["cells"]), 6)
        self.assertTrue(data["verification_eigenvectors_recomputed"])
        self.assertEqual(data["new_physics_cells"], 0)
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])
        self.assertFalse(data["same_physics_state_tracking_claim"])
        self.assertIn('("embedding_robustness_suite"', (ROOT / "run_verification.py").read_text(encoding="utf-8"))

    def test_profiles_and_previous_linear_results_are_reproduced(self):
        data = load("embedding_robustness_analysis.json")
        source = load("repeated_category_analysis.json")
        previous = load("subspace_overlap_analysis.json")
        for cell in data["cells"]:
            old = next(row for row in source["all_cells"] if (row["n"], row["strength"], row["seed"]) == (cell["n"], cell["strength"], cell["seed"]))
            for pair in cell["pairs"]:
                self.assertEqual(pair["stored_profile_sha256"], old["pairs"][pair["pair_index"]]["profile_sha256"])
                self.assertLessEqual(pair["max_profile_absolute_error"], 1e-10)
                self.assertLessEqual(pair["edge_weight_absolute_error"], 1e-10)
        self.assertLessEqual(data["max_profile_absolute_error"], 1e-10)
        for case in data["cases"]:
            old = next(row for row in previous["cases"] if row["label"] == case["label"])
            for method in case["methods"].values():
                self.assertEqual(len(method["grids"]), 3)
            for index, grid in enumerate(case["methods"]["linear_point"]["grids"]):
                old_grid = old["grids"][index]
                self.assertEqual(grid["m"], old_grid["m"])
                self.assertAlmostEqual(grid["diagonal_score"], old_grid["diagonal_score"], places=12)
                self.assertAlmostEqual(grid["swapped_score"], old_grid["swapped_score"], places=12)
                for i in range(2):
                    for j in range(2):
                        self.assertAlmostEqual(grid["overlap_matrix"][i][j]["overlap"], old_grid["overlap_matrix"][i][j]["overlap"], places=12)
        self.assertLessEqual(data["max_linear_reproduction_error"], 1e-12)

    def test_overlap_metrics_are_consistent_for_both_methods(self):
        data = load("embedding_robustness_analysis.json")
        for case in data["cases"]:
            for name in METHODS:
                for grid in case["methods"][name]["grids"]:
                    matrix = grid["overlap_matrix"]
                    for i in range(2):
                        for j in range(2):
                            entry = matrix[i][j]
                            singular = entry["singular_values"]
                            self.assertEqual(len(singular), 2)
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

    def test_method_comparison_and_summary_are_exact(self):
        data = load("embedding_robustness_analysis.json")
        diagonal_count = 0
        finest_same = 0
        for case in data["cases"]:
            self.assertEqual(len(case["method_comparisons"]), 3)
            for index, comparison in enumerate(case["method_comparisons"]):
                linear = case["methods"]["linear_point"]["grids"][index]
                cell = case["methods"]["cell_average"]["grids"][index]
                self.assertEqual(comparison["m"], linear["m"])
                self.assertAlmostEqual(comparison["diagonal_score_change_cell_minus_linear"], cell["diagonal_score"] - linear["diagonal_score"], places=12)
                self.assertAlmostEqual(comparison["linear_diagonal_score"], linear["diagonal_score"], places=12)
                self.assertAlmostEqual(comparison["cell_average_diagonal_score"], cell["diagonal_score"], places=12)
                expected_change = max(abs(linear["overlap_matrix"][i][j]["overlap"] - cell["overlap_matrix"][i][j]["overlap"]) for i in range(2) for j in range(2))
                self.assertAlmostEqual(comparison["max_overlap_entry_absolute_change"], expected_change, places=12)
                self.assertEqual(comparison["same_dominant_assignment"], linear["dominant_assignment"] == cell["dominant_assignment"])
                diagonal_count += sum(grid["dominant_assignment"] == "diagonal" for grid in (linear, cell))
                if comparison["m"] == 4800 and comparison["same_dominant_assignment"]:
                    finest_same += 1
        summary = data["summary"]
        self.assertEqual(summary["method_grid_count"], 18)
        self.assertEqual(summary["diagonal_dominant_count"], diagonal_count)
        self.assertEqual(summary["finest_same_assignment_count"], finest_same)
        expected_max = max(abs(row["diagonal_score_change_cell_minus_linear"]) for case in data["cases"] for row in case["method_comparisons"])
        self.assertAlmostEqual(summary["max_absolute_diagonal_score_change"], expected_max, places=12)

    def test_no_representation_invariant_or_state_tracking_claim(self):
        data = load("embedding_robustness_analysis.json")
        source = load("repeated_category_analysis.json")
        self.assertEqual(data["original_category_counts"], source["category_counts"])
        self.assertFalse(data["representation_invariant_claim"])
        self.assertFalse(data["embedding_convergence_proof"])
        self.assertFalse(data["rank_exchange_proven"])
        self.assertFalse(data["second_pair_topological_claim"])
        self.assertFalse(data["new_taxonomy_claim"])
        self.assertFalse(data["categories_changed"])
        self.assertFalse(data["universal_mechanism_claim"])

    def test_figure_markdown_and_reviewed_word(self):
        with Image.open(ROOT / "embedding-robustness.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "EMBEDDING_ROBUSTNESS.md").read_text(encoding="utf-8")
        for phrase in ("单元平均", "线性", "共同表示", "不是", "态追踪", "不新增类别", "N=640"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-共同表示稳健性.docx"
        with zipfile.ZipFile(docx) as package:
            document = package.read("word/document.xml").decode("utf-8")
            footer = "".join(package.read(name).decode("utf-8") for name in package.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            media = [name for name in package.namelist() if name.startswith("word/media/") and not name.endswith("/")]
        self.assertIn("m:oMath", document)
        self.assertIn("TOC", document)
        self.assertIn("PAGE", footer)
        self.assertEqual(len(media), 1)
        grids = re.findall(r"<w:tblGrid>(.*?)</w:tblGrid>", document)
        self.assertTrue(grids)
        for grid in grids:
            self.assertLessEqual(sum(int(value) for value in re.findall(r'w:w="(\d+)"', grid)), 9906)
        qa = load("embedding-robustness-word-qa.json")
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])
        runner = (ROOT / "run_embedding_robustness_verification.py").read_text(encoding="utf-8")
        self.assertNotIn('("docx_build"', runner)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
