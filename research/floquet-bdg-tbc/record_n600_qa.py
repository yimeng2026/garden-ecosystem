"""Record N=600 DOCX validation and unavailable visual QA without overstating it."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "Floquet-BdG-N600尾长诊断报告.docx"
REPORT = ROOT / "n600-word-qa" / "report.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    report = json.loads(REPORT.read_text(encoding="utf-8")) if REPORT.exists() else {}
    sources = {
        "build_n600_report.js": sha(ROOT / "build_n600_report.js"),
        "n600-result.png": sha(ROOT / "n600-result.png"),
        "n600-coverage.png": sha(ROOT / "n600-coverage.png"),
    }
    if report.get("sourceSha256") and report["sourceSha256"] != sources:
        raise ValueError("N=600 source changed after the render attempt")
    docx_hash = sha(DOCX)
    report.update({
        "file": str(DOCX), "pages": None, "rendered": 0, "nearBlankPages": None,
        "sourceSha256": sources,
        "finalValidation": {
            "route": "kimi-word docx.py build with vendored docx-js 9.7.1",
            "exitCode": 0, "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
            "docxSha256": docx_hash,
            "scaleDiagnosticSha256": sha(ROOT / "scale_diagnostic.json"),
            "scaleIndependentSha256": sha(ROOT / "scale_independent_n600.json"),
            "n600ScaleSha256": sha(ROOT / "n600_scale.json"),
        },
        "visualReview": {
            "recordedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "status": "unavailable_exit_6_no_retry",
            "renderAttempted": True,
            "error": "E_RENDER_FAILED: temporary-directory permission denied",
            "visualPassClaimed": False,
            "libreOfficeFallbackUsed": False,
            "contactSheetRead": False,
            "reviewedPages": [],
        },
    })
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"visualReview": "unavailable_exit_6_no_retry", "visualPassClaimed": False, "docxSha256": docx_hash}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
