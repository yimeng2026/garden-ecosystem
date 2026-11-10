"""Record the observed four-page visual review and final artifact hashes."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "word-qa" / "report.json"
report = json.loads(REPORT.read_text(encoding="utf-8"))
if report.get("pages") != 4 or report.get("rendered") != 4 or report.get("nearBlankPages"):
    raise ValueError("Expected four nonblank rendered pages")
if any(row.get("clipped") for row in report.get("pageFiles", [])):
    raise ValueError("Clipped page reported")
report["recordedUtc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
report["finalValidation"] = {
    "command": "PATH=/c/Program Files/nodejs:$PATH; DOCX_PY_NO_VENDOR=1; python .../docx.py build .../build_report.js .../REPORT.docx",
    "exitCode": 0,
    "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
    "docxSha256": hashlib.sha256((ROOT / "REPORT.docx").read_bytes()).hexdigest(),
    "resultsSha256": hashlib.sha256((ROOT / "results.json").read_bytes()).hexdigest(),
}
report["manualReview"] = {
    "status": "passed",
    "contactSheetRead": True,
    "reviewedPages": [1, 2, 3, 4],
    "tocCachedPages": [2, 3, 4],
    "pageObservations": {
        "1": "封面、目录及缓存页码 2、3、4 完整。",
        "2": "子空间公式、尾部公式和方法修正表完整，无符号裁切。",
        "3": "尾部和包络表格、四联图及来源脚注完整，无字体方框。",
        "4": "IPR 表、独立验证、短链支持和全尺寸未决边界清晰，无近空白页。",
    },
    "contentLossReviewed": [{
        "part": "word/numbering.xml",
        "element": "w:lvlOverride",
        "count": 1,
        "severity": "low",
        "observation": "渲染器提示编号级别覆盖兼容性；逐页未见正文、目录或表格内容丢失。",
    }],
    "visualPassClaimed": True,
    "libreOfficeFallbackUsed": False,
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"pages": 4, "manualReview": "passed", "docxSha256": report["finalValidation"]["docxSha256"]}, ensure_ascii=False))
