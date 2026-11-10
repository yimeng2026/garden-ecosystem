import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "hydrides_overview": "5b3c56d2ea572412b894f6643fb2ab7e31e693ad7755b63e112e51c0fa46f277",
    "batch_overview": "243ef403bc372d13b442cc0086807fade7f7f478dba010bbfef2d3b9eeb11167",
    "complete_overview": "314402bf0ae374bd74200c3a8492af8727b53082062d26b3bb7eaf28f2aa4fc7",
    "technical_review": "992707a8092e65297ebe604d16d5ca203c0f2e0e32a76b43132e16133b7bea05",
    "htsc_pdf": "b1669a6771c685519a5fbcfb45258dd606b957df23720405663408f59809af01",
    "patsnap_excerpts": "4c43394d89bf1d8eb48e2a9dadb6b7396b2640f1a702f7ae87a19c65bb6d6a10",
    "boron_prb111_excerpts": "542a2bac4ad20821e68b87879c7a07a1c10128dabfe3b6e9c8207f5c51973883",
    "main_claims_review": "e9ac6ff0bc88f11b1c2c91ae61ce398a05fc077815803f48669b46536d6f2f45",
    "validation_materials_review": "17eaa27d30df6849f752e3712d563ebe492ae394ea9c74b1b072ac0755acb491",
    "isotope_dft_review": "e04428ca5980171619ca97bd2cc450fa772074cd9edd73f980905a72b1c2d4b4",
    "dmrg_qec_review": "367fada5ec9f68011ea50bb437922d140aa7fcb77bbab7517d8548196332a68d",
    "methods_review": "f30d15d8665644d11957166efaea95d59f7a742037dc697b737704cd15dc9e21",
}


class DataGovernanceAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))

    def test_source_lineage_and_directions(self):
        self.assertEqual(self.data["source_lineage"]["research_program_count"], 1)
        self.assertEqual(len(self.data["directions"]), 4)
        self.assertEqual(
            {row["id"] for row in self.data["directions"]},
            {"claim_lineage", "benchmark_scope", "data_completeness", "research_update"},
        )
        self.assertEqual({row["id"]: row["sha256"] for row in self.data["sources"]}, EXPECTED_HASHES)

    def test_song_evidence_and_circular_confirmation(self):
        row = self.data["evidence"]["song"]
        self.assertFalse(row["direct_meissner_completed"])
        self.assertFalse(row["independent_positive_replication"])
        self.assertFalse(row["first_four_standards_met"])
        self.assertFalse(row["all_five_standards_met"])
        self.assertTrue(row["duplicate_overviews_not_independent_evidence"])

    def test_htsc_scope_and_values(self):
        row = self.data["evidence"]["htsc"]
        self.assertEqual(row["sample_count"], 140)
        self.assertEqual(row["average_tc_k"], 27.3)
        self.assertEqual(row["maximum_tc_k"], 160)
        self.assertTrue(row["high_pressure_excluded"])
        self.assertTrue(row["unconventional_excluded"])
        self.assertTrue(row["leakage_exclusion_required"])
        self.assertTrue(row["open_data_available"])
        self.assertEqual(row["li2nah17_document_tc_k"], 340)
        self.assertEqual(row["li2nah17_htsc_discussion_tc_k"], 297)
        self.assertTrue(row["li2nah17_outside_benchmark"])
        self.assertTrue(row["li2nah17_requires_jiang_source"])

    def test_validation_blog_and_boron_roles(self):
        validation = self.data["evidence"]["validation"]
        self.assertTrue(validation["patsnap_secondary_blog"])
        self.assertFalse(validation["global_consensus_established"])
        self.assertEqual(validation["blog_threshold_k"], 273)
        self.assertEqual(validation["project_theorem_threshold_k"], 300)
        boron = self.data["evidence"]["boron"]
        self.assertEqual(boron["compound_count"], 96)
        self.assertEqual(boron["ca_b8c_predicted_tc_k"], 77.1)
        self.assertFalse(boron["experimental_realization"])

    def test_kruglov_pressure_and_data_completeness(self):
        row = self.data["evidence"]["kruglov"]
        self.assertEqual(row["article"], "024508")
        self.assertEqual(row["nf_unit"], "states/f.u./Ry")
        self.assertFalse(row["nf_unit_states_per_ev"])
        self.assertFalse(row["full_spectrum_and_inputs_open"])
        pressure = self.data["evidence"]["pressure"]
        self.assertTrue(pressure["mixed_method_curve"])
        self.assertFalse(pressure["experimental_curve_established"])

    def test_research_updates_and_qec_propagation(self):
        dmrg = self.data["evidence"]["research_update"]["dmrg"]
        self.assertEqual(dmrg["chen_legs"], 8)
        self.assertFalse(dmrg["thermodynamic_limit_proven"])
        self.assertFalse(dmrg["static_all_controversy_only"])
        qec = self.data["evidence"]["research_update"]["qec"]
        self.assertFalse(qec["google_absolute_first_supported"])
        self.assertFalse(qec["neutral_48_ldpc_distance7"])

    def test_governance_and_open_boundaries(self):
        self.assertEqual(len(self.data["corrections"]), 10)
        self.assertTrue(self.data["evidence"]["governance"]["completed_status_not_evidence"])
        self.assertTrue(self.data["evidence"]["governance"]["duplicates_not_independent"])
        for key in (
            "meissner_verified",
            "first_four_standards_met",
            "htsc_high_pressure_included",
            "boron_experimental_realization",
            "full_spectrum_open",
            "all_overview_claims_checked",
            "full_repository_audit",
        ):
            self.assertFalse(self.data["open_boundaries"][key])

    def test_figure_scope(self):
        for label in ("140", "27.3 K", "77.1 K", "[[8,3,2]]", "直接 Meissner 未确立"):
            self.assertIn(label, self.data["figure"]["labels"])
        self.assertFalse(self.data["figure"]["verification_percentage_plotted"])

    def test_markdown_and_native_word_contract(self):
        markdown = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        for text in ("140 个样本", "27.3 K", "77.1 K", "024508", "图 1", "全库审计尚未完成"):
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
        self.assertIn("总览与技术复盘", header.decode("utf-8"))
        self.assertTrue(any(name.startswith("word/media/") for name in names))
        for source_id in ("2506.03837", "014510", "2510.01273", "024508", "12-资料收集-氢化物与验证进展.md", "16-资料收集-总览与下一步.md", "20-资料收集-总览与完整清单.md", "21-技术复盘-全领域数据审计.md"):
            self.assertIn(source_id, footnotes)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
