"""Independently verify main-claims review data against saved primary evidence."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent


class PrimarySourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))
        cls.song = (ROOT / "sources/song-2510.01273-fulltext.txt").read_text(encoding="utf-8")
        cls.semenok = (ROOT / "sources/semenok-2605.29985-fulltext.txt").read_text(encoding="utf-8")
        cls.excerpts = (ROOT / "sources/primary-source-excerpts.md").read_text(encoding="utf-8")
        for parent in ROOT.parents:
            candidate = parent / ".worktrees/critical-manifold/papers/room_temp_sc/critical_manifold/results.json"
            if candidate.is_file():
                cls.critical = json.loads(candidate.read_text(encoding="utf-8"))
                break
        else:
            raise FileNotFoundError("critical-manifold results.json")

    def test_song_positive_report_and_future_meissner(self):
        for text in (
            "Through thirteen reproducible experimental runs",
            "271-298 kelvin at 195-266 GPa",
            "Extending such measurements above 200 GPa",
            "direct magnetic characterization",
        ):
            self.assertIn(text, self.song)
        row = self.data["evidence"]["song"]
        self.assertEqual(row["reproducible_runs_reported"], 13)
        self.assertFalse(row["direct_meissner_completed"])

    def test_semenok_negative_replication(self):
        for text in (
            "Seven experimental attempts",
            "unsuccessful",
            "245-300 K",
            "The method for preparing the precursor",
        ):
            self.assertIn(text, self.semenok)
        row = self.data["evidence"]["semenok"]
        self.assertEqual(row["unsuccessful_attempts"], 7)
        self.assertEqual(row["no_superconductivity_range_k"], [245, 300])

    def test_nature_crossref_mismatch(self):
        self.assertIn("10.1038/s41586-024-07036-5", self.excerpts)
        self.assertIn("Twisted-layer boron nitride ceramic with high deformability and strength", self.excerpts)
        self.assertIn("Nature 626, 779–784 (2024)", self.excerpts)
        self.assertTrue(self.data["evidence"]["nature_citation"]["citation_mismatch"])

    def test_anecdote_has_no_located_support(self):
        for text in ("42nd", "43rd", "success rate", "million RMB"):
            self.assertNotIn(text, self.song)
        self.assertEqual(self.data["evidence"]["handbook_narrative"]["anecdote_status"], "unverified")

    def test_critical_counterexample_consistency(self):
        expected = self.data["evidence"]["critical_manifold"]
        self.assertEqual(self.critical["domain"]["root_count"], expected["root_count"])
        self.assertEqual(self.critical["domain"]["grid_point_count"], expected["grid_point_count"])
        self.assertEqual(self.critical["summary"]["grid_class_disagreements"], expected["grid_class_disagreements"])
        actual_anchors = [row["tc_K"] for row in self.critical["temperature_anchors"]]
        expected_anchors = [row["tc_K"] for row in expected["temperature_anchors"]]
        self.assertEqual(actual_anchors, expected_anchors)
        self.assertTrue(all(value < 300 for value in actual_anchors))


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
