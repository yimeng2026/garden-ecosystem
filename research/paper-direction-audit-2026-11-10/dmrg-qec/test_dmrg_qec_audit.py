import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "dmrg_notes": "59e6b00f0cb240b9b0d3417f0f7906ae0fb5cf4a9b7cbcf79a8229181147d392",
    "qec_notes": "59e747f55a96fd8d93885455d7ae7c2579acdeff4139e292023f5a723ec3fce2",
    "stripes_pdf": "d37490cd24da075fd622ef48bc3f212ce35fa09ec8db8bcd737a7fe4b04e1531",
    "finite_temperature_pdf": "e1ce8e1480fcf95156b7fffd23800b2b8dc4d6def9b64afb5835903cca3ae107",
    "extended_hubbard_pdf": "2cbaa6cd2ec3e9b00a61627d23cf3f5e3f5ac022b1cd80d73e495028646a7a55",
    "global_dwave_html": "3c2a77b1550f35e8a8eb8870150872cdc5e7b80c3ddd1d2799f9f455d3a2daca",
    "google_pdf": "9ba05a64dfec13f5d733e0e22484e8f22db2482dc2a5a0d63e6f0766c9c3d368",
    "xzzx_pdf": "918860f120639eb6897faff9d834aa977fbf54f781522276bff17c88c8db0cb7",
    "neutral_atoms_pdf": "0b81702eedfd2525eb6ab74fe82f43a7dbc930a219298f1f21c7ee7698afa8e7",
}


class DmrgQecAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))

    def test_source_lineage_and_directions(self):
        self.assertEqual(self.data["source_lineage"]["research_program_count"], 1)
        self.assertEqual(len(self.data["directions"]), 4)
        self.assertEqual(
            {row["id"] for row in self.data["directions"]},
            {"dmrg_evidence_ladder", "extended_model_completion", "qec_benchmark_roles", "cross_domain_governance"},
        )
        self.assertEqual({row["id"]: row["sha256"] for row in self.data["sources"]}, EXPECTED_HASHES)

    def test_dmrg_evidence_ladder(self):
        rows = self.data["evidence"]["dmrg"]
        self.assertEqual(rows["finite_temperature"]["max_width"], 6)
        self.assertAlmostEqual(rows["finite_temperature"]["min_temperature_t_over_j"], 0.06)
        self.assertTrue(rows["finite_temperature"]["positive_t_prime_dome"])
        self.assertTrue(rows["finite_temperature"]["negative_t_prime_weaker"])
        self.assertFalse(rows["finite_temperature"]["infinite_2d_ground_state_proof"])
        global_row = rows["global_ground_state"]
        self.assertEqual(global_row["legs"], 8)
        self.assertEqual(global_row["uniform_abs_t2_over_t1"], 0.15)
        self.assertTrue(global_row["pure_tj_dwave"])
        self.assertTrue(global_row["gce_natural_ground_state"])
        self.assertTrue(global_row["code_data_available"])
        self.assertFalse(global_row["thermodynamic_limit_proven"])
        self.assertEqual(global_row["pnas_year"], 2025)
        self.assertEqual(global_row["document_year"], 2024)

    def test_stripes_and_extended_model(self):
        stripes = self.data["evidence"]["stripes"]
        self.assertEqual(stripes["dwave_reference_ids"], [43, 44])
        self.assertEqual(stripes["cdw_reference_ids"], [41, 42])
        self.assertTrue(stripes["document_mapping_reversed"])
        self.assertAlmostEqual(stripes["energy_difference_t"], 0.01)
        extended = self.data["evidence"]["extended_hubbard"]
        self.assertEqual(extended["article"], "L201102")
        self.assertEqual(extended["legs"], 4)
        self.assertTrue(extended["current_dwave_enhancement"])
        self.assertFalse(extended["current_pwave_result"])
        self.assertTrue(extended["previous_1d_pwave"])

    def test_qec_noise_and_google(self):
        xzzx = self.data["evidence"]["qec"]["xzzx"]
        self.assertEqual(xzzx["depolarizing_threshold"], 0.187)
        self.assertEqual(xzzx["pure_pauli_threshold"], 0.5)
        self.assertFalse(xzzx["cross_decoder_threshold_comparison_valid"])
        google = self.data["evidence"]["qec"]["google"]
        self.assertEqual(google["distances"], [5, 7])
        self.assertEqual(google["lambda"], 2.14)
        self.assertEqual(google["latency_us"], 63)
        self.assertFalse(google["first_below_threshold_claim_supported"])
        self.assertTrue(google["prior_surface_code_2023"])

    def test_neutral_atoms_and_cross_domain(self):
        row = self.data["evidence"]["qec"]["neutral_atoms"]
        self.assertEqual(row["year"], 2024)
        self.assertEqual(row["logical_48_code"], "3D [[8,3,2]]")
        self.assertTrue(row["distance7_surface_bell_pairs"])
        self.assertFalse(row["logical_48_ldpc_distance7"])
        cross = self.data["evidence"]["cross_domain"]
        self.assertFalse(cross["ldpc_universal_overhead_and_decoding"])
        self.assertFalse(cross["vortex_qubit_experimental_evidence"])
        self.assertFalse(cross["double_fault_tolerance_proven"])

    def test_corrections_and_open_boundaries(self):
        self.assertEqual(len(self.data["corrections"]), 9)
        for key in (
            "dmrg_2d_limit_proven",
            "qec_threshold_cross_model_comparable",
            "neutral_48_ldpc_d7_verified",
            "vortex_qubit_verified",
            "all_citations_checked",
            "full_repository_audit",
        ):
            self.assertFalse(self.data["open_boundaries"][key])

    def test_figure_scope(self):
        for label in ("8-leg", "18.7%", "63 μs", "[[8,3,2]]", "distance-7 LDPC"):
            self.assertIn(label, self.data["figure"]["labels"])
        self.assertFalse(self.data["figure"]["success_percentage_plotted"])

    def test_markdown_and_native_word_contract(self):
        markdown = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        for text in ("8-leg", "18.7%", "63 μs", "[[8,3,2]]", "图 1", "全库审计尚未完成"):
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
        self.assertIn("DMRG 与量子纠错", header.decode("utf-8"))
        self.assertTrue(any(name.startswith("word/media/") for name in names))
        for source_id in ("2501.15709", "2311.15092", "2206.03486", "2408.13687", "[[8,3,2]]", "14-资料收集-DMRG-Hubbard模型.md", "18-资料收集-量子纠错码进展.md"):
            self.assertIn(source_id, footnotes)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
