"""Add a restrained header and a native PAGE field to a DOCX or unpacked report."""
from pathlib import Path
from contextlib import nullcontext
import sys

VERIFY = r"C:\Users\一梦\AppData\Roaming\kimi-desktop\daimon-share\daimon\runtime\kimi-code\home\plugins\managed\kimi-word\skills\kimi-word\scripts\verify"
sys.path.insert(0, VERIFY)
import opc
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

root = Path(sys.argv[1]).resolve()
report_title = sys.argv[2] if len(sys.argv) > 2 else "论文方向与未竟工作初审 · 2026-11-10"
with (opc.edit_docx(root) if root.is_dir() else nullcontext(__import__("docx").Document(str(root)))) as doc:
    for section in doc.sections:
        section.header.is_linked_to_previous = False
        paragraph = section.header.paragraphs[0]
        paragraph.style = doc.styles["Normal"]
        paragraph.text = report_title
        paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for run in paragraph.runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(8.5)
            run.font.color.rgb = RGBColor(0x55, 0x71, 0x80)
            run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "SimSun")

        section.footer.is_linked_to_previous = False
        footer = section.footer.paragraphs[0]
        footer.style = doc.styles["Normal"]
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        prefix = footer.add_run("第 ")
        begin = footer.add_run()
        begin_char = OxmlElement("w:fldChar")
        begin_char.set(qn("w:fldCharType"), "begin")
        begin._r.append(begin_char)
        instruction = footer.add_run()
        instruction_text = OxmlElement("w:instrText")
        instruction_text.set(qn("xml:space"), "preserve")
        instruction_text.text = " PAGE "
        instruction._r.append(instruction_text)
        separate = footer.add_run()
        separate_char = OxmlElement("w:fldChar")
        separate_char.set(qn("w:fldCharType"), "separate")
        separate._r.append(separate_char)
        result = footer.add_run("1")
        end = footer.add_run()
        end_char = OxmlElement("w:fldChar")
        end_char.set(qn("w:fldCharType"), "end")
        end._r.append(end_char)
        suffix = footer.add_run(" 页")
        for run in footer.runs:
            run.font.name = "Times New Roman"
            run.font.size = Pt(8.5)
            run.font.color.rgb = RGBColor(0x55, 0x71, 0x80)
            run._element.get_or_add_rPr().get_or_add_rFonts().set(qn("w:eastAsia"), "SimSun")
if root.is_file():
    doc.save(str(root))
print("header and native PAGE field added")
