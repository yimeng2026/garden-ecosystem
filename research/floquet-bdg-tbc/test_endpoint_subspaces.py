"""Contracts for the bounded first/second-pair endpoint-subspace diagnostic."""

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


class EndpointSubspaceTests(unittest.TestCase):
    def test_registry_and_original_winding_are_unchanged(self):
        data = json.loads((ROOT / "endpoint_subspace_analysis.json").read_text(encoding="utf-8"))
        original = json.loads((ROOT / "scale_diagnostic.json").read_text(encoding="utf-8"))
        self.assertEqual(data["source_sha256"], sha(ROOT / "scale_diagnostic.json"))
        self.assertEqual(data["n640_computed"], False)
        self.assertEqual(data["thermodynamic_limit_proof"], False)
        for n, strength, passed in ((400, 0.1, True), (600, 0.05, False)):
            case = next(row for row in data["cases"] if row["n"] == n)
            old = next(row for row in original["rows"] if row["n"] == n)
            self.assertEqual(case["strength"], strength)
            self.assertEqual(case["seed"], 0)
            self.assertEqual(case["original_joint_pass"], passed)
            self.assertEqual(case["original_winding_integer"], old["zero"]["nearest_integer"])

    def test_first_pair_reproduces_existing_profile_hashes(self):
        data = json.loads((ROOT / "endpoint_subspace_analysis.json").read_text(encoding="utf-8"))
        for n in (400, 600):
            old = json.loads((ROOT / f"n{n}_scale.json").read_text(encoding="utf-8"))
            case = next(row for row in data["cases"] if row["n"] == n)
            first = case["pairs"][0]
            self.assertEqual(first["pair_index"], 0)
            self.assertEqual(first["profile_sha256"], old["profile_sha256"])
            self.assertEqual(first["edge_weight"], old["edge_weight"])
            self.assertEqual(first["L50"], old["L50"])
            self.assertEqual(first["L90"], old["L90"])

    def test_second_pair_cannot_retroactively_restore_endpoint(self):
        data = json.loads((ROOT / "endpoint_subspace_analysis.json").read_text(encoding="utf-8"))
        self.assertEqual(data["second_pair_role"], "diagnostic_only_no_retroactive_recovery")
        for case in data["cases"]:
            self.assertEqual(len(case["pairs"]), 2)
            self.assertEqual(case["pairs"][1]["pair_index"], 1)
            self.assertEqual(case["original_joint_pass"], case["reported_joint_pass"])
            self.assertIn("selection_caveat", case)

    def test_single_end_and_second_pair_mechanism_readout(self):
        data = json.loads((ROOT / "endpoint_subspace_analysis.json").read_text(encoding="utf-8"))
        n400 = next(case for case in data["cases"] if case["n"] == 400)
        first400, second400 = n400["pairs"]
        self.assertLess(first400["left_edge_weight"], 0.2)
        self.assertGreater(first400["right_edge_weight"], 0.4)
        self.assertLess(second400["left_edge_weight"], 0.001)
        self.assertGreater(second400["right_edge_weight"], 0.4)
        self.assertFalse(second400["diagnostic_joint_pass"])
        n600 = next(case for case in data["cases"] if case["n"] == 600)
        first600, second600 = n600["pairs"]
        self.assertLess(second600["edge_weight"], first600["edge_weight"])
        self.assertGreater(second600["L50"], first600["L50"])
        self.assertGreater(second600["center20_mass"], first600["center20_mass"])
        self.assertEqual(second600["max_separation_ratio"], 1.0)
        text = (ROOT / "ENDPOINT_SUBSPACES.md").read_text(encoding="utf-8")
        self.assertIn("右端主导", text)
        self.assertIn("单端权重不等于拓扑证明", text)

    def test_figure_and_markdown_preserve_limitations(self):
        with Image.open(ROOT / "endpoint-subspaces.png") as image:
            self.assertGreater(image.width, 1400)
            self.assertGreater(image.height, 700)
        text = (ROOT / "ENDPOINT_SUBSPACES.md").read_text(encoding="utf-8")
        self.assertIn("次近对", text)
        self.assertIn("不回溯恢复", text)
        self.assertIn("N=640", text)
        self.assertIn("不同无序强度", text)
        self.assertIn("endpoint-subspaces.png", text)

    def test_native_word_structure_and_visual_review(self):
        docx = ROOT / "Floquet-BdG-端点子空间诊断.docx"
        with zipfile.ZipFile(docx) as package:
            document = package.read("word/document.xml").decode("utf-8")
            footer = "".join(package.read(name).decode("utf-8") for name in package.namelist() if name.startswith("word/footer") and name.endswith(".xml"))
            media = [name for name in package.namelist() if name.startswith("word/media/") and not name.endswith("/")]
        self.assertIn("m:oMath", document)
        self.assertIn("TOC", document)
        self.assertIn("cantSplit", document)
        self.assertIn("PAGE", footer)
        self.assertNotIn("NUMPAGES", footer)
        self.assertEqual(len(media), 1)
        qa = json.loads((ROOT / "endpoint-word-qa.json").read_text(encoding="utf-8"))
        self.assertEqual(qa["visualReview"]["status"], "passed")
        self.assertEqual(qa["visualReview"]["pagesReviewed"], 4)
        self.assertEqual(qa["visualReview"]["docxSha256"], sha(docx))
        self.assertEqual(qa["visualReview"]["nearBlankPages"], [])
        self.assertEqual(qa["visualReview"]["clippedPages"], [])

    def test_independent_backend_and_projector_reproduce_both_pairs(self):
        result = json.loads((ROOT / "endpoint_subspace_independent.json").read_text(encoding="utf-8"))
        self.assertTrue(result["all_passed"])
        self.assertEqual(result["eigensolver"], "scipy.linalg.eig")
        self.assertEqual(result["projector"], "direct_gram_inverse")
        self.assertEqual(len(result["cases"]), 2)
        for case in result["cases"]:
            self.assertEqual(len(case["pairs"]), 2)
            for pair in case["pairs"]:
                self.assertLessEqual(pair["max_profile_absolute_error"], 1e-10)
                self.assertLessEqual(pair["edge_weight_absolute_error"], 1e-10)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
