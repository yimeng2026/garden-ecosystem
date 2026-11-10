import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DOCX = ROOT / "REVIEW.docx"
REPORT = ROOT / "word-qa" / "report.json"
report = json.loads(REPORT.read_text(encoding="utf-8"))
if report.get("pages") != 5 or report.get("rendered") != 5:
    raise ValueError("final visual review requires exactly five rendered pages")
if report.get("nearBlankPages"):
    raise ValueError(f"near-blank pages require review: {report['nearBlankPages']}")

report["finalValidation"] = {
    "command": "python docx.py validate REVIEW.docx",
    "exitCode": 0,
    "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
    "sha256": hashlib.sha256(DOCX.read_bytes()).hexdigest(),
}
report["manualReview"] = {
    "status": "passed",
    "contactSheetRead": True,
    "reviewedPages": [1, 2, 3, 4, 5],
    "pageObservations": {
        "1": "封面和目录完整；六个可见缓存页码为 2、3、4、4、4、5。",
        "2": "四方向、七项 LF-MD5 血缘和 17 项来源哈希完整，文字与表格未越界，两条来源脚注可见。",
        "3": "资产、生成器和六份 PDF 表格完整；图 1 位于资产表之后、逐篇裁决之前，两条脚注可见。",
        "4": "11 篇裁决、两个原生公式、计算表、科学边界及勘误表头完整；六条对应脚注可见，无裁切。",
        "5": "勘误表跨页重复表头，开放边界、后续任务、结尾和技术文档来源脚注完整，无孤立末页。",
    },
    "tocCachedPages": [2, 3, 4, 4, 4, 5],
    "nearBlankPagesReviewed": [],
    "contentLossReviewed": [
        {
            "part": "word/numbering.xml",
            "element": "w:lvlOverride",
            "count": 1,
            "severity": "low",
            "observation": "渲染器提示编号级别覆盖兼容性；逐页未见编号导致的内容缺失，标题、目录、表格和脚注均可见。",
        }
    ],
    "layoutIterations": 2,
    "layoutCorrection": "初次为七页，后三节强制分页留白过多；取消后三节强制分页后为五页，再按实际页面把目录修正为 2、3、4、4、4、5 并逐页复核。",
    "magazinePdfVisualReviewClaimed": False,
    "magazinePdfScope": "六份杂志 PDF 仅做只读元数据检查；本视觉验收只针对审计 REVIEW.docx。",
    "visualPassClaimed": True,
    "libreOfficeFallbackUsed": False,
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "pages": report["pages"],
    "rendered": report["rendered"],
    "manualReview": report["manualReview"]["status"],
    "visualPassClaimed": report["manualReview"]["visualPassClaimed"],
    "sha256": report["finalValidation"]["sha256"],
}, ensure_ascii=False, indent=2))
