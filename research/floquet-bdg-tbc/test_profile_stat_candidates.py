"""Contracts for preregistered profile-statistic screening without predictive fitting."""

import hashlib
import json
import re
import sys
import unittest
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "profile_stat_candidates_analysis.json"
MASTER_METRICS = ["mean", "std", "min", "q01", "q02", "q05", "q10", "q25", "q50", "q75", "q90", "q95", "q98", "q99", "max", "mad", "iqr", "low_frac_0p05", "low_frac_0p1", "low_frac_0p2", "high_frac_0p8", "high_frac_0p85", "high_frac_0p9", "high_frac_0p95", "lag1", "lag2", "lag3", "lag4", "roughness_rms", "total_variation", "sign_changes"]
BLOCK_METRICS = ["block_mean_min", "block_mean_max", "block_mean_std", "block_std_max", "block_std_mean", "low_block_frac_0p1", "high_block_frac_0p8", "left_right_delta", "endpoint_delta"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def evidence(test):
    test.assertTrue(DATA.is_file(), "Profile-statistic candidate analysis is missing")
    return load(DATA.name)


class ProfileStatCandidatesTests(unittest.TestCase):
    def test_sources_dedup_profiles_and_metric_inventory(self):
        data = evidence(self)
        protocol = load("profile_stat_candidates_protocol.json")
        self.assertEqual(data["schema"], "floquet-bdg-profile-stat-candidates-analysis-v1")
        self.assertEqual(data["protocol_sha256"], sha(ROOT / "profile_stat_candidates_protocol.json"))
        self.assertTrue(protocol["registered_before_analysis"])
        self.assertEqual(len(data["profiles"]), 8)
        self.assertEqual([row["seed"] for row in data["profiles"]], list(range(8)))
        self.assertEqual(data["new_floquet_cells_computed"], 0)
        self.assertEqual(data["new_seed_count"], 0)
        self.assertEqual(len(data["metric_records"]), 40)
        for row in data["profiles"]:
            seed = row["seed"]
            master = np.random.default_rng(20261111 + seed).random(4800)
            self.assertTrue(np.array_equal(np.asarray(row["master_profile"]), master))
            self.assertEqual(row["master_profile_sha256"], hashlib.sha256(master.tobytes()).hexdigest())
            self.assertTrue(np.array_equal(np.asarray(row["beta400"]), master.reshape(400, 12).mean(axis=1)))
            self.assertTrue(np.array_equal(np.asarray(row["beta600"]), master.reshape(600, 8).mean(axis=1)))
        self.assertEqual({row["metric"] for row in data["metric_records"]}, set(MASTER_METRICS + BLOCK_METRICS))
        self.assertIn('("profile_stat_candidates_suite"', (ROOT / "run_verification.py").read_text(encoding="utf-8"))

    def test_master_metric_definitions(self):
        data = evidence(self)
        for row in data["profiles"]:
            x = np.asarray(row["master_profile"])
            stats = row["master_metrics"]
            self.assertAlmostEqual(stats["mean"], float(np.mean(x)), places=15)
            self.assertAlmostEqual(stats["std"], float(np.std(x, ddof=0)), places=15)
            self.assertAlmostEqual(stats["min"], float(np.min(x)), places=15)
            self.assertAlmostEqual(stats["max"], float(np.max(x)), places=15)
            self.assertAlmostEqual(stats["q50"], float(np.quantile(x, 0.5)), places=15)
            self.assertAlmostEqual(stats["q02"], float(np.quantile(x, 0.02)), places=15)
            self.assertAlmostEqual(stats["q05"], float(np.quantile(x, 0.05)), places=15)
            self.assertAlmostEqual(stats["q95"], float(np.quantile(x, 0.95)), places=15)
            self.assertAlmostEqual(stats["q98"], float(np.quantile(x, 0.98)), places=15)
            self.assertAlmostEqual(stats["iqr"], float(np.quantile(x, 0.75) - np.quantile(x, 0.25)), places=15)
            self.assertAlmostEqual(stats["mad"], float(np.median(np.abs(x - np.median(x)))), places=15)
            self.assertAlmostEqual(stats["low_frac_0p05"], float(np.mean(x < 0.05)), places=15)
            self.assertAlmostEqual(stats["low_frac_0p1"], float(np.mean(x < 0.1)), places=15)
            self.assertAlmostEqual(stats["low_frac_0p2"], float(np.mean(x < 0.2)), places=15)
            self.assertAlmostEqual(stats["high_frac_0p8"], float(np.mean(x > 0.8)), places=15)
            self.assertAlmostEqual(stats["high_frac_0p85"], float(np.mean(x > 0.85)), places=15)
            self.assertAlmostEqual(stats["high_frac_0p9"], float(np.mean(x > 0.9)), places=15)
            self.assertAlmostEqual(stats["high_frac_0p95"], float(np.mean(x > 0.95)), places=15)
            differences = np.diff(x)
            self.assertAlmostEqual(stats["roughness_rms"], float(np.sqrt(np.mean(differences ** 2))), places=15)
            self.assertAlmostEqual(stats["total_variation"], float(np.mean(np.abs(differences))), places=15)
            self.assertEqual(stats["sign_changes"], int(np.sum(np.signbit(differences[1:]) != np.signbit(differences[:-1]))))

    def test_block_metrics_and_lag_statistics(self):
        data = evidence(self)
        for row in data["profiles"]:
            x = np.asarray(row["master_profile"])
            for n in (400, 600):
                block = x.reshape(n, 4800 // n)
                means = block.mean(axis=1)
                stds = block.std(axis=1, ddof=0)
                stats = row["block_metrics"][f"n{n}"]
                self.assertAlmostEqual(stats["block_mean_min"], float(np.min(means)), places=15)
                self.assertAlmostEqual(stats["block_mean_max"], float(np.max(means)), places=15)
                self.assertAlmostEqual(stats["block_mean_std"], float(np.std(means, ddof=0)), places=15)
                self.assertAlmostEqual(stats["block_std_max"], float(np.max(stds)), places=15)
                self.assertAlmostEqual(stats["block_std_mean"], float(np.mean(stds)), places=15)
                self.assertAlmostEqual(stats["low_block_frac_0p1"], float(np.mean(means < 0.1)), places=15)
                self.assertAlmostEqual(stats["high_block_frac_0p8"], float(np.mean(means > 0.8)), places=15)
                self.assertAlmostEqual(stats["left_right_delta"], float(np.mean(means[:n // 2]) - np.mean(means[n // 2:])), places=15)
                self.assertAlmostEqual(stats["endpoint_delta"], float(means[0] - means[-1]), places=15)
            for lag in (1, 2, 3, 4):
                expected = float(np.corrcoef(x[:-lag], x[lag:])[0, 1])
                self.assertAlmostEqual(row["master_metrics"][f"lag{lag}"], expected, places=12)

    def test_candidate_rule_and_coarsening_labels(self):
        data = evidence(self)
        self.assertEqual(len(data["candidate_metrics"]), len([row for row in data["metric_records"] if row["candidate"]]))
        for row in data["metric_records"]:
            self.assertGreaterEqual(row["unique_count"], 1)
            values = {str(seed): row["values"][str(seed)] for seed in (0, 1, 6)}
            if row["values"]["1"] < row["values"]["0"] < row["values"]["6"]:
                expected = "same_as_jump_changes"
            elif row["values"]["1"] > row["values"]["0"] > row["values"]["6"]:
                expected = "opposite_to_jump_changes"
            else:
                expected = "unordered"
            self.assertEqual(row["direction"], expected)
            self.assertEqual(row["candidate"], row["unique_count"] >= 6 and expected != "unordered")
            if row["level"] == "block":
                self.assertIn(row["coarsening_direction"], {"both_same", "different", "unordered"})
            else:
                self.assertEqual(row["coarsening_direction"], "not_applicable")
        self.assertFalse(data["predictive_model_fitted"])
        self.assertFalse(data["correlation_claim"])
        self.assertFalse(data["statistical_significance_claim"])

    def test_path_bindings_and_no_prediction_boundary(self):
        data = evidence(self)
        self.assertEqual(data["seed01_analysis_sha256"], sha(ROOT / "seed01_matrix_midpoint_analysis.json"))
        self.assertEqual(data["seed6_analysis_sha256"], sha(ROOT / "seed6_matrix_midpoint_analysis.json"))
        self.assertEqual(data["path_jump_counts"], {"0": 4, "1": 0, "6": 6})
        self.assertEqual(data["path_driver_counts"], {"0": 4, "1": 4, "6": 4})
        self.assertFalse(data["causal_mechanism_proven"])
        self.assertFalse(data["universal_size_law_claim"])
        self.assertFalse(data["thermodynamic_limit_proof"])

    def test_independent_metric_recheck(self):
        path = ROOT / "profile_stat_candidates_independent.json"
        self.assertTrue(path.is_file(), "Independent profile-statistic recheck is missing")
        independent = load(path.name)
        self.assertTrue(independent["all_passed"])
        self.assertEqual(independent["protocol_sha256"], sha(ROOT / "profile_stat_candidates_protocol.json"))
        self.assertEqual(independent["profile_count"], 8)
        self.assertEqual(independent["metric_record_count"], 40)
        self.assertEqual(independent["max_master_absolute_error"], 0.0)
        self.assertEqual(independent["max_beta_absolute_error"], 0.0)
        self.assertLessEqual(independent["max_metric_absolute_error"], 1e-12)
        self.assertEqual(independent["candidate_mismatch_count"], 0)
        self.assertFalse(independent["new_floquet_spectra_recomputed"])

    def test_figure_markdown_and_native_word_review(self):
        evidence(self)
        with Image.open(ROOT / "profile-stat-candidates.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 900)
        text = (ROOT / "PROFILE_STAT_CANDIDATES.md").read_text(encoding="utf-8")
        for phrase in ("主剖面", "block", "粗糙度", "不归一化", "不能外推", "不补算体 winding", "N=640", "不筛选", "探索性候选"):
            self.assertIn(phrase, text)
        docx = ROOT / "Floquet-BdG-无序剖面候选统计指标.docx"
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
        qa = load("profile-stat-candidates-word-qa.json")
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 5)
        self.assertTrue(qa["visualReview"]["contactSheetRead"])
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])

    def test_word_layout_and_analysis_scope(self):
        from xml.etree import ElementTree as ET

        data = evidence(self)
        docx = ROOT / "Floquet-BdG-无序剖面候选统计指标.docx"
        with zipfile.ZipFile(docx) as package:
            root = ET.fromstring(package.read("word/document.xml"))
        ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        attr = lambda name: f"{{{ns['w']}}}{name}"
        for table in root.findall(".//w:tbl", ns):
            for cell in table.findall(".//w:tc", ns):
                spacing = cell.find("w:p/w:pPr/w:spacing", ns)
                self.assertEqual(spacing.get(attr("after")), "40")
                self.assertEqual(spacing.get(attr("line")), "240")
                self.assertEqual(spacing.get(attr("lineRule")), "auto")
                margins = cell.find("w:tcPr/w:tcMar", ns)
                for side, expected in (("top", "80"), ("bottom", "80"), ("left", "60"), ("right", "60")):
                    self.assertEqual(margins.find(f"w:{side}", ns).get(attr("w")), expected)
        self.assertEqual(data["new_floquet_cells_computed"], 0)
        self.assertTrue(data["all_preregistered_results_retained"])
        self.assertFalse(data["statistical_significance_claim"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() and result.testsRun else 1)
