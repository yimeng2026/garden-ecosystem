"""Independent verification of generated remediation assets and source integrity."""

import csv
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

from test_remediation import EXPECTED_HASHES

ROOT = Path(__file__).resolve().parent
AUDIT_ROOT = ROOT.parent / "paper-direction-audit-2026-11-10"
DATA = json.loads((ROOT / "remediation.json").read_text(encoding="utf-8"))


def source_root():
    for parent in ROOT.parents:
        candidate = parent / "toe-sylva-audit/papers/room_temp_sc"
        if candidate.is_dir():
            return candidate
    raise FileNotFoundError("room_temp_sc source root")


PAPER = source_root()
PATHS = {
    "coverage_inventory": AUDIT_ROOT / "project-intro/sources/coverage-inventory.json",
    "base_bib": PAPER / "organized/09-参考文献/01-参考文献.bib",
    "main_claims_review": AUDIT_ROOT / "main-claims/review.json",
    "main_claims_builder": AUDIT_ROOT / "main-claims/build_report.js",
    "old_enhanced_bib": PAPER / "organized/09-参考文献/02-增强参考文献.bib",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class IndependentRemediationTests(unittest.TestCase):
    def test_inputs_unchanged(self):
        for source_id, expected in EXPECTED_HASHES.items():
            self.assertEqual(sha256(PATHS[source_id]), expected, source_id)
        self.assertFalse(DATA["verification_scope"]["source_documents_modified"])

    def test_navigation_against_real_tree(self):
        actual = {path.relative_to(PAPER / "organized").as_posix() for path in (PAPER / "organized").rglob("*.md")}
        rows = DATA["coverage"]["rows"]
        paths = [row["path"] for row in rows]
        index = (ROOT / "INDEX.md").read_text(encoding="utf-8")
        self.assertEqual(len(actual), 44)
        self.assertEqual(set(paths), actual)
        self.assertEqual(len(set(paths)), 44)
        for row in rows:
            self.assertIn(row["path"], index)
            self.assertEqual(sha256(PAPER / "organized" / row["path"]), row["source_sha256"])
            self.assertTrue((AUDIT_ROOT / row["batch"] / "REVIEW.md").exists(), row["batch"])
        for number in range(22):
            self.assertIn(f"{number:02d}", DATA["coverage"]["groups"])
        self.assertIn("PRL 版本未找到", index)
        self.assertIn("references_repaired.bib", index)

    def test_csv_and_links(self):
        with (ROOT / "coverage.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 44)
        self.assertEqual(len({row["path"] for row in rows}), 44)
        for row in rows:
            self.assertTrue((AUDIT_ROOT / row["batch"] / "REVIEW.md").exists(), row["path"])
            self.assertEqual(len(row["source_sha256"]), 64)

    def test_bibtex_structure_and_legacy_prefix(self):
        generated = (ROOT / "references_repaired.bib").read_bytes()
        self.assertTrue(generated.startswith(PATHS["base_bib"].read_bytes()))
        text = generated.decode("utf-8")
        entries = re.findall(r"(?m)^@(\w+)\{([^,]+),", text)
        keys = [key for _, key in entries]
        self.assertEqual(len(entries), 27)
        self.assertEqual(len(set(keys)), 27)
        for identifier in ("10.1073/pnas.2401840121", "2510.01273", "2605.29985"):
            self.assertIn(identifier, text)
        for role_comment in ("theoretical prediction only", "author-reported positive preprint", "independent negative replication preprint"):
            self.assertIn(role_comment, text)
        self.assertEqual(len(re.findall(r"(?m)^% \[TO_BE_COMPLETED", text)), 5)
        self.assertEqual(text.count("TO_BE_COMPLETED"), 6)

    def test_old_enhanced_not_reused(self):
        raw = PATHS["old_enhanced_bib"].read_bytes()
        self.assertEqual(len(raw), 22)
        self.assertEqual(raw.decode("utf-8").strip(), ": true # [source skip]")
        self.assertEqual(len(re.findall(r"(?m)^@", raw.decode("utf-8"))), 0)
        self.assertNotEqual((ROOT / "references_repaired.bib").read_bytes(), raw)
        self.assertEqual(DATA["references"]["old_enhanced_entries"], 0)

    def test_dual_completion_and_roles(self):
        boundaries = DATA["open_boundaries"]
        self.assertTrue(boundaries["navigation_delivery_complete"])
        self.assertTrue(boundaries["reference_delivery_parseable"])
        for key in ("reference_library_ready", "scientific_validation_complete", "all_unfinished_work_completed", "lean_proof_complete", "experimental_replication_complete", "whole_repository_research_complete"):
            self.assertFalse(boundaries[key], key)
        roles = {row["id"]: row["role"] for row in DATA["modern_sources"]}
        self.assertEqual(roles["pnas_2024"], "theoretical_prediction")
        self.assertEqual(roles["song_2025"], "author_positive_preprint")
        self.assertEqual(roles["semenok_2026"], "independent_negative_preprint")
        self.assertFalse(DATA["verification_scope"]["all_legacy_entries_reverified"])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
