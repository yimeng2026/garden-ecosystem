import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "directory_index": "633844466f9c1fad0929a5250380a7e0467b7a458c24dc9006d820071dcad317",
    "project_intro": "ddab8da04e8373fccedacc4634dfee09c7fc4be8eee5064e050f162f6bee4164",
    "handbook_intro": "dd6721843deed0ad442b5ec3fc53303d4c895b6638d5d3dd5eb8b207b166161a",
    "magazine_plan": "7f691b8f56f4d7ff04d4a3b3090cc4b48974fd7da89922ddeb8597bd046c34aa",
    "base_bib": "ca014a4bae5023081149a1c4d051917e7f0540df18241400992c2b2276d43698",
    "enhanced_bib": "d4a7d80243bc2fec0b05af4b0c9519d1be86edd0a62cd0d3d82b94a912ab870f",
    "original_readme": "8eca2b541eb2412517af4ed28feafb301a29caeac960b6dede08be3717e1b9ff",
    "handbook_task": "e520e11faa500339ceac76c324bddbcae9c6de16908d299fa832cfd7f85edec7",
    "handbook_docx": "c2b77fa2b705b634a19f9959015acc990f663ba41d0b116bc6b48a37aa451b50",
    "main_claims_review": "e9ac6ff0bc88f11b1c2c91ae61ce398a05fc077815803f48669b46536d6f2f45",
    "theory_review": "e6acb59a95f4dc159db2692e5db0a6ae40d640f8a8aef04ca1b69da80e3ed8c8",
    "validation_review": "17eaa27d30df6849f752e3712d563ebe492ae394ea9c74b1b072ac0755acb491",
    "isotope_review": "e04428ca5980171619ca97bd2cc450fa772074cd9edd73f980905a72b1c2d4b4",
    "dmrg_review": "367fada5ec9f68011ea50bb437922d140aa7fcb77bbab7517d8548196332a68d",
    "data_review": "e09aeb77dd254d061d980c306e6762c1ef21ad8a5e826be6a08226d581680aa8",
    "handbook_review": "0394b996c271a6ca24b4692d7bd078b4c0fa8925eefde6df0347a478f298ac48",
    "methods_review": "f30d15d8665644d11957166efaea95d59f7a742037dc697b737704cd15dc9e21",
    "technical_review": "d27fca5597387c24e9d0038e971055566522441a1f1f1dd8a0dd7dfe662e305f",
    "magazine_review": "f025cef1935a604b67fe1c0504d6cdfc377ab2c69db450d3fd2da6034364b3bb",
}


class ProjectIntroAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))

    def test_source_freeze(self):
        self.assertEqual(len(self.data["sources"]), 19)
        self.assertEqual({row["id"]: row["sha256"] for row in self.data["sources"]}, EXPECTED_HASHES)

    def test_coverage_44_unique_and_complete(self):
        coverage = self.data["coverage"]
        self.assertEqual(coverage["actual_markdown_count"], 44)
        self.assertEqual(coverage["prior_covered_count"], 40)
        self.assertEqual(coverage["current_batch_count"], 4)
        self.assertEqual(coverage["covered_count"], 44)
        self.assertEqual(coverage["uncovered"], [])
        self.assertEqual(coverage["duplicates"], [])
        self.assertEqual(coverage["batch_review_count"], 10)
        self.assertEqual(len(coverage["rows"]), 44)
        self.assertEqual(len({row["path"] for row in coverage["rows"]}), 44)
        self.assertTrue(coverage["organized_44_coverage_complete"])
        self.assertFalse(coverage["whole_repository_research_complete"])

    def test_directions_and_final_documents(self):
        self.assertEqual(self.data["source_lineage"]["research_program_count"], 1)
        self.assertEqual(self.data["source_lineage"]["new_theory_count"], 0)
        self.assertEqual(len(self.data["directions"]), 4)
        self.assertEqual(
            {row["id"] for row in self.data["directions"]},
            {"coverage_governance", "conditional_formalization", "handbook_reference_governance", "public_communication"},
        )
        self.assertEqual(len(self.data["document_assessments"]), 4)
        for row in self.data["document_assessments"]:
            self.assertFalse(row["represents_new_theory"])
            self.assertTrue(row["direction_ids"])
            self.assertTrue(row["unfinished"])
            self.assertTrue(row["next"])

    def test_index_and_reference_evidence(self):
        index = self.data["evidence"]["index"]
        self.assertEqual(index["omitted_top_level_groups"], [str(number) for number in range(12, 22)])
        self.assertTrue(index["prl_claimed"])
        self.assertFalse(index["prl_found"])
        references = self.data["evidence"]["references"]
        self.assertEqual(references["base_entries"], 24)
        self.assertEqual(references["base_placeholders"], 5)
        self.assertEqual(references["enhanced_bytes"], 22)
        self.assertEqual(references["enhanced_entries"], 0)
        self.assertEqual(references["missing_modern_identifiers"], ["2510.01273", "2605.29985", "2401840121"])
        self.assertFalse(references["enhanced_usable"])

    def test_formalization_version_and_handbook_assets(self):
        formal = self.data["evidence"]["formalization"]
        self.assertFalse(formal["theoretical_framework_found"])
        self.assertFalse(formal["expected_lean_found"])
        self.assertEqual(formal["m1_m5_modules_found"], 0)
        self.assertTrue(formal["sorry_present"])
        self.assertTrue(formal["no_error_claim"])
        self.assertTrue(formal["readme_version_mismatch"])
        timeline = self.data["evidence"]["timeline"]
        self.assertTrue(timeline["handbook_update_precedes_october_breakthrough"])
        handbook = self.data["evidence"]["handbook_asset"]
        self.assertTrue(handbook["exists"])
        self.assertEqual(handbook["bytes"], 44510)
        self.assertEqual(handbook["app_pages"], 1)
        self.assertEqual(handbook["app_words"], 0)
        self.assertEqual(handbook["media_files"], 0)
        self.assertFalse(handbook["has_omml"])
        self.assertFalse(handbook["approx_50_pages_verified"])

    def test_corrections_and_dual_boundaries(self):
        self.assertEqual(len(self.data["corrections"]), 12)
        self.assertEqual(len({row["id"] for row in self.data["corrections"]}), 12)
        self.assertTrue(self.data["open_boundaries"]["organized_44_coverage_complete"])
        for key in (
            "scientific_validation_complete",
            "all_unfinished_work_completed",
            "index_updated",
            "reference_library_ready",
            "lean_proof_complete",
            "production_ready",
            "whole_repository_research_complete",
        ):
            self.assertFalse(self.data["open_boundaries"][key])
        self.assertFalse(self.data["verification_scope"]["source_documents_modified"])
        self.assertGreater(self.data["coverage"]["prior_open_false_items"], 0)

    def test_deliverables_and_native_word(self):
        markdown = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        for text in ("44／44", "40＋4", "24 条", "0 条", "图 1", "覆盖完成不等于研究闭合"):
            self.assertIn(text, markdown)
        self.assertIn("44／44", self.data["figure"]["labels"])
        self.assertIn("增强 BibTeX 0 条", self.data["figure"]["labels"])
        with zipfile.ZipFile(ROOT / "REVIEW.docx") as package:
            names = package.namelist()
            document = package.read("word/document.xml")
            header = b"".join(package.read(name) for name in names if name.startswith("word/header") and name.endswith(".xml"))
            footer = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn("word/footnotes.xml", names)
        self.assertIn(b"<m:oMath", document)
        self.assertIn(b"TOC", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 7)
        self.assertIn(b"PAGE", footer)
        self.assertIn("目录与项目介绍", header.decode("utf-8"))
        self.assertTrue(any(name.startswith("word/media/") for name in names))


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
