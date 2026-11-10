from pathlib import Path
from pypdf import PdfReader

path = Path(__file__).resolve().parent / "sources/htsc-2506.03837v2.pdf"
reader = PdfReader(path)
text = "\n\n".join(f"=== PDF PAGE {index} ===\n{page.extract_text() or ''}" for index, page in enumerate(reader.pages, 1))
output = path.with_suffix(".txt")
output.write_text(text, encoding="utf-8")
print(f"{path.name}: pages={len(reader.pages)}, chars={len(text)}, output={output.name}")
