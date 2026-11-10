import hashlib
import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "delivery_summary": "957e71d98c74e813bed8780614552b20b0802f0ec6c4c598e2f3a39d2c49cdfc",
    "final_report": "563b2fae7222a9ac9ccec3fac849b467e9ae46d571e99def0ef423a9f878e667",
    "progress_report": "a4ffcdc575a2d9f0ae21108b5679856ed022c827bdd549020dc1f3be59d524bb",
    "quality_progress": "0da15ed8122b1908bb8ce155956aebd55166330ca094982f81c6637624354d64",
    "integration_checklist": "1510c3bc360560a1b131c9352616cd28717691abee41ff3951231a65d26d2909",
    "main_claims_review": "e9ac6ff0bc88f11b1c2c91ae61ce398a05fc077815803f48669b46536d6f2f45",
    "validation_review": "17eaa27d30df6849f752e3712d563ebe492ae394ea9c74b1b072ac0755acb491",
    "methods_review": "f30d15d8665644d11957166efaea95d59f7a742037dc697b737704cd15dc9e21",
    "handbook_review": "0394b996c271a6ca24b4692d7bd078b4c0fa8925eefde6df0347a478f298ac48",
}


class TechnicalDocsAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))
        cls.inventory_hash = hashlib.sha256((ROOT / "sources/artifact-inventory.json").read_bytes()).hexdigest()

    def test_source_lineage_and_directions(self):
        self.assertEqual(self.data["source_lineage"]["research_program_count"], 1)
        self.assertEqual(len(self.data["directions"]), 4)
        self.assertEqual(
            {row["id"] for row in self.data["directions"]},
            {"artifact_existence", "status_evidence", "scientific_validation", "delivery_governance"},
        )
        expected = dict(EXPECTED_HASHES, artifact_inventory=self.inventory_hash)
        self.assertEqual({row["id"]: row["sha256"] for row in self.data["sources"]}, expected)

    def test_status_contradiction(self):
        row = self.data["evidence"]["status"]
        self.assertTrue(row["final_100_claimed"])
        self.assertTrue(row["a_and_d_running"])
        self.assertTrue(row["quality_deepening_ongoing"])
        self.assertTrue(row["checklist_template"])
        self.assertTrue(row["contradiction"])

    def test_artifact_existence(self):
        row = self.data["evidence"]["assets"]
        self.assertFalse(row["tar_exists"])
        self.assertFalse(row["md5_verifiable"])
        self.assertEqual(row["figures_found"], 0)
        self.assertEqual(row["references_enhanced_found"], 0)
        self.assertFalse(row["prl_tex_exists"])
        self.assertTrue(row["claimed_markdown_missing"])
        self.assertEqual(row["tex_variants_present"], 4)
        self.assertFalse(row["expected_lean_exists"])
        self.assertTrue(row["alternate_lean_exists"])
        self.assertTrue(row["alternate_si_exists"])
        self.assertEqual(row["si_placeholder_count"], 31)

    def test_scientific_validation(self):
        row = self.data["evidence"]["science"]
        self.assertAlmostEqual(row["h3s_computed_tc_k"], 161.08184379177882)
        self.assertEqual(row["h3s_claimed_tc_k"], 203)
        self.assertFalse(row["scoring_rubric_available"])
        self.assertFalse(row["lean_build_passed"])
        self.assertFalse(row["direct_meissner_completed"])
        self.assertFalse(row["independent_positive_replication"])
        self.assertTrue(row["pnas_is_prediction"])

    def test_metadata_and_open_boundaries(self):
        row = self.data["evidence"]["metadata"]
        self.assertEqual(row["delivery_date"], "2025-04-19")
        self.assertEqual(row["cited_breakthrough_month"], "2025-10")
        self.assertTrue(row["date_precedes_cited_breakthrough"])
        for key in (
            "tar_verified",
            "figures_verified",
            "references99_verified",
            "scientific_validation",
            "delivery_ready",
            "full_repository_audit",
        ):
            self.assertFalse(self.data["open_boundaries"][key])

    def test_corrections_and_figure(self):
        self.assertEqual(len(self.data["corrections"]), 8)
        for label in ("完成状态 100%", "TEMPLATE", "room_temp_sc_paper_FINAL_v2.tar.gz", "references_enhanced.bib", "manuscript_prl.tex"):
            self.assertIn(label, self.data["figure"]["labels"])
        self.assertFalse(self.data["figure"]["completion_percentage_plotted"])

    def test_markdown_source_count(self):
        markdown = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        self.assertEqual(len(self.data["sources"]), 10)
        self.assertIn("本批使用十项冻结来源", markdown)
        self.assertNotIn("本批使用九项冻结来源", markdown)

    def test_native_word_contract(self):
        markdown = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        for text in ("完成状态 100%", "未找到", "161.081844", "图 1", "全库审计尚未完成"):
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
        self.assertIn("技术文档交付与验证", header.decode("utf-8"))
        self.assertTrue(any(name.startswith("word/media/") for name in names))
        for source_id in (
            "2510.01273",
            "024508",
            "01-交付摘要.md",
            "02-最终报告.md",
            "03-进度报告.md",
            "04-质量进展.md",
            "05-整合检查清单.md",
        ):
            self.assertIn(source_id, footnotes)

    def test_footnote_claim_mapping_and_toc_cache(self):
        import xml.etree.ElementTree as ET

        namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        ns = {"w": namespace}
        with zipfile.ZipFile(ROOT / "REVIEW.docx") as package:
            root = ET.fromstring(package.read("word/document.xml"))

        def text_of(element):
            return "".join(node.text or "" for node in element.findall(".//w:t", ns))

        paragraphs = root.findall(".//w:p", ns)
        expected_references = {
            "最终报告写完成状态 100%": {"4"},
            "最终报告还声称 99 条引用": {"2"},
            "进度报告中的 A／D 运行中": {"3"},
            "整合检查清单明确保留": {"5"},
            "实际资产清单同时保留": {"6"},
            "H₃S 的文内参数": {"8", "10"},
            "Lean 未编译且存在证明债务": {"9"},
            "Song 的直接 Meissner": {"7"},
            "交付日期 2025-04-19 早于所引 2025-10 突破，构成元数据时间矛盾": {"1"},
        }
        referenced = set()
        for marker, expected in expected_references.items():
            matches = [p for p in paragraphs if marker in text_of(p)]
            self.assertEqual(len(matches), 1, marker)
            actual = {
                node.attrib[f"{{{namespace}}}id"]
                for node in matches[0].findall(".//w:footnoteReference", ns)
            }
            self.assertEqual(actual, expected, marker)
            referenced.update(actual)
        self.assertEqual(referenced, {str(index) for index in range(1, 11)})

        toc = root.find(".//w:sdt", ns)
        self.assertIsNotNone(toc)
        cached = [text_of(p) for p in toc.findall(".//w:p", ns)]
        expected_toc = [
            ("一、血缘裁决与四个发展方向", "2"),
            ("二、状态矛盾与实际资产", "2"),
            ("三、科学验证仍不闭合", "3"),
            ("四、分档勘误与验收任务", "4"),
            ("五、验证范围与开放边界", "4"),
        ]
        for title, page in expected_toc:
            self.assertIn(f"{title}{page}", cached)


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
