"""Independent verification of final sources and coverage, without review.json."""

import hashlib
import json
import re
import sys
import unittest
import zipfile
from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET

from test_project_intro_audit import EXPECTED_HASHES

ROOT = Path(__file__).resolve().parent
INVENTORY = json.loads((ROOT / "sources/coverage-inventory.json").read_text(encoding="utf-8"))
REVIEWS = {
    "main_claims_review": "main-claims",
    "theory_review": "theory-breakthrough",
    "validation_review": "validation-materials",
    "isotope_review": "isotope-dft",
    "dmrg_review": "dmrg-qec",
    "data_review": "data-governance",
    "handbook_review": "handbook-chapters",
    "methods_review": "room-temp-methods",
    "technical_review": "technical-docs",
    "magazine_review": "magazine-design",
}


def roots():
    for parent in ROOT.parents:
        candidate = parent / "toe-sylva-audit/papers/room_temp_sc"
        if candidate.is_dir():
            return candidate, candidate / "organized"
    raise FileNotFoundError("room_temp_sc organized root")


PAPER, ORGANIZED = roots()
PATHS = {
    "directory_index": ORGANIZED / "00-目录索引.md",
    "project_intro": ORGANIZED / "01-封面与介绍/01-项目说明.md",
    "handbook_intro": ORGANIZED / "01-封面与介绍/02-手册说明.md",
    "magazine_plan": ORGANIZED / "01-封面与介绍/03-杂志简介.md",
    "base_bib": ORGANIZED / "09-参考文献/01-参考文献.bib",
    "enhanced_bib": ORGANIZED / "09-参考文献/02-增强参考文献.bib",
    "original_readme": PAPER / "README.md",
    "handbook_task": PAPER / "HANDBOOK_TASK.md",
    "handbook_docx": PAPER / "handbook/room_temp_sc_handbook.docx",
}
for source_id, batch in REVIEWS.items():
    PATHS[source_id] = ROOT.parent / batch / "review.json"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class PrimarySourceTests(unittest.TestCase):
    def test_frozen_sources(self):
        self.assertEqual(len(INVENTORY["sources"]), 19)
        for source_id, expected in EXPECTED_HASHES.items():
            self.assertEqual(sha256(PATHS[source_id]), expected, source_id)

    def test_coverage_against_real_tree_and_reviews(self):
        actual = {path.relative_to(ORGANIZED).as_posix() for path in ORGANIZED.rglob("*.md")}
        rows = INVENTORY["coverage"]["rows"]
        paths = [row["path"] for row in rows]
        self.assertEqual(len(actual), 44)
        self.assertEqual(set(paths), actual)
        self.assertEqual(len(set(paths)), 44)
        self.assertNotIn("00-目录索引.md", INVENTORY["coverage"]["uncovered"])
        self.assertEqual(INVENTORY["coverage"]["duplicates"], [])
        counts = Counter(row["batch"] for row in rows if row["batch"] != "project-intro")
        self.assertEqual(sum(counts.values()), 40)
        for row in rows:
            self.assertEqual(sha256(ORGANIZED / row["path"]), row["source_sha256"])
            if row["batch"] == "project-intro":
                continue
            review = json.loads((ROOT.parent / row["review_path"]).read_text(encoding="utf-8"))
            self.assertEqual(sha256(ROOT.parent / row["review_path"]), row["review_sha256"])
            self.assertIn(row["source_id"], {source["id"] for source in review["sources"]})

    def test_index_and_reference_sources(self):
        index = PATHS["directory_index"].read_text(encoding="utf-8")
        base = PATHS["base_bib"].read_text(encoding="utf-8")
        enhanced = PATHS["enhanced_bib"].read_text(encoding="utf-8")
        self.assertIn("PRL", index)
        self.assertFalse(any("prl" in path.stem.lower() for path in (ORGANIZED / "02-主论文").glob("*.md")))
        for number in range(12, 22):
            self.assertTrue(any(path.name.startswith(f"{number}-") for path in ORGANIZED.glob("*.md")), number)
        self.assertEqual(len(re.findall(r"(?m)^@", base)), 24)
        self.assertEqual(len(re.findall(r"(?m)^% \[TO_BE_COMPLETED", base)), 5)
        self.assertEqual(base.count("TO_BE_COMPLETED"), 6)
        self.assertEqual(enhanced.strip(), ": true # [source skip]")
        self.assertEqual(len(re.findall(r"(?m)^@", enhanced)), 0)
        for identifier in ("2510.01273", "2605.29985", "2401840121"):
            self.assertNotIn(identifier, base)

    def test_formalization_and_version_lineage(self):
        project = PATHS["project_intro"].read_text(encoding="utf-8")
        original = PATHS["original_readme"].read_text(encoding="utf-8")
        self.assertIn("admit/sorry", project)
        self.assertIn("不会报错", project)
        self.assertIn("实现五个形式化模块", project)
        self.assertFalse((PAPER / "theoretical_framework.md").exists())
        self.assertFalse((PAPER / "RoomTempSuperconductivity.lean").exists())
        for module in ("SymmetryClassification", "MaterialFamily", "ManyBodyPairing", "MetaTheorems", "Renormalization"):
            self.assertFalse(any(PAPER.rglob(f"Superconductivity.{module}.lean")), module)
        self.assertIn("v7.33", original)
        self.assertIn("0.1-alpha", project)
        self.assertNotEqual(
            PATHS["original_readme"].read_bytes().replace(b"\r\n", b"\n"),
            PATHS["project_intro"].read_bytes().replace(b"\r\n", b"\n"),
        )

    def test_handbook_timeline_and_metadata(self):
        text = PATHS["handbook_intro"].read_text(encoding="utf-8")
        self.assertIn("最后更新**：2025年4月", text)
        self.assertIn("2025年10月", text)
        with zipfile.ZipFile(PATHS["handbook_docx"]) as package:
            app = ET.fromstring(package.read("docProps/app.xml"))
            properties = {element.tag.split("}")[-1]: element.text for element in app}
            self.assertEqual(properties["Pages"], "1")
            self.assertEqual(properties["Words"], "0")
            self.assertEqual(len([name for name in package.namelist() if name.startswith("word/media/")]), 0)
            self.assertNotIn(b"<m:oMath", package.read("word/document.xml"))

    def test_open_status_not_erased_by_coverage(self):
        coverage = INVENTORY["coverage"]
        false_count = 0
        for batch in REVIEWS.values():
            review = json.loads((ROOT.parent / batch / "review.json").read_text(encoding="utf-8"))
            false_count += sum(value is False for value in review.get("open_boundaries", {}).values())
        self.assertEqual(false_count, 64)
        self.assertEqual(coverage["prior_open_false_items"], 64)
        self.assertTrue(coverage["organized_44_coverage_complete"])
        self.assertFalse(coverage["whole_repository_research_complete"])


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
