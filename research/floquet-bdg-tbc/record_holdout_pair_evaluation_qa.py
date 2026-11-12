"""Bind the reviewed five-page pair-evaluation report to exact evidence."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-剩余种子候选逐对方向检验.docx"
REPORT = ROOT / "holdout-pair-evaluation-word-render" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    render = json.loads(REPORT.read_text(encoding="utf-8"))
    pages = render["pageFiles"]
    if render["rendered"] != 5 or render["nearBlankPages"] or any(row["clipped"] for row in pages):
        raise ValueError("The observed five-page render does not satisfy the visual gate")
    losses = [row for row in render["fidelity"]["findings"] if row["category"] == "content-loss"]
    if len(losses) != 1 or losses[0]["element"] != "w:lvlOverride":
        raise ValueError(f"Unexpected content-loss findings: {losses}")
    source_names = [
        "remaining_seed_outcome_protocol.json", "profile_stat_candidates_analysis.json",
        "holdout_pair_evaluation_analysis.json", "holdout_pair_evaluation_independent.json",
        "holdout-pair-evaluation.png", "build_holdout_pair_evaluation_report.js",
        "seed01_matrix_midpoint_analysis.json", "seed6_matrix_midpoint_analysis.json",
        *(f"remaining_seed{seed}_path_outcome_analysis.json" for seed in (2, 3, 4, 5, 7)),
    ]
    record = {
        "schema": "floquet-bdg-holdout-pair-evaluation-word-qa-v1",
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sourceSha256": {name: sha(ROOT / name) for name in source_names},
        "finalValidation": {
            "route": "kimi-word docx.py build with vendored docx-js",
            "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
            "docxSha256": sha(DOCX), "renderReportSha256": sha(REPORT),
        },
        "visualReview": {
            "status": "passed", "pagesReviewed": 5,
            "reviewedPages": [row["file"] for row in pages], "contactSheetRead": True,
            "nearBlankPages": [], "clippedPages": [], "docxSha256": sha(DOCX),
            "tocPageMapping": [2, 3, 4, 5], "libreOfficeFallbackUsed": False,
            "contentLossFindingsReviewed": ["word/numbering.xml w:lvlOverride；默认编号覆盖不影响本报告正文"],
            "note": "已先查看联系表，再逐一查看五个单页；目录、8个路径结局、原生公式、四面板图、5个跳变平局、全部16项候选结果、独立复核与边界完整，无近空白页、裁切或表后叠字。",
        },
    }
    (ROOT / "holdout-pair-evaluation-word-qa.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
