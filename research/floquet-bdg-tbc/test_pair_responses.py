"""Contracts for rank-matched first/second-pair size-response auditing."""

import hashlib
import json
import math
import re
import sys
import unittest
import zipfile
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def sign(value):
    return (value > 0) - (value < 0)


def response(data, seed, strength, pair_index):
    return next(row for row in data["responses"] if (row["seed"], row["strength"], row["pair_index"]) == (seed, strength, pair_index))


def relation_counts(rows, key):
    counts = Counter()
    for row in rows:
        product = sign(row[f"pair0_{key}"]) * sign(row[f"pair1_{key}"])
        counts["same_nonzero" if product > 0 else "opposite_nonzero" if product < 0 else "at_least_one_zero"] += 1
    return dict(counts)


class PairResponseTests(unittest.TestCase):
    def test_frozen_registry_and_sources(self):
        protocol = load("pair_response_protocol.json")
        data = load("pair_response_analysis.json")
        source = load("repeated_category_analysis.json")
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "pair_response_protocol.json"))
        self.assertEqual(data["source_sha256"], sha(ROOT / "repeated_category_analysis.json"))
        self.assertEqual(data["near_miss_source_sha256"], sha(ROOT / "near_miss_spatial_analysis.json"))
        self.assertEqual(protocol["seeds"], list(range(8)))
        self.assertEqual(protocol["strengths"], [0.05, 0.1])
        self.assertEqual(protocol["pair_indices"], [0, 1])
        self.assertEqual(protocol["new_seed_count"], 0)
        self.assertEqual(len(data["cases"]), 16)
        self.assertEqual(len(data["responses"]), 32)
        self.assertEqual(len(data["records"]), 64)
        self.assertEqual(data["original_category_counts"], source["category_counts"])
        self.assertFalse(data["new_eigenpairs_computed"])
        self.assertFalse(data["new_winding_computed"])
        self.assertFalse(data["n640_computed"])
        self.assertFalse(data["new_taxonomy_claim"])
        self.assertIn('("pair_response_suite"', (ROOT / "run_verification.py").read_text(encoding="utf-8"))

    def test_records_reproduce_original_endpoint_definitions(self):
        data = load("pair_response_analysis.json")
        source = load("repeated_category_analysis.json")
        for row in data["records"]:
            case = next(item for item in source["all_cells"] if (item["n"], item["strength"], item["seed"]) == (row["n"], row["strength"], row["seed"]))
            pair = case["pairs"][row["pair_index"]]
            profile = pair["profile"]
            width = pair["edge_sites_per_end"]
            left = math.fsum(profile[:width])
            right = math.fsum(profile[-width:])
            edge = left + right
            self.assertEqual(width, row["n"] // 10)
            self.assertEqual(row["profile_sha256"], pair["profile_sha256"])
            self.assertAlmostEqual(row["left"], left, places=14)
            self.assertAlmostEqual(row["right"], right, places=14)
            self.assertAlmostEqual(row["edge"], edge, places=14)
            self.assertAlmostEqual(row["edge"], pair["edge_weight"], places=14)
            self.assertAlmostEqual(row["asymmetry"], abs(left - right) / edge, places=12)
            self.assertEqual(row["L50"], pair["L50"])
            self.assertEqual(row["max_separation_ratio"], pair["max_separation_ratio"])
        self.assertLessEqual(data["max_original_metric_recompute_error"], 1e-12)

    def test_first_pair_deltas_match_frozen_comparisons(self):
        data = load("pair_response_analysis.json")
        source = load("repeated_category_analysis.json")
        for old in source["cases"]:
            row = response(data, old["seed"], old["strength"], 0)
            comparison = old["comparison"]
            self.assertAlmostEqual(row["left_delta"], comparison["left_delta"], places=14)
            self.assertAlmostEqual(row["right_delta"], comparison["right_delta"], places=14)
            self.assertAlmostEqual(row["edge_delta"], comparison["edge_delta"], places=14)
            self.assertAlmostEqual(row["asymmetry_delta"], comparison["asymmetry_delta"], places=14)
            self.assertEqual(row["L50_delta"], comparison["delta_L50"])
            self.assertEqual(row["original_category"], old["category"])
            self.assertAlmostEqual(row["left_delta"] + row["right_delta"], row["edge_delta"], places=14)

    def test_sign_tables_are_descriptive_and_complete(self):
        data = load("pair_response_analysis.json")
        joined = []
        for case in data["cases"]:
            first = response(data, case["seed"], case["strength"], 0)
            second = response(data, case["seed"], case["strength"], 1)
            joined.append({
                "pair0_edge_delta": first["edge_delta"], "pair1_edge_delta": second["edge_delta"],
                "pair0_L50_delta": first["L50_delta"], "pair1_L50_delta": second["L50_delta"],
            })
        self.assertEqual(data["edge_relation_counts"], relation_counts(joined, "edge_delta"))
        self.assertEqual(data["L50_relation_counts"], relation_counts(joined, "L50_delta"))
        self.assertEqual(sum(data["edge_relation_counts"].values()), 16)
        self.assertEqual(sum(data["L50_relation_counts"].values()), 16)
        for metric in ("edge", "L50"):
            table = data[f"{metric}_sign_crosstab"]
            self.assertEqual(sum(sum(row.values()) for row in table.values()), 16)
            for case in data["cases"]:
                first = response(data, case["seed"], case["strength"], 0)
                second = response(data, case["seed"], case["strength"], 1)
                key = "edge_delta" if metric == "edge" else "L50_delta"
                self.assertGreaterEqual(table[str(sign(first[key]))][str(sign(second[key]))], 0)
        self.assertFalse(data["statistical_significance_claim"])

    def test_second_pair_is_rank_matched_not_tracked_or_topological(self):
        data = load("pair_response_analysis.json")
        self.assertEqual(data["pair_identity"], "same_spectral_rank_not_adiabatic_state_tracking")
        self.assertFalse(data["second_pair_topological_claim"])
        self.assertFalse(data["categories_changed"])
        self.assertFalse(data["universal_mechanism_claim"])
        for case in data["cases"]:
            second = response(data, case["seed"], case["strength"], 1)
            self.assertIn("both_sizes_joint_pass", second)
            self.assertIn("max_separation_ratio_delta", second)
        near = load("near_miss_spatial_analysis.json")
        for old in near["cases"]:
            row = response(data, old["seed"], old["strength"], 1)
            previous = next(item for item in near["size_deltas"] if item["label"] == old["label"] and item["pair_index"] == 1)
            self.assertAlmostEqual(row["edge_delta"], previous["edge10pct"], places=14)
            self.assertEqual(row["L50_delta"], previous["L50"])

    def test_figure_markdown_and_reviewed_word(self):
        from analyze_pair_responses import heatmap_text_color
        self.assertEqual(heatmap_text_color(7, 7), "#FFFFFF")
        self.assertEqual(heatmap_text_color(9, 9), "#FFFFFF")
        self.assertEqual(heatmap_text_color(1, 9), "#203B35")
        with Image.open(ROOT / "pair-response-audit.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "PAIR_RESPONSE_AUDIT.md").read_text(encoding="utf-8")
        for phrase in ("次近对", "谱排序", "不是", "不新增类别", "不补算体 winding", "N=640"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-最近对与次近对响应审计.docx"
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
        qa = load("pair-response-word-qa.json")
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])
        runner = (ROOT / "run_pair_response_verification.py").read_text(encoding="utf-8")
        self.assertNotIn('("docx_build"', runner)


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
