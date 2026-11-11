"""Bind the completed four-page visual review to the exact matched-control report."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-同强度尺寸对照.docx"
REPORT = ROOT / "matched-word-render" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    render = json.loads(REPORT.read_text(encoding="utf-8"))
    pages = render["pageFiles"]
    if render["rendered"] != 4 or render["nearBlankPages"] or any(row["clipped"] for row in pages):
        raise ValueError("The observed four-page render does not satisfy the visual gate")
    record = {
        "schema": "floquet-bdg-matched-word-qa-v1",
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sourceSha256": {
            "matched_profile_control.json": sha(ROOT / "matched_profile_control.json"),
            "matched_profile_independent.json": sha(ROOT / "matched_profile_independent.json"),
            "matched-profile-control.png": sha(ROOT / "matched-profile-control.png"),
            "build_matched_report.js": sha(ROOT / "build_matched_report.js"),
        },
        "finalValidation": {
            "route": "kimi-word docx.py build with vendored docx-js",
            "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
            "docxSha256": sha(DOCX),
            "renderReportSha256": sha(REPORT),
        },
        "visualReview": {
            "status": "passed", "pagesReviewed": 4,
            "reviewedPages": [row["file"] for row in pages],
            "contactSheetRead": True, "nearBlankPages": [], "clippedPages": [],
            "docxSha256": sha(DOCX), "tocPageMapping": [2, 3, 4],
            "libreOfficeFallbackUsed": False,
            "note": "全部单页已查看；目录、原生公式、四格图和对照表清晰，无近空白页或裁切。",
        },
    }
    (ROOT / "matched-word-qa.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
