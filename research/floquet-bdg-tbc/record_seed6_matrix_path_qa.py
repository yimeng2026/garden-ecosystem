"""Bind the reviewed five-page seed-6 matrix-path report to exact evidence."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-固定种子矩阵路径.docx"
REPORT = ROOT / "seed6-matrix-path-word-render" / "report.json"


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
    record = {
        "schema": "floquet-bdg-seed6-matrix-path-word-qa-v1",
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sourceSha256": {
            "seed6_matrix_path_protocol.json": sha(ROOT / "seed6_matrix_path_protocol.json"),
            "seed6_matrix_path_analysis.json": sha(ROOT / "seed6_matrix_path_analysis.json"),
            "seed6_matrix_path_independent.json": sha(ROOT / "seed6_matrix_path_independent.json"),
            "matched_beta_batch_b_analysis.json": sha(ROOT / "matched_beta_batch_b_analysis.json"),
            "matched_beta_batch_c_analysis.json": sha(ROOT / "matched_beta_batch_c_analysis.json"),
            "seed6-matrix-path.png": sha(ROOT / "seed6-matrix-path.png"),
            "build_seed6_matrix_path_report.js": sha(ROOT / "build_seed6_matrix_path_report.js"),
        },
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
            "note": "已先查看联系表，再逐一查看五个单页；原生公式、18行谱表、矩阵项与主导通道表、四面板图、原生链接及边界完整，无近空白页、裁切或表后叠字。",
        },
    }
    (ROOT / "seed6-matrix-path-word-qa.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
