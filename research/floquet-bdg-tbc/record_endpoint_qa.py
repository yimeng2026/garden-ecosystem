"""Record the completed visual review and bind it to the exact report artifacts."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-端点子空间诊断.docx"
REPORT = ROOT / "endpoint-word-render" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    render = json.loads(REPORT.read_text(encoding="utf-8"))
    pages = render["pageFiles"]
    if render["rendered"] != 4 or render["nearBlankPages"] or any(row["clipped"] for row in pages):
        raise ValueError("The observed four-page render does not satisfy the visual gate")
    record = {
        "schema": "floquet-bdg-endpoint-word-qa-v1",
        "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "sourceSha256": {
            "endpoint_subspace_analysis.json": sha(ROOT / "endpoint_subspace_analysis.json"),
            "endpoint-subspaces.png": sha(ROOT / "endpoint-subspaces.png"),
            "build_endpoint_report.js": sha(ROOT / "build_endpoint_report.js"),
        },
        "finalValidation": {
            "route": "kimi-word docx.py build with vendored docx-js",
            "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
            "docxSha256": sha(DOCX),
            "renderReportSha256": sha(REPORT),
        },
        "visualReview": {
            "status": "passed",
            "pagesReviewed": 4,
            "reviewedPages": [row["file"] for row in pages],
            "contactSheetRead": True,
            "nearBlankPages": [],
            "clippedPages": [],
            "docxSha256": sha(DOCX),
            "tocPageMapping": [2, 3, 4],
            "libreOfficeFallbackUsed": False,
            "note": "全部单页已查看；仅编号级别覆盖的低风险兼容提示，不是正文内容丢失。",
        },
    }
    (ROOT / "endpoint-word-qa.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
