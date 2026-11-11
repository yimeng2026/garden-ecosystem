"""Contracts for the preregistered four-seed factorial profile pilot."""

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


def case(data, n, strength, seed):
    return next(row for row in data["cases"] if (row["n"], row["strength"], row["seed"]) == (n, strength, seed))


class MultiSeedTests(unittest.TestCase):
    def test_protocol_and_full_factorial(self):
        data = json.loads((ROOT / "multi_seed_profile_control.json").read_text(encoding="utf-8"))
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "multi_seed_protocol.json"))
        self.assertEqual(data["seeds"], [0, 1, 2, 3])
        self.assertEqual(len(data["cases"]), 16)
        self.assertEqual({(row["n"], row["strength"], row["seed"]) for row in data["cases"]}, {(n, r, s) for n in (400, 600) for r in (0.05, 0.1) for s in (0, 1, 2, 3)})
        self.assertTrue(all(len(row["pairs"]) == 2 for row in data["cases"]))
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])
        self.assertFalse(data["causal_or_statistical_claim"])

    def test_seed_zero_matches_frozen_factorial(self):
        data = json.loads((ROOT / "multi_seed_profile_control.json").read_text(encoding="utf-8"))
        old = json.loads((ROOT / "matched_profile_control.json").read_text(encoding="utf-8"))
        self.assertEqual(data["matched_source_sha256"], sha(ROOT / "matched_profile_control.json"))
        for n, strength in ((400, 0.05), (400, 0.1), (600, 0.05), (600, 0.1)):
            previous = next(row for row in old["cases"] if (row["n"], row["strength"]) == (n, strength))["pairs"][0]
            first = case(data, n, strength, 0)["pairs"][0]
            self.assertEqual(first["profile_sha256"], previous["profile_sha256"])
            self.assertEqual(first["edge_weight"], previous["edge_weight"])
            self.assertEqual(first["L50"], previous["L50"])

    def test_every_seed_and_sign_is_reported(self):
        data = json.loads((ROOT / "multi_seed_profile_control.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["contrasts"]["size_at_fixed_strength"]), 8)
        self.assertEqual(len(data["contrasts"]["strength_at_fixed_size"]), 8)
        self.assertEqual(len(data["contrasts"]["interaction"]), 4)
        for row in data["contrasts"]["size_at_fixed_strength"]:
            n400 = case(data, 400, row["strength"], row["seed"])["pairs"][0]
            n600 = case(data, 600, row["strength"], row["seed"])["pairs"][0]
            self.assertEqual(row["delta_L50"], n600["L50"] - n400["L50"])
            self.assertAlmostEqual(row["delta_edge_weight"], n600["edge_weight"] - n400["edge_weight"])
        for group in data["sign_summaries"].values():
            for summary in group.values():
                self.assertEqual(summary["positive"] + summary["negative"] + summary["zero"], 4)
                self.assertLessEqual(summary["minimum"], summary["median"])
                self.assertLessEqual(summary["median"], summary["maximum"])
        self.assertFalse(data["post_hoc_seed_selection"])

    def test_stability_conclusions_match_all_sign_counts(self):
        data = json.loads((ROOT / "multi_seed_profile_control.json").read_text(encoding="utf-8"))
        summaries = data["sign_summaries"]
        for group in ("size_r0.05", "size_r0.1"):
            self.assertEqual(summaries[group]["delta_edge_weight"]["positive"], 3)
            self.assertEqual(summaries[group]["delta_edge_weight"]["negative"], 1)
            self.assertEqual(summaries[group]["delta_L50"]["positive"], 2)
            self.assertEqual(summaries[group]["delta_L50"]["negative"], 2)
            self.assertEqual(summaries[group]["delta_center20_mass"]["negative"], 4)
        for group in ("strength_N400", "strength_N600"):
            self.assertEqual(summaries[group]["delta_edge_weight"]["positive"], 4)
        self.assertEqual(summaries["strength_N400"]["delta_L50"]["negative"], 4)
        self.assertEqual(summaries["strength_N600"]["delta_L50"]["negative"], 3)
        self.assertEqual(summaries["interaction"]["delta_edge_weight"]["positive"], 2)
        self.assertEqual(summaries["interaction"]["delta_edge_weight"]["negative"], 2)
        text = (ROOT / "MULTI_SEED_CONTROL.md").read_text(encoding="utf-8")
        self.assertIn("尺寸端点权重并非全员同号", text)
        self.assertIn("强度升高端点权重在 4/4 种子中增加", text)
        self.assertIn("尺寸效应的符号反转不能普适化", text)

    def test_independent_backend_reproduces_all_seeds(self):
        result = json.loads((ROOT / "multi_seed_independent.json").read_text(encoding="utf-8"))
        self.assertTrue(result["all_passed"])
        self.assertEqual(result["eigensolver"], "scipy.linalg.eig")
        self.assertEqual(result["projector"], "direct_gram_inverse")
        self.assertEqual(len(result["cases"]), 16)
        for row in result["cases"]:
            self.assertEqual(len(row["pairs"]), 2)
            for pair in row["pairs"]:
                self.assertLessEqual(pair["max_profile_absolute_error"], 1e-10)

    def test_figure_markdown_and_word_visual_gate(self):
        with Image.open(ROOT / "multi-seed-control.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 700)
        text = (ROOT / "MULTI_SEED_CONTROL.md").read_text(encoding="utf-8")
        for phrase in ("4 个预登记种子", "方向计数不是置信区间", "不补算体 winding", "N=640", "交互项"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-多种子稳健性对照.docx"
        with zipfile.ZipFile(docx) as package:
            document = package.read("word/document.xml").decode("utf-8")
            footer = "".join(package.read(name).decode("utf-8") for name in package.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            media = [name for name in package.namelist() if name.startswith("word/media/") and not name.endswith("/")]
        self.assertIn("m:oMath", document)
        self.assertIn("TOC", document)
        self.assertIn("PAGE", footer)
        self.assertEqual(len(media), 1)
        qa = json.loads((ROOT / "multi-seed-word-qa.json").read_text(encoding="utf-8"))
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])

    def test_word_error_value_matches_latest_independent_backend(self):
        result = json.loads((ROOT / "multi_seed_independent.json").read_text(encoding="utf-8"))
        maximum = max(pair["max_profile_absolute_error"] for case in result["cases"] for pair in case["pairs"])
        with zipfile.ZipFile(ROOT / "Floquet-BdG-多种子稳健性对照.docx") as package:
            document = package.read("word/document.xml").decode("utf-8")
        self.assertIn(f"最大剖面绝对误差为 {maximum:.3e}", document)
        runner = (ROOT / "run_multi_seed_verification.py").read_text(encoding="utf-8")
        self.assertNotIn('("docx_build"', runner)
        self.assertNotIn('("multi_seed_analysis"', runner)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
