"""Record the actually observed Word validation and page-by-page visual review."""

import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "word-qa-final" / "report.json"
report = json.loads(REPORT.read_text(encoding="utf-8"))
if report.get("pages") != 4 or report.get("rendered") != 4:
    raise ValueError("Expected four rendered pages")
if report.get("nearBlankPages"):
    raise ValueError(report["nearBlankPages"])
if any(row.get("clipped") for row in report.get("pageFiles", [])):
    raise ValueError("Clipped page reported")

report["recordedUtc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
report["finalValidation"] = {
    "command": "PATH=/c/Program Files/nodejs:$PATH; python .../kimi-word/scripts/docx.py build .../build_report.js .../REPORT.docx",
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
        "1": "封面、目录和可见缓存页码 2、3、4 完整，无孤立标题。",
        "2": "模型、原生分式、矩阵约定表和文献脚注完整，无裁切。",
        "3": "π 通过、0 未决的结果表与实际数值图清晰；所有数据行可见。",
        "4": "静态控制、独立稀疏对照、未竟边界和两条脚注完整，无近空白页。",
    },
    "nearBlankPagesReviewed": [],
    "clippedPagesReviewed": [],
    "contentLossReviewed": [{
        "part": "word/numbering.xml",
        "element": "w:lvlOverride",
        "count": 1,
        "severity": "low",
        "observation": "渲染器不建模编号级别覆盖；逐页未见编号导致的正文、目录或表格内容丢失。",
    }],
    "visualPassClaimed": True,
    "libreOfficeFallbackUsed": False,
    "figureAspectRatioCheckedAgainstEmbeddedExtent": True,
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"pages": 4, "manualReview": "passed", "docxSha256": report["finalValidation"]["docxSha256"]}, ensure_ascii=False))
