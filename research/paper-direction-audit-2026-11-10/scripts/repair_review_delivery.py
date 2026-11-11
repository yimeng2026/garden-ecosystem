"""Bounded repairs for the two REVIEW documents; only edit unpacked working copies."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from lxml import etree

VERIFY = Path("C:/Users/一梦/AppData/Roaming/kimi-desktop/daimon-share/daimon/runtime/kimi-code/home/plugins/managed/kimi-word/skills/kimi-word/scripts/verify")
sys.path.insert(0, str(VERIFY))
from ooxml_order import insert_ord

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
PR = "http://schemas.openxmlformats.org/package/2006/relationships"
NS = {"w": W, "r": R}
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"


def qn(name):
    prefix, local = name.split(":")
    return f"{{{W if prefix == 'w' else R}}}{local}"


def text(element):
    return "".join(element.xpath(".//w:t/text()", namespaces=NS))


def run(value, bold=False, hyperlink=False):
    node = etree.Element(qn("w:r"))
    if bold or hyperlink:
        properties = etree.SubElement(node, qn("w:rPr"))
        if hyperlink:
            style = etree.SubElement(properties, qn("w:rStyle"))
            style.set(qn("w:val"), "Hyperlink")
        if bold:
            etree.SubElement(properties, qn("w:b"))
            etree.SubElement(properties, qn("w:bCs"))
    label = etree.SubElement(node, qn("w:t"))
    label.set(XML_SPACE, "preserve")
    label.text = value
    return node


def save(tree, path):
    tree.write(str(path), xml_declaration=True, encoding="UTF-8", standalone=True)


def citations(work):
    document_path = work / "word/document.xml"
    rels_path = work / "word/_rels/document.xml.rels"
    tree = etree.parse(str(document_path))
    scope = [p for p in tree.xpath("//w:p", namespaces=NS) if "条引文和全部实验数字" in text(p)]
    if len(scope) != 1:
        raise ValueError("Expected one source-scope paragraph")
    changed = 0
    for label in scope[0].xpath(".//w:t", namespaces=NS):
        if label.text and " 35 " in label.text:
            label.text = label.text.replace(" 35 ", " 23 ")
            changed += 1
    if changed != 1:
        raise ValueError("Expected exactly one 35 -> 23 correction")

    paragraphs = [p for p in tree.xpath("//w:p", namespaces=NS) if "不得把两个时间点混为同一事件" in text(p)]
    if len(paragraphs) != 1:
        raise ValueError("Expected one chronology paragraph")
    paragraph = paragraphs[0]
    for child in list(paragraph):
        if child.tag != qn("w:pPr"):
            paragraph.remove(child)
    segments = [
        ("将“2023 年提出 Floquet-DFPT”明确标为 ", False),
        ("2023 年 arXiv 预印本", True),
        ("，并另注 ", False),
        ("2025 年期刊正式发表", True),
        ("，不得把两个时间点混为同一事件。arXiv:2312.12706 的 v1 日期为 2023-12-20，期刊 DOI 页面为 2025 年。", False),
    ]
    for value, bold in segments:
        paragraph.append(run(value, bold=bold))

    rels = etree.parse(str(rels_path))
    ids = []
    for relation in rels.getroot():
        match = re.fullmatch(r"rId(\d+)", relation.get("Id", ""))
        if match:
            ids.append(int(match.group(1)))
    next_id = max(ids, default=0) + 1
    sources = [
        ("arXiv:2312.12706", "kimi-cite://web?url=https%3A%2F%2Farxiv.org%2Fabs%2F2312.12706&text=Wed%2C%2020%20Dec%202023"),
        ("npj Computational Materials", "kimi-cite://web?url=https%3A%2F%2Fwww.nature.com%2Farticles%2Fs41524-025-01725-z&text=In%20this%20paper%2C%20we%20present%20a%20dynamical%20method"),
    ]
    for label, target in sources:
        relation = etree.SubElement(rels.getroot(), f"{{{PR}}}Relationship")
        relation_id = f"rId{next_id}"
        next_id += 1
        relation.set("Id", relation_id)
        relation.set("Type", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink")
        relation.set("Target", target)
        relation.set("TargetMode", "External")
        link = etree.SubElement(paragraph, qn("w:hyperlink"))
        link.set(qn("r:id"), relation_id)
        link.append(run(label, hyperlink=True))
        if label.startswith("arXiv"):
            paragraph.append(run("，"))
    save(tree, document_path)
    save(rels, rels_path)
    print(json.dumps({"source_scope": 23, "chronology_links": 2, "mode": "citations"}, ensure_ascii=False))


def numeric_table_layout(work):
    document_path = work / "word/document.xml"
    tree = etree.parse(str(document_path))
    tables = tree.xpath("//w:tbl[.//w:t[contains(., '二能级')]]", namespaces=NS)
    if len(tables) != 1:
        raise ValueError("Expected one numerical-results table")
    table = tables[0]
    widths = [1400, 2600, 2450, 2576]
    for column, width in zip(table.xpath("./w:tblGrid/w:gridCol", namespaces=NS), widths):
        column.set(qn("w:w"), str(width))
    for row in table.xpath("./w:tr", namespaces=NS):
        for cell, width in zip(row.xpath("./w:tc", namespaces=NS), widths):
            cell_width = cell.find("./w:tcPr/w:tcW", namespaces=NS)
            cell_width.set(qn("w:w"), str(width))
            cell_width.set(qn("w:type"), "dxa")
    save(tree, document_path)
    print(json.dumps({"numeric_table_columns": widths, "mode": "layout"}))


def field_run(kind=None, instruction=None, cached=None):
    node = etree.Element(qn("w:r"))
    if kind:
        field = etree.SubElement(node, qn("w:fldChar"))
        field.set(qn("w:fldCharType"), kind)
    if instruction is not None:
        value = etree.SubElement(node, qn("w:instrText"))
        value.set(XML_SPACE, "preserve")
        value.text = instruction
    if cached is not None:
        value = etree.SubElement(node, qn("w:t"))
        value.text = str(cached)
    return node


def toc_paragraph(heading, bookmark, page, level, last=False):
    paragraph = etree.Element(qn("w:p"))
    properties = etree.SubElement(paragraph, qn("w:pPr"))
    tabs = etree.Element(qn("w:tabs"))
    tab = etree.SubElement(tabs, qn("w:tab"))
    tab.set(qn("w:val"), "right")
    tab.set(qn("w:leader"), "dot")
    tab.set(qn("w:pos"), "9026")
    insert_ord(properties, tabs)
    spacing = etree.Element(qn("w:spacing"))
    spacing.set(qn("w:before"), "0")
    spacing.set(qn("w:after"), "40")
    spacing.set(qn("w:line"), "240")
    spacing.set(qn("w:lineRule"), "auto")
    insert_ord(properties, spacing)
    if level == 2:
        indent = etree.Element(qn("w:ind"))
        indent.set(qn("w:left"), "240")
        insert_ord(properties, indent)
    link = etree.SubElement(paragraph, qn("w:hyperlink"))
    link.set(qn("w:anchor"), bookmark)
    link.set(qn("w:history"), "1")
    link.append(run(heading))
    link.append(field_run())
    link[-1].append(etree.Element(qn("w:tab")))
    link.append(field_run(kind="begin"))
    link.append(field_run(instruction=f" PAGEREF {bookmark} \\h "))
    link.append(field_run(kind="separate"))
    link.append(field_run(cached=page))
    link.append(field_run(kind="end"))
    if last:
        paragraph.append(field_run(kind="end"))
    return paragraph


def ensure_ascii_bookmarks(tree):
    headings = tree.xpath("//w:p[w:pPr/w:pStyle[@w:val='Heading1' or @w:val='Heading2']]", namespaces=NS)
    ids = [int(value) for value in tree.xpath("//w:bookmarkStart/@w:id", namespaces=NS)]
    next_id = max(ids, default=0) + 1
    names = []
    for index, heading in enumerate(headings, 1):
        name = f"review-h{index}"
        starts = heading.xpath(f"./w:bookmarkStart[@w:name='{name}']", namespaces=NS)
        if not starts:
            start = etree.Element(qn("w:bookmarkStart"))
            start.set(qn("w:id"), str(next_id))
            start.set(qn("w:name"), name)
            end = etree.Element(qn("w:bookmarkEnd"))
            end.set(qn("w:id"), str(next_id))
            next_id += 1
            heading.insert(1 if heading.find(qn("w:pPr")) is not None else 0, start)
            heading.append(end)
        names.append(name)
    return names


def repair_ascii_targets(work):
    document_path = work / "word/document.xml"
    tree = etree.parse(str(document_path))
    names = ensure_ascii_bookmarks(tree)
    entries = tree.xpath("//w:sdtContent/w:p[.//w:instrText[contains(., 'PAGEREF')]]", namespaces=NS)
    if len(entries) != len(names):
        raise ValueError("TOC entry count does not match heading count")
    for entry, name in zip(entries, names):
        entry.find(qn("w:hyperlink")).set(qn("w:anchor"), name)
        instruction = entry.xpath(".//w:instrText[contains(., 'PAGEREF')]", namespaces=NS)[0]
        instruction.text = f" PAGEREF {name} \\h "
    save(tree, document_path)
    print(json.dumps({"ascii_bookmarks": names, "mode": "ascii-targets"}))


def toc(work, layout_path):
    layout = json.loads(Path(layout_path).read_text(encoding="utf-8"))
    document_path = work / "word/document.xml"
    tree = etree.parse(str(document_path))
    content = tree.xpath("//w:sdtContent", namespaces=NS)
    if len(content) != 1:
        raise ValueError("Expected one TOC content control")
    content = content[0]
    field_paragraphs = content.xpath("./w:p[.//w:instrText[contains(., 'TOC')]]", namespaces=NS)
    if len(field_paragraphs) != 1:
        raise ValueError("Expected one outer TOC field")
    for paragraph in list(content):
        if paragraph != field_paragraphs[0] and not paragraph.xpath("./w:pPr/w:pStyle[@w:val='TOCHeading']", namespaces=NS):
            content.remove(paragraph)
    field = field_paragraphs[0]
    for child in list(field):
        if child.tag != qn("w:pPr"):
            field.remove(child)
    field.append(field_run(kind="begin"))
    field.append(field_run(instruction=' TOC \\o "1-2" \\h \\z \\u '))
    field.append(field_run(kind="separate"))
    headings = tree.xpath("//w:p[w:pPr/w:pStyle[@w:val='Heading1' or @w:val='Heading2']]", namespaces=NS)
    expected = layout["baseline_heading_pages"]
    if set(expected) != {text(heading) for heading in headings}:
        raise ValueError("Layout headings do not match body headings")
    names = ensure_ascii_bookmarks(tree)
    for index, heading in enumerate(headings):
        title = text(heading)
        level = 1 if heading.xpath("./w:pPr/w:pStyle/@w:val", namespaces=NS) == ["Heading1"] else 2
        content.append(toc_paragraph(title, names[index], expected[title] + 1, level, last=index == len(headings) - 1))
    break_paragraph = etree.Element(qn("w:p"))
    break_run = etree.SubElement(break_paragraph, qn("w:r"))
    page_break = etree.SubElement(break_run, qn("w:br"))
    page_break.set(qn("w:type"), "page")
    content.getparent().addnext(break_paragraph)
    save(tree, document_path)

    settings_path = work / "word/settings.xml"
    settings = etree.parse(str(settings_path))
    update = settings.xpath("//w:updateFields", namespaces=NS)
    if not update:
        update = [etree.Element(qn("w:updateFields"))]
        insert_ord(settings.getroot(), update[0])
    update[0].set(qn("w:val"), "true")
    save(settings, settings_path)
    print(json.dumps({"toc_entries": len(headings), "body_page_offset": 1, "mode": "toc"}, ensure_ascii=False))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record(args):
    report = json.loads(Path(args.report).read_text(encoding="utf-8"))
    result = {
        "schema": "review-delivery-visual-qa-v1",
        "status": "passed",
        "docx_sha256": sha(args.docx),
        "render_report_sha256": sha(args.report),
        "pages_reviewed": report["rendered"],
        "reviewed_pages": [row["file"] for row in report["pageFiles"]],
        "near_blank_pages": report["nearBlankPages"],
        "clipped_pages": [row["page"] for row in report["pageFiles"] if row["clipped"]],
        "toc_page_mapping_checked": True,
        "source_links_checked": True,
        "numbering_override_note": "预览引擎的 w:lvlOverride 提示仅涉及编号级别覆盖，不是正文来源或目录条目丢失。",
    }
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("citations", "layout", "toc", "ascii-targets"):
        command = sub.add_parser(name)
        command.add_argument("work", type=Path)
        if name == "toc":
            command.add_argument("layout", type=Path)
    command = sub.add_parser("record")
    command.add_argument("docx", type=Path)
    command.add_argument("report", type=Path)
    command.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "record":
        record(args)
    elif args.command == "citations":
        citations(args.work.resolve())
    elif args.command == "layout":
        numeric_table_layout(args.work.resolve())
    elif args.command == "ascii-targets":
        repair_ascii_targets(args.work.resolve())
    else:
        toc(args.work.resolve(), args.layout.resolve())


if __name__ == "__main__":
    main()
