import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "main_master": "862e3232520ee961bc307a8e97cfd0b32a869a97197b159281596be3437d227f",
    "nature_version": "fc5505cff6e3f65ee080ae4ec7a8f51f8ea2b4404e33a0d59146122bf91c568c",
    "science_version": "598de079d503596b9c9a5d43ba5027fafc5d9a13a12c4b3b03a3ba3e36d2e809",
    "arxiv_version": "7893cc30f25baca9aef27a3a3f9fc1a232e86fafdde109753885487f9268fc3b",
    "handbook_materials": "2816948242751325c7d3d28995f1ce836fb064e426f7d2bc941df3b14c8d5acd",
    "handbook_future": "43e7826fac1fd4260e1cf0c01bf2ba6c1ffd6616652bb9b8825ea4fa006443bd",
    "critical_results": "f9438c770c1125c68b42a67778458d551f3694d1954b112bdf61d6942bac970b",
    "prior_methods_review": "cc73b74ad9951d6b0d25dee50ac06babd8f8ea2ffdde8a4823923d506cc466f7",
    "song_pdf": "b820d4dac9162c0f8b914282afbbbe85e7005bce68c7b217abff070a715debdf",
    "semenok_pdf": "a1dc4c13ecf800baf422e97aa51ba004b85ec7e6e32ecc7bf9f850df39a09bef",
}


class MainClaimsAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))

    def test_source_lineage_hashes_and_directions(self):
        self.assertEqual(self.data["source_lineage"]["research_program_count"], 1)
        self.assertEqual(len(self.data["directions"]), 4)
        actual = {row["id"]: row["sha256"] for row in self.data["sources"]}
        self.assertEqual(actual, EXPECTED_HASHES)

    def test_song_positive_preprint_scope(self):
        row = self.data["evidence"]["song"]
        self.assertTrue(row["exists"])
        self.assertTrue(row["reports_experimental_synthesis"])
        self.assertEqual(row["onset_tc_k"], [271, 298])
        self.assertEqual(row["pressure_gpa"], [195, 266])
        self.assertEqual(row["reproducible_runs_reported"], 13)
        self.assertFalse(row["peer_review_established"])
        self.assertFalse(row["independent_positive_replication"])
        self.assertFalse(row["direct_meissner_completed"])

    def test_semenok_negative_replication_scope(self):
        row = self.data["evidence"]["semenok"]
        self.assertTrue(row["exists"])
        self.assertEqual(row["unsuccessful_attempts"], 7)
        self.assertEqual(row["synthesis_pressure_gpa"], [250, 280])
        self.assertEqual(row["no_superconductivity_range_k"], [245, 300])
        self.assertTrue(row["theoretical_tc_above_300_at_300_gpa"])

    def test_controversy_and_open_boundaries(self):
        self.assertTrue(self.data["evidence"]["controversy"]["contested_evidence"])
        for key in (
            "formal_proof_completed",
            "lean_proof_verified",
            "si_complete",
            "peer_review_established",
            "independent_positive_replication",
            "direct_meissner_completed",
            "success_rate_100_supported",
            "ultimate_necessity_proven",
            "full_repository_audit_completed",
        ):
            self.assertFalse(self.data["open_boundaries"][key])

    def test_confirmed_nature_citation_mismatch(self):
        row = self.data["evidence"]["nature_citation"]
        self.assertTrue(row["citation_mismatch"])
        self.assertEqual(
            row["actual_title"],
            "Twisted-layer boron nitride ceramic with high deformability and strength",
        )
        self.assertEqual(row["actual_doi"], "10.1038/s41586-024-07036-5")
        self.assertEqual(row["actual_pages"], "779-784")

    def test_counterexample_scope(self):
        row = self.data["evidence"]["critical_manifold"]
        self.assertEqual(row["root_count"], 936)
        self.assertEqual(row["grid_point_count"], 38376)
        self.assertEqual(row["grid_class_disagreements"], 0)
        self.assertTrue(all(anchor["tc_K"] < 300 for anchor in row["temperature_anchors"]))
        self.assertFalse(row["full_eliashberg_theory_refuted"])

    def test_lean_and_si_debt(self):
        lean = self.data["evidence"]["formalization"]
        si = self.data["evidence"]["si"]
        self.assertEqual(lean["markdown_proof_hole_count"], 48)
        self.assertEqual(lean["standalone_sorry_count"], 3)
        self.assertFalse(lean["build_passed"])
        self.assertEqual(si["placeholder_count"], 31)
        self.assertEqual(si["status"], "template_only")

    def test_handbook_narrative_boundaries(self):
        row = self.data["evidence"]["handbook_narrative"]
        self.assertFalse(row["success_rate_100_supported"])
        self.assertEqual(row["anecdote_status"], "unverified")
        self.assertFalse(row["direct_meissner_completed"])
        self.assertFalse(row["ultimate_necessity_proven"])

    def test_prior_audit_addendum_and_direction_roles(self):
        self.assertTrue(self.data["prior_audit_addendum"]["required"])
        self.assertTrue(self.data["prior_audit_addendum"]["pnas_prediction_role_unchanged"])
        self.assertTrue(self.data["prior_audit_addendum"]["song_was_missing"])
        self.assertTrue(self.data["prior_audit_addendum"]["semenok_was_missing"])

    def test_markdown_and_native_word_contract(self):
        markdown = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        for text in (
            "正向实验预印本与独立负向复现并存",
            "不是真伪投票",
            "不是 2024 年 Nature 论文",
            "成功率 100% 不受支持",
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
        self.assertGreaterEqual(document.count(b"<w:cantSplit"), 30)
        self.assertIn(b"PAGE", footer)
        self.assertIn("主论文与手册", header.decode("utf-8"))
        self.assertTrue(any(name.startswith("word/media/") for name in names))
        for source_id in (
            b"2401840121",
            b"2510.01273",
            b"2605.29985",
            b"07036-5",
            b"critical_manifold",
        ):
            self.assertIn(source_id, footnotes)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
