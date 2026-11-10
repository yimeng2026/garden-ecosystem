import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "theory_framework": "c53b9b8fbab8018e3e2948e8ecff71d0232dd47e60c8a86f4281e58200c262fb",
    "breakthrough_report": "7d9711df200880690a82c814380e4392f35a1ca3c6df957cabe6607678ba00ce",
    "main_claims_review": "e9ac6ff0bc88f11b1c2c91ae61ce398a05fc077815803f48669b46536d6f2f45",
    "methods_review": "f30d15d8665644d11957166efaea95d59f7a742037dc697b737704cd15dc9e21",
}


class TheoryBreakthroughAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))

    def test_source_lineage_and_directions(self):
        self.assertEqual(self.data["source_lineage"]["research_program_count"], 1)
        self.assertEqual(len(self.data["directions"]), 4)
        self.assertEqual(
            {row["id"] for row in self.data["directions"]},
            {"conditional_proof", "assumption_falsifiability", "experimental_controversy", "provenance_governance"},
        )
        actual = {row["id"]: row["sha256"] for row in self.data["sources"]}
        self.assertEqual(actual, EXPECTED_HASHES)

    def test_theory_proof_debt(self):
        row = self.data["evidence"]["theory"]
        self.assertEqual(row["admit_count"], 17)
        self.assertEqual(row["sorry_count"], 5)
        self.assertEqual(row["proof_debt_total"], 22)
        self.assertEqual(len(row["module_references"]), 5)
        self.assertEqual(row["repository_module_match_count"], 0)
        self.assertFalse(row["lean_compilation_attempted"])
        self.assertFalse(row["formal_proof_completed"])

    def test_logic_scope_and_counterexample_boundary(self):
        row = self.data["evidence"]["logic"]
        self.assertFalse(row["existence_to_universal_valid"])
        self.assertFalse(row["continuity_bridges_universal"])
        anchor = row["simplified_formula_anchor"]
        self.assertEqual(anchor["lambda"], 2.0)
        self.assertEqual(anchor["mu_star"], 0.15)
        self.assertLess(anchor["tc_k"], 300)
        self.assertAlmostEqual(anchor["tc_k"], 148.24313461676417)
        self.assertFalse(row["full_eliashberg_refuted"])
        self.assertFalse(row["specific_material_refuted"])

    def test_experimental_roles(self):
        row = self.data["evidence"]["experiment"]
        self.assertEqual(row["song"]["onset_tc_k"], [271, 298])
        self.assertLess(max(row["song"]["onset_tc_k"]), 300)
        self.assertEqual(row["song"]["reproducible_runs_reported"], 13)
        self.assertTrue(row["song"]["preprint"])
        self.assertFalse(row["song"]["direct_meissner_completed"])
        self.assertFalse(row["song"]["independent_positive_replication"])
        self.assertFalse(row["song"]["author_runs_equal_independent_labs"])
        self.assertEqual(row["semenok"]["unsuccessful_attempts"], 7)
        self.assertFalse(row["semenok"]["final_refutation_of_material_family"])
        self.assertEqual(row["pnas"]["predicted_tc_k"], [316, 331])
        self.assertTrue(row["pnas"]["theoretical_prediction"])

    def test_breakthrough_specific_corrections(self):
        row = self.data["evidence"]["breakthrough"]
        self.assertTrue(row["tc_298_316_mixed_roles"])
        self.assertFalse(row["p6mmm_implies_quasi_2d"])
        self.assertFalse(row["mechanism_verified_by_structure_and_tc"])
        self.assertTrue(row["metadata_date_precedes_cited_preprint"])
        self.assertEqual(row["document_date"], "2025-04-19")
        self.assertEqual(row["cited_preprint_month"], "2025-10")

    def test_corrections_and_open_boundaries(self):
        self.assertEqual(len(self.data["corrections"]), 6)
        for key in (
            "formal_proof_completed",
            "lean_modules_resolved",
            "necessity_experimentally_proven",
            "independent_positive_replication",
            "direct_meissner_completed",
            "full_repository_audit",
        ):
            self.assertFalse(self.data["open_boundaries"][key])

    def test_figure_scope(self):
        figure = self.data["figure"]
        for label in ("单点存在", "普遍必然", "PNAS 预测", "Song 预印本", "Semenok 负向复现"):
            self.assertIn(label, figure["labels"])
        self.assertFalse(figure["success_percentage_plotted"])

    def test_markdown_and_native_word_contract(self):
        markdown = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        for text in ("17 处 admit", "5 处 sorry", "298 K 低于 300 K", "图 1", "全库审计尚未完成"):
            self.assertIn(text, markdown)
        with zipfile.ZipFile(ROOT / "REVIEW.docx") as package:
            names = package.namelist()
            document = package.read("word/document.xml")
            header = b"".join(package.read(name) for name in names if name.startswith("word/header") and name.endswith(".xml"))
            footer = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn("word/footnotes.xml", names)
            footnotes = package.read("word/footnotes.xml")
        self.assertIn(b"<m:oMath", document)
        self.assertIn(b"TOC", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 4)
        self.assertIn(b"PAGE", footer)
        self.assertIn("理论框架与突破详解", header.decode("utf-8"))
        self.assertTrue(any(name.startswith("word/media/") for name in names))
        for source_id in (b"critical_manifold/results.json", b"2401840121", b"2510.01273", b"2605.29985"):
            self.assertIn(source_id, footnotes)
        self.assertIn("01-理论框架.md", footnotes.decode("utf-8"))


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
