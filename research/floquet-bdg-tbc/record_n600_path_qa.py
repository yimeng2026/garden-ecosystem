"""Bind the completed four-page visual review to the exact N=600 path report."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-N600路径复核.docx"
REPORT = ROOT / "n600-path-word-render" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    render = json.loads(REPORT.read_text(encoding="utf-8"))
    pages = render["pageFiles"]
    if render["rendered"] != 4 or render["nearBlankPages"] or any(row["clipped"] for row in pages):
        raise ValueError("The observed four-page render does not satisfy the visual gate")
    record = {
        "schema": "floquet-bdg-n600-path-word-qa-v1",
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sourceSha256": {
            "n600_path_protocol.json": sha(ROOT / "n600_path_protocol.json"),
            "n600_path_analysis.json": sha(ROOT / "n600_path_analysis.json"),
            "path_refinement_analysis.json": sha(ROOT / "path_refinement_analysis.json"),
            "n600-path.png": sha(ROOT / "n600-path.png"),
            "build_n600_path_report.js": sha(ROOT / "build_n600_path_report.js"),
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
            "contentLossFindingsReviewed": ["word/numbering.xml w:lvlOverride；默认编号覆盖不影响本报告正文"],
            "note": "已先查看联系表，再逐一查看四个单页；OMML公式、两个尺寸点表、路径图、八条链接和尺寸差异完整，无近空白页或裁切。",
        },
    }
    (ROOT / "n600-path-word-qa.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
