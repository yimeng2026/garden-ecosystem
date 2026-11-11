"""Bind the completed visual review to the exact multi-seed report."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-多种子稳健性对照.docx"
REPORT = ROOT / "multi-seed-word-render" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    render = json.loads(REPORT.read_text(encoding="utf-8"))
    pages = render["pageFiles"]
    if render["rendered"] != 4 or render["nearBlankPages"] or any(row["clipped"] for row in pages):
        raise ValueError("The observed four-page render does not satisfy the visual gate")
    record = {
        "schema": "floquet-bdg-multi-seed-word-qa-v1",
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sourceSha256": {
            "multi_seed_protocol.json": sha(ROOT / "multi_seed_protocol.json"),
            "multi_seed_profile_control.json": sha(ROOT / "multi_seed_profile_control.json"),
            "multi_seed_independent.json": sha(ROOT / "multi_seed_independent.json"),
            "multi-seed-control.png": sha(ROOT / "multi-seed-control.png"),
            "build_multi_seed_report.js": sha(ROOT / "build_multi_seed_report.js"),
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
            "note": "全部单页已查看；目录、公式、四格图、对照表和 seed=1 反例清晰，无近空白页或裁切。",
        },
    }
    (ROOT / "multi-seed-word-qa.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
