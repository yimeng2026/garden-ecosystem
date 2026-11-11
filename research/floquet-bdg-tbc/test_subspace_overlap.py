"""Contracts for common-grid cross-size principal-subspace diagnostics."""

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


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class SubspaceOverlapTests(unittest.TestCase):
    def test_frozen_registry_and_sources(self):
        protocol = load("subspace_overlap_protocol.json")
        data = load("subspace_overlap_analysis.json")
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "subspace_overlap_protocol.json"))
        self.assertEqual(data["source_sha256"], sha(ROOT / "repeated_category_analysis.json"))
        self.assertEqual(data["pair_response_source_sha256"], sha(ROOT / "pair_response_analysis.json"))
        self.assertEqual(protocol["common_grids"], [1200, 2400, 4800])
        self.assertEqual(protocol["selected_cases"], [
            {"label": "near_miss_low", "seed": 5, "strength": 0.05},
            {"label": "near_miss_high", "seed": 5, "strength": 0.1},
            {"label": "reference_weakening", "seed": 2, "strength": 0.1},
        ])
        self.assertEqual(protocol["new_physics_cells"], 0)
        self.assertEqual(len(data["cases"]), 3)
        self.assertEqual(len(data["cells"]), 6)
        self.assertTrue(data["verification_eigenvectors_recomputed"])
        self.assertEqual(data["new_physics_cells"], 0)
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])
        self.assertFalse(data["same_physics_state_tracking_claim"])
        self.assertIn('("subspace_overlap_suite"', (ROOT / "run_verification.py").read_text(encoding="utf-8"))

    def test_recomputed_eigenvectors_match_frozen_profiles(self):
        data = load("subspace_overlap_analysis.json")
        source = load("repeated_category_analysis.json")
        self.assertEqual(data["eigensolver"], "scipy.linalg.eig")
        self.assertEqual(data["projector"], "direct_gram_inverse")
        for cell in data["cells"]:
            old = next(row for row in source["all_cells"] if (row["n"], row["strength"], row["seed"]) == (cell["n"], cell["strength"], cell["seed"]))
            self.assertEqual(len(cell["pairs"]), 2)
            for pair in cell["pairs"]:
                stored = old["pairs"][pair["pair_index"]]
                self.assertEqual(pair["stored_profile_sha256"], stored["profile_sha256"])
                self.assertLessEqual(pair["max_profile_absolute_error"], 1e-10)
                self.assertLessEqual(pair["edge_weight_absolute_error"], 1e-10)
        self.assertLessEqual(data["max_profile_absolute_error"], 1e-10)
        self.assertEqual(data["new_physics_cells"], 0)

    def test_principal_subspace_metrics_are_internally_consistent(self):
        data = load("subspace_overlap_analysis.json")
        for case in data["cases"]:
            self.assertEqual(len(case["grids"]), 3)
            for grid in case["grids"]:
                matrix = grid["overlap_matrix"]
                self.assertEqual(len(matrix), 2)
                for i in range(2):
                    for j in range(2):
                        entry = matrix[i][j]
                        singular = entry["singular_values"]
                        self.assertEqual(len(singular), 2)
                        self.assertGreaterEqual(singular[0], singular[1])
                        self.assertTrue(all(0 <= value <= 1 + 1e-12 for value in singular))
                        self.assertAlmostEqual(entry["overlap"], sum(value * value for value in singular) / 2, places=12)
                        angles = [math.degrees(math.acos(min(1.0, max(0.0, value)))) for value in singular]
                        self.assertAlmostEqual(entry["principal_angles_deg"][0], angles[0], places=8)
                        self.assertAlmostEqual(entry["principal_angles_deg"][1], angles[1], places=8)
                        self.assertGreaterEqual(entry["overlap"], 0)
                        self.assertLessEqual(entry["overlap"], 1 + 1e-12)
                # Rows always belong to N=400 and columns to N=600. Swapping i,j
                # does not also swap sizes, so this cross-size matrix need not be symmetric.
                diagonal = (matrix[0][0]["overlap"] + matrix[1][1]["overlap"]) / 2
                swapped = (matrix[0][1]["overlap"] + matrix[1][0]["overlap"]) / 2
                self.assertAlmostEqual(grid["diagonal_score"], diagonal, places=12)
                self.assertAlmostEqual(grid["swapped_score"], swapped, places=12)
                expected = "diagonal" if diagonal > swapped else "swapped" if swapped > diagonal else "tie_exact"
                self.assertEqual(grid["dominant_assignment"], expected)

    def test_overlap_does_not_promote_rank_matching_to_state_tracking(self):
        data = load("subspace_overlap_analysis.json")
        self.assertEqual(data["pair_identity"], "common_grid_principal_subspace_diagnostic")
        self.assertEqual(sum(data["finest_assignment_counts"].values()), 3)
        for case in data["cases"]:
            finest = case["grids"][-1]
            self.assertEqual(finest["m"], 4800)
            self.assertIn(finest["dominant_assignment"], ("diagonal", "swapped", "tie_exact"))
        self.assertFalse(data["rank_exchange_proven"])
        self.assertFalse(data["second_pair_topological_claim"])
        self.assertFalse(data["new_taxonomy_claim"])
        self.assertFalse(data["categories_changed"])
        self.assertFalse(data["universal_mechanism_claim"])
        self.assertFalse(data["grid_convergence_proof"])

    def test_previous_categories_and_pair_response_evidence_are_unchanged(self):
        data = load("subspace_overlap_analysis.json")
        source = load("repeated_category_analysis.json")
        pair_response = load("pair_response_analysis.json")
        self.assertEqual(data["original_category_counts"], source["category_counts"])
        self.assertEqual(pair_response["edge_relation_counts"], {"same_nonzero": 6, "opposite_nonzero": 10})
        self.assertEqual(pair_response["L50_relation_counts"], {"same_nonzero": 10, "opposite_nonzero": 6})
        for case in data["cases"]:
            old = next(row for row in source["cases"] if (row["seed"], row["strength"]) == (case["seed"], case["strength"]))
            self.assertEqual(case["original_category"], old["category"])

    def test_figure_markdown_and_reviewed_word(self):
        self.assertIn('set_yscale("log")', (ROOT / "analyze_subspace_overlap.py").read_text(encoding="utf-8"))
        self.assertNotIn('f"{value:.3f}"', (ROOT / "analyze_subspace_overlap.py").read_text(encoding="utf-8"))
        with Image.open(ROOT / "subspace-overlap.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "SUBSPACE_OVERLAP.md").read_text(encoding="utf-8")
        for phrase in ("共同网格", "主子空间", "不是", "态追踪", "不新增类别", "不补算体 winding", "N=640"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-跨尺寸子空间重叠.docx"
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
        qa = load("subspace-overlap-word-qa.json")
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])
        runner = (ROOT / "run_subspace_overlap_verification.py").read_text(encoding="utf-8")
        self.assertNotIn('("docx_build"', runner)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
