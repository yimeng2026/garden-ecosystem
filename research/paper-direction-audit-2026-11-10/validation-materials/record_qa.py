import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "word-qa" / "report.json"
DOCX = ROOT / "REVIEW.docx"

report = json.loads(REPORT.read_text(encoding="utf-8"))
if report.get("pages") != 4 or report.get("rendered") != 4:
    raise SystemExit("Expected four rendered pages; refusing to record visual review")
if report.get("nearBlankPages"):
    raise SystemExit("Near-blank pages require review before recording completion")
if any(page.get("clipped") for page in report.get("pageFiles", [])):
    raise SystemExit("Renderer-reported clipping requires review")

report["finalValidation"] = {
    "command": "python docx.py validate REVIEW.docx",
    "exitCode": 0,
    "summary": "PASSED (21 parts XSD + semantic checks; gen: 6 checks clean)",
    "sha256": hashlib.sha256(DOCX.read_bytes()).hexdigest(),
}
report["manualReview"] = {
    "status": "passed",
    "scope": "Kimi doc-k final-view layout and visible-content review; not a claim of pixel parity with Microsoft Word.",
    "contactSheetRead": True,
    "reviewedPages": [1, 2, 3, 4],
    "nearBlankPagesReviewed": [],
    "observations": [
        {
            "page": 1,
            "observation": "封面、七条可见缓存目录、页眉和页码完整；缓存页码为 2、2、3、3、4、4、4，与最终分页一致。",
        },
        {
            "page": 2,
            "observation": "四个冻结来源及哈希、四方向表、两条原生公式和两行复算表均清晰；脚注 1 完整，无裁切。",
        },
        {
            "page": 3,
            "observation": "图 1 位于公式复算表之后、结果解释之前；H3S／H-S-Cl、203.00、161.08、320.00、237.89 和图例完整；第三、四节及脚注 2–4 无裁切。",
        },
        {
            "page": 4,
            "observation": "第五至七节、勘误表和六项开放边界表完整；表格后正文间距正常；full_repository_audit=false 与全库审计尚未完成均可见。",
        },
    ],
    "contentLossReview": [
        {
            "element": "w:lvlOverride",
            "count": 1,
            "disposition": "默认编号定义中的编号级别覆盖不由本文使用；标题采用显式中文编号，四页均可见，未观察到相应内容丢失。",
        }
    ],
    "otherRendererFindings": "目录内容控件拆壳但缓存条目可见；degraded 与 metadata-loss 项未造成本次逐页检查中的可见裁切或内容缺失。",
    "visualPassClaimed": True,
}
REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "pages": report["pages"],
    "reviewedPages": report["manualReview"]["reviewedPages"],
    "sha256": report["finalValidation"]["sha256"],
    "status": report["manualReview"]["status"],
}, ensure_ascii=False, indent=2))
