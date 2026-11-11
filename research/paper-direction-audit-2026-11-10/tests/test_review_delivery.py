"""Regression contracts for review citation fidelity and usable native TOCs."""

import hashlib
import json
import re
import unittest
import zipfile
from pathlib import Path

from lxml import etree

AUDIT = Path(__file__).resolve().parents[1]
WORKSPACE = AUDIT.parents[2]
FLOQUET = AUDIT / "floquet-superconductivity"
NECESSITY = AUDIT / "necessity-theorem"
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS = {"w": W, "r": R}


def paragraph_text(paragraph):
    return "".join(paragraph.xpath(".//w:t/text()", namespaces=NS))


def document_tree(path):
    with zipfile.ZipFile(path) as package:
        return etree.fromstring(package.read("word/document.xml"))


class ReviewDeliveryTests(unittest.TestCase):
    def test_source_scope_count_matches_registered_citations(self):
        source = (WORKSPACE / "toe-sylva-audit/papers/room_temp_sc/floquet_superconductivity_deep.md").read_text(encoding="utf-8")
        citation_ids = [int(value) for value in re.findall(r"^\| \[(\d+)\] \|", source, flags=re.MULTILINE)]
        self.assertEqual(citation_ids, list(range(1, 24)))
        markdown = (FLOQUET / "REVIEW.md").read_text(encoding="utf-8")
        scope = re.search(r"不是对全部\s*(\d+)\s*条引文", markdown)
        self.assertIsNotNone(scope)
        self.assertEqual(int(scope.group(1)), len(citation_ids))
        review = json.loads((FLOQUET / "review.json").read_text(encoding="utf-8"))
        self.assertEqual(review["source_scope"]["registered_citation_entries"], len(citation_ids))

    def test_chronology_claim_matches_markdown_and_keeps_two_primary_sources(self):
        markdown = (FLOQUET / "REVIEW.md").read_text(encoding="utf-8")
        markdown_line = next(line for line in markdown.splitlines() if "不得把两个时间点混为同一事件" in line)
        expected_text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", markdown_line).replace("**", "").strip()
        expected_text = re.sub(r"^\d+\.\s*", "", expected_text)
        expected_text = re.sub(r"，\[", "，[", expected_text)
        tree = document_tree(FLOQUET / "REVIEW.docx")
        paragraphs = [p for p in tree.xpath("//w:p", namespaces=NS) if "不得把两个时间点混为同一事件" in paragraph_text(p)]
        self.assertEqual(len(paragraphs), 1)
        paragraph = paragraphs[0]
        self.assertEqual(paragraph_text(paragraph), expected_text)
        self.assertEqual(len(paragraph.xpath("./w:hyperlink", namespaces=NS)), 2)
        with zipfile.ZipFile(FLOQUET / "REVIEW.docx") as package:
            rels = etree.fromstring(package.read("word/_rels/document.xml.rels"))
        targets = {rel.get("Id"): rel.get("Target") for rel in rels}
        linked = [targets[node.get(f"{{{R}}}id")] for node in paragraph.xpath("./w:hyperlink", namespaces=NS)]
        self.assertEqual(len([url for url in linked if url.startswith("kimi-cite://web?") and "arxiv.org%2Fabs%2F2312.12706" in url]), 1)
        self.assertEqual(len([url for url in linked if url.startswith("kimi-cite://web?") and "nature.com%2Farticles%2Fs41524-025-01725-z" in url]), 1)

    def test_numeric_result_column_prevents_omega_line_collision(self):
        tree = document_tree(FLOQUET / "REVIEW.docx")
        table = tree.xpath("//w:tbl[.//w:t[contains(., '二能级')]]", namespaces=NS)
        self.assertEqual(len(table), 1)
        widths = [int(value) for value in table[0].xpath("./w:tblGrid/w:gridCol/@w:w", namespaces=NS)]
        self.assertEqual(sum(widths), 9026)
        self.assertGreaterEqual(widths[1], 2600)
        for row in table[0].xpath("./w:tr", namespaces=NS):
            cell_widths = [int(value) for value in row.xpath("./w:tc/w:tcPr/w:tcW/@w:w", namespaces=NS)]
            self.assertEqual(cell_widths, widths)

    def test_tocs_have_visible_pageref_entries_for_every_registered_heading(self):
        for directory in (FLOQUET, NECESSITY):
            with self.subTest(directory=directory.name):
                tree = document_tree(directory / "REVIEW.docx")
                headings = [paragraph_text(p) for p in tree.xpath("//w:p[w:pPr/w:pStyle[@w:val='Heading1' or @w:val='Heading2']]", namespaces=NS)]
                toc_text = "".join(tree.xpath("//w:sdtContent//w:t/text()", namespaces=NS))
                instructions = tree.xpath("//w:sdtContent//w:instrText/text()", namespaces=NS)
                for heading in headings:
                    self.assertIn(heading, toc_text)
                self.assertEqual(sum("PAGEREF" in value for value in instructions), len(headings))
                page_results = tree.xpath("//w:sdtContent//w:instrText[contains(., 'PAGEREF')]/following::w:t[1]/text()", namespaces=NS)
                self.assertTrue(all(value.isdigit() and int(value) >= 2 for value in page_results))
                layout = json.loads((directory / "toc-layout.json").read_text(encoding="utf-8"))
                expected_pages = [page + layout["body_page_offset"] for page in layout["baseline_heading_pages"].values()]
                self.assertEqual([int(value) for value in page_results], expected_pages)
                with zipfile.ZipFile(directory / "REVIEW.docx") as package:
                    settings = etree.fromstring(package.read("word/settings.xml"))
                update = settings.xpath("//w:updateFields/@w:val", namespaces=NS)
                self.assertEqual(update, ["true"])

    def test_toc_targets_have_paired_ascii_bookmarks(self):
        for directory in (FLOQUET, NECESSITY):
            with self.subTest(directory=directory.name):
                tree = document_tree(directory / "REVIEW.docx")
                entries = tree.xpath("//w:sdtContent/w:p[.//w:instrText[contains(., 'PAGEREF')]]", namespaces=NS)
                expected_names = [f"review-h{index}" for index in range(1, len(entries) + 1)]
                anchors = [entry.xpath("./w:hyperlink/@w:anchor", namespaces=NS)[0] for entry in entries]
                self.assertEqual(anchors, expected_names)
                for entry, name in zip(entries, expected_names):
                    instruction = entry.xpath(".//w:instrText[contains(., 'PAGEREF')]/text()", namespaces=NS)[0]
                    self.assertEqual(instruction, f" PAGEREF {name} \\h ")
                    starts = tree.xpath(f"//w:bookmarkStart[@w:name='{name}']/@w:id", namespaces=NS)
                    self.assertEqual(len(starts), 1)
                    self.assertEqual(len(tree.xpath(f"//w:bookmarkEnd[@w:id='{starts[0]}']", namespaces=NS)), 1)

    def test_visual_review_binds_current_docx_and_every_page(self):
        for directory in (FLOQUET, NECESSITY):
            with self.subTest(directory=directory.name):
                manifest = directory / "review-delivery-qa.json"
                self.assertTrue(manifest.is_file())
                result = json.loads(manifest.read_text(encoding="utf-8"))
                self.assertEqual(result["status"], "passed")
                self.assertGreaterEqual(result["pages_reviewed"], 2)
                self.assertEqual(result["pages_reviewed"], len(result["reviewed_pages"]))
                self.assertEqual(result["near_blank_pages"], [])
                self.assertEqual(result["clipped_pages"], [])
                self.assertTrue(result["toc_page_mapping_checked"])
                self.assertTrue(result["source_links_checked"])
                digest = hashlib.sha256((directory / "REVIEW.docx").read_bytes()).hexdigest()
                self.assertEqual(result["docx_sha256"], digest)
                report = directory / "review-delivery-render/report.json"
                self.assertEqual(result["render_report_sha256"], hashlib.sha256(report.read_bytes()).hexdigest())
                render = json.loads(report.read_text(encoding="utf-8"))
                self.assertEqual(render["rendered"], result["pages_reviewed"])
                self.assertFalse(any(row["clipped"] for row in render["pageFiles"]))


def run_all_tests():
    suite = unittest.defaultTestLoader.loadTestsFromModule(__import__(__name__))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() and result.testsRun else 1


if __name__ == "__main__":
    raise SystemExit(run_all_tests())
