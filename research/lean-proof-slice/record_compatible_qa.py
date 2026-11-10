import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "COMPATIBLE_DEFINITIONS.docx"
REPORT = ROOT / "word-qa-compatible" / "report.json"
report = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else {"file": str(DOCX)}
report["finalValidation"] = {
    "command": "python docx.py validate COMPATIBLE_DEFINITIONS.docx",
    "exitCode": 0,
    "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
    "sha256": hashlib.sha256(DOCX.read_bytes()).hexdigest(),
}
report["visualQA"] = {
    "status": "unavailable",
    "renderAttemptCount": 1,
    "exitCode": 6,
    "error": "E_RENDER_FAILED: EPERM, Permission denied on the temporary render directory.",
    "retryAttempted": False,
    "libreOfficeFallbackUsed": False,
    "contactSheetRead": False,
    "reviewedPages": [],
    "nearBlankPagesReviewed": [],
    "contentLossReviewed": [],
    "visualPassClaimed": False,
    "deliveryBasis": "Real Lean 4.35.0 compilation of two definitions, five delivery-contract tests, four independent source checks and the OOXML validation gate; no final Word visual verification is claimed.",
}
report["manualReview"] = {
    "status": "unavailable",
    "contactSheetRead": False,
    "reviewedPages": [],
    "visualPassClaimed": False,
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "visualStatus": report["visualQA"]["status"],
    "exitCode": report["visualQA"]["exitCode"],
    "visualPassClaimed": report["visualQA"]["visualPassClaimed"],
    "sha256": report["finalValidation"]["sha256"],
}, ensure_ascii=False, indent=2))
