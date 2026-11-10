"""Contract for the Floquet resonance-to-critical-temperature evidence audit."""

import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RESEARCH = ROOT.parent
ORIGINAL = Path(
    "C:/Users/一梦/Documents/kimi/workspace/toe-sylva-audit/"
    "papers/room_temp_sc/room_temp_sc_Formalization.lean"
)
XIE = (
    RESEARCH
    / "paper-direction-audit-2026-11-10"
    / "room-temp-methods"
    / "sources"
    / "xie-floquet-fulltext.txt"
)
ORIGINAL_SHA256 = "1971e95d7b375c24778d3adae8a1ab3be4c5abeb1ee8b79a2b1f347b7aa00439"


class FloquetEvidenceBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "evidence.json").read_text(encoding="utf-8"))

    def test_sources_are_immutable_and_traceable(self):
        sources = {row["id"]: row for row in self.data["sources"]}
        self.assertEqual(hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(), ORIGINAL_SHA256)
        self.assertEqual(sources["original_lean"]["sha256"], ORIGINAL_SHA256)
        self.assertEqual(sources["xie_2025"]["sha256"], hashlib.sha256(XIE.read_bytes()).hexdigest())
        self.assertEqual(sources["xie_2025"]["doi"], "10.1038/s41524-025-01725-z")
        self.assertFalse(sources["original_lean"]["modified"])

    def test_resonance_has_no_modeled_tc_relation(self):
        original = self.data["original_theorem"]
        self.assertEqual(original["name"], "floquet_enhanced_tc")
        self.assertEqual(original["source_lines"], [171, 185])
        self.assertEqual(original["status"], "proof_debt_not_a_physical_theorem")
        self.assertTrue(original["bare_existential_trivially_inhabitable"])
        self.assertEqual(original["trivial_witness"], "T_c_eq + 1")
        self.assertFalse(original["intended_physical_claim_follows_from_premise"])
        self.assertFalse(original["countermodel_is_physical_evidence"])
        self.assertEqual(original["countermodel"]["t_c_eq_k"], 250)
        self.assertEqual(original["countermodel"]["t_c_f_k"], 200)
        self.assertTrue(original["countermodel"]["resonance_exact"])
        self.assertEqual(original["countermodel"]["scope"], "stronger_material_response_relation_not_formalized_in_original")
        self.assertIn("Tc_as_a_function_of_drive_and_material", original["missing_premises"])
        self.assertIn("positive_planck_constant", original["missing_premises"])

    def test_checked_paper_is_off_resonant_not_two_gap_resonance(self):
        assumptions = self.data["xie_model_assumptions"]
        self.assertEqual(assumptions["photon_energy_mev"], 400)
        self.assertEqual(assumptions["laser_wavelength_um"], 3)
        self.assertEqual(assumptions["drive_regime"], "off_resonant_lowest_order_floquet")
        self.assertEqual(assumptions["tc_estimator"], "Allen-Dynes")
        self.assertFalse(assumptions["two_gap_resonance_used_to_derive_tc"])
        self.assertEqual(assumptions["nonthermal_distribution_scope"], "checked_finite_order_assumption_not_general_proof")

    def test_pressure_and_estimator_roles_are_not_conflated(self):
        rows = self.data["xie_tc_estimates"]
        actual = {row["pressure_gpa"]: row for row in rows}
        self.assertEqual(set(actual), {150, 200, 220, 250})
        self.assertEqual((actual[220]["equilibrium_k"], actual[220]["driven_k"]), (258, 320))
        self.assertEqual((actual[250]["equilibrium_k"], actual[250]["driven_k"]), (237, 322))
        self.assertEqual((actual[150]["equilibrium_k"], actual[150]["driven_k"]), (249, 285))
        self.assertEqual((actual[200]["equilibrium_k"], actual[200]["driven_k"]), (240, 301))
        for pressure in (220, 250):
            self.assertEqual(actual[pressure]["role"], "direct_floquet_dfpt_allen_dynes_estimate")
        for pressure in (150, 200):
            self.assertEqual(actual[pressure]["role"], "dos_scaling_lower_bound_claim_not_general_bound")
            self.assertFalse(actual[pressure]["accurate_prediction"])
        self.assertAlmostEqual(actual[220]["reported_increase_percent"], 25)
        self.assertAlmostEqual(actual[250]["reported_increase_percent"], 35)
        self.assertNotAlmostEqual((320 - 258) / 258 * 100, 25)
        self.assertNotAlmostEqual((322 - 237) / 237 * 100, 35)

    def test_limitations_and_negative_boundaries_remain_open(self):
        limitations = self.data["limitations"]
        for name in (
            "nonthermal_steady_state_experimental_challenge",
            "fixed_equilibrium_phonons",
            "finite_order_electronic_distribution",
            "multireference_dft",
            "strong_coupling_quantum_fluctuations",
            "experimental_confirmation",
            "independent_reproduction",
        ):
            self.assertIn(name, limitations)
        self.assertEqual(self.data["conclusion"]["resonance_enhancement"], "not_derived")
        self.assertEqual(self.data["conclusion"]["resonance_enhancement_disproved_experimentally"], False)
        self.assertEqual(self.data["conclusion"]["xie_material_estimates_experimentally_confirmed"], False)
        self.assertFalse(self.data["conclusion"]["physics_proof_complete"])

    def test_verbatim_evidence_is_really_in_the_local_primary_text(self):
        # Match the audit's LF numbering; PDF form feeds are not extra lines.
        source_lines = XIE.read_text(encoding="utf-8").split("\n")
        anchors = self.data["source_anchors"]
        self.assertGreaterEqual(len(anchors), 8)
        for row in anchors:
            start, end = row["lines"]
            excerpt = re.sub(r"\s+", " ", " ".join(source_lines[start - 1 : end]))
            self.assertIn(re.sub(r"\s+", " ", row["quote"]), excerpt, row["id"])

    def test_readme_separates_logic_countermodel_from_physics(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for required in (
            "非共振",
            "400 meV",
            "不能推出",
            "逻辑反模型不是物理反证",
            "DOS-scaling",
            "未完成实验验证",
            "不是 Floquet 增强证明",
        ):
            self.assertIn(required, text)
        approximation = (RESEARCH / "lean-proof-slice" / "FloquetApproximation.lean").read_text(encoding="utf-8")
        self.assertNotIn("floquet_enhanced_tc", approximation)
        self.assertNotRegex(approximation, r"(?m)^\s*(axiom|postulate)\b")
        self.assertNotRegex(approximation, r"(?m)^\s*(sorry|admit)\b")


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
