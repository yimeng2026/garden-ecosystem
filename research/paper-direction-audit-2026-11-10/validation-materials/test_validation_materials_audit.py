import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "validation_report": "51a4709522000dca521dcecd071f20766763821eca94cb9e279335ea91f47e90",
    "material_predictions": "050b52aa56bb633fd1db95e198f9804085de26080f4b18f135f44e3c8ef326ef",
    "numeric_spotcheck": "c11de34cb4f238e9c837effb735ebc9629921ea9494af28d474d75fddcee95d9",
    "primary_excerpts": "62cf61470cc7be0d17ee5e53a7e9f01b8cf8013c009698526aeafdcf5c281528",
}


class ValidationMaterialsAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))

    def test_source_lineage_and_directions(self):
        self.assertEqual(self.data["source_lineage"]["research_program_count"], 1)
        self.assertEqual(len(self.data["directions"]), 4)
        actual = {row["id"]: row["sha256"] for row in self.data["sources"]}
        self.assertEqual(actual, EXPECTED_HASHES)

    def test_numeric_spotcheck(self):
        rows = self.data["evidence"]["formula_spotcheck"]
        self.assertAlmostEqual(rows["h3s"]["computed_tc_k"], 161.081843791778823)
        self.assertAlmostEqual(rows["h3s"]["claimed_tc_k"], 203.0)
        self.assertAlmostEqual(rows["h_s_cl"]["computed_tc_k"], 237.894818964651591)
        self.assertAlmostEqual(rows["h_s_cl"]["claimed_tc_k"], 320.0)
        self.assertFalse(rows["h_s_cl"]["is_first_principles_result"])

    def test_lanio2_doping_scope(self):
        row = self.data["evidence"]["lanio2"]
        self.assertEqual(row["superconducting_dome"], [0.15, 0.3])
        self.assertTrue(row["undoped_insulating"])
        self.assertFalse(row["undoped_tc_20_40_verified"])

    def test_grockowiak_role(self):
        row = self.data["evidence"]["grockowiak"]
        self.assertEqual(row["initial_tc_k"], 294)
        self.assertEqual(row["maximum_onset_tc_k"], 556)
        self.assertTrue(row["irreversible_higher_order"])
        self.assertFalse(row["meissner_completed"])
        self.assertFalse(row["binary_lah10_routine_validation"])

    def test_cl_doping_direction(self):
        rows = self.data["evidence"]["cl_doping"]["results"]
        self.assertEqual([row["tc_k"] for row in rows], [161, 136])
        self.assertTrue(all(row["pressure_gpa"] == 200 for row in rows))
        self.assertTrue(self.data["evidence"]["cl_doping"]["lowers_stabilization_pressure"])
        self.assertFalse(self.data["evidence"]["cl_doping"]["supports_320k_prediction"])

    def test_scoring_and_open_boundaries(self):
        self.assertFalse(self.data["evidence"]["scoring"]["rubric_available"])
        for key in (
            "global_fit",
            "first_principles_recomputed",
            "prediction_replaced",
            "experimental_verification",
            "full_document_source_audit",
            "full_repository_audit",
        ):
            self.assertFalse(self.data["open_boundaries"][key])

    def test_markdown_and_native_word_contract(self):
        markdown = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        for text in (
            "不是材料预测",
            "未掺杂薄膜绝缘",
            "全库审计尚未完成",
            "图 1",
        ):
            self.assertIn(text, markdown)
        with zipfile.ZipFile(ROOT / "REVIEW.docx") as package:
            names = package.namelist()
            document = package.read("word/document.xml")
            header = b"".join(
                package.read(name)
                for name in names
                if name.startswith("word/header") and name.endswith(".xml")
            )
            footer = b"".join(
                package.read(name)
                for name in names
                if name.startswith("word/footer") and name.endswith(".xml")
            )
            self.assertIn("word/footnotes.xml", names)
            footnotes = package.read("word/footnotes.xml")
        self.assertIn(b"<m:oMath", document)
        self.assertIn(b"TOC", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 4)
        self.assertIn(b"PAGE", footer)
        self.assertIn("实验验证与材料预测", header.decode("utf-8"))
        self.assertTrue(any(name.startswith("word/media/") for name in names))
        for source_id in (
            b"femat.2022.837651",
            b"PMC8856608",
            b"1804.08224",
            b"numeric_spotcheck.py",
        ):
            self.assertIn(source_id, footnotes)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
