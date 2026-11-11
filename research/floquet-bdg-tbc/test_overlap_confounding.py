"""Contracts for separating rank, embedding, size and disorder-profile effects."""

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
DATA = ROOT / "overlap_confounding_analysis.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def evidence(test):
    test.assertTrue(DATA.is_file(), "Overlap-confounding analysis has not been generated")
    return load(DATA.name)


class OverlapConfoundingTests(unittest.TestCase):
    def test_protocol_sources_and_full_census_scope(self):
        data = evidence(self)
        protocol = load("overlap_confounding_protocol.json")
        self.assertEqual(data["schema"], "floquet-bdg-overlap-confounding-analysis-v1")
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "overlap_confounding_protocol.json"))
        self.assertEqual(data["source_sha256"], sha(ROOT / "embedding_census_analysis.json"))
        self.assertTrue(protocol["registered_before_analysis"])
        self.assertEqual(protocol["seeds"], list(range(8)))
        self.assertEqual(protocol["strengths"], [0.05, 0.1])
        self.assertEqual(protocol["common_grids"], [1200, 2400, 4800])
        self.assertEqual(len(data["cases"]), 16)
        self.assertEqual(len(data["cells"]), 32)
        self.assertEqual(data["new_physics_cells"], 0)
        self.assertEqual(data["new_seed_count"], 0)
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])
        self.assertIn('("overlap_confounding_suite"', (ROOT / "run_verification.py").read_text(encoding="utf-8"))

    def test_cross_size_evidence_and_frozen_profiles_are_reproduced(self):
        data = evidence(self)
        old = load("embedding_census_analysis.json")
        self.assertLessEqual(data["max_cross_size_reproduction_error"], 1e-12)
        self.assertLessEqual(data["max_profile_absolute_error"], 1e-10)
        for case in data["cases"]:
            previous = next(row for row in old["cases"] if row["label"] == case["label"])
            for method in ("linear_point", "cell_average"):
                for grid, old_grid in zip(case["methods"][method]["grids"], previous["methods"][method]["grids"]):
                    self.assertEqual(grid["dominant_assignment"], old_grid["dominant_assignment"])
                    self.assertAlmostEqual(grid["diagonal_score"], old_grid["diagonal_score"], places=12)
                    self.assertAlmostEqual(grid["swapped_score"], old_grid["swapped_score"], places=12)
                    for i in range(2):
                        for j in range(2):
                            self.assertAlmostEqual(grid["overlap_matrix"][i][j]["overlap"], old_grid["overlap_matrix"][i][j]["overlap"], places=12)

    def test_representation_fidelity_is_bidirectional_and_not_a_correction(self):
        data = evidence(self)
        rows = [row for case in data["cases"] for grid in case["diagnostics"] for row in grid["representation_fidelity"]]
        self.assertEqual(len(rows), 192)
        self.assertLessEqual(data["summary"]["max_representation_direction_absolute_error"], 1e-12)
        for row in rows:
            self.assertIn(row["n"], (400, 600))
            self.assertIn(row["pair_index"], (0, 1))
            self.assertGreaterEqual(row["forward"], 0)
            self.assertLessEqual(row["forward"], 1 + 1e-12)
            self.assertAlmostEqual(row["forward"], row["reverse"], places=12)
            self.assertAlmostEqual(row["forward"], sum(value * value for value in row["singular_values"]) / 2, places=12)
            expected_angles = [math.degrees(math.acos(min(1.0, max(0.0, value)))) for value in row["singular_values"]]
            self.assertTrue(np.allclose(row["principal_angles_deg"], expected_angles, rtol=0, atol=1e-8))
        self.assertFalse(data["normalization_correction_applied"])
        self.assertFalse(data["representation_invariant_claim"])

    def test_same_n_rank_controls_identify_embedding_leakage(self):
        data = evidence(self)
        rows = [row for case in data["cases"] for grid in case["diagnostics"] for row in grid["same_n_rank_controls"]]
        native = [row for case in data["cases"] for row in case["native_same_n_rank_controls"]]
        self.assertEqual(len(rows), 192)
        self.assertEqual(len(native), 32)
        summary = data["summary"]
        self.assertLessEqual(summary["max_same_n_self_error"], 1e-12)
        self.assertAlmostEqual(summary["max_same_n_off_diagonal"], 3.2111372980829987e-06, places=17)
        self.assertLessEqual(summary["max_native_same_n_off_diagonal"], 1e-12)
        self.assertLessEqual(summary["max_cell_average_same_n_off_diagonal"], 1e-12)
        self.assertGreater(summary["max_linear_point_same_n_off_diagonal"], 1e-12)
        self.assertFalse(data["same_n_embedding_rank_gate_passed"])
        self.assertTrue(data["native_control_added_after_observed_leakage"])
        for row in rows + native:
            self.assertAlmostEqual(row["self00"], 1, places=12)
            self.assertAlmostEqual(row["self11"], 1, places=12)
            self.assertAlmostEqual(row["off01"], row["off10"], places=12)
        self.assertFalse(data["rank_exchange_proven"])
        self.assertFalse(data["same_physics_state_tracking_claim"])

    def test_beta_mismatch_is_recomputed_and_size_is_not_isolated(self):
        data = evidence(self)
        rows = [row for case in data["cases"] for grid in case["diagnostics"] for row in grid["beta_profile_methods"].values()]
        self.assertEqual(len(rows), 96)
        self.assertFalse(data["same_disorder_realization"])
        self.assertFalse(data["common_disorder_profile_control_computed"])
        self.assertFalse(data["size_effect_separated"])
        case = next(row for row in data["cases"] if (row["seed"], row["strength"]) == (6, 0.05))
        grid = next(row for row in case["diagnostics"] if row["m"] == 1200)
        beta = {n: np.random.default_rng(20261111 + 6).random(n) for n in (400, 600)}
        for method in ("linear_point", "cell_average"):
            refined = {}
            for n in (400, 600):
                if method == "linear_point":
                    source_x = (np.arange(n) + 0.5) / n
                    target_x = (np.arange(1200) + 0.5) / 1200
                    refined[n] = np.interp(target_x, source_x, beta[n])
                else:
                    refined[n] = np.repeat(beta[n], 1200 // n)
            difference = refined[400] - refined[600]
            expected_rms = float(np.sqrt(np.mean(difference ** 2)))
            expected_max = float(np.max(np.abs(difference)))
            actual = grid["beta_profile_methods"][method]
            self.assertAlmostEqual(actual["rms_absolute_difference"], expected_rms, places=14)
            self.assertAlmostEqual(actual["max_absolute_difference"], expected_max, places=14)
            self.assertAlmostEqual(actual["mean_absolute_difference"], float(np.mean(np.abs(difference))), places=14)
            self.assertAlmostEqual(actual["pearson_correlation"], float(np.corrcoef(refined[400], refined[600])[0, 1]), places=14)
        self.assertFalse(data["statistical_significance_claim"])

    def test_figure_markdown_and_native_word_review(self):
        data = evidence(self)
        self.assertFalse(data["new_taxonomy_claim"])
        self.assertFalse(data["second_pair_topological_claim"])
        self.assertFalse(data["thermodynamic_limit_proof"])
        with Image.open(ROOT / "overlap-confounding-audit.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "OVERLAP_CONFOUNDING_AUDIT.md").read_text(encoding="utf-8")
        for phrase in ("共同表示", "无序剖面", "不能归因于尺寸", "不做归一化", "不补算体 winding", "N=640"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-重叠差异混杂审计.docx"
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
        qa = load("overlap-confounding-word-qa.json")
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertTrue(qa["visualReview"]["contactSheetRead"])
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
