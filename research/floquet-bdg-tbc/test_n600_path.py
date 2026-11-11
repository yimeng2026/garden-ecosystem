"""Contracts for N=600 replication of the two refined path regions."""

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
GRIDS = {
    "max_change": [0.05, 0.050625, 0.05125, 0.051875, 0.0525],
    "minimum_region": [0.04, 0.04125, 0.0425, 0.04375, 0.045],
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class N600PathTests(unittest.TestCase):
    def test_registry_and_sources(self):
        protocol = load("n600_path_protocol.json")
        data = load("n600_path_analysis.json")
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "n600_path_protocol.json"))
        self.assertEqual(data["source_sha256"], sha(ROOT / "repeated_category_analysis.json"))
        self.assertEqual(data["n400_source_sha256"], sha(ROOT / "path_refinement_analysis.json"))
        self.assertEqual(data["coarse_source_sha256"], sha(ROOT / "fixed_n_path_analysis.json"))
        self.assertEqual(protocol["n"], 600)
        self.assertEqual(protocol["seed"], 6)
        self.assertEqual(protocol["regions"], GRIDS)
        self.assertEqual(len(data["regions"]), 2)
        self.assertEqual(data["new_parameter_points"], 9)
        self.assertEqual(data["new_seed_count"], 0)
        self.assertTrue(data["fixed_random_stream"])
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])
        self.assertIn('("n600_path_suite"', (ROOT / "run_verification.py").read_text(encoding="utf-8"))
        self.assertIn('"--check-only"', (ROOT / "run_n600_path_verification.py").read_text(encoding="utf-8"))

    def test_reference_cell_is_reproduced(self):
        data = load("n600_path_analysis.json")
        source = load("repeated_category_analysis.json")
        old = next(row for row in source["all_cells"] if (row["n"], row["strength"], row["seed"]) == (600, 0.05, 6))
        for pair_text, error in data["reference_errors"].items():
            stored = old["pairs"][int(pair_text)]
            self.assertEqual(error["stored_profile_sha256"], stored["profile_sha256"])
            self.assertLessEqual(error["max_profile_absolute_error"], 1e-10)
            self.assertLessEqual(error["edge_weight_absolute_error"], 1e-10)
            self.assertLessEqual(error["stored_distance_max_absolute_error"], 1e-10)
            self.assertLessEqual(error["separation_ratio_absolute_error"], 1e-10)
            self.assertTrue(error["joint_pass_matches"])
        self.assertLessEqual(data["max_reference_error"], 1e-10)
        reference = next(point for region in data["regions"] for point in region["points"] if point["strength"] == 0.05)
        self.assertEqual(reference["pairs"][0]["diagnostic_joint_pass"], old["pairs"][0]["diagnostic_joint_pass"])
        self.assertEqual(reference["pairs"][1]["diagnostic_joint_pass"], old["pairs"][1]["diagnostic_joint_pass"])

    def test_centers_and_adjacent_overlaps_are_consistent(self):
        data = load("n600_path_analysis.json")
        for region in data["regions"]:
            self.assertEqual([point["strength"] for point in region["points"]], GRIDS[region["label"]])
            self.assertEqual(len(region["links"]), 4)
            for point in region["points"]:
                for pair in point["pairs"]:
                    distances = pair["distances"]
                    self.assertAlmostEqual(pair["center"], sum(distances) / 2, places=14)
                    self.assertAlmostEqual(pair["within_distance_difference"], abs(distances[1] - distances[0]), places=14)
                    self.assertLessEqual(pair["within_distance_difference"], 1e-10)
                separation = abs(point["pairs"][1]["center"] - point["pairs"][0]["center"])
                self.assertAlmostEqual(point["center_separation"], separation, places=14)
                self.assertGreater(separation, 0)
            for link in region["links"]:
                matrix = link["overlap_matrix"]
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
                self.assertAlmostEqual(link["diagonal_score"], diagonal, places=12)
                self.assertAlmostEqual(link["swapped_score"], swapped, places=12)
                expected = "diagonal" if diagonal > swapped else "swapped" if swapped > diagonal else "tie_exact"
                self.assertEqual(link["dominant_assignment"], expected)

    def test_summaries_and_n400_comparison_are_exact(self):
        data = load("n600_path_analysis.json")
        n400 = load("path_refinement_analysis.json")
        all_links = []
        for region in data["regions"]:
            summary = region["summary"]
            assignments = [link["dominant_assignment"] for link in region["links"]]
            self.assertEqual(summary["diagonal_link_count"], assignments.count("diagonal"))
            self.assertEqual(summary["swapped_link_count"], assignments.count("swapped"))
            self.assertEqual(summary["tie_link_count"], assignments.count("tie_exact"))
            minimum = min(region["points"], key=lambda row: row["center_separation"])
            self.assertEqual(summary["min_center_separation"], minimum["center_separation"])
            self.assertEqual(summary["min_center_separation_strength"], minimum["strength"])
            changes = [abs(link["center_separation_after"] - link["center_separation_before"]) for link in region["links"]]
            self.assertAlmostEqual(summary["max_adjacent_center_separation_change"], max(changes), places=14)
            all_links.extend(region["links"])
        summary = data["summary"]
        assignments = [link["dominant_assignment"] for link in all_links]
        self.assertEqual(summary["diagonal_link_count"], assignments.count("diagonal"))
        self.assertEqual(summary["swapped_link_count"], assignments.count("swapped"))
        self.assertEqual(summary["tie_link_count"], assignments.count("tie_exact"))
        all_points = [point for region in data["regions"] for point in region["points"]]
        minimum = min(all_points, key=lambda row: row["center_separation"])
        self.assertEqual(summary["min_center_separation"], minimum["center_separation"])
        self.assertEqual(summary["min_center_separation_strength"], minimum["strength"])
        changes = [abs(link["center_separation_after"] - link["center_separation_before"]) for link in all_links]
        self.assertAlmostEqual(summary["max_adjacent_center_separation_change"], max(changes), places=14)
        comparison = data["size_comparison"]
        n400_links = [link for region in n400["regions"] for link in region["links"]]
        self.assertEqual(comparison["assignment_agreement_count"], sum(new["dominant_assignment"] == old["dominant_assignment"] for new, old in zip(all_links, n400_links)))
        self.assertEqual(comparison["min_center_separation_same_strength"], summary["min_center_separation_strength"] == n400["summary"]["min_center_separation_strength"])
        self.assertAlmostEqual(comparison["max_diagonal_score_absolute_difference"], max(abs(new["diagonal_score"] - old["diagonal_score"]) for new, old in zip(all_links, n400_links)), places=12)
        n400_points = [point for region in n400["regions"] for point in region["points"]]
        self.assertAlmostEqual(comparison["max_center_separation_absolute_difference"], max(abs(new["center_separation"] - old["center_separation"]) for new, old in zip(all_points, n400_points)), places=12)
        self.assertEqual(summary["pair0_joint_pass_strengths"], [point["strength"] for point in all_points if point["pairs"][0]["diagnostic_joint_pass"]])
        self.assertEqual(summary["pair1_joint_pass_strengths"], [point["strength"] for point in all_points if point["pairs"][1]["diagnostic_joint_pass"]])

    def test_size_replication_is_not_crossing_or_invariance_proof(self):
        data = load("n600_path_analysis.json")
        source = load("repeated_category_analysis.json")
        self.assertEqual(data["original_category_counts"], source["category_counts"])
        self.assertFalse(data["size_invariance_claim"])
        self.assertFalse(data["continuous_path_proof"])
        self.assertFalse(data["spectral_crossing_proven"])
        self.assertFalse(data["avoided_crossing_claim"])
        self.assertFalse(data["state_exchange_proven"])
        self.assertFalse(data["second_pair_topological_claim"])
        self.assertFalse(data["new_taxonomy_claim"])
        self.assertFalse(data["categories_changed"])
        self.assertFalse(data["universal_mechanism_claim"])

    def test_figure_markdown_and_reviewed_word(self):
        with Image.open(ROOT / "n600-path.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "N600_PATH.md").read_text(encoding="utf-8")
        for phrase in ("N=600", "N=400", "同 N", "不是", "避免交叉", "不新增类别", "N=640"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-N600路径复核.docx"
        with zipfile.ZipFile(docx) as package:
            document = package.read("word/document.xml").decode("utf-8")
            footer = "".join(package.read(name).decode("utf-8") for name in package.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            media = [name for name in package.namelist() if name.startswith("word/media/") and not name.endswith("/")]
        self.assertIn("m:oMath", document)
        self.assertIn("<m:sSub", document)
        self.assertIn("<m:f>", document)
        self.assertIn("TOC", document)
        self.assertIn("PAGE", footer)
        self.assertEqual(len(media), 1)
        grids = re.findall(r"<w:tblGrid>(.*?)</w:tblGrid>", document)
        self.assertTrue(grids)
        for grid in grids:
            self.assertLessEqual(sum(int(value) for value in re.findall(r'w:w="(\d+)"', grid)), 9906)
        qa = load("n600-path-word-qa.json")
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])
        runner = (ROOT / "run_n600_path_verification.py").read_text(encoding="utf-8")
        self.assertNotIn('("docx_build"', runner)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
