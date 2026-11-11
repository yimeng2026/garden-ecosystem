"""Contracts for the preregistered 2x2 profile-only control."""

import hashlib
import json
import sys
import unittest
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def case(data, n, strength):
    return next(row for row in data["cases"] if row["n"] == n and row["strength"] == strength)


class MatchedProfileTests(unittest.TestCase):
    def test_factorial_registry_and_scope(self):
        data = json.loads((ROOT / "matched_profile_control.json").read_text(encoding="utf-8"))
        self.assertEqual(data["source_sha256"], sha(ROOT / "scale_diagnostic.json"))
        self.assertEqual({(row["n"], row["strength"]) for row in data["cases"]}, {(400, 0.05), (400, 0.1), (600, 0.05), (600, 0.1)})
        self.assertTrue(all(row["seed"] == 0 for row in data["cases"]))
        self.assertTrue(all(len(row["pairs"]) == 2 for row in data["cases"]))
        self.assertTrue(data["new_cases_are_profile_only"])
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])
        self.assertFalse(data["thermodynamic_limit_proof"])

    def test_existing_cells_match_frozen_evidence(self):
        data = json.loads((ROOT / "matched_profile_control.json").read_text(encoding="utf-8"))
        for n, strength in ((400, 0.1), (600, 0.05)):
            old = json.loads((ROOT / f"n{n}_scale.json").read_text(encoding="utf-8"))
            first = case(data, n, strength)["pairs"][0]
            self.assertEqual(first["profile_sha256"], old["profile_sha256"])
            self.assertEqual(first["edge_weight"], old["edge_weight"])
            self.assertEqual(first["L50"], old["L50"])
            self.assertEqual(first["L90"], old["L90"])
            self.assertEqual(first["diagnostic_joint_pass"], old["joint_pass"])

    def test_factor_contrasts_are_descriptive_not_causal(self):
        data = json.loads((ROOT / "matched_profile_control.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["contrasts"]["size_at_fixed_strength"]), 2)
        self.assertEqual(len(data["contrasts"]["strength_at_fixed_size"]), 2)
        for row in data["contrasts"]["size_at_fixed_strength"]:
            n400 = case(data, 400, row["strength"])["pairs"][0]
            n600 = case(data, 600, row["strength"])["pairs"][0]
            self.assertEqual(row["delta_L50"], n600["L50"] - n400["L50"])
            self.assertAlmostEqual(row["delta_edge_weight"], n600["edge_weight"] - n400["edge_weight"])
        for row in data["contrasts"]["strength_at_fixed_size"]:
            low = case(data, row["n"], 0.05)["pairs"][0]
            high = case(data, row["n"], 0.1)["pairs"][0]
            self.assertEqual(row["delta_L50"], high["L50"] - low["L50"])
            self.assertAlmostEqual(row["delta_edge_weight"], high["edge_weight"] - low["edge_weight"])
        self.assertEqual(data["contrasts"]["interaction"]["status"], "descriptive_single_seed_only")
        self.assertFalse(data["causal_or_statistical_claim"])

    def test_observed_directions_do_not_promote_new_topology(self):
        data = json.loads((ROOT / "matched_profile_control.json").read_text(encoding="utf-8"))
        low, high = data["contrasts"]["size_at_fixed_strength"]
        self.assertLess(low["delta_edge_weight"], 0)
        self.assertGreater(high["delta_edge_weight"], 0)
        self.assertGreater(low["delta_L50"], 0)
        self.assertGreater(high["delta_L50"], 0)
        for row in data["contrasts"]["strength_at_fixed_size"]:
            self.assertLess(row["delta_L50"], 0)
            self.assertGreater(row["delta_edge_weight"], 0)
        self.assertTrue(case(data, 600, 0.1)["pairs"][0]["diagnostic_joint_pass"])
        self.assertFalse(data["new_winding_computed"])
        text = (ROOT / "MATCHED_PROFILE_CONTROL.md").read_text(encoding="utf-8")
        self.assertIn("尺寸效应在两种强度下方向不同", text)
        self.assertIn("强度升高伴随端点权重增加", text)
        self.assertIn("N=600、r=0.1 的新 profile 判据通过", text)
        self.assertIn("不等于体 winding 已验证", text)

    def test_independent_backend_reproduces_all_cells(self):
        result = json.loads((ROOT / "matched_profile_independent.json").read_text(encoding="utf-8"))
        self.assertTrue(result["all_passed"])
        self.assertEqual(result["eigensolver"], "scipy.linalg.eig")
        self.assertEqual(result["projector"], "direct_gram_inverse")
        self.assertEqual(len(result["cases"]), 4)
        for row in result["cases"]:
            self.assertEqual(len(row["pairs"]), 2)
            for pair in row["pairs"]:
                self.assertLessEqual(pair["max_profile_absolute_error"], 1e-10)

    def test_word_error_value_matches_latest_independent_backend(self):
        result = json.loads((ROOT / "matched_profile_independent.json").read_text(encoding="utf-8"))
        maximum = max(pair["max_profile_absolute_error"] for case in result["cases"] for pair in case["pairs"])
        with zipfile.ZipFile(ROOT / "Floquet-BdG-同强度尺寸对照.docx") as package:
            document = package.read("word/document.xml").decode("utf-8")
        self.assertIn(f"最大剖面绝对误差为 {maximum:.3e}", document)

    def test_figure_markdown_and_word_visual_gate(self):
        with Image.open(ROOT / "matched-profile-control.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 700)
        text = (ROOT / "MATCHED_PROFILE_CONTROL.md").read_text(encoding="utf-8")
        for phrase in ("2×2", "单种子", "不补算体 winding", "N=640", "交互项"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-同强度尺寸对照.docx"
        with zipfile.ZipFile(docx) as package:
            document = package.read("word/document.xml").decode("utf-8")
            footer = "".join(package.read(name).decode("utf-8") for name in package.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            media = [name for name in package.namelist() if name.startswith("word/media/") and not name.endswith("/")]
        self.assertIn("m:oMath", document)
        self.assertIn("TOC", document)
        self.assertIn("PAGE", footer)
        self.assertEqual(len(media), 1)
        qa = json.loads((ROOT / "matched-word-qa.json").read_text(encoding="utf-8"))
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
