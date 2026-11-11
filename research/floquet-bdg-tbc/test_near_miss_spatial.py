"""Contracts for frozen-profile near-miss spatial and second-pair diagnostics."""

import hashlib
import json
import math
import sys
import unittest
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
WINDOWS = ("left_outer40", "left_inner40", "central40", "right_inner40", "right_outer40")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def source_cell(source, n, strength, seed):
    return next(row for row in source["all_cells"] if (row["n"], row["strength"], row["seed"]) == (n, strength, seed))


def delta(data, label, pair_index):
    return next(row for row in data["size_deltas"] if row["label"] == label and row["pair_index"] == pair_index)


class NearMissSpatialTests(unittest.TestCase):
    def test_frozen_registry_and_sources(self):
        protocol = load("near_miss_spatial_protocol.json")
        data = load("near_miss_spatial_analysis.json")
        source = load("repeated_category_analysis.json")
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "near_miss_spatial_protocol.json"))
        self.assertEqual(data["source_sha256"], sha(ROOT / "repeated_category_analysis.json"))
        self.assertEqual(data["unclassified_source_sha256"], sha(ROOT / "unclassified_signature_analysis.json"))
        self.assertEqual(protocol["selected_cases"], [
            {"label": "near_miss_low", "seed": 5, "strength": 0.05},
            {"label": "near_miss_high", "seed": 5, "strength": 0.1},
            {"label": "reference_weakening", "seed": 2, "strength": 0.1},
        ])
        self.assertEqual(protocol["pair_indices"], [0, 1])
        self.assertEqual(protocol["new_seed_count"], 0)
        self.assertEqual(len(data["records"]), 12)
        self.assertEqual(len(data["size_deltas"]), 6)
        self.assertEqual(data["original_category_counts"], source["category_counts"])
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])
        self.assertFalse(data["new_taxonomy_claim"])
        self.assertFalse(data["second_pair_topological_claim"])
        self.assertIn('("near_miss_suite"', (ROOT / "run_verification.py").read_text(encoding="utf-8"))

    def test_windows_recomputed_from_independently_verified_profiles(self):
        data = load("near_miss_spatial_analysis.json")
        source = load("repeated_category_analysis.json")
        for row in data["records"]:
            pair = source_cell(source, row["n"], row["strength"], row["seed"])["pairs"][row["pair_index"]]
            profile = pair["profile"]
            n = row["n"]
            expected = {
                "left_outer40": math.fsum(profile[:40]),
                "left_inner40": math.fsum(profile[40:80]),
                "central40": math.fsum(profile[n // 2 - 20:n // 2 + 20]),
                "right_inner40": math.fsum(profile[n - 80:n - 40]),
                "right_outer40": math.fsum(profile[n - 40:]),
            }
            self.assertEqual(row["profile_sha256"], pair["profile_sha256"])
            for name in WINDOWS:
                self.assertAlmostEqual(row["windows"][name], expected[name], places=14)
            self.assertAlmostEqual(row["edge40"], expected["left_outer40"] + expected["right_outer40"], places=14)
            self.assertAlmostEqual(row["signed_asymmetry40"], (expected["right_outer40"] - expected["left_outer40"]) / row["edge40"], places=12)
            edge_sites = pair["edge_sites_per_end"]
            left = math.fsum(profile[:edge_sites])
            right = math.fsum(profile[-edge_sites:])
            self.assertAlmostEqual(row["left10pct"], left, places=14)
            self.assertAlmostEqual(row["right10pct"], right, places=14)
            self.assertAlmostEqual(row["edge10pct"], pair["edge_weight"], places=14)
            self.assertAlmostEqual(row["asymmetry10pct"], abs(left - right) / row["edge10pct"], places=12)
            self.assertEqual(row["L50"], pair["L50"])
            self.assertEqual(row["max_separation_ratio"], pair["max_separation_ratio"])
            self.assertLessEqual(data["max_original_metric_recompute_error"], 1e-12)

    def test_size_deltas_explain_the_two_near_misses(self):
        data = load("near_miss_spatial_analysis.json")
        source = load("repeated_category_analysis.json")
        for row in data["size_deltas"]:
            case = next(item for item in data["cases"] if item["label"] == row["label"])
            original = next(item for item in source["cases"] if (item["seed"], item["strength"]) == (case["seed"], case["strength"]))["comparison"]
            if row["pair_index"] == 0:
                self.assertAlmostEqual(row["left10pct"], original["left_delta"], places=14)
                self.assertAlmostEqual(row["right10pct"], original["right_delta"], places=14)
                self.assertAlmostEqual(row["edge10pct"], original["edge_delta"], places=14)
                self.assertAlmostEqual(row["asymmetry10pct"], original["asymmetry_delta"], places=14)
                self.assertEqual(row["L50"], original["delta_L50"])
        low = delta(data, "near_miss_low", 0)
        self.assertGreater(low["left10pct"], 0)
        self.assertLess(low["right10pct"], 0)
        self.assertGreater(low["edge10pct"], 0)
        self.assertAlmostEqual(low["left10pct"] + low["right10pct"], low["edge10pct"], places=14)
        high = delta(data, "near_miss_high", 0)
        self.assertGreater(high["left10pct"], 0)
        self.assertLess(high["right10pct"], 0)
        self.assertLess(high["edge10pct"], 0)
        self.assertLess(high["asymmetry10pct"], 0)
        self.assertGreater(high["L50"], 0)
        reference = delta(data, "reference_weakening", 0)
        self.assertLess(reference["right10pct"], 0)
        self.assertLess(reference["edge10pct"], 0)
        self.assertGreater(reference["asymmetry10pct"], 0)
        self.assertEqual(set(delta(data, "near_miss_low", 1)), {"label", "pair_index", *WINDOWS, "edge40", "signed_asymmetry40", "left10pct", "right10pct", "edge10pct", "asymmetry10pct", "L50", "max_separation_ratio"})

    def test_second_pair_is_diagnostic_and_categories_are_unchanged(self):
        data = load("near_miss_spatial_analysis.json")
        source = load("repeated_category_analysis.json")
        for label in ("near_miss_low", "near_miss_high", "reference_weakening"):
            second = delta(data, label, 1)
            for name in WINDOWS + ("edge40", "signed_asymmetry40", "left10pct", "right10pct", "edge10pct", "asymmetry10pct", "L50", "max_separation_ratio"):
                self.assertIn(name, second)
            case = next(row for row in data["cases"] if row["label"] == label)
            old = next(row for row in source["cases"] if (row["seed"], row["strength"]) == (case["seed"], case["strength"]))
            self.assertEqual(case["original_category"], old["category"])
        self.assertFalse(data["categories_changed"])
        self.assertFalse(data["second_pair_topological_claim"])
        self.assertFalse(data["universal_mechanism_claim"])

    def test_tables_fit_word_page(self):
        import re
        docx = ROOT / "Floquet-BdG-近miss空间分布与次近对.docx"
        with zipfile.ZipFile(docx) as package:
            document = package.read("word/document.xml").decode("utf-8")
        grids = re.findall(r"<w:tblGrid>(.*?)</w:tblGrid>", document)
        self.assertTrue(grids)
        for grid in grids:
            widths = [int(value) for value in re.findall(r'w:w="(\d+)"', grid)]
            self.assertLessEqual(sum(widths), 9906)

    def test_figure_markdown_and_reviewed_word(self):
        with Image.open(ROOT / "near-miss-spatial.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 1000)
        text = (ROOT / "NEAR_MISS_SPATIAL.md").read_text(encoding="utf-8")
        for phrase in ("次近对", "左外40", "右内40", "近 miss", "不新增类别", "不补算体 winding", "N=640"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-近miss空间分布与次近对.docx"
        with zipfile.ZipFile(docx) as package:
            document = package.read("word/document.xml").decode("utf-8")
            footer = "".join(package.read(name).decode("utf-8") for name in package.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            media = [name for name in package.namelist() if name.startswith("word/media/") and not name.endswith("/")]
        self.assertIn("m:oMath", document)
        self.assertIn("TOC", document)
        self.assertIn("PAGE", footer)
        self.assertEqual(len(media), 1)
        qa = load("near-miss-word-qa.json")
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])
        runner = (ROOT / "run_near_miss_verification.py").read_text(encoding="utf-8")
        self.assertNotIn('("docx_build"', runner)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
