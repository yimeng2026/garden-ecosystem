"""Independently re-read the primary sources and check the evidence boundary."""

import hashlib
import json
import math
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
XIE = ROOT.parent / "paper-direction-audit-2026-11-10" / "room-temp-methods" / "sources" / "xie-floquet-fulltext.txt"
ORIGINAL = Path("C:/Users/一梦/Documents/kimi/workspace/toe-sylva-audit/papers/room_temp_sc/room_temp_sc_Formalization.lean")


def compact(text):
    return re.sub(r"\s+", " ", text)


class IndependentFloquetEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "evidence.json").read_text(encoding="utf-8"))
        cls.xie_lines = XIE.read_text(encoding="utf-8").split("\n")
        cls.original_lines = ORIGINAL.read_text(encoding="utf-8").split("\n")

    def excerpt(self, lines):
        start, end = lines
        return compact(" ".join(self.xie_lines[start - 1 : end]))

    def test_original_statement_and_proof_debt_unchanged(self):
        source = next(row for row in self.data["sources"] if row["id"] == "original_lean")
        self.assertEqual(hashlib.sha256(ORIGINAL.read_bytes()).hexdigest(), source["sha256"])
        self.assertIn("theorem floquet_enhanced_tc", self.original_lines[170])
        self.assertIn("∃ T_c_F, T_c_F > T_c_eq", self.original_lines[172])
        self.assertEqual(self.original_lines[184].strip(), "sorry")
        self.assertTrue(self.data["original_theorem"]["bare_existential_trivially_inhabitable"])
        self.assertFalse(self.data["original_theorem"]["trivial_witness_accepted_as_physics"])

    def test_every_anchor_matches_the_read_only_text(self):
        ids = set()
        for row in self.data["source_anchors"]:
            ids.add(row["id"])
            self.assertIn(compact(row["quote"]), self.excerpt(row["lines"]), row["id"])
        self.assertEqual(len(ids), 15)
        xie = next(row for row in self.data["sources"] if row["id"] == "xie_2025")
        self.assertEqual(hashlib.sha256(XIE.read_bytes()).hexdigest(), xie["sha256"])

    def test_off_resonance_and_allen_dynes_are_explicit(self):
        methods = self.excerpt([204, 212])
        self.assertIn("ℏΩ = 400 meV", methods)
        self.assertIn("off-resonance approximations", methods)
        self.assertIn("Allen-Dynes formula", self.excerpt([420, 428]))
        self.assertFalse(self.data["xie_model_assumptions"]["two_gap_resonance_used_to_derive_tc"])

    def test_temperature_rows_match_source_and_rounded_percentages(self):
        expected = {220: (258, 320, 25), 250: (237, 322, 35), 150: (249, 285, None), 200: (240, 301, None)}
        rows = {row["pressure_gpa"]: row for row in self.data["xie_tc_estimates"]}
        self.assertEqual(set(rows), set(expected))
        for pressure, (equilibrium, driven, reported) in expected.items():
            row = rows[pressure]
            self.assertEqual((row["equilibrium_k"], row["driven_k"]), (equilibrium, driven))
            source_excerpt = self.excerpt(row["source_lines"])
            self.assertIn(f"{equilibrium} K", source_excerpt)
            self.assertIn(f"{driven} K", source_excerpt)
            calculated = (driven - equilibrium) / equilibrium * 100
            self.assertTrue(math.isclose(row["recomputed_increase_percent"], calculated))
            if reported is not None:
                # The paper says "yielding a 25% estimated increase" and
                # "yielding a 35% estimated increase". Integer-rounded
                # endpoint ratios do not exactly reproduce those statements.
                self.assertIn(f"a {reported}% estimated increase", source_excerpt)
                self.assertLess(abs(calculated - reported), 1.1)
            else:
                self.assertEqual(row["role"], "dos_scaling_lower_bound_claim_not_general_bound")
                self.assertFalse(row["accurate_prediction"])
            self.assertFalse(row["experimental_confirmation"])

    def test_countermodel_only_tests_the_missing_response_relation(self):
        row = self.data["original_theorem"]["countermodel"]
        self.assertGreater(row["hbar"], 0)
        self.assertTrue(math.isclose(row["omega_drive"], 2 * row["delta"] / row["hbar"]))
        self.assertLess(row["t_c_f_k"], row["t_c_eq_k"])
        self.assertFalse(row["enhancement"])
        self.assertFalse(self.data["original_theorem"]["countermodel_is_physical_evidence"])
        self.assertFalse(self.data["conclusion"]["resonance_enhancement_disproved_experimentally"])

    def test_open_physics_and_no_vacuous_lean_patch(self):
        self.assertEqual(self.data["conclusion"]["resonance_enhancement"], "not_derived")
        self.assertFalse(self.data["conclusion"]["physics_proof_complete"])
        self.assertFalse(self.data["conclusion"]["xie_material_estimates_experimentally_confirmed"])
        text = (ROOT.parent / "lean-proof-slice" / "FloquetApproximation.lean").read_text(encoding="utf-8")
        self.assertNotIn("T_c_eq + 1", text)
        self.assertNotIn("floquet_enhanced_tc", text)
        self.assertIsNone(re.search(r"(?m)^\s*(axiom|postulate|sorry|admit)\b", text))


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
