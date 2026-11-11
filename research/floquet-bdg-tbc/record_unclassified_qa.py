"""Bind the completed four-page visual review to the exact unclassified report."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-未归类与未复现诊断.docx"
REPORT = ROOT / "unclassified-word-render" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    render = json.loads(REPORT.read_text(encoding="utf-8"))
    pages = render["pageFiles"]
    if render["rendered"] != 4 or render["nearBlankPages"] or any(row["clipped"] for row in pages):
        raise ValueError("The observed four-page render does not satisfy the visual gate")
    record = {
        "schema": "floquet-bdg-unclassified-word-qa-v1",
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sourceSha256": {
            "unclassified_signature_analysis.json": sha(ROOT / "unclassified_signature_analysis.json"),
            "repeated_category_analysis.json": sha(ROOT / "repeated_category_analysis.json"),
            "category_new_cells_independent.json": sha(ROOT / "category_new_cells_independent.json"),
            "unclassified-signatures.png": sha(ROOT / "unclassified-signatures.png"),
            "build_unclassified_report.js": sha(ROOT / "build_unclassified_report.js"),
        },
        "finalValidation": {
            "route": "kimi-word docx.py build with vendored docx-js",
            "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
            "docxSha256": sha(DOCX), "renderReportSha256": sha(REPORT),
        },
        "visualReview": {
            "status": "passed", "pagesReviewed": 4,
            "reviewedPages": [row["file"] for row in pages], "contactSheetRead": True,
            "nearBlankPages": [], "clippedPages": [], "docxSha256": sha(DOCX),
            "tocPageMapping": [2, 3, 4], "libreOfficeFallbackUsed": False,
            "note": "全部单页已查看；目录、公式、条件图、未归类表和近 miss 解释清晰，无近空白页或裁切。",
        },
    }
    (ROOT / "unclassified-word-qa.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
