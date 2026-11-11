"""Contracts for fixed-N, fixed-random-stream discrete path diagnostics."""

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


class FixedNPathTests(unittest.TestCase):
    def test_protocol_registry_and_sources(self):
        protocol = load("fixed_n_path_protocol.json")
        data = load("fixed_n_path_analysis.json")
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "fixed_n_path_protocol.json"))
        self.assertEqual(data["source_sha256"], sha(ROOT / "repeated_category_analysis.json"))
        self.assertEqual(data["candidate_source_sha256"], sha(ROOT / "swap_candidate_spectrum_analysis.json"))
        self.assertEqual(protocol["n"], 400)
        self.assertEqual(protocol["seed"], 6)
        self.assertEqual(protocol["strengths"], [0.04, 0.0425, 0.045, 0.0475, 0.05, 0.0525, 0.055, 0.0575, 0.06])
        self.assertEqual(len(data["path"]), 9)
        self.assertEqual(len(data["links"]), 8)
        self.assertEqual(data["new_parameter_points"], 9)
        self.assertEqual(data["new_seed_count"], 0)
        self.assertTrue(data["fixed_random_stream"])
        self.assertTrue(data["discrete_path"])
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])
        self.assertIn('("fixed_n_path_suite"', (ROOT / "run_verification.py").read_text(encoding="utf-8"))

    def test_reference_cell_profiles_and_distances_are_reproduced(self):
        data = load("fixed_n_path_analysis.json")
        source = load("repeated_category_analysis.json")
        old = next(row for row in source["all_cells"] if (row["n"], row["strength"], row["seed"]) == (400, 0.05, 6))
        reference = next(row for row in data["path"] if row["strength"] == 0.05)
        for pair in reference["pairs"]:
            stored = old["pairs"][pair["pair_index"]]
            error = data["reference_errors"][str(pair["pair_index"])]
            self.assertEqual(error["stored_profile_sha256"], stored["profile_sha256"])
            self.assertLessEqual(error["max_profile_absolute_error"], 1e-10)
            self.assertLessEqual(error["edge_weight_absolute_error"], 1e-10)
            self.assertLessEqual(error["stored_distance_max_absolute_error"], 1e-10)
            self.assertLessEqual(error["separation_ratio_absolute_error"], 1e-10)
            self.assertEqual(pair["diagnostic_joint_pass"], stored["diagnostic_joint_pass"])
        self.assertLessEqual(data["max_reference_profile_absolute_error"], 1e-10)
        self.assertLessEqual(data["max_reference_distance_absolute_error"], 1e-10)

    def test_path_centers_and_adjacent_overlaps_are_consistent(self):
        data = load("fixed_n_path_analysis.json")
        for point in data["path"]:
            for pair in point["pairs"]:
                distances = pair["distances"]
                self.assertAlmostEqual(pair["center"], sum(distances) / 2, places=14)
                self.assertAlmostEqual(pair["within_distance_difference"], abs(distances[1] - distances[0]), places=14)
                self.assertLessEqual(pair["within_distance_difference"], 1e-10)
            separation = abs(point["pairs"][1]["center"] - point["pairs"][0]["center"])
            self.assertAlmostEqual(point["center_separation"], separation, places=14)
            self.assertGreater(separation, 0)
        for link in data["links"]:
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

    def test_summary_counts_and_extrema_are_exact(self):
        data = load("fixed_n_path_analysis.json")
        summary = data["summary"]
        assignments = [link["dominant_assignment"] for link in data["links"]]
        self.assertEqual(summary["diagonal_link_count"], assignments.count("diagonal"))
        self.assertEqual(summary["swapped_link_count"], assignments.count("swapped"))
        self.assertEqual(summary["tie_link_count"], assignments.count("tie_exact"))
        self.assertEqual(len(summary["assignment_sequence"]), 8)
        minimum = min(data["path"], key=lambda row: row["center_separation"])
        self.assertEqual(summary["min_center_separation"], minimum["center_separation"])
        self.assertEqual(summary["min_center_separation_strength"], minimum["strength"])
        changes = [abs(link["center_separation_after"] - link["center_separation_before"]) for link in data["links"]]
        self.assertAlmostEqual(summary["max_adjacent_center_separation_change"], max(changes), places=14)
        self.assertEqual(summary["pair0_joint_pass_strengths"], [row["strength"] for row in data["path"] if row["pairs"][0]["diagnostic_joint_pass"]])
        self.assertEqual(summary["pair1_joint_pass_strengths"], [row["strength"] for row in data["path"] if row["pairs"][1]["diagnostic_joint_pass"]])

    def test_discrete_path_is_not_crossing_or_state_tracking_proof(self):
        data = load("fixed_n_path_analysis.json")
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
        with Image.open(ROOT / "fixed-n-path.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "FIXED_N_PATH.md").read_text(encoding="utf-8")
        for phrase in ("固定随机流", "相邻", "离散路径", "不是", "避免交叉", "不新增类别", "N=640"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-固定尺寸参数路径.docx"
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
        qa = load("fixed-n-path-word-qa.json")
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])
        runner = (ROOT / "run_fixed_n_path_verification.py").read_text(encoding="utf-8")
        self.assertNotIn('("docx_build"', runner)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
