from pathlib import Path
from urllib.request import Request, urlopen
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
SOURCES = {
    "xie-floquet": "https://www.nature.com/articles/s41524-025-01725-z.pdf",
    "lasch24": "https://www.pnas.org/doi/epdf/10.1073/pnas.2401840121",
}

for name, url in SOURCES.items():
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=60) as response:
        payload = response.read()
    pdf_path = ROOT / f"{name}.pdf"
    pdf_path.write_bytes(payload)
    reader = PdfReader(pdf_path)
    text = "\n\f\n".join(page.extract_text() or "" for page in reader.pages)
    (ROOT / f"{name}-fulltext.txt").write_text(text, encoding="utf-8", newline="\n")
    print(f"{name}: pages={len(reader.pages)} bytes={len(payload)} text_chars={len(text)}")
