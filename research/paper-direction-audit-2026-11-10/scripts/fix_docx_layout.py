"""Apply deterministic CJK and table-layout fixes to an unpacked DOCX."""
from __future__ import annotations

import sys
from pathlib import Path
from lxml import etree

ROOT = Path(sys.argv[1]).resolve()
W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W14 = "http://schemas.microsoft.com/office/word/2010/wordml"
NS = {"w": W}
qn = lambda name: f"{{{W}}}{name}"


def save(tree, path):
    tree.write(str(path), xml_declaration=True, encoding="UTF-8", standalone=True)


for name in ("document.xml", "styles.xml"):
    path = ROOT / "word" / name
    tree = etree.parse(str(path))
    changed = 0
    for fonts in tree.xpath("//w:rFonts", namespaces=NS):
        if fonts.get(qn("eastAsia")) is None and (fonts.get(qn("ascii")) or fonts.get(qn("hAnsi"))):
            fonts.set(qn("eastAsia"), "SimSun")
            changed += 1
    if changed:
        save(tree, path)
    print(f"{name}: eastAsia additions={changed}")

path = ROOT / "word" / "document.xml"
tree = etree.parse(str(path))
sect = tree.xpath("//w:sectPr[last()]", namespaces=NS)[0]
page = sect.find(qn("pgSz"))
if page is None:
    page = etree.SubElement(sect, qn("pgSz"))
page.set(qn("w"), "11906")
page.set(qn("h"), "16838")
margins = sect.find(qn("pgMar"))
if margins is None:
    margins = etree.SubElement(sect, qn("pgMar"))
for side in ("top", "left", "bottom", "right"):
    margins.set(qn(side), "1440")
margins.set(qn("header"), "720")
margins.set(qn("footer"), "720")
margins.set(qn("gutter"), "0")
available = int(page.get(qn("w"))) - int(margins.get(qn("left"))) - int(margins.get(qn("right")))
for table in tree.xpath("//w:tbl", namespaces=NS):
    first_cells = table.xpath("./w:tr[1]/w:tc", namespaces=NS)
    if len(first_cells) == 6:
        widths = [650, 750, 750, 800, 1000, available - 3950]
    elif len(first_cells) == 5:
        widths = [1500, 1900, 1900, 3000, available - 8300]
    elif len(first_cells) == 2:
        widths = [1800, available - 1800]
    else:
        widths = [available // len(first_cells)] * len(first_cells)
        widths[-1] += available - sum(widths)
    table_pr = table.find(qn("tblPr"))
    table_w = table_pr.find(qn("tblW"))
    if table_w is None:
        table_w = etree.SubElement(table_pr, qn("tblW"))
    table_w.set(qn("w"), str(available))
    table_w.set(qn("type"), "dxa")
    grid = table.find(qn("tblGrid"))
    for column, width in zip(grid.findall(qn("gridCol")), widths):
        column.set(qn("w"), str(width))
    for row in table.findall(qn("tr")):
        for cell, width in zip(row.findall(qn("tc")), widths):
            tc_pr = cell.find(qn("tcPr"))
            if tc_pr is None:
                tc_pr = etree.Element(qn("tcPr"))
                cell.insert(0, tc_pr)
            tc_w = tc_pr.find(qn("tcW"))
            if tc_w is None:
                tc_w = etree.SubElement(tc_pr, qn("tcW"))
            tc_w.set(qn("w"), str(width))
            tc_w.set(qn("type"), "dxa")
save(tree, path)
print(f"document.xml: explicit table width={available} twips")

for path in (ROOT / "word").glob("header*.xml"):
    tree = etree.parse(str(path))
    for paragraph in tree.xpath("//w:p", namespaces=NS):
        paragraph.attrib.pop(f"{{{W14}}}paraId", None)
    save(tree, path)
for path in (ROOT / "word").glob("footer*.xml"):
    tree = etree.parse(str(path))
    for paragraph in tree.xpath("//w:p", namespaces=NS):
        paragraph.attrib.pop(f"{{{W14}}}paraId", None)
    save(tree, path)
