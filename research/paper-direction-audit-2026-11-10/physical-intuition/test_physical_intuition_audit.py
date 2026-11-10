import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class PhysicalIntuitionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))

    def test_source_lineage_and_direction_count(self):
        self.assertEqual(len(self.data["sources"]), 2)
        self.assertEqual(self.data["source_lineage"]["research_program_count"], 1)
        self.assertEqual(len(self.data["directions"]), 4)
        self.assertEqual(len({row["id"] for row in self.data["directions"]}), 4)

    def test_frozen_source_hashes(self):
        expected = {
            "physical-intuition:research/physical-intuition/MATH_PHYSICS_WORLDVIEW_2026.md": "89fc5499acd3f5afd05ffd0b4eacae3f40d33822802679a3c105d34acc0f9eb4",
            "physical-intuition:research/physical-intuition/TOTAL_PROJECT_2026-11-08/TOTAL_REPORT.md": "91f6653c273c3783e9fc71ef8b9b64463a038fecd5763633038e601d93ae862d",
        }
        actual = {row["id"]: row["sha256"] for row in self.data["sources"]}
        self.assertEqual(actual, expected)

    def test_h0_slice_is_not_global_fit_and_does_not_trigger_expansion(self):
        h0 = self.data["evidence"]["h0_scan"]
        self.assertEqual(h0["case_count"], 10)
        self.assertEqual(h0["minimum_h0"], 85.0)
        self.assertAlmostEqual(
            h0["minimum_delta_chi_squared"],
            141291.74549083476,
            delta=1e-8,
        )
        self.assertFalse(h0["expanded_scan_triggered"])
        self.assertFalse(h0["posterior_sampling_performed"])

    def test_open_boundaries_are_explicit(self):
        boundaries = self.data["open_boundaries"]
        self.assertFalse(boundaries["global_cosmological_fit_completed"])
        self.assertFalse(boundaries["nonlinear_matter_spectrum_completed"])
        self.assertFalse(boundaries["extreme_phase_sequence_converged"])
        self.assertFalse(boundaries["accuracy_boost_8_completed"])
        self.assertFalse(boundaries["physical_intuition_engine_validated"])

    def test_actual_test_count_and_other_observations(self):
        verification = self.data["evidence"]
        self.assertEqual(verification["unit_tests"]["passed"], 41)
        self.assertEqual(verification["unit_tests"]["total"], 41)
        self.assertGreater(
            verification["planck_lensing"]["maximum_delta_chi_squared"],
            1238.0,
        )
        self.assertGreater(
            verification["full_cmb_hyrec"]["delta_chi_squared_total"],
            179000.0,
        )
        self.assertLess(
            verification["bbn"]["maximum_absolute_delta_chi_squared"],
            0.005,
        )

    def test_markdown_and_native_word_contract(self):
        markdown = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        self.assertIn("不是整个无 CDM 模型族的排除", markdown)
        self.assertIn("物理直觉引擎尚未验证有效", markdown)
        self.assertIn("图 1", markdown)
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
        self.assertIn(b"<m:oMath", document)
        self.assertIn(b"TOC", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 2)
        self.assertIn(b"PAGE", footer)
        self.assertIn("物理直觉", header.decode("utf-8"))


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
