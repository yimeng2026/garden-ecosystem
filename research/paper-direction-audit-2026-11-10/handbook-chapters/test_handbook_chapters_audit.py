import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "handbook_intro": "bb67c6d7b57a2dad1f42eed1bd2729697e590c643953e05e19ca0a7016463d23",
    "handbook_theorem": "062b0011cc45b34ed8545a5890769ca71382608b09371641af5a51060c476e97",
    "physics_foundations": "93dd0cc19dc0b72c3103c607ded0a513837f664b3aaa872150e9bcb0a7d1c13e",
    "main_claims_review": "e9ac6ff0bc88f11b1c2c91ae61ce398a05fc077815803f48669b46536d6f2f45",
    "theory_review": "e6acb59a95f4dc159db2692e5db0a6ae40d640f8a8aef04ca1b69da80e3ed8c8",
    "data_governance_review": "e09aeb77dd254d061d980c306e6762c1ef21ad8a5e826be6a08226d581680aa8",
}


class HandbookChaptersAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))

    def test_source_lineage_and_directions(self):
        self.assertEqual(self.data["source_lineage"]["research_program_count"], 1)
        self.assertEqual(len(self.data["directions"]), 4)
        self.assertEqual(
            {row["id"] for row in self.data["directions"]},
            {"pedagogical_physics", "conditional_model", "experimental_roles", "unit_provenance"},
        )
        self.assertEqual({row["id"]: row["sha256"] for row in self.data["sources"]}, EXPECTED_HASHES)

    def test_formula4_and_correct_example(self):
        bad = self.data["evidence"]["formula4"]
        self.assertAlmostEqual(bad["computed_tc_k"], 259.594501207478)
        self.assertEqual(bad["claimed_tc_k"], 326)
        self.assertFalse(bad["claim_supported"])
        good = self.data["evidence"]["correct_example"]
        self.assertAlmostEqual(good["computed_tc_k"], 326.617107973496)
        self.assertEqual(good["claimed_tc_k"], 326)
        self.assertTrue(good["rounding_supported"])
        self.assertAlmostEqual(self.data["evidence"]["threshold_lambda25"]["computed_theta_d_k"], 2426.861882935184)

    def test_frequency_temperature_conversion(self):
        rows = self.data["evidence"]["units"]
        self.assertAlmostEqual(rows["omega_210_mev_k"], 2436.948806, places=5)
        self.assertAlmostEqual(rows["omega_150_mev_k"], 1740.677718, places=5)
        self.assertFalse(rows["theta_d_2100_is_omega_max_210_mev"])

    def test_condition_sets_and_model_scope(self):
        row = self.data["evidence"]["conditions"]
        self.assertEqual(row["original_lambda"], ">2")
        self.assertEqual(row["theorem_lambda"], ">=2.5")
        self.assertEqual(row["original_phonon_mev"], 150)
        self.assertEqual(row["theorem_theta_d_k"], 1800)
        self.assertFalse(row["sets_equivalent"])
        self.assertFalse(row["quasi_2d_used_in_proof"])
        self.assertTrue(row["simplified_model_sufficient_condition"])
        self.assertFalse(row["physical_necessity_proven"])

    def test_experimental_roles(self):
        row = self.data["evidence"]["experiment"]
        self.assertEqual(row["song_onset_max_k"], 298)
        self.assertLess(row["song_onset_max_k"], 300)
        self.assertFalse(row["direct_meissner_completed"])
        self.assertFalse(row["independent_positive_replication"])
        self.assertTrue(row["semenok_negative_replication_exists"])
        self.assertFalse(row["p6mmm_automatically_quasi_2d"])
        self.assertFalse(row["liu_and_song_same_author_list"])

    def test_intro_pedagogy(self):
        row = self.data["evidence"]["intro"]
        self.assertEqual(row["year_1986_tc_k"], 35)
        self.assertEqual(row["year_1987_tc_k"], 93)
        self.assertEqual(row["liquid_nitrogen_k"], 77)
        self.assertEqual(row["correct_chemical_formula"], "H₃S")
        self.assertFalse(row["mcmillan_universal_cap"])
        self.assertFalse(row["cooper_pairs_simple_boson_gas"])

    def test_corrections_and_open_boundaries(self):
        self.assertEqual(len(self.data["corrections"]), 8)
        for key in (
            "formula4_verified",
            "three_conditions_proven",
            "theta_d_source_closed",
            "experimental_necessity_proven",
            "all_intro_facts_checked",
            "full_repository_audit",
        ):
            self.assertFalse(self.data["open_boundaries"][key])

    def test_figure_scope(self):
        for label in ("259.594501", "326.617108", "298 K", "准二维", "H₃S"):
            self.assertIn(label, self.data["figure"]["labels"])
        self.assertFalse(self.data["figure"]["verification_percentage_plotted"])

    def test_markdown_and_native_word_contract(self):
        markdown = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        for text in ("259.594501", "326.617108", "2436.948806", "图 1", "全库审计尚未完成"):
            self.assertIn(text, markdown)
        with zipfile.ZipFile(ROOT / "REVIEW.docx") as package:
            names = package.namelist()
            document = package.read("word/document.xml")
            header = b"".join(package.read(name) for name in names if name.startswith("word/header") and name.endswith(".xml"))
            footer = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn("word/footnotes.xml", names)
            footnotes = package.read("word/footnotes.xml").decode("utf-8")
        self.assertIn(b"<m:oMath", document)
        self.assertIn(b"TOC", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 5)
        self.assertIn(b"PAGE", footer)
        self.assertIn("手册第 1–3 章", header.decode("utf-8"))
        self.assertTrue(any(name.startswith("word/media/") for name in names))
        for source_id in ("108.1175", "167.331", "2510.01273", "01-第1-2章_超导入门与科普.md", "02-第3章_必然性定理.md"):
            self.assertIn(source_id, footnotes)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
