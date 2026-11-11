"""Contracts for targeted refinement of the two observed fixed-N path regions."""

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


class PathRefinementTests(unittest.TestCase):
    def test_refinement_registry_and_sources(self):
        protocol = load("path_refinement_protocol.json")
        data = load("path_refinement_analysis.json")
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "path_refinement_protocol.json"))
        self.assertEqual(data["source_sha256"], sha(ROOT / "fixed_n_path_analysis.json"))
        self.assertEqual(data["candidate_source_sha256"], sha(ROOT / "swap_candidate_spectrum_analysis.json"))
        self.assertEqual(protocol["n"], 400)
        self.assertEqual(protocol["seed"], 6)
        self.assertEqual(protocol["regions"], GRIDS)
        self.assertEqual(len(data["regions"]), 2)
        self.assertEqual(data["new_parameter_points"], 5)
        self.assertEqual(data["new_seed_count"], 0)
        self.assertTrue(data["fixed_random_stream"])
        self.assertTrue(data["adaptive_refinement_only"])
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])
        self.assertIn('("path_refinement_suite"', (ROOT / "run_verification.py").read_text(encoding="utf-8"))

    def test_coarse_points_are_reproduced(self):
        data = load("path_refinement_analysis.json")
        coarse = load("fixed_n_path_analysis.json")
        for strength_text, errors in data["reference_errors"].items():
            strength = float(strength_text)
            old_point = next(row for row in coarse["path"] if row["strength"] == strength)
            new_point = next(point for region in data["regions"] for point in region["points"] if point["strength"] == strength)
            for pair_text, error in errors.items():
                old = old_point["pairs"][int(pair_text)]
                new = new_point["pairs"][int(pair_text)]
                self.assertAlmostEqual(error["center_absolute_error"], abs(new["center"] - old["center"]), places=15)
                self.assertAlmostEqual(error["distance_max_absolute_error"], max(abs(a - b) for a, b in zip(new["distances"], old["distances"])), places=15)
                self.assertAlmostEqual(error["separation_ratio_absolute_error"], abs(new["max_separation_ratio"] - old["max_separation_ratio"]), places=15)
                self.assertAlmostEqual(error["edge_weight_absolute_error"], abs(new["edge_weight"] - old["edge_weight"]), places=15)
                self.assertLessEqual(error["distance_max_absolute_error"], 1e-10)
                self.assertLessEqual(error["separation_ratio_absolute_error"], 1e-10)
                self.assertLessEqual(error["edge_weight_absolute_error"], 1e-10)
                self.assertEqual(new["diagnostic_joint_pass"], old["diagnostic_joint_pass"])
                self.assertTrue(error["joint_pass_matches"])
                self.assertAlmostEqual(error["coarse_center"], old["center"], places=15)
        self.assertLessEqual(data["max_reference_error"], 1e-10)
        reference = next(row for row in coarse["path"] if row["strength"] == 0.05)
        self.assertEqual(reference["pairs"][0]["diagnostic_joint_pass"], True)
        self.assertEqual(reference["pairs"][1]["diagnostic_joint_pass"], False)

    def test_refined_centers_and_links_are_consistent(self):
        data = load("path_refinement_analysis.json")
        for region in data["regions"]:
            label = region["label"]
            self.assertEqual([point["strength"] for point in region["points"]], GRIDS[label])
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

    def test_region_and_global_summaries_are_exact(self):
        data = load("path_refinement_analysis.json")
        all_links = []
        for region in data["regions"]:
            assignments = [link["dominant_assignment"] for link in region["links"]]
            summary = region["summary"]
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

    def test_refinement_is_not_crossing_or_state_tracking_proof(self):
        data = load("path_refinement_analysis.json")
        source = load("repeated_category_analysis.json")
        self.assertEqual(data["original_category_counts"], source["category_counts"])
        self.assertFalse(data["continuous_path_proof"])
        self.assertFalse(data["spectral_crossing_proven"])
        self.assertFalse(data["avoided_crossing_claim"])
        self.assertFalse(data["state_exchange_proven"])
        self.assertFalse(data["second_pair_topological_claim"])
        self.assertFalse(data["new_taxonomy_claim"])
        self.assertFalse(data["categories_changed"])
        self.assertFalse(data["universal_mechanism_claim"])

    def test_figure_markdown_and_reviewed_word(self):
        with Image.open(ROOT / "path-refinement.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "PATH_REFINEMENT.md").read_text(encoding="utf-8")
        for phrase in ("细化", "邻域", "离散", "不是", "避免交叉", "不新增类别", "N=640"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-参数路径细化.docx"
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
        qa = load("path-refinement-word-qa.json")
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])
        runner = (ROOT / "run_path_refinement_verification.py").read_text(encoding="utf-8")
        self.assertNotIn('("docx_build"', runner)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
