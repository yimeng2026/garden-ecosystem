import csv
import json
import re
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "coverage_inventory": "638f1e0cfb41ed7902869d28677d6adf50cc7644abe7de3a82a9e0ba6d025f7b",
    "base_bib": "ca014a4bae5023081149a1c4d051917e7f0540df18241400992c2b2276d43698",
    "main_claims_review": "e9ac6ff0bc88f11b1c2c91ae61ce398a05fc077815803f48669b46536d6f2f45",
    "main_claims_builder": "ebd3fa8f7459a502218f58e10f1629e0c7de38f9f37905a6ac1c0bde72a4958d",
    "old_enhanced_bib": "d4a7d80243bc2fec0b05af4b0c9519d1be86edd0a62cd0d3d82b94a912ab870f",
}


class RemediationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "remediation.json").read_text(encoding="utf-8"))

    def test_frozen_inputs(self):
        self.assertEqual(len(self.data["source_inputs"]), 5)
        self.assertEqual({row["id"]: row["sha256"] for row in self.data["source_inputs"]}, EXPECTED_HASHES)
        self.assertFalse(self.data["verification_scope"]["source_documents_modified"])

    def test_real_44_navigation(self):
        coverage = self.data["coverage"]
        self.assertEqual(coverage["actual_markdown_count"], 44)
        self.assertEqual(coverage["covered_count"], 44)
        self.assertEqual(coverage["prior_covered_count"], 40)
        self.assertEqual(coverage["current_batch_count"], 4)
        self.assertEqual(coverage["uncovered"], [])
        self.assertEqual(coverage["duplicates"], [])
        self.assertEqual(coverage["groups"], [f"{number:02d}" for number in range(22)])
        self.assertFalse(coverage["prl_delivered"])
        index = (ROOT / "INDEX.md").read_text(encoding="utf-8")
        for row in coverage["rows"]:
            self.assertIn(row["path"], index)
        for text in ("12-资料收集", "21-技术复盘", "PRL 版本未找到", "references_repaired.bib"):
            self.assertIn(text, index)

    def test_csv_44_rows_and_audit_links(self):
        with (ROOT / "coverage.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 44)
        self.assertEqual(len({row["path"] for row in rows}), 44)
        self.assertEqual(
            set(rows[0]),
            {"path", "source_id", "batch", "direction_ids", "source_sha256", "review_path"},
        )
        self.assertTrue(self.data["navigation"]["audit_links_verified"])

    def test_bibtex_27_unique_and_legacy_prefix(self):
        text = (ROOT / "references_repaired.bib").read_text(encoding="utf-8")
        entries = re.findall(r"(?m)^@(\w+)\{([^,]+),", text)
        self.assertEqual(len(entries), 27)
        keys = [key for _, key in entries]
        self.assertEqual(len(set(keys)), 27)
        for identifier in ("10.1073/pnas.2401840121", "2510.01273", "2605.29985"):
            self.assertIn(identifier, text)
        for parent in ROOT.parents:
            candidate = parent / "toe-sylva-audit/papers/room_temp_sc/organized/09-参考文献/01-参考文献.bib"
            if candidate.exists():
                self.assertTrue((ROOT / "references_repaired.bib").read_bytes().startswith(candidate.read_bytes()))
                break
        else:
            self.fail("original base BibTeX not found")
        references = self.data["references"]
        self.assertEqual(references["base_entries"], 24)
        self.assertEqual(references["new_entries"], 3)
        self.assertEqual(references["total_entries"], 27)
        self.assertTrue(references["new_library_parseable"])
        self.assertFalse(references["reference_library_ready"])

    def test_placeholders_and_source_roles(self):
        text = (ROOT / "references_repaired.bib").read_text(encoding="utf-8")
        self.assertEqual(len(re.findall(r"(?m)^% \[TO_BE_COMPLETED", text)), 5)
        self.assertEqual(text.count("TO_BE_COMPLETED"), 6)
        references = self.data["references"]
        self.assertEqual(references["placeholder_sections"], 5)
        self.assertEqual(references["placeholder_token_occurrences"], 6)
        self.assertEqual(references["old_enhanced_entries"], 0)
        roles = {row["id"]: row["role"] for row in self.data["modern_sources"]}
        self.assertEqual(roles["pnas_2024"], "theoretical_prediction")
        self.assertEqual(roles["song_2025"], "author_positive_preprint")
        self.assertEqual(roles["semenok_2026"], "independent_negative_preprint")

    def test_dual_completion_boundaries(self):
        boundaries = self.data["open_boundaries"]
        self.assertTrue(boundaries["navigation_delivery_complete"])
        self.assertTrue(boundaries["reference_delivery_parseable"])
        for key in (
            "reference_library_ready",
            "scientific_validation_complete",
            "all_unfinished_work_completed",
            "lean_proof_complete",
            "experimental_replication_complete",
            "whole_repository_research_complete",
        ):
            self.assertFalse(boundaries[key])
        self.assertFalse(self.data["verification_scope"]["all_legacy_entries_reverified"])

    def test_report_figure_and_native_word(self):
        markdown = (ROOT / "REMEDIATION.md").read_text(encoding="utf-8")
        for text in ("44／44", "24＋3＝27", "可解析≠全部回源", "图 1", "5 个待补区块"):
            self.assertIn(text, markdown)
        for label in ("44／44", "24＋3＝27", "5 个待补区块"):
            self.assertIn(label, self.data["figure"]["labels"])
        with zipfile.ZipFile(ROOT / "REMEDIATION.docx") as package:
            names = package.namelist()
            document = package.read("word/document.xml")
            header = b"".join(package.read(name) for name in names if name.startswith("word/header") and name.endswith(".xml"))
            footer = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn("word/footnotes.xml", names)
        self.assertIn(b"<m:oMath", document)
        self.assertIn(b"TOC", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 5)
        self.assertIn(b"PAGE", footer)
        self.assertIn("导航与参考文献修复", header.decode("utf-8"))
        self.assertTrue(any(name.startswith("word/media/") for name in names))

    def test_toc_cache_and_footnote_claim_mapping(self):
        import xml.etree.ElementTree as ET

        namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        ns = {"w": namespace}
        with zipfile.ZipFile(ROOT / "REMEDIATION.docx") as package:
            root = ET.fromstring(package.read("word/document.xml"))

        def text_of(element):
            return "".join(node.text or "" for node in element.findall(".//w:t", ns))

        toc = root.find(".//w:sdt", ns)
        self.assertIsNotNone(toc)
        cached = [text_of(p) for p in toc.findall(".//w:p", ns)]
        titles = ["一、整改交付与证据图", "二、真实导航与现代来源", "三、输入血缘与验证", "四、剩余边界与下一步"]
        for title, page in zip(titles, [2, 2, 3, 3]):
            self.assertIn(f"{title}{page}", cached)

        expected_references = {
            "覆盖清单来自实际 44 个 Markdown 路径": {"1"},
            "基础 24 条作为字节级前缀保留": {"2"},
            "三条新增记录分别承担理论预测": {"3"},
            "题名、年份、卷页和标识来自": {"4"},
            "旧增强参考文献只有": {"5"},
        }
        referenced = set()
        paragraphs = root.findall(".//w:p", ns)
        for marker, expected in expected_references.items():
            matches = [
                p for p in paragraphs
                if marker in text_of(p) and p.find(".//w:footnoteReference", ns) is not None
            ]
            self.assertEqual(len(matches), 1, marker)
            actual = {
                node.attrib[f"{{{namespace}}}id"]
                for node in matches[0].findall(".//w:footnoteReference", ns)
            }
            self.assertEqual(actual, expected, marker)
            referenced.update(actual)
        self.assertEqual(referenced, {"1", "2", "3", "4", "5"})


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
