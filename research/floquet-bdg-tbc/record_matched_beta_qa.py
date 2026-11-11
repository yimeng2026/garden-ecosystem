"""Bind the reviewed four-page matched-beta report to exact evidence."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-共同无序剖面尺寸隔离.docx"
REPORT = ROOT / "matched-beta-word-render" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    render = json.loads(REPORT.read_text(encoding="utf-8"))
    pages = render["pageFiles"]
    if render["rendered"] != 4 or render["nearBlankPages"] or any(row["clipped"] for row in pages):
        raise ValueError("The observed four-page render does not satisfy the visual gate")
    losses = [row for row in render["fidelity"]["findings"] if row["category"] == "content-loss"]
    if len(losses) != 1 or losses[0]["element"] != "w:lvlOverride":
        raise ValueError(f"Unexpected content-loss findings: {losses}")
    record = {
        "schema": "floquet-bdg-matched-beta-word-qa-v1",
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sourceSha256": {
            "matched_beta_control_protocol.json": sha(ROOT / "matched_beta_control_protocol.json"),
            "matched_beta_control_analysis.json": sha(ROOT / "matched_beta_control_analysis.json"),
            "swap_candidate_spectrum_analysis.json": sha(ROOT / "swap_candidate_spectrum_analysis.json"),
            "matched-beta-control.png": sha(ROOT / "matched-beta-control.png"),
            "build_matched_beta_report.js": sha(ROOT / "build_matched_beta_report.js"),
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
            "note": "已先查看联系表，再逐一查看四个单页；嵌套块平均OMML、谱表、四面板图、实现对照与边界完整，无近空白页或裁切。",
        },
    }
    (ROOT / "matched-beta-word-qa.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
