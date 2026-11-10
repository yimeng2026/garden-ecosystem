from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent / "sources"
FILES = [
    "kruglov-1810.01113.pdf",
    "isotope-1912.09663.pdf",
    "jarvis-2312.12694.pdf",
]
for name in FILES:
    path = ROOT / name
    reader = PdfReader(path)
    text = "\n\n".join(f"=== PDF PAGE {index} ===\n{page.extract_text() or ''}" for index, page in enumerate(reader.pages, 1))
    output = path.with_suffix(".txt")
    output.write_text(text, encoding="utf-8")
    print(f"{name}: pages={len(reader.pages)}, chars={len(text)}, output={output.name}")
