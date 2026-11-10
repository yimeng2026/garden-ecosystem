import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "latest_digest": "41aea15ed19c68375f29877f7e22deba22394757df178cb67ca827a458a0aa75",
    "floquet_notes": "37b5436dc39bada84c3a520943ea94515d5d08e75c27e808aba5070059d48ab9",
    "eliashberg_notes": "841c1954c7fea9c41e3179476602c64b47eca936643f383e24215284324d0a20",
    "lean_markdown": "c171f6e5d5e5b6547bddc88d94138b9dc0a87d8c3a6ec59ff696e35746f59141",
    "si_template": "9d54064ba6089c82de39ddef90afeb82e47d511f95b35dd0490ee50aef63d97f",
    "lean_standalone": "1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439",
}


class RoomTempMethodsAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))

    def test_source_lineage_and_hashes(self):
        self.assertEqual(self.data["source_lineage"]["research_program_count"], 1)
        self.assertEqual(len(self.data["directions"]), 5)
        actual = {row["id"]: row["sha256"] for row in self.data["sources"]}
        self.assertEqual(actual, EXPECTED_HASHES)

    def test_floquet_pressure_mapping(self):
        rows = self.data["evidence"]["floquet"]["dfpt_estimates"]
        actual = {row["pressure_gpa"]: row["driven_tc_k"] for row in rows}
        self.assertEqual(actual, {220: 320, 250: 322})

    def test_dos_scaling_is_lower_bound(self):
        rows = self.data["evidence"]["floquet"]["dos_scaling_estimates"]
        actual = {row["pressure_gpa"]: row["driven_tc_k"] for row in rows}
        self.assertEqual(actual, {150: 285, 200: 301})
        self.assertTrue(
            all(
                row["role"] == "lower_bound_not_accurate_prediction"
                for row in rows
            )
        )

    def test_dmrg_bibliography_and_scope(self):
        row = self.data["evidence"]["dmrg"]
        self.assertEqual((row["volume"], row["article"]), (133, "256003"))
        self.assertEqual(row["max_cylinder_width"], 6)
        self.assertAlmostEqual(row["max_characteristic_tc_star_over_j"], 0.15)

    def test_lasch24_is_prediction_and_issue_26(self):
        row = self.data["evidence"]["lasc2h24"]
        self.assertEqual(row["issue"], 26)
        self.assertTrue(row["theoretical_prediction"])
        self.assertFalse(row["experimental_confirmation"])

    def test_kiessling_constant_roles(self):
        row = self.data["evidence"]["eliashberg"]
        self.assertAlmostEqual(row["sharp_constant"], 0.1827262477)
        self.assertAlmostEqual(row["upper_bound_multiplier"], 2.034)
        self.assertAlmostEqual(
            row["upper_bound_coefficient"],
            row["sharp_constant"] * row["upper_bound_multiplier"],
        )
        self.assertNotEqual(row["upper_bound_coefficient"], row["sharp_constant"])

    def test_lean_is_unverified_draft(self):
        row = self.data["evidence"]["lean"]
        self.assertEqual(row["status"], "draft_not_machine_verified")
        self.assertFalse(row["build_attempted"])
        self.assertFalse(row["build_passed"])
        self.assertGreater(row["markdown_proof_hole_count"], 0)
        self.assertEqual(
            set(row["standalone_sorry_theorems"]),
            {
                "allenDynes_weak_coupling_limit",
                "bcs_isotope_effect",
                "floquet_enhanced_tc",
            },
        )

    def test_si_is_template_and_negative_boundaries(self):
        self.assertEqual(self.data["evidence"]["si"]["status"], "template_only")
        self.assertGreater(self.data["evidence"]["si"]["placeholder_count"], 0)
        for key in (
            "global_fit",
            "material_prediction",
            "lean_proof_verified",
            "dft_inputs_available",
            "phonon_spectra_available",
            "full_repository_audit_completed",
        ):
            self.assertFalse(self.data["open_boundaries"][key])

    def test_unverified_and_out_of_scope_findings_are_registered(self):
        self.assertEqual(
            self.data["evidence"]["external_lean_metrics"]["status"],
            "unverified",
        )
        self.assertGreaterEqual(len(self.data["out_of_scope_findings"]), 3)

    def test_markdown_and_native_word_contract(self):
        markdown = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        for text in (
            "220 GPa → 320 K",
            "250 GPa → 322 K",
            "草案，不是机器证明",
            "模板，不是已完成的补充信息",
            "全库审计尚未完成",
        ):
            self.assertIn(text, markdown)
        with zipfile.ZipFile(ROOT / "REVIEW.docx") as package:
            document = package.read("word/document.xml")
            names = package.namelist()
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
        for doi in (
            b"10.1038/s41524-025-01725-z",
            b"10.1103/PhysRevLett.133.256003",
            b"10.1073/pnas.2401840121",
            b"2409.00532",
        ):
            self.assertIn(doi, footnotes)
        self.assertIn(b"<m:oMath", document)
        self.assertIn(b"TOC", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 4)
        self.assertIn(b"PAGE", footer)
        self.assertIn("室温超导", header.decode("utf-8"))


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
