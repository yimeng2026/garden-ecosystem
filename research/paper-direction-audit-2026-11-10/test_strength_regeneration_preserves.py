import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

AUDIT = Path(__file__).resolve().parent


def workspace_root():
    for parent in AUDIT.parents:
        if (parent / "garden-ecosystem").is_dir() and (parent / "toe-sylva-audit").is_dir():
            return parent
    raise RuntimeError("cannot locate workspace containing garden-ecosystem and toe-sylva-audit")


RESEARCH = workspace_root() / "garden-ecosystem/research"
SCRIPT = AUDIT / "scripts/render_strength_review.py"
INPUTS = [
    "math-focus.json",
    "strength-review.json",
    "strength-review-summary.json",
    "STRENGTH_SERIES_REVIEW.md",
]
RECORD_BASELINE = {
    "id",
    "series",
    "title",
    "role",
    "novelty",
    "unfinished",
    "priority",
    "evidence",
    "source_line_1",
}
SUMMARY_BASELINE = {
    "status",
    "reviewed",
    "series",
    "priorities",
    "unique_ids",
    "evidence_files_exist",
    "external_novelty_certified",
    "machine_proofs_certified_by_this_review",
}


class RegenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before_records = json.loads(
            (AUDIT / "strength-review.json").read_text(encoding="utf-8")
        )["records"]
        cls.before_summary = json.loads(
            (AUDIT / "strength-review-summary.json").read_text(encoding="utf-8")
        )
        cls.before_md = (AUDIT / "STRENGTH_SERIES_REVIEW.md").read_text(encoding="utf-8")
        cls.temp = tempfile.TemporaryDirectory(
            prefix="strength-regeneration-",
            dir=RESEARCH,
        )
        cls.copy = Path(cls.temp.name)
        (cls.copy / "scripts").mkdir()
        shutil.copy2(SCRIPT, cls.copy / "scripts/render_strength_review.py")
        for name in INPUTS:
            shutil.copy2(AUDIT / name, cls.copy / name)
        cls.completed = subprocess.run(
            [sys.executable, str(cls.copy / "scripts/render_strength_review.py")],
            cwd=cls.copy,
            encoding="utf-8",
            capture_output=True,
            timeout=120,
        )
        if cls.completed.returncode != 0:
            raise RuntimeError(
                f"base renderer failed: {cls.completed.stdout}\n{cls.completed.stderr}"
            )
        cls.after_records = json.loads(
            (cls.copy / "strength-review.json").read_text(encoding="utf-8")
        )["records"]
        cls.after_summary = json.loads(
            (cls.copy / "strength-review-summary.json").read_text(encoding="utf-8")
        )
        cls.after_md = (cls.copy / "STRENGTH_SERIES_REVIEW.md").read_text(encoding="utf-8")

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_resolution_fields_preserved_by_id(self):
        after_by_id = {record["id"]: record for record in self.after_records}
        losses = []
        for before in self.before_records:
            after = after_by_id.get(before["id"], {})
            for key, value in before.items():
                if key not in RECORD_BASELINE and after.get(key) != value:
                    losses.append((before["id"], key))
        self.assertEqual(losses, [])

    def test_summary_resolution_fields_preserved(self):
        losses = [
            key
            for key, value in self.before_summary.items()
            if key not in SUMMARY_BASELINE and self.after_summary.get(key) != value
        ]
        self.assertEqual(losses, [])

    def test_supplements_preserved_in_order_without_duplicates(self):
        headings = [
            line[3:].strip()
            for line in self.before_md.splitlines()
            if line.startswith(("## K1a ", "## K1b ", "## K2 "))
        ]
        self.assertEqual(len(headings), 17)
        self.assertTrue(all(self.after_md.count(heading) == 1 for heading in headings))
        positions = [self.after_md.index(heading) for heading in headings]
        self.assertEqual(positions, sorted(positions))


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
