from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
for stem in ("song-2510.01273", "semenok-2605.29985"):
    pdf = ROOT / f"{stem}.pdf"
    reader = PdfReader(pdf)
    text = "\n\f\n".join(page.extract_text() or "" for page in reader.pages)
    output = ROOT / f"{stem}-fulltext.txt"
    output.write_text(text, encoding="utf-8", newline="\n")
    print(f"{stem}: pages={len(reader.pages)} text_chars={len(text)} pdf_bytes={pdf.stat().st_size}")
