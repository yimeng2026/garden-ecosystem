from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent / "sources"
FILES = [
    "stripes-2501.15709.pdf",
    "dwave-2211.06322.pdf",
    "extended-hubbard-2206.03486.pdf",
    "google-2408.13687.pdf",
    "xzzx-surface-code.pdf",
    "neutral-atoms-s41586-023-06927-3.pdf",
]
for name in FILES:
    path = ROOT / name
    reader = PdfReader(path)
    text = "\n\n".join(f"=== PDF PAGE {index} ===\n{page.extract_text() or ''}" for index, page in enumerate(reader.pages, 1))
    output = path.with_suffix(".txt")
    output.write_text(text, encoding="utf-8")
    print(f"{name}: pages={len(reader.pages)}, chars={len(text)}, output={output.name}")
