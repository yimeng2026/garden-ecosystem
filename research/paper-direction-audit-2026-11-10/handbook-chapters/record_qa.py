import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "word-qa" / "report.json"
REPORT.parent.mkdir(parents=True, exist_ok=True)
DOCX = ROOT / "REVIEW.docx"
report = {
    "file": str(DOCX),
    "engine": "doc-k final view (attempted)",
    "renderAttemptCount": 1,
    "finalValidation": {
        "command": "python docx.py validate REVIEW.docx",
        "exitCode": 0,
        "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
        "sha256": hashlib.sha256(DOCX.read_bytes()).hexdigest(),
    },
    "visualQA": {
        "status": "unavailable",
        "exitCode": 6,
        "error": "E_RENDER_FAILED: EPERM, Permission denied on the temporary render directory.",
        "retryAttempted": False,
        "libreOfficeFallbackUsed": False,
        "contactSheetRead": False,
        "reviewedPages": [],
        "nearBlankPagesReviewed": [],
        "contentLossReviewed": [],
        "visualPassClaimed": False,
        "deliveryBasis": "OOXML validation gate, nine delivery-contract tests, eight independent source tests and separate source-figure review only; no final Word visual verification is claimed.",
    },
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "visualStatus": report["visualQA"]["status"],
    "exitCode": report["visualQA"]["exitCode"],
    "sha256": report["finalValidation"]["sha256"],
    "visualPassClaimed": report["visualQA"]["visualPassClaimed"],
}, ensure_ascii=False, indent=2))
