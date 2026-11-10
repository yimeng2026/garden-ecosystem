import hashlib
import json
import sys
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED_HASHES = {
    "magazine_readme": "8462664575ea8c2be26f87edb185bd92ad5bd79ed05edc4d9b83a86508f46920",
    "magazine_intro": "7137a7552f2eefd97eee3681da904a35d4bffcb68af12c0e063620f6106f2b3d",
    "pixel_system": "2b05baac70fe8d8760df027d2d625f2801c5c0e947ece6beb3de93a4defe31b2",
    "vi_design": "a7508aeda44598c028c200c0b3bdd1f30807f652c9cc26c88b9171dbefe52826",
    "layout_system": "4602f8893cf31707858ff373c76068d2f080283599cc5894f2ee741d332089f8",
    "content_architecture": "97cfb31cdb3269f3645f5f953b418d001139137eadfae2f562aa37d61db3670a",
    "web_layout": "6c1d2e6d183b63d62a8a7355180f3c6fcbf6711da81a189ae959fe8430c943c4",
    "chat_culture": "fe0dbae3b98307a02b32a286055657e7ecb604f31d621e579789880fe6746a7b",
    "page_designs": "740e6d85ceb025e263f62d1772c8c60270836a39d595c07bf7e696ac71400036",
    "print_guide": "d7ea6c943ea3c33ed16c4d41cbda3e8e5caed48573a3f4104aa8d0a09571ef72",
    "design_notes": "71780e9bce7b365779a7b462091d405100f17508da378d3cb020dc0cc8cc2221",
    "generator": "0d1a07296af61de49ed651f6210e237e561da6e77f9859c5795d3d56a778460c",
    "delivery_report": "95bb50a5188edc8ac904bf5e7c057212d8606a711592222103ccd904ca82c10f",
    "file_index": "8dab54d9cb830f649eed67574fba3fc7c22d85b309f274cfa852d46e8d43d3da",
    "checksums": "b5e402be6adc80031d48994d4b80b6e81ea9b26d73435e791c257517e72e0b69",
    "handbook_review": "0394b996c271a6ca24b4692d7bd078b4c0fa8925eefde6df0347a478f298ac48",
    "technical_review": "d27fca5597387c24e9d0038e971055566522441a1f1f1dd8a0dd7dfe662e305f",
}


class MagazineDesignAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "review.json").read_text(encoding="utf-8"))

    def test_source_freeze_and_lineage(self):
        self.assertEqual(len(self.data["sources"]), 17)
        actual = {row["id"]: row["sha256"] for row in self.data["sources"]}
        self.assertEqual(actual, EXPECTED_HASHES)
        lineage = self.data["evidence"]["lineage"]
        self.assertEqual(lineage["normalized_lf_md5_matches"], 7)
        self.assertEqual(lineage["original_markdown_paths_missing"], 7)
        self.assertEqual(lineage["organized_documents_present"], 11)
        self.assertFalse(lineage["content_loss_inferred_from_raw_md5"])

    def test_directions_and_document_verdicts(self):
        self.assertEqual(self.data["source_lineage"]["research_program_count"], 1)
        self.assertEqual(self.data["source_lineage"]["new_theory_count"], 0)
        self.assertEqual(len(self.data["document_assessments"]), 11)
        self.assertEqual(
            {row["id"] for row in self.data["directions"]},
            {"editorial_evidence", "computational_design", "accessible_media", "production_provenance"},
        )
        for row in self.data["document_assessments"]:
            self.assertFalse(row["represents_new_theory"])
            self.assertTrue(row["direction_ids"])
            self.assertTrue(row["unfinished"])
            self.assertTrue(row["next"])

    def test_generator_and_assets(self):
        row = self.data["evidence"]["assets"]
        self.assertEqual(row["pdf_count"], 6)
        self.assertEqual(
            row["pdf_pages"],
            {
                "Sylva_Magazine_Complete.pdf": 108,
                "Sylva_Magazine_Full.pdf": 22,
                "Sylva_Magazine_RoomTempSC.pdf": 15,
                "Sylva_Magazine_Volume1.pdf": 118,
                "Sylva_Magazine_Volume2.pdf": 21,
                "Sylva_Magazine_Volume3.pdf": 7,
            },
        )
        self.assertTrue(row["all_first_pages_a4"])
        self.assertFalse(row["any_pdf_x_marker"])
        self.assertFalse(row["any_output_intent"])
        self.assertEqual(row["indd_templates_found"], 0)
        self.assertFalse(row["vi_asset_pack_found"])
        self.assertFalse(row["claimed_archive_found"])
        generator = self.data["evidence"]["generator"]
        self.assertEqual(generator["missing_design_docs"], 7)
        self.assertEqual(generator["preview_characters"], 500)
        self.assertTrue(generator["overwrites_three_source_docs"])
        self.assertFalse(generator["complete_magazine_generator"])
        self.assertFalse(generator["executed"])

    def test_layout_and_version_math(self):
        row = self.data["evidence"]["layout"]
        self.assertEqual(row["layout_grid_width_mm"], 212)
        self.assertEqual(row["layout_claimed_text_width_mm"], 174)
        self.assertAlmostEqual(row["layout_correct_column_mm"], 174 / 12 - 11 * 4 / 12)
        self.assertEqual(row["page_grid_width_mm"], 176)
        self.assertEqual(row["page_claimed_text_width_mm"], 165)
        self.assertAlmostEqual(row["page_correct_column_mm"], 165 / 12 - 11 * 4 / 12)
        self.assertEqual(row["intro_pages"], 106)
        self.assertEqual(row["architecture_pages"], 60)
        self.assertEqual(row["cover_story_allocated_pages"], 14)
        self.assertEqual(row["cover_story_detailed_pages"], 16)

    def test_science_and_editorial_claims(self):
        row = self.data["evidence"]["editorial"]
        self.assertTrue(row["mcmillan_strict_proof_claim"])
        self.assertTrue(row["experimental_13_and_6pct_claim"])
        self.assertTrue(row["h2s_pressure_under_magnetic_field_column"])
        self.assertTrue(row["energy_99pct_unverified"])
        self.assertTrue(row["direct_quotes_unverified"])
        self.assertTrue(row["absolute_quantum_security_claim"])
        self.assertTrue(row["production_ready_claim"])
        self.assertFalse(row["production_ready_supported"])

    def test_accessibility_recomputation(self):
        rows = {row["foreground"]: row for row in self.data["evidence"]["accessibility"]["contrast"]}
        self.assertAlmostEqual(rows["#B829DD"]["ratio_on_dark"], 4.137746343925)
        self.assertAlmostEqual(rows["#606070"]["ratio_on_dark"], 3.202043685501)
        self.assertFalse(rows["#B829DD"]["passes_normal_text"])
        self.assertFalse(rows["#606070"]["passes_normal_text"])
        self.assertTrue(rows["#00D9FF"]["passes_normal_text"])
        self.assertFalse(self.data["evidence"]["accessibility"]["reduced_motion_specified"])
        self.assertFalse(self.data["evidence"]["accessibility"]["keyboard_long_press_alternative"])

    def test_corrections_and_open_boundaries(self):
        self.assertEqual(len(self.data["corrections"]), 12)
        self.assertEqual(len({row["id"] for row in self.data["corrections"]}), 12)
        for key in (
            "scientific_claims_verified",
            "production_ready",
            "pdf_print_verified",
            "web_accessibility_verified",
            "archive_verified",
            "full_repository_audit",
        ):
            self.assertFalse(self.data["open_boundaries"][key])
        self.assertFalse(self.data["verification_scope"]["source_documents_modified"])
        self.assertFalse(self.data["verification_scope"]["generator_executed"])

    def test_deliverables_and_native_word(self):
        markdown = (ROOT / "REVIEW.md").read_text(encoding="utf-8")
        for text in ("11 份", "四个方向", "212", "4.137746", "图 1", "全库审计尚未完成"):
            self.assertIn(text, markdown)
        figure = self.data["figure"]
        self.assertIn("212 mm", figure["labels"])
        self.assertIn("4.137746", figure["labels"])
        self.assertFalse(figure["completion_percentage_plotted"])
        with zipfile.ZipFile(ROOT / "REVIEW.docx") as package:
            names = package.namelist()
            document = package.read("word/document.xml")
            header = b"".join(package.read(name) for name in names if name.startswith("word/header") and name.endswith(".xml"))
            footer = b"".join(package.read(name) for name in names if name.startswith("word/footer") and name.endswith(".xml"))
            self.assertIn("word/footnotes.xml", names)
        self.assertIn(b"<m:oMath", document)
        self.assertIn(b"TOC", document)
        self.assertGreaterEqual(document.count(b"<w:tbl>"), 6)
        self.assertIn(b"PAGE", footer)
        self.assertIn("杂志设计", header.decode("utf-8"))
        self.assertTrue(any(name.startswith("word/media/") for name in names))

    def test_toc_cache_and_footnote_claim_mapping(self):
        import xml.etree.ElementTree as ET

        namespace = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        ns = {"w": namespace}
        with zipfile.ZipFile(ROOT / "REVIEW.docx") as package:
            root = ET.fromstring(package.read("word/document.xml"))

        def text_of(element):
            return "".join(node.text or "" for node in element.findall(".//w:t", ns))

        toc = root.find(".//w:sdt", ns)
        self.assertIsNotNone(toc)
        cached = [text_of(p) for p in toc.findall(".//w:p", ns)]
        titles = [
            "一、方向与来源血缘",
            "二、资产与生成链",
            "三、11 份文档逐篇裁决",
            "四、计算、科学与无障碍",
            "五、十二项分级勘误",
            "六、开放边界与后续",
        ]
        for title, page in zip(titles, [2, 3, 4, 4, 4, 5]):
            self.assertIn(f"{title}{page}", cached)

        expected_references = {
            "七份组织后设计文档在 CRLF": {"1"},
            "历史 file_index.json": {"2"},
            "交付报告声称 67 KB": {"4"},
            "generate_pdf.py 对每份设计文档": {"3"},
            "杂志简介把 McMillan": {"5"},
            "既有手册审计明确保留": {"6"},
            "页面设计的数据表把 H₂S": {"7"},
            "网页手册自己要求普通文本": {"8"},
            "网聊手册包含量子通信": {"9"},
            "内容架构标记 READY_FOR_PRODUCTION": {"10"},
            "前批技术文档审计同样要求": {"11"},
        }
        referenced = set()
        paragraphs = root.findall(".//w:p", ns)
        for marker, expected in expected_references.items():
            matches = [p for p in paragraphs if marker in text_of(p)]
            self.assertEqual(len(matches), 1, marker)
            actual = {
                node.attrib[f"{{{namespace}}}id"]
                for node in matches[0].findall(".//w:footnoteReference", ns)
            }
            self.assertEqual(actual, expected, marker)
            referenced.update(actual)
        self.assertEqual(referenced, {str(index) for index in range(1, 12)})


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if result.testsRun == 0:
        return 1
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
