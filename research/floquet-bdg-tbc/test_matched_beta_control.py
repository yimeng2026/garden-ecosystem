"""Contracts for the nested common-beta size-isolation control."""

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
DATA = ROOT / "matched_beta_control_analysis.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def evidence(test):
    test.assertTrue(DATA.is_file(), "Matched-beta control analysis is missing")
    return load(DATA.name)


class MatchedBetaControlTests(unittest.TestCase):
    def test_protocol_and_exact_nested_coarsening(self):
        data = evidence(self)
        protocol = load("matched_beta_control_protocol.json")
        self.assertEqual(data["schema"], "floquet-bdg-matched-beta-control-analysis-v1")
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "matched_beta_control_protocol.json"))
        self.assertTrue(protocol["registered_before_analysis"])
        self.assertEqual(protocol["master_grid"], 4800)
        self.assertEqual(protocol["n_values"], [400, 600])
        self.assertEqual(protocol["seed"], 6)
        self.assertEqual(protocol["strength"], 0.05)
        self.assertEqual(data["new_control_cells"], 2)
        self.assertEqual(data["new_seed_count"], 0)
        master = np.random.default_rng(20261111 + 6).random(4800)
        self.assertEqual(data["master_profile_sha256"], hashlib.sha256(master.tobytes()).hexdigest())
        for cell in data["cells"]:
            n = cell["n"]
            expected = master.reshape(n, 4800 // n).mean(axis=1)
            self.assertAlmostEqual(cell["coarsening_max_absolute_error"], 0.0, places=15)
            self.assertTrue(np.allclose(np.asarray(cell["beta"]), expected, rtol=0, atol=0))
        self.assertIn('("matched_beta_control_suite"', (ROOT / "run_verification.py").read_text(encoding="utf-8"))

    def test_spectrum_and_pair_metrics_are_consistent(self):
        data = evidence(self)
        for cell in data["cells"]:
            self.assertEqual(len(cell["pairs"]), 2)
            self.assertEqual(len(cell["spectrum_first_six"]), 6)
            self.assertGreater(cell["center_separation"], 0)
            for pair in cell["pairs"]:
                self.assertEqual(len(pair["distances"]), 2)
                self.assertAlmostEqual(pair["center"], float(np.mean(pair["distances"])), places=15)
                self.assertAlmostEqual(pair["within_distance_difference"], abs(pair["distances"][1] - pair["distances"][0]), places=15)
            expected = abs(cell["pairs"][1]["center"] - cell["pairs"][0]["center"])
            self.assertAlmostEqual(cell["center_separation"], expected, places=15)
        self.assertFalse(data["spectral_crossing_proven"])
        self.assertFalse(data["avoided_crossing_claim"])

    def test_cross_size_overlap_and_direction_symmetry(self):
        data = evidence(self)
        for method in ("linear_point", "cell_average"):
            grids = data["methods"][method]["grids"]
            self.assertEqual([grid["m"] for grid in grids], [1200, 2400, 4800])
            for grid in grids:
                matrix = grid["overlap_matrix"]
                diagonal = (matrix[0][0]["overlap"] + matrix[1][1]["overlap"]) / 2
                swapped = (matrix[0][1]["overlap"] + matrix[1][0]["overlap"]) / 2
                self.assertAlmostEqual(grid["diagonal_score"], diagonal, places=12)
                self.assertAlmostEqual(grid["swapped_score"], swapped, places=12)
                expected = "diagonal" if diagonal > swapped else "swapped" if swapped > diagonal else "tie_exact"
                self.assertEqual(grid["dominant_assignment"], expected)
                for row in matrix:
                    for entry in row:
                        self.assertAlmostEqual(entry["overlap"], sum(value * value for value in entry["singular_values"]) / 2, places=12)
                        angles = [math.degrees(math.acos(min(1.0, max(0.0, value)))) for value in entry["singular_values"]]
                        self.assertTrue(np.allclose(entry["principal_angles_deg"], angles, rtol=0, atol=1e-8))
        self.assertLessEqual(data["summary"]["max_direction_absolute_error"], 1e-12)

    def test_representation_and_native_rank_controls(self):
        data = evidence(self)
        fidelity = data["representation_fidelity"]
        self.assertEqual(len(fidelity), 12)
        for row in fidelity:
            self.assertAlmostEqual(row["forward"], row["reverse"], places=12)
            self.assertAlmostEqual(row["forward"], sum(value * value for value in row["singular_values"]) / 2, places=12)
        self.assertEqual(len(data["native_rank_controls"]), 2)
        self.assertLessEqual(data["summary"]["max_native_off_diagonal"], 1e-12)
        self.assertLessEqual(data["summary"]["max_cell_average_off_diagonal"], 1e-12)
        self.assertFalse(data["normalization_correction_applied"])
        self.assertFalse(data["representation_invariant_claim"])

    def test_common_beta_control_and_old_candidate_boundaries(self):
        data = evidence(self)
        self.assertTrue(data["common_disorder_profile_control_computed"])
        self.assertEqual(data["size_effect_separated"], "matched_nested_profile_descriptive_only")
        self.assertTrue(data["old_candidate_is_different_realization"])
        self.assertTrue(data["difference_from_original_is_not_size_effect"])
        self.assertEqual(data["candidate_source_sha256"], sha(ROOT / "swap_candidate_spectrum_analysis.json"))
        self.assertFalse(data["universal_size_law_claim"])
        self.assertFalse(data["continuous_path_proof"])
        self.assertFalse(data["state_exchange_proven"])
        self.assertFalse(data["second_pair_topological_claim"])
        self.assertFalse(data["statistical_significance_claim"])
        self.assertFalse(data["thermodynamic_limit_proof"])
        self.assertFalse(data["new_taxonomy_claim"])
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])

    def test_independent_nested_beta_and_spectrum_recheck(self):
        path = ROOT / "matched_beta_independent.json"
        self.assertTrue(path.is_file(), "Independent matched-beta spectrum recheck is missing")
        independent = load("matched_beta_independent.json")
        self.assertTrue(independent["all_passed"])
        self.assertEqual(independent["protocol_sha256"], sha(ROOT / "matched_beta_control_protocol.json"))
        self.assertEqual(independent["candidate_source_sha256"], sha(ROOT / "swap_candidate_spectrum_analysis.json"))
        self.assertEqual(independent["cell_count"], 2)
        self.assertEqual(independent["max_coarsening_absolute_error"], 0.0)
        self.assertLessEqual(independent["max_spectrum_absolute_error"], 1e-12)
        self.assertLessEqual(independent["max_pair_center_absolute_error"], 1e-12)
        self.assertFalse(independent["new_winding_computed"])
        self.assertFalse(independent["n640_computed"])

    def test_figure_markdown_and_native_word_review(self):
        data = evidence(self)
        with Image.open(ROOT / "matched-beta-control.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "MATCHED_BETA_CONTROL.md").read_text(encoding="utf-8")
        for phrase in ("共同无序剖面", "嵌套块平均", "不归一化", "不能外推", "不补算体 winding", "N=640"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-共同无序剖面尺寸隔离.docx"
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
        qa = load("matched-beta-word-qa.json")
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertTrue(qa["visualReview"]["contactSheetRead"])
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])


    def test_word_layout_regression_guards(self):
        from xml.etree import ElementTree as ET

        docx = ROOT / "Floquet-BdG-共同无序剖面尺寸隔离.docx"
        with zipfile.ZipFile(docx) as package:
            root = ET.fromstring(package.read("word/document.xml"))
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        attr = lambda name: f"{{{ns['w']}}}{name}"
        paragraphs = root.findall(".//w:p", ns)
        subtitle = next(p for p in paragraphs if "同一主剖面" in "".join(p.itertext()))
        self.assertEqual("".join(subtitle.itertext()), "同一主剖面，而不是仅共享随机种子名称")
        for table in root.findall(".//w:tbl", ns):
            for cell in table.findall(".//w:tc", ns):
                spacing = cell.find("w:p/w:pPr/w:spacing", ns)
                self.assertIsNotNone(spacing)
                self.assertEqual(spacing.get(attr("after")), "40")
                self.assertEqual(spacing.get(attr("line")), "240")
                self.assertEqual(spacing.get(attr("lineRule")), "auto")
                margins = cell.find("w:tcPr/w:tcMar", ns)
                self.assertIsNotNone(margins)
                for side, expected in (("top", "80"), ("bottom", "80"), ("left", "60"), ("right", "60")):
                    self.assertEqual(margins.find(f"w:{side}", ns).get(attr("w")), expected)
        body = root.find("w:body", ns)
        blocks = list(body)
        following_texts = ("跨尺寸重叠不做归一化修正", "旧交换候选与共同")
        for index, block in enumerate(blocks[:-1]):
            if block.tag != attr("tbl"):
                continue
            following = blocks[index + 1]
            text = "".join(following.itertext())
            if text.startswith(following_texts):
                self.assertEqual(following.find("w:pPr/w:spacing", ns).get(attr("before")), "120")


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
