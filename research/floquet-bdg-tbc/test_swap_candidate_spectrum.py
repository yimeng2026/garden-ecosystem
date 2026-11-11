"""Contracts for the targeted swap-candidate spectral-structure audit."""

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


class SwapCandidateSpectrumTests(unittest.TestCase):
    def test_target_registry_and_sources(self):
        protocol = load("swap_candidate_spectrum_protocol.json")
        data = load("swap_candidate_spectrum_analysis.json")
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "swap_candidate_spectrum_protocol.json"))
        self.assertEqual(data["source_sha256"], sha(ROOT / "repeated_category_analysis.json"))
        self.assertEqual(data["census_source_sha256"], sha(ROOT / "embedding_census_analysis.json"))
        self.assertEqual(protocol["seed"], 6)
        self.assertEqual(protocol["strength"], 0.05)
        self.assertEqual(protocol["n_values"], [400, 600])
        self.assertEqual(protocol["spectrum_rank_count"], 6)
        self.assertEqual(data["new_physics_cells"], 0)
        self.assertEqual(len(data["cells"]), 2)
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])
        self.assertIn('("swap_candidate_spectrum_suite"', (ROOT / "run_verification.py").read_text(encoding="utf-8"))

    def test_profiles_and_stored_distances_are_reproduced(self):
        data = load("swap_candidate_spectrum_analysis.json")
        source = load("repeated_category_analysis.json")
        for cell in data["cells"]:
            old = next(row for row in source["all_cells"] if (row["n"], row["strength"], row["seed"]) == (cell["n"], 0.05, 6))
            distances = [row["distance"] for row in cell["spectrum"]]
            self.assertEqual(len(distances), 6)
            self.assertTrue(all(value >= 0 for value in distances))
            self.assertEqual(distances, sorted(distances))
            for pair in cell["pairs"]:
                stored = old["pairs"][pair["pair_index"]]
                self.assertEqual(pair["stored_profile_sha256"], stored["profile_sha256"])
                self.assertLessEqual(pair["max_profile_absolute_error"], 1e-10)
                self.assertLessEqual(pair["edge_weight_absolute_error"], 1e-10)
                self.assertLessEqual(pair["stored_distance_max_absolute_error"], 1e-10)
                self.assertEqual(pair["max_separation_ratio"], stored["max_separation_ratio"])
                self.assertEqual(pair["diagnostic_joint_pass"], stored["diagnostic_joint_pass"])
            self.assertLessEqual(cell["max_stored_distance_absolute_error"], 1e-10)
        self.assertLessEqual(data["max_profile_absolute_error"], 1e-10)

    def test_pair_centers_and_separations_are_exact(self):
        data = load("swap_candidate_spectrum_analysis.json")
        for cell in data["cells"]:
            distances = [row["distance"] for row in cell["spectrum"]]
            for pair_index in (0, 1):
                pair = cell["pairs"][pair_index]
                center = (distances[2 * pair_index] + distances[2 * pair_index + 1]) / 2
                splitting = abs(distances[2 * pair_index + 1] - distances[2 * pair_index])
                self.assertAlmostEqual(pair["center"], center, places=14)
                self.assertAlmostEqual(pair["within_distance_difference"], splitting, places=14)
                self.assertLessEqual(splitting, 1e-10)
            separation = abs(cell["pairs"][1]["center"] - cell["pairs"][0]["center"])
            self.assertAlmostEqual(cell["center_separation"], separation, places=14)
            self.assertGreater(separation, 0)
            expected_ratio = separation / max(cell["pairs"][0]["center"], cell["pairs"][1]["center"])
            self.assertAlmostEqual(cell["center_separation_ratio"], expected_ratio, places=12)
        comparison = data["size_comparison"]
        first, second = data["cells"]
        self.assertAlmostEqual(comparison["center_separation_delta"], second["center_separation"] - first["center_separation"], places=14)
        self.assertAlmostEqual(comparison["pair0_center_delta"], second["pairs"][0]["center"] - first["pairs"][0]["center"], places=14)
        self.assertAlmostEqual(comparison["pair1_center_delta"], second["pairs"][1]["center"] - first["pairs"][1]["center"], places=14)
        self.assertFalse(data["cross_pair_exact_degenerate"])
        self.assertFalse(data["near_degeneracy_threshold_added"])

    def test_overlap_advantage_is_cross_term_not_state_exchange(self):
        data = load("swap_candidate_spectrum_analysis.json")
        census = load("embedding_census_analysis.json")
        old = next(row for row in census["cases"] if row["label"] == "seed_6_r_0p05")
        for method in ("linear_point", "cell_average"):
            current = data["candidate_overlap"][method]
            stored = old["methods"][method]["grids"][-1]
            self.assertAlmostEqual(current["diagonal_score"], stored["diagonal_score"], places=12)
            self.assertAlmostEqual(current["swapped_score"], stored["swapped_score"], places=12)
            self.assertGreater(current["swapped_score"], current["diagonal_score"])
            self.assertTrue(current["cross_term_exceeds_each_diagonal_entry"])
            for i in range(2):
                for j in range(2):
                    self.assertAlmostEqual(current["overlap_matrix"][i][j]["overlap"], stored["overlap_matrix"][i][j]["overlap"], places=12)
        for cell in data["cells"]:
            self.assertFalse(cell["pairs"][1]["diagnostic_joint_pass"])
        self.assertFalse(data["spectral_crossing_proven"])
        self.assertFalse(data["avoided_crossing_claim"])
        self.assertFalse(data["state_exchange_proven"])
        self.assertFalse(data["second_pair_topological_claim"])

    def test_static_rank_is_not_parameter_tracking(self):
        data = load("swap_candidate_spectrum_analysis.json")
        source = load("repeated_category_analysis.json")
        self.assertEqual(data["original_category_counts"], source["category_counts"])
        self.assertTrue(data["sorted_order_is_constructed_not_tracking"])
        self.assertFalse(data["rank_swap_observed"])
        self.assertFalse(data["new_taxonomy_claim"])
        self.assertFalse(data["categories_changed"])
        self.assertFalse(data["universal_mechanism_claim"])

    def test_figure_markdown_and_reviewed_word(self):
        self.assertIn('axes[1, 1].margins(y=0.25)', (ROOT / "analyze_swap_candidate_spectrum.py").read_text(encoding="utf-8"))
        with Image.open(ROOT / "swap-candidate-spectrum.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "SWAP_CANDIDATE_SPECTRUM.md").read_text(encoding="utf-8")
        for phrase in ("TBC", "中心间隔", "交换候选", "不是", "谱交叉", "不新增类别", "N=640"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-交换候选谱结构.docx"
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
        qa = load("swap-candidate-spectrum-word-qa.json")
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])
        runner = (ROOT / "run_swap_candidate_spectrum_verification.py").read_text(encoding="utf-8")
        self.assertNotIn('("docx_build"', runner)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
